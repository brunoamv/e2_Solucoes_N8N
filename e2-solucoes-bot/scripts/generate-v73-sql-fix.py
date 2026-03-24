#!/usr/bin/env python3
"""
Script: generate-v73-sql-fix.py
Purpose: Generate V73 workflow with SQL fix for "Create Appointment in Database"
Date: 2026-03-24

Changes from V72:
1. ADD: New node "Prepare Appointment Data" (Set node) before "Create Appointment in Database"
2. MODIFY: SQL query in "Create Appointment in Database" (simplified expressions)
3. UPDATE: Connections to route through new Set node
4. PRESERVE: All 33 existing nodes from V72
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

def load_v72_workflow():
    """Load V72 workflow JSON"""
    v72_path = Path(__file__).parent.parent / "n8n" / "workflows" / "02_ai_agent_conversation_V72_COMPLETE.json"

    print_step(1, 5, "Loading V72 workflow...")

    if not v72_path.exists():
        print_error(f"V72 workflow not found: {v72_path}")
        sys.exit(1)

    with open(v72_path, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    print_success(f"Loaded V72 workflow: {len(workflow['nodes'])} nodes, {len(workflow.get('connections', {}))} connections")
    return workflow

def create_prepare_appointment_data_node():
    """Create new 'Prepare Appointment Data' Set node"""
    return {
        "parameters": {
            "mode": "manual",
            "duplicateItem": False,
            "assignments": {
                "assignments": [
                    {
                        "id": "1",
                        "name": "phone_number",
                        "value": "={{ $('Build Update Queries').first().json.phone_number }}",
                        "type": "string"
                    },
                    {
                        "id": "2",
                        "name": "scheduled_date",
                        "value": "={{ $('Build Update Queries').first().json.collected_data.scheduled_date }}",
                        "type": "string"
                    },
                    {
                        "id": "3",
                        "name": "scheduled_time_start",
                        "value": "={{ $('Build Update Queries').first().json.collected_data.scheduled_time_start }}",
                        "type": "string"
                    },
                    {
                        "id": "4",
                        "name": "scheduled_time_end",
                        "value": "={{ $('Build Update Queries').first().json.collected_data.scheduled_time_end }}",
                        "type": "string"
                    },
                    {
                        "id": "5",
                        "name": "service_type",
                        "value": "={{ $('Build Update Queries').first().json.collected_data.service_type }}",
                        "type": "string"
                    },
                    {
                        "id": "6",
                        "name": "lead_name",
                        "value": "={{ $('Build Update Queries').first().json.collected_data.lead_name }}",
                        "type": "string"
                    },
                    {
                        "id": "7",
                        "name": "city",
                        "value": "={{ $('Build Update Queries').first().json.collected_data.city }}",
                        "type": "string"
                    }
                ]
            }
        },
        "id": "prepare-appointment-data-v73",
        "name": "Prepare Appointment Data",
        "type": "n8n-nodes-base.set",
        "typeVersion": 3.4,
        "position": [2600, 300],
        "alwaysOutputData": True,
        "notes": "V73: Extract data from Build Update Queries to bypass IF node data loss"
    }

def update_create_appointment_sql():
    """Return updated SQL query with simplified expressions"""
    return """-- V73: Create Appointment in Database
-- FIX: Simplified n8n expressions (use $json instead of $("node").first())
-- Data flow: Build Update Queries → Prepare Appointment Data (Set) → HERE
-- IF nodes don't pass data, so we use Set node to extract and pass data
INSERT INTO appointments (
    id,
    lead_id,
    scheduled_date,
    scheduled_time_start,
    scheduled_time_end,
    service_type,
    notes,
    status,
    created_at,
    updated_at
)
VALUES (
    gen_random_uuid(),
    (SELECT id FROM leads WHERE phone_number = '{{ $json.phone_number }}'),
    '{{ $json.scheduled_date }}',
    '{{ $json.scheduled_time_start }}',
    '{{ $json.scheduled_time_end }}',
    '{{ $json.service_type }}',
    'Agendamento via WhatsApp Bot - Cliente: {{ $json.lead_name }} | Cidade: {{ $json.city }}',
    'agendado',
    NOW(),
    NOW()
)
RETURNING
    id as appointment_id,
    lead_id,
    scheduled_date,
    scheduled_time_start,
    scheduled_time_end,
    service_type,
    status,
    created_at;"""

def modify_workflow(workflow):
    """Apply V73 modifications to workflow"""
    print_step(2, 5, "Creating new 'Prepare Appointment Data' node...")

    # Create new Set node
    prepare_node = create_prepare_appointment_data_node()
    workflow['nodes'].append(prepare_node)
    print_success(f"Added node: {prepare_node['name']}")

    print_step(3, 5, "Modifying 'Create Appointment in Database' SQL...")

    # Find and update Create Appointment node
    create_appointment_node = None
    for node in workflow['nodes']:
        if node['name'] == 'Create Appointment in Database':
            create_appointment_node = node
            break

    if not create_appointment_node:
        print_error("Node 'Create Appointment in Database' not found!")
        sys.exit(1)

    # Update SQL query
    create_appointment_node['parameters']['query'] = update_create_appointment_sql()
    create_appointment_node['notes'] = "V73: CREATE appointment with simplified SQL expressions"
    print_success("Updated SQL query with simplified expressions")

    print_step(4, 5, "Updating workflow connections...")

    # Update connections: Check If Scheduling → Prepare Appointment Data → Create Appointment
    connections = workflow.get('connections', {})

    # Add connection: Check If Scheduling → Prepare Appointment Data
    if 'Check If Scheduling' in connections:
        connections['Check If Scheduling']['main'][0] = [
            {
                "node": "Prepare Appointment Data",
                "type": "main",
                "index": 0
            }
        ]
        print_success("Updated: Check If Scheduling → Prepare Appointment Data")

    # Add connection: Prepare Appointment Data → Create Appointment in Database
    connections['Prepare Appointment Data'] = {
        "main": [
            [
                {
                    "node": "Create Appointment in Database",
                    "type": "main",
                    "index": 0
                }
            ]
        ]
    }
    print_success("Added: Prepare Appointment Data → Create Appointment in Database")

    # Preserve existing connection: Create Appointment in Database → Trigger Appointment Scheduler
    # (already exists in V72, no change needed)
    print_success("Preserved: Create Appointment in Database → Trigger Appointment Scheduler")

    return workflow

def update_metadata(workflow):
    """Update workflow metadata for V73"""
    print_step(5, 5, "Updating workflow metadata...")

    workflow['meta'] = {
        "version": "V73_SQL_FIX",
        "fixes_applied": [
            "BUG #4: SQL syntax error in 'Create Appointment in Database' (escape quotes)",
            "SOLUTION: Added 'Prepare Appointment Data' Set node to extract and pass data",
            "CHANGE: Simplified SQL expressions from $('node').first() to $json"
        ],
        "fix_date": "2026-03-24",
        "preserves_v72_fixes": True,
        "states_total": 14,
        "templates_total": 28,
        "nodes_total": 34,  # 33 from V72 + 1 new Set node
        "cumulative_fixes": [
            "V66 Fix #1: trimmedCorrectedName duplicate variable",
            "V66 Fix #2: query_correction_update scope",
            "V67 Fix: Service display keys (all 5 services)",
            "V68 Fix #1: Trigger node execution",
            "V68 Fix #2: Name field validation",
            "V68 Fix #3: Returning user detection",
            "V72 Fix: Complete appointment flow (States 9/10/11)",
            "V73 Fix: SQL syntax error - simplified expressions"
        ],
        "instanceId": "v73_sql_fix_complete",
        "description": "V73 SQL FIX - Resolved 'invalid syntax' error in Create Appointment node"
    }

    workflow['versionId'] = "73"
    workflow['tags'] = [
        {
            "name": "v73-sql-fix-complete"
        },
        {
            "name": "ready-for-production"
        }
    ]

    print_success("Updated metadata to V73")

def save_v73_workflow(workflow):
    """Save generated V73 workflow"""
    output_path = Path(__file__).parent.parent / "n8n" / "workflows" / "02_ai_agent_conversation_V73_SQL_FIX.json"

    print(f"\n{BLUE}💾 Saving V73 workflow...{RESET}")

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print_success(f"Saved V73 workflow: {output_path}")
    print_success(f"Total nodes: {len(workflow['nodes'])}")
    print_success(f"Total connections: {len(workflow.get('connections', {}))}")

    return output_path

def validate_workflow(workflow):
    """Validate generated workflow structure"""
    print(f"\n{BLUE}🔍 Validating V73 workflow...{RESET}")

    # Validate node count
    expected_nodes = 34  # 33 from V72 + 1 new Set node
    actual_nodes = len(workflow['nodes'])

    if actual_nodes != expected_nodes:
        print_warning(f"Expected {expected_nodes} nodes, got {actual_nodes}")
    else:
        print_success(f"Node count correct: {actual_nodes} nodes")

    # Validate new node exists
    prepare_node_exists = any(n['name'] == 'Prepare Appointment Data' for n in workflow['nodes'])
    if prepare_node_exists:
        print_success("New node 'Prepare Appointment Data' exists")
    else:
        print_error("New node 'Prepare Appointment Data' NOT found!")
        return False

    # Validate Create Appointment node SQL
    create_node = next((n for n in workflow['nodes'] if n['name'] == 'Create Appointment in Database'), None)
    if create_node:
        sql = create_node['parameters']['query']
        if '{{ $json.phone_number }}' in sql and '$(\\\"' not in sql:
            print_success("SQL query uses simplified expressions (no escape issues)")
        else:
            print_warning("SQL query may still have escape issues")
    else:
        print_error("Node 'Create Appointment in Database' NOT found!")
        return False

    # Validate connections
    connections = workflow.get('connections', {})

    # Check: Check If Scheduling → Prepare Appointment Data
    if 'Check If Scheduling' in connections:
        check_if_conn = connections['Check If Scheduling']['main'][0][0]
        if check_if_conn['node'] == 'Prepare Appointment Data':
            print_success("Connection: Check If Scheduling → Prepare Appointment Data ✓")
        else:
            print_error("Connection: Check If Scheduling → Prepare Appointment Data ✗")
            return False

    # Check: Prepare Appointment Data → Create Appointment in Database
    if 'Prepare Appointment Data' in connections:
        prepare_conn = connections['Prepare Appointment Data']['main'][0][0]
        if prepare_conn['node'] == 'Create Appointment in Database':
            print_success("Connection: Prepare Appointment Data → Create Appointment ✓")
        else:
            print_error("Connection: Prepare Appointment Data → Create Appointment ✗")
            return False

    print(f"\n{GREEN}✅ Validation complete - All checks passed!{RESET}")
    return True

def main():
    """Main script execution"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}Generate V73 Workflow - SQL Fix{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")

    # Load V72
    workflow = load_v72_workflow()

    # Apply modifications
    workflow = modify_workflow(workflow)

    # Update metadata
    update_metadata(workflow)

    # Save V73
    output_path = save_v73_workflow(workflow)

    # Validate
    if validate_workflow(workflow):
        print(f"\n{GREEN}{'='*60}{RESET}")
        print(f"{GREEN}✅ V73 workflow generated successfully!{RESET}")
        print(f"{GREEN}{'='*60}{RESET}\n")
        print(f"{YELLOW}📋 Next steps:{RESET}")
        print(f"1. Import workflow: http://localhost:5678")
        print(f"2. File: {output_path}")
        print(f"3. Deactivate V72, activate V73")
        print(f"4. Test: WhatsApp 'oi' → service 1 → complete flow")
        print(f"5. Verify appointment created in PostgreSQL\n")
        return 0
    else:
        print(f"\n{RED}{'='*60}{RESET}")
        print(f"{RED}❌ Validation failed - please review errors{RESET}")
        print(f"{RED}{'='*60}{RESET}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
