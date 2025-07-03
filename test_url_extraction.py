#!/usr/bin/env python3
"""Test script to debug URL extraction issues"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from url_enhancer import URLEnhancer
from puppeteer_handler import PuppeteerHandler
import requests

def test_url(url):
    print(f"\n=== Testing URL: {url} ===\n")
    
    # Test Level 2 (Enhanced HTTP)
    print("--- Level 2: Enhanced HTTP Request ---")
    try:
        response = URLEnhancer.fetch_with_retry(url, max_retries=2)
        print(f"Status Code: {response.status_code}")
        print(f"Content Length: {len(response.content)}")
        print(f"Content Type: {response.headers.get('Content-Type', 'Unknown')}")
        
        # Check if JavaScript is required
        if URLEnhancer.is_javascript_required(response.text):
            print("JavaScript appears to be required for this page")
        
        # Extract text
        text, title, author = URLEnhancer.extract_text_enhanced(response.text, url)
        print(f"\nExtracted Title: {title}")
        print(f"Extracted Author: {author}")
        print(f"Extracted Text Length: {len(text)}")
        
        # Show first 500 chars of extracted text
        print(f"\nFirst 500 chars of extracted text:")
        print("-" * 50)
        print(text[:500])
        print("-" * 50)
        
        # Check for encoding issues
        print(f"\nChecking for encoding issues...")
        # Count non-ASCII characters
        non_ascii_count = sum(1 for char in text if ord(char) > 127)
        print(f"Non-ASCII characters: {non_ascii_count}")
        
        # Check if text is mostly gibberish
        if non_ascii_count > len(text) * 0.5:
            print("WARNING: Text appears to be mostly non-ASCII characters!")
            
        # Save raw HTML for inspection
        with open('debug_raw_html.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print("\nRaw HTML saved to debug_raw_html.html")
        
    except Exception as e:
        print(f"Level 2 Failed: {str(e)}")
        
        # Test Level 3 (Puppeteer)
        print("\n--- Level 3: Puppeteer/JavaScript Rendering ---")
        try:
            puppeteer = PuppeteerHandler()
            js_content = puppeteer.fetch_with_js_sync(url)
            
            print(f"Puppeteer Content Length: {len(js_content)}")
            
            # Extract text from JS-rendered content
            text, title, author = URLEnhancer.extract_text_enhanced(js_content, url)
            print(f"\nPuppeteer Extracted Title: {title}")
            print(f"Puppeteer Extracted Text Length: {len(text)}")
            
            # Show first 500 chars
            print(f"\nFirst 500 chars of Puppeteer-extracted text:")
            print("-" * 50)
            print(text[:500])
            print("-" * 50)
            
            # Save Puppeteer HTML
            with open('debug_puppeteer_html.html', 'w', encoding='utf-8') as f:
                f.write(js_content)
            print("\nPuppeteer HTML saved to debug_puppeteer_html.html")
            
        except Exception as e:
            print(f"Level 3 Failed: {str(e)}")

if __name__ == "__main__":
    test_url("https://analyticsindiamag.com/ai-features/cloudflare-just-became-an-enemy-of-all-ai-companies/")