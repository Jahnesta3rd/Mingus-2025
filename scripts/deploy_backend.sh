#!/bin/bash
# ============================================================================
# Mingus Application - Backend Deployment Script
# Deploys the Flask backend application
# ============================================================================

set -e
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
    exit 1
}

cd "$PROJECT_ROOT"

log "Starting backend deployment..."

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
log "Python version: $PYTHON_VERSION"

# Create virtual environment
if [ ! -d "venv" ]; then
    log "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
log "Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install dependencies
log "Installing dependencies..."
pip install -r requirements.txt

# Install gunicorn for production
if ! pip show gunicorn &> /dev/null; then
    log "Installing gunicorn..."
    pip install gunicorn
fi

# Run tests (optional)
if [ "${SKIP_TESTS:-false}" != "true" ]; then
    log "Running backend tests..."
    if python3 -m pytest backend/tests/unit/test_validation.py -v --tb=short; then
        success "Tests passed"
    else
        log "Some tests failed, but continuing deployment..."
    fi
fi

# Create gunicorn config if it doesn't exist
if [ ! -f "$PROJECT_ROOT/gunicorn_config.py" ]; then
    log "Creating gunicorn configuration..."
    cat > "$PROJECT_ROOT/gunicorn_config.py" << 'EOF'
import multiprocessing
import os

bind = os.environ.get('GUNICORN_BIND', '0.0.0.0:5001')
workers = int(os.environ.get('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1))
worker_class = 'sync'
worker_connections = 1000
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 50
preload_app = True
accesslog = os.environ.get('GUNICORN_ACCESS_LOG', '-')
errorlog = os.environ.get('GUNICORN_ERROR_LOG', '-')
loglevel = os.environ.get('GUNICORN_LOG_LEVEL', 'info')
EOF
    success "Gunicorn config created"
fi

# Initialize database if needed
if [ -f "$PROJECT_ROOT/backend/models/database.py" ]; then
    log "Initializing database..."
    python3 -c "
from backend.models.database import init_database
from app import app
with app.app_context():
    init_database(app)
    print('Database initialized')
" || warning "Database initialization failed or already exists"
fi

success "Backend deployment completed"

# Show deployment info
log "Backend deployment summary:"
log "  - Python: $PYTHON_VERSION"
log "  - Virtual environment: $PROJECT_ROOT/venv"
log "  - Application: $PROJECT_ROOT/app.py"
log "  - Gunicorn config: $PROJECT_ROOT/gunicorn_config.py"
