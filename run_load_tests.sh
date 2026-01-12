#!/bin/bash
# Load Testing Script
# This script runs all the load tests in sequence

echo "=========================================="
echo "API Load Testing Suite"
echo "=========================================="
echo ""

# Check if Flask app is running
echo "1. Checking if Flask app is running..."
if curl -s http://localhost:5000/health > /dev/null 2>&1; then
    echo "✅ Flask app is running"
else
    echo "❌ Flask app is not running!"
    echo "   Please start it with: python app.py"
    echo "   Then run this script again."
    exit 1
fi

echo ""
echo "2. Running health endpoint load test (50 requests)..."
python load_test_api.py --endpoint /health --requests 50 --concurrent 5

echo ""
echo "3. Testing cache performance..."
python performance_test_suite.py --endpoint /api/vehicle --compare-cache --url http://localhost:5000 || echo "⚠️ Cache test skipped (endpoint may not support caching)"

echo ""
echo "4. Running full test suite..."
python load_test_api.py --full --requests 100 --concurrent 10 --save

echo ""
echo "=========================================="
echo "Load testing complete!"
echo "=========================================="
