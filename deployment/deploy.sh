#!/bin/bash

# =============================================================================
# Enhanced Income Comparison Calculator - Production Deployment Script
# Mingus Platform
# =============================================================================

set -e  # Exit on any error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DEPLOYMENT_ENV="${1:-production}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="${PROJECT_ROOT}/backups/${TIMESTAMP}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   error "This script should not be run as root"
   exit 1
fi

# Check if Docker is installed and running
check_docker() {
    log "Checking Docker installation..."
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        error "Docker is not running. Please start Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    success "Docker and Docker Compose are ready"
}

# Check environment file
check_environment() {
    log "Checking environment configuration..."
    
    if [[ ! -f "${PROJECT_ROOT}/.env.production" ]]; then
        error "Production environment file (.env.production) not found!"
        error "Please copy env.production.example to .env.production and configure it."
        exit 1
    fi
    
    # Check required environment variables
    source "${PROJECT_ROOT}/.env.production"
    
    required_vars=(
        "DATABASE_URL"
        "POSTGRES_PASSWORD"
        "SECRET_KEY"
        "ALLOWED_HOSTS"
        "EMAIL_HOST"
        "EMAIL_HOST_USER"
        "EMAIL_HOST_PASSWORD"
    )
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            error "Required environment variable $var is not set in .env.production"
            exit 1
        fi
    done
    
    success "Environment configuration is valid"
}

# Create backup
create_backup() {
    log "Creating backup before deployment..."
    
    mkdir -p "$BACKUP_DIR"
    
    # Backup database
    if docker ps | grep -q mingus-postgres; then
        log "Backing up database..."
        docker exec mingus-postgres pg_dump -U mingus_user mingus > "${BACKUP_DIR}/database_backup.sql"
        success "Database backup created: ${BACKUP_DIR}/database_backup.sql"
    fi
    
    # Backup environment files
    cp "${PROJECT_ROOT}/.env.production" "${BACKUP_DIR}/env.production.backup"
    
    # Backup current images
    if docker images | grep -q mingus-app; then
        docker save mingus-app:latest > "${BACKUP_DIR}/mingus-app-backup.tar"
        success "Application image backup created"
    fi
    
    success "Backup completed: $BACKUP_DIR"
}

# Build application
build_application() {
    log "Building application..."
    
    cd "$PROJECT_ROOT"
    
    # Build production image
    docker-compose -f docker-compose.prod.yml build --no-cache mingus-web
    
    # Build backup image if needed
    if [[ -f "Dockerfile.backup" ]]; then
        docker-compose -f docker-compose.prod.yml build backup
    fi
    
    success "Application build completed"
}

# Run database migrations
run_migrations() {
    log "Running database migrations..."
    
    cd "$PROJECT_ROOT"
    
    # Wait for database to be ready
    log "Waiting for database to be ready..."
    timeout 60 bash -c 'until docker exec mingus-postgres pg_isready -U mingus_user; do sleep 2; done'
    
    # Run migrations
    docker-compose -f docker-compose.prod.yml exec -T mingus-web python manage.py migrate --noinput
    
    success "Database migrations completed"
}

# Collect static files
collect_static() {
    log "Collecting static files..."
    
    cd "$PROJECT_ROOT"
    
    docker-compose -f docker-compose.prod.yml exec -T mingus-web python manage.py collectstatic --noinput
    
    success "Static files collected"
}

# Deploy application
deploy_application() {
    log "Deploying application..."
    
    cd "$PROJECT_ROOT"
    
    # Stop existing services
    log "Stopping existing services..."
    docker-compose -f docker-compose.prod.yml down --remove-orphans
    
    # Start services
    log "Starting services..."
    docker-compose -f docker-compose.prod.yml up -d
    
    # Wait for services to be healthy
    log "Waiting for services to be healthy..."
    timeout 120 bash -c 'until docker-compose -f docker-compose.prod.yml ps | grep -q "healthy"; do sleep 5; done'
    
    success "Application deployment completed"
}

# Run health checks
health_checks() {
    log "Running health checks..."
    
    cd "$PROJECT_ROOT"
    
    # Check web service
    if curl -f http://localhost/health/ > /dev/null 2>&1; then
        success "Web service is healthy"
    else
        error "Web service health check failed"
        return 1
    fi
    
    # Check database
    if docker exec mingus-postgres pg_isready -U mingus_user > /dev/null 2>&1; then
        success "Database is healthy"
    else
        error "Database health check failed"
        return 1
    fi
    
    # Check Redis
    if docker exec mingus-redis redis-cli ping > /dev/null 2>&1; then
        success "Redis is healthy"
    else
        error "Redis health check failed"
        return 1
    fi
    
    # Check Celery workers
    if docker exec mingus-celery-worker celery -A backend.celery inspect ping > /dev/null 2>&1; then
        success "Celery workers are healthy"
    else
        error "Celery workers health check failed"
        return 1
    fi
    
    success "All health checks passed"
}

# Initialize data
initialize_data() {
    log "Initializing application data..."
    
    cd "$PROJECT_ROOT"
    
    # Load initial data
    docker-compose -f docker-compose.prod.yml exec -T mingus-web python manage.py loaddata initial_data.json 2>/dev/null || warning "No initial data to load"
    
    # Create superuser if needed
    if [[ -n "$CREATE_SUPERUSER" ]]; then
        log "Creating superuser..."
        docker-compose -f docker-compose.prod.yml exec -T mingus-web python manage.py createsuperuser --noinput
    fi
    
    success "Data initialization completed"
}

# Setup monitoring
setup_monitoring() {
    log "Setting up monitoring..."
    
    cd "$PROJECT_ROOT"
    
    # Create monitoring directories
    mkdir -p monitoring/grafana/dashboards
    mkdir -p monitoring/grafana/datasources
    
    # Start monitoring services if enabled
    if [[ "$PROMETHEUS_ENABLED" == "true" ]]; then
        docker-compose -f docker-compose.prod.yml up -d prometheus grafana
        success "Monitoring services started"
    fi
}

# Setup SSL certificates
setup_ssl() {
    log "Setting up SSL certificates..."
    
    cd "$PROJECT_ROOT"
    
    # Create SSL directory
    mkdir -p nginx/ssl
    
    # Check if SSL certificates exist
    if [[ ! -f "nginx/ssl/cert.pem" ]] || [[ ! -f "nginx/ssl/key.pem" ]]; then
        warning "SSL certificates not found. Generating self-signed certificates..."
        
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout nginx/ssl/key.pem \
            -out nginx/ssl/cert.pem \
            -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
        
        success "Self-signed SSL certificates generated"
    else
        success "SSL certificates found"
    fi
}

# Cleanup old backups
cleanup_backups() {
    log "Cleaning up old backups..."
    
    # Keep only last 5 backups
    cd "${PROJECT_ROOT}/backups"
    ls -t | tail -n +6 | xargs -r rm -rf
    
    success "Old backups cleaned up"
}

# Main deployment function
main() {
    log "Starting deployment for environment: $DEPLOYMENT_ENV"
    
    # Pre-deployment checks
    check_docker
    check_environment
    
    # Create backup
    create_backup
    
    # Build and deploy
    build_application
    deploy_application
    
    # Wait for services to be ready
    sleep 10
    
    # Post-deployment tasks
    run_migrations
    collect_static
    initialize_data
    setup_monitoring
    setup_ssl
    
    # Health checks
    health_checks
    
    # Cleanup
    cleanup_backups
    
    success "Deployment completed successfully!"
    
    # Display service status
    log "Service status:"
    docker-compose -f docker-compose.prod.yml ps
    
    # Display access information
    echo ""
    log "Access Information:"
    echo "  - Web Application: http://localhost"
    echo "  - API Documentation: http://localhost/api/docs/"
    echo "  - Admin Panel: http://localhost/admin/"
    echo "  - Grafana Dashboard: http://localhost:3000"
    echo "  - Prometheus: http://localhost:9090"
    echo ""
    
    success "Deployment script completed!"
}

# Rollback function
rollback() {
    log "Rolling back deployment..."
    
    cd "$PROJECT_ROOT"
    
    # Stop current services
    docker-compose -f docker-compose.prod.yml down
    
    # Restore from backup
    if [[ -d "$BACKUP_DIR" ]]; then
        log "Restoring from backup: $BACKUP_DIR"
        
        # Restore database if backup exists
        if [[ -f "${BACKUP_DIR}/database_backup.sql" ]]; then
            docker-compose -f docker-compose.prod.yml up -d postgres
            sleep 10
            docker exec -i mingus-postgres psql -U mingus_user mingus < "${BACKUP_DIR}/database_backup.sql"
        fi
        
        # Restore environment if needed
        if [[ -f "${BACKUP_DIR}/env.production.backup" ]]; then
            cp "${BACKUP_DIR}/env.production.backup" "${PROJECT_ROOT}/.env.production"
        fi
        
        # Restore image if backup exists
        if [[ -f "${BACKUP_DIR}/mingus-app-backup.tar" ]]; then
            docker load < "${BACKUP_DIR}/mingus-app-backup.tar"
        fi
        
        # Restart services
        docker-compose -f docker-compose.prod.yml up -d
        
        success "Rollback completed"
    else
        error "No backup found for rollback"
        exit 1
    fi
}

# Show usage
usage() {
    echo "Usage: $0 [production|staging] [--rollback]"
    echo ""
    echo "Options:"
    echo "  production    Deploy to production environment (default)"
    echo "  staging       Deploy to staging environment"
    echo "  --rollback    Rollback to previous deployment"
    echo "  --help        Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  CREATE_SUPERUSER    Set to 'true' to create a superuser during deployment"
    echo "  PROMETHEUS_ENABLED  Set to 'true' to enable monitoring services"
}

# Parse command line arguments
case "${1:-production}" in
    production|staging)
        DEPLOYMENT_ENV="$1"
        shift
        ;;
    --rollback)
        rollback
        exit 0
        ;;
    --help|-h)
        usage
        exit 0
        ;;
    *)
        error "Invalid argument: $1"
        usage
        exit 1
        ;;
esac

# Run main deployment
main "$@" 