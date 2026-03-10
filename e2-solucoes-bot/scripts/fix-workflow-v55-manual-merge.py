#!/usr/bin/env python3
"""
V55: Manual Merge Node Fix
Replaces native n8n Merge node with Code nodes for explicit conversation_id extraction

Problem: n8n native Merge modes don't preserve conversation_id properly
Solution: Manual merge with $input.all() and explicit field extraction

Date: 2026-03-09
Author: Claude Code V55 Manual Merge Solution
"""

import json
import uuid
from datetime import datetime
from pathlib import Path

# Base workflow - CORRECTED to use V54 (has database fixes)
BASE_WORKFLOW = "n8n/workflows/02_ai_agent_conversation_V54_CONVERSATION_ID_FIX.json"
OUTPUT_WORKFLOW = "n8n/workflows/02_ai_agent_conversation_V55_MANUAL_MERGE.json"

# Manual Merge Code for NEW User (from Create New Conversation + Merge Queries Data)
MANUAL_MERGE_NEW_USER_CODE = """// V55 Manual Merge for New User - Explicit conversation_id extraction
console.log('=== V55 MANUAL MERGE NEW USER START ===');

// Get all inputs using n8n's $input.all()
const allInputs = $input.all();
const inputCount = allInputs.length;

console.log(`V55: Received ${inputCount} inputs`);

// Validate exactly 2 inputs
if (inputCount !== 2) {
  console.error(`V55 ERROR: Expected 2 inputs, received ${inputCount}`);
  throw new Error(`Manual merge requires 2 inputs, received ${inputCount}`);
}

// Extract data from both inputs
const input0 = allInputs[0].json;  // From "Merge Queries Data"
const input1 = allInputs[1].json;  // From "Create New Conversation" (database)

console.log('V55 Input 0 (Queries) keys:', Object.keys(input0).join(', '));
console.log('V55 Input 1 (Database) keys:', Object.keys(input1).join(', '));

// CRITICAL: Extract conversation_id from database result
// Try multiple field names to ensure we get it
const conversation_id = input1.id ||           // PostgreSQL RETURNING id
                       input1.conversation_id || // Explicit field
                       null;

console.log('V55: Extracted conversation_id:', conversation_id);
console.log('V55: conversation_id type:', typeof conversation_id);

// CRITICAL VALIDATION: conversation_id must not be null/undefined
if (!conversation_id) {
  console.error('V55 CRITICAL ERROR: conversation_id extraction failed!');
  console.error('V55: Input 1 (Database) full data:', JSON.stringify(input1, null, 2));
  throw new Error('V55: No conversation_id found in database result - cannot proceed');
}

// Manually merge all fields from both inputs
// Database fields (input1) have priority for duplicates
const mergedData = {
  ...input0,  // All fields from Merge Queries Data
  ...input1,  // All fields from database (overrides duplicates)

  // EXPLICIT conversation_id mapping (CRITICAL FIX)
  conversation_id: conversation_id,
  id: conversation_id,  // Ensure both exist

  // Preserve critical fields explicitly
  phone_number: input1.phone_number || input0.phone_number || '',
  message: input0.message || input0.body || input0.text || '',

  // V55 metadata for debugging
  v55_merge_executed: true,
  v55_merge_timestamp: new Date().toISOString(),
  v55_merge_path: 'new_user',
  v55_input_count: inputCount
};

console.log('V55: Merged data keys:', Object.keys(mergedData).join(', '));
console.log('V55: conversation_id in output:', mergedData.conversation_id);
console.log('V55: phone_number in output:', mergedData.phone_number);
console.log('✅ V55 MANUAL MERGE NEW USER COMPLETE');

// Return as array (n8n expects arrays)
return [mergedData];
"""

# Manual Merge Code for EXISTING User (from Get Conversation Details + Merge Queries Data1)
MANUAL_MERGE_EXISTING_USER_CODE = """// V55 Manual Merge for Existing User - Explicit conversation_id extraction
console.log('=== V55 MANUAL MERGE EXISTING USER START ===');

const allInputs = $input.all();
const inputCount = allInputs.length;

console.log(`V55: Received ${inputCount} inputs`);

if (inputCount !== 2) {
  console.error(`V55 ERROR: Expected 2 inputs, received ${inputCount}`);
  throw new Error(`Manual merge requires 2 inputs, received ${inputCount}`);
}

const input0 = allInputs[0].json;  // From "Merge Queries Data1"
const input1 = allInputs[1].json;  // From "Get Conversation Details" (database)

console.log('V55 Input 0 (Queries) keys:', Object.keys(input0).join(', '));
console.log('V55 Input 1 (Database) keys:', Object.keys(input1).join(', '));

// CRITICAL: Extract conversation_id from existing conversation
const conversation_id = input1.id || input1.conversation_id || null;

console.log('V55: Extracted conversation_id:', conversation_id);
console.log('V55: conversation_id type:', typeof conversation_id);

if (!conversation_id) {
  console.error('V55 CRITICAL ERROR: No conversation_id in existing user data!');
  console.error('V55: Input 1 (Database) full data:', JSON.stringify(input1, null, 2));
  throw new Error('V55: No conversation_id found in existing conversation');
}

const mergedData = {
  ...input0,
  ...input1,

  // EXPLICIT conversation_id mapping
  conversation_id: conversation_id,
  id: conversation_id,

  phone_number: input1.phone_number || input0.phone_number || '',
  message: input0.message || input0.body || input0.text || '',

  v55_merge_executed: true,
  v55_merge_timestamp: new Date().toISOString(),
  v55_merge_path: 'existing_user',
  v55_input_count: inputCount
};

console.log('V55: Merged data keys:', Object.keys(mergedData).join(', '));
console.log('V55: conversation_id in output:', mergedData.conversation_id);
console.log('V55: phone_number in output:', mergedData.phone_number);
console.log('✅ V55 MANUAL MERGE EXISTING USER COMPLETE');

return [mergedData];
"""


def load_workflow(filepath):
    """Load workflow JSON"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_workflow(workflow, filepath):
    """Save workflow JSON"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)
    print(f"✅ Workflow saved: {filepath}")


def create_manual_merge_node(name, code, position, node_id=None):
    """Create a Code node for manual merge"""
    return {
        "parameters": {
            "mode": "runOnceForAllItems",
            "jsCode": code
        },
        "id": node_id or str(uuid.uuid4()),
        "name": name,
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": position
    }


def fix_workflow_v55():
    """
    V55 Fix: Replace native Merge nodes with manual Code nodes

    V54 has TWO native Merge nodes to replace:
    1. "Merge New User Data" (mergeByPosition)
    2. "Merge Existing User Data" (mergeByPosition)

    Changes:
    1. Find both native Merge nodes in V54
    2. Replace each with a Code node using $input.all()
    3. Update connections
    4. Remove old native Merge nodes
    """

    print("=" * 60)
    print("V55: Manual Merge Node Fix (V54 Base)")
    print("=" * 60)

    # Load base workflow
    print(f"\n📂 Loading base workflow: {BASE_WORKFLOW}")
    workflow = load_workflow(BASE_WORKFLOW)

    # Find BOTH native Merge nodes in V54
    merge_new_user_name = "Merge New User Data"
    merge_existing_user_name = "Merge Existing User Data"

    merge_new_node = None
    merge_new_idx = None
    merge_existing_node = None
    merge_existing_idx = None

    for idx, node in enumerate(workflow['nodes']):
        if node['name'] == merge_new_user_name:
            merge_new_node = node
            merge_new_idx = idx
        elif node['name'] == merge_existing_user_name:
            merge_existing_node = node
            merge_existing_idx = idx

    if not merge_new_node or not merge_existing_node:
        print(f"❌ ERROR: Could not find V54 Merge nodes")
        print(f"   Found 'Merge New User Data': {bool(merge_new_node)}")
        print(f"   Found 'Merge Existing User Data': {bool(merge_existing_node)}")
        return False

    print(f"✅ Found V54 Merge nodes:")
    print(f"   1. {merge_new_user_name} (Position: {merge_new_node.get('position', 'N/A')})")
    print(f"   2. {merge_existing_user_name} (Position: {merge_existing_node.get('position', 'N/A')})")

    # Create TWO manual merge Code nodes to replace V54 native Merge nodes
    # Use same positions as the native Merge nodes
    manual_merge_new = create_manual_merge_node(
        name="Manual Merge New User V55",
        code=MANUAL_MERGE_NEW_USER_CODE,
        position=merge_new_node.get('position', [176, 400]),
        node_id=str(uuid.uuid4())
    )

    manual_merge_existing = create_manual_merge_node(
        name="Manual Merge Existing User V55",
        code=MANUAL_MERGE_EXISTING_USER_CODE,
        position=merge_existing_node.get('position', [176, 1100]),
        node_id=str(uuid.uuid4())
    )

    print(f"\n🔧 Creating manual merge Code nodes:")
    print(f"   - Manual Merge New User V55 (ID: {manual_merge_new['id']})")
    print(f"   - Manual Merge Existing User V55 (ID: {manual_merge_existing['id']})")

    # Update connections to replace V54 Merge nodes with V55 Code nodes
    print(f"\n🔌 Updating connections...")

    new_connections = {}

    for source_name, outputs in workflow['connections'].items():
        new_connections[source_name] = {}

        for output_type, target_lists in outputs.items():
            new_targets = []

            for target_list in target_lists:
                new_target_list = []

                for target in target_list:
                    # Replace connections to V54 Merge nodes with V55 Code nodes
                    if target['node'] == merge_new_user_name:
                        new_target = target.copy()
                        new_target['node'] = 'Manual Merge New User V55'
                        new_target_list.append(new_target)
                        print(f"   ✓ Rerouted: {source_name} → Manual Merge New User V55")
                    elif target['node'] == merge_existing_user_name:
                        new_target = target.copy()
                        new_target['node'] = 'Manual Merge Existing User V55'
                        new_target_list.append(new_target)
                        print(f"   ✓ Rerouted: {source_name} → Manual Merge Existing User V55")
                    else:
                        new_target_list.append(target)

                if new_target_list:
                    new_targets.append(new_target_list)

            if new_targets:
                new_connections[source_name][output_type] = new_targets

    # Add connections FROM V55 manual merge nodes TO State Machine Logic
    # Copy the existing connections from V54 Merge nodes
    target_node = "State Machine Logic"

    if merge_new_user_name in workflow['connections']:
        new_connections['Manual Merge New User V55'] = workflow['connections'][merge_new_user_name]
        print(f"   ✓ Copied connections: Manual Merge New User V55 → {target_node}")

    if merge_existing_user_name in workflow['connections']:
        new_connections['Manual Merge Existing User V55'] = workflow['connections'][merge_existing_user_name]
        print(f"   ✓ Copied connections: Manual Merge Existing User V55 → {target_node}")

    # Remove old V54 Merge nodes from connections
    if merge_new_user_name in new_connections:
        del new_connections[merge_new_user_name]
        print(f"   ✓ Removed V54 Merge: {merge_new_user_name}")

    if merge_existing_user_name in new_connections:
        del new_connections[merge_existing_user_name]
        print(f"   ✓ Removed V54 Merge: {merge_existing_user_name}")

    # Replace nodes array - replace BOTH V54 Merge nodes with V55 Code nodes
    new_nodes = []
    replaced_count = 0

    for idx, node in enumerate(workflow['nodes']):
        if idx == merge_new_idx:
            # Replace first V54 Merge with V55 Code node
            new_nodes.append(manual_merge_new)
            replaced_count += 1
            print(f"\n🔄 Replaced '{merge_new_user_name}' with 'Manual Merge New User V55'")
        elif idx == merge_existing_idx:
            # Replace second V54 Merge with V55 Code node
            new_nodes.append(manual_merge_existing)
            replaced_count += 1
            print(f"🔄 Replaced '{merge_existing_user_name}' with 'Manual Merge Existing User V55'")
        else:
            new_nodes.append(node)

    workflow['nodes'] = new_nodes
    workflow['connections'] = new_connections

    # Update workflow metadata
    workflow['name'] = '02 - AI Agent Conversation V55 (Manual Merge Fix from V54)'
    workflow['meta'] = {
        'instanceId': '2d06ab7e4b229c8b36c3844fc8460ea6b891c39a3f5920e60f273c62eb6ab041'
    }

    if 'settings' not in workflow:
        workflow['settings'] = {}

    workflow['settings']['executionOrder'] = 'v1'

    # Update version ID
    workflow['versionId'] = 'v55-manual-merge-from-v54'

    # Add version tag
    workflow['tags'] = [
        {'id': 'v55', 'name': 'V55 Manual Merge'},
        {'id': 'conversation_id_fix', 'name': 'Conversation ID Fix'},
        {'id': 'from_v54', 'name': 'Based on V54'}
    ]

    # Save new workflow
    print(f"\n💾 Saving V55 workflow...")
    save_workflow(workflow, OUTPUT_WORKFLOW)

    # Summary
    print("\n" + "=" * 60)
    print("✅ V55 FIX COMPLETE (Based on V54)")
    print("=" * 60)
    print(f"Input:  {BASE_WORKFLOW}")
    print(f"Output: {OUTPUT_WORKFLOW}")
    print(f"\nChanges:")
    print(f"  - Removed: 2 V54 native Merge nodes (mergeByPosition)")
    print(f"    • {merge_new_user_name}")
    print(f"    • {merge_existing_user_name}")
    print(f"  - Added: 2 V55 Code nodes for manual merge")
    print(f"    • Manual Merge New User V55")
    print(f"    • Manual Merge Existing User V55")
    print(f"  - Preserved: All V54 database fixes and improvements")
    print(f"  - Updated: All connections rerouted correctly")
    print(f"\n🎯 Critical Fix:")
    print(f"  ✓ conversation_id explicitly extracted from database 'id' field")
    print(f"  ✓ Validation ensures conversation_id is not NULL")
    print(f"  ✓ All fields from both inputs preserved via $input.all()")
    print(f"  ✓ Comprehensive V55 diagnostic logging added")
    print(f"  ✓ V54 database fixes preserved (phone formatting, state mapping)")
    print(f"\n📋 Next Steps:")
    print(f"  1. Import workflow in n8n: {OUTPUT_WORKFLOW}")
    print(f"  2. Deactivate V54 workflow")
    print(f"  3. Activate V55 workflow")
    print(f"  4. Test with WhatsApp message")
    print(f"  5. Monitor logs for 'V55' diagnostic messages")
    print(f"  6. Verify conversation_id is not NULL in State Machine Logic")
    print("=" * 60)

    return True


if __name__ == '__main__':
    success = fix_workflow_v55()
    exit(0 if success else 1)
