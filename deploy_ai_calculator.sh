#!/bin/bash

# AI Job Impact Calculator Deployment Script
# This script helps deploy the AI Job Impact Calculator lead magnet

set -e

echo "🤖 AI Job Impact Calculator Deployment Script"
echo "=============================================="

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

# Check if required files exist
check_files() {
    print_status "Checking required files..."
    
    required_files=(
        "ai_job_impact_schema.sql"
        "ai-job-impact-calculator.html"
        "backend/routes/ai_job_assessment.py"
        "backend/routes/ai_calculator_api.py"
        "backend/models/ai_job_models.py"
        "backend/config/ai_calculator_config.py"
        "AI_JOB_IMPACT_CALCULATOR_README.md"
        "AI_CALCULATOR_API_DOCUMENTATION.md"
    )
    
    for file in "${required_files[@]}"; do
        if [ -f "$file" ]; then
            print_success "✓ Found $file"
        else
            print_error "✗ Missing $file"
            exit 1
        fi
    done
}

# Database setup
setup_database() {
    print_status "Setting up database..."
    
    if [ -z "$DATABASE_URL" ]; then
        print_warning "DATABASE_URL not set. Please set it before running database setup."
        echo "Example: export DATABASE_URL=postgresql://user:pass@localhost/mingus"
        return 1
    fi
    
    # Extract database name from URL
    DB_NAME=$(echo $DATABASE_URL | sed 's/.*\///')
    
    print_status "Creating database tables..."
    psql "$DATABASE_URL" -f ai_job_impact_schema.sql
    
    if [ $? -eq 0 ]; then
        print_success "Database setup completed successfully"
    else
        print_error "Database setup failed"
        return 1
    fi
}

# Backend setup
setup_backend() {
    print_status "Setting up backend..."
    
    # Check if backend directory exists
    if [ ! -d "backend" ]; then
        print_error "Backend directory not found. Please run this script from the project root."
        return 1
    fi
    
    # Check if the route file is in the correct location
    if [ ! -f "backend/routes/ai_job_assessment.py" ]; then
        print_error "AI job assessment route file not found in backend/routes/"
        return 1
    fi
    
    print_success "Backend files are in place"
    print_warning "Remember to register the blueprints in your main Flask app:"
    echo "from backend.routes.ai_job_assessment import ai_job_assessment_bp"
    echo "from backend.routes.ai_calculator_api import ai_calculator_bp"
    echo "app.register_blueprint(ai_job_assessment_bp)"
    echo "app.register_blueprint(ai_calculator_bp)"
}

# Frontend setup
setup_frontend() {
    print_status "Setting up frontend..."
    
    # Check if landing page exists
    if [ ! -f "landing.html" ]; then
        print_warning "landing.html not found. Please ensure it's updated with the calculator link."
    else
        print_success "Frontend files are ready"
    fi
    
    print_status "Frontend files to deploy:"
    echo "  - ai-job-impact-calculator.html"
    echo "  - landing.html (updated with calculator link)"
    echo ""
    print_status "Backend files to deploy:"
    echo "  - backend/routes/ai_calculator_api.py"
    echo "  - backend/models/ai_job_models.py"
    echo "  - backend/config/ai_calculator_config.py"
}

# Environment check
check_environment() {
    print_status "Checking environment variables..."
    
    required_vars=(
        "RESEND_API_KEY"
        "RESEND_FROM_EMAIL"
        "RESEND_FROM_NAME"
        "STRIPE_SECRET_KEY"
        "STRIPE_PUBLISHABLE_KEY"
    )
    
    missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        else
            print_success "✓ $var is set"
        fi
    done
    
    if [ ${#missing_vars[@]} -gt 0 ]; then
        print_warning "Missing environment variables:"
        for var in "${missing_vars[@]}"; do
            echo "  - $var"
        done
        echo ""
        echo "Please set these variables before deployment:"
                        echo "export RESEND_API_KEY=your_resend_api_key"
                echo "export RESEND_FROM_EMAIL=noreply@mingusapp.com"
                echo "export RESEND_FROM_NAME='MINGUS Financial Wellness'"
                echo "export STRIPE_SECRET_KEY=sk_test_..."
                echo "export STRIPE_PUBLISHABLE_KEY=pk_test_..."
    fi
}

# Test setup
test_setup() {
    print_status "Running basic tests..."
    
    # Test database connection
    if [ ! -z "$DATABASE_URL" ]; then
        print_status "Testing database connection..."
        if psql "$DATABASE_URL" -c "SELECT 1;" > /dev/null 2>&1; then
            print_success "Database connection successful"
        else
            print_error "Database connection failed"
        fi
    fi
    
    # Test if calculator HTML is valid
    if command -v tidy > /dev/null 2>&1; then
        print_status "Validating HTML..."
        if tidy -q -e ai-job-impact-calculator.html > /dev/null 2>&1; then
            print_success "HTML validation passed"
        else
            print_warning "HTML validation found issues (this is normal for dynamic content)"
        fi
    fi
}

# Main deployment function
deploy() {
    echo ""
    print_status "Starting AI Job Impact Calculator deployment..."
    echo ""
    
    # Check files
    check_files
    echo ""
    
    # Check environment
    check_environment
    echo ""
    
    # Setup database (if DATABASE_URL is set)
    if [ ! -z "$DATABASE_URL" ]; then
        setup_database
        echo ""
    else
        print_warning "Skipping database setup (DATABASE_URL not set)"
        echo ""
    fi
    
    # Setup backend
    setup_backend
    echo ""
    
    # Setup frontend
    setup_frontend
    echo ""
    
    # Test setup
    test_setup
    echo ""
    
    print_success "Deployment completed!"
    echo ""
    echo "Next steps:"
    echo "1. Deploy the frontend files to your web server"
    echo "2. Register the backend blueprint in your Flask app"
                echo "3. Test the calculator at: /ai-job-impact-calculator.html"
            echo "4. Test API endpoints:"
            echo "   - POST /api/ai-calculator/assess"
            echo "   - GET /api/ai-calculator/job-search"
            echo "   - POST /api/ai-calculator/convert"
            echo "5. Check email delivery via Resend dashboard"
            echo "6. Verify Stripe integration for paid conversions"
    echo ""
    echo "For detailed documentation, see: AI_JOB_IMPACT_CALCULATOR_README.md"
}

# Help function
show_help() {
    echo "AI Job Impact Calculator Deployment Script"
    echo ""
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  --help, -h     Show this help message"
    echo "  --check        Check files and environment only"
    echo "  --database     Setup database only"
    echo "  --test         Run tests only"
    echo ""
    echo "Environment Variables:"
    echo "  DATABASE_URL   PostgreSQL connection string"
    echo "  RESEND_API_KEY Resend API key for email delivery"
    echo "  RESEND_FROM_EMAIL Email address for sending emails"
    echo "  RESEND_FROM_NAME Name for sending emails"
    echo ""
    echo "Examples:"
    echo "  $0                    # Full deployment"
    echo "  $0 --check            # Check setup only"
    echo "  $0 --database         # Setup database only"
    echo ""
}

# Parse command line arguments
case "${1:-}" in
    --help|-h)
        show_help
        exit 0
        ;;
    --check)
        check_files
        echo ""
        check_environment
        echo ""
        test_setup
        exit 0
        ;;
    --database)
        setup_database
        exit 0
        ;;
    --test)
        test_setup
        exit 0
        ;;
    "")
        deploy
        exit 0
        ;;
    *)
        print_error "Unknown option: $1"
        show_help
        exit 1
        ;;
esac
