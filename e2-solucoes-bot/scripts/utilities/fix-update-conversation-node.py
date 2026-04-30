#!/usr/bin/env python3
"""
Fix Update Conversation State node to:
1. Use correct variable (next_stage instead of new_state)
2. Update to typeVersion 2.5
3. Add alwaysOutputData: true to prevent workflow stopping
"""
import json

def fix_update_conversation_node():
    """
    Fix the Update Conversation State node to use correct data and always output data
    """

    # Read the workflow file
    with open('/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V1_MENU_FIXED.json', 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    # Find and fix the Update Conversation State node
    for node in workflow['nodes']:
        if node['id'] == 'node_update_conversation':
            print(f"Found Update Conversation State node, fixing...")

            # Fix the query to use next_stage from State Machine output
            node['parameters']['query'] = """UPDATE conversations
SET current_state = '{{ $json.next_stage }}',
    collected_data = '{{ JSON.stringify($json.collected_data) }}',
    updated_at = NOW()
WHERE phone_number = '{{ $json.phone_number }}'
RETURNING *"""

            # Update to newer typeVersion that handles empty results better
            node['typeVersion'] = 2.5

            # Add alwaysOutputData to ensure workflow continues even with no results
            node['alwaysOutputData'] = True

            # Also ensure options has queryBatching for better performance
            if 'options' not in node['parameters']:
                node['parameters']['options'] = {}
            node['parameters']['options']['queryBatching'] = 'independent'

            # Add credentials if missing
            if 'credentials' not in node:
                node['credentials'] = {
                    "postgres": {
                        "id": "1",
                        "name": "PostgreSQL E2"
                    }
                }

            print("✅ Fixed Update Conversation State node")
            break

    # Also fix the Save Inbound and Outbound Message nodes to use proper data references
    for node in workflow['nodes']:
        if node['id'] == 'node_save_inbound_message':
            # Update query to use State Machine output properly
            node['parameters']['query'] = """INSERT INTO messages (conversation_id, direction, content, message_type, whatsapp_message_id)
VALUES (
  (SELECT id FROM conversations WHERE phone_number = '{{ $json.phone_number }}' LIMIT 1),
  'inbound',
  '{{ ($json.message || "").replace(/'/g, "''") }}',
  '{{ $json.message_type || "text" }}',
  '{{ $json.message_id || "" }}'
) RETURNING *"""
            node['typeVersion'] = 2.5
            node['alwaysOutputData'] = True
            if 'options' not in node['parameters']:
                node['parameters']['options'] = {}
            node['parameters']['options']['queryBatching'] = 'independent'
            print("✅ Fixed Save Inbound Message node")

        elif node['id'] == 'node_save_outbound_message':
            # Update query to use State Machine output properly
            node['parameters']['query'] = """INSERT INTO messages (conversation_id, direction, content, message_type, whatsapp_message_id)
VALUES (
  (SELECT id FROM conversations WHERE phone_number = '{{ $json.phone_number }}' LIMIT 1),
  'outbound',
  '{{ ($json.response_text || "").replace(/'/g, "''") }}',
  'text',
  'out_{{ Date.now() }}'
) RETURNING *"""
            node['typeVersion'] = 2.5
            node['alwaysOutputData'] = True
            if 'options' not in node['parameters']:
                node['parameters']['options'] = {}
            node['parameters']['options']['queryBatching'] = 'independent'
            print("✅ Fixed Save Outbound Message node")

    # Save the fixed workflow
    output_file = '/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V1_MENU_FIXED_v2.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Fixed workflow saved to: {output_file}")
    print("\nKey fixes applied:")
    print("1. Update Conversation State now uses $json.next_stage (from State Machine)")
    print("2. Added collected_data JSON storage for state persistence")
    print("3. Updated all PostgreSQL nodes to typeVersion 2.5")
    print("4. Added alwaysOutputData: true to prevent workflow stopping")
    print("5. Fixed message saving nodes with proper null handling")

    return output_file

if __name__ == "__main__":
    fix_update_conversation_node()