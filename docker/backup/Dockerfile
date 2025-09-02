# MINGUS Backup System Docker Image
# Enterprise-grade backup solution for financial applications

FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    redis-tools \
    tar \
    gzip \
    bzip2 \
    xz-utils \
    gnupg \
    curl \
    wget \
    cron \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements-backup.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Create backup user
RUN useradd -m -s /bin/bash backup && \
    mkdir -p /home/backup/{backups,logs,config} && \
    chown -R backup:backup /home/backup

# Create backup directories
RUN mkdir -p /var/backups/{postgresql,redis,files} && \
    mkdir -p /var/recovery/postgresql && \
    mkdir -p /var/lib/postgresql/wal_archive && \
    chown -R backup:backup /var/backups /var/recovery /var/lib/postgresql

# Copy application code
COPY backend/ /app/backend/
COPY scripts/ /app/scripts/
COPY docker/backup/entrypoint.sh /app/entrypoint.sh
COPY docker/backup/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Set working directory
WORKDIR /app

# Make entrypoint executable
RUN chmod +x /app/entrypoint.sh

# Create log directories
RUN mkdir -p /app/logs && \
    chown -R backup:backup /app

# Switch to backup user
USER backup

# Expose ports
EXPOSE 9090 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
