#!/usr/bin/env python3
"""
Fix collected_data handling in Update Conversation State node.
The problem is that JSON.stringify() is being used directly in the SQL query,
which can fail if the object has undefined values or special characters.
"""
import json

def fix_collected_data_handling():
    """
    Fix the collected_data handling by:
    1. Using a Code node to properly stringify the data
    2. Handling null/undefined values
    3. Escaping special characters properly
    """

    # Read the workflow file
    with open('/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V1_MENU_FIXED_v2.json', 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    # First, add a new Code node to properly handle collected_data
    prepare_data_node = {
        "parameters": {
            "jsCode": """// Prepare data for database update
const input = $input.first().json;

// Safely handle collected_data
let collectedData = input.collected_data || {};

// Ensure collected_data is a valid object
if (typeof collectedData !== 'object' || collectedData === null) {
    collectedData = {};
}

// Remove undefined values and ensure all values are strings or primitives
const cleanedData = {};
for (const [key, value] of Object.entries(collectedData)) {
    if (value !== undefined && value !== null) {
        // Convert to string if needed
        cleanedData[key] = typeof value === 'object' ? JSON.stringify(value) : String(value);
    }
}

// Safely stringify the cleaned data
let collectedDataJson = '{}';
try {
    collectedDataJson = JSON.stringify(cleanedData);
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
};"""
        },
        "id": "node_prepare_update_data",
        "name": "Prepare Update Data",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [1150, 300]
    }

    # Insert the new node after State Machine Logic
    nodes_to_add = []
    for i, node in enumerate(workflow['nodes']):
        if node['id'] == 'node_state_machine':
            # Insert the new node after State Machine
            workflow['nodes'].insert(i + 1, prepare_data_node)
            break

    # Update the Update Conversation State node to use prepared data
    for node in workflow['nodes']:
        if node['id'] == 'node_update_conversation':
            # Update the query to use the pre-processed JSON string
            node['parameters']['query'] = """UPDATE conversations
SET current_state = '{{ $json.next_stage }}',
    collected_data = '{{ $json.collected_data_json }}'::jsonb,
    updated_at = NOW()
WHERE phone_number = '{{ $json.phone_number }}'
RETURNING *"""

            # Ensure it has the correct settings
            node['typeVersion'] = 2.5
            node['alwaysOutputData'] = True

            if 'options' not in node['parameters']:
                node['parameters']['options'] = {}
            node['parameters']['options']['queryBatching'] = 'independent'

            print("✅ Fixed Update Conversation State node")

    # Update connections to go through the new Prepare Data node
    if 'State Machine Logic' in workflow['connections']:
        # Change State Machine to connect to Prepare Update Data
        workflow['connections']['State Machine Logic'] = {
            "main": [[{
                "node": "Prepare Update Data",
                "type": "main",
                "index": 0
            }]]
        }

        # Add connection from Prepare Update Data to Update Conversation State
        workflow['connections']['Prepare Update Data'] = {
            "main": [[{
                "node": "Update Conversation State",
                "type": "main",
                "index": 0
            }]]
        }

        print("✅ Updated workflow connections")

    # Also fix the message saving nodes to use the prepared data
    for node in workflow['nodes']:
        if node['id'] == 'node_save_inbound_message':
            node['parameters']['query'] = """INSERT INTO messages (conversation_id, direction, content, message_type, whatsapp_message_id)
VALUES (
  (SELECT id FROM conversations WHERE phone_number = '{{ $node["Prepare Update Data"].json.phone_number }}' LIMIT 1),
  'inbound',
  '{{ ($node["Prepare Update Data"].json.message || "").replace(/'/g, "''") }}',
  '{{ $node["Prepare Update Data"].json.message_type || "text" }}',
  '{{ $node["Prepare Update Data"].json.message_id || "" }}'
)
ON CONFLICT DO NOTHING
RETURNING *"""
            node['alwaysOutputData'] = True
            print("✅ Fixed Save Inbound Message node")

        elif node['id'] == 'node_save_outbound_message':
            node['parameters']['query'] = """INSERT INTO messages (conversation_id, direction, content, message_type, whatsapp_message_id)
VALUES (
  (SELECT id FROM conversations WHERE phone_number = '{{ $node["Prepare Update Data"].json.phone_number }}' LIMIT 1),
  'outbound',
  '{{ ($node["Prepare Update Data"].json.response_text || "").replace(/'/g, "''") }}',
  'text',
  'out_{{ Date.now() }}'
)
ON CONFLICT DO NOTHING
RETURNING *"""
            node['alwaysOutputData'] = True
            print("✅ Fixed Save Outbound Message node")

    # Fix the Upsert Lead Data node to handle collected_data properly
    for node in workflow['nodes']:
        if node['id'] == 'node_upsert_lead':
            # Use the prepared data for lead upsert
            node['parameters']['operation'] = 'executeQuery'
            node['parameters']['query'] = """INSERT INTO leads (whatsapp_number, lead_name, phone, email, city, service_type, stage, collected_data, created_at, updated_at)
VALUES (
  '{{ $node["Prepare Update Data"].json.phone_number }}',
  '{{ $node["Prepare Update Data"].json.collected_data_json | jsonParse.lead_name || "" }}',
  '{{ $node["Prepare Update Data"].json.collected_data_json | jsonParse.phone || "" }}',
  '{{ $node["Prepare Update Data"].json.collected_data_json | jsonParse.email || "" }}',
  '{{ $node["Prepare Update Data"].json.collected_data_json | jsonParse.city || "" }}',
  '{{ $node["Prepare Update Data"].json.collected_data_json | jsonParse.service_type || "" }}',
  '{{ $node["Prepare Update Data"].json.next_stage }}',
  '{{ $node["Prepare Update Data"].json.collected_data_json }}'::jsonb,
  NOW(),
  NOW()
)
ON CONFLICT (whatsapp_number)
DO UPDATE SET
  lead_name = EXCLUDED.lead_name,
  phone = EXCLUDED.phone,
  email = EXCLUDED.email,
  city = EXCLUDED.city,
  service_type = EXCLUDED.service_type,
  stage = EXCLUDED.stage,
  collected_data = EXCLUDED.collected_data,
  updated_at = NOW()
RETURNING *"""

            # Remove the old parameters
            if 'table' in node['parameters']:
                del node['parameters']['table']
            if 'updateKey' in node['parameters']:
                del node['parameters']['updateKey']
            if 'columns' in node['parameters']:
                del node['parameters']['columns']
            if 'values' in node['parameters']:
                del node['parameters']['values']

            node['typeVersion'] = 2.5
            node['alwaysOutputData'] = True

            print("✅ Fixed Upsert Lead Data node")

    # Save the fixed workflow
    output_file = '/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V1_MENU_FIXED_v3.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Fixed workflow saved to: {output_file}")
    print("\nKey fixes applied:")
    print("1. Added 'Prepare Update Data' node to properly handle collected_data")
    print("2. Safely stringify collected_data with null/undefined handling")
    print("3. Use ::jsonb casting for proper PostgreSQL JSONB storage")
    print("4. Fixed message saving nodes to use prepared data")
    print("5. Fixed lead upsert to properly handle JSON data")
    print("6. Added ON CONFLICT DO NOTHING to prevent duplicate errors")
    print("\n📝 IMPORTANT: The collected_data column in PostgreSQL must be of type JSONB!")

    return output_file

if __name__ == "__main__":
    fix_collected_data_handling()