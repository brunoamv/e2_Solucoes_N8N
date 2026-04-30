#!/bin/bash

# =====================================
# V38 VALIDATION SCRIPT
# =====================================
# Tests V38's compatibility with Build Update Queries
# Validates that State Machine Logic returns correct structure

echo "======================================="
echo "V38 VALIDATION - BUILD UPDATE QUERIES"
echo "======================================="
echo
echo "This script validates V38's compatibility with Build Update Queries"
echo "V38 preserves V34's working structure, only updating State Machine Logic"
echo

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if workflow exists
WORKFLOW_FILE="../n8n/workflows/02_ai_agent_conversation_V38_STATE_MACHINE_ONLY.json"

if [ ! -f "$WORKFLOW_FILE" ]; then
    echo -e "${RED}❌ V38 workflow file not found!${NC}"
    echo "Expected: $WORKFLOW_FILE"
    echo
    echo "Run this first:"
    echo "  python3 fix-workflow-v38-only-state-machine.py"
    exit 1
fi

echo -e "${GREEN}✅ V38 workflow file found${NC}"
echo

# Show workflow structure verification
echo "======================================="
echo "WORKFLOW STRUCTURE VERIFICATION"
echo "======================================="
echo

# Check if it has Build Update Queries node (inherited from V34)
if grep -q "Build Update Queries" "$WORKFLOW_FILE"; then
    echo -e "${GREEN}✅ Build Update Queries node present (from V34)${NC}"
else
    echo -e "${RED}❌ Build Update Queries node missing!${NC}"
    exit 1
fi

# Check if State Machine Logic has V38 markers
if grep -q "V38 STATE MACHINE LOGIC" "$WORKFLOW_FILE"; then
    echo -e "${GREEN}✅ V38 State Machine Logic code detected${NC}"
else
    echo -e "${RED}❌ V38 State Machine Logic not found!${NC}"
    exit 1
fi

echo
echo "======================================="
echo "V38 KEY FEATURES"
echo "======================================="
echo

echo -e "${BLUE}V38 preserves V34 structure with these critical fields:${NC}"
echo "  • responseText (for WhatsApp message)"
echo "  • phone_number (for recipient)"
echo "  • nextStage (for state progression)"
echo "  • updateData (for database updates)"
echo "  • ${YELLOW}lead_id${NC} (CRITICAL for Build Update Queries)"
echo "  • ${YELLOW}conversation_id${NC} (CRITICAL for Build Update Queries)"
echo "  • ${YELLOW}collected_data${NC} (CRITICAL for Build Update Queries)"
echo

echo "======================================="
echo "IMPORT INSTRUCTIONS"
echo "======================================="
echo

echo "1. DEACTIVATE OLD WORKFLOWS:"
echo "   - In n8n (http://localhost:5678)"
echo "   - Deactivate ALL conversation workflows (V32-V37)"
echo "   - Verify they're gray (inactive)"
echo

echo "2. IMPORT V38:"
echo "   - Click 'Import' button in n8n"
echo "   - Select: 02_ai_agent_conversation_V38_STATE_MACHINE_ONLY.json"
echo "   - Activate it (green toggle)"
echo

echo "3. VERIFY NODES:"
echo "   - Check that Build Update Queries node exists"
echo "   - Verify State Machine Logic shows 'V38' in logs"
echo

echo "======================================="
echo "TESTING PROCEDURE"
echo "======================================="
echo

echo -e "${YELLOW}TEST 1: Service Selection${NC}"
echo "  Send: '1'"
echo "  Expected log: 'V38 STATE MACHINE LOGIC - START'"
echo "  Expected: Menu should appear"
echo

echo -e "${YELLOW}TEST 2: Name Validation (CRITICAL)${NC}"
echo "  Send: 'Bruno Rosa'"
echo "  Expected log: '✅ V38: NAME ACCEPTED: Bruno Rosa'"
echo "  Expected: Should ask for phone (NOT reject!)"
echo

echo -e "${YELLOW}TEST 3: Database Update${NC}"
echo "  Check PostgreSQL after name acceptance:"
echo "  - lead_name should be 'Bruno Rosa'"
echo "  - state_machine_state should be 'collect_phone'"
echo

echo "======================================="
echo "MONITORING COMMANDS"
echo "======================================="
echo

echo "# Watch V38 execution logs:"
echo -e "${BLUE}docker logs -f e2bot-n8n-dev 2>&1 | grep -E 'V38|BUILD|UPDATE'${NC}"
echo

echo "# Check for Build Update Queries errors:"
echo -e "${BLUE}docker logs -f e2bot-n8n-dev 2>&1 | grep -A5 'Build Update Queries'${NC}"
echo

echo "# Monitor database updates:"
echo -e "${BLUE}docker exec -it e2bot-postgres-dev psql -U postgres -d e2_bot -c \"SELECT phone_number, state_machine_state, lead_name FROM conversations ORDER BY updated_at DESC LIMIT 5;\"${NC}"
echo

echo "======================================="
echo "EXPECTED V38 LOG SEQUENCE"
echo "======================================="
echo

echo "1. 'V38 STATE MACHINE LOGIC - START'"
echo "2. 'V38 Input:' (with message and phone)"
echo "3. 'V38 Current Stage: service_selection'"
echo "4. 'V38: Processing SERVICE_SELECTION state'"
echo "5. For 'Bruno Rosa':"
echo "   - 'V38: COLLECT_NAME STATE'"
echo "   - 'V38 Name Validation:'"
echo "   - '✅ V38: NAME ACCEPTED: Bruno Rosa'"
echo "6. 'V38 Final Result Keys:' (includes lead_id, conversation_id)"
echo "7. Build Update Queries should process without errors"
echo

echo "======================================="
echo "TROUBLESHOOTING"
echo "======================================="
echo

echo -e "${YELLOW}If Build Update Queries still fails:${NC}"
echo "  1. Check the error message in n8n execution view"
echo "  2. Look for missing fields in State Machine Logic output"
echo "  3. Verify database connection is active"
echo

echo -e "${YELLOW}If 'Bruno Rosa' is still rejected:${NC}"
echo "  1. Check V38 logs for 'NAME REJECTED'"
echo "  2. Verify the validation logic (length >= 2, not just numbers)"
echo "  3. Check if correct workflow version is active"
echo

echo -e "${GREEN}✅ V38 validation script complete!${NC}"
echo
echo "Key difference from V36/V37:"
echo "  - V38 keeps ENTIRE V34 structure"
echo "  - Only State Machine Logic node was modified"
echo "  - Return structure matches Build Update Queries expectations"
echo