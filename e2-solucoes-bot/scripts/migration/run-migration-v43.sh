#!/bin/bash
# V43 Migration Execution Script
# Adds missing columns to conversations table

echo "=========================================="
echo "V43 DATABASE MIGRATION"
echo "=========================================="
echo ""
echo "MIGRATION: Add columns to conversations table"
echo "  - service_id VARCHAR(100)"
echo "  - contact_name VARCHAR(255)"
echo "  - contact_email VARCHAR(255)"
echo "  - city VARCHAR(100)"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if PostgreSQL container is running
if ! docker ps | grep -q "e2bot-postgres-dev"; then
    echo -e "${RED}❌ ERROR${NC}: PostgreSQL container not running"
    echo ""
    echo "Start the container first:"
    echo "  cd docker && docker-compose -f docker-compose-dev.yml up -d e2bot-postgres-dev"
    exit 1
fi

echo -e "${GREEN}✅${NC} PostgreSQL container is running"
echo ""

# Backup current schema
echo "1. Creating backup of current schema..."
docker exec e2bot-postgres-dev pg_dump -U postgres -d e2bot_dev --schema-only > "/tmp/e2bot_schema_backup_$(date +%Y%m%d_%H%M%S).sql"
echo -e "${GREEN}✅${NC} Backup created"
echo ""

# Execute migration
echo "2. Executing migration..."
docker exec -i e2bot-postgres-dev psql -U postgres -d e2bot_dev < database/migrations/001_add_conversation_columns.sql

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅${NC} Migration executed successfully"
else
    echo -e "${RED}❌${NC} Migration failed"
    echo ""
    echo "Check the error message above and restore from backup if needed"
    exit 1
fi
echo ""

# Verify columns exist
echo "3. Verifying new columns..."
VERIFICATION=$(docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -t -c "
    SELECT
        CASE
            WHEN COUNT(*) = 4 THEN 'SUCCESS'
            ELSE 'FAILED'
        END as status
    FROM information_schema.columns
    WHERE table_name = 'conversations'
    AND column_name IN ('service_id', 'contact_name', 'contact_email', 'city');
" | tr -d ' ')

if [ "$VERIFICATION" = "SUCCESS" ]; then
    echo -e "${GREEN}✅${NC} All 4 columns verified"
else
    echo -e "${RED}❌${NC} Column verification failed"
    exit 1
fi
echo ""

# Show current schema
echo "4. Current conversations table schema:"
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "\d conversations"
echo ""

echo "=========================================="
echo "V43 MIGRATION COMPLETE"
echo "=========================================="
echo ""
echo "📋 NEXT STEPS:"
echo ""
echo "1. VERIFY in database:"
echo "   docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -c \\"
echo "     \"SELECT column_name, data_type FROM information_schema.columns \\"
echo "     WHERE table_name = 'conversations' \\"
echo "     AND column_name IN ('service_id', 'contact_name', 'contact_email', 'city');\""
echo ""
echo "2. ACTIVATE V41 workflow (if not already active):"
echo "   - Open n8n: http://localhost:5678"
echo "   - Ensure V41 workflow is active"
echo "   - Deactivate V42 if it's active"
echo ""
echo "3. TEST end-to-end:"
echo "   a) Send 'oi' to WhatsApp bot"
echo "   b) Bot should show menu with 5 options"
echo "   c) Send '1' (Energia Solar)"
echo "   d) Bot should ask for name"
echo "   e) Send 'Bruno Rosa'"
echo "   f) Bot should ask for phone (NOT go back to menu)"
echo ""
echo "4. VERIFY executions:"
echo "   - Check: http://localhost:5678/projects/08qzhIsou3TK6J3Z/executions"
echo "   - All executions should show 'success' status"
echo "   - No executions stuck in 'running'"
echo ""
echo "5. VERIFY database data:"
echo "   docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -c \\"
echo "     \"SELECT phone_number, contact_name, contact_email, city, collected_data \\"
echo "     FROM conversations WHERE phone_number = '5562999887766';\""
echo ""
echo "✅ V43 Migration Ready for Testing!"
echo ""
