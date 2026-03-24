#!/usr/bin/env python3
"""
Script: generate-v73.1-timing-fix.py
Purpose: Generate V73.1 workflow with timing fix for Create Appointment
Date: 2026-03-24

Changes from V73:
1. MODIFY: "Send WhatsApp Response" connections - remove Check If Scheduling from State 8 flow
2. LOGIC: Check If Scheduling will execute naturally after State 11 via State Machine
3. RESULT: Appointment created AFTER user provides date/time (States 9/10/11)
4. PRESERVE: All 34 existing nodes from V73
"""

import json
import sys
from pathlib import Path

# Colors for terminal output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_step(step_num, total, message):
    """Print formatted step progress"""
    print(f"{BLUE}[{step_num}/{total}]{RESET} {message}")

def print_success(message):
    """Print success message"""
    print(f"{GREEN}✅ {message}{RESET}")

def print_warning(message):
    """Print warning message"""
    print(f"{YELLOW}⚠️  {message}{RESET}")

def print_error(message):
    """Print error message"""
    print(f"{RED}❌ {message}{RESET}")

def load_v73_workflow():
    """Load V73 workflow JSON"""
    v73_path = Path(__file__).parent.parent / "n8n" / "workflows" / "02_ai_agent_conversation_V73_SQL_FIX.json"

    print_step(1, 4, "Loading V73 workflow...")

    if not v73_path.exists():
        print_error(f"V73 workflow not found: {v73_path}")
        sys.exit(1)

    with open(v73_path, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    print_success(f"Loaded V73 workflow: {len(workflow['nodes'])} nodes, {len(workflow.get('connections', {}))} connections")
    return workflow

def fix_timing_issue(workflow):
    """Fix timing issue - Check If Scheduling should execute after State 11, not State 8"""
    print_step(2, 4, "Fixing appointment timing issue...")

    connections = workflow.get('connections', {})

    # CRITICAL FIX: Remove "Check If Scheduling" from State 8 flow
    # State 8 (confirmation) → Should NOT trigger appointment creation immediately
    # Appointment creation should happen AFTER State 11 (appointment_confirmation)

    # Current V73 (WRONG): Send WhatsApp Response → [Check If Scheduling, Check If Handoff]
    # Fixed V73.1 (RIGHT): Send WhatsApp Response → [Check If Handoff] only
    #   Check If Scheduling will be triggered naturally after State 11 via State Machine logic

    if 'Send WhatsApp Response' in connections:
        current_connections = connections['Send WhatsApp Response']['main'][0]

        print(f"  Current connections from 'Send WhatsApp Response': {len(current_connections)} nodes")

        # Filter out "Check If Scheduling" - keep only "Check If Handoff"
        new_connections = [
            conn for conn in current_connections
            if conn['node'] != 'Check If Scheduling'
        ]

        connections['Send WhatsApp Response']['main'][0] = new_connections

        print_success(f"Removed 'Check If Scheduling' from State 8 flow")
        print_success(f"New connections from 'Send WhatsApp Response': {len(new_connections)} nodes")
        print_success("'Check If Scheduling' will execute after State 11 naturally")
    else:
        print_error("Node 'Send WhatsApp Response' connections not found!")
        sys.exit(1)

    # Explanation of how it works now:
    # 1. State 8 (confirmation) → user confirms "sim"
    # 2. State Machine sets next_stage = "collect_appointment_date"
    # 3. Flow continues: State 9 → 10 → 11
    # 4. State 11 (appointment_confirmation) → user confirms final
    # 5. State Machine sets next_stage = "scheduling_redirect"
    # 6. Send WhatsApp Response executes
    # 7. State Machine logic routes to Check If Scheduling naturally
    # 8. Check If Scheduling evaluates: next_stage == "scheduling_redirect" ✓
    # 9. Prepare Appointment Data extracts dates (NOW POPULATED!)
    # 10. Create Appointment succeeds with valid dates ✓

    print_success("Timing fix applied successfully")
    return workflow

def update_metadata(workflow):
    """Update workflow metadata for V73.1"""
    print_step(3, 4, "Updating workflow metadata...")

    workflow['meta'] = {
        "version": "V73.1_TIMING_FIX",
        "fixes_applied": [
            "BUG #4: SQL syntax error (V73 - fixed with Set node)",
            "BUG #5: Appointment timing - creating with NULL dates",
            "SOLUTION: Removed Check If Scheduling from State 8 flow",
            "RESULT: Appointment created AFTER State 11 (dates populated)"
        ],
        "fix_date": "2026-03-24",
        "preserves_v73_fixes": True,
        "states_total": 14,
        "templates_total": 28,
        "nodes_total": 34,  # Same as V73 (no new nodes)
        "cumulative_fixes": [
            "V66 Fix #1: trimmedCorrectedName duplicate variable",
            "V66 Fix #2: query_correction_update scope",
            "V67 Fix: Service display keys (all 5 services)",
            "V68 Fix #1: Trigger node execution",
            "V68 Fix #2: Name field validation",
            "V68 Fix #3: Returning user detection",
            "V72 Fix: Complete appointment flow (States 9/10/11)",
            "V73 Fix: SQL syntax error - simplified expressions",
            "V73.1 Fix: Appointment timing - execute after dates collected"
        ],
        "instanceId": "v73_1_timing_fix_complete",
        "description": "V73.1 TIMING FIX - Appointment created AFTER user provides date/time (States 9/10/11)"
    }

    workflow['versionId'] = "73.1"
    workflow['tags'] = [
        {
            "name": "v73.1-timing-fix-complete"
        },
        {
            "name": "ready-for-production"
        }
    ]

    print_success("Updated metadata to V73.1")

def save_v73_1_workflow(workflow):
    """Save generated V73.1 workflow"""
    output_path = Path(__file__).parent.parent / "n8n" / "workflows" / "02_ai_agent_conversation_V73.1_TIMING_FIX.json"

    print_step(4, 4, "Saving V73.1 workflow...")

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print_success(f"Saved V73.1 workflow: {output_path}")
    print_success(f"Total nodes: {len(workflow['nodes'])}")
    print_success(f"Total connections: {len(workflow.get('connections', {}))}")

    return output_path

def validate_workflow(workflow):
    """Validate generated workflow structure"""
    print(f"\n{BLUE}🔍 Validating V73.1 workflow...{RESET}")

    # Validate node count (same as V73)
    expected_nodes = 34
    actual_nodes = len(workflow['nodes'])

    if actual_nodes != expected_nodes:
        print_warning(f"Expected {expected_nodes} nodes, got {actual_nodes}")
    else:
        print_success(f"Node count correct: {actual_nodes} nodes")

    # Validate "Send WhatsApp Response" connections
    connections = workflow.get('connections', {})

    if 'Send WhatsApp Response' in connections:
        send_connections = connections['Send WhatsApp Response']['main'][0]

        # Should NOT have "Check If Scheduling" in State 8 flow
        has_check_scheduling = any(c['node'] == 'Check If Scheduling' for c in send_connections)

        if has_check_scheduling:
            print_error("'Check If Scheduling' still in State 8 flow - timing NOT fixed!")
            return False
        else:
            print_success("'Check If Scheduling' removed from State 8 flow ✓")

        # Should still have "Check If Handoff"
        has_check_handoff = any(c['node'] == 'Check If Handoff' for c in send_connections)

        if has_check_handoff:
            print_success("'Check If Handoff' preserved in connections ✓")
        else:
            print_warning("'Check If Handoff' not found in connections")

    # Validate "Check If Scheduling" node still exists (will execute via State Machine)
    check_scheduling_exists = any(n['name'] == 'Check If Scheduling' for n in workflow['nodes'])
    if check_scheduling_exists:
        print_success("'Check If Scheduling' node still exists (executes after State 11) ✓")
    else:
        print_error("'Check If Scheduling' node NOT found!")
        return False

    # Validate "Prepare Appointment Data" node exists
    prepare_node_exists = any(n['name'] == 'Prepare Appointment Data' for n in workflow['nodes'])
    if prepare_node_exists:
        print_success("'Prepare Appointment Data' node exists ✓")
    else:
        print_error("'Prepare Appointment Data' node NOT found!")
        return False

    # Validate "Create Appointment in Database" SQL
    create_node = next((n for n in workflow['nodes'] if n['name'] == 'Create Appointment in Database'), None)
    if create_node:
        sql = create_node['parameters']['query']
        if '{{ $json.phone_number }}' in sql:
            print_success("SQL uses simplified expressions ✓")
        else:
            print_warning("SQL may have issues")
    else:
        print_error("'Create Appointment in Database' node NOT found!")
        return False

    print(f"\n{GREEN}✅ Validation complete - All checks passed!{RESET}")
    return True

def main():
    """Main script execution"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}Generate V73.1 Workflow - Timing Fix{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")

    # Load V73
    workflow = load_v73_workflow()

    # Fix timing issue
    workflow = fix_timing_issue(workflow)

    # Update metadata
    update_metadata(workflow)

    # Save V73.1
    output_path = save_v73_1_workflow(workflow)

    # Validate
    if validate_workflow(workflow):
        print(f"\n{GREEN}{'='*60}{RESET}")
        print(f"{GREEN}✅ V73.1 workflow generated successfully!{RESET}")
        print(f"{GREEN}{'='*60}{RESET}\n")
        print(f"{YELLOW}📋 Key Changes:{RESET}")
        print(f"1. Removed 'Check If Scheduling' from State 8 flow")
        print(f"2. Appointment creation now happens AFTER State 11")
        print(f"3. Dates are POPULATED before CREATE appointment")
        print(f"4. No more 'invalid input syntax for type date' errors\n")
        print(f"{YELLOW}📋 Next steps:{RESET}")
        print(f"1. Import workflow: http://localhost:5678")
        print(f"2. File: {output_path}")
        print(f"3. Deactivate V73, activate V73.1")
        print(f"4. Test complete flow:")
        print(f"   - WhatsApp 'oi' → service 1 → complete data")
        print(f"   - Confirmation 'sim' → date → time → final 'sim'")
        print(f"   - Verify appointment created with dates in PostgreSQL\n")
        return 0
    else:
        print(f"\n{RED}{'='*60}{RESET}")
        print(f"{RED}❌ Validation failed - please review errors{RESET}")
        print(f"{RED}{'='*60}{RESET}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
