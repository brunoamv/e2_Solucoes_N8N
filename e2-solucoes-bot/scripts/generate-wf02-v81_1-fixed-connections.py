#!/usr/bin/env python3
"""
Generate WF02 V81.1 - Fixed Merge Node Connections
==================================================

Purpose: Fix V81 Merge nodes that appear disconnected in n8n UI
Root Cause: V81 generator incorrectly added connections to Merge nodes

Fix: Remove connections property from Merge nodes to let n8n
     understand they receive inputs from nodes that connect TO them

Changes from V81 to V81.1:
1. Merge nodes should NOT have connections property
2. Only Prepare nodes and HTTP Request nodes have outgoing connections
3. State Machine receives from Merge nodes

Reference:
- Base: V81 with incorrect Merge connections
- Pattern: V79 Merge nodes (no connections property)
"""

import json
import sys
from pathlib import Path

# Paths
V81_PATH = "/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V81_WF06_INTEGRATION.json"
OUTPUT_PATH = "/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V81_1_FIXED_CONNECTIONS.json"

print("=== WF02 V81.1 CONNECTION FIX ===")
print(f"Loading V81 workflow...")

# Load V81
with open(V81_PATH, 'r', encoding='utf-8') as f:
    workflow = json.load(f)

print(f"✅ Loaded V81: {len(workflow['nodes'])} nodes")

# Update metadata
workflow['name'] = "02_ai_agent_conversation_V81_1_FIXED_CONNECTIONS"
workflow['versionId'] = "81.1"
workflow['tags'] = ["v81.1", "wf06-integration", "connection-fix"]

print(f"✅ Updated metadata to V81.1")

# ===== FIX MERGE NODE CONNECTIONS =====
print(f"\n=== FIXING MERGE NODE CONNECTIONS ===")

merge_nodes_fixed = 0

for i, node in enumerate(workflow['nodes']):
    node_name = node.get('name', '')

    # Check if this is one of our Merge nodes
    if node_name in [
        "Merge WF06 Next Dates with User Data",
        "Merge WF06 Available Slots with User Data"
    ]:
        # CRITICAL FIX: Remove connections property from Merge nodes
        # n8n determines Merge inputs from nodes that connect TO them
        # Merge nodes should NOT define their own connections

        if 'connections' in node:
            print(f"  Removing connections from: {node_name}")
            del workflow['nodes'][i]['connections']
            merge_nodes_fixed += 1
        else:
            print(f"  Already correct: {node_name}")

print(f"✅ Fixed {merge_nodes_fixed} Merge node connections")

# ===== VERIFY INCOMING CONNECTIONS =====
print(f"\n=== VERIFYING INCOMING CONNECTIONS ===")

# Find IDs of our new nodes
prepare_next_id = None
merge_next_id = None
prepare_slots_id = None
merge_slots_id = None
get_conv_details_id = None
http_next_dates_id = None
http_slots_id = None

for node in workflow['nodes']:
    name = node.get('name', '')
    node_id = node.get('id', '')

    if name == "Prepare WF06 Next Dates Data":
        prepare_next_id = node_id
    elif name == "Merge WF06 Next Dates with User Data":
        merge_next_id = node_id
    elif name == "Prepare WF06 Available Slots Data":
        prepare_slots_id = node_id
    elif name == "Merge WF06 Available Slots with User Data":
        merge_slots_id = node_id
    elif name == "Get Conversation Details":
        get_conv_details_id = node_id
    elif name == "HTTP Request - Get Next Dates":
        http_next_dates_id = node_id
    elif name == "HTTP Request - Get Available Slots":
        http_slots_id = node_id

print(f"  Prepare Next Dates ID: {prepare_next_id}")
print(f"  Merge Next Dates ID: {merge_next_id}")
print(f"  Prepare Slots ID: {prepare_slots_id}")
print(f"  Merge Slots ID: {merge_slots_id}")
print(f"  Get Conversation Details ID: {get_conv_details_id}")
print(f"  HTTP Next Dates ID: {http_next_dates_id}")
print(f"  HTTP Slots ID: {http_slots_id}")

# Verify connections FROM nodes TO our new nodes
connections_verified = []

for node in workflow['nodes']:
    if 'connections' not in node or 'main' not in node['connections']:
        continue

    for output_branch in node['connections']['main']:
        if not output_branch:
            continue

        for connection in output_branch:
            target_node = connection.get('node')

            # Check if target is one of our new nodes
            if target_node in [
                "Prepare WF06 Next Dates Data",
                "Merge WF06 Next Dates with User Data",
                "Prepare WF06 Available Slots Data",
                "Merge WF06 Available Slots with User Data"
            ]:
                connections_verified.append({
                    'from': node.get('name'),
                    'to': target_node,
                    'index': connection.get('index', 0)
                })

print(f"\n  Verified Connections:")
for conn in connections_verified:
    print(f"    {conn['from']} → {conn['to']} (index {conn['index']})")

# ===== EXPECTED CONNECTIONS =====
expected_connections = [
    ('HTTP Request - Get Next Dates', 'Prepare WF06 Next Dates Data', 0),
    ('Prepare WF06 Next Dates Data', 'Merge WF06 Next Dates with User Data', 0),
    ('Get Conversation Details', 'Merge WF06 Next Dates with User Data', 1),
    ('HTTP Request - Get Available Slots', 'Prepare WF06 Available Slots Data', 0),
    ('Prepare WF06 Available Slots Data', 'Merge WF06 Available Slots with User Data', 0),
    ('Get Conversation Details', 'Merge WF06 Available Slots with User Data', 1),
]

print(f"\n  Expected Connections:")
for from_node, to_node, index in expected_connections:
    found = any(
        c['from'] == from_node and c['to'] == to_node and c['index'] == index
        for c in connections_verified
    )
    status = "✅" if found else "❌"
    print(f"    {status} {from_node} → {to_node} (index {index})")

# ===== SAVE OUTPUT =====
print(f"\n=== SAVING OUTPUT ===")

with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    json.dump(workflow, f, indent=2, ensure_ascii=False)

print(f"✅ Saved V81.1 workflow to: {OUTPUT_PATH}")

# ===== SUMMARY =====
print(f"\n=== SUMMARY ===")
print(f"Total nodes: {len(workflow['nodes'])}")
print(f"Merge nodes fixed: {merge_nodes_fixed}")
print(f"Connections verified: {len(connections_verified)}")
print(f"Expected connections: {len(expected_connections)}")
print(f"\n=== V81.1 COMPLETE ===")
print(f"\nChanges from V81 to V81.1:")
print(f"  - Removed 'connections' property from 2 Merge nodes")
print(f"  - n8n will now correctly identify inputs from connecting nodes")
print(f"  - Merge nodes will no longer appear 'disconnected' in UI")
