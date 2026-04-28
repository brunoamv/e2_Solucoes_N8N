#!/usr/bin/env python3
"""
Generate WF02 V78.1.6 FINAL - HTTP Request TypeVersion Fix
===========================================================

CRITICAL FIX FROM V78.1.5:
- V78.1.5 PROBLEM: HTTP Request typeVersion 4.2 incompatible with n8n 2.15.0
- Root Cause: "options" structure for v4.2 differs from v3
- V78.1.6 FIX: Use typeVersion 3 (same as V74 working nodes) ✅

n8n HTTP Request Node v3 configuration:
- typeVersion: 3 ✅
- Simple options: {} structure ✅
- Body parameters instead of jsonBody ✅
- Proven working in V74.1_2_FUNCIONANDO.json ✅

Date: 2026-04-13
Author: E2 Bot Development Team - V78.1.6 TypeVersion Fix
Version: V78.1.6 FINAL
"""

import json
import uuid
import sys
from pathlib import Path

# Configuration
BASE_V74 = Path(__file__).parent.parent / "n8n" / "workflows" / "02_ai_agent_conversation_V74.1_2_FUNCIONANDO.json"
STATE_MACHINE_JS = Path(__file__).parent / "wf02-v78-state-machine.js"
OUTPUT_V78_1_6 = Path(__file__).parent.parent / "n8n" / "workflows" / "02_ai_agent_conversation_V78_1_6_FINAL.json"

WF06_WEBHOOK_URL = "http://e2bot-n8n-dev:5678/webhook/calendar-availability"


def generate_uuid():
    """Generate unique UUID for n8n nodes."""
    return str(uuid.uuid4())


def create_switch_node_v78_1_6(position, node_id=None):
    """
    Create properly configured Switch node for V78.1.6.

    Uses mode: "rules" with fallbackOutput for 3 outputs.
    NO empty options parameter (causes import errors).
    """
    if node_id is None:
        node_id = generate_uuid()

    return {
        "parameters": {
            "mode": "rules",
            "output": "multipleOutputs",
            "rules": {
                "rules": [
                    {
                        "expression": "={{ $json.next_stage === 'trigger_wf06_next_dates' }}",
                        "outputIndex": 0
                    },
                    {
                        "expression": "={{ $json.next_stage === 'trigger_wf06_available_slots' }}",
                        "outputIndex": 1
                    }
                ]
            },
            "fallbackOutput": 2
            # ✅ NO "options" parameter
        },
        "id": node_id,
        "name": "Route Based on Stage",
        "type": "n8n-nodes-base.switch",
        "typeVersion": 3,
        "position": position
    }


def create_http_request_node_v3(name, body_params, position, node_id=None):
    """
    Create HTTP Request node using typeVersion 3 (V74 working version).

    CRITICAL: Uses V74's proven structure with bodyParameters, not jsonBody.
    """
    if node_id is None:
        node_id = generate_uuid()

    return {
        "parameters": {
            "method": "POST",
            "url": WF06_WEBHOOK_URL,
            "sendHeaders": True,
            "headerParameters": {
                "parameters": [
                    {
                        "name": "Content-Type",
                        "value": "application/json"
                    }
                ]
            },
            "sendBody": True,
            "bodyParameters": {
                "parameters": body_params
            },
            "options": {}  # Empty options OK for v3
        },
        "id": node_id,
        "name": name,
        "type": "n8n-nodes-base.httpRequest",
        "typeVersion": 3,  # ✅ CRITICAL FIX: Use v3 like V74
        "position": position
    }


def find_node_by_name(workflow, node_name):
    """Find node in workflow by name."""
    for node in workflow["nodes"]:
        if node.get("name") == node_name:
            return node
    return None


def calculate_position(base_node, offset_x=100, offset_y=0):
    """Calculate new node position relative to base node."""
    base_pos = base_node.get("position", [0, 0])
    return [base_pos[0] + offset_x, base_pos[1] + offset_y]


def update_state_machine_code(workflow, state_machine_js_path):
    """Update State Machine Logic node with V78 JavaScript code."""
    print("\n📝 Updating State Machine Logic code...")

    state_machine_node = find_node_by_name(workflow, "State Machine Logic")
    if not state_machine_node:
        print("❌ ERROR: State Machine Logic node not found!")
        return False

    if not state_machine_js_path.exists():
        print(f"❌ ERROR: State Machine JS not found: {state_machine_js_path}")
        return False

    with open(state_machine_js_path, "r", encoding="utf-8") as f:
        state_machine_code = f.read()

    state_machine_node["parameters"]["jsCode"] = state_machine_code

    print(f"   ✅ State Machine code updated ({len(state_machine_code)} characters)")
    print(f"   ✅ Code embedded in workflow - no manual copy needed!")

    return True


def setup_v78_1_6_connections(workflow, switch_node, http_node1, http_node2, existing_update_conv_node):
    """Setup V78.1.6 connection architecture."""
    print("\n🔗 Setting up V78.1.6 connection architecture...")
    print(f"   ℹ️  Using EXISTING Update Conversation State at position {existing_update_conv_node['position']}")

    connections = workflow.get("connections", {})

    # Connection 1: Build Update Queries → Switch Node
    build_update_name = "Build Update Queries"

    if build_update_name not in connections:
        connections[build_update_name] = {}

    if "main" not in connections[build_update_name]:
        connections[build_update_name]["main"] = [[]]

    connections[build_update_name]["main"][0] = [{
        "node": switch_node["name"],
        "type": "main",
        "index": 0
    }]

    print(f"   ✅ Connected: {build_update_name} → {switch_node['name']}")

    # Connection 2: Switch Node → 3 outputs
    connections[switch_node["name"]] = {
        "main": [
            # Output 0: trigger_wf06_next_dates → HTTP Request 1
            [{
                "node": http_node1["name"],
                "type": "main",
                "index": 0
            }],

            # Output 1: trigger_wf06_available_slots → HTTP Request 2
            [{
                "node": http_node2["name"],
                "type": "main",
                "index": 0
            }],

            # Output 2 (fallback): default → ALL 5 PARALLEL NODES
            [
                {"node": existing_update_conv_node["name"], "type": "main", "index": 0},
                {"node": "Save Inbound Message", "type": "main", "index": 0},
                {"node": "Save Outbound Message", "type": "main", "index": 0},
                {"node": "Upsert Lead Data", "type": "main", "index": 0},
                {"node": "Send WhatsApp Response", "type": "main", "index": 0}
            ]
        ]
    }

    print(f"   ✅ Connected: {switch_node['name']} (Output 0) → {http_node1['name']}")
    print(f"   ✅ Connected: {switch_node['name']} (Output 1) → {http_node2['name']}")
    print(f"   ✅ Connected: {switch_node['name']} (Output 2 - fallback) → 5 PARALLEL NODES")

    # Connection 3: HTTP Requests → State Machine Logic
    state_machine_name = "State Machine Logic"

    connections[http_node1["name"]] = {
        "main": [[{"node": state_machine_name, "type": "main", "index": 0}]]
    }

    connections[http_node2["name"]] = {
        "main": [[{"node": state_machine_name, "type": "main", "index": 0}]]
    }

    print(f"   ✅ Connected: {http_node1['name']} → {state_machine_name} (loop back)")
    print(f"   ✅ Connected: {http_node2['name']} → {state_machine_name} (loop back)")

    workflow["connections"] = connections

    print("   ✅ V78.1.6 connection architecture complete!")


def generate_v78_1_6_final():
    """Generate V78.1.6 FINAL workflow with HTTP Request typeVersion fix."""

    print("=" * 80)
    print("GENERATE WF02 V78.1.6 FINAL - HTTP REQUEST TYPEVERSION FIX")
    print("=" * 80)

    print(f"\n✅ Loading base V74 (working) from: {BASE_V74}")
    if not BASE_V74.exists():
        print(f"❌ ERROR: Base V74 file not found: {BASE_V74}")
        return 1

    with open(BASE_V74, "r", encoding="utf-8") as f:
        workflow = json.load(f)

    print(f"   - Workflow name: {workflow.get('name')}")
    print(f"   - Total nodes: {len(workflow.get('nodes', []))}")

    workflow["name"] = "02_ai_agent_conversation_V78_1_6_FINAL"

    build_update_queries = find_node_by_name(workflow, "Build Update Queries")
    if not build_update_queries:
        print("❌ ERROR: Build Update Queries node not found!")
        return 1

    existing_update_conv = find_node_by_name(workflow, "Update Conversation State")
    if not existing_update_conv:
        print("❌ ERROR: Update Conversation State node not found in V74!")
        return 1

    print(f"\n📍 Found Build Update Queries at position: {build_update_queries.get('position')}")
    print(f"📍 Found EXISTING Update Conversation State at position: {existing_update_conv.get('position')}")

    switch_position = calculate_position(build_update_queries, offset_x=200, offset_y=0)
    http1_position = calculate_position(build_update_queries, offset_x=400, offset_y=-100)
    http2_position = calculate_position(build_update_queries, offset_x=400, offset_y=100)

    print("\n📝 Creating new nodes with typeVersion 3...")

    # Switch Node
    switch_id = generate_uuid()
    switch_node = create_switch_node_v78_1_6(
        position=switch_position,
        node_id=switch_id
    )

    print(f"   ✅ Created: {switch_node['name']}")
    print(f"      - ID: {switch_id}")
    print(f"      - TypeVersion: 3")

    # HTTP Request 1 - Next Dates (typeVersion 3)
    http1_id = generate_uuid()
    http_node1 = create_http_request_node_v3(
        name="HTTP Request - Get Next Dates",
        body_params=[
            {"name": "action", "value": "next_dates"},
            {"name": "count", "value": "3"},
            {"name": "start_date", "value": "={{ new Date().toISOString().split('T')[0] }}"},
            {"name": "duration_minutes", "value": "120"}
        ],
        position=http1_position,
        node_id=http1_id
    )

    print(f"   ✅ Created: {http_node1['name']}")
    print(f"      - TypeVersion: 3 (V74 compatible)")

    # HTTP Request 2 - Available Slots (typeVersion 3)
    http2_id = generate_uuid()
    http_node2 = create_http_request_node_v3(
        name="HTTP Request - Get Available Slots",
        body_params=[
            {"name": "action", "value": "available_slots"},
            {"name": "date", "value": "={{ $json.scheduled_date }}"},
            {"name": "duration_minutes", "value": "120"}
        ],
        position=http2_position,
        node_id=http2_id
    )

    print(f"   ✅ Created: {http_node2['name']}")
    print(f"      - TypeVersion: 3 (V74 compatible)")

    workflow["nodes"].extend([switch_node, http_node1, http_node2])

    if not update_state_machine_code(workflow, STATE_MACHINE_JS):
        print("⚠️  WARNING: State Machine code not updated")

    setup_v78_1_6_connections(workflow, switch_node, http_node1, http_node2, existing_update_conv)

    print(f"\n💾 Saving V78.1.6 FINAL to: {OUTPUT_V78_1_6}")
    OUTPUT_V78_1_6.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_V78_1_6, "w", encoding="utf-8") as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 80)
    print("✅ V78.1.6 FINAL WORKFLOW GENERATED SUCCESSFULLY!")
    print("=" * 80)

    print(f"\n📁 Output: {OUTPUT_V78_1_6}")

    print(f"\n📊 Statistics:")
    print(f"   - Total nodes: {len(workflow['nodes'])}")
    print(f"   - New nodes added: 3 (1 Switch v3 + 2 HTTP Request v3)")
    print(f"   - Nodes reused from V74: 1 (Update Conversation State)")
    print(f"   - State Machine code: EMBEDDED ✅")

    print(f"\n🎯 V78.1.6 FINAL Features:")
    print("   1. ✅ HTTP Request typeVersion 3 (V74 compatible)")
    print("   2. ✅ bodyParameters structure (not jsonBody)")
    print("   3. ✅ Empty options: {} (valid for v3)")
    print("   4. ✅ Switch Node mode: 'rules' (correct)")
    print("   5. ✅ All parallel connections preserved")
    print("   6. ✅ State Machine code embedded")

    print(f"\n🔧 Critical Fix (V78.1.6):")
    print("   - V78.1.5 PROBLEM: HTTP Request typeVersion 4.2 incompatible")
    print("   - Root Cause: Different options structure for v4.2")
    print("   - V78.1.6 FIX: Use typeVersion 3 (same as V74)")
    print("   - Result: Should import successfully in n8n 2.15.0")

    print(f"\n📝 Next Steps:")
    print("   1. Import 02_ai_agent_conversation_V78_1_6_FINAL.json to n8n")
    print("   2. ✅ Should import without errors (v3 compatible)")
    print("   3. Verify all nodes configured correctly")
    print("   4. Test WF06 integration")
    print("   5. Activate workflow")

    return 0


if __name__ == "__main__":
    sys.exit(generate_v78_1_6_final())
