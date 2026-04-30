#!/usr/bin/env python3
"""
Fix complete data loss in collected_data for V3 workflow
Preserves ALL data and maintains proper types
"""
import json
import sys
from datetime import datetime

def fix_workflow_complete():
    """
    Complete fix for data loss and type preservation issues
    """

    # Read workflow
    workflow_path = '/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V1_MENU_FIXED_v3.json'

    try:
        with open(workflow_path, 'r', encoding='utf-8') as f:
            workflow = json.load(f)
    except FileNotFoundError:
        print(f"❌ Workflow file not found: {workflow_path}")
        sys.exit(1)

    fixes_applied = []

    # Fix 1: Update Prepare Update Data node - COMPLETE FIX
    for node in workflow['nodes']:
        if node.get('id') == 'node_prepare_update_data' and node.get('name') == 'Prepare Update Data':
            print("📋 Fixing Prepare Update Data node for complete data preservation...")

            node['parameters']['jsCode'] = '''// Prepare data for database update with COMPLETE data preservation
const input = $input.first().json;

// Get ALL collected data from state machine
let collectedData = input.collected_data || {};

// Log input for debugging
console.log('=== PREPARE UPDATE DATA DEBUG ===');
console.log('Input phone_number:', input.phone_number);
console.log('Input collected_data:', JSON.stringify(collectedData));
console.log('Input collected_data type:', typeof collectedData);
console.log('Input collected_data keys:', Object.keys(collectedData));

// Ensure collected_data is a valid object
if (typeof collectedData !== 'object' || collectedData === null) {
    console.log('WARNING: collected_data is not an object, initializing as empty object');
    collectedData = {};
}

// CRITICAL FIX: Preserve ALL data with correct types
const cleanedData = {};

// Process each field with type preservation
for (const [key, value] of Object.entries(collectedData)) {
    console.log(`Processing key: ${key}, value: ${value}, type: ${typeof value}`);

    // Skip only undefined values
    if (value === undefined) {
        console.log(`  Skipping undefined value for key: ${key}`);
        continue;
    }

    // PRESERVE NATIVE TYPES - Critical for proper functioning
    if (value === null) {
        cleanedData[key] = null;
        console.log(`  Preserved null for key: ${key}`);
    } else if (typeof value === 'number') {
        cleanedData[key] = value;  // Keep as number
        console.log(`  Preserved number ${value} for key: ${key}`);
    } else if (typeof value === 'boolean') {
        cleanedData[key] = value;  // Keep as boolean
        console.log(`  Preserved boolean ${value} for key: ${key}`);
    } else if (typeof value === 'string') {
        cleanedData[key] = value;  // Keep as string (even if empty)
        console.log(`  Preserved string "${value}" for key: ${key}`);
    } else if (Array.isArray(value)) {
        cleanedData[key] = value;  // Keep arrays
        console.log(`  Preserved array for key: ${key}`);
    } else if (typeof value === 'object') {
        cleanedData[key] = value;  // Keep objects (will be stringified by JSON.stringify)
        console.log(`  Preserved object for key: ${key}`);
    } else {
        // Only convert truly unknown types to string
        cleanedData[key] = String(value);
        console.log(`  Converted unknown type to string for key: ${key}`);
    }
}

// Log cleaned data
console.log('Cleaned data object:', cleanedData);
console.log('Cleaned data keys:', Object.keys(cleanedData));
console.log('Cleaned data values:', Object.values(cleanedData));

// Safely stringify the cleaned data
let collectedDataJson = '{}';
try {
    collectedDataJson = JSON.stringify(cleanedData);
    console.log('Successfully stringified to JSON:', collectedDataJson);
    console.log('JSON length:', collectedDataJson.length);
} catch (e) {
    console.error('ERROR stringifying collected_data:', e);
    console.error('Falling back to empty object');
    collectedDataJson = '{}';
}

console.log('=== END PREPARE UPDATE DATA DEBUG ===');

// Return all necessary data for the update
return {
    phone_number: input.phone_number || '',
    next_stage: input.next_stage || input.current_state || 'greeting',
    collected_data_json: collectedDataJson,  // This should contain ALL data
    response_text: input.response_text || '',
    message: input.message || '',
    message_type: input.message_type || 'text',
    message_id: input.message_id || '',
    timestamp: input.timestamp || new Date().toISOString()
};'''

            fixes_applied.append("Prepare Update Data - Complete data preservation")
            print("✅ Fixed Prepare Update Data node")
            break

    # Fix 2: Update State Machine to ensure all data is preserved
    for node in workflow['nodes']:
        if node.get('id') == 'node_state_machine' and node.get('name') == 'State Machine Logic':
            print("📋 Fixing State Machine Logic for data accumulation...")

            code = node['parameters']['functionCode']

            # Find the section where updateData.error_count is set
            if "// Update error count\nupdateData.error_count = errorCount;" in code:
                code = code.replace(
                    "// Update error count\nupdateData.error_count = errorCount;",
                    """// Update error count and preserve ALL existing data
// CRITICAL: This ensures we never lose collected data
const preservedData = {
    ...stageData,      // Start with ALL existing data
    ...updateData,     // Apply new updates on top
    error_count: errorCount  // Ensure error_count is always current
};

// Final updateData contains everything
updateData = preservedData;

// Debug logging to verify data preservation
console.log('=== STATE MACHINE DATA PRESERVATION ===');
console.log('Original stageData:', stageData);
console.log('New updates:', updateData);
console.log('Final preservedData:', preservedData);
console.log('Data keys preserved:', Object.keys(preservedData));
console.log('=== END STATE MACHINE DEBUG ===');"""
                )
                node['parameters']['functionCode'] = code
                fixes_applied.append("State Machine - Data accumulation preservation")
                print("✅ Fixed State Machine Logic")
            else:
                print("⚠️  Could not find error_count update section in State Machine")
                # Add preservation logic at the end anyway
                return_section = code.rfind("return [")
                if return_section > 0:
                    insertion_point = return_section
                    preservation_code = """
// CRITICAL: Ensure all data is preserved before returning
updateData = {
    ...stageData,      // Keep ALL existing data
    ...updateData,     // Apply updates
    error_count: errorCount || 0  // Ensure error_count exists
};

console.log('Final updateData being returned:', updateData);

"""
                    code = code[:insertion_point] + preservation_code + code[insertion_point:]
                    node['parameters']['functionCode'] = code
                    fixes_applied.append("State Machine - Added data preservation before return")
                    print("✅ Added data preservation to State Machine")
            break

    # Fix 3: Verify Update Conversation State query
    for node in workflow['nodes']:
        if node.get('id') == 'node_update_conversation' and node.get('name') == 'Update Conversation State':
            print("📋 Checking Update Conversation State query...")

            current_query = node['parameters']['query']
            print(f"Current query: {current_query[:100]}...")

            # The query looks correct, but add COALESCE for safety
            if "collected_data = " in current_query and "COALESCE" not in current_query:
                node['parameters']['query'] = """UPDATE conversations
SET current_state = '{{ $json.next_stage }}',
    collected_data = COALESCE(
        NULLIF('{{ $json.collected_data_json }}', '')::jsonb,
        '{}'::jsonb
    ),
    updated_at = NOW()
WHERE phone_number = '{{ $json.phone_number }}'
RETURNING *"""
                fixes_applied.append("Update Conversation State - Added COALESCE safety")
                print("✅ Added COALESCE safety to Update query")
            break

    # Update workflow metadata
    workflow['versionId'] = 'v5-complete-data-preservation-fix'
    workflow['meta'] = workflow.get('meta', {})
    workflow['meta']['lastModified'] = datetime.now().isoformat()
    workflow['meta']['fixesApplied'] = fixes_applied

    # Save the fixed workflow
    output_path = '/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V1_MENU_FIXED_v5.json'

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Fixed workflow saved to: {output_path}")

    # Print summary
    print("\n📊 Summary of Fixes Applied:")
    for i, fix in enumerate(fixes_applied, 1):
        print(f"{i}. {fix}")

    print("\n📝 Next Steps:")
    print("1. Import the fixed workflow into n8n:")
    print(f"   - File: {output_path}")
    print("   - IMPORTANT: Deactivate the v3 workflow first!")
    print("   - Import and activate the v5 workflow")
    print("\n2. Test the complete fix:")
    print("   a. Send 'Oi' to start conversation")
    print("   b. Select service (1-5)")
    print("   c. Enter name, phone, email, city")
    print("   d. Check database after EACH step:")
    print("      docker exec e2bot-postgres-dev psql -U postgres -d e2_bot -c \"SELECT phone_number, current_state, jsonb_pretty(collected_data) FROM conversations WHERE phone_number='YOUR_NUMBER';\"")
    print("\n3. Verify ALL data is preserved:")
    print("   - error_count should be a number")
    print("   - All collected fields (name, phone, email, etc.) should persist")
    print("   - No data should be lost between steps")

    return output_path

def create_test_script():
    """
    Create a comprehensive test script to verify the fix works
    """
    test_script = '''#!/bin/bash
# Comprehensive test for collected_data preservation

echo "🧪 Testing collected_data preservation and types..."
echo "============================================"

# Test phone number
PHONE="5562981755485"

# Function to check database state
check_db() {
    echo ""
    echo "📊 Current collected_data for $PHONE:"
    docker exec e2bot-postgres-dev psql -U postgres -d e2_bot -c "
    SELECT
        phone_number,
        current_state,
        jsonb_pretty(collected_data) as collected_data,
        jsonb_typeof(collected_data->'error_count') as error_count_type,
        collected_data->'error_count' as error_count_value,
        collected_data->'lead_name' as lead_name,
        collected_data->'phone' as phone,
        collected_data->'email' as email,
        collected_data->'city' as city
    FROM conversations
    WHERE phone_number = '$PHONE';"
    echo "============================================"
}

# Main test sequence
echo "🔍 Checking initial state..."
check_db

echo ""
echo "✅ Expected results:"
echo "1. error_count_type should show 'number' not 'text'"
echo "2. All fields (lead_name, phone, email, city) should be preserved"
echo "3. No data should be lost between workflow steps"
echo ""
echo "❌ If data is missing or types are wrong, the fix didn't work properly"

# Optional: Clear test data
echo ""
read -p "Clear test data for fresh test? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    echo "🗑️  Clearing test data..."
    docker exec e2bot-postgres-dev psql -U postgres -d e2_bot -c "
    DELETE FROM conversations WHERE phone_number = '$PHONE';"
    echo "✅ Test data cleared. Ready for fresh test."
fi
'''

    test_path = '/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/scripts/test-complete-data-preservation.sh'

    with open(test_path, 'w') as f:
        f.write(test_script)

    import os
    os.chmod(test_path, 0o755)

    print(f"\n✅ Test script created: {test_path}")
    print("   Run it after importing the workflow to verify the fix")

if __name__ == "__main__":
    print("🔧 Fixing complete data loss and type preservation issues...")
    print("=" * 60)

    output_file = fix_workflow_complete()
    create_test_script()

    print("\n" + "=" * 60)
    print("✨ Complete fix applied! Follow the next steps above to test it.")
    print("\n⚠️  CRITICAL: This fix addresses:")
    print("   1. Type preservation (numbers stay numbers)")
    print("   2. Complete data preservation (no fields lost)")
    print("   3. Proper data accumulation across conversation steps")