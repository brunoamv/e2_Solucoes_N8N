#!/usr/bin/env python3
"""
Generate WF02 V81 Complete Workflow JSON
========================================

Purpose: Create WF02 V81 with:
1. Base structure from WF02 V79
2. State Machine V80 code integrated (740 lines)
3. 4 new data preparation nodes:
   - Prepare WF06 Next Dates Data (Code node)
   - Merge WF06 Next Dates with User Data (Merge node)
   - Prepare WF06 Available Slots Data (Code node)
   - Merge WF06 Available Slots with User Data (Merge node)
4. Updated connections for correct data flow

Data Flow:
  HTTP Request - Get Next Dates
      ↓
  Prepare WF06 Next Dates Data  (NEW)
      ↓
  Merge WF06 Next Dates with User Data  (NEW)
      ↓ + ←
  Get Conversation Details
      ↓
  State Machine Logic

Reference:
- Base: n8n/workflows/02_ai_agent_conversation_V79_1_SCHEMA_FIX.json
- State Machine: scripts/wf02-v80-complete-state-machine.js
- Bugfix: docs/fix/BUGFIX_WF02_V80_WF06_INTEGRATION.md
"""

import json
import uuid
from datetime import datetime

# Paths
WF02_V79_PATH = "/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V79_1_SCHEMA_FIX.json"
STATE_MACHINE_V80_PATH = "/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/scripts/wf02-v80-complete-state-machine.js"
OUTPUT_PATH = "/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V81_WF06_INTEGRATION.json"

print("=== WF02 V81 GENERATOR ===")
print(f"Loading base workflow from V79...")

# Load V79 base
with open(WF02_V79_PATH, 'r', encoding='utf-8') as f:
    workflow = json.load(f)

print(f"✅ Loaded V79 base: {len(workflow['nodes'])} nodes")

# Load State Machine V80 code
with open(STATE_MACHINE_V80_PATH, 'r', encoding='utf-8') as f:
    state_machine_v80_code = f.read()

print(f"✅ Loaded State Machine V80: {len(state_machine_v80_code)} characters")

# Update workflow metadata
workflow['name'] = "02_ai_agent_conversation_V81_WF06_INTEGRATION"
workflow['id'] = "ja97SAbNzpFkG1ZJ"  # Keep same ID for existing workflow
workflow['tags'] = ["v81", "wf06-integration", "state-machine-v80", "complete"]
workflow['versionId'] = "81"

print(f"✅ Updated metadata to V81")

# ===== STEP 1: Create 4 new preparation nodes =====

# Generate unique IDs for new nodes
prepare_next_dates_id = str(uuid.uuid4())
merge_next_dates_id = str(uuid.uuid4())
prepare_slots_id = str(uuid.uuid4())
merge_slots_id = str(uuid.uuid4())

print(f"\n=== CREATING NEW NODES ===")
print(f"Prepare Next Dates ID: {prepare_next_dates_id}")
print(f"Merge Next Dates ID: {merge_next_dates_id}")
print(f"Prepare Slots ID: {prepare_slots_id}")
print(f"Merge Slots ID: {merge_slots_id}")

# Node 1: Prepare WF06 Next Dates Data
prepare_next_dates_node = {
    "parameters": {
        "jsCode": '''// Prepare WF06 Next Dates Response for State Machine V80
// Wraps HTTP Request response in wf06_next_dates property

const wf06Response = $input.first().json;

console.log('=== PREPARE WF06 NEXT DATES DATA ===');
console.log('WF06 response:', JSON.stringify(wf06Response));

// Wrap response in wf06_next_dates property
const preparedData = {
  wf06_next_dates: wf06Response
};

console.log('Prepared data:', JSON.stringify(preparedData));

return preparedData;'''
    },
    "id": prepare_next_dates_id,
    "name": "Prepare WF06 Next Dates Data",
    "type": "n8n-nodes-base.code",
    "typeVersion": 2,
    "position": [850, 100]  # Position between HTTP Request and Merge
}

# Node 2: Merge WF06 Next Dates with User Data
merge_next_dates_node = {
    "parameters": {
        "mode": "append",
        "mergeByFields": {"values": []},
        "options": {}
    },
    "id": merge_next_dates_id,
    "name": "Merge WF06 Next Dates with User Data",
    "type": "n8n-nodes-base.merge",
    "typeVersion": 2.1,
    "position": [1050, 200]  # Position after Prepare node
}

# Node 3: Prepare WF06 Available Slots Data
prepare_slots_node = {
    "parameters": {
        "jsCode": '''// Prepare WF06 Available Slots Response for State Machine V80
// Wraps HTTP Request response in wf06_available_slots property

const wf06Response = $input.first().json;

console.log('=== PREPARE WF06 AVAILABLE SLOTS DATA ===');
console.log('WF06 response:', JSON.stringify(wf06Response));

// Wrap response in wf06_available_slots property
const preparedData = {
  wf06_available_slots: wf06Response
};

console.log('Prepared data:', JSON.stringify(preparedData));

return preparedData;'''
    },
    "id": prepare_slots_id,
    "name": "Prepare WF06 Available Slots Data",
    "type": "n8n-nodes-base.code",
    "typeVersion": 2,
    "position": [850, 400]  # Position between HTTP Request and Merge
}

# Node 4: Merge WF06 Available Slots with User Data
merge_slots_node = {
    "parameters": {
        "mode": "append",
        "mergeByFields": {"values": []},
        "options": {}
    },
    "id": merge_slots_id,
    "name": "Merge WF06 Available Slots with User Data",
    "type": "n8n-nodes-base.merge",
    "typeVersion": 2.1,
    "position": [1050, 500]  # Position after Prepare node
}

# Add new nodes to workflow
workflow['nodes'].extend([
    prepare_next_dates_node,
    merge_next_dates_node,
    prepare_slots_node,
    merge_slots_node
])

print(f"✅ Created 4 new preparation nodes")

# ===== STEP 2: Update State Machine Logic node with V80 code =====

print(f"\n=== UPDATING STATE MACHINE ===")

# Find State Machine Logic node
state_machine_node = None
for node in workflow['nodes']:
    if node['name'] == "State Machine Logic":
        state_machine_node = node
        break

if not state_machine_node:
    print("❌ ERROR: State Machine Logic node not found!")
    exit(1)

# Replace State Machine code with V80
state_machine_node['parameters']['functionCode'] = state_machine_v80_code

print(f"✅ Updated State Machine Logic with V80 code ({len(state_machine_v80_code)} chars)")

# ===== STEP 3: Update node connections =====

print(f"\n=== UPDATING CONNECTIONS ===")

# Find HTTP Request nodes
http_next_dates_node = None
http_slots_node = None
get_conversation_details_node = None

for node in workflow['nodes']:
    if node['name'] == "HTTP Request - Get Next Dates":
        http_next_dates_node = node
    elif node['name'] == "HTTP Request - Get Available Slots":
        http_slots_node = node
    elif node['name'] == "Get Conversation Details":
        get_conversation_details_node = node

if not http_next_dates_node or not http_slots_node or not get_conversation_details_node:
    print("❌ ERROR: Required nodes not found!")
    print(f"  HTTP Next Dates: {http_next_dates_node is not None}")
    print(f"  HTTP Slots: {http_slots_node is not None}")
    print(f"  Get Conversation Details: {get_conversation_details_node is not None}")
    exit(1)

# Update HTTP Request - Get Next Dates connections
# BEFORE: HTTP Request → State Machine Logic
# AFTER: HTTP Request → Prepare WF06 Next Dates Data
http_next_dates_node_index = workflow['nodes'].index(http_next_dates_node)
workflow['nodes'][http_next_dates_node_index] = {
    **http_next_dates_node,
    "connections": {
        "main": [[{
            "node": "Prepare WF06 Next Dates Data",
            "type": "main",
            "index": 0
        }]]
    }
}

# Update Prepare WF06 Next Dates Data connections
# Prepare → Merge (Input 1)
prepare_next_dates_node_index = workflow['nodes'].index(prepare_next_dates_node)
workflow['nodes'][prepare_next_dates_node_index] = {
    **prepare_next_dates_node,
    "connections": {
        "main": [[{
            "node": "Merge WF06 Next Dates with User Data",
            "type": "main",
            "index": 0
        }]]
    }
}

# Update Merge WF06 Next Dates with User Data connections
# Merge has 2 inputs:
# - Input 1: Prepare WF06 Next Dates Data (already connected above)
# - Input 2: Get Conversation Details
# Output: State Machine Logic
merge_next_dates_node_index = workflow['nodes'].index(merge_next_dates_node)
workflow['nodes'][merge_next_dates_node_index] = {
    **merge_next_dates_node,
    "connections": {
        "main": [[{
            "node": "State Machine Logic",
            "type": "main",
            "index": 0
        }]]
    }
}

# Update Get Conversation Details connections
# Add connection to both Merge nodes
get_conv_details_index = workflow['nodes'].index(get_conversation_details_node)
workflow['nodes'][get_conv_details_index] = {
    **get_conversation_details_node,
    "connections": {
        "main": [[
            {
                "node": "Merge WF06 Next Dates with User Data",
                "type": "main",
                "index": 1  # Input 2 of Merge
            },
            {
                "node": "Merge WF06 Available Slots with User Data",
                "type": "main",
                "index": 1  # Input 2 of Merge
            }
        ]]
    }
}

# Update HTTP Request - Get Available Slots connections
# BEFORE: HTTP Request → State Machine Logic
# AFTER: HTTP Request → Prepare WF06 Available Slots Data
http_slots_node_index = workflow['nodes'].index(http_slots_node)
workflow['nodes'][http_slots_node_index] = {
    **http_slots_node,
    "connections": {
        "main": [[{
            "node": "Prepare WF06 Available Slots Data",
            "type": "main",
            "index": 0
        }]]
    }
}

# Update Prepare WF06 Available Slots Data connections
# Prepare → Merge (Input 1)
prepare_slots_node_index = workflow['nodes'].index(prepare_slots_node)
workflow['nodes'][prepare_slots_node_index] = {
    **prepare_slots_node,
    "connections": {
        "main": [[{
            "node": "Merge WF06 Available Slots with User Data",
            "type": "main",
            "index": 0
        }]]
    }
}

# Update Merge WF06 Available Slots with User Data connections
# Merge has 2 inputs:
# - Input 1: Prepare WF06 Available Slots Data (already connected above)
# - Input 2: Get Conversation Details (already connected above)
# Output: State Machine Logic
merge_slots_node_index = workflow['nodes'].index(merge_slots_node)
workflow['nodes'][merge_slots_node_index] = {
    **merge_slots_node,
    "connections": {
        "main": [[{
            "node": "State Machine Logic",
            "type": "main",
            "index": 0
        }]]
    }
}

print(f"✅ Updated all node connections")
print(f"   HTTP Next Dates → Prepare → Merge → State Machine")
print(f"   HTTP Slots → Prepare → Merge → State Machine")
print(f"   Get Conversation Details → Both Merge nodes")

# ===== STEP 4: Save output =====

print(f"\n=== SAVING OUTPUT ===")

with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    json.dump(workflow, f, indent=2, ensure_ascii=False)

print(f"✅ Saved V81 workflow to: {OUTPUT_PATH}")
print(f"\n=== SUMMARY ===")
print(f"Total nodes: {len(workflow['nodes'])}")
print(f"  V79 base: {len(workflow['nodes']) - 4} nodes")
print(f"  New nodes: 4 (2 Prepare + 2 Merge)")
print(f"State Machine: V80 ({len(state_machine_v80_code)} chars)")
print(f"WF06 Integration: Complete ✅")
print(f"\n=== V81 COMPLETE ===")
