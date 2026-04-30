#!/usr/bin/env python3
"""
CORREÇÃO FINAL - Evolution API Endpoint Correto
Problema: Endpoint errado causando 404
Solução: Usar o endpoint correto da Evolution API
"""

import json
import sys
from pathlib import Path

def fix_workflow_final(workflow_path):
    """Corrige definitivamente o endpoint da Evolution API"""

    print(f"📄 Lendo workflow: {workflow_path}")
    with open(workflow_path, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    fixes_applied = []

    # Procurar pelo nó Send WhatsApp Response
    for node in workflow.get('nodes', []):
        if node.get('name') == 'Send WhatsApp Response':
            print(f"\n🔧 Corrigindo nó: {node['name']}")

            # CORREÇÃO DEFINITIVA - Endpoint correto confirmado
            node['parameters'] = {
                "authentication": "none",
                "requestMethod": "POST",
                # ENDPOINT CORRETO: /message/sendText/{instanceName}
                "url": "http://e2bot-evolution-dev:8080/message/sendText/e2-solucoes-bot",
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
                # Body com formato correto para Evolution API
                "bodyParametersJson": json.dumps({
                    "number": "{{ $json.phone_number }}",
                    "text": "{{ $json.response }}"
                }, indent=2)
            }

            fixes_applied.append("Send WhatsApp Response - Endpoint definitivo corrigido")
            print("   ✅ URL: http://e2bot-evolution-dev:8080/message/sendText/e2-solucoes-bot")
            print("   ✅ Método: POST")
            print("   ✅ Body: {number: phone_number, text: response}")

        # Garantir que Prepare Update Data passa os dados corretos
        elif node.get('name') == 'Prepare Update Data':
            print(f"\n🔍 Ajustando nó: {node['name']}")

            # Código atualizado que garante phone_number sem @s.whatsapp.net
            new_code = '''// Preparar dados para atualização
const inputData = $input.first().json;

// Extrair e limpar phone_number (remover @s.whatsapp.net se existir)
let phone_number = inputData.phone_number || '';
if (phone_number.includes('@')) {
  phone_number = phone_number.split('@')[0];
}

// Garantir que é apenas números
phone_number = phone_number.replace(/[^0-9]/g, '');

// Adicionar código do país se não tiver
if (phone_number && !phone_number.startsWith('55')) {
  phone_number = '55' + phone_number;
}

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

// IMPORTANTE: Sempre retornar phone_number limpo e response
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
            fixes_applied.append("Prepare Update Data - Limpeza de phone_number")
            print("   ✅ Phone number será limpo (apenas números)")
            print("   ✅ Remove @s.whatsapp.net automaticamente")
            print("   ✅ Adiciona código 55 se necessário")

    # Salvar workflow corrigido
    output_path = workflow_path.replace('.json', '_FINAL_FIX_v5.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Workflow corrigido salvo em: {output_path}")
    print(f"\n📋 Correções aplicadas:")
    for fix in fixes_applied:
        print(f"   • {fix}")

    return output_path

def main():
    workflow_path = "/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V1_MENU_FIXED_v3_COMPLETE_FIX_v4.json"

    if not Path(workflow_path).exists():
        print(f"❌ Arquivo não encontrado: {workflow_path}")
        sys.exit(1)

    print("🚀 CORREÇÃO FINAL DO WORKFLOW - Evolution API")
    print("=" * 60)
    print("Endpoint correto confirmado via teste:")
    print("POST http://e2bot-evolution-dev:8080/message/sendText/e2-solucoes-bot")
    print("=" * 60)

    output = fix_workflow_final(workflow_path)

    print("\n" + "=" * 60)
    print("✅ WORKFLOW CORRIGIDO COM SUCESSO!")
    print("\n📋 INSTRUÇÕES FINAIS:")
    print("1. Acesse n8n: http://localhost:5678")
    print("2. Delete TODOS os workflows antigos de AI Agent")
    print("3. Importe o arquivo:")
    print(f"   {output}")
    print("4. Ative o novo workflow")
    print("5. Teste enviando mensagem no WhatsApp")
    print("\n✅ FORMATO CORRETO DO BODY:")
    print('   {')
    print('     "number": "5562999999999",')
    print('     "text": "Mensagem aqui"')
    print('   }')
    print("\nNÃO usa @s.whatsapp.net no número!")

if __name__ == "__main__":
    main()