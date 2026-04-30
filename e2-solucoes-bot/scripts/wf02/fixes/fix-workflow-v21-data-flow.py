#!/usr/bin/env python3
"""
Fix V21 - Corrige o fluxo de dados para Build Update Queries
O problema: Build Update Queries não está recebendo todos os dados necessários
Solução: Fazer Build Update Queries receber dados diretamente do State Machine Logic
"""

import json
import sys
import os
from datetime import datetime

def create_v21_workflow():
    """Cria V21 com fluxo de dados corrigido"""

    workflow_path = "/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V20_QUERY_FIX.json"

    # Check if file exists
    if not os.path.exists(workflow_path):
        print(f"❌ File not found: {workflow_path}")
        return False

    print(f"📖 Reading V20 workflow: {workflow_path}")

    try:
        with open(workflow_path, 'r', encoding='utf-8') as f:
            workflow = json.load(f)
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return False

    print("🔧 Creating V21 with fixed data flow...")

    # 1. Update Build Update Queries node to be more robust
    for node in workflow['nodes']:
        if node.get('name') == 'Build Update Queries':
            node['parameters']['jsCode'] = """// Build Update Queries - V21 FIXED DATA FLOW
// Recebe dados DIRETAMENTE do State Machine Logic
const inputData = $input.first().json;

console.log('=== V21 BUILD UPDATE QUERIES DEBUG ===');
console.log('Input keys:', Object.keys(inputData));
console.log('Phone number:', inputData.phone_number);
console.log('Response text:', inputData.response_text);
console.log('Next stage:', inputData.next_stage);
console.log('Collected data:', inputData.collected_data);

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

// CRITICAL FIX: Extrair dados com fallbacks robustos
let phone_number = String(inputData.phone_number || '');

// Limpar e garantir formato correto
phone_number = phone_number.replace(/[^0-9]/g, '');

// Adicionar código 55 se necessário
if (phone_number && !phone_number.startsWith('55')) {
  if (phone_number.length === 10 || phone_number.length === 11) {
    phone_number = '55' + phone_number;
  }
}

// Criar versões com e sem código
const phone_with_code = phone_number;
const phone_without_code = phone_number.startsWith('55') ? phone_number.substring(2) : phone_number;

// Extrair outros dados necessários
const response_text = escapeSql(inputData.response_text || 'Olá! Como posso ajudar?');
const next_stage = inputData.next_stage || inputData.current_state || 'greeting';
const collected_data = inputData.collected_data || {};
const collected_data_json = prepareJsonb(collected_data);
const message_content = escapeSql(inputData.message || '');
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

console.log('=== V21 QUERY BUILDING ===');
console.log('Phone with code:', phone_with_code);
console.log('Phone without code:', phone_without_code);
console.log('Next stage:', next_stage);
console.log('DB State:', db_state);
console.log('Conversation ID:', conversation_id);

// Query 1: Update Conversation State (com UPSERT)
const query_update_conversation = `
-- V21: Upsert conversation with fixed data flow
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
    service_type = ${collected_data?.service_type ? "'" + escapeSql(collected_data.service_type) + "'" : 'service_type'},
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
    '${escapeSql(collected_data?.lead_name || '')}',
    '${db_state}',
    '${next_stage}',
    '${collected_data_json}'::jsonb,
    ${collected_data?.service_type ? "'" + escapeSql(collected_data.service_type) + "'" : 'NULL'},
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
    name = COALESCE(NULLIF('${escapeSql(collected_data?.lead_name || '')}', ''), name),
    email = COALESCE(NULLIF('${escapeSql(collected_data?.email || '')}', ''), email),
    city = COALESCE(NULLIF('${escapeSql(collected_data?.city || '')}', ''), city),
    service_type = COALESCE(NULLIF('${escapeSql(collected_data?.service_type || '')}', ''), service_type),
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
    '${escapeSql(collected_data?.lead_name || '')}',
    '${escapeSql(collected_data?.email || '')}',
    '${escapeSql(collected_data?.city || '')}',
    '${escapeSql(collected_data?.service_type || '')}',
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
console.log('✅ V21: All queries built successfully as pure SQL strings');

// Retornar todas as queries e TODOS os dados necessários
return {
  // Dados originais do State Machine
  phone_number: phone_with_code,
  phone_with_code: phone_with_code,
  phone_without_code: phone_without_code,
  response_text: inputData.response_text,
  next_stage: next_stage,
  collected_data: collected_data,
  conversation_id: conversation_id,
  message: inputData.message,
  message_type: message_type,
  message_id: message_id,

  // Queries SQL prontas
  query_update_conversation,
  query_save_inbound,
  query_save_outbound,
  query_upsert_lead,

  // Metadados
  timestamp: new Date().toISOString()
};"""
            print("✅ Updated Build Update Queries with V21 fixes")

    # 2. Remove Prepare Update Data node (não é mais necessário)
    workflow['nodes'] = [node for node in workflow['nodes'] if node.get('name') != 'Prepare Update Data']
    print("✅ Removed unnecessary Prepare Update Data node")

    # 3. Update connections - State Machine Logic connects directly to Build Update Queries
    if 'connections' in workflow:
        # State Machine Logic now connects directly to Build Update Queries
        workflow['connections']['State Machine Logic'] = {
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

        # Build Update Queries keeps its connections to Update Conversation State and Send WhatsApp
        # (already configured correctly in V20)

        print("✅ Updated workflow connections for direct data flow")

    # 4. Update Send WhatsApp Response to use correct data path
    for node in workflow['nodes']:
        if node.get('name') == 'Send WhatsApp Response':
            # Update the body parameters to use Build Update Queries output
            if 'bodyParameters' in node['parameters']:
                for param in node['parameters']['bodyParameters']['parameters']:
                    if param['name'] == 'number':
                        param['value'] = "={{ $node[\"Build Update Queries\"].json[\"phone_number\"] }}"
                    elif param['name'] == 'text':
                        param['value'] = "={{ $node[\"Build Update Queries\"].json[\"response_text\"] }}"
            print("✅ Updated Send WhatsApp Response to use Build Update Queries data")

    # 5. Update workflow name and version
    workflow['name'] = "AI Agent Conversation - V21 (Data Flow Fixed)"

    # Save the V21 workflow
    output_path = workflow_path.replace('V20_QUERY_FIX.json', 'V21_DATA_FLOW_FIXED.json')
    print(f"\n💾 Saving V21 workflow: {output_path}")

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(workflow, f, indent=2, ensure_ascii=False)
        print(f"✅ V21 workflow saved successfully!")
        print(f"\n📋 Improvements in V21:")
        print("1. ✅ Build Update Queries receives data directly from State Machine Logic")
        print("2. ✅ Removed unnecessary Prepare Update Data node")
        print("3. ✅ All required fields are properly extracted with fallbacks")
        print("4. ✅ SQL queries are built with complete data")
        print("5. ✅ Send WhatsApp Response uses correct data paths")
        print(f"\n🚀 Next steps:")
        print(f"1. Import V21 into n8n: {output_path}")
        print(f"2. Deactivate V20 workflow")
        print(f"3. Activate V21 workflow")
        print(f"4. Test the complete flow - should work now!")
        return True
    except Exception as e:
        print(f"❌ Error saving file: {e}")
        return False

if __name__ == "__main__":
    success = create_v21_workflow()
    sys.exit(0 if success else 1)