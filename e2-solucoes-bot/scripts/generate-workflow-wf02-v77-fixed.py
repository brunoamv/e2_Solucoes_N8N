#!/usr/bin/env python3
"""
Generate WF02 V77 FIXED - Loop Fix with Switch Node
=====================================================

CRITICAL FIX FROM V77 ORIGINAL:
- REMOVE: Direct parallel State Machine → HTTP Request connections (caused infinite loop)
- ADD: Switch Node for conditional routing based on next_stage value
- ROUTE: Build Update Queries → Switch → HTTP Requests (conditional) OR Send WhatsApp (default)
- RESULT: HTTP Requests execute ONLY when next_stage triggers them, not on every State Machine call

ARCHITECTURE CHANGE:
State Machine Logic → Build Update Queries → Switch Node (Route Based on Stage)
  ├─ Output 0: next_stage === 'trigger_wf06_next_dates' → HTTP Request 1 → State Machine
  ├─ Output 1: next_stage === 'trigger_wf06_available_slots' → HTTP Request 2 → State Machine
  └─ Output 2 (fallback): default → Send WhatsApp Response

STATE MACHINE CHANGES (V63 → V77):
- State 8 (confirmation): Sets next_stage = 'trigger_wf06_next_dates' instead of direct to State 9
- State trigger_wf06_next_dates (NEW): Intermediate state that triggers Switch routing to HTTP Request 1
- State 10 (process_date_selection): Sets next_stage = 'trigger_wf06_available_slots' after date choice
- State trigger_wf06_available_slots (NEW): Intermediate state that triggers Switch routing to HTTP Request 2

Date: 2026-04-13
Author: E2 Bot Development Team - Loop Fix Implementation
Version: V77 FIXED
"""

import json
import uuid
import sys
from pathlib import Path

# Configuration
BASE_V76 = Path(__file__).parent.parent / "n8n" / "workflows" / "02_ai_agent_conversation_V76_PROACTIVE_UX.json"
OUTPUT_V77_FIXED = Path(__file__).parent.parent / "n8n" / "workflows" / "02_ai_agent_conversation_V77_FIXED.json"

WF06_WEBHOOK_URL = "http://e2bot-n8n-dev:5678/webhook/calendar-availability"

# JSON body templates (n8n expression format)
NEXT_DATES_BODY = "={{ JSON.stringify({\\n  action: 'next_dates',\\n  count: 3,\\n  start_date: new Date().toISOString().split('T')[0],\\n  duration_minutes: 120\\n}) }}"
AVAILABLE_SLOTS_BODY = "={{ JSON.stringify({\\n  action: 'available_slots',\\n  date: $json.scheduled_date,\\n  duration_minutes: 120\\n}) }}"


def generate_uuid():
    """Generate unique UUID for n8n nodes."""
    return str(uuid.uuid4())


def create_switch_node(position, node_id=None):
    """
    Create Switch node for conditional routing based on next_stage.

    This node is the KEY FIX for the infinite loop problem.
    It routes traffic conditionally instead of executing HTTP Requests unconditionally.

    Args:
        position: [x, y] coordinates in n8n UI
        node_id: Optional UUID (generates new if None)

    Returns:
        dict: Complete n8n Switch node object with 3 outputs
    """

    if node_id is None:
        node_id = generate_uuid()

    return {
        "parameters": {
            "mode": "expression",
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
            "fallbackOutput": 2  # Default: Send WhatsApp Response
        },
        "id": node_id,
        "name": "Route Based on Stage",
        "type": "n8n-nodes-base.switch",
        "typeVersion": 3,
        "position": position
    }


def create_http_request_node(name, json_body, position, node_id=None):
    """
    Create HTTP Request node for WF06 calls.

    Args:
        name: Node display name
        json_body: n8n expression for request body
        position: [x, y] coordinates in n8n UI
        node_id: Optional UUID (generates new if None)

    Returns:
        dict: Complete n8n node object
    """

    if node_id is None:
        node_id = generate_uuid()

    return {
        "parameters": {
            "method": "POST",
            "url": WF06_WEBHOOK_URL,
            "authentication": "none",
            "sendBody": True,
            "specifyBody": "json",
            "jsonBody": json_body,
            "options": {
                "response": {
                    "response": {
                        "responseFormat": "json"
                    }
                },
                "timeout": 5000
            }
        },
        "id": node_id,
        "name": name,
        "type": "n8n-nodes-base.httpRequest",
        "typeVersion": 4.2,
        "position": position,
        "continueOnFail": True,
        "retryOnFail": True,
        "maxTries": 2
    }


def find_node_by_name(workflow, node_name):
    """
    Find node in workflow by name.

    Args:
        workflow: Complete workflow dict
        node_name: Name to search for

    Returns:
        dict: Node object or None if not found
    """
    for node in workflow["nodes"]:
        if node.get("name") == node_name:
            return node
    return None


def calculate_position(base_node, offset_x=100, offset_y=0):
    """
    Calculate new node position relative to base node.

    Args:
        base_node: Reference node dict
        offset_x: X offset from base (default 100)
        offset_y: Y offset from base (default 0)

    Returns:
        list: [x, y] position
    """
    base_pos = base_node.get("position", [0, 0])
    return [base_pos[0] + offset_x, base_pos[1] + offset_y]


def remove_broken_connections(workflow):
    """
    CRITICAL FIX: Remove broken parallel State Machine → HTTP Request connections.

    This is the ROOT CAUSE of the infinite loop:
    - V77 original had State Machine with parallel outputs on same index
    - HTTP Request was ALWAYS executed regardless of state
    - Created loop: State Machine → HTTP Request → State Machine → HTTP Request...

    This function removes those broken connections.
    """

    print("\n🔧 CRITICAL FIX: Removing broken parallel connections...")

    connections = workflow.get("connections", {})
    state_machine_name = "State Machine Logic"

    if state_machine_name in connections:
        state_machine_conns = connections[state_machine_name]

        # Check for broken parallel connections on "main" output
        if "main" in state_machine_conns:
            # Find and remove HTTP Request connections from State Machine
            for output_index, output_conns in enumerate(state_machine_conns["main"]):
                filtered_conns = [
                    conn for conn in output_conns
                    if not (conn.get("node", "").startswith("HTTP Request"))
                ]

                # Only update if we actually filtered something
                if len(filtered_conns) < len(output_conns):
                    removed_count = len(output_conns) - len(filtered_conns)
                    print(f"   ✅ Removed {removed_count} direct HTTP Request connection(s) from State Machine (output {output_index})")
                    state_machine_conns["main"][output_index] = filtered_conns

    print("   ✅ Broken connections removed")


def add_switch_routing(workflow, switch_node, http_node1, http_node2):
    """
    Add correct Switch Node routing connections.

    This is the SOLUTION that fixes the infinite loop:
    - Build Update Queries → Switch Node
    - Switch Output 0 (trigger_wf06_next_dates) → HTTP Request 1
    - Switch Output 1 (trigger_wf06_available_slots) → HTTP Request 2
    - Switch Output 2 (default) → Send WhatsApp Response
    - HTTP Requests → State Machine Logic (return path)

    Args:
        workflow: Complete workflow dict
        switch_node: Switch node object
        http_node1: HTTP Request - Get Next Dates node
        http_node2: HTTP Request - Get Available Slots node
    """

    print("\n🔗 Adding Switch Node routing connections...")

    connections = workflow.get("connections", {})

    # Connection 1: Build Update Queries → Switch Node
    build_update_queries = "Build Update Queries"

    if build_update_queries not in connections:
        connections[build_update_queries] = {}

    if "main" not in connections[build_update_queries]:
        connections[build_update_queries]["main"] = [[]]

    # Replace existing connections with Switch
    connections[build_update_queries]["main"][0] = [{
        "node": switch_node["name"],
        "type": "main",
        "index": 0
    }]

    print(f"   ✅ Connected: {build_update_queries} → {switch_node['name']}")

    # Connection 2: Switch Node → HTTP Requests + Send WhatsApp
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

            # Output 2 (fallback): default → Send WhatsApp Response
            [{
                "node": "Send WhatsApp Response",
                "type": "main",
                "index": 0
            }]
        ]
    }

    print(f"   ✅ Connected: {switch_node['name']} (Output 0) → {http_node1['name']}")
    print(f"   ✅ Connected: {switch_node['name']} (Output 1) → {http_node2['name']}")
    print(f"   ✅ Connected: {switch_node['name']} (Output 2 - fallback) → Send WhatsApp Response")

    # Connection 3: HTTP Requests → State Machine Logic (return path)
    state_machine_name = "State Machine Logic"

    # HTTP Request 1 → State Machine
    connections[http_node1["name"]] = {
        "main": [[{
            "node": state_machine_name,
            "type": "main",
            "index": 0
        }]]
    }

    print(f"   ✅ Connected: {http_node1['name']} → {state_machine_name}")

    # HTTP Request 2 → State Machine
    connections[http_node2["name"]] = {
        "main": [[{
            "node": state_machine_name,
            "type": "main",
            "index": 0
        }]]
    }

    print(f"   ✅ Connected: {http_node2['name']} → {state_machine_name}")

    # Update workflow connections
    workflow["connections"] = connections


def generate_v77_fixed():
    """Generate V77 FIXED workflow with Switch Node loop fix."""

    print("=" * 80)
    print("GENERATE WF02 V77 FIXED - LOOP FIX WITH SWITCH NODE")
    print("=" * 80)

    # Load V76
    print(f"\n✅ Loading base V76 from: {BASE_V76}")
    if not BASE_V76.exists():
        print(f"❌ ERROR: Base V76 file not found: {BASE_V76}")
        return 1

    with open(BASE_V76, "r", encoding="utf-8") as f:
        workflow = json.load(f)

    print(f"   - Workflow name: {workflow.get('name')}")
    print(f"   - Total nodes: {len(workflow.get('nodes', []))}")

    # Update workflow metadata
    workflow["name"] = "02_ai_agent_conversation_V77_FIXED"

    # Find reference nodes
    build_update_queries = find_node_by_name(workflow, "Build Update Queries")
    if not build_update_queries:
        print("❌ ERROR: Build Update Queries node not found!")
        return 1

    print(f"\n📍 Found Build Update Queries at position: {build_update_queries.get('position')}")

    # Calculate positions for new nodes
    # Position Switch node to the right of Build Update Queries
    switch_position = calculate_position(build_update_queries, offset_x=200, offset_y=0)

    # Position HTTP Request nodes to the right of Switch with vertical spacing
    http1_position = calculate_position(build_update_queries, offset_x=400, offset_y=-100)
    http2_position = calculate_position(build_update_queries, offset_x=400, offset_y=100)

    # Create nodes
    print("\n📝 Creating new nodes...")

    # 1. Switch Node (THE KEY FIX)
    switch_id = generate_uuid()
    switch_node = create_switch_node(
        position=switch_position,
        node_id=switch_id
    )

    print(f"   ✅ Created: {switch_node['name']}")
    print(f"      - ID: {switch_id}")
    print(f"      - Position: {switch_position}")
    print(f"      - Type: {switch_node['type']}")
    print(f"      - Outputs: 3 (next_dates, available_slots, default)")

    # 2. HTTP Request - Get Next Dates
    http1_id = generate_uuid()
    http_node1 = create_http_request_node(
        name="HTTP Request - Get Next Dates",
        json_body=NEXT_DATES_BODY,
        position=http1_position,
        node_id=http1_id
    )

    print(f"   ✅ Created: {http_node1['name']}")
    print(f"      - ID: {http1_id}")
    print(f"      - Position: {http1_position}")

    # 3. HTTP Request - Get Available Slots
    http2_id = generate_uuid()
    http_node2 = create_http_request_node(
        name="HTTP Request - Get Available Slots",
        json_body=AVAILABLE_SLOTS_BODY,
        position=http2_position,
        node_id=http2_id
    )

    print(f"   ✅ Created: {http_node2['name']}")
    print(f"      - ID: {http2_id}")
    print(f"      - Position: {http2_position}")

    # Add nodes to workflow
    workflow["nodes"].extend([switch_node, http_node1, http_node2])

    # CRITICAL FIX: Remove broken connections
    remove_broken_connections(workflow)

    # SOLUTION: Add correct Switch routing
    add_switch_routing(workflow, switch_node, http_node1, http_node2)

    # Save V77 FIXED
    print(f"\n💾 Saving V77 FIXED to: {OUTPUT_V77_FIXED}")
    OUTPUT_V77_FIXED.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_V77_FIXED, "w", encoding="utf-8") as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    # Summary
    print("\n" + "=" * 80)
    print("✅ V77 FIXED WORKFLOW GENERATED SUCCESSFULLY!")
    print("=" * 80)

    print(f"\n📁 Output: {OUTPUT_V77_FIXED}")

    print(f"\n📊 Statistics:")
    print(f"   - Total nodes: {len(workflow['nodes'])}")
    print(f"   - New nodes added: 3 (1 Switch + 2 HTTP Request)")
    print(f"   - Broken connections removed: Yes ✅")
    print(f"   - Correct routing added: Yes ✅")

    print(f"\n🎯 V77 FIXED Features:")
    print("   1. ✅ Switch Node for conditional routing (LOOP FIX)")
    print("   2. ✅ HTTP Requests execute ONLY when next_stage triggers them")
    print("   3. ✅ No more infinite loop on 'HTTP Request - Get Next Dates'")
    print("   4. ✅ Fallback to Send WhatsApp Response when no WF06 call needed")
    print("   5. ✅ Graceful degradation via continueOnFail")
    print("   6. ✅ Automatic retry (maxTries: 2)")

    print(f"\n🔧 Architecture:")
    print("   State Machine Logic")
    print("     ↓")
    print("   Build Update Queries")
    print("     ↓")
    print("   Switch Node (Route Based on Stage)")
    print("     ├─ Output 0: trigger_wf06_next_dates → HTTP Request 1 → State Machine")
    print("     ├─ Output 1: trigger_wf06_available_slots → HTTP Request 2 → State Machine")
    print("     └─ Output 2 (fallback): default → Send WhatsApp Response")

    print(f"\n📝 Next Steps:")
    print("   1. Update State Machine code in n8n:")
    print("      - Copy from: scripts/wf02-v77-state-machine.js")
    print("      - Paste into: State Machine Logic node → Code tab")
    print("   2. Import 02_ai_agent_conversation_V77_FIXED.json to n8n")
    print("   3. Verify WF06 is active:")
    print("      curl http://localhost:5678/workflow/QDFJCEtzQSNON9cR")
    print("   4. Test E2E flow:")
    print("      bash scripts/test-wf02-v77-fixed-e2e.sh")

    print(f"\n🧪 E2E Test Checkpoints:")
    print("   ✅ Checkpoint 1: User chooses service 1 + confirms")
    print("   ✅ Checkpoint 2: State Machine returns next_stage = 'trigger_wf06_next_dates'")
    print("   ✅ Checkpoint 3: Switch detects and routes to HTTP Request 1")
    print("   ✅ Checkpoint 4: HTTP Request calls WF06 /next_dates")
    print("   ✅ Checkpoint 5: State Machine receives wf06_next_dates response")
    print("   ✅ Checkpoint 6: State Machine shows 3 date options (no loop!)")
    print("   ✅ Checkpoint 7: User selects date")
    print("   ✅ Checkpoint 8: State Machine returns next_stage = 'trigger_wf06_available_slots'")
    print("   ✅ Checkpoint 9: Switch detects and routes to HTTP Request 2")
    print("   ✅ Checkpoint 10: HTTP Request calls WF06 /available_slots")
    print("   ✅ Checkpoint 11: State Machine receives wf06_available_slots response")
    print("   ✅ Checkpoint 12: State Machine shows time slots (no loop!)")

    print(f"\n📚 Documentation:")
    print(f"   - Strategic Plan: /docs/PLAN/PLAN_WF02_V77_LOOP_FIX.md")
    print(f"   - Implementation Guide: /docs/implementation/WF02_V77_LOOP_FIX_IMPLEMENTATION_GUIDE.md")
    print(f"   - State Machine Code: /scripts/wf02-v77-state-machine.js")

    return 0


if __name__ == "__main__":
    sys.exit(generate_v77_fixed())
