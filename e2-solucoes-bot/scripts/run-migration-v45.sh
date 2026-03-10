#!/bin/bash

# V45 Migration Script
# Purpose: Add state_machine_state column to conversations table

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "V45 Migration: Add state_machine_state"
echo "=========================================="

# Check if container is running
if ! docker ps | grep -q e2bot-postgres-dev; then
    echo -e "${RED}❌${NC} PostgreSQL container not running"
    echo "Start with: docker-compose -f docker/docker-compose-dev.yml up -d postgres-dev"
    exit 1
fi

# Check if database exists
DB_EXISTS=$(docker exec e2bot-postgres-dev psql -U postgres -lqt | cut -d \| -f 1 | grep -w e2bot_dev | wc -l)
if [ "$DB_EXISTS" -eq "0" ]; then
    echo -e "${RED}❌${NC} Database e2bot_dev does not exist"
    exit 1
fi

echo -e "${GREEN}✅${NC} Database e2bot_dev found"

# Execute migration
echo ""
echo "Executing migration..."
docker exec -i e2bot-postgres-dev psql -U postgres -d e2bot_dev << 'EOF'
-- V45 Migration: Add state_machine_state column
BEGIN;

-- Add column
ALTER TABLE conversations
ADD COLUMN IF NOT EXISTS state_machine_state VARCHAR(50);

-- Create index
CREATE INDEX IF NOT EXISTS idx_conversations_state_machine
ON conversations(state_machine_state);

-- Populate existing records
UPDATE conversations
SET state_machine_state = CASE current_state
  WHEN 'novo' THEN 'greeting'
  WHEN 'identificando_servico' THEN 'service_selection'
  WHEN 'coletando_dados' THEN 'collect_name'
  WHEN 'agendando' THEN 'scheduling'
  WHEN 'handoff_comercial' THEN 'handoff_comercial'
  WHEN 'concluido' THEN 'completed'
  ELSE 'greeting'
END
WHERE state_machine_state IS NULL;

COMMIT;
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅${NC} Migration executed successfully"
else
    echo -e "${RED}❌${NC} Migration failed"
    exit 1
fi

# Verify migration
echo ""
echo "Verifying migration..."

# Check column exists
COLUMN_EXISTS=$(docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -t -c "
    SELECT COUNT(*)
    FROM information_schema.columns
    WHERE table_name = 'conversations'
    AND column_name = 'state_machine_state';
" | tr -d ' ')

if [ "$COLUMN_EXISTS" = "1" ]; then
    echo -e "${GREEN}✅${NC} Column state_machine_state exists"
else
    echo -e "${RED}❌${NC} Column state_machine_state NOT found"
    exit 1
fi

# Check index exists
INDEX_EXISTS=$(docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -t -c "
    SELECT COUNT(*)
    FROM pg_indexes
    WHERE tablename = 'conversations'
    AND indexname = 'idx_conversations_state_machine';
" | tr -d ' ')

if [ "$INDEX_EXISTS" = "1" ]; then
    echo -e "${GREEN}✅${NC} Index idx_conversations_state_machine exists"
else
    echo -e "${YELLOW}⚠️${NC} Index idx_conversations_state_machine NOT found"
fi

# Show column details
echo ""
echo "Column details:"
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "
    SELECT column_name, data_type, character_maximum_length
    FROM information_schema.columns
    WHERE table_name = 'conversations'
    AND column_name = 'state_machine_state';
"

# Show sample data
echo ""
echo "Sample data (last 3 records):"
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "
    SELECT
        phone_number,
        current_state,
        state_machine_state,
        LEFT(COALESCE(whatsapp_name, ''), 20) as name
    FROM conversations
    ORDER BY updated_at DESC
    LIMIT 3;
"

echo ""
echo "=========================================="
echo -e "${GREEN}✅ V45 Migration Complete${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Test workflow V41: Send WhatsApp message 'oi'"
echo "2. Verify n8n execution: http://localhost:5678/projects/08qzhIsou3TK6J3Z/executions"
echo "3. Check database: state_machine_state should be populated"
echo ""
