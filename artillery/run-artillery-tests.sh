#!/bin/bash
# Artillery Load Testing Script
# Runs Artillery load tests with different scenarios

set -e

BASE_URL="${1:-http://localhost:5001}"
ARTILLERY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS_DIR="${ARTILLERY_DIR}/results"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "=========================================="
echo "Artillery Load Testing Suite"
echo "=========================================="
echo ""
echo "Target: $BASE_URL"
echo "Results: $RESULTS_DIR"
echo ""

# Check if Artillery is installed (local or global)
if ! command -v artillery &> /dev/null && [ ! -f "${ARTILLERY_DIR}/node_modules/.bin/artillery" ]; then
    echo -e "${YELLOW}⚠️  Artillery not found globally, using npx${NC}"
    ARTILLERY_CMD="npx artillery"
else
    if command -v artillery &> /dev/null; then
        ARTILLERY_CMD="artillery"
    else
        ARTILLERY_CMD="${ARTILLERY_DIR}/node_modules/.bin/artillery"
    fi
fi

# Check if server is running
echo "Checking if server is running..."
if curl -s -f "${BASE_URL}/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Server is running${NC}"
else
    echo -e "${RED}❌ Server is not running!${NC}"
    echo "Please start the Flask app first:"
    echo "  export FLASK_PORT=5001"
    echo "  python app.py"
    exit 1
fi

# Create results directory
mkdir -p "$RESULTS_DIR"

echo ""
echo "=========================================="
echo "Running Load Tests"
echo "=========================================="
echo ""

# Test 1: Standard Load Test
echo -e "${YELLOW}Test 1: Standard Load Test${NC}"
$ARTILLERY_CMD run \
    --target "$BASE_URL" \
    --output "${RESULTS_DIR}/standard-${TIMESTAMP}.json" \
    "${ARTILLERY_DIR}/artillery-config.yml" \
    > "${RESULTS_DIR}/standard-${TIMESTAMP}.txt" 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Standard load test completed${NC}"
    $ARTILLERY_CMD report "${RESULTS_DIR}/standard-${TIMESTAMP}.json" \
        > "${RESULTS_DIR}/standard-${TIMESTAMP}-report.html" 2>&1 || true
else
    echo -e "${RED}❌ Standard load test failed${NC}"
fi

echo ""

# Test 2: Stress Test
echo -e "${YELLOW}Test 2: Stress Test${NC}"
$ARTILLERY_CMD run \
    --target "$BASE_URL" \
    --output "${RESULTS_DIR}/stress-${TIMESTAMP}.json" \
    "${ARTILLERY_DIR}/artillery-stress.yml" \
    > "${RESULTS_DIR}/stress-${TIMESTAMP}.txt" 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Stress test completed${NC}"
    $ARTILLERY_CMD report "${RESULTS_DIR}/stress-${TIMESTAMP}.json" \
        > "${RESULTS_DIR}/stress-${TIMESTAMP}-report.html" 2>&1 || true
else
    echo -e "${RED}❌ Stress test failed${NC}"
fi

echo ""

# Test 3: Spike Test
echo -e "${YELLOW}Test 3: Spike Test${NC}"
$ARTILLERY_CMD run \
    --target "$BASE_URL" \
    --output "${RESULTS_DIR}/spike-${TIMESTAMP}.json" \
    "${ARTILLERY_DIR}/artillery-spike.yml" \
    > "${RESULTS_DIR}/spike-${TIMESTAMP}.txt" 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Spike test completed${NC}"
    $ARTILLERY_CMD report "${RESULTS_DIR}/spike-${TIMESTAMP}.json" \
        > "${RESULTS_DIR}/spike-${TIMESTAMP}-report.html" 2>&1 || true
else
    echo -e "${RED}❌ Spike test failed${NC}"
fi

echo ""
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo ""
echo "Results saved to: $RESULTS_DIR"
echo ""
echo "View reports:"
echo "  - Standard: ${RESULTS_DIR}/standard-${TIMESTAMP}-report.html"
echo "  - Stress: ${RESULTS_DIR}/stress-${TIMESTAMP}-report.html"
echo "  - Spike: ${RESULTS_DIR}/spike-${TIMESTAMP}-report.html"
echo ""
echo "View JSON results:"
echo "  - Standard: ${RESULTS_DIR}/standard-${TIMESTAMP}.json"
echo "  - Stress: ${RESULTS_DIR}/stress-${TIMESTAMP}.json"
echo "  - Spike: ${RESULTS_DIR}/spike-${TIMESTAMP}.json"
echo ""
