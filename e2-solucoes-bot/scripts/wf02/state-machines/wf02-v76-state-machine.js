// ===================================================
// V76 STATE MACHINE - PROACTIVE UX IMPLEMENTATION
// ===================================================
// Changes from V75:
// - REPLACED: States 9-10 (reactive) with States 9-12 (proactive)
// - ADDED: WF06 integration for date/time suggestions
// - ADDED: Fallback to manual input when WF06 unavailable
// - STATES: 12 (was 10 in V75)
// - TEMPLATES: 16 (was 12 in V75)
// Date: 2026-04-06
// Version: V76 Proactive UX
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

console.log('=== V76 STATE MACHINE START ===');
console.log('V76: Current stage:', currentStage);
console.log('V76: User message:', message);
console.log('V76: Current data:', JSON.stringify(currentData));

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

// Templates (16 total - V76 adds 4 new for proactive UX)
const templates = {
  // ... [Keep all V75 templates - States 1-8] ...
  // [Copy from V75 workflow: greeting, invalid_service, service_acknowledged, etc.]

  // V76 NEW TEMPLATES FOR PROACTIVE UX
  "show_available_dates_v76": `📅 *Agendar Visita Técnica - {{service_name}}*

📆 *Próximas datas com horários disponíveis:*

{{date_options}}

💡 *Escolha uma opção (1-3)*
_Ou digite uma data específica em DD/MM/AAAA_

⏱️ *Duração*: 2 horas
📍 *Cidade*: {{city}}`,

  "show_available_slots_v76": `🕐 *Horários Disponíveis - {{date_display}}*

{{slot_options}}

💡 *Escolha um horário (1-{{count}})*
_Ou digite um horário específico em HH:MM_

⏱️ *Duração*: 2 horas
📍 *Cidade*: {{city}}
{{service_emoji}} *Serviço*: {{service_name}}`,

  "no_dates_available": `⚠️ *Agenda cheia nos próximos dias*

Nossa agenda está completa para os próximos dias úteis.

*Opções:*
1️⃣ Informar uma data específica que preferir
2️⃣ Falar com um atendente para verificar disponibilidade

_Digite 1 ou 2:_`,

  "date_fully_booked": `❌ *Esta data está totalmente ocupada*

A data {{date_display}} não possui horários disponíveis.

Vamos escolher outra data com mais disponibilidade.

_Voltando para seleção de datas..._`
};

// Initialize response variables
let responseText = '';
let nextStage = currentStage;
let updateData = {};

// ===================================================
// V76 STATE MACHINE LOGIC
// ===================================================

switch (currentStage) {

  // ===== STATES 1-8: UNCHANGED from V75 =====
  // [Copy exact State 1-8 logic from V75]
  // - greeting
  // - service_selection
  // - collect_name
  // - collect_phone_whatsapp_confirmation
  // - collect_phone_alternative
  // - collect_email
  // - collect_city
  // - confirmation

  // ===== V76 STATE 9-NEW: SHOW_AVAILABLE_DATES - Proactive date selection =====
  case 'show_available_dates':
    console.log('V76: Showing available dates (PROACTIVE UX)');

    // This state is entered from State 8 confirmation (option 1)
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
      console.warn('V76: WF06 failed, falling back to manual date input');
      responseText = `⚠️ *Não conseguimos buscar disponibilidade automaticamente*\n\n` +
                    `Por favor, informe a data desejada (DD/MM/AAAA):\n\n` +
                    `💡 *Lembre-se:*\n` +
                    `• Data futura (não pode ser hoje ou passado)\n` +
                    `• Dia útil (segunda a sexta-feira)\n\n` +
                    `_Digite a data..._`;

      nextStage = 'collect_appointment_date_manual'; // Fallback to V75 logic
    }
    break;

  // ===== V76 STATE 10-NEW: PROCESS_DATE_SELECTION - Handle user date choice =====
  case 'process_date_selection':
    console.log('V76: Processing date selection');

    const dateChoice = message.trim();

    // Case 1: User selected from suggestions (1-3)
    if (/^[1-3]$/.test(dateChoice)) {
      const selectedIndex = parseInt(dateChoice) - 1;
      const suggestions = currentData.date_suggestions || [];

      if (selectedIndex >= 0 && selectedIndex < suggestions.length) {
        const selectedDate = suggestions[selectedIndex];
        console.log('V76: Date selected from suggestions:', selectedDate.date);

        // Store selected date
        updateData.scheduled_date = selectedDate.date;           // YYYY-MM-DD (for WF06 API)
        updateData.scheduled_date_display = selectedDate.display; // "Quarta (08/04)" (for messages)

        // Go to State 11: Show available slots
        nextStage = 'show_available_slots';

      } else {
        responseText = `❌ *Opção inválida*\n\nEscolha 1, 2 ou 3.`;
        nextStage = 'process_date_selection';
      }
    }

    // Case 2: User entered custom date (DD/MM/AAAA) - FALLBACK
    else if (/^\d{2}\/\d{2}\/\d{4}$/.test(dateChoice)) {
      console.log('V76: Custom date entered, validating:', dateChoice);

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
        console.log('V76: Custom date validated successfully');

        // Store date
        updateData.scheduled_date = isoDate;
        updateData.scheduled_date_display = dateChoice;

        // Go to State 11: Show available slots
        nextStage = 'show_available_slots';
      }
    }

    // Case 3: Invalid format
    else {
      responseText = `❌ *Formato inválido*\n\nEscolha 1-3 ou digite uma data em DD/MM/AAAA`;
      nextStage = 'process_date_selection';
    }
    break;

  // ===== V76 STATE 11-NEW: SHOW_AVAILABLE_SLOTS - Proactive time selection =====
  case 'show_available_slots':
    console.log('V76: Showing available slots (PROACTIVE UX)');

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
      console.warn('V76: No slots available for selected date');
      responseText = `❌ *Esta data está totalmente ocupada*\n\n` +
                    `Vamos escolher outra data com mais disponibilidade.\n\n` +
                    `_Voltando para seleção de datas..._`;

      nextStage = 'show_available_dates'; // Go back to date selection
    } else {
      // WF06 failed - fallback to manual time input
      console.error('V76: WF06 available_slots failed, falling back to manual');
      responseText = `⚠️ *Não conseguimos buscar horários disponíveis*\n\n` +
                    `Por favor, informe o horário desejado (HH:MM):\n\n` +
                    `⏰ *Horários de atendimento:*\n` +
                    `• Segunda a Sexta: 08:00 às 18:00\n\n` +
                    `_Digite o horário..._`;

      nextStage = 'collect_appointment_time_manual'; // Fallback to V75 logic
    }
    break;

  // ===== V76 STATE 12-NEW: PROCESS_SLOT_SELECTION - Handle user time choice =====
  case 'process_slot_selection':
    console.log('V76: Processing slot selection');

    const slotChoice = message.trim();
    const availableSlots = currentData.available_slots || [];

    // Case 1: User selected from suggestions (1-N)
    if (/^\d+$/.test(slotChoice)) {
      const selectedIndex = parseInt(slotChoice) - 1;

      if (selectedIndex >= 0 && selectedIndex < availableSlots.length) {
        const selectedSlot = availableSlots[selectedIndex];
        console.log('V76: Slot selected from suggestions:', selectedSlot);

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

        // Go to final confirmation (State 13)
        nextStage = 'appointment_final_confirmation';

      } else {
        responseText = `❌ *Opção inválida*\n\nEscolha um número de 1 a ${availableSlots.length}`;
        nextStage = 'process_slot_selection';
      }
    }

    // Case 2: User entered custom time (HH:MM) - FALLBACK
    else if (/^\d{2}:\d{2}$/.test(slotChoice)) {
      console.log('V76: Custom time entered, validating:', slotChoice);

      // Validate time format and business hours
      const [hours, minutes] = slotChoice.split(':').map(Number);

      if (hours < 8 || hours >= 18 || minutes < 0 || minutes >= 60) {
        responseText = `❌ *Horário inválido*\n\nNosso atendimento é de Segunda a Sexta, 08:00 às 18:00.\n\nPor favor, escolha um horário dentro deste período.`;
        nextStage = 'process_slot_selection';
      } else {
        console.log('V76: Custom time validated, checking calendar availability...');

        // TODO: Call WF06 to check if this specific time is available
        // For now, accept and let WF05 handle validation

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

  // ===== V76 FALLBACK STATES: Manual Input (Keep V75 Logic) =====

  case 'collect_appointment_date_manual':
    // [Copy exact collect_appointment_date logic from V75 State 9]
    // Allows fallback to manual date input when WF06 unavailable
    break;

  case 'collect_appointment_time_manual':
    // [Copy exact collect_appointment_time logic from V75 State 10]
    // Allows fallback to manual time input when WF06 unavailable
    break;

  // ===== STATE 13: APPOINTMENT_FINAL_CONFIRMATION (UNCHANGED from V75) =====
  case 'appointment_final_confirmation':
  case 'scheduling_redirect':
    // [Copy exact appointment_final_confirmation logic from V75 State 11]
    // No changes needed - receives scheduled_date, scheduled_time_start, scheduled_time_end
    // Triggers WF05 appointment creation
    break;

  // ===== REMAINING STATES: UNCHANGED from V75 =====
  // [Copy all other states from V75: handoff_comercial, correction flows, etc.]

  default:
    console.error('V76: Unknown state:', currentStage);
    responseText = `⚠️ *Estado desconhecido*\n\nPor favor, reinicie a conversa digitando: *menu*`;
    nextStage = 'greeting';
}

// ===================================================
// RETURN RESULT
// ===================================================

console.log('V76: Response text:', responseText);
console.log('V76: Next stage:', nextStage);
console.log('V76: Update data:', JSON.stringify(updateData));
console.log('=== V76 STATE MACHINE END ===');

return {
  response: responseText,
  next_stage: nextStage,
  updateData: updateData
};
