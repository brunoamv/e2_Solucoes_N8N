#!/usr/bin/env python3
"""
Corrige o problema de updated_at no workflow 01
Remove a dependência de updated_at do ON CONFLICT
"""

import json
import sys
import os

def fix_workflow_01():
    """Corrige o workflow 01 para não depender de updated_at"""

    workflow_path = "/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/01_main_whatsapp_handler_V2.5_DEDUP_FIXED.json"

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

    print("🔍 Procurando node 'Save Message'...")

    # Encontrar e corrigir o node Save Message
    fixed = False
    for node in workflow.get('nodes', []):
        if node.get('name') == 'Save Message':
            print(f"✅ Node encontrado: {node['name']}")

            # Corrigir a query para não depender de updated_at
            if 'parameters' in node and 'query' in node['parameters']:
                # Nova query sem updated_at
                new_query = """=INSERT INTO messages (conversation_id, direction, content, message_type, media_url, whatsapp_message_id) VALUES (null, 'inbound', '{{ $json.content.replace(/'/g, "''") }}', '{{ $json.message_type }}', {{ $json.media_url ? "'" + $json.media_url.replace(/'/g, "''") + "'" : "null" }}, '{{ $json.message_id.replace(/'/g, "''") }}') ON CONFLICT (whatsapp_message_id) DO UPDATE SET content = EXCLUDED.content, media_url = EXCLUDED.media_url RETURNING id, created_at, CASE WHEN xmax = 0 THEN 'inserted' ELSE 'updated' END as operation"""

                node['parameters']['query'] = new_query
                fixed = True
                print("✅ Query do node atualizada (removido updated_at)")

    if not fixed:
        print("⚠️ Node 'Save Message' não encontrado")
        return False

    # Salvar arquivo corrigido
    output_path = workflow_path.replace('.json', '_NO_UPDATED_AT.json')
    print(f"\n💾 Salvando workflow corrigido: {output_path}")

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(workflow, f, indent=2, ensure_ascii=False)
        print(f"✅ Arquivo salvo com sucesso!")
        print(f"\n📋 Próximos passos:")
        print(f"1. Importar no n8n: {output_path}")
        print(f"2. Desativar workflow 01 antigo")
        print(f"3. Ativar novo workflow corrigido")
        return True
    except Exception as e:
        print(f"❌ Erro ao salvar arquivo: {e}")
        return False

if __name__ == "__main__":
    success = fix_workflow_01()
    sys.exit(0 if success else 1)