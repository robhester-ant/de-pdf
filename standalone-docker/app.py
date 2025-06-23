from flask import Flask, request, jsonify, send_file, render_template_string, send_from_directory, Response
import anthropic
import pdfplumber
from docx import Document
from bs4 import BeautifulSoup
import os
import json
import io
import base64

app = Flask(__name__, static_folder=None)
API_KEY_FILE = 'api_key.json'

# Serve static files (fonts)
@app.route('/assets/<path:path>')
def send_static(path):
    # In Docker, fonts are mounted at /app/font
    # Outside Docker, they're in the parent directory
    try:
        if os.path.exists('/app/font'):
            # Running in Docker
            file_path = os.path.join('/app', path)
            if os.path.exists(file_path):
                return send_file(file_path)
            else:
                return f"File not found: {file_path}", 404
        else:
            # Running locally
            parent_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
            file_path = os.path.join(parent_path, path)
            if os.path.exists(file_path):
                return send_file(file_path)
            else:
                return f"File not found: {file_path}", 404
    except Exception as e:
        return f"Error: {str(e)}", 500

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Document to Markdown Converter</title>
    <!-- Marked.js for Markdown to HTML conversion -->
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <style>
        /* Fallback to a similar monospace font since local font serving is having issues */
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400&display=swap');
        
        body {
            font-family: 'JetBrains Mono', monospace;
            background-color: #ffffff;
            margin: 0;
            padding: 20px;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            box-sizing: border-box;
        }
        .container {
            background-color: white;
            padding: 40px;
            width: 98%;
            max-width: 1400px;
            height: 90vh;
            max-height: 900px;
            display: flex;
            flex-direction: column;
            box-sizing: border-box;
        }
        @media (max-width: 768px) {
            body {
                padding: 10px;
            }
            .container {
                padding: 20px;
                width: 100%;
                height: auto;
                max-height: none;
            }
        }
        h1 {
            color: #2563eb;
            text-align: center;
            margin-bottom: 30px;
            font-weight: 500;
        }
        input[type="text"], input[type="password"] {
            width: 100%;
            padding: 12px;
            border: 1px solid #e5e7eb;
            font-size: 16px;
            box-sizing: border-box;
            font-family: 'JetBrains Mono', monospace;
        }
        input[type="text"]:focus, input[type="password"]:focus {
            outline: none;
            border-color: #2563eb;
        }
        button {
            background-color: #2563eb;
            color: white;
            border: none;
            padding: 12px 24px;
            font-size: 16px;
            cursor: pointer;
            width: 100%;
            margin-top: 20px;
            transition: background-color 0.2s;
            font-family: 'JetBrains Mono', monospace;
        }
        button:hover {
            background-color: #1d4ed8;
        }
        button:disabled {
            background-color: #9ca3af;
            cursor: not-allowed;
        }
        .reset-link {
            position: absolute;
            top: 20px;
            right: 20px;
            color: #2563eb;
            text-decoration: none;
            font-size: 14px;
        }
        .reset-link:hover {
            text-decoration: underline;
        }
        .upload-area {
            border: 2px dashed #e5e7eb;
            padding: 40px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
        }
        .upload-area:hover {
            border-color: #2563eb;
            background-color: #f0f9ff;
        }
        .upload-area.drag-over {
            border-color: #2563eb;
            background-color: #dbeafe;
        }
        .file-input {
            display: none;
        }
        .progress-bar {
            width: 100%;
            height: 8px;
            background-color: #e5e7eb;
            overflow: hidden;
            margin: 20px 0;
            display: none;
        }
        .progress-fill {
            height: 100%;
            background-color: #2563eb;
            width: 0%;
            transition: width 0.3s;
        }
        .button-group {
            display: flex;
            gap: 10px;
            margin-top: 20px;
        }
        .button-group button {
            flex: 1;
            margin-top: 0;
        }
        .success-message {
            color: #059669;
            text-align: center;
            margin-top: 20px;
            display: none;
        }
        .error-message {
            color: #dc2626;
            text-align: center;
            margin-top: 20px;
            display: none;
        }
        .markdown-display {
            width: 100%;
            height: 100%;
            min-height: 400px;
            padding: 12px;
            border: 1px solid #e5e7eb;
            font-size: 14px;
            overflow-y: auto;
            background-color: #fff;
            box-sizing: border-box;
            line-height: 1.6;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }
        .markdown-display:focus {
            outline: none;
            border-color: #2563eb;
        }
        .markdown-display h1 { font-size: 2em; margin: 0.67em 0; font-weight: bold; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
        .markdown-display h2 { font-size: 1.5em; margin: 0.75em 0; font-weight: bold; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
        .markdown-display h3 { font-size: 1.17em; margin: 0.83em 0; font-weight: bold; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
        .markdown-display h4 { font-size: 1em; margin: 1.12em 0; font-weight: bold; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
        .markdown-display h5 { font-size: 0.83em; margin: 1.5em 0; font-weight: bold; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
        .markdown-display h6 { font-size: 0.75em; margin: 1.67em 0; font-weight: bold; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
        .markdown-display p { margin: 1em 0; }
        .markdown-display blockquote { 
            margin: 1em 0; 
            padding-left: 1em; 
            border-left: 4px solid #e5e7eb; 
            color: #6b7280; 
        }
        .markdown-display code {
            background-color: #f3f4f6;
            padding: 2px 4px;
            font-family: monospace;
            font-size: 0.9em;
        }
        .markdown-display pre {
            background-color: #f3f4f6;
            padding: 12px;
            overflow-x: auto;
        }
        .markdown-display pre code {
            background-color: transparent;
            padding: 0;
        }
        .markdown-display ul, .markdown-display ol {
            margin: 1em 0;
            padding-left: 2em;
        }
        .markdown-display li {
            margin: 0.5em 0;
        }
        .markdown-display a {
            color: #2563eb;
            text-decoration: underline;
        }
        .markdown-display hr {
            border: none;
            border-top: 1px solid #e5e7eb;
            margin: 2em 0;
        }
        .markdown-display table {
            border-collapse: collapse;
            margin: 1em 0;
        }
        .markdown-display th, .markdown-display td {
            border: 1px solid #e5e7eb;
            padding: 8px;
        }
        .markdown-display th {
            background-color: #f3f4f6;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="container">
        <div id="api-key-section">
            <h1>Document to Markdown</h1>
            <p style="text-align: center; color: #6b7280; margin-bottom: 30px;">Enter your Claude API key to get started</p>
            <input type="password" id="api-key" placeholder="Enter your Claude API key" autocomplete="off">
            <button onclick="saveApiKey()">Submit</button>
        </div>
        
        <div id="upload-section" style="display: none; height: 100%; display: flex; flex-direction: column;">
            <a href="#" class="reset-link" onclick="resetApiKey()">Reset Key</a>
            <h1 style="margin-top: 0; font-family: 'JetBrains Mono', monospace;">De-PDF</h1>
            <div class="upload-area" id="upload-area" onclick="document.getElementById('file-input').click()">
                <p style="margin: 0; color: #6b7280;">Drop your file here or click to browse</p>
                <p style="margin: 10px 0 0 0; color: #9ca3af; font-size: 14px;">Supports PDF, HTML, and DOC files</p>
                <input type="file" id="file-input" class="file-input" accept=".pdf,.html,.htm,.doc,.docx" onchange="handleFileSelect(event)">
            </div>
            <div class="progress-bar" id="progress-bar" style="display: none;">
                <div class="progress-fill" id="progress-fill"></div>
            </div>
            <div id="conversion-container" style="display: none; flex: 1; flex-direction: column; min-height: 0;">
                <p id="status-text" style="margin: 20px 0 10px 0; color: #6b7280; font-size: 14px; display: none;">Extracting text from document...</p>
                <div class="progress-bar" id="conversion-progress" style="margin-bottom: 20px;">
                    <div class="progress-fill" id="conversion-progress-fill"></div>
                </div>
                <div id="conversion-output" class="markdown-display" contenteditable="false" style="display: none; flex: 1; min-height: 0;"></div>
            </div>
            <div class="button-group" id="result-buttons" style="display: none;">
                <button onclick="downloadMarkdown()">Download</button>
                <button onclick="copyPlaintext()">Copy Plaintext</button>
                <button onclick="copyMarkdown()">Copy Markdown</button>
                <button onclick="copyRichText()">Copy Rich Text</button>
            </div>
            <div class="success-message" id="success-message">Copied to clipboard!</div>
            <div class="error-message" id="error-message"></div>
        </div>
    </div>

    <script>
        let convertedMarkdown = '';
        let apiKey = '';

        // Check if API key exists on load
        window.onload = function() {
            fetch('/check-api-key')
                .then(response => response.json())
                .then(data => {
                    if (data.hasKey) {
                        apiKey = 'stored';
                        showUploadSection();
                    }
                });
        };

        function saveApiKey() {
            const key = document.getElementById('api-key').value;
            if (!key) {
                alert('Please enter an API key');
                return;
            }

            fetch('/save-api-key', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({key: key})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    apiKey = 'stored';
                    showUploadSection();
                }
            });
        }

        function showUploadSection() {
            document.getElementById('api-key-section').style.display = 'none';
            document.getElementById('upload-section').style.display = 'block';
        }

        function resetApiKey() {
            fetch('/reset-api-key', {method: 'POST'})
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        location.reload();
                    }
                });
        }

        // Drag and drop functionality
        const uploadArea = document.getElementById('upload-area');
        
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('drag-over');
        });

        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('drag-over');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('drag-over');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                handleFile(files[0]);
            }
        });

        function handleFileSelect(event) {
            const file = event.target.files[0];
            if (file) {
                handleFile(file);
            }
        }

        function handleFile(file) {
            const formData = new FormData();
            formData.append('file', file);

            // Show conversion container with progress
            document.getElementById('conversion-container').style.display = 'block';
            document.getElementById('conversion-output').style.display = 'none';
            document.getElementById('conversion-output').innerHTML = '';
            convertedMarkdown = ''; // Reset the stored markdown
            document.getElementById('result-buttons').style.display = 'none';
            document.getElementById('error-message').style.display = 'none';
            document.getElementById('status-text').style.display = 'block';
            document.getElementById('status-text').textContent = 'Extracting text from document...';
            document.getElementById('conversion-progress').style.display = 'block';
            document.getElementById('conversion-progress-fill').style.width = '20%';

            fetch('/convert-stream', {
                method: 'POST',
                body: formData
            })
            .then(response => {
                if (!response.ok) throw new Error('Conversion failed');
                
                document.getElementById('status-text').textContent = 'Cleaning up...';
                document.getElementById('conversion-progress').style.display = 'none';
                document.getElementById('conversion-output').style.display = 'block';
                
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let buffer = '';
                
                function processStream() {
                    reader.read().then(({ done, value }) => {
                        if (done) return;
                        
                        buffer += decoder.decode(value, { stream: true });
                        const lines = buffer.split('\\n');
                        buffer = lines.pop() || '';
                        
                        for (const line of lines) {
                            if (line.startsWith('data: ')) {
                                try {
                                    const data = JSON.parse(line.slice(6));
                                    if (data.chunk) {
                                        // Append the chunk to the markdown
                                        convertedMarkdown += data.chunk;
                                        // Convert markdown to HTML and display as rich text
                                        const html = marked.parse(convertedMarkdown);
                                        const output = document.getElementById('conversion-output');
                                        output.innerHTML = html;
                                        // Auto-scroll to bottom
                                        output.scrollTop = output.scrollHeight;
                                    } else if (data.done) {
                                        // Conversion complete
                                        document.getElementById('result-buttons').style.display = 'flex';
                                        document.getElementById('status-text').textContent = 'Conversion complete!';
                                        return;
                                    } else if (data.error) {
                                        throw new Error(data.error);
                                    }
                                } catch (e) {
                                    console.error('Parse error:', e);
                                }
                            }
                        }
                        
                        processStream();
                    }).catch(error => {
                        console.error('Stream error:', error);
                        throw error;
                    });
                }
                
                processStream();
            })
            .catch(error => {
                document.getElementById('conversion-container').style.display = 'none';
                document.getElementById('error-message').textContent = error.message;
                document.getElementById('error-message').style.display = 'block';
            });
        }

        function downloadMarkdown() {
            const blob = new Blob([convertedMarkdown], {type: 'text/markdown'});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'converted.md';
            a.click();
            URL.revokeObjectURL(url);
        }

        function copyPlaintext() {
            // Extract plain text from the rich text display
            const plaintext = document.getElementById('conversion-output').innerText;
            navigator.clipboard.writeText(plaintext).then(() => {
                showSuccessMessage('Plaintext copied to clipboard!');
            }).catch(err => {
                showError('Failed to copy: ' + err.message);
            });
        }

        function copyMarkdown() {
            navigator.clipboard.writeText(convertedMarkdown).then(() => {
                showSuccessMessage('Markdown copied to clipboard!');
            }).catch(err => {
                showError('Failed to copy: ' + err.message);
            });
        }

        async function copyRichText() {
            try {
                let html = document.getElementById('conversion-output').innerHTML;
                const plaintext = document.getElementById('conversion-output').innerText;
                
                // Convert HTML to be more Slack-compatible
                // Replace strong tags with b tags for better Slack compatibility
                html = html.replace(/<strong>/g, '<b>').replace(/<\/strong>/g, '</b>');
                
                // Ensure paragraphs have proper spacing
                html = html.replace(/<p>/g, '<p style="margin: 0 0 1em 0;">').replace(/<\/p>/g, '</p>');
                
                // Add line breaks BEFORE headers for Slack (not after)
                html = html.replace(/(<h[1-6]>)/g, '<br>$1');
                
                // Ensure list items have proper spacing
                html = html.replace(/<li>/g, '<li style="margin: 0.25em 0;">');
                
                // Also ensure double line break between paragraphs for Slack
                html = html.replace(/<\/p>\s*<p/g, '</p><br><p');
                
                // Create a more complete HTML document for better compatibility
                const fullHtml = `<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.5; }
b { font-weight: bold; }
i, em { font-style: italic; }
p { margin: 0 0 1em 0; }
h1, h2, h3, h4, h5, h6 { font-weight: bold; margin: 0.5em 0; }
ul, ol { margin: 0.5em 0; padding-left: 1.5em; }
li { margin: 0.25em 0; }
code { background-color: #f4f4f4; padding: 2px 4px; border-radius: 3px; font-family: monospace; }
pre { background-color: #f4f4f4; padding: 8px; border-radius: 4px; overflow-x: auto; margin: 1em 0; }
blockquote { border-left: 4px solid #ddd; margin: 0.5em 0; padding-left: 1em; color: #666; }
</style>
</head>
<body>${html}</body>
</html>`;
                
                // Try to write both HTML and plain text for maximum compatibility
                const htmlBlob = new Blob([fullHtml], { type: 'text/html' });
                const textBlob = new Blob([plaintext], { type: 'text/plain' });
                
                const clipboardItem = new ClipboardItem({
                    'text/html': htmlBlob,
                    'text/plain': textBlob
                });
                
                await navigator.clipboard.write([clipboardItem]);
                showSuccessMessage('Rich text copied to clipboard!');
            } catch (err) {
                // Fallback to plain text if rich text fails
                navigator.clipboard.writeText(document.getElementById('conversion-output').innerText).then(() => {
                    showSuccessMessage('Copied as plain text (rich text not supported)');
                }).catch(err2 => {
                    showError('Failed to copy: ' + err2.message);
                });
            }
        }

        function showSuccessMessage(message) {
            document.getElementById('success-message').textContent = message;
            document.getElementById('success-message').style.display = 'block';
            setTimeout(() => {
                document.getElementById('success-message').style.display = 'none';
                document.getElementById('success-message').textContent = 'Copied to clipboard!';
            }, 2000);
        }

        function showError(message) {
            document.getElementById('error-message').textContent = message;
            document.getElementById('error-message').style.display = 'block';
        }
    </script>
</body>
</html>
'''

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

def convert_to_markdown(text, api_key):
    """Convert text to markdown using Claude API"""
    client = anthropic.Anthropic(
        api_key=api_key,
    )
    
    # Truncate if needed
    if len(text) > 100000:  # Increased limit for Claude 4
        text = text[:100000] + "\n\n[Article continues but was truncated due to length...]"
    
    message = client.messages.create(
        model="claude-opus-4-20250514",
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
8. If the text is long, that's fine - use all 4000 tokens if needed

Article text:

{text}"""
            }
        ]
    )
    
    return message.content[0].text

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.route('/check-api-key')
def check_api_key():
    return jsonify({'hasKey': os.path.exists(API_KEY_FILE)})

@app.route('/save-api-key', methods=['POST'])
def save_api_key():
    data = request.get_json()
    api_key = data.get('key')
    
    with open(API_KEY_FILE, 'w') as f:
        json.dump({'key': api_key}, f)
    
    return jsonify({'success': True})

@app.route('/reset-api-key', methods=['POST'])
def reset_api_key():
    if os.path.exists(API_KEY_FILE):
        os.remove(API_KEY_FILE)
    return jsonify({'success': True})

@app.route('/convert', methods=['POST'])
def convert():
    try:
        # Get API key
        if not os.path.exists(API_KEY_FILE):
            return jsonify({'success': False, 'error': 'API key not configured'})
        
        with open(API_KEY_FILE, 'r') as f:
            api_key = json.load(f)['key']
        
        # Get uploaded file
        file = request.files.get('file')
        if not file:
            return jsonify({'success': False, 'error': 'No file uploaded'})
        
        file_content = file.read()
        filename = file.filename.lower()
        
        # Extract text based on file type
        if filename.endswith('.pdf'):
            text = extract_text_from_pdf(file_content)
        elif filename.endswith(('.doc', '.docx')):
            text = extract_text_from_docx(file_content)
        elif filename.endswith(('.html', '.htm')):
            text = extract_text_from_html(file_content)
        else:
            return jsonify({'success': False, 'error': 'Unsupported file type'})
        
        if not text.strip():
            return jsonify({'success': False, 'error': 'Could not extract text from file'})
        
        # Convert to markdown using Claude
        markdown = convert_to_markdown(text, api_key)
        
        return jsonify({'success': True, 'markdown': markdown})
        
    except Exception as e:
        import traceback
        print(f"Error in /convert: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': str(e)})

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
        print(f"Extracting text from {filename}...")
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
        
        print(f"Extracted {len(text)} characters")
        
        # Truncate if too long to prevent token limits
        if len(text) > 100000:  # Increased limit for Claude 4
            text = text[:100000] + "\n\n[Article continues but was truncated due to length...]"
            print("Text truncated to 100000 characters")
        
    except Exception as e:
        import traceback
        print(f"Error processing request: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return Response(
            f"data: {json.dumps({'error': str(e)})}\n\n",
            mimetype='text/event-stream'
        )
    
    # Generator function with all data captured
    def generate():
        try:
            # Convert to markdown using Claude with streaming
            client = anthropic.Anthropic(api_key=api_key)
            
            print("Starting Claude Opus 4 streaming response...")
            
            stream = client.messages.create(
                model="claude-opus-4-20250514",
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
8. If the text is long, that's fine - use all 4000 tokens if needed

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
                        print(f"  Streamed {chunk_count} chunks, {len(total_text)} chars...")
            
            print(f"Streaming complete: {chunk_count} chunks, {len(total_text)} chars")
            yield f"data: {json.dumps({'done': True})}\n\n"
                    
        except Exception as e:
            import traceback
            print(f"Error in streaming: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    print("\n🚀 Starting Document to Markdown Converter")
    print("📍 Server running on: http://localhost:3333")
    print("   Access the app at this URL in your browser\n")
    app.run(host='0.0.0.0', port=3333, debug=False)