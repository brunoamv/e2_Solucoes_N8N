#!/usr/bin/env python3
"""
Fix V25: Simplify Update Conversation State Query
Problem: V24 CTE-based UPSERT not saving to database
Solution: Use native PostgreSQL INSERT...ON CONFLICT
"""

import json
import sys
from pathlib import Path

def fix_update_conversation_query(js_code):
    """Replace complex CTE query with simplified UPSERT"""

    # Find the query_update_conversation section
    start_marker = "// Query 1: Update Conversation State"
    end_marker = "// Query 2: Save Inbound Message"

    start_idx = js_code.find(start_marker)
    end_idx = js_code.find(end_marker)

    if start_idx == -1 or end_idx == -1:
        print("Warning: Could not find query section markers")
        return js_code

    # Build the new simplified query
    new_query_section = """// Query 1: Update Conversation State (V25 SIMPLIFIED)
const query_update_conversation = `
-- V25: Simplified UPSERT with native PostgreSQL INSERT...ON CONFLICT
INSERT INTO conversations (
  phone_number,
  whatsapp_name,
  current_state,
  state_machine_state,
  collected_data,
  service_type,
  contact_name,
  contact_email,
  city,
  status,
  last_message_at,
  created_at,
  updated_at
) VALUES (
  '${phone_with_code}',
  '${escapeSql(collected_data?.lead_name || '')}',
  '${db_state}',
  '${next_stage}',
  '${collected_data_json}'::jsonb,
  ${collected_data?.service_type ? "'" + escapeSql(collected_data.service_type) + "'" : 'NULL'},
  '${escapeSql(collected_data?.lead_name || '')}',
  '${escapeSql(collected_data?.email || '')}',
  '${escapeSql(collected_data?.city || '')}',
  'active',
  NOW(),
  NOW(),
  NOW()
)
ON CONFLICT (phone_number)
DO UPDATE SET
  current_state = EXCLUDED.current_state,
  state_machine_state = EXCLUDED.state_machine_state,
  collected_data = EXCLUDED.collected_data,
  service_type = COALESCE(EXCLUDED.service_type, conversations.service_type),
  contact_name = COALESCE(NULLIF(EXCLUDED.contact_name, ''), conversations.contact_name),
  contact_email = COALESCE(NULLIF(EXCLUDED.contact_email, ''), conversations.contact_email),
  city = COALESCE(NULLIF(EXCLUDED.city, ''), conversations.city),
  whatsapp_name = COALESCE(NULLIF(EXCLUDED.whatsapp_name, ''), conversations.whatsapp_name),
  last_message_at = NOW(),
  updated_at = NOW()
RETURNING *`.trim();

console.log('✅ V25: Simplified UPSERT query built');
console.log('Query length:', query_update_conversation.length);

"""

    # Replace the section
    new_js_code = js_code[:start_idx] + new_query_section + js_code[end_idx:]

    # Also update the debug message
    new_js_code = new_js_code.replace(
        "console.log('=== V21 BUILD UPDATE QUERIES DEBUG ===');",
        "console.log('=== V25 BUILD UPDATE QUERIES DEBUG (SIMPLIFIED) ===');"
    )
    new_js_code = new_js_code.replace(
        "console.log('=== V21 QUERY BUILDING ===');",
        "console.log('=== V25 QUERY BUILDING (SIMPLIFIED) ===');"
    )
    new_js_code = new_js_code.replace(
        "console.log('✅ V21: All queries built successfully as pure SQL strings');",
        "console.log('✅ V25: All queries built with simplified UPSERT');"
    )

    return new_js_code

def main():
    # Load V24 workflow
    v24_path = Path('n8n/workflows/02_ai_agent_conversation_V24.json')
    if not v24_path.exists():
        print(f"Error: {v24_path} not found")
        sys.exit(1)

    with open(v24_path, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    # Update workflow name
    workflow['name'] = 'AI Agent Conversation - V25 (Simplified UPSERT)'

    # Find and fix Build Update Queries node
    fixed = False
    for node in workflow['nodes']:
        if node.get('name') == 'Build Update Queries':
            print(f"Found Build Update Queries node: {node['id']}")

            # Fix the JavaScript code
            original_code = node['parameters']['jsCode']
            fixed_code = fix_update_conversation_query(original_code)
            node['parameters']['jsCode'] = fixed_code

            fixed = True
            print("✅ Fixed Build Update Queries node with simplified UPSERT")
            break

    if not fixed:
        print("Error: Could not find Build Update Queries node")
        sys.exit(1)

    # Ensure Update Conversation State node has correct settings
    for node in workflow['nodes']:
        if node.get('name') == 'Update Conversation State':
            # Ensure it always outputs data
            node['alwaysOutputData'] = True
            # Ensure query batching is set correctly
            if 'options' not in node['parameters']:
                node['parameters']['options'] = {}
            node['parameters']['options']['queryBatching'] = 'independent'
            print("✅ Updated Update Conversation State node settings")

    # Save as V25
    v25_path = Path('n8n/workflows/02_ai_agent_conversation_V25_SIMPLIFIED_UPSERT.json')
    with open(v25_path, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Created V25 workflow: {v25_path}")
    print("\n📋 Next steps:")
    print("1. Import V25 workflow into n8n")
    print("2. Deactivate V24 workflow")
    print("3. Activate V25 workflow")
    print("4. Test with WhatsApp message")
    print("5. Verify database updates with:")
    print("   docker exec e2bot-postgres-dev psql -U postgres -d e2_bot \\")
    print("     -c \"SELECT phone_number, state_machine_state, last_message_at, updated_at\"")
    print("        FROM conversations WHERE phone_number LIKE '%6181755748%';\"")

if __name__ == '__main__':
    main()