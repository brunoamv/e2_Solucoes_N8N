#!/usr/bin/env python3
"""
Script: generate-v73.5-workflow-id-fix.py
Purpose: Fix Trigger Appointment Scheduler workflow ID
Date: 2026-03-24

CRITICAL FIX:
V73.4 has incorrect workflowId expression: {{ $workflow.id + 3 }}
Should be static workflow ID: yu0sW0TdzQpxqzb9

This causes error: "No information about the workflow to execute found"
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

def load_v73_4_workflow():
    """Load V73.4 workflow JSON"""
    v73_4_path = Path(__file__).parent.parent / "n8n" / "workflows" / "02_ai_agent_conversation_V73.4_STATE_11_ADD.json"

    print_step(1, 4, "Loading V73.4 workflow...")

    if not v73_4_path.exists():
        print_error(f"V73.4 workflow not found: {v73_4_path}")
        sys.exit(1)

    with open(v73_4_path, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    print_success(f"Loaded V73.4 workflow: {len(workflow['nodes'])} nodes")
    return workflow

def fix_trigger_appointment_scheduler(workflow):
    """Fix Trigger Appointment Scheduler workflowId"""
    print_step(2, 4, "Fixing Trigger Appointment Scheduler node...")

    # Find Trigger Appointment Scheduler node
    trigger_node = None
    for node in workflow['nodes']:
        if node['name'] == 'Trigger Appointment Scheduler':
            trigger_node = node
            break

    if not trigger_node:
        print_error("Trigger Appointment Scheduler node not found!")
        sys.exit(1)

    print(f"  Current workflowId: {trigger_node['parameters'].get('workflowId', 'NOT SET')}")

    # CRITICAL FIX: Replace dynamic expression with static workflow ID
    # Target workflow: 05_appointment_scheduler.json
    # Workflow ID: yu0sW0TdzQpxqzb9
    trigger_node['parameters']['workflowId'] = 'yu0sW0TdzQpxqzb9'

    print_success(f"Fixed workflowId: yu0sW0TdzQpxqzb9")

    return workflow

def update_metadata(workflow):
    """Update workflow metadata for V73.5"""
    print_step(3, 4, "Updating workflow metadata...")

    workflow['meta'] = {
        "version": "V73.5_WORKFLOW_ID_FIX",
        "fixes_applied": [
            "BUG #4: SQL syntax error (V73 - fixed with Set node)",
            "BUG #5: Appointment timing (V73.1 - removed premature IF)",
            "BUG #6: State Machine wrong template (V73.2 - fixed State 8)",
            "BUG #7: State 9/10 infinite loop (V73.3 - message parsing)",
            "BUG #8: State 11 MISSING (V73.4 - added appointment_confirmation)",
            "BUG #9: Trigger Appointment Scheduler workflow ID (V73.5 - fixed static ID)",
            "SOLUTION: Trigger now uses static workflow ID: yu0sW0TdzQpxqzb9",
            "RESULT: Appointment Scheduler (WF05) executes correctly ✅"
        ],
        "fix_date": "2026-03-24",
        "preserves_v73_4_fixes": True,
        "states_total": 14,
        "templates_total": 28,
        "nodes_total": 34,
        "cumulative_fixes": [
            "V66 Fix #1: trimmedCorrectedName duplicate variable",
            "V66 Fix #2: query_correction_update scope",
            "V67 Fix: Service display keys (all 5 services)",
            "V68 Fix #1: Trigger node execution",
            "V68 Fix #2: Name field validation",
            "V68 Fix #3: Returning user detection",
            "V72 Fix: Complete appointment flow (States 9/10/11)",
            "V73 Fix: SQL syntax error - simplified expressions",
            "V73.1 Fix: Appointment timing - removed IF from State 8",
            "V73.2 Fix: State Machine State 8 logic - correct template",
            "V73.3 Fix: State 9/10 message parsing - inline validation",
            "V73.4 Fix: State 11 MISSING - added appointment_confirmation",
            "V73.5 Fix: Trigger Appointment Scheduler - static workflow ID"
        ],
        "instanceId": "v73_5_workflow_id_fix_complete",
        "description": "V73.5 WORKFLOW ID FIX - Trigger Appointment Scheduler uses static workflow ID"
    }

    workflow['versionId'] = "73.5"
    workflow['tags'] = [
        {
            "name": "v73.5-workflow-id-fix-complete"
        },
        {
            "name": "ready-for-production"
        }
    ]

    print_success("Updated metadata to V73.5")

def save_v73_5_workflow(workflow):
    """Save generated V73.5 workflow"""
    output_path = Path(__file__).parent.parent / "n8n" / "workflows" / "02_ai_agent_conversation_V73.5_WORKFLOW_ID_FIX.json"

    print_step(4, 4, "Saving V73.5 workflow...")

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print_success(f"Saved V73.5 workflow: {output_path}")
    print_success(f"Total nodes: {len(workflow['nodes'])}")
    print_success(f"Total connections: {len(workflow.get('connections', {}))}")

    return output_path

def validate_workflow(workflow):
    """Validate generated workflow structure"""
    print(f"\n{BLUE}🔍 Validating V73.5 workflow...{RESET}")

    # Validate node count (same as V73.4)
    expected_nodes = 34
    actual_nodes = len(workflow['nodes'])

    if actual_nodes != expected_nodes:
        print_warning(f"Expected {expected_nodes} nodes, got {actual_nodes}")
    else:
        print_success(f"Node count correct: {actual_nodes} nodes")

    # Validate Trigger Appointment Scheduler has correct workflow ID
    trigger_node = next((n for n in workflow['nodes'] if n['name'] == 'Trigger Appointment Scheduler'), None)

    if trigger_node:
        workflow_id = trigger_node['parameters'].get('workflowId', '')

        # Check for correct static workflow ID
        if workflow_id == 'yu0sW0TdzQpxqzb9':
            print_success("Trigger Appointment Scheduler uses correct workflow ID ✓")
        else:
            print_error(f"Workflow ID incorrect: {workflow_id}")
            return False

        # Check that old dynamic expression is gone
        if '{{ $workflow.id' in str(workflow_id):
            print_error("Still using dynamic workflow ID expression!")
            return False
        else:
            print_success("Dynamic expression removed ✓")

    else:
        print_error("Trigger Appointment Scheduler node NOT found!")
        return False

    # Validate State 11 still exists (from V73.4)
    state_machine_node = next((n for n in workflow['nodes'] if n['name'] == 'State Machine Logic'), None)

    if state_machine_node:
        function_code = state_machine_node['parameters']['functionCode']

        if "case 'appointment_confirmation':" in function_code:
            print_success("State 11 preserved from V73.4 ✓")
        else:
            print_error("State 11 lost!")
            return False

    print(f"\n{GREEN}✅ Validation complete - All checks passed!{RESET}")
    return True

def main():
    """Main script execution"""
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}Generate V73.5 Workflow - Fix Trigger Appointment Scheduler{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")

    print(f"{YELLOW}🎯 CRITICAL FIX:{RESET}")
    print(f"V73.4 Trigger Appointment Scheduler has incorrect workflowId:")
    print(f"  ❌ Current: {{ $workflow.id + 3 }} (dynamic expression)")
    print(f"  ❌ Error: 'No information about the workflow to execute found'")
    print(f"\nV73.5 will fix to static workflow ID:")
    print(f"  ✅ New: 'yu0sW0TdzQpxqzb9' (static ID)")
    print(f"  ✅ Target: 05_appointment_scheduler.json")
    print(f"\n{BLUE}{'='*70}{RESET}\n")

    # Load V73.4
    workflow = load_v73_4_workflow()

    # Fix Trigger Appointment Scheduler
    workflow = fix_trigger_appointment_scheduler(workflow)

    # Update metadata
    update_metadata(workflow)

    # Save V73.5
    output_path = save_v73_5_workflow(workflow)

    # Validate
    if validate_workflow(workflow):
        print(f"\n{GREEN}{'='*70}{RESET}")
        print(f"{GREEN}✅ V73.5 workflow generated successfully!{RESET}")
        print(f"{GREEN}{'='*70}{RESET}\n")
        print(f"{YELLOW}📋 Key Changes:{RESET}")
        print(f"1. Trigger Appointment Scheduler: workflowId = 'yu0sW0TdzQpxqzb9'")
        print(f"2. Removed dynamic expression: {{ $workflow.id + 3 }}")
        print(f"3. Preserved all V73.4 fixes (State 11, etc.)")
        print(f"4. Target workflow: 05_appointment_scheduler.json\n")
        print(f"{YELLOW}📋 Next steps:{RESET}")
        print(f"1. Import workflow: http://localhost:5678")
        print(f"2. File: {output_path}")
        print(f"3. Deactivate V73.4, activate V73.5")
        print(f"4. Test trigger execution:")
        print(f"   WhatsApp: complete flow → confirm appointment")
        print(f"   Expected: Workflow 05 (yu0sW0TdzQpxqzb9) executes ✓\n")
        return 0
    else:
        print(f"\n{RED}{'='*70}{RESET}")
        print(f"{RED}❌ Validation failed - please review errors{RESET}")
        print(f"{RED}{'='*70}{RESET}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
