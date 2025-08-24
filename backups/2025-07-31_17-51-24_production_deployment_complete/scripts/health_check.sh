#!/bin/bash

# Mingus Application Health Check Script
# Comprehensive health monitoring for all application components

set -e

# Configuration
APP_NAME="mingus-app"
HEALTH_ENDPOINT="/health"
API_ENDPOINT="/api/auth/check-auth"
DB_ENDPOINT="/api/health/database"
REDIS_ENDPOINT="/api/health/redis"
METRICS_ENDPOINT="/monitoring/metrics"

# Thresholds
CPU_THRESHOLD=80
MEMORY_THRESHOLD=85
DISK_THRESHOLD=85
RESPONSE_TIME_THRESHOLD=5

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
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

# Function to get service URL
get_service_url() {
    local service_name=$1
    local port=${2:-80}
    
    # Try to get from kubectl first
    if command -v kubectl >/dev/null 2>&1; then
        local url=$(kubectl get service $service_name -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null)
        if [ ! -z "$url" ]; then
            echo "http://$url:$port"
            return
        fi
    fi
    
    # Fallback to localhost
    echo "http://localhost:$port"
}

# Function to check HTTP endpoint
check_http_endpoint() {
    local url=$1
    local endpoint=$2
    local description=$3
    local timeout=${4:-10}
    
    local full_url="${url}${endpoint}"
    
    log_info "Checking $description: $full_url"
    
    local start_time=$(date +%s.%N)
    local response=$(curl -s -w "%{http_code}" -o /tmp/response_body --max-time $timeout "$full_url" 2>/dev/null || echo "000")
    local end_time=$(date +%s.%N)
    
    local http_code=${response: -3}
    local response_time=$(echo "$end_time - $start_time" | bc)
    
    if [ "$http_code" = "200" ]; then
        log_success "$description is healthy (${response_time}s)"
        return 0
    else
        log_error "$description is unhealthy (HTTP $http_code, ${response_time}s)"
        return 1
    fi
}

# Function to check application health
check_application_health() {
    log_info "Checking application health..."
    
    local app_url=$(get_service_url $APP_NAME 5002)
    local health_status=0
    
    # Check main health endpoint
    if ! check_http_endpoint "$app_url" "$HEALTH_ENDPOINT" "Application Health"; then
        health_status=1
    fi
    
    # Check API endpoint
    if ! check_http_endpoint "$app_url" "$API_ENDPOINT" "API Endpoint"; then
        health_status=1
    fi
    
    # Check database connectivity
    if ! check_http_endpoint "$app_url" "$DB_ENDPOINT" "Database Connectivity"; then
        health_status=1
    fi
    
    # Check Redis connectivity
    if ! check_http_endpoint "$app_url" "$REDIS_ENDPOINT" "Redis Connectivity"; then
        health_status=1
    fi
    
    # Check metrics endpoint
    if ! check_http_endpoint "$app_url" "$METRICS_ENDPOINT" "Metrics Endpoint"; then
        log_warning "Metrics endpoint not accessible"
    fi
    
    return $health_status
}

# Function to check system resources
check_system_resources() {
    log_info "Checking system resources..."
    
    local health_status=0
    
    # Check CPU usage
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    if (( $(echo "$cpu_usage > $CPU_THRESHOLD" | bc -l) )); then
        log_warning "High CPU usage: ${cpu_usage}%"
        health_status=1
    else
        log_success "CPU usage: ${cpu_usage}%"
    fi
    
    # Check memory usage
    local memory_usage=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
    if (( $(echo "$memory_usage > $MEMORY_THRESHOLD" | bc -l) )); then
        log_warning "High memory usage: ${memory_usage}%"
        health_status=1
    else
        log_success "Memory usage: ${memory_usage}%"
    fi
    
    # Check disk usage
    local disk_usage=$(df / | tail -1 | awk '{print $5}' | cut -d'%' -f1)
    if [ "$disk_usage" -gt "$DISK_THRESHOLD" ]; then
        log_warning "High disk usage: ${disk_usage}%"
        health_status=1
    else
        log_success "Disk usage: ${disk_usage}%"
    fi
    
    return $health_status
}

# Function to check database health
check_database_health() {
    log_info "Checking database health..."
    
    # Try to connect to PostgreSQL
    if command -v psql >/dev/null 2>&1; then
        if [ ! -z "$DATABASE_URL" ]; then
            if psql "$DATABASE_URL" -c "SELECT 1;" >/dev/null 2>&1; then
                log_success "Database connection successful"
                
                # Check for long-running queries
                local long_queries=$(psql "$DATABASE_URL" -c "SELECT count(*) FROM pg_stat_activity WHERE state = 'active' AND query_start < NOW() - INTERVAL '5 minutes';" -t | tr -d ' ')
                if [ "$long_queries" -gt 5 ]; then
                    log_warning "Found $long_queries long-running queries"
                fi
                
                return 0
            else
                log_error "Database connection failed"
                return 1
            fi
        fi
    fi
    
    log_warning "Database health check skipped (psql not available or DATABASE_URL not set)"
    return 0
}

# Function to check Redis health
check_redis_health() {
    log_info "Checking Redis health..."
    
    # Try to connect to Redis
    if command -v redis-cli >/dev/null 2>&1; then
        if [ ! -z "$REDIS_URL" ]; then
            if redis-cli -u "$REDIS_URL" ping >/dev/null 2>&1; then
                log_success "Redis connection successful"
                
                # Check memory usage
                local memory_info=$(redis-cli -u "$REDIS_URL" info memory | grep "used_memory_human:" | cut -d: -f2)
                log_info "Redis memory usage: $memory_info"
                
                return 0
            else
                log_error "Redis connection failed"
                return 1
            fi
        fi
    fi
    
    log_warning "Redis health check skipped (redis-cli not available or REDIS_URL not set)"
    return 0
}

# Function to check container health
check_container_health() {
    log_info "Checking container health..."
    
    if command -v docker >/dev/null 2>&1; then
        local containers=$(docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep $APP_NAME || true)
        
        if [ ! -z "$containers" ]; then
            log_success "Application containers running:"
            echo "$containers"
            
            # Check for unhealthy containers
            local unhealthy=$(docker ps --filter "name=$APP_NAME" --filter "health=unhealthy" --format "{{.Names}}" | wc -l)
            if [ "$unhealthy" -gt 0 ]; then
                log_error "Found $unhealthy unhealthy containers"
                return 1
            fi
        else
            log_error "No application containers found"
            return 1
        fi
    elif command -v kubectl >/dev/null 2>&1; then
        # Check Kubernetes pods
        local pods=$(kubectl get pods -l app=$APP_NAME --no-headers 2>/dev/null || true)
        
        if [ ! -z "$pods" ]; then
            log_success "Application pods:"
            echo "$pods"
            
            # Check for failed pods
            local failed=$(kubectl get pods -l app=$APP_NAME --no-headers 2>/dev/null | grep -E "(Error|CrashLoopBackOff|Pending)" | wc -l)
            if [ "$failed" -gt 0 ]; then
                log_error "Found $failed failed pods"
                return 1
            fi
        else
            log_error "No application pods found"
            return 1
        fi
    else
        log_warning "Container health check skipped (docker/kubectl not available)"
    fi
    
    return 0
}

# Function to check network connectivity
check_network_connectivity() {
    log_info "Checking network connectivity..."
    
    local health_status=0
    
    # Check DNS resolution
    if nslookup google.com >/dev/null 2>&1; then
        log_success "DNS resolution working"
    else
        log_error "DNS resolution failed"
        health_status=1
    fi
    
    # Check internet connectivity
    if ping -c 1 8.8.8.8 >/dev/null 2>&1; then
        log_success "Internet connectivity working"
    else
        log_error "Internet connectivity failed"
        health_status=1
    fi
    
    # Check application port
    local app_url=$(get_service_url $APP_NAME 5002)
    local host=$(echo $app_url | sed 's|http://||' | cut -d: -f1)
    local port=$(echo $app_url | cut -d: -f2)
    
    if nc -z "$host" "$port" 2>/dev/null; then
        log_success "Application port $port accessible"
    else
        log_error "Application port $port not accessible"
        health_status=1
    fi
    
    return $health_status
}

# Function to check log files
check_log_files() {
    log_info "Checking log files..."
    
    local log_dir="/app/logs"
    local health_status=0
    
    if [ -d "$log_dir" ]; then
        # Check for error logs
        local error_count=$(find "$log_dir" -name "*.log" -exec grep -l "ERROR\|CRITICAL" {} \; 2>/dev/null | wc -l)
        if [ "$error_count" -gt 0 ]; then
            log_warning "Found $error_count log files with errors"
            health_status=1
        fi
        
        # Check log file sizes
        local large_logs=$(find "$log_dir" -name "*.log" -size +100M 2>/dev/null | wc -l)
        if [ "$large_logs" -gt 0 ]; then
            log_warning "Found $large_logs large log files (>100MB)"
        fi
        
        log_success "Log files check completed"
    else
        log_warning "Log directory not found: $log_dir"
    fi
    
    return $health_status
}

# Function to generate health report
generate_health_report() {
    local overall_status=$1
    
    log_info "Generating health report..."
    
    local report_file="/tmp/health_report_$(date +%Y%m%d_%H%M%S).txt"
    
    {
        echo "Mingus Application Health Report"
        echo "Generated: $(date)"
        echo "Overall Status: $([ $overall_status -eq 0 ] && echo "HEALTHY" || echo "UNHEALTHY")"
        echo ""
        echo "System Information:"
        echo "- Hostname: $(hostname)"
        echo "- Uptime: $(uptime)"
        echo "- Load Average: $(uptime | awk -F'load average:' '{print $2}')"
        echo ""
        echo "Resource Usage:"
        echo "- CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)%"
        echo "- Memory: $(free | grep Mem | awk '{printf "%.1f%%", $3/$2 * 100.0}')"
        echo "- Disk: $(df / | tail -1 | awk '{print $5}')"
        echo ""
        echo "Application Status:"
        if command -v kubectl >/dev/null 2>&1; then
            kubectl get pods -l app=$APP_NAME 2>/dev/null || echo "No pods found"
        fi
        echo ""
        echo "Recent Logs:"
        tail -20 /app/logs/*.log 2>/dev/null || echo "No logs found"
    } > "$report_file"
    
    log_success "Health report generated: $report_file"
    echo "$report_file"
}

# Function to send alerts
send_alert() {
    local status=$1
    local message=$2
    
    log_info "Sending health alert..."
    
    # Send Slack notification
    if [ ! -z "$SLACK_WEBHOOK_URL" ]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"Health Check $status: $message\"}" \
            "$SLACK_WEBHOOK_URL" 2>/dev/null || true
    fi
    
    # Send email notification
    if [ ! -z "$ALERT_EMAIL" ]; then
        echo "Health Check $status: $message" | mail -s "Mingus Health Alert" "$ALERT_EMAIL" 2>/dev/null || true
    fi
    
    log_success "Alert sent"
}

# Main health check function
main() {
    log_info "Starting comprehensive health check..."
    
    local overall_status=0
    local failed_checks=()
    
    # Run all health checks
    if ! check_application_health; then
        overall_status=1
        failed_checks+=("Application")
    fi
    
    if ! check_system_resources; then
        overall_status=1
        failed_checks+=("System Resources")
    fi
    
    if ! check_database_health; then
        overall_status=1
        failed_checks+=("Database")
    fi
    
    if ! check_redis_health; then
        overall_status=1
        failed_checks+=("Redis")
    fi
    
    if ! check_container_health; then
        overall_status=1
        failed_checks+=("Containers")
    fi
    
    if ! check_network_connectivity; then
        overall_status=1
        failed_checks+=("Network")
    fi
    
    if ! check_log_files; then
        overall_status=1
        failed_checks+=("Log Files")
    fi
    
    # Generate report
    local report_file=$(generate_health_report $overall_status)
    
    # Display summary
    echo ""
    log_info "Health Check Summary:"
    if [ $overall_status -eq 0 ]; then
        log_success "All systems are healthy!"
    else
        log_error "Health check failed for: ${failed_checks[*]}"
        send_alert "FAILED" "Failed checks: ${failed_checks[*]}"
    fi
    
    echo "Report saved to: $report_file"
    
    return $overall_status
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  -v, --verbose  Verbose output"
    echo "  -r, --report   Generate detailed report only"
    echo ""
    echo "Environment Variables:"
    echo "  DATABASE_URL   PostgreSQL connection string"
    echo "  REDIS_URL      Redis connection string"
    echo "  SLACK_WEBHOOK_URL  Slack webhook for alerts"
    echo "  ALERT_EMAIL    Email address for alerts"
}

# Parse command line arguments
VERBOSE=0
REPORT_ONLY=0

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_usage
            exit 0
            ;;
        -v|--verbose)
            VERBOSE=1
            shift
            ;;
        -r|--report)
            REPORT_ONLY=1
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Execute main function
main "$@" 