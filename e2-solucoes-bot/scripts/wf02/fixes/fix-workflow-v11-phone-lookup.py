#!/usr/bin/env python3
"""
Fix workflow V11 - Corrige lookup de phone_number para incluir código 55
Problema: Get Conversation Count busca sem código 55, mas banco tem com 55
Solução: Adicionar formatação de phone no Validate Input Data
"""

import json

# Ler o workflow v10
with open('/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V10.json', 'r') as f:
    workflow = json.load(f)

print("🔍 Analisando problema de lookup de telefone...")
print("   - Erro: Get Conversation Count busca '6181755748'")
print("   - Banco tem: '556181755748' (adicionado pelo V9)")
print("   - Resultado: Sempre cria nova conversa, sempre mostra menu")

# Corrigir o Validate Input Data para formatar phone ANTES do lookup
for node in workflow['nodes']:
    if node['name'] == 'Validate Input Data':
        print("🔧 Corrigindo Validate Input Data...")

        # Adicionar lógica de formatação com código 55
        node['parameters']['jsCode'] = """// Validação de entrada do Workflow 01
const inputData = $input.first().json;

// Validação crítica do phone_number
if (!inputData.phone_number || inputData.phone_number === 'undefined') {
    throw new Error('Phone number is required but was not received from Workflow 01');
}

// Limpar e validar formato do phone_number
let phone_number = String(inputData.phone_number).replace(/[^0-9]/g, '');

// Remover @s.whatsapp.net se existir
if (phone_number.includes('@')) {
  phone_number = phone_number.split('@')[0];
}

// IMPORTANTE: Adicionar código 55 se não tiver (MOVIDO DO PREPARE UPDATE DATA)
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

// Validação de formato brasileiro (DDD + número) - AGORA COM 55
if (phone_number.length < 12 || phone_number.length > 13) {
    console.warn(`Phone number format unusual: ${phone_number} (expected 12-13 digits with country code)`);
}

console.log('Validated input:', {
    phone_number: phone_number,  // Agora já tem 55
    whatsapp_name: inputData.whatsapp_name,
    message_type: inputData.message_type
});

return {
    phone_number: phone_number,  // COM código 55
    whatsapp_name: inputData.whatsapp_name || '',
    message: inputData.message || '',
    message_type: inputData.message_type || 'text',
    media_url: inputData.media_url || null,
    message_id: inputData.message_id || '',
    timestamp: inputData.timestamp || new Date().toISOString()
};"""

        print("✅ Validate Input Data corrigido!")
        print("   - Phone formatado COM código 55 ANTES do lookup")
        break

# Simplificar o Prepare Update Data já que o phone já vem formatado
for node in workflow['nodes']:
    if node['name'] == 'Prepare Update Data':
        print("🔧 Simplificando Prepare Update Data...")

        node['parameters']['jsCode'] = """// Preparar dados para atualização do banco e resposta
const inputData = $input.first().json;

// DEBUG - Ver o que está chegando
console.log('=== PREPARE UPDATE DATA DEBUG ===');
console.log('Input phone_number:', inputData.phone_number);
console.log('Input response_text:', inputData.response_text);

// 1. Phone number - JÁ VEM COM código 55 do Validate Input Data
let phone_number = String(inputData.phone_number || '');

// Apenas garantir que está limpo (sem caracteres especiais)
phone_number = phone_number.replace(/[^0-9]/g, '');

console.log('Phone final:', phone_number);

// 2. Resposta e estado do State Machine
const response_text = inputData.response_text || 'Olá! Como posso ajudar?';
const next_stage = inputData.next_stage || inputData.current_state || 'greeting';
const collected_data = inputData.collected_data || {};

// 3. Preparar JSON para o banco (PostgreSQL JSONB)
const collected_data_json = JSON.stringify(collected_data);

// 4. RETORNAR dados estruturados para os próximos nós
return {
  // Para o Send WhatsApp Response - CRÍTICO
  phone_number: phone_number, // Já tem 55 desde o início
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

        print("✅ Prepare Update Data simplificado!")
        break

# Atualizar metadados do workflow
workflow['name'] = "02 - AI Agent Conversation V11 (Phone Lookup Fix)"
workflow['versionId'] = "v11-phone-lookup-fix"

# Salvar novo workflow
output_path = '/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V11.json'
with open(output_path, 'w') as f:
    json.dump(workflow, f, indent=2, ensure_ascii=False)

print("\n✅ Workflow V11 criado com sucesso!")
print(f"📄 Arquivo: {output_path}")
print("\n🔄 Principais correções:")
print("1. ✅ Phone formatado com 55 no INÍCIO do fluxo")
print("2. ✅ Get Conversation Count agora busca '556181755748'")
print("3. ✅ Lookup no banco encontrará conversas existentes")
print("4. ✅ State Machine receberá estado correto")
print("5. ✅ Opção '1' será processada corretamente")

print("\n📋 Fluxo corrigido:")
print("  1. Webhook recebe: 6181755748")
print("  2. Validate Input: adiciona 55 → 556181755748")
print("  3. Get Conversation Count: busca 556181755748 ✓")
print("  4. Encontra conversa existente → pega estado atual")
print("  5. State Machine processa opção '1' corretamente")

print("\n🚀 Para testar:")
print("1. Importe o V11 no n8n")
print("2. Ative o workflow")
print("3. Envie mensagem '1' no WhatsApp")
print("4. Deve processar a opção, NÃO mostrar menu novamente")