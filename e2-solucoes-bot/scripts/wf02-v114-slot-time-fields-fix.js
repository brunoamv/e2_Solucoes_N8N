// ===================================================
// V114 STATE MACHINE - SLOT TIME FIELDS FIX
// ===================================================
// CRITICAL BUG FIX: V113.1 - Missing scheduled_time_start and scheduled_time_end
//
// ROOT CAUSE (Execution #10015):
// - User selects time slot successfully
// - State Machine saves scheduled_time_display: "8h às 10h"
// - BUT DOES NOT save scheduled_time_start and scheduled_time_end
// - "Prepare Appointment Data" node reads undefined values
// - PostgreSQL rejects INSERT: "invalid input syntax for type time: 'null'"
//
// V114 SOLUTION:
// 1. Extract start_time and end_time from selected slot (line 888-891)
// 2. Save to collected_data as scheduled_time_start and scheduled_time_end
// 3. Ensure PostgreSQL receives valid TIME values, not null
//
// V114 CHANGES:
// 1. Lines 888-891: Extract start_time and end_time from selectedSlot
// 2. Lines 892-894: Save as scheduled_time_start and scheduled_time_end
// 3. Lines 1002-1004: Preserve time fields in collected_data output
// 4. Version marker: V110 → V114
// 5. All log prefixes: V110 → V114
//
// WHY THIS HAPPENED:
// - State 14 (process_slot_selection) only saved formatted display
// - Database TIME columns require "HH:MM:SS" format
// - WF06 slot structure has start_time and end_time fields
// - We just weren't extracting and saving them
//
// Date: 2026-04-28
// Version: V114 Slot Time Fields Fix
// Based on: V110 Intermediate State Message Handler
// ===================================================

// Helper function for phone formatting
function formatPhoneDisplay(phone) {
  if (!phone) return '';
  const cleaned = phone.replace(/\D/g, '');
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
// V99 CRITICAL FIX: COMPREHENSIVE DATA PRESERVATION
// ===================================================
// Merge ALL data sources to prevent loss
const currentData = {
  // Base: Start with currentData from previous execution
  ...(input.currentData || {}),

  // Merge: Add collected_data from previous state
  ...(input.collected_data || {}),

  // Preserve: Individual fields from input root (highest priority)
  lead_name: input.lead_name || input.currentData?.lead_name || input.collected_data?.lead_name,
  email: input.email || input.currentData?.email || input.collected_data?.email,
  phone_number: input.phone_number || input.currentData?.phone_number || input.collected_data?.phone_number,
  contact_phone: input.contact_phone || input.currentData?.contact_phone || input.collected_data?.contact_phone,
  service_type: input.service_type || input.currentData?.service_type || input.collected_data?.service_type,
  service_selected: input.service_selected || input.currentData?.service_selected || input.collected_data?.service_selected,
  city: input.city || input.currentData?.city || input.collected_data?.city,

  // Preserve scheduling data
  scheduled_date: input.scheduled_date || input.currentData?.scheduled_date || input.collected_data?.scheduled_date,
  scheduled_date_display: input.scheduled_date_display || input.currentData?.scheduled_date_display || input.collected_data?.scheduled_date_display,
  scheduled_time: input.scheduled_time || input.currentData?.scheduled_time || input.collected_data?.scheduled_time,
  scheduled_time_display: input.scheduled_time_display || input.currentData?.scheduled_time_display || input.collected_data?.scheduled_time_display,
  scheduled_end_time: input.scheduled_end_time || input.currentData?.scheduled_end_time || input.collected_data?.scheduled_end_time,

  // V114 CRITICAL: Preserve TIME fields for database
  scheduled_time_start: input.scheduled_time_start || input.currentData?.scheduled_time_start || input.collected_data?.scheduled_time_start,
  scheduled_time_end: input.scheduled_time_end || input.currentData?.scheduled_time_end || input.collected_data?.scheduled_time_end,

  // Preserve suggestions
  date_suggestions: input.date_suggestions || input.currentData?.date_suggestions || input.collected_data?.date_suggestions,
  slot_suggestions: input.slot_suggestions || input.currentData?.slot_suggestions || input.collected_data?.slot_suggestions,

  // V108: CRITICAL - Preserve selected_date from previous execution
  selected_date: input.selected_date || input.currentData?.selected_date || input.collected_data?.selected_date
};

// ===================================================
// V108 CRITICAL FIX: WF06 RESPONSE PROCESSING
// ===================================================
// Process WF06 awaiting flags WITH user message (not before state resolution!)
let forcedStage = null;
let processWF06Selection = false;

// Check if user is responding to WF06 next dates
if (currentData.awaiting_wf06_next_dates === true && message) {
  console.log('🔄 V114: User responding to WF06 dates WITH message:', message);
  forcedStage = 'process_date_selection';
  processWF06Selection = true;  // Flag to process date selection immediately

  // DO NOT clear flag yet - will be cleared after successful processing
}
// Check if user is responding to WF06 available slots
else if (currentData.awaiting_wf06_available_slots === true && message) {
  console.log('🔄 V114: User responding to WF06 slots WITH message:', message);
  forcedStage = 'process_slot_selection';
  processWF06Selection = true;  // Flag to process slot selection immediately

  // DO NOT clear flag yet - will be cleared after successful processing
}

// V100: State resolution with preservation (V108: use forcedStage if set)
const currentStage = forcedStage ||
                     input.current_stage ||
                     input.next_stage ||
                     input.currentData?.current_stage ||
                     input.currentData?.next_stage ||
                     'greeting';

// V100: Identify intermediate states that trigger WF06
const intermediateStates = [
  'trigger_wf06_next_dates',
  'trigger_wf06_available_slots'
];

const isIntermediateState = intermediateStates.includes(currentStage);

// V114: Enhanced logging for debugging
console.log('=== V114 STATE MACHINE START (SLOT TIME FIELDS FIX) ===');
console.log('V114: conversation_id:', input.conversation_id || input.id || 'NULL');
console.log('V114: Current stage:', currentStage);
console.log('V114: Is intermediate state:', isIntermediateState);
console.log('V114: Forced stage from awaiting flag:', forcedStage);
console.log('V114: Process WF06 selection immediately:', processWF06Selection);
console.log('V114: User message:', message);
console.log('V114: Merged currentData keys:', Object.keys(currentData));
console.log('V114: Preserved selected_date:', currentData.selected_date);
console.log('V114: Preserved scheduled_date:', currentData.scheduled_date);
console.log('V114: ✅ CRITICAL - Preserved scheduled_time_start:', currentData.scheduled_time_start);
console.log('V114: ✅ CRITICAL - Preserved scheduled_time_end:', currentData.scheduled_time_end);
console.log('V114: Input keys:', Object.keys(input));

// V100: Check for WF06 responses
const hasWF06NextDates = !!(input.wf06_next_dates);
const hasWF06Slots = !!(input.wf06_available_slots);
const hasWF06Response = hasWF06NextDates || hasWF06Slots;

console.log('V114: Has WF06 response:', hasWF06Response);
if (hasWF06NextDates) console.log('V114: Has next_dates data');
if (hasWF06Slots) console.log('V114: Has available_slots data');

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

// V104: Track if WF06 was handled by auto-correction
let wf06HandledByAutoCorrection = false;

// V104: Auto-correct state if we have WF06 response but wrong state
if (hasWF06Response) {
  if (hasWF06NextDates && currentStage !== 'show_available_dates') {
    console.log('V104: AUTO-CORRECTING state to show_available_dates (has WF06 next_dates)');
    nextStage = 'show_available_dates';
    // Process immediately without re-entering switch
    const nextDatesResponse = input.wf06_next_dates;

    if (nextDatesResponse.success && nextDatesResponse.dates && nextDatesResponse.dates.length > 0) {
      let dateOptions = '';
      nextDatesResponse.dates.forEach((dateObj, index) => {
        const number = index + 1;
        const qualityEmoji = dateObj.quality === 'high' ? '✨' :
                            dateObj.quality === 'medium' ? '📅' : '⚠️';
        dateOptions += `${number}️⃣ *${dateObj.display}*\n   🕐 ${dateObj.total_slots} horários livres ${qualityEmoji}\n\n`;
      });

      responseText = `📅 *Agendar Visita Técnica - ${getServiceName(currentData.service_selected || '1')}*\n\n` +
                    `📆 *Próximas datas com horários disponíveis:*\n\n` +
                    dateOptions +
                    `💡 *Escolha uma opção (1-3)*\n` +
                    `_Ou digite uma data específica em DD/MM/AAAA_\n\n` +
                    `⏱️ *Duração*: 2 horas\n` +
                    `📍 *Cidade*: ${currentData.city}`;

      updateData.date_suggestions = nextDatesResponse.dates;
      updateData.awaiting_wf06_next_dates = true;  // V108: Set flag for next user input
      nextStage = 'process_date_selection';

      // V114 DEBUG: Verify flag was actually set
      console.log('V114: AUTO-CORRECTION - Set flags:', {
        date_suggestions_count: updateData.date_suggestions?.length || 0,
        awaiting_wf06_next_dates: updateData.awaiting_wf06_next_dates,
        nextStage: nextStage
      });

      // V104: Mark WF06 as handled by auto-correction
      wf06HandledByAutoCorrection = true;
    }
  } else if (hasWF06Slots && currentStage !== 'show_available_slots') {
    console.log('V104: AUTO-CORRECTING state to show_available_slots (has WF06 available_slots)');
    nextStage = 'show_available_slots';
    // Process immediately
    const slotsResponse = input.wf06_available_slots;

    if (slotsResponse.success && slotsResponse.available_slots && slotsResponse.available_slots.length > 0) {
      let slotOptions = '';
      slotsResponse.available_slots.forEach((slot, index) => {
        const number = index + 1;
        slotOptions += `${number}️⃣ *${slot.formatted}* ✅\n`;
      });

      responseText = `🕐 *Horários Disponíveis - ${currentData.scheduled_date_display}*\n\n` +
                    slotOptions + `\n` +
                    `💡 *Escolha um horário (1-${slotsResponse.available_slots.length})*\n` +
                    `_Ou digite 0 para voltar e escolher outra data_`;

      updateData.slot_suggestions = slotsResponse.available_slots;
      updateData.awaiting_wf06_available_slots = true;  // V108: Set flag for next user input
      nextStage = 'process_slot_selection';

      // V104: Mark WF06 as handled by auto-correction
      wf06HandledByAutoCorrection = true;
    }
  }
}

// V104: Skip switch for intermediate states without message and no WF06 response
if (isIntermediateState && !message && !hasWF06Response) {
  console.log('V104: Intermediate state without data - maintaining transition');

  if (currentStage === 'trigger_wf06_next_dates') {
    nextStage = 'show_available_dates';
    responseText = ''; // Empty is OK for intermediate
  } else if (currentStage === 'trigger_wf06_available_slots') {
    nextStage = 'show_available_slots';
    responseText = '';
  }
}
// V114 FIX 1: Handle intermediate states WITH user message (unexpected situation)
else if (isIntermediateState && message && !hasWF06Response) {
  console.error('V114: ❌ UNEXPECTED - User sent message while in intermediate state!');
  console.error('V114: currentStage:', currentStage);
  console.error('V114: message:', message);
  console.error('V114: This means WF06 HTTP Request never executed!');

  // Inform user about the problem and reset to greeting
  responseText = `⚠️ *Ops! Algo deu errado...*\n\n` +
                `Parece que houve um problema ao buscar as informações.\n\n` +
                `Por favor, digite *reiniciar* para começar novamente.\n\n` +
                `📞 *Ou ligue:* (62) 3092-2900`;
  nextStage = 'greeting';

  // V114: Log full context for debugging
  console.error('V114: Full input keys:', Object.keys(input));
  console.error('V114: state_machine_state from DB:', input.state_machine_state);
  console.error('V114: awaiting_wf06_next_dates:', currentData.awaiting_wf06_next_dates);
  console.error('V114: hasWF06NextDates:', hasWF06NextDates);
  console.error('V114: hasWF06Slots:', hasWF06Slots);
}
// V104: Only process switch if NOT already handled by WF06 auto-correction
else if (!wf06HandledByAutoCorrection && !isIntermediateState) {
  console.log('V104: Entering switch - WF06 not handled by auto-correction');

// ===================================================
// V104 STATE MACHINE LOGIC - ALL STATES IMPLEMENTED
// ===================================================

switch (currentStage) {

  // ===== STATE 1: GREETING - Show menu =====
  case 'greeting':
  case 'menu':
    console.log('V101: Processing GREETING state');
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
    console.log('V101: Processing SERVICE_SELECTION state');

    if (/^[1-5]$/.test(message)) {
      console.log('V101: Valid service number:', message);
      updateData.service_selected = message;
      updateData.service_type = serviceMapping[message];
      console.log('V101: Service mapped:', message, '→', updateData.service_type);

      responseText = `✅ *Perfeito!*

👤 *Qual é o seu nome completo?*

💡 _Exemplo: Maria Silva Santos_
_Usaremos para personalizar seu atendimento_`;
      nextStage = 'collect_name';
    } else {
      console.log('V101: Invalid service selection');
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
    console.log('V101: Processing COLLECT_NAME state');

    const trimmedName = message.trim();

    if (trimmedName.length >= 2 && !/^[0-9]+$/.test(trimmedName)) {
      console.log('V101: Valid name received:', trimmedName);
      updateData.lead_name = trimmedName;

      const whatsappPhone = input.phone_number || input.phone_with_code || '';
      console.log('V101: WhatsApp phone from input:', whatsappPhone);

      responseText = `📱 *Ótimo, ${trimmedName}!*

Vi que você está me enviando mensagens pelo número:
*${formatPhoneDisplay(whatsappPhone)}*

Este é o melhor número para contato?

1️⃣ *Sim, pode usar este*
2️⃣ *Não, vou informar outro*

💡 _Digite 1 ou 2_`;

      nextStage = 'collect_phone_whatsapp_confirmation';
      console.log('V101: Skip collect_phone, go directly to WhatsApp confirmation');

    } else {
      console.log('V101: Invalid name format');
      responseText = `❌ *Nome inválido*

Por favor, informe seu nome completo (mínimo 2 letras).

_Não use apenas números ou caracteres especiais._`;
      nextStage = 'collect_name';
    }
    break;

  // ===== STATE 4: PHONE WHATSAPP CONFIRMATION =====
  case 'collect_phone_whatsapp_confirmation':
    console.log('V101: Processing PHONE_WHATSAPP_CONFIRMATION state');

    if (message === '1') {
      console.log('V101: WhatsApp number confirmed');

      const confirmedPhone = input.phone_number || input.phone_with_code || '';
      updateData.phone_number = confirmedPhone;
      updateData.contact_phone = confirmedPhone;

      responseText = `📧 *Qual é o seu e-mail, ${currentData.lead_name || 'cliente'}?*

💡 _Exemplo: maria.silva@email.com_

Se preferir não informar, digite *pular*
_O e-mail nos ajuda a enviar documentação técnica e propostas_`;
      nextStage = 'collect_email';

    } else if (message === '2') {
      console.log('V101: User wants alternative phone');

      responseText = `📱 *Qual número prefere para contato, ${currentData.lead_name || 'cliente'}?*

Por favor, informe com DDD:

💡 _Exemplo: (62) 98765-4321_
_Usaremos este número para agendarmos sua visita técnica_`;
      nextStage = 'collect_phone_alternative';

    } else {
      console.log('V101: Invalid WhatsApp confirmation option');
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
    console.log('V101: Processing COLLECT_PHONE_ALTERNATIVE state');

    const phoneRegex = /^\(?\d{2}\)?\s?9?\d{4}[-\s]?\d{4}$/;

    if (phoneRegex.test(message)) {
      console.log('V101: Valid alternative phone received');

      const cleanedPhone = message.replace(/\D/g, '');
      updateData.phone_number = cleanedPhone;
      updateData.contact_phone = cleanedPhone;

      responseText = `📧 *Qual é o seu e-mail, ${currentData.lead_name || 'cliente'}?*

💡 _Exemplo: maria.silva@email.com_

Se preferir não informar, digite *pular*
_O e-mail nos ajuda a enviar documentação técnica e propostas_`;
      nextStage = 'collect_email';

    } else {
      console.log('V101: Invalid alternative phone format');
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
    console.log('V101: Processing COLLECT_EMAIL state');

    if (message === 'pular') {
      console.log('V101: User skipped email');
      updateData.email = 'não informado';
      responseText = `📍 *Em qual cidade você está, ${currentData.lead_name || 'cliente'}?*

💡 _Exemplo: Goiânia - GO_
_Precisamos saber para agendar a visita técnica com nossa equipe local_`;
      nextStage = 'collect_city';

    } else {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

      if (emailRegex.test(message)) {
        console.log('V101: Valid email received');
        updateData.email = message;
        responseText = `📍 *Em qual cidade você está, ${currentData.lead_name || 'cliente'}?*

💡 _Exemplo: Goiânia - GO_
_Precisamos saber para agendar a visita técnica com nossa equipe local_`;
        nextStage = 'collect_city';
      } else {
        console.log('V101: Invalid email format');
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
    console.log('V101: Processing COLLECT_CITY state');

    if (message.length >= 2) {
      console.log('V101: Valid city received');
      updateData.city = message;

      // V99 FIX: Use merged currentData with multiple fallbacks
      const leadName = currentData.lead_name || 'não informado';
      const phoneNumber = currentData.contact_phone || currentData.phone_number || 'não informado';
      const email = currentData.email || 'não informado';
      const city = updateData.city || 'não informado';
      const serviceType = currentData.service_type || 'não informado';
      const serviceInfo = serviceDisplay[serviceType] || { emoji: '❓', name: 'Não informado' };

      console.log('V101: Confirmation summary data:');
      console.log('V101:   lead_name:', leadName);
      console.log('V101:   phoneNumber:', phoneNumber);
      console.log('V101:   email:', email);
      console.log('V101:   city:', city);
      console.log('V101:   serviceType:', serviceType);

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
      console.log('V101: Going to State 8 (confirmation)');

    } else {
      console.log('V101: Invalid city (too short)');
      responseText = `❌ *Cidade inválida*

Por favor, informe uma cidade válida (mínimo 2 letras).

_Exemplo: Goiânia, Brasília, Anápolis..._`;
      nextStage = 'collect_city';
    }
    break;

  // ===== STATE 8: CONFIRMATION =====
  case 'confirmation':
    console.log('V101: Processing CONFIRMATION state');

    if (message === '1') {
      // V99 CRITICAL FIX: Robust service type resolution
      const serviceSelected = currentData.service_selected ||
                             currentData.service_type ||
                             input.service_selected ||
                             input.service_type ||
                             '1';

      // Map numeric to service type if needed
      const serviceMapped = serviceMapping[serviceSelected] || serviceSelected;

      console.log('V101: Service resolution chain:');
      console.log('V101:   service_selected from currentData:', currentData.service_selected);
      console.log('V101:   service_type from currentData:', currentData.service_type);
      console.log('V101:   Final serviceSelected:', serviceSelected);
      console.log('V101:   Final serviceMapped:', serviceMapped);

      if (serviceMapped === 'energia_solar' || serviceMapped === 'projeto_eletrico') {
        console.log('V101: Services 1 or 3 → trigger WF06 next_dates');

        nextStage = 'trigger_wf06_next_dates';
        responseText = '⏳ *Buscando próximas datas disponíveis...*\n\n_Aguarde um momento..._';

        // V108: DO NOT set awaiting flag here - it will be set after WF06 returns dates

      } else {
        console.log('V101: Services 2, 4, or 5 → handoff to commercial');

        // V99 FIX: Null-safe lead name
        const leadName = currentData.lead_name || 'Cliente';

        responseText = `Obrigado pelas informações, ${leadName}! 👍\n\n` +
                      `Para o serviço de *${getServiceName(serviceSelected)}*, nossa equipe comercial ` +
                      `entrará em contato em breve para alinhar os detalhes.\n\n` +
                      `📞 Caso prefira falar agora: (62) 3092-2900\n\n` +
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
      responseText = `📝 *Correção de Dados*\n\n` +
                    `Digite o que deseja corrigir:\n\n` +
                    `1️⃣ - Nome\n` +
                    `2️⃣ - Telefone\n` +
                    `3️⃣ - Email\n` +
                    `4️⃣ - Cidade\n` +
                    `5️⃣ - Serviço\n\n` +
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
    console.log('V101: INTERMEDIATE STATE - Trigger WF06 next_dates');
    nextStage = 'show_available_dates';
    responseText = ''; // Empty for intermediate state
    break;

  // ===== STATE 10: SHOW AVAILABLE DATES =====
  case 'show_available_dates':
    console.log('V101: Processing SHOW_AVAILABLE_DATES');

    const nextDatesResponse = input.wf06_next_dates || {};

    if (nextDatesResponse.success && nextDatesResponse.dates && nextDatesResponse.dates.length > 0) {
      let dateOptions = '';
      nextDatesResponse.dates.forEach((dateObj, index) => {
        const number = index + 1;
        const qualityEmoji = dateObj.quality === 'high' ? '✨' :
                            dateObj.quality === 'medium' ? '📅' : '⚠️';
        dateOptions += `${number}️⃣ *${dateObj.display}*\n   🕐 ${dateObj.total_slots} horários livres ${qualityEmoji}\n\n`;
      });

      responseText = `📅 *Agendar Visita Técnica - ${getServiceName(currentData.service_selected || '1')}*\n\n` +
                    `📆 *Próximas datas com horários disponíveis:*\n\n` +
                    dateOptions +
                    `💡 *Escolha uma opção (1-3)*\n` +
                    `_Ou digite uma data específica em DD/MM/AAAA_\n\n` +
                    `⏱️ *Duração*: 2 horas\n` +
                    `📍 *Cidade*: ${currentData.city}`;

      updateData.date_suggestions = nextDatesResponse.dates;
      updateData.awaiting_wf06_next_dates = true;  // V108: Set flag AFTER showing dates
      nextStage = 'process_date_selection';

      // V114 DEBUG: Verify flag was actually set
      console.log('V114: STATE 10 - Set flags:', {
        date_suggestions_count: updateData.date_suggestions?.length || 0,
        awaiting_wf06_next_dates: updateData.awaiting_wf06_next_dates,
        nextStage: nextStage
      });

    } else {
      console.warn('V100: WF06 failed, falling back to manual');
      responseText = `⚠️ *Não conseguimos buscar disponibilidade automaticamente*\n\n` +
                    `Por favor, informe a data desejada (DD/MM/AAAA):\n\n` +
                    `💡 *Lembre-se:*\n` +
                    `• Data futura (não pode ser hoje ou passado)\n` +
                    `• Dia útil (segunda a sexta-feira)\n\n` +
                    `_Digite a data..._`;

      nextStage = 'collect_appointment_date_manual';
    }
    break;

  // ===== STATE 11: PROCESS DATE SELECTION =====
  case 'process_date_selection':
    console.log('V114: Processing DATE SELECTION');

    const dateChoice = message.trim();

    if (/^[1-3]$/.test(dateChoice)) {
      const selectedIndex = parseInt(dateChoice) - 1;
      const suggestions = currentData.date_suggestions || [];

      if (selectedIndex >= 0 && selectedIndex < suggestions.length) {
        const selectedDate = suggestions[selectedIndex];
        console.log('V114: Date selected:', selectedDate.date);

        // V108 CRITICAL: Store selected_date for HTTP Request access
        updateData.selected_date = selectedDate.date;  // ISO format for WF06
        updateData.scheduled_date = selectedDate.date;
        updateData.scheduled_date_display = selectedDate.display;

        console.log('V114: STORED selected_date:', updateData.selected_date);
        console.log('V114: Date → trigger WF06 available_slots');

        nextStage = 'trigger_wf06_available_slots';
        responseText = '⏳ *Buscando horários disponíveis...*\n\n_Aguarde um momento..._';

        // V108: Clear awaiting_next_dates flag (user responded successfully)
        updateData.awaiting_wf06_next_dates = false;
        // V108: DO NOT set awaiting_slots flag here - will be set after WF06 returns

      } else {
        responseText = `❌ *Opção inválida*\n\nEscolha 1, 2 ou 3.`;
        nextStage = 'process_date_selection';
      }
    }
    else if (/^\d{2}\/\d{2}\/\d{4}$/.test(dateChoice)) {
      console.log('V114: Custom date:', dateChoice);

      const [day, month, year] = dateChoice.split('/');
      const isoDate = `${year}-${month}-${day}`;
      const dateObj = new Date(isoDate);

      const today = new Date();
      today.setHours(0, 0, 0, 0);

      const dayOfWeek = dateObj.getDay();
      const isWeekend = (dayOfWeek === 0 || dayOfWeek === 6);
      const isPast = dateObj < today;

      if (isPast) {
        responseText = `❌ *Data inválida*\n\nA data deve ser no futuro.\n\nPor favor, escolha uma das opções ou digite outra data.`;
        nextStage = 'process_date_selection';
      }
      else if (isWeekend) {
        responseText = `❌ *Data inválida*\n\nNão atendemos aos finais de semana.\n\nPor favor, escolha uma data de segunda a sexta.`;
        nextStage = 'process_date_selection';
      }
      else {
        console.log('V114: Date validated');

        // V108 CRITICAL: Store selected_date for HTTP Request access
        updateData.selected_date = isoDate;  // ISO format for WF06
        updateData.scheduled_date = isoDate;
        updateData.scheduled_date_display = dateChoice;

        console.log('V114: STORED selected_date:', updateData.selected_date);

        nextStage = 'trigger_wf06_available_slots';
        responseText = '⏳ *Buscando horários disponíveis...*\n\n_Aguarde um momento..._';

        // V108: Clear awaiting_next_dates flag
        updateData.awaiting_wf06_next_dates = false;
      }
    }
    else {
      responseText = `❌ *Formato inválido*\n\nEscolha 1-3 ou digite uma data em DD/MM/AAAA`;
      nextStage = 'process_date_selection';
    }
    break;

  // ===== STATE 12: INTERMEDIATE - Trigger WF06 Slots =====
  case 'trigger_wf06_available_slots':
    console.log('V114: INTERMEDIATE STATE - Trigger WF06 available_slots');
    console.log('V114: selected_date for WF06:', currentData.selected_date || updateData.selected_date);
    nextStage = 'show_available_slots';
    responseText = ''; // Empty for intermediate
    break;

  // ===== STATE 13: SHOW AVAILABLE SLOTS =====
  case 'show_available_slots':
    console.log('V114: Processing SHOW_AVAILABLE_SLOTS');

    const slotsResponse = input.wf06_available_slots || {};

    if (slotsResponse.success && slotsResponse.available_slots && slotsResponse.available_slots.length > 0) {
      let slotOptions = '';
      slotsResponse.available_slots.forEach((slot, index) => {
        const number = index + 1;
        slotOptions += `${number}️⃣ *${slot.formatted}* ✅\n`;
      });

      responseText = `🕐 *Horários Disponíveis - ${currentData.scheduled_date_display}*\n\n` +
                    slotOptions + `\n` +
                    `💡 *Escolha um horário (1-${slotsResponse.available_slots.length})*\n` +
                    `_Ou digite 0 para voltar e escolher outra data_`;

      updateData.slot_suggestions = slotsResponse.available_slots;
      updateData.awaiting_wf06_available_slots = true;  // V108: Set flag AFTER showing slots
      nextStage = 'process_slot_selection';

    } else {
      console.warn('V100: No slots available');
      responseText = `⚠️ *Sem horários disponíveis nesta data*\n\n` +
                    `Por favor, escolha outra data ou entre em contato:\n` +
                    `📞 (62) 3092-2900\n\n` +
                    `Digite *voltar* para escolher outra data.`;

      nextStage = 'process_date_selection';
    }
    break;

  // ===== STATE 14: PROCESS SLOT SELECTION =====
  case 'process_slot_selection':
    console.log('V114: Processing SLOT SELECTION');

    const slotChoice = message.trim();

    if (slotChoice === '0' || slotChoice === 'voltar') {
      console.log('V114: User wants different date');

      // Go back to date selection
      const nextDatesResponse = currentData.date_suggestions || [];
      if (nextDatesResponse.length > 0) {
        let dateOptions = '';
        nextDatesResponse.forEach((dateObj, index) => {
          const number = index + 1;
          const qualityEmoji = dateObj.quality === 'high' ? '✨' :
                              dateObj.quality === 'medium' ? '📅' : '⚠️';
          dateOptions += `${number}️⃣ *${dateObj.display}*\n   🕐 ${dateObj.total_slots} horários livres ${qualityEmoji}\n\n`;
        });

        responseText = `📅 *Escolha outra data:*\n\n` + dateOptions +
                      `💡 *Escolha uma opção (1-3)*\n` +
                      `_Ou digite uma data específica em DD/MM/AAAA_`;
      } else {
        responseText = `📅 *Informe a data desejada (DD/MM/AAAA):*\n\n` +
                      `💡 *Lembre-se:*\n` +
                      `• Data futura\n` +
                      `• Dia útil (segunda a sexta-feira)`;
      }

      updateData.awaiting_wf06_available_slots = false;  // V108: Clear flag
      updateData.awaiting_wf06_next_dates = true;  // V108: Set flag for date selection
      nextStage = 'process_date_selection';
    }
    else if (/^[1-9]\d*$/.test(slotChoice)) {
      const selectedIndex = parseInt(slotChoice) - 1;
      const suggestions = currentData.slot_suggestions || [];

      if (selectedIndex >= 0 && selectedIndex < suggestions.length) {
        const selectedSlot = suggestions[selectedIndex];
        console.log('V114: Slot selected:', selectedSlot.formatted);

        // ===================================================
        // V114 CRITICAL FIX: Extract TIME fields from slot
        // ===================================================
        // WF06 slot structure: { start_time: "08:00", end_time: "10:00", formatted: "8h às 10h" }
        // PostgreSQL TIME columns need "HH:MM:SS" format
        // Extract start_time and end_time for database INSERT

        const startTime = selectedSlot.start_time || selectedSlot.start || null;
        const endTime = selectedSlot.end_time || selectedSlot.end || null;

        console.log('V114: ✅ CRITICAL FIX - Extracted TIME fields:');
        console.log('V114:   start_time:', startTime);
        console.log('V114:   end_time:', endTime);
        console.log('V114:   formatted display:', selectedSlot.formatted);

        // V114 CRITICAL: Save TIME fields for database
        updateData.scheduled_time = startTime;  // Backward compatibility
        updateData.scheduled_time_display = selectedSlot.formatted;  // For WhatsApp
        updateData.scheduled_end_time = endTime;  // Backward compatibility

        // V114 NEW: Explicit TIME fields for PostgreSQL
        updateData.scheduled_time_start = startTime;  // PostgreSQL TIME column
        updateData.scheduled_time_end = endTime;      // PostgreSQL TIME column

        // V99 FIX: Null-safe final confirmation
        const leadName = currentData.lead_name || 'Cliente';
        const serviceInfo = serviceDisplay[currentData.service_type] || { emoji: '📋', name: 'Serviço' };

        responseText = `✅ *Agendamento Confirmado!*\n\n` +
                      `👤 *Cliente:* ${leadName}\n` +
                      `${serviceInfo.emoji} *Serviço:* ${serviceInfo.name}\n` +
                      `📅 *Data:* ${currentData.scheduled_date_display}\n` +
                      `🕐 *Horário:* ${selectedSlot.formatted}\n` +
                      `📍 *Cidade:* ${currentData.city}\n\n` +
                      `🎯 *Próximos passos:*\n` +
                      `1️⃣ Você receberá um e-mail de confirmação\n` +
                      `2️⃣ Nossa equipe técnica entrará em contato 24h antes\n` +
                      `3️⃣ Prepare documentação do imóvel para a visita\n\n` +
                      `📞 *Dúvidas?* (62) 3092-2900\n\n` +
                      `Obrigado por escolher a E2 Soluções! 🚀`;

        nextStage = 'schedule_confirmation';
        updateData.appointment_scheduled = true;
        updateData.status = 'scheduled';

        // V108: Clear awaiting flag
        updateData.awaiting_wf06_available_slots = false;

      } else {
        responseText = `❌ *Opção inválida*\n\nEscolha um número entre 1 e ${suggestions.length}.`;
        nextStage = 'process_slot_selection';
      }
    }
    else {
      responseText = `❌ *Formato inválido*\n\nEscolha o número do horário desejado ou digite 0 para voltar.`;
      nextStage = 'process_slot_selection';
    }
    break;

  // ===== STATE 15: SCHEDULE CONFIRMATION =====
  case 'schedule_confirmation':
    console.log('V114: SCHEDULE CONFIRMATION - Flow complete');
    // This is a final state, no next action needed
    nextStage = 'completed';
    responseText = ''; // Already sent confirmation
    break;

  // ===== DEFAULT: Unknown state =====
  default:
    console.error('V100: Unknown state:', currentStage);
    responseText = `❌ *Erro no sistema*\n\nPor favor, digite *reiniciar* para começar novamente.`;
    nextStage = 'greeting';
    break;
}

} // End of switch wrapper
else {
  // V104: WF06 was handled by auto-correction, skip switch execution
  console.log('V104: Skipping switch - WF06 already handled by auto-correction');
  console.log('V104: Using auto-correction output - nextStage:', nextStage);
  console.log('V104: Using auto-correction output - responseText length:', responseText.length);
}

// ===================================================
// V114 FIX 2: CRITICAL VALIDATION - Detect empty response_text
// ===================================================
if (!responseText && !isIntermediateState) {
  console.error('V114: ❌ CRITICAL - response_text is EMPTY in non-intermediate state!');
  console.error('V114: currentStage:', currentStage);
  console.error('V114: nextStage:', nextStage);
  console.error('V114: message:', message);
  console.error('V114: isIntermediateState:', isIntermediateState);
  console.error('V114: hasWF06Response:', hasWF06Response);
  console.error('V114: wf06HandledByAutoCorrection:', wf06HandledByAutoCorrection);
  console.error('V114: awaiting_wf06_next_dates:', currentData.awaiting_wf06_next_dates);
  console.error('V114: awaiting_wf06_available_slots:', currentData.awaiting_wf06_available_slots);

  // Emergency fallback
  responseText = `⚠️ *Erro no processamento*\n\n` +
                `Desculpe, algo deu errado.\n\n` +
                `Por favor, digite *reiniciar* para começar novamente.\n\n` +
                `📞 *Ou ligue:* (62) 3092-2900`;
  nextStage = 'greeting';
}

// ===================================================
// V114 CRITICAL: Build output with TIME fields preservation
// ===================================================
const output = {
  response_text: responseText,
  conversation_id: input.conversation_id || input.id || input.currentData?.conversation_id || null,

  // V100: Merge ALL data for next execution
  collected_data: {
    ...updateData,  // New data from current execution

    // V100: PRESERVE existing data if not overwritten
    lead_name: updateData.lead_name || currentData.lead_name,
    email: updateData.email || currentData.email,
    phone_number: updateData.phone_number || currentData.phone_number,
    contact_phone: updateData.contact_phone || currentData.contact_phone,
    service_type: updateData.service_type || currentData.service_type,
    service_selected: updateData.service_selected || currentData.service_selected,
    city: updateData.city || currentData.city,

    // V108 CRITICAL: Preserve selected_date for HTTP Request access
    selected_date: updateData.selected_date || currentData.selected_date,

    // Preserve scheduling data
    scheduled_date: updateData.scheduled_date || currentData.scheduled_date,
    scheduled_date_display: updateData.scheduled_date_display || currentData.scheduled_date_display,
    scheduled_time: updateData.scheduled_time || currentData.scheduled_time,
    scheduled_time_display: updateData.scheduled_time_display || currentData.scheduled_time_display,
    scheduled_end_time: updateData.scheduled_end_time || currentData.scheduled_end_time,

    // V114 CRITICAL: Preserve TIME fields for PostgreSQL
    scheduled_time_start: updateData.scheduled_time_start || currentData.scheduled_time_start,
    scheduled_time_end: updateData.scheduled_time_end || currentData.scheduled_time_end,

    // Preserve suggestions
    date_suggestions: updateData.date_suggestions || currentData.date_suggestions,
    slot_suggestions: updateData.slot_suggestions || currentData.slot_suggestions,

    // V104 FIX: CRITICAL - Include state information in collected_data
    // This ensures Build Update Queries can access state fields and update database
    current_stage: nextStage,
    next_stage: nextStage,
    previous_stage: currentStage,

    // V109 FIX: Default to false instead of undefined
    // Bug: When both updateData and currentData have undefined flags (default when not set),
    // output will have undefined, causing detection logic at line 94 to fail (undefined !== true)
    // Solution: Explicitly default to false using || operator
    awaiting_wf06_next_dates: updateData.awaiting_wf06_next_dates !== undefined ?
                               updateData.awaiting_wf06_next_dates :
                               (currentData.awaiting_wf06_next_dates || false),
    awaiting_wf06_available_slots: updateData.awaiting_wf06_available_slots !== undefined ?
                                    updateData.awaiting_wf06_available_slots :
                                    (currentData.awaiting_wf06_available_slots || false)
  },

  next_stage: nextStage,
  current_stage: nextStage,  // V100: EXPLICIT state preservation for next execution
  phone_number: input.phone_number || input.phone_with_code,
  previous_stage: currentStage,  // V100: Track previous state for debugging
  version: 'V114',  // V114: Slot time fields fix
  timestamp: new Date().toISOString()
};

// V114: Enhanced logging for state transitions
console.log('V114: Current → Next:', currentStage, '→', nextStage);
console.log('V114: Response length:', responseText.length);
console.log('V114: Update data keys:', Object.keys(output.collected_data));
console.log('V114: Preserved data in collected_data:');
console.log('V114:   lead_name:', output.collected_data.lead_name);
console.log('V114:   email:', output.collected_data.email);
console.log('V114:   phone_number:', output.collected_data.phone_number);
console.log('V114:   service_type:', output.collected_data.service_type);
console.log('V114:   service_selected:', output.collected_data.service_selected);
console.log('V114: ✅ CRITICAL - selected_date in collected_data:', output.collected_data.selected_date);
console.log('V114: ✅ CRITICAL - TIME fields in collected_data:');
console.log('V114:   scheduled_time_start:', output.collected_data.scheduled_time_start);
console.log('V114:   scheduled_time_end:', output.collected_data.scheduled_time_end);
console.log('V114:   scheduled_time_display:', output.collected_data.scheduled_time_display);
console.log('V114: ✅ CRITICAL - State fields in collected_data:');
console.log('V114:   current_stage:', output.collected_data.current_stage);
console.log('V114:   next_stage:', output.collected_data.next_stage);
console.log('V114:   previous_stage:', output.collected_data.previous_stage);
console.log('V114: ✅ WF06 FLAGS:');
console.log('V114:   awaiting_wf06_next_dates:', output.collected_data.awaiting_wf06_next_dates);
console.log('V114:   awaiting_wf06_available_slots:', output.collected_data.awaiting_wf06_available_slots);
console.log('V114: Output conversation_id:', output.conversation_id);
console.log('=== V114 STATE MACHINE END ===');

return output;
