#!/usr/bin/env python3
"""
Fix V72 COMPLETE IF Node Data Loss
===================================

PROBLEM: "Check If Scheduling" is an IF node that doesn't pass through data
SOLUTION: Change "Create Appointment in Database" to read from "Build Update Queries" instead

Root Cause:
  1. IF nodes in n8n evaluate conditions and route to true/false outputs
  2. They DO NOT automatically pass through input data
  3. Downstream nodes receive empty/minimal data
  4. Current flow: Build Update Queries → Check If Scheduling (IF) → Create Appointment
  5. "Create Appointment" receives NO DATA because IF node doesn't pass it through

Fix Strategy:
  1. Keep IF node for routing logic (required for flow control)
  2. Change "Create Appointment in Database" expressions to read from "Build Update Queries"
  3. Use: {{ $('Build Update Queries').first().json.collected_data.* }}
  4. This reaches back to the node BEFORE the IF node that has all data

Author: Claude Code
Date: 2026-03-18
"""

import json
import sys
from pathlib import Path

def fix_if_node_data_loss(workflow_path: str) -> bool:
    """
    Fix data loss caused by IF node in appointment flow.
    Update Create Appointment in Database to read from Build Update Queries.
    """

    print(f"🔧 V72 IF Node Data Loss Fix")
    print(f"=" * 70)
    print(f"Input: {workflow_path}\n")

    # Read workflow
    try:
        with open(workflow_path, 'r', encoding='utf-8') as f:
            workflow = json.load(f)
    except Exception as e:
        print(f"❌ ERROR: Could not read workflow file: {e}")
        return False

    print("✅ Workflow loaded")

    # Find Create Appointment in Database node
    node_found = False
    for node in workflow['nodes']:
        if node['name'] == 'Create Appointment in Database':
            node_found = True

            print("✅ Found 'Create Appointment in Database' node")
            print()

            print("🔍 PROBLEM ANALYSIS:")
            print("   Current Data Flow:")
            print("   Build Update Queries → Check If Scheduling (IF NODE) → Create Appointment")
            print("                              ↓")
            print("                         LOSES DATA (IF nodes don't pass through)")
            print()

            print("🔧 FIX STRATEGY:")
            print("   Change expressions to read from 'Build Update Queries' (before IF node)")
            print("   Old: {{ $json.collected_data.* }}")
            print("   New: {{ $('Build Update Queries').first().json.collected_data.* }}")
            print()

            # NEW QUERY: Read from Build Update Queries (before IF node)
            new_query = """-- V72: Create Appointment in Database
-- FIX: Read from 'Build Update Queries' to bypass IF node data loss
-- Data flow: State Machine → Build Update Queries → Check If Scheduling (IF) → HERE
-- IF nodes don't pass data, so we read from Build Update Queries
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
    (SELECT id FROM leads WHERE phone_number = '{{ $(\\"Build Update Queries\\").first().json.phone_number }}'),
    '{{ $(\\"Build Update Queries\\").first().json.collected_data.scheduled_date }}',
    '{{ $(\\"Build Update Queries\\").first().json.collected_data.scheduled_time_start }}',
    '{{ $(\\"Build Update Queries\\").first().json.collected_data.scheduled_time_end }}',
    '{{ $(\\"Build Update Queries\\").first().json.collected_data.service_type }}',
    'Agendamento via WhatsApp Bot - Cliente: {{ $(\\"Build Update Queries\\").first().json.collected_data.lead_name }} | Cidade: {{ $(\\"Build Update Queries\\").first().json.collected_data.city }}',
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

            print("📝 OLD Query (reads from $json - empty due to IF node):")
            print(node['parameters']['query'][:200])
            print("...")
            print()

            print("✅ NEW Query (reads from 'Build Update Queries' directly):")
            print(new_query[:300])
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
    print(f"✅ IF NODE DATA LOSS FIXED")
    print(f"{'='*70}\n")

    print("📋 Technical Details:")
    print("   - IF nodes in n8n evaluate conditions but don't pass through data")
    print("   - Downstream nodes receive empty $json object")
    print("   - Solution: Reference node BEFORE the IF node using $('NodeName').first().json")
    print("   - 'Build Update Queries' has all data: phone_number, collected_data, etc.")
    print("   - 'Create Appointment' now reads directly from 'Build Update Queries'")
    print()

    print("📋 Data Flow (FIXED):")
    print("   1. State Machine Logic → outputs collected_data")
    print("   2. Build Update Queries → passes collected_data + phone_number")
    print("   3. Check If Scheduling (IF) → routes based on next_stage (doesn't pass data)")
    print("   4. Create Appointment → reads from 'Build Update Queries' ✅")
    print()

    return True


if __name__ == '__main__':
    workflow_path = 'n8n/workflows/02_ai_agent_conversation_V72_COMPLETE.json'

    if not Path(workflow_path).exists():
        print(f"❌ ERROR: Workflow file not found: {workflow_path}")
        sys.exit(1)

    success = fix_if_node_data_loss(workflow_path)
    sys.exit(0 if success else 1)
