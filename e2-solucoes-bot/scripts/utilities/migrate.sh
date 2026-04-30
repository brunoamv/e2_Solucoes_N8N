#!/bin/bash

# Database Migration Script for E2 Soluções Bot
# Safe database migration execution with backup and rollback capabilities
# Requires: PostgreSQL client tools, environment variables from .env

set -e  # Exit on error

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   E2 Soluções - Database Migration Tool         ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════╝${NC}"
echo ""

# Load environment variables
if [ -f "../.env" ]; then
    export $(cat ../.env | grep -v '^#' | xargs)
    echo -e "${GREEN}✓${NC} Environment variables loaded"
else
    echo -e "${RED}✗${NC} .env file not found. Please create it with database credentials."
    exit 1
fi

# Configuration
MIGRATIONS_DIR="../database/migrations"
BACKUP_DIR="../backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
MIGRATION_BACKUP="migration_backup_${TIMESTAMP}.sql"

# Check if running inside Docker or host
if [ -f "/.dockerenv" ]; then
    PGHOST="postgres"
    PGPORT="5432"
else
    PGHOST="localhost"
    PGPORT="${POSTGRES_PORT:-5432}"
fi

# Helper function to execute SQL
execute_sql() {
    local sql=$1
    PGPASSWORD="${POSTGRES_PASSWORD}" psql \
        -h "${PGHOST}" \
        -p "${PGPORT}" \
        -U "${POSTGRES_USER}" \
        -d "${POSTGRES_DB}" \
        -c "${sql}"
}

# Helper function to execute SQL file
execute_sql_file() {
    local file=$1
    PGPASSWORD="${POSTGRES_PASSWORD}" psql \
        -h "${PGHOST}" \
        -p "${PGPORT}" \
        -U "${POSTGRES_USER}" \
        -d "${POSTGRES_DB}" \
        -f "${file}"
}

# Create migrations table if it doesn't exist
create_migrations_table() {
    echo -e "${YELLOW}📋 Initializing migrations tracking...${NC}"

    execute_sql "
        CREATE TABLE IF NOT EXISTS schema_migrations (
            id SERIAL PRIMARY KEY,
            version VARCHAR(255) UNIQUE NOT NULL,
            applied_at TIMESTAMP DEFAULT NOW(),
            description TEXT,
            checksum VARCHAR(64)
        );
    " >/dev/null 2>&1

    echo -e "${GREEN}✓${NC} Migrations table ready"
}

# Create pre-migration backup
create_backup() {
    echo ""
    echo -e "${YELLOW}💾 Creating pre-migration backup...${NC}"

    mkdir -p "$BACKUP_DIR"

    PGPASSWORD="${POSTGRES_PASSWORD}" pg_dump \
        -h "${PGHOST}" \
        -p "${PGPORT}" \
        -U "${POSTGRES_USER}" \
        -d "${POSTGRES_DB}" \
        --clean \
        --if-exists \
        > "${BACKUP_DIR}/${MIGRATION_BACKUP}"

    if [ $? -eq 0 ]; then
        gzip "${BACKUP_DIR}/${MIGRATION_BACKUP}"
        SIZE=$(du -h "${BACKUP_DIR}/${MIGRATION_BACKUP}.gz" | cut -f1)
        echo -e "${GREEN}✓${NC} Backup created: ${MIGRATION_BACKUP}.gz (${SIZE})"
        return 0
    else
        echo -e "${RED}✗${NC} Backup failed!"
        return 1
    fi
}

# Get applied migrations
get_applied_migrations() {
    execute_sql "SELECT version FROM schema_migrations ORDER BY version;" 2>/dev/null | tail -n +3 | head -n -2 || echo ""
}

# Calculate file checksum
calculate_checksum() {
    local file=$1
    sha256sum "$file" | cut -d' ' -f1
}

# Apply single migration
apply_migration() {
    local migration_file=$1
    local version=$(basename "$migration_file" .sql)
    local description=$(head -n 1 "$migration_file" | sed 's/--//' | xargs)
    local checksum=$(calculate_checksum "$migration_file")

    echo ""
    echo -e "${BLUE}🔄 Applying migration: ${version}${NC}"
    echo -e "   Description: ${description}"

    # Begin transaction
    PGPASSWORD="${POSTGRES_PASSWORD}" psql \
        -h "${PGHOST}" \
        -p "${PGPORT}" \
        -U "${POSTGRES_USER}" \
        -d "${POSTGRES_DB}" \
        <<EOF
BEGIN;

-- Execute migration file
\i ${migration_file}

-- Record migration
INSERT INTO schema_migrations (version, description, checksum)
VALUES ('${version}', '${description}', '${checksum}');

COMMIT;
EOF

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} Migration applied successfully"
        return 0
    else
        echo -e "${RED}✗${NC} Migration failed! Rolling back..."
        return 1
    fi
}

# Rollback to backup
rollback() {
    local backup_file=$1

    echo ""
    echo -e "${RED}⏮️  Rolling back to backup...${NC}"

    if [ -f "${backup_file}" ]; then
        gunzip -c "${backup_file}" | PGPASSWORD="${POSTGRES_PASSWORD}" psql \
            -h "${PGHOST}" \
            -p "${PGPORT}" \
            -U "${POSTGRES_USER}" \
            -d "${POSTGRES_DB}" \
            >/dev/null 2>&1

        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓${NC} Database restored to pre-migration state"
        else
            echo -e "${RED}✗${NC} Rollback failed! Manual intervention required."
        fi
    else
        echo -e "${RED}✗${NC} Backup file not found! Manual recovery needed."
    fi
}

# Main migration flow
main() {
    # Check if migrations directory exists
    if [ ! -d "$MIGRATIONS_DIR" ]; then
        echo -e "${YELLOW}⚠${NC}  Migrations directory not found: ${MIGRATIONS_DIR}"
        echo -e "   Creating directory..."
        mkdir -p "$MIGRATIONS_DIR"
        echo -e "${GREEN}✓${NC} Directory created"
        echo ""
        echo "Add migration files to ${MIGRATIONS_DIR}/"
        echo "Format: YYYYMMDD_HHMMSS_description.sql"
        exit 0
    fi

    # Initialize migrations tracking
    create_migrations_table

    # Create backup
    if ! create_backup; then
        echo -e "${RED}✗${NC} Cannot proceed without backup. Aborting."
        exit 1
    fi

    # Get applied migrations
    APPLIED_MIGRATIONS=$(get_applied_migrations)

    # Find pending migrations
    echo ""
    echo -e "${YELLOW}🔍 Scanning for pending migrations...${NC}"

    PENDING_MIGRATIONS=()
    for migration_file in $(ls ${MIGRATIONS_DIR}/*.sql 2>/dev/null | sort); do
        version=$(basename "$migration_file" .sql)

        # Check if already applied
        if echo "$APPLIED_MIGRATIONS" | grep -q "^${version}$"; then
            echo -e "  ${GREEN}✓${NC} ${version} (already applied)"
        else
            echo -e "  ${BLUE}→${NC} ${version} (pending)"
            PENDING_MIGRATIONS+=("$migration_file")
        fi
    done

    # Check if there are pending migrations
    if [ ${#PENDING_MIGRATIONS[@]} -eq 0 ]; then
        echo ""
        echo -e "${GREEN}✓${NC} No pending migrations. Database is up to date."
        exit 0
    fi

    # Confirm migration execution
    echo ""
    echo -e "${YELLOW}⚠️  Found ${#PENDING_MIGRATIONS[@]} pending migration(s).${NC}"
    read -p "Do you want to apply these migrations? (yes/no): " CONFIRM

    if [ "$CONFIRM" != "yes" ]; then
        echo -e "${YELLOW}⚠${NC}  Migration cancelled by user."
        exit 0
    fi

    # Apply migrations
    echo ""
    echo -e "${BLUE}🚀 Applying migrations...${NC}"

    SUCCESS_COUNT=0
    FAILED_MIGRATION=""

    for migration_file in "${PENDING_MIGRATIONS[@]}"; do
        if apply_migration "$migration_file"; then
            ((SUCCESS_COUNT++))
        else
            FAILED_MIGRATION="$migration_file"
            break
        fi
    done

    # Check results
    echo ""
    if [ -z "$FAILED_MIGRATION" ]; then
        echo -e "${GREEN}╔══════════════════════════════════════════════════╗${NC}"
        echo -e "${GREEN}║     ✅ All Migrations Applied Successfully!      ║${NC}"
        echo -e "${GREEN}╚══════════════════════════════════════════════════╝${NC}"
        echo ""
        echo -e "Applied: ${SUCCESS_COUNT} migration(s)"
        echo -e "Backup: ${BACKUP_DIR}/${MIGRATION_BACKUP}.gz"
    else
        echo -e "${RED}╔══════════════════════════════════════════════════╗${NC}"
        echo -e "${RED}║        ⚠️  Migration Failed!                      ║${NC}"
        echo -e "${RED}╚══════════════════════════════════════════════════╝${NC}"
        echo ""
        echo -e "Applied: ${SUCCESS_COUNT} migration(s)"
        echo -e "Failed at: $(basename $FAILED_MIGRATION)"
        echo ""
        read -p "Do you want to rollback to pre-migration state? (yes/no): " ROLLBACK_CONFIRM

        if [ "$ROLLBACK_CONFIRM" == "yes" ]; then
            rollback "${BACKUP_DIR}/${MIGRATION_BACKUP}.gz"
        else
            echo -e "${YELLOW}⚠${NC}  Database left in current state. Manual intervention required."
        fi

        exit 1
    fi

    # Show current migration status
    echo ""
    echo -e "${BLUE}📊 Current Migration Status:${NC}"
    execute_sql "SELECT version, applied_at, description FROM schema_migrations ORDER BY version DESC LIMIT 5;"
}

# Run main function
main
