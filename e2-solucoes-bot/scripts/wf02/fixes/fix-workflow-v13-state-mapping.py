#!/usr/bin/env python3
"""
Fix workflow V13 - Corrige mapeamento de estados para constraints do banco
Problema: current_state tentando usar 'greeting' mas constraint só aceita 'novo'
Solução: Usar campos corretos - current_state='novo', state_machine_state='greeting'
"""

import json

# Ler o workflow v12
with open('/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V12.json', 'r') as f:
    workflow = json.load(f)

print("🔍 Analisando problema de constraint de estados...")
print("   - Erro: current_state='greeting' viola constraint valid_state")
print("   - Constraint aceita: novo, identificando_servico, coletando_dados, etc.")
print("   - Solução: Usar current_state='novo' e state_machine_state='greeting'")

# 1. Corrigir Create New Conversation
for node in workflow['nodes']:
    if node['name'] == 'Create New Conversation':
        print("🔧 Corrigindo Create New Conversation...")

        # Query corrigida com mapeamento correto de estados
        node['parameters']['query'] = """-- Primeiro, limpa possíveis duplicados antigos sem código 55
DELETE FROM conversations
WHERE phone_number = '{{ String($node["Validate Input Data"].json.phone_number).replace(/^55/, "") }}'
  AND phone_number != '{{ $node["Validate Input Data"].json.phone_number }}';

-- Agora insere ou atualiza a conversa
INSERT INTO conversations (
  phone_number,
  whatsapp_name,
  current_state,       -- Campo do banco com constraint
  state_machine_state,  -- Campo novo para estado do bot
  created_at,
  updated_at
)
VALUES (
  '{{ $node["Validate Input Data"].json.phone_number }}',
  '{{ $node["Validate Input Data"].json.whatsapp_name }}',
  'novo',     -- ✅ Valor válido para current_state
  'greeting',  -- ✅ Estado do state machine
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

        print("✅ Create New Conversation corrigido!")
        break

# 2. Corrigir Update Conversation State para mapear estados corretamente
for node in workflow['nodes']:
    if node['name'] == 'Update Conversation State':
        print("🔧 Corrigindo Update Conversation State...")

        node['parameters']['query'] = """-- Função inline para mapear state_machine_state para current_state válido
WITH state_mapping AS (
  SELECT
    '{{ $node["Prepare Update Data"].json.next_stage }}' as sm_state,
    CASE '{{ $node["Prepare Update Data"].json.next_stage }}'
      WHEN 'greeting' THEN 'novo'
      WHEN 'service_selection' THEN 'identificando_servico'
      WHEN 'collect_name' THEN 'coletando_dados'
      WHEN 'collect_phone' THEN 'coletando_dados'
      WHEN 'collect_email' THEN 'coletando_dados'
      WHEN 'collect_city' THEN 'coletando_dados'
      WHEN 'confirmation' THEN 'coletando_dados'
      WHEN 'scheduling' THEN 'agendando'
      WHEN 'handoff_comercial' THEN 'handoff_comercial'
      WHEN 'completed' THEN 'concluido'
      ELSE 'novo'
    END as db_state
),
-- Busca conversa existente
existing_conversation AS (
  SELECT id
  FROM conversations
  WHERE phone_number IN (
    '{{ $node["Prepare Update Data"].json.phone_number }}',
    '{{ String($node["Prepare Update Data"].json.phone_number).replace(/^55/, "") }}'
  )
  ORDER BY updated_at DESC
  LIMIT 1
),
-- Se existir, fazemos UPDATE
updated AS (
  UPDATE conversations
  SET
    current_state = (SELECT db_state FROM state_mapping),
    state_machine_state = (SELECT sm_state FROM state_mapping),
    collected_data = '{{ $node["Prepare Update Data"].json.collected_data_json }}'::jsonb,
    service_type = COALESCE(
      NULLIF('{{ $node["Prepare Update Data"].json.collected_data.service_type || "" }}', ''),
      service_type
    ),
    phone_number = '{{ $node["Prepare Update Data"].json.phone_number }}',
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
    (SELECT db_state FROM state_mapping),
    (SELECT sm_state FROM state_mapping),
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
SELECT * FROM inserted;"""

        print("✅ Update Conversation State corrigido com mapeamento!")
        break

# 3. Atualizar Get Conversation Details para pegar state_machine_state
for node in workflow['nodes']:
    if node['name'] == 'Get Conversation Details':
        print("🔧 Atualizando Get Conversation Details...")

        node['parameters']['query'] = """-- Busca conversa mais recente com OU sem código 55
SELECT
  *,
  -- Retorna o estado correto para o State Machine
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
  '{{ $node["Validate Input Data"].json.phone_number }}',
  '{{ String($node["Validate Input Data"].json.phone_number).replace(/^55/, "") }}'
)
ORDER BY updated_at DESC
LIMIT 1;"""

        print("✅ Get Conversation Details atualizado!")
        break

# 4. Atualizar State Machine Logic para usar o campo correto
for node in workflow['nodes']:
    if node['name'] == 'State Machine Logic':
        print("🔧 Atualizando State Machine Logic...")

        code = node['parameters']['functionCode']

        # Substituir uso de current_state por state_machine_state ou state_for_machine
        code = code.replace(
            "const currentStage = conversation.current_state || 'greeting';",
            "const currentStage = conversation.state_machine_state || conversation.state_for_machine || conversation.current_state || 'greeting';"
        )

        node['parameters']['functionCode'] = code
        print("✅ State Machine Logic atualizado!")
        break

# Atualizar metadados do workflow
workflow['name'] = "02 - AI Agent Conversation V13 (State Mapping Fix)"
workflow['versionId'] = "v13-state-mapping-fix"

# Salvar novo workflow
output_path = '/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V13.json'
with open(output_path, 'w') as f:
    json.dump(workflow, f, indent=2, ensure_ascii=False)

print("\n✅ Workflow V13 criado com sucesso!")
print(f"📄 Arquivo: {output_path}")
print("\n🔄 Principais correções:")
print("1. ✅ current_state usa valores válidos (novo, identificando_servico, etc.)")
print("2. ✅ state_machine_state mantém estados do bot (greeting, service_selection, etc.)")
print("3. ✅ Mapeamento automático entre os dois sistemas de estados")
print("4. ✅ Get Conversation Details retorna estado correto para State Machine")
print("5. ✅ State Machine Logic usa campo apropriado")

print("\n📋 Mapeamento de estados:")
print("  State Machine         →  Database (current_state)")
print("  greeting              →  novo")
print("  service_selection     →  identificando_servico")
print("  collect_*             →  coletando_dados")
print("  scheduling            →  agendando")
print("  handoff_comercial     →  handoff_comercial")
print("  completed             →  concluido")

print("\n🎯 Como funciona agora:")
print("1. Dois campos separados para estados")
print("2. current_state: para o banco (válido para constraint)")
print("3. state_machine_state: para o bot (estados do menu)")
print("4. Mapeamento automático entre eles")
print("5. Sem mais erros de constraint!")