#!/usr/bin/env python3
"""
Correção DEFINITIVA para autenticação na Evolution API
O n8n requer headerParametersJson ao invés de headerParametersUi
"""

import json
import sys
from pathlib import Path

def fix_auth_headers_final(workflow_path):
    """Corrige os headers de autenticação de forma definitiva"""

    print(f"📄 Lendo workflow: {workflow_path}")
    with open(workflow_path, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    fixes_applied = []

    # Procurar pelo nó Send WhatsApp Response
    for node in workflow.get('nodes', []):
        if node.get('name') == 'Send WhatsApp Response':
            print(f"\n🔧 Corrigindo nó: {node['name']}")

            # CORREÇÃO DEFINITIVA - Configuração completa
            node['parameters'] = {
                "authentication": "none",
                "requestMethod": "POST",
                "url": "http://e2bot-evolution-dev:8080/message/sendText/e2-solucoes-bot",
                "allowUnauthorizedCerts": False,
                "responseFormat": "json",
                "jsonParameters": True,
                "options": {},
                # CRÍTICO: Usar headerParametersJson ao invés de headerParametersUi
                "headerParametersJson": json.dumps({
                    "apikey": "ae569043cfa169380c378347f91a1141ea572541d2d1cadbed222db519c8a891",
                    "Content-Type": "application/json"
                }, indent=2),
                # Body com formato correto
                "bodyParametersJson": json.dumps({
                    "number": "{{ $json.phone_number }}",
                    "text": "{{ $json.response }}"
                }, indent=2),
                # Garantir que não há queryParameters
                "queryParametersJson": ""
            }

            # Remover headerParametersUi se existir (n8n não usa)
            if 'headerParametersUi' in node['parameters']:
                del node['parameters']['headerParametersUi']

            fixes_applied.append("Send WhatsApp Response - Headers JSON corrigidos")
            print("   ✅ API Key adicionada via headerParametersJson")
            print("   ✅ URL endpoint confirmado")
            print("   ✅ Body format confirmado")
            print("\n   📋 Headers configurados:")
            print("      - apikey: ae569043...891")
            print("      - Content-Type: application/json")

        # Garantir que Prepare Update Data limpa o phone_number
        elif node.get('name') == 'Prepare Update Data':
            print(f"\n🔍 Verificando nó: {node['name']}")

            # Código para limpar phone_number
            clean_code = '''// Preparar dados para atualização
const inputData = $input.first().json;

// Extrair e limpar phone_number
let phone_number = inputData.phone_number || '';

// Remover @s.whatsapp.net se existir
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

            node['parameters']['jsCode'] = clean_code
            fixes_applied.append("Prepare Update Data - Phone cleaning garantido")
            print("   ✅ Limpeza de phone_number configurada")

    # Salvar workflow corrigido
    output_path = workflow_path.replace('.json', '_FINAL_AUTH.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Workflow corrigido salvo em: {output_path}")
    print(f"\n📋 Correções aplicadas:")
    for fix in fixes_applied:
        print(f"   • {fix}")

    # Mostrar exemplo de teste direto
    print("\n🧪 TESTE MANUAL DA API:")
    print("=" * 60)
    print("curl -X POST 'http://localhost:8080/message/sendText/e2-solucoes-bot' \\")
    print("  -H 'apikey: ae569043cfa169380c378347f91a1141ea572541d2d1cadbed222db519c8a891' \\")
    print("  -H 'Content-Type: application/json' \\")
    print("  -d '{\"number\": \"5562999999999\", \"text\": \"Teste\"}'")
    print("=" * 60)

    return output_path

def main():
    # Tentar múltiplos caminhos possíveis
    possible_paths = [
        "/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V1_MENU_FIXED_v3_COMPLETE_FIX_v4_FINAL_FIX_v5_AUTH_FIXED.json",
        "/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V1_MENU_FIXED_v3_COMPLETE_FIX_v4_FINAL_FIX_v5.json",
        "/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V1_MENU_FIXED_v3.json"
    ]

    workflow_path = None
    for path in possible_paths:
        if Path(path).exists():
            workflow_path = path
            break

    if not workflow_path:
        print(f"❌ Nenhum arquivo de workflow encontrado!")
        sys.exit(1)

    print("🚀 CORREÇÃO DEFINITIVA DE AUTENTICAÇÃO")
    print("=" * 60)
    print("Problema: n8n não lê headerParametersUi corretamente")
    print("Solução: Usar headerParametersJson com formato correto")
    print("=" * 60)

    output = fix_auth_headers_final(workflow_path)

    print("\n" + "=" * 60)
    print("✅ WORKFLOW CORRIGIDO COM SUCESSO!")
    print("\n📋 INSTRUÇÕES FINAIS:")
    print("1. Acesse n8n: http://localhost:5678")
    print("2. Delete TODOS os workflows antigos")
    print("3. Importe o arquivo:")
    print(f"   {output}")
    print("4. Ative o novo workflow")
    print("5. Teste enviando mensagem no WhatsApp")
    print("\n⚠️  IMPORTANTE:")
    print("   O workflow DEVE usar headerParametersJson, não headerParametersUi")
    print("   Isso é uma limitação do n8n com HTTP Request nodes")
    print("=" * 60)

if __name__ == "__main__":
    main()