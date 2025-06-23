#!/bin/bash

# Mingus Application - Onboarding Tests Runner
# This script helps run the Cypress onboarding workflow tests

set -e

echo "🧪 Mingus Application - Onboarding Tests Runner"
echo "================================================"

# Check if Flask app is running
echo "🔍 Checking if Flask app is running on port 5002..."
if ! curl -s http://localhost:5002/api/auth/check-auth > /dev/null 2>&1; then
    echo "❌ Flask app is not running on port 5002"
    echo "Please start the Flask application first:"
    echo "   python app.py"
    exit 1
fi
echo "✅ Flask app is running"

# Check if we're in the right directory
if [ ! -f "cypress/package.json" ]; then
    echo "❌ Please run this script from the project root directory"
    exit 1
fi

# Navigate to cypress directory
cd cypress

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing Cypress dependencies..."
    npm install
fi

# Function to run tests
run_tests() {
    local test_type=$1
    local headed=$2
    
    echo ""
    echo "🚀 Running $test_type tests..."
    
    if [ "$headed" = "true" ]; then
        echo "🌐 Opening browser window..."
        npm run test:onboarding:headed
    else
        echo "🖥️  Running in headless mode..."
        npm run test:onboarding
    fi
}

# Parse command line arguments
HEADED=false
TEST_TYPE="onboarding"

while [[ $# -gt 0 ]]; do
    case $1 in
        --headed)
            HEADED=true
            shift
            ;;
        --complete)
            TEST_TYPE="complete"
            shift
            ;;
        --all)
            TEST_TYPE="all"
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --headed     Run tests with browser window visible"
            echo "  --complete   Run complete onboarding workflow tests"
            echo "  --all        Run all test suites"
            echo "  --help       Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                    # Run basic onboarding tests (headless)"
            echo "  $0 --headed           # Run basic onboarding tests (headed)"
            echo "  $0 --complete         # Run complete onboarding tests"
            echo "  $0 --complete --headed # Run complete tests with browser"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Run appropriate tests
case $TEST_TYPE in
    "onboarding")
        run_tests "basic onboarding" $HEADED
        ;;
    "complete")
        if [ "$headed" = "true" ]; then
            echo "🌐 Running complete onboarding tests with browser..."
            npm run test:complete-onboarding -- --headed
        else
            echo "🖥️  Running complete onboarding tests..."
            npm run test:complete-onboarding
        fi
        ;;
    "all")
        if [ "$headed" = "true" ]; then
            echo "🌐 Running all tests with browser..."
            npm run test:all -- --headed
        else
            echo "🖥️  Running all tests..."
            npm run test:all
        fi
        ;;
esac

echo ""
echo "✅ Tests completed!"
echo ""
echo "📁 Test results:"
echo "   - Videos: cypress/videos/"
echo "   - Screenshots: cypress/screenshots/"
echo ""
echo "🔗 To view test results interactively:"
echo "   cd cypress && npm run cypress:open" 