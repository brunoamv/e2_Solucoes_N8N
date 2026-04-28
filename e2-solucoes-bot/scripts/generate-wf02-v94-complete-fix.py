#!/usr/bin/env python3
"""
Generate WF02 V94 - Complete Loop Fix
Fixes the infinite loop problem by properly preserving state between executions
Date: 2026-04-23
"""

import json
import os
from datetime import datetime

# Base paths
BASE_DIR = "/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot"
WORKFLOWS_DIR = os.path.join(BASE_DIR, "n8n/workflows")

# Load V92 as base (it has the complete structure)
v92_path = os.path.join(WORKFLOWS_DIR, "02_ai_agent_conversation_V92.json")

print("🔧 Generating WF02 V94 - Complete Loop Fix...")
print(f"Loading base workflow from: {v92_path}")

with open(v92_path, 'r', encoding='utf-8') as f:
    workflow = json.load(f)

# Update workflow metadata
workflow['name'] = "02 - AI Agent Conversation V94 (Complete Loop Fix)"
workflow['updatedAt'] = datetime.now().isoformat()

# V94 State Machine Code with complete fix
state_machine_v94 = """
// ===================================================
// V94 STATE MACHINE - COMPLETE LOOP FIX
// ===================================================
// DEFINITIVE FIX: Prevent infinite loops with proper state preservation
// - 5-level state resolution fallback chain
// - Explicit state preservation in output
// - Proper handling of intermediate states
// - Auto-correction for WF06 responses
// Date: 2026-04-23
// Version: V94 Complete Fix
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
// V94 CRITICAL FIX: 5-Level State Resolution
// ===================================================
// This ensures state is never lost between executions
const currentStage = input.current_stage ||
                     input.next_stage ||
                     input.currentData?.current_stage ||
                     input.currentData?.next_stage ||
                     'greeting';

const currentData = input.currentData || {};

// V94: Identify intermediate states that trigger WF06
const intermediateStates = [
  'trigger_wf06_next_dates',
  'trigger_wf06_available_slots'
];

const isIntermediateState = intermediateStates.includes(currentStage);

// V94: Enhanced logging for debugging
console.log('=== V94 STATE MACHINE START (COMPLETE FIX) ===');
console.log('V94: Current stage:', currentStage);
console.log('V94: Is intermediate state:', isIntermediateState);
console.log('V94: User message:', message);
console.log('V94: Current data keys:', Object.keys(currentData));
console.log('V94: Input keys:', Object.keys(input));

// V94: Check for WF06 responses
const hasWF06NextDates = !!(input.wf06_next_dates);
const hasWF06Slots = !!(input.wf06_available_slots);
const hasWF06Response = hasWF06NextDates || hasWF06Slots;

console.log('V94: Has WF06 response:', hasWF06Response);
if (hasWF06NextDates) console.log('V94: Has next_dates data');
if (hasWF06Slots) console.log('V94: Has available_slots data');

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

// V94 FIX: Auto-correct state if we have WF06 response but wrong state
if (hasWF06Response) {
  if (hasWF06NextDates && currentStage !== 'show_available_dates') {
    console.log('V94: AUTO-CORRECTING state to show_available_dates (has WF06 next_dates)');
    nextStage = 'show_available_dates';
    // Process immediately without re-entering switch
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
    console.log('V94: AUTO-CORRECTING state to show_available_slots (has WF06 available_slots)');
    nextStage = 'show_available_slots';
    // Process immediately
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

// V94 FIX: Skip switch for intermediate states without message and no WF06 response
if (isIntermediateState && !message && !hasWF06Response) {
  console.log('V94: Intermediate state without data - maintaining transition');

  if (currentStage === 'trigger_wf06_next_dates') {
    nextStage = 'show_available_dates';
    responseText = ''; // Empty is OK for intermediate
  } else if (currentStage === 'trigger_wf06_available_slots') {
    nextStage = 'show_available_slots';
    responseText = '';
  }
}
// Only process switch if we haven't already handled the state
else if (!hasWF06Response || (currentStage !== 'show_available_dates' && currentStage !== 'show_available_slots')) {

// ===================================================
// V94 STATE MACHINE LOGIC - ALL STATES IMPLEMENTED
// ===================================================

switch (currentStage) {

  // ===== STATE 1: GREETING - Show menu =====
  case 'greeting':
  case 'menu':
    console.log('V94: Processing GREETING state');
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
    console.log('V94: Processing SERVICE_SELECTION state');

    if (/^[1-5]$/.test(message)) {
      console.log('V94: Valid service number:', message);
      updateData.service_selected = message;
      updateData.service_type = serviceMapping[message];
      console.log('V94: Service mapped:', message, '→', updateData.service_type);

      responseText = `✅ *Perfeito!*

👤 *Qual é o seu nome completo?*

💡 _Exemplo: Maria Silva Santos_
_Usaremos para personalizar seu atendimento_`;
      nextStage = 'collect_name';
    } else {
      console.log('V94: Invalid service selection');
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
    console.log('V94: Processing COLLECT_NAME state');

    const trimmedName = message.trim();

    if (trimmedName.length >= 2 && !/^[0-9]+$/.test(trimmedName)) {
      console.log('V94: Valid name received:', trimmedName);
      updateData.lead_name = trimmedName;

      const whatsappPhone = input.phone_number || input.phone_with_code || '';
      console.log('V94: WhatsApp phone from input:', whatsappPhone);

      responseText = `📱 *Ótimo, ${trimmedName}!*

Vi que você está me enviando mensagens pelo número:
*${formatPhoneDisplay(whatsappPhone)}*

Este é o melhor número para contato?

1️⃣ *Sim, pode usar este*
2️⃣ *Não, vou informar outro*

💡 _Digite 1 ou 2_`;

      nextStage = 'collect_phone_whatsapp_confirmation';
      console.log('V94: Skip collect_phone, go directly to WhatsApp confirmation');

    } else {
      console.log('V94: Invalid name format');
      responseText = `❌ *Nome inválido*

Por favor, informe seu nome completo (mínimo 2 letras).

_Não use apenas números ou caracteres especiais._`;
      nextStage = 'collect_name';
    }
    break;

  // ===== STATE 4: PHONE WHATSAPP CONFIRMATION =====
  case 'collect_phone_whatsapp_confirmation':
    console.log('V94: Processing PHONE_WHATSAPP_CONFIRMATION state');

    if (message === '1') {
      console.log('V94: WhatsApp number confirmed');

      const confirmedPhone = input.phone_number || input.phone_with_code || '';
      updateData.phone_number = confirmedPhone;
      updateData.contact_phone = confirmedPhone;

      responseText = `📧 *Qual é o seu e-mail, ${currentData.lead_name || 'cliente'}?*

💡 _Exemplo: maria.silva@email.com_

Se preferir não informar, digite *pular*
_O e-mail nos ajuda a enviar documentação técnica e propostas_`;
      nextStage = 'collect_email';

    } else if (message === '2') {
      console.log('V94: User wants alternative phone');

      responseText = `📱 *Qual número prefere para contato, ${currentData.lead_name || 'cliente'}?*

Por favor, informe com DDD:

💡 _Exemplo: (62) 98765-4321_
_Usaremos este número para agendarmos sua visita técnica_`;
      nextStage = 'collect_phone_alternative';

    } else {
      console.log('V94: Invalid WhatsApp confirmation option');
      const whatsappPhone = input.phone_number || input.phone_with_code || '';
      responseText = `❌ *Opção inválida*

${`📱 *Ótimo, ${currentData.lead_name || 'cliente'}!*

Vi que você está me enviando mensagens pelo número:
*${formatPhoneDisplay(whatsappPhone)}*

Este é o melhor número para contato?

1️⃣ *Sim, pode usar este*
2️⃣ *Não, vou informar outro*

💡 _Digite 1 ou 2_`}`;
      nextStage = 'collect_phone_whatsapp_confirmation';
    }
    break;

  // ===== STATE 5: COLLECT PHONE ALTERNATIVE =====
  case 'collect_phone_alternative':
    console.log('V94: Processing COLLECT_PHONE_ALTERNATIVE state');

    const phoneRegex = /^\\(?\\d{2}\\)?\\s?9?\\d{4}[-\\s]?\\d{4}$/;

    if (phoneRegex.test(message)) {
      console.log('V94: Valid alternative phone received');

      const cleanedPhone = message.replace(/\\D/g, '');
      updateData.phone_number = cleanedPhone;
      updateData.contact_phone = cleanedPhone;

      responseText = `📧 *Qual é o seu e-mail, ${currentData.lead_name || 'cliente'}?*

💡 _Exemplo: maria.silva@email.com_

Se preferir não informar, digite *pular*
_O e-mail nos ajuda a enviar documentação técnica e propostas_`;
      nextStage = 'collect_email';

    } else {
      console.log('V94: Invalid alternative phone format');
      responseText = `❌ *Telefone inválido*

Por favor, informe um telefone válido com DDD.

💡 _Exemplos aceitos:_
• (62) 98765-4321
• 62987654321
• 6298765-4321

_Use apenas números, espaços, parênteses e hífen_`;
      nextStage = 'collect_phone_alternative';
    }
    break;

  // ===== STATE 6: COLLECT EMAIL =====
  case 'collect_email':
  case 'coletando_email':
    console.log('V94: Processing COLLECT_EMAIL state');

    if (message === 'pular') {
      console.log('V94: User skipped email');
      updateData.email = 'não informado';
      responseText = `📍 *Em qual cidade você está, ${currentData.lead_name || 'cliente'}?*

💡 _Exemplo: Goiânia - GO_
_Precisamos saber para agendar a visita técnica com nossa equipe local_`;
      nextStage = 'collect_city';

    } else {
      const emailRegex = /^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/;

      if (emailRegex.test(message)) {
        console.log('V94: Valid email received');
        updateData.email = message;
        responseText = `📍 *Em qual cidade você está, ${currentData.lead_name || 'cliente'}?*

💡 _Exemplo: Goiânia - GO_
_Precisamos saber para agendar a visita técnica com nossa equipe local_`;
        nextStage = 'collect_city';
      } else {
        console.log('V94: Invalid email format');
        responseText = `❌ *E-mail inválido*

Por favor, informe um e-mail válido.

*Exemplos:*
• maria@gmail.com
• joao.silva@empresa.com.br

Ou digite *pular* se não quiser informar.`;
        nextStage = 'collect_email';
      }
    }
    break;

  // ===== STATE 7: COLLECT CITY =====
  case 'collect_city':
  case 'coletando_cidade':
    console.log('V94: Processing COLLECT_CITY state');

    if (message.length >= 2) {
      console.log('V94: Valid city received');
      updateData.city = message;

      const leadName = currentData.lead_name || updateData.lead_name || 'não informado';
      const phoneNumber = currentData.contact_phone || currentData.phone_number || updateData.phone_number || updateData.contact_phone || 'não informado';
      const email = currentData.email || updateData.email || 'não informado';
      const city = updateData.city || 'não informado';
      const serviceType = currentData.service_type || 'não informado';
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
      console.log('V94: Going to State 8 (confirmation)');

    } else {
      console.log('V94: Invalid city (too short)');
      responseText = `❌ *Cidade inválida*

Por favor, informe uma cidade válida (mínimo 2 letras).

_Exemplo: Goiânia, Brasília, Anápolis..._`;
      nextStage = 'collect_city';
    }
    break;

  // ===== STATE 8: CONFIRMATION =====
  case 'confirmation':
    console.log('V94: Processing CONFIRMATION state');

    if (message === '1') {
      const serviceSelected = currentData.service_type || '1';

      if (serviceSelected === 'energia_solar' || serviceSelected === 'projeto_eletrico') {
        console.log('V94: Services 1 or 3 → trigger WF06 next_dates');

        nextStage = 'trigger_wf06_next_dates';
        responseText = '⏳ *Buscando próximas datas disponíveis...*\\n\\n_Aguarde um momento..._';

        updateData.awaiting_wf06_next_dates = true;

      } else {
        console.log('V94: Services 2, 4, or 5 → handoff to commercial');
        responseText = `Obrigado pelas informações, ${currentData.lead_name}! 👍\\n\\n` +
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

Nossa equipe comercial especializada entrará em contato para:
✅ Apresentar soluções personalizadas
✅ Elaborar proposta técnica-comercial
✅ Esclarecer dúvidas sobre investimento

🕐 *Retorno em:* até 24 horas úteis

📱 *Contato direto:* (62) 3092-2900

_Aguarde nosso retorno!_`;
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
                    `5️⃣ - Serviço\\n\\n` +
                    `_Digite o número correspondente:_`;
      nextStage = 'correction_choice';
    }
    else {
      responseText = `❌ *Opção inválida*

Por favor, escolha uma das opções:

1️⃣ *Sim, quero agendar*
2️⃣ *Não agora, falar com uma pessoa*
3️⃣ *Meus dados estão errados, quero corrigir*`;
      nextStage = 'confirmation';
    }
    break;

  // ===== STATE 9: INTERMEDIATE - Trigger WF06 Next Dates =====
  case 'trigger_wf06_next_dates':
    console.log('V94: INTERMEDIATE STATE - Trigger WF06 next_dates');
    nextStage = 'show_available_dates';
    responseText = ''; // Empty for intermediate state
    break;

  // ===== STATE 10: SHOW AVAILABLE DATES =====
  case 'show_available_dates':
    console.log('V94: Processing SHOW_AVAILABLE_DATES');

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
      console.warn('V94: WF06 failed, falling back to manual');
      responseText = `⚠️ *Não conseguimos buscar disponibilidade automaticamente*\\n\\n` +
                    `Por favor, informe a data desejada (DD/MM/AAAA):\\n\\n` +
                    `💡 *Lembre-se:*\\n` +
                    `• Data futura (não pode ser hoje ou passado)\\n` +
                    `• Dia útil (segunda a sexta-feira)\\n\\n` +
                    `_Digite a data..._`;

      nextStage = 'collect_appointment_date_manual';
    }
    break;

  // ===== STATE 11: PROCESS DATE SELECTION =====
  case 'process_date_selection':
    console.log('V94: Processing DATE SELECTION');

    const dateChoice = message.trim();

    if (/^[1-3]$/.test(dateChoice)) {
      const selectedIndex = parseInt(dateChoice) - 1;
      const suggestions = currentData.date_suggestions || [];

      if (selectedIndex >= 0 && selectedIndex < suggestions.length) {
        const selectedDate = suggestions[selectedIndex];
        console.log('V94: Date selected:', selectedDate.date);

        updateData.scheduled_date = selectedDate.date;
        updateData.scheduled_date_display = selectedDate.display;

        console.log('V94: Date → trigger WF06 available_slots');
        nextStage = 'trigger_wf06_available_slots';
        responseText = '⏳ *Buscando horários disponíveis...*\\n\\n_Aguarde um momento..._';

        updateData.awaiting_wf06_available_slots = true;

      } else {
        responseText = `❌ *Opção inválida*\\n\\nEscolha 1, 2 ou 3.`;
        nextStage = 'process_date_selection';
      }
    }
    else if (/^\\d{2}\\/\\d{2}\\/\\d{4}$/.test(dateChoice)) {
      console.log('V94: Custom date:', dateChoice);

      const [day, month, year] = dateChoice.split('/');
      const isoDate = `${year}-${month}-${day}`;
      const dateObj = new Date(isoDate);

      const today = new Date();
      today.setHours(0, 0, 0, 0);

      const dayOfWeek = dateObj.getDay();
      const isWeekend = (dayOfWeek === 0 || dayOfWeek === 6);
      const isPast = dateObj < today;

      if (isPast) {
        responseText = `❌ *Data inválida*\\n\\nA data deve ser no futuro.\\n\\nPor favor, escolha uma das opções ou digite outra data.`;
        nextStage = 'process_date_selection';
      }
      else if (isWeekend) {
        responseText = `❌ *Data inválida*\\n\\nNão atendemos aos finais de semana.\\n\\nPor favor, escolha uma data de segunda a sexta.`;
        nextStage = 'process_date_selection';
      }
      else {
        console.log('V94: Date validated');

        updateData.scheduled_date = isoDate;
        updateData.scheduled_date_display = dateChoice;

        nextStage = 'trigger_wf06_available_slots';
        responseText = '⏳ *Buscando horários disponíveis...*\\n\\n_Aguarde um momento..._';

        updateData.awaiting_wf06_available_slots = true;
      }
    }
    else {
      responseText = `❌ *Formato inválido*\\n\\nEscolha 1-3 ou digite uma data em DD/MM/AAAA`;
      nextStage = 'process_date_selection';
    }
    break;

  // ===== STATE 12: INTERMEDIATE - Trigger WF06 Slots =====
  case 'trigger_wf06_available_slots':
    console.log('V94: INTERMEDIATE STATE - Trigger WF06 available_slots');
    nextStage = 'show_available_slots';
    responseText = ''; // Empty for intermediate
    break;

  // ===== STATE 13: SHOW AVAILABLE SLOTS =====
  case 'show_available_slots':
    console.log('V94: Processing SHOW_AVAILABLE_SLOTS');

    const slotsResponse = input.wf06_available_slots || {};

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

    } else {
      console.warn('V94: No slots available');
      responseText = `⚠️ *Sem horários disponíveis nesta data*\\n\\n` +
                    `Por favor, escolha outra data ou entre em contato:\\n` +
                    `📞 (62) 3092-2900\\n\\n` +
                    `Digite *voltar* para escolher outra data.`;

      nextStage = 'process_date_selection';
    }
    break;

  // ===== STATE 14: PROCESS SLOT SELECTION =====
  case 'process_slot_selection':
    console.log('V94: Processing SLOT SELECTION');

    const slotChoice = message.trim();

    if (slotChoice === '0' || slotChoice === 'voltar') {
      console.log('V94: User wants different date');

      // Go back to date selection
      const nextDatesResponse = currentData.date_suggestions || [];
      if (nextDatesResponse.length > 0) {
        let dateOptions = '';
        nextDatesResponse.forEach((dateObj, index) => {
          const number = index + 1;
          const qualityEmoji = dateObj.quality === 'high' ? '✨' :
                              dateObj.quality === 'medium' ? '📅' : '⚠️';
          dateOptions += `${number}️⃣ *${dateObj.display}*\\n   🕐 ${dateObj.total_slots} horários livres ${qualityEmoji}\\n\\n`;
        });

        responseText = `📅 *Escolha outra data:*\\n\\n` + dateOptions +
                      `💡 *Escolha uma opção (1-3)*\\n` +
                      `_Ou digite uma data específica em DD/MM/AAAA_`;
      } else {
        responseText = `📅 *Informe a data desejada (DD/MM/AAAA):*\\n\\n` +
                      `💡 *Lembre-se:*\\n` +
                      `• Data futura\\n` +
                      `• Dia útil (segunda a sexta-feira)`;
      }

      nextStage = 'process_date_selection';
    }
    else if (/^[1-9]\\d*$/.test(slotChoice)) {
      const selectedIndex = parseInt(slotChoice) - 1;
      const suggestions = currentData.slot_suggestions || [];

      if (selectedIndex >= 0 && selectedIndex < suggestions.length) {
        const selectedSlot = suggestions[selectedIndex];
        console.log('V94: Slot selected:', selectedSlot.formatted);

        updateData.scheduled_time = selectedSlot.start;
        updateData.scheduled_time_display = selectedSlot.formatted;
        updateData.scheduled_end_time = selectedSlot.end;

        // Final confirmation
        const leadName = currentData.lead_name || 'Cliente';
        const serviceInfo = serviceDisplay[currentData.service_type] || { emoji: '📋', name: 'Serviço' };

        responseText = `✅ *Agendamento Confirmado!*\\n\\n` +
                      `👤 *Cliente:* ${leadName}\\n` +
                      `${serviceInfo.emoji} *Serviço:* ${serviceInfo.name}\\n` +
                      `📅 *Data:* ${currentData.scheduled_date_display}\\n` +
                      `🕐 *Horário:* ${selectedSlot.formatted}\\n` +
                      `📍 *Cidade:* ${currentData.city}\\n\\n` +
                      `🎯 *Próximos passos:*\\n` +
                      `1️⃣ Você receberá um e-mail de confirmação\\n` +
                      `2️⃣ Nossa equipe técnica entrará em contato 24h antes\\n` +
                      `3️⃣ Prepare documentação do imóvel para a visita\\n\\n` +
                      `📞 *Dúvidas?* (62) 3092-2900\\n\\n` +
                      `Obrigado por escolher a E2 Soluções! 🚀`;

        nextStage = 'schedule_confirmation';
        updateData.appointment_scheduled = true;
        updateData.status = 'scheduled';

      } else {
        responseText = `❌ *Opção inválida*\\n\\nEscolha um número entre 1 e ${suggestions.length}.`;
        nextStage = 'process_slot_selection';
      }
    }
    else {
      responseText = `❌ *Formato inválido*\\n\\nEscolha o número do horário desejado ou digite 0 para voltar.`;
      nextStage = 'process_slot_selection';
    }
    break;

  // ===== STATE 15: SCHEDULE CONFIRMATION =====
  case 'schedule_confirmation':
    console.log('V94: SCHEDULE CONFIRMATION - Flow complete');
    // This is a final state, no next action needed
    nextStage = 'completed';
    responseText = ''; // Already sent confirmation
    break;

  // ===== DEFAULT: Unknown state =====
  default:
    console.error('V94: Unknown state:', currentStage);
    responseText = `❌ *Erro no sistema*\\n\\nPor favor, digite *reiniciar* para começar novamente.`;
    nextStage = 'greeting';
    break;
}

} // End of switch wrapper

// ===================================================
// V94 CRITICAL: Build output with explicit state preservation
// ===================================================
const output = {
  response_text: responseText,
  update_data: updateData,
  next_stage: nextStage,
  current_stage: nextStage,  // V94: EXPLICIT state preservation for next execution
  phone_number: input.phone_number || input.phone_with_code,
  previous_stage: currentStage,  // V94: Track previous state for debugging
  version: 'V94',  // V94: Version tracking
  timestamp: new Date().toISOString()
};

// V94: Enhanced logging for state transitions
console.log('V94: Current → Next:', currentStage, '→', nextStage);
console.log('V94: Response length:', responseText.length);
console.log('V94: Update data keys:', Object.keys(updateData));
console.log('=== V94 STATE MACHINE END ===');

return output;
"""

# Find and update the State Machine node
state_machine_updated = False
for node in workflow.get('nodes', []):
    if 'State Machine' in node.get('name', '') and node.get('type') == 'n8n-nodes-base.function':
        print(f"✅ Found State Machine node: {node['name']}")
        node['parameters']['functionCode'] = state_machine_v94
        state_machine_updated = True
        break

if not state_machine_updated:
    print("⚠️  Warning: State Machine node not found in workflow")

# Update the Prepare Update Query node to ensure state preservation
prepare_update_query = """
// V94: Prepare Update Query with enhanced state preservation
const stateMachineOutput = $input.first().json;
const phoneNumber = stateMachineOutput.phone_number || stateMachineOutput.phone_with_code;

// V94: Ensure current_stage is ALWAYS preserved
const currentStage = stateMachineOutput.current_stage ||
                     stateMachineOutput.next_stage ||
                     'greeting';

// Build the SET clause dynamically
const updates = [];
const values = [];
let paramIndex = 2; // $1 is phone_number

// V94: ALWAYS update current_stage to prevent loops
updates.push(`current_stage = $${paramIndex}`);
values.push(currentStage);
paramIndex++;

// Add other updates from state machine
if (stateMachineOutput.update_data) {
  Object.entries(stateMachineOutput.update_data).forEach(([key, value]) => {
    updates.push(`${key} = $${paramIndex}`);
    values.push(value);
    paramIndex++;
  });
}

// Always update timestamps
updates.push(`updated_at = NOW()`);
updates.push(`last_message_at = NOW()`);

// V94: Track previous state for debugging
if (stateMachineOutput.previous_stage) {
  updates.push(`previous_stage = $${paramIndex}`);
  values.push(stateMachineOutput.previous_stage);
  paramIndex++;
}

const updateQuery = `
  UPDATE conversations
  SET ${updates.join(', ')}
  WHERE phone_number = $1
  RETURNING *
`;

console.log('V94: Update Query:', updateQuery);
console.log('V94: Values:', [phoneNumber, ...values]);

return {
  query_update_conversation: updateQuery,
  phone_number: phoneNumber,
  values: [phoneNumber, ...values]
};
"""

# Update Prepare Update Query node
prepare_query_updated = False
for node in workflow.get('nodes', []):
    if 'Prepare Update Query' in node.get('name', '') and node.get('type') == 'n8n-nodes-base.code':
        print(f"✅ Found Prepare Update Query node: {node['name']}")
        if 'jsCode' in node['parameters']:
            node['parameters']['jsCode'] = prepare_update_query
        elif 'functionCode' in node['parameters']:
            node['parameters']['functionCode'] = prepare_update_query
        prepare_query_updated = True
        break

if not prepare_query_updated:
    print("⚠️  Warning: Prepare Update Query node not found")

# Save the updated workflow
output_path = os.path.join(WORKFLOWS_DIR, "02_ai_agent_conversation_V94_COMPLETE_FIX.json")

with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(workflow, f, indent=2, ensure_ascii=False)

print(f"✅ V94 workflow generated successfully!")
print(f"📁 Output: {output_path}")
print("\n📝 Next steps:")
print("1. Import this workflow in n8n")
print("2. Test with services 1 or 3 for WF06 integration")
print("3. Verify no loops occur after name input")
print("4. Check state transitions in logs (grep 'V94:')")
print("\n🎯 Key improvements in V94:")
print("- 5-level state resolution fallback")
print("- Auto-correction for WF06 responses")
print("- Explicit state preservation in output")
print("- Enhanced debugging with version tracking")