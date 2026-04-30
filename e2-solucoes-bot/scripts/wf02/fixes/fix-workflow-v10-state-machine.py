#!/usr/bin/env python3
"""
Fix workflow V10 - Adiciona suporte ao novo campo state_machine_state
Problema: Constraint valid_status não aceita estados do State Machine
Solução: Usar novo campo state_machine_state e manter mapeamento para status
"""

import json

# Ler o workflow v9
with open('/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V9.json', 'r') as f:
    workflow = json.load(f)

print("🔍 Analisando problema de constraint de status...")
print("   - Erro: 'service_selection' não é válido para campo status")
print("   - Solução: Usar novo campo state_machine_state")
print("   - Benefício: Mantém estado exato + status mapeado automaticamente")

# Atualizar o nó Upsert Lead Data para usar novo campo
for node in workflow['nodes']:
    if node['name'] == 'Upsert Lead Data':
        print("🔧 Corrigindo Upsert Lead Data...")

        # Nova query SQL com state_machine_state
        node['parameters']['query'] = """-- Primeiro, vamos verificar se já existe um lead com este phone_number
WITH existing_lead AS (
  SELECT id
  FROM leads
  WHERE phone_number = '{{ $node["Prepare Update Data"].json.phone_number }}'
  LIMIT 1
),
-- Se existir, fazemos UPDATE
updated AS (
  UPDATE leads
  SET
    name = COALESCE(
      NULLIF('{{ $node["Prepare Update Data"].json.collected_data.lead_name || $node["Prepare Update Data"].json.collected_data.nome || "" }}', ''),
      name
    ),
    email = COALESCE(
      NULLIF('{{ $node["Prepare Update Data"].json.collected_data.email || "" }}', ''),
      email
    ),
    address = COALESCE(
      NULLIF('{{ $node["Prepare Update Data"].json.collected_data.endereco || $node["Prepare Update Data"].json.collected_data.address || "" }}', ''),
      address
    ),
    city = COALESCE(
      NULLIF('{{ $node["Prepare Update Data"].json.collected_data.cidade || $node["Prepare Update Data"].json.collected_data.city || "" }}', ''),
      city
    ),
    service_type = COALESCE(
      NULLIF('{{ $node["Prepare Update Data"].json.collected_data.service_type || $node["Prepare Update Data"].json.collected_data.servico || "" }}', ''),
      service_type
    ),
    -- IMPORTANTE: Usar state_machine_state em vez de status diretamente
    state_machine_state = '{{ $node["Prepare Update Data"].json.next_stage || "greeting" }}',
    -- O status será atualizado automaticamente pelo trigger
    service_details = '{{ $node["Prepare Update Data"].json.collected_data_json }}'::jsonb,
    updated_at = NOW()
  WHERE id IN (SELECT id FROM existing_lead)
  RETURNING *, 'updated' as operation
),
-- Se não existir, fazemos INSERT
inserted AS (
  INSERT INTO leads (
    phone_number,
    name,
    email,
    address,
    city,
    service_type,
    state_machine_state,
    service_details,
    created_at,
    updated_at
  )
  SELECT
    '{{ $node["Prepare Update Data"].json.phone_number }}',
    '{{ $node["Prepare Update Data"].json.collected_data.lead_name || $node["Prepare Update Data"].json.collected_data.nome || "" }}',
    '{{ $node["Prepare Update Data"].json.collected_data.email || "" }}',
    '{{ $node["Prepare Update Data"].json.collected_data.endereco || $node["Prepare Update Data"].json.collected_data.address || "" }}',
    '{{ $node["Prepare Update Data"].json.collected_data.cidade || $node["Prepare Update Data"].json.collected_data.city || "" }}',
    '{{ $node["Prepare Update Data"].json.collected_data.service_type || $node["Prepare Update Data"].json.collected_data.servico || "" }}',
    '{{ $node["Prepare Update Data"].json.next_stage || "greeting" }}',
    '{{ $node["Prepare Update Data"].json.collected_data_json }}'::jsonb,
    NOW(),
    NOW()
  WHERE NOT EXISTS (SELECT 1 FROM existing_lead)
  RETURNING *, 'inserted' as operation
)
-- Retorna o resultado (seja UPDATE ou INSERT)
SELECT * FROM updated
UNION ALL
SELECT * FROM inserted"""

        print("✅ Upsert Lead Data atualizado!")
        print("   - Usa state_machine_state para estado exato")
        print("   - Trigger atualiza status automaticamente")
        break

# Também atualizar Update Conversation State para usar o novo campo
for node in workflow['nodes']:
    if node['name'] == 'Update Conversation State':
        print("🔧 Atualizando Update Conversation State...")

        # Nova query SQL para conversations
        node['parameters']['query'] = """-- Primeiro, vamos verificar se já existe uma conversa com este phone_number
WITH existing_conversation AS (
  SELECT id
  FROM conversations
  WHERE phone_number = '{{ $node["Prepare Update Data"].json.phone_number }}'
  LIMIT 1
),
-- Se existir, fazemos UPDATE
updated AS (
  UPDATE conversations
  SET
    current_state = '{{ $node["Prepare Update Data"].json.next_stage }}',
    state_machine_state = '{{ $node["Prepare Update Data"].json.next_stage }}',
    collected_data = '{{ $node["Prepare Update Data"].json.collected_data_json }}'::jsonb,
    service_type = COALESCE(
      NULLIF('{{ $node["Prepare Update Data"].json.collected_data.service_type || "" }}', ''),
      service_type
    ),
    last_message_at = NOW(),
    updated_at = NOW()
  WHERE id IN (SELECT id FROM existing_conversation)
  RETURNING *, 'updated' as operation
),
-- Se não existir, fazemos INSERT
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
    '{{ $node["Prepare Update Data"].json.phone_number }}',
    '{{ $node["Prepare Update Data"].json.collected_data.lead_name || "" }}',
    '{{ $node["Prepare Update Data"].json.next_stage }}',
    '{{ $node["Prepare Update Data"].json.next_stage }}',
    '{{ $node["Prepare Update Data"].json.collected_data_json }}'::jsonb,
    '{{ $node["Prepare Update Data"].json.collected_data.service_type || "" }}',
    'active',
    NOW(),
    NOW(),
    NOW()
  WHERE NOT EXISTS (SELECT 1 FROM existing_conversation)
  RETURNING *, 'inserted' as operation
)
-- Retorna o resultado (seja UPDATE ou INSERT)
SELECT * FROM updated
UNION ALL
SELECT * FROM inserted"""

        print("✅ Update Conversation State atualizado!")
        break

# Atualizar metadados do workflow
workflow['name'] = "02 - AI Agent Conversation V10 (State Machine Field)"
workflow['versionId'] = "v10-state-machine-field"

# Salvar novo workflow
output_path = '/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V10.json'
with open(output_path, 'w') as f:
    json.dump(workflow, f, indent=2, ensure_ascii=False)

print("\n✅ Workflow V10 criado com sucesso!")
print(f"📄 Arquivo: {output_path}")
print("\n🔄 Principais correções:")
print("1. ✅ Novo campo state_machine_state para estado exato")
print("2. ✅ Campo status atualizado automaticamente via trigger")
print("3. ✅ Compatibilidade total com estados do State Machine")
print("4. ✅ Sem mais erros de constraint")

print("\n📋 Mapeamento automático (via trigger):")
print("  - greeting → novo")
print("  - service_selection → em_atendimento")
print("  - collect_* → em_atendimento")
print("  - confirmation → em_atendimento")
print("  - scheduling → agendado")
print("  - handoff_comercial → handoff")
print("  - completed → concluido")

print("\n🚀 Benefícios:")
print("1. Estado exato preservado (state_machine_state)")
print("2. Status de negócio mantido (status)")
print("3. Trigger garante consistência")
print("4. Sem necessidade de mapeamento manual no workflow")