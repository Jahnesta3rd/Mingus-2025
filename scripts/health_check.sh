#!/bin/bash
# =====================================================
# Mingus Meme Splash Page - Health Check Script
# Comprehensive health monitoring for production deployment
# =====================================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="mingus-meme-app"
HEALTH_URL="http://localhost/health"
DB_FILE="mingus_memes.db"
LOG_FILE="health_check.log"

# Functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a $LOG_FILE
}

success() {
    echo -e "${GREEN}✅ $1${NC}" | tee -a $LOG_FILE
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}" | tee -a $LOG_FILE
}

error() {
    echo -e "${RED}❌ $1${NC}" | tee -a $LOG_FILE
}

# Check container status
check_containers() {
    log "Checking container status..."
    
    if docker-compose ps | grep -q "Up"; then
        success "All containers are running"
        docker-compose ps
    else
        error "Some containers are not running"
        docker-compose ps
        return 1
    fi
}

# Check application health endpoint
check_application_health() {
    log "Checking application health endpoint..."
    
    if curl -f -s $HEALTH_URL > /dev/null; then
        success "Application health endpoint is responding"
        
        # Get health status
        HEALTH_RESPONSE=$(curl -s $HEALTH_URL)
        echo "Health response: $HEALTH_RESPONSE"
    else
        error "Application health endpoint is not responding"
        return 1
    fi
}

# Check database connectivity
check_database() {
    log "Checking database connectivity..."
    
    if docker-compose exec -T $APP_NAME python3 -c "
import sqlite3
try:
    conn = sqlite3.connect('$DB_FILE')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM memes')
    count = cursor.fetchone()[0]
    print(f'Database connected successfully. Memes count: {count}')
    conn.close()
except Exception as e:
    print(f'Database error: {e}')
    exit(1)
" 2>/dev/null; then
        success "Database connectivity verified"
    else
        error "Database connectivity check failed"
        return 1
    fi
}

# Check file system
check_filesystem() {
    log "Checking file system..."
    
    # Check disk space
    DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ $DISK_USAGE -gt 80 ]; then
        warning "Disk usage is high: ${DISK_USAGE}%"
    else
        success "Disk usage is normal: ${DISK_USAGE}%"
    fi
    
    # Check memory usage
    MEMORY_USAGE=$(free | awk 'NR==2{printf "%.2f", $3*100/$2}')
    if (( $(echo "$MEMORY_USAGE > 80" | bc -l) )); then
        warning "Memory usage is high: ${MEMORY_USAGE}%"
    else
        success "Memory usage is normal: ${MEMORY_USAGE}%"
    fi
    
    # Check uploads directory
    if docker-compose exec -T $APP_NAME test -d /app/static/uploads; then
        success "Uploads directory exists"
    else
        error "Uploads directory not found"
        return 1
    fi
}

# Check network connectivity
check_network() {
    log "Checking network connectivity..."
    
    # Check if application is accessible
    if curl -f -s http://localhost > /dev/null; then
        success "Application is accessible via HTTP"
    else
        error "Application is not accessible via HTTP"
        return 1
    fi
    
    # Check if HTTPS is working (if configured)
    if curl -f -s https://localhost > /dev/null 2>&1; then
        success "Application is accessible via HTTPS"
    else
        warning "HTTPS not configured or not accessible"
    fi
}

# Check logs for errors
check_logs() {
    log "Checking application logs for errors..."
    
    # Check for recent errors
    RECENT_ERRORS=$(docker-compose logs --tail=100 $APP_NAME | grep -i error | wc -l)
    
    if [ $RECENT_ERRORS -gt 0 ]; then
        warning "Found $RECENT_ERRORS recent errors in logs"
        echo "Recent errors:"
        docker-compose logs --tail=20 $APP_NAME | grep -i error
    else
        success "No recent errors found in logs"
    fi
    
    # Check for warnings
    RECENT_WARNINGS=$(docker-compose logs --tail=100 $APP_NAME | grep -i warning | wc -l)
    
    if [ $RECENT_WARNINGS -gt 0 ]; then
        warning "Found $RECENT_WARNINGS recent warnings in logs"
    else
        success "No recent warnings found in logs"
    fi
}

# Check external services
check_external_services() {
    log "Checking external services..."
    
    # Check AWS S3 connectivity (if configured)
    if grep -q "AWS_ACCESS_KEY_ID=" .env && ! grep -q "AWS_ACCESS_KEY_ID=your-aws-access-key" .env; then
        if docker-compose exec -T $APP_NAME python3 -c "
import boto3
import os
try:
    s3 = boto3.client('s3')
    s3.list_buckets()
    print('AWS S3 connectivity verified')
except Exception as e:
    print(f'AWS S3 error: {e}')
    exit(1)
" 2>/dev/null; then
            success "AWS S3 connectivity verified"
        else
            warning "AWS S3 connectivity check failed"
        fi
    else
        warning "AWS S3 not configured"
    fi
    
    # Check Redis connectivity (if configured)
    if docker-compose ps | grep -q redis; then
        if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
            success "Redis connectivity verified"
        else
            warning "Redis connectivity check failed"
        fi
    else
        warning "Redis not configured"
    fi
}

# Check security
check_security() {
    log "Checking security configuration..."
    
    # Check if secret key is set and not default
    if grep -q "SECRET_KEY=" .env && ! grep -q "SECRET_KEY=your-super-secret-key" .env; then
        success "Secret key is configured"
    else
        error "Secret key is not properly configured"
        return 1
    fi
    
    # Check SSL certificate (if configured)
    if [ -f "/etc/nginx/ssl/cert.pem" ]; then
        CERT_EXPIRY=$(openssl x509 -in /etc/nginx/ssl/cert.pem -noout -enddate | cut -d= -f2)
        CERT_EXPIRY_EPOCH=$(date -d "$CERT_EXPIRY" +%s)
        CURRENT_EPOCH=$(date +%s)
        DAYS_UNTIL_EXPIRY=$(( (CERT_EXPIRY_EPOCH - CURRENT_EPOCH) / 86400 ))
        
        if [ $DAYS_UNTIL_EXPIRY -lt 30 ]; then
            warning "SSL certificate expires in $DAYS_UNTIL_EXPIRY days"
        else
            success "SSL certificate is valid for $DAYS_UNTIL_EXPIRY days"
        fi
    else
        warning "SSL certificate not found"
    fi
}

# Performance check
check_performance() {
    log "Checking application performance..."
    
    # Test response time
    RESPONSE_TIME=$(curl -w "%{time_total}" -o /dev/null -s $HEALTH_URL)
    
    if (( $(echo "$RESPONSE_TIME < 1.0" | bc -l) )); then
        success "Response time is good: ${RESPONSE_TIME}s"
    elif (( $(echo "$RESPONSE_TIME < 3.0" | bc -l) )); then
        warning "Response time is acceptable: ${RESPONSE_TIME}s"
    else
        error "Response time is slow: ${RESPONSE_TIME}s"
        return 1
    fi
    
    # Check database performance
    if docker-compose exec -T $APP_NAME python3 -c "
import sqlite3
import time
conn = sqlite3.connect('$DB_FILE')
cursor = conn.cursor()
start = time.time()
cursor.execute('SELECT COUNT(*) FROM memes WHERE is_active = 1')
count = cursor.fetchone()[0]
end = time.time()
print(f'Database query time: {end - start:.3f}s, Active memes: {count}')
conn.close()
" 2>/dev/null; then
        success "Database performance check completed"
    else
        warning "Database performance check failed"
    fi
}

# Generate health report
generate_report() {
    log "Generating health report..."
    
    REPORT_FILE="health_report_$(date +%Y%m%d_%H%M%S).txt"
    
    {
        echo "Mingus Meme Splash Page - Health Report"
        echo "Generated: $(date)"
        echo "========================================"
        echo ""
        
        echo "Container Status:"
        docker-compose ps
        echo ""
        
        echo "System Resources:"
        df -h
        echo ""
        free -h
        echo ""
        
        echo "Application Logs (last 50 lines):"
        docker-compose logs --tail=50 $APP_NAME
        echo ""
        
        echo "Database Status:"
        docker-compose exec -T $APP_NAME sqlite3 $DB_FILE "SELECT COUNT(*) as total_memes FROM memes;"
        docker-compose exec -T $APP_NAME sqlite3 $DB_FILE "SELECT COUNT(*) as active_memes FROM memes WHERE is_active = 1;"
        echo ""
        
    } > $REPORT_FILE
    
    success "Health report generated: $REPORT_FILE"
}

# Main health check function
main() {
    log "Starting comprehensive health check..."
    
    local exit_code=0
    
    check_containers || exit_code=1
    check_application_health || exit_code=1
    check_database || exit_code=1
    check_filesystem || exit_code=1
    check_network || exit_code=1
    check_logs
    check_external_services
    check_security || exit_code=1
    check_performance || exit_code=1
    
    if [ $exit_code -eq 0 ]; then
        success "All health checks passed!"
    else
        error "Some health checks failed"
    fi
    
    generate_report
    
    return $exit_code
}

# Handle script arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "Options:"
        echo "  --help, -h     Show this help message"
        echo "  --report-only  Only generate health report"
        echo "  --quick        Run quick health check (containers + app only)"
        echo ""
        exit 0
        ;;
    --report-only)
        generate_report
        exit 0
        ;;
    --quick)
        log "Running quick health check..."
        check_containers || exit 1
        check_application_health || exit 1
        success "Quick health check completed"
        exit 0
        ;;
    *)
        main
        exit $?
        ;;
esac
