#!/usr/bin/env python3
"""
Correção FINAL v4 - Resolve problema de variáveis não sendo substituídas
Cria arquivo com nome limpo e configuração correta
"""

import json
import sys
from pathlib import Path

def create_final_workflow():
    """Cria o workflow final com todas as correções aplicadas"""

    # Ler o workflow base
    input_path = "/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V1_MENU_FIXED_v3_COMPLETE_FIX_v4_FINAL_FIX_v5_AUTH_FIXED_FINAL_AUTH.json"

    if not Path(input_path).exists():
        # Tentar arquivo alternativo
        input_path = "/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V1_MENU_FIXED_v3.json"

    print(f"📄 Lendo workflow base: {Path(input_path).name}")
    with open(input_path, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    fixes_applied = []

    # Procurar e corrigir o nó Send WhatsApp Response
    for node in workflow.get('nodes', []):
        if node.get('name') == 'Send WhatsApp Response':
            print(f"\n🔧 Corrigindo nó: {node['name']}")

            # CORREÇÃO CRÍTICA: bodyParametersJson deve ser string com placeholders
            # mas headerParametersJson deve ser JSON real
            node['parameters'] = {
                "authentication": "none",
                "requestMethod": "POST",
                "url": "http://e2bot-evolution-dev:8080/message/sendText/e2-solucoes-bot",
                "allowUnauthorizedCerts": False,
                "responseFormat": "json",
                "jsonParameters": True,
                "options": {},
                # Headers como JSON string (n8n não interpreta placeholders aqui)
                "headerParametersJson": '{\n  "apikey": "ae569043cfa169380c378347f91a1141ea572541d2d1cadbed222db519c8a891",\n  "Content-Type": "application/json"\n}',
                # CRÍTICO: Body como string com placeholders para n8n interpretar
                "bodyParametersJson": '{\n  "number": "{{ $json.phone_number }}",\n  "text": "{{ $json.response }}"\n}',
                "queryParametersJson": ""
            }

            fixes_applied.append("Send WhatsApp Response - Variáveis configuradas para substituição")
            print("   ✅ Headers com API Key (JSON estático)")
            print("   ✅ Body com placeholders (para n8n substituir)")
            print("   ✅ URL endpoint correto")

        # Garantir que Prepare Update Data retorna os dados corretos
        elif node.get('name') == 'Prepare Update Data':
            print(f"\n🔍 Ajustando nó: {node['name']}")

            # Código otimizado para garantir output correto
            clean_code = '''// Preparar dados para atualização do banco e resposta
const inputData = $input.first().json;

// 1. Extrair e limpar phone_number
let phone_number = inputData.phone_number || '';

// Remover @s.whatsapp.net se existir
if (phone_number && phone_number.includes('@')) {
  phone_number = phone_number.split('@')[0];
}

// Remover caracteres não numéricos
phone_number = phone_number.replace(/[^0-9]/g, '');

// Adicionar código do país 55 se não tiver
if (phone_number && phone_number.length <= 11 && !phone_number.startsWith('55')) {
  phone_number = '55' + phone_number;
}

// 2. Preparar resposta e estado
const response = inputData.response || 'Olá! Como posso ajudar?';
const stageData = inputData.stageData || {};
const newState = inputData.newState || inputData.state || 'greeting';
const collectedData = inputData.collectedData || {};

// 3. Preparar JSON seguro para PostgreSQL
const safeCollectedData = JSON.stringify(collectedData)
  .replace(/\\\\/g, '\\\\\\\\')
  .replace(/"/g, '\\\\"')
  .replace(/'/g, "''")
  .replace(/\\n/g, '\\\\n')
  .replace(/\\r/g, '\\\\r')
  .replace(/\\t/g, '\\\\t');

// 4. DEBUG - Log para verificação
console.log('Phone Number:', phone_number);
console.log('Response:', response);

// 5. RETORNAR dados estruturados
return {
  phone_number: phone_number,       // CRÍTICO: Este campo é usado no Send WhatsApp
  response: response,                // CRÍTICO: Este campo é usado no Send WhatsApp
  state: newState,
  collected_data_json: safeCollectedData,
  stage_data: stageData,
  collected_data: collectedData,
  alwaysOutputData: true            // Garantir output mesmo se vazio
};'''

            node['parameters']['jsCode'] = clean_code
            fixes_applied.append("Prepare Update Data - Output garantido com phone_number e response")
            print("   ✅ Limpeza e formatação de phone_number")
            print("   ✅ Garantia de output dos campos críticos")
            print("   ✅ Debug logs adicionados")

    # Salvar com nome limpo
    output_path = "/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V1_MENU_FIXED_v4.json"

    # Atualizar metadata do workflow
    workflow['name'] = "02 - AI Agent Conversation V1 Menu (Fixed v4)"

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Workflow salvo com nome limpo:")
    print(f"   {output_path}")

    print(f"\n📋 Correções aplicadas:")
    for fix in fixes_applied:
        print(f"   • {fix}")

    return output_path

def validate_workflow(workflow_path):
    """Valida que o workflow está correto"""
    print("\n🔍 Validando workflow...")

    with open(workflow_path, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    for node in workflow.get('nodes', []):
        if node.get('name') == 'Send WhatsApp Response':
            params = node.get('parameters', {})
            body = params.get('bodyParametersJson', '')
            headers = params.get('headerParametersJson', '')

            # Verificar que body tem placeholders
            if '{{ $json.phone_number }}' in body and '{{ $json.response }}' in body:
                print("   ✅ Body contém placeholders corretos")
            else:
                print("   ❌ ERRO: Body não contém placeholders!")
                return False

            # Verificar que headers tem API key
            if 'ae569043' in headers:
                print("   ✅ Headers contém API Key")
            else:
                print("   ❌ ERRO: Headers sem API Key!")
                return False

            # Verificar URL
            if params.get('url') == 'http://e2bot-evolution-dev:8080/message/sendText/e2-solucoes-bot':
                print("   ✅ URL endpoint correto")
            else:
                print("   ❌ ERRO: URL incorreto!")
                return False

    print("   ✅ Workflow validado com sucesso!")
    return True

def main():
    print("🚀 CRIANDO WORKFLOW FINAL CORRIGIDO v4")
    print("=" * 60)
    print("Objetivo: Resolver problema de variáveis não sendo substituídas")
    print("=" * 60)

    # Criar workflow corrigido
    output = create_final_workflow()

    # Validar
    if validate_workflow(output):
        print("\n" + "=" * 60)
        print("✅ WORKFLOW CRIADO E VALIDADO COM SUCESSO!")
        print("\n📋 INSTRUÇÕES FINAIS:")
        print("")
        print("1. Acesse n8n: http://localhost:5678")
        print("")
        print("2. Delete TODOS os workflows antigos")
        print("")
        print("3. Importe o novo workflow:")
        print(f"   {output}")
        print("")
        print("4. Após importar, abra o workflow e:")
        print("   - Verifique o nó 'Send WhatsApp Response'")
        print("   - Confirme que Body Parameters tem:")
        print('     { "number": "{{ $json.phone_number }}", "text": "{{ $json.response }}" }')
        print("")
        print("5. ATIVE o workflow")
        print("")
        print("6. Teste enviando mensagem no WhatsApp")
        print("")
        print("⚠️  IMPORTANTE:")
        print("   As variáveis {{ $json.xxx }} devem aparecer em LARANJA no n8n")
        print("   Se aparecerem como texto preto, há um problema")
        print("=" * 60)
    else:
        print("\n❌ Erro na validação! Verifique o workflow manualmente.")

if __name__ == "__main__":
    main()