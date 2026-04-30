#!/usr/bin/env python3
"""
Fix V20 - Corrige problema de queries SQL não sendo processadas
O problema: Update Conversation State não está executando porque as template strings {{ }}
não estão sendo processadas antes de chegar ao PostgreSQL
Solução: Criar node intermediário que prepara todas as queries SQL como strings puras
"""

import json
import sys
import os
from datetime import datetime

def create_v20_workflow():
    """Cria V20 com queries SQL preparadas corretamente"""

    workflow_path = "/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V19.json"

    # Check if file exists
    if not os.path.exists(workflow_path):
        print(f"❌ File not found: {workflow_path}")
        return False

    print(f"📖 Reading V19 workflow: {workflow_path}")

    try:
        with open(workflow_path, 'r', encoding='utf-8') as f:
            workflow = json.load(f)
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return False

    print("🔧 Creating V20 with fixed query processing...")

    # 1. Create the Build Update Queries node
    build_update_queries_node = {
        "parameters": {
            "jsCode": """// Build Update Queries - Prepara todas as queries SQL como strings puras
const inputData = $input.first().json;

// Função helper para escapar SQL
const escapeSql = (str) => {
  if (str === null || str === undefined || str === '') return '';
  return String(str).replace(/'/g, "''");
};

// Função para preparar JSON para PostgreSQL
const prepareJsonb = (obj) => {
  if (!obj || typeof obj !== 'object') return '{}';
  return JSON.stringify(obj).replace(/'/g, "''");
};

// Extrair dados necessários
const phone_with_code = inputData.phone_with_code || inputData.phone_number || '';
const phone_without_code = inputData.phone_without_code || phone_with_code.replace(/^55/, '') || '';
const response_text = escapeSql(inputData.response_text || 'Olá! Como posso ajudar?');
const next_stage = inputData.next_stage || 'greeting';
const collected_data_json = prepareJsonb(inputData.collected_data || {});
const message_content = escapeSql(inputData.message || inputData.content || '');
const message_type = inputData.message_type || 'text';
const message_id = inputData.message_id || '';
const conversation_id = inputData.conversation_id || null;

// Mapear estados para o banco
const state_mapping = {
  'greeting': 'novo',
  'service_selection': 'identificando_servico',
  'collect_name': 'coletando_dados',
  'collect_phone': 'coletando_dados',
  'collect_email': 'coletando_dados',
  'collect_city': 'coletando_dados',
  'confirmation': 'coletando_dados',
  'scheduling': 'agendando',
  'handoff_comercial': 'handoff_comercial',
  'completed': 'concluido'
};

const db_state = state_mapping[next_stage] || 'novo';

console.log('=== BUILD UPDATE QUERIES DEBUG ===');
console.log('Phone with code:', phone_with_code);
console.log('Phone without code:', phone_without_code);
console.log('Next stage:', next_stage);
console.log('DB State:', db_state);
console.log('Conversation ID:', conversation_id);

// Query 1: Update Conversation State (com UPSERT)
const query_update_conversation = `
-- Upsert conversation
WITH existing_conversation AS (
  SELECT id
  FROM conversations
  WHERE phone_number IN ('${phone_with_code}', '${phone_without_code}')
  ORDER BY updated_at DESC
  LIMIT 1
),
updated AS (
  UPDATE conversations
  SET
    current_state = '${db_state}',
    state_machine_state = '${next_stage}',
    collected_data = '${collected_data_json}'::jsonb,
    service_type = ${inputData.collected_data?.service_type ? "'" + escapeSql(inputData.collected_data.service_type) + "'" : 'service_type'},
    phone_number = '${phone_with_code}',
    last_message_at = NOW(),
    updated_at = NOW()
  WHERE id IN (SELECT id FROM existing_conversation)
  RETURNING *, 'updated' as operation
),
inserted AS (
  INSERT INTO conversations (
    phone_number,
    whatsapp_name,
    current_state,
    state_machine_state,
    collected_data,
    service_type,
    status,
    created_at,
    updated_at,
    last_message_at
  )
  SELECT
    '${phone_with_code}',
    '${escapeSql(inputData.collected_data?.lead_name || '')}',
    '${db_state}',
    '${next_stage}',
    '${collected_data_json}'::jsonb,
    ${inputData.collected_data?.service_type ? "'" + escapeSql(inputData.collected_data.service_type) + "'" : 'NULL'},
    'active',
    NOW(),
    NOW(),
    NOW()
  WHERE NOT EXISTS (SELECT 1 FROM existing_conversation)
  RETURNING *, 'inserted' as operation
)
SELECT * FROM updated
UNION ALL
SELECT * FROM inserted`.trim();

// Query 2: Save Inbound Message
const query_save_inbound = `
INSERT INTO messages (
  conversation_id,
  direction,
  content,
  message_type,
  whatsapp_message_id,
  created_at
)
VALUES (
  (SELECT id FROM conversations WHERE phone_number IN ('${phone_with_code}', '${phone_without_code}') ORDER BY updated_at DESC LIMIT 1),
  'inbound',
  '${message_content}',
  '${message_type}',
  '${message_id}',
  NOW()
)
ON CONFLICT (whatsapp_message_id)
WHERE whatsapp_message_id IS NOT NULL AND whatsapp_message_id != ''
DO NOTHING
RETURNING *`.trim();

// Query 3: Save Outbound Message
const query_save_outbound = `
INSERT INTO messages (
  conversation_id,
  direction,
  content,
  message_type,
  whatsapp_message_id,
  created_at
)
VALUES (
  (SELECT id FROM conversations WHERE phone_number IN ('${phone_with_code}', '${phone_without_code}') ORDER BY updated_at DESC LIMIT 1),
  'outbound',
  '${response_text}',
  'text',
  'out_' || extract(epoch from NOW())::bigint || '_' || random()::text,
  NOW()
)
RETURNING *`.trim();

// Query 4: Upsert Lead Data
const query_upsert_lead = `
WITH existing_lead AS (
  SELECT id
  FROM leads
  WHERE phone_number IN ('${phone_with_code}', '${phone_without_code}')
  LIMIT 1
),
updated AS (
  UPDATE leads
  SET
    name = COALESCE(NULLIF('${escapeSql(inputData.collected_data?.lead_name || '')}', ''), name),
    email = COALESCE(NULLIF('${escapeSql(inputData.collected_data?.email || '')}', ''), email),
    city = COALESCE(NULLIF('${escapeSql(inputData.collected_data?.city || '')}', ''), city),
    service_type = COALESCE(NULLIF('${escapeSql(inputData.collected_data?.service_type || '')}', ''), service_type),
    state_machine_state = '${next_stage}',
    service_details = '${collected_data_json}'::jsonb,
    updated_at = NOW()
  WHERE id IN (SELECT id FROM existing_lead)
  RETURNING *, 'updated' as operation
),
inserted AS (
  INSERT INTO leads (
    phone_number,
    name,
    email,
    city,
    service_type,
    state_machine_state,
    service_details,
    created_at,
    updated_at
  )
  SELECT
    '${phone_with_code}',
    '${escapeSql(inputData.collected_data?.lead_name || '')}',
    '${escapeSql(inputData.collected_data?.email || '')}',
    '${escapeSql(inputData.collected_data?.city || '')}',
    '${escapeSql(inputData.collected_data?.service_type || '')}',
    '${next_stage}',
    '${collected_data_json}'::jsonb,
    NOW(),
    NOW()
  WHERE NOT EXISTS (SELECT 1 FROM existing_lead)
  RETURNING *, 'inserted' as operation
)
SELECT * FROM updated
UNION ALL
SELECT * FROM inserted`.trim();

// Log para debug
console.log('✅ All queries built successfully as pure SQL strings');

// Retornar todas as queries e dados originais
return {
  ...inputData,
  query_update_conversation,
  query_save_inbound,
  query_save_outbound,
  query_upsert_lead
};"""
        },
        "id": "build-update-queries",
        "name": "Build Update Queries",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [1056, 0],
        "alwaysOutputData": True
    }

    # Add the new node to workflow
    workflow['nodes'].append(build_update_queries_node)
    print("✅ Added Build Update Queries node")

    # 2. Update existing PostgreSQL nodes to use prepared queries
    for node in workflow['nodes']:
        if node.get('name') == 'Update Conversation State':
            node['parameters']['query'] = '={{ $json.query_update_conversation }}'
            print("✅ Updated Update Conversation State to use prepared query")

        elif node.get('name') == 'Save Inbound Message':
            node['parameters']['query'] = '={{ $json.query_save_inbound }}'
            print("✅ Updated Save Inbound Message to use prepared query")

        elif node.get('name') == 'Save Outbound Message':
            node['parameters']['query'] = '={{ $json.query_save_outbound }}'
            print("✅ Updated Save Outbound Message to use prepared query")

        elif node.get('name') == 'Upsert Lead Data':
            node['parameters']['query'] = '={{ $json.query_upsert_lead }}'
            print("✅ Updated Upsert Lead Data to use prepared query")

    # 3. Update workflow connections
    if 'connections' in workflow:
        # Prepare Update Data now connects to Build Update Queries
        if 'Prepare Update Data' in workflow['connections']:
            workflow['connections']['Prepare Update Data'] = {
                "main": [
                    [
                        {
                            "node": "Build Update Queries",
                            "type": "main",
                            "index": 0
                        }
                    ]
                ]
            }

        # Build Update Queries connects to all PostgreSQL nodes and Send WhatsApp
        workflow['connections']['Build Update Queries'] = {
            "main": [
                [
                    {
                        "node": "Update Conversation State",
                        "type": "main",
                        "index": 0
                    },
                    {
                        "node": "Send WhatsApp Response",
                        "type": "main",
                        "index": 0
                    }
                ]
            ]
        }

        print("✅ Updated workflow connections")

    # 4. Update workflow name and version
    workflow['name'] = "AI Agent Conversation - V20 (Query Fix)"

    # Save the V20 workflow
    output_path = workflow_path.replace('V19.json', 'V20_QUERY_FIX.json')
    print(f"\n💾 Saving V20 workflow: {output_path}")

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(workflow, f, indent=2, ensure_ascii=False)
        print(f"✅ V20 workflow saved successfully!")
        print(f"\n📋 Improvements in V20:")
        print("1. ✅ All SQL queries are pre-built as pure strings")
        print("2. ✅ No template processing needed in PostgreSQL nodes")
        print("3. ✅ last_message_at will be properly updated")
        print("4. ✅ Conversation state transitions will work correctly")
        print("5. ✅ Menu loop issue should be resolved")
        print(f"\n🚀 Next steps:")
        print(f"1. Import V20 into n8n: {output_path}")
        print(f"2. Deactivate V19 workflow")
        print(f"3. Activate V20 workflow")
        print(f"4. Test menu navigation (should work now!)")
        return True
    except Exception as e:
        print(f"❌ Error saving file: {e}")
        return False

if __name__ == "__main__":
    success = create_v20_workflow()
    sys.exit(0 if success else 1)