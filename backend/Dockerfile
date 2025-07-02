FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    # Dependencies for PyMuPDF
    libmupdf-dev \
    mupdf \
    mupdf-tools \
    python3-dev \
    pkg-config \
    libfreetype6-dev \
    libharfbuzz-dev \
    libfribidi-dev \
    libjpeg-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install PyTorch separately first with increased timeout
RUN pip install --no-cache-dir --timeout 600 torch==2.2.1

# Install remaining Python dependencies with increased timeout
RUN pip install --no-cache-dir --timeout 600 -r requirements.txt

# Copy application code
COPY . .

# Create uploads and chroma directories
RUN mkdir -p uploads chroma_db && \
    chown -R nobody:nogroup uploads chroma_db && \
    chmod -R 777 uploads chroma_db

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"] 