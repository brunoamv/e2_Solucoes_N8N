#!/bin/bash

echo "🔧 Comprehensive Fix for Workflow 02 - State Names & Phone Number"
echo "=================================================================="

# Create backup
BACKUP_FILE="n8n/workflows/02_ai_agent_conversation_V1_MENU.json.backup_$(date +%Y%m%d_%H%M%S)"
cp n8n/workflows/02_ai_agent_conversation_V1_MENU.json "$BACKUP_FILE"
echo "✅ Backup created: $BACKUP_FILE"

# Create fixed JavaScript for State Machine Logic
cat > /tmp/state_machine_fixed.js << 'EOF'
// ============================================================================
// E2 Soluções Bot v1 - Menu State Machine (FULLY FIXED)
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
    text = text.replace(new RegExp(\`{{\${key}}}\`, 'g'), value);
  }
  return text;
}

// ============================================================================
// State Machine Logic - FULLY PORTUGUESE STATES
// ============================================================================

let nextStage = currentStage;
let responseText = '';
let updateData = { ...stageData };
let errorCount = stageData.error_count || 0;
const MAX_ERRORS = 3;

// Map database states to internal logic for processing
// This helps maintain readable switch cases
const internalStage = currentStage === 'novo' ? 'greeting' :
                     currentStage === 'identificando_servico' ? 'service_selection' :
                     currentStage === 'coletando_dados' ? (stageData.stage_step || 'collect_name') :
                     currentStage === 'agendando' ? 'scheduling' :
                     currentStage === 'agendado' ? 'scheduled' :
                     currentStage === 'handoff_comercial' ? 'handoff' :
                     currentStage === 'concluido' ? 'completed' :
                     currentStage;

switch (internalStage) {
  case 'greeting':
    responseText = templates.greeting.text;
    nextStage = 'identificando_servico';  // Portuguese state
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

      nextStage = 'coletando_dados';  // Portuguese state
      errorCount = 0;
    } else {
      responseText = templates.invalid_option.text + '\n\n' + templates.greeting.text;
      errorCount++;

      if (errorCount >= MAX_ERRORS) {
        nextStage = 'handoff_comercial';  // Portuguese state
        responseText = '⚠️ Percebi dificuldades. Vou transferir você para um especialista.\n\nAguarde um momento...';
      }
    }
    break;

  case 'collect_name':
    if (validators.text_min_3_chars(message)) {
      updateData.lead_name = message.trim();
      updateData.stage_step = 'collect_phone';
      responseText = templates.collect_phone.text;
      nextStage = 'coletando_dados';  // Stay in Portuguese state
      errorCount = 0;
    } else {
      responseText = '❌ Nome muito curto.\n\n👤 Digite seu nome completo:';
      errorCount++;

      if (errorCount >= MAX_ERRORS) {
        nextStage = 'handoff_comercial';  // Portuguese state
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
      nextStage = 'coletando_dados';  // Stay in Portuguese state
      errorCount = 0;
    } else {
      responseText = templates.invalid_phone.text;
      errorCount++;

      if (errorCount >= MAX_ERRORS) {
        nextStage = 'handoff_comercial';  // Portuguese state
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
      nextStage = 'coletando_dados';  // Stay in Portuguese state
      errorCount = 0;
    } else {
      responseText = templates.invalid_email.text;
      errorCount++;

      if (errorCount >= MAX_ERRORS) {
        nextStage = 'handoff_comercial';  // Portuguese state
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

      nextStage = 'coletando_dados';  // Stay in Portuguese state for confirmation
      errorCount = 0;
    } else {
      responseText = '❌ Cidade inválida.\n\n📍 Digite o nome da cidade:';
      errorCount++;

      if (errorCount >= MAX_ERRORS) {
        nextStage = 'handoff_comercial';  // Portuguese state
        responseText = '⚠️ Vou transferir você para um especialista.\n\nAguarde...';
      }
    }
    break;

  case 'confirmation':
    if (validators.confirmation_1_or_2(message)) {
      const choice = parseInt(message);

      if (choice === 1) {
        // User wants to schedule
        nextStage = 'agendando';  // Portuguese state
        updateData.wants_appointment = true;
        responseText = '🗓️ Perfeito! Vou verificar os horários disponíveis...\n\n⏳ Aguarde um momento.';
      } else {
        // User wants to speak with specialist
        nextStage = 'handoff_comercial';  // Portuguese state
        updateData.wants_appointment = false;
        responseText = '👨‍💼 Entendi! Vou transferir você para um especialista da equipe.\n\n⏳ Aguarde um momento...';
      }

      errorCount = 0;
    } else {
      responseText = '❌ Opção inválida.\n\n_Digite 1 para agendar ou 2 para falar com especialista:_';
      errorCount++;

      if (errorCount >= MAX_ERRORS) {
        nextStage = 'handoff_comercial';  // Portuguese state
        responseText = '⚠️ Vou transferir você para um especialista.\n\nAguarde...';
      }
    }
    break;

  case 'handoff':
    responseText = '👨‍💼 Você foi transferido para nossa equipe comercial.\n\nEm breve um especialista entrará em contato!\n\n_Horário de atendimento: Segunda a Sexta, 8h às 18h_';
    nextStage = 'concluido';  // Portuguese state
    break;

  case 'completed':
    responseText = '✅ Seu atendimento já foi finalizado.\n\nPara iniciar uma nova conversa, digite *NOVO*.';

    if (message.toLowerCase().includes('novo')) {
      responseText = templates.greeting.text;
      nextStage = 'identificando_servico';  // Portuguese state
      updateData = {};
    }
    break;

  default:
    responseText = templates.error_generic.text;
    nextStage = 'novo';  // Portuguese state
}

// Update error count
updateData.error_count = errorCount;

// ============================================================================
// Return Output - ENSURE PHONE NUMBER IS INCLUDED
// ============================================================================

return [
  {
    json: {
      phone_number: leadId,  // This must be passed correctly
      conversation_id: conversationId,
      message: message,
      current_state: currentStage,
      next_stage: nextStage,  // This will be Portuguese state
      collected_data: updateData,
      response_text: responseText,
      timestamp: new Date().toISOString()
    }
  }
];
EOF

echo "✅ Fixed State Machine JavaScript created"

# Now update the workflow JSON with the fixed script
python3 << 'PYTHON'
import json
import sys

# Read the workflow
with open('n8n/workflows/02_ai_agent_conversation_V1_MENU.json', 'r') as f:
    workflow = json.load(f)

# Read the fixed JavaScript
with open('/tmp/state_machine_fixed.js', 'r') as f:
    fixed_js = f.read()

# Find and update the State Machine Logic node
for node in workflow['nodes']:
    if node.get('name') == 'State Machine Logic':
        # Change node type to Code (version 2)
        node['type'] = 'n8n-nodes-base.code'
        node['typeVersion'] = 2

        # Replace functionCode with jsCode
        if 'functionCode' in node.get('parameters', {}):
            del node['parameters']['functionCode']

        # Set the fixed JavaScript
        node['parameters'] = {
            'jsCode': fixed_js
        }
        print("✅ Updated State Machine Logic node")

    # Fix the Update Conversation State node
    elif node.get('name') == 'Update Conversation State':
        # Ensure the query uses correct template variables
        node['parameters']['query'] = "=UPDATE conversations SET current_state = '{{ $json.next_stage.replace(/'/g, \"''\") }}', collected_data = '{{ JSON.stringify($json.collected_data).replace(/'/g, \"''\") }}', updated_at = NOW() WHERE phone_number = '{{ $json.phone_number.replace(/'/g, \"''\") }}' RETURNING id"

        # Fix credentials
        if 'credentials' not in node or 'postgres' not in node.get('credentials', {}):
            node['credentials'] = {
                'postgres': {
                    'id': 'VXA1r8sd0TMIdPvS',
                    'name': 'PostgreSQL - E2 Bot'
                }
            }
        print("✅ Updated Update Conversation State node")

    # Fix the Create New Conversation node
    elif node.get('name') == 'Create New Conversation':
        # Ensure the query uses phone_number correctly
        node['parameters']['query'] = "=INSERT INTO conversations (phone_number, current_state, collected_data) VALUES ('{{ $json.phone_number.replace(/'/g, \"''\") }}', 'novo', '{}') ON CONFLICT (phone_number) DO UPDATE SET current_state = 'novo', collected_data = '{}', updated_at = NOW() RETURNING id, phone_number, current_state, collected_data, created_at, updated_at"

        # Fix credentials
        if 'credentials' not in node or 'postgres' not in node.get('credentials', {}):
            node['credentials'] = {
                'postgres': {
                    'id': 'VXA1r8sd0TMIdPvS',
                    'name': 'PostgreSQL - E2 Bot'
                }
            }
        print("✅ Updated Create New Conversation node with ON CONFLICT handling")

    # Fix the Check If Scheduling node
    elif node.get('name') == 'Check If Scheduling':
        if node.get('type') == 'n8n-nodes-base.if':
            # Update condition to check for Portuguese state
            if 'conditions' in node.get('parameters', {}):
                conditions = node['parameters']['conditions'].get('conditions', [])
                for condition in conditions:
                    if 'scheduling' in str(condition.get('rightValue', '')):
                        condition['rightValue'] = 'agendando'
                print("✅ Updated Check If Scheduling to check for 'agendando'")

# Write the fixed workflow
with open('n8n/workflows/02_ai_agent_conversation_V1_MENU_COMPREHENSIVE_FIX.json', 'w') as f:
    json.dump(workflow, f, indent=2)

print("✅ Fixed workflow written to 02_ai_agent_conversation_V1_MENU_COMPREHENSIVE_FIX.json")
PYTHON

echo ""
echo "✅ Comprehensive fix completed!"
echo ""
echo "📋 Summary of changes:"
echo "  1. ALL state names now use Portuguese (novo, identificando_servico, coletando_dados, etc.)"
echo "  2. State Machine always outputs Portuguese states for database"
echo "  3. Phone number is correctly passed through all nodes"
echo "  4. Create New Conversation now uses ON CONFLICT to handle duplicates"
echo "  5. Update Conversation State uses correct Portuguese states"
echo "  6. Check If Scheduling checks for 'agendando' instead of 'scheduling'"
echo ""
echo "📁 Files created:"
echo "  - Original backup: $BACKUP_FILE"
echo "  - Fixed workflow: 02_ai_agent_conversation_V1_MENU_COMPREHENSIVE_FIX.json"
echo ""
echo "📝 Next steps:"
echo "  1. Import the fixed workflow in n8n UI (http://localhost:5678)"
echo "  2. Deactivate ALL old workflows (V1_MENU, FIXED, etc.)"
echo "  3. Activate the COMPREHENSIVE_FIX workflow"
echo "  4. Test with a WhatsApp message"
echo ""
echo "🧹 Optional: Clean up the test conversation with empty phone:"
echo "  docker exec e2bot-postgres-dev psql -U postgres -d e2_bot -c \"DELETE FROM conversations WHERE phone_number = '' OR phone_number IS NULL;\""