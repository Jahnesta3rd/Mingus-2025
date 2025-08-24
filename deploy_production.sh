#!/bin/bash

# =====================================================
# MINGUS PRODUCTION DEPLOYMENT SCRIPT
# =====================================================
# Script to deploy the MINGUS application with article library

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

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

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if .env file exists
    if [ ! -f ".env" ]; then
        log_warning ".env file not found. Creating from template..."
        if [ -f "config/production.env" ]; then
            cp config/production.env .env
            log_warning "Please update .env file with your production values before continuing."
            log_warning "Press Enter when ready to continue..."
            read -r
        else
            log_error "Production environment template not found at config/production.env"
            exit 1
        fi
    fi
    
    log_success "Prerequisites check completed"
}

# Load environment variables
load_environment() {
    log_info "Loading environment variables..."
    
    if [ -f ".env" ]; then
        export $(cat .env | grep -v '^#' | xargs)
        log_success "Environment variables loaded"
    else
        log_error ".env file not found"
        exit 1
    fi
}

# Validate environment variables
validate_environment() {
    log_info "Validating environment variables..."
    
    required_vars=(
        "POSTGRES_PASSWORD"
        "SECRET_KEY"
        "JWT_SECRET_KEY"
        "OPENAI_API_KEY"
    )
    
    missing_vars=()
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ] || [[ "${!var}" == *"your-"* ]]; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -gt 0 ]; then
        log_error "Missing or invalid environment variables:"
        for var in "${missing_vars[@]}"; do
            log_error "  - $var"
        done
        log_error "Please update your .env file with proper values."
        exit 1
    fi
    
    log_success "Environment validation completed"
}

# Create necessary directories
create_directories() {
    log_info "Creating necessary directories..."
    
    mkdir -p nginx/ssl
    mkdir -p monitoring/grafana/dashboards
    mkdir -p monitoring/grafana/datasources
    mkdir -p scripts
    mkdir -p logs
    
    log_success "Directories created"
}

# Create Nginx configuration
create_nginx_config() {
    log_info "Creating Nginx configuration..."
    
    cat > nginx/nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream mingus_app {
        server mingus-app:5000;
    }
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=search:10m rate=5r/s;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
    
    server {
        listen 80;
        server_name _;
        
        # Redirect HTTP to HTTPS
        return 301 https://$server_name$request_uri;
    }
    
    server {
        listen 443 ssl http2;
        server_name _;
        
        # SSL configuration
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;
        
        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
        
        # Client max body size
        client_max_body_size 10M;
        
        # API routes with rate limiting
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://mingus_app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_connect_timeout 30s;
            proxy_send_timeout 30s;
            proxy_read_timeout 30s;
        }
        
        # Search endpoint with specific rate limiting
        location /api/articles/search {
            limit_req zone=search burst=10 nodelay;
            proxy_pass http://mingus_app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        # Health check
        location /health {
            proxy_pass http://mingus_app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        # Static files
        location /static/ {
            alias /var/www/static/;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
        
        # Default proxy to Flask app
        location / {
            proxy_pass http://mingus_app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_connect_timeout 30s;
            proxy_send_timeout 30s;
            proxy_read_timeout 30s;
        }
    }
}
EOF

    log_success "Nginx configuration created"
}

# Create database initialization script
create_db_init_script() {
    log_info "Creating database initialization script..."
    
    cat > scripts/init-db.sql << 'EOF'
-- MINGUS Database Initialization Script
-- This script runs when the PostgreSQL container starts for the first time

-- Create extensions if they don't exist
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create additional indexes for article library
CREATE INDEX IF NOT EXISTS idx_articles_title_gin ON articles USING gin(to_tsvector('english', title));
CREATE INDEX IF NOT EXISTS idx_articles_content_gin ON articles USING gin(to_tsvector('english', content));
CREATE INDEX IF NOT EXISTS idx_articles_published_date ON articles(published_date DESC);
CREATE INDEX IF NOT EXISTS idx_articles_category ON articles(category);
CREATE INDEX IF NOT EXISTS idx_articles_cultural_relevance ON articles(cultural_relevance_score DESC);

-- Create indexes for user progress
CREATE INDEX IF NOT EXISTS idx_user_article_progress_user_id ON user_article_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_user_article_progress_article_id ON user_article_progress(article_id);
CREATE INDEX IF NOT EXISTS idx_user_article_progress_completed_at ON user_article_progress(completed_at DESC);

-- Create indexes for assessments
CREATE INDEX IF NOT EXISTS idx_user_assessment_scores_user_id ON user_assessment_scores(user_id);
CREATE INDEX IF NOT EXISTS idx_user_assessment_scores_framework ON user_assessment_scores(framework);

-- Create indexes for folders
CREATE INDEX IF NOT EXISTS idx_article_folders_user_id ON article_folders(user_id);
CREATE INDEX IF NOT EXISTS idx_article_folders_name ON article_folders(name);

-- Create indexes for bookmarks
CREATE INDEX IF NOT EXISTS idx_article_bookmarks_user_id ON article_bookmarks(user_id);
CREATE INDEX IF NOT EXISTS idx_article_bookmarks_article_id ON article_bookmarks(article_id);

-- Create indexes for analytics
CREATE INDEX IF NOT EXISTS idx_article_analytics_article_id ON article_analytics(article_id);
CREATE INDEX IF NOT EXISTS idx_article_analytics_date ON article_analytics(date);

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO mingus;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO mingus;
EOF

    log_success "Database initialization script created"
}

# Create Prometheus configuration
create_prometheus_config() {
    log_info "Creating Prometheus configuration..."
    
    cat > monitoring/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  # - "first_rules.yml"
  # - "second_rules.yml"

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'mingus-app'
    static_configs:
      - targets: ['mingus-app:5000']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:5432']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']

  - job_name: 'celery'
    static_configs:
      - targets: ['celery-worker:5555']
EOF

    log_success "Prometheus configuration created"
}

# Create Grafana datasource configuration
create_grafana_datasources() {
    log_info "Creating Grafana datasource configuration..."
    
    mkdir -p monitoring/grafana/datasources
    
    cat > monitoring/grafana/datasources/prometheus.yml << 'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
EOF

    log_success "Grafana datasource configuration created"
}

# Build and start services
deploy_services() {
    log_info "Building and starting services..."
    
    # Build images
    docker-compose -f docker-compose.production.yml build
    
    # Start core services
    docker-compose -f docker-compose.production.yml up -d postgres redis
    
    # Wait for database to be ready
    log_info "Waiting for database to be ready..."
    sleep 30
    
    # Start application services
    docker-compose -f docker-compose.production.yml up -d mingus-app celery-worker celery-beat
    
    # Wait for application to be ready
    log_info "Waiting for application to be ready..."
    sleep 30
    
    # Start optional services if profiles are enabled
    if [ "$ENABLE_MONITORING" = "true" ]; then
        log_info "Starting monitoring services..."
        docker-compose -f docker-compose.production.yml --profile monitoring up -d
    fi
    
    if [ "$ENABLE_SEARCH" = "true" ]; then
        log_info "Starting search services..."
        docker-compose -f docker-compose.production.yml --profile search up -d
    fi
    
    # Start nginx
    docker-compose -f docker-compose.production.yml up -d nginx
    
    log_success "Services deployed successfully"
}

# Check service health
check_health() {
    log_info "Checking service health..."
    
    # Check if services are running
    services=("mingus-app" "postgres" "redis" "celery-worker" "celery-beat")
    
    for service in "${services[@]}"; do
        if docker-compose -f docker-compose.production.yml ps | grep -q "$service.*Up"; then
            log_success "$service is running"
        else
            log_error "$service is not running"
            return 1
        fi
    done
    
    # Check application health endpoint
    if curl -f http://localhost:5000/api/health > /dev/null 2>&1; then
        log_success "Application health check passed"
    else
        log_warning "Application health check failed (this might be normal during startup)"
    fi
    
    log_success "Health check completed"
}

# Show deployment status
show_status() {
    log_info "Deployment Status:"
    echo ""
    
    echo "Services:"
    docker-compose -f docker-compose.production.yml ps
    
    echo ""
    echo "Logs (last 10 lines of each service):"
    echo "====================================="
    
    services=("mingus-app" "celery-worker" "celery-beat" "postgres" "redis")
    for service in "${services[@]}"; do
        echo ""
        echo "$service logs:"
        docker-compose -f docker-compose.production.yml logs --tail=10 "$service" 2>/dev/null || echo "No logs available"
    done
    
    echo ""
    echo "Access URLs:"
    echo "============"
    echo "Application: http://localhost (or your domain)"
    echo "API Health: http://localhost/api/health"
    echo "Flower (Celery): http://localhost:5555 (if monitoring enabled)"
    echo "Grafana: http://localhost:3000 (if monitoring enabled)"
    echo "Prometheus: http://localhost:9090 (if monitoring enabled)"
}

# Main deployment function
main() {
    log_info "Starting MINGUS Production Deployment..."
    echo ""
    
    check_prerequisites
    load_environment
    validate_environment
    create_directories
    create_nginx_config
    create_db_init_script
    create_prometheus_config
    create_grafana_datasources
    deploy_services
    check_health
    show_status
    
    echo ""
    log_success "🎉 MINGUS Production Deployment Completed!"
    echo ""
    log_info "Next steps:"
    log_info "1. Configure your domain and SSL certificates"
    log_info "2. Set up monitoring dashboards in Grafana"
    log_info "3. Configure backup strategies for database and data"
    log_info "4. Set up CI/CD pipeline for future deployments"
    echo ""
    log_info "For troubleshooting, check logs with:"
    log_info "  docker-compose -f docker-compose.production.yml logs -f [service-name]"
}

# Handle command line arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "status")
        show_status
        ;;
    "logs")
        service="${2:-mingus-app}"
        docker-compose -f docker-compose.production.yml logs -f "$service"
        ;;
    "restart")
        docker-compose -f docker-compose.production.yml restart
        ;;
    "stop")
        docker-compose -f docker-compose.production.yml down
        ;;
    "clean")
        docker-compose -f docker-compose.production.yml down -v
        docker system prune -f
        ;;
    *)
        echo "Usage: $0 {deploy|status|logs|restart|stop|clean}"
        echo ""
        echo "Commands:"
        echo "  deploy   - Deploy the application (default)"
        echo "  status   - Show deployment status"
        echo "  logs     - Show logs for a service (default: mingus-app)"
        echo "  restart  - Restart all services"
        echo "  stop     - Stop all services"
        echo "  clean    - Stop and remove all containers and volumes"
        exit 1
        ;;
esac
