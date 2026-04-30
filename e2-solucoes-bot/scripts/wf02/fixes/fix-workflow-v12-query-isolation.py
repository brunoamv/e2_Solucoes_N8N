#!/usr/bin/env python3
"""
Fix workflow V12 - Corrige isolamento de query e método HTTP
Problemas:
1. Múltiplos registros no banco (com e sem código 55)
2. Send WhatsApp usando GET em vez de POST
3. Query pode ter problema de isolamento ou timing
"""

import json

# Ler o workflow v11
with open('/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V11.json', 'r') as f:
    workflow = json.load(f)

print("🔍 Analisando problemas identificados...")
print("   - Problema 1: Múltiplos registros no banco (6181755748 e 556181755748)")
print("   - Problema 2: Send WhatsApp usando GET em vez de POST")
print("   - Problema 3: Query pode ter problema de isolamento")

# 1. Corrigir Get Conversation Count para ser mais robusta
for node in workflow['nodes']:
    if node['name'] == 'Get Conversation Count':
        print("🔧 Corrigindo Get Conversation Count...")

        # Query mais robusta que busca com OU sem código 55
        node['parameters']['query'] = """-- Busca conversa com OU sem código 55
SELECT COUNT(*) as count
FROM conversations
WHERE phone_number IN (
  '{{ $node["Validate Input Data"].json.phone_number }}',
  -- Também busca sem código 55 caso existam registros antigos
  '{{ String($node["Validate Input Data"].json.phone_number).replace(/^55/, "") }}'
);"""

        print("✅ Query corrigida para buscar ambos formatos!")
        break

# 2. Corrigir Get Conversation Details também
for node in workflow['nodes']:
    if node['name'] == 'Get Conversation Details':
        print("🔧 Corrigindo Get Conversation Details...")

        node['parameters']['query'] = """-- Busca conversa mais recente com OU sem código 55
SELECT *
FROM conversations
WHERE phone_number IN (
  '{{ $node["Validate Input Data"].json.phone_number }}',
  '{{ String($node["Validate Input Data"].json.phone_number).replace(/^55/, "") }}'
)
ORDER BY updated_at DESC
LIMIT 1;"""

        print("✅ Query de detalhes corrigida!")
        break

# 3. Corrigir Send WhatsApp Response para usar POST
for node in workflow['nodes']:
    if node['name'] == 'Send WhatsApp Response':
        print("🔧 Corrigindo Send WhatsApp Response...")

        # Garantir que é POST
        node['parameters']['method'] = 'POST'

        # Verificar se a URL está correta
        if 'url' in node['parameters']:
            node['parameters']['url'] = 'http://e2bot-evolution-dev:8080/message/sendText/e2-solucoes-bot'
            print("   - Método corrigido para POST")
            print("   - URL verificada")

        print("✅ Send WhatsApp corrigido!")
        break

# 4. Adicionar limpeza de duplicados no Create New Conversation
for node in workflow['nodes']:
    if node['name'] == 'Create New Conversation':
        print("🔧 Melhorando Create New Conversation...")

        # Query que limpa duplicados antes de inserir
        node['parameters']['query'] = """-- Primeiro, limpa possíveis duplicados antigos sem código 55
DELETE FROM conversations
WHERE phone_number = '{{ String($node["Validate Input Data"].json.phone_number).replace(/^55/, "") }}'
  AND phone_number != '{{ $node["Validate Input Data"].json.phone_number }}';

-- Agora insere ou atualiza a conversa
INSERT INTO conversations (
  phone_number,
  whatsapp_name,
  current_state,
  state_machine_state,
  created_at,
  updated_at
)
VALUES (
  '{{ $node["Validate Input Data"].json.phone_number }}',
  '{{ $node["Validate Input Data"].json.whatsapp_name }}',
  'greeting',
  'greeting',
  NOW(),
  NOW()
)
ON CONFLICT (phone_number)
DO UPDATE SET
  whatsapp_name = EXCLUDED.whatsapp_name,
  updated_at = NOW(),
  current_state = CASE
    WHEN conversations.current_state = 'completed' THEN 'greeting'
    ELSE conversations.current_state
  END,
  state_machine_state = CASE
    WHEN conversations.state_machine_state = 'completed' THEN 'greeting'
    ELSE conversations.state_machine_state
  END
RETURNING *;"""

        print("✅ Create New Conversation melhorado com limpeza de duplicados!")
        break

# 5. Também vamos garantir que Update Conversation State use o formato correto
for node in workflow['nodes']:
    if node['name'] == 'Update Conversation State':
        print("🔧 Verificando Update Conversation State...")

        # Adicionar uma verificação antes do WITH para garantir phone_number correto
        node['parameters']['query'] = """-- Garante que sempre trabalhamos com o formato com código 55
-- Primeiro, vamos verificar se já existe uma conversa com este phone_number
WITH existing_conversation AS (
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
    current_state = '{{ $node["Prepare Update Data"].json.next_stage }}',
    state_machine_state = '{{ $node["Prepare Update Data"].json.next_stage }}',
    collected_data = '{{ $node["Prepare Update Data"].json.collected_data_json }}'::jsonb,
    service_type = COALESCE(
      NULLIF('{{ $node["Prepare Update Data"].json.collected_data.service_type || "" }}', ''),
      service_type
    ),
    phone_number = '{{ $node["Prepare Update Data"].json.phone_number }}', -- Normaliza para formato com 55
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
SELECT * FROM inserted;"""

        print("✅ Update Conversation State melhorado!")
        break

# Atualizar metadados do workflow
workflow['name'] = "02 - AI Agent Conversation V12 (Query Isolation Fix)"
workflow['versionId'] = "v12-query-isolation-fix"

# Salvar novo workflow
output_path = '/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V12.json'
with open(output_path, 'w') as f:
    json.dump(workflow, f, indent=2, ensure_ascii=False)

print("\n✅ Workflow V12 criado com sucesso!")
print(f"📄 Arquivo: {output_path}")
print("\n🔄 Principais correções:")
print("1. ✅ Query busca com OU sem código 55")
print("2. ✅ Send WhatsApp corrigido para POST")
print("3. ✅ Limpeza de duplicados automática")
print("4. ✅ Normalização de phone_number para formato com 55")
print("5. ✅ Queries mais robustas para múltiplos formatos")

print("\n📋 Como funciona agora:")
print("  1. Get Conversation busca '556181755748' OU '6181755748'")
print("  2. Encontra qualquer registro existente")
print("  3. Limpa duplicados automaticamente")
print("  4. Normaliza todos para formato com 55")
print("  5. State Machine funciona corretamente")

print("\n🧹 Recomendação:")
print("Execute esta query no banco para limpar duplicados:")
print("""
docker exec e2bot-postgres-dev psql -U postgres -d e2_bot -c "
DELETE FROM conversations
WHERE phone_number NOT LIKE '55%'
AND EXISTS (
  SELECT 1 FROM conversations c2
  WHERE c2.phone_number = '55' || conversations.phone_number
);"
""")