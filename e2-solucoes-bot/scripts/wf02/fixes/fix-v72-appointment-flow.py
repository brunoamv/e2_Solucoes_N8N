#!/usr/bin/env python3
"""
Fix V72 COMPLETE Appointment Flow
==================================

PROBLEM: "Create Appointment in Database" node is disconnected from flow.
         "Trigger Appointment Scheduler" tries to reference it but it never executes.

SOLUTION: Insert "Create Appointment in Database" before "Trigger Appointment Scheduler"

Flow BEFORE (BROKEN):
  Check If Scheduling → Trigger Appointment Scheduler → Respond to Webhook
                              ↓ (tries to read from unexecuted node)
  Create Appointment in Database (ISOLATED, NO INPUT)

Flow AFTER (FIXED):
  Check If Scheduling → Create Appointment in Database → Trigger Appointment Scheduler → Respond to Webhook

Author: Claude Code
Date: 2026-03-18
"""

import json
import sys
from pathlib import Path

def fix_appointment_flow(workflow_path: str) -> bool:
    """
    Fix appointment flow by connecting Create Appointment in Database
    between Check If Scheduling and Trigger Appointment Scheduler.
    """

    print(f"🔧 V72 COMPLETE Appointment Flow Fix")
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
    print(f"   Total nodes: {len(workflow['nodes'])}\n")

    # Current connections
    print("🔍 Current Flow:")
    print()

    # Find Check If Scheduling connections
    if 'Check If Scheduling' in workflow['connections']:
        check_conn = workflow['connections']['Check If Scheduling']
        print("📤 Check If Scheduling →")
        for output_type in check_conn:
            for connection_list in check_conn[output_type]:
                for target in connection_list:
                    print(f"      → {target['node']}")
        print()

    # Find Trigger Appointment Scheduler connections
    if 'Create Appointment in Database' in workflow['connections']:
        create_conn = workflow['connections']['Create Appointment in Database']
        print("📤 Create Appointment in Database →")
        for output_type in create_conn:
            for connection_list in create_conn[output_type]:
                for target in connection_list:
                    print(f"      → {target['node']}")
        print()
    else:
        print("📤 Create Appointment in Database → (NO CONNECTIONS)")
        print()

    print("=" * 70)
    print("🔧 Applying Fix")
    print("=" * 70)
    print()

    # Step 1: Update Check If Scheduling to point to Create Appointment in Database
    if 'Check If Scheduling' not in workflow['connections']:
        workflow['connections']['Check If Scheduling'] = {}

    if 'main' not in workflow['connections']['Check If Scheduling']:
        workflow['connections']['Check If Scheduling']['main'] = [[]]

    # Find current connection from Check If Scheduling to Trigger Appointment Scheduler
    old_connection = None
    if workflow['connections']['Check If Scheduling']['main']:
        for i, conn_list in enumerate(workflow['connections']['Check If Scheduling']['main']):
            for conn in conn_list:
                if conn['node'] == 'Trigger Appointment Scheduler':
                    old_connection = {
                        'output_index': i,
                        'conn': conn
                    }
                    break

    if old_connection:
        print(f"✅ Found: Check If Scheduling → Trigger Appointment Scheduler")
        print(f"   Changing to: Check If Scheduling → Create Appointment in Database")
        print()

        # Replace connection
        output_idx = old_connection['output_index']
        workflow['connections']['Check If Scheduling']['main'][output_idx] = [
            {
                'node': 'Create Appointment in Database',
                'type': 'main',
                'index': 0
            }
        ]

        print(f"✅ STEP 1: Check If Scheduling now connects to Create Appointment in Database")
        print()

    else:
        print("⚠️  WARNING: No direct connection from Check If Scheduling to Trigger Appointment Scheduler")
        print("   Adding new connection anyway...")
        print()

        # Add connection to first output
        if not workflow['connections']['Check If Scheduling']['main']:
            workflow['connections']['Check If Scheduling']['main'] = [[]]

        workflow['connections']['Check If Scheduling']['main'][0] = [
            {
                'node': 'Create Appointment in Database',
                'type': 'main',
                'index': 0
            }
        ]

    # Step 2: Create Appointment in Database already connects to Trigger Appointment Scheduler
    if 'Create Appointment in Database' in workflow['connections']:
        print(f"✅ STEP 2: Create Appointment in Database already connects to Trigger Appointment Scheduler")
        print()
    else:
        print(f"⚠️  Adding: Create Appointment in Database → Trigger Appointment Scheduler")
        workflow['connections']['Create Appointment in Database'] = {
            'main': [[
                {
                    'node': 'Trigger Appointment Scheduler',
                    'type': 'main',
                    'index': 0
                }
            ]]
        }
        print(f"✅ STEP 2: Connected Create Appointment in Database → Trigger Appointment Scheduler")
        print()

    # Verify fixed flow
    print("=" * 70)
    print("✅ Fixed Flow:")
    print("=" * 70)
    print()

    print("📤 Check If Scheduling →")
    if 'Check If Scheduling' in workflow['connections']:
        check_conn = workflow['connections']['Check If Scheduling']
        for output_type in check_conn:
            for connection_list in check_conn[output_type]:
                for target in connection_list:
                    print(f"      → {target['node']}")
    print()

    print("📤 Create Appointment in Database →")
    if 'Create Appointment in Database' in workflow['connections']:
        create_conn = workflow['connections']['Create Appointment in Database']
        for output_type in create_conn:
            for connection_list in create_conn[output_type]:
                for target in connection_list:
                    print(f"      → {target['node']}")
    print()

    print("📤 Trigger Appointment Scheduler →")
    if 'Trigger Appointment Scheduler' in workflow['connections']:
        trigger_conn = workflow['connections']['Trigger Appointment Scheduler']
        for output_type in trigger_conn:
            for connection_list in trigger_conn[output_type]:
                for target in connection_list:
                    print(f"      → {target['node']}")
    print()

    # Save fixed workflow
    output_path = workflow_path  # Overwrite original

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(workflow, f, indent=2, ensure_ascii=False)

        print(f"💾 Saved fixed workflow to: {output_path}")

        # Validate JSON
        with open(output_path, 'r', encoding='utf-8') as f:
            json.load(f)  # Will raise if invalid

        print(f"✅ JSON syntax validated")

    except Exception as e:
        print(f"❌ ERROR: Could not save fixed workflow: {e}")
        return False

    print(f"\n{'='*70}")
    print(f"✅ V72 COMPLETE APPOINTMENT FLOW FIXED")
    print(f"{'='*70}\n")

    print("📋 Next Steps:")
    print("   1. Import workflow to n8n: http://localhost:5678")
    print("   2. Navigate to: Workflows → Import from File")
    print("   3. Select: n8n/workflows/02_ai_agent_conversation_V72_COMPLETE.json")
    print("   4. Verify connections visually in workflow editor")
    print("   5. Test appointment flow: service 1/3 → complete data → confirm → schedule")
    print()

    return True


if __name__ == '__main__':
    workflow_path = 'n8n/workflows/02_ai_agent_conversation_V72_COMPLETE.json'

    if not Path(workflow_path).exists():
        print(f"❌ ERROR: Workflow file not found: {workflow_path}")
        sys.exit(1)

    success = fix_appointment_flow(workflow_path)
    sys.exit(0 if success else 1)
