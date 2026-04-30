#!/usr/bin/env python3
"""
Fix workflow V5 - Corrige erro de coluna whatsapp_number para phone_number
E também corrige os campos do collected_data para usar a estrutura correta
"""

import json

# Ler o workflow v4
with open('/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V4.json', 'r') as f:
    workflow = json.load(f)

# Encontrar e corrigir o nó Upsert Lead Data
for node in workflow['nodes']:
    if node['name'] == 'Upsert Lead Data':
        print(f"Corrigindo nó: {node['name']}")

        # Corrigir a query SQL - trocar whatsapp_number por phone_number
        # E também ajustar os campos para usar o padrão correto de collected_data
        node['parameters']['query'] = """INSERT INTO leads (
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
VALUES (
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
)
ON CONFLICT (phone_number, email)
DO UPDATE SET
  name = COALESCE(EXCLUDED.name, leads.name),
  email = COALESCE(EXCLUDED.email, leads.email),
  address = COALESCE(EXCLUDED.address, leads.address),
  city = COALESCE(EXCLUDED.city, leads.city),
  service_type = COALESCE(EXCLUDED.service_type, leads.service_type),
  status = EXCLUDED.status,
  service_details = EXCLUDED.service_details,
  updated_at = NOW()
RETURNING *"""

        print("✅ Query SQL corrigida!")
        print("   - whatsapp_number → phone_number")
        print("   - lead_name → name (coluna correta)")
        print("   - phone → removido (phone_number já usado)")
        print("   - stage → status (coluna correta)")
        print("   - collected_data → service_details (coluna correta)")
        print("   - ON CONFLICT agora usa (phone_number, email)")
        print("   - COALESCE para não sobrescrever dados existentes com NULL")
        break

# Atualizar metadados do workflow
workflow['name'] = "02 - AI Agent Conversation V5 (Database Fix)"
workflow['versionId'] = "v5-database-fix"

# Salvar novo workflow
output_path = '/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V5.json'
with open(output_path, 'w') as f:
    json.dump(workflow, f, indent=2, ensure_ascii=False)

print("\n✅ Workflow V5 criado com sucesso!")
print(f"📄 Arquivo: {output_path}")
print("\n🔄 Principais correções:")
print("1. ✅ Coluna whatsapp_number → phone_number (correta no schema)")
print("2. ✅ Campos ajustados para o schema correto da tabela leads")
print("3. ✅ ON CONFLICT usa índice composto (phone_number, email)")
print("4. ✅ COALESCE para preservar dados existentes")
print("5. ✅ Compatível com estrutura JSONB do collected_data")

print("\n📋 Estrutura de collected_data esperada:")
print("  - nome/lead_name: Nome do lead")
print("  - email: E-mail do lead")
print("  - endereco/address: Endereço")
print("  - cidade/city: Cidade")
print("  - servico/service_type: Tipo de serviço")

print("\n🚀 Próximos passos:")
print("1. Importe o arquivo V5 no n8n")
print("2. Teste o fluxo completo de conversação")
print("3. Verifique se os dados são salvos corretamente na tabela leads")