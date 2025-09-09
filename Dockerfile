# =====================================================
# Mingus Meme Splash Page - Production Dockerfile
# Multi-stage build for optimized production deployment
# =====================================================

# Stage 1: Build stage
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY requirements_meme_admin.txt requirements.txt
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Stage 2: Production stage
FROM python:3.11-slim as production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=meme_admin_app.py \
    FLASK_ENV=production \
    PATH="/opt/venv/bin:$PATH"

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Create non-root user for security
RUN groupadd -r mingus && useradd -r -g mingus mingus

# Create application directory
WORKDIR /app

# Copy application code
COPY meme_admin_app.py .
COPY backend/ ./backend/
COPY templates/ ./templates/
COPY static/ ./static/
COPY meme_database_schema.sql .
COPY meme_analytics_schema.sql .

# Create necessary directories
RUN mkdir -p /app/static/uploads \
    /app/logs \
    /app/database_backups \
    && chown -R mingus:mingus /app

# Set proper permissions
RUN chmod -R 755 /app && \
    chmod -R 777 /app/static/uploads && \
    chmod -R 777 /app/logs

# Switch to non-root user
USER mingus

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Default command
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "--keep-alive", "2", "--max-requests", "1000", "--max-requests-jitter", "100", "meme_admin_app:app"]
