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

# Save the raw extracted text for debugging
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
raw_file = f"raw_extracted_{timestamp}.txt"
with open(raw_file, 'w') as f:
    f.write(text)
print(f"Raw extracted text saved to: {raw_file}")

# Try different text lengths
test_lengths = [30000, 25000, 20000]  # Increased limits

for max_length in test_lengths:
    print(f"\n=== Testing with {max_length} character limit ===")
    
    # Truncate text
    truncated_text = text
    if len(text) > max_length:
        truncated_text = text[:max_length]
        print(f"Text truncated from {len(text)} to {len(truncated_text)} characters")
    
    # Create a more direct prompt
    prompt = f"""{anthropic.HUMAN_PROMPT} Convert the following extracted PDF text to Markdown format.

IMPORTANT: 
- DO NOT SUMMARIZE - include ALL content
- Fix any OCR errors (like "LLiisstteenn" -> "Listen")
- Format with proper Markdown headings and structure
- Include EVERY paragraph and sentence from the source
- This should be a complete, word-for-word conversion

Text to convert:

{truncated_text}

{anthropic.AI_PROMPT}"""
    
    try:
        client = anthropic.Anthropic(api_key=api_key)
        
        # Non-streaming first to see full response
        print(f"Requesting conversion (non-streaming)...")
        response = client.completions.create(
            model="claude-2.1",
            prompt=prompt,
            max_tokens_to_sample=4000,
            temperature=0
        )
        
        output_file = f"output_full_{max_length}_{timestamp}.md"
        with open(output_file, 'w') as f:
            f.write(response.completion)
        
        print(f"Output saved to: {output_file}")
        print(f"Response length: {len(response.completion)} characters")
        
        # Check if response seems complete
        if response.completion.strip().endswith(("...", "truncated", "]")):
            print("WARNING: Response appears truncated!")
        
        # Count approximate words
        word_count = len(response.completion.split())
        print(f"Approximate word count: {word_count}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

# Also test with a specific page range
print("\n=== Testing with just first 3 pages ===")
try:
    partial_text = ""
    with pdfplumber.open(input_file) as pdf:
        for i in range(min(3, len(pdf.pages))):
            page_text = pdf.pages[i].extract_text() or ""
            partial_text += page_text + "\n"
    
    print(f"Extracted {len(partial_text)} characters from first 3 pages")
    
    prompt = f"""{anthropic.HUMAN_PROMPT} Convert this article text to proper Markdown format. Include ALL content - do not summarize:

{partial_text}

{anthropic.AI_PROMPT}"""
    
    response = client.completions.create(
        model="claude-2.1",
        prompt=prompt,
        max_tokens_to_sample=4000,
        temperature=0
    )
    
    output_file = f"output_3pages_{timestamp}.md"
    with open(output_file, 'w') as f:
        f.write(response.completion)
    
    print(f"3-page output saved to: {output_file}")
    print(f"Response length: {len(response.completion)} characters")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()