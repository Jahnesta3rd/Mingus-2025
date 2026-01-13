#!/bin/bash
# ============================================================================
# Mingus Application - Database Migration Script
# Runs database migrations safely with backup
# ============================================================================

set -e
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKUP_DIR="$PROJECT_ROOT/backups"
MIGRATIONS_DIR="$PROJECT_ROOT/migrations"

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

cd "$PROJECT_ROOT"

log "Starting database migration..."

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Backup database
DB_FILE="$PROJECT_ROOT/assessments.db"
if [ -f "$DB_FILE" ]; then
    BACKUP_FILE="$BACKUP_DIR/assessments_$(date +%Y%m%d_%H%M%S).db"
    log "Creating database backup..."
    cp "$DB_FILE" "$BACKUP_FILE"
    success "Database backed up to: $BACKUP_FILE"
else
    warning "Database file not found, will be created"
fi

# Run migrations
if [ -d "$MIGRATIONS_DIR" ]; then
    log "Running migrations..."
    
    # Check for Python migration script
    if [ -f "$MIGRATIONS_DIR/migrate.py" ]; then
        python3 "$MIGRATIONS_DIR/migrate.py"
        success "Migrations completed"
    elif [ -f "$MIGRATIONS_DIR/versions" ]; then
        # Use Flask-Migrate if available
        if command -v flask &> /dev/null; then
            export FLASK_APP=app.py
            flask db upgrade
            success "Flask migrations completed"
        else
            warning "Flask not found, skipping Flask-Migrate migrations"
        fi
    else
        warning "No migration scripts found"
    fi
else
    warning "Migrations directory not found"
fi

# Verify database
if [ -f "$DB_FILE" ]; then
    log "Verifying database..."
    python3 -c "
import sqlite3
conn = sqlite3.connect('$DB_FILE')
cursor = conn.cursor()
cursor.execute('SELECT name FROM sqlite_master WHERE type=\"table\"')
tables = cursor.fetchall()
print(f'Database verified: {len(tables)} tables found')
conn.close()
" || warning "Database verification failed"
fi

success "Database migration completed"
