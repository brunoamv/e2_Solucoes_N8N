#!/usr/bin/env python3
"""
Script: generate-appointment-scheduler-v3.py
Purpose: Fix queryParameters in all PostgreSQL nodes
Date: 2026-03-24

CRITICAL FIXES:
1. Get Appointment & Lead Data: $1 → {{ $json.appointment_id }}
2. Update Appointment: $1/$2/$3 → direct expressions
3. Create Appointment Reminders: $1 → direct expression

Strategy: Replace parameterized queries with direct n8n expressions
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

def load_v2_1_workflow():
    """Load V2.1 workflow JSON"""
    v2_1_path = Path(__file__).parent.parent / "n8n" / "workflows" / "05_appointment_scheduler_v2.1.json"

    print_step(1, 5, "Loading V2.1 workflow...")

    if not v2_1_path.exists():
        print_error(f"V2.1 workflow not found: {v2_1_path}")
        sys.exit(1)

    with open(v2_1_path, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    print_success(f"Loaded V2.1 workflow: {len(workflow['nodes'])} nodes")
    return workflow

def fix_get_appointment_node(workflow):
    """Fix Get Appointment & Lead Data queryParameters"""
    print_step(2, 5, "Fixing Get Appointment & Lead Data...")

    # Find node
    node = None
    for n in workflow['nodes']:
        if n['name'] == 'Get Appointment & Lead Data':
            node = n
            break

    if not node:
        print_error("Get Appointment & Lead Data node not found!")
        sys.exit(1)

    print(f"  Current query uses: $1 parameter")

    # NEW SQL: Replace $1 with direct expression
    new_query = """SELECT
    a.id as appointment_id,
    a.scheduled_date,
    a.scheduled_time_start,
    a.scheduled_time_end,
    a.service_type,
    a.notes,
    a.status,
    l.id as lead_id,
    l.name as lead_name,
    l.email as lead_email,
    l.phone_number,
    l.address,
    l.city,
    l.state,
    l.zip_code,
    l.service_details,
    l.rdstation_deal_id,
    c.whatsapp_name
FROM appointments a
INNER JOIN leads l ON a.lead_id = l.id
LEFT JOIN conversations c ON l.conversation_id = c.id
WHERE a.id = '{{ $json.appointment_id }}'
  AND a.status IN ('agendado', 'reagendado')
LIMIT 1;"""

    # Update query
    node['parameters']['query'] = new_query

    # CRITICAL: Remove queryParameters field
    if 'additionalFields' in node['parameters']:
        if 'queryParameters' in node['parameters']['additionalFields']:
            del node['parameters']['additionalFields']['queryParameters']
            print_success("Removed queryParameters field")

    print_success("Fixed query to use direct expression: {{ $json.appointment_id }}")

    return workflow

def fix_update_appointment_node(workflow):
    """Fix Update Appointment queryParameters"""
    print_step(3, 5, "Fixing Update Appointment...")

    # Find node
    node = None
    for n in workflow['nodes']:
        if n['name'] == 'Update Appointment':
            node = n
            break

    if not node:
        print_error("Update Appointment node not found!")
        sys.exit(1)

    print(f"  Current query uses: $1, $2, $3 parameters")

    # NEW SQL: Replace $1/$2/$3 with direct expressions
    new_query = """UPDATE appointments
SET
    google_calendar_event_id = CASE
        WHEN '{{ $('Create Google Calendar Event').item.json.id || 'NULL' }}' != 'NULL'
        THEN '{{ $('Create Google Calendar Event').item.json.id }}'
        ELSE google_calendar_event_id
    END,
    status = CASE
        WHEN '{{ $('Create Google Calendar Event').item.json.id || 'NULL' }}' != 'NULL'
        THEN 'confirmado'
        ELSE 'erro_calendario'
    END,
    notes = CASE
        WHEN '{{ $('Create Google Calendar Event').item.json.id || 'NULL' }}' = 'NULL'
             AND '{{ $('Create Google Calendar Event').item.json.error || 'NULL' }}' != 'NULL'
        THEN COALESCE(notes, '') || '
[ERRO] Falha ao criar evento no Google Calendar: ' || '{{ $('Create Google Calendar Event').item.json.error || '' }}'
        ELSE notes
    END,
    updated_at = NOW()
WHERE id = '{{ $('Build Calendar Event Data').item.json.appointment_id }}'
RETURNING
    id,
    status,
    google_calendar_event_id,
    CASE
        WHEN google_calendar_event_id IS NOT NULL THEN true
        ELSE false
    END as calendar_success;"""

    # Update query
    node['parameters']['query'] = new_query

    # CRITICAL: Remove queryParameters field
    if 'additionalFields' in node['parameters']:
        if 'queryParameters' in node['parameters']['additionalFields']:
            del node['parameters']['additionalFields']['queryParameters']
            print_success("Removed queryParameters field")

    print_success("Fixed query to use direct expressions")

    return workflow

def fix_create_reminders_node(workflow):
    """Fix Create Appointment Reminders queryParameters"""
    print_step(4, 5, "Fixing Create Appointment Reminders...")

    # Find node
    node = None
    for n in workflow['nodes']:
        if n['name'] == 'Create Appointment Reminders':
            node = n
            break

    if not node:
        print_error("Create Appointment Reminders node not found!")
        sys.exit(1)

    print(f"  Current query uses: $1 parameter")

    # NEW SQL: Replace $1 with direct expression
    new_query = """SELECT create_appointment_reminders('{{ $('Build Calendar Event Data').item.json.appointment_id }}');"""

    # Update query
    node['parameters']['query'] = new_query

    # CRITICAL: Remove queryParameters field
    if 'additionalFields' in node['parameters']:
        if 'queryParameters' in node['parameters']['additionalFields']:
            del node['parameters']['additionalFields']['queryParameters']
            print_success("Removed queryParameters field")

    print_success("Fixed query to use direct expression")

    return workflow

def update_metadata(workflow):
    """Update workflow metadata for V3"""
    print_step(5, 5, "Updating workflow metadata...")

    workflow['name'] = "05 - Appointment Scheduler V3"
    workflow['versionId'] = "3.0"

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
            "name": "v3.0",
            "createdAt": "2026-03-24T00:00:00.000000"
        },
        {
            "name": "query-params-fixed",
            "createdAt": "2026-03-24T00:00:00.000000"
        }
    ]

    print_success("Updated metadata to V3.0")

def save_v3_workflow(workflow):
    """Save generated V3 workflow"""
    output_path = Path(__file__).parent.parent / "n8n" / "workflows" / "05_appointment_scheduler_v3.json"

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print_success(f"Saved V3 workflow: {output_path}")
    print_success(f"Total nodes: {len(workflow['nodes'])}")

    return output_path

def validate_workflow(workflow):
    """Validate generated workflow structure"""
    print(f"\n{BLUE}🔍 Validating V3 workflow...{RESET}")

    # Validate node count (same as V2.1)
    expected_nodes = 11
    actual_nodes = len(workflow['nodes'])

    if actual_nodes != expected_nodes:
        print_warning(f"Expected {expected_nodes} nodes, got {actual_nodes}")
    else:
        print_success(f"Node count correct: {actual_nodes} nodes")

    # Validate all 3 nodes have NO queryParameters
    nodes_to_check = [
        'Get Appointment & Lead Data',
        'Update Appointment',
        'Create Appointment Reminders'
    ]

    all_clean = True
    for node_name in nodes_to_check:
        node = next((n for n in workflow['nodes'] if n['name'] == node_name), None)

        if node:
            has_query_params = (
                'additionalFields' in node['parameters'] and
                'queryParameters' in node['parameters']['additionalFields']
            )

            if has_query_params:
                print_error(f"{node_name} still has queryParameters!")
                all_clean = False
            else:
                print_success(f"{node_name}: queryParameters removed ✓")

            # Check query uses expressions
            query = node['parameters']['query']
            if '{{' in query and '}}' in query:
                print_success(f"{node_name}: uses n8n expressions ✓")
            else:
                print_warning(f"{node_name}: may not use expressions")

        else:
            print_error(f"{node_name} node NOT found!")
            all_clean = False

    if all_clean:
        print(f"\n{GREEN}✅ Validation complete - All checks passed!{RESET}")
        return True
    else:
        print(f"\n{RED}❌ Validation failed - please review errors{RESET}")
        return False

def main():
    """Main script execution"""
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}Generate Appointment Scheduler V3 - Query Parameter Fix{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")

    print(f"{YELLOW}🎯 CRITICAL FIXES:{RESET}")
    print(f"1. Get Appointment & Lead Data: $1 → {{ $json.appointment_id }}")
    print(f"2. Update Appointment: $1/$2/$3 → direct expressions")
    print(f"3. Create Appointment Reminders: $1 → direct expression")
    print(f"\nStrategy: Remove queryParameters, use n8n expressions")
    print(f"\n{BLUE}{'='*70}{RESET}\n")

    # Load V2.1
    workflow = load_v2_1_workflow()

    # Fix all 3 nodes
    workflow = fix_get_appointment_node(workflow)
    workflow = fix_update_appointment_node(workflow)
    workflow = fix_create_reminders_node(workflow)

    # Update metadata
    update_metadata(workflow)

    # Save V3
    output_path = save_v3_workflow(workflow)

    # Validate
    if validate_workflow(workflow):
        print(f"\n{GREEN}{'='*70}{RESET}")
        print(f"{GREEN}✅ V3 workflow generated successfully!{RESET}")
        print(f"{GREEN}{'='*70}{RESET}\n")
        print(f"{YELLOW}📋 Key Changes:{RESET}")
        print(f"1. Get Appointment & Lead Data: Removed $1 parameter")
        print(f"2. Update Appointment: Removed $1/$2/$3 parameters")
        print(f"3. Create Appointment Reminders: Removed $1 parameter")
        print(f"4. All queries now use direct n8n expressions\n")
        print(f"{YELLOW}📋 Next steps:{RESET}")
        print(f"1. Import workflow: http://localhost:5678")
        print(f"2. File: {output_path}")
        print(f"3. Deactivate V2.1, activate V3")
        print(f"4. Test complete flow:\"")
        print(f"   WF02 (V73.5) → Confirm appointment → WF05 (V3) executes")
        print(f"   Expected: All 3 queries execute without parameter errors ✓\n")
        return 0
    else:
        print(f"\n{RED}{'='*70}{RESET}")
        print(f"{RED}❌ Validation failed - please review errors{RESET}")
        print(f"{RED}{'='*70}{RESET}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
