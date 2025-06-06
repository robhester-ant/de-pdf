#!/bin/bash

echo "Building portable Document to Markdown converter..."

# Option 1: Build Electron app in Docker
if [ "$1" = "electron" ]; then
    echo "Building Electron app with Docker (this will take a while)..."
    cd electron-app
    ./build-with-docker.sh linux
    echo "Electron app built! Check electron-app/dist/"
    exit 0
fi

# Option 2: Use the standalone Docker version
echo "Setting up standalone Docker version..."
cd standalone-docker

# Build the Docker image
docker-compose build

echo "
✅ Build complete!

To run the Document to Markdown converter:

1. Start the app:
   cd standalone-docker
   docker-compose up -d

2. Open your browser to:
   http://localhost:3333

3. To stop:
   docker-compose down

The app will save your API key between restarts.
"