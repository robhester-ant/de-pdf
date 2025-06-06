# Standalone Docker image with embedded Python and web interface
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app.py .
COPY run.sh .

# Make run script executable
RUN chmod +x run.sh

# Expose port
EXPOSE 3333

# Set environment variable for data persistence
ENV ELECTRON_DATA_DIR=/data

# Create data volume
VOLUME ["/data"]

# Run the application
CMD ["./run.sh"]