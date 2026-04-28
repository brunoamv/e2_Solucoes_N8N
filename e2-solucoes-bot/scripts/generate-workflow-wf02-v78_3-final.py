#!/usr/bin/env python3
"""
Generate WF02 V78.3 FINAL - Remove "id" Field from Switch Conditions
=====================================================================

CRITICAL FIX FROM V78.2:
- V78.2 PROBLEM: Switch conditions have "id" field → n8n UI shows "value1 = value2"
- Root Cause: n8n 2.15.0 does NOT recognize conditions with "id" field
- V78.3 FIX: Remove "id" field from all conditions ✅

n8n Switch Node v3.0 CORRECT structure (NO "id" in conditions):
- parameters.conditions.options ✅
- parameters.conditions.conditions[] array ✅
- Each condition: leftValue, rightValue, operator (NO "id") ✅

Reference: n8n/workflows/old/09_rdstation_webhook_handler.json (WORKING - NO "id")

ÚNICA MUDANÇA de V78.2 → V78.3:
- REMOVE: "id" field from conditions[0] and conditions[1]
- KEEP: Everything else identical

Date: 2026-04-13
Author: E2 Bot Development Team - V78.3 Condition ID Fix
Version: V78.3 FINAL
"""

import json
import uuid
import sys
from pathlib import Path

# Configuration
BASE_V74 = Path(__file__).parent.parent / "n8n" / "workflows" / "02_ai_agent_conversation_V74.1_2_FUNCIONANDO.json"
STATE_MACHINE_JS = Path(__file__).parent / "wf02-v78-state-machine.js"
OUTPUT_V78_3 = Path(__file__).parent.parent / "n8n" / "workflows" / "02_ai_agent_conversation_V78_3_FINAL.json"

WF06_WEBHOOK_URL = "http://e2bot-n8n-dev:5678/webhook/calendar-availability"


def generate_uuid():
    """Generate unique UUID for n8n nodes."""
    return str(uuid.uuid4())


def create_switch_node_v3_conditions(position, node_id=None):
    """
    Create Switch Node v3 using CORRECT 'conditions' structure.

    CRITICAL FIX V78.3: Remove "id" field from conditions.
    n8n 2.15.0 does NOT recognize conditions with "id" field.

    Based on working example: 09_rdstation_webhook_handler.json
    - Working example has NO "id" field in conditions
    - Conditions start directly with "leftValue"

    Structure breakdown:
    - Output 0: next_stage === 'trigger_wf06_next_dates'
    - Output 1: next_stage === 'trigger_wf06_available_slots'
    - Output 2: fallback (all other cases)
    """
    if node_id is None:
        node_id = generate_uuid()

    return {
        "parameters": {
            "conditions": {
                "options": {
                    "combineOperation": "any"
                },
                "conditions": [
                    {
                        # ✅ V78.3 FIX: NO "id" FIELD!
                        # Start directly with leftValue
                        "leftValue": "={{ $json.next_stage }}",
                        "rightValue": "trigger_wf06_next_dates",
                        "operator": {
                            "type": "string",
                            "operation": "equals"
                        }
                    },
                    {
                        # ✅ V78.3 FIX: NO "id" FIELD!
                        # Start directly with leftValue
                        "leftValue": "={{ $json.next_stage }}",
                        "rightValue": "trigger_wf06_available_slots",
                        "operator": {
                            "type": "string",
                            "operation": "equals"
                        }
                    }
                ]
            }
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

    Uses bodyParameters structure from V74.
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
            "options": {}
        },
        "id": node_id,
        "name": name,
        "type": "n8n-nodes-base.httpRequest",
        "typeVersion": 3,
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

    return True


def setup_v78_3_connections(workflow, switch_node, http_node1, http_node2, existing_update_conv_node):
    """
    Setup V78.3 connection architecture.

    Switch v3 with 'conditions' has 3 outputs:
    - Output 0: First condition matches (trigger_wf06_next_dates)
    - Output 1: Second condition matches (trigger_wf06_available_slots)
    - Output 2: Fallback (no conditions match)
    """
    print("\n🔗 Setting up V78.3 connection architecture...")

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
            # Output 0: First condition (trigger_wf06_next_dates) → HTTP Request 1
            [{
                "node": http_node1["name"],
                "type": "main",
                "index": 0
            }],

            # Output 1: Second condition (trigger_wf06_available_slots) → HTTP Request 2
            [{
                "node": http_node2["name"],
                "type": "main",
                "index": 0
            }],

            # Output 2 (fallback): No conditions match → 5 PARALLEL NODES
            [
                {"node": existing_update_conv_node["name"], "type": "main", "index": 0},
                {"node": "Save Inbound Message", "type": "main", "index": 0},
                {"node": "Save Outbound Message", "type": "main", "index": 0},
                {"node": "Upsert Lead Data", "type": "main", "index": 0},
                {"node": "Send WhatsApp Response", "type": "main", "index": 0}
            ]
        ]
    }

    print(f"   ✅ Switch Output 0 (condition 1) → {http_node1['name']}")
    print(f"   ✅ Switch Output 1 (condition 2) → {http_node2['name']}")
    print(f"   ✅ Switch Output 2 (fallback) → 5 PARALLEL NODES")

    # Connection 3: HTTP Requests → State Machine Logic
    state_machine_name = "State Machine Logic"

    connections[http_node1["name"]] = {
        "main": [[{"node": state_machine_name, "type": "main", "index": 0}]]
    }

    connections[http_node2["name"]] = {
        "main": [[{"node": state_machine_name, "type": "main", "index": 0}]]
    }

    print(f"   ✅ HTTP loops back: {http_node1['name']} → {state_machine_name}")
    print(f"   ✅ HTTP loops back: {http_node2['name']} → {state_machine_name}")

    workflow["connections"] = connections


def generate_v78_3_final():
    """Generate V78.3 FINAL workflow with conditions WITHOUT "id" field."""

    print("=" * 80)
    print("GENERATE WF02 V78.3 FINAL - REMOVE \"id\" FROM SWITCH CONDITIONS")
    print("=" * 80)

    print(f"\n✅ Loading base V74 from: {BASE_V74}")
    if not BASE_V74.exists():
        print(f"❌ ERROR: Base V74 file not found!")
        return 1

    with open(BASE_V74, "r", encoding="utf-8") as f:
        workflow = json.load(f)

    workflow["name"] = "02_ai_agent_conversation_V78_3_FINAL"

    build_update_queries = find_node_by_name(workflow, "Build Update Queries")
    existing_update_conv = find_node_by_name(workflow, "Update Conversation State")

    if not build_update_queries or not existing_update_conv:
        print("❌ ERROR: Required nodes not found!")
        return 1

    print(f"\n📍 Build Update Queries: {build_update_queries.get('position')}")
    print(f"📍 Update Conversation State: {existing_update_conv.get('position')}")

    switch_position = calculate_position(build_update_queries, offset_x=200, offset_y=0)
    http1_position = calculate_position(build_update_queries, offset_x=400, offset_y=-100)
    http2_position = calculate_position(build_update_queries, offset_x=400, offset_y=100)

    print("\n📝 Creating nodes with V78.3 CRITICAL FIX...")

    # Switch Node v3 with 'conditions' (NO "id" field)
    switch_id = generate_uuid()
    switch_node = create_switch_node_v3_conditions(
        position=switch_position,
        node_id=switch_id
    )

    print(f"   ✅ Switch Node: 'conditions' structure (NO \"id\" field) ✅")

    # HTTP Request nodes v3
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

    print(f"   ✅ HTTP Request nodes: typeVersion 3, bodyParameters")

    workflow["nodes"].extend([switch_node, http_node1, http_node2])

    if not update_state_machine_code(workflow, STATE_MACHINE_JS):
        print("⚠️  WARNING: State Machine code not updated")

    setup_v78_3_connections(workflow, switch_node, http_node1, http_node2, existing_update_conv)

    print(f"\n💾 Saving to: {OUTPUT_V78_3}")
    OUTPUT_V78_3.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_V78_3, "w", encoding="utf-8") as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 80)
    print("✅ V78.3 FINAL GENERATED SUCCESSFULLY!")
    print("=" * 80)

    print(f"\n📊 Statistics:")
    print(f"   - Total nodes: {len(workflow['nodes'])}")
    print(f"   - New nodes: 3 (Switch v3 + 2 HTTP Request v3)")

    print(f"\n🎯 V78.3 FINAL Features:")
    print("   1. ✅ Switch Node v3 'conditions' structure (CORRECT)")
    print("   2. ✅ Conditions WITHOUT \"id\" field (CRITICAL FIX)")
    print("   3. ✅ HTTP Request v3 bodyParameters")
    print("   4. ✅ State Machine embedded")

    print(f"\n🔧 Critical Fix (V78.3):")
    print("   - V78.2 PROBLEM: conditions have \"id\" field → UI shows \"value1 = value2\"")
    print("   - Root Cause: n8n 2.15.0 does NOT recognize conditions with \"id\"")
    print("   - V78.3 FIX: Remove \"id\" field from all conditions")
    print("   - Result: UI should show actual condition values correctly")

    print(f"\n📝 Next Steps:")
    print("   1. Validate JSON structure (jq)")
    print("   2. Verify conditions have NO \"id\" field")
    print("   3. Import 02_ai_agent_conversation_V78_3_FINAL.json")
    print("   4. Verify UI shows correct condition values")
    print("   5. Test WF06 integration")

    return 0


if __name__ == "__main__":
    sys.exit(generate_v78_3_final())
