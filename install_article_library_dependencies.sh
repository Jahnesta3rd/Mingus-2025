#!/bin/bash

# =====================================================
# MINGUS ARTICLE LIBRARY - DEPENDENCY INSTALLATION SCRIPT
# =====================================================
# Installs all dependencies needed for the article library feature

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="$PROJECT_ROOT/logs/dependency-installation-$(date +%Y%m%d-%H%M%S).log"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if Python is installed
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed. Please install Python 3.8+ first."
        exit 1
    fi
    
    # Check Python version
    python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    required_version="3.8"
    
    if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
        log_error "Python version $python_version is too old. Please install Python 3.8+"
        exit 1
    fi
    
    log_success "Python $python_version is installed"
    
    # Check if pip is installed
    if ! command -v pip3 &> /dev/null; then
        log_error "pip3 is not installed. Please install pip first."
        exit 1
    fi
    
    log_success "pip3 is installed"
    
    # Check if virtual environment exists
    if [ ! -d "$PROJECT_ROOT/venv" ]; then
        log_warning "Virtual environment not found. Creating one..."
        python3 -m venv "$PROJECT_ROOT/venv"
        log_success "Virtual environment created"
    else
        log_success "Virtual environment found"
    fi
    
    # Activate virtual environment
    source "$PROJECT_ROOT/venv/bin/activate"
    log_success "Virtual environment activated"
}

# Upgrade pip
upgrade_pip() {
    log_info "Upgrading pip..."
    pip install --upgrade pip
    log_success "pip upgraded"
}

# Install base dependencies
install_base_dependencies() {
    log_info "Installing base dependencies..."
    
    # Install core Flask dependencies
    pip install Flask>=2.3.2 Flask-SQLAlchemy>=3.0.5 Flask-Migrate>=4.0.4 Flask-JWT-Extended>=4.5.2 Flask-CORS>=4.0.0 Flask-Caching>=2.1.0 Flask-Limiter>=3.3.1
    
    # Install database dependencies
    pip install psycopg2-binary>=2.9.7 redis>=4.6.0 sqlalchemy-searchable>=1.2.0
    
    log_success "Base dependencies installed"
}

# Install article library dependencies
install_article_library_dependencies() {
    log_info "Installing article library dependencies..."
    
    # AI and Natural Language Processing
    pip install openai>=1.0.0 nltk>=3.8.1 textstat>=0.7.3
    
    # Web Scraping and Content Extraction
    pip install newspaper3k>=0.2.8 beautifulsoup4>=4.12.0 lxml>=4.9.0 feedparser>=6.0.10
    
    # Search and Indexing
    pip install whoosh>=2.7.4 elasticsearch>=8.0.0 elasticsearch-dsl>=8.0.0
    
    # Content Processing
    pip install python-magic>=0.4.27 chardet>=5.0.0 langdetect>=1.0.9
    
    # Background Processing
    pip install celery>=5.3.0 flower>=2.0.1
    
    # Monitoring and Logging
    pip install sentry-sdk[flask]>=1.32.0 structlog>=23.1.0
    
    # Data Processing
    pip install pandas>=2.0.0 numpy>=1.24.0
    
    log_success "Article library dependencies installed"
}

# Install development dependencies (optional)
install_development_dependencies() {
    log_info "Installing development dependencies..."
    
    # Testing Framework
    pip install pytest>=7.4.0 pytest-flask>=1.2.0 pytest-cov>=4.1.0 pytest-html>=3.2.0 factory-boy>=3.3.0
    
    # Code Quality
    pip install black>=23.0.0 flake8>=6.0.0 isort>=5.12.0
    
    # Development Tools
    pip install ipdb>=0.13.0 ipython>=8.0.0
    
    log_success "Development dependencies installed"
}

# Download NLTK data
download_nltk_data() {
    log_info "Downloading NLTK data..."
    
    python3 -c "
import nltk
import ssl

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

# Download required NLTK data
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('averaged_perceptron_tagger')
nltk.download('maxent_ne_chunker')
nltk.download('words')
print('NLTK data downloaded successfully')
"
    
    log_success "NLTK data downloaded"
}

# Verify installation
verify_installation() {
    log_info "Verifying installation..."
    
    # Test imports
    python3 -c "
import sys
import importlib

required_modules = [
    'flask',
    'flask_sqlalchemy',
    'flask_migrate',
    'flask_jwt_extended',
    'flask_cors',
    'flask_caching',
    'flask_limiter',
    'openai',
    'newspaper',
    'beautifulsoup4',
    'whoosh',
    'elasticsearch',
    'celery',
    'pandas',
    'numpy',
    'nltk',
    'textstat'
]

failed_imports = []
for module in required_modules:
    try:
        importlib.import_module(module)
        print(f'✅ {module}')
    except ImportError as e:
        print(f'❌ {module}: {e}')
        failed_imports.append(module)

if failed_imports:
    print(f'\\n❌ Failed to import: {failed_imports}')
    sys.exit(1)
else:
    print('\\n✅ All required modules imported successfully')
"
    
    if [ $? -eq 0 ]; then
        log_success "Installation verification passed"
    else
        log_error "Installation verification failed"
        exit 1
    fi
}

# Create installation summary
create_summary() {
    log_info "Creating installation summary..."
    
    summary_file="$PROJECT_ROOT/logs/dependency-installation-summary.md"
    
    cat > "$summary_file" << EOF
# MINGUS Article Library - Dependency Installation Summary

## Installation Details
- **Date**: $(date)
- **Python Version**: $(python3 --version)
- **Pip Version**: $(pip --version)
- **Virtual Environment**: $PROJECT_ROOT/venv

## Installed Dependencies

### Core Framework
- Flask>=2.3.2
- Flask-SQLAlchemy>=3.0.5
- Flask-Migrate>=4.0.4
- Flask-JWT-Extended>=4.5.2
- Flask-CORS>=4.0.0
- Flask-Caching>=2.1.0
- Flask-Limiter>=3.3.1

### Database and ORM
- psycopg2-binary>=2.9.7
- redis>=4.6.0
- sqlalchemy-searchable>=1.2.0

### Article Library Core
- openai>=1.0.0
- nltk>=3.8.1
- textstat>=0.7.3
- newspaper3k>=0.2.8
- beautifulsoup4>=4.12.0
- lxml>=4.9.0
- feedparser>=6.0.10
- whoosh>=2.7.4
- elasticsearch>=8.0.0
- elasticsearch-dsl>=8.0.0
- python-magic>=0.4.27
- chardet>=5.0.0
- langdetect>=1.0.9

### Background Processing
- celery>=5.3.0
- flower>=2.0.1

### Monitoring and Logging
- sentry-sdk[flask]>=1.32.0
- structlog>=23.1.0

### Data Processing
- pandas>=2.0.0
- numpy>=1.24.0

### Development and Testing
- pytest>=7.4.0
- pytest-flask>=1.2.0
- pytest-cov>=4.1.0
- factory-boy>=3.3.0
- black>=23.0.0
- flake8>=6.0.0
- isort>=5.12.0
- ipdb>=0.13.0
- ipython>=8.0.0

## Next Steps
1. Configure environment variables in .env file
2. Run database migrations: flask db upgrade
3. Start the application: python backend/app_article_library.py
4. Run tests: python test_article_library_integration.py

## Troubleshooting
- Check logs in: $PROJECT_ROOT/logs/
- Verify virtual environment activation: source venv/bin/activate
- Reinstall dependencies: pip install -r requirements-article-library.txt
EOF
    
    log_success "Installation summary created: $summary_file"
}

# Main installation function
main() {
    log_info "Starting MINGUS Article Library dependency installation..."
    
    # Create log directory
    mkdir -p "$(dirname "$LOG_FILE")"
    touch "$LOG_FILE"
    
    # Run installation steps
    check_prerequisites
    upgrade_pip
    install_base_dependencies
    install_article_library_dependencies
    install_development_dependencies
    download_nltk_data
    verify_installation
    create_summary
    
    log_success "MINGUS Article Library dependency installation completed successfully!"
    log_info "Installation log saved to: $LOG_FILE"
    
    echo ""
    echo "🎉 Installation Complete!"
    echo "📋 Next steps:"
    echo "   1. Configure environment variables: cp config/article_library.env.example .env"
    echo "   2. Update .env file with your actual values"
    echo "   3. Run database migrations: flask db upgrade"
    echo "   4. Start the application: python backend/app_article_library.py"
    echo "   5. Run tests: python test_article_library_integration.py"
    echo ""
    echo "📚 For more information, see:"
    echo "   - MINGUS_ARTICLE_LIBRARY_CONFIGURATION_GUIDE.md"
    echo "   - FLASK_APPLICATION_INTEGRATION_SUMMARY.md"
    echo "   - logs/dependency-installation-summary.md"
}

# Handle script arguments
case "${1:-install}" in
    "install")
        main
        ;;
    "verify")
        verify_installation
        ;;
    "nltk")
        download_nltk_data
        ;;
    "dev")
        install_development_dependencies
        ;;
    *)
        echo "Usage: $0 {install|verify|nltk|dev}"
        echo "  install - Install all dependencies (default)"
        echo "  verify  - Verify installation"
        echo "  nltk    - Download NLTK data only"
        echo "  dev     - Install development dependencies only"
        exit 1
        ;;
esac
