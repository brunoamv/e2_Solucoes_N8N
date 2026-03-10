#!/usr/bin/env python3
"""
V54 Fix Script - Enhanced Conversation ID Extraction
Purpose: Add explicit conversation_id extraction and validation
Root Cause: V53 merge works but State Machine can't find 'id' field
Solution: Enhanced logging and explicit conversation_id extraction in State Machine
"""

import json
from pathlib import Path

def fix_workflow_v54_conversation_id():
    """Enhance State Machine Logic with explicit conversation_id extraction"""

    base_dir = Path(__file__).parent.parent
    workflow_v53 = base_dir / "n8n/workflows/02_ai_agent_conversation_V53_MERGE_BY_POSITION.json"
    workflow_v54 = base_dir / "n8n/workflows/02_ai_agent_conversation_V54_CONVERSATION_ID_FIX.json"

    print("=== V54 CONVERSATION ID EXTRACTION FIX ===")
    print(f"Reading: {workflow_v53}")

    with open(workflow_v53, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    changes_made = []

    # Find State Machine Logic node and enhance conversation_id extraction
    for i, node in enumerate(workflow['nodes']):
        if node['name'] == 'State Machine Logic' and node['type'] == 'n8n-nodes-base.function':
            print(f"\n✅ Found 'State Machine Logic' node")

            # Get current code
            current_code = node['parameters']['functionCode']

            # Find the V48 conversation_id section and replace it
            v48_section_start = current_code.find('// ============================================================================\n// V48: CONVERSATION ID PROPAGATION FIX')
            v48_section_end = current_code.find('// ============================================================================', v48_section_start + 10)

            if v48_section_start != -1 and v48_section_end != -1:
                # Extract parts before and after V48 section
                before_v48 = current_code[:v48_section_start]
                after_v48 = current_code[v48_section_end + 78:]  # Skip closing line

                # Create enhanced V54 conversation_id extraction section
                v54_section = '''// ============================================================================
// V54: ENHANCED CONVERSATION ID EXTRACTION (replaces V48)
// ============================================================================
console.log('=== V54 CONVERSATION ID EXTRACTION ===');

// Get input data
const input_data = $input.first().json;

// Comprehensive diagnostic logging
console.log('V54 Diagnostics:');
console.log('  All available keys:', Object.keys(input_data).join(', '));
console.log('  Total fields:', Object.keys(input_data).length);

// Check all possible conversation_id sources
console.log('V54 Field Checks:');
console.log('  input_data.id:', input_data.id, '(type:', typeof input_data.id, ')');
console.log('  input_data.conversation_id:', input_data.conversation_id, '(type:', typeof input_data.conversation_id, ')');

// Check if we received database output
const hasDbFields = !!(
  input_data.state_machine_state ||
  input_data.current_state ||
  input_data.created_at ||
  input_data.updated_at
);

console.log('  Database fields present:', hasDbFields);

// Try to extract conversation_id from multiple sources
let conversation_id = null;

// Source 1: Direct id field from database
if (input_data.id) {
  conversation_id = input_data.id;
  console.log('✅ V54: Found id from database:', conversation_id);
}
// Source 2: Explicit conversation_id field
else if (input_data.conversation_id) {
  conversation_id = input_data.conversation_id;
  console.log('✅ V54: Found conversation_id field:', conversation_id);
}
// Source 3: Try to extract from conversation object (legacy support)
else if (input_data.conversation && input_data.conversation.id) {
  conversation_id = input_data.conversation.id;
  console.log('✅ V54: Found id in conversation object:', conversation_id);
}

// CRITICAL: Validate conversation_id
if (!conversation_id) {
  console.error('V54 CRITICAL ERROR: conversation_id is NULL!');
  console.error('V54 Full Diagnostic Dump:');
  console.error('  Available keys:', Object.keys(input_data));
  console.error('  Has DB fields?:', hasDbFields);
  console.error('  Input 0 (Merge Queries) likely has:', 'phone_number, message, query_*');
  console.error('  Input 1 (Database) should have:', 'id, state_machine_state, created_at');
  console.error('  Full input data:', JSON.stringify(input_data, null, 2).substring(0, 500) + '...');

  throw new Error('V54: conversation_id extraction failed - no id field found in merge output');
}

console.log('✅ V54 SUCCESS: conversation_id validated:', conversation_id);
console.log('=== V54 CONVERSATION ID EXTRACTION COMPLETE ===');
// ============================================================================'''

                # Reconstruct the function code
                new_code = before_v48 + v54_section + '\n' + after_v48

                # Update node
                workflow['nodes'][i]['parameters']['functionCode'] = new_code
                changes_made.append("Enhanced State Machine Logic with V54 conversation_id extraction")
                print(f"   ✅ Replaced V48 section with V54 enhanced extraction")
                print(f"   ✅ Added comprehensive diagnostic logging")
                print(f"   ✅ Added multiple conversation_id source checks")
            else:
                print(f"   ⚠️  Warning: V48 section not found in exact format")
                print(f"   ℹ️  Will add V54 section at beginning of function")

                # Add V54 section at start of function if V48 not found
                v54_injection = '''
// ============================================================================
// V54: ENHANCED CONVERSATION ID EXTRACTION
// ============================================================================
console.log('=== V54 CONVERSATION ID EXTRACTION ===');
const input_data = $input.first().json;
console.log('V54: All keys:', Object.keys(input_data).join(', '));
console.log('V54: id =', input_data.id, ', conversation_id =', input_data.conversation_id);

const conversation_id = input_data.id || input_data.conversation_id || null;
if (!conversation_id) {
  console.error('V54 ERROR: No conversation_id found!');
  console.error('V54: Available fields:', Object.keys(input_data));
  throw new Error('V54: conversation_id extraction failed');
}
console.log('✅ V54: conversation_id =', conversation_id);
// ============================================================================

'''
                workflow['nodes'][i]['parameters']['functionCode'] = v54_injection + current_code
                changes_made.append("Injected V54 conversation_id extraction at function start")

    # Update workflow metadata
    workflow['name'] = "02 - AI Agent Conversation V54 (Conversation ID Fix)"
    workflow['versionId'] = "v54-conversation-id-fix"

    # Save V54
    print(f"\nSaving fixed workflow: {workflow_v54}")
    with open(workflow_v54, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print("\n✅ V54 Conversation ID Fix Complete!")

    if changes_made:
        print("\n" + "="*60)
        print("CHANGES MADE:")
        print("="*60)
        for i, change in enumerate(changes_made, 1):
            print(f"{i}. {change}")
    else:
        print("\n" + "="*60)
        print("WARNING: No changes made!")
        print("="*60)

    print("\n" + "="*60)
    print("WHY V54 FIXES conversation_id NULL (vs V53):")
    print("="*60)
    print("❌ V53 Problem:")
    print("   - mergeByPosition works correctly")
    print("   - But State Machine can't find 'id' field")
    print("   - Limited diagnostic logging")
    print("")
    print("✅ V54 Solution:")
    print("   - Enhanced diagnostic logging shows all available fields")
    print("   - Multiple conversation_id extraction sources")
    print("   - Explicit validation with detailed error messages")
    print("   - Full input dump on error for debugging")

    print("\n" + "="*60)
    print("V54 ENHANCED EXTRACTION LOGIC:")
    print("="*60)
    print("1. Check input_data.id (direct from database)")
    print("2. Check input_data.conversation_id (explicit field)")
    print("3. Check input_data.conversation.id (legacy nested object)")
    print("4. Log ALL available fields if extraction fails")
    print("5. Provide full diagnostic dump for debugging")

    print("\n" + "="*60)
    print("TESTING V54:")
    print("="*60)
    print("1. Clean test data:")
    print("   docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \\")
    print("     -c \"DELETE FROM conversations WHERE phone_number = '556181755748';\"")
    print("")
    print("2. Import V54 in n8n: http://localhost:5678")
    print("3. Deactivate V53, activate V54")
    print("")
    print("4. Test NEW user flow:")
    print("   - Send 'oi' → Bot shows menu")
    print("   - Send '1' → Bot asks for name")
    print("   - Send 'Bruno Rosa' → Bot asks for phone (NOT menu!)")
    print("")
    print("5. Check V54 execution logs:")
    print("   docker logs e2bot-n8n-dev 2>&1 | grep -A 15 'V54'")
    print("")
    print("   Expected output:")
    print("   === V54 CONVERSATION ID EXTRACTION ===")
    print("   V54 Diagnostics:")
    print("     All available keys: [list of fields]")
    print("   V54 Field Checks:")
    print("     input_data.id: [value]")
    print("   ✅ V54 SUCCESS: conversation_id validated: [value]")
    print("="*60)

    return True

if __name__ == '__main__':
    success = fix_workflow_v54_conversation_id()
    exit(0 if success else 1)
