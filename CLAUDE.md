# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This directory currently contains:
- A PDF document: "Anthropic CEO Amodei Steers $61 Billion AI Powerhouse - Bloomberg.pdf"
- An image file: "style.png"

No code structure or development files are present at this time.

## Important: Two Versions of the Application
This project has TWO versions of the document converter that must be kept in sync:
1. **Standalone HTML version**: `/document-to-markdown.html` - A single-file HTML/JS application
2. **Docker/Electron version**: `/electron-app/index.html` and `/electron-app/renderer.js` - Used in the Docker container

**CRITICAL**: When making UI or functionality changes, you MUST update BOTH versions and explicitly confirm to the user that both have been updated.