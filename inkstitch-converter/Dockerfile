# Use Ubuntu as base image
FROM ubuntu:22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV DISPLAY=:99
ENV PORT=5000

# Install system dependencies - simplified approach
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    xvfb \
    wget \
    curl \
    git \
    unzip \
    libxml2-dev \
    libxslt-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip3 install --no-cache-dir \
    lxml \
    numpy \
    Pillow \
    shapely \
    networkx \
    flask \
    requests \
    gunicorn \
    pyembroidery

# Copy our conversion scripts
COPY inkstitch-converter/convert.py /opt/convert.py
COPY inkstitch-converter/server.py /opt/server.py

# Set working directory
WORKDIR /opt

# Make scripts executable
RUN chmod +x convert.py server.py

# Expose port for API
EXPOSE $PORT

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:$PORT/health || exit 1

# Start the conversion server with gunicorn for production
CMD gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 server:app 