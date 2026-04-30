#!/usr/bin/env python3
"""
Fix workflow V8 - Corrige erro de inicialização de stageData
Problema: stageData está sendo usada antes de ser declarada (linha 32 antes da linha 35)
"""

import json

# Ler o workflow v7
with open('/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V7.json', 'r') as f:
    workflow = json.load(f)

print("🔍 Analisando problema no State Machine Logic...")
print("   - Erro: stageData usada antes de ser declarada")
print("   - Linha 32: console.log usa stageData")
print("   - Linha 35: stageData é declarada")

# Encontrar e corrigir o State Machine Logic
for node in workflow['nodes']:
    if node['name'] == 'State Machine Logic':
        print("🔧 Corrigindo State Machine Logic...")

        # Novo código corrigido com ordem correta das variáveis
        node['parameters']['functionCode'] = """// ============================================================================
// E2 Soluções Bot v1 - Menu State Machine
// ============================================================================

const items = $input.all();
const leadId = items[0].json.phone_number;
const message = items[0].json.content || items[0].json.body || items[0].json.text || '';

// Get conversation state
let conversation;
let conversationId;

if (items.length > 1 && items[1].json) {
  conversation = items[1].json;
  conversationId = conversation.id; // Pegar o UUID do banco
} else {
  conversation = {
    phone_number: leadId,
    current_state: 'greeting',
    collected_data: {}
  };
  conversationId = null; // Será criado no CREATE
}

// IMPORTANTE: Declarar stageData ANTES de usar
const currentStage = conversation.current_state || 'greeting';
const stageData = conversation.collected_data || {};

// DEBUG - Agora stageData já está declarada
console.log('=== STATE MACHINE DEBUG ===');
console.log('Current Stage:', currentStage);
console.log('Message:', message);
console.log('Stage Data:', JSON.stringify(stageData)); // Agora funciona!
console.log('Phone Number:', leadId);
console.log('Conversation ID:', conversationId);

// ============================================================================
// Service Mapping
// ============================================================================

const serviceMapping = {
  '1': {
    id: 'energia_solar',
    name: 'Energia Solar',
    description: 'Projetos fotovoltaicos residenciais, comerciais e industriais',
    emoji: '☀️'
  },
  '2': {
    id: 'subestacao',
    name: 'Subestação',
    description: 'Reforma, manutenção e construção de subestações',
    emoji: '⚡'
  },
  '3': {
    id: 'projetos_eletricos',
    name: 'Projetos Elétricos',
    description: 'Projetos elétricos, adequações e laudos de conformidade',
    emoji: '📐'
  },
  '4': {
    id: 'bess',
    name: 'BESS (Armazenamento)',
    description: 'Sistemas de armazenamento de energia com baterias',
    emoji: '🔋'
  },
  '5': {
    id: 'analise_laudos',
    name: 'Análise e Laudos',
    description: 'Análise de qualidade de energia e laudos técnicos',
    emoji: '📊'
  }
};

// ============================================================================
// Validators
// ============================================================================

const validators = {
  number_1_to_5: (input) => {
    const num = parseInt(input.trim());
    return num >= 1 && num <= 5;
  },

  text_min_3_chars: (input) => {
    return input.trim().length >= 3;
  },

  phone_brazil: (input) => {
    const cleaned = input.replace(/\\D/g, '');
    const regex = /^(\\d{2})(\\d{4,5})(\\d{4})$/;
    return regex.test(cleaned) && cleaned.length >= 10 && cleaned.length <= 11;
  },

  email_or_skip: (input) => {
    const trimmed = input.trim().toLowerCase();
    if (trimmed === 'pular') return true;
    const emailRegex = /^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/;
    return emailRegex.test(trimmed);
  },

  city_name: (input) => {
    return input.trim().length >= 3;
  },

  confirmation_1_or_2: (input) => {
    const num = parseInt(input.trim());
    return num === 1 || num === 2;
  }
};

// ============================================================================
// Message Templates
// ============================================================================

const templates = {
  greeting: {
    text: '🤖 Olá! Bem-vindo à *E2 Soluções*!\\n\\nSomos especialistas em engenharia elétrica.\\n\\n*Escolha o serviço desejado:*\\n\\n☀️ 1 - Energia Solar\\n⚡ 2 - Subestação\\n📐 3 - Projetos Elétricos\\n🔋 4 - BESS (Armazenamento)\\n📊 5 - Análise e Laudos\\n\\n_Digite o número de 1 a 5:_',
    footer: 'E2 Soluções Engenharia'
  },

  service_selected: {
    template: '{{emoji}} *{{service_name}}*\\n\\n{{description}}\\n\\n━━━━━━━━━━━━━━━\\n\\nPerfeito! Vou coletar alguns dados para melhor atendê-lo.\\n\\n👤 *Qual seu nome completo?*'
  },

  collect_phone: {
    text: '📱 *Qual seu telefone com DDD?*\\n\\n_Exemplo: (62) 99988-7766_'
  },

  collect_email: {
    text: '📧 *Qual seu email?*\\n\\n_Ou digite "pular" para não informar_'
  },

  collect_city: {
    text: '📍 *Em qual cidade você está?*\\n\\n_Exemplo: Goiânia_'
  },

  confirmation: {
    template: '✅ *Dados confirmados!*\\n\\n👤 *Nome:* {{lead_name}}\\n📱 *Telefone:* {{phone}}\\n📧 *Email:* {{email}}\\n📍 *Cidade:* {{city}}\\n{{emoji}} *Serviço:* {{service_name}}\\n\\n━━━━━━━━━━━━━━━\\n\\n🗓️ Deseja agendar uma *visita técnica gratuita*?\\n\\n1️⃣ Sim, quero agendar\\n2️⃣ Não, prefiro falar com especialista\\n\\n_Digite 1 ou 2:_'
  },

  invalid_option: {
    text: '❌ Opção inválida. Por favor, escolha uma opção válida.'
  },

  invalid_phone: {
    text: '❌ Telefone inválido.\\n\\n📱 Digite um telefone válido com DDD:\\n_Exemplo: (62) 99988-7766_'
  },

  invalid_email: {
    text: '❌ Email inválido.\\n\\n📧 Digite um email válido ou "pular":\\n_Exemplo: seu@email.com_'
  },

  error_generic: {
    text: '⚠️ Ops! Algo deu errado.\\n\\nPor favor, tente novamente ou digite *AJUDA* para falar com um especialista.'
  }
};

// ============================================================================
// Template Filler
// ============================================================================

function fillTemplate(template, data) {
  let text = template;
  for (const [key, value] of Object.entries(data)) {
    text = text.replace(new RegExp(`{{${key}}}`, 'g'), value);
  }
  return text;
}

// ============================================================================
// State Machine Logic
// ============================================================================

let nextStage = currentStage;
let responseText = '';
let updateData = { ...stageData };
let errorCount = stageData.error_count || 0;
const MAX_ERRORS = 3;

// DEBUG - Log antes do switch
console.log('Processing stage:', currentStage, 'with message:', message);

switch (currentStage) {
  case 'greeting':
    responseText = templates.greeting.text;
    nextStage = 'service_selection';
    break;

  case 'service_selection':
    if (validators.number_1_to_5(message)) {
      const service = serviceMapping[message];
      updateData.service_type = service.id;
      updateData.service_name = service.name;
      updateData.service_emoji = service.emoji;

      responseText = fillTemplate(templates.service_selected.template, {
        emoji: service.emoji,
        service_name: service.name,
        description: service.description
      });

      nextStage = 'collect_name';
      errorCount = 0;
    } else {
      responseText = templates.invalid_option.text + '\\n\\n' + templates.greeting.text;
      errorCount++;

      if (errorCount >= MAX_ERRORS) {
        nextStage = 'handoff_comercial';
        responseText = '⚠️ Percebi dificuldades. Vou transferir você para um especialista.\\n\\nAguarde um momento...';
      }
    }
    break;

  case 'collect_name':
    if (validators.text_min_3_chars(message)) {
      updateData.lead_name = message.trim();
      responseText = templates.collect_phone.text;
      nextStage = 'collect_phone';
      errorCount = 0;
    } else {
      responseText = '❌ Nome muito curto.\\n\\n👤 Digite seu nome completo:';
      errorCount++;

      if (errorCount >= MAX_ERRORS) {
        nextStage = 'handoff_comercial';
        responseText = '⚠️ Vou transferir você para um especialista.\\n\\nAguarde...';
      }
    }
    break;

  case 'collect_phone':
    if (validators.phone_brazil(message)) {
      const cleaned = message.replace(/\\D/g, '');
      const formatted = cleaned.replace(/(\\d{2})(\\d{4,5})(\\d{4})/, '($1) $2-$3');
      updateData.phone = formatted;
      responseText = templates.collect_email.text;
      nextStage = 'collect_email';
      errorCount = 0;
    } else {
      responseText = templates.invalid_phone.text;
      errorCount++;

      if (errorCount >= MAX_ERRORS) {
        nextStage = 'handoff_comercial';
        responseText = '⚠️ Vou transferir você para um especialista.\\n\\nAguarde...';
      }
    }
    break;

  case 'collect_email':
    if (validators.email_or_skip(message)) {
      const trimmed = message.trim().toLowerCase();
      updateData.email = trimmed === 'pular' ? 'Não informado' : trimmed;
      responseText = templates.collect_city.text;
      nextStage = 'collect_city';
      errorCount = 0;
    } else {
      responseText = templates.invalid_email.text;
      errorCount++;

      if (errorCount >= MAX_ERRORS) {
        nextStage = 'handoff_comercial';
        responseText = '⚠️ Vou transferir você para um especialista.\\n\\nAguarde...';
      }
    }
    break;

  case 'collect_city':
    if (validators.city_name(message)) {
      updateData.city = message.trim();

      responseText = fillTemplate(templates.confirmation.template, {
        lead_name: updateData.lead_name,
        phone: updateData.phone,
        email: updateData.email,
        city: updateData.city,
        emoji: updateData.service_emoji,
        service_name: updateData.service_name
      });

      nextStage = 'confirmation';
      errorCount = 0;
    } else {
      responseText = '❌ Cidade inválida.\\n\\n📍 Digite o nome da cidade:';
      errorCount++;

      if (errorCount >= MAX_ERRORS) {
        nextStage = 'handoff_comercial';
        responseText = '⚠️ Vou transferir você para um especialista.\\n\\nAguarde...';
      }
    }
    break;

  case 'confirmation':
    if (validators.confirmation_1_or_2(message)) {
      const choice = parseInt(message);

      if (choice === 1) {
        // User wants to schedule
        nextStage = 'scheduling';
        updateData.wants_appointment = true;
        responseText = '🗓️ Perfeito! Vou verificar os horários disponíveis...\\n\\n⏳ Aguarde um momento.';
      } else {
        // User wants to speak with specialist
        nextStage = 'handoff_comercial';
        updateData.wants_appointment = false;
        responseText = '👨‍💼 Entendi! Vou transferir você para um especialista da equipe.\\n\\n⏳ Aguarde um momento...';
      }

      errorCount = 0;
    } else {
      responseText = '❌ Opção inválida.\\n\\n_Digite 1 para agendar ou 2 para falar com especialista:_';
      errorCount++;

      if (errorCount >= MAX_ERRORS) {
        nextStage = 'handoff_comercial';
        responseText = '⚠️ Vou transferir você para um especialista.\\n\\nAguarde...';
      }
    }
    break;

  case 'handoff_comercial':
    responseText = '👨‍💼 Você foi transferido para nossa equipe comercial.\\n\\nEm breve um especialista entrará em contato!\\n\\n_Horário de atendimento: Segunda a Sexta, 8h às 18h_';
    nextStage = 'completed';
    break;

  case 'completed':
    responseText = '✅ Seu atendimento já foi finalizado.\\n\\nPara iniciar uma nova conversa, digite *NOVO*.';

    if (message.toLowerCase().includes('novo')) {
      responseText = templates.greeting.text;
      nextStage = 'service_selection';
      updateData = {};
    }
    break;

  default:
    responseText = templates.error_generic.text;
    nextStage = 'greeting';
}

// Update error count
updateData.error_count = errorCount;

// DEBUG - Log resultado
console.log('Next stage:', nextStage);
console.log('Response prepared');

// ============================================================================
// Return Output
// ============================================================================

return [
  {
    json: {
      phone_number: leadId,
      conversation_id: conversationId,
      message: message,
      current_state: currentStage,
      next_stage: nextStage,
      collected_data: updateData,
      response_text: responseText,
      timestamp: new Date().toISOString()
    }
  }
];"""

        print("✅ State Machine Logic corrigido!")
        print("   - stageData agora é declarada ANTES de ser usada")
        print("   - Debug logs reorganizados corretamente")
        print("   - Adicionados logs extras para troubleshooting")
        break

# Atualizar metadados do workflow
workflow['name'] = "02 - AI Agent Conversation V8 (StageData Fix)"
workflow['versionId'] = "v8-stagedata-fix"

# Salvar novo workflow
output_path = '/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V8.json'
with open(output_path, 'w') as f:
    json.dump(workflow, f, indent=2, ensure_ascii=False)

print("\n✅ Workflow V8 criado com sucesso!")
print(f"📄 Arquivo: {output_path}")
print("\n🔄 Principais correções:")
print("1. ✅ stageData declarada ANTES de ser usada nos console.log")
print("2. ✅ Ordem correta das variáveis no State Machine")
print("3. ✅ Debug logs reorganizados para funcionar corretamente")
print("4. ✅ Adicionados logs extras para troubleshooting")

print("\n📋 Ordem correta agora:")
print("  Linha ~25: const currentStage = ...")
print("  Linha ~26: const stageData = ... (DECLARAÇÃO)")
print("  Linha ~28: console.log(...stageData) (USO - agora funciona!)")

print("\n🚀 Teste esperado:")
print("1. Importe o V8 no n8n")
print("2. O State Machine deve funcionar sem erros de inicialização")
print("3. Os logs de debug devem aparecer no console do n8n")