#!/usr/bin/env python3
"""
Fix V72 Create Appointment in Database Query
=============================================

PROBLEM: Query uses $1, $2 parameters but data comes from n8n expressions
SOLUTION: Replace parameterized query with n8n expression-based query

Author: Claude Code
Date: 2026-03-18
"""

import json
import sys
from pathlib import Path

def fix_create_appointment_query(workflow_path: str) -> bool:
    """
    Fix Create Appointment in Database query to use proper n8n expressions.
    """

    print(f"🔧 V72 Create Appointment Query Fix")
    print(f"=" * 70)
    print(f"Input: {workflow_path}\n")

    # Read workflow
    try:
        with open(workflow_path, 'r', encoding='utf-8') as f:
            workflow = json.load(f)
    except Exception as e:
        print(f"❌ ERROR: Could not read workflow file: {e}")
        return False

    # Find Create Appointment in Database node
    node_found = False
    for node in workflow['nodes']:
        if node['name'] == 'Create Appointment in Database':
            node_found = True

            print("✅ Found 'Create Appointment in Database' node")
            print()

            # NEW QUERY: Uses collected_data from State Machine Logic output
            # Data flow: State Machine Logic → Build Update Queries → ... → Create Appointment
            new_query = """-- V72: Create Appointment in Database
-- Data comes from State Machine Logic output via collected_data
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
    '{{ $json.collected_data.scheduled_date }}',
    '{{ $json.collected_data.scheduled_time_start }}',
    '{{ $json.collected_data.scheduled_time_end }}',
    '{{ $json.collected_data.service_type }}',
    'Agendamento via WhatsApp Bot - Cliente: {{ $json.collected_data.lead_name }} | Cidade: {{ $json.collected_data.city }}',
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

            print("📝 OLD Query:")
            print(node['parameters']['query'][:200])
            print("...")
            print()

            print("✅ NEW Query:")
            print(new_query[:200])
            print("...")
            print()

            # Update query
            node['parameters']['query'] = new_query

            # Remove queryParameters if exists
            if 'additionalFields' in node['parameters']:
                if 'queryParameters' in node['parameters']['additionalFields']:
                    del node['parameters']['additionalFields']['queryParameters']
                    print("✅ Removed queryParameters from additionalFields")
                    print()

            break

    if not node_found:
        print("❌ ERROR: 'Create Appointment in Database' node not found")
        return False

    # Save workflow
    try:
        with open(workflow_path, 'w', encoding='utf-8') as f:
            json.dump(workflow, f, indent=2, ensure_ascii=False)

        print(f"💾 Saved fixed workflow to: {workflow_path}")

        # Validate JSON
        with open(workflow_path, 'r', encoding='utf-8') as f:
            json.load(f)

        print(f"✅ JSON syntax validated")

    except Exception as e:
        print(f"❌ ERROR: Could not save fixed workflow: {e}")
        return False

    print(f"\n{'='*70}")
    print(f"✅ CREATE APPOINTMENT QUERY FIXED")
    print(f"{'='*70}\n")

    print("📋 Data Flow:")
    print("   1. State 9 → Validate Date → saves scheduled_date to currentData")
    print("   2. State 10 → Validate Time → saves scheduled_time_start/end to currentData")
    print("   3. State 8 → State Machine Logic → merges currentData into collected_data")
    print("   4. Build Update Queries → passes collected_data to downstream nodes")
    print("   5. Create Appointment → reads from collected_data ✅")
    print()

    print("📋 Query Fields:")
    print("   - phone_number: from $json.phone_number (State Machine output)")
    print("   - scheduled_date: from $json.collected_data.scheduled_date (validated)")
    print("   - scheduled_time_start: from $json.collected_data.scheduled_time_start (validated)")
    print("   - scheduled_time_end: from $json.collected_data.scheduled_time_end (validated)")
    print("   - service_type: from $json.collected_data.service_type")
    print("   - lead_name, city: from $json.collected_data (for notes)")
    print()

    return True


if __name__ == '__main__':
    workflow_path = 'n8n/workflows/02_ai_agent_conversation_V72_COMPLETE.json'

    if not Path(workflow_path).exists():
        print(f"❌ ERROR: Workflow file not found: {workflow_path}")
        sys.exit(1)

    success = fix_create_appointment_query(workflow_path)
    sys.exit(0 if success else 1)
