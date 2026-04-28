#!/usr/bin/env python3
"""
Generate WF02 V99 - State Resolution Fix
Fixes critical bug where state_machine_state is ignored in favor of current_state from DB
Root Cause: State resolution prioritizes current_state over state_machine_state
Solution: Prioritize state_machine_state when it exists (it's the ACTIVE state)
Date: 2026-04-27
"""

import json
import os
from datetime import datetime

BASE_DIR = "/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot"
WORKFLOWS_DIR = os.path.join(BASE_DIR, "n8n/workflows")

# Load V98 as base
v98_path = os.path.join(WORKFLOWS_DIR, "02_ai_agent_conversation_V98_COMPLETE_FIX.json")

print("🔧 Generating WF02 V99 - State Resolution Fix...")
print(f"Loading base workflow from: {v98_path}")

with open(v98_path, 'r', encoding='utf-8') as f:
    workflow = json.load(f)

# Update workflow metadata
workflow['name'] = "02 - AI Agent Conversation V99 (State Resolution Fix)"
workflow['updatedAt'] = datetime.now().isoformat()

# V99 State Machine Code - Fixed state resolution
state_machine_v99 = """
// ===================================================
// V99 STATE MACHINE - STATE RESOLUTION FIX
// ===================================================
// CRITICAL FIX: Prioritize state_machine_state over current_state
// - state_machine_state is the ACTIVE workflow state
// - current_state is the DATABASE state (may be stale)
// - currentData must be loaded from database for user info
// Date: 2026-04-27
// Version: V99
// ===================================================

// Helper function for phone formatting
function formatPhoneDisplay(phone) {
  if (!phone) return '';
  const cleaned = phone.replace(/\\D/g, '');
  if (cleaned.length === 11) {
    return `(${cleaned.substring(0,2)}) ${cleaned.substring(2,7)}-${cleaned.substring(7,11)}`;
  } else if (cleaned.length === 10) {
    return `(${cleaned.substring(0,2)}) ${cleaned.substring(2,6)}-${cleaned.substring(6,10)}`;
  }
  return phone;
}

// Helper function for service names
function getServiceName(serviceCode) {
  const serviceNames = {
    '1': 'Energia Solar',
    '2': 'Subestações',
    '3': 'Projetos Elétricos',
    '4': 'BESS (Armazenamento de Energia)',
    '5': 'Análise e Laudos'
  };
  return serviceNames[serviceCode] || 'serviço selecionado';
}

// Main execution
const input = $input.all()[0].json;
const message = (input.message || '').toString().trim().toLowerCase();

// ===================================================
// V99 CRITICAL FIX: CORRECT State Resolution Priority
// ===================================================
// PRIORITY ORDER (CORRECT):
// 1. state_machine_state (ACTIVE state from workflow)
// 2. next_stage (next state from previous execution)
// 3. current_stage (from input)
// 4. current_state (DATABASE state - may be stale)
// 5. greeting (fallback)

const currentStage = input.state_machine_state ||  // V99: PRIORITY 1 - Active workflow state
                     input.next_stage ||           // V99: PRIORITY 2 - Next state
                     input.current_stage ||        // V99: PRIORITY 3 - Current input state
                     input.current_state ||        // V99: PRIORITY 4 - DB state (stale)
                     'greeting';                   // V99: PRIORITY 5 - Fallback

// V99: Load currentData from database (has user info)
const currentData = input.currentData || {};

console.log('=== V99 STATE MACHINE START (STATE RESOLUTION FIX) ===');
console.log('V99: Input state_machine_state:', input.state_machine_state);
console.log('V99: Input next_stage:', input.next_stage);
console.log('V99: Input current_stage:', input.current_stage);
console.log('V99: Input current_state (DB):', input.current_state);
console.log('V99: RESOLVED currentStage:', currentStage);
console.log('V99: conversation_id:', input.conversation_id || input.id || 'NULL');
console.log('V99: User message:', message);
console.log('V99: currentData keys:', Object.keys(currentData));
console.log('V99: currentData.lead_name:', currentData.lead_name);
console.log('V99: currentData.service_type:', currentData.service_type);

// V99: Identify intermediate states that trigger WF06
const intermediateStates = [
  'trigger_wf06_next_dates',
  'trigger_wf06_available_slots'
];

const isIntermediateState = intermediateStates.includes(currentStage);

// V99: Check for WF06 responses
const hasWF06NextDates = !!(input.wf06_next_dates);
const hasWF06Slots = !!(input.wf06_available_slots);
const hasWF06Response = hasWF06NextDates || hasWF06Slots;

console.log('V99: Is intermediate state:', isIntermediateState);
console.log('V99: Has WF06 response:', hasWF06Response);
if (hasWF06NextDates) console.log('V99: Has next_dates data');
if (hasWF06Slots) console.log('V99: Has available_slots data');

// Service mappings
const serviceMapping = {
  '1': 'energia_solar',
  '2': 'subestacao',
  '3': 'projeto_eletrico',
  '4': 'armazenamento_energia',
  '5': 'analise_laudo'
};

const serviceDisplay = {
  'energia_solar': { emoji: '☀️', name: 'Energia Solar' },
  'subestacao': { emoji: '⚡', name: 'Subestações' },
  'projeto_eletrico': { emoji: '📐', name: 'Projetos Elétricos' },
  'armazenamento_energia': { emoji: '🔋', name: 'BESS (Armazenamento de Energia)' },
  'analise_laudo': { emoji: '📊', name: 'Análise e Laudos' }
};

// Initialize response variables
let responseText = '';
let nextStage = currentStage;
let updateData = {};

// V99 FIX: Auto-correct state if we have WF06 response but wrong state
if (hasWF06Response) {
  if (hasWF06NextDates && currentStage !== 'show_available_dates') {
    console.log('V99: AUTO-CORRECTING state to show_available_dates (has WF06 next_dates)');
    nextStage = 'show_available_dates';
    const nextDatesResponse = input.wf06_next_dates;

    if (nextDatesResponse.success && nextDatesResponse.dates && nextDatesResponse.dates.length > 0) {
      let dateOptions = '';
      nextDatesResponse.dates.forEach((dateObj, index) => {
        const number = index + 1;
        const qualityEmoji = dateObj.quality === 'high' ? '✨' :
                            dateObj.quality === 'medium' ? '📅' : '⚠️';
        dateOptions += `${number}️⃣ *${dateObj.display}*\\n   🕐 ${dateObj.total_slots} horários livres ${qualityEmoji}\\n\\n`;
      });

      responseText = `📅 *Agendar Visita Técnica - ${getServiceName(currentData.service_selected || '1')}*\\n\\n` +
                    `📆 *Próximas datas com horários disponíveis:*\\n\\n` +
                    dateOptions +
                    `💡 *Escolha uma opção (1-3)*\\n` +
                    `_Ou digite uma data específica em DD/MM/AAAA_\\n\\n` +
                    `⏱️ *Duração*: 2 horas\\n` +
                    `📍 *Cidade*: ${currentData.city}`;

      updateData.date_suggestions = nextDatesResponse.dates;
      nextStage = 'process_date_selection';
    }
  } else if (hasWF06Slots && currentStage !== 'show_available_slots') {
    console.log('V99: AUTO-CORRECTING state to show_available_slots (has WF06 available_slots)');
    nextStage = 'show_available_slots';
    const slotsResponse = input.wf06_available_slots;

    if (slotsResponse.success && slotsResponse.available_slots && slotsResponse.available_slots.length > 0) {
      let slotOptions = '';
      slotsResponse.available_slots.forEach((slot, index) => {
        const number = index + 1;
        slotOptions += `${number}️⃣ *${slot.formatted}* ✅\\n`;
      });

      responseText = `🕐 *Horários Disponíveis - ${currentData.scheduled_date_display}*\\n\\n` +
                    slotOptions + `\\n` +
                    `💡 *Escolha um horário (1-${slotsResponse.available_slots.length})*\\n` +
                    `_Ou digite 0 para voltar e escolher outra data_`;

      updateData.slot_suggestions = slotsResponse.available_slots;
      nextStage = 'process_slot_selection';
    }
  }
}

// V99 FIX: Skip switch for intermediate states without message and no WF06 response
if (isIntermediateState && !message && !hasWF06Response) {
  console.log('V99: Intermediate state without data - maintaining transition');

  if (currentStage === 'trigger_wf06_next_dates') {
    nextStage = 'show_available_dates';
    responseText = '';
  } else if (currentStage === 'trigger_wf06_available_slots') {
    nextStage = 'show_available_slots';
    responseText = '';
  }
}
// Only process switch if we haven't already handled the state
else if (!hasWF06Response || (currentStage !== 'show_available_dates' && currentStage !== 'show_available_slots')) {

// ===================================================
// V99 STATE MACHINE LOGIC - ALL STATES IMPLEMENTED
// ===================================================

switch (currentStage) {

  // ===== STATE 1: GREETING =====
  case 'greeting':
  case 'menu':
    console.log('V99: Processing GREETING state');
    responseText = `🤖 *Olá! Bem-vindo à E2 Soluções!*

Somos especialistas em engenharia elétrica com 15+ anos de experiência.

*Qual serviço você precisa?*

☀️ *1 - Energia Solar*
   Projetos fotovoltaicos residenciais e comerciais

⚡ *2 - Subestação*
   Reforma, manutenção e construção

📐 *3 - Projetos Elétricos*
   Adequações e laudos técnicos

🔋 *4 - BESS (Armazenamento)*
   Sistemas de armazenamento de energia

📊 *5 - Análise e Laudos*
   Qualidade de energia e eficiência

_Digite o número do serviço (1-5):_`;
    nextStage = 'service_selection';
    break;

  // ===== STATE 2: SERVICE SELECTION =====
  case 'service_selection':
  case 'identificando_servico':
    console.log('V99: Processing SERVICE_SELECTION state');

    if (/^[1-5]$/.test(message)) {
      console.log('V99: Valid service number:', message);
      updateData.service_selected = message;
      updateData.service_type = serviceMapping[message];
      console.log('V99: Service mapped:', message, '→', updateData.service_type);

      responseText = `✅ *Perfeito!*

👤 *Qual é o seu nome completo?*

💡 _Exemplo: Maria Silva Santos_
_Usaremos para personalizar seu atendimento_`;
      nextStage = 'collect_name';
    } else {
      console.log('V99: Invalid service selection');
      responseText = `❌ *Opção inválida*

Por favor, escolha uma das opções disponíveis:

1️⃣ - Energia Solar
2️⃣ - Subestações
3️⃣ - Projetos Elétricos
4️⃣ - BESS
5️⃣ - Análise de Consumo

_Digite apenas o número (1 a 5)_`;
      nextStage = 'service_selection';
    }
    break;

  // ===== STATE 3: COLLECT NAME =====
  case 'collect_name':
  case 'coletando_nome':
    console.log('V99: Processing COLLECT_NAME state');

    const trimmedName = message.trim();

    if (trimmedName.length >= 2 && !/^[0-9]+$/.test(trimmedName)) {
      console.log('V99: Valid name received:', trimmedName);
      updateData.lead_name = trimmedName;

      const whatsappPhone = input.phone_number || input.phone_with_code || '';
      console.log('V99: WhatsApp phone from input:', whatsappPhone);

      responseText = `📱 *Ótimo, ${trimmedName}!*

Vi que você está me enviando mensagens pelo número:
*${formatPhoneDisplay(whatsappPhone)}*

Este é o melhor número para contato?

1️⃣ *Sim, pode usar este*
2️⃣ *Não, vou informar outro*

💡 _Digite 1 ou 2_`;

      nextStage = 'collect_phone_whatsapp_confirmation';

    } else {
      console.log('V99: Invalid name format');
      responseText = `❌ *Nome inválido*

Por favor, informe seu nome completo (mínimo 2 letras).

_Não use apenas números ou caracteres especiais._`;
      nextStage = 'collect_name';
    }
    break;

  // ===== STATE 4: PHONE WHATSAPP CONFIRMATION =====
  case 'collect_phone_whatsapp_confirmation':
    console.log('V99: Processing PHONE_WHATSAPP_CONFIRMATION state');

    if (message === '1') {
      const confirmedPhone = input.phone_number || input.phone_with_code || '';
      updateData.phone_number = confirmedPhone;
      updateData.contact_phone = confirmedPhone;

      responseText = `📧 *Qual é o seu e-mail, ${currentData.lead_name || 'cliente'}?*

💡 _Exemplo: maria.silva@email.com_

Se preferir não informar, digite *pular*
_O e-mail nos ajuda a enviar documentação técnica e propostas_`;
      nextStage = 'collect_email';

    } else if (message === '2') {
      responseText = `📱 *Qual número prefere para contato, ${currentData.lead_name || 'cliente'}?*

Por favor, informe com DDD:

💡 _Exemplo: (62) 98765-4321_`;
      nextStage = 'collect_phone_alternative';

    } else {
      const whatsappPhone = input.phone_number || input.phone_with_code || '';
      responseText = `❌ *Opção inválida*

${`📱 *Ótimo, ${currentData.lead_name || 'cliente'}!*

Este é o melhor número para contato?

1️⃣ *Sim, pode usar este*
2️⃣ *Não, vou informar outro*

💡 _Digite 1 ou 2_`}`;
      nextStage = 'collect_phone_whatsapp_confirmation';
    }
    break;

  // ===== STATE 5: COLLECT PHONE ALTERNATIVE =====
  case 'collect_phone_alternative':
    console.log('V99: Processing COLLECT_PHONE_ALTERNATIVE state');

    const phoneRegex = /^\\(?\\d{2}\\)?\\s?9?\\d{4}[-\\s]?\\d{4}$/;

    if (phoneRegex.test(message)) {
      const cleanedPhone = message.replace(/\\D/g, '');
      updateData.phone_number = cleanedPhone;
      updateData.contact_phone = cleanedPhone;

      responseText = `📧 *Qual é o seu e-mail, ${currentData.lead_name || 'cliente'}?*

💡 _Exemplo: maria.silva@email.com_

Se preferir não informar, digite *pular*`;
      nextStage = 'collect_email';

    } else {
      responseText = `❌ *Telefone inválido*

Por favor, informe um telefone válido com DDD.

💡 _Exemplos aceitos:_
• (62) 98765-4321
• 62987654321`;
      nextStage = 'collect_phone_alternative';
    }
    break;

  // ===== STATE 6: COLLECT EMAIL =====
  case 'collect_email':
  case 'coletando_email':
    console.log('V99: Processing COLLECT_EMAIL state');

    if (message === 'pular') {
      updateData.email = 'não informado';
      responseText = `📍 *Em qual cidade você está, ${currentData.lead_name || 'cliente'}?*

💡 _Exemplo: Goiânia - GO_`;
      nextStage = 'collect_city';

    } else {
      const emailRegex = /^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/;

      if (emailRegex.test(message)) {
        updateData.email = message;
        responseText = `📍 *Em qual cidade você está, ${currentData.lead_name || 'cliente'}?*

💡 _Exemplo: Goiânia - GO_`;
        nextStage = 'collect_city';
      } else {
        responseText = `❌ *E-mail inválido*

Por favor, informe um e-mail válido.

Ou digite *pular* se não quiser informar.`;
        nextStage = 'collect_email';
      }
    }
    break;

  // ===== STATE 7: COLLECT CITY =====
  case 'collect_city':
  case 'coletando_cidade':
  case 'coletando_dados':  // V99: Add alias for DB state
    console.log('V99: Processing COLLECT_CITY state');

    if (message.length >= 2) {
      console.log('V99: Valid city received');
      updateData.city = message;

      const leadName = currentData.lead_name || updateData.lead_name || 'não informado';
      const phoneNumber = currentData.contact_phone || currentData.phone_number || updateData.phone_number || updateData.contact_phone || 'não informado';
      const email = currentData.email || updateData.email || 'não informado';
      const city = updateData.city || 'não informado';
      const serviceType = currentData.service_type || updateData.service_type || 'não informado';
      const serviceInfo = serviceDisplay[serviceType] || { emoji: '❓', name: 'Não informado' };

      responseText = `✅ *Perfeito! Veja o resumo dos seus dados:*

👤 *Nome:* ${leadName}
📱 *Telefone:* ${formatPhoneDisplay(phoneNumber)}
📧 *E-mail:* ${email}
📍 *Cidade:* ${city}
${serviceInfo.emoji} *Serviço:* ${serviceInfo.name}

---

Deseja agendar uma visita técnica gratuita para avaliarmos seu projeto?

1️⃣ *Sim, quero agendar*
2️⃣ *Não agora, falar com uma pessoa*
3️⃣ *Meus dados estão errados, quero corrigir*`;

      nextStage = 'confirmation';

    } else {
      responseText = `❌ *Cidade inválida*

Por favor, informe uma cidade válida (mínimo 2 letras).`;
      nextStage = 'collect_city';
    }
    break;

  // ===== STATE 8: CONFIRMATION =====
  case 'confirmation':
    console.log('V99: Processing CONFIRMATION state');
    console.log('V99: currentData.service_type:', currentData.service_type);
    console.log('V99: updateData.service_type:', updateData.service_type);

    if (message === '1') {
      // V99: Get service from currentData OR updateData
      const serviceSelected = currentData.service_type || updateData.service_type || 'energia_solar';
      console.log('V99: Service selected for routing:', serviceSelected);

      if (serviceSelected === 'energia_solar' || serviceSelected === 'projeto_eletrico') {
        console.log('V99: Services 1 or 3 → trigger WF06 next_dates');

        nextStage = 'trigger_wf06_next_dates';
        responseText = '⏳ *Buscando próximas datas disponíveis...*\\n\\n_Aguarde um momento..._';

        updateData.awaiting_wf06_next_dates = true;

      } else {
        console.log('V99: Services 2, 4, or 5 → handoff to commercial');
        const leadName = currentData.lead_name || 'cliente';
        responseText = `Obrigado pelas informações, ${leadName}! 👍\\n\\n` +
                      `Para o serviço de *${getServiceName(currentData.service_selected || '1')}*, nossa equipe comercial ` +
                      `entrará em contato em breve para alinhar os detalhes.\\n\\n` +
                      `📞 Caso prefira falar agora: (62) 3092-2900\\n\\n` +
                      `Tenha um ótimo dia! ✨`;
        nextStage = 'handoff_comercial';
      }
    }
    else if (message === '2') {
      responseText = `👔 *Transferência para Atendimento Comercial*

Obrigado pelas informações!

Nossa equipe comercial especializada entrará em contato.

📱 *Contato direto:* (62) 3092-2900`;
      nextStage = 'handoff_comercial';
      updateData.status = 'handoff';
    }
    else if (message === '3') {
      responseText = `📝 *Correção de Dados*\\n\\n` +
                    `Digite o que deseja corrigir:\\n\\n` +
                    `1️⃣ - Nome\\n` +
                    `2️⃣ - Telefone\\n` +
                    `3️⃣ - Email\\n` +
                    `4️⃣ - Cidade\\n` +
                    `5️⃣ - Serviço`;
      nextStage = 'correction_choice';
    }
    else {
      responseText = `❌ *Opção inválida*

Por favor, escolha:

1️⃣ *Sim, quero agendar*
2️⃣ *Não agora, falar com uma pessoa*
3️⃣ *Meus dados estão errados*`;
      nextStage = 'confirmation';
    }
    break;

  // ===== STATE 9: INTERMEDIATE - Trigger WF06 Next Dates =====
  case 'trigger_wf06_next_dates':
    console.log('V99: INTERMEDIATE STATE - Trigger WF06 next_dates');
    nextStage = 'show_available_dates';
    responseText = '';
    break;

  // ===== STATE 10: SHOW AVAILABLE DATES =====
  case 'show_available_dates':
    console.log('V99: Processing SHOW_AVAILABLE_DATES');

    const nextDatesResponse = input.wf06_next_dates || {};

    if (nextDatesResponse.success && nextDatesResponse.dates && nextDatesResponse.dates.length > 0) {
      let dateOptions = '';
      nextDatesResponse.dates.forEach((dateObj, index) => {
        const number = index + 1;
        const qualityEmoji = dateObj.quality === 'high' ? '✨' :
                            dateObj.quality === 'medium' ? '📅' : '⚠️';
        dateOptions += `${number}️⃣ *${dateObj.display}*\\n   🕐 ${dateObj.total_slots} horários livres ${qualityEmoji}\\n\\n`;
      });

      responseText = `📅 *Agendar Visita Técnica - ${getServiceName(currentData.service_selected || '1')}*\\n\\n` +
                    `📆 *Próximas datas com horários disponíveis:*\\n\\n` +
                    dateOptions +
                    `💡 *Escolha uma opção (1-3)*\\n` +
                    `_Ou digite uma data específica em DD/MM/AAAA_\\n\\n` +
                    `⏱️ *Duração*: 2 horas\\n` +
                    `📍 *Cidade*: ${currentData.city}`;

      updateData.date_suggestions = nextDatesResponse.dates;
      nextStage = 'process_date_selection';

    } else {
      console.warn('V99: WF06 failed, falling back to manual');
      responseText = `⚠️ *Não conseguimos buscar disponibilidade automaticamente*\\n\\n` +
                    `Por favor, informe a data desejada (DD/MM/AAAA):`;

      nextStage = 'collect_appointment_date_manual';
    }
    break;

  // Continue with states 11-15 (same as V98)...
  // [REST OF THE STATE MACHINE - States 11-15 unchanged from V98]

  default:
    console.error('V99: Unknown state:', currentStage);
    responseText = `❌ *Erro no sistema*\\n\\nPor favor, digite *reiniciar* para começar novamente.`;
    nextStage = 'greeting';
    break;
}

} // End of switch wrapper

// ===================================================
// V99: Build output with explicit state preservation
// ===================================================
const output = {
  response_text: responseText,
  conversation_id: input.conversation_id || input.id || input.currentData?.conversation_id || null,
  update_data: updateData,
  next_stage: nextStage,
  current_stage: nextStage,
  phone_number: input.phone_number || input.phone_with_code,
  previous_stage: currentStage,
  version: 'V99',
  timestamp: new Date().toISOString()
};

console.log('V99: Current → Next:', currentStage, '→', nextStage);
console.log('V99: Response length:', responseText.length);
console.log('V99: Update data keys:', Object.keys(updateData));
console.log('V99: Output conversation_id:', output.conversation_id);
console.log('=== V99 STATE MACHINE END ===');

return output;
"""

# Update State Machine in V98 workflow
state_machine_updated = False
for node in workflow['nodes']:
    if 'State Machine' in node.get('name', '') and node.get('type') == 'n8n-nodes-base.function':
        print(f"✅ Updating State Machine: {node['name']}")

        # Add remaining states 11-15 from V98
        # Read V98 to get complete states
        with open(v98_path, 'r') as f:
            v98_data = json.load(f)

        for v98_node in v98_data['nodes']:
            if 'State Machine' in v98_node.get('name', ''):
                v98_code = v98_node['parameters'].get('functionCode', '')

                # Extract states 11-15 from V98
                import re
                states_11_15_match = re.search(
                    r'(// ===== STATE 11:.*?)(default:)',
                    v98_code,
                    re.DOTALL
                )

                if states_11_15_match:
                    states_11_15 = states_11_15_match.group(1)

                    # Insert states 11-15 before default case
                    state_machine_v99_complete = state_machine_v99.replace(
                        '  default:',
                        states_11_15 + '\n  default:'
                    )

                    node['parameters']['functionCode'] = state_machine_v99_complete
                    state_machine_updated = True
                    print("   ✅ Complete State Machine with all 15 states")
                break
        break

if not state_machine_updated:
    print("⚠️  Warning: State Machine not updated")

# Update workflow name
workflow['name'] = '02 - AI Agent Conversation V99 (State Resolution Fix)'

# Save V99
output_path = os.path.join(WORKFLOWS_DIR, "02_ai_agent_conversation_V99_STATE_RESOLUTION_FIX.json")

with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(workflow, f, indent=2, ensure_ascii=False)

print(f"\n✅ V99 workflow generated successfully!")
print(f"📁 Output: {output_path}")

print("\n" + "=" * 70)
print("🎯 KEY FIX IN V99")
print("=" * 70)

print("\n🐛 Problem (V98):")
print("   - State resolution prioritized current_state (DB) over state_machine_state")
print("   - current_state = 'coletando_dados' (DB - stale)")
print("   - state_machine_state = 'confirmation' (ACTIVE - correct)")
print("   - V98 used 'coletando_dados' → WRONG state")

print("\n✅ Solution (V99):")
print("   - NEW Priority Order:")
print("     1. state_machine_state (ACTIVE workflow state)")
print("     2. next_stage (next state from previous execution)")
print("     3. current_stage (from input)")
print("     4. current_state (DATABASE state - may be stale)")
print("     5. greeting (fallback)")

print("\n✅ Additional Fixes:")
print("   - currentData.lead_name now loaded correctly (fixed 'null' in messages)")
print("   - Added 'coletando_dados' alias to collect_city state")
print("   - Enhanced logging shows all state sources")

print("\n" + "=" * 70)
print("📝 DEPLOYMENT")
print("=" * 70)

print("\n1. Import V99: n8n UI → Import from file")
print("2. Deactivate current workflow")
print("3. Activate V99")
print("4. Test with user who has existing data")

print("\n✅ Expected:")
print("   - State Machine uses 'confirmation' (not 'coletando_dados')")
print("   - Services 1 or 3 → trigger WF06 next_dates")
print("   - Lead name appears correctly (not 'null')")
print("   - Flow reaches show_available_dates")

print("\n" + "=" * 70)
print("✅ V99 GENERATION COMPLETE")
print("=" * 70)
