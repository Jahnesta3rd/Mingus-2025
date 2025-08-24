#!/bin/bash

# =====================================================
# MINGUS PRODUCTION DEPLOYMENT SCRIPT
# =====================================================
# Complete production deployment orchestration
# Handles environment setup, SSL, database, and services

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="$PROJECT_ROOT/logs/deployment.log"
BACKUP_DIR="$PROJECT_ROOT/backups"
SSL_DIR="$PROJECT_ROOT/ssl"
LOGS_DIR="$PROJECT_ROOT/logs"
DATA_DIR="$PROJECT_ROOT/data"

# Function to log messages
log() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${timestamp} [${level}] ${message}" | tee -a "$LOG_FILE"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        log "ERROR" "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    log "INFO" "Docker is running"
}

# Function to setup environment
setup_environment() {
    log "INFO" "Setting up production environment..."
    
    # Create necessary directories
    mkdir -p "$LOGS_DIR" "$BACKUP_DIR" "$SSL_DIR" "$DATA_DIR"
    mkdir -p "$PROJECT_ROOT/static" "$PROJECT_ROOT/uploads"
    mkdir -p "$LOGS_DIR/nginx" "$LOGS_DIR/redis" "$LOGS_DIR/postgres"
    
    # Set proper permissions
    chmod 755 "$LOGS_DIR" "$BACKUP_DIR" "$SSL_DIR" "$DATA_DIR"
    chmod 755 "$PROJECT_ROOT/static" "$PROJECT_ROOT/uploads"
    
    # Load environment variables
    if [[ -f "$PROJECT_ROOT/.env.production" ]]; then
        log "INFO" "Loading production environment variables..."
        export $(grep -v '^#' "$PROJECT_ROOT/.env.production" | xargs)
    else
        log "WARNING" "No .env.production file found. Using default values."
    fi
    
    # Set default values for critical variables
    export POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-"mingus_production_password"}
    export REDIS_PASSWORD=${REDIS_PASSWORD:-"mingus_redis_password"}
    export SECRET_KEY=${SECRET_KEY:-"mingus-secret-key-change-in-production"}
    
    log "INFO" "Environment setup complete"
}

# Function to setup SSL certificates
setup_ssl_certificates() {
    log "INFO" "Setting up SSL certificates..."
    
    if [[ ! -f "$SSL_DIR/certificate.crt" ]] || [[ ! -f "$SSL_DIR/private.key" ]]; then
        log "WARNING" "SSL certificates not found. Generating self-signed certificates for development/testing..."
        
        # Generate self-signed certificate
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout "$SSL_DIR/private.key" \
            -out "$SSL_DIR/certificate.crt" \
            -subj "/C=US/ST=State/L=City/O=MINGUS/CN=localhost" \
            -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"
        
        # Set proper permissions
        chmod 600 "$SSL_DIR/private.key"
        chmod 644 "$SSL_DIR/certificate.crt"
        
        log "INFO" "Self-signed SSL certificates generated"
    else
        log "INFO" "SSL certificates found"
    fi
}

# Function to setup Docker Compose
setup_docker_compose() {
    log "INFO" "Setting up Docker Compose..."
    
    # Build images
    log "INFO" "Building Docker images..."
    docker-compose -f "$SCRIPT_DIR/docker-compose.production.yml" build --no-cache
    
    # Create network if it doesn't exist
    if ! docker network ls | grep -q "mingus_network"; then
        docker network create mingus_network
        log "INFO" "Created Docker network: mingus_network"
    fi
    
    log "INFO" "Docker Compose setup complete"
}

# Function to setup database
setup_database() {
    log "INFO" "Setting up database..."
    
    # Start PostgreSQL
    log "INFO" "Starting PostgreSQL..."
    docker-compose -f "$SCRIPT_DIR/docker-compose.production.yml" up -d postgres
    
    # Wait for PostgreSQL to be ready
    log "INFO" "Waiting for PostgreSQL to be ready..."
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if docker-compose -f "$SCRIPT_DIR/docker-compose.production.yml" exec -T postgres pg_isready -U mingus_user -d mingus_production >/dev/null 2>&1; then
            log "INFO" "PostgreSQL is ready"
            break
        fi
        
        log "INFO" "Waiting for PostgreSQL... (attempt $attempt/$max_attempts)"
        sleep 10
        ((attempt++))
    done
    
    if [[ $attempt -gt $max_attempts ]]; then
        log "ERROR" "PostgreSQL failed to start within expected time"
        exit 1
    fi
    
    # Run database migrations
    log "INFO" "Running database migrations..."
    if [[ -f "$PROJECT_ROOT/scripts/apply_postgres_migrations.py" ]]; then
        docker-compose -f "$SCRIPT_DIR/docker-compose.production.yml" run --rm web python scripts/apply_postgres_migrations.py
    else
        log "WARNING" "Migration script not found. Skipping migrations."
    fi
    
    log "INFO" "Database setup complete"
}

# Function to setup Redis
setup_redis() {
    log "INFO" "Setting up Redis..."
    
    # Start Redis
    docker-compose -f "$SCRIPT_DIR/docker-compose.production.yml" up -d redis
    
    # Wait for Redis to be ready
    log "INFO" "Waiting for Redis to be ready..."
    local max_attempts=10
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if docker-compose -f "$SCRIPT_DIR/docker-compose.production.yml" exec -T redis redis-cli ping >/dev/null 2>&1; then
            log "INFO" "Redis is ready"
            break
        fi
        
        log "INFO" "Waiting for Redis... (attempt $attempt/$max_attempts)"
        sleep 5
        ((attempt++))
    done
    
    if [[ $attempt -gt $max_attempts ]]; then
        log "ERROR" "Redis failed to start within expected time"
        exit 1
    fi
    
    log "INFO" "Redis setup complete"
}

# Function to setup application services
setup_application_services() {
    log "INFO" "Setting up application services..."
    
    # Start Celery workers
    log "INFO" "Starting Celery workers..."
    docker-compose -f "$SCRIPT_DIR/docker-compose.production.yml" up -d \
        celery-worker \
        celery-sms-worker \
        celery-email-worker \
        celery-analytics-worker \
        celery-monitoring-worker \
        celery-optimization-worker
    
    # Start Celery beat
    log "INFO" "Starting Celery beat scheduler..."
    docker-compose -f "$SCRIPT_DIR/docker-compose.production.yml" up -d celery-beat
    
    # Start web application
    log "INFO" "Starting web application..."
    docker-compose -f "$SCRIPT_DIR/docker-compose.production.yml" up -d web
    
    # Start monitoring services
    log "INFO" "Starting monitoring services..."
    docker-compose -f "$SCRIPT_DIR/docker-compose.production.yml" up -d statsd graphite
    
    # Start Nginx
    log "INFO" "Starting Nginx reverse proxy..."
    docker-compose -f "$SCRIPT_DIR/docker-compose.production.yml" up -d nginx
    
    log "INFO" "Application services setup complete"
}

# Function to check service health
check_service_health() {
    local service=$1
    local max_attempts=10
    local attempt=1
    
    log "INFO" "Checking health of $service..."
    
    while [[ $attempt -le $max_attempts ]]; do
        if docker-compose -f "$SCRIPT_DIR/docker-compose.production.yml" ps "$service" | grep -q "Up"; then
            log "INFO" "$service is healthy"
            return 0
        fi
        
        log "INFO" "Waiting for $service... (attempt $attempt/$max_attempts)"
        sleep 10
        ((attempt++))
    done
    
    log "ERROR" "$service failed health check"
    return 1
}

# Function to perform health checks
perform_health_checks() {
    log "INFO" "Performing health checks..."
    
    local services=("web" "postgres" "redis" "celery-worker" "nginx")
    local failed_services=()
    
    for service in "${services[@]}"; do
        if ! check_service_health "$service"; then
            failed_services+=("$service")
        fi
    done
    
    if [[ ${#failed_services[@]} -gt 0 ]]; then
        log "ERROR" "The following services failed health checks: ${failed_services[*]}"
        return 1
    fi
    
    log "INFO" "All services are healthy"
    return 0
}

# Function to setup monitoring
setup_monitoring() {
    log "INFO" "Setting up monitoring..."
    
    # Create monitoring configuration files
    mkdir -p "$SCRIPT_DIR/monitoring"
    
    # StatsD configuration
    cat > "$SCRIPT_DIR/monitoring/statsd.conf" << 'EOF'
{
  graphitePort: 2003,
  graphiteHost: "graphite",
  port: 8125,
  backends: [ "./backends/graphite" ],
  graphite: {
    legacyNamespace: false,
    globalPrefix: "mingus"
  }
}
EOF
    
    # Graphite configuration
    cat > "$SCRIPT_DIR/monitoring/graphite.conf" << 'EOF'
[default]
default_duration = 1s
log_cache_hits = True
log_cache_misses = True
log_metric_access = True
log_rendering = True
log_rotation = True
log_rotation_count = 1
log_rotation_size = 10MB
EOF
    
    log "INFO" "Monitoring setup complete"
}

# Function to setup backups
setup_backups() {
    log "INFO" "Setting up automated backups..."
    
    # Create backup script
    cat > "$PROJECT_ROOT/scripts/backup_database.py" << 'EOF'
#!/usr/bin/env python3
"""
Automated database backup script for MINGUS production
"""

import os
import subprocess
import sys
from datetime import datetime
import gzip
import shutil

def backup_postgres():
    """Backup PostgreSQL database"""
    backup_dir = os.environ.get('BACKUP_DIRECTORY', '/app/backups/database')
    retention_days = int(os.environ.get('BACKUP_RETENTION_DAYS', 30))
    compression = os.environ.get('BACKUP_COMPRESSION', 'gzip')
    
    # Create backup directory
    os.makedirs(backup_dir, exist_ok=True)
    
    # Generate backup filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f"{backup_dir}/mingus_production_{timestamp}.sql"
    
    # Perform backup
    cmd = [
        'pg_dump',
        '--host=postgres',
        '--port=5432',
        '--username=mingus_user',
        '--dbname=mingus_production',
        '--verbose',
        '--clean',
        '--no-owner',
        '--no-privileges',
        f'--file={backup_file}'
    ]
    
    env = os.environ.copy()
    env['PGPASSWORD'] = os.environ.get('POSTGRES_PASSWORD')
    
    try:
        subprocess.run(cmd, env=env, check=True)
        print(f"PostgreSQL backup completed: {backup_file}")
        
        # Compress backup
        if compression == 'gzip':
            with open(backup_file, 'rb') as f_in:
                with gzip.open(f"{backup_file}.gz", 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            os.remove(backup_file)
            print(f"Backup compressed: {backup_file}.gz")
        
        # Clean old backups
        cleanup_old_backups(backup_dir, retention_days)
        
    except subprocess.CalledProcessError as e:
        print(f"PostgreSQL backup failed: {e}")
        sys.exit(1)

def backup_redis():
    """Backup Redis data"""
    backup_dir = os.environ.get('BACKUP_DIRECTORY', '/app/backups/redis')
    retention_days = int(os.environ.get('BACKUP_RETENTION_DAYS', 30))
    
    # Create backup directory
    os.makedirs(backup_dir, exist_ok=True)
    
    # Generate backup filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f"{backup_dir}/redis_backup_{timestamp}.rdb"
    
    # Perform backup
    cmd = ['redis-cli', '--rdb', backup_file]
    
    try:
        subprocess.run(cmd, check=True)
        print(f"Redis backup completed: {backup_file}")
        
        # Clean old backups
        cleanup_old_backups(backup_dir, retention_days)
        
    except subprocess.CalledProcessError as e:
        print(f"Redis backup failed: {e}")
        sys.exit(1)

def cleanup_old_backups(backup_dir, retention_days):
    """Clean up old backup files"""
    import time
    cutoff_time = time.time() - (retention_days * 24 * 60 * 60)
    
    for filename in os.listdir(backup_dir):
        filepath = os.path.join(backup_dir, filename)
        if os.path.isfile(filepath) and os.path.getmtime(filepath) < cutoff_time:
            os.remove(filepath)
            print(f"Removed old backup: {filename}")

if __name__ == '__main__':
    backup_postgres()
    backup_redis()
    print("Backup process completed successfully")
EOF
    
    # Make backup script executable
    chmod +x "$PROJECT_ROOT/scripts/backup_database.py"
    
    # Setup cron job for automated backups (if running on host)
    if [[ -f /etc/crontab ]]; then
        log "INFO" "Setting up cron job for automated backups..."
        # Add cron job to run backup daily at 2 AM
        (crontab -l 2>/dev/null; echo "0 2 * * * $PROJECT_ROOT/scripts/backup_database.py >> $LOGS_DIR/backup.log 2>&1") | crontab -
    fi
    
    log "INFO" "Backup setup complete"
}

# Function to setup log rotation
setup_log_rotation() {
    log "INFO" "Setting up log rotation..."
    
    # Create logrotate configuration
    cat > /etc/logrotate.d/mingus << EOF
$LOGS_DIR/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 root root
    postrotate
        docker-compose -f $SCRIPT_DIR/docker-compose.production.yml restart web
    endscript
}
EOF
    
    log "INFO" "Log rotation setup complete"
}

# Function to display deployment status
display_status() {
    log "INFO" "Deployment Status:"
    echo
    echo -e "${GREEN}=== MINGUS PRODUCTION DEPLOYMENT STATUS ===${NC}"
    echo
    
    # Check service status
    docker-compose -f "$SCRIPT_DIR/docker-compose.production.yml" ps
    
    echo
    echo -e "${GREEN}=== SERVICE ENDPOINTS ===${NC}"
    echo -e "Web Application: ${BLUE}http://localhost${NC}"
    echo -e "Web Application (Direct): ${BLUE}http://localhost:5002${NC}"
    echo -e "Graphite Dashboard: ${BLUE}http://localhost:8080${NC}"
    echo -e "PostgreSQL: ${BLUE}localhost:5432${NC}"
    echo -e "Redis: ${BLUE}localhost:6379${NC}"
    
    echo
    echo -e "${GREEN}=== LOG FILES ===${NC}"
    echo -e "Deployment Log: ${BLUE}$LOG_FILE${NC}"
    echo -e "Application Logs: ${BLUE}$LOGS_DIR/${NC}"
    
    echo
    echo -e "${GREEN}=== USEFUL COMMANDS ===${NC}"
    echo -e "View logs: ${YELLOW}docker-compose -f $SCRIPT_DIR/docker-compose.production.yml logs -f${NC}"
    echo -e "Restart services: ${YELLOW}docker-compose -f $SCRIPT_DIR/docker-compose.production.yml restart${NC}"
    echo -e "Stop all services: ${YELLOW}docker-compose -f $SCRIPT_DIR/docker-compose.production.yml down${NC}"
    echo -e "Backup database: ${YELLOW}docker-compose -f $SCRIPT_DIR/docker-compose.production.yml run --rm backup${NC}"
    
    echo
    echo -e "${GREEN}=== DEPLOYMENT COMPLETE ===${NC}"
}

# Function to cleanup on exit
cleanup() {
    log "INFO" "Cleaning up..."
    # Add any cleanup tasks here
}

# Main deployment function
main() {
    log "INFO" "Starting MINGUS production deployment..."
    
    # Set up cleanup trap
    trap cleanup EXIT
    
    # Check prerequisites
    check_docker
    
    # Setup environment
    setup_environment
    
    # Setup SSL certificates
    setup_ssl_certificates
    
    # Setup Docker Compose
    setup_docker_compose
    
    # Setup database
    setup_database
    
    # Setup Redis
    setup_redis
    
    # Setup application services
    setup_application_services
    
    # Setup monitoring
    setup_monitoring
    
    # Setup backups
    setup_backups
    
    # Setup log rotation
    setup_log_rotation
    
    # Perform health checks
    if perform_health_checks; then
        log "INFO" "All services are healthy"
    else
        log "ERROR" "Some services failed health checks"
        exit 1
    fi
    
    # Display deployment status
    display_status
    
    log "INFO" "MINGUS production deployment completed successfully!"
}

# Run main function
main "$@" 