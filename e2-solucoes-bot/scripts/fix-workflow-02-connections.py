#!/usr/bin/env python3
"""
Fix Workflow 02 connections to ensure Execute Workflow Trigger goes through Validate Input Data
"""
import json
import sys

def fix_workflow_connections():
    """
    Fix the connection flow to ensure phone_number is properly extracted
    """

    # Read the workflow file
    with open('/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V1_MENU_COMPLETE_REFACTOR.json', 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    # Fix the connections section
    # Current wrong connection: Execute Workflow Trigger → Get Conversation Count
    # Should be: Execute Workflow Trigger → Validate Input Data → Get Conversation Count

    # Update connections
    workflow['connections']['Execute Workflow Trigger'] = {
        "main": [
            [
                {
                    "node": "Validate Input Data",
                    "type": "main",
                    "index": 0
                }
            ]
        ]
    }

    # Add connection from Validate Input Data to Get Conversation Count
    workflow['connections']['Validate Input Data'] = {
        "main": [
            [
                {
                    "node": "Get Conversation Count",
                    "type": "main",
                    "index": 0
                }
            ]
        ]
    }

    # Also update the Create New Conversation query to use the validated phone_number
    for node in workflow['nodes']:
        if node['id'] == 'node_create_conversation':
            # Fix the query to get phone_number from the Validate Input Data node
            node['parameters']['query'] = """INSERT INTO conversations (phone_number, whatsapp_name, current_state, created_at, updated_at)
VALUES ('{{ $node["Validate Input Data"].json.phone_number }}', '{{ $node["Validate Input Data"].json.whatsapp_name }}', 'novo', NOW(), NOW())
ON CONFLICT (phone_number)
DO UPDATE SET
  whatsapp_name = EXCLUDED.whatsapp_name,
  updated_at = NOW(),
  current_state = CASE
    WHEN conversations.current_state = 'concluido' THEN 'novo'
    ELSE conversations.current_state
  END
RETURNING *"""

        # Also fix Get Conversation Count to use validated data
        elif node['id'] == 'node_get_conversation':
            node['parameters']['query'] = "SELECT COUNT(*) as count FROM conversations WHERE phone_number = '{{ $node[\"Validate Input Data\"].json.phone_number }}';"

        # Fix Get Conversation Details
        elif node['id'] == 'node_get_conversation_details':
            node['parameters']['query'] = "SELECT * FROM conversations WHERE phone_number = '{{ $node[\"Validate Input Data\"].json.phone_number }}' ORDER BY updated_at DESC LIMIT 1;"

    # Save the fixed workflow
    output_file = '/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V1_MENU_FIXED.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print(f"✅ Fixed workflow saved to: {output_file}")
    print("\nKey fixes applied:")
    print("1. Execute Workflow Trigger → Validate Input Data → Get Conversation Count")
    print("2. Create New Conversation now uses $node[\"Validate Input Data\"].json.phone_number")
    print("3. Get Conversation queries now reference validated phone_number")

    return output_file

if __name__ == "__main__":
    fix_workflow_connections()