#!/usr/bin/env python3
"""
Script COMPLETO para corrigir TODOS os problemas do workflow 02
- Corrige endpoint de envio para Evolution API v2.3.7
- Corrige referências de dados para evitar undefined
- Configura headers e body corretamente
"""

import json
import sys
from pathlib import Path

def fix_workflow_complete(workflow_path):
    """Aplica todas as correções necessárias no workflow"""

    print(f"📄 Lendo workflow: {workflow_path}")
    with open(workflow_path, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    fixes_applied = []

    # Procurar por todos os nós que precisam correção
    for node in workflow.get('nodes', []):

        # 1. Corrigir o nó Send WhatsApp Response
        if node.get('name') == 'Send WhatsApp Response':
            print(f"\n🔧 Corrigindo nó: {node['name']}")

            # Verificar qual nó anterior tem os dados
            # Os dados vêm do "Prepare Update Data" que já tem phone_number e response

            # Atualizar parâmetros
            node['parameters'] = {
                "authentication": "none",
                "requestMethod": "POST",
                "url": "http://e2bot-evolution-dev:8080/message/send/text",
                "allowUnauthorizedCerts": False,
                "responseFormat": "json",
                "jsonParameters": True,
                "options": {},
                "headerParametersUi": {
                    "parameter": [
                        {
                            "name": "apikey",
                            "value": "ae569043cfa169380c378347f91a1141ea572541d2d1cadbed222db519c8a891"
                        },
                        {
                            "name": "Content-Type",
                            "value": "application/json"
                        }
                    ]
                },
                "queryParametersUi": {},
                # CRÍTICO: Usar os dados do nó anterior corretamente
                # O nó anterior "Prepare Update Data" já tem phone_number e response
                "bodyParametersJson": json.dumps({
                    "instance": "e2-solucoes-bot",
                    "to": "{{ $json.phone_number }}@s.whatsapp.net",
                    "text": "{{ $json.response }}",
                    "options": {
                        "delay": 1200,
                        "presence": "composing"
                    }
                }, indent=2)
            }

            fixes_applied.append("Send WhatsApp Response - Endpoint e referências")
            print("   ✅ URL: http://e2bot-evolution-dev:8080/message/send/text")
            print("   ✅ Método: POST")
            print("   ✅ Headers: apikey e Content-Type")
            print("   ✅ Body: Usando $json.phone_number e $json.response")

        # 2. Garantir que Prepare Update Data passa os dados corretos
        elif node.get('name') == 'Prepare Update Data':
            print(f"\n🔍 Verificando nó: {node['name']}")

            # Verificar se o código está passando phone_number e response
            code = node['parameters'].get('jsCode', '')

            # Adicionar verificação para garantir que phone_number e response são passados
            if 'phone_number' not in code or 'response' not in code:
                print("   ⚠️  Ajustando código para garantir phone_number e response...")

                # Atualizar o código para sempre incluir phone_number e response
                new_code = '''// Preparar dados para atualização
const inputData = $input.first().json;

// Dados essenciais que sempre devem ser passados
const phone_number = inputData.phone_number || '';
const response = inputData.response || '';
const stageData = inputData.stageData || {};
const newState = inputData.newState || inputData.state || 'greeting';
const collectedData = inputData.collectedData || {};

// Preparar JSON seguro para PostgreSQL
const safeCollectedData = JSON.stringify(collectedData)
  .replace(/\\\\/g, '\\\\\\\\')
  .replace(/"/g, '\\\\"')
  .replace(/'/g, "''")
  .replace(/\\n/g, '\\\\n')
  .replace(/\\r/g, '\\\\r')
  .replace(/\\t/g, '\\\\t');

// IMPORTANTE: Sempre retornar phone_number e response
return {
  phone_number: phone_number,
  response: response,
  state: newState,
  collected_data_json: safeCollectedData,
  stage_data: stageData,
  collected_data: collectedData,
  alwaysOutputData: true
};'''

                node['parameters']['jsCode'] = new_code
                fixes_applied.append("Prepare Update Data - Garantir phone_number e response")
                print("   ✅ Código atualizado para sempre passar phone_number e response")

    # Salvar workflow corrigido
    output_path = workflow_path.replace('.json', '_COMPLETE_FIX_v4.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Workflow corrigido salvo em: {output_path}")
    print(f"\n📋 Correções aplicadas:")
    for fix in fixes_applied:
        print(f"   • {fix}")

    return output_path

def main():
    workflow_path = "/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V1_MENU_FIXED_v3.json"

    if not Path(workflow_path).exists():
        print(f"❌ Arquivo não encontrado: {workflow_path}")
        sys.exit(1)

    print("🔧 CORREÇÃO COMPLETA DO WORKFLOW 02")
    print("=" * 60)
    print("Problemas a corrigir:")
    print("1. Endpoint incorreto da Evolution API")
    print("2. Valores undefined (phone_number e response)")
    print("3. Headers e autenticação")
    print("=" * 60)

    output = fix_workflow_complete(workflow_path)

    print("\n" + "=" * 60)
    print("✅ SUCESSO! Workflow completamente corrigido!")
    print("\n📋 PRÓXIMOS PASSOS:")
    print("1. Acesse n8n: http://localhost:5678")
    print("2. Importe o arquivo:")
    print(f"   {output}")
    print("3. Desative o workflow antigo")
    print("4. Ative o novo workflow")
    print("5. Teste enviando uma mensagem no WhatsApp")
    print("\n💡 DICA: Se ainda houver undefined, verifique no n8n:")
    print("   - Clique no nó 'Send WhatsApp Response'")
    print("   - Veja se os dados estão chegando do nó anterior")
    print("   - Use o modo 'Execute Previous Nodes' para debug")

if __name__ == "__main__":
    main()