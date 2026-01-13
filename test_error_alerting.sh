#!/bin/bash
# Quick test script for error monitoring and alerting

echo "=========================================="
echo "Error Monitoring and Alerting Test"
echo "=========================================="
echo ""

BASE_URL="${1:-http://localhost:5001}"

echo "Testing against: $BASE_URL"
echo ""

# Check if server is running
echo "1. Checking server health..."
if curl -s -f "$BASE_URL/health" > /dev/null; then
    echo "✅ Server is running"
else
    echo "❌ Server is not running. Please start the Flask app first."
    exit 1
fi
echo ""

# Test error statistics
echo "2. Testing error statistics endpoint..."
STATS=$(curl -s "$BASE_URL/api/errors/stats?hours=24")
if [ $? -eq 0 ]; then
    echo "✅ Error statistics endpoint accessible"
    TOTAL=$(echo "$STATS" | grep -o '"total":[0-9]*' | grep -o '[0-9]*' | head -1)
    echo "   Total errors (24h): ${TOTAL:-0}"
else
    echo "❌ Error statistics endpoint failed"
fi
echo ""

# Test error list
echo "3. Testing error list endpoint..."
ERRORS=$(curl -s "$BASE_URL/api/errors?limit=5")
if [ $? -eq 0 ]; then
    echo "✅ Error list endpoint accessible"
    COUNT=$(echo "$ERRORS" | grep -o '"count":[0-9]*' | grep -o '[0-9]*' | head -1)
    echo "   Errors retrieved: ${COUNT:-0}"
else
    echo "❌ Error list endpoint failed"
fi
echo ""

# Test error health
echo "4. Testing error health endpoint..."
HEALTH=$(curl -s "$BASE_URL/api/errors/health")
if [ $? -eq 0 ]; then
    echo "✅ Error health endpoint accessible"
    STATUS=$(echo "$HEALTH" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
    echo "   Error health status: ${STATUS:-unknown}"
else
    echo "❌ Error health endpoint failed"
fi
echo ""

# Test alerts
echo "5. Testing alerts endpoint..."
ALERTS=$(curl -s "$BASE_URL/api/dashboard/alerts")
if [ $? -eq 0 ]; then
    echo "✅ Alerts endpoint accessible"
    ALERT_COUNT=$(echo "$ALERTS" | grep -o '"count":[0-9]*' | grep -o '[0-9]*' | head -1)
    echo "   Active alerts: ${ALERT_COUNT:-0}"
else
    echo "❌ Alerts endpoint failed"
fi
echo ""

# Generate test errors
echo "6. Generating test errors..."
for i in {1..5}; do
    curl -s "$BASE_URL/api/test-error-$i" > /dev/null 2>&1
done
sleep 2
echo "✅ Test errors generated"
echo ""

# Check error statistics after generation
echo "7. Checking error statistics after test..."
STATS_AFTER=$(curl -s "$BASE_URL/api/errors/stats?hours=1")
TOTAL_AFTER=$(echo "$STATS_AFTER" | grep -o '"total":[0-9]*' | grep -o '[0-9]*' | head -1)
echo "   Total errors (last hour): ${TOTAL_AFTER:-0}"
echo ""

echo "=========================================="
echo "Test Complete"
echo "=========================================="
echo ""
echo "View error statistics:"
echo "  curl $BASE_URL/api/errors/stats?hours=24 | jq"
echo ""
echo "View active alerts:"
echo "  curl $BASE_URL/api/dashboard/alerts | jq"
echo ""
echo "View error health:"
echo "  curl $BASE_URL/api/errors/health | jq"
echo ""
