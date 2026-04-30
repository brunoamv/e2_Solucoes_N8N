#!/usr/bin/env python3
"""
Fix workflow V9 - Corrige formatação do phone_number para incluir código do país
Problema: phone_number está chegando sem o código 55 do Brasil
"""

import json

# Ler o workflow v8
with open('/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V8.json', 'r') as f:
    workflow = json.load(f)

print("🔍 Analisando problema de formatação de telefone...")
print("   - Erro: phone_number sem código do país (55)")
print("   - Recebido: 6181755748")
print("   - Esperado: 556181755748")

# Corrigir o Prepare Update Data para garantir código do país
for node in workflow['nodes']:
    if node['name'] == 'Prepare Update Data':
        print("🔧 Corrigindo Prepare Update Data...")

        node['parameters']['jsCode'] = """// Preparar dados para atualização do banco e resposta
const inputData = $input.first().json;

// DEBUG - Ver o que está chegando
console.log('=== PREPARE UPDATE DATA DEBUG ===');
console.log('Input phone_number:', inputData.phone_number);
console.log('Input response_text:', inputData.response_text);

// 1. Phone number - GARANTIR código do país 55
let phone_number = String(inputData.phone_number || '');

// Limpar caracteres não numéricos
phone_number = phone_number.replace(/[^0-9]/g, '');

// Remover @s.whatsapp.net se existir
if (phone_number.includes('@')) {
  phone_number = phone_number.split('@')[0];
}

// IMPORTANTE: Adicionar código 55 se não tiver
if (phone_number && !phone_number.startsWith('55')) {
  // Se tem 10 ou 11 dígitos (formato brasileiro), adiciona 55
  if (phone_number.length === 10 || phone_number.length === 11) {
    phone_number = '55' + phone_number;
    console.log('Adicionado código 55:', phone_number);
  }
  // Se tem 12 ou 13 dígitos começando com outro código, mantém
  else if (phone_number.length >= 12) {
    console.log('Número já tem código de país:', phone_number);
  }
  // Qualquer outro caso, tenta adicionar 55
  else {
    phone_number = '55' + phone_number;
    console.log('Formato desconhecido, adicionado 55:', phone_number);
  }
}

console.log('Phone formatado final:', phone_number);

// 2. Resposta e estado do State Machine
const response_text = inputData.response_text || 'Olá! Como posso ajudar?';
const next_stage = inputData.next_stage || inputData.current_state || 'greeting';
const collected_data = inputData.collected_data || {};

// 3. Preparar JSON para o banco (PostgreSQL JSONB)
const collected_data_json = JSON.stringify(collected_data);

// 4. RETORNAR dados estruturados para os próximos nós
return {
  // Para o Send WhatsApp Response - CRÍTICO
  phone_number: phone_number, // Agora sempre com 55
  response_text: response_text,

  // Para Update Conversation State
  next_stage: next_stage,
  collected_data: collected_data,
  collected_data_json: collected_data_json,

  // Metadata
  timestamp: new Date().toISOString(),

  // Garantir output
  alwaysOutputData: true
};"""

        print("✅ Prepare Update Data corrigido!")
        print("   - Lógica robusta para adicionar código 55")
        print("   - Debug logs para verificação")
        break

# Também vamos garantir que o State Machine está passando o phone_number corretamente
for node in workflow['nodes']:
    if node['name'] == 'State Machine Logic':
        print("🔧 Verificando State Machine Logic...")

        code = node['parameters']['functionCode']

        # Verificar se o leadId está sendo extraído corretamente
        if 'const leadId = items[0].json.phone_number;' in code:
            print("   - State Machine está pegando phone_number corretamente")

        # Adicionar log para debug do phone_number no início
        if 'const leadId = items[0].json.phone_number;' in code:
            new_code = code.replace(
                'const leadId = items[0].json.phone_number;',
                """const leadId = items[0].json.phone_number;
console.log('=== PHONE NUMBER DEBUG ===');
console.log('Raw phone from webhook:', leadId);"""
            )
            node['parameters']['functionCode'] = new_code
            print("✅ Debug adicionado ao State Machine para phone_number")

# Verificar também o nó Send WhatsApp Response
for node in workflow['nodes']:
    if node['name'] == 'Send WhatsApp Response':
        print("🔧 Verificando Send WhatsApp Response...")

        # Verificar se está usando o campo correto
        params = node.get('parameters', {})
        body_params = params.get('bodyParameters', {}).get('parameters', [])

        for param in body_params:
            if param.get('name') == 'number':
                current_value = param.get('value', '')
                if 'Prepare Update Data' in current_value and 'phone_number' in current_value:
                    print("   ✅ Send WhatsApp está usando o campo correto")
                else:
                    print("   ⚠️ Ajustando referência ao phone_number")
                    param['value'] = '={{ $node["Prepare Update Data"].json["phone_number"] }}'

# Atualizar metadados do workflow
workflow['name'] = "02 - AI Agent Conversation V9 (Phone Format Fix)"
workflow['versionId'] = "v9-phone-format-fix"

# Salvar novo workflow
output_path = '/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V9.json'
with open(output_path, 'w') as f:
    json.dump(workflow, f, indent=2, ensure_ascii=False)

print("\n✅ Workflow V9 criado com sucesso!")
print(f"📄 Arquivo: {output_path}")
print("\n🔄 Principais correções:")
print("1. ✅ Phone number sempre formatado com código 55")
print("2. ✅ Lógica robusta para diferentes formatos de entrada")
print("3. ✅ Debug logs para rastrear formatação")
print("4. ✅ Validação do campo no Send WhatsApp Response")

print("\n📋 Como funciona agora:")
print("  - Se número tem 10 ou 11 dígitos → adiciona 55")
print("  - Se número já começa com 55 → mantém")
print("  - Se número tem 12+ dígitos → assume que já tem código")
print("  - Qualquer outro caso → adiciona 55 por segurança")

print("\n🚀 Teste esperado:")
print("1. Número 6181755748 → 556181755748")
print("2. Número 11981755748 → 5511981755748")
print("3. Número 556181755748 → 556181755748 (mantém)")
print("4. Mensagens devem ser enviadas corretamente")