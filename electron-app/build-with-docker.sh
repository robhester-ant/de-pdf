#!/bin/bash

# Build script using Docker

echo "Building Document to Markdown Electron app with Docker..."

# Create dist directory
mkdir -p dist

# Build for different platforms
case "$1" in
  "mac")
    echo "Building for macOS..."
    BUILD_TARGET=mac docker-compose -f docker-compose.build.yml up --build
    ;;
  "win")
    echo "Building for Windows..."
    BUILD_TARGET=win docker-compose -f docker-compose.build.yml up --build
    ;;
  "linux")
    echo "Building for Linux..."
    BUILD_TARGET=linux docker-compose -f docker-compose.build.yml up --build
    ;;
  *)
    echo "Building for Linux (default)..."
    BUILD_TARGET=linux docker-compose -f docker-compose.build.yml up --build
    ;;
esac

# Clean up
docker-compose -f docker-compose.build.yml down

echo "Build complete! Check the dist/ folder for the built application."