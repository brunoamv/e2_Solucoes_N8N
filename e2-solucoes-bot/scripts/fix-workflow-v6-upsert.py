#!/usr/bin/env python3
"""
Fix workflow V6 - Corrige o problema de ON CONFLICT com lógica de UPSERT manual
Como não há constraint única em phone_number, faremos um SELECT + INSERT/UPDATE
"""

import json

# Ler o workflow v5
with open('/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V5.json', 'r') as f:
    workflow = json.load(f)

# Encontrar e corrigir o nó Upsert Lead Data
for node in workflow['nodes']:
    if node['name'] == 'Upsert Lead Data':
        print(f"Corrigindo nó: {node['name']}")

        # Nova query que primeiro verifica se existe, depois insere ou atualiza
        # Usando uma CTE (Common Table Expression) para fazer tudo em uma query
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
    status = '{{ $node["Prepare Update Data"].json.next_stage || "novo" }}',
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
    status,
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
    '{{ $node["Prepare Update Data"].json.next_stage || "novo" }}',
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

        print("✅ Query SQL corrigida com lógica UPSERT manual!")
        print("   - Usa CTE para verificar existência")
        print("   - Faz UPDATE se existir")
        print("   - Faz INSERT se não existir")
        print("   - COALESCE + NULLIF para não sobrescrever com strings vazias")
        print("   - Retorna o lead com operação realizada")
        break

# Atualizar metadados do workflow
workflow['name'] = "02 - AI Agent Conversation V6 (UPSERT Fix)"
workflow['versionId'] = "v6-upsert-fix"

# Salvar novo workflow
output_path = '/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V6.json'
with open(output_path, 'w') as f:
    json.dump(workflow, f, indent=2, ensure_ascii=False)

print("\n✅ Workflow V6 criado com sucesso!")
print(f"📄 Arquivo: {output_path}")
print("\n🔄 Principais correções:")
print("1. ✅ Removido ON CONFLICT que causava erro")
print("2. ✅ Implementado UPSERT manual com CTE")
print("3. ✅ SELECT primeiro para verificar existência")
print("4. ✅ UPDATE se existir, INSERT se não existir")
print("5. ✅ COALESCE + NULLIF para preservar dados existentes")

print("\n📋 Como funciona a nova lógica:")
print("  1. Verifica se existe lead com phone_number")
print("  2. Se existir: UPDATE preservando dados não vazios")
print("  3. Se não existir: INSERT com dados novos")
print("  4. Retorna o lead atualizado/inserido com operação")

print("\n🚀 Próximos passos:")
print("1. Importe o arquivo V6 no n8n")
print("2. Teste o fluxo com um número novo")
print("3. Teste novamente com o mesmo número para verificar UPDATE")