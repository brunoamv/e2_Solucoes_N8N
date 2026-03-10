#!/usr/bin/env python3
"""
V48.4 Fix Script - Replace Merge Node with Custom Code
Purpose: Fix Merge node issues by using explicit JavaScript merge logic
Root Cause: n8n Merge node modes não funcionam para nosso caso
Result: Custom code node with explicit field merging
"""

import json
from pathlib import Path

def fix_workflow_v48_4_custom_merge():
    """Replace Merge node with custom code node for explicit merging"""

    # Paths
    base_dir = Path(__file__).parent.parent
    workflow_v48_3 = base_dir / "n8n/workflows/02_ai_agent_conversation_V48_3_MERGE_COMBINE_FIX.json"
    workflow_v48_4 = base_dir / "n8n/workflows/02_ai_agent_conversation_V48_4_CUSTOM_MERGE.json"

    print("=== V48.4 CUSTOM MERGE FIX ===")
    print(f"Reading: {workflow_v48_3}")

    # Read workflow V48.3
    with open(workflow_v48_3, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    changes_made = []

    # Find Merge Conversation Data node
    merge_node = None
    merge_node_idx = None
    for idx, node in enumerate(workflow['nodes']):
        if node['name'] == 'Merge Conversation Data':
            merge_node = node
            merge_node_idx = idx
            break

    if merge_node:
        print(f"\n✅ Found 'Merge Conversation Data' node")
        print(f"   Current type: {merge_node['type']}")
        print(f"   Current mode: {merge_node.get('parameters', {}).get('mode', 'NOT SET')}")

        # Replace with Code node
        custom_code = """// Merge Conversation Data - V48.4 CUSTOM CODE MERGE
// Explicitly merge ALL fields from BOTH inputs

const queryInput = $input.first().json;  // Merge Queries Data output
const dbInput = $input.last().json;      // Get Conversation Details or Create output

// DEBUG: Log inputs
console.log('=== V48.4 CUSTOM MERGE ===');
console.log('Query input keys:', Object.keys(queryInput));
console.log('DB input keys:', Object.keys(dbInput));
console.log('DB input id:', dbInput.id);

// CRITICAL: Combine ALL fields from BOTH inputs
// Database fields take precedence for duplicates (mais recente)
const mergedData = {
  // Start with query data (phone formats, queries, message)
  ...queryInput,

  // Override/add with database data (id, state_machine_state, collected_data)
  ...dbInput,

  // CRITICAL: Explicitly ensure id and conversation_id fields
  id: dbInput.id || queryInput.id || null,
  conversation_id: dbInput.id || queryInput.conversation_id || null,

  // Ensure conversation object for State Machine
  conversation: {
    id: dbInput.id,
    phone_number: dbInput.phone_number || queryInput.phone_number,
    state_machine_state: dbInput.state_machine_state || 'greeting',
    collected_data: dbInput.collected_data || {},
    error_count: dbInput.error_count || 0,
    ...dbInput
  },

  // Explicitly preserve critical fields
  phone_number: queryInput.phone_number || dbInput.phone_number,
  phone_with_code: queryInput.phone_with_code,
  phone_without_code: queryInput.phone_without_code,

  // Preserve message data with fallbacks
  message: queryInput.message || queryInput.body || queryInput.text || '',
  content: queryInput.content || queryInput.message || '',
  body: queryInput.body || queryInput.message || '',
  text: queryInput.text || queryInput.message || '',

  // Preserve query strings
  query_count: queryInput.query_count,
  query_details: queryInput.query_details,
  query_upsert: queryInput.query_upsert
};

// DEBUG: Verify merge result
console.log('================================');
console.log('V48.4 CUSTOM MERGE RESULT');
console.log('================================');
console.log('Merged data keys:', Object.keys(mergedData).sort());
console.log('');
console.log('CRITICAL FIELDS:');
console.log('  id:', mergedData.id);
console.log('  conversation_id:', mergedData.conversation_id);
console.log('  conversation.id:', mergedData.conversation?.id);
console.log('  phone_number:', mergedData.phone_number);
console.log('  message:', mergedData.message ? 'PRESENT' : 'MISSING');
console.log('  query_count:', mergedData.query_count ? 'PRESENT' : 'MISSING');
console.log('  query_details:', mergedData.query_details ? 'PRESENT' : 'MISSING');
console.log('================================');

// VALIDATION: Ensure critical fields exist
if (!mergedData.id && !mergedData.conversation_id) {
  console.error('⚠️ WARNING: No conversation ID found in merge result!');
  console.error('DB input:', JSON.stringify(dbInput, null, 2));
}

if (!mergedData.phone_number) {
  console.error('⚠️ WARNING: No phone number in merge result!');
}

// CRITICAL: Return single object (not array)
return mergedData;"""

        # Create new Code node to replace Merge node
        new_code_node = {
            "parameters": {
                "jsCode": custom_code
            },
            "id": merge_node['id'],  # Keep same ID for connections
            "name": "Merge Conversation Data",  # Keep same name
            "type": "n8n-nodes-base.code",  # Change to Code node
            "typeVersion": 2,
            "position": merge_node['position'],
            "alwaysOutputData": True
        }

        # Replace node in workflow
        workflow['nodes'][merge_node_idx] = new_code_node

        changes_made.append("Replaced Merge node with custom Code node")
        changes_made.append("Added explicit field merging logic")
        changes_made.append("Added comprehensive debugging logs")
        changes_made.append("Added validation for critical fields")

        print("✅ Replaced Merge node with custom Code node")
        print("   New type: n8n-nodes-base.code")
        print("   Logic: Explicit field merging with fallbacks")
    else:
        print("❌ ERROR: 'Merge Conversation Data' node not found")
        return False

    # Update workflow metadata
    workflow['name'] = "02 - AI Agent Conversation V48.4 (Custom Merge)"
    workflow['versionId'] = "v48-4-custom-merge"

    # Save as V48.4
    print(f"\nSaving fixed workflow: {workflow_v48_4}")
    with open(workflow_v48_4, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print("\n✅ V48.4 Custom Merge Fix Complete!")
    print("\n" + "="*60)
    print("CHANGES MADE:")
    print("="*60)
    for i, change in enumerate(changes_made, 1):
        print(f"{i}. {change}")

    print("\n" + "="*60)
    print("SOLUTION APPROACH:")
    print("="*60)
    print("❌ V48.2 (mergeByIndex): Only first input fields")
    print("❌ V48.3 (combine): Breaks execution")
    print("❌ V48.3 (append): Works but doesn't merge fields")
    print("✅ V48.4 (custom code): Explicit field merging")
    print("")
    print("Custom code:")
    print("  - Receives both inputs explicitly")
    print("  - Spreads query data first")
    print("  - Spreads database data second (override)")
    print("  - Explicitly ensures id and conversation_id")
    print("  - Creates conversation object for State Machine")
    print("  - Comprehensive debugging logs")

    print("\n" + "="*60)
    print("EXPECTED BEHAVIOR:")
    print("="*60)
    print("Input 1 (Query Data):")
    print("  {phone_number, query_count, query_details, message, ...}")
    print("")
    print("Input 2 (Database Result):")
    print("  {id, phone_number, state_machine_state, collected_data, ...}")
    print("")
    print("Custom Merge Output:")
    print("  {")
    print("    ...ALL fields from Input 1,")
    print("    ...ALL fields from Input 2 (overrides duplicates),")
    print("    id: db.id,                    ✅ CRITICAL")
    print("    conversation_id: db.id,       ✅ CRITICAL")
    print("    conversation: {...db data},   ✅ For State Machine")
    print("    phone_number: query or db,")
    print("    message: query.message,")
    print("    query_count: query SQL,")
    print("    query_details: query SQL")
    print("  }")

    print("\n" + "="*60)
    print("TESTING STEPS:")
    print("="*60)
    print("1. Import workflow V48.4 in n8n")
    print("   http://localhost:5678")
    print("")
    print("2. Deactivate V48.3")
    print("")
    print("3. Activate V48.4")
    print("")
    print("4. Clean test data:")
    print("   docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \\")
    print("     -c \"DELETE FROM conversations WHERE phone_number = '556181755748';\"")
    print("")
    print("5. Test with WhatsApp:")
    print("   - Send 'oi' → Bot shows menu")
    print("   - Send '1' → Bot asks for name")
    print("   - Send 'Bruno Rosa' → Bot asks for phone (NOT menu!)")
    print("")
    print("6. Check V48.4 logs:")
    print("   docker logs e2bot-n8n-dev 2>&1 | grep 'V48.4'")
    print("")
    print("   Expected:")
    print("   ✅ V48.4 CUSTOM MERGE")
    print("   ✅ Merged data keys: [..., 'id', ...]")
    print("   ✅ id: d784ce32-06f6-4423-9ff8-99e49ed81a15")
    print("   ✅ conversation_id: d784ce32-06f6-4423-9ff8-99e49ed81a15")
    print("   ✅ conversation.id: d784ce32-06f6-4423-9ff8-99e49ed81a15")
    print("")
    print("7. Check V48 State Machine logs:")
    print("   docker logs e2bot-n8n-dev 2>&1 | grep -A 10 'V48 CONVERSATION ID CHECK'")
    print("")
    print("   Expected:")
    print("   ✅ Input data keys: [..., 'id', ...]")
    print("   ✅ raw_id: d784ce32... (NOT undefined!)")
    print("   ✅ FINAL conversation_id: d784ce32... (NOT null!)")
    print("   ✅ V48: conversation_id validated")
    print("")
    print("8. Verify database:")
    print("   docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -c \\")
    print("     \"SELECT phone_number, state_machine_state, contact_name \\")
    print("      FROM conversations WHERE phone_number = '556181755748';\"")
    print("")
    print("   Expected:")
    print("   - state_machine_state: collect_phone (NOT service_selection)")
    print("   - contact_name: Bruno Rosa (NOT empty)")

    print("\n" + "="*60)
    print("VALIDATION:")
    print("="*60)
    print("✅ Custom Code node created successfully")
    print("✅ Explicit merge logic implemented")
    print("✅ Debugging logs added")
    print("✅ Field validation included")
    print("✅ Ready for import and testing")
    print("="*60)

    return True

if __name__ == '__main__':
    success = fix_workflow_v48_4_custom_merge()
    exit(0 if success else 1)
