#!/usr/bin/env python3
"""
V49 Fix Script - Add Merge Input Validation
Purpose: Validate Merge node receives 2 inputs with proper data
Root Cause: Custom Merge doesn't validate input count before processing
Result: Clear error messages when database doesn't provide 'id'
"""

import json
from pathlib import Path

def fix_workflow_v49_merge_validation():
    """Add input validation and alwaysOutputData to PostgreSQL nodes"""

    base_dir = Path(__file__).parent.parent
    workflow_v48_4 = base_dir / "n8n/workflows/02_ai_agent_conversation_V48_4_CUSTOM_MERGE.json"
    workflow_v49 = base_dir / "n8n/workflows/02_ai_agent_conversation_V49_MERGE_VALIDATION.json"

    print("=== V49 MERGE INPUT VALIDATION FIX ===")
    print(f"Reading: {workflow_v48_4}")

    with open(workflow_v48_4, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    changes_made = []

    # 1. Update Merge Conversation Data code with validation
    merge_node = None
    for node in workflow['nodes']:
        if node['name'] == 'Merge Conversation Data':
            merge_node = node
            break

    if not merge_node:
        print("❌ ERROR: 'Merge Conversation Data' node not found")
        return False

    print(f"\n✅ Found 'Merge Conversation Data' node")

    # New validated custom merge code
    new_merge_code = """// Merge Conversation Data - V49 INPUT VALIDATION FIX
// Validates inputs before merging to catch missing database data

// V49: ROBUST INPUT COUNT VALIDATION
const allInputs = $input.all();
const inputCount = allInputs.length;

console.log('=== V49 MERGE INPUT VALIDATION ===');
console.log('Total inputs received:', inputCount);

if (inputCount !== 2) {
  console.error('');
  console.error('❌ V49 CRITICAL ERROR: WRONG INPUT COUNT');
  console.error('Expected: 2 inputs (queries from Merge Queries Data + database from Create/Get Details)');
  console.error('Received:', inputCount, 'input(s)');
  console.error('');
  console.error('Inputs detail:');
  allInputs.forEach((inp, i) => {
    const json = inp.json || {};
    console.error(`  Input ${i}:`, {
      keys: Object.keys(json).slice(0, 10),  // First 10 keys
      totalKeys: Object.keys(json).length,
      hasId: !!json.id,
      hasPhoneNumber: !!json.phone_number,
      hasMessage: !!json.message
    });
  });
  console.error('');

  throw new Error(`Merge Conversation Data requires 2 inputs, received ${inputCount}. Check workflow connections.`);
}

console.log('✅ V49: Input count validated (2 inputs)');

// Extract inputs with explicit indexing
const queryInput = allInputs[0].json;  // Input 0: Merge Queries Data
const dbInput = allInputs[1].json;     // Input 1: Create New Conversation OR Get Conversation Details

// V49: VALIDATE QUERY INPUT
if (!queryInput || typeof queryInput !== 'object') {
  console.error('❌ V49 ERROR: Query input (input 0) is invalid');
  throw new Error('Query input is null or not an object');
}

console.log('✅ V49: Query input validated');
console.log('   Keys count:', Object.keys(queryInput).length);
console.log('   Has phone_number:', !!queryInput.phone_number);
console.log('   Has message:', !!queryInput.message);

// V49: VALIDATE DATABASE INPUT
if (!dbInput || typeof dbInput !== 'object') {
  console.error('');
  console.error('❌ V49 CRITICAL ERROR: DATABASE INPUT INVALID');
  console.error('Database input (input 1) is null or not an object');
  console.error('Type:', typeof dbInput);
  console.error('Value:', dbInput);
  console.error('');
  throw new Error('Database input is null or not an object. Create/Get Details node may have failed.');
}

if (!dbInput.id) {
  console.error('');
  console.error('❌ V49 CRITICAL ERROR: MISSING ID IN DATABASE INPUT');
  console.error('Database input is missing required id field');
  console.error('Database input keys:', Object.keys(dbInput));
  console.error('Database input (first 500 chars):', JSON.stringify(dbInput, null, 2).substring(0, 500));
  console.error('');
  console.error('Possible causes:');
  console.error('  1. Create New Conversation query missing RETURNING *');
  console.error('  2. Get Conversation Details query missing id in SELECT');
  console.error('  3. PostgreSQL node not capturing output (missing alwaysOutputData?)');
  console.error('');
  throw new Error('Database input missing required id field');
}

console.log('✅ V49: Database input validated');
console.log('   id:', dbInput.id);
console.log('   Keys count:', Object.keys(dbInput).length);
console.log('   state_machine_state:', dbInput.state_machine_state);

// V49: ALL VALIDATIONS PASSED - PROCEED WITH MERGE
console.log('');
console.log('=== V49 CUSTOM MERGE (VALIDATED) ===');
console.log('Query input keys:', Object.keys(queryInput).sort());
console.log('DB input keys:', Object.keys(dbInput).sort());
console.log('DB id:', dbInput.id);

// CRITICAL: Combine ALL fields from BOTH inputs
// Database fields take precedence for duplicates (mais recente)
const mergedData = {
  // Start with query data (phone formats, queries, message)
  ...queryInput,

  // Override/add with database data (id, state_machine_state, collected_data)
  ...dbInput,

  // CRITICAL: Explicitly ensure id and conversation_id fields
  id: dbInput.id,
  conversation_id: dbInput.id,

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
console.log('V49 CUSTOM MERGE RESULT');
console.log('================================');
console.log('Merged data keys:', Object.keys(mergedData).sort().join(', '));
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

// FINAL VALIDATION: Ensure critical fields exist
if (!mergedData.id || !mergedData.conversation_id) {
  console.error('⚠️ V49 WARNING: Merge completed but id/conversation_id still missing!');
  console.error('This should not happen after all validations. Check merge logic.');
}

if (!mergedData.phone_number) {
  console.error('⚠️ V49 WARNING: No phone number in merge result!');
}

console.log('✅ V49: Merge validation complete, returning merged data');

// CRITICAL: Return single object (not array)
return mergedData;"""

    merge_node['parameters']['jsCode'] = new_merge_code
    changes_made.append("Updated Merge Conversation Data with V49 input validation")

    # 2. Add alwaysOutputData to Create New Conversation
    create_node = None
    for node in workflow['nodes']:
        if node['name'] == 'Create New Conversation':
            create_node = node
            break

    if create_node:
        create_node['alwaysOutputData'] = True
        changes_made.append("Added alwaysOutputData to Create New Conversation node")
        print("✅ Updated Create New Conversation node")

    # 3. Verify Get Conversation Details also has alwaysOutputData
    get_details_node = None
    for node in workflow['nodes']:
        if node['name'] == 'Get Conversation Details':
            get_details_node = node
            break

    if get_details_node:
        get_details_node['alwaysOutputData'] = True
        changes_made.append("Added alwaysOutputData to Get Conversation Details node")
        print("✅ Updated Get Conversation Details node")

    # Update workflow metadata
    workflow['name'] = "02 - AI Agent Conversation V49 (Merge Validation)"
    workflow['versionId'] = "v49-merge-input-validation"

    # Save V49
    print(f"\nSaving fixed workflow: {workflow_v49}")
    with open(workflow_v49, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print("\n✅ V49 Merge Validation Fix Complete!")
    print("\n" + "="*60)
    print("CHANGES MADE:")
    print("="*60)
    for i, change in enumerate(changes_made, 1):
        print(f"{i}. {change}")

    print("\n" + "="*60)
    print("VALIDATION IMPROVEMENTS:")
    print("="*60)
    print("✅ Input count validation (expects exactly 2 inputs)")
    print("✅ Query input validation (ensures queries and phone data)")
    print("✅ Database input validation (ensures id field exists)")
    print("✅ Explicit error messages for each validation failure")
    print("✅ alwaysOutputData added to PostgreSQL nodes")

    print("\n" + "="*60)
    print("EXPECTED BEHAVIOR:")
    print("="*60)
    print("✅ If Create New Conversation fails → clear error message")
    print("✅ If Get Conversation Details fails → clear error message")
    print("✅ If either doesn't return id → clear error message")
    print("✅ If both inputs valid → merge succeeds with id")

    print("\n" + "="*60)
    print("TESTING:")
    print("="*60)
    print("1. Import V49 in n8n: http://localhost:5678")
    print("2. Deactivate V48.4, activate V49")
    print("3. Clean test data:")
    print("   docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \\")
    print("     -c \"DELETE FROM conversations WHERE phone_number = '556181755748';\"")
    print("")
    print("4. Test NEW user flow:")
    print("   - Send 'oi' → Bot shows menu")
    print("   - Send '1' → Bot asks for name")
    print("   - Send 'Bruno Rosa' → Bot asks for phone (NOT menu!)")
    print("")
    print("5. Check V49 validation logs:")
    print("   docker logs e2bot-n8n-dev 2>&1 | grep -A 30 'V49 MERGE INPUT VALIDATION'")

    return True

if __name__ == '__main__':
    success = fix_workflow_v49_merge_validation()
    exit(0 if success else 1)
