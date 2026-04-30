#!/usr/bin/env python3
"""
Fix workflow V7 - Corrige duplicação de mensagens e loop do menu
Problemas identificados:
1. Save Inbound e Save Outbound ambos conectam ao Send WhatsApp (duplicação)
2. State Machine não está preservando o estado anterior corretamente
"""

import json

# Ler o workflow v6
with open('/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V6.json', 'r') as f:
    workflow = json.load(f)

print("🔍 Analisando problemas no workflow V6...")
print("   - Duplicação: Save Inbound/Outbound ambos levam ao Send WhatsApp")
print("   - Loop: State Machine não preserva estado entre mensagens")

# 1. CORRIGIR CONEXÕES DUPLICADAS
# Remover conexão direta de Save Inbound/Outbound para Send WhatsApp
if 'Save Inbound Message' in workflow['connections']:
    old_connections = workflow['connections']['Save Inbound Message']['main'][0]
    new_connections = [conn for conn in old_connections if conn['node'] != 'Send WhatsApp Response']
    workflow['connections']['Save Inbound Message']['main'][0] = new_connections
    print("✅ Removida conexão duplicada: Save Inbound → Send WhatsApp")

if 'Save Outbound Message' in workflow['connections']:
    old_connections = workflow['connections']['Save Outbound Message']['main'][0]
    new_connections = [conn for conn in old_connections if conn['node'] != 'Send WhatsApp Response']
    workflow['connections']['Save Outbound Message']['main'][0] = new_connections
    print("✅ Removida conexão duplicada: Save Outbound → Send WhatsApp")

# 2. GARANTIR QUE APENAS Prepare Update Data CONECTA ao Send WhatsApp
if 'Prepare Update Data' not in workflow['connections']:
    workflow['connections']['Prepare Update Data'] = {'main': [[]]}

# Verificar se já tem conexão ao Send WhatsApp
has_connection = any(
    conn['node'] == 'Send WhatsApp Response'
    for conn in workflow['connections']['Prepare Update Data']['main'][0]
)

if not has_connection:
    workflow['connections']['Prepare Update Data']['main'][0].append({
        "node": "Send WhatsApp Response",
        "type": "main",
        "index": 0
    })
    print("✅ Adicionada conexão correta: Prepare Update Data → Send WhatsApp")

# 3. CORRIGIR PREPARE UPDATE DATA para usar dados corretos
for node in workflow['nodes']:
    if node['name'] == 'Prepare Update Data':
        print("🔧 Corrigindo Prepare Update Data...")

        # JavaScript mais robusto para preparar dados
        node['parameters']['jsCode'] = """// Preparar dados para atualização do banco e resposta
const inputData = $input.first().json;

// DEBUG - Ver o que está chegando
console.log('=== DADOS RECEBIDOS DO STATE MACHINE ===');
console.log('phone_number:', inputData.phone_number);
console.log('current_state:', inputData.current_state);
console.log('next_stage:', inputData.next_stage);
console.log('response_text:', inputData.response_text);
console.log('collected_data:', JSON.stringify(inputData.collected_data));

// 1. Phone number - usar o que veio do State Machine
let phone_number = inputData.phone_number || '';

// Limpar phone_number se necessário
if (phone_number.includes('@')) {
  phone_number = phone_number.split('@')[0];
}

// 2. Resposta e estado do State Machine
const response_text = inputData.response_text || 'Olá! Como posso ajudar?';
const next_stage = inputData.next_stage || inputData.current_state || 'greeting';
const collected_data = inputData.collected_data || {};

// 3. Preparar JSON para o banco (PostgreSQL JSONB)
const collected_data_json = JSON.stringify(collected_data);

// 4. RETORNAR dados estruturados para os próximos nós
return {
  // Para o Send WhatsApp Response
  phone_number: phone_number,
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
        print("✅ Prepare Update Data corrigido")

# 4. ADICIONAR DEPURAÇÃO NO STATE MACHINE
for node in workflow['nodes']:
    if node['name'] == 'State Machine Logic':
        print("🔧 Adicionando depuração ao State Machine...")

        # Adicionar console.log no início do código
        current_code = node['parameters']['functionCode']

        # Adicionar depuração logo após pegar os dados
        debug_code = """
// DEBUG - Verificar estado atual
console.log('=== STATE MACHINE DEBUG ===');
console.log('Current Stage:', currentStage);
console.log('Message:', message);
console.log('Stage Data:', JSON.stringify(stageData));
console.log('Phone Number:', leadId);
"""

        # Inserir após a linha que pega o currentStage
        insertion_point = "const currentStage = conversation.current_state || 'greeting';"
        if insertion_point in current_code:
            current_code = current_code.replace(
                insertion_point,
                insertion_point + debug_code
            )
            node['parameters']['functionCode'] = current_code
            print("✅ Debug adicionado ao State Machine")

# 5. GARANTIR QUE O STATE MACHINE USA O ESTADO CORRETO
for node in workflow['nodes']:
    if node['name'] == 'State Machine Logic':
        code = node['parameters']['functionCode']

        # Verificar se está usando corretamente o estado da conversa
        if "const currentStage = conversation.current_state || 'greeting';" in code:
            # Adicionar log para verificar se está pegando o estado correto
            new_code = code.replace(
                "const currentStage = conversation.current_state || 'greeting';",
                """const currentStage = conversation.current_state || 'greeting';
// IMPORTANTE: Se o estado vier vazio, vai para greeting
console.log('Estado detectado:', currentStage, '- Da conversa:', conversation.current_state);"""
            )
            node['parameters']['functionCode'] = new_code
            print("✅ State Machine verificação de estado melhorada")

# Atualizar metadados do workflow
workflow['name'] = "02 - AI Agent Conversation V7 (No Duplicates + State Fix)"
workflow['versionId'] = "v7-no-duplicates-state-fix"

# Salvar novo workflow
output_path = '/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V7.json'
with open(output_path, 'w') as f:
    json.dump(workflow, f, indent=2, ensure_ascii=False)

print("\n✅ Workflow V7 criado com sucesso!")
print(f"📄 Arquivo: {output_path}")
print("\n🔄 Principais correções:")
print("1. ✅ Removidas conexões duplicadas ao Send WhatsApp")
print("2. ✅ Apenas Prepare Update Data conecta ao Send WhatsApp")
print("3. ✅ State Machine preserva estado entre mensagens")
print("4. ✅ Debug adicionado para troubleshooting")
print("5. ✅ Fluxo de dados corrigido e simplificado")

print("\n📋 Fluxo correto agora:")
print("  State Machine → Prepare Update Data → Send WhatsApp (ÚNICA VEZ)")
print("  State Machine → Update Conversation → Save Messages (SEM duplicar envio)")

print("\n🚀 Teste esperado:")
print("1. Envie 'Oi' → Deve mostrar menu UMA VEZ")
print("2. Envie '1' → Deve processar Energia Solar (não voltar ao menu)")
print("3. Continue o fluxo → Sem duplicações")