#!/usr/bin/env python3
"""
Script para corrigir o erro de tipo de autenticação no workflow n8n
Remove configuração inválida de genericCredentialType
"""

import json
import sys
from datetime import datetime

def fix_auth_type():
    """Corrige o tipo de autenticação no workflow v6"""

    workflow_path = 'n8n/workflows/02_ai_agent_conversation_V1_MENU_FIXED_v6.json'
    output_path = 'n8n/workflows/02_ai_agent_conversation_V1_MENU_FIXED_v7.json'

    print(f"🔧 Iniciando correção do tipo de autenticação...")
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

                # Log configuração atual
                print(f"\n📋 Configuração atual:")
                if 'authentication' in node.get('parameters', {}):
                    print(f"   authentication: {node['parameters']['authentication']}")
                if 'genericAuthType' in node.get('parameters', {}):
                    print(f"   genericAuthType: {node['parameters']['genericAuthType']}")
                if 'credentials' in node:
                    print(f"   credentials: {node['credentials']}")

                # Remover configurações problemáticas
                if 'authentication' in node.get('parameters', {}):
                    del node['parameters']['authentication']
                    print(f"\n   ✅ Removido campo 'authentication'")

                if 'genericAuthType' in node.get('parameters', {}):
                    del node['parameters']['genericAuthType']
                    print(f"   ✅ Removido campo 'genericAuthType'")

                # Remover bloco de credenciais se existir
                if 'credentials' in node:
                    del node['credentials']
                    print(f"   ✅ Removido bloco 'credentials'")

                # Garantir que os headers estão corretos
                if 'headerParameters' not in node.get('parameters', {}):
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
                    print(f"   ✅ Headers de autenticação adicionados")
                else:
                    print(f"   ℹ️ Headers já estão configurados")

                # Garantir configurações essenciais
                node['parameters']['httpMethod'] = 'POST'
                node['parameters']['sendHeaders'] = True
                node['parameters']['sendBody'] = True
                node['parameters']['bodyContentType'] = 'json'

                print(f"\n   ✅ Configurações essenciais garantidas")
                print(f"\n✅ Nó '{node['name']}' corrigido com sucesso!")
                break

        if not node_found:
            print("\n⚠️  AVISO: Nó 'Send WhatsApp Response' não encontrado!")
            return False

        # Atualizar metadados
        if 'meta' not in workflow:
            workflow['meta'] = {}

        workflow['meta']['lastModified'] = datetime.now().isoformat()
        workflow['meta']['fixesApplied'] = workflow['meta'].get('fixesApplied', [])
        workflow['meta']['fixesApplied'].append(
            f"Authentication type fix - Removed invalid genericCredentialType - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        # Atualizar versionId
        workflow['versionId'] = 'v7-auth-type-fixed'

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
        print("2. Importe o workflow: 02_ai_agent_conversation_V1_MENU_FIXED_v7.json")
        print("3. Desative o workflow v6 (se estiver ativo)")
        print("4. Ative o workflow v7")
        print("5. Teste enviando uma mensagem via WhatsApp")

        return True

    except FileNotFoundError:
        print(f"\n❌ ERRO: Arquivo não encontrado: {workflow_path}")
        return False
    except json.JSONDecodeError as e:
        print(f"\n❌ ERRO: Falha ao decodificar JSON: {e}")
        return False
    except Exception as e:
        print(f"\n❌ ERRO inesperado: {e}")
        return False

if __name__ == "__main__":
    success = fix_auth_type()
    sys.exit(0 if success else 1)