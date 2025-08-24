# MINGUS Article Library - Dependency Management Summary

## Overview

This document summarizes the dependency management setup for the MINGUS Article Library feature. All necessary dependencies have been organized and documented to ensure smooth installation and deployment.

## Dependency Files Created

### 1. Updated Main Requirements (`requirements.txt`)
- **Purpose**: Main production dependencies for the entire MINGUS application
- **Scope**: Includes existing MINGUS dependencies plus article library dependencies
- **Usage**: `pip install -r requirements.txt`

### 2. Article Library Requirements (`requirements-article-library.txt`)
- **Purpose**: Standalone dependencies for article library feature only
- **Scope**: Core dependencies needed for article library functionality
- **Usage**: `pip install -r requirements-article-library.txt`

### 3. Development Requirements (`requirements-article-library-dev.txt`)
- **Purpose**: Development and testing dependencies for article library
- **Scope**: Testing frameworks, code quality tools, debugging utilities
- **Usage**: `pip install -r requirements-article-library-dev.txt`

### 4. Installation Script (`install_article_library_dependencies.sh`)
- **Purpose**: Automated dependency installation with validation
- **Features**: Prerequisites checking, virtual environment setup, NLTK data download
- **Usage**: `./install_article_library_dependencies.sh`

## Dependency Categories

### Core Framework Dependencies
```bash
# Flask and Extensions
Flask>=2.3.2
Flask-SQLAlchemy>=3.0.5
Flask-Migrate>=4.0.4
Flask-JWT-Extended>=4.5.2
Flask-CORS>=4.0.0
Flask-Caching>=2.1.0
Flask-Limiter>=3.3.1
```

### Database and ORM Dependencies
```bash
# Database Drivers and ORM
psycopg2-binary>=2.9.7
redis>=4.6.0
sqlalchemy-searchable>=1.2.0
```

### Article Library Core Dependencies

#### AI and Natural Language Processing
```bash
openai>=1.0.0          # OpenAI API for article classification
nltk>=3.8.1            # Natural Language Toolkit
textstat>=0.7.3        # Text statistics and readability
```

#### Web Scraping and Content Extraction
```bash
newspaper3k>=0.2.8     # Article extraction from news sites
beautifulsoup4>=4.12.0 # HTML/XML parsing
lxml>=4.9.0            # Fast XML/HTML processing
feedparser>=6.0.10     # RSS/Atom feed parsing
```

#### Search and Indexing
```bash
whoosh>=2.7.4          # Pure Python search engine
elasticsearch>=8.0.0   # Elasticsearch client
elasticsearch-dsl>=8.0.0 # Elasticsearch DSL
```

#### Content Processing
```bash
python-magic>=0.4.27   # File type detection
chardet>=5.0.0         # Character encoding detection
langdetect>=1.0.9      # Language detection
```

### Background Processing Dependencies
```bash
celery>=5.3.0          # Distributed task queue
flower>=2.0.1          # Celery monitoring tool
```

### Monitoring and Logging Dependencies
```bash
sentry-sdk[flask]>=1.32.0 # Error tracking and monitoring
structlog>=23.1.0      # Structured logging
```

### Data Processing Dependencies
```bash
pandas>=2.0.0          # Data manipulation and analysis
numpy>=1.24.0          # Numerical computing
```

### Development and Testing Dependencies
```bash
# Testing Framework
pytest>=7.4.0
pytest-flask>=1.2.0
pytest-cov>=4.1.0
pytest-html>=3.2.0
factory-boy>=3.3.0

# Code Quality
black>=23.0.0          # Code formatting
flake8>=6.0.0          # Linting
isort>=5.12.0          # Import sorting
mypy>=1.0.0            # Type checking

# Development Tools
ipdb>=0.13.0           # Debugger
ipython>=8.0.0         # Enhanced Python shell
```

## Installation Methods

### Method 1: Automated Installation Script (Recommended)
```bash
# Install all dependencies with validation
./install_article_library_dependencies.sh

# Install only development dependencies
./install_article_library_dependencies.sh dev

# Verify installation
./install_article_library_dependencies.sh verify

# Download NLTK data only
./install_article_library_dependencies.sh nltk
```

### Method 2: Manual Installation
```bash
# Install article library dependencies only
pip install -r requirements-article-library.txt

# Install development dependencies
pip install -r requirements-article-library-dev.txt

# Install all dependencies (including existing MINGUS)
pip install -r requirements.txt
```

### Method 3: Individual Package Installation
```bash
# Core dependencies
pip install Flask>=2.3.2 Flask-SQLAlchemy>=3.0.5

# Article library dependencies
pip install openai>=1.0.0 newspaper3k>=0.2.8

# Search and indexing
pip install whoosh>=2.7.4 elasticsearch>=8.0.0

# Background processing
pip install celery>=5.3.0 flower>=2.0.1
```

## Prerequisites

### System Requirements
- **Python**: 3.8 or higher
- **pip**: Latest version
- **Virtual Environment**: Recommended for isolation
- **System Libraries**: Some packages may require system-level dependencies

### System Dependencies (Linux/macOS)
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install python3-dev python3-pip python3-venv
sudo apt-get install libxml2-dev libxslt1-dev libffi-dev libssl-dev

# macOS (using Homebrew)
brew install python3
brew install libxml2 libxslt openssl

# CentOS/RHEL
sudo yum install python3-devel python3-pip
sudo yum install libxml2-devel libxslt-devel openssl-devel
```

### NLTK Data Requirements
The installation script automatically downloads required NLTK data:
- punkt (tokenization)
- stopwords (common stop words)
- wordnet (lexical database)
- averaged_perceptron_tagger (POS tagging)
- maxent_ne_chunker (named entity recognition)
- words (word list)

## Version Compatibility

### Python Version Compatibility
- **Minimum**: Python 3.8
- **Recommended**: Python 3.9 or 3.10
- **Maximum**: Python 3.11 (tested)

### Flask Version Compatibility
- **Minimum**: Flask 2.3.2
- **Recommended**: Flask 3.0.2
- **Compatibility**: All Flask extensions are compatible

### Database Compatibility
- **PostgreSQL**: 12.0 or higher
- **Redis**: 6.0 or higher
- **SQLAlchemy**: 2.0.41 (compatible with existing MINGUS)

## Dependency Conflicts and Resolutions

### Known Conflicts
1. **SQLAlchemy Version Conflicts**: Resolved by using compatible versions
2. **Flask Extension Conflicts**: All extensions use compatible versions
3. **OpenAI API Version**: Using latest stable version

### Resolution Strategies
1. **Virtual Environment**: Isolate dependencies
2. **Version Pinning**: Use specific versions where needed
3. **Dependency Groups**: Separate production and development dependencies

## Security Considerations

### Security Scanning
```bash
# Install security scanning tools
pip install bandit>=1.7.0 safety>=2.3.0

# Run security scans
bandit -r backend/
safety check
```

### Vulnerability Monitoring
- **Sentry SDK**: Error tracking and security monitoring
- **Safety**: Automated vulnerability scanning
- **Dependabot**: Automated dependency updates (GitHub)

## Performance Considerations

### Heavy Dependencies
- **newspaper3k**: Large package, consider lazy loading
- **nltk**: Large data files, download only required data
- **elasticsearch**: Optional for advanced search

### Optimization Strategies
- **Lazy Loading**: Import heavy modules only when needed
- **Caching**: Use Redis for caching expensive operations
- **Background Processing**: Use Celery for heavy tasks

## Troubleshooting

### Common Installation Issues

#### 1. Compilation Errors
```bash
# Install build dependencies
sudo apt-get install build-essential python3-dev

# Use pre-compiled packages
pip install --only-binary=all package-name
```

#### 2. NLTK Data Issues
```bash
# Manual NLTK data download
python3 -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"
```

#### 3. Permission Issues
```bash
# Use virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-article-library.txt
```

#### 4. Network Issues
```bash
# Use alternative package index
pip install -i https://pypi.org/simple/ package-name

# Use proxy if needed
pip install --proxy http://proxy:port package-name
```

### Verification Commands
```bash
# Check Python version
python3 --version

# Check pip version
pip --version

# Verify virtual environment
which python
which pip

# Test imports
python3 -c "import flask, openai, newspaper, whoosh; print('All imports successful')"
```

## Maintenance

### Regular Updates
```bash
# Update all dependencies
pip install --upgrade -r requirements-article-library.txt

# Update specific packages
pip install --upgrade openai newspaper3k

# Check for outdated packages
pip list --outdated
```

### Dependency Auditing
```bash
# Security audit
safety check

# Dependency tree
pip install pipdeptree
pipdeptree -r requirements-article-library.txt
```

### Cleanup
```bash
# Remove unused packages
pip install pip-autoremove
pip-autoremove package-name

# Clean pip cache
pip cache purge
```

## Next Steps

### After Installation
1. **Configure Environment**: Set up environment variables
2. **Database Setup**: Run migrations and create tables
3. **Service Configuration**: Configure Redis, Celery, and other services
4. **Testing**: Run integration tests to verify installation

### Ongoing Maintenance
1. **Regular Updates**: Keep dependencies up to date
2. **Security Monitoring**: Monitor for vulnerabilities
3. **Performance Monitoring**: Monitor resource usage
4. **Documentation**: Keep dependency documentation current

## Conclusion

The dependency management for the MINGUS Article Library is comprehensive and well-organized:

✅ **Complete Coverage**: All necessary dependencies included
✅ **Version Compatibility**: Compatible with existing MINGUS application
✅ **Security Focused**: Security scanning and monitoring included
✅ **Performance Optimized**: Heavy dependencies optimized
✅ **Easy Installation**: Automated installation script provided
✅ **Well Documented**: Comprehensive documentation and troubleshooting
✅ **Maintainable**: Clear update and maintenance procedures

The article library dependencies are ready for production deployment and can be easily integrated into the existing MINGUS application infrastructure.
