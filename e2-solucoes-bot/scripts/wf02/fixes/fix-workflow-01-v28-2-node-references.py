#!/usr/bin/env python3
"""
Workflow 01 V2.8.2: Complete Node Reference Fix
Corrige TODAS as referências a nós deletados (ghost connections + node parameters)

CRITICAL FIXES:
1. Remove ghost connections (V2.8.1 fix)
2. Update "Is Image?" node reference from Merge Results → Check Operation
3. Update "Prepare Data for AI Agent" reference from Merge Results → Check Operation
4. Garante execução completa até chamar Workflow 02

Date: 2026-03-10
Author: Claude Code V2.8.2 Fix
"""

import json
from pathlib import Path

# Input and output
INPUT_WORKFLOW = "n8n/workflows/01_main_whatsapp_handler_V2.7_SAVE_ORDER_FIX.json"
OUTPUT_WORKFLOW = "n8n/workflows/01_main_whatsapp_handler_V2.8.2_FINAL.json"


def fix_workflow_01_v28_2_complete():
    """
    Fix Workflow 01 com TODAS as referências atualizadas

    V2.8.2 = V2.8.1 + Node Parameter Updates
    """

    print("=" * 80)
    print("Workflow 01 V2.8.2: Complete Node Reference Fix")
    print("=" * 80)

    # Load V2.7 workflow
    print(f"\n📂 Loading Workflow 01 V2.7: {INPUT_WORKFLOW}")
    with open(INPUT_WORKFLOW, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    print(f"✅ Workflow loaded: {len(workflow['nodes'])} nodes")

    # Find nodes to modify
    extract_idx = None
    save_message_idx = None
    check_duplicate_idx = None
    merge_results_idx = None
    is_duplicate_idx = None
    is_image_idx = None
    prepare_data_idx = None

    for idx, node in enumerate(workflow['nodes']):
        if node['name'] == 'Extract Message Data':
            extract_idx = idx
        elif node['name'] == 'Save Message':
            save_message_idx = idx
        elif node['name'] == 'Check Duplicate':
            check_duplicate_idx = idx
        elif node['name'] == 'Merge Results':
            merge_results_idx = idx
        elif node['name'] == 'Is Duplicate?':
            is_duplicate_idx = idx
        elif node['name'] == 'Is Image?':
            is_image_idx = idx
        elif node['name'] == 'Prepare Data for AI Agent':
            prepare_data_idx = idx

    if any(idx is None for idx in [extract_idx, save_message_idx, is_duplicate_idx, is_image_idx, prepare_data_idx]):
        print("❌ ERROR: Could not find all required nodes!")
        return False

    print(f"\n🔍 Found nodes:")
    print(f"   Extract Message Data: index {extract_idx}")
    print(f"   Save Message: index {save_message_idx}")
    print(f"   Check Duplicate: index {check_duplicate_idx}")
    print(f"   Merge Results: index {merge_results_idx}")
    print(f"   Is Duplicate?: index {is_duplicate_idx}")
    print(f"   Is Image?: index {is_image_idx}")
    print(f"   Prepare Data for AI Agent: index {prepare_data_idx}")

    # Step 1: Update Save Message query
    print(f"\n🔧 Step 1: Fixing Save Message query...")
    save_message_node = workflow['nodes'][save_message_idx]

    new_save_query = """=INSERT INTO messages (
  conversation_id,
  direction,
  content,
  message_type,
  media_url,
  whatsapp_message_id
) VALUES (
  null,
  'inbound',
  '{{ $json.content.replace(/'/g, "''") }}',
  '{{ $json.message_type }}',
  {{ $json.media_url ? "'" + $json.media_url.replace(/'/g, "''") + "'" : "null" }},
  '{{ $json.message_id.replace(/'/g, "''") }}'
) ON CONFLICT (whatsapp_message_id)
DO UPDATE SET
  content = EXCLUDED.content,
  media_url = EXCLUDED.media_url
RETURNING id, created_at, CASE WHEN xmax = 0 THEN 'inserted' ELSE 'updated' END as operation"""

    save_message_node['parameters']['query'] = new_save_query
    print("   ✓ Save Message query updated with RETURNING clause")

    # Step 2: Update "Is Image?" node BEFORE removing Merge Results
    print(f"\n🔧 Step 2: Fixing 'Is Image?' node reference...")
    is_image_node = workflow['nodes'][is_image_idx]

    # Update condition to use $json.message_type instead of $node["Merge Results"].json.message_type
    if 'parameters' in is_image_node and 'conditions' in is_image_node['parameters']:
        conditions = is_image_node['parameters']['conditions']
        if 'conditions' in conditions and len(conditions['conditions']) > 0:
            # Find the image check condition
            for condition in conditions['conditions']:
                if 'leftValue' in condition:
                    old_value = condition['leftValue']
                    # Update reference to use $json instead of $node["Merge Results"].json
                    condition['leftValue'] = "={{ $json.message_type }}"
                    print(f"   ✓ Is Image? condition updated:")
                    print(f"     OLD: {old_value}")
                    print(f"     NEW: {{ $json.message_type }}")

    # Step 3: Update "Prepare Data for AI Agent" node BEFORE removing Merge Results
    print(f"\n🔧 Step 3: Fixing 'Prepare Data for AI Agent' node reference...")
    prepare_data_node = workflow['nodes'][prepare_data_idx]

    if 'parameters' in prepare_data_node and 'jsCode' in prepare_data_node['parameters']:
        old_code = prepare_data_node['parameters']['jsCode']

        # Update reference from $node["Merge Results"] to $node["Check Operation"]
        new_code = old_code.replace(
            '$node["Merge Results"].json',
            '$node["Check Operation"].json'
        )

        prepare_data_node['parameters']['jsCode'] = new_code
        print(f"   ✓ Prepare Data code updated:")
        print(f"     Changed: $node[\"Merge Results\"].json → $node[\"Check Operation\"].json")

    # Step 4: Remove old Check Duplicate and Merge Results nodes
    print(f"\n🔧 Step 4: Removing obsolete nodes...")
    if check_duplicate_idx is not None:
        workflow['nodes'].pop(check_duplicate_idx)
        print("   ✓ Check Duplicate node removed")
        # Adjust indices after removal
        if merge_results_idx and merge_results_idx > check_duplicate_idx:
            merge_results_idx -= 1
        if save_message_idx > check_duplicate_idx:
            save_message_idx -= 1
        if is_duplicate_idx > check_duplicate_idx:
            is_duplicate_idx -= 1
        if is_image_idx > check_duplicate_idx:
            is_image_idx -= 1
        if extract_idx > check_duplicate_idx:
            extract_idx -= 1
        if prepare_data_idx > check_duplicate_idx:
            prepare_data_idx -= 1

    if merge_results_idx is not None:
        workflow['nodes'].pop(merge_results_idx)
        print("   ✓ Merge Results node removed")
        # Adjust indices after removal
        if save_message_idx > merge_results_idx:
            save_message_idx -= 1
        if is_duplicate_idx > merge_results_idx:
            is_duplicate_idx -= 1
        if is_image_idx > merge_results_idx:
            is_image_idx -= 1
        if extract_idx > merge_results_idx:
            extract_idx -= 1
        if prepare_data_idx > merge_results_idx:
            prepare_data_idx -= 1

    # Step 5: Create new "Check Operation" node
    print(f"\n🔧 Step 5: Creating Check Operation node...")
    check_operation_node = {
        "parameters": {
            "jsCode": """// Check if Save Message resulted in INSERT or UPDATE
const saveResult = $input.first().json;

console.log('V2.8.2 Check Operation:');
console.log('  Save Message Result:', saveResult);
console.log('  Operation:', saveResult.operation);

// Extract message data from previous node
const extractData = $node["Extract Message Data"].json;

// Determine if this is a duplicate
const isDuplicate = (saveResult.operation === 'updated');

console.log('  Is Duplicate?:', isDuplicate);

// Return combined data with duplicate status
return {
  ...extractData,
  message_db_id: saveResult.id,
  is_duplicate: isDuplicate,
  operation: saveResult.operation
};"""
        },
        "id": "check-operation",
        "name": "Check Operation",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [-600, 200]
    }

    workflow['nodes'].append(check_operation_node)
    print("   ✓ Check Operation node created")

    # Step 6: CRITICAL - CLEAN ALL CONNECTIONS (remove fantasmas)
    print(f"\n🔧 Step 6: CLEANING ALL CONNECTIONS (removing ghost connections)...")

    # Create NEW clean connections object
    new_connections = {}

    # Copy ONLY valid connections (nodes that still exist)
    for node_name, connections in workflow['connections'].items():
        # Skip connections FROM deleted nodes
        if node_name in ['Check Duplicate', 'Merge Results']:
            print(f"   🗑️  Removing ghost connection FROM: {node_name}")
            continue

        # Clean connections TO deleted nodes
        cleaned_connections = {"main": []}
        for output_idx, output_connections in enumerate(connections.get('main', [])):
            cleaned_output = []
            for conn in output_connections:
                target_node = conn.get('node')
                if target_node not in ['Check Duplicate', 'Merge Results']:
                    cleaned_output.append(conn)
                else:
                    print(f"   🗑️  Removing ghost connection TO: {target_node}")

            if cleaned_output:  # Only add if has valid connections
                cleaned_connections['main'].append(cleaned_output)

        if cleaned_connections['main']:  # Only add if has valid outputs
            new_connections[node_name] = cleaned_connections

    # Replace connections with cleaned version
    workflow['connections'] = new_connections
    print("   ✓ Ghost connections removed")

    # Step 7: Set CORRECT connections for V2.8.2 flow
    print(f"\n🔧 Step 7: Setting CORRECT V2.8.2 connections...")

    # Extract → Save Message
    workflow['connections']['Extract Message Data'] = {
        "main": [[{
            "node": "Save Message",
            "type": "main",
            "index": 0
        }]]
    }
    print("   ✓ Extract Message Data → Save Message")

    # Save Message → Check Operation
    workflow['connections']['Save Message'] = {
        "main": [[{
            "node": "Check Operation",
            "type": "main",
            "index": 0
        }]]
    }
    print("   ✓ Save Message → Check Operation")

    # Check Operation → Is Duplicate?
    workflow['connections']['Check Operation'] = {
        "main": [[{
            "node": "Is Duplicate?",
            "type": "main",
            "index": 0
        }]]
    }
    print("   ✓ Check Operation → Is Duplicate?")

    # Is Duplicate? connections stay the same (to Webhook Response Duplicate and Is Image?)
    # These are already clean from Step 6

    # Step 8: Update node positions
    print(f"\n🔧 Step 8: Updating node positions...")
    workflow['nodes'][extract_idx]['position'] = [-1000, 200]
    workflow['nodes'][save_message_idx]['position'] = [-800, 200]
    # Check Operation node already has position set
    workflow['nodes'][is_duplicate_idx]['position'] = [-400, 200]
    workflow['nodes'][is_image_idx]['position'] = [-200, 100]
    print("   ✓ Node positions updated")

    # Step 9: Update workflow metadata
    workflow['name'] = '01 - WhatsApp Handler V2.8.2 (Complete Fix - FINAL)'
    workflow['versionId'] = 'v2-8-2-complete-fix-final'
    workflow['id'] = 'workflow-01-v28-2-complete-fix'
    print(f"\n✅ Workflow metadata updated")

    # Save corrected workflow
    print(f"\n💾 Saving V2.8.2 workflow...")
    with open(OUTPUT_WORKFLOW, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print(f"✅ Workflow saved: {OUTPUT_WORKFLOW}")

    # Summary
    print("\n" + "=" * 80)
    print("✅ WORKFLOW 01 V2.8.2 COMPLETE FIX - FINAL")
    print("=" * 80)
    print(f"Input:  {INPUT_WORKFLOW}")
    print(f"Output: {OUTPUT_WORKFLOW}")
    print(f"\n🔧 Critical Fixes Applied:")
    print(f"  1. ✓ Moved Save Message to FIRST position (after Extract)")
    print(f"  2. ✓ Updated 'Is Image?' node reference (Merge Results → Check Operation)")
    print(f"  3. ✓ Updated 'Prepare Data' node reference (Merge Results → Check Operation)")
    print(f"  4. ✓ Removed old Check Duplicate node (PostgreSQL query)")
    print(f"  5. ✓ Removed old Merge Results node (no longer needed)")
    print(f"  6. ✓ Created new Check Operation node (analyzes RETURNING)")
    print(f"  7. ✓ CLEANED ALL GHOST CONNECTIONS")
    print(f"  8. ✓ Set correct V2.8.2 connection flow")
    print(f"\n🐛 Bugs Fixed:")
    print(f"  ✓ Bug #1: Race Condition - Save Message agora é PRIMEIRO")
    print(f"  ✓ Bug #2: Ghost Connections - Conexões fantasma REMOVIDAS")
    print(f"  ✓ Bug #3: Node Parameter References - TODAS atualizadas")
    print(f"  ✓ Bug #4: ExpressionError - Referências a nós deletados CORRIGIDAS")
    print(f"\n📋 New Execution Flow (COMPLETE):")
    print(f"  1. Extract Message Data")
    print(f"  2. Save Message (ON CONFLICT, RETURNING operation)")
    print(f"  3. Check Operation (analyzes 'inserted' vs 'updated')")
    print(f"  4. Is Duplicate? (baseado em operation)")
    print(f"     ├─ true (updated) → Webhook Response Duplicate")
    print(f"     └─ false (inserted) → Is Image? (usando $json.message_type)")
    print(f"        ├─ true → Trigger Image Analysis")
    print(f"        └─ false → Prepare Data (usando $node['Check Operation'].json)")
    print(f"                    ↓")
    print(f"                 Trigger AI Agent (Workflow 02) ✅")
    print(f"\n🎯 Expected Behavior:")
    print(f"  ✓ V2.8.2 logs will show 'V2.8.2 Check Operation' messages")
    print(f"  ✓ operation='inserted' for new messages")
    print(f"  ✓ operation='updated' for duplicates (blocked)")
    print(f"  ✓ NO ExpressionError about 'Merge Results'")
    print(f"  ✓ Workflow completes execution successfully")
    print(f"  ✓ Workflow 02 WILL BE CALLED for non-duplicates ✅")
    print(f"\n📋 Next Steps:")
    print(f"  1. Import workflow in n8n: {OUTPUT_WORKFLOW}")
    print(f"  2. Deactivate V2.8.1")
    print(f"  3. Activate V2.8.2")
    print(f"  4. Test with WhatsApp message")
    print(f"  5. Verify logs show 'V2.8.2 Check Operation'")
    print(f"  6. Verify Workflow 02 is called")
    print(f"  7. Verify only ONE execution per unique message")
    print("=" * 80)

    return True


if __name__ == '__main__':
    success = fix_workflow_01_v28_2_complete()
    exit(0 if success else 1)
