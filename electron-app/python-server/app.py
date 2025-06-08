from flask import Flask, request, jsonify, Response
import anthropic
import pdfplumber
from docx import Document
from bs4 import BeautifulSoup
import os
import json
import io
import sys
import requests
from url_enhancer import URLEnhancer

app = Flask(__name__)

# Get data directory from environment or use default
DATA_DIR = os.environ.get('ELECTRON_DATA_DIR', os.path.dirname(os.path.abspath(__file__)))
API_KEY_FILE = os.path.join(DATA_DIR, 'api_key.json')

def extract_text_from_pdf(file_content):
    """Extract text from PDF file"""
    text = ""
    with pdfplumber.open(io.BytesIO(file_content)) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

def extract_text_from_docx(file_content):
    """Extract text from DOCX file"""
    doc = Document(io.BytesIO(file_content))
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text

def extract_text_from_html(file_content):
    """Extract text from HTML file"""
    soup = BeautifulSoup(file_content, 'lxml')
    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()
    text = soup.get_text()
    # Clean up text
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = '\n'.join(chunk for chunk in chunks if chunk)
    return text

@app.route('/check-api-key')
def check_api_key():
    return jsonify({'hasKey': os.path.exists(API_KEY_FILE)})

@app.route('/save-api-key', methods=['POST'])
def save_api_key():
    data = request.get_json()
    api_key = data.get('key')
    
    # Ensure data directory exists
    os.makedirs(DATA_DIR, exist_ok=True)
    
    with open(API_KEY_FILE, 'w') as f:
        json.dump({'key': api_key}, f)
    
    return jsonify({'success': True})

@app.route('/reset-api-key', methods=['POST'])
def reset_api_key():
    if os.path.exists(API_KEY_FILE):
        os.remove(API_KEY_FILE)
    return jsonify({'success': True})

@app.route('/convert-stream', methods=['POST'])
def convert_stream():
    """Stream the conversion response"""
    # Extract all request data before creating generator
    try:
        # Get API key
        if not os.path.exists(API_KEY_FILE):
            return Response(
                f"data: {json.dumps({'error': 'API key not configured'})}\n\n",
                mimetype='text/event-stream'
            )
        
        with open(API_KEY_FILE, 'r') as f:
            api_key = json.load(f)['key']
        
        # Get uploaded file
        file = request.files.get('file')
        if not file:
            return Response(
                f"data: {json.dumps({'error': 'No file uploaded'})}\n\n",
                mimetype='text/event-stream'
            )
        
        file_content = file.read()
        filename = file.filename.lower()
        
        # Extract text based on file type
        print(f"Extracting text from {filename}...", flush=True)
        if filename.endswith('.pdf'):
            text = extract_text_from_pdf(file_content)
        elif filename.endswith(('.doc', '.docx')):
            text = extract_text_from_docx(file_content)
        elif filename.endswith(('.html', '.htm')):
            text = extract_text_from_html(file_content)
        else:
            return Response(
                f"data: {json.dumps({'error': 'Unsupported file type'})}\n\n",
                mimetype='text/event-stream'
            )
        
        if not text.strip():
            return Response(
                f"data: {json.dumps({'error': 'Could not extract text from file'})}\n\n",
                mimetype='text/event-stream'
            )
        
        print(f"Extracted {len(text)} characters", flush=True)
        
        # Truncate if too long to prevent token limits
        if len(text) > 100000:  # Increased limit for Claude 4
            text = text[:100000] + "\n\n[Article continues but was truncated due to length...]"
            print("Text truncated to 100000 characters", flush=True)
        
    except Exception as e:
        import traceback
        print(f"Error processing request: {str(e)}", flush=True)
        print(f"Traceback: {traceback.format_exc()}", flush=True)
        return Response(
            f"data: {json.dumps({'error': str(e)})}\n\n",
            mimetype='text/event-stream'
        )
    
    # Generator function with all data captured
    def generate():
        try:
            # Convert to markdown using Claude with streaming
            client = anthropic.Anthropic(api_key=api_key)
            
            print("Starting Claude 3.5 Sonnet streaming response...", flush=True)
            
            stream = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=8192,  # Claude 4 supports up to 64K output tokens
                temperature=0,
                messages=[
                    {
                        "role": "user",
                        "content": f"""Convert the following article text to Markdown format.

IMPORTANT: This is a FORMAT CONVERSION, not a summary. Include EVERY sentence.

CRITICAL INSTRUCTIONS:
1. Fix OCR errors (e.g., "technolo y" -> "technology", "LLiisstteenn" -> "Listen")
2. Use proper Markdown formatting (# for main title, ## for sections, etc.)
3. Include ALL paragraphs and sentences - do not skip anything
4. Remove only obvious website UI elements (like "https://www.bloomberg.com/..." URLs)
5. Keep author names, dates, and all article content
6. DO NOT stop early or say "Content continues" - include the ENTIRE article
7. DO NOT be lazy - convert the COMPLETE text provided
8. If the text is long, that's fine - use all 8192 tokens if needed

Article text:

{text}"""
                    }
                ],
                stream=True
            )
            
            chunk_count = 0
            total_text = ""
            for event in stream:
                if event.type == "content_block_delta":
                    chunk_count += 1
                    text_chunk = event.delta.text
                    total_text += text_chunk
                    yield f"data: {json.dumps({'chunk': text_chunk})}\n\n"
                    if chunk_count % 50 == 0:
                        print(f"  Streamed {chunk_count} chunks, {len(total_text)} chars...", flush=True)
            
            print(f"Streaming complete: {chunk_count} chunks, {len(total_text)} chars", flush=True)
            yield f"data: {json.dumps({'done': True})}\n\n"
                    
        except Exception as e:
            import traceback
            print(f"Error in streaming: {str(e)}", flush=True)
            print(f"Traceback: {traceback.format_exc()}", flush=True)
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')

@app.route('/convert-url-stream')
def convert_url_stream():
    """Stream the conversion response for a URL"""
    # Get URL from query parameter
    url = request.args.get('url')
    if not url:
        return Response(
            f"data: {json.dumps({'error': 'No URL provided'})}\n\n",
            mimetype='text/event-stream'
        )
    
    try:
        # Get API key
        if not os.path.exists(API_KEY_FILE):
            return Response(
                f"data: {json.dumps({'error': 'API key not configured'})}\n\n",
                mimetype='text/event-stream'
            )
        
        with open(API_KEY_FILE, 'r') as f:
            api_key = json.load(f)['key']
        
        # Fetch URL content with enhanced headers and retry logic
        print(f"Fetching content from {url} with enhanced headers...", flush=True)
        
        try:
            response = URLEnhancer.fetch_with_retry(url)
            
            # Check if JavaScript is required
            if URLEnhancer.is_javascript_required(response.text):
                print("JavaScript-rendered content detected. Using basic extraction but Level 3 integration recommended.", flush=True)
            
            # Extract text with enhanced extraction
            text, title, author = URLEnhancer.extract_text_enhanced(response.content, url)
            
            # Add metadata to the beginning of text if available
            metadata_parts = []
            if title:
                metadata_parts.append(f"Title: {title}")
            if author:
                metadata_parts.append(f"Author: {author}")
            if metadata_parts:
                text = '\n'.join(metadata_parts) + '\n\n' + text
                
        except Exception as e:
            # Check if it's a bot detection issue
            if "Cloudflare" in str(e) or "CAPTCHA" in str(e) or "Level 3" in str(e):
                return Response(
                    f"data: {json.dumps({'error': f'{str(e)} Please try a different URL or wait for Level 3 integration.'})}\n\n",
                    mimetype='text/event-stream'
                )
            raise
        
        if not text.strip():
            return Response(
                f"data: {json.dumps({'error': 'Could not extract text from URL'})}\n\n",
                mimetype='text/event-stream'
            )
        
        print(f"Extracted {len(text)} characters", flush=True)
        
        # Truncate if too long to prevent token limits
        if len(text) > 100000:  # Increased limit for Claude 4
            text = text[:100000] + "\n\n[Article continues but was truncated due to length...]"
            print("Text truncated to 100000 characters", flush=True)
        
    except requests.RequestException as e:
        import traceback
        print(f"Error fetching URL: {str(e)}", flush=True)
        print(f"Traceback: {traceback.format_exc()}", flush=True)
        return Response(
            f"data: {json.dumps({'error': f'Failed to fetch URL: {str(e)}'})}\n\n",
            mimetype='text/event-stream'
        )
    except Exception as e:
        import traceback
        print(f"Error processing request: {str(e)}", flush=True)
        print(f"Traceback: {traceback.format_exc()}", flush=True)
        return Response(
            f"data: {json.dumps({'error': str(e)})}\n\n",
            mimetype='text/event-stream'
        )
    
    # Generator function with all data captured
    def generate():
        try:
            # Convert to markdown using Claude with streaming
            client = anthropic.Anthropic(api_key=api_key)
            
            print("Starting Claude 3.5 Sonnet streaming response...", flush=True)
            
            stream = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=8192,  # Claude 4 supports up to 64K output tokens
                temperature=0,
                messages=[
                    {
                        "role": "user",
                        "content": f"""Convert the following article text to Markdown format.

IMPORTANT: This is a FORMAT CONVERSION, not a summary. Include EVERY sentence.

CRITICAL INSTRUCTIONS:
1. Fix OCR errors (e.g., "technolo y" -> "technology", "LLiisstteenn" -> "Listen")
2. Use proper Markdown formatting (# for main title, ## for sections, etc.)
3. Include ALL paragraphs and sentences - do not skip anything
4. Remove only obvious website UI elements (like "https://www.bloomberg.com/..." URLs)
5. Keep author names, dates, and all article content
6. DO NOT stop early or say "Content continues" - include the ENTIRE article
7. DO NOT be lazy - convert the COMPLETE text provided
8. If the text is long, that's fine - use all 8192 tokens if needed

Article text:

{text}"""
                    }
                ],
                stream=True
            )
            
            chunk_count = 0
            total_text = ""
            for event in stream:
                if event.type == "content_block_delta":
                    chunk_count += 1
                    text_chunk = event.delta.text
                    total_text += text_chunk
                    yield f"data: {json.dumps({'chunk': text_chunk})}\n\n"
                    if chunk_count % 50 == 0:
                        print(f"  Streamed {chunk_count} chunks, {len(total_text)} chars...", flush=True)
            
            print(f"Streaming complete: {chunk_count} chunks, {len(total_text)} chars", flush=True)
            yield f"data: {json.dumps({'done': True})}\n\n"
                    
        except Exception as e:
            import traceback
            print(f"Error in streaming: {str(e)}", flush=True)
            print(f"Traceback: {traceback.format_exc()}", flush=True)
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    # Flush stdout to ensure prints are visible in Electron
    sys.stdout.flush()
    print("\n🚀 Starting Document to Markdown Converter (Electron mode)", flush=True)
    print("📍 Server running on: http://localhost:3333", flush=True)
    print("   Electron app will connect to this server\n", flush=True)
    app.run(host='127.0.0.1', port=3333, debug=False)