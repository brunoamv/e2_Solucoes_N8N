#!/bin/bash
# =====================================
# V58.1 DATABASE ROLLBACK SCRIPT
# =====================================
# Purpose: Complete rollback of V58.1 database changes
# Reverts: Gap #8 (contact_phone), Gap #6 (service_type), Gap #1 (states)
# Date: 2026-03-10
# Author: Claude Code (automated)
# =====================================

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${RED}========================================${NC}"
echo -e "${RED}V58.1 DATABASE ROLLBACK${NC}"
echo -e "${RED}========================================${NC}"
echo ""

# Database connection info
DB_CONTAINER="e2bot-postgres-dev"
DB_USER="postgres"
DB_NAME="e2bot_dev"

# Confirmation prompt
echo -e "${YELLOW}⚠️  WARNING: This will rollback ALL V58.1 database changes!${NC}"
echo -e "${YELLOW}   - Remove contact_phone column${NC}"
echo -e "${YELLOW}   - Restore original service_type constraint${NC}"
echo -e "${YELLOW}   - Restore original state constraint${NC}"
echo ""
read -p "Are you sure you want to continue? (type 'yes' to confirm): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo -e "${RED}Rollback cancelled.${NC}"
    exit 0
fi

echo ""

# Check if container is running
if ! docker ps | grep -q "$DB_CONTAINER"; then
    echo -e "${RED}❌ ERROR: PostgreSQL container not running${NC}"
    echo -e "${YELLOW}   Run: docker-compose up -d${NC}"
    exit 1
fi

echo -e "${GREEN}✅ PostgreSQL container running${NC}"
echo ""

# =====================================
# STEP 1: BACKUP BEFORE ROLLBACK
# =====================================
echo -e "${BLUE}[STEP 1] Creating rollback backup...${NC}"

BACKUP_FILE="/tmp/e2bot_backup_before_rollback_v58_1_$(date +%Y%m%d_%H%M%S).sql"

docker exec "$DB_CONTAINER" pg_dump -U "$DB_USER" "$DB_NAME" > "$BACKUP_FILE" 2>/dev/null

if [ -f "$BACKUP_FILE" ]; then
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo -e "${GREEN}✅ Backup created: $BACKUP_FILE ($BACKUP_SIZE)${NC}"
else
    echo -e "${RED}❌ Failed to create backup${NC}"
    exit 1
fi
echo ""

# =====================================
# STEP 2: EXECUTE ROLLBACK SQL
# =====================================
echo -e "${BLUE}[STEP 2] Executing rollback...${NC}"

ROLLBACK_SQL=$(cat <<'EOF'
BEGIN;

-- =====================================
-- V58.1 ROLLBACK - REVERT ALL CHANGES
-- =====================================

-- ROLLBACK GAP #8: Remove contact_phone column
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='conversations' AND column_name='contact_phone'
    ) THEN
        -- Drop index first
        DROP INDEX IF EXISTS idx_conversations_contact_phone;

        -- Drop column
        ALTER TABLE conversations DROP COLUMN contact_phone;

        RAISE NOTICE 'V58.1 ROLLBACK: contact_phone column removed';
    ELSE
        RAISE NOTICE 'V58.1 ROLLBACK: contact_phone column does not exist';
    END IF;
END $$;

-- ROLLBACK GAP #6: Restore original service_type constraint
DO $$
BEGIN
    -- Drop V58.1 constraint
    IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname='valid_service_v58') THEN
        ALTER TABLE conversations DROP CONSTRAINT valid_service_v58;
        RAISE NOTICE 'V58.1 ROLLBACK: Dropped V58.1 service_type constraint';
    END IF;

    -- Restore V43 constraint (snake_case only)
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='valid_service') THEN
        ALTER TABLE conversations ADD CONSTRAINT valid_service CHECK (
            service_type IS NULL OR
            service_type IN (
                'energia_solar',
                'subestacao',
                'projeto_eletrico',
                'armazenamento_energia',
                'analise_laudo',
                'outro'
            )
        );
        RAISE NOTICE 'V58.1 ROLLBACK: Restored original service_type constraint';
    END IF;
END $$;

-- ROLLBACK GAP #1: Restore original state constraint
DO $$
BEGIN
    -- Drop V58.1 constraint
    IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname='valid_state_v58') THEN
        ALTER TABLE conversations DROP CONSTRAINT valid_state_v58;
        RAISE NOTICE 'V58.1 ROLLBACK: Dropped V58.1 state constraint';
    END IF;

    -- Restore V43 constraint (8 original states)
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='valid_state') THEN
        ALTER TABLE conversations ADD CONSTRAINT valid_state CHECK (
            current_state IN (
                'novo',
                'identificando_servico',
                'coletando_dados',
                'aguardando_foto',
                'agendando',
                'agendado',
                'handoff_comercial',
                'concluido'
            )
        );
        RAISE NOTICE 'V58.1 ROLLBACK: Restored original state constraint';
    END IF;
END $$;

-- Remove V58.1 migration record
DELETE FROM schema_migrations WHERE version = 'V58.1';

COMMIT;

-- =====================================
-- V58.1 ROLLBACK COMPLETE
-- =====================================
SELECT
    'V58.1 Rollback Complete' as status,
    NOW() as completed_at;
EOF
)

# Execute rollback
echo -e "${YELLOW}Executing rollback SQL...${NC}"

ROLLBACK_OUTPUT=$(docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -c "$ROLLBACK_SQL" 2>&1)

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Rollback executed successfully${NC}"
    echo ""
    echo -e "${BLUE}Rollback output:${NC}"
    echo "$ROLLBACK_OUTPUT" | grep -E "NOTICE|status|completed_at" || echo "$ROLLBACK_OUTPUT"
else
    echo -e "${RED}❌ Rollback failed${NC}"
    echo "$ROLLBACK_OUTPUT"
    echo ""
    echo -e "${YELLOW}To restore pre-rollback state:${NC}"
    echo -e "${YELLOW}  cat $BACKUP_FILE | docker exec -i $DB_CONTAINER psql -U $DB_USER -d $DB_NAME${NC}"
    exit 1
fi

echo ""

# =====================================
# STEP 3: VERIFY ROLLBACK
# =====================================
echo -e "${BLUE}[STEP 3] Verifying rollback...${NC}"

# Verify contact_phone column removed
VERIFY_CONTACT_PHONE=$(docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -t -c \
    "SELECT COUNT(*) FROM information_schema.columns WHERE table_name='conversations' AND column_name='contact_phone';" | tr -d ' ')

if [ "$VERIFY_CONTACT_PHONE" -eq "0" ]; then
    echo -e "${GREEN}✅ contact_phone column removed${NC}"
else
    echo -e "${RED}❌ contact_phone column still exists${NC}"
    exit 1
fi

# Verify original service_type constraint restored
VERIFY_SERVICE=$(docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -t -c \
    "SELECT conname FROM pg_constraint WHERE conname='valid_service';" | tr -d ' ')

if [ -n "$VERIFY_SERVICE" ]; then
    echo -e "${GREEN}✅ Original service_type constraint restored${NC}"
else
    echo -e "${RED}❌ Original service_type constraint NOT found${NC}"
fi

# Verify V58.1 service constraint removed
VERIFY_SERVICE_V58=$(docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -t -c \
    "SELECT COUNT(*) FROM pg_constraint WHERE conname='valid_service_v58';" | tr -d ' ')

if [ "$VERIFY_SERVICE_V58" -eq "0" ]; then
    echo -e "${GREEN}✅ V58.1 service_type constraint removed${NC}"
else
    echo -e "${RED}❌ V58.1 service_type constraint still exists${NC}"
fi

# Verify original state constraint restored
VERIFY_STATE=$(docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -t -c \
    "SELECT conname FROM pg_constraint WHERE conname='valid_state';" | tr -d ' ')

if [ -n "$VERIFY_STATE" ]; then
    echo -e "${GREEN}✅ Original state constraint restored${NC}"
else
    echo -e "${RED}❌ Original state constraint NOT found${NC}"
fi

# Verify V58.1 state constraint removed
VERIFY_STATE_V58=$(docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -t -c \
    "SELECT COUNT(*) FROM pg_constraint WHERE conname='valid_state_v58';" | tr -d ' ')

if [ "$VERIFY_STATE_V58" -eq "0" ]; then
    echo -e "${GREEN}✅ V58.1 state constraint removed${NC}"
else
    echo -e "${RED}❌ V58.1 state constraint still exists${NC}"
fi

# Verify migration record removed
VERIFY_MIGRATION=$(docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -t -c \
    "SELECT COUNT(*) FROM schema_migrations WHERE version='V58.1';" 2>/dev/null | tr -d ' ')

if [ "$VERIFY_MIGRATION" -eq "0" ]; then
    echo -e "${GREEN}✅ V58.1 migration record removed${NC}"
else
    echo -e "${YELLOW}⚠️  V58.1 migration record still exists (non-critical)${NC}"
fi

echo ""

# =====================================
# STEP 4: SHOW SCHEMA SUMMARY
# =====================================
echo -e "${BLUE}[STEP 4] Schema summary after rollback:${NC}"

docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -c \
    "SELECT
        column_name,
        data_type,
        character_maximum_length,
        CASE WHEN is_nullable = 'YES' THEN 'NULL' ELSE 'NOT NULL' END as nullable
    FROM information_schema.columns
    WHERE table_name = 'conversations'
    AND column_name IN ('phone_number', 'service_type', 'current_state', 'state_machine_state')
    ORDER BY column_name;"

echo ""

# =====================================
# SUMMARY
# =====================================
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✅ V58.1 ROLLBACK COMPLETE${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}Changes reverted:${NC}"
echo -e "  ${GREEN}✅ GAP #8${NC}: contact_phone column removed"
echo -e "  ${GREEN}✅ GAP #6${NC}: service_type constraint restored to V43"
echo -e "  ${GREEN}✅ GAP #1${NC}: state constraint restored to V43 (8 states)"
echo ""
echo -e "${BLUE}Backup location:${NC}"
echo -e "  ${YELLOW}$BACKUP_FILE${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo -e "  1. Deactivate V58.1 workflow in n8n"
echo -e "  2. Activate V57.2 workflow (or earlier version)"
echo -e "  3. Verify bot functionality"
echo ""
echo -e "${RED}⚠️  IMPORTANT:${NC}"
echo -e "  ${YELLOW}Any conversations using V58.1 features (contact_phone, new states)${NC}"
echo -e "  ${YELLOW}will need to be cleaned up or migrated manually.${NC}"
echo ""
