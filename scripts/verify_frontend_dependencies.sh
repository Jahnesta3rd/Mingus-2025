#!/bin/bash
# ============================================================================
# Mingus Application - Frontend Dependencies Verification Script
# Verifies that all frontend dependencies are properly installed on DigitalOcean
# ============================================================================

set -e
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

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
echo -e "${CYAN}║  Frontend Dependencies Verification for DigitalOcean        ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

cd "$FRONTEND_DIR" || {
    error "Frontend directory not found: $FRONTEND_DIR"
    exit 1
}

log "Verifying frontend dependencies in: $FRONTEND_DIR"
echo ""

# 1. Check if package.json exists
log "Step 1: Checking package.json..."
if [ -f "package.json" ]; then
    success "package.json found"
else
    error "package.json not found"
    exit 1
fi

# 2. Check Node.js and npm versions
log "Step 2: Checking Node.js and npm versions..."
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    success "Node.js installed: $NODE_VERSION"
    
    # Check if Node.js version is 18+ (required for React 18)
    NODE_MAJOR=$(echo "$NODE_VERSION" | sed 's/v//' | cut -d. -f1)
    if [ "$NODE_MAJOR" -ge 18 ]; then
        success "Node.js version is compatible (>= 18.x)"
    else
        warning "Node.js version may be too old (recommended: >= 18.x)"
    fi
else
    error "Node.js not installed"
    exit 1
fi

if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm --version)
    success "npm installed: $NPM_VERSION"
else
    error "npm not installed"
    exit 1
fi
echo ""

# 3. Check if node_modules exists
log "Step 3: Checking node_modules directory..."
if [ -d "node_modules" ]; then
    success "node_modules directory exists"
    
    # Count installed packages
    MODULE_COUNT=$(find node_modules -maxdepth 1 -type d | wc -l)
    info "Found $MODULE_COUNT top-level modules in node_modules"
else
    error "node_modules directory not found - dependencies not installed"
    FAILED=1
fi
echo ""

# 4. Check if package-lock.json exists
log "Step 4: Checking package-lock.json..."
if [ -f "package-lock.json" ]; then
    success "package-lock.json found"
else
    warning "package-lock.json not found - using npm install may result in version mismatches"
fi
echo ""

# 5. Verify all production dependencies
log "Step 5: Verifying production dependencies..."
if [ -f "package.json" ] && [ -d "node_modules" ]; then
    # Extract dependencies from package.json
    DEPS=$(node -e "const pkg = require('./package.json'); const deps = {...(pkg.dependencies || {})}; console.log(Object.keys(deps).join(' '));" 2>/dev/null)
    
    MISSING_DEPS=()
    for DEP in $DEPS; do
        if [ ! -d "node_modules/$DEP" ]; then
            MISSING_DEPS+=("$DEP")
            error "Missing dependency: $DEP"
        else
            success "Dependency found: $DEP"
        fi
    done
    
    if [ ${#MISSING_DEPS[@]} -eq 0 ]; then
        success "All production dependencies are installed"
    else
        error "${#MISSING_DEPS[@]} production dependencies are missing"
    fi
else
    warning "Cannot verify dependencies - node_modules or package.json missing"
fi
echo ""

# 6. Check critical dependencies
log "Step 6: Checking critical dependencies..."
CRITICAL_DEPS=("react" "react-dom" "react-router-dom" "vite" "@vitejs/plugin-react")
for DEP in "${CRITICAL_DEPS[@]}"; do
    if [ -d "node_modules/$DEP" ]; then
        VERSION=$(node -e "try { console.log(require('./node_modules/$DEP/package.json').version); } catch(e) { console.log('unknown'); }" 2>/dev/null)
        success "Critical dependency found: $DEP@$VERSION"
    else
        error "Critical dependency missing: $DEP"
    fi
done
echo ""

# 7. Check if build directory exists
log "Step 7: Checking build output..."
if [ -d "dist" ]; then
    success "Build directory (dist) exists"
    
    if [ -z "$(ls -A dist 2>/dev/null)" ]; then
        warning "Build directory is empty - frontend may not be built"
    else
        BUILD_SIZE=$(du -sh dist 2>/dev/null | cut -f1)
        FILE_COUNT=$(find dist -type f 2>/dev/null | wc -l)
        success "Build directory contains files (Size: $BUILD_SIZE, Files: $FILE_COUNT)"
        
        # Check for critical build files
        if [ -f "dist/index.html" ]; then
            success "index.html found in build"
        else
            warning "index.html not found in build"
        fi
    fi
else
    warning "Build directory (dist) not found - frontend needs to be built"
fi
echo ""

# 8. Verify npm can list installed packages
log "Step 8: Verifying npm package listing..."
if npm list --depth=0 &> /dev/null; then
    success "npm can list installed packages"
    
    # Count installed vs expected
    INSTALLED_COUNT=$(npm list --depth=0 2>/dev/null | grep -c "├──" || echo "0")
    info "Found $INSTALLED_COUNT installed packages"
else
    warning "npm list command had issues (this may be normal)"
fi
echo ""

# 9. Check for common issues
log "Step 9: Checking for common issues..."

# Check for broken symlinks
BROKEN_LINKS=$(find node_modules -type l ! -exec test -e {} \; -print 2>/dev/null | wc -l)
if [ "$BROKEN_LINKS" -gt 0 ]; then
    warning "Found $BROKEN_LINKS broken symlinks in node_modules"
else
    success "No broken symlinks found"
fi

# Check disk space
AVAILABLE_SPACE=$(df -h "$FRONTEND_DIR" | awk 'NR==2 {print $4}')
info "Available disk space: $AVAILABLE_SPACE"
echo ""

# 10. Test if build would work
log "Step 10: Testing build capability..."
if [ -f "package.json" ] && command -v npm &> /dev/null; then
    # Check if vite is available
    if [ -f "node_modules/.bin/vite" ] || [ -f "node_modules/vite/bin/vite.js" ]; then
        success "Vite build tool is available"
    else
        error "Vite build tool not found"
    fi
    
    # Check if TypeScript is available (if used)
    if [ -f "tsconfig.json" ]; then
        if [ -f "node_modules/.bin/tsc" ] || [ -f "node_modules/typescript/bin/tsc" ]; then
            success "TypeScript compiler is available"
        else
            warning "TypeScript config found but compiler may not be installed"
        fi
    fi
else
    warning "Cannot test build capability"
fi
echo ""

# Summary
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
    echo -e "${GREEN}✅ All critical checks passed! Frontend dependencies appear to be properly installed.${NC}"
    echo ""
    echo "To ensure everything is up to date, run:"
    echo "  cd $FRONTEND_DIR"
    echo "  npm install"
    echo "  npm run build"
    exit 0
else
    echo -e "${RED}❌ Some checks failed. Please review the errors above.${NC}"
    echo ""
    echo "To fix dependency issues, run:"
    echo "  cd $FRONTEND_DIR"
    echo "  rm -rf node_modules package-lock.json"
    echo "  npm install"
    echo "  npm run build"
    exit 1
fi
