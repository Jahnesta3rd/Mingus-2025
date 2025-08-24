#!/bin/bash

# =====================================================
# MINGUS ARTICLE LIBRARY - TEST RUNNER
# =====================================================
# Script to run tests for the MINGUS application

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in a virtual environment
check_environment() {
    if [[ "$VIRTUAL_ENV" == "" ]]; then
        log_warning "Not in a virtual environment. Consider activating one."
    else
        log_info "Using virtual environment: $VIRTUAL_ENV"
    fi
}

# Check if pytest is installed
check_pytest() {
    if ! command -v pytest &> /dev/null; then
        log_error "pytest is not installed. Please install it first:"
        log_error "pip install pytest pytest-cov pytest-html"
        exit 1
    fi
}

# Run all tests
run_all_tests() {
    log_info "Running all tests..."
    pytest tests/ -v --tb=short
}

# Run integration tests
run_integration_tests() {
    log_info "Running integration tests..."
    pytest tests/test_integration.py -v --tb=short -m integration
}

# Run API tests
run_api_tests() {
    log_info "Running API tests..."
    pytest tests/ -v --tb=short -m api
}

# Run database tests
run_database_tests() {
    log_info "Running database tests..."
    pytest tests/ -v --tb=short -m database
}

# Run tests with coverage
run_tests_with_coverage() {
    log_info "Running tests with coverage..."
    pytest tests/ -v --cov=backend --cov-report=html --cov-report=term-missing
}

# Run tests and generate HTML report
run_tests_with_html_report() {
    log_info "Running tests with HTML report..."
    pytest tests/ -v --html=reports/test_report.html --self-contained-html
}

# Run specific test file
run_specific_test() {
    local test_file="$1"
    if [ -z "$test_file" ]; then
        log_error "Please specify a test file"
        exit 1
    fi
    
    if [ ! -f "$test_file" ]; then
        log_error "Test file not found: $test_file"
        exit 1
    fi
    
    log_info "Running specific test: $test_file"
    pytest "$test_file" -v --tb=short
}

# Run tests in parallel
run_parallel_tests() {
    log_info "Running tests in parallel..."
    pytest tests/ -v -n auto
}

# Run slow tests only
run_slow_tests() {
    log_info "Running slow tests..."
    pytest tests/ -v -m slow
}

# Run fast tests only (exclude slow)
run_fast_tests() {
    log_info "Running fast tests..."
    pytest tests/ -v -m "not slow"
}

# Clean up test artifacts
cleanup_tests() {
    log_info "Cleaning up test artifacts..."
    rm -rf .pytest_cache/
    rm -rf htmlcov/
    rm -rf reports/
    rm -rf .coverage
    find . -name "*.pyc" -delete
    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    log_success "Test artifacts cleaned up"
}

# Show test coverage
show_coverage() {
    if [ -f ".coverage" ]; then
        log_info "Showing coverage report..."
        coverage report
    else
        log_warning "No coverage data found. Run tests with coverage first."
    fi
}

# Open coverage report in browser
open_coverage_report() {
    if [ -d "htmlcov" ]; then
        log_info "Opening coverage report in browser..."
        if command -v open &> /dev/null; then
            open htmlcov/index.html
        elif command -v xdg-open &> /dev/null; then
            xdg-open htmlcov/index.html
        else
            log_info "Coverage report available at: htmlcov/index.html"
        fi
    else
        log_warning "No coverage report found. Run tests with coverage first."
    fi
}

# Run tests in Docker
run_docker_tests() {
    log_info "Running tests in Docker..."
    if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
        docker-compose -f docker-compose.dev.yml exec web python -m pytest tests/ -v
    else
        log_error "Docker or Docker Compose not available"
        exit 1
    fi
}

# Show test statistics
show_test_stats() {
    log_info "Test Statistics:"
    echo ""
    
    # Count test files
    test_files=$(find tests/ -name "test_*.py" | wc -l)
    echo "Test files: $test_files"
    
    # Count test functions
    test_functions=$(grep -r "def test_" tests/ | wc -l)
    echo "Test functions: $test_functions"
    
    # Show recent test results
    if [ -f "reports/test_report.html" ]; then
        echo "Latest test report: reports/test_report.html"
    fi
    
    if [ -d "htmlcov" ]; then
        echo "Coverage report: htmlcov/index.html"
    fi
}

# Main function
main() {
    case "${1:-help}" in
        "all")
            check_environment
            check_pytest
            run_all_tests
            ;;
        "integration")
            check_environment
            check_pytest
            run_integration_tests
            ;;
        "api")
            check_environment
            check_pytest
            run_api_tests
            ;;
        "database")
            check_environment
            check_pytest
            run_database_tests
            ;;
        "coverage")
            check_environment
            check_pytest
            run_tests_with_coverage
            ;;
        "html")
            check_environment
            check_pytest
            run_tests_with_html_report
            ;;
        "parallel")
            check_environment
            check_pytest
            run_parallel_tests
            ;;
        "slow")
            check_environment
            check_pytest
            run_slow_tests
            ;;
        "fast")
            check_environment
            check_pytest
            run_fast_tests
            ;;
        "docker")
            run_docker_tests
            ;;
        "clean")
            cleanup_tests
            ;;
        "show-coverage")
            show_coverage
            ;;
        "open-coverage")
            open_coverage_report
            ;;
        "stats")
            show_test_stats
            ;;
        "file")
            run_specific_test "$2"
            ;;
        "help"|*)
            echo "Usage: $0 {all|integration|api|database|coverage|html|parallel|slow|fast|docker|clean|show-coverage|open-coverage|stats|file|help}"
            echo ""
            echo "Commands:"
            echo "  all              - Run all tests"
            echo "  integration      - Run integration tests only"
            echo "  api              - Run API tests only"
            echo "  database         - Run database tests only"
            echo "  coverage         - Run tests with coverage report"
            echo "  html             - Run tests with HTML report"
            echo "  parallel         - Run tests in parallel"
            echo "  slow             - Run slow tests only"
            echo "  fast             - Run fast tests only (exclude slow)"
            echo "  docker           - Run tests in Docker container"
            echo "  clean            - Clean up test artifacts"
            echo "  show-coverage    - Show coverage report"
            echo "  open-coverage    - Open coverage report in browser"
            echo "  stats            - Show test statistics"
            echo "  file <filename>  - Run specific test file"
            echo "  help             - Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 all                    # Run all tests"
            echo "  $0 integration            # Run integration tests"
            echo "  $0 coverage               # Run with coverage"
            echo "  $0 file tests/test_api.py # Run specific test file"
            echo "  $0 docker                 # Run tests in Docker"
            ;;
    esac
}

# Run main function
main "$@"
