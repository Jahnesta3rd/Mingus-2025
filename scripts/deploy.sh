#!/bin/bash
# =====================================================
# Mingus Meme Splash Page - Deployment Script
# Automated deployment script for production environments
# =====================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="mingus-meme-app"
BACKUP_DIR="database_backups"
LOG_FILE="deployment.log"

# Functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a $LOG_FILE
}

success() {
    echo -e "${GREEN}✅ $1${NC}" | tee -a $LOG_FILE
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}" | tee -a $LOG_FILE
}

error() {
    echo -e "${RED}❌ $1${NC}" | tee -a $LOG_FILE
    exit 1
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed"
    fi
    
    # Check if .env file exists
    if [ ! -f ".env" ]; then
        error ".env file not found. Please copy env.example to .env and configure it"
    fi
    
    success "Prerequisites check passed"
}

# Create backup
create_backup() {
    log "Creating database backup..."
    
    # Create backup directory if it doesn't exist
    mkdir -p $BACKUP_DIR
    
    # Create timestamped backup
    BACKUP_FILE="$BACKUP_DIR/mingus_memes_backup_$(date +%Y%m%d_%H%M%S).db"
    
    if [ -f "mingus_memes.db" ]; then
        cp mingus_memes.db $BACKUP_FILE
        success "Database backup created: $BACKUP_FILE"
    else
        warning "No existing database found, skipping backup"
    fi
}

# Run database migrations
run_migrations() {
    log "Running database migrations..."
    
    # Check if migration script exists
    if [ ! -f "migrations/migrate.py" ]; then
        error "Migration script not found"
    fi
    
    # Run migrations
    if python3 migrations/migrate.py; then
        success "Database migrations completed"
    else
        error "Database migrations failed"
    fi
}

# Build and deploy application
deploy_application() {
    log "Building and deploying application..."
    
    # Stop existing containers
    log "Stopping existing containers..."
    docker-compose down || true
    
    # Build and start new containers
    log "Building new containers..."
    docker-compose build --no-cache
    
    log "Starting containers..."
    docker-compose up -d
    
    # Wait for application to be ready
    log "Waiting for application to be ready..."
    sleep 30
    
    # Check if application is responding
    if curl -f http://localhost/health > /dev/null 2>&1; then
        success "Application is responding"
    else
        error "Application health check failed"
    fi
}

# Verify deployment
verify_deployment() {
    log "Verifying deployment..."
    
    # Check container status
    if docker-compose ps | grep -q "Up"; then
        success "Containers are running"
    else
        error "Some containers are not running"
    fi
    
    # Check database connectivity
    if docker-compose exec -T $APP_NAME python3 -c "import sqlite3; conn = sqlite3.connect('mingus_memes.db'); conn.close()" 2>/dev/null; then
        success "Database connectivity verified"
    else
        error "Database connectivity check failed"
    fi
    
    # Check file uploads directory
    if docker-compose exec -T $APP_NAME test -d /app/static/uploads; then
        success "Uploads directory exists"
    else
        error "Uploads directory not found"
    fi
    
    # Check logs for errors
    if docker-compose logs $APP_NAME | grep -i error | tail -5; then
        warning "Found errors in application logs"
    else
        success "No errors found in application logs"
    fi
}

# Setup monitoring
setup_monitoring() {
    log "Setting up monitoring..."
    
    # Check if Sentry DSN is configured
    if grep -q "SENTRY_DSN=" .env && ! grep -q "SENTRY_DSN=your-sentry-dsn" .env; then
        success "Sentry configuration found"
    else
        warning "Sentry DSN not configured"
    fi
    
    # Check if New Relic is configured
    if grep -q "NEW_RELIC_LICENSE_KEY=" .env && ! grep -q "NEW_RELIC_LICENSE_KEY=your-new-relic-key" .env; then
        success "New Relic configuration found"
    else
        warning "New Relic license key not configured"
    fi
}

# Cleanup old backups
cleanup_backups() {
    log "Cleaning up old backups..."
    
    # Keep only last 7 days of backups
    find $BACKUP_DIR -name "mingus_memes_backup_*.db" -mtime +7 -delete 2>/dev/null || true
    
    success "Old backups cleaned up"
}

# Main deployment function
main() {
    log "Starting deployment of Mingus Meme Splash Page..."
    
    check_prerequisites
    create_backup
    run_migrations
    deploy_application
    verify_deployment
    setup_monitoring
    cleanup_backups
    
    success "Deployment completed successfully!"
    log "Application is available at: http://localhost"
    log "Health check: http://localhost/health"
    log "Admin interface: http://localhost"
    
    # Show container status
    echo ""
    log "Container status:"
    docker-compose ps
}

# Handle script arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "Options:"
        echo "  --help, -h     Show this help message"
        echo "  --backup-only  Only create backup"
        echo "  --migrate-only Only run migrations"
        echo "  --verify-only  Only verify deployment"
        echo ""
        exit 0
        ;;
    --backup-only)
        check_prerequisites
        create_backup
        exit 0
        ;;
    --migrate-only)
        check_prerequisites
        run_migrations
        exit 0
        ;;
    --verify-only)
        verify_deployment
        exit 0
        ;;
    *)
        main
        ;;
esac
