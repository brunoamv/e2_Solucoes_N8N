#!/bin/bash
# V42 Database Column Fix Validation Script

echo "=========================================="
echo "V42 DATABASE COLUMN FIX VALIDATION"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

VALIDATION_PASSED=true

# 1. Check if V42 workflow exists
echo "1. Checking if V42 workflow file exists..."
if [ -f "n8n/workflows/02_ai_agent_conversation_V42_DATABASE_COLUMNS_FIX.json" ]; then
    echo -e "${GREEN}✅ PASS${NC}: V42 workflow file exists"
else
    echo -e "${RED}❌ FAIL${NC}: V42 workflow file not found"
    VALIDATION_PASSED=false
fi
echo ""

# 2. Check for removed columns in V42
echo "2. Checking for non-existent columns in V42..."
PROBLEMATIC_COLUMNS=$(grep -i "contact_name\|service_id" n8n/workflows/02_ai_agent_conversation_V42_DATABASE_COLUMNS_FIX.json | grep -v "// " | grep -v "lead_name" || true)

if [ -z "$PROBLEMATIC_COLUMNS" ]; then
    echo -e "${GREEN}✅ PASS${NC}: No non-existent columns found (contact_name, service_id removed)"
else
    echo -e "${RED}❌ FAIL${NC}: Found references to non-existent columns:"
    echo "$PROBLEMATIC_COLUMNS"
    VALIDATION_PASSED=false
fi
echo ""

# 3. Verify collected_data JSONB is used
echo "3. Checking if collected_data JSONB is properly used..."
if grep -q "collected_data" n8n/workflows/02_ai_agent_conversation_V42_DATABASE_COLUMNS_FIX.json; then
    echo -e "${GREEN}✅ PASS${NC}: collected_data JSONB is used"
else
    echo -e "${RED}❌ FAIL${NC}: collected_data not found in workflow"
    VALIDATION_PASSED=false
fi
echo ""

# 4. Check database schema alignment
echo "4. Verifying database schema alignment..."
echo "   Checking if 'conversations' table has correct structure..."

# Check if Docker container is running
if docker ps | grep -q "e2bot-postgres-dev"; then
    # Check for non-existent columns in database
    SCHEMA_CHECK=$(docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -t -c "\d conversations" 2>/dev/null | grep -i "contact_name\|service_id" || true)

    if [ -z "$SCHEMA_CHECK" ]; then
        echo -e "${GREEN}✅ PASS${NC}: Database schema correct (no contact_name, service_id)"
    else
        echo -e "${YELLOW}⚠️  WARNING${NC}: Found unexpected columns in database:"
        echo "$SCHEMA_CHECK"
        echo "   This might indicate schema migration needed"
    fi
else
    echo -e "${YELLOW}⚠️  SKIP${NC}: PostgreSQL container not running - cannot verify schema"
fi
echo ""

# 5. Check if V42 has proper RETURNING * statements
echo "5. Checking if queries have RETURNING * for data retrieval..."
RETURNING_COUNT=$(grep -c "RETURNING \*" n8n/workflows/02_ai_agent_conversation_V42_DATABASE_COLUMNS_FIX.json || echo "0")

if [ "$RETURNING_COUNT" -ge 3 ]; then
    echo -e "${GREEN}✅ PASS${NC}: Found $RETURNING_COUNT RETURNING * statements"
else
    echo -e "${YELLOW}⚠️  WARNING${NC}: Only found $RETURNING_COUNT RETURNING * statements"
    echo "   Expected at least 3 (conversation update, inbound msg, outbound msg)"
fi
echo ""

# 6. Verify node count
echo "6. Verifying node count preservation..."
V41_NODES=$(grep -o '"nodes"' n8n/workflows/02_ai_agent_conversation_V41_QUERY_BATCHING_FIX.json | wc -l)
V42_NODES=$(grep -o '"nodes"' n8n/workflows/02_ai_agent_conversation_V42_DATABASE_COLUMNS_FIX.json | wc -l)

if [ "$V41_NODES" -eq "$V42_NODES" ]; then
    echo -e "${GREEN}✅ PASS${NC}: Node count preserved (V41: $V41_NODES = V42: $V42_NODES)"
else
    echo -e "${YELLOW}⚠️  WARNING${NC}: Node count changed (V41: $V41_NODES → V42: $V42_NODES)"
fi
echo ""

# 7. Summary
echo "=========================================="
echo "VALIDATION SUMMARY"
echo "=========================================="
if [ "$VALIDATION_PASSED" = true ]; then
    echo -e "${GREEN}✅ ALL CRITICAL VALIDATIONS PASSED${NC}"
    echo ""
    echo "📋 NEXT STEPS:"
    echo ""
    echo "1. Open n8n interface: http://localhost:5678"
    echo ""
    echo "2. DEACTIVATE V41 workflow:"
    echo "   - Find: '02 - AI Agent Conversation V41 (Query Batching Fix)'"
    echo "   - Click toggle to deactivate"
    echo ""
    echo "3. IMPORT V42 workflow:"
    echo "   - Click 'Import from File'"
    echo "   - Select: n8n/workflows/02_ai_agent_conversation_V42_DATABASE_COLUMNS_FIX.json"
    echo ""
    echo "4. ACTIVATE V42 workflow:"
    echo "   - Find: '02 - AI Agent Conversation V42 (Database Columns Fix)'"
    echo "   - Click toggle to activate"
    echo ""
    echo "5. CLEAR execution cache (optional):"
    echo "   docker exec e2bot-n8n-dev rm -rf /home/node/.n8n/cache/*"
    echo ""
    echo "6. TEST end-to-end:"
    echo "   a) Send 'oi' to WhatsApp bot"
    echo "   b) Bot should show menu with 5 options"
    echo "   c) Send '1' (Energia Solar)"
    echo "   d) Bot should ask for name"
    echo "   e) Send 'Bruno Rosa'"
    echo "   f) Bot should ask for phone (NOT go back to menu)"
    echo ""
    echo "7. VERIFY executions:"
    echo "   - Check: http://localhost:5678/projects/08qzhIsou3TK6J3Z/executions"
    echo "   - All executions should show 'success' status"
    echo "   - No executions stuck in 'running'"
    echo ""
    echo "8. VERIFY database:"
    echo "   docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -c \\"
    echo "     \"SELECT phone_number, collected_data FROM conversations \\"
    echo "     WHERE phone_number = '5562999887766';\""
    echo ""
    echo "   Expected output:"
    echo "   collected_data should contain:"
    echo "   {"
    echo '     "lead_name": "Bruno Rosa",'
    echo '     "service_type": "energia_solar",'
    echo "     ..."
    echo "   }"
    echo ""
    exit 0
else
    echo -e "${RED}❌ VALIDATION FAILED${NC}"
    echo ""
    echo "Please review the errors above and fix them before proceeding."
    echo ""
    exit 1
fi
