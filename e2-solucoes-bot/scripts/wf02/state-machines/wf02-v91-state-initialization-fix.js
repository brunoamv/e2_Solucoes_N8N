// ===================================================
// V91 STATE MACHINE - CRITICAL FIX: State Initialization
// ===================================================
// ROOT CAUSE FIX (V90 Bug):
// - State Machine executes TWICE in workflow
// - First: trigger_wf06_next_dates → next_stage: 'show_available_dates' ✅
// - Second: input.current_stage UNDEFINED → defaults to 'greeting' ❌
//
// V91 SOLUTION:
// 1. Enhanced currentStage resolution with fallback chain
// 2. Explicit validation of state consistency
// 3. WARNING logs for undefined state scenarios
// 4. Defensive programming for WF06 return path
//
// CRITICAL STATES FOR WF06 INTEGRATION:
// State 8: confirmation → trigger_wf06_next_dates
// State 9: trigger_wf06_next_dates → show_available_dates (MUST RETURN HERE)
// State 10: show_available_dates → display 3 dates
// State 11: process_date_selection → trigger_wf06_available_slots
// State 12: trigger_wf06_available_slots → show_available_slots
// State 13: show_available_slots → display N slots
//
// Date: 2026-04-20
// Version: V91 CRITICAL FIX
// ===================================================

// ===================================================
// HELPER FUNCTIONS
// ===================================================

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

// ===================================================
// CONFIGURATION
// ===================================================

const SERVICE_MAPPING = {
  '1': 'energia_solar',
  '2': 'subestacao',
  '3': 'projeto_eletrico',
  '4': 'armazenamento_energia',
  '5': 'analise_laudo'
};

const SERVICE_DISPLAY = {
  'energia_solar': { emoji: '☀️', name: 'Energia Solar' },
  'subestacao': { emoji: '⚡', name: 'Subestações' },
  'projeto_eletrico': { emoji: '📐', name: 'Projetos Elétricos' },
  'armazenamento_energia': { emoji: '🔋', name: 'BESS (Armazenamento de Energia)' },
  'analise_laudo': { emoji: '📊', name: 'Análise e Laudos' }
};

// ===================================================
// MAIN EXECUTION
// ===================================================

const input = $input.all()[0].json;
const message = (input.message || '').toString().trim().toLowerCase();
const currentData = input.currentData || {};

// ===================================================
// V91 CRITICAL FIX: Enhanced State Resolution
// ===================================================
// Priority chain for currentStage resolution:
// 1. input.current_stage (direct from previous node)
// 2. input.next_stage (from previous State Machine execution)
// 3. currentData.current_stage (from database via Get Conversation Details)
// 4. currentData.next_stage (database backup)
// 5. Default: 'greeting'
//
// CRITICAL: WF06 return path MUST preserve state from previous execution
// ===================================================

let currentStage = input.current_stage ||
                   input.next_stage ||
                   currentData.current_stage ||
                   currentData.next_stage ||
                   'greeting';

// V91: Enhanced validation logging
console.log('=== V91 STATE MACHINE START ===');
console.log('V91: ========================================');
console.log('V91: STATE INITIALIZATION');
console.log('V91: ========================================');
console.log('V91: input.current_stage:', input.current_stage);
console.log('V91: input.next_stage:', input.next_stage);
console.log('V91: currentData.current_stage:', currentData.current_stage);
console.log('V91: currentData.next_stage:', currentData.next_stage);
console.log('V91: ========================================');
console.log('V91: RESOLVED currentStage:', currentStage);
console.log('V91: ========================================');

// V91: WARNING if state is undefined at ANY level
if (!input.current_stage && !input.next_stage && !currentData.current_stage && !currentData.next_stage) {
  console.warn('V91: ⚠️⚠️⚠️ WARNING: ALL stage sources are undefined!');
  console.warn('V91: ⚠️⚠️⚠️ This may indicate a workflow configuration issue');
  console.warn('V91: ⚠️⚠️⚠️ Defaulting to greeting, but review node connections');
}

console.log('V91: User message:', message);
console.log('V91: CurrentData keys:', Object.keys(currentData));

// V91: Enhanced WF06 data logging
console.log('V91: ========================================');
console.log('V91: WF06 DATA AVAILABILITY');
console.log('V91: ========================================');
console.log('V91: input.wf06_next_dates:', !!input.wf06_next_dates);
console.log('V91: currentData.wf06_next_dates:', !!currentData.wf06_next_dates);
console.log('V91: input.wf06_available_slots:', !!input.wf06_available_slots);
console.log('V91: currentData.wf06_available_slots:', !!currentData.wf06_available_slots);
console.log('V91: ========================================');

// Initialize response variables
let responseText = '';
let nextStage = currentStage;  // V91: Maintain current stage by default
let updateData = {};

// ===================================================
// STATE MACHINE LOGIC
// ===================================================

switch (currentStage) {

  // ===== STATE 1: GREETING =====
  case 'greeting':
  case 'menu':
    console.log('V91: ■ STATE 1 - GREETING');
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
    console.log('V91: ■ STATE 2 - SERVICE SELECTION');

    if (/^[1-5]$/.test(message)) {
      updateData.service_selected = message;
      updateData.service_type = SERVICE_MAPPING[message];
      console.log('V91: ✅ Service selected:', message, '→', updateData.service_type);

      responseText = `✅ *Perfeito!*

👤 *Qual é o seu nome completo?*

💡 _Exemplo: Maria Silva Santos_
_Usaremos para personalizar seu atendimento_`;
      nextStage = 'collect_name';
    } else {
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
    console.log('V91: ■ STATE 3 - COLLECT NAME');

    const trimmedName = message.trim();

    if (trimmedName.length >= 2 && !/^[0-9]+$/.test(trimmedName)) {
      updateData.lead_name = trimmedName;

      const whatsappPhone = input.phone_number || input.phone_with_code || '';
      responseText = `📱 *Ótimo, ${trimmedName}!*

Vi que você está me enviando mensagens pelo número:
*${formatPhoneDisplay(whatsappPhone)}*

Este é o melhor número para contato?

1️⃣ *Sim, pode usar este*
2️⃣ *Não, vou informar outro*

💡 _Digite 1 ou 2_`;
      nextStage = 'collect_phone_whatsapp_confirmation';

    } else {
      responseText = `❌ *Nome inválido*

Por favor, informe seu nome completo (mínimo 2 letras).

_Não use apenas números ou caracteres especiais._`;
      nextStage = 'collect_name';
    }
    break;

  // ===== STATE 4: PHONE WHATSAPP CONFIRMATION =====
  case 'collect_phone_whatsapp_confirmation':
    console.log('V91: ■ STATE 4 - PHONE WHATSAPP CONFIRMATION');

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

💡 _Exemplo: (62) 98765-4321_
_Usaremos este número para agendarmos sua visita técnica_`;
      nextStage = 'collect_phone_alternative';

    } else {
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
    console.log('V91: ■ STATE 5 - COLLECT PHONE ALTERNATIVE');

    const phoneRegex = /^\(?\d{2}\)?\s?9?\d{4}[-\s]?\d{4}$/;

    if (phoneRegex.test(message)) {
      const cleanedPhone = message.replace(/\D/g, '');
      updateData.phone_number = cleanedPhone;
      updateData.contact_phone = cleanedPhone;

      responseText = `📧 *Qual é o seu e-mail, ${currentData.lead_name || 'cliente'}?*

💡 _Exemplo: maria.silva@email.com_

Se preferir não informar, digite *pular*
_O e-mail nos ajuda a enviar documentação técnica e propostas_`;
      nextStage = 'collect_email';

    } else {
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
    console.log('V91: ■ STATE 6 - COLLECT EMAIL');

    if (message === 'pular') {
      updateData.email = 'não informado';
      responseText = `📍 *Em qual cidade você está, ${currentData.lead_name || 'cliente'}?*

💡 _Exemplo: Goiânia - GO_
_Precisamos saber para agendar a visita técnica com nossa equipe local_`;
      nextStage = 'collect_city';

    } else {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

      if (emailRegex.test(message)) {
        updateData.email = message;
        responseText = `📍 *Em qual cidade você está, ${currentData.lead_name || 'cliente'}?*

💡 _Exemplo: Goiânia - GO_
_Precisamos saber para agendar a visita técnica com nossa equipe local_`;
        nextStage = 'collect_city';
      } else {
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
    console.log('V91: ■ STATE 7 - COLLECT CITY');

    if (message.length >= 2) {
      updateData.city = message;

      const leadName = currentData.lead_name || updateData.lead_name || 'não informado';
      const phoneNumber = currentData.contact_phone || currentData.phone_number || updateData.phone_number || updateData.contact_phone || 'não informado';
      const email = currentData.email || updateData.email || 'não informado';
      const city = updateData.city || 'não informado';
      const serviceType = currentData.service_type || 'não informado';
      const serviceInfo = SERVICE_DISPLAY[serviceType] || { emoji: '❓', name: 'Não informado' };

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

Por favor, informe uma cidade válida (mínimo 2 letras).

_Exemplo: Goiânia, Brasília, Anápolis..._`;
      nextStage = 'collect_city';
    }
    break;

  // ===== STATE 8: CONFIRMATION =====
  case 'confirmation':
    console.log('V91: ■ STATE 8 - CONFIRMATION');

    if (message === '1') {
      const serviceSelected = currentData.service_type || '1';

      if (serviceSelected === 'energia_solar' || serviceSelected === 'projeto_eletrico') {
        console.log('V91: ✅ Services 1 or 3 → trigger WF06 next_dates');

        nextStage = 'trigger_wf06_next_dates';
        responseText = '⏳ *Buscando próximas datas disponíveis...*\n\n_Aguarde um momento..._';
        updateData.awaiting_wf06_next_dates = true;

      } else {
        console.log('V91: ✅ Services 2, 4, or 5 → handoff to commercial');
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

  // ===== STATE 9: INTERMEDIATE - TRIGGER WF06 NEXT DATES =====
  case 'trigger_wf06_next_dates':
    console.log('V91: ■ STATE 9 - INTERMEDIATE - Triggering WF06 next_dates');
    console.log('V91: ⚠️ CRITICAL: This is pass-through state, WF06 HTTP Request executes externally');
    console.log('V91: ⚠️ CRITICAL: MUST return to show_available_dates after WF06 completes');

    nextStage = 'show_available_dates';
    responseText = '';  // Empty for intermediate state

    // V91: Explicit flag for debugging
    updateData.v91_expecting_wf06_return = true;
    break;

  // ===== STATE 10: SHOW AVAILABLE DATES =====
  case 'show_available_dates':
    console.log('V91: ■ STATE 10 - SHOW AVAILABLE DATES');
    console.log('V91: ========================================');
    console.log('V91: WF06 NEXT_DATES DATA SEARCH');
    console.log('V91: ========================================');

    // V91: Multi-location WF06 data access with enhanced logging
    let nextDatesResponse = null;
    let dataSource = 'NONE';

    if (input.wf06_next_dates) {
      nextDatesResponse = input.wf06_next_dates;
      dataSource = 'input.wf06_next_dates';
    }
    else if (currentData.wf06_next_dates) {
      nextDatesResponse = currentData.wf06_next_dates;
      dataSource = 'currentData.wf06_next_dates';
    }
    else if (input.currentData && input.currentData.wf06_next_dates) {
      nextDatesResponse = input.currentData.wf06_next_dates;
      dataSource = 'input.currentData.wf06_next_dates';
    }
    else {
      nextDatesResponse = {};
      dataSource = 'NOT_FOUND';
    }

    console.log('V91: WF06 data source:', dataSource);
    console.log('V91: WF06 success:', !!nextDatesResponse.success);
    console.log('V91: WF06 dates count:', nextDatesResponse.dates?.length || 0);
    console.log('V91: ========================================');

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
      console.log('V91: ✅ SUCCESS - Displaying', nextDatesResponse.dates.length, 'dates to user');

    } else {
      console.warn('V91: ❌ WF06 failed or no data, fallback to manual');
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
    console.log('V91: ■ STATE 11 - PROCESS DATE SELECTION');

    const dateChoice = message.trim();

    if (/^[1-3]$/.test(dateChoice)) {
      const selectedIndex = parseInt(dateChoice) - 1;
      const suggestions = currentData.date_suggestions || [];

      if (selectedIndex >= 0 && selectedIndex < suggestions.length) {
        const selectedDate = suggestions[selectedIndex];
        console.log('V91: ✅ Date selected:', selectedDate.date);

        updateData.scheduled_date = selectedDate.date;
        updateData.scheduled_date_display = selectedDate.display;

        nextStage = 'trigger_wf06_available_slots';
        responseText = '⏳ *Buscando horários disponíveis...*\n\n_Aguarde um momento..._';
        updateData.awaiting_wf06_available_slots = true;

      } else {
        responseText = `❌ *Opção inválida*\n\nEscolha 1, 2 ou 3.`;
        nextStage = 'process_date_selection';
      }
    }
    else if (/^\d{2}\/\d{2}\/\d{4}$/.test(dateChoice)) {
      console.log('V91: Custom date entered:', dateChoice);

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
        updateData.scheduled_date = isoDate;
        updateData.scheduled_date_display = dateChoice;

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

  // ===== STATE 12: INTERMEDIATE - TRIGGER WF06 AVAILABLE SLOTS =====
  case 'trigger_wf06_available_slots':
    console.log('V91: ■ STATE 12 - INTERMEDIATE - Triggering WF06 available_slots');
    console.log('V91: ⚠️ CRITICAL: MUST return to show_available_slots after WF06 completes');

    nextStage = 'show_available_slots';
    responseText = '';
    updateData.v91_expecting_wf06_slots_return = true;
    break;

  // ===== STATE 13: SHOW AVAILABLE SLOTS =====
  case 'show_available_slots':
    console.log('V91: ■ STATE 13 - SHOW AVAILABLE SLOTS');

    // V91: Multi-location slots access with enhanced logging
    let slotsResponse = null;
    let slotsDataSource = 'NONE';

    if (input.wf06_available_slots) {
      slotsResponse = input.wf06_available_slots;
      slotsDataSource = 'input.wf06_available_slots';
    }
    else if (currentData.wf06_available_slots) {
      slotsResponse = currentData.wf06_available_slots;
      slotsDataSource = 'currentData.wf06_available_slots';
    }
    else if (input.currentData && input.currentData.wf06_available_slots) {
      slotsResponse = input.currentData.wf06_available_slots;
      slotsDataSource = 'input.currentData.wf06_available_slots';
    }
    else {
      slotsResponse = {};
      slotsDataSource = 'NOT_FOUND';
    }

    console.log('V91: WF06 slots data source:', slotsDataSource);
    console.log('V91: WF06 slots success:', !!slotsResponse.success);
    console.log('V91: WF06 slots count:', slotsResponse.available_slots?.length || 0);

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
                    `${SERVICE_DISPLAY[currentData.service_type]?.emoji || '🔧'} *Serviço*: ${getServiceName(currentData.service_selected || '1')}`;

      updateData.available_slots = slotsResponse.available_slots;
      nextStage = 'process_slot_selection';
      console.log('V91: ✅ SUCCESS - Displaying', slotsResponse.available_slots.length, 'slots');

    } else if (slotsResponse && slotsResponse.success && slotsResponse.total_available === 0) {
      console.warn('V91: ⚠️ No slots available');
      responseText = `❌ *Esta data está totalmente ocupada*\n\n` +
                    `Vamos escolher outra data com mais disponibilidade.\n\n` +
                    `_Voltando para seleção de datas..._`;
      nextStage = 'show_available_dates';
    } else {
      console.error('V91: ❌ WF06 slots failed, fallback to manual');
      responseText = `⚠️ *Não conseguimos buscar horários disponíveis*\n\n` +
                    `Por favor, informe o horário desejado (HH:MM):\n\n` +
                    `⏰ *Horários de atendimento:*\n` +
                    `• Segunda a Sexta: 08:00 às 18:00\n\n` +
                    `_Digite o horário..._`;
      nextStage = 'collect_appointment_time_manual';
    }
    break;

  // ===== STATE 14: PROCESS SLOT SELECTION =====
  case 'process_slot_selection':
    console.log('V91: ■ STATE 14 - PROCESS SLOT SELECTION');

    const slotChoice = message.trim();
    const availableSlots = currentData.available_slots || [];

    if (/^\d+$/.test(slotChoice)) {
      const selectedIndex = parseInt(slotChoice) - 1;

      if (selectedIndex >= 0 && selectedIndex < availableSlots.length) {
        const selectedSlot = availableSlots[selectedIndex];

        updateData.scheduled_time_start = selectedSlot.start_time;
        updateData.scheduled_time_end = selectedSlot.end_time;

        responseText = `✅ *Agendamento Confirmado!*\n\n` +
                      `📅 *Data:* ${currentData.scheduled_date_display}\n` +
                      `🕐 *Horário:* ${selectedSlot.formatted}\n` +
                      `📍 *Cidade*: ${currentData.city}\n` +
                      `${SERVICE_DISPLAY[currentData.service_type]?.emoji || '🔧'} *Serviço*: ${getServiceName(currentData.service_selected || '1')}\n\n` +
                      `_Processando agendamento..._`;

        nextStage = 'appointment_final_confirmation';

      } else {
        responseText = `❌ *Opção inválida*\n\nEscolha um número de 1 a ${availableSlots.length}`;
        nextStage = 'process_slot_selection';
      }
    }
    else if (/^\d{2}:\d{2}$/.test(slotChoice)) {
      const [hours, minutes] = slotChoice.split(':').map(Number);

      if (hours < 8 || hours >= 18 || minutes < 0 || minutes >= 60) {
        responseText = `❌ *Horário inválido*\n\nNosso atendimento é de Segunda a Sexta, 08:00 às 18:00.\n\nPor favor, escolha um horário dentro deste período.`;
        nextStage = 'process_slot_selection';
      } else {
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
    console.log('V91: ■ FALLBACK - Manual input');
    responseText = `⚠️ *Sistema temporariamente indisponível*\n\nPor favor, entre em contato diretamente:\n📱 (62) 3092-2900`;
    nextStage = 'handoff_comercial';
    break;

  // ===== STATE 15: APPOINTMENT FINAL CONFIRMATION =====
  case 'appointment_final_confirmation':
  case 'scheduling_redirect':
    console.log('V91: ■ STATE 15 - APPOINTMENT FINAL CONFIRMATION');

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
    console.log('V91: ■ Handoff to commercial team');
    responseText = responseText || 'Obrigado! Nossa equipe entrará em contato em breve.';
    nextStage = 'completed';
    break;

  case 'correction_choice':
    console.log('V91: ■ Correction flow');
    responseText = `⚠️ *Sistema de correção temporariamente indisponível*\n\nPor favor, entre em contato:\n📱 (62) 3092-2900`;
    nextStage = 'handoff_comercial';
    break;

  case 'completed':
    console.log('V91: ■ Conversation completed');
    responseText = 'Conversa finalizada. Digite *menu* para reiniciar.';
    nextStage = 'completed';
    break;

  default:
    console.error('V91: ■ ❌ UNKNOWN STATE:', currentStage);
    console.error('V91: ❌ This should NEVER happen - investigate workflow configuration!');
    console.error('V91: ❌ Falling back to greeting');
    responseText = `⚠️ *Estado desconhecido*\n\nPor favor, reinicie a conversa digitando: *menu*`;
    nextStage = 'greeting';
}

// ===================================================
// RETURN RESULT
// ===================================================

console.log('V91: ========================================');
console.log('V91: STATE MACHINE RESULT');
console.log('V91: ========================================');
console.log('V91: Current stage:', currentStage);
console.log('V91: Next stage:', nextStage);
console.log('V91: Response text length:', responseText.length);
console.log('V91: Update data keys:', Object.keys(updateData));
console.log('V91: ========================================');
console.log('=== V91 STATE MACHINE END ===');

return {
  response_text: responseText,
  next_stage: nextStage,
  update_data: updateData,

  // V91: Explicit current_stage for next execution
  current_stage: nextStage,

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

  // V91 Metadata
  v91_state_initialization_fix: true,
  v91_enhanced_logging: true,
  v91_wf06_return_path_defensive: true,
  timestamp: new Date().toISOString()
};
