# Use Python 3.11 slim image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        curl \
        git \
        && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install additional monitoring dependencies
RUN pip install --no-cache-dir \
    psutil \
    prometheus-client \
    redis \
    celery[redis] \
    boto3 \
    gunicorn

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/backups

# Create non-root user
RUN useradd --create-home --shell /bin/bash mingus \
    && chown -R mingus:mingus /app

# Switch to non-root user
USER mingus

# Expose port
EXPOSE 5002

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5002/health || exit 1

# Default command
CMD ["gunicorn", "--bind", "0.0.0.0:5002", "--workers", "4", "--timeout", "120", "app:app"] 