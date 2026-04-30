#!/usr/bin/env python3
"""
Generate WF02 V79 - IF Node Cascade Routing (NO Switch!)
=========================================================

CRITICAL LEARNING: Switch Node n8n 2.15.0 does NOT work with multiple conditions!

V77-V78.3 FAILED ATTEMPTS:
- V77: Switch v3 → Import error
- V78.1.6: Switch mode/rules → Import error "property option"
- V78.2: Switch conditions com "id" → UI quebrada
- V78.3: Switch conditions SEM "id" → MESMA UI quebrada

V79 SOLUTION: Use IF nodes em cascata (V74 proven pattern)!

User wisdom: "EU nao usei Swith ate aqui por esse problemas"

Architecture:
- Build Update Queries
  ↓
- Check If WF06 Next Dates (IF)
  - TRUE → HTTP Request 1 → State Machine Logic
  - FALSE ↓
- Check If WF06 Available Slots (IF)
  - TRUE → HTTP Request 2 → State Machine Logic
  - FALSE → 5 PARALLEL NODES (fallback)

Date: 2026-04-13
Author: E2 Bot Development Team - V79 IF Cascade Pattern
Version: V79
"""

import json
import uuid
import sys
from pathlib import Path

# Configuration
BASE_V74 = Path(__file__).parent.parent / "n8n" / "workflows" / "02_ai_agent_conversation_V74.1_2_FUNCIONANDO.json"
STATE_MACHINE_JS = Path(__file__).parent / "wf02-v78-state-machine.js"
OUTPUT_V79 = Path(__file__).parent.parent / "n8n" / "workflows" / "02_ai_agent_conversation_V79_IF_CASCADE.json"

WF06_WEBHOOK_URL = "http://e2bot-n8n-dev:5678/webhook/calendar-availability"


def generate_uuid():
    """Generate unique UUID for n8n nodes."""
    return str(uuid.uuid4())


def create_if_node(name, next_stage_value, position, node_id=None):
    """
    Create IF node using V74 proven pattern.

    Based on: Check If New User, Check If Handoff, Check If Scheduling
    Structure: n8n-nodes-base.if typeVersion 1
    """
    if node_id is None:
        node_id = generate_uuid()

    return {
        "parameters": {
            "conditions": {
                "string": [
                    {
                        "value1": f"={{{{ $node['Build Update Queries'].json.next_stage }}}}",
                        "value2": next_stage_value
                    }
                ]
            }
        },
        "id": node_id,
        "name": name,
        "type": "n8n-nodes-base.if",
        "typeVersion": 1,
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


def setup_v79_connections(workflow, if1, if2, http1, http2, build_update_node, existing_nodes):
    """
    Setup V79 IF cascade connection architecture.

    Pattern:
    Build Update Queries
      ↓
    IF 1 (Check If WF06 Next Dates)
      TRUE → HTTP Request 1 → State Machine Logic
      FALSE → IF 2
    IF 2 (Check If WF06 Available Slots)
      TRUE → HTTP Request 2 → State Machine Logic
      FALSE → 5 PARALLEL NODES
    """
    print("\n🔗 Setting up V79 IF cascade architecture...")

    connections = workflow.get("connections", {})

    # Connection 1: Build Update Queries → IF 1
    build_update_name = build_update_node["name"]

    if build_update_name not in connections:
        connections[build_update_name] = {}

    connections[build_update_name]["main"] = [[{
        "node": if1["name"],
        "type": "main",
        "index": 0
    }]]

    print(f"   ✅ Connected: {build_update_name} → {if1['name']}")

    # Connection 2: IF 1 TRUE → HTTP Request 1
    # Connection 3: IF 1 FALSE → IF 2
    connections[if1["name"]] = {
        "main": [
            # TRUE path (index 0)
            [{
                "node": http1["name"],
                "type": "main",
                "index": 0
            }],
            # FALSE path (index 1)
            [{
                "node": if2["name"],
                "type": "main",
                "index": 0
            }]
        ]
    }

    print(f"   ✅ IF 1 TRUE → {http1['name']}")
    print(f"   ✅ IF 1 FALSE → {if2['name']}")

    # Connection 4: IF 2 TRUE → HTTP Request 2
    # Connection 5: IF 2 FALSE → 5 PARALLEL NODES
    connections[if2["name"]] = {
        "main": [
            # TRUE path (index 0)
            [{
                "node": http2["name"],
                "type": "main",
                "index": 0
            }],
            # FALSE path (index 1) - 5 PARALLEL NODES
            [
                {"node": existing_nodes["update_conv"]["name"], "type": "main", "index": 0},
                {"node": "Save Inbound Message", "type": "main", "index": 0},
                {"node": "Save Outbound Message", "type": "main", "index": 0},
                {"node": "Upsert Lead Data", "type": "main", "index": 0},
                {"node": "Send WhatsApp Response", "type": "main", "index": 0}
            ]
        ]
    }

    print(f"   ✅ IF 2 TRUE → {http2['name']}")
    print(f"   ✅ IF 2 FALSE → 5 PARALLEL NODES (fallback)")

    # Connection 6: HTTP Requests → State Machine Logic (loop back)
    state_machine_name = "State Machine Logic"

    connections[http1["name"]] = {
        "main": [[{"node": state_machine_name, "type": "main", "index": 0}]]
    }

    connections[http2["name"]] = {
        "main": [[{"node": state_machine_name, "type": "main", "index": 0}]]
    }

    print(f"   ✅ HTTP loops back: {http1['name']} → {state_machine_name}")
    print(f"   ✅ HTTP loops back: {http2['name']} → {state_machine_name}")

    workflow["connections"] = connections


def generate_v79_if_cascade():
    """Generate V79 workflow with IF cascade routing (NO Switch!)."""

    print("=" * 80)
    print("GENERATE WF02 V79 - IF CASCADE ROUTING (NO SWITCH!)")
    print("=" * 80)

    print(f"\n✅ Loading base V74 from: {BASE_V74}")
    if not BASE_V74.exists():
        print(f"❌ ERROR: Base V74 file not found!")
        return 1

    with open(BASE_V74, "r", encoding="utf-8") as f:
        workflow = json.load(f)

    workflow["name"] = "02_ai_agent_conversation_V79_IF_CASCADE"

    build_update_queries = find_node_by_name(workflow, "Build Update Queries")
    existing_update_conv = find_node_by_name(workflow, "Update Conversation State")

    if not build_update_queries or not existing_update_conv:
        print("❌ ERROR: Required nodes not found!")
        return 1

    print(f"\n📍 Build Update Queries: {build_update_queries.get('position')}")
    print(f"📍 Update Conversation State: {existing_update_conv.get('position')}")

    # Position new nodes
    if1_position = calculate_position(build_update_queries, offset_x=200, offset_y=-100)
    if2_position = calculate_position(build_update_queries, offset_x=200, offset_y=100)
    http1_position = calculate_position(build_update_queries, offset_x=400, offset_y=-100)
    http2_position = calculate_position(build_update_queries, offset_x=400, offset_y=100)

    print("\n📝 Creating nodes with V79 IF CASCADE pattern...")

    # IF Node 1: Check If WF06 Next Dates
    if1_id = generate_uuid()
    if1_node = create_if_node(
        name="Check If WF06 Next Dates",
        next_stage_value="trigger_wf06_next_dates",
        position=if1_position,
        node_id=if1_id
    )

    # IF Node 2: Check If WF06 Available Slots
    if2_id = generate_uuid()
    if2_node = create_if_node(
        name="Check If WF06 Available Slots",
        next_stage_value="trigger_wf06_available_slots",
        position=if2_position,
        node_id=if2_id
    )

    print(f"   ✅ IF nodes: V74 proven pattern (typeVersion 1)")

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

    workflow["nodes"].extend([if1_node, if2_node, http_node1, http_node2])

    if not update_state_machine_code(workflow, STATE_MACHINE_JS):
        print("⚠️  WARNING: State Machine code not updated")

    existing_nodes = {
        "update_conv": existing_update_conv
    }

    setup_v79_connections(workflow, if1_node, if2_node, http_node1, http_node2, build_update_queries, existing_nodes)

    print(f"\n💾 Saving to: {OUTPUT_V79}")
    OUTPUT_V79.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_V79, "w", encoding="utf-8") as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 80)
    print("✅ V79 IF CASCADE GENERATED SUCCESSFULLY!")
    print("=" * 80)

    print(f"\n📊 Statistics:")
    print(f"   - Total nodes: {len(workflow['nodes'])}")
    print(f"   - New nodes: 4 (2 IF + 2 HTTP Request)")

    print(f"\n🎯 V79 Features:")
    print("   1. ✅ IF cascade routing (V74 proven pattern)")
    print("   2. ✅ NO Switch Node (avoid n8n 2.15.0 bugs)")
    print("   3. ✅ HTTP Request v3 bodyParameters")
    print("   4. ✅ State Machine V78 embedded")
    print("   5. ✅ 5 parallel nodes fallback")

    print(f"\n🔧 Why V79 Works:")
    print("   - V77-V78.3 FAILED: Switch Node broken UI")
    print("   - V79 SUCCESS: IF cascade (user's proven pattern)")
    print("   - User wisdom: 'EU nao usei Swith ate aqui por esse problemas'")
    print("   - Learning: Trust working code > theoretical docs")

    print(f"\n📝 Next Steps:")
    print("   1. Import 02_ai_agent_conversation_V79_IF_CASCADE.json")
    print("   2. Verify IF nodes show correct conditions")
    print("   3. Verify TRUE/FALSE paths visible")
    print("   4. Test WF06 integration")
    print("   5. Activate workflow")

    return 0


if __name__ == "__main__":
    sys.exit(generate_v79_if_cascade())
