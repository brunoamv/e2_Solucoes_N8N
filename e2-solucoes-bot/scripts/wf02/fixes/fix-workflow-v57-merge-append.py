#!/usr/bin/env python3
"""
V57: Merge Append Solution - Solução Definitiva
Replaces V54 Merge nodes with Merge append + Code processor pattern

Problem: All native Merge modes have limitations
- V55: Code nodes don't support multiple input ports
- V56: combine mode requires "Fields to Match" configuration

Solution: Merge append (creates array) + Code processor (combines data)

Date: 2026-03-09
Author: Claude Code V57 Final Solution
Base: V54 (has all database fixes)
"""

import json
import uuid
from datetime import datetime
from pathlib import Path

# Base workflow - V54 with all fixes
BASE_WORKFLOW = "n8n/workflows/02_ai_agent_conversation_V54_CONVERSATION_ID_FIX.json"
OUTPUT_WORKFLOW = "n8n/workflows/02_ai_agent_conversation_V57_MERGE_APPEND.json"

# Code Processor JavaScript for NEW User
CODE_PROCESSOR_NEW_USER = """// V57 Code Processor - Process append-merged data (NEW USER PATH)
console.log('=== V57 CODE PROCESSOR NEW USER START ===');

// Get all items from Merge append (should be exactly 2)
const items = $input.all();
console.log(`V57: Received ${items.length} items from Merge append`);

// VALIDATION: Must have exactly 2 items
if (items.length !== 2) {
  console.error(`V57 ERROR: Expected 2 items from append, received ${items.length}`);
  throw new Error(`V57: Merge append should produce 2 items, got ${items.length}`);
}

// Extract data from both items (append preserves input order)
const queriesData = items[0].json;  // Input 0 from Merge (Queries)
const dbData = items[1].json;       // Input 1 from Merge (Database)

console.log('V57 Item 0 (Queries) keys:', Object.keys(queriesData).join(', '));
console.log('V57 Item 1 (Database) keys:', Object.keys(dbData).join(', '));

// CRITICAL: Extract conversation_id from database result (item[1])
const conversation_id = dbData.id ||           // PostgreSQL RETURNING id
                       dbData.conversation_id || // Explicit field
                       null;

console.log('V57: Extracted conversation_id:', conversation_id);
console.log('V57: Type:', typeof conversation_id);

// VALIDATION: conversation_id must not be null
if (!conversation_id) {
  console.error('V57 CRITICAL ERROR: conversation_id is NULL!');
  console.error('V57: Database data (item[1]):', JSON.stringify(dbData, null, 2));
  throw new Error('V57: No conversation_id found in database result');
}

// Manually combine data from both items
// Database fields have priority for duplicates
const combinedData = {
  ...queriesData,  // All fields from Queries (item[0])
  ...dbData,       // All fields from Database (item[1])

  // EXPLICIT conversation_id mapping (CRITICAL)
  conversation_id: conversation_id,
  id: conversation_id,

  // Preserve critical fields explicitly
  phone_number: dbData.phone_number || queriesData.phone_number || '',
  message: queriesData.message || queriesData.body || queriesData.text || '',

  // V57 metadata for debugging
  v57_processor_executed: true,
  v57_processor_timestamp: new Date().toISOString(),
  v57_items_processed: items.length,
  v57_conversation_id_source: 'dbData.id',
  v57_path: 'new_user'
};

console.log('V57: Combined data keys:', Object.keys(combinedData).join(', '));
console.log('V57: conversation_id in output:', combinedData.conversation_id);
console.log('V57: phone_number in output:', combinedData.phone_number);
console.log('✅ V57 CODE PROCESSOR NEW USER COMPLETE');

// Return as array (n8n expects arrays)
return [combinedData];
"""

# Code Processor JavaScript for EXISTING User
CODE_PROCESSOR_EXISTING_USER = """// V57 Code Processor - Process append-merged data (EXISTING USER PATH)
console.log('=== V57 CODE PROCESSOR EXISTING USER START ===');

const items = $input.all();
console.log(`V57: Received ${items.length} items from Merge append`);

if (items.length !== 2) {
  console.error(`V57 ERROR: Expected 2 items from append, received ${items.length}`);
  throw new Error(`V57: Merge append should produce 2 items, got ${items.length}`);
}

const queriesData = items[0].json;  // Input 0 from Merge (Queries)
const dbData = items[1].json;       // Input 1 from Merge (Database)

console.log('V57 Item 0 (Queries) keys:', Object.keys(queriesData).join(', '));
console.log('V57 Item 1 (Database) keys:', Object.keys(dbData).join(', '));

// CRITICAL: Extract conversation_id from existing conversation
const conversation_id = dbData.id || dbData.conversation_id || null;

console.log('V57: Extracted conversation_id:', conversation_id);
console.log('V57: Type:', typeof conversation_id);

if (!conversation_id) {
  console.error('V57 CRITICAL ERROR: No conversation_id in existing user data!');
  console.error('V57: Database data (item[1]):', JSON.stringify(dbData, null, 2));
  throw new Error('V57: No conversation_id found in existing conversation');
}

const combinedData = {
  ...queriesData,
  ...dbData,

  // EXPLICIT conversation_id mapping
  conversation_id: conversation_id,
  id: conversation_id,

  phone_number: dbData.phone_number || queriesData.phone_number || '',
  message: queriesData.message || queriesData.body || queriesData.text || '',

  v57_processor_executed: true,
  v57_processor_timestamp: new Date().toISOString(),
  v57_items_processed: items.length,
  v57_conversation_id_source: 'dbData.id',
  v57_path: 'existing_user'
};

console.log('V57: Combined data keys:', Object.keys(combinedData).join(', '));
console.log('V57: conversation_id in output:', combinedData.conversation_id);
console.log('V57: phone_number in output:', combinedData.phone_number);
console.log('✅ V57 CODE PROCESSOR EXISTING USER COMPLETE');

return [combinedData];
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


def create_merge_append_node_v57(name, position, node_id=None):
    """Create Merge node with append mode"""
    return {
        "parameters": {
            "mode": "append",
            "options": {}
        },
        "id": node_id or str(uuid.uuid4()),
        "name": name,
        "type": "n8n-nodes-base.merge",
        "typeVersion": 2.1,
        "position": position,
        "alwaysOutputData": True
    }


def create_code_processor_v57(name, code, position, node_id=None):
    """Create Code processor node"""
    return {
        "parameters": {
            "mode": "runOnceForAllItems",
            "jsCode": code
        },
        "id": node_id or str(uuid.uuid4()),
        "name": name,
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": position,
        "alwaysOutputData": True
    }


def fix_workflow_v57():
    """
    V57 Fix: Replace V54 Merge nodes with Merge append + Code processor pattern

    V54 has TWO Merge nodes to replace:
    1. "Merge New User Data" (mergeByPosition)
    2. "Merge Existing User Data" (mergeByPosition)

    Each will be replaced with:
    1. Merge Append V57 (mode: append)
    2. Code Processor V57 (combines array items)
    """

    print("=" * 60)
    print("V57: Merge Append Solution (V54 Base)")
    print("=" * 60)

    # Load base workflow
    print(f"\n📂 Loading base workflow: {BASE_WORKFLOW}")
    workflow = load_workflow(BASE_WORKFLOW)

    # Find BOTH Merge nodes in V54
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

    # Create FOUR new nodes to replace TWO V54 Merge nodes
    # Path 1: New User
    merge_append_new = create_merge_append_node_v57(
        name="Merge Append New User V57",
        position=merge_new_node.get('position', [176, 400]),
        node_id=str(uuid.uuid4())
    )

    processor_new = create_code_processor_v57(
        name="Process New User Data V57",
        code=CODE_PROCESSOR_NEW_USER,
        position=[merge_new_node.get('position', [176, 400])[0] + 150,
                 merge_new_node.get('position', [176, 400])[1]],
        node_id=str(uuid.uuid4())
    )

    # Path 2: Existing User
    merge_append_existing = create_merge_append_node_v57(
        name="Merge Append Existing User V57",
        position=merge_existing_node.get('position', [176, 1100]),
        node_id=str(uuid.uuid4())
    )

    processor_existing = create_code_processor_v57(
        name="Process Existing User Data V57",
        code=CODE_PROCESSOR_EXISTING_USER,
        position=[merge_existing_node.get('position', [176, 1100])[0] + 150,
                 merge_existing_node.get('position', [176, 1100])[1]],
        node_id=str(uuid.uuid4())
    )

    print(f"\n🔧 Creating V57 nodes:")
    print(f"   - Merge Append New User V57 (ID: {merge_append_new['id'][:8]}...)")
    print(f"   - Process New User Data V57 (ID: {processor_new['id'][:8]}...)")
    print(f"   - Merge Append Existing User V57 (ID: {merge_append_existing['id'][:8]}...)")
    print(f"   - Process Existing User Data V57 (ID: {processor_existing['id'][:8]}...)")

    # Update connections
    print(f"\n🔌 Updating connections...")

    new_connections = {}

    for source_name, outputs in workflow['connections'].items():
        new_connections[source_name] = {}

        for output_type, target_lists in outputs.items():
            new_targets = []

            for target_list in target_lists:
                new_target_list = []

                for target in target_list:
                    # Replace connections TO old Merge nodes with connections TO new Merge Append nodes
                    if target['node'] == merge_new_user_name:
                        new_target = target.copy()
                        new_target['node'] = 'Merge Append New User V57'
                        new_target_list.append(new_target)
                        print(f"   ✓ Rerouted: {source_name} → Merge Append New User V57")
                    elif target['node'] == merge_existing_user_name:
                        new_target = target.copy()
                        new_target['node'] = 'Merge Append Existing User V57'
                        new_target_list.append(new_target)
                        print(f"   ✓ Rerouted: {source_name} → Merge Append Existing User V57")
                    else:
                        new_target_list.append(target)

                if new_target_list:
                    new_targets.append(new_target_list)

            if new_targets:
                new_connections[source_name][output_type] = new_targets

    # Add connections FROM Merge Append → Code Processor
    new_connections['Merge Append New User V57'] = {
        "main": [[{"node": "Process New User Data V57", "type": "main", "index": 0}]]
    }
    print(f"   ✓ Added: Merge Append New User V57 → Process New User Data V57")

    new_connections['Merge Append Existing User V57'] = {
        "main": [[{"node": "Process Existing User Data V57", "type": "main", "index": 0}]]
    }
    print(f"   ✓ Added: Merge Append Existing User V57 → Process Existing User Data V57")

    # Add connections FROM Code Processor → State Machine Logic
    # Find what the old Merge nodes connected to
    state_machine_target = None
    if merge_new_user_name in workflow['connections']:
        old_targets = workflow['connections'][merge_new_user_name].get('main', [[]])[0]
        if old_targets:
            state_machine_target = old_targets[0]['node']

    if state_machine_target:
        new_connections['Process New User Data V57'] = {
            "main": [[{"node": state_machine_target, "type": "main", "index": 0}]]
        }
        print(f"   ✓ Added: Process New User Data V57 → {state_machine_target}")

        new_connections['Process Existing User Data V57'] = {
            "main": [[{"node": state_machine_target, "type": "main", "index": 0}]]
        }
        print(f"   ✓ Added: Process Existing User Data V57 → {state_machine_target}")

    # Remove old V54 Merge nodes from connections
    if merge_new_user_name in new_connections:
        del new_connections[merge_new_user_name]
        print(f"   ✓ Removed old Merge: {merge_new_user_name}")

    if merge_existing_user_name in new_connections:
        del new_connections[merge_existing_user_name]
        print(f"   ✓ Removed old Merge: {merge_existing_user_name}")

    # Replace nodes array - replace TWO V54 Merge nodes with FOUR V57 nodes
    new_nodes = []
    replaced_count = 0

    for idx, node in enumerate(workflow['nodes']):
        if idx == merge_new_idx:
            # Replace first V54 Merge with TWO V57 nodes (Merge + Processor)
            new_nodes.append(merge_append_new)
            new_nodes.append(processor_new)
            replaced_count += 1
            print(f"\n🔄 Replaced '{merge_new_user_name}' with:")
            print(f"   - Merge Append New User V57")
            print(f"   - Process New User Data V57")
        elif idx == merge_existing_idx:
            # Replace second V54 Merge with TWO V57 nodes (Merge + Processor)
            new_nodes.append(merge_append_existing)
            new_nodes.append(processor_existing)
            replaced_count += 1
            print(f"🔄 Replaced '{merge_existing_user_name}' with:")
            print(f"   - Merge Append Existing User V57")
            print(f"   - Process Existing User Data V57")
        else:
            new_nodes.append(node)

    workflow['nodes'] = new_nodes
    workflow['connections'] = new_connections

    # Update workflow metadata
    workflow['name'] = '02 - AI Agent Conversation V57 (Merge Append Solution from V54)'
    workflow['meta'] = {
        'instanceId': '2d06ab7e4b229c8b36c3844fc8460ea6b891c39a3f5920e60f273c62eb6ab041'
    }

    if 'settings' not in workflow:
        workflow['settings'] = {}

    workflow['settings']['executionOrder'] = 'v1'

    # Update version ID
    workflow['versionId'] = 'v57-merge-append-from-v54'

    # Add version tag
    workflow['tags'] = [
        {'id': 'v57', 'name': 'V57 Merge Append'},
        {'id': 'conversation_id_fix', 'name': 'Conversation ID Fix'},
        {'id': 'from_v54', 'name': 'Based on V54'}
    ]

    # Save new workflow
    print(f"\n💾 Saving V57 workflow...")
    save_workflow(workflow, OUTPUT_WORKFLOW)

    # Summary
    print("\n" + "=" * 60)
    print("✅ V57 FIX COMPLETE (Based on V54)")
    print("=" * 60)
    print(f"Input:  {BASE_WORKFLOW}")
    print(f"Output: {OUTPUT_WORKFLOW}")
    print(f"\nChanges:")
    print(f"  - Removed: 2 V54 Merge nodes (mergeByPosition)")
    print(f"    • {merge_new_user_name}")
    print(f"    • {merge_existing_user_name}")
    print(f"  - Added: 4 V57 nodes (2 Merge Append + 2 Code Processor)")
    print(f"    • Merge Append New User V57")
    print(f"    • Process New User Data V57")
    print(f"    • Merge Append Existing User V57")
    print(f"    • Process Existing User Data V57")
    print(f"  - Preserved: All V54 database fixes and improvements")
    print(f"  - Updated: All connections rerouted correctly")
    print(f"\n🎯 Critical Fix:")
    print(f"  ✓ Merge append mode creates array: [queries, database]")
    print(f"  ✓ Code processor receives array via $input.all()")
    print(f"  ✓ conversation_id extracted from items[1].id")
    print(f"  ✓ Validation ensures conversation_id is not NULL")
    print(f"  ✓ Data combined with explicit conversation_id mapping")
    print(f"  ✓ Comprehensive V57 diagnostic logging added")
    print(f"  ✓ V54 database fixes preserved (phone formatting, state mapping)")
    print(f"\n📋 Next Steps:")
    print(f"  1. Import workflow in n8n: {OUTPUT_WORKFLOW}")
    print(f"  2. Deactivate V55 workflow")
    print(f"  3. Activate V57 workflow")
    print(f"  4. Test with WhatsApp message")
    print(f"  5. Monitor logs for 'V57' diagnostic messages")
    print(f"  6. Verify conversation_id is not NULL in State Machine Logic")
    print("=" * 60)

    return True


if __name__ == '__main__':
    success = fix_workflow_v57()
    exit(0 if success else 1)
