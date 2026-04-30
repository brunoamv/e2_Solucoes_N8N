#!/bin/bash

# =========================================
# V35 EXECUTION FIX - VALIDATION SCRIPT
# =========================================
# Tests both minimal and full V35 workflows
# Verifies code execution and database fields

set -e

echo "========================================"
echo "V35 EXECUTION FIX VALIDATION"
echo "========================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Database connection params (corrected)
DB_USER="postgres"
DB_NAME="e2_bot"
CONTAINER="e2bot-postgres-dev"

echo "📋 PHASE 1: DATABASE VERIFICATION"
echo "---------------------------------"

# Test database connection with correct parameters
echo -n "Testing database connection... "
if docker exec $CONTAINER psql -U $DB_USER -d $DB_NAME -c "SELECT 1;" &>/dev/null; then
    echo -e "${GREEN}✓ Connected${NC}"
else
    echo -e "${RED}✗ Failed${NC}"
    echo "Try: docker exec $CONTAINER psql -U postgres -l"
    exit 1
fi

# Check conversations table structure
echo -n "Checking conversations table... "
COLUMNS=$(docker exec $CONTAINER psql -U $DB_USER -d $DB_NAME -t -c "SELECT column_name FROM information_schema.columns WHERE table_name = 'conversations';" | tr -d ' \n')
if [[ $COLUMNS == *"phone_number"* ]] && [[ $COLUMNS == *"state_machine_state"* ]]; then
    echo -e "${GREEN}✓ Correct fields found${NC}"
    echo "  - phone_number field: ✓"
    echo "  - state_machine_state field: ✓"
else
    echo -e "${RED}✗ Missing expected fields${NC}"
    echo "Expected: phone_number, state_machine_state"
    echo "Found: $COLUMNS"
fi

echo ""
echo "📋 PHASE 2: WORKFLOW FILE VERIFICATION"
echo "-------------------------------------"

# Check if V35 files exist
V35_MINIMAL="../n8n/workflows/02_ai_agent_conversation_V35_MINIMAL_TEST.json"
V35_FULL="../n8n/workflows/02_ai_agent_conversation_V35_EXECUTION_FIX.json"

echo -n "V35 Minimal Test workflow... "
if [ -f "$V35_MINIMAL" ]; then
    echo -e "${GREEN}✓ File exists${NC}"
    # Check for key V35 minimal markers
    if grep -q "V35 MINIMAL TEST" "$V35_MINIMAL"; then
        echo "  - Contains V35 minimal test code: ✓"
    fi
else
    echo -e "${RED}✗ File not found${NC}"
fi

echo -n "V35 Full workflow... "
if [ -f "$V35_FULL" ]; then
    echo -e "${GREEN}✓ File exists${NC}"
    # Check for key V35 full markers
    if grep -q "V35 FULL VERSION EXECUTING" "$V35_FULL"; then
        echo "  - Contains V35 full code: ✓"
    fi
    if grep -q "phone_number" "$V35_FULL" && grep -q "state_machine_state" "$V35_FULL"; then
        echo "  - Uses correct DB fields: ✓"
    fi
else
    echo -e "${RED}✗ File not found${NC}"
fi

echo ""
echo "📋 PHASE 3: IMPORT INSTRUCTIONS"
echo "-------------------------------"
echo ""
echo -e "${YELLOW}CRITICAL: Import V35 workflows in this order:${NC}"
echo ""
echo "1️⃣  TEST MINIMAL FIRST (Critical for debugging):"
echo "   a. Open n8n: http://localhost:5678"
echo "   b. DEACTIVATE all V32/V33/V34 workflows"
echo "   c. Import: 02_ai_agent_conversation_V35_MINIMAL_TEST.json"
echo "   d. Activate V35 MINIMAL"
echo "   e. Send ANY message to bot"
echo ""
echo "2️⃣  MONITOR MINIMAL LOGS:"
echo "   docker logs -f e2bot-n8n-dev 2>&1 | grep V35"
echo ""
echo "   Expected output:"
echo "   ================================"
echo "   # V35 MINIMAL TEST EXECUTING   #"
echo "   ================================"
echo "   V35 Input: {\"message\":\"test\"...}"
echo ""
echo "   ✅ If you see this → Code is executing!"
echo "   ❌ If not → Check node configuration"
echo ""
echo "3️⃣  IF MINIMAL WORKS, TEST FULL:"
echo "   a. Deactivate V35 MINIMAL"
echo "   b. Import: 02_ai_agent_conversation_V35_EXECUTION_FIX.json"
echo "   c. Activate V35 FULL"
echo "   d. Send \"1\" to bot"
echo "   e. Check for menu response"
echo "   f. Send \"Bruno Rosa\""
echo "   g. Should ACCEPT and ask for phone"
echo ""

echo "📋 PHASE 4: TESTING COMMANDS"
echo "----------------------------"
echo ""
echo "# Clear conversation state (replace with your number):"
echo "docker exec $CONTAINER psql -U $DB_USER -d $DB_NAME \\"
echo "  -c \"DELETE FROM conversations WHERE phone_number = '5562XXXXXXXXX';\""
echo ""
echo "# Watch V35 logs in real-time:"
echo "docker logs -f e2bot-n8n-dev 2>&1 | grep -E 'V35|EXECUTION|Bruno'"
echo ""
echo "# Check last conversation state:"
echo "docker exec $CONTAINER psql -U $DB_USER -d $DB_NAME \\"
echo "  -c \"SELECT phone_number, state_machine_state, collected_data FROM conversations ORDER BY updated_at DESC LIMIT 1;\""
echo ""

echo "📋 PHASE 5: DIAGNOSTIC DECISION TREE"
echo "------------------------------------"
echo ""
echo "NO V35 LOGS AT ALL?"
echo "├─ Yes → Node not executing"
echo "│   ├─ Check node type is 'Code' or 'Function'"
echo "│   ├─ Check webhook properly connected"
echo "│   ├─ Try V35 MINIMAL first"
echo "│   └─ Restart n8n: docker restart e2bot-n8n-dev"
echo "│"
echo "└─ No (logs appear) → Code executing"
echo "    ├─ Check state values in logs"
echo "    ├─ Check message values"
echo "    └─ Debug validation logic"
echo ""

echo "📋 PHASE 6: SUCCESS CRITERIA"
echo "----------------------------"
echo ""
echo "V35 MINIMAL Success:"
echo "  ✅ See: \"V35 MINIMAL TEST EXECUTING\""
echo "  ✅ See: \"V35 Input: {...}\""
echo "  ✅ Response: \"V35 MINIMAL TEST - If you see this...\""
echo ""
echo "V35 FULL Success:"
echo "  ✅ See: \"V35 FULL VERSION EXECUTING\""
echo "  ✅ \"Bruno Rosa\" → ACCEPTED"
echo "  ✅ Bot asks for phone number"
echo "  ✅ State transitions work"
echo ""

echo "========================================"
echo -e "${GREEN}VALIDATION SCRIPT COMPLETE${NC}"
echo "========================================"
echo ""
echo "🚀 START WITH STEP 1: Import V35 MINIMAL"
echo "   This is CRITICAL to verify code execution!"
echo ""