#!/bin/bash
# ============================================================================
# Mingus Application - Complete Dependency Verification Script
# Checks all system, frontend, and backend dependencies on DigitalOcean
# ============================================================================

set -e
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
BACKEND_DIR="$PROJECT_ROOT/backend"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Counters
PASSED=0
FAILED=0
WARNINGS=0

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
    ((PASSED++))
}

error() {
    echo -e "${RED}❌ $1${NC}"
    ((FAILED++))
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    ((WARNINGS++))
}

info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

# Header
echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  Complete Dependency Verification for DigitalOcean         ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

log "Checking dependencies in: $PROJECT_ROOT"
echo ""

# ============================================================================
# SYSTEM DEPENDENCIES
# ============================================================================

echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}SYSTEM DEPENDENCIES${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check Node.js
log "Checking Node.js..."
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    NODE_MAJOR=$(echo "$NODE_VERSION" | sed 's/v//' | cut -d. -f1)
    if [ "$NODE_MAJOR" -ge 18 ]; then
        success "Node.js installed: $NODE_VERSION (compatible)"
    else
        warning "Node.js version may be too old: $NODE_VERSION (recommended: >= 18.x)"
    fi
else
    error "Node.js not installed"
fi

# Check npm
log "Checking npm..."
if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm --version)
    success "npm installed: $NPM_VERSION"
else
    error "npm not installed"
fi

# Check Python
log "Checking Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    success "Python installed: $PYTHON_VERSION"
else
    error "Python3 not installed"
fi

# Check pip
log "Checking pip..."
if command -v pip3 &> /dev/null || python3 -m pip --version &> /dev/null; then
    PIP_VERSION=$(python3 -m pip --version 2>/dev/null | head -n1 || echo "pip available")
    success "pip installed: $PIP_VERSION"
else
    error "pip not installed"
fi

# Check Nginx
log "Checking Nginx..."
if command -v nginx &> /dev/null; then
    NGINX_VERSION=$(nginx -v 2>&1 | grep -oP 'nginx/\K[0-9.]+' || echo "unknown")
    if systemctl is-active --quiet nginx 2>/dev/null; then
        success "Nginx installed: $NGINX_VERSION (running)"
    else
        warning "Nginx installed: $NGINX_VERSION (not running)"
    fi
else
    error "Nginx not installed"
fi

# Check PostgreSQL
log "Checking PostgreSQL..."
if command -v psql &> /dev/null; then
    PSQL_VERSION=$(psql --version | grep -oP 'psql \(PostgreSQL\) \K[0-9.]+' || echo "unknown")
    if systemctl is-active --quiet postgresql 2>/dev/null || systemctl is-active --quiet postgresql@*-main 2>/dev/null; then
        success "PostgreSQL installed: $PSQL_VERSION (running)"
    else
        warning "PostgreSQL installed: $PSQL_VERSION (not running)"
    fi
else
    warning "PostgreSQL client not found (may be using remote database)"
fi

# Check Redis
log "Checking Redis..."
if command -v redis-cli &> /dev/null; then
    REDIS_VERSION=$(redis-cli --version 2>/dev/null | grep -oP 'redis-cli \K[0-9.]+' || echo "unknown")
    if systemctl is-active --quiet redis 2>/dev/null || systemctl is-active --quiet redis-server 2>/dev/null; then
        success "Redis installed: $REDIS_VERSION (running)"
    else
        warning "Redis installed: $REDIS_VERSION (not running)"
    fi
else
    warning "Redis not found (may be using remote Redis)"
fi

# Check Git
log "Checking Git..."
if command -v git &> /dev/null; then
    GIT_VERSION=$(git --version | grep -oP 'git version \K[0-9.]+' || echo "unknown")
    success "Git installed: $GIT_VERSION"
else
    error "Git not installed"
fi

echo ""

# ============================================================================
# FRONTEND DEPENDENCIES
# ============================================================================

echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}FRONTEND DEPENDENCIES${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

if [ ! -d "$FRONTEND_DIR" ]; then
    error "Frontend directory not found: $FRONTEND_DIR"
else
    cd "$FRONTEND_DIR"
    
    # Check package.json
    log "Checking package.json..."
    if [ -f "package.json" ]; then
        success "package.json found"
    else
        error "package.json not found"
    fi
    
    # Check package-lock.json
    log "Checking package-lock.json..."
    if [ -f "package-lock.json" ]; then
        success "package-lock.json found"
    else
        warning "package-lock.json not found"
    fi
    
    # Check node_modules
    log "Checking node_modules..."
    if [ -d "node_modules" ]; then
        MODULE_COUNT=$(find node_modules -maxdepth 1 -type d 2>/dev/null | wc -l)
        success "node_modules directory exists ($MODULE_COUNT top-level modules)"
        
        # Check critical dependencies
        log "Checking critical frontend dependencies..."
        CRITICAL_DEPS=("react" "react-dom" "react-router-dom" "vite" "@vitejs/plugin-react")
        for DEP in "${CRITICAL_DEPS[@]}"; do
            if [ -d "node_modules/$DEP" ]; then
                VERSION=$(node -e "try { console.log(require('./node_modules/$DEP/package.json').version); } catch(e) { console.log('unknown'); }" 2>/dev/null || echo "unknown")
                success "  ✓ $DEP@$VERSION"
            else
                error "  ✗ $DEP missing"
            fi
        done
    else
        error "node_modules directory not found - dependencies not installed"
    fi
    
    # Check build directory
    log "Checking build output..."
    if [ -d "dist" ]; then
        if [ -z "$(ls -A dist 2>/dev/null)" ]; then
            warning "Build directory exists but is empty"
        else
            BUILD_SIZE=$(du -sh dist 2>/dev/null | cut -f1)
            FILE_COUNT=$(find dist -type f 2>/dev/null | wc -l)
            success "Build directory exists (Size: $BUILD_SIZE, Files: $FILE_COUNT)"
        fi
    else
        warning "Build directory (dist) not found - frontend needs to be built"
    fi
    
    # Check if npm can list packages
    log "Verifying npm package installation..."
    if npm list --depth=0 &> /dev/null; then
        INSTALLED_COUNT=$(npm list --depth=0 2>/dev/null | grep -c "├──" || echo "0")
        info "Found $INSTALLED_COUNT installed packages"
    else
        warning "npm list command had issues"
    fi
fi

echo ""

# ============================================================================
# BACKEND DEPENDENCIES
# ============================================================================

echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}BACKEND DEPENDENCIES${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

cd "$PROJECT_ROOT"

# Check requirements.txt
log "Checking requirements.txt..."
if [ -f "requirements.txt" ]; then
    success "requirements.txt found"
    REQ_COUNT=$(wc -l < requirements.txt | tr -d ' ')
    info "Found $REQ_COUNT requirements"
else
    warning "requirements.txt not found in root"
    
    # Check backend directory
    if [ -d "$BACKEND_DIR" ] && [ -f "$BACKEND_DIR/requirements.txt" ]; then
        success "requirements.txt found in backend directory"
        REQ_COUNT=$(wc -l < "$BACKEND_DIR/requirements.txt" | tr -d ' ')
        info "Found $REQ_COUNT requirements"
    fi
fi

# Check virtual environment
log "Checking Python virtual environment..."
if [ -d "venv" ]; then
    success "Virtual environment (venv) found"
    
    # Check if venv is activated or can be activated
    if [ -f "venv/bin/activate" ]; then
        success "Virtual environment is valid"
        
        # Check critical Python packages
        log "Checking critical Python packages..."
        source venv/bin/activate
        
        CRITICAL_PYTHON_DEPS=("flask" "gunicorn" "psycopg2" "redis" "stripe")
        for DEP in "${CRITICAL_PYTHON_DEPS[@]}"; do
            if python3 -c "import $DEP" 2>/dev/null; then
                VERSION=$(python3 -c "import $DEP; print(getattr($DEP, '__version__', 'unknown'))" 2>/dev/null || echo "installed")
                success "  ✓ $DEP@$VERSION"
            else
                error "  ✗ $DEP not installed"
            fi
        done
        
        deactivate
    else
        error "Virtual environment is invalid"
    fi
else
    warning "Virtual environment (venv) not found"
    
    # Check if using system Python packages
    log "Checking system Python packages..."
    if python3 -c "import flask" 2>/dev/null; then
        warning "Flask found in system Python (consider using virtual environment)"
    else
        error "Flask not found (needs virtual environment or system installation)"
    fi
fi

# Check backend application files
log "Checking backend application structure..."
if [ -d "$BACKEND_DIR" ]; then
    success "Backend directory found: $BACKEND_DIR"
    
    # Check for main app file
    if [ -f "$BACKEND_DIR/app.py" ] || [ -f "app.py" ]; then
        success "Main application file found"
    else
        warning "Main application file (app.py) not found"
    fi
else
    warning "Backend directory not found: $BACKEND_DIR"
fi

echo ""

# ============================================================================
# SERVICE STATUS
# ============================================================================

echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}SERVICE STATUS${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check mingus-backend service
log "Checking mingus-backend service..."
if systemctl list-unit-files | grep -q mingus-backend; then
    if systemctl is-active --quiet mingus-backend 2>/dev/null; then
        success "mingus-backend service is running"
    else
        error "mingus-backend service exists but is not running"
    fi
else
    warning "mingus-backend service not found"
fi

# Check nginx service
log "Checking nginx service..."
if systemctl is-active --quiet nginx 2>/dev/null; then
    success "nginx service is running"
else
    error "nginx service is not running"
fi

# Check PostgreSQL service
log "Checking PostgreSQL service..."
if systemctl is-active --quiet postgresql 2>/dev/null || systemctl is-active --quiet postgresql@*-main 2>/dev/null; then
    success "PostgreSQL service is running"
else
    warning "PostgreSQL service is not running (may be using remote database)"
fi

# Check Redis service
log "Checking Redis service..."
if systemctl is-active --quiet redis 2>/dev/null || systemctl is-active --quiet redis-server 2>/dev/null; then
    success "Redis service is running"
else
    warning "Redis service is not running (may be using remote Redis)"
fi

echo ""

# ============================================================================
# DISK SPACE AND RESOURCES
# ============================================================================

echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}SYSTEM RESOURCES${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check disk space
log "Checking disk space..."
df -h / | tail -1 | awk '{print "Disk usage: " $5 " used (" $3 " / " $2 ")"}'
USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$USAGE" -lt 80 ]; then
    success "Disk space is adequate"
elif [ "$USAGE" -lt 90 ]; then
    warning "Disk space is getting low ($USAGE% used)"
else
    error "Disk space is critically low ($USAGE% used)"
fi

# Check memory
log "Checking memory..."
MEM_INFO=$(free -h | grep Mem)
MEM_TOTAL=$(echo "$MEM_INFO" | awk '{print $2}')
MEM_AVAIL=$(echo "$MEM_INFO" | awk '{print $7}')
info "Memory: $MEM_AVAIL available of $MEM_TOTAL total"

echo ""

# ============================================================================
# SUMMARY
# ============================================================================

echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  Verification Summary                                         ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${GREEN}✅ Passed:${NC} $PASSED"
echo -e "  ${RED}❌ Failed:${NC} $FAILED"
echo -e "  ${YELLOW}⚠️  Warnings:${NC} $WARNINGS"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All critical checks passed! All dependencies appear to be properly installed.${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Ensure services are running: sudo systemctl status mingus-backend nginx"
    echo "  2. Verify application is accessible: curl https://mingusapp.com"
    echo "  3. Check logs if needed: sudo journalctl -u mingus-backend -f"
    exit 0
else
    echo -e "${RED}❌ Some critical checks failed. Please review the errors above.${NC}"
    echo ""
    echo "Common fixes:"
    echo "  Frontend: cd frontend && npm install && npm run build"
    echo "  Backend: source venv/bin/activate && pip install -r requirements.txt"
    echo "  Services: sudo systemctl start mingus-backend nginx"
    exit 1
fi
