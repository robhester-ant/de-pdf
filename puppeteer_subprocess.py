#!/usr/bin/env python3
"""
Subprocess wrapper for Puppeteer to avoid asyncio threading issues
"""
import sys
import json
import asyncio
from pyppeteer import launch
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def fetch_with_js(url: str):
    """
    Fetch and render a JavaScript-heavy page
    Returns: JSON with html_content, text_content, title, author
    """
    browser = None
    try:
        logger.info(f"Launching headless Chromium for {url}")
        
        # Launch browser with proper args for Docker container
        browser = await launch({
            'headless': True,
            'executablePath': '/usr/lib/chromium/chromium',
            'args': [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--no-first-run',
                '--no-zygote',
                '--single-process',  # Required for Docker
                '--disable-extensions'
            ]
        })
        
        page = await browser.newPage()
        
        # Set user agent based on domain
        if 'archive.ph' in url or 'archive.is' in url:
            await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0')
            # Set viewport to appear more real
            await page.setViewport({'width': 1366, 'height': 768})
            
            # Add extra headers for archive sites
            await page.setExtraHTTPHeaders({
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0',
            })
        else:
            await page.setUserAgent('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
            await page.setViewport({'width': 1920, 'height': 1080})
        
        logger.info(f"Navigating to {url}")
        
        # Navigate with increased timeout for slow sites
        await page.goto(url, {
            'waitUntil': ['networkidle2', 'domcontentloaded'],
            'timeout': 60000  # 60 seconds
        })
        
        # Wait a bit for dynamic content to load
        await page.waitFor(2000)
        
        # For archive.ph, wait for specific content
        if 'archive.ph' in url or 'archive.is' in url:
            try:
                # Wait for the main content div
                await page.waitForSelector('div#CONTENT', {'timeout': 10000})
            except:
                logger.warning("Could not find archive.ph content div, continuing anyway")
        
        # Get the page content
        html_content = await page.content()
        
        # Extract text content using page evaluation
        text_content = await page.evaluate('''() => {
            // Remove scripts, styles, and other non-content elements
            const elementsToRemove = document.querySelectorAll('script, style, noscript, iframe, object, embed, form, button, input, select, textarea');
            elementsToRemove.forEach(el => el.remove());
            
            // Try to find main content
            let contentElement = document.querySelector('article, main, [role="main"], .article-content, .post-content, .entry-content, .content, #content, .story-body, #CONTENT');
            
            if (!contentElement) {
                // For archive.ph specifically
                contentElement = document.querySelector('div#CONTENT') || document.querySelector('div.CONTENT');
            }
            
            if (!contentElement) {
                contentElement = document.body;
            }
            
            return contentElement.innerText || contentElement.textContent || '';
        }''')
        
        # Extract title
        title = await page.evaluate('() => document.title')
        
        # Try to extract author
        author = await page.evaluate('''() => {
            const authorMeta = document.querySelector('meta[name="author"]') || 
                              document.querySelector('meta[property="article:author"]') ||
                              document.querySelector('[itemprop="author"]') ||
                              document.querySelector('.author, .by-author, .byline');
            return authorMeta ? (authorMeta.content || authorMeta.innerText || authorMeta.textContent) : null;
        }''')
        
        logger.info(f"Successfully extracted {len(text_content)} characters from {url}")
        
        return {
            'success': True,
            'html': html_content,
            'text': text_content,
            'title': title,
            'author': author
        }
        
    except Exception as e:
        logger.error(f"Puppeteer error for {url}: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        if browser:
            await browser.close()


async def main():
    if len(sys.argv) != 2:
        print(json.dumps({'success': False, 'error': 'URL argument required'}))
        sys.exit(1)
    
    url = sys.argv[1]
    result = await fetch_with_js(url)
    print(json.dumps(result))


if __name__ == '__main__':
    asyncio.run(main())