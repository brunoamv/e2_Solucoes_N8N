#!/usr/bin/env python3
"""
Fix collected_data type preservation in Prepare Update Data node
Preserves numbers, booleans, and null values instead of converting everything to strings
"""
import json
import sys
from datetime import datetime

def fix_prepare_update_data():
    """
    Fix the Prepare Update Data node to preserve data types instead of converting to strings
    """

    # Read workflow file
    workflow_path = '/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V1_MENU_FIXED_v3.json'

    try:
        with open(workflow_path, 'r', encoding='utf-8') as f:
            workflow = json.load(f)
    except FileNotFoundError:
        print(f"❌ Workflow file not found: {workflow_path}")
        sys.exit(1)

    # Find and fix Prepare Update Data node
    node_found = False
    for node in workflow['nodes']:
        if node.get('id') == 'node_prepare_update_data' and node.get('name') == 'Prepare Update Data':
            print("📋 Found Prepare Update Data node")

            # Update the JavaScript code to preserve types
            node['parameters']['jsCode'] = '''// Prepare data for database update with type preservation
const input = $input.first().json;

// Safely handle collected_data
let collectedData = input.collected_data || {};

// Ensure collected_data is a valid object
if (typeof collectedData !== 'object' || collectedData === null) {
    collectedData = {};
}

// Clean data PRESERVING TYPES
const cleanedData = {};
for (const [key, value] of Object.entries(collectedData)) {
    if (value !== undefined) {
        // CRITICAL: Preserve native types
        if (value === null) {
            cleanedData[key] = null;
        } else if (typeof value === 'number') {
            cleanedData[key] = value;  // Keep as number
        } else if (typeof value === 'boolean') {
            cleanedData[key] = value;  // Keep as boolean
        } else if (typeof value === 'string') {
            cleanedData[key] = value;  // Keep as string
        } else if (typeof value === 'object') {
            cleanedData[key] = value;  // Keep object (will be stringified by JSON.stringify)
        } else {
            // Only convert unknown types to string
            cleanedData[key] = String(value);
        }
    }
}

// Log for debugging
console.log('Cleaned data with preserved types:', cleanedData);

// Safely stringify the cleaned data
let collectedDataJson = '{}';
try {
    collectedDataJson = JSON.stringify(cleanedData);
    console.log('Stringified JSON:', collectedDataJson);
} catch (e) {
    console.error('Error stringifying collected_data:', e);
    collectedDataJson = '{}';
}

// Return all necessary data for the update
return {
    phone_number: input.phone_number || '',
    next_stage: input.next_stage || input.current_state || 'greeting',
    collected_data_json: collectedDataJson,
    response_text: input.response_text || '',
    message: input.message || '',
    message_type: input.message_type || 'text',
    message_id: input.message_id || '',
    timestamp: input.timestamp || new Date().toISOString()
};'''

            node_found = True
            print("✅ Updated Prepare Update Data node code")
            break

    if not node_found:
        print("❌ Prepare Update Data node not found in workflow")
        sys.exit(1)

    # Also check if State Machine Logic needs improvement
    for node in workflow['nodes']:
        if node.get('id') == 'node_state_machine' and node.get('name') == 'State Machine Logic':
            print("📋 Found State Machine Logic node")

            # Check if we need to add type parsing logic
            current_code = node['parameters'].get('functionCode', '')

            # Add type safety check at the beginning of conversation data handling
            if 'typeof conversation.collected_data === \'string\'' not in current_code:
                print("⚠️  State Machine Logic might need type parsing update")
                print("   Consider adding JSON.parse for string collected_data")

    # Update workflow metadata
    workflow['versionId'] = 'v4-type-preservation-fix'
    workflow['meta'] = workflow.get('meta', {})
    workflow['meta']['lastModified'] = datetime.now().isoformat()
    workflow['meta']['fixApplied'] = 'collected_data_type_preservation'

    # Save the fixed workflow
    output_path = '/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V1_MENU_FIXED_v4.json'

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Fixed workflow saved to: {output_path}")

    # Print summary
    print("\n📊 Summary of Changes:")
    print("1. Prepare Update Data node now preserves data types:")
    print("   - Numbers remain as numbers (error_count: 0, not \"0\")")
    print("   - Booleans remain as booleans (wants_appointment: true, not \"true\")")
    print("   - Null values remain as null (not empty strings)")
    print("   - Strings remain as strings")
    print("\n2. This fixes the error_count always resetting to 0 issue")

    # Print next steps
    print("\n📝 Next Steps:")
    print("1. Import the fixed workflow into n8n:")
    print(f"   - File: {output_path}")
    print("   - Delete or deactivate the old workflow")
    print("   - Import and activate the new one")
    print("\n2. Test the fix:")
    print("   - Send 'Oi' to start conversation")
    print("   - Send invalid option '9' (should increment error_count)")
    print("   - Check database: SELECT collected_data FROM conversations WHERE phone_number='YOUR_NUMBER';")
    print("   - Verify error_count is 1 (number) not \"1\" (string)")

    return output_path

def create_test_script():
    """
    Create a test script to verify the fix works
    """
    test_script = '''#!/bin/bash
# Test script to verify collected_data type preservation

echo "🧪 Testing collected_data type preservation..."

# Get a test phone number
PHONE="5562981755485"

# Check current state in database
echo "📊 Current collected_data for $PHONE:"
docker exec e2bot-postgres-dev psql -U postgres -d e2_bot -c "
SELECT
    phone_number,
    current_state,
    collected_data,
    jsonb_typeof(collected_data->'error_count') as error_count_type,
    collected_data->'error_count' as error_count_value
FROM conversations
WHERE phone_number = '$PHONE';"

echo ""
echo "✅ If error_count_type shows 'number', the fix is working!"
echo "❌ If error_count_type shows 'text' or null, the fix didn't work."
'''

    test_path = '/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/scripts/test-collected-data-types.sh'

    with open(test_path, 'w') as f:
        f.write(test_script)

    import os
    os.chmod(test_path, 0o755)

    print(f"\n✅ Test script created: {test_path}")
    print("   Run it after importing the workflow to verify the fix")

if __name__ == "__main__":
    print("🔧 Fixing collected_data type preservation issue...")
    print("=" * 60)

    output_file = fix_prepare_update_data()
    create_test_script()

    print("\n" + "=" * 60)
    print("✨ Fix complete! Follow the next steps above to apply it.")