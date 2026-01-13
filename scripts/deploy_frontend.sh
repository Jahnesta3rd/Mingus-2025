#!/bin/bash
# ============================================================================
# Mingus Application - Frontend Deployment Script
# Deploys the React frontend application
# ============================================================================

set -e
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
BUILD_DIR="$FRONTEND_DIR/dist"

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

cd "$FRONTEND_DIR"

log "Starting frontend deployment..."

# Check Node.js version
NODE_VERSION=$(node --version)
NPM_VERSION=$(npm --version)
log "Node.js version: $NODE_VERSION"
log "npm version: $NPM_VERSION"

# Clean previous build
if [ -d "$BUILD_DIR" ]; then
    log "Cleaning previous build..."
    rm -rf "$BUILD_DIR"
fi

# Install dependencies
log "Installing dependencies..."
if [ -f "package-lock.json" ]; then
    npm ci
else
    npm install
fi

# Run tests (optional)
if [ "${SKIP_TESTS:-false}" != "true" ]; then
    log "Running frontend tests..."
    if npm test -- --watchAll=false --passWithNoTests; then
        success "Tests passed"
    else
        log "Some tests failed, but continuing deployment..."
    fi
fi

# Build frontend
log "Building frontend for production..."
npm run build

# Verify build
if [ ! -d "$BUILD_DIR" ]; then
    error "Build directory not created"
fi

if [ -z "$(ls -A $BUILD_DIR)" ]; then
    error "Build directory is empty"
fi

success "Frontend deployment completed"

# Show build info
BUILD_SIZE=$(du -sh "$BUILD_DIR" | cut -f1)
log "Frontend deployment summary:"
log "  - Node.js: $NODE_VERSION"
log "  - Build directory: $BUILD_DIR"
log "  - Build size: $BUILD_SIZE"

# List build files
log "Build files:"
ls -lh "$BUILD_DIR" | head -10
