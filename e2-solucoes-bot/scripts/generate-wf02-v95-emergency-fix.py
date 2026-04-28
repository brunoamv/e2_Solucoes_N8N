#!/usr/bin/env python3
"""
Generate WF02 V95 - Emergency Fix with Enhanced Diagnostics
Fixes the persistent loop problem where names are treated as invalid input
"""

import json
import os

def generate_v95_state_machine():
    """Generate V95 State Machine code with emergency fixes"""

    return '''// ===================================================
// V95 EMERGENCY FIX - DIAGNOSTIC VERSION
// ===================================================
// Problem: Names being treated as invalid service selection
// Solution: Enhanced state detection and validation
// Date: 2026-04-23
// ===================================================

// Helper functions
function formatPhoneDisplay(phone) {
  if (!phone) return 'Número não disponível';
  const cleaned = String(phone).replace(/[^0-9]/g, '');
  if (cleaned.length === 13) {
    return `+${cleaned.slice(0,2)} ${cleaned.slice(2,4)} ${cleaned.slice(4,9)}-${cleaned.slice(9)}`;
  } else if (cleaned.length === 11) {
    return `(${cleaned.slice(0,2)}) ${cleaned.slice(2,7)}-${cleaned.slice(7)}`;
  }
  return phone;
}

function getServiceName(serviceCode) {
  const services = {
    '1': '☀️ Energia Solar',
    '2': '⚡ Subestação',
    '3': '📐 Projetos Elétricos',
    '4': '🔋 BESS (Armazenamento)',
    '5': '📊 Análise e Laudos'
  };
  return services[serviceCode] || 'Serviço não especificado';
}

// Main execution
const input = $input.all()[0].json;
const message = (input.message || '').toString().trim().toLowerCase();

// V95 EMERGENCY: Ultra-verbose logging
console.log('=== V95 EMERGENCY DIAGNOSTIC START ===');
console.log('V95: Raw input:', JSON.stringify(input));
console.log('V95: Message received:', message);
console.log('V95: Input keys:', Object.keys(input));

// V95: 7-level state resolution with emergency fallbacks
const resolvedStage =
  input.current_stage ||
  input.currentStage ||
  input.next_stage ||
  input.nextStage ||
  input.currentData?.current_stage ||
  input.currentData?.next_stage ||
  input.current_state || // Check database field name
  'greeting';

console.log('V95: State resolution chain:');
console.log('  Level 1 (current_stage):', input.current_stage);
console.log('  Level 2 (currentStage):', input.currentStage);
console.log('  Level 3 (next_stage):', input.next_stage);
console.log('  Level 4 (nextStage):', input.nextStage);
console.log('  Level 5 (currentData.current):', input.currentData?.current_stage);
console.log('  Level 6 (currentData.next):', input.currentData?.next_stage);
console.log('  Level 7 (current_state):', input.current_state);
console.log('V95: RESOLVED STAGE:', resolvedStage);

// V95 CRITICAL: Detect if we're in wrong state
let currentStage = resolvedStage;

// V95: Auto-correct based on conversation context
const hasServiceSelected = input.currentData?.service_type || input.service_type;
const hasName = input.currentData?.lead_name || input.lead_name;

console.log('V95: Context check:');
console.log('  Has service:', hasServiceSelected);
console.log('  Has name:', hasName);
console.log('  Current stage before correction:', currentStage);

// V95 EMERGENCY FIX: Force correct state based on context
if (currentStage === 'greeting' || currentStage === 'service_selection') {
  if (hasServiceSelected && !hasName) {
    console.log('V95: EMERGENCY CORRECTION - Has service but no name, forcing collect_name');
    currentStage = 'collect_name';
  } else if (hasServiceSelected && hasName && !input.currentData?.phone_confirmed) {
    console.log('V95: EMERGENCY CORRECTION - Has service and name, forcing phone confirmation');
    currentStage = 'collect_phone_whatsapp_confirmation';
  }
}

// V95: Check for WF06 data and auto-correct
if ((currentStage === 'greeting' || currentStage === 'service_selection') && input.wf06_next_dates) {
  console.log('V95: AUTO-CORRECTING from', currentStage, 'to show_available_dates (WF06 data detected)');
  currentStage = 'show_available_dates';
}

if ((currentStage === 'greeting' || currentStage === 'service_selection') && input.wf06_available_slots) {
  console.log('V95: AUTO-CORRECTING from', currentStage, 'to show_available_slots (WF06 data detected)');
  currentStage = 'show_available_slots';
}

console.log('V95: Final current stage:', currentStage);

const currentData = input.currentData || {};

// Initialize response variables
let responseText = '';
let nextStage = currentStage;
let updateData = {};

// V95: Enhanced state machine with emergency fixes
switch (currentStage) {
  case 'greeting':
    console.log('V95: Processing GREETING state');
    responseText = `🤖 Olá! Bem-vindo à E2 Soluções!

Somos especialistas em engenharia elétrica com 15+ anos de experiência.

Qual serviço você precisa?

☀️ 1 - Energia Solar
   Projetos fotovoltaicos residenciais e comerciais

⚡ 2 - Subestação
   Reforma, manutenção e construção

📐 3 - Projetos Elétricos
   Adequações e laudos técnicos

🔋 4 - BESS (Armazenamento)
   Sistemas de armazenamento de energia

📊 5 - Análise e Laudos
   Qualidade de energia e eficiência

Digite o número do serviço (1-5):`;
    nextStage = 'service_selection';
    break;

  case 'service_selection':
    console.log('V95: Processing SERVICE_SELECTION state');
    console.log('V95: Message for service selection:', message);

    // V95 FIX: Check if this is actually a name (not a number)
    if (message && !['1','2','3','4','5'].includes(message)) {
      // Check if we already have a service selected
      if (hasServiceSelected) {
        console.log('V95: Detected NAME input in wrong state, processing as name');
        // This is likely a name, not a service selection
        updateData.lead_name = message;
        responseText = `✅ Obrigado, ${message}!

📱 O número ${formatPhoneDisplay(input.phone_number)} é seu WhatsApp correto?

Digite:
1️⃣ - Sim, está correto
2️⃣ - Não, preciso informar outro`;
        nextStage = 'collect_phone_whatsapp_confirmation';
        break;
      }
    }

    if (['1', '2', '3', '4', '5'].includes(message)) {
      const serviceName = getServiceName(message);
      updateData.service_type = message;
      responseText = `✅ Perfeito!

👤 Qual é o seu nome completo?

💡 Exemplo: Maria Silva Santos
Usaremos para personalizar seu atendimento`;
      nextStage = 'collect_name';
    } else {
      responseText = `❌ Opção inválida

Por favor, escolha uma das opções disponíveis:

1️⃣ - Energia Solar
2️⃣ - Subestações
3️⃣ - Projetos Elétricos
4️⃣ - BESS
5️⃣ - Análise de Consumo

Digite apenas o número (1 a 5)`;
      nextStage = 'service_selection';
    }
    break;

  case 'collect_name':
    console.log('V95: Processing COLLECT_NAME state');
    console.log('V95: Name received:', message);

    if (message && message.length >= 2) {
      updateData.lead_name = message;
      responseText = `✅ Obrigado, ${message}!

📱 O número ${formatPhoneDisplay(input.phone_number)} é seu WhatsApp correto?

Digite:
1️⃣ - Sim, está correto
2️⃣ - Não, preciso informar outro`;
      nextStage = 'collect_phone_whatsapp_confirmation';
    } else {
      responseText = `Por favor, informe seu nome completo para continuarmos.

💡 Exemplo: João Silva`;
      nextStage = 'collect_name';
    }
    break;

  case 'collect_phone_whatsapp_confirmation':
    console.log('V95: Processing PHONE_CONFIRMATION state');
    if (message === '1' || message === 'sim') {
      updateData.phone_confirmed = true;
      responseText = `📧 Agora, qual é o seu melhor e-mail?

💡 Exemplo: seunome@email.com
Enviaremos os orçamentos por e-mail`;
      nextStage = 'collect_email';
    } else if (message === '2' || message === 'não' || message === 'nao') {
      responseText = `📱 Por favor, informe o número de WhatsApp correto:

💡 Exemplo: (11) 98765-4321`;
      nextStage = 'collect_phone_alternative';
    } else {
      responseText = `Por favor, digite:
1️⃣ se o número está correto
2️⃣ se precisa informar outro`;
      nextStage = 'collect_phone_whatsapp_confirmation';
    }
    break;

  case 'collect_phone_alternative':
    console.log('V95: Processing PHONE_ALTERNATIVE state');
    if (message) {
      const phoneRegex = /\\d{10,11}/;
      const cleanPhone = message.replace(/\\D/g, '');

      if (phoneRegex.test(cleanPhone)) {
        updateData.phone_alternative = cleanPhone;
        updateData.phone_confirmed = true;
        responseText = `✅ Número atualizado!

📧 Agora, qual é o seu melhor e-mail?

💡 Exemplo: seunome@email.com`;
        nextStage = 'collect_email';
      } else {
        responseText = `❌ Formato inválido

Por favor, informe um número de WhatsApp válido
Exemplo: (11) 98765-4321`;
        nextStage = 'collect_phone_alternative';
      }
    }
    break;

  case 'collect_email':
    console.log('V95: Processing COLLECT_EMAIL state');
    if (message) {
      const emailRegex = /^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/;

      if (emailRegex.test(message)) {
        updateData.email = message;
        responseText = `📍 Qual é a sua cidade?

💡 Exemplo: São Paulo - SP
Importante para calcularmos frete e prazos`;
        nextStage = 'collect_city';
      } else {
        responseText = `❌ E-mail inválido

Por favor, informe um e-mail válido
Exemplo: seunome@email.com`;
        nextStage = 'collect_email';
      }
    }
    break;

  case 'collect_city':
    console.log('V95: Processing COLLECT_CITY state');
    if (message && message.length >= 2) {
      updateData.city = message;

      const serviceName = getServiceName(currentData.service_type || updateData.service_type);
      const name = currentData.lead_name || updateData.lead_name || 'Cliente';
      const phone = formatPhoneDisplay(input.phone_number);
      const email = currentData.email || updateData.email || 'Não informado';
      const city = message;

      responseText = `📋 Confirme seus dados:

👤 Nome: ${name}
📱 WhatsApp: ${phone}
📧 E-mail: ${email}
📍 Cidade: ${city}
⚡ Serviço: ${serviceName}

Os dados estão corretos?

1️⃣ - Sim, agendar consulta
2️⃣ - Não, corrigir dados`;
      nextStage = 'confirmation';
    } else {
      responseText = `Por favor, informe sua cidade para continuarmos.

💡 Exemplo: Belo Horizonte - MG`;
      nextStage = 'collect_city';
    }
    break;

  case 'confirmation':
    console.log('V95: Processing CONFIRMATION state');
    const serviceType = currentData.service_type || updateData.service_type;

    if (message === '1' || message === 'sim') {
      if (serviceType === '1' || serviceType === '3') {
        nextStage = 'trigger_wf06_next_dates';
        responseText = '';
        console.log('V95: Moving to trigger_wf06_next_dates for service', serviceType);
      } else {
        responseText = `✅ Perfeito! Seus dados foram registrados.

🤝 Nossa equipe comercial entrará em contato em breve pelo WhatsApp ${formatPhoneDisplay(input.phone_number)}.

⏰ Horário de atendimento:
Segunda a Sexta: 8h às 18h

Obrigado pela confiança!`;
        nextStage = 'handoff_comercial';
      }
    } else if (message === '2' || message === 'não' || message === 'nao') {
      responseText = `O que você gostaria de corrigir?

1️⃣ - Nome
2️⃣ - Telefone
3️⃣ - E-mail
4️⃣ - Cidade
5️⃣ - Serviço

Digite o número correspondente:`;
      nextStage = 'correction_choice';
    } else {
      responseText = `Por favor, digite:
1️⃣ para confirmar e prosseguir
2️⃣ para corrigir os dados`;
      nextStage = 'confirmation';
    }
    break;

  case 'trigger_wf06_next_dates':
    console.log('V95: State 9 - TRIGGER_WF06_NEXT_DATES');
    nextStage = 'show_available_dates';
    responseText = '';
    console.log('V95: Transitioning to show_available_dates');
    break;

  case 'show_available_dates':
    console.log('V95: State 10 - SHOW_AVAILABLE_DATES');

    const dates = input.wf06_next_dates || [];
    console.log('V95: Available dates count:', dates.length);

    if (dates.length > 0) {
      responseText = `📅 Datas disponíveis para agendamento:

`;
      dates.forEach((date, index) => {
        responseText += `${index + 1}️⃣ - ${date.formatted_date} - ${date.available_slots_count} horários disponíveis
`;
      });

      responseText += `
Digite o número da data desejada (1-${dates.length}):`;
      nextStage = 'process_date_selection';
    } else {
      responseText = `⚠️ Não há datas disponíveis no momento.

Nossa equipe entrará em contato para agendar.`;
      nextStage = 'handoff_comercial';
    }
    break;

  case 'process_date_selection':
    console.log('V95: State 11 - PROCESS_DATE_SELECTION');
    const availableDates = input.wf06_next_dates || [];
    const selection = parseInt(message);

    if (selection >= 1 && selection <= availableDates.length) {
      updateData.selected_date = availableDates[selection - 1];
      nextStage = 'trigger_wf06_available_slots';
      responseText = '';
    } else {
      responseText = `Por favor, escolha uma data válida (1-${availableDates.length})`;
      nextStage = 'process_date_selection';
    }
    break;

  case 'trigger_wf06_available_slots':
    console.log('V95: State 12 - TRIGGER_WF06_AVAILABLE_SLOTS');
    nextStage = 'show_available_slots';
    responseText = '';
    break;

  case 'show_available_slots':
    console.log('V95: State 13 - SHOW_AVAILABLE_SLOTS');
    const slots = input.wf06_available_slots || [];

    if (slots.length > 0) {
      responseText = `🕐 Horários disponíveis:

`;
      slots.forEach((slot, index) => {
        responseText += `${index + 1}️⃣ - ${slot.start_time}
`;
      });

      responseText += `
Digite o número do horário desejado (1-${slots.length}):`;
      nextStage = 'process_slot_selection';
    } else {
      responseText = `⚠️ Não há horários disponíveis nesta data.

Por favor, escolha outra data ou aguarde contato da equipe.`;
      nextStage = 'show_available_dates';
    }
    break;

  case 'process_slot_selection':
    console.log('V95: State 14 - PROCESS_SLOT_SELECTION');
    const availableSlots = input.wf06_available_slots || [];
    const slotSelection = parseInt(message);

    if (slotSelection >= 1 && slotSelection <= availableSlots.length) {
      updateData.selected_slot = availableSlots[slotSelection - 1];

      const selectedDate = currentData.selected_date || updateData.selected_date;
      const selectedSlot = availableSlots[slotSelection - 1];

      responseText = `✅ Agendamento confirmado!

📅 Data: ${selectedDate.formatted_date}
🕐 Horário: ${selectedSlot.start_time}
👤 Nome: ${currentData.lead_name}
📱 WhatsApp: ${formatPhoneDisplay(input.phone_number)}

Você receberá uma confirmação por e-mail e WhatsApp.

Obrigado por escolher a E2 Soluções!`;
      nextStage = 'schedule_confirmation';
    } else {
      responseText = `Por favor, escolha um horário válido (1-${availableSlots.length})`;
      nextStage = 'process_slot_selection';
    }
    break;

  case 'schedule_confirmation':
    console.log('V95: State 15 - SCHEDULE_CONFIRMATION');
    responseText = `Agendamento finalizado. Até breve!`;
    nextStage = 'schedule_confirmation';
    break;

  case 'handoff_comercial':
    console.log('V95: HANDOFF_COMERCIAL state');
    responseText = `Processo finalizado. Nossa equipe entrará em contato.`;
    nextStage = 'handoff_comercial';
    break;

  case 'correction_choice':
    console.log('V95: CORRECTION_CHOICE state');
    if (['1', '2', '3', '4', '5'].includes(message)) {
      switch (message) {
        case '1':
          responseText = `Digite seu nome correto:`;
          nextStage = 'correct_name';
          break;
        case '2':
          responseText = `Digite o telefone correto:`;
          nextStage = 'correct_phone';
          break;
        case '3':
          responseText = `Digite o e-mail correto:`;
          nextStage = 'correct_email';
          break;
        case '4':
          responseText = `Digite a cidade correta:`;
          nextStage = 'correct_city';
          break;
        case '5':
          responseText = `Escolha o serviço correto:

1️⃣ - Energia Solar
2️⃣ - Subestações
3️⃣ - Projetos Elétricos
4️⃣ - BESS
5️⃣ - Análise de Consumo`;
          nextStage = 'correct_service';
          break;
      }
    } else {
      responseText = `Por favor, escolha o que deseja corrigir (1-5)`;
      nextStage = 'correction_choice';
    }
    break;

  default:
    console.log('V95: WARNING - Unknown state:', currentStage);
    responseText = `Estado desconhecido. Reiniciando...`;
    nextStage = 'greeting';
}

// V95: Comprehensive output logging
console.log('=== V95 STATE MACHINE OUTPUT ===');
console.log('V95: Current → Next:', currentStage, '→', nextStage);
console.log('V95: Response length:', responseText.length);
console.log('V95: Update data:', JSON.stringify(updateData));

// V95: Always return complete state information
const output = {
  response_text: responseText,
  next_stage: nextStage,
  update_data: updateData,
  current_stage: nextStage,  // V95: Explicit state preservation
  previous_stage: currentStage,  // V95: Track previous for debugging
  version: 'V95-EMERGENCY',
  timestamp: new Date().toISOString(),
  diagnostic: {
    input_stage: resolvedStage,
    corrected_stage: currentStage,
    had_service: hasServiceSelected,
    had_name: hasName
  }
};

console.log('V95: Final output:', JSON.stringify(output));
console.log('=== V95 EMERGENCY DIAGNOSTIC END ===');

return output;'''

def main():
    """Main function to generate V95 workflow"""

    print("🔧 Generating WF02 V95 - Emergency Fix...")

    # Load V92 as base (since V94 wasn't imported)
    base_file = "/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V92.json"

    if not os.path.exists(base_file):
        print(f"❌ Error: Base file not found: {base_file}")
        return

    print(f"Loading base workflow from: {base_file}")

    with open(base_file, 'r') as f:
        workflow = json.load(f)

    # Update workflow name
    workflow['name'] = '02 - AI Agent Conversation V95 (Emergency Fix)'

    # Generate V95 State Machine code
    v95_code = generate_v95_state_machine()

    # Find and update State Machine node
    state_machine_updated = False
    for node in workflow['nodes']:
        if node.get('name') == 'State Machine Logic' or node.get('name') == 'State Machine V80':
            print(f"✅ Found State Machine node: {node['name']}")

            # Update the JavaScript code
            if 'parameters' in node:
                if 'functionCode' in node['parameters']:
                    node['parameters']['functionCode'] = v95_code
                elif 'jsCode' in node['parameters']:
                    node['parameters']['jsCode'] = v95_code

                state_machine_updated = True
                break

    if not state_machine_updated:
        print("⚠️  Warning: State Machine node not found - creating new Function node")
        # Add a new State Machine node if not found
        new_node = {
            "parameters": {
                "functionCode": v95_code
            },
            "id": "state-machine-v95",
            "name": "State Machine V95 Emergency",
            "type": "n8n-nodes-base.function",
            "typeVersion": 1,
            "position": [368, 240]
        }
        workflow['nodes'].append(new_node)

    # Save V95 workflow
    output_file = "/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V95_EMERGENCY_FIX.json"

    with open(output_file, 'w') as f:
        json.dump(workflow, f, indent=2)

    print(f"✅ V95 workflow generated successfully!")
    print(f"📁 Output: {output_file}")
    print("\n📝 Next steps:")
    print("1. Import this workflow in n8n")
    print("2. DISABLE the old workflow first")
    print("3. Test with the exact scenario that was failing:")
    print("   - Send 'oi' → Choose '1' → Send name 'Bruno Rosa'")
    print("4. Monitor logs: docker logs -f e2bot-n8n-dev | grep 'V95:'")
    print("\n🎯 Key improvements in V95:")
    print("- 7-level state resolution fallback")
    print("- Emergency context-based state correction")
    print("- Detection when name is sent in wrong state")
    print("- Ultra-verbose diagnostic logging")
    print("- Explicit state preservation with previous state tracking")

if __name__ == "__main__":
    main()