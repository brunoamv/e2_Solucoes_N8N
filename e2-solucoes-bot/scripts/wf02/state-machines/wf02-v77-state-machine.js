// ===================================================
// V77 STATE MACHINE - LOOP FIX IMPLEMENTATION
// ===================================================
// Changes from V76:
// - ADDED: State trigger_wf06_next_dates (intermediate routing state)
// - ADDED: State trigger_wf06_available_slots (intermediate routing state)
// - MODIFIED: State 8 confirmation → triggers WF06 via Switch Node
// - MODIFIED: State 10 process_date_selection → triggers WF06 slots via Switch
// - FIX: Infinite loop resolved with conditional Switch routing
// - STATES: 14 (was 12 in V76) - Added 2 intermediate states
// Date: 2026-04-13
// Version: V77 Loop Fix
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

console.log('=== V77 STATE MACHINE START ===');
console.log('V77: Current stage:', currentStage);
console.log('V77: User message:', message);
console.log('V77: Current data:', JSON.stringify(currentData));

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
// V77 STATE MACHINE LOGIC
// ===================================================

switch (currentStage) {

  // ===== STATES 1-7: UNCHANGED from V76 =====
  // [Keep all V76 logic for states 1-7]
  // - greeting
  // - service_selection
  // - collect_name
  // - collect_phone_whatsapp_confirmation
  // - collect_phone_alternative
  // - collect_email
  // - collect_city

  // ===== V77 STATE 8-MODIFIED: CONFIRMATION - Modified to trigger WF06 via Switch =====
  case 'confirmation':
    console.log('V77: Processing CONFIRMATION state');

    if (message === '1') {
      const serviceSelected = currentData.service_type || '1';

      if (serviceSelected === '1' || serviceSelected === '3') {
        // V77 FIX: Set intermediate stage to trigger WF06 call via Switch Node
        console.log('V77 FIX: Services 1 or 3 → trigger WF06 next_dates call');

        nextStage = 'trigger_wf06_next_dates';  // ← CRITICAL CHANGE
        responseText = '⏳ *Buscando próximas datas disponíveis...*\n\n_Aguarde um momento..._';

        // Set debugging flag
        updateData.awaiting_wf06_next_dates = true;

      } else {
        // Services 2, 4, 5 → handoff to commercial
        console.log('V77: Services 2, 4, or 5 → handoff to commercial');
        responseText = `Obrigado pelas informações, ${currentData.lead_name}! 👍\n\n` +
                      `Para o serviço de *${getServiceName(serviceSelected)}*, nossa equipe comercial ` +
                      `entrará em contato em breve para alinhar os detalhes.\n\n` +
                      `📞 Caso prefira falar agora: (62) 3092-2900\n\n` +
                      `Tenha um ótimo dia! ✨`;
        nextStage = 'handoff_comercial';
      }
    }
    else if (message === '2') {
      // Correction flow
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
      responseText = `❌ *Opção inválida*\n\nDigite *1* para confirmar ou *2* para corrigir.`;
      nextStage = 'confirmation';
    }
    break;

  // ===== V77 STATE 9-NEW: INTERMEDIATE STATE - Trigger WF06 Next Dates =====
  case 'trigger_wf06_next_dates':
    console.log('V77: INTERMEDIATE STATE - Triggering WF06 next_dates call');

    // This state exists ONLY to trigger the Switch Node in workflow
    // Workflow detects next_stage === 'trigger_wf06_next_dates' and routes to HTTP Request 1
    // After HTTP Request returns, workflow passes data back to State Machine
    // Then State Machine advances to 'show_available_dates' to process WF06 response

    console.log('V77: Waiting for WF06 response...');

    // Set next stage to process WF06 response
    nextStage = 'show_available_dates';  // ← State Machine will be called again after HTTP Request
    responseText = '';  // ← No message here, HTTP Request sends "Aguarde..."

    break;

  // ===== V77 STATE 10: SHOW_AVAILABLE_DATES - Process WF06 response (UNCHANGED from V76) =====
  case 'show_available_dates':
    console.log('V77: Showing available dates (PROACTIVE UX)');

    // This state is entered from trigger_wf06_next_dates after HTTP Request completes
    // HTTP Request node should have already called WF06 and stored response
    const nextDatesResponse = input.wf06_next_dates || {};

    if (nextDatesResponse.success && nextDatesResponse.dates && nextDatesResponse.dates.length > 0) {
      // Build proactive date selection message
      let dateOptions = '';
      nextDatesResponse.dates.forEach((dateObj, index) => {
        const number = index + 1;
        const qualityEmoji = dateObj.quality === 'high' ? '✨' :
                            dateObj.quality === 'medium' ? '📅' : '⚠️';
        dateOptions += `${number}️⃣ *${dateObj.display}*\n   🕐 ${dateObj.total_slots} horários livres ${qualityEmoji}\n\n`;
      });

      responseText = `📅 *Agendar Visita Técnica - ${getServiceName(currentData.service_type)}*\n\n` +
                    `📆 *Próximas datas com horários disponíveis:*\n\n` +
                    dateOptions +
                    `💡 *Escolha uma opção (1-3)*\n` +
                    `_Ou digite uma data específica em DD/MM/AAAA_\n\n` +
                    `⏱️ *Duração*: 2 horas\n` +
                    `📍 *Cidade*: ${currentData.city}`;

      // Store date suggestions for next state
      updateData.date_suggestions = nextDatesResponse.dates;
      nextStage = 'process_date_selection';

    } else {
      // WF06 failed or no availability - fallback to manual input
      console.warn('V77: WF06 failed, falling back to manual date input');
      responseText = `⚠️ *Não conseguimos buscar disponibilidade automaticamente*\n\n` +
                    `Por favor, informe a data desejada (DD/MM/AAAA):\n\n` +
                    `💡 *Lembre-se:*\n` +
                    `• Data futura (não pode ser hoje ou passado)\n` +
                    `• Dia útil (segunda a sexta-feira)\n\n` +
                    `_Digite a data..._`;

      nextStage = 'collect_appointment_date_manual'; // Fallback to V76 logic
    }
    break;

  // ===== V77 STATE 11-MODIFIED: PROCESS_DATE_SELECTION - Modified to trigger WF06 slots via Switch =====
  case 'process_date_selection':
    console.log('V77: Processing date selection');

    const dateChoice = message.trim();

    // Case 1: User selected from suggestions (1-3)
    if (/^[1-3]$/.test(dateChoice)) {
      const selectedIndex = parseInt(dateChoice) - 1;
      const suggestions = currentData.date_suggestions || [];

      if (selectedIndex >= 0 && selectedIndex < suggestions.length) {
        const selectedDate = suggestions[selectedIndex];
        console.log('V77: Date selected from suggestions:', selectedDate.date);

        // Store selected date
        updateData.scheduled_date = selectedDate.date;           // YYYY-MM-DD (for WF06 API)
        updateData.scheduled_date_display = selectedDate.display; // "Quarta (08/04)" (for messages)

        // V77 FIX: Set intermediate stage to trigger WF06 available_slots call
        console.log('V77 FIX: Date selected → trigger WF06 available_slots call');
        nextStage = 'trigger_wf06_available_slots';  // ← CRITICAL CHANGE
        responseText = '⏳ *Buscando horários disponíveis...*\n\n_Aguarde um momento..._';

        // Set debugging flag
        updateData.awaiting_wf06_available_slots = true;

      } else {
        responseText = `❌ *Opção inválida*\n\nEscolha 1, 2 ou 3.`;
        nextStage = 'process_date_selection';
      }
    }

    // Case 2: User entered custom date (DD/MM/AAAA) - FALLBACK
    else if (/^\d{2}\/\d{2}\/\d{4}$/.test(dateChoice)) {
      console.log('V77: Custom date entered, validating:', dateChoice);

      // Convert DD/MM/AAAA → YYYY-MM-DD
      const [day, month, year] = dateChoice.split('/');
      const isoDate = `${year}-${month}-${day}`;
      const dateObj = new Date(isoDate);

      // Validate date
      const today = new Date();
      today.setHours(0, 0, 0, 0);

      const dayOfWeek = dateObj.getDay();
      const isWeekend = (dayOfWeek === 0 || dayOfWeek === 6); // Sunday or Saturday
      const isPast = dateObj < today;

      if (isPast) {
        responseText = `❌ *Data inválida*\n\nA data deve ser no futuro (não pode ser hoje ou passado).\n\nPor favor, escolha uma das opções ou digite outra data.`;
        nextStage = 'process_date_selection';
      }
      else if (isWeekend) {
        responseText = `❌ *Data inválida*\n\nNão atendemos aos finais de semana.\n\nPor favor, escolha uma data de segunda a sexta.`;
        nextStage = 'process_date_selection';
      }
      else {
        console.log('V77: Custom date validated successfully');

        // Store date
        updateData.scheduled_date = isoDate;
        updateData.scheduled_date_display = dateChoice;

        // V77 FIX: Trigger WF06 available_slots for custom date
        console.log('V77 FIX: Custom date validated → trigger WF06 available_slots');
        nextStage = 'trigger_wf06_available_slots';  // ← CRITICAL CHANGE
        responseText = '⏳ *Buscando horários disponíveis...*\n\n_Aguarde um momento..._';

        updateData.awaiting_wf06_available_slots = true;
      }
    }

    // Case 3: Invalid format
    else {
      responseText = `❌ *Formato inválido*\n\nEscolha 1-3 ou digite uma data em DD/MM/AAAA`;
      nextStage = 'process_date_selection';
    }
    break;

  // ===== V77 STATE 12-NEW: INTERMEDIATE STATE - Trigger WF06 Available Slots =====
  case 'trigger_wf06_available_slots':
    console.log('V77: INTERMEDIATE STATE - Triggering WF06 available_slots call');

    // This state exists ONLY to trigger the Switch Node in workflow
    // Workflow detects next_stage === 'trigger_wf06_available_slots' and routes to HTTP Request 2
    // After HTTP Request returns, workflow passes data back to State Machine
    // Then State Machine advances to 'show_available_slots' to process WF06 response

    console.log('V77: Waiting for WF06 slots response...');

    // Set next stage to process WF06 slots response
    nextStage = 'show_available_slots';  // ← State Machine will be called again after HTTP Request
    responseText = '';  // ← No message here, HTTP Request sends "Aguarde..."

    break;

  // ===== V77 STATE 13: SHOW_AVAILABLE_SLOTS - Process WF06 slots response (UNCHANGED from V76) =====
  case 'show_available_slots':
    console.log('V77: Showing available slots (PROACTIVE UX)');

    // HTTP Request node should have already called WF06 and stored response
    const slotsResponse = input.wf06_available_slots || {};

    if (slotsResponse.success && slotsResponse.available_slots && slotsResponse.available_slots.length > 0) {
      // Build visual slot selection message
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
                    `${serviceDisplay[currentData.service_type]?.emoji || '🔧'} *Serviço*: ${getServiceName(currentData.service_type)}`;

      // Store slots for selection
      updateData.available_slots = slotsResponse.available_slots;
      nextStage = 'process_slot_selection';

    } else if (slotsResponse.success && slotsResponse.total_available === 0) {
      // No slots available for this date
      console.warn('V77: No slots available for selected date');
      responseText = `❌ *Esta data está totalmente ocupada*\n\n` +
                    `Vamos escolher outra data com mais disponibilidade.\n\n` +
                    `_Voltando para seleção de datas..._`;

      nextStage = 'show_available_dates'; // Go back to date selection
    } else {
      // WF06 failed - fallback to manual time input
      console.error('V77: WF06 available_slots failed, falling back to manual');
      responseText = `⚠️ *Não conseguimos buscar horários disponíveis*\n\n` +
                    `Por favor, informe o horário desejado (HH:MM):\n\n` +
                    `⏰ *Horários de atendimento:*\n` +
                    `• Segunda a Sexta: 08:00 às 18:00\n\n` +
                    `_Digite o horário..._`;

      nextStage = 'collect_appointment_time_manual'; // Fallback to V76 logic
    }
    break;

  // ===== V77 STATE 14: PROCESS_SLOT_SELECTION - Handle user time choice (UNCHANGED from V76) =====
  case 'process_slot_selection':
    console.log('V77: Processing slot selection');

    const slotChoice = message.trim();
    const availableSlots = currentData.available_slots || [];

    // Case 1: User selected from suggestions (1-N)
    if (/^\d+$/.test(slotChoice)) {
      const selectedIndex = parseInt(slotChoice) - 1;

      if (selectedIndex >= 0 && selectedIndex < availableSlots.length) {
        const selectedSlot = availableSlots[selectedIndex];
        console.log('V77: Slot selected from suggestions:', selectedSlot);

        // Store appointment time
        updateData.scheduled_time_start = selectedSlot.start_time;  // "09:00"
        updateData.scheduled_time_end = selectedSlot.end_time;      // "11:00"

        // Build final confirmation message
        const confirmationMessage = `✅ *Agendamento Confirmado!*\n\n` +
                                  `📅 *Data:* ${currentData.scheduled_date_display}\n` +
                                  `🕐 *Horário:* ${selectedSlot.formatted}\n` +
                                  `📍 *Cidade:* ${currentData.city}\n` +
                                  `${serviceDisplay[currentData.service_type]?.emoji || '🔧'} *Serviço*: ${getServiceName(currentData.service_type)}\n\n` +
                                  `_Processando agendamento..._`;

        responseText = confirmationMessage;

        // Go to final confirmation (State 15)
        nextStage = 'appointment_final_confirmation';

      } else {
        responseText = `❌ *Opção inválida*\n\nEscolha um número de 1 a ${availableSlots.length}`;
        nextStage = 'process_slot_selection';
      }
    }

    // Case 2: User entered custom time (HH:MM) - FALLBACK
    else if (/^\d{2}:\d{2}$/.test(slotChoice)) {
      console.log('V77: Custom time entered, validating:', slotChoice);

      // Validate time format and business hours
      const [hours, minutes] = slotChoice.split(':').map(Number);

      if (hours < 8 || hours >= 18 || minutes < 0 || minutes >= 60) {
        responseText = `❌ *Horário inválido*\n\nNosso atendimento é de Segunda a Sexta, 08:00 às 18:00.\n\nPor favor, escolha um horário dentro deste período.`;
        nextStage = 'process_slot_selection';
      } else {
        console.log('V77: Custom time validated successfully');

        updateData.scheduled_time_start = slotChoice;
        // Calculate end time (add 2 hours)
        const endHours = hours + 2;
        updateData.scheduled_time_end = `${String(endHours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`;

        responseText = `✅ *Horário registrado*\n\n` +
                      `📅 *Data:* ${currentData.scheduled_date_display}\n` +
                      `🕐 *Horário:* ${slotChoice} às ${updateData.scheduled_time_end}\n\n` +
                      `_Processando agendamento..._`;

        nextStage = 'appointment_final_confirmation';
      }
    }

    // Case 3: Invalid format
    else {
      responseText = `❌ *Formato inválido*\n\nEscolha um número (1-${availableSlots.length}) ou digite um horário em HH:MM`;
      nextStage = 'process_slot_selection';
    }
    break;

  // ===== V77 FALLBACK STATES: Manual Input (Keep V76 Logic) =====

  case 'collect_appointment_date_manual':
    // Fallback to manual date input when WF06 unavailable
    console.log('V77: FALLBACK - Manual date input');

    // Manual date validation logic (same as V76)
    if (/^\d{2}\/\d{2}\/\d{4}$/.test(message)) {
      const [day, month, year] = message.split('/');
      const isoDate = `${year}-${month}-${day}`;
      const dateObj = new Date(isoDate);

      const today = new Date();
      today.setHours(0, 0, 0, 0);

      const dayOfWeek = dateObj.getDay();
      const isWeekend = (dayOfWeek === 0 || dayOfWeek === 6);
      const isPast = dateObj < today;

      if (isPast) {
        responseText = `❌ *Data inválida*\n\nA data deve ser no futuro.\n\nPor favor, digite novamente.`;
        nextStage = 'collect_appointment_date_manual';
      }
      else if (isWeekend) {
        responseText = `❌ *Data inválida*\n\nNão atendemos aos finais de semana.\n\nDigite uma data de segunda a sexta.`;
        nextStage = 'collect_appointment_date_manual';
      }
      else {
        updateData.scheduled_date = isoDate;
        updateData.scheduled_date_display = message;

        responseText = `📅 *Data registrada:* ${message}\n\nAgora informe o horário desejado (HH:MM):\n\n⏰ Segunda a Sexta: 08:00 às 18:00`;
        nextStage = 'collect_appointment_time_manual';
      }
    } else {
      responseText = `❌ *Formato inválido*\n\nDigite a data no formato DD/MM/AAAA`;
      nextStage = 'collect_appointment_date_manual';
    }
    break;

  case 'collect_appointment_time_manual':
    // Fallback to manual time input when WF06 unavailable
    console.log('V77: FALLBACK - Manual time input');

    if (/^\d{2}:\d{2}$/.test(message)) {
      const [hours, minutes] = message.split(':').map(Number);

      if (hours < 8 || hours >= 18 || minutes < 0 || minutes >= 60) {
        responseText = `❌ *Horário inválido*\n\nAtendimento: Segunda a Sexta, 08:00 às 18:00.\n\nDigite novamente.`;
        nextStage = 'collect_appointment_time_manual';
      } else {
        updateData.scheduled_time_start = message;
        const endHours = hours + 2;
        updateData.scheduled_time_end = `${String(endHours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`;

        responseText = `✅ *Horário registrado*\n\n` +
                      `📅 Data: ${currentData.scheduled_date_display}\n` +
                      `🕐 Horário: ${message} às ${updateData.scheduled_time_end}\n\n` +
                      `_Processando agendamento..._`;

        nextStage = 'appointment_final_confirmation';
      }
    } else {
      responseText = `❌ *Formato inválido*\n\nDigite o horário no formato HH:MM`;
      nextStage = 'collect_appointment_time_manual';
    }
    break;

  // ===== STATE 15: APPOINTMENT_FINAL_CONFIRMATION (UNCHANGED from V76) =====
  case 'appointment_final_confirmation':
  case 'scheduling_redirect':
    console.log('V77: APPOINTMENT FINAL CONFIRMATION');

    // Trigger WF05 appointment creation
    responseText = `✅ *Agendamento realizado com sucesso!*\n\n` +
                  `📅 *Data:* ${currentData.scheduled_date_display}\n` +
                  `🕐 *Horário:* ${currentData.scheduled_time_start} às ${currentData.scheduled_time_end}\n\n` +
                  `📧 Você receberá um email de confirmação em breve.\n\n` +
                  `Até lá! ✨`;

    nextStage = 'completed';
    updateData.appointment_completed = true;
    break;

  // ===== REMAINING STATES: Correction flows, handoff, etc. (UNCHANGED from V76) =====

  case 'handoff_comercial':
    console.log('V77: Handoff to commercial team');
    responseText = responseText || 'Obrigado! Nossa equipe entrará em contato em breve.';
    nextStage = 'completed';
    break;

  case 'correction_choice':
    console.log('V77: Correction flow');
    // Handle correction choices (1-5)
    // [Keep V76 correction logic]
    break;

  case 'completed':
    console.log('V77: Conversation completed');
    responseText = 'Conversa finalizada. Digite *menu* para reiniciar.';
    nextStage = 'completed';
    break;

  default:
    console.error('V77: Unknown state:', currentStage);
    responseText = `⚠️ *Estado desconhecido*\n\nPor favor, reinicie a conversa digitando: *menu*`;
    nextStage = 'greeting';
}

// ===================================================
// RETURN RESULT
// ===================================================

console.log('V77: Response text:', responseText);
console.log('V77: Next stage:', nextStage);
console.log('V77: Update data:', JSON.stringify(updateData));
console.log('=== V77 STATE MACHINE END ===');

return {
  response: responseText,
  next_stage: nextStage,
  updateData: updateData
};
