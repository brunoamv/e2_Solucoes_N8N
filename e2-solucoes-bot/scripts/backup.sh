#!/bin/bash

# PostgreSQL Backup Script for E2 Soluções Bot
# Automated database backup with retention policy and compression
# Requires: PostgreSQL client tools, environment variables from .env

set -e  # Exit on error

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   E2 Soluções - Database Backup Tool            ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════╝${NC}"
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
BACKUP_DIR="../backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="e2bot_backup_${TIMESTAMP}.sql"
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-30}  # Default 30 days

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

echo -e "${YELLOW}📦 Starting database backup...${NC}"
echo ""

# Check if running inside Docker or host
if [ -f "/.dockerenv" ]; then
    # Running inside container
    PGHOST="postgres"
    PGPORT="5432"
else
    # Running on host, connect to Docker container
    PGHOST="localhost"
    PGPORT="${POSTGRES_PORT:-5432}"
fi

# Perform backup using pg_dump
echo -e "🔄 Dumping database: ${POSTGRES_DB}"

PGPASSWORD="${POSTGRES_PASSWORD}" pg_dump \
    -h "${PGHOST}" \
    -p "${PGPORT}" \
    -U "${POSTGRES_USER}" \
    -d "${POSTGRES_DB}" \
    --verbose \
    --clean \
    --if-exists \
    --create \
    --format=plain \
    --encoding=UTF8 \
    > "${BACKUP_DIR}/${BACKUP_FILE}" 2>&1

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓${NC} Database dump created successfully"

    # Compress backup
    echo -e "🗜️  Compressing backup..."
    gzip "${BACKUP_DIR}/${BACKUP_FILE}"
    BACKUP_FILE="${BACKUP_FILE}.gz"

    # Get file size
    SIZE=$(du -h "${BACKUP_DIR}/${BACKUP_FILE}" | cut -f1)
    echo -e "${GREEN}✓${NC} Backup compressed: ${SIZE}"

    # Verify backup integrity
    echo -e "🔍 Verifying backup integrity..."
    if gzip -t "${BACKUP_DIR}/${BACKUP_FILE}" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} Backup file integrity verified"
    else
        echo -e "${RED}✗${NC} Backup file is corrupted!"
        exit 1
    fi

    # Generate checksum
    echo -e "🔐 Generating checksum..."
    CHECKSUM=$(sha256sum "${BACKUP_DIR}/${BACKUP_FILE}" | cut -d' ' -f1)
    echo "${CHECKSUM}" > "${BACKUP_DIR}/${BACKUP_FILE}.sha256"
    echo -e "${GREEN}✓${NC} Checksum saved"

    # List database statistics
    echo ""
    echo -e "${YELLOW}📊 Database Statistics:${NC}"

    TABLES_COUNT=$(PGPASSWORD="${POSTGRES_PASSWORD}" psql \
        -h "${PGHOST}" \
        -p "${PGPORT}" \
        -U "${POSTGRES_USER}" \
        -d "${POSTGRES_DB}" \
        -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")

    TOTAL_SIZE=$(PGPASSWORD="${POSTGRES_PASSWORD}" psql \
        -h "${PGHOST}" \
        -p "${PGPORT}" \
        -U "${POSTGRES_USER}" \
        -d "${POSTGRES_DB}" \
        -t -c "SELECT pg_size_pretty(pg_database_size('${POSTGRES_DB}'));")

    echo -e "  Tables: ${TABLES_COUNT// /}"
    echo -e "  Database Size: ${TOTAL_SIZE// /}"
    echo -e "  Backup Size: ${SIZE}"

else
    echo ""
    echo -e "${RED}✗${NC} Database backup failed!"
    exit 1
fi

# Cleanup old backups (retention policy)
echo ""
echo -e "${YELLOW}🗑️  Cleaning up old backups (retention: ${RETENTION_DAYS} days)...${NC}"

OLD_BACKUPS=$(find "${BACKUP_DIR}" -name "e2bot_backup_*.sql.gz" -type f -mtime +${RETENTION_DAYS})

if [ -n "$OLD_BACKUPS" ]; then
    DELETED_COUNT=0
    while IFS= read -r backup; do
        if [ -f "$backup" ]; then
            echo -e "  Deleting: $(basename $backup)"
            rm -f "$backup"
            rm -f "${backup}.sha256"  # Also remove checksum file
            ((DELETED_COUNT++))
        fi
    done <<< "$OLD_BACKUPS"

    echo -e "${GREEN}✓${NC} Removed ${DELETED_COUNT} old backup(s)"
else
    echo -e "${GREEN}✓${NC} No old backups to clean up"
fi

# List remaining backups
echo ""
echo -e "${YELLOW}📋 Current Backups:${NC}"
ls -lh "${BACKUP_DIR}"/e2bot_backup_*.sql.gz 2>/dev/null | awk '{print "  " $9 " (" $5 ")"}'

# Summary
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║          ✅ Backup Completed Successfully!       ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "📁 Backup Location: ${BACKUP_DIR}/${BACKUP_FILE}"
echo -e "🔐 Checksum: ${CHECKSUM:0:16}..."
echo -e "📅 Timestamp: $(date)"
echo ""

# Optional: Upload to cloud storage (uncomment and configure)
# if [ -n "${BACKUP_S3_BUCKET}" ]; then
#     echo -e "${YELLOW}☁️  Uploading to S3...${NC}"
#     aws s3 cp "${BACKUP_DIR}/${BACKUP_FILE}" "s3://${BACKUP_S3_BUCKET}/e2bot-backups/" --storage-class STANDARD_IA
#     echo -e "${GREEN}✓${NC} Backup uploaded to S3"
# fi

exit 0
