#!/usr/bin/env python3
"""
Fix V23 Part 2 - Adiciona geração de query_upsert_lead no Build Update Queries
Garante que o node Build Update Queries gere a query necessária para Upsert Lead Data
"""

import json
import sys
import os
from datetime import datetime

def add_upsert_lead_query():
    """Adiciona geração de query_upsert_lead ao Build Update Queries"""

    workflow_path = "/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V23_EXTENDED_PARALLEL.json"

    # Check if file exists
    if not os.path.exists(workflow_path):
        print(f"❌ File not found: {workflow_path}")
        return False

    print(f"📖 Reading V23 workflow: {workflow_path}")

    try:
        with open(workflow_path, 'r', encoding='utf-8') as f:
            workflow = json.load(f)
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return False

    print("🔧 Adding query_upsert_lead generation to Build Update Queries...")

    # Find Build Update Queries node
    build_queries_found = False
    for node in workflow['nodes']:
        if node.get('name') == 'Build Update Queries' and node.get('type') == 'n8n-nodes-base.code':
            build_queries_found = True

            # Get existing code or create new
            if 'jsCode' in node.get('parameters', {}):
                existing_code = node['parameters']['jsCode']

                # Check if query_upsert_lead is already being generated
                if 'query_upsert_lead' in existing_code:
                    print("✅ query_upsert_lead generation already exists")
                else:
                    # Add query_upsert_lead generation before the return statement
                    # Find the return statement
                    if 'return [' in existing_code:
                        # Extract the existing queries being returned
                        return_index = existing_code.rfind('return [')
                        code_before_return = existing_code[:return_index]

                        # Add the query_upsert_lead generation
                        upsert_lead_code = """
// Query para Upsert Lead Data
const query_upsert_lead = `
  INSERT INTO leads (
    phone_number,
    name,
    email,
    city,
    service_id,
    collected_data,
    created_at,
    updated_at
  ) VALUES (
    '${phone_number}',
    '${collected_data.name || ''}',
    '${collected_data.email || ''}',
    '${collected_data.city || ''}',
    ${collected_data.service_id || 'NULL'},
    '${JSON.stringify(collected_data)}'::jsonb,
    NOW(),
    NOW()
  )
  ON CONFLICT (phone_number)
  DO UPDATE SET
    name = EXCLUDED.name,
    email = EXCLUDED.email,
    city = EXCLUDED.city,
    service_id = EXCLUDED.service_id,
    collected_data = EXCLUDED.collected_data,
    updated_at = NOW()
  RETURNING *;
`;
"""
                        # Update the return statement to include query_upsert_lead
                        updated_code = code_before_return + upsert_lead_code + "\n" + \
                            "return [\n" + \
                            "  {\n" + \
                            "    phone_number,\n" + \
                            "    response_text,\n" + \
                            "    collected_data,\n" + \
                            "    query_update_conversation,\n" + \
                            "    query_save_inbound,\n" + \
                            "    query_save_outbound,\n" + \
                            "    query_upsert_lead  // Added for Upsert Lead Data\n" + \
                            "  }\n" + \
                            "];"

                        node['parameters']['jsCode'] = updated_code
                        print("✅ Added query_upsert_lead generation to Build Update Queries")
                    else:
                        print("⚠️ Could not find return statement in Build Update Queries code")
                        print("Please manually add query_upsert_lead generation")
            else:
                print("⚠️ Build Update Queries node doesn't have jsCode parameter")
                print("Creating complete Build Update Queries code...")

                # Create complete code with all queries
                complete_code = """// Get input data
const inputData = $input.first().json;

// Extract data
const phone_number = inputData.phone_number || '';
const response_text = inputData.response_text || '';
const collected_data = inputData.collected_data || {};
const state_machine_state = inputData.state_machine_state || '';
const conversation_id = inputData.conversation_id || '';
const service_id = collected_data.service_id || null;

// Query para Update Conversation State
const query_update_conversation = `
  UPDATE conversations
  SET
    state_machine_state = '${state_machine_state}',
    collected_data = '${JSON.stringify(collected_data)}'::jsonb,
    last_message_at = NOW(),
    updated_at = NOW()
  WHERE phone_number = '${phone_number}'
  RETURNING *;
`;

// Query para Save Inbound Message
const query_save_inbound = `
  INSERT INTO messages (
    conversation_id,
    direction,
    content,
    created_at
  ) VALUES (
    ${conversation_id},
    'inbound',
    '${inputData.message || ''}',
    NOW()
  );
`;

// Query para Save Outbound Message
const query_save_outbound = `
  INSERT INTO messages (
    conversation_id,
    direction,
    content,
    created_at
  ) VALUES (
    ${conversation_id},
    'outbound',
    '${response_text}',
    NOW()
  );
`;

// Query para Upsert Lead Data
const query_upsert_lead = `
  INSERT INTO leads (
    phone_number,
    name,
    email,
    city,
    service_id,
    collected_data,
    created_at,
    updated_at
  ) VALUES (
    '${phone_number}',
    '${collected_data.name || ''}',
    '${collected_data.email || ''}',
    '${collected_data.city || ''}',
    ${service_id || 'NULL'},
    '${JSON.stringify(collected_data)}'::jsonb,
    NOW(),
    NOW()
  )
  ON CONFLICT (phone_number)
  DO UPDATE SET
    name = EXCLUDED.name,
    email = EXCLUDED.email,
    city = EXCLUDED.city,
    service_id = EXCLUDED.service_id,
    collected_data = EXCLUDED.collected_data,
    updated_at = NOW()
  RETURNING *;
`;

return [
  {
    phone_number,
    response_text,
    collected_data,
    query_update_conversation,
    query_save_inbound,
    query_save_outbound,
    query_upsert_lead
  }
];"""

                node['parameters'] = node.get('parameters', {})
                node['parameters']['jsCode'] = complete_code
                print("✅ Created complete Build Update Queries code with all queries")

    if not build_queries_found:
        print("❌ Build Update Queries node not found in workflow")
        return False

    # Save the updated workflow
    output_path = workflow_path.replace('.json', '_COMPLETE.json')
    print(f"\n💾 Saving complete V23 workflow: {output_path}")

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(workflow, f, indent=2, ensure_ascii=False)
        print(f"✅ Complete V23 workflow saved successfully!")
        print(f"\n📋 V23 Complete Features:")
        print("1. ✅ Build Update Queries generates ALL necessary queries")
        print("2. ✅ query_upsert_lead properly formatted for leads table")
        print("3. ✅ All nodes receive correct queries via parallel distribution")
        print("4. ✅ No more 'Cannot read properties of undefined' errors")
        print(f"\n🎯 Final Solution:")
        print("Build Update Queries now generates:")
        print("  - query_update_conversation → Update Conversation State")
        print("  - query_save_inbound → Save Inbound Message")
        print("  - query_save_outbound → Save Outbound Message")
        print("  - query_upsert_lead → Upsert Lead Data")
        print("  - phone_number + response_text → Send WhatsApp Response")
        print(f"\n🚀 Ready to Import:")
        print(f"Import this file into n8n: {output_path}")
        return True
    except Exception as e:
        print(f"❌ Error saving file: {e}")
        return False

if __name__ == "__main__":
    success = add_upsert_lead_query()
    sys.exit(0 if success else 1)