#!/usr/bin/env python3
"""
Corrige o problema de "Parameter 'query' must be a text string" no workflow V17
Problema: O node "Build SQL Queries" está retornando um objeto, mas o PostgreSQL espera strings
"""

import json
import sys
import os

def fix_workflow_v17():
    """Corrige o workflow V17 para garantir que queries sejam strings"""

    workflow_path = "/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V17.json"

    # Verificar se o arquivo existe
    if not os.path.exists(workflow_path):
        print(f"❌ Arquivo não encontrado: {workflow_path}")
        return False

    print(f"📖 Lendo workflow: {workflow_path}")

    try:
        with open(workflow_path, 'r', encoding='utf-8') as f:
            workflow = json.load(f)
    except Exception as e:
        print(f"❌ Erro ao ler arquivo: {e}")
        return False

    print("🔍 Procurando node 'Build SQL Queries'...")

    # Encontrar e corrigir o node Build SQL Queries
    fixed = False
    for node in workflow.get('nodes', []):
        if node.get('name') == 'Build SQL Queries':
            print(f"✅ Node encontrado: {node['name']}")

            # Novo código corrigido que retorna apenas strings
            new_code = """// Build SQL Queries Node - Prepara todas as queries SQL
// Recebe dados do node anterior
const data = $input.first().json;
const phone_with_code = data.phone_with_code || '';
const phone_without_code = data.phone_without_code || '';

// Validação de segurança
if (!phone_with_code || !phone_without_code) {
  throw new Error('Phone numbers not properly formatted');
}

// Escape simples para SQL injection
const escapeSql = (str) => {
  return String(str).replace(/'/g, "''");
};

// Query para contar conversas existentes
const query_count = `
  SELECT COUNT(*) as count
  FROM conversations
  WHERE phone_number IN ('${escapeSql(phone_with_code)}', '${escapeSql(phone_without_code)}')
`.trim();

// Query para buscar detalhes da conversa
const query_details = `
  SELECT
    *,
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
  WHERE phone_number IN ('${escapeSql(phone_with_code)}', '${escapeSql(phone_without_code)}')
  ORDER BY updated_at DESC
  LIMIT 1
`.trim();

// Query para criar/atualizar conversa
const query_upsert = `
  -- Limpar duplicatas antigas
  DELETE FROM conversations
  WHERE phone_number IN ('${escapeSql(phone_with_code)}', '${escapeSql(phone_without_code)}')
  AND id NOT IN (
    SELECT id FROM conversations
    WHERE phone_number IN ('${escapeSql(phone_with_code)}', '${escapeSql(phone_without_code)}')
    ORDER BY updated_at DESC
    LIMIT 1
  );

  -- Inserir ou atualizar conversa
  INSERT INTO conversations (
    phone_number,
    whatsapp_name,
    service_id,
    contact_name,
    contact_email,
    city,
    current_state,
    state_machine_state,
    collected_data,
    error_count,
    created_at,
    updated_at
  ) VALUES (
    '${escapeSql(phone_without_code)}',
    '${escapeSql(data.whatsapp_name || '')}',
    NULL,
    NULL,
    NULL,
    NULL,
    'novo',
    'greeting',
    '{}'::jsonb,
    0,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
  )
  ON CONFLICT (phone_number) DO UPDATE SET
    whatsapp_name = COALESCE(EXCLUDED.whatsapp_name, conversations.whatsapp_name),
    last_message_at = CURRENT_TIMESTAMP,
    updated_at = CURRENT_TIMESTAMP,
    state_machine_state = CASE
      WHEN conversations.state_machine_state IN ('completed', 'handoff_comercial')
      THEN 'greeting'
      ELSE conversations.state_machine_state
    END
  RETURNING *
`.trim();

// Log para debug
console.log('=== BUILD SQL QUERIES (FIXED) ===');
console.log('Phone with code:', phone_with_code);
console.log('Phone without code:', phone_without_code);
console.log('Queries built successfully as STRINGS');

// IMPORTANTE: Retornar cada query como campo string individual
return {
  ...data,
  query_count: query_count,        // String SQL
  query_details: query_details,    // String SQL
  query_upsert: query_upsert       // String SQL
};"""

            # Atualizar o código
            if 'parameters' in node and 'jsCode' in node['parameters']:
                node['parameters']['jsCode'] = new_code
                fixed = True
                print("✅ Código do node atualizado")

    if not fixed:
        print("⚠️ Node 'Build SQL Queries' não encontrado")
        return False

    # Salvar arquivo corrigido
    output_path = workflow_path.replace('.json', '_QUERY_FIXED.json')
    print(f"\n💾 Salvando workflow corrigido: {output_path}")

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(workflow, f, indent=2, ensure_ascii=False)
        print(f"✅ Arquivo salvo com sucesso!")
        print(f"\n📋 Próximos passos:")
        print(f"1. Importar no n8n: {output_path}")
        print(f"2. Desativar workflow V17 antigo")
        print(f"3. Ativar novo workflow corrigido")
        return True
    except Exception as e:
        print(f"❌ Erro ao salvar arquivo: {e}")
        return False

if __name__ == "__main__":
    success = fix_workflow_v17()
    sys.exit(0 if success else 1)