#!/bin/bash

# =====================================================
# MINGUS ARTICLE LIBRARY - DEPLOYMENT SCRIPT
# =====================================================
# Comprehensive deployment script for article library feature

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
ENV_FILE="$PROJECT_ROOT/.env"
DOCKER_COMPOSE_FILE="$PROJECT_ROOT/docker-compose.article-library.yml"

# Logging
LOG_FILE="$PROJECT_ROOT/logs/deployment-$(date +%Y%m%d-%H%M%S).log"

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
    if [ ! -f "$ENV_FILE" ]; then
        log_warning ".env file not found. Creating from template..."
        cp "$PROJECT_ROOT/config/article_library.env.example" "$ENV_FILE"
        log_warning "Please update $ENV_FILE with your actual configuration values."
        exit 1
    fi
    
    log_success "Prerequisites check completed."
}

# Load environment variables
load_environment() {
    log_info "Loading environment variables..."
    
    if [ -f "$ENV_FILE" ]; then
        export $(cat "$ENV_FILE" | grep -v '^#' | xargs)
        log_success "Environment variables loaded."
    else
        log_error "Environment file not found: $ENV_FILE"
        exit 1
    fi
}

# Validate environment configuration
validate_environment() {
    log_info "Validating environment configuration..."
    
    # Required variables
    required_vars=(
        "DATABASE_URL"
        "REDIS_URL"
        "SECRET_KEY"
        "OPENAI_API_KEY"
    )
    
    missing_vars=()
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -ne 0 ]; then
        log_error "Missing required environment variables: ${missing_vars[*]}"
        log_error "Please update $ENV_FILE with the required values."
        exit 1
    fi
    
    log_success "Environment validation completed."
}

# Setup directories
setup_directories() {
    log_info "Setting up directories..."
    
    mkdir -p "$PROJECT_ROOT/logs"
    mkdir -p "$PROJECT_ROOT/data"
    mkdir -p "$PROJECT_ROOT/static"
    mkdir -p "$PROJECT_ROOT/instance"
    mkdir -p "$PROJECT_ROOT/nginx/ssl"
    mkdir -p "$PROJECT_ROOT/monitoring/grafana/dashboards"
    mkdir -p "$PROJECT_ROOT/monitoring/grafana/datasources"
    
    log_success "Directories setup completed."
}

# Run database migrations
run_migrations() {
    log_info "Running database migrations..."
    
    # Check if database is accessible
    if ! docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T postgres pg_isready -U mingus_user -d mingus_production; then
        log_warning "Database not ready. Starting database first..."
        docker-compose -f "$DOCKER_COMPOSE_FILE" up -d postgres
        sleep 10
    fi
    
    # Run migrations
    docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T mingus-app python -m flask db upgrade
    
    log_success "Database migrations completed."
}

# Build and start services
deploy_services() {
    log_info "Deploying services..."
    
    # Build images
    log_info "Building Docker images..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" build --no-cache
    
    # Start services
    log_info "Starting services..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d
    
    log_success "Services deployment completed."
}

# Wait for services to be ready
wait_for_services() {
    log_info "Waiting for services to be ready..."
    
    # Wait for database
    log_info "Waiting for database..."
    timeout=60
    while [ $timeout -gt 0 ]; do
        if docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T postgres pg_isready -U mingus_user -d mingus_production; then
            break
        fi
        sleep 1
        timeout=$((timeout - 1))
    done
    
    if [ $timeout -eq 0 ]; then
        log_error "Database failed to start within 60 seconds."
        exit 1
    fi
    
    # Wait for Redis
    log_info "Waiting for Redis..."
    timeout=30
    while [ $timeout -gt 0 ]; do
        if docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T redis redis-cli ping; then
            break
        fi
        sleep 1
        timeout=$((timeout - 1))
    done
    
    if [ $timeout -eq 0 ]; then
        log_error "Redis failed to start within 30 seconds."
        exit 1
    fi
    
    # Wait for Flask app
    log_info "Waiting for Flask application..."
    timeout=60
    while [ $timeout -gt 0 ]; do
        if curl -f http://localhost:5000/health &> /dev/null; then
            break
        fi
        sleep 1
        timeout=$((timeout - 1))
    done
    
    if [ $timeout -eq 0 ]; then
        log_error "Flask application failed to start within 60 seconds."
        exit 1
    fi
    
    log_success "All services are ready."
}

# Initialize article library
initialize_article_library() {
    log_info "Initializing article library..."
    
    # Create article tables
    docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T mingus-app python -c "
from backend.integrations.article_library_integration import integrate_article_library
from backend.app_factory import create_app

app = create_app()
integration = integrate_article_library(app)
print('Article library integration completed successfully')
"
    
    log_success "Article library initialization completed."
}

# Run health checks
run_health_checks() {
    log_info "Running health checks..."
    
    # Check Flask app
    if curl -f http://localhost:5000/health; then
        log_success "Flask application health check passed."
    else
        log_error "Flask application health check failed."
        exit 1
    fi
    
    # Check API endpoints
    if curl -f http://localhost:5000/api/articles; then
        log_success "Article API health check passed."
    else
        log_warning "Article API health check failed (may be expected if no articles exist)."
    fi
    
    # Check Celery workers
    if docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T celery-worker celery -A backend.tasks.article_tasks inspect active; then
        log_success "Celery workers health check passed."
    else
        log_warning "Celery workers health check failed."
    fi
    
    log_success "Health checks completed."
}

# Show deployment status
show_status() {
    log_info "Deployment Status:"
    
    echo "=========================================="
    echo "Service Status:"
    docker-compose -f "$DOCKER_COMPOSE_FILE" ps
    
    echo ""
    echo "=========================================="
    echo "Access URLs:"
    echo "Flask API: http://localhost:5000"
    echo "Frontend: http://localhost:3000"
    echo "Grafana: http://localhost:3001"
    echo "Prometheus: http://localhost:9090"
    echo "Elasticsearch: http://localhost:9200"
    
    echo ""
    echo "=========================================="
    echo "Logs:"
    echo "Application logs: docker-compose -f $DOCKER_COMPOSE_FILE logs mingus-app"
    echo "Worker logs: docker-compose -f $DOCKER_COMPOSE_FILE logs celery-worker"
    echo "Database logs: docker-compose -f $DOCKER_COMPOSE_FILE logs postgres"
    
    echo ""
    echo "=========================================="
    echo "Useful Commands:"
    echo "Stop services: docker-compose -f $DOCKER_COMPOSE_FILE down"
    echo "View logs: docker-compose -f $DOCKER_COMPOSE_FILE logs -f"
    echo "Restart services: docker-compose -f $DOCKER_COMPOSE_FILE restart"
}

# Main deployment function
main() {
    log_info "Starting MINGUS Article Library deployment..."
    
    # Create log file
    mkdir -p "$(dirname "$LOG_FILE")"
    touch "$LOG_FILE"
    
    # Run deployment steps
    check_prerequisites
    load_environment
    validate_environment
    setup_directories
    deploy_services
    wait_for_services
    run_migrations
    initialize_article_library
    run_health_checks
    show_status
    
    log_success "MINGUS Article Library deployment completed successfully!"
    log_info "Deployment log saved to: $LOG_FILE"
}

# Handle script arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "stop")
        log_info "Stopping MINGUS Article Library services..."
        docker-compose -f "$DOCKER_COMPOSE_FILE" down
        log_success "Services stopped."
        ;;
    "restart")
        log_info "Restarting MINGUS Article Library services..."
        docker-compose -f "$DOCKER_COMPOSE_FILE" restart
        log_success "Services restarted."
        ;;
    "logs")
        docker-compose -f "$DOCKER_COMPOSE_FILE" logs -f
        ;;
    "status")
        docker-compose -f "$DOCKER_COMPOSE_FILE" ps
        ;;
    "clean")
        log_info "Cleaning up MINGUS Article Library deployment..."
        docker-compose -f "$DOCKER_COMPOSE_FILE" down -v
        docker system prune -f
        log_success "Cleanup completed."
        ;;
    *)
        echo "Usage: $0 {deploy|stop|restart|logs|status|clean}"
        echo "  deploy  - Deploy the article library (default)"
        echo "  stop    - Stop all services"
        echo "  restart - Restart all services"
        echo "  logs    - View service logs"
        echo "  status  - Show service status"
        echo "  clean   - Clean up all containers and volumes"
        exit 1
        ;;
esac
