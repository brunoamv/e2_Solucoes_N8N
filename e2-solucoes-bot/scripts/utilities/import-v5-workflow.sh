#!/bin/bash
# Script to import v5 workflow into n8n and fix the collected_data issue
# This will replace the existing workflow with the fixed version

set -e

echo "🚀 E2 Bot Workflow v5 Import Script"
echo "===================================="
echo ""
echo "This script will:"
echo "1. Check n8n status"
echo "2. Import the fixed v5 workflow"
echo "3. Validate the import"
echo ""

# Configuration
N8N_URL="http://localhost:5678"
WORKFLOW_FILE="/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V1_MENU_FIXED_v5.json"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "📋 Step 1: Checking n8n status..."
if curl -s -o /dev/null -w "%{http_code}" $N8N_URL/api/v1/workflows | grep -q "401"; then
    echo -e "${GREEN}✅${NC} n8n is running"
else
    echo -e "${RED}❌${NC} n8n is not accessible. Please make sure it's running."
    exit 1
fi

echo ""
echo "📋 Step 2: Checking if v5 workflow file exists..."
if [ -f "$WORKFLOW_FILE" ]; then
    echo -e "${GREEN}✅${NC} Workflow file found: $WORKFLOW_FILE"
else
    echo -e "${RED}❌${NC} Workflow file not found!"
    echo "Creating v5 workflow now..."
    python3 /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/scripts/fix-complete-data-loss.py
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅${NC} Workflow v5 created successfully"
    else
        echo -e "${RED}❌${NC} Failed to create workflow v5"
        exit 1
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔧 MANUAL IMPORT REQUIRED"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Please follow these steps in n8n UI:"
echo ""
echo "1. Open n8n: ${YELLOW}$N8N_URL${NC}"
echo ""
echo "2. Go to Workflows page"
echo ""
echo "3. Find the workflow: '02 - AI Agent Conversation_V1_MENU'"
echo "   - If it's active (green toggle), turn it OFF"
echo "   - Delete or rename it to '_OLD' for backup"
echo ""
echo "4. Click 'Import from File' button"
echo "   - Select file: ${YELLOW}$WORKFLOW_FILE${NC}"
echo "   - Or copy the full path above"
echo ""
echo "5. After import:"
echo "   - Check the workflow name is '02 - AI Agent Conversation_V1_MENU_FIXED_v5'"
echo "   - Activate the workflow (green toggle ON)"
echo "   - Note the workflow ID shown in the URL"
echo ""
echo "6. Test the workflow:"
echo "   - Click 'Execute Workflow' button"
echo "   - Check for any errors"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "After import, run the validation script:"
echo -e "${YELLOW}./scripts/validate-v5-fix.sh${NC}"
echo ""
echo "If you see issues, check:"
echo "1. Old workflows are deactivated"
echo "2. v5 workflow is active"
echo "3. No duplicate workflows with same name"
echo ""

# Optional: Try to open browser
if command -v xdg-open &> /dev/null; then
    echo "Opening n8n in browser..."
    xdg-open $N8N_URL 2>/dev/null || true
fi