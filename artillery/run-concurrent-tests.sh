#!/bin/bash
# Run concurrent user scenario tests

set -e

BASE_URL="${1:-http://localhost:5001}"
ARTILLERY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS_DIR="${ARTILLERY_DIR}/results"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "=========================================="
echo "Concurrent User Scenario Tests"
echo "=========================================="
echo ""
echo "Target: $BASE_URL"
echo "Results: $RESULTS_DIR"
echo ""

# Check server
echo "Checking server..."
if curl -s -f "${BASE_URL}/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Server is running${NC}"
else
    echo -e "${RED}❌ Server is not running!${NC}"
    echo "Please start Flask app: export FLASK_PORT=5001 && python app.py"
    exit 1
fi

# Check Artillery
if ! command -v artillery &> /dev/null && [ ! -f "${ARTILLERY_DIR}/node_modules/.bin/artillery" ]; then
    ARTILLERY_CMD="npx artillery"
else
    if command -v artillery &> /dev/null; then
        ARTILLERY_CMD="artillery"
    else
        ARTILLERY_CMD="${ARTILLERY_DIR}/node_modules/.bin/artillery"
    fi
fi

mkdir -p "$RESULTS_DIR"

echo ""
echo "=========================================="
echo "Test 1: Concurrent User Levels"
echo "=========================================="
echo ""

$ARTILLERY_CMD run \
    --target "$BASE_URL" \
    --output "${RESULTS_DIR}/concurrent-${TIMESTAMP}.json" \
    "${ARTILLERY_DIR}/artillery-concurrent.yml" \
    2>&1 | tee "${RESULTS_DIR}/concurrent-${TIMESTAMP}.txt"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Concurrent test completed${NC}"
    $ARTILLERY_CMD report "${RESULTS_DIR}/concurrent-${TIMESTAMP}.json" \
        > "${RESULTS_DIR}/concurrent-${TIMESTAMP}-report.html" 2>&1 || true
else
    echo -e "${RED}❌ Concurrent test failed${NC}"
fi

echo ""
echo "=========================================="
echo "Test 2: Concurrent User Ramp-Up"
echo "=========================================="
echo ""

$ARTILLERY_CMD run \
    --target "$BASE_URL" \
    --output "${RESULTS_DIR}/concurrent-ramp-${TIMESTAMP}.json" \
    "${ARTILLERY_DIR}/artillery-concurrent-ramp.yml" \
    2>&1 | tee "${RESULTS_DIR}/concurrent-ramp-${TIMESTAMP}.txt"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Ramp-up test completed${NC}"
    $ARTILLERY_CMD report "${RESULTS_DIR}/concurrent-ramp-${TIMESTAMP}.json" \
        > "${RESULTS_DIR}/concurrent-ramp-${TIMESTAMP}-report.html" 2>&1 || true
else
    echo -e "${RED}❌ Ramp-up test failed${NC}"
fi

echo ""
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo ""
echo "Results saved to: $RESULTS_DIR"
echo ""
echo "Files:"
echo "  - Concurrent: ${RESULTS_DIR}/concurrent-${TIMESTAMP}.json"
echo "  - Concurrent Ramp: ${RESULTS_DIR}/concurrent-ramp-${TIMESTAMP}.json"
echo ""
echo "Reports:"
echo "  - Concurrent: ${RESULTS_DIR}/concurrent-${TIMESTAMP}-report.html"
echo "  - Concurrent Ramp: ${RESULTS_DIR}/concurrent-ramp-${TIMESTAMP}-report.html"
echo ""
