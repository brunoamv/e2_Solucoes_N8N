#!/bin/bash
# WF02 V76 Deployment Script
# Generates V76 workflow from V75 base with V76 proactive UX changes
# Created: 2026-04-06

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
WORKFLOWS_DIR="$PROJECT_ROOT/n8n/workflows"
DOCS_DIR="$PROJECT_ROOT/docs"

V75_WORKFLOW="$WORKFLOWS_DIR/02_ai_agent_conversation_V75_APPOINTMENT_FINAL_MESSAGE.json"
V76_WORKFLOW="$WORKFLOWS_DIR/02_ai_agent_conversation_V76_PROACTIVE_UX.json"
V76_STATE_MACHINE="$SCRIPT_DIR/wf02-v76-state-machine.js"

print_header() {
    echo ""
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}========================================${NC}"
}

print_step() {
    echo ""
    echo -e "${BLUE}[STEP] $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Step 1: Validate prerequisites
validate_prerequisites() {
    print_header "Step 1: Validate Prerequisites"

    local errors=0

    # Check if V75 exists
    if [ -f "$V75_WORKFLOW" ]; then
        print_success "V75 workflow found: $V75_WORKFLOW"
    else
        print_error "V75 workflow not found: $V75_WORKFLOW"
        ((errors++))
    fi

    # Check if WF06 docs exist (indicates WF06 is deployed)
    if [ -f "$DOCS_DIR/WF06_CALENDAR_AVAILABILITY_SERVICE.md" ]; then
        print_success "WF06 documentation found (WF06 is deployed)"
    else
        print_warning "WF06 documentation not found - ensure WF06 is deployed"
    fi

    # Check if V76 implementation guide exists
    if [ -f "$DOCS_DIR/WF02_V76_IMPLEMENTATION_GUIDE.md" ]; then
        print_success "V76 implementation guide found"
    else
        print_error "V76 implementation guide not found"
        ((errors++))
    fi

    # Check if jq is installed (for JSON manipulation)
    if command -v jq &> /dev/null; then
        print_success "jq is installed"
    else
        print_error "jq is not installed - required for JSON manipulation"
        print_warning "Install with: sudo apt-get install jq (Ubuntu/Debian) or brew install jq (Mac)"
        ((errors++))
    fi

    # Check if node is available (for validation)
    if command -v node &> /dev/null; then
        print_success "Node.js is installed"
    else
        print_warning "Node.js not found - JSON validation will be skipped"
    fi

    if [ $errors -gt 0 ]; then
        print_error "Prerequisites validation failed with $errors errors"
        return 1
    fi

    print_success "All prerequisites validated"
    return 0
}

# Step 2: Extract state machine code from V75
extract_state_machine() {
    print_header "Step 2: Extract V75 State Machine Code"

    print_step "Extracting JavaScript code from V75 workflow"

    # Extract the "functionCode" field from the Function node
    # This contains the state machine logic
    jq -r '.nodes[] | select(.name == "State Machine Logic") | .parameters.functionCode' "$V75_WORKFLOW" > "$V76_STATE_MACHINE.tmp"

    if [ -s "$V76_STATE_MACHINE.tmp" ]; then
        print_success "State machine code extracted ($(wc -l < "$V76_STATE_MACHINE.tmp") lines)"
    else
        print_error "Failed to extract state machine code"
        return 1
    fi
}

# Step 3: Apply V76 modifications to state machine
apply_v76_modifications() {
    print_header "Step 3: Apply V76 Modifications to State Machine"

    print_step "Creating V76 state machine with proactive UX"

    # This is where we would apply modifications programmatically
    # For now, we'll note that manual intervention is needed

    print_warning "MANUAL STEP REQUIRED:"
    echo ""
    echo "The state machine code has been extracted to:"
    echo "  $V76_STATE_MACHINE.tmp"
    echo ""
    echo "You need to apply the following changes manually:"
    echo ""
    echo "1. Replace States 9-10 (collect_appointment_date, collect_appointment_time)"
    echo "   with States 9-12 from the implementation guide:"
    echo "   - State 9:  show_available_dates"
    echo "   - State 10: process_date_selection"
    echo "   - State 11: show_available_slots"
    echo "   - State 12: process_slot_selection"
    echo ""
    echo "2. Add 4 new templates:"
    echo "   - show_available_dates_v76"
    echo "   - show_available_slots_v76"
    echo "   - no_dates_available"
    echo "   - date_fully_booked"
    echo ""
    echo "3. Add fallback states:"
    echo "   - collect_appointment_date_manual"
    echo "   - collect_appointment_time_manual"
    echo ""
    echo "Reference: $DOCS_DIR/WF02_V76_IMPLEMENTATION_GUIDE.md"
    echo ""

    read -p "Press Enter when you have completed the manual modifications..."

    if [ -f "$V76_STATE_MACHINE" ]; then
        print_success "V76 state machine file found"
        return 0
    else
        print_error "V76 state machine file not found: $V76_STATE_MACHINE"
        print_warning "Please save your modified state machine to this path"
        return 1
    fi
}

# Step 4: Generate V76 workflow JSON
generate_v76_workflow() {
    print_header "Step 4: Generate V76 Workflow JSON"

    print_step "Creating V76 workflow from V75 base"

    # Copy V75 as base
    cp "$V75_WORKFLOW" "$V76_WORKFLOW"
    print_success "Copied V75 as V76 base"

    # Update workflow name
    jq '.name = "02_ai_agent_conversation_V76_PROACTIVE_UX"' "$V76_WORKFLOW" > "$V76_WORKFLOW.tmp"
    mv "$V76_WORKFLOW.tmp" "$V76_WORKFLOW"
    print_success "Updated workflow name to V76"

    # Update webhook path to test endpoint
    jq '(.nodes[] | select(.type == "n8n-nodes-base.webhook") | .parameters.path) = "webhook-ai-agent-v76"' "$V76_WORKFLOW" > "$V76_WORKFLOW.tmp"
    mv "$V76_WORKFLOW.tmp" "$V76_WORKFLOW"
    print_success "Updated webhook path to webhook-ai-agent-v76"

    # TODO: Add HTTP Request nodes for WF06 integration
    # This requires complex JSON manipulation - will need manual intervention

    print_warning "MANUAL STEP REQUIRED:"
    echo ""
    echo "V76 workflow base has been created at:"
    echo "  $V76_WORKFLOW"
    echo ""
    echo "You need to manually add the following nodes using n8n UI:"
    echo ""
    echo "1. HTTP Request - Get Next Dates (after State 8 confirmation)"
    echo "   - URL: http://e2bot-n8n-dev:5678/webhook/calendar-availability"
    echo "   - Method: POST"
    echo "   - Body: {\"action\": \"next_dates\", \"count\": 3, \"duration_minutes\": 120}"
    echo ""
    echo "2. HTTP Request - Get Available Slots (after State 10 date selection)"
    echo "   - URL: http://e2bot-n8n-dev:5678/webhook/calendar-availability"
    echo "   - Method: POST"
    echo "   - Body: {\"action\": \"available_slots\", \"date\": \$json.selectedDate, \"duration_minutes\": 120}"
    echo ""
    echo "3. Update State Machine node with V76 code from: $V76_STATE_MACHINE"
    echo ""
    echo "Reference: $DOCS_DIR/WF02_V76_IMPLEMENTATION_GUIDE.md (Section: New Nodes Required)"
    echo ""
}

# Step 5: Validate V76 workflow
validate_v76_workflow() {
    print_header "Step 5: Validate V76 Workflow"

    print_step "Validating JSON structure"

    # Validate JSON syntax
    if jq empty "$V76_WORKFLOW" 2>/dev/null; then
        print_success "V76 workflow JSON is valid"
    else
        print_error "V76 workflow JSON is invalid"
        return 1
    fi

    # Check for required elements
    local workflow_name=$(jq -r '.name' "$V76_WORKFLOW")
    if [ "$workflow_name" == "02_ai_agent_conversation_V76_PROACTIVE_UX" ]; then
        print_success "Workflow name is correct: $workflow_name"
    else
        print_warning "Workflow name unexpected: $workflow_name"
    fi

    # Check webhook path
    local webhook_path=$(jq -r '.nodes[] | select(.type == "n8n-nodes-base.webhook") | .parameters.path' "$V76_WORKFLOW")
    if [ "$webhook_path" == "webhook-ai-agent-v76" ]; then
        print_success "Webhook path is correct: $webhook_path"
    else
        print_warning "Webhook path unexpected: $webhook_path"
    fi

    # Count nodes
    local node_count=$(jq '.nodes | length' "$V76_WORKFLOW")
    print_success "V76 workflow has $node_count nodes"

    print_success "Validation completed"
}

# Step 6: Deployment instructions
show_deployment_instructions() {
    print_header "Step 6: Deployment Instructions"

    echo ""
    echo -e "${CYAN}📋 V76 Workflow Deployment Steps:${NC}"
    echo ""
    echo "1. ${BLUE}Import V76 to n8n:${NC}"
    echo "   - Open: http://localhost:5678"
    echo "   - Go to: Workflows → Import from File"
    echo "   - Select: $V76_WORKFLOW"
    echo "   - Keep INACTIVE initially"
    echo ""
    echo "2. ${BLUE}Manual Configuration in n8n UI:${NC}"
    echo "   a) Add HTTP Request nodes (see implementation guide)"
    echo "   b) Update State Machine code with V76 logic"
    echo "   c) Save workflow (DO NOT activate yet)"
    echo ""
    echo "3. ${BLUE}Test with E2E script:${NC}"
    echo "   bash $SCRIPT_DIR/test-wf02-v76-e2e.sh"
    echo ""
    echo "4. ${BLUE}Verify WF06 integration:${NC}"
    echo "   bash $SCRIPT_DIR/test-wf06-endpoints.sh"
    echo ""
    echo "5. ${BLUE}Canary Deployment (20% traffic):${NC}"
    echo "   - Update WF01 routing logic (see deployment guide)"
    echo "   - Monitor for 24 hours"
    echo "   - Success criteria: <1% error rate, >90% completion"
    echo ""
    echo "6. ${BLUE}Progressive Rollout:${NC}"
    echo "   - Day 3: 50% traffic"
    echo "   - Day 3 PM: 80% traffic"
    echo "   - Day 4: 100% traffic"
    echo ""
    echo "📚 ${CYAN}Complete Guide:${NC} $DOCS_DIR/WF02_V76_IMPLEMENTATION_GUIDE.md"
    echo ""
    echo "⚠️  ${YELLOW}Rollback Plan:${NC}"
    echo "   If error rate >5% OR critical bugs:"
    echo "   1. Update WF01 routing to 100% V75"
    echo "   2. Deactivate V76 workflow"
    echo "   3. Review logs: docker logs e2bot-n8n-dev | grep V76"
    echo ""
}

# Main execution
main() {
    print_header "WF02 V76 - Proactive UX Deployment"

    echo "This script will guide you through deploying WF02 V76"
    echo "with proactive date/time selection (zero-error UX)."
    echo ""
    echo "Prerequisites:"
    echo "  ✅ WF06 Calendar Availability Service deployed"
    echo "  ✅ WF02 V75 in production"
    echo "  ✅ V76 implementation guide reviewed"
    echo ""
    read -p "Press Enter to continue or Ctrl+C to cancel..."

    # Execute deployment steps
    if ! validate_prerequisites; then
        print_error "Prerequisites validation failed - cannot continue"
        exit 1
    fi

    extract_state_machine || {
        print_error "State machine extraction failed"
        exit 1
    }

    apply_v76_modifications || {
        print_warning "V76 modifications require manual intervention"
        print_warning "Continuing with workflow generation..."
    }

    generate_v76_workflow

    if validate_v76_workflow; then
        print_success "V76 workflow generated successfully"
    else
        print_error "V76 workflow validation failed"
        exit 1
    fi

    show_deployment_instructions

    print_header "Deployment Preparation Complete"
    echo ""
    print_success "V76 workflow ready for import to n8n"
    print_warning "Follow deployment instructions above to complete"
    echo ""
}

# Run main function
main
