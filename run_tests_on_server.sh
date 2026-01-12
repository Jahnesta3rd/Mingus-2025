#!/bin/bash
# Script to run comprehensive tests on the Mingus test server
# Usage: ./run_tests_on_server.sh

set -e

echo "=========================================="
echo "Mingus Application - Server Test Runner"
echo "=========================================="
echo ""

# Server configuration
SERVER_HOST="mingus-test"
SERVER_USER="root"
SERVER_IP="64.225.16.241"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    case $status in
        "info")
            echo -e "${BLUE}ℹ${NC} $message"
            ;;
        "success")
            echo -e "${GREEN}✓${NC} $message"
            ;;
        "warning")
            echo -e "${YELLOW}⚠${NC} $message"
            ;;
        "error")
            echo -e "${RED}✗${NC} $message"
            ;;
    esac
}

# Check if SSH connection works
print_status "info" "Checking SSH connection to server..."
if ssh -o ConnectTimeout=5 -o BatchMode=yes $SERVER_HOST "echo 'Connection successful'" 2>/dev/null; then
    print_status "success" "SSH connection to $SERVER_HOST successful"
else
    print_status "error" "Cannot connect to server. Please check:"
    echo "  1. SSH config is set up for 'mingus-test'"
    echo "  2. Server is accessible at $SERVER_IP"
    echo "  3. SSH key is properly configured"
    exit 1
fi

echo ""
print_status "info" "Installing Python test dependencies on server..."

# Install Python dependencies on server
ssh $SERVER_HOST << 'ENDSSH'
    echo "Updating package list..."
    apt-get update -qq > /dev/null 2>&1 || true
    
    echo "Installing Python dependencies..."
    pip3 install --quiet --upgrade pip 2>/dev/null || python3 -m pip install --quiet --upgrade pip 2>/dev/null || true
    
    echo "Installing test packages..."
    pip3 install --quiet requests psycopg2-binary redis stripe 2>/dev/null || \
    python3 -m pip install --quiet requests psycopg2-binary redis stripe 2>/dev/null || true
    
    echo "Dependencies installed"
ENDSSH

print_status "success" "Python dependencies installed"

echo ""
print_status "info" "Setting up test environment on server..."

# Create test script on server
ssh $SERVER_HOST << 'ENDSSH'
    cd /root || cd ~
    
    # Create test directory if it doesn't exist
    mkdir -p /tmp/mingus_tests
    
    # Set environment variables
    export BASE_URL=http://localhost:5000
    export DB_HOST=localhost
    export DB_PORT=5432
    export DB_NAME=mingus_db
    export DB_USER=mingus_user
    export DB_PASSWORD='MingusApp2026!'
    export REDIS_HOST=localhost
    export REDIS_PORT=6379
    # Note: REDIS_PASSWORD should be set if Redis requires authentication
    # export REDIS_PASSWORD='your_redis_password'
    
    # STRIPE keys - these should be set from your environment
    # export STRIPE_TEST_SECRET_KEY=sk_test_...
    # export STRIPE_TEST_PUBLISHABLE_KEY=pk_test_...
    
    echo "Environment variables set"
ENDSSH

echo ""
print_status "info" "Uploading test script to server..."

# Check if comprehensive_testing_protocol.py exists locally
if [ -f "comprehensive_testing_protocol.py" ]; then
    print_status "info" "Uploading comprehensive_testing_protocol.py to server..."
    scp comprehensive_testing_protocol.py $SERVER_HOST:/tmp/mingus_tests/ > /dev/null 2>&1
    print_status "success" "Test script uploaded"
else
    print_status "warning" "comprehensive_testing_protocol.py not found locally"
    print_status "info" "Will use existing script on server if available"
fi

echo ""
print_status "info" "Running comprehensive tests on server..."
echo ""

# Run tests on server
ssh $SERVER_HOST << 'ENDSSH'
    cd /tmp/mingus_tests || cd ~
    
    # Set environment variables
    export BASE_URL=http://localhost:5000
    export DB_HOST=localhost
    export DB_PORT=5432
    export DB_NAME=mingus_db
    export DB_USER=mingus_user
    export DB_PASSWORD='MingusApp2026!'
    export REDIS_HOST=localhost
    export REDIS_PORT=6379
    
    # Find and run the test script
    if [ -f "/tmp/mingus_tests/comprehensive_testing_protocol.py" ]; then
        python3 /tmp/mingus_tests/comprehensive_testing_protocol.py
    elif [ -f "comprehensive_testing_protocol.py" ]; then
        python3 comprehensive_testing_protocol.py
    elif [ -f "/root/comprehensive_testing_protocol.py" ]; then
        python3 /root/comprehensive_testing_protocol.py
    else
        echo "Error: comprehensive_testing_protocol.py not found"
        echo "Please ensure the test script is available on the server"
        exit 1
    fi
ENDSSH

TEST_EXIT_CODE=$?

echo ""
if [ $TEST_EXIT_CODE -eq 0 ]; then
    print_status "success" "Tests completed successfully!"
else
    print_status "error" "Tests completed with exit code: $TEST_EXIT_CODE"
fi

echo ""
print_status "info" "Retrieving test results from server..."

# Try to retrieve test results
ssh $SERVER_HOST << 'ENDSSH' 2>/dev/null || true
    cd /tmp/mingus_tests || cd ~ || cd /root
    if ls test_results_*.json 1> /dev/null 2>&1; then
        LATEST_RESULT=$(ls -t test_results_*.json | head -1)
        echo "Latest test result: $LATEST_RESULT"
        cat "$LATEST_RESULT"
    fi
ENDSSH

echo ""
print_status "info" "Test execution complete!"
echo ""
echo "To view detailed results, SSH into the server and check:"
echo "  - Test output above"
echo "  - JSON results file: /tmp/mingus_tests/test_results_*.json"
echo ""
echo "To SSH into server:"
echo "  ssh $SERVER_HOST"
echo ""

exit $TEST_EXIT_CODE
