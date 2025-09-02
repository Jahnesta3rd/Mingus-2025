#!/bin/bash

# =====================================================
# MINGUS APPLICATION - PRODUCTION DEPLOYMENT SCRIPT
# =====================================================
# Automates the complete deployment process
# Resolves 403 errors and configures production environment

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   error "This script should not be run as root"
fi

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    error "Docker is not installed or not in PATH"
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    error "Docker Compose is not installed or not in PATH"
fi

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        warning "Port $port is already in use"
        lsof -i :$port
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            error "Port $port is in use. Please free it up and try again."
        fi
    fi
}

# Function to generate random password
generate_password() {
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-25
}

# Function to check SSL certificates
check_ssl_certificates() {
    log "Checking SSL certificates..."
    
    local ssl_dir="deployment/nginx/ssl"
    local cert_file="$ssl_dir/certificate.crt"
    local key_file="$ssl_dir/private.key"
    
    if [[ ! -f "$cert_file" ]] || [[ ! -f "$key_file" ]]; then
        warning "SSL certificates not found. Generating new ones..."
        
        mkdir -p "$ssl_dir"
        cd "$ssl_dir"
        
        # Generate self-signed certificate
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout private.key -out certificate.crt \
            -subj "/C=US/ST=State/L=City/O=MINGUS/CN=localhost"
        
        # Set proper permissions
        chmod 600 private.key
        chmod 644 certificate.crt
        
        cd - > /dev/null
        success "SSL certificates generated successfully"
    else
        success "SSL certificates found"
        
        # Check permissions
        if [[ $(stat -c %a "$key_file") != "600" ]]; then
            warning "Fixing private key permissions..."
            chmod 600 "$key_file"
        fi
        
        if [[ $(stat -c %a "$cert_file") != "644" ]]; then
            warning "Fixing certificate permissions..."
            chmod 644 "$cert_file"
        fi
    fi
}

# Function to check environment file
check_environment() {
    log "Checking environment configuration..."
    
    if [[ ! -f ".env" ]]; then
        if [[ -f "env.production.example" ]]; then
            warning "No .env file found. Creating from template..."
            cp env.production.example .env
            warning "Please edit .env file with your actual values before continuing"
            read -p "Press Enter after editing .env file..."
        else
            error "No .env file or template found"
        fi
    fi
    
    # Check if .env has placeholder values
    if grep -q "your_secure_postgres_password_here" .env; then
        warning ".env file contains placeholder values. Please update with real values."
        read -p "Press Enter after updating .env file..."
    fi
    
    success "Environment configuration checked"
}

# Function to update Nginx configuration
update_nginx_config() {
    log "Updating Nginx configuration..."
    
    local nginx_dir="deployment/nginx"
    local prod_config="$nginx_dir/nginx-production.conf"
    local current_config="$nginx_dir/nginx.conf"
    
    if [[ ! -f "$prod_config" ]]; then
        error "Production Nginx configuration not found: $prod_config"
    fi
    
    # Backup current config
    if [[ -f "$current_config" ]]; then
        cp "$current_config" "$current_config.backup.$(date +%Y%m%d_%H%M%S)"
        log "Current Nginx config backed up"
    fi
    
    # Use production config
    cp "$prod_config" "$current_config"
    success "Nginx configuration updated to production version"
}

# Function to check Docker services
check_docker_services() {
    log "Checking Docker services..."
    
    local compose_file="deployment/docker-compose.production.yml"
    
    if [[ ! -f "$compose_file" ]]; then
        error "Docker Compose production file not found: $compose_file"
    fi
    
    # Check if services are running
    if docker compose -f "$compose_file" ps --quiet | grep -q .; then
        warning "Some Docker services are already running"
        docker compose -f "$compose_file" ps
        
        read -p "Stop existing services and continue? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log "Stopping existing services..."
            docker compose -f "$compose_file" down
        else
            error "Please stop existing services manually and try again"
        fi
    fi
    
    success "Docker services checked"
}

# Function to deploy services
deploy_services() {
    log "Deploying Docker services..."
    
    local compose_file="deployment/docker-compose.production.yml"
    
    # Build and start services
    log "Building and starting services..."
    docker compose -f "$compose_file" up --build -d
    
    # Wait for services to be ready
    log "Waiting for services to be ready..."
    sleep 10
    
    # Check service status
    log "Checking service status..."
    docker compose -f "$compose_file" ps
    
    success "Services deployed successfully"
}

# Function to verify deployment
verify_deployment() {
    log "Verifying deployment..."
    
    # Wait a bit more for services to fully start
    sleep 5
    
    # Check if containers are running
    local compose_file="deployment/docker-compose.production.yml"
    local running_containers=$(docker compose -f "$compose_file" ps --quiet | wc -l)
    local expected_containers=6  # Adjust based on your compose file
    
    if [[ $running_containers -lt $expected_containers ]]; then
        warning "Not all containers are running. Expected: $expected_containers, Running: $running_containers"
        docker compose -f "$compose_file" ps
    else
        success "All containers are running"
    fi
    
    # Check Nginx logs for errors
    log "Checking Nginx logs..."
    if docker logs mingus_nginx_prod 2>&1 | grep -q "error\|Error\|ERROR"; then
        warning "Nginx logs contain errors:"
        docker logs mingus_nginx_prod | grep -i error | tail -5
    else
        success "No errors in Nginx logs"
    fi
    
    # Check web container logs
    log "Checking web container logs..."
    if docker logs mingus_web_prod 2>&1 | grep -q "error\|Error\|ERROR"; then
        warning "Web container logs contain errors:"
        docker logs mingus_web_prod | grep -i error | tail -5
    else
        success "No errors in web container logs"
    fi
}

# Function to test endpoints
test_endpoints() {
    log "Testing endpoints..."
    
    # Wait for services to be fully ready
    sleep 15
    
    # Test health endpoint
    log "Testing health endpoint..."
    if curl -s -f -k https://localhost/health > /dev/null 2>&1; then
        success "Health endpoint responding"
    else
        warning "Health endpoint not responding"
    fi
    
    # Test API endpoint
    log "Testing API endpoint..."
    if curl -s -f -k https://localhost/api/health > /dev/null 2>&1; then
        success "API endpoint responding"
    else
        warning "API endpoint not responding"
    fi
    
    # Test security headers
    log "Testing security headers..."
    local headers=$(curl -s -I -k https://localhost/ | grep -E "(Strict-Transport-Security|X-Frame-Options|Content-Security-Policy)" | wc -l)
    if [[ $headers -ge 3 ]]; then
        success "Security headers present"
    else
        warning "Some security headers missing"
    fi
}

# Main deployment function
main() {
    echo -e "${BLUE}"
    echo "====================================================="
    echo "  MINGUS APPLICATION - PRODUCTION DEPLOYMENT"
    echo "====================================================="
    echo -e "${NC}"
    
    log "Starting production deployment..."
    
    # Pre-deployment checks
    check_port 80
    check_port 443
    check_ssl_certificates
    check_environment
    update_nginx_config
    check_docker_services
    
    # Deployment
    deploy_services
    
    # Post-deployment verification
    verify_deployment
    test_endpoints
    
    echo -e "${GREEN}"
    echo "====================================================="
    echo "  DEPLOYMENT COMPLETED SUCCESSFULLY!"
    echo "====================================================="
    echo -e "${NC}"
    
    log "Your MINGUS application should now be accessible at:"
    echo "  - HTTP:  http://localhost (redirects to HTTPS)"
    echo "  - HTTPS: https://localhost"
    echo "  - Health: https://localhost/health"
    echo "  - API:   https://localhost/api/health"
    
    log "To monitor your application:"
    echo "  - Check status: docker compose -f deployment/docker-compose.production.yml ps"
    echo "  - View logs: docker logs mingus_nginx_prod"
    echo "  - Troubleshoot: python3 deployment/nginx/troubleshoot_403.py"
    
    log "Deployment completed successfully!"
}

# Run main function
main "$@"
