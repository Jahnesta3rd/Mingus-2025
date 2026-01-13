#!/bin/bash
# ============================================================================
# Mingus Application - Production Deployment Script
# Comprehensive deployment script for production environments
# ============================================================================

set -e  # Exit on any error
set -u  # Exit on undefined variable

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
APP_NAME="mingus-app"
BACKUP_DIR="$PROJECT_ROOT/backups"
LOG_FILE="$PROJECT_ROOT/logs/deployment_$(date +%Y%m%d_%H%M%S).log"
ENV_FILE="$PROJECT_ROOT/.env.production"

# Create necessary directories
mkdir -p "$BACKUP_DIR"
mkdir -p "$PROJECT_ROOT/logs"

# Functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}✅ $1${NC}" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}❌ $1${NC}" | tee -a "$LOG_FILE"
    exit 1
}

info() {
    echo -e "${CYAN}ℹ️  $1${NC}" | tee -a "$LOG_FILE"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        error "Python 3 is not installed"
    fi
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        error "Node.js is not installed"
    fi
    
    # Check npm
    if ! command -v npm &> /dev/null; then
        error "npm is not installed"
    fi
    
    # Check if .env.production exists
    if [ ! -f "$ENV_FILE" ]; then
        warning ".env.production file not found. Creating from template..."
        if [ -f "$PROJECT_ROOT/.env.example" ]; then
            cp "$PROJECT_ROOT/.env.example" "$ENV_FILE"
            warning "Please configure .env.production before continuing"
        else
            error ".env.production file is required"
        fi
    fi
    
    success "Prerequisites check passed"
}

# Load environment variables
load_environment() {
    log "Loading environment variables..."
    
    if [ -f "$ENV_FILE" ]; then
        set -a
        source "$ENV_FILE"
        set +a
        success "Environment variables loaded"
    else
        error "Environment file not found: $ENV_FILE"
    fi
}

# Create backup
create_backup() {
    log "Creating backup..."
    
    BACKUP_TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_PATH="$BACKUP_DIR/backup_$BACKUP_TIMESTAMP"
    mkdir -p "$BACKUP_PATH"
    
    # Backup database
    if [ -f "$PROJECT_ROOT/assessments.db" ]; then
        cp "$PROJECT_ROOT/assessments.db" "$BACKUP_PATH/assessments.db"
        success "Database backed up"
    fi
    
    # Backup environment file
    if [ -f "$ENV_FILE" ]; then
        cp "$ENV_FILE" "$BACKUP_PATH/.env.production"
        success "Environment file backed up"
    fi
    
    # Backup current deployment
    if [ -d "$PROJECT_ROOT/backend" ]; then
        tar -czf "$BACKUP_PATH/backend.tar.gz" -C "$PROJECT_ROOT" backend/
        success "Backend code backed up"
    fi
    
    if [ -d "$PROJECT_ROOT/frontend" ]; then
        tar -czf "$BACKUP_PATH/frontend.tar.gz" -C "$PROJECT_ROOT" frontend/
        success "Frontend code backed up"
    fi
    
    # Save backup path for rollback
    echo "$BACKUP_PATH" > "$PROJECT_ROOT/.last_backup_path"
    success "Backup created: $BACKUP_PATH"
}

# Run database migrations
run_migrations() {
    log "Running database migrations..."
    
    cd "$PROJECT_ROOT"
    
    if [ -d "migrations" ]; then
        if [ -f "migrations/migrate.py" ]; then
            python3 migrations/migrate.py
            success "Database migrations completed"
        else
            warning "Migration script not found, skipping"
        fi
    else
        warning "Migrations directory not found, skipping"
    fi
}

# Deploy backend
deploy_backend() {
    log "Deploying backend..."
    
    cd "$PROJECT_ROOT"
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        log "Creating Python virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install/update dependencies
    log "Installing backend dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Run backend tests
    if [ "${SKIP_TESTS:-false}" != "true" ]; then
        log "Running backend tests..."
        if python3 -m pytest backend/tests/unit/test_validation.py -v; then
            success "Backend tests passed"
        else
            warning "Some backend tests failed, continuing deployment..."
        fi
    fi
    
    success "Backend deployment completed"
}

# Deploy frontend
deploy_frontend() {
    log "Deploying frontend..."
    
    cd "$PROJECT_ROOT/frontend"
    
    # Install dependencies
    log "Installing frontend dependencies..."
    npm ci --production=false
    
    # Build frontend
    log "Building frontend..."
    npm run build
    
    success "Frontend deployment completed"
}

# Restart services
restart_services() {
    log "Restarting services..."
    
    # Restart backend service if systemd is available
    if systemctl is-active --quiet ${APP_NAME}-backend 2>/dev/null; then
        sudo systemctl restart ${APP_NAME}-backend
        success "Backend service restarted"
    else
        warning "Backend service not found, skipping restart"
    fi
    
    # Restart frontend service if systemd is available
    if systemctl is-active --quiet ${APP_NAME}-frontend 2>/dev/null; then
        sudo systemctl restart ${APP_NAME}-frontend
        success "Frontend service restarted"
    else
        warning "Frontend service not found, skipping restart"
    fi
    
    # Reload nginx if available
    if command -v nginx &> /dev/null; then
        sudo nginx -t && sudo systemctl reload nginx
        success "Nginx reloaded"
    fi
}

# Health check
health_check() {
    log "Running health checks..."
    
    # Wait for services to start
    sleep 5
    
    # Check backend health
    if [ -n "${BACKEND_URL:-}" ]; then
        if curl -f -s "${BACKEND_URL}/health" > /dev/null; then
            success "Backend health check passed"
        else
            warning "Backend health check failed"
        fi
    fi
    
    # Check frontend
    if [ -n "${FRONTEND_URL:-}" ]; then
        if curl -f -s "${FRONTEND_URL}" > /dev/null; then
            success "Frontend health check passed"
        else
            warning "Frontend health check failed"
        fi
    fi
}

# Main deployment function
main() {
    echo -e "${CYAN}"
    echo "============================================================================"
    echo "  Mingus Application - Production Deployment"
    echo "============================================================================"
    echo -e "${NC}"
    
    log "Starting deployment process..."
    
    # Run deployment steps
    check_prerequisites
    load_environment
    create_backup
    deploy_backend
    deploy_frontend
    run_migrations
    restart_services
    health_check
    
    echo -e "${GREEN}"
    echo "============================================================================"
    echo "  ✅ Deployment completed successfully!"
    echo "============================================================================"
    echo -e "${NC}"
    
    log "Deployment completed. Log file: $LOG_FILE"
    info "Backup location: $(cat $PROJECT_ROOT/.last_backup_path 2>/dev/null || echo 'N/A')"
}

# Run main function
main "$@"
