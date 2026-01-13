#!/bin/bash
# ============================================================================
# Mingus Application - Service Monitoring and Auto-Restart Script
# Monitors services and automatically restarts them on failure
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_FILE="$PROJECT_ROOT/logs/service_monitor_$(date +%Y%m%d).log"
MAX_RESTARTS=5
RESTART_WINDOW=300  # 5 minutes

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Create logs directory
mkdir -p "$(dirname "$LOG_FILE")"

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}✅ $1${NC}" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}❌ $1${NC}" | tee -a "$LOG_FILE"
}

# Track restart counts
RESTART_COUNT_FILE="$PROJECT_ROOT/.service_restart_counts"
declare -A RESTART_COUNTS
declare -A LAST_RESTART_TIME

# Load restart counts
load_restart_counts() {
    if [ -f "$RESTART_COUNT_FILE" ]; then
        while IFS='=' read -r service count time; do
            RESTART_COUNTS[$service]=${count:-0}
            LAST_RESTART_TIME[$service]=${time:-0}
        done < "$RESTART_COUNT_FILE"
    fi
}

# Save restart counts
save_restart_counts() {
    > "$RESTART_COUNT_FILE"
    for service in "${!RESTART_COUNTS[@]}"; do
        echo "$service=${RESTART_COUNTS[$service]}=${LAST_RESTART_TIME[$service]}" >> "$RESTART_COUNT_FILE"
    done
}

# Reset restart count if outside window
reset_restart_count_if_needed() {
    local service=$1
    local current_time=$(date +%s)
    local last_restart=${LAST_RESTART_TIME[$service]:-0}
    
    if [ $((current_time - last_restart)) -gt $RESTART_WINDOW ]; then
        RESTART_COUNTS[$service]=0
        log "Reset restart count for $service (outside time window)"
    fi
}

# Check if service should be restarted
should_restart() {
    local service=$1
    local count=${RESTART_COUNTS[$service]:-0}
    
    if [ $count -ge $MAX_RESTARTS ]; then
        return 1  # Don't restart
    fi
    return 0  # Can restart
}

# Increment restart count
increment_restart_count() {
    local service=$1
    local current_time=$(date +%s)
    
    reset_restart_count_if_needed "$service"
    
    RESTART_COUNTS[$service]=$((${RESTART_COUNTS[$service]:-0} + 1))
    LAST_RESTART_TIME[$service]=$current_time
    
    save_restart_counts
}

# Check service status
check_service() {
    local service=$1
    
    if systemctl is-active --quiet "$service" 2>/dev/null; then
        return 0  # Service is active
    else
        return 1  # Service is not active
    fi
}

# Restart service
restart_service() {
    local service=$1
    
    log "Attempting to restart service: $service"
    
    # Check if we should restart
    if ! should_restart "$service"; then
        error "Service $service has exceeded max restart attempts ($MAX_RESTARTS). Manual intervention required."
        # Send alert (implement your alerting mechanism here)
        send_alert "$service" "Service exceeded max restart attempts"
        return 1
    fi
    
    # Increment restart count
    increment_restart_count "$service"
    local count=${RESTART_COUNTS[$service]}
    
    log "Restart attempt $count/$MAX_RESTARTS for $service"
    
    # Restart the service
    if sudo systemctl restart "$service"; then
        # Wait a bit and check if it started successfully
        sleep 5
        
        if check_service "$service"; then
            success "Service $service restarted successfully (attempt $count)"
            return 0
        else
            warning "Service $service restart attempted but not active"
            return 1
        fi
    else
        error "Failed to restart service $service"
        return 1
    fi
}

# Send alert (implement your alerting mechanism)
send_alert() {
    local service=$1
    local message=$2
    
    log "ALERT: $service - $message"
    
    # Example: Send email
    # echo "$message" | mail -s "Mingus App Alert: $service" admin@example.com
    
    # Example: Send to webhook
    # curl -X POST https://hooks.slack.com/your-webhook -d "{\"text\":\"$message\"}"
    
    # Example: Write to alert log
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] ALERT: $service - $message" >> "$PROJECT_ROOT/logs/alerts.log"
}

# Monitor a service
monitor_service() {
    local service=$1
    
    if ! check_service "$service"; then
        warning "Service $service is not active"
        restart_service "$service"
    else
        # Service is active, reset count if needed
        reset_restart_count_if_needed "$service"
        if [ ${RESTART_COUNTS[$service]:-0} -gt 0 ]; then
            log "Service $service is healthy, resetting restart count"
            RESTART_COUNTS[$service]=0
            save_restart_counts
        fi
    fi
}

# Health check for service
health_check_service() {
    local service=$1
    local health_url=$2
    
    if [ -n "$health_url" ]; then
        if curl -f -s --max-time 5 "$health_url" > /dev/null 2>&1; then
            return 0
        else
            return 1
        fi
    fi
    
    # Fallback to systemd status
    return $(check_service "$service" && echo 0 || echo 1)
}

# Main monitoring function
main() {
    log "Starting service monitoring..."
    
    load_restart_counts
    
    # Monitor backend service
    monitor_service "mingus-backend"
    
    # Health check for backend
    if check_service "mingus-backend"; then
        if ! health_check_service "mingus-backend" "${BACKEND_URL:-http://localhost:5001}/health"; then
            warning "Backend service is running but health check failed"
            # Optionally restart if health check fails multiple times
        fi
    fi
    
    # Monitor frontend service
    monitor_service "mingus-frontend"
    
    # Health check for frontend
    if check_service "mingus-frontend"; then
        if ! health_check_service "mingus-frontend" "${FRONTEND_URL:-http://localhost:3000}"; then
            warning "Frontend service is running but health check failed"
        fi
    fi
    
    log "Service monitoring cycle completed"
}

# Run in daemon mode
run_daemon() {
    local interval=${MONITOR_INTERVAL:-30}
    
    log "Starting service monitor daemon (checking every ${interval}s)"
    
    while true; do
        main
        sleep $interval
    done
}

# Show usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --daemon          Run in daemon mode (continuous monitoring)"
    echo "  --interval SEC    Set monitoring interval in seconds (default: 30)"
    echo "  --max-restarts N  Set maximum restart attempts (default: 5)"
    echo "  --reset           Reset restart counts"
    echo "  --status          Show current service status and restart counts"
    echo "  --help            Show this help message"
    exit 0
}

# Reset restart counts
reset_counts() {
    > "$RESTART_COUNT_FILE"
    log "Restart counts reset"
}

# Show status
show_status() {
    echo "Service Status and Restart Counts"
    echo "=================================="
    echo ""
    
    for service in mingus-backend mingus-frontend; do
        if check_service "$service"; then
            echo -e "${GREEN}✅ $service: ACTIVE${NC}"
        else
            echo -e "${RED}❌ $service: INACTIVE${NC}"
        fi
        
        local count=${RESTART_COUNTS[$service]:-0}
        local last_restart=${LAST_RESTART_TIME[$service]:-0}
        
        if [ $last_restart -gt 0 ]; then
            local time_str=$(date -d "@$last_restart" '+%Y-%m-%d %H:%M:%S' 2>/dev/null || echo "Unknown")
            echo "  Restart count: $count/$MAX_RESTARTS"
            echo "  Last restart: $time_str"
        else
            echo "  Restart count: 0/$MAX_RESTARTS"
        fi
        echo ""
    done
}

# Parse arguments
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    usage
fi

if [ "$1" = "--reset" ]; then
    reset_counts
    exit 0
fi

if [ "$1" = "--status" ]; then
    load_restart_counts
    show_status
    exit 0
fi

if [ "$1" = "--daemon" ]; then
    run_daemon
else
    # Load environment if available
    if [ -f "$PROJECT_ROOT/.env.production" ]; then
        source "$PROJECT_ROOT/.env.production"
    fi
    
    main
fi
