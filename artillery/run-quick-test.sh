#!/bin/bash
# Quick Artillery Test Runner
# Runs a quick 30-second load test

set -e

BASE_URL="${1:-http://localhost:5001}"
ARTILLERY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================="
echo "Artillery Quick Load Test"
echo "=========================================="
echo ""
echo "Target: $BASE_URL"
echo ""

# Check if Artillery is installed (local or global)
if ! command -v artillery &> /dev/null && [ ! -f "${ARTILLERY_DIR}/node_modules/.bin/artillery" ]; then
    echo "⚠️  Artillery not found, using npx"
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
    echo "✅ Server is running"
else
    echo "❌ Server is not running!"
    echo "Please start the Flask app first:"
    echo "  export FLASK_PORT=5001"
    echo "  python app.py"
    exit 1
fi

echo ""
echo "Running quick load test (30 seconds)..."
echo ""

# Run quick test
$ARTILLERY_CMD run \
    --target "$BASE_URL" \
    "$ARTILLERY_DIR/artillery-quick.yml"

echo ""
echo "=========================================="
echo "Quick test complete!"
echo "=========================================="
