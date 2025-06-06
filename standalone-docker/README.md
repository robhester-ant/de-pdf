# Document to Markdown Converter - Standalone Docker Version

A simple, self-contained Docker application that converts PDFs, HTML, and DOC files to Markdown using Claude 4 Sonnet.

## Quick Start

1. Start the application:
```bash
docker-compose up -d
```

2. Open your browser to: http://localhost:3333

3. Enter your Claude API key (saved in Docker volume)

4. Upload files and convert!

## Features

- Same features as the main app
- API key persists across restarts (stored in Docker volume)
- No local installation required
- Completely self-contained

## Stop the Application

```bash
docker-compose down
```

## Reset API Key

To reset the stored API key:
```bash
docker-compose down -v  # This removes the volume
docker-compose up -d    # Start fresh
```

## Build and Run Without Compose

```bash
# Build
docker build -t doc-to-markdown .

# Run with persistent storage
docker run -d \
  -p 3333:3333 \
  -v doc-to-markdown-data:/data \
  --name doc-converter \
  doc-to-markdown
```