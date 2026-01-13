#!/bin/bash
# ============================================================================
# Mingus Application - Configure Automatic Service Restart
# Configures systemd services and monitoring for automatic restart on failure
# ============================================================================

set -e
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
    exit 1
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    error "This script must be run as root (use sudo)"
fi

log "Configuring automatic service restart on failure..."

# Install enhanced systemd service files
log "Installing enhanced systemd service files..."

if [ -f "$SCRIPT_DIR/systemd/mingus-backend.service" ]; then
    cp "$SCRIPT_DIR/systemd/mingus-backend.service" /etc/systemd/system/
    success "Backend service file installed"
else
    error "Backend service file not found"
fi

if [ -f "$SCRIPT_DIR/systemd/mingus-frontend.service" ]; then
    cp "$SCRIPT_DIR/systemd/mingus-frontend.service" /etc/systemd/system/
    success "Frontend service file installed"
else
    error "Frontend service file not found"
fi

# Install monitoring service
if [ -f "$SCRIPT_DIR/systemd/mingus-monitor.service" ]; then
    cp "$SCRIPT_DIR/systemd/mingus-monitor.service" /etc/systemd/system/
    success "Monitor service file installed"
else
    warning "Monitor service file not found"
fi

# Reload systemd
log "Reloading systemd daemon..."
systemctl daemon-reload
success "Systemd daemon reloaded"

# Configure service overrides (optional, for additional restart policies)
log "Configuring service overrides..."

# Backend service override
mkdir -p /etc/systemd/system/mingus-backend.service.d/
cat > /etc/systemd/system/mingus-backend.service.d/override.conf << 'EOF'
[Service]
# Additional restart policies
Restart=always
RestartSec=10

# On failure actions
OnFailure=mingus-backend-failure@%n.service

# Watchdog (if supported by application)
# WatchdogSec=30
EOF
success "Backend service override configured"

# Frontend service override
mkdir -p /etc/systemd/system/mingus-frontend.service.d/
cat > /etc/systemd/system/mingus-frontend.service.d/override.conf << 'EOF'
[Service]
# Additional restart policies
Restart=always
RestartSec=10

# On failure actions
OnFailure=mingus-frontend-failure@%n.service
EOF
success "Frontend service override configured"

# Create failure notification service (optional)
log "Creating failure notification service..."

cat > /etc/systemd/system/mingus-backend-failure@.service << 'EOF'
[Unit]
Description=Backend Service Failure Notification
After=mingus-backend.service

[Service]
Type=oneshot
ExecStart=/bin/bash -c 'echo "Mingus backend service failed at $(date)" >> /var/log/mingus-app/failures.log'
EOF

cat > /etc/systemd/system/mingus-frontend-failure@.service << 'EOF'
[Unit]
Description=Frontend Service Failure Notification
After=mingus-frontend.service

[Service]
Type=oneshot
ExecStart=/bin/bash -c 'echo "Mingus frontend service failed at $(date)" >> /var/log/mingus-app/failures.log'
EOF

success "Failure notification services created"

# Enable and start monitoring service
if systemctl list-unit-files | grep -q mingus-monitor.service; then
    log "Enabling monitoring service..."
    systemctl enable mingus-monitor.service
    systemctl start mingus-monitor.service
    success "Monitoring service enabled and started"
fi

# Reload systemd again
systemctl daemon-reload

# Show current configuration
log "Current service configuration:"
echo ""
echo "Backend service:"
systemctl show mingus-backend.service | grep -E "^(Restart|RestartSec|StartLimit)" || true
echo ""
echo "Frontend service:"
systemctl show mingus-frontend.service | grep -E "^(Restart|RestartSec|StartLimit)" || true

# Test restart functionality
log "Testing restart functionality..."
read -p "Do you want to test the restart functionality? (yes/no): " test_restart

if [ "$test_restart" = "yes" ]; then
    log "Stopping backend service to test auto-restart..."
    systemctl stop mingus-backend.service
    sleep 2
    
    if systemctl is-active --quiet mingus-backend.service; then
        success "Backend service auto-restarted successfully"
    else
        warning "Backend service did not auto-restart. Check configuration."
    fi
fi

success "Automatic restart configuration completed"

log ""
log "Configuration summary:"
log "  - Services configured with Restart=always"
log "  - Restart delay: 10 seconds"
log "  - Start limit: 5 restarts per 5 minutes"
log "  - Monitoring service: Enabled"
log "  - Failure notifications: Configured"
log ""
log "To view service status:"
log "  sudo systemctl status mingus-backend"
log "  sudo systemctl status mingus-frontend"
log "  sudo systemctl status mingus-monitor"
log ""
log "To view restart history:"
log "  journalctl -u mingus-backend -f"
log "  journalctl -u mingus-frontend -f"
