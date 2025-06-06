#!/usr/bin/env python3
import anthropic
import pdfplumber
import json
import os
import sys
from datetime import datetime

# Load API key
with open('api_key.json', 'r') as f:
    api_key = json.load(f)['key']

# Extract text from first 5 pages only for testing
text = ""
with pdfplumber.open("input.pdf") as pdf:
    for i in range(min(5, len(pdf.pages))):
        print(f"Extracting page {i+1}...")
        page_text = pdf.pages[i].extract_text() or ""
        text += page_text + "\n\n"

print(f"Extracted {len(text)} characters from first 5 pages")

# Save raw text
with open("first_5_pages_raw.txt", 'w') as f:
    f.write(text)

# Create a very explicit prompt
prompt = f"""{anthropic.HUMAN_PROMPT} I need you to convert the following article text to clean Markdown format.

CRITICAL REQUIREMENTS:
1. Include EVERY SINGLE SENTENCE from the source text
2. Do NOT summarize or shorten anything
3. Fix obvious OCR errors (like "technolo y" -> "technology", "LLiisstteenn" -> "Listen")
4. Format with Markdown headings (#, ##, ###)
5. Keep all paragraphs intact
6. This is NOT a summary - it's a FORMAT CONVERSION only

The text below is from a Bloomberg article about Anthropic. Convert it to clean Markdown:

{text}

{anthropic.AI_PROMPT} I'll convert this article to Markdown format, including every sentence and fixing OCR errors:

# """

client = anthropic.Anthropic(api_key=api_key)

# Test 1: Regular completion
print("\nTest 1: Regular completion...")
response = client.completions.create(
    model="claude-2.1",
    prompt=prompt,
    max_tokens_to_sample=4000,
    temperature=0
)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
with open(f"test_regular_{timestamp}.md", 'w') as f:
    f.write(response.completion)

print(f"Regular output length: {len(response.completion)} chars")
print("First 500 chars:")
print(response.completion[:500])
print("\nLast 500 chars:")
print(response.completion[-500:])

# Test 2: Streaming
print("\n\nTest 2: Streaming completion...")
response_stream = client.completions.create(
    model="claude-2.1",
    prompt=prompt,
    max_tokens_to_sample=4000,
    temperature=0,
    stream=True
)

full_response = ""
chunk_count = 0
with open(f"test_streaming_{timestamp}.md", 'w') as f:
    for chunk in response_stream:
        if hasattr(chunk, 'completion'):
            full_response += chunk.completion
            f.write(chunk.completion)
            chunk_count += 1
            if chunk_count % 100 == 0:
                print(f"  Received {chunk_count} chunks, {len(full_response)} chars total...")

print(f"Streaming output length: {len(full_response)} chars")
print(f"Total chunks: {chunk_count}")

# Compare
print("\n\nComparison:")
print(f"Regular length: {len(response.completion)}")
print(f"Streaming length: {len(full_response)}")
if response.completion == full_response:
    print("✓ Regular and streaming outputs match!")
else:
    print("✗ Outputs differ!")