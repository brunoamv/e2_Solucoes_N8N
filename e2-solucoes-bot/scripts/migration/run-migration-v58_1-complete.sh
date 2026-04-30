#!/bin/bash
# =====================================
# V58.1 DATABASE MIGRATION - ALL GAPS FIXED
# =====================================
# Purpose: Complete database migration for V58.1 UX Refactor
# Fixes: Gap #8 (contact_phone) + Gap #1 (state constraints)
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

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}V58.1 DATABASE MIGRATION${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Database connection info
DB_CONTAINER="e2bot-postgres-dev"
DB_USER="postgres"
DB_NAME="e2bot_dev"

# Check if container is running
if ! docker ps | grep -q "$DB_CONTAINER"; then
    echo -e "${RED}❌ ERROR: PostgreSQL container not running${NC}"
    echo -e "${YELLOW}   Run: docker-compose up -d${NC}"
    exit 1
fi

echo -e "${GREEN}✅ PostgreSQL container running${NC}"
echo ""

# =====================================
# STEP 1: BACKUP CURRENT DATABASE
# =====================================
echo -e "${BLUE}[STEP 1] Creating database backup...${NC}"

BACKUP_FILE="/tmp/e2bot_backup_v58_1_$(date +%Y%m%d_%H%M%S).sql"

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
# STEP 2: ANALYZE CURRENT SCHEMA
# =====================================
echo -e "${BLUE}[STEP 2] Analyzing current schema...${NC}"

# Check if contact_phone exists
CONTACT_PHONE_EXISTS=$(docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -t -c \
    "SELECT COUNT(*) FROM information_schema.columns WHERE table_name='conversations' AND column_name='contact_phone';" | tr -d ' ')

if [ "$CONTACT_PHONE_EXISTS" -eq "1" ]; then
    echo -e "${YELLOW}⚠️  Column 'contact_phone' already exists - skipping creation${NC}"
    NEEDS_CONTACT_PHONE=false
else
    echo -e "${GREEN}✅ Column 'contact_phone' needs to be created${NC}"
    NEEDS_CONTACT_PHONE=true
fi

# Check service_type constraint
SERVICE_TYPE_CORRECT=$(docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -t -c \
    "SELECT COUNT(*) FROM pg_constraint WHERE conname='valid_service_v58';" | tr -d ' ')

if [ "$SERVICE_TYPE_CORRECT" -eq "1" ]; then
    echo -e "${YELLOW}⚠️  service_type constraint 'valid_service_v58' already exists${NC}"
    NEEDS_SERVICE_TYPE_UPDATE=false
else
    echo -e "${GREEN}✅ service_type constraint needs update${NC}"
    NEEDS_SERVICE_TYPE_UPDATE=true
fi

# Check state constraint
STATE_CONSTRAINT_CORRECT=$(docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -t -c \
    "SELECT COUNT(*) FROM pg_constraint WHERE conname='valid_state_v58';" | tr -d ' ')

if [ "$STATE_CONSTRAINT_CORRECT" -eq "1" ]; then
    echo -e "${YELLOW}⚠️  state constraint 'valid_state_v58' already exists${NC}"
    NEEDS_STATE_UPDATE=false
else
    echo -e "${GREEN}✅ state constraint needs update for V58.1 states${NC}"
    NEEDS_STATE_UPDATE=true
fi

echo ""

# =====================================
# STEP 3: APPLY MIGRATION
# =====================================
echo -e "${BLUE}[STEP 3] Applying V58.1 migration...${NC}"

# Migration SQL
MIGRATION_SQL=$(cat <<'EOF'
BEGIN;

-- =====================================
-- V58.1 MIGRATION - ALL GAPS
-- =====================================

-- GAP #8: Add contact_phone column
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='conversations' AND column_name='contact_phone'
    ) THEN
        ALTER TABLE conversations
        ADD COLUMN contact_phone VARCHAR(20);

        COMMENT ON COLUMN conversations.contact_phone IS
        'V58.1 GAP #8: Primary contact phone (WhatsApp confirmed or alternative)';

        RAISE NOTICE 'V58.1 GAP #8: contact_phone column added';
    ELSE
        RAISE NOTICE 'V58.1: contact_phone column already exists';
    END IF;
END $$;

-- Create index for contact_phone
CREATE INDEX IF NOT EXISTS idx_conversations_contact_phone
ON conversations(contact_phone);

-- GAP #6: Update service_type constraint to accept STRING values
DO $$
BEGIN
    -- Drop old constraint if exists
    IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname='valid_service') THEN
        ALTER TABLE conversations DROP CONSTRAINT valid_service;
        RAISE NOTICE 'V58.1: Dropped old service_type constraint';
    END IF;

    -- Add new constraint with STRING values (V58.1 Gap #6)
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='valid_service_v58') THEN
        ALTER TABLE conversations ADD CONSTRAINT valid_service_v58 CHECK (
            service_type IS NULL OR
            service_type IN (
                -- V58.1: STRING service names (Gap #6)
                'Energia Solar',
                'Subestação',
                'Projetos Elétricos',
                'BESS',
                'Análise e Laudos',
                -- Legacy: snake_case values (backward compatibility)
                'energia_solar',
                'subestacao',
                'projeto_eletrico',
                'armazenamento_energia',
                'analise_laudo',
                'outro'
            )
        );
        RAISE NOTICE 'V58.1 GAP #6: service_type constraint updated for STRING values';
    END IF;
END $$;

-- GAP #1: Update valid_state constraint for new V58.1 states
DO $$
BEGIN
    -- Drop old constraint if exists
    IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname='valid_state') THEN
        ALTER TABLE conversations DROP CONSTRAINT valid_state;
        RAISE NOTICE 'V58.1: Dropped old state constraint';
    END IF;

    -- Add new constraint with V58.1 states (Gap #1)
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='valid_state_v58') THEN
        ALTER TABLE conversations ADD CONSTRAINT valid_state_v58 CHECK (
            current_state IN (
                -- Original states
                'novo',
                'identificando_servico',
                'coletando_dados',
                'aguardando_foto',
                'agendando',
                'agendado',
                'handoff_comercial',
                'concluido',
                -- V58.1 NEW: Phone confirmation states (Gap #1 & #3)
                'coletando_telefone_confirmacao_whatsapp',
                'coletando_telefone_alternativo'
            )
        );
        RAISE NOTICE 'V58.1 GAP #1: state constraint updated with 2 new states';
    END IF;
END $$;

-- V58.1: Populate contact_phone from existing data (migration helper)
UPDATE conversations
SET contact_phone = phone_number
WHERE contact_phone IS NULL
  AND phone_number IS NOT NULL
  AND phone_number != '';

-- V58.1: Add migration metadata
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_name='schema_migrations'
    ) THEN
        CREATE TABLE schema_migrations (
            version VARCHAR(50) PRIMARY KEY,
            applied_at TIMESTAMP DEFAULT NOW(),
            description TEXT
        );
        RAISE NOTICE 'V58.1: Created schema_migrations table';
    END IF;
END $$;

INSERT INTO schema_migrations (version, description)
VALUES
    ('V58.1', 'Complete UX Refactor - All 8 Gaps Fixed: contact_phone column, service_type STRING mapping, new phone confirmation states')
ON CONFLICT (version) DO NOTHING;

COMMIT;

-- =====================================
-- V58.1 MIGRATION COMPLETE
-- =====================================
SELECT
    'V58.1 Migration Complete' as status,
    NOW() as completed_at;
EOF
)

# Execute migration
echo -e "${YELLOW}Executing migration SQL...${NC}"

MIGRATION_OUTPUT=$(docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -c "$MIGRATION_SQL" 2>&1)

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Migration executed successfully${NC}"
    echo ""
    echo -e "${BLUE}Migration output:${NC}"
    echo "$MIGRATION_OUTPUT" | grep -E "NOTICE|status|completed_at" || echo "$MIGRATION_OUTPUT"
else
    echo -e "${RED}❌ Migration failed${NC}"
    echo "$MIGRATION_OUTPUT"
    echo ""
    echo -e "${YELLOW}To restore backup:${NC}"
    echo -e "${YELLOW}  cat $BACKUP_FILE | docker exec -i $DB_CONTAINER psql -U $DB_USER -d $DB_NAME${NC}"
    exit 1
fi

echo ""

# =====================================
# STEP 4: VERIFY MIGRATION
# =====================================
echo -e "${BLUE}[STEP 4] Verifying migration...${NC}"

# Verify contact_phone column
VERIFY_CONTACT_PHONE=$(docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -t -c \
    "SELECT column_name, data_type FROM information_schema.columns WHERE table_name='conversations' AND column_name='contact_phone';" | tr -d ' ')

if [ -n "$VERIFY_CONTACT_PHONE" ]; then
    echo -e "${GREEN}✅ contact_phone column exists${NC}"
else
    echo -e "${RED}❌ contact_phone column NOT found${NC}"
    exit 1
fi

# Verify service_type constraint
VERIFY_SERVICE=$(docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -t -c \
    "SELECT conname FROM pg_constraint WHERE conname='valid_service_v58';" | tr -d ' ')

if [ -n "$VERIFY_SERVICE" ]; then
    echo -e "${GREEN}✅ service_type constraint updated (Gap #6)${NC}"
else
    echo -e "${RED}❌ service_type constraint NOT found${NC}"
fi

# Verify state constraint
VERIFY_STATE=$(docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -t -c \
    "SELECT conname FROM pg_constraint WHERE conname='valid_state_v58';" | tr -d ' ')

if [ -n "$VERIFY_STATE" ]; then
    echo -e "${GREEN}✅ state constraint updated (Gap #1)${NC}"
else
    echo -e "${RED}❌ state constraint NOT found${NC}"
fi

# Verify migration record
VERIFY_MIGRATION=$(docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -t -c \
    "SELECT version FROM schema_migrations WHERE version='V58.1';" | tr -d ' ')

if [ -n "$VERIFY_MIGRATION" ]; then
    echo -e "${GREEN}✅ Migration recorded in schema_migrations${NC}"
else
    echo -e "${YELLOW}⚠️  Migration record not found (non-critical)${NC}"
fi

echo ""

# =====================================
# STEP 5: SHOW SCHEMA SUMMARY
# =====================================
echo -e "${BLUE}[STEP 5] Schema summary:${NC}"

docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -c \
    "SELECT
        column_name,
        data_type,
        character_maximum_length,
        CASE WHEN is_nullable = 'YES' THEN 'NULL' ELSE 'NOT NULL' END as nullable
    FROM information_schema.columns
    WHERE table_name = 'conversations'
    AND column_name IN ('phone_number', 'service_type', 'contact_phone', 'current_state', 'state_machine_state')
    ORDER BY column_name;"

echo ""

# =====================================
# SUMMARY
# =====================================
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✅ V58.1 MIGRATION COMPLETE${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}Changes applied:${NC}"
echo -e "  ${GREEN}✅ GAP #8${NC}: contact_phone column added"
echo -e "  ${GREEN}✅ GAP #6${NC}: service_type accepts STRING values"
echo -e "  ${GREEN}✅ GAP #1${NC}: current_state accepts 2 new phone states"
echo ""
echo -e "${BLUE}Backup location:${NC}"
echo -e "  ${YELLOW}$BACKUP_FILE${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo -e "  1. Import V58.1 workflow to n8n"
echo -e "  2. Test 3 paths from QUICKSTART.md"
echo -e "  3. Verify contact_phone population"
echo ""
echo -e "${BLUE}Rollback command (if needed):${NC}"
echo -e "  ${YELLOW}cat $BACKUP_FILE | docker exec -i $DB_CONTAINER psql -U $DB_USER -d $DB_NAME${NC}"
echo ""
