#!/usr/bin/env python3
"""
Script para corrigir o problema de undefined no nó Send WhatsApp Response
Problema: phone_number e response estão vindo como undefined
Solução: Corrigir o mapeamento de dados no workflow
"""

import json
import sys
from pathlib import Path

def fix_send_whatsapp_node(workflow_path):
    """Corrige o nó Send WhatsApp Response para usar os dados corretos"""

    print(f"📄 Lendo workflow: {workflow_path}")

    with open(workflow_path, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    # Encontrar o nó Send WhatsApp Response
    node_found = False
    for node in workflow.get('nodes', []):
        if node.get('name') == 'Send WhatsApp Response':
            node_found = True
            print(f"✅ Nó encontrado: {node['name']}")

            # Atualizar URL para Evolution API v2.3.7
            old_url = node['parameters'].get('url', '')
            print(f"   URL atual: {old_url}")

            # Corrigir para o endpoint correto da v2.3.7
            node['parameters']['url'] = "http://e2bot-evolution-dev:8080/message/send/text"
            node['parameters']['requestMethod'] = "POST"

            # Configurar o body corretamente
            # IMPORTANTE: Usar a referência correta dos dados do nó anterior
            node['parameters']['jsonParameters'] = True
            node['parameters']['options'] = {}

            # O problema está aqui - precisamos referenciar os dados corretamente
            # Os dados vêm do nó "State Machine Logic" que passa phone_number e response
            node['parameters']['bodyParametersJson'] = '''{
    "instance": "e2-solucoes-bot",
    "to": "{{ $('State Machine Logic').item.json.phone_number }}@s.whatsapp.net",
    "text": "{{ $('State Machine Logic').item.json.response }}",
    "options": {
        "delay": 1200,
        "presence": "composing"
    }
}'''

            print("   ✅ URL atualizada para: http://e2bot-evolution-dev:8080/message/send/text")
            print("   ✅ Método: POST")
            print("   ✅ Body configurado com referências corretas")

            # Adicionar header de Content-Type
            if 'headerParametersUi' not in node['parameters']:
                node['parameters']['headerParametersUi'] = {}

            node['parameters']['headerParametersUi'] = {
                "parameter": [
                    {
                        "name": "Content-Type",
                        "value": "application/json"
                    },
                    {
                        "name": "apikey",
                        "value": "ae569043cfa169380c378347f91a1141ea572541d2d1cadbed222db519c8a891"
                    }
                ]
            }

            break

    if not node_found:
        print("❌ Nó 'Send WhatsApp Response' não encontrado!")
        return False

    # Salvar o workflow corrigido
    output_path = workflow_path.replace('.json', '_SEND_FIXED.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print(f"✅ Workflow corrigido salvo em: {output_path}")
    print("\n📋 INSTRUÇÕES:")
    print("1. Importe o novo workflow no n8n")
    print("2. Desative o workflow antigo")
    print("3. Ative o novo workflow")
    print("4. Teste enviando uma mensagem")

    return True

def main():
    # Caminho do workflow 02
    workflow_path = "/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V1_MENU_FIXED_v3.json"

    if not Path(workflow_path).exists():
        print(f"❌ Arquivo não encontrado: {workflow_path}")
        sys.exit(1)

    print("🔧 Corrigindo problema de undefined no Send WhatsApp Response")
    print("=" * 60)

    if fix_send_whatsapp_node(workflow_path):
        print("\n✅ Correção aplicada com sucesso!")
        print("\n⚠️  IMPORTANTE:")
        print("O problema de 'undefined' ocorre porque o nó estava tentando")
        print("acessar {{$json.phone_number}} diretamente, mas os dados")
        print("estão no contexto do nó 'State Machine Logic'.")
        print("\nAgora está usando: {{ $('State Machine Logic').item.json.phone_number }}")
    else:
        print("\n❌ Falha ao aplicar correção")
        sys.exit(1)

if __name__ == "__main__":
    main()