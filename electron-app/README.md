# Document to Markdown Converter - Electron App

A desktop application that converts PDFs, HTML, and DOC files to Markdown using Claude 4 Sonnet.

## Features

- Convert PDF, HTML, and DOC/DOCX files to Markdown
- Uses Claude 4 Sonnet for accurate, word-for-word conversion
- Real-time streaming output
- Save API key locally
- Download or copy converted Markdown
- No Docker required - runs as a native desktop app

## Development

### Prerequisites

- Node.js 18+ and npm
- Python 3.8+ with pip

### Setup

1. Install Node dependencies:
```bash
npm install
```

2. Install Python dependencies:
```bash
cd python-server
pip install -r requirements.txt
cd ..
```

3. Run the app in development mode:
```bash
npm start
```

### Building

To build for your current platform:
```bash
npm run build-mac    # For macOS
npm run build-win    # For Windows  
npm run build-linux  # For Linux
```

The built app will be in the `dist` folder.

## Usage

1. Launch the app
2. Enter your Claude API key (saved locally)
3. Upload a PDF, HTML, or DOC file
4. Watch the real-time conversion
5. Download or copy the converted Markdown

## Architecture

- **Electron Main Process**: Manages app lifecycle and Python subprocess
- **Python Backend**: Flask server handling file processing and Claude API calls
- **Renderer Process**: Web-based UI for file upload and display

The app bundles a Python server that runs locally on port 3333.

## Notes

- API keys are stored locally in the app's user data directory
- The Python server is spawned as a subprocess and managed by Electron
- All processing happens locally - files are not uploaded to any external service