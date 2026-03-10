#!/usr/bin/env python3
"""
Workflow 01 V2.7: Save Message Order Fix
Fix conversation_id NULL issue by reordering workflow execution

Problem: Save Message executes BEFORE Trigger AI Agent
- conversation_id is hardcoded as null
- INSERT fails because conversation_id is required
- Execution 10298 gets stuck

Solution: Reorder workflow to save message AFTER AI Agent execution
- Trigger AI Agent first (gets/creates conversation)
- Extract conversation_id from response
- Save Message with valid conversation_id

Date: 2026-03-10
Author: Claude Code V2.7 Fix
"""

import json
from pathlib import Path

# Input and output
INPUT_WORKFLOW = "n8n/workflows/01_main_whatsapp_handler_V2.6.json"
OUTPUT_WORKFLOW = "n8n/workflows/01_main_whatsapp_handler_V2.7_SAVE_ORDER_FIX.json"


def fix_workflow_01_v27():
    """
    Fix Workflow 01 Save Message execution order

    Current order (WRONG):
    Is Duplicate? → Save Message (null) → Is Image? → Prepare → Trigger AI

    Corrected order:
    Is Duplicate? → Is Image? → Prepare → Trigger AI → Extract ID → Save Message (valid)
    """

    print("=" * 80)
    print("Workflow 01 V2.7: Save Message Order Fix")
    print("=" * 80)

    # Load V2.6 workflow
    print(f"\n📂 Loading Workflow 01 V2.6: {INPUT_WORKFLOW}")
    with open(INPUT_WORKFLOW, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    print(f"✅ Workflow loaded: {len(workflow['nodes'])} nodes")

    # Find nodes to modify
    save_message_idx = None
    is_image_idx = None
    prepare_data_idx = None
    trigger_ai_idx = None
    webhook_success_idx = None

    for idx, node in enumerate(workflow['nodes']):
        if node['name'] == 'Save Message':
            save_message_idx = idx
        elif node['name'] == 'Is Image?':
            is_image_idx = idx
        elif node['name'] == 'Prepare Data for AI Agent':
            prepare_data_idx = idx
        elif node['name'] == 'Trigger AI Agent':
            trigger_ai_idx = idx
        elif node['name'] == 'Webhook Response Success':
            webhook_success_idx = idx

    if any(idx is None for idx in [save_message_idx, is_image_idx, prepare_data_idx, trigger_ai_idx, webhook_success_idx]):
        print("❌ ERROR: Could not find all required nodes!")
        return False

    print(f"\n🔍 Found nodes:")
    print(f"   Save Message: index {save_message_idx}")
    print(f"   Is Image?: index {is_image_idx}")
    print(f"   Prepare Data: index {prepare_data_idx}")
    print(f"   Trigger AI Agent: index {trigger_ai_idx}")
    print(f"   Webhook Response: index {webhook_success_idx}")

    # Step 1: Update Save Message query to use conversation_id from AI Agent
    print(f"\n🔧 Step 1: Updating Save Message query...")
    save_message_node = workflow['nodes'][save_message_idx]

    # New query that uses conversation_id from Trigger AI Agent response
    new_query = """=INSERT INTO messages (
  conversation_id,
  direction,
  content,
  message_type,
  media_url,
  whatsapp_message_id
) VALUES (
  {{ $node["Extract Conversation ID"].json.conversation_id }},
  'inbound',
  '{{ $node["Merge Results"].json.content.replace(/'/g, "''") }}',
  '{{ $node["Merge Results"].json.message_type }}',
  {{ $node["Merge Results"].json.media_url ? "'" + $node["Merge Results"].json.media_url.replace(/'/g, "''") + "'" : "null" }},
  '{{ $node["Merge Results"].json.message_id.replace(/'/g, "''") }}'
) ON CONFLICT (whatsapp_message_id)
DO UPDATE SET
  content = EXCLUDED.content,
  media_url = EXCLUDED.media_url,
  conversation_id = EXCLUDED.conversation_id
RETURNING id, created_at, CASE WHEN xmax = 0 THEN 'inserted' ELSE 'updated' END as operation"""

    save_message_node['parameters']['query'] = new_query
    print("   ✓ Query updated to use conversation_id from AI Agent")

    # Step 2: Create new "Extract Conversation ID" node
    print(f"\n🔧 Step 2: Creating Extract Conversation ID node...")
    extract_id_node = {
        "parameters": {
            "jsCode": """// Extract conversation_id from Trigger AI Agent response
const aiResponse = $input.first().json;

console.log('V2.7 Extract Conversation ID:');
console.log('  AI Agent Response Keys:', Object.keys(aiResponse).join(', '));

// Try multiple possible fields
let conversation_id = null;

if (aiResponse.conversation_id) {
    conversation_id = aiResponse.conversation_id;
    console.log('  ✓ Found conversation_id:', conversation_id);
} else if (aiResponse.id) {
    conversation_id = aiResponse.id;
    console.log('  ✓ Found id (using as conversation_id):', conversation_id);
} else {
    console.error('  ❌ ERROR: No conversation_id found in AI response!');
    console.error('  Available keys:', Object.keys(aiResponse));
    throw new Error('V2.7: conversation_id not found in AI Agent response');
}

// Return conversation_id plus all original data for Save Message
return {
    ...aiResponse,
    conversation_id: conversation_id
};"""
        },
        "id": "extract-conversation-id",
        "name": "Extract Conversation ID",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [300, 200]
    }

    workflow['nodes'].append(extract_id_node)
    print("   ✓ Extract Conversation ID node created")

    # Step 3: Update connections
    print(f"\n🔧 Step 3: Updating connections...")

    # OLD: Is Duplicate? → Save Message → Is Image?
    # NEW: Is Duplicate? → Is Image? (direct)
    workflow['connections']['Is Duplicate?']['main'][1] = [
        {
            "node": "Is Image?",
            "type": "main",
            "index": 0
        }
    ]
    print("   ✓ Is Duplicate? now connects to Is Image? (skips Save Message)")

    # Is Image? connections stay the same (to Trigger Image Analysis and Prepare Data)

    # OLD: Trigger AI Agent → Webhook Response Success
    # NEW: Trigger AI Agent → Extract Conversation ID
    workflow['connections']['Trigger AI Agent'] = {
        "main": [[
            {
                "node": "Extract Conversation ID",
                "type": "main",
                "index": 0
            }
        ]]
    }
    print("   ✓ Trigger AI Agent now connects to Extract Conversation ID")

    # NEW: Extract Conversation ID → Save Message
    workflow['connections']['Extract Conversation ID'] = {
        "main": [[
            {
                "node": "Save Message",
                "type": "main",
                "index": 0
            }
        ]]
    }
    print("   ✓ Extract Conversation ID now connects to Save Message")

    # KEEP: Save Message → Webhook Response Success (reuse existing connection)
    workflow['connections']['Save Message'] = {
        "main": [[
            {
                "node": "Webhook Response Success",
                "type": "main",
                "index": 0
            }
        ]]
    }
    print("   ✓ Save Message connects to Webhook Response Success")

    # Step 4: Update positions for better visualization
    print(f"\n🔧 Step 4: Updating node positions...")
    workflow['nodes'][save_message_idx]['position'] = [400, 200]
    workflow['nodes'][is_image_idx]['position'] = [-200, 100]
    workflow['nodes'][prepare_data_idx]['position'] = [0, 200]
    workflow['nodes'][trigger_ai_idx]['position'] = [200, 200]
    workflow['nodes'][webhook_success_idx]['position'] = [500, 200]
    print("   ✓ Node positions updated for clarity")

    # Step 5: Update workflow metadata
    workflow['name'] = '01 - WhatsApp Handler V2.7 (Save Message Order Fix)'
    workflow['versionId'] = 'v2-7-save-message-order-fix'
    workflow['id'] = 'workflow-01-v27-save-order-fix'
    print(f"\n✅ Workflow metadata updated")

    # Save corrected workflow
    print(f"\n💾 Saving V2.7 workflow...")
    with open(OUTPUT_WORKFLOW, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print(f"✅ Workflow saved: {OUTPUT_WORKFLOW}")

    # Summary
    print("\n" + "=" * 80)
    print("✅ WORKFLOW 01 V2.7 FIX COMPLETE")
    print("=" * 80)
    print(f"Input:  {INPUT_WORKFLOW}")
    print(f"Output: {OUTPUT_WORKFLOW}")
    print(f"\n🔧 Changes Applied:")
    print(f"  1. ✓ Reordered execution: AI Agent BEFORE Save Message")
    print(f"  2. ✓ Added Extract Conversation ID node")
    print(f"  3. ✓ Updated Save Message query to use extracted conversation_id")
    print(f"  4. ✓ Updated all node connections")
    print(f"  5. ✓ Node positions adjusted for clarity")
    print(f"\n📋 New Execution Flow:")
    print(f"  1. Is Duplicate? (check)")
    print(f"  2. Is Image? (route)")
    print(f"  3. Prepare Data for AI Agent")
    print(f"  4. Trigger AI Agent → returns conversation_id ✅")
    print(f"  5. Extract Conversation ID (new node)")
    print(f"  6. Save Message → uses valid conversation_id ✅")
    print(f"  7. Webhook Response Success")
    print(f"\n🎯 Critical Fix:")
    print(f"  ✓ conversation_id is now valid (from AI Agent response)")
    print(f"  ✓ INSERT will succeed (no NULL constraint violation)")
    print(f"  ✓ Executions will complete (no stuck 'running' status)")
    print(f"\n📋 Next Steps:")
    print(f"  1. Import workflow in n8n: {OUTPUT_WORKFLOW}")
    print(f"  2. Deactivate V2.6 workflow")
    print(f"  3. Activate V2.7 workflow")
    print(f"  4. Test with WhatsApp message")
    print(f"  5. Verify Save Message executes successfully")
    print(f"  6. Check database: messages table has conversation_id")
    print("=" * 80)

    return True


if __name__ == '__main__':
    success = fix_workflow_01_v27()
    exit(0 if success else 1)
