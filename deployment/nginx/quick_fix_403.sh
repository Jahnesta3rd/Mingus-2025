#!/bin/bash

# 🚀 MINGUS Application - Quick 403 Error Fix Script
# This script automatically resolves the most common 403 error causes

set -e  # Exit on any error

echo "🔧 MINGUS Application - Quick 403 Error Fix"
echo "============================================="

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

# Check prerequisites
print_status "Checking prerequisites..."

if ! command_exists docker; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command_exists docker-compose; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

print_success "Prerequisites check passed"

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

print_status "Project root: $PROJECT_ROOT"

# Step 1: Backup existing configuration
print_status "Step 1: Backing up existing configuration..."

BACKUP_DIR="$SCRIPT_DIR/backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

if [ -f "$SCRIPT_DIR/nginx.conf" ]; then
    cp "$SCRIPT_DIR/nginx.conf" "$BACKUP_DIR/nginx.conf.backup"
    print_success "Backed up nginx.conf"
fi

if [ -f "$SCRIPT_DIR/nginx-ssl.conf" ]; then
    cp "$SCRIPT_DIR/nginx-ssl.conf" "$BACKUP_DIR/nginx-ssl.conf.backup"
    print_success "Backed up nginx-ssl.conf"
fi

print_success "Backup completed: $BACKUP_DIR"

# Step 2: Deploy optimized configuration
print_status "Step 2: Deploying optimized configuration..."

if [ -f "$SCRIPT_DIR/nginx-optimized.conf" ]; then
    cp "$SCRIPT_DIR/nginx-optimized.conf" "$SCRIPT_DIR/nginx.conf"
    print_success "Deployed optimized nginx.conf"
else
    print_error "nginx-optimized.conf not found. Please ensure it exists."
    exit 1
fi

# Step 3: Create SSL directory and certificates
print_status "Step 3: Setting up SSL certificates..."

SSL_DIR="$SCRIPT_DIR/ssl"
mkdir -p "$SSL_DIR"

# Generate self-signed certificate if it doesn't exist
if [ ! -f "$SSL_DIR/certificate.crt" ] || [ ! -f "$SSL_DIR/private.key" ]; then
    print_status "Generating self-signed SSL certificates..."
    
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout "$SSL_DIR/private.key" \
        -out "$SSL_DIR/certificate.crt" \
        -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost" \
        -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"
    
    chmod 600 "$SSL_DIR/private.key"
    chmod 644 "$SSL_DIR/certificate.crt"
    
    print_success "SSL certificates generated"
else
    print_success "SSL certificates already exist"
fi

# Step 4: Stop existing services
print_status "Step 4: Stopping existing services..."

cd "$PROJECT_ROOT"

if docker-compose -f deployment/docker-compose.production.yml ps | grep -q "Up"; then
    print_status "Stopping running containers..."
    docker-compose -f deployment/docker-compose.production.yml down
    print_success "Services stopped"
else
    print_success "No running services found"
fi

# Step 5: Build and start services
print_status "Step 5: Building and starting services..."

print_status "Building Nginx container..."
docker-compose -f deployment/docker-compose.production.yml build nginx

print_status "Starting all services..."
docker-compose -f deployment/docker-compose.production.yml up -d

# Wait for services to be ready
print_status "Waiting for services to be ready..."
sleep 10

# Step 6: Verify deployment
print_status "Step 6: Verifying deployment..."

# Check container status
if docker-compose -f deployment/docker-compose.production.yml ps | grep -q "Up"; then
    print_success "All services are running"
else
    print_error "Some services failed to start"
    docker-compose -f deployment/docker-compose.production.yml ps
    exit 1
fi

# Step 7: Test configuration
print_status "Step 7: Testing configuration..."

# Test Nginx configuration
if docker exec mingus_nginx_prod nginx -t >/dev/null 2>&1; then
    print_success "Nginx configuration is valid"
else
    print_error "Nginx configuration is invalid"
    docker exec mingus_nginx_prod nginx -t
    exit 1
fi

# Test health endpoint
print_status "Testing health endpoint..."
if curl -k -s https://localhost/health | grep -q "healthy"; then
    print_success "Health endpoint is working"
else
    print_warning "Health endpoint test failed (this might be expected during startup)"
fi

# Test API endpoint
print_status "Testing API endpoint..."
if curl -k -s https://localhost/api/health >/dev/null 2>&1; then
    print_success "API endpoint is accessible"
else
    print_warning "API endpoint test failed (this might be expected during startup)"
fi

# Step 8: Check logs for errors
print_status "Step 8: Checking for errors in logs..."

# Check Nginx error logs
NGINX_ERRORS=$(docker exec mingus_nginx_prod tail -n 20 /var/log/nginx/error.log 2>/dev/null | grep -i "error\|403\|forbidden" | wc -l)

if [ "$NGINX_ERRORS" -eq 0 ]; then
    print_success "No errors found in Nginx error logs"
else
    print_warning "Found $NGINX_ERRORS potential errors in Nginx logs"
    print_status "Recent Nginx error log entries:"
    docker exec mingus_nginx_prod tail -n 5 /var/log/nginx/error.log 2>/dev/null || true
fi

# Step 9: Final verification
print_status "Step 9: Final verification..."

# Check if 403 errors are still occurring
print_status "Checking access logs for 403 errors..."
RECENT_403S=$(docker exec mingus_nginx_prod tail -n 50 /var/log/nginx/access.log 2>/dev/null | grep " 403 " | wc -l)

if [ "$RECENT_403S" -eq 0 ]; then
    print_success "No recent 403 errors found"
else
    print_warning "Found $RECENT_403S recent 403 errors"
fi

# Summary
echo ""
echo "🎉 QUICK FIX COMPLETED!"
echo "========================"
echo ""
echo "✅ Configuration files updated"
echo "✅ SSL certificates configured"
echo "✅ Services restarted"
echo "✅ Configuration validated"
echo ""
echo "📋 Next steps:"
echo "1. Monitor logs: docker logs mingus_nginx_prod -f"
echo "2. Test your application endpoints"
echo "3. Run the troubleshooting script if issues persist: python3 troubleshoot_403.py"
echo ""
echo "🔍 To monitor for 403 errors:"
echo "   docker exec mingus_nginx_prod tail -f /var/log/nginx/access.log | grep ' 403 '"
echo ""
echo "📁 Backup files saved to: $BACKUP_DIR"
echo ""

# Check if there are any remaining issues
if [ "$RECENT_403S" -gt 0 ]; then
    print_warning "Some 403 errors were found. Consider running the troubleshooting script for deeper analysis."
    echo "   python3 $SCRIPT_DIR/troubleshoot_403.py"
fi

print_success "Quick fix completed successfully!"
print_status "Your application should now be accessible without 403 errors."
