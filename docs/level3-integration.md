# Level 3 Integration Guide: Full Puppeteer-Based Web Crawling

## Overview

This guide describes how to integrate the full Puppeteer-based crawler from the terms-watch project as a microservice for De-PDF. Level 3 provides advanced capabilities for handling JavaScript-rendered content and sites with sophisticated bot protection.

## When to Use Level 3

Level 3 integration is recommended when:
- Websites require JavaScript rendering (React, Vue, Angular apps)
- Sites have Cloudflare or similar bot protection
- CAPTCHA challenges are encountered
- Dynamic content loading is needed
- Level 2 enhancements fail to extract content

## Architecture

```
User Input URL
    ↓
De-PDF Frontend
    ↓
Python Backend (Level 2 attempt)
    ↓ (if fails)
Crawler Microservice (Level 3)
    ↓
Text Extraction
    ↓
Claude API (Markdown conversion)
```

## Implementation Steps

### 1. Copy Crawler Service

```bash
# From de-pdf directory
cp -r /path/to/terms-watch/1-crawler ./crawler-service

# Update package.json name and description
cd crawler-service
# Edit package.json to rename project
```

### 2. Create Crawler API Endpoint

Add a new endpoint to `crawler-service/src/server.ts`:

```typescript
app.post('/api/extract', async (req: Request, res: Response) => {
  const { url } = req.body;
  
  if (!url) {
    return res.status(400).json({ error: 'URL required' });
  }

  try {
    const crawler = container.resolve(CrawlerService);
    const browser = await puppeteer.launch({
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    
    const page = await browser.newPage();
    
    // Apply bot detection avoidance
    if (url.includes('anthropic.com')) {
      await page.setUserAgent(config.USER_AGENT);
      await page.setExtraHTTPHeaders({
        'Sec-CH-UA': '"Chromium";v="135", "Not-A.Brand";v="24"',
        'Sec-CH-UA-Mobile': '?0',
        'Sec-CH-UA-Platform': '"Linux"',
      });
    }
    
    await page.goto(url, { 
      waitUntil: 'networkidle2',
      timeout: 30000 
    });
    
    // Wait for dynamic content
    await page.waitForTimeout(2000);
    
    // Get page content
    const content = await page.content();
    const text = await page.evaluate(() => document.body.innerText);
    
    await browser.close();
    
    res.json({ 
      success: true, 
      text,
      html: content,
      metadata: {
        title: await page.title(),
        url: page.url()
      }
    });
    
  } catch (error) {
    res.status(500).json({ 
      error: 'Failed to extract content', 
      details: error.message 
    });
  }
});
```

### 3. Update Python Backend

Modify `electron-app/python-server/app.py` to fallback to crawler:

```python
# In convert-url-stream endpoint, after Level 2 attempt fails:

if "Level 3" in str(e) or "JavaScript" in str(e):
    try:
        # Fallback to crawler microservice
        crawler_response = requests.post(
            'http://crawler:3334/api/extract',
            json={'url': url},
            timeout=60
        )
        crawler_data = crawler_response.json()
        
        if crawler_data.get('success'):
            text = crawler_data['text']
            title = crawler_data.get('metadata', {}).get('title')
            # Continue with normal processing
        else:
            raise Exception(crawler_data.get('error', 'Crawler failed'))
    except Exception as crawler_error:
        return Response(
            f"data: {json.dumps({'error': f'Level 3 crawler failed: {str(crawler_error)}'})}\n\n",
            mimetype='text/event-stream'
        )
```

### 4. Docker Configuration

The `docker-compose.yml` is already prepared. To enable Level 3:

```bash
# Start with crawler service
docker-compose --profile with-crawler up

# Or just the main service (Level 2 only)
docker-compose up
```

### 5. Crawler Service Dockerfile

Create `crawler-service/Dockerfile`:

```dockerfile
FROM node:20-alpine

# Install Chromium and dependencies
RUN apk add --no-cache \
    chromium \
    nss \
    freetype \
    freetype-dev \
    harfbuzz \
    ca-certificates \
    ttf-freefont

# Tell Puppeteer to use installed Chromium
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true \
    PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium-browser

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci --only=production

# Copy application files
COPY . .

# Build TypeScript
RUN npm run build

EXPOSE 3334

CMD ["npm", "start"]
```

## Configuration

### Environment Variables

Add to `.env` file:
```
# Crawler Configuration
CRAWLER_ENABLED=false  # Set to true to enable Level 3
CRAWLER_URL=http://crawler:3334
CRAWLER_TIMEOUT=60
```

### Domain-Specific Rules

The crawler already includes domain-specific handling for:
- `anthropic.com` - Special TLS fingerprinting
- Sites requiring specific user agents
- Rate limiting per domain

Add new rules in `crawler-service/src/config/crawler-config.ts`.

## Testing Level 3

1. Start services with crawler:
   ```bash
   docker-compose --profile with-crawler up
   ```

2. Test with JavaScript-heavy site:
   ```
   https://example-spa.com/article
   ```

3. Monitor logs:
   ```bash
   docker-compose logs -f crawler
   ```

## Performance Considerations

- **Resource Usage**: Puppeteer uses ~100-200MB RAM per browser instance
- **Latency**: Adds 2-5 seconds vs Level 2
- **Scaling**: Consider connection pooling for high volume
- **Caching**: Implement Redis cache for repeated URLs

## Troubleshooting

### Common Issues

1. **Chromium crashes**
   - Increase Docker memory limit
   - Add `--disable-dev-shm-usage` flag

2. **Timeout errors**
   - Increase page timeout
   - Add retry logic
   - Check if site needs specific viewport

3. **Bot detection still failing**
   - Implement residential proxy support
   - Add mouse movement simulation
   - Use puppeteer-extra-plugin-stealth

## Future Enhancements

1. **Connection Pool**: Reuse browser instances
2. **Queue System**: Handle multiple requests efficiently  
3. **Proxy Support**: Rotate IPs for better success
4. **Screenshot Capture**: For debugging failed extractions
5. **Cookie Persistence**: Handle login-required content

## Rollback

To disable Level 3 and use only Level 2:

1. Stop crawler container:
   ```bash
   docker-compose stop crawler
   ```

2. Or restart without profile:
   ```bash
   docker-compose up
   ```

Level 2 will continue working independently.