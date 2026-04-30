#!/usr/bin/env python3
"""
Fix workflow V14 - Resolve query discrepancy by pre-processing phone numbers
Problem: n8n doesn't execute JavaScript within SQL templates
Solution: Add dedicated Code node to prepare both phone formats before SQL queries
"""

import json

# Read the V13 workflow
with open('/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V13.json', 'r') as f:
    workflow = json.load(f)

print("🔍 Analyzing V13 Query Problem...")
print("   - Issue: JavaScript String().replace() not evaluated in SQL templates")
print("   - Impact: Queries return 0 instead of 1")
print("   - Solution: Pre-process phone formats in Code node")

# Add new Code node after Validate Input Data to prepare phone formats
prepare_phone_formats_node = {
    "parameters": {
        "jsCode": """// Prepare both phone formats for SQL queries
const inputData = $input.first().json;

// Get the phone number from validation
const phone_with_code = String(inputData.phone_number || '');

// Create version without country code for compatibility
let phone_without_code = phone_with_code;
if (phone_with_code.startsWith('55')) {
    phone_without_code = phone_with_code.substring(2);
}

console.log('=== PHONE FORMAT PREPARATION ===');
console.log('With code (55):', phone_with_code);
console.log('Without code:', phone_without_code);

// Return both formats and pass through all other data
return {
    ...inputData, // Pass through all original data
    phone_with_code: phone_with_code,      // e.g., "556181755748"
    phone_without_code: phone_without_code, // e.g., "6181755748"
    // Keep original for compatibility
    phone_number: phone_with_code
};"""
    },
    "id": "prepare-phone-formats",
    "name": "Prepare Phone Formats",
    "type": "n8n-nodes-base.code",
    "typeVersion": 2,
    "position": [-950, 200]
}

# Insert the new node into the workflow
workflow['nodes'].insert(2, prepare_phone_formats_node)

# Update Get Conversation Count to use pre-processed variables
for node in workflow['nodes']:
    if node['name'] == 'Get Conversation Count':
        print("🔧 Updating Get Conversation Count...")

        # Use pre-processed variables instead of JavaScript expressions
        node['parameters']['query'] = """-- Query using pre-processed phone formats
SELECT COUNT(*) as count
FROM conversations
WHERE phone_number IN (
  '{{ $node["Prepare Phone Formats"].json.phone_with_code }}',
  '{{ $node["Prepare Phone Formats"].json.phone_without_code }}'
);"""

        print("   ✅ Query updated to use pre-processed variables")
        break

# Update Get Conversation Details similarly
for node in workflow['nodes']:
    if node['name'] == 'Get Conversation Details':
        print("🔧 Updating Get Conversation Details...")

        node['parameters']['query'] = """-- Query using pre-processed phone formats
SELECT
  *,
  -- Return the correct state for the State Machine
  COALESCE(state_machine_state,
    CASE current_state
      WHEN 'novo' THEN 'greeting'
      WHEN 'identificando_servico' THEN 'service_selection'
      WHEN 'coletando_dados' THEN 'collect_name'
      WHEN 'agendando' THEN 'scheduling'
      WHEN 'handoff_comercial' THEN 'handoff_comercial'
      WHEN 'concluido' THEN 'completed'
      ELSE 'greeting'
    END
  ) as state_for_machine
FROM conversations
WHERE phone_number IN (
  '{{ $node["Prepare Phone Formats"].json.phone_with_code }}',
  '{{ $node["Prepare Phone Formats"].json.phone_without_code }}'
)
ORDER BY updated_at DESC
LIMIT 1;"""

        print("   ✅ Query updated to use pre-processed variables")
        break

# Update Create New Conversation to use pre-processed formats
for node in workflow['nodes']:
    if node['name'] == 'Create New Conversation':
        print("🔧 Updating Create New Conversation...")

        node['parameters']['query'] = """-- First, clean possible old duplicates without code 55
DELETE FROM conversations
WHERE phone_number = '{{ $node["Prepare Phone Formats"].json.phone_without_code }}'
  AND phone_number != '{{ $node["Prepare Phone Formats"].json.phone_with_code }}';

-- Now insert or update the conversation
INSERT INTO conversations (
  phone_number,
  whatsapp_name,
  current_state,       -- Database field with constraint
  state_machine_state,  -- New field for bot state
  created_at,
  updated_at
)
VALUES (
  '{{ $node["Prepare Phone Formats"].json.phone_with_code }}',
  '{{ $node["Prepare Phone Formats"].json.whatsapp_name }}',
  'novo',     -- ✅ Valid value for current_state
  'greeting',  -- ✅ State machine state
  NOW(),
  NOW()
)
ON CONFLICT (phone_number)
DO UPDATE SET
  whatsapp_name = EXCLUDED.whatsapp_name,
  updated_at = NOW(),
  current_state = CASE
    WHEN conversations.current_state = 'concluido' THEN 'novo'
    ELSE conversations.current_state
  END,
  state_machine_state = CASE
    WHEN conversations.state_machine_state = 'completed' THEN 'greeting'
    ELSE conversations.state_machine_state
  END
RETURNING *;"""

        print("   ✅ Query updated to use pre-processed variables")
        break

# Update connections to route through the new node
print("🔧 Updating workflow connections...")

# Validate Input Data now connects to Prepare Phone Formats
workflow['connections']['Validate Input Data'] = {
    "main": [[{
        "node": "Prepare Phone Formats",
        "type": "main",
        "index": 0
    }]]
}

# Prepare Phone Formats connects to Get Conversation Count
workflow['connections']['Prepare Phone Formats'] = {
    "main": [[{
        "node": "Get Conversation Count",
        "type": "main",
        "index": 0
    }]]
}

print("   ✅ Connections updated")

# Update workflow metadata
workflow['name'] = "02 - AI Agent Conversation V14 (Query Preprocessing Fix)"
workflow['versionId'] = "v14-query-preprocessing-fix"

# Save the new workflow
output_path = '/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V14.json'
with open(output_path, 'w') as f:
    json.dump(workflow, f, indent=2, ensure_ascii=False)

print("\n✅ Workflow V14 created successfully!")
print(f"📄 File: {output_path}")

print("\n🔄 Key Changes:")
print("1. ✅ Added 'Prepare Phone Formats' Code node")
print("2. ✅ Pre-processes both phone formats (with/without 55)")
print("3. ✅ SQL queries now use pre-processed variables")
print("4. ✅ No JavaScript expressions in SQL templates")
print("5. ✅ Clean variable interpolation that n8n can process")

print("\n📋 How it works:")
print("1. Validate Input Data → validates and formats phone")
print("2. Prepare Phone Formats → creates both versions")
print("3. SQL nodes → use simple variable references")
print("4. n8n properly interpolates the values")
print("5. Queries work correctly!")

print("\n🎯 Expected Result:")
print("- Get Conversation Count will return 1")
print("- Get Conversation Details will find the record")
print("- State machine will process user input correctly")

print("\n🧪 Test SQL that will be generated:")
print("""
WHERE phone_number IN (
  '556181755748',    -- from phone_with_code
  '6181755748'       -- from phone_without_code
)
""")

print("\n✨ Ready to import into n8n!")