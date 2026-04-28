// ===================================================
// V89 STATE MACHINE - FIX WF06 DATA ACCESS
// ===================================================
// CRITICAL FIX: Improved WF06 response data access
// - V88: Prepare nodes preserve user data ✅
// - V89: State Machine accesses WF06 data from multiple locations
// - V89: Better logging for data flow debugging
//
// Root Cause (V88 issue):
// - State Machine checked ONLY input.wf06_next_dates
// - After Merge, data might be in currentData.wf06_next_dates
// - Condition failed → fell through to default → reset to greeting ❌
//
// V89 Fix:
// - Check input.wf06_next_dates (direct from Prepare node)
// - Check currentData.wf06_next_dates (from Merge + Get Conversation)
// - Check input.currentData.wf06_next_dates (nested structure)
// - Explicit logging of data structure for debugging
//
// Date: 2026-04-20
// Version: V89
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
const currentStage = input.current_stage || 'greeting';
const currentData = input.currentData || {};

console.log('=== V89 STATE MACHINE START ===');
console.log('V89: Current stage:', currentStage);
console.log('V89: User message:', message);
console.log('V89: Input keys:', Object.keys(input));
console.log('V89: CurrentData keys:', Object.keys(currentData));
console.log('V89: Has input.wf06_next_dates:', !!input.wf06_next_dates);
console.log('V89: Has currentData.wf06_next_dates:', !!currentData.wf06_next_dates);
console.log('V89: Has input.wf06_available_slots:', !!input.wf06_available_slots);
console.log('V89: Has currentData.wf06_available_slots:', !!currentData.wf06_available_slots);

// Service type mapping
const serviceMapping = {
  '1': 'energia_solar',
  '2': 'subestacao',
  '3': 'projeto_eletrico',
  '4': 'armazenamento_energia',
  '5': 'analise_laudo'
};

// Service emoji and name mapping
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

// ===================================================
// V89 STATE MACHINE LOGIC - ALL STATES IMPLEMENTED
// ===================================================

switch (currentStage) {

  // ===== STATE 1: GREETING - Show menu =====
  case 'greeting':
  case 'menu':
    console.log('V89: Processing GREETING state');
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
    console.log('V89: Processing SERVICE_SELECTION state');

    if (/^[1-5]$/.test(message)) {
      console.log('V89: Valid service number:', message);
      updateData.service_selected = message;
      updateData.service_type = serviceMapping[message];
      console.log('V89: Service mapped:', message, '→', updateData.service_type);

      responseText = `✅ *Perfeito!*

👤 *Qual é o seu nome completo?*

💡 _Exemplo: Maria Silva Santos_
_Usaremos para personalizar seu atendimento_`;
      nextStage = 'collect_name';
    } else {
      console.log('V89: Invalid service selection');
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
    console.log('V89: Processing COLLECT_NAME state');

    const trimmedName = message.trim();

    if (trimmedName.length >= 2 && !/^[0-9]+$/.test(trimmedName)) {
      console.log('V89: Valid name received:', trimmedName);
      updateData.lead_name = trimmedName;

      const whatsappPhone = input.phone_number || input.phone_with_code || '';
      console.log('V89: WhatsApp phone from input:', whatsappPhone);

      responseText = `📱 *Ótimo, ${trimmedName}!*

Vi que você está me enviando mensagens pelo número:
*${formatPhoneDisplay(whatsappPhone)}*

Este é o melhor número para contato?

1️⃣ *Sim, pode usar este*
2️⃣ *Não, vou informar outro*

💡 _Digite 1 ou 2_`;

      nextStage = 'collect_phone_whatsapp_confirmation';

    } else {
      console.log('V89: Invalid name format');
      responseText = `❌ *Nome inválido*

Por favor, informe seu nome completo (mínimo 2 letras).

_Não use apenas números ou caracteres especiais._`;
      nextStage = 'collect_name';
    }
    break;

  // ===== STATE 4: PHONE WHATSAPP CONFIRMATION =====
  case 'collect_phone_whatsapp_confirmation':
    console.log('V89: Processing PHONE_WHATSAPP_CONFIRMATION state');

    if (message === '1') {
      console.log('V89: WhatsApp number confirmed');

      const confirmedPhone = input.phone_number || input.phone_with_code || '';
      updateData.phone_number = confirmedPhone;
      updateData.contact_phone = confirmedPhone;

      responseText = `📧 *Qual é o seu e-mail, ${currentData.lead_name || 'cliente'}?*

💡 _Exemplo: maria.silva@email.com_

Se preferir não informar, digite *pular*
_O e-mail nos ajuda a enviar documentação técnica e propostas_`;
      nextStage = 'collect_email';

    } else if (message === '2') {
      console.log('V89: User wants alternative phone');

      responseText = `📱 *Qual número prefere para contato, ${currentData.lead_name || 'cliente'}?*

Por favor, informe com DDD:

💡 _Exemplo: (62) 98765-4321_
_Usaremos este número para agendarmos sua visita técnica_`;
      nextStage = 'collect_phone_alternative';

    } else {
      console.log('V89: Invalid WhatsApp confirmation option');
      const whatsappPhone = input.phone_number || input.phone_with_code || '';
      responseText = `❌ *Opção inválida*

📱 *Ótimo, ${currentData.lead_name || 'cliente'}!*

Vi que você está me enviando mensagens pelo número:
*${formatPhoneDisplay(whatsappPhone)}*

Este é o melhor número para contato?

1️⃣ *Sim, pode usar este*
2️⃣ *Não, vou informar outro*

💡 _Digite 1 ou 2_`;
      nextStage = 'collect_phone_whatsapp_confirmation';
    }
    break;

  // ===== STATE 5: COLLECT PHONE ALTERNATIVE =====
  case 'collect_phone_alternative':
    console.log('V89: Processing COLLECT_PHONE_ALTERNATIVE state');

    const phoneRegex = /^\(?\d{2}\)?\s?9?\d{4}[-\s]?\d{4}$/;

    if (phoneRegex.test(message)) {
      console.log('V89: Valid alternative phone received');

      const cleanedPhone = message.replace(/\D/g, '');
      updateData.phone_number = cleanedPhone;
      updateData.contact_phone = cleanedPhone;

      responseText = `📧 *Qual é o seu e-mail, ${currentData.lead_name || 'cliente'}?*

💡 _Exemplo: maria.silva@email.com_

Se preferir não informar, digite *pular*
_O e-mail nos ajuda a enviar documentação técnica e propostas_`;
      nextStage = 'collect_email';

    } else {
      console.log('V89: Invalid alternative phone format');
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
    console.log('V89: Processing COLLECT_EMAIL state');

    if (message === 'pular') {
      console.log('V89: User skipped email');
      updateData.email = 'não informado';
      responseText = `📍 *Em qual cidade você está, ${currentData.lead_name || 'cliente'}?*

💡 _Exemplo: Goiânia - GO_
_Precisamos saber para agendar a visita técnica com nossa equipe local_`;
      nextStage = 'collect_city';

    } else {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

      if (emailRegex.test(message)) {
        console.log('V89: Valid email received');
        updateData.email = message;
        responseText = `📍 *Em qual cidade você está, ${currentData.lead_name || 'cliente'}?*

💡 _Exemplo: Goiânia - GO_
_Precisamos saber para agendar a visita técnica com nossa equipe local_`;
        nextStage = 'collect_city';
      } else {
        console.log('V89: Invalid email format');
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
    console.log('V89: Processing COLLECT_CITY state');

    if (message.length >= 2) {
      console.log('V89: Valid city received');
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

    } else {
      console.log('V89: Invalid city (too short)');
      responseText = `❌ *Cidade inválida*

Por favor, informe uma cidade válida (mínimo 2 letras).

_Exemplo: Goiânia, Brasília, Anápolis..._`;
      nextStage = 'collect_city';
    }
    break;

  // ===== V89 STATE 8: CONFIRMATION =====
  case 'confirmation':
    console.log('V89: Processing CONFIRMATION state');

    if (message === '1') {
      const serviceSelected = currentData.service_type || '1';

      if (serviceSelected === 'energia_solar' || serviceSelected === 'projeto_eletrico') {
        console.log('V89: Services 1 or 3 → trigger WF06 next_dates via Switch');

        nextStage = 'trigger_wf06_next_dates';
        responseText = '⏳ *Buscando próximas datas disponíveis...*\n\n_Aguarde um momento..._';

        updateData.awaiting_wf06_next_dates = true;

      } else {
        console.log('V89: Services 2, 4, or 5 → handoff to commercial');
        responseText = `Obrigado pelas informações, ${currentData.lead_name}! 👍\n\n` +
                      `Para o serviço de *${getServiceName(currentData.service_selected || '1')}*, nossa equipe comercial ` +
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

  // ===== V89 STATE 9: INTERMEDIATE STATE - Trigger WF06 Next Dates =====
  case 'trigger_wf06_next_dates':
    console.log('V89: INTERMEDIATE STATE - Triggering WF06 next_dates call');

    nextStage = 'show_available_dates';
    responseText = '';
    break;

  // ===== V89 STATE 10: SHOW_AVAILABLE_DATES - IMPROVED WF06 DATA ACCESS =====
  case 'show_available_dates':
    console.log('V89: Showing available dates (PROACTIVE UX)');
    console.log('V89: DEBUG - Checking all possible locations for WF06 data');
    console.log('V89: DEBUG - input.wf06_next_dates:', JSON.stringify(input.wf06_next_dates || null));
    console.log('V89: DEBUG - currentData.wf06_next_dates:', JSON.stringify(currentData.wf06_next_dates || null));

    // V89 FIX: Check multiple locations for WF06 data
    let nextDatesResponse = null;

    // Priority 1: Direct from Prepare node (most common after V88 fix)
    if (input.wf06_next_dates) {
      nextDatesResponse = input.wf06_next_dates;
      console.log('V89: ✅ Found WF06 data in input.wf06_next_dates');
    }
    // Priority 2: From currentData (after Merge)
    else if (currentData.wf06_next_dates) {
      nextDatesResponse = currentData.wf06_next_dates;
      console.log('V89: ✅ Found WF06 data in currentData.wf06_next_dates');
    }
    // Priority 3: Nested in input.currentData
    else if (input.currentData && input.currentData.wf06_next_dates) {
      nextDatesResponse = input.currentData.wf06_next_dates;
      console.log('V89: ✅ Found WF06 data in input.currentData.wf06_next_dates');
    }
    // No WF06 data found
    else {
      nextDatesResponse = {};
      console.error('V89: ❌ WF06 data NOT found in any location');
      console.error('V89: ❌ input keys:', Object.keys(input));
      console.error('V89: ❌ currentData keys:', Object.keys(currentData));
    }

    if (nextDatesResponse && nextDatesResponse.success && nextDatesResponse.dates && nextDatesResponse.dates.length > 0) {
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
      nextStage = 'process_date_selection';

      console.log('V89: ✅ SUCCESS - Displaying', nextDatesResponse.dates.length, 'dates to user');

    } else {
      console.warn('V89: WF06 failed or no data, falling back to manual date input');
      responseText = `⚠️ *Não conseguimos buscar disponibilidade automaticamente*\n\n` +
                    `Por favor, informe a data desejada (DD/MM/AAAA):\n\n` +
                    `💡 *Lembre-se:*\n` +
                    `• Data futura (não pode ser hoje ou passado)\n` +
                    `• Dia útil (segunda a sexta-feira)\n\n` +
                    `_Digite a data..._`;

      nextStage = 'collect_appointment_date_manual';
    }
    break;

  // ===== V89 STATE 11: PROCESS_DATE_SELECTION =====
  case 'process_date_selection':
    console.log('V89: Processing date selection');

    const dateChoice = message.trim();

    if (/^[1-3]$/.test(dateChoice)) {
      const selectedIndex = parseInt(dateChoice) - 1;
      const suggestions = currentData.date_suggestions || [];

      if (selectedIndex >= 0 && selectedIndex < suggestions.length) {
        const selectedDate = suggestions[selectedIndex];
        console.log('V89: Date selected from suggestions:', selectedDate.date);

        updateData.scheduled_date = selectedDate.date;
        updateData.scheduled_date_display = selectedDate.display;

        console.log('V89: Date selected → trigger WF06 available_slots via Switch');
        nextStage = 'trigger_wf06_available_slots';
        responseText = '⏳ *Buscando horários disponíveis...*\n\n_Aguarde um momento..._';

        updateData.awaiting_wf06_available_slots = true;

      } else {
        responseText = `❌ *Opção inválida*\n\nEscolha 1, 2 ou 3.`;
        nextStage = 'process_date_selection';
      }
    }
    else if (/^\d{2}\/\d{2}\/\d{4}$/.test(dateChoice)) {
      console.log('V89: Custom date entered, validating:', dateChoice);

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
        console.log('V89: Custom date validated successfully');

        updateData.scheduled_date = isoDate;
        updateData.scheduled_date_display = dateChoice;

        console.log('V89: Custom date validated → trigger WF06 available_slots via Switch');
        nextStage = 'trigger_wf06_available_slots';
        responseText = '⏳ *Buscando horários disponíveis...*\n\n_Aguarde um momento..._';

        updateData.awaiting_wf06_available_slots = true;
      }
    }
    else {
      responseText = `❌ *Formato inválido*\n\nEscolha 1-3 ou digite uma data em DD/MM/AAAA`;
      nextStage = 'process_date_selection';
    }
    break;

  // ===== V89 STATE 12: INTERMEDIATE STATE - Trigger WF06 Available Slots =====
  case 'trigger_wf06_available_slots':
    console.log('V89: INTERMEDIATE STATE - Triggering WF06 available_slots call');

    nextStage = 'show_available_slots';
    responseText = '';
    break;

  // ===== V89 STATE 13: SHOW_AVAILABLE_SLOTS - IMPROVED WF06 DATA ACCESS =====
  case 'show_available_slots':
    console.log('V89: Showing available slots (PROACTIVE UX)');
    console.log('V89: DEBUG - Checking all possible locations for WF06 slots data');
    console.log('V89: DEBUG - input.wf06_available_slots:', JSON.stringify(input.wf06_available_slots || null));
    console.log('V89: DEBUG - currentData.wf06_available_slots:', JSON.stringify(currentData.wf06_available_slots || null));

    // V89 FIX: Check multiple locations for WF06 slots data
    let slotsResponse = null;

    // Priority 1: Direct from Prepare node
    if (input.wf06_available_slots) {
      slotsResponse = input.wf06_available_slots;
      console.log('V89: ✅ Found WF06 slots in input.wf06_available_slots');
    }
    // Priority 2: From currentData
    else if (currentData.wf06_available_slots) {
      slotsResponse = currentData.wf06_available_slots;
      console.log('V89: ✅ Found WF06 slots in currentData.wf06_available_slots');
    }
    // Priority 3: Nested in input.currentData
    else if (input.currentData && input.currentData.wf06_available_slots) {
      slotsResponse = input.currentData.wf06_available_slots;
      console.log('V89: ✅ Found WF06 slots in input.currentData.wf06_available_slots');
    }
    // No WF06 slots data found
    else {
      slotsResponse = {};
      console.error('V89: ❌ WF06 slots NOT found in any location');
    }

    if (slotsResponse && slotsResponse.success && slotsResponse.available_slots && slotsResponse.available_slots.length > 0) {
      let slotOptions = '';
      slotsResponse.available_slots.forEach((slot, index) => {
        const number = index + 1;
        slotOptions += `${number}️⃣ *${slot.formatted}* ✅\n`;
      });

      responseText = `🕐 *Horários Disponíveis - ${currentData.scheduled_date_display}*\n\n` +
                    slotOptions + `\n` +
                    `💡 *Escolha um horário (1-${slotsResponse.total_available})*\n` +
                    `_Ou digite um horário específico em HH:MM_\n\n` +
                    `⏱️ *Duração*: 2 horas\n` +
                    `📍 *Cidade*: ${currentData.city}\n` +
                    `${serviceDisplay[currentData.service_type]?.emoji || '🔧'} *Serviço*: ${getServiceName(currentData.service_selected || '1')}`;

      updateData.available_slots = slotsResponse.available_slots;
      nextStage = 'process_slot_selection';

      console.log('V89: ✅ SUCCESS - Displaying', slotsResponse.available_slots.length, 'slots to user');

    } else if (slotsResponse && slotsResponse.success && slotsResponse.total_available === 0) {
      console.warn('V89: No slots available for selected date');
      responseText = `❌ *Esta data está totalmente ocupada*\n\n` +
                    `Vamos escolher outra data com mais disponibilidade.\n\n` +
                    `_Voltando para seleção de datas..._`;

      nextStage = 'show_available_dates';
    } else {
      console.error('V89: WF06 available_slots failed, falling back to manual');
      responseText = `⚠️ *Não conseguimos buscar horários disponíveis*\n\n` +
                    `Por favor, informe o horário desejado (HH:MM):\n\n` +
                    `⏰ *Horários de atendimento:*\n` +
                    `• Segunda a Sexta: 08:00 às 18:00\n\n` +
                    `_Digite o horário..._`;

      nextStage = 'collect_appointment_time_manual';
    }
    break;

  // ===== V89 STATE 14: PROCESS_SLOT_SELECTION =====
  case 'process_slot_selection':
    console.log('V89: Processing slot selection');

    const slotChoice = message.trim();
    const availableSlots = currentData.available_slots || [];

    if (/^\d+$/.test(slotChoice)) {
      const selectedIndex = parseInt(slotChoice) - 1;

      if (selectedIndex >= 0 && selectedIndex < availableSlots.length) {
        const selectedSlot = availableSlots[selectedIndex];
        console.log('V89: Slot selected from suggestions:', selectedSlot);

        updateData.scheduled_time_start = selectedSlot.start_time;
        updateData.scheduled_time_end = selectedSlot.end_time;

        const confirmationMessage = `✅ *Agendamento Confirmado!*\n\n` +
                                  `📅 *Data:* ${currentData.scheduled_date_display}\n` +
                                  `🕐 *Horário:* ${selectedSlot.formatted}\n` +
                                  `📍 *Cidade*: ${currentData.city}\n` +
                                  `${serviceDisplay[currentData.service_type]?.emoji || '🔧'} *Serviço*: ${getServiceName(currentData.service_selected || '1')}\n\n` +
                                  `_Processando agendamento..._`;

        responseText = confirmationMessage;
        nextStage = 'appointment_final_confirmation';

      } else {
        responseText = `❌ *Opção inválida*\n\nEscolha um número de 1 a ${availableSlots.length}`;
        nextStage = 'process_slot_selection';
      }
    }
    else if (/^\d{2}:\d{2}$/.test(slotChoice)) {
      console.log('V89: Custom time entered, validating:', slotChoice);

      const [hours, minutes] = slotChoice.split(':').map(Number);

      if (hours < 8 || hours >= 18 || minutes < 0 || minutes >= 60) {
        responseText = `❌ *Horário inválido*\n\nNosso atendimento é de Segunda a Sexta, 08:00 às 18:00.\n\nPor favor, escolha um horário dentro deste período.`;
        nextStage = 'process_slot_selection';
      } else {
        console.log('V89: Custom time validated successfully');

        updateData.scheduled_time_start = slotChoice;
        const endHours = hours + 2;
        updateData.scheduled_time_end = `${String(endHours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`;

        responseText = `✅ *Horário registrado*\n\n` +
                      `📅 *Data:* ${currentData.scheduled_date_display}\n` +
                      `🕐 *Horário:* ${slotChoice} às ${updateData.scheduled_time_end}\n\n` +
                      `_Processando agendamento..._`;

        nextStage = 'appointment_final_confirmation';
      }
    }
    else {
      responseText = `❌ *Formato inválido*\n\nEscolha um número (1-${availableSlots.length}) ou digite um horário em HH:MM`;
      nextStage = 'process_slot_selection';
    }
    break;

  // ===== FALLBACK STATES =====
  case 'collect_appointment_date_manual':
  case 'collect_appointment_time_manual':
    console.log('V89: FALLBACK - Manual input (placeholder)');
    responseText = `⚠️ *Sistema temporariamente indisponível*\n\nPor favor, entre em contato diretamente:\n📱 (62) 3092-2900`;
    nextStage = 'handoff_comercial';
    break;

  // ===== STATE 15: APPOINTMENT_FINAL_CONFIRMATION =====
  case 'appointment_final_confirmation':
  case 'scheduling_redirect':
    console.log('V89: APPOINTMENT FINAL CONFIRMATION');

    responseText = `✅ *Agendamento realizado com sucesso!*\n\n` +
                  `📅 *Data:* ${currentData.scheduled_date_display}\n` +
                  `🕐 *Horário:* ${currentData.scheduled_time_start} às ${currentData.scheduled_time_end}\n\n` +
                  `📧 Você receberá um email de confirmação em breve.\n\n` +
                  `Até lá! ✨`;

    nextStage = 'completed';
    updateData.appointment_completed = true;
    break;

  // ===== REMAINING STATES =====
  case 'handoff_comercial':
    console.log('V89: Handoff to commercial team');
    responseText = responseText || 'Obrigado! Nossa equipe entrará em contato em breve.';
    nextStage = 'completed';
    break;

  case 'correction_choice':
    console.log('V89: Correction flow (placeholder)');
    responseText = `⚠️ *Sistema de correção temporariamente indisponível*\n\nPor favor, entre em contato:\n📱 (62) 3092-2900`;
    nextStage = 'handoff_comercial';
    break;

  case 'completed':
    console.log('V89: Conversation completed');
    responseText = 'Conversa finalizada. Digite *menu* para reiniciar.';
    nextStage = 'completed';
    break;

  default:
    console.error('V89: Unknown state:', currentStage);
    responseText = `⚠️ *Estado desconhecido*\n\nPor favor, reinicie a conversa digitando: *menu*`;
    nextStage = 'greeting';
}

// ===================================================
// RETURN RESULT (V74 STRUCTURE)
// ===================================================

console.log('V89: Response text:', responseText);
console.log('V89: Next stage:', nextStage);
console.log('V89: Update data:', JSON.stringify(updateData));
console.log('=== V89 STATE MACHINE END ===');

return {
  response_text: responseText,
  next_stage: nextStage,
  update_data: updateData,

  // Pass phone data
  phone_number: input.phone_number || input.phone_with_code || '',
  phone_with_code: input.phone_with_code || input.phone_number || '',
  phone_without_code: input.phone_without_code || '',

  // Pass conversation data
  conversation_id: input.conversation_id || null,
  message: input.message || '',
  message_id: input.message_id || '',
  message_type: input.message_type || 'text',

  // Pass collected_data
  collected_data: {
    ...currentData,
    ...updateData,
    lead_name: updateData.lead_name || currentData.lead_name || '',
    contact_name: updateData.contact_name || currentData.contact_name || updateData.lead_name || currentData.lead_name || ''
  },

  // V89 Metadata
  v89_wf06_data_access_fixed: true,
  timestamp: new Date().toISOString()
};
