#!/bin/bash
# Start Flask app and run Artillery tests

set -e

echo "=========================================="
echo "Starting Flask App and Running Artillery Tests"
echo "=========================================="
echo ""

# Set port
export FLASK_PORT=5001

# Start Flask app in background
echo "1. Starting Flask app on port 5001..."
cd "$(dirname "$0")"
python app.py > flask.log 2>&1 &
FLASK_PID=$!
echo "   Flask app started (PID: $FLASK_PID)"
echo ""

# Wait for server to start
echo "2. Waiting for server to start..."
for i in {1..30}; do
    if curl -s -f http://localhost:5001/health > /dev/null 2>&1; then
        echo "   ✅ Server is running!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "   ❌ Server failed to start after 30 seconds"
        echo "   Check flask.log for errors:"
        tail -50 flask.log
        kill $FLASK_PID 2>/dev/null || true
        exit 1
    fi
    sleep 1
done
echo ""

# Run Artillery tests
echo "3. Running Artillery quick test..."
cd artillery
npx artillery run artillery-quick.yml --target http://localhost:5001
echo ""

echo "4. Running Artillery standard test..."
npx artillery run artillery-config.yml --target http://localhost:5001
echo ""

# Cleanup
echo "5. Stopping Flask app..."
kill $FLASK_PID 2>/dev/null || true
echo "   ✅ Done!"
echo ""

echo "=========================================="
echo "Tests Complete!"
echo "=========================================="
