#!/usr/bin/env python3
"""
Fix conversation_id null issue in V19 workflow
The State Machine Logic node needs to receive both input data AND conversation details
"""

import json
import sys
import os
from datetime import datetime

def fix_workflow_v19():
    """Fix the conversation_id flow in V19 workflow"""

    workflow_path = "/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V19.json"

    # Check if file exists
    if not os.path.exists(workflow_path):
        print(f"❌ File not found: {workflow_path}")
        return False

    print(f"📖 Reading workflow: {workflow_path}")

    try:
        with open(workflow_path, 'r', encoding='utf-8') as f:
            workflow = json.load(f)
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return False

    print("🔍 Analyzing State Machine Logic node connections...")

    # Find the State Machine Logic node
    state_machine_node = None
    for node in workflow.get('nodes', []):
        if node.get('name') == 'State Machine Logic':
            state_machine_node = node
            print(f"✅ Found State Machine Logic node: {node['id']}")
            break

    if not state_machine_node:
        print("❌ State Machine Logic node not found")
        return False

    # Fix the State Machine Logic function code to properly handle inputs
    print("🔧 Fixing State Machine Logic code to handle multiple inputs correctly...")

    new_function_code = """// ============================================================================
// E2 Soluções Bot v1 - Menu State Machine (FIXED)
// ============================================================================

const items = $input.all();
console.log('=== INPUT DEBUG ===');
console.log('Total inputs received:', items.length);
console.log('Input 0:', JSON.stringify(items[0]?.json || {}));
console.log('Input 1:', JSON.stringify(items[1]?.json || {}));

// Get basic input data (phone, message, etc)
const inputData = items[0].json;
const leadId = inputData.phone_number;
const message = inputData.content || inputData.body || inputData.text || inputData.message || '';

console.log('=== PHONE NUMBER DEBUG ===');
console.log('Raw phone from input:', leadId);
console.log('Message:', message);

// Get conversation state from database (second input if exists)
let conversation;
let conversationId;

// Check if we have conversation data from database
if (items.length > 1 && items[1].json && items[1].json.id) {
  conversation = items[1].json;
  conversationId = conversation.id; // UUID from database
  console.log('✅ Found existing conversation with ID:', conversationId);
} else {
  // New conversation - no ID yet
  conversation = {
    phone_number: leadId,
    current_state: 'greeting',
    state_machine_state: 'greeting',
    collected_data: {}
  };
  conversationId = null;
  console.log('⚠️ New conversation - no ID yet');
}

// Get current state and stage data
const currentStage = conversation.state_machine_state || conversation.state_for_machine || conversation.current_state || 'greeting';
const stageData = conversation.collected_data || {};

// DEBUG
console.log('=== STATE MACHINE DEBUG ===');
console.log('Conversation ID:', conversationId);
console.log('Current Stage:', currentStage);
console.log('Message:', message);
console.log('Stage Data:', JSON.stringify(stageData));
console.log('Phone Number:', leadId);

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
console.log('=== FINAL STATE ===');
console.log('Next stage:', nextStage);
console.log('Conversation ID being passed:', conversationId);
console.log('Response prepared');

// ============================================================================
// Return Output
// ============================================================================

return [
  {
    json: {
      phone_number: leadId,
      conversation_id: conversationId, // Will be null for new conversations, UUID for existing
      message: message,
      current_state: currentStage,
      next_stage: nextStage,
      collected_data: updateData,
      response_text: responseText,
      timestamp: new Date().toISOString()
    }
  }
];"""

    # Update the State Machine Logic node with the fixed code
    for node in workflow['nodes']:
        if node.get('name') == 'State Machine Logic':
            node['parameters']['functionCode'] = new_function_code
            print("✅ Updated State Machine Logic function code")
            break

    # Now we need to fix the connections to ensure proper data flow
    print("🔧 Fixing workflow connections for proper data flow...")

    # We need to add a Merge node to combine the input data with conversation details
    # First, let's add a Merge node
    merge_node = {
        "parameters": {},
        "id": "merge-conversation-data",
        "name": "Merge Conversation Data",
        "type": "n8n-nodes-base.merge",
        "typeVersion": 2.1,
        "position": [640, 240],
        "executeOnce": False
    }

    # Add the merge node to the workflow
    workflow['nodes'].append(merge_node)
    print("✅ Added Merge Conversation Data node")

    # Update connections to route through the merge node
    if 'connections' in workflow:
        # Update Get Conversation Details to connect to Merge node
        if 'Get Conversation Details' in workflow['connections']:
            workflow['connections']['Get Conversation Details']['main'][0][0] = {
                "node": "Merge Conversation Data",
                "type": "main",
                "index": 1  # Second input of merge
            }

        # Update Create New Conversation to connect to Merge node
        if 'Create New Conversation' in workflow['connections']:
            workflow['connections']['Create New Conversation']['main'][0][0] = {
                "node": "Merge Conversation Data",
                "type": "main",
                "index": 1  # Second input of merge
            }

        # Add connections for Merge Queries nodes to Merge Conversation Data
        if 'Merge Queries Data' not in workflow['connections']:
            workflow['connections']['Merge Queries Data'] = {"main": [[]]}
        workflow['connections']['Merge Queries Data']['main'][0].append({
            "node": "Merge Conversation Data",
            "type": "main",
            "index": 0  # First input of merge
        })

        if 'Merge Queries Data1' not in workflow['connections']:
            workflow['connections']['Merge Queries Data1'] = {"main": [[]]}
        workflow['connections']['Merge Queries Data1']['main'][0].append({
            "node": "Merge Conversation Data",
            "type": "main",
            "index": 0  # First input of merge
        })

        # Add Merge Conversation Data connections to State Machine Logic
        workflow['connections']['Merge Conversation Data'] = {
            "main": [
                [
                    {
                        "node": "State Machine Logic",
                        "type": "main",
                        "index": 0
                    }
                ]
            ]
        }

        print("✅ Updated workflow connections")

    # Save the fixed workflow
    output_path = workflow_path.replace('.json', '_CONVERSATION_ID_FIXED.json')
    print(f"\n💾 Saving fixed workflow: {output_path}")

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(workflow, f, indent=2, ensure_ascii=False)
        print(f"✅ Workflow saved successfully!")
        print(f"\n📋 Next steps:")
        print(f"1. Import the fixed workflow into n8n")
        print(f"2. Deactivate the old V19 workflow")
        print(f"3. Activate the new fixed workflow")
        print(f"4. Test with a WhatsApp message")
        return True
    except Exception as e:
        print(f"❌ Error saving file: {e}")
        return False

if __name__ == "__main__":
    success = fix_workflow_v19()
    sys.exit(0 if success else 1)