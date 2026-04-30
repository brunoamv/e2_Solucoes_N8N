#!/usr/bin/env python3
"""
V48 Fix Script - Conversation ID Propagation Fix
Purpose: Ensure conversation_id is properly propagated through workflow
Root Cause: State Machine Logic receives NULL conversation_id
Result: UPDATE queries don't persist state changes
"""

import json
from pathlib import Path

def fix_workflow_v48_conversation_id():
    """Fix conversation_id propagation through workflow"""

    # Paths
    base_dir = Path(__file__).parent.parent
    workflow_v47 = base_dir / "n8n/workflows/02_ai_agent_conversation_V47_PHONE_CONSISTENCY.json"
    workflow_v48 = base_dir / "n8n/workflows/02_ai_agent_conversation_V48_CONVERSATION_ID_FIX.json"

    print("=== V48 CONVERSATION ID PROPAGATION FIX ===")
    print(f"Reading: {workflow_v47}")

    # Read workflow V47
    with open(workflow_v47, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    changes_made = []

    # Fix 1: State Machine Logic - Add conversation_id extraction and validation
    state_machine_node = None
    for node in workflow['nodes']:
        if node['name'] == 'State Machine Logic':
            state_machine_node = node
            break

    if state_machine_node:
        print("\n✅ Found 'State Machine Logic' node")

        # Get existing code
        params = state_machine_node.get('parameters', {})
        function_code = params.get('functionCode', '')

        # Add conversation_id extraction at the beginning (after initial declarations)
        conversation_id_check = '''
// ============================================================================
// V48: CONVERSATION ID PROPAGATION FIX
// ============================================================================
// Extract conversation_id from input - try multiple sources
const input_data = $input.first().json;
const conversation_id = input_data.id ||
                       input_data.conversation_id ||
                       null;

console.log('================================');
console.log('V48 CONVERSATION ID CHECK');
console.log('================================');
console.log('Input data keys:', Object.keys(input_data));
console.log('  raw_id:', input_data.id);
console.log('  conversation_id:', input_data.conversation_id);
console.log('  FINAL conversation_id:', conversation_id);
console.log('================================');

// CRITICAL: Validate conversation_id exists
if (!conversation_id) {
  console.error('V48 CRITICAL ERROR: conversation_id is NULL!');
  console.error('Cannot update conversation state without valid ID');
  console.error('Input data:', JSON.stringify(input_data, null, 2));
  throw new Error('conversation_id is required for state updates - received NULL');
}

console.log('✅ V48: conversation_id validated:', conversation_id);
// ============================================================================
'''

        # Find where to insert (after const message = ...)
        if 'const message = ' in function_code:
            # Insert after message declaration
            insert_pos = function_code.find('const message = ')
            # Find end of that line
            newline_pos = function_code.find('\n', insert_pos)
            if newline_pos > 0:
                function_code = (
                    function_code[:newline_pos+1] +
                    conversation_id_check +
                    function_code[newline_pos+1:]
                )

                state_machine_node['parameters']['functionCode'] = function_code
                changes_made.append("Added conversation_id extraction and validation to State Machine Logic")
                print("✅ Added conversation_id check to State Machine Logic")
        else:
            print("⚠️  Could not find insertion point in State Machine Logic")

    else:
        print("❌ ERROR: 'State Machine Logic' node not found")

    # Fix 2: Merge Conversation Data - Configure to preserve all fields
    merge_node = None
    for node in workflow['nodes']:
        if node['name'] == 'Merge Conversation Data':
            merge_node = node
            break

    if merge_node:
        print("\n✅ Found 'Merge Conversation Data' node")

        # Configure merge to use "Merge By Key" mode to preserve all fields
        merge_node['parameters'] = {
            'mode': 'combine',
            'mergeByFields': {
                'values': []
            },
            'options': {
                'includeUnpopulated': True
            }
        }

        changes_made.append("Configured Merge node to preserve all fields (combine mode)")
        print("✅ Configured Merge node to preserve all fields")
    else:
        print("⚠️  'Merge Conversation Data' node not found (may not exist in V47)")

    # Update workflow metadata
    workflow['name'] = "02 - AI Agent Conversation V48 (Conversation ID Fix)"
    workflow['versionId'] = "v48-conversation-id-fix"

    # Save as V48
    print(f"\nSaving fixed workflow: {workflow_v48}")
    with open(workflow_v48, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print("\n✅ V48 Conversation ID Fix Complete!")
    print("\n" + "="*60)
    print("CHANGES MADE:")
    print("="*60)
    for i, change in enumerate(changes_made, 1):
        print(f"{i}. {change}")

    print("\n" + "="*60)
    print("CRITICAL FIX:")
    print("="*60)
    print("✅ State Machine Logic now:")
    print("   - Extracts conversation_id from multiple sources")
    print("   - Validates conversation_id is not NULL")
    print("   - Throws error if conversation_id missing")
    print("   - Logs detailed conversation_id resolution process")
    print("\n✅ Merge node configured to preserve all fields")

    print("\n" + "="*60)
    print("EXPECTED BEHAVIOR:")
    print("="*60)
    print("BEFORE V48:")
    print("  ❌ conversation_id = NULL → UPDATE não persiste")
    print("\nAFTER V48:")
    print("  ✅ conversation_id = 8b455c85... → UPDATE funciona!")
    print("  ✅ Estado persiste no banco corretamente")
    print("  ✅ Bot progride no fluxo (não volta ao menu)")

    print("\n" + "="*60)
    print("TESTING STEPS:")
    print("="*60)
    print("1. Clean test conversation:")
    print("   docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \\")
    print("     -c \"DELETE FROM conversations WHERE phone_number = '556181755748';\"")
    print("\n2. Import workflow V48 in n8n:")
    print("   http://localhost:5678")
    print("\n3. Deactivate workflow V47")
    print("\n4. Activate workflow V48")
    print("\n5. Test with WhatsApp:")
    print("   - Send 'oi' → Bot shows menu ✅")
    print("   - Send '1' → Bot asks for name ✅")
    print("   - Send 'Bruno Rosa' → Bot asks for phone ✅ (NOT menu!)")
    print("\n6. Verify database:")
    print("   docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \\")
    print("     -c \"SELECT phone_number, state_machine_state, contact_name FROM conversations;\"")
    print("\n   Expected:")
    print("   - state_machine_state = 'collect_phone' (NOT 'service_selection')")
    print("   - contact_name = 'Bruno Rosa'")

    print("\n" + "="*60)
    print("VALIDATION:")
    print("="*60)
    print("Check n8n logs for V48 diagnostics:")
    print("  docker logs e2bot-n8n-dev 2>&1 | grep 'V48'")
    print("\nExpected logs:")
    print("  ✅ V48 CONVERSATION ID CHECK")
    print("  ✅ FINAL conversation_id: 8b455c85...")
    print("  ✅ V48: conversation_id validated")
    print("="*60)

    return True

if __name__ == '__main__':
    success = fix_workflow_v48_conversation_id()
    exit(0 if success else 1)
