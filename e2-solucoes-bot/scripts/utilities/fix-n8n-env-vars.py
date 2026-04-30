#!/usr/bin/env python3
"""
Script para corrigir variáveis de ambiente no workflow n8n
Corrige o problema de variáveis undefined no nó Send WhatsApp Response
"""

import json
import sys
from datetime import datetime

def fix_workflow():
    """Corrige o workflow do n8n para usar URL fixa no ambiente de desenvolvimento"""

    workflow_path = 'n8n/workflows/02_ai_agent_conversation_V1_MENU_FIXED_v5.json'
    output_path = 'n8n/workflows/02_ai_agent_conversation_V1_MENU_FIXED_v6.json'

    print(f"🔧 Iniciando correção do workflow n8n...")
    print(f"📖 Lendo arquivo: {workflow_path}")

    try:
        # Carregar workflow
        with open(workflow_path, 'r', encoding='utf-8') as f:
            workflow = json.load(f)

        print(f"✅ Workflow carregado com sucesso")
        print(f"📊 Total de nós: {len(workflow.get('nodes', []))}")

        # Encontrar e corrigir o nó Send WhatsApp Response
        node_found = False
        for node in workflow.get('nodes', []):
            if node.get('name') == 'Send WhatsApp Response':
                node_found = True
                print(f"\n🎯 Nó encontrado: '{node['name']}'")
                print(f"   Tipo: {node.get('type')}")
                print(f"   ID: {node.get('id')}")

                # Backup da configuração atual
                old_url = node.get('parameters', {}).get('url', 'não definida')
                print(f"\n   ❌ URL antiga: {old_url}")

                # Aplicar correção - URL fixa para desenvolvimento
                node['parameters']['url'] = 'http://e2bot-evolution-dev:8080/message/sendText/e2-solucoes-bot'
                print(f"   ✅ URL nova: {node['parameters']['url']}")

                # Garantir método HTTP correto
                if 'httpMethod' not in node['parameters']:
                    node['parameters']['httpMethod'] = 'POST'
                    print(f"   ✅ Método HTTP definido: POST")

                # Garantir que está enviando headers
                node['parameters']['sendHeaders'] = True
                print(f"   ✅ sendHeaders ativado")

                # Configurar header de autenticação com API Key
                node['parameters']['headerParameters'] = {
                    "parameters": [
                        {
                            "name": "apikey",
                            "value": "ae569043cfa169380c378347f91a1141ea572541d2d1cadbed222db519c8a891"
                        },
                        {
                            "name": "Content-Type",
                            "value": "application/json"
                        }
                    ]
                }
                print(f"   ✅ Headers de autenticação configurados")

                # Garantir que o body está sendo enviado corretamente
                if 'sendBody' not in node['parameters']:
                    node['parameters']['sendBody'] = True
                    print(f"   ✅ sendBody ativado")

                # Garantir formato JSON para o body
                if 'bodyContentType' not in node['parameters']:
                    node['parameters']['bodyContentType'] = 'json'
                    print(f"   ✅ bodyContentType definido como JSON")

                print(f"\n✅ Nó '{node['name']}' corrigido com sucesso!")
                break

        if not node_found:
            print("\n⚠️  AVISO: Nó 'Send WhatsApp Response' não encontrado no workflow!")
            print("    Verifique se o nome do nó está correto.")
            return False

        # Atualizar metadados
        if 'meta' not in workflow:
            workflow['meta'] = {}

        workflow['meta']['lastModified'] = datetime.now().isoformat()
        workflow['meta']['fixesApplied'] = workflow['meta'].get('fixesApplied', [])
        workflow['meta']['fixesApplied'].append(
            f"Environment variables fix - URL hardcoded for development - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        # Atualizar versionId
        workflow['versionId'] = 'v6-env-vars-fixed'

        # Salvar workflow corrigido
        print(f"\n💾 Salvando workflow corrigido em: {output_path}")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(workflow, f, indent=2, ensure_ascii=False)

        print(f"✅ Workflow salvo com sucesso!")

        # Validar JSON
        print(f"\n🔍 Validando JSON...")
        with open(output_path, 'r', encoding='utf-8') as f:
            json.load(f)
        print(f"✅ JSON válido!")

        print("\n" + "="*60)
        print("🎉 CORREÇÃO CONCLUÍDA COM SUCESSO!")
        print("="*60)
        print("\n📋 Próximos passos:")
        print("1. Acesse o n8n: http://localhost:5678")
        print("2. Importe o workflow: 02_ai_agent_conversation_V1_MENU_FIXED_v6.json")
        print("3. Desative o workflow v5 (se estiver ativo)")
        print("4. Ative o workflow v6")
        print("5. Teste enviando uma mensagem via WhatsApp")

        return True

    except FileNotFoundError:
        print(f"\n❌ ERRO: Arquivo não encontrado: {workflow_path}")
        print("    Verifique se você está executando o script do diretório correto.")
        return False
    except json.JSONDecodeError as e:
        print(f"\n❌ ERRO: Falha ao decodificar JSON: {e}")
        return False
    except Exception as e:
        print(f"\n❌ ERRO inesperado: {e}")
        return False

if __name__ == "__main__":
    success = fix_workflow()
    sys.exit(0 if success else 1)