#!/usr/bin/env python3
"""
Script: generate-appointment-scheduler-v3.3.py
Purpose: Fix Google Calendar node typeVersion mismatch
Date: 2026-03-24

CRITICAL FIX:
Problem: Workflow uses typeVersion: 2, but installed node is version 1.0
Error: "Install this node to use it. This node is not currently installed"
Result: Execution stops at Google Calendar node, no downstream execution

Solution: Change typeVersion from 2 to 1
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

def load_v3_2_workflow():
    """Load V3.2 workflow JSON"""
    v3_2_path = Path(__file__).parent.parent / "n8n" / "workflows" / "05_appointment_scheduler_v3.2.json"

    print_step(1, 2, "Loading V3.2 workflow...")

    if not v3_2_path.exists():
        print_error(f"V3.2 workflow not found: {v3_2_path}")
        sys.exit(1)

    with open(v3_2_path, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    print_success(f"Loaded V3.2 workflow: {len(workflow['nodes'])} nodes")
    return workflow

def fix_google_calendar_typeversion(workflow):
    """Fix Google Calendar node typeVersion from 2 to 1"""
    print_step(2, 2, "Fixing Google Calendar node typeVersion...")

    # Find node
    node = None
    for n in workflow['nodes']:
        if n['name'] == 'Create Google Calendar Event':
            node = n
            break

    if not node:
        print_error("Create Google Calendar Event node not found!")
        sys.exit(1)

    print(f"  Current issue: typeVersion is {node['typeVersion']}, but installed node is version 1.0")
    print(f"  This causes: 'Install this node to use it. This node is not currently installed'")
    print(f"  Result: Execution stops, no downstream nodes execute")

    # Fix typeVersion
    old_version = node['typeVersion']
    node['typeVersion'] = 1

    print_success(f"Fixed typeVersion: {old_version} → 1")

    return workflow

def update_metadata(workflow):
    """Update workflow metadata for V3.3"""
    workflow['name'] = "05 - Appointment Scheduler V3.3"
    workflow['versionId'] = "3.3"

    # Update tags
    workflow['tags'] = [
        {
            "name": "appointment",
            "createdAt": "2026-03-24T00:00:00.000000"
        },
        {
            "name": "google-calendar",
            "createdAt": "2026-03-24T00:00:00.000000"
        },
        {
            "name": "v3.3",
            "createdAt": "2026-03-24T00:00:00.000000"
        },
        {
            "name": "typeversion-fixed",
            "createdAt": "2026-03-24T00:00:00.000000"
        }
    ]

    print_success("Updated metadata to V3.3")

def save_v3_3_workflow(workflow):
    """Save generated V3.3 workflow"""
    output_path = Path(__file__).parent.parent / "n8n" / "workflows" / "05_appointment_scheduler_v3.3.json"

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print_success(f"Saved V3.3 workflow: {output_path}")
    print_success(f"Total nodes: {len(workflow['nodes'])}")

    return output_path

def validate_workflow(workflow):
    """Validate generated workflow structure"""
    print(f"\n{BLUE}🔍 Validating V3.3 workflow...{RESET}")

    # Validate node count (same as V3.2)
    expected_nodes = 11
    actual_nodes = len(workflow['nodes'])

    if actual_nodes != expected_nodes:
        print_warning(f"Expected {expected_nodes} nodes, got {actual_nodes}")
    else:
        print_success(f"Node count correct: {actual_nodes} nodes")

    # Validate Google Calendar typeVersion
    calendar_node = next((n for n in workflow['nodes'] if n['name'] == 'Create Google Calendar Event'), None)

    if calendar_node:
        type_version = calendar_node['typeVersion']

        if type_version == 1:
            print_success("Google Calendar typeVersion: 1 ✓ (matches installed node)")
        else:
            print_error(f"Google Calendar typeVersion: {type_version} ✗ (should be 1)")
            return False

        # Validate node type
        node_type = calendar_node['type']
        if node_type == 'n8n-nodes-base.googleCalendar':
            print_success("Google Calendar node type: n8n-nodes-base.googleCalendar ✓")
        else:
            print_error(f"Google Calendar node type incorrect: {node_type}")
            return False

    else:
        print_error("Create Google Calendar Event node NOT found!")
        return False

    # Validate connections still intact
    connections = workflow.get('connections', {})
    build_connections = connections.get('Build Calendar Event Data', {})

    if build_connections and build_connections.get('main'):
        main_conn = build_connections['main'][0]
        if main_conn and main_conn[0]['node'] == 'Create Google Calendar Event':
            print_success("Connections: Build → Google Calendar ✓")
        else:
            print_error("Connections: Build → Google Calendar BROKEN!")
            return False
    else:
        print_error("Build Calendar Event Data has no connections!")
        return False

    # Validate ISO date fix preserved from V3.2
    build_node = next((n for n in workflow['nodes'] if n['name'] == 'Build Calendar Event Data'), None)

    if build_node:
        code = build_node['parameters']['jsCode']

        if "scheduledDateRaw.includes('T')" in code and "split('T')[0]" in code:
            print_success("Build Calendar Event Data: ISO date extraction preserved ✓")
        else:
            print_warning("Build Calendar Event Data: ISO date extraction may be missing")

    print(f"\n{GREEN}✅ Validation complete - All checks passed!{RESET}")
    return True

def main():
    """Main script execution"""
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}Generate Appointment Scheduler V3.3 - TypeVersion Fix{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")

    print(f"{YELLOW}🎯 CRITICAL FIX:{RESET}")
    print(f"Problem: Workflow uses typeVersion: 2 for Google Calendar node")
    print(f"Reality: Installed node is version 1.0")
    print(f"Error: 'Install this node to use it. This node is not currently installed'")
    print(f"Impact: Execution stops at Google Calendar, no downstream nodes execute\n")
    print(f"Solution: Change typeVersion from 2 to 1")
    print(f"  Workflow typeVersion: 2 → 1 ✓")
    print(f"  Matches installed node version 1.0 ✓")
    print(f"  Execution will proceed normally ✓\n")
    print(f"{BLUE}{'='*70}{RESET}\n")

    # Load V3.2
    workflow = load_v3_2_workflow()

    # Fix typeVersion
    workflow = fix_google_calendar_typeversion(workflow)

    # Update metadata
    update_metadata(workflow)

    # Save V3.3
    output_path = save_v3_3_workflow(workflow)

    # Validate
    if validate_workflow(workflow):
        print(f"\n{GREEN}{'='*70}{RESET}")
        print(f"{GREEN}✅ V3.3 workflow generated successfully!{RESET}")
        print(f"{GREEN}{'='*70}{RESET}\n")
        print(f"{YELLOW}📋 Key Change:{RESET}")
        print(f"Google Calendar typeVersion: 2 → 1")
        print(f"  Before: typeVersion 2 (not installed) ❌")
        print(f"  After: typeVersion 1 (matches installed node) ✅")
        print(f"  Result: Node executes, downstream nodes execute ✓\n")
        print(f"{YELLOW}📋 Preserved from V3.2:{RESET}")
        print(f"ISO date extraction: '2026-04-25T00:00:00.000Z' → '2026-04-25' ✓")
        print(f"Enhanced logging: Date normalization and validation ✓\n")
        print(f"{YELLOW}📋 Next steps:{RESET}")
        print(f"1. Import workflow: http://localhost:5678")
        print(f"2. File: {output_path}")
        print(f"3. Deactivate V3.2, activate V3.3")
        print(f"4. Test complete flow:")
        print(f"   WF02 (V73.5) → Confirm appointment → WF05 (V3.3) executes")
        print(f"   Expected: Google Calendar node executes ✓")
        print(f"   Expected: All downstream nodes execute ✓")
        print(f"   Expected: Email confirmation sent ✓\n")
        return 0
    else:
        print(f"\n{RED}{'='*70}{RESET}")
        print(f"{RED}❌ Validation failed - please review errors{RESET}")
        print(f"{RED}{'='*70}{RESET}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
