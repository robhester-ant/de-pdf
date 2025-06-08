"""
URL Enhancement Module for De-PDF
Implements Level 2 enhancements based on crawler techniques
"""
import random
import time
from urllib.parse import urlparse
from typing import Dict, Optional, Tuple
import requests
from bs4 import BeautifulSoup


class URLEnhancer:
    """Handles enhanced URL fetching with bot detection avoidance"""
    
    # User agents for different scenarios
    USER_AGENTS = {
        'chrome_mac': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'chrome_windows': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'safari': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15',
        'firefox': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
        'bot': 'De-PDF Bot/1.0 (+https://github.com/de-pdf; contact@de-pdf.com)'
    }
    
    # Domain-specific configurations
    DOMAIN_CONFIG = {
        'anthropic.com': {
            'user_agent': 'bot',  # Some sites prefer honest bots
            'extra_headers': {
                'Sec-CH-UA': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
                'Sec-CH-UA-Mobile': '?0',
                'Sec-CH-UA-Platform': '"macOS"',
            }
        },
        'bloomberg.com': {
            'user_agent': 'chrome_mac',
            'delay': 2.0  # Seconds to wait after request
        },
        'nytimes.com': {
            'user_agent': 'chrome_windows',
            'delay': 1.5
        }
    }
    
    # Default headers to appear more browser-like
    DEFAULT_HEADERS = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
    }
    
    @classmethod
    def get_enhanced_headers(cls, url: str) -> Dict[str, str]:
        """Get optimized headers for a given URL"""
        domain = urlparse(url).netloc.lower()
        headers = cls.DEFAULT_HEADERS.copy()
        
        # Check for domain-specific configuration
        config = None
        for key in cls.DOMAIN_CONFIG:
            if key in domain:
                config = cls.DOMAIN_CONFIG[key]
                break
        
        if not config:
            # Use random browser user agent for unknown domains
            config = {
                'user_agent': random.choice(['chrome_mac', 'chrome_windows', 'safari', 'firefox'])
            }
        
        # Set user agent
        headers['User-Agent'] = cls.USER_AGENTS[config['user_agent']]
        
        # Add any extra headers
        if 'extra_headers' in config:
            headers.update(config['extra_headers'])
        
        # Add referer for better authenticity
        headers['Referer'] = f"https://{domain}/"
        
        return headers, config.get('delay', 0)
    
    @classmethod
    def fetch_with_retry(cls, url: str, max_retries: int = 3, timeout: int = 30) -> requests.Response:
        """Fetch URL with retry logic and exponential backoff"""
        headers, delay = cls.get_enhanced_headers(url)
        
        for attempt in range(max_retries):
            try:
                # Add session for cookie handling
                session = requests.Session()
                response = session.get(url, headers=headers, timeout=timeout, allow_redirects=True)
                
                # Check for common bot detection responses
                if response.status_code == 403:
                    if 'cloudflare' in response.text.lower() or 'cf-ray' in response.headers:
                        raise Exception("Cloudflare protection detected. Level 3 integration required.")
                    elif 'captcha' in response.text.lower():
                        raise Exception("CAPTCHA detected. Level 3 integration required.")
                
                response.raise_for_status()
                
                # Apply domain-specific delay
                if delay > 0:
                    time.sleep(delay)
                
                return response
                
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + random.uniform(0, 1)  # Exponential backoff with jitter
                    print(f"Timeout on attempt {attempt + 1}, retrying in {wait_time:.1f}s...")
                    time.sleep(wait_time)
                else:
                    raise
            
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    print(f"Request failed on attempt {attempt + 1}: {str(e)}, retrying in {wait_time:.1f}s...")
                    time.sleep(wait_time)
                else:
                    raise
    
    @classmethod
    def extract_text_enhanced(cls, html_content: str, url: str) -> Tuple[str, Optional[str], Optional[str]]:
        """Enhanced text extraction with metadata"""
        soup = BeautifulSoup(html_content, 'lxml')
        
        # Remove script, style, and other non-content elements
        for element in soup(['script', 'style', 'noscript', 'header', 'footer', 'nav', 'aside', 'form']):
            element.decompose()
        
        # Try to extract title
        title = None
        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.get_text(strip=True)
        
        # Try to extract author
        author = None
        author_meta = soup.find('meta', attrs={'name': 'author'}) or soup.find('meta', attrs={'property': 'article:author'})
        if author_meta:
            author = author_meta.get('content')
        
        # Try to find main content using various selectors
        content_selectors = [
            'article',
            'main',
            '[role="main"]',
            '.article-content',
            '.post-content',
            '.entry-content',
            '.content',
            '#content',
            '.story-body',
            '.article-body'
        ]
        
        main_content = None
        for selector in content_selectors:
            main_content = soup.select_one(selector)
            if main_content:
                break
        
        # If no main content found, try to identify by text density
        if not main_content:
            # Find the element with the most text
            max_text_length = 0
            for element in soup.find_all(['div', 'section']):
                text_length = len(element.get_text(strip=True))
                if text_length > max_text_length:
                    max_text_length = text_length
                    main_content = element
        
        # Extract text from main content or full body
        if main_content:
            text = main_content.get_text(separator='\n', strip=True)
        else:
            text = soup.get_text(separator='\n', strip=True)
        
        # Clean up text - remove multiple newlines and spaces
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        text = '\n'.join(lines)
        
        return text, title, author
    
    @classmethod
    def is_javascript_required(cls, html_content: str) -> bool:
        """Detect if page requires JavaScript"""
        indicators = [
            'please enable javascript',
            'javascript is required',
            'this site requires javascript',
            'noscript',
            '__NEXT_DATA__',  # Next.js
            '__NUXT__',       # Nuxt.js
            'window.React',   # React apps
            'ng-app',         # Angular
        ]
        
        lower_content = html_content.lower()
        return any(indicator in lower_content for indicator in indicators)