#!/usr/bin/env python3
import anthropic
import pdfplumber
import json
import os
import sys
from datetime import datetime

# Load API key from file
if not os.path.exists('api_key.json'):
    print("Error: api_key.json not found")
    sys.exit(1)

with open('api_key.json', 'r') as f:
    api_key = json.load(f)['key']

print(f"API Key loaded: {api_key[:10]}...")

# Extract text from the PDF
input_file = "input.pdf"
if not os.path.exists(input_file):
    print(f"Error: {input_file} not found")
    sys.exit(1)

print(f"Extracting text from {input_file}...")
text = ""
try:
    with pdfplumber.open(input_file) as pdf:
        for i, page in enumerate(pdf.pages):
            print(f"  Processing page {i+1}/{len(pdf.pages)}...")
            page_text = page.extract_text() or ""
            text += page_text + "\n"
    print(f"Extracted {len(text)} characters")
except Exception as e:
    print(f"Error extracting PDF: {e}")
    sys.exit(1)

# Truncate if too long
if len(text) > 15000:
    text = text[:15000] + "\n\n[Text truncated due to length...]"
    print("Text truncated to 15000 characters")

# Create prompt
prompt = f"""{anthropic.HUMAN_PROMPT} You are a document converter. Your ONLY job is to convert the given text to proper Markdown formatting.

CRITICAL RULES - YOU MUST FOLLOW THESE EXACTLY:
1. DO NOT SUMMARIZE - Include EVERY sentence from the article
2. DO NOT SHORTEN - Include ALL paragraphs in their entirety  
3. DO NOT PARAPHRASE - Use the EXACT words from the original text
4. DO NOT SKIP CONTENT - Include every detail, quote, and data point
5. DO NOT ADD COMMENTARY - Only format the existing text

Your task is to:
- Take the extracted article text below
- Convert it to clean Markdown format with proper headings
- Include 100% of the article content word-for-word
- Only remove obvious website navigation, ads, or footer text
- Think of this like Safari's "Reader Mode" - extract the full article

Article text to convert to Markdown:

{text}

{anthropic.AI_PROMPT}"""

# Try different approaches
print("\n=== Testing anthropic 0.7.0 streaming ===")

# Test 1: Check what happens with streaming
print("\nTest 1: Testing with stream=True parameter...")
try:
    client = anthropic.Anthropic(api_key=api_key)
    response = client.completions.create(
        model="claude-2.1",
        prompt=prompt,
        max_tokens_to_sample=4000,
        temperature=0,
        stream=True
    )
    
    print(f"Response type: {type(response)}")
    print(f"Response attributes: {[attr for attr in dir(response) if not attr.startswith('_')]}")
    
    # Try to iterate
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"output_{timestamp}.md"
    
    with open(output_file, 'w') as f:
        if hasattr(response, '__iter__'):
            print("Response is iterable, attempting to stream...")
            chunk_count = 0
            for chunk in response:
                chunk_count += 1
                print(f"  Chunk {chunk_count}: {type(chunk)}")
                if hasattr(chunk, 'completion'):
                    f.write(chunk.completion)
                    print(f"    Written: {len(chunk.completion)} chars")
                elif hasattr(chunk, 'text'):
                    f.write(chunk.text)
                    print(f"    Written: {len(chunk.text)} chars")
                else:
                    print(f"    Chunk attributes: {[attr for attr in dir(chunk) if not attr.startswith('_')]}")
        else:
            print("Response is not iterable")
            if hasattr(response, 'completion'):
                f.write(response.completion)
                print(f"Written complete response: {len(response.completion)} chars")
            
    print(f"\nOutput saved to: {output_file}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

# Test 2: Try without streaming
print("\n\nTest 2: Testing without stream parameter...")
try:
    client = anthropic.Anthropic(api_key=api_key)
    response = client.completions.create(
        model="claude-2.1",
        prompt=prompt,
        max_tokens_to_sample=4000,
        temperature=0
    )
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"output_nostream_{timestamp}.md"
    
    with open(output_file, 'w') as f:
        f.write(response.completion)
    
    print(f"Non-streaming output saved to: {output_file}")
    print(f"Response length: {len(response.completion)} characters")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()