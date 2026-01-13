#!/bin/bash
# ============================================================================
# Mingus Application - Service Health Check with Auto-Restart
# Checks service health and restarts if unhealthy
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Load environment
if [ -f "$PROJECT_ROOT/.env.production" ]; then
    source "$PROJECT_ROOT/.env.production"
fi

BACKEND_URL="${BACKEND_URL:-http://localhost:5001}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost:3000}"
AUTO_RESTART="${AUTO_RESTART:-true}"

check_service_status() {
    local service=$1
    
    if systemctl is-active --quiet "$service" 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

check_health_endpoint() {
    local url=$1
    local timeout=${2:-5}
    
    if curl -f -s --max-time "$timeout" "$url" > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

restart_service() {
    local service=$1
    
    echo -e "${YELLOW}Restarting $service...${NC}"
    if sudo systemctl restart "$service"; then
        sleep 3
        if check_service_status "$service"; then
            echo -e "${GREEN}✅ $service restarted successfully${NC}"
            return 0
        else
            echo -e "${RED}❌ $service restart failed${NC}"
            return 1
        fi
    else
        echo -e "${RED}❌ Failed to restart $service${NC}"
        return 1
    fi
}

check_backend() {
    echo -n "Checking backend service... "
    
    # Check if service is running
    if ! check_service_status "mingus-backend"; then
        echo -e "${RED}❌ NOT RUNNING${NC}"
        if [ "$AUTO_RESTART" = "true" ]; then
            restart_service "mingus-backend"
        fi
        return 1
    fi
    
    # Check health endpoint
    if ! check_health_endpoint "$BACKEND_URL/health"; then
        echo -e "${YELLOW}⚠️  RUNNING BUT UNHEALTHY${NC}"
        if [ "$AUTO_RESTART" = "true" ]; then
            echo "Health check failed, attempting restart..."
            restart_service "mingus-backend"
        fi
        return 1
    fi
    
    echo -e "${GREEN}✅ HEALTHY${NC}"
    return 0
}

check_frontend() {
    echo -n "Checking frontend service... "
    
    # Check if service is running
    if ! check_service_status "mingus-frontend"; then
        echo -e "${RED}❌ NOT RUNNING${NC}"
        if [ "$AUTO_RESTART" = "true" ]; then
            restart_service "mingus-frontend"
        fi
        return 1
    fi
    
    # Check if frontend is accessible
    if ! check_health_endpoint "$FRONTEND_URL"; then
        echo -e "${YELLOW}⚠️  RUNNING BUT INACCESSIBLE${NC}"
        if [ "$AUTO_RESTART" = "true" ]; then
            echo "Frontend check failed, attempting restart..."
            restart_service "mingus-frontend"
        fi
        return 1
    fi
    
    echo -e "${GREEN}✅ HEALTHY${NC}"
    return 0
}

main() {
    echo -e "${BLUE}Mingus Application Service Health Check${NC}"
    echo "=========================================="
    echo ""
    
    FAILED=0
    
    check_backend || FAILED=$((FAILED + 1))
    echo ""
    check_frontend || FAILED=$((FAILED + 1))
    
    echo ""
    echo "=========================================="
    
    if [ $FAILED -eq 0 ]; then
        echo -e "${GREEN}✅ All services are healthy${NC}"
        exit 0
    else
        echo -e "${YELLOW}⚠️  $FAILED service(s) had issues${NC}"
        exit 1
    fi
}

# Run with auto-restart disabled
if [ "$1" = "--no-restart" ]; then
    AUTO_RESTART=false
fi

main
