# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

De-PDF is a document to markdown converter that uses Claude API to convert PDFs, HTML files, and web URLs into clean markdown format.

## Application Architecture

The application uses a Flask backend (`/app.py`) with:
- Web interface served from `/templates/index.html`
- JavaScript frontend in `/static/js/app.js`
- Electron wrapper for desktop app in `/electron-app/`
- Docker container support

## Key Features
- PDF, HTML, and DOCX file conversion
- URL to markdown conversion with Puppeteer support for JavaScript-rendered pages
- Reader mode for clean reading experience
- URL path ingestion:
  - Direct: `localhost:3333?url=https://example.com/article`
  - Path-based: `localhost:3333/https://example.com/article` (redirects to query param)