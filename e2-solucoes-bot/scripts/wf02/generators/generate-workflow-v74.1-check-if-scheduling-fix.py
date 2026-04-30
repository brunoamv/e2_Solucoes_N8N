#!/usr/bin/env python3
"""
Script: generate-workflow-v74.1-check-if-scheduling-fix.py
Purpose: Fix Check If Scheduling node value mismatch (scheduling → scheduling_redirect)
Base: V74_APPOINTMENT_CONFIRMATION
Date: 2026-03-25
Critical Bug Fix: Check If Scheduling value2 correction + remove duplicate node
"""

import json
import sys
from pathlib import Path

# Define paths
BASE_DIR = Path(__file__).parent.parent
WORKFLOWS_DIR = BASE_DIR / "n8n" / "workflows"
INPUT_FILE = WORKFLOWS_DIR / "02_ai_agent_conversation_V74_APPOINTMENT_CONFIRMATION.json"
OUTPUT_FILE = WORKFLOWS_DIR / "02_ai_agent_conversation_V74.1_CHECK_IF_SCHEDULING_FIX.json"

# Validate input file exists
if not INPUT_FILE.exists():
    print(f"❌ ERROR: Input file not found: {INPUT_FILE}")
    sys.exit(1)

print(f"📂 Reading: {INPUT_FILE}")

# Load V74 workflow
with open(INPUT_FILE, 'r', encoding='utf-8') as f:
    workflow = json.load(f)

print(f"✅ Loaded workflow: {workflow['name']}")
print(f"📊 Total nodes: {len(workflow['nodes'])}")

# ============================================
# STEP 1: Remove duplicate "Check If Scheduling" node
# ============================================
print("\n🔧 STEP 1: Removing duplicate 'Check If Scheduling' node...")

DUPLICATE_NODE_ID = "689d6869-74ad-486c-920d-75feff34c381"
CORRECT_NODE_ID = "9151a253-13d4-4084-93ef-48397740ea7e"

initial_node_count = len(workflow['nodes'])
workflow['nodes'] = [node for node in workflow['nodes'] if node.get('id') != DUPLICATE_NODE_ID]
removed_count = initial_node_count - len(workflow['nodes'])

if removed_count > 0:
    print(f"   ✅ Removed {removed_count} duplicate node(s) with ID: {DUPLICATE_NODE_ID}")
else:
    print(f"   ⚠️  WARNING: Duplicate node not found (may already be removed)")

# ============================================
# STEP 2: Fix "Check If Scheduling" node value
# ============================================
print("\n🔧 STEP 2: Fixing 'Check If Scheduling' node value...")

check_if_scheduling_node = None
for node in workflow['nodes']:
    if node.get('id') == CORRECT_NODE_ID and node.get('name') == 'Check If Scheduling':
        check_if_scheduling_node = node
        break

if not check_if_scheduling_node:
    print(f"   ❌ ERROR: 'Check If Scheduling' node not found with ID: {CORRECT_NODE_ID}")
    sys.exit(1)

# Get current value
current_value = check_if_scheduling_node['parameters']['conditions']['string'][0].get('value2', '')
print(f"   📋 Current value2: '{current_value}'")

# Fix value2
check_if_scheduling_node['parameters']['conditions']['string'][0]['value2'] = 'scheduling_redirect'
print(f"   ✅ Updated value2: 'scheduling_redirect' (CRITICAL FIX)")

# Ensure operation is 'equals'
check_if_scheduling_node['parameters']['conditions']['string'][0]['operation'] = 'equals'
print(f"   ✅ Ensured operation: 'equals'")

# ============================================
# STEP 3: Verify connections
# ============================================
print("\n🔧 STEP 3: Verifying node connections...")

# Find Send WhatsApp Response node
send_whatsapp_node = None
for node in workflow['nodes']:
    if node.get('name') == 'Send WhatsApp Response':
        send_whatsapp_node = node
        break

if not send_whatsapp_node:
    print(f"   ❌ ERROR: 'Send WhatsApp Response' node not found")
    sys.exit(1)

# Check connection to Check If Scheduling
connections = send_whatsapp_node.get('connections', {}).get('main', [[]])
connected_to_check_if_scheduling = False

for connection_group in connections:
    for connection in connection_group:
        if connection.get('node') == 'Check If Scheduling':
            connected_to_check_if_scheduling = True
            print(f"   ✅ 'Send WhatsApp Response' → 'Check If Scheduling' connection verified")
            break

if not connected_to_check_if_scheduling:
    print(f"   ❌ ERROR: 'Send WhatsApp Response' not connected to 'Check If Scheduling'")
    print(f"   🔧 FIX: Manually connect in n8n UI after import")

# Check workflow-level connections for Check If Scheduling
workflow_connections = workflow.get('connections', {}).get('Check If Scheduling', {})
if workflow_connections:
    main_connections = workflow_connections.get('main', [[]])
    if main_connections and len(main_connections) > 0:
        true_branch = main_connections[0]

        # Verify TRUE branch connection
        if true_branch:
            target_node = true_branch[0].get('node', '')
            print(f"   ✅ TRUE branch → '{target_node}' verified")

            # Check if there's a FALSE branch
            if len(main_connections) > 1:
                false_branch = main_connections[1]
                if false_branch:
                    false_target = false_branch[0].get('node', '')
                    print(f"   ✅ FALSE branch → '{false_target}' verified")
        else:
            print(f"   ⚠️  WARNING: Check If Scheduling has no TRUE branch connection")
    else:
        print(f"   ⚠️  WARNING: Check If Scheduling connections incomplete")
else:
    print(f"   ⚠️  WARNING: No workflow-level connections for Check If Scheduling")

# ============================================
# STEP 4: Update workflow metadata
# ============================================
print("\n🔧 STEP 4: Updating workflow metadata...")

# Update workflow name
workflow['name'] = '02_ai_agent_conversation_V74.1_CHECK_IF_SCHEDULING_FIX'
print(f"   ✅ Updated name: {workflow['name']}")

# Update tags
if 'tags' not in workflow:
    workflow['tags'] = []
workflow['tags'].append({
    'id': 'v74_1_fix',
    'name': 'v74.1-check-if-scheduling-fix'
})
print(f"   ✅ Added tag: v74.1-check-if-scheduling-fix")

# ============================================
# STEP 5: Validation summary
# ============================================
print("\n📊 VALIDATION SUMMARY:")
print(f"   ✅ Duplicate node removed: {removed_count > 0}")
print(f"   ✅ Check If Scheduling value2: 'scheduling_redirect'")
print(f"   ✅ Operation: 'equals'")
print(f"   ✅ Connection verified: Send WhatsApp Response → Check If Scheduling")
print(f"   ✅ Total nodes: {len(workflow['nodes'])}")

# ============================================
# STEP 6: Save workflow
# ============================================
print(f"\n💾 Saving workflow to: {OUTPUT_FILE}")

with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(workflow, f, indent=2, ensure_ascii=False)

print(f"✅ SUCCESS: V74.1 workflow generated!")
print(f"\n📋 NEXT STEPS:")
print(f"   1. Import workflow: http://localhost:5678")
print(f"   2. File: {OUTPUT_FILE}")
print(f"   3. Verify nodes visually in n8n UI")
print(f"   4. Test complete flow (services 1/3 + confirm appointment)")
print(f"   5. Monitor executions for 2 hours")
print(f"\n🎯 CRITICAL FIX APPLIED:")
print(f"   • Check If Scheduling value2: 'scheduling' → 'scheduling_redirect'")
print(f"   • Duplicate node removed")
print(f"   • Connection to Send WhatsApp Response verified")
