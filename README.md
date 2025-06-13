# De-PDF - Document to Markdown Converter

A powerful tool to convert PDF, HTML, and DOCX documents to clean Markdown format using Claude AI.

## Features

- **Multiple Input Formats**: Supports PDF, HTML, and DOCX files
- **AI-Powered Conversion**: Uses Claude 4 Sonnet for intelligent text cleanup and formatting
- **Rich Text Preview**: Real-time preview of converted content during processing
- **Multiple Copy Options**: Copy as plaintext, markdown, or rich text (Slack-compatible)
- **Multiple Deployment Options**: Run as standalone web app, Electron desktop app, or Docker container
- **URL Path Ingestion**: Convert URLs directly by visiting `localhost:3333/https://example.com/article`
- **Reader Mode**: Clean, distraction-free reading view in a popup window

## Quick Start

### Option 1: Run with Docker (Recommended)
```bash
docker-compose up
```
Then open http://localhost:3333 in your browser.

### Option 2: Run Standalone
```bash
pip install -r requirements.txt
python app.py
```

### Option 3: Run as Electron App
```bash
cd electron-app
npm install
npm start
```

## Setup

1. Get a Claude API key from [Anthropic](https://console.anthropic.com/)
2. Run the application using one of the methods above
3. Enter your API key when prompted (stored locally)
4. Upload a document and wait for the conversion

## Project Structure

- `app.py` - Main Flask application
- `templates/` - HTML templates for web interface
- `static/` - CSS and JavaScript files
- `electron-app/` - Electron desktop application
- `standalone-docker/` - Dockerized version with all dependencies

## Requirements

- Python 3.11+
- Flask
- Anthropic Claude API access
- Docker (for containerized deployment)
- Node.js (for Electron app)

## API Key Security

Your API key is stored locally and never transmitted except to Anthropic's API. For production use, consider using environment variables or a secrets management system.

## License

[Add your license here]