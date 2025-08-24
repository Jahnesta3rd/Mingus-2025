#!/bin/bash

# =====================================================
# MINGUS DEVELOPMENT DEPLOYMENT SCRIPT
# =====================================================
# Script to deploy the MINGUS application in development mode

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
        log_warning ".env file not found. Creating from development template..."
        if [ -f "config/development.env" ]; then
            cp config/development.env .env
            log_warning "Please update .env file with your development values before continuing."
            log_warning "At minimum, update your OPENAI_API_KEY if you want to test AI features."
            log_warning "Press Enter when ready to continue..."
            read -r
        else
            log_error "Development environment template not found at config/development.env"
            exit 1
        fi
    fi
    
    log_success "Prerequisites check completed"
}

# Create necessary directories
create_directories() {
    log_info "Creating necessary directories..."
    
    mkdir -p data
    mkdir -p logs
    mkdir -p cache
    mkdir -p scripts
    
    log_success "Directories created"
}

# Build and start services
deploy_services() {
    log_info "Building and starting development services..."
    
    # Build images
    docker-compose -f docker-compose.dev.yml build
    
    # Start core services
    docker-compose -f docker-compose.dev.yml up -d db redis
    
    # Wait for database to be ready
    log_info "Waiting for database to be ready..."
    sleep 15
    
    # Start application services
    docker-compose -f docker-compose.dev.yml up -d web celery celery-beat flower
    
    # Wait for application to be ready
    log_info "Waiting for application to be ready..."
    sleep 20
    
    # Start optional services if requested
    if [ "$ENABLE_SEARCH" = "true" ]; then
        log_info "Starting Elasticsearch for advanced search..."
        docker-compose -f docker-compose.dev.yml --profile search up -d elasticsearch
        log_info "Waiting for Elasticsearch to be ready..."
        sleep 30
    fi
    
    log_success "Development services deployed successfully"
}

# Check service health
check_health() {
    log_info "Checking service health..."
    
    # Check if services are running
    services=("web" "db" "redis" "celery" "celery-beat" "flower")
    
    for service in "${services[@]}"; do
        if docker-compose -f docker-compose.dev.yml ps | grep -q "$service.*Up"; then
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

# Show development status
show_status() {
    log_info "Development Environment Status:"
    echo ""
    
    echo "Services:"
    docker-compose -f docker-compose.dev.yml ps
    
    echo ""
    echo "Access URLs:"
    echo "============"
    echo "Flask Application: http://localhost:5000"
    echo "API Health: http://localhost:5000/api/health"
    echo "API Documentation: http://localhost:5000/api/docs"
    echo "Flower (Celery): http://localhost:5555"
    echo "PostgreSQL: localhost:5432"
    echo "Redis: localhost:6379"
    if [ "$ENABLE_SEARCH" = "true" ]; then
        echo "Elasticsearch: http://localhost:9200"
    fi
    
    echo ""
    echo "Development Commands:"
    echo "===================="
    echo "View logs: ./deploy_dev.sh logs [service]"
    echo "Restart: ./deploy_dev.sh restart"
    echo "Stop: ./deploy_dev.sh stop"
    echo "Clean: ./deploy_dev.sh clean"
    echo ""
    echo "Database Commands:"
    echo "=================="
    echo "Connect to DB: docker exec -it mingus-db-dev psql -U mingus -d mingus"
    echo "Run migrations: docker exec -it mingus-web-dev flask db upgrade"
    echo "Create migration: docker exec -it mingus-web-dev flask db migrate -m 'description'"
    echo ""
    echo "Celery Commands:"
    echo "================"
    echo "View tasks: docker exec -it mingus-celery-dev celery -A backend.celery_app inspect active"
    echo "Purge tasks: docker exec -it mingus-celery-dev celery -A backend.celery_app purge"
    echo ""
    echo "Testing:"
    echo "========"
    echo "Run tests: docker exec -it mingus-web-dev python -m pytest"
    echo "Run with coverage: docker exec -it mingus-web-dev python -m pytest --cov=backend"
}

# Main deployment function
main() {
    log_info "Starting MINGUS Development Deployment..."
    echo ""
    
    check_prerequisites
    create_directories
    deploy_services
    check_health
    show_status
    
    echo ""
    log_success "🎉 MINGUS Development Environment Ready!"
    echo ""
    log_info "Next steps:"
    log_info "1. Open http://localhost:5000 in your browser"
    log_info "2. Check the API health at http://localhost:5000/api/health"
    log_info "3. Monitor Celery tasks at http://localhost:5555"
    log_info "4. Start developing! Your code changes will auto-reload"
    echo ""
    log_info "For troubleshooting, check logs with:"
    log_info "  ./deploy_dev.sh logs [service-name]"
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
        service="${2:-web}"
        docker-compose -f docker-compose.dev.yml logs -f "$service"
        ;;
    "restart")
        docker-compose -f docker-compose.dev.yml restart
        ;;
    "stop")
        docker-compose -f docker-compose.dev.yml down
        ;;
    "clean")
        docker-compose -f docker-compose.dev.yml down -v
        docker system prune -f
        ;;
    "shell")
        service="${2:-web}"
        docker exec -it "mingus-${service}-dev" bash
        ;;
    "db")
        docker exec -it mingus-db-dev psql -U mingus -d mingus
        ;;
    "migrate")
        docker exec -it mingus-web-dev flask db upgrade
        ;;
    "test")
        docker exec -it mingus-web-dev python -m pytest "${@:2}"
        ;;
    "search")
        log_info "Starting Elasticsearch..."
        docker-compose -f docker-compose.dev.yml --profile search up -d elasticsearch
        log_success "Elasticsearch started. Access at http://localhost:9200"
        ;;
    *)
        echo "Usage: $0 {deploy|status|logs|restart|stop|clean|shell|db|migrate|test|search}"
        echo ""
        echo "Commands:"
        echo "  deploy   - Deploy the development environment (default)"
        echo "  status   - Show development status"
        echo "  logs     - Show logs for a service (default: web)"
        echo "  restart  - Restart all services"
        echo "  stop     - Stop all services"
        echo "  clean    - Stop and remove all containers and volumes"
        echo "  shell    - Open shell in a service container (default: web)"
        echo "  db       - Connect to PostgreSQL database"
        echo "  migrate  - Run database migrations"
        echo "  test     - Run tests with pytest"
        echo "  search   - Start Elasticsearch for advanced search"
        exit 1
        ;;
esac
