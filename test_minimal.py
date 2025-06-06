#!/usr/bin/env python3
import anthropic
import json

# Load API key
with open('api_key.json', 'r') as f:
    api_key = json.load(f)['key']

# Test with minimal text
test_text = """5/19/25, 7:10 AM Anthropic CEO Amodei Steers $61 Billion AI Powerhouse - Bloomberg

Anthropic Is Trying to Win the AI Race Without Losing Its Soul

Dario Amodei has transformed himself from an academic into the CEO of a $61 billion startup.

By Shirin Ghaffary
May 19, 2025 at 6:00 AM EDT

Anthropic Chief Executive Officer Dario Amodei received a message on Slack one day in mid-February: Senior members of his company's safety team were concerned that, without the right safeguards, the artificial intelligence model they were about to release to the public could be used to help create bioweapons.

LLiisstteenn ttoo tthhee SSttoorryy

This startling revelation came at a time when pressure was already ratcheting up on Amodei."""

prompt = f"""{anthropic.HUMAN_PROMPT} Convert this text to Markdown format. Include ALL content, fix OCR errors (like "LLiisstteenn" should be "Listen"):

{test_text}

{anthropic.AI_PROMPT}"""

print("Testing Claude API...")
client = anthropic.Anthropic(api_key=api_key)

try:
    response = client.completions.create(
        model="claude-2.1",
        prompt=prompt,
        max_tokens_to_sample=1000,
        temperature=0
    )
    
    print("\nResponse:")
    print(response.completion)
    print(f"\nLength: {len(response.completion)} characters")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()