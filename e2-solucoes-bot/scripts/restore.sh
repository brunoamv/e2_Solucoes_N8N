#!/bin/bash

# ============================================================================
# E2 Soluções Bot - Database Restore Script
# ============================================================================
# Restaura backup do banco de dados PostgreSQL
# Usage: ./restore.sh <backup-file>
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Default backup directory
BACKUP_DIR="${PROJECT_ROOT}/backups"

# Function to print colored messages
print_info() {
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

# Function to check if Docker containers are running
check_containers() {
    print_info "Checking Docker containers..."

    if ! docker ps | grep -q e2-postgres; then
        print_error "PostgreSQL container is not running"
        print_info "Start containers with: ./scripts/start-dev.sh"
        exit 1
    fi

    print_success "Containers are running"
}

# Function to restore database from backup
restore_database() {
    local backup_file=$1

    if [ ! -f "$backup_file" ]; then
        print_error "Backup file not found: $backup_file"
        exit 1
    fi

    print_info "Backup file: $backup_file"
    print_info "File size: $(du -h "$backup_file" | cut -f1)"

    # Extract database name from env
    source "${PROJECT_ROOT}/docker/.env.dev"

    print_warning "This will REPLACE all data in database: ${POSTGRES_DB}"
    read -p "Are you sure you want to continue? (yes/no): " confirm

    if [ "$confirm" != "yes" ]; then
        print_info "Restore cancelled"
        exit 0
    fi

    print_info "Stopping dependent services..."
    docker-compose -f "${PROJECT_ROOT}/docker/docker-compose-dev.yml" stop n8n 2>/dev/null || true

    print_info "Dropping existing database..."
    docker exec e2-postgres psql -U "${POSTGRES_USER}" -c "DROP DATABASE IF EXISTS ${POSTGRES_DB};" 2>/dev/null || true

    print_info "Creating fresh database..."
    docker exec e2-postgres psql -U "${POSTGRES_USER}" -c "CREATE DATABASE ${POSTGRES_DB};" 2>/dev/null || true

    print_info "Restoring database from backup..."

    if [[ "$backup_file" == *.sql.gz ]]; then
        # Compressed backup
        gunzip -c "$backup_file" | docker exec -i e2-postgres psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}"
    else
        # Uncompressed backup
        docker exec -i e2-postgres psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" < "$backup_file"
    fi

    if [ $? -eq 0 ]; then
        print_success "Database restored successfully!"
    else
        print_error "Database restore failed"
        exit 1
    fi

    print_info "Restarting dependent services..."
    docker-compose -f "${PROJECT_ROOT}/docker/docker-compose-dev.yml" start n8n

    print_success "Restore complete!"
}

# Function to list available backups
list_backups() {
    print_info "Available backups in ${BACKUP_DIR}:"
    echo ""

    if [ ! -d "$BACKUP_DIR" ]; then
        print_warning "No backup directory found"
        return
    fi

    local backups=$(find "$BACKUP_DIR" -name "*.sql*" -type f | sort -r)

    if [ -z "$backups" ]; then
        print_warning "No backups found"
        return
    fi

    local count=1
    while IFS= read -r backup; do
        local size=$(du -h "$backup" | cut -f1)
        local date=$(stat -c %y "$backup" | cut -d' ' -f1,2 | cut -d'.' -f1)
        echo "  ${count}. $(basename "$backup")"
        echo "     Size: ${size} | Date: ${date}"
        echo ""
        ((count++))
    done <<< "$backups"
}

# Function to restore latest backup
restore_latest() {
    print_info "Finding latest backup..."

    if [ ! -d "$BACKUP_DIR" ]; then
        print_error "No backup directory found"
        exit 1
    fi

    local latest_backup=$(find "$BACKUP_DIR" -name "*.sql*" -type f | sort -r | head -n1)

    if [ -z "$latest_backup" ]; then
        print_error "No backups found"
        exit 1
    fi

    print_info "Latest backup: $(basename "$latest_backup")"
    restore_database "$latest_backup"
}

# Main execution
main() {
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║          E2 Soluções Bot - Database Restore                   ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""

    # Check if backup file provided
    if [ $# -eq 0 ]; then
        print_info "No backup file specified"
        echo ""
        list_backups
        echo ""
        print_info "Usage:"
        echo "  ./restore.sh <backup-file>     # Restore specific backup"
        echo "  ./restore.sh --latest          # Restore latest backup"
        echo "  ./restore.sh --list            # List available backups"
        exit 0
    fi

    case "$1" in
        --list)
            list_backups
            ;;
        --latest)
            check_containers
            restore_latest
            ;;
        --help)
            echo "Usage: $0 [OPTIONS] [BACKUP_FILE]"
            echo ""
            echo "Options:"
            echo "  --list          List available backups"
            echo "  --latest        Restore latest backup"
            echo "  --help          Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 backups/e2_bot_20250615_143022.sql.gz"
            echo "  $0 --latest"
            ;;
        *)
            check_containers
            restore_database "$1"
            ;;
    esac
}

main "$@"
