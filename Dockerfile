FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including Chromium
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Set up Chromium environment variables
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true \
    PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app.py url_enhancer.py puppeteer_handler.py puppeteer_subprocess.py ./
COPY static ./static
COPY templates ./templates

# Expose port
EXPOSE 3333

# Run the application
CMD ["python", "app.py"]