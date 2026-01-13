#!/bin/bash
# ============================================================================
# Mingus Application - Rollback Script
# Rolls back to previous deployment version
# ============================================================================

set -e
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKUP_DIR="$PROJECT_ROOT/backups"
LAST_BACKUP_FILE="$PROJECT_ROOT/.last_backup_path"

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

# Function to list available backups
list_backups() {
    log "Available backups:"
    if [ -d "$BACKUP_DIR" ]; then
        ls -1t "$BACKUP_DIR" | head -10 | nl
    else
        warning "No backups directory found"
    fi
}

# Function to restore from backup
restore_backup() {
    local backup_path=$1
    
    if [ ! -d "$backup_path" ]; then
        error "Backup directory not found: $backup_path"
    fi
    
    log "Restoring from backup: $backup_path"
    
    # Restore database
    if [ -f "$backup_path/assessments.db" ]; then
        log "Restoring database..."
        cp "$backup_path/assessments.db" "$PROJECT_ROOT/assessments.db"
        success "Database restored"
    fi
    
    # Restore environment file
    if [ -f "$backup_path/.env.production" ]; then
        log "Restoring environment file..."
        cp "$backup_path/.env.production" "$PROJECT_ROOT/.env.production"
        success "Environment file restored"
    fi
    
    # Restore backend
    if [ -f "$backup_path/backend.tar.gz" ]; then
        log "Restoring backend..."
        tar -xzf "$backup_path/backend.tar.gz" -C "$PROJECT_ROOT"
        success "Backend restored"
    fi
    
    # Restore frontend
    if [ -f "$backup_path/frontend.tar.gz" ]; then
        log "Restoring frontend..."
        tar -xzf "$backup_path/frontend.tar.gz" -C "$PROJECT_ROOT"
        success "Frontend restored"
    fi
}

# Main rollback function
main() {
    echo -e "${YELLOW}"
    echo "============================================================================"
    echo "  Mingus Application - Rollback"
    echo "============================================================================"
    echo -e "${NC}"
    
    # Check if backup path is provided
    if [ $# -eq 0 ]; then
        # Try to use last backup
        if [ -f "$LAST_BACKUP_FILE" ]; then
            BACKUP_PATH=$(cat "$LAST_BACKUP_FILE")
            log "Using last backup: $BACKUP_PATH"
        else
            error "No backup specified and no last backup found"
        fi
    else
        BACKUP_PATH="$1"
    fi
    
    # Confirm rollback
    warning "This will restore the application from backup: $BACKUP_PATH"
    read -p "Are you sure you want to continue? (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        log "Rollback cancelled"
        exit 0
    fi
    
    # Create backup of current state before rollback
    log "Creating backup of current state..."
    "$SCRIPT_DIR/deploy.sh" --backup-only 2>/dev/null || warning "Could not backup current state"
    
    # Restore from backup
    restore_backup "$BACKUP_PATH"
    
    # Restart services
    log "Restarting services..."
    if systemctl is-active --quiet mingus-app-backend 2>/dev/null; then
        sudo systemctl restart mingus-app-backend
    fi
    
    if systemctl is-active --quiet mingus-app-frontend 2>/dev/null; then
        sudo systemctl restart mingus-app-frontend
    fi
    
    success "Rollback completed"
    
    # Run health check
    log "Running health check..."
    "$SCRIPT_DIR/health_check.sh" || warning "Health check failed"
}

# Show usage
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Usage: $0 [backup_path]"
    echo ""
    echo "Rolls back to a previous deployment version."
    echo ""
    echo "Options:"
    echo "  backup_path    Path to backup directory to restore from"
    echo "  --list         List available backups"
    echo "  --help         Show this help message"
    echo ""
    exit 0
fi

# List backups
if [ "$1" = "--list" ]; then
    list_backups
    exit 0
fi

# Run main function
main "$@"
