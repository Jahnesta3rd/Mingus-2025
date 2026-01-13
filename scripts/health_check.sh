#!/bin/bash
# ============================================================================
# Mingus Application - Health Check Script
# Checks the health of all application components
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

check_service() {
    local name=$1
    local url=$2
    local expected_status=${3:-200}
    
    echo -n "Checking $name... "
    
    if response=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$url" 2>/dev/null); then
        if [ "$response" = "$expected_status" ]; then
            echo -e "${GREEN}✅ OK${NC} (HTTP $response)"
            return 0
        else
            echo -e "${YELLOW}⚠️  WARNING${NC} (HTTP $response, expected $expected_status)"
            return 1
        fi
    else
        echo -e "${RED}❌ FAILED${NC} (Connection failed)"
        return 1
    fi
}

check_database() {
    echo -n "Checking database... "
    
    DB_FILE="$PROJECT_ROOT/assessments.db"
    if [ -f "$DB_FILE" ]; then
        if python3 -c "
import sqlite3
conn = sqlite3.connect('$DB_FILE')
cursor = conn.cursor()
cursor.execute('SELECT 1')
conn.close()
" 2>/dev/null; then
            echo -e "${GREEN}✅ OK${NC}"
            return 0
        else
            echo -e "${RED}❌ FAILED${NC} (Cannot connect)"
            return 1
        fi
    else
        echo -e "${YELLOW}⚠️  WARNING${NC} (Database file not found)"
        return 1
    fi
}

check_disk_space() {
    echo -n "Checking disk space... "
    
    USAGE=$(df -h "$PROJECT_ROOT" | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ "$USAGE" -lt 80 ]; then
        echo -e "${GREEN}✅ OK${NC} ($USAGE% used)"
        return 0
    elif [ "$USAGE" -lt 90 ]; then
        echo -e "${YELLOW}⚠️  WARNING${NC} ($USAGE% used)"
        return 1
    else
        echo -e "${RED}❌ CRITICAL${NC} ($USAGE% used)"
        return 1
    fi
}

check_process() {
    local name=$1
    local pattern=$2
    
    echo -n "Checking $name process... "
    
    if pgrep -f "$pattern" > /dev/null; then
        echo -e "${GREEN}✅ RUNNING${NC}"
        return 0
    else
        echo -e "${RED}❌ NOT RUNNING${NC}"
        return 1
    fi
}

echo -e "${BLUE}Mingus Application Health Check${NC}"
echo "=================================="
echo ""

FAILED=0

# Check services
check_service "Backend API" "$BACKEND_URL/health" || FAILED=$((FAILED + 1))
check_service "Frontend" "$FRONTEND_URL" || FAILED=$((FAILED + 1))

# Check database
check_database || FAILED=$((FAILED + 1))

# Check processes
check_process "Backend" "gunicorn.*app:app" || check_process "Backend" "python.*app.py" || FAILED=$((FAILED + 1))
check_process "Frontend" "node.*vite" || check_process "Frontend" "npm.*start" || FAILED=$((FAILED + 1))

# Check disk space
check_disk_space || FAILED=$((FAILED + 1))

echo ""
echo "=================================="
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All health checks passed${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️  $FAILED check(s) failed${NC}"
    exit 1
fi
