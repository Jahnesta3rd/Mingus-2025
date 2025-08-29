#!/bin/bash

# MINGUS Assessment Data Seeding Script Runner
# This script sets up the environment and runs the assessment data seeder

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check Python version
check_python_version() {
    if command_exists python3; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        REQUIRED_VERSION="3.8"
        
        if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
            print_success "Python $PYTHON_VERSION found (>= $REQUIRED_VERSION required)"
            return 0
        else
            print_error "Python $PYTHON_VERSION found, but $REQUIRED_VERSION or higher is required"
            return 1
        fi
    else
        print_error "Python 3 not found. Please install Python 3.8 or higher."
        return 1
    fi
}

# Function to check and install dependencies
check_dependencies() {
    print_status "Checking dependencies..."
    
    # Check if psycopg2 is installed
    if python3 -c "import psycopg2" 2>/dev/null; then
        print_success "psycopg2-binary is installed"
    else
        print_warning "psycopg2-binary not found. Installing..."
        pip3 install psycopg2-binary
        if [ $? -eq 0 ]; then
            print_success "psycopg2-binary installed successfully"
        else
            print_error "Failed to install psycopg2-binary"
            return 1
        fi
    fi
}

# Function to set default environment variables
set_default_env() {
    # Set default environment if not already set
    if [ -z "$ENVIRONMENT" ]; then
        export ENVIRONMENT="development"
        print_status "Setting ENVIRONMENT=development (default)"
    fi
    
    # Set default logging level if not already set
    if [ -z "$LOG_LEVEL" ]; then
        export LOG_LEVEL="INFO"
        print_status "Setting LOG_LEVEL=INFO (default)"
    fi
    
    # Set default skip existing if not already set
    if [ -z "$SKIP_EXISTING" ]; then
        export SKIP_EXISTING="true"
        print_status "Setting SKIP_EXISTING=true (default)"
    fi
}

# Function to validate environment
validate_environment() {
    print_status "Validating environment configuration..."
    
    # Check if we're in the right directory
    if [ ! -f "scripts/seed_assessment_data.py" ]; then
        print_error "seed_assessment_data.py not found. Please run this script from the project root directory."
        exit 1
    fi
    
    # Check if configuration file exists
    if [ ! -f "scripts/assessment_seeding_config.py" ]; then
        print_error "assessment_seeding_config.py not found. Please ensure all script files are present."
        exit 1
    fi
    
    print_success "Environment validation passed"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -e, --environment ENV    Set environment (development, staging, production, local)"
    echo "  -l, --log-level LEVEL    Set log level (DEBUG, INFO, WARNING, ERROR)"
    echo "  -s, --skip-existing      Skip existing assessments (default: true)"
    echo "  -f, --force              Force overwrite existing assessments"
    echo "  -b, --backup             Create database backup before seeding"
    echo "  -v, --validate           Validate data before insertion"
    echo "  -h, --help               Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  ENVIRONMENT              Environment name (default: development)"
    echo "  LOG_LEVEL               Logging level (default: INFO)"
    echo "  SKIP_EXISTING           Skip existing assessments (default: true)"
    echo "  BACKUP_BEFORE_SEED      Create backup before seeding (default: false)"
    echo "  VALIDATE_DATA           Validate data before insertion (default: true)"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Run with defaults"
    echo "  $0 -e production                      # Run in production environment"
    echo "  $0 -e development -l DEBUG            # Run with debug logging"
    echo "  $0 -f -b                              # Force overwrite with backup"
    echo ""
}

# Function to parse command line arguments
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -e|--environment)
                export ENVIRONMENT="$2"
                shift 2
                ;;
            -l|--log-level)
                export LOG_LEVEL="$2"
                shift 2
                ;;
            -s|--skip-existing)
                export SKIP_EXISTING="true"
                shift
                ;;
            -f|--force)
                export SKIP_EXISTING="false"
                shift
                ;;
            -b|--backup)
                export BACKUP_BEFORE_SEED="true"
                shift
                ;;
            -v|--validate)
                export VALIDATE_DATA="true"
                shift
                ;;
            -h|--help)
                show_usage
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
}

# Function to run the seeding script
run_seeding() {
    print_status "Starting assessment data seeding..."
    print_status "Environment: $ENVIRONMENT"
    print_status "Log Level: $LOG_LEVEL"
    print_status "Skip Existing: $SKIP_EXISTING"
    print_status "Backup Before Seed: ${BACKUP_BEFORE_SEED:-false}"
    print_status "Validate Data: ${VALIDATE_DATA:-true}"
    
    # Change to scripts directory
    cd scripts
    
    # Run the Python script
    python3 seed_assessment_data.py
    
    # Check exit status
    if [ $? -eq 0 ]; then
        print_success "Assessment data seeding completed successfully!"
        return 0
    else
        print_error "Assessment data seeding failed!"
        return 1
    fi
}

# Main execution
main() {
    echo "=========================================="
    echo "MINGUS Assessment Data Seeding Script"
    echo "=========================================="
    echo ""
    
    # Parse command line arguments
    parse_arguments "$@"
    
    # Set default environment variables
    set_default_env
    
    # Validate environment
    validate_environment
    
    # Check Python version
    if ! check_python_version; then
        exit 1
    fi
    
    # Check dependencies
    if ! check_dependencies; then
        exit 1
    fi
    
    # Run the seeding script
    if run_seeding; then
        echo ""
        print_success "All operations completed successfully!"
        echo ""
        echo "Next steps:"
        echo "1. Verify the assessments were created correctly"
        echo "2. Test the assessment functionality"
        echo "3. Check the logs for any warnings or issues"
        echo ""
        exit 0
    else
        echo ""
        print_error "Seeding failed. Please check the logs for details."
        echo ""
        exit 1
    fi
}

# Run main function with all arguments
main "$@"
