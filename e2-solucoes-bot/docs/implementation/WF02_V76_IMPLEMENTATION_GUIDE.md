# WF02 V76 - Proactive UX Implementation Guide

> **Base**: WF02 V75 + WF06 V1
> **Goal**: Replace reactive States 9-10 with proactive date/time selection
> **Status**: Implementation Plan - Ready for Development
> **Timeline**: 4 days (State refactoring + Integration + Testing)

---

## Overview

WF02 V76 refactors the appointment scheduling flow from **REACTIVE** (user types dates/times → system validates) to **PROACTIVE** (system proposes pre-validated options → user selects).

**UX Impact**:
- **Interactions**: 7-10 → 2-3 (70% reduction)
- **Errors**: 2-3 → 0 (100% elimination)
- **Time to book**: 2-3 min → 30 seconds (75% faster)

**Technical Changes**:
- Replace States 9-10 with 4 new states
- Add 2 HTTP Request nodes calling WF06 endpoints
- Add 4 new templates for proactive UX
- Modify state machine logic for single-digit selection

---

## Architecture Changes

### State Machine Flow Comparison

#### V75 (REACTIVE - Current)
```
State 7: collect_city
  ↓
State 8: confirmation → User chooses "1 - Sim, quero agendar"
  ↓
State 9: collect_appointment_date
  Bot: "Digite a data (DD/MM/AAAA)"
  User: "15/04/2026" (manual typing)
  ↓ validate → error loop if weekend/past date
  ↓
State 10: collect_appointment_time
  Bot: "Digite o horário (HH:MM)"
  User: "14:30" (manual typing)
  ↓ check calendar → error loop if occupied
  ↓
State 11: appointment_final_confirmation
  → Call WF05 to schedule

Problems: Manual typing, blind guessing, error loops
```

#### V76 (PROACTIVE - New)
```
State 7: collect_city
  ↓
State 8: confirmation → User chooses "1 - Sim, quero agendar"
  ↓
State 9-NEW: show_available_dates
  HTTP Request to WF06 next_dates endpoint
  Bot: "📅 Próximas datas:
       1️⃣ Amanhã (07/04) - 3 horários
       2️⃣ Quarta (08/04) - 5 horários
       3️⃣ Quinta (09/04) - 2 horários"
  User: "2" (single-digit selection)
  ↓
State 10-NEW: process_date_selection
  Validate user choice (1-3)
  Store selected date
  ↓
State 11-NEW: show_available_slots
  HTTP Request to WF06 available_slots endpoint
  Bot: "🕐 Horários disponíveis - Quarta (08/04):
       1️⃣ 9h às 11h ✅
       2️⃣ 14h às 16h ✅
       3️⃣ 16h às 18h ✅"
  User: "2" (single-digit selection)
  ↓
State 12-NEW: process_slot_selection
  Validate user choice (1-N)
  Store selected time
  ↓
State 13: appointment_final_confirmation
  → Call WF05 to schedule

Benefits: Zero errors, visual clarity, mobile-friendly
```

### New Nodes Required

#### Node: "HTTP Request - Get Next Dates" (after State 8 confirmation)
```json
{
  "parameters": {
    "method": "POST",
    "url": "http://e2bot-n8n-dev:5678/webhook/calendar-availability",
    "authentication": "none",
    "jsonParameters": true,
    "options": {
      "bodyParametersJson": "={{ JSON.stringify({\n  action: 'next_dates',\n  count: 3,\n  duration_minutes: 120,\n  start_date: new Date().toISOString().split('T')[0]\n}) }}"
    }
  },
  "name": "HTTP Request - Get Next Dates",
  "type": "n8n-nodes-base.httpRequest",
  "continueOnFail": true,
  "retryOnFail": true,
  "maxTries": 2
}
```

#### Node: "HTTP Request - Get Available Slots" (after State 10 date selection)
```json
{
  "parameters": {
    "method": "POST",
    "url": "http://e2bot-n8n-dev:5678/webhook/calendar-availability",
    "authentication": "none",
    "jsonParameters": true,
    "options": {
      "bodyParametersJson": "={{ JSON.stringify({\n  action: 'available_slots',\n  date: $json.selectedDate,\n  duration_minutes: 120\n}) }}"
    }
  },
  "name": "HTTP Request - Get Available Slots",
  "type": "n8n-nodes-base.httpRequest",
  "continueOnFail": true,
  "retryOnFail": true,
  "maxTries": 2
}
```

---

## State Machine Logic Changes

### State 9-NEW: `show_available_dates`

**Purpose**: Call WF06 next_dates and show 3 date options with availability

**Code Logic**:
```javascript
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
```

### State 10-NEW: `process_date_selection`

**Purpose**: Process user's date choice (1-3) or custom date input

**Code Logic**:
```javascript
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
```

### State 11-NEW: `show_available_slots`

**Purpose**: Call WF06 available_slots and show time options

**Code Logic**:
```javascript
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
```

### State 12-NEW: `process_slot_selection`

**Purpose**: Process user's slot choice (1-N) or custom time input

**Code Logic**:
```javascript
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
```

### State 13: `appointment_final_confirmation` (UNCHANGED from V75)

**Purpose**: Call WF05 to create calendar event and send confirmation

**No changes needed** - this state remains identical to V75. It receives:
- `scheduled_date` (YYYY-MM-DD)
- `scheduled_time_start` (HH:MM)
- `scheduled_time_end` (HH:MM)

WF05 V7 handles the rest (calendar creation, email trigger).

---

## Workflow Integration Points

### 1. After State 8 Confirmation (User chooses "1 - Sim, quero agendar")

**Current V75 Flow**:
```
State 8: confirmation → choice "1"
  ↓
State 9: collect_appointment_date (manual input)
```

**New V76 Flow**:
```
State 8: confirmation → choice "1"
  ↓
HTTP Request Node: Get Next Dates
  ↓ (store response in workflow data)
  ↓
State 9-NEW: show_available_dates (display options)
```

**Implementation**: Add HTTP Request node BEFORE State 9 code execution

### 2. After State 10 Date Selection

**New V76 Flow**:
```
State 10-NEW: process_date_selection → valid date selected
  ↓
HTTP Request Node: Get Available Slots
  ↓ (store response in workflow data)
  ↓
State 11-NEW: show_available_slots (display options)
```

**Implementation**: Add HTTP Request node BEFORE State 11 code execution

### 3. Error Handling & Fallbacks

**WF06 Failure Scenarios**:
1. **WF06 not responding**: Fallback to manual date/time input (V75 logic)
2. **No dates available**: Show message, ask for custom date
3. **No slots available**: Return to date selection with different options
4. **Network timeout**: Retry once, then fallback

**Fallback States** (keep V75 logic):
- `collect_appointment_date_manual` - Manual date input (DD/MM/AAAA)
- `collect_appointment_time_manual` - Manual time input (HH:MM)

---

## Template Changes

### New Templates Required (4)

#### Template: `show_available_dates_v76`
```javascript
const show_available_dates_v76 = `📅 *Agendar Visita Técnica - {{service_name}}*

📆 *Próximas datas com horários disponíveis:*

{{date_options}}

💡 *Escolha uma opção (1-3)*
_Ou digite uma data específica em DD/MM/AAAA_

⏱️ *Duração*: 2 horas
📍 *Cidade*: {{city}}`;
```

#### Template: `show_available_slots_v76`
```javascript
const show_available_slots_v76 = `🕐 *Horários Disponíveis - {{date_display}}*

{{slot_options}}

💡 *Escolha um horário (1-{{count}})*
_Ou digite um horário específico em HH:MM_

⏱️ *Duração*: 2 horas
📍 *Cidade*: {{city}}
{{service_emoji}} *Serviço*: {{service_name}}`;
```

#### Template: `no_dates_available`
```javascript
const no_dates_available = `⚠️ *Agenda cheia nos próximos dias*

Nossa agenda está completa para os próximos dias úteis.

*Opções:*
1️⃣ Informar uma data específica que preferir
2️⃣ Falar com um atendente para verificar disponibilidade

_Digite 1 ou 2:_`;
```

#### Template: `date_fully_booked`
```javascript
const date_fully_booked = `❌ *Esta data está totalmente ocupada*

A data {{date_display}} não possui horários disponíveis.

Vamos escolher outra data com mais disponibilidade.

_Voltando para seleção de datas..._`;
```

---

## Testing Plan

### Unit Tests (Per State)

#### Test Suite 1: State 9 (show_available_dates)
```bash
# Test 1: WF06 returns 3 dates successfully
Input: (triggered from State 8, WF06 response with 3 dates)
Expected: Message with 3 numbered options, proactive selection prompt
State transition: show_available_dates → process_date_selection

# Test 2: WF06 returns empty dates
Input: (WF06 response with empty dates array)
Expected: Fallback to manual date input
State transition: show_available_dates → collect_appointment_date_manual

# Test 3: WF06 fails/timeout
Input: (WF06 error or timeout)
Expected: Fallback to manual date input with apology message
State transition: show_available_dates → collect_appointment_date_manual
```

#### Test Suite 2: State 10 (process_date_selection)
```bash
# Test 1: User selects option "2"
Input: "2"
Expected: Store date_suggestions[1], transition to show_available_slots
State transition: process_date_selection → show_available_slots

# Test 2: User enters custom date "15/04/2026" (valid)
Input: "15/04/2026"
Expected: Validate date (business day, future), transition to show_available_slots
State transition: process_date_selection → show_available_slots

# Test 3: User enters weekend date "12/04/2026" (Saturday)
Input: "12/04/2026"
Expected: Error message about weekends, stay in same state
State transition: process_date_selection → process_date_selection

# Test 4: User enters past date "01/01/2026"
Input: "01/01/2026"
Expected: Error message about past dates, stay in same state
State transition: process_date_selection → process_date_selection

# Test 5: User enters invalid format "15-04-2026"
Input: "15-04-2026"
Expected: Error message about format, stay in same state
State transition: process_date_selection → process_date_selection
```

#### Test Suite 3: State 11 (show_available_slots)
```bash
# Test 1: WF06 returns 5 slots successfully
Input: (triggered from State 10, WF06 response with 5 slots)
Expected: Message with 5 numbered time options
State transition: show_available_slots → process_slot_selection

# Test 2: WF06 returns 0 slots (date fully booked)
Input: (WF06 response with empty slots array)
Expected: Message "date fully booked", return to date selection
State transition: show_available_slots → show_available_dates

# Test 3: WF06 fails/timeout
Input: (WF06 error or timeout)
Expected: Fallback to manual time input
State transition: show_available_slots → collect_appointment_time_manual
```

#### Test Suite 4: State 12 (process_slot_selection)
```bash
# Test 1: User selects option "2"
Input: "2"
Expected: Store available_slots[1], transition to final confirmation
State transition: process_slot_selection → appointment_final_confirmation

# Test 2: User enters custom time "14:30" (valid business hours)
Input: "14:30"
Expected: Validate time, transition to final confirmation
State transition: process_slot_selection → appointment_final_confirmation

# Test 3: User enters time "20:00" (outside business hours)
Input: "20:00"
Expected: Error message about business hours, stay in same state
State transition: process_slot_selection → process_slot_selection

# Test 4: User enters invalid format "2:30pm"
Input: "2:30pm"
Expected: Error message about format, stay in same state
State transition: process_slot_selection → process_slot_selection
```

### E2E Happy Path Test

**Scenario**: Complete appointment booking with zero errors

```bash
# Step 1: User completes data collection (States 1-7)
User: [service selection, name, phone, email, city]
Bot: [confirmation message with all data]

# Step 2: User confirms and chooses to schedule
User: "1" (Sim, quero agendar)
Bot: [WF06 call] "📅 Próximas datas:
     1️⃣ Amanhã (07/04) - 3 horários ✨
     2️⃣ Quarta (08/04) - 5 horários ✨
     3️⃣ Quinta (09/04) - 2 horários ⚠️"

# Step 3: User selects date
User: "2" (Quarta 08/04)
Bot: [WF06 call] "🕐 Horários disponíveis - Quarta (08/04):
     1️⃣ 9h às 11h ✅
     2️⃣ 14h às 16h ✅
     3️⃣ 16h às 18h ✅"

# Step 4: User selects time
User: "2" (14h às 16h)
Bot: "✅ Agendamento Confirmado!
     📅 Data: Quarta (08/04)
     🕐 Horário: 14h às 16h
     [calling WF05...]"

# Step 5: Final confirmation (V75 logic - UNCHANGED)
Bot: [WF05 success] "✅ Visita agendada com sucesso!
     📅 Quarta, 08/04/2026
     🕐 14h às 16h
     📍 Cocal, GO
     📧 Confirmação enviada para seu e-mail
     🔗 Google Calendar: [link]"

# Expected:
# ✅ Zero errors
# ✅ 3 interactions total (confirmation → date → time)
# ✅ 30 seconds completion time
# ✅ Appointment created in Google Calendar
# ✅ Email sent via WF07
```

### Performance Benchmarks

| Metric | V75 (Current) | V76 (Target) | Actual (Test Result) |
|--------|---------------|--------------|----------------------|
| Avg interactions to book | 7-10 | 2-3 | _TBD_ |
| Avg errors per booking | 2-3 | 0 | _TBD_ |
| Time to complete booking | 2-3 min | 30 sec | _TBD_ |
| WF06 API call latency | N/A | <2s | _TBD_ |
| Happy path success rate | 60% | 95% | _TBD_ |

---

## Deployment Strategy

### Phase 1: Import WF02 V76 (Day 1)

**Prerequisites**:
- ✅ WF06 V1 deployed and tested
- ✅ WF02 V76 JSON generated
- ✅ All new templates added to code

**Steps**:
```bash
# 1. Backup V75
http://localhost:5678 → Export → 02_ai_agent_conversation_V75_APPOINTMENT_FINAL_MESSAGE.json

# 2. Import V76 (INACTIVE initially)
http://localhost:5678 → Import → 02_ai_agent_conversation_V76_PROACTIVE_UX.json

# 3. Configure webhook
# Keep V75 webhook active: /webhook-ai-agent
# Create V76 test webhook: /webhook-ai-agent-v76

# 4. Test manually with test WhatsApp number
# Send messages to test webhook, validate States 9-12
```

### Phase 2: Canary Testing (Day 2)

**20% Traffic Split**:
```javascript
// In WF01 Main Handler - Add routing logic
const isCanaryUser = Math.random() < 0.20; // 20% traffic

if (isCanaryUser) {
    // Route to WF02 V76
    workflowId = '02_ai_agent_conversation_V76_PROACTIVE_UX';
} else {
    // Route to WF02 V75 (stable)
    workflowId = '02_ai_agent_conversation_V75_APPOINTMENT_FINAL_MESSAGE';
}
```

**Monitoring**:
```bash
# Watch n8n logs for V76 errors
docker logs -f e2bot-n8n-dev | grep -E "V76|show_available_dates|process_.*_selection"

# Check database for appointment success rates
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT
        CASE WHEN current_state LIKE '%v76%' THEN 'V76' ELSE 'V75' END as version,
        COUNT(*) as total,
        SUM(CASE WHEN status = 'confirmed' THEN 1 ELSE 0 END) as confirmed
      FROM conversations
      WHERE updated_at > NOW() - INTERVAL '24 hours'
      GROUP BY version;"
```

**Success Criteria for Phase 3**:
- ✅ Error rate <1% for V76 users
- ✅ Booking completion rate >90%
- ✅ WF06 API success rate >95%
- ✅ No critical bugs reported

### Phase 3: Progressive Rollout (Days 3-4)

**50% → 80% → 100% Traffic**:
```bash
# Day 3 Morning: 50%
# Update WF01 routing: isCanaryUser = Math.random() < 0.50

# Day 3 Afternoon: 80% (if 50% stable for 4+ hours)
# Update WF01 routing: isCanaryUser = Math.random() < 0.80

# Day 4 Morning: 100% (if 80% stable for 12+ hours)
# Activate V76 webhook as primary: /webhook-ai-agent
# Deactivate V75 workflow
```

**Rollback Plan**:
```bash
# IF error rate >5% OR critical bugs detected:

# 1. Immediate rollback to V75 (< 2 minutes)
WF01 routing: workflowId = 'V75'; // 100% to V75

# 2. Deactivate V76
http://localhost:5678 → Workflows → V76 → Toggle OFF

# 3. Investigate logs
docker logs e2bot-n8n-dev | grep -A 20 "ERROR.*V76"

# 4. Fix issues, restart from Phase 1
```

### Phase 4: Cleanup (Day 5)

**After 48h stable at 100% V76**:
```bash
# 1. Archive V75 workflow
http://localhost:5678 → Workflows → V75 → Export → Archive

# 2. Remove V75 routing logic from WF01

# 3. Update documentation
# - Mark V76 as PROD in CLAUDE.md
# - Archive V75 docs in docs/archive/

# 4. Monitor for 1 week
# - Check appointment completion rates
# - Validate email/calendar integration
# - Collect user feedback
```

---

## Risk Assessment & Mitigation

### High-Risk Areas

#### Risk 1: WF06 Dependency Failure
**Scenario**: WF06 service unavailable or returning errors
**Impact**: 🔴 HIGH - Users cannot book appointments
**Probability**: 🟡 MEDIUM (new service, potential bugs)

**Mitigation**:
- ✅ Fallback to V75 manual input logic (already coded)
- ✅ HTTP Request retry logic (maxTries: 2)
- ✅ Monitoring alerts for WF06 failures
- ✅ Rollback to V75 if WF06 error rate >10%

#### Risk 2: State Machine Logic Errors
**Scenario**: Incorrect state transitions or data loss
**Impact**: 🔴 HIGH - Broken user experience
**Probability**: 🟡 MEDIUM (complex refactoring)

**Mitigation**:
- ✅ Comprehensive unit tests per state (16 tests)
- ✅ E2E happy path test before deployment
- ✅ Canary testing with 20% traffic first
- ✅ Database logging of all state transitions

#### Risk 3: User Confusion with New UX
**Scenario**: Users don't understand new selection format
**Impact**: 🟡 MEDIUM - Lower booking completion rate
**Probability**: 🟢 LOW (simpler UX than V75)

**Mitigation**:
- ✅ Clear instructions in every message ("Digite 1-3")
- ✅ Fallback option to manual input still available
- ✅ Monitor conversion rate V75 vs V76
- ✅ User feedback collection after 1 week

### Medium-Risk Areas

#### Risk 4: Performance Degradation
**Scenario**: WF06 API calls add latency
**Impact**: 🟡 MEDIUM - Slower user experience
**Probability**: 🟢 LOW (WF06 designed for <2s response)

**Mitigation**:
- ✅ Performance benchmarks before deployment
- ✅ Timeout handling (2s timeout, then fallback)
- ✅ Monitoring of API response times

---

## Success Metrics

### Primary KPIs (Track for 2 weeks)

| Metric | V75 Baseline | V76 Target | Week 1 | Week 2 |
|--------|-------------|-----------|---------|---------|
| **Booking completion rate** | 60% | 95% | _TBD_ | _TBD_ |
| **Avg errors per booking** | 2-3 | 0 | _TBD_ | _TBD_ |
| **Avg interactions to book** | 7-10 | 2-3 | _TBD_ | _TBD_ |
| **Time to complete booking** | 2-3 min | 30 sec | _TBD_ | _TBD_ |
| **Mobile typing instances** | 100% | 20% | _TBD_ | _TBD_ |

### Secondary KPIs

| Metric | Target | Week 1 | Week 2 |
|--------|--------|---------|---------|
| **WF06 API success rate** | >95% | _TBD_ | _TBD_ |
| **Fallback to manual input rate** | <10% | _TBD_ | _TBD_ |
| **User satisfaction (self-reported)** | >8/10 | _TBD_ | _TBD_ |
| **Appointment no-show rate** | <15% | _TBD_ | _TBD_ |

---

## Next Steps

### Immediate Actions (Day 1)

1. **Generate WF02 V76 workflow JSON** (4-6 hours)
   - Copy WF02 V75 JSON as base
   - Add 2 HTTP Request nodes (Get Next Dates, Get Available Slots)
   - Replace States 9-10 code with new States 9-12 code
   - Add 4 new templates
   - Update state machine switch cases

2. **Create E2E test script** (2 hours)
   - Bash script simulating WhatsApp messages
   - Test happy path with mock WF06 responses
   - Validate all state transitions

3. **Import and test V76** (2 hours)
   - Import to n8n development environment
   - Manual testing with test WhatsApp number
   - Verify WF06 integration

### Follow-up Actions (Days 2-5)

4. **Canary deployment** (Day 2)
   - 20% traffic split in WF01
   - Monitor metrics for 24 hours

5. **Progressive rollout** (Days 3-4)
   - 50% → 80% → 100% traffic
   - Continuous monitoring

6. **Cleanup and documentation** (Day 5)
   - Archive V75 workflow
   - Update project documentation
   - Collect user feedback

---

**Version**: V76 Implementation Guide | **Status**: Ready for Development
**Timeline**: 4-5 days (Development + Testing + Deployment)
**Next**: Generate WF02 V76 JSON workflow file

