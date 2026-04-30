#!/usr/bin/env python3
"""
WF02 V92 Complete Workflow Generator
====================================
Generates complete V92 workflow JSON from V90 base with:
1. V91 state machine code
2. Database refresh node after "Prepare WF06 Next Dates Data"
3. Updated Merge node connections for fresh database data

Date: 2026-04-20
Version: V92 Database Refresh Fix
"""

import json
import sys
import uuid
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent.parent
V90_WORKFLOW = BASE_DIR / "n8n/workflows/02_ai_agent_conversation_V90_COMPLETE.json"
V91_STATE_MACHINE = BASE_DIR / "scripts/wf02-v91-state-initialization-fix.js"
OUTPUT_V92 = BASE_DIR / "n8n/workflows/02_ai_agent_conversation_V92.json"

def load_v90_workflow():
    """Load V90 workflow JSON"""
    print(f"📖 Loading V90 workflow from: {V90_WORKFLOW}")
    with open(V90_WORKFLOW, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_v91_state_machine():
    """Load V91 state machine code"""
    print(f"📖 Loading V91 state machine from: {V91_STATE_MACHINE}")
    with open(V91_STATE_MACHINE, 'r', encoding='utf-8') as f:
        return f.read()

def find_node_by_name(workflow, name):
    """Find node by exact name"""
    for i, node in enumerate(workflow['nodes']):
        if node.get('name') == name:
            return i, node
    return None, None

def update_state_machine_code(workflow, v91_code):
    """Update State Machine Logic node with V91 code"""
    print("🔄 Updating State Machine Logic with V91 code...")

    idx, node = find_node_by_name(workflow, "State Machine Logic")
    if not node:
        print("❌ ERROR: State Machine Logic node not found!")
        return False

    # Update jsCode parameter
    if 'parameters' in node and 'jsCode' in node['parameters']:
        node['parameters']['jsCode'] = v91_code
        print("✅ State Machine Logic updated with V91 code")
        return True
    else:
        print("❌ ERROR: State Machine Logic node has no jsCode parameter!")
        return False

def create_refresh_node():
    """Create 'Get Conversation Details (Refresh)' node"""
    print("🆕 Creating 'Get Conversation Details (Refresh)' node...")

    refresh_node = {
        "parameters": {
            "operation": "executeQuery",
            "query": "SELECT\n  phone_number,\n  lead_name,\n  contact_name,\n  contact_phone,\n  email,\n  city,\n  service_type,\n  service_selected,\n  current_state,\n  collected_data::text as collected_data_text,\n  created_at,\n  updated_at\nFROM conversations\nWHERE phone_number = '{{ $node[\"Prepare WF06 Next Dates Data\"].json.phone_number }}'\nLIMIT 1;",
            "additionalFields": {}
        },
        "id": str(uuid.uuid4()),
        "name": "Get Conversation Details (Refresh)",
        "type": "n8n-nodes-base.postgres",
        "typeVersion": 1,
        "position": [1140, 200],
        "alwaysOutputData": True,
        "credentials": {
            "postgres": {
                "id": "VXA1r8sd0TMIdPvS",
                "name": "PostgreSQL - E2 Bot"
            }
        }
    }

    print(f"✅ Refresh node created with ID: {refresh_node['id']}")
    return refresh_node

def insert_refresh_node(workflow, refresh_node):
    """Insert refresh node after 'Prepare WF06 Next Dates Data'"""
    print("🔧 Inserting refresh node into workflow...")

    # Find Prepare node
    prepare_idx, prepare_node = find_node_by_name(workflow, "Prepare WF06 Next Dates Data")
    if not prepare_node:
        print("❌ ERROR: 'Prepare WF06 Next Dates Data' node not found!")
        return False

    print(f"✅ Found 'Prepare WF06 Next Dates Data' at index {prepare_idx}")

    # Insert refresh node after prepare node
    workflow['nodes'].insert(prepare_idx + 1, refresh_node)
    print(f"✅ Refresh node inserted at index {prepare_idx + 1}")

    return True

def update_connections(workflow):
    """Update workflow connections for V92"""
    print("🔗 Updating workflow connections...")

    # Find node indices
    prepare_idx, prepare_node = find_node_by_name(workflow, "Prepare WF06 Next Dates Data")
    refresh_idx, refresh_node = find_node_by_name(workflow, "Get Conversation Details (Refresh)")
    merge_idx, merge_node = find_node_by_name(workflow, "Merge WF06 Next Dates with User Data")
    old_details_idx, old_details_node = find_node_by_name(workflow, "Get Conversation Details")

    if not all([prepare_node, refresh_node, merge_node]):
        print("❌ ERROR: Required nodes not found!")
        return False

    print(f"✅ Found nodes - Prepare: {prepare_idx}, Refresh: {refresh_idx}, Merge: {merge_idx}")

    # Initialize connections if not exists
    if 'connections' not in workflow:
        workflow['connections'] = {}

    # Connection 1: Prepare → Refresh
    prepare_name = prepare_node['name']
    if prepare_name not in workflow['connections']:
        workflow['connections'][prepare_name] = {"main": [[]]}

    # Add connection to Refresh (if not exists)
    refresh_connection = {
        "node": "Get Conversation Details (Refresh)",
        "type": "main",
        "index": 0
    }

    if refresh_connection not in workflow['connections'][prepare_name]['main'][0]:
        workflow['connections'][prepare_name]['main'][0].append(refresh_connection)
        print("✅ Added connection: Prepare → Refresh")

    # Connection 2: Refresh → Merge (Input 1)
    refresh_name = refresh_node['name']
    if refresh_name not in workflow['connections']:
        workflow['connections'][refresh_name] = {"main": [[]]}

    merge_connection = {
        "node": "Merge WF06 Next Dates with User Data",
        "type": "main",
        "index": 1
    }

    workflow['connections'][refresh_name]['main'][0] = [merge_connection]
    print("✅ Added connection: Refresh → Merge (Input 1)")

    # Connection 3: Remove old "Get Conversation Details" → Merge (Input 1) connection
    if old_details_node:
        old_details_name = old_details_node['name']
        if old_details_name in workflow['connections']:
            # Filter out Merge connections from old details node
            old_connections = workflow['connections'][old_details_name].get('main', [[]])[0]
            new_connections = [
                conn for conn in old_connections
                if conn.get('node') != "Merge WF06 Next Dates with User Data"
            ]
            workflow['connections'][old_details_name]['main'][0] = new_connections
            print("✅ Removed old connection: Get Conversation Details → Merge")

    return True

def update_workflow_metadata(workflow):
    """Update workflow name and metadata"""
    print("📝 Updating workflow metadata...")

    workflow['name'] = "02_ai_agent_conversation_V92"
    print("✅ Workflow name updated to V92")

    return True

def save_v92_workflow(workflow):
    """Save V92 workflow to file"""
    print(f"💾 Saving V92 workflow to: {OUTPUT_V92}")

    # Ensure directory exists
    OUTPUT_V92.parent.mkdir(parents=True, exist_ok=True)

    # Save with pretty formatting
    with open(OUTPUT_V92, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print(f"✅ V92 workflow saved successfully ({OUTPUT_V92.stat().st_size} bytes)")
    return True

def validate_v92_workflow(workflow):
    """Validate V92 workflow structure"""
    print("\n🔍 Validating V92 workflow...")

    errors = []
    warnings = []

    # Check required nodes exist
    required_nodes = [
        "State Machine Logic",
        "Get Conversation Details (Refresh)",
        "Prepare WF06 Next Dates Data",
        "Merge WF06 Next Dates with User Data"
    ]

    for node_name in required_nodes:
        if not find_node_by_name(workflow, node_name)[1]:
            errors.append(f"Missing required node: {node_name}")

    # Check State Machine has V91 code
    _, state_machine = find_node_by_name(workflow, "State Machine Logic")
    if state_machine:
        code = state_machine.get('parameters', {}).get('jsCode', '')
        if 'V91' not in code:
            warnings.append("State Machine Logic does not contain V91 code markers")
        if 'v91_state_initialization_fix' not in code:
            warnings.append("State Machine Logic does not return v91_state_initialization_fix flag")

    # Check connections
    refresh_name = "Get Conversation Details (Refresh)"
    if refresh_name in workflow.get('connections', {}):
        refresh_conns = workflow['connections'][refresh_name].get('main', [[]])[0]
        has_merge_conn = any(
            conn.get('node') == "Merge WF06 Next Dates with User Data" and conn.get('index') == 1
            for conn in refresh_conns
        )
        if not has_merge_conn:
            errors.append("Refresh node does not connect to Merge Input 1")
    else:
        errors.append("Refresh node has no connections")

    # Print validation results
    print("\n" + "=" * 60)
    print("VALIDATION RESULTS")
    print("=" * 60)

    if errors:
        print(f"\n❌ ERRORS ({len(errors)}):")
        for error in errors:
            print(f"  • {error}")

    if warnings:
        print(f"\n⚠️  WARNINGS ({len(warnings)}):")
        for warning in warnings:
            print(f"  • {warning}")

    if not errors and not warnings:
        print("\n✅ ALL CHECKS PASSED")

    print("=" * 60)

    return len(errors) == 0

def main():
    """Main generation workflow"""
    print("\n" + "=" * 60)
    print("WF02 V92 COMPLETE WORKFLOW GENERATOR")
    print("=" * 60 + "\n")

    try:
        # Step 1: Load V90 workflow
        workflow = load_v90_workflow()
        print(f"✅ Loaded V90 workflow with {len(workflow.get('nodes', []))} nodes\n")

        # Step 2: Load V91 state machine code
        v91_code = load_v91_state_machine()
        print(f"✅ Loaded V91 state machine code ({len(v91_code)} chars)\n")

        # Step 3: Update State Machine Logic with V91 code
        if not update_state_machine_code(workflow, v91_code):
            print("❌ Failed to update State Machine Logic")
            return 1
        print()

        # Step 4: Create refresh node
        refresh_node = create_refresh_node()
        print()

        # Step 5: Insert refresh node
        if not insert_refresh_node(workflow, refresh_node):
            print("❌ Failed to insert refresh node")
            return 1
        print()

        # Step 6: Update connections
        if not update_connections(workflow):
            print("❌ Failed to update connections")
            return 1
        print()

        # Step 7: Update metadata
        update_workflow_metadata(workflow)
        print()

        # Step 8: Validate workflow
        if not validate_v92_workflow(workflow):
            print("\n⚠️  Validation failed, but workflow will be saved anyway")

        # Step 9: Save workflow
        if not save_v92_workflow(workflow):
            print("❌ Failed to save V92 workflow")
            return 1

        print("\n" + "=" * 60)
        print("✅ V92 WORKFLOW GENERATED SUCCESSFULLY")
        print("=" * 60)
        print(f"\n📄 Output file: {OUTPUT_V92}")
        print(f"📊 Total nodes: {len(workflow.get('nodes', []))}")
        print(f"🔗 Total connections: {len(workflow.get('connections', {}))}")
        print("\n🚀 Ready for deployment!")
        print("\n" + "=" * 60 + "\n")

        return 0

    except FileNotFoundError as e:
        print(f"\n❌ ERROR: File not found: {e}")
        return 1
    except json.JSONDecodeError as e:
        print(f"\n❌ ERROR: Invalid JSON: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
