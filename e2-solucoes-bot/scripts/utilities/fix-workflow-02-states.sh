#!/bin/bash

# Fix Workflow 02 - Correct State Names Script
# Updates the State Machine Logic to use Portuguese state names that match DB constraints

echo "🔧 Fixing Workflow 02 AI Agent - State Names Issue"
echo "=================================="

# Backup original workflow
cp /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V1_MENU.json \
   /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V1_MENU.json.backup_$(date +%s)

# Create fixed JavaScript code for the State Machine Logic node
cat > /tmp/fixed_state_machine.js << 'EOF'
// ============================================================================
// E2 Soluções Bot v1 - Menu State Machine (FIXED STATE NAMES)
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
    current_state: 'novo',
    collected_data: {}
  };
  conversationId = null; // Será criado no CREATE
}

const currentStage = conversation.current_state || 'novo';
const stageData = conversation.collected_data || {};

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
    id: 'projeto_eletrico',
    name: 'Projetos Elétricos',
    description: 'Projetos elétricos, adequações e laudos de conformidade',
    emoji: '📐'
  },
  '4': {
    id: 'armazenamento_energia',
    name: 'BESS (Armazenamento)',
    description: 'Sistemas de armazenamento de energia com baterias',
    emoji: '🔋'
  },
  '5': {
    id: 'analise_laudo',
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
    const cleaned = input.replace(/\D/g, '');
    const regex = /^(\d{2})(\d{4,5})(\d{4})$/;
    return regex.test(cleaned) && cleaned.length >= 10 && cleaned.length <= 11;
  },

  email_or_skip: (input) => {
    const trimmed = input.trim().toLowerCase();
    if (trimmed === 'pular') return true;
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
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
    text: '🤖 Olá! Bem-vindo à *E2 Soluções*!\n\nSomos especialistas em engenharia elétrica.\n\n*Escolha o serviço desejado:*\n\n☀️ 1 - Energia Solar\n⚡ 2 - Subestação\n📐 3 - Projetos Elétricos\n🔋 4 - BESS (Armazenamento)\n📊 5 - Análise e Laudos\n\n_Digite o número de 1 a 5:_',
    footer: 'E2 Soluções Engenharia'
  },

  service_selected: {
    template: '{{emoji}} *{{service_name}}*\n\n{{description}}\n\n━━━━━━━━━━━━━━━\n\nPerfeito! Vou coletar alguns dados para melhor atendê-lo.\n\n👤 *Qual seu nome completo?*'
  },

  collect_phone: {
    text: '📱 *Qual seu telefone com DDD?*\n\n_Exemplo: (62) 99988-7766_'
  },

  collect_email: {
    text: '📧 *Qual seu email?*\n\n_Ou digite "pular" para não informar_'
  },

  collect_city: {
    text: '📍 *Em qual cidade você está?*\n\n_Exemplo: Goiânia_'
  },

  confirmation: {
    template: '✅ *Dados confirmados!*\n\n👤 *Nome:* {{lead_name}}\n📱 *Telefone:* {{phone}}\n📧 *Email:* {{email}}\n📍 *Cidade:* {{city}}\n{{emoji}} *Serviço:* {{service_name}}\n\n━━━━━━━━━━━━━━━\n\n🗓️ Deseja agendar uma *visita técnica gratuita*?\n\n1️⃣ Sim, quero agendar\n2️⃣ Não, prefiro falar com especialista\n\n_Digite 1 ou 2:_'
  },

  invalid_option: {
    text: '❌ Opção inválida. Por favor, escolha uma opção válida.'
  },

  invalid_phone: {
    text: '❌ Telefone inválido.\n\n📱 Digite um telefone válido com DDD:\n_Exemplo: (62) 99988-7766_'
  },

  invalid_email: {
    text: '❌ Email inválido.\n\n📧 Digite um email válido ou "pular":\n_Exemplo: seu@email.com_'
  },

  error_generic: {
    text: '⚠️ Ops! Algo deu errado.\n\nPor favor, tente novamente ou digite *AJUDA* para falar com um especialista.'
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
// State Machine Logic with FIXED STATE NAMES
// ============================================================================

let nextStage = currentStage;
let responseText = '';
let updateData = { ...stageData };
let errorCount = stageData.error_count || 0;
const MAX_ERRORS = 3;

// Map DB states to internal logic states for easier switch handling
const internalStage = currentStage === 'novo' ? 'greeting' :
                     currentStage === 'identificando_servico' ? 'service_selection' :
                     currentStage === 'coletando_dados' ? (stageData.stage_step || 'collect_name') :
                     currentStage === 'agendando' ? 'scheduling' :
                     currentStage === 'concluido' ? 'completed' :
                     currentStage;

switch (internalStage) {
  case 'greeting':
    responseText = templates.greeting.text;
    nextStage = 'identificando_servico';  // Use Portuguese state name
    break;

  case 'service_selection':
    if (validators.number_1_to_5(message)) {
      const service = serviceMapping[message];
      updateData.service_type = service.id;
      updateData.service_name = service.name;
      updateData.service_emoji = service.emoji;
      updateData.stage_step = 'collect_name';

      responseText = fillTemplate(templates.service_selected.template, {
        emoji: service.emoji,
        service_name: service.name,
        description: service.description
      });

      nextStage = 'coletando_dados';  // Use Portuguese state name
      errorCount = 0;
    } else {
      responseText = templates.invalid_option.text + '\n\n' + templates.greeting.text;
      errorCount++;

      if (errorCount >= MAX_ERRORS) {
        nextStage = 'handoff_comercial';
        responseText = '⚠️ Percebi dificuldades. Vou transferir você para um especialista.\n\nAguarde um momento...';
      }
    }
    break;

  case 'collect_name':
    if (validators.text_min_3_chars(message)) {
      updateData.lead_name = message.trim();
      updateData.stage_step = 'collect_phone';
      responseText = templates.collect_phone.text;
      nextStage = 'coletando_dados';  // Stay in data collection
      errorCount = 0;
    } else {
      responseText = '❌ Nome muito curto.\n\n👤 Digite seu nome completo:';
      errorCount++;

      if (errorCount >= MAX_ERRORS) {
        nextStage = 'handoff_comercial';
        responseText = '⚠️ Vou transferir você para um especialista.\n\nAguarde...';
      }
    }
    break;

  case 'collect_phone':
    if (validators.phone_brazil(message)) {
      const cleaned = message.replace(/\D/g, '');
      const formatted = cleaned.replace(/(\d{2})(\d{4,5})(\d{4})/, '($1) $2-$3');
      updateData.phone = formatted;
      updateData.stage_step = 'collect_email';
      responseText = templates.collect_email.text;
      nextStage = 'coletando_dados';  // Stay in data collection
      errorCount = 0;
    } else {
      responseText = templates.invalid_phone.text;
      errorCount++;

      if (errorCount >= MAX_ERRORS) {
        nextStage = 'handoff_comercial';
        responseText = '⚠️ Vou transferir você para um especialista.\n\nAguarde...';
      }
    }
    break;

  case 'collect_email':
    if (validators.email_or_skip(message)) {
      const trimmed = message.trim().toLowerCase();
      updateData.email = trimmed === 'pular' ? 'Não informado' : trimmed;
      updateData.stage_step = 'collect_city';
      responseText = templates.collect_city.text;
      nextStage = 'coletando_dados';  // Stay in data collection
      errorCount = 0;
    } else {
      responseText = templates.invalid_email.text;
      errorCount++;

      if (errorCount >= MAX_ERRORS) {
        nextStage = 'handoff_comercial';
        responseText = '⚠️ Vou transferir você para um especialista.\n\nAguarde...';
      }
    }
    break;

  case 'collect_city':
    if (validators.city_name(message)) {
      updateData.city = message.trim();
      updateData.stage_step = 'confirmation';

      responseText = fillTemplate(templates.confirmation.template, {
        lead_name: updateData.lead_name,
        phone: updateData.phone,
        email: updateData.email,
        city: updateData.city,
        emoji: updateData.service_emoji,
        service_name: updateData.service_name
      });

      nextStage = 'coletando_dados';  // Stay in data collection until confirmed
      errorCount = 0;
    } else {
      responseText = '❌ Cidade inválida.\n\n📍 Digite o nome da cidade:';
      errorCount++;

      if (errorCount >= MAX_ERRORS) {
        nextStage = 'handoff_comercial';
        responseText = '⚠️ Vou transferir você para um especialista.\n\nAguarde...';
      }
    }
    break;

  case 'confirmation':
    if (validators.confirmation_1_or_2(message)) {
      const choice = parseInt(message);

      if (choice === 1) {
        // User wants to schedule
        nextStage = 'agendando';  // Use Portuguese state name
        updateData.wants_appointment = true;
        responseText = '🗓️ Perfeito! Vou verificar os horários disponíveis...\n\n⏳ Aguarde um momento.';
      } else {
        // User wants to speak with specialist
        nextStage = 'handoff_comercial';
        updateData.wants_appointment = false;
        responseText = '👨‍💼 Entendi! Vou transferir você para um especialista da equipe.\n\n⏳ Aguarde um momento...';
      }

      errorCount = 0;
    } else {
      responseText = '❌ Opção inválida.\n\n_Digite 1 para agendar ou 2 para falar com especialista:_';
      errorCount++;

      if (errorCount >= MAX_ERRORS) {
        nextStage = 'handoff_comercial';
        responseText = '⚠️ Vou transferir você para um especialista.\n\nAguarde...';
      }
    }
    break;

  case 'handoff_comercial':
    responseText = '👨‍💼 Você foi transferido para nossa equipe comercial.\n\nEm breve um especialista entrará em contato!\n\n_Horário de atendimento: Segunda a Sexta, 8h às 18h_';
    nextStage = 'concluido';  // Use Portuguese state name
    break;

  case 'completed':
    responseText = '✅ Seu atendimento já foi finalizado.\n\nPara iniciar uma nova conversa, digite *NOVO*.';

    if (message.toLowerCase().includes('novo')) {
      responseText = templates.greeting.text;
      nextStage = 'identificando_servico';  // Use Portuguese state name
      updateData = {};
    } else {
      nextStage = 'concluido';  // Stay in completed state
    }
    break;

  default:
    responseText = templates.error_generic.text;
    nextStage = 'novo';  // Use Portuguese state name
}

// Update error count
updateData.error_count = errorCount;

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
];
EOF

echo "✅ Fixed State Machine JavaScript created"

# Create Python script to update the JSON workflow
cat > /tmp/fix_workflow.py << 'EOF'
import json

# Read the workflow
with open('/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V1_MENU.json', 'r') as f:
    workflow = json.load(f)

# Read the fixed JavaScript code
with open('/tmp/fixed_state_machine.js', 'r') as f:
    fixed_code = f.read()

# Find and update the State Machine Logic node
for node in workflow['nodes']:
    if node['id'] == 'node_state_machine':
        # Update the type to n8n-nodes-base.code and typeVersion to 2
        node['type'] = 'n8n-nodes-base.code'
        node['typeVersion'] = 2

        # Update the parameters
        if 'functionCode' in node['parameters']:
            del node['parameters']['functionCode']
        node['parameters']['jsCode'] = fixed_code
        print("✅ Updated State Machine Logic node")
        break

# Also fix the credential references
for node in workflow['nodes']:
    if 'credentials' in node and 'postgres' in node['credentials']:
        # Fix the credential ID
        node['credentials']['postgres'] = {
            "id": "VXA1r8sd0TMIdPvS",
            "name": "PostgreSQL - E2 Bot"
        }

# Also fix the Update Conversation State node to use executeQuery properly
for node in workflow['nodes']:
    if node['name'] == 'Update Conversation State':
        node['parameters'] = {
            "operation": "executeQuery",
            "query": "=UPDATE conversations SET current_state = '{{ $json.next_stage.replace(/'/g, \"''\") }}', collected_data = '{{ JSON.stringify($json.collected_data).replace(/'/g, \"''\") }}', updated_at = NOW() WHERE phone_number = '{{ $json.phone_number.replace(/'/g, \"''\") }}' RETURNING id",
            "options": {}
        }
        node['typeVersion'] = 2.5
        print("✅ Updated Update Conversation State node")
        break

# Also fix the Check If Scheduling node to check for 'agendando' instead of 'scheduling'
for node in workflow['nodes']:
    if node['name'] == 'Check If Scheduling':
        node['parameters']['conditions']['string'][0]['value2'] = 'agendando'
        print("✅ Updated Check If Scheduling node")
        break

# Write the fixed workflow
with open('/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V1_MENU_FIXED.json', 'w') as f:
    json.dump(workflow, f, indent=2, ensure_ascii=False)

print("✅ Fixed workflow written to 02_ai_agent_conversation_V1_MENU_FIXED.json")
EOF

# Run the Python script
python3 /tmp/fix_workflow.py

echo ""
echo "✅ Workflow has been fixed!"
echo ""
echo "📋 Summary of changes:"
echo "  1. Fixed state names to use Portuguese (novo, identificando_servico, coletando_dados, etc.)"
echo "  2. Updated State Machine Logic node to use Code type with version 2"
echo "  3. Fixed PostgreSQL credential references"
echo "  4. Updated Check If Scheduling to check for 'agendando' instead of 'scheduling'"
echo "  5. Fixed Update Conversation State node to use executeQuery properly"
echo ""
echo "📁 Files created:"
echo "  - Original backup: 02_ai_agent_conversation_V1_MENU.json.backup_*"
echo "  - Fixed workflow: 02_ai_agent_conversation_V1_MENU_FIXED.json"
echo ""
echo "📝 Next steps:"
echo "  1. Import the fixed workflow in n8n UI (http://localhost:5678)"
echo "  2. Deactivate the old workflow"
echo "  3. Activate the fixed workflow"
echo "  4. Test with a WhatsApp message"

# Clean up temporary files
rm /tmp/fixed_state_machine.js /tmp/fix_workflow.py