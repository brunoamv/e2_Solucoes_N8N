# WF02 State Machine - WF06 Integration Problem Analysis

> **Execution**: http://localhost:5678/workflow/ja97SAbNzpFkG1ZJ/executions/125
> **Date**: 2026-04-14
> **Status**: ❌ WF06 NOT TRIGGERING
> **Issue**: State Machine V63/V73.2 missing WF06 integration logic

---

## 🚨 Problem Summary

**Symptom**: User selects "1" (agendar visita) for service 1 (Solar) or 3 (Projetos), but bot asks for manual date input instead of proactively showing WF06 calendar availability.

**Expected Behavior**:
```
User: 1 (confirm schedule)
Bot: ⏳ Buscando próximas datas disponíveis...
[WF06 triggered]
Bot: 📅 Próximas datas com horários disponíveis:
     1️⃣ Terça, 15/04/2026 - 8 horários livres ✨
     2️⃣ Quarta, 16/04/2026 - 6 horários livres 📅
     3️⃣ Quinta, 17/04/2026 - 4 horários livres ⚠️
```

**Actual Behavior**:
```
User: 1 (confirm schedule)
Bot: 📅 Ótimo! Vamos agendar sua visita técnica.
     Qual a melhor data para você? (formato DD/MM/AAAA)
     💡 Exemplo: 25/04/2026
[WF06 NEVER triggered]
```

---

## 🔍 Root Cause Analysis

### Active Workflow Investigation

**File**: `n8n/workflows/02_ai_agent_conversation_V74.1_2_FUNCIONANDO.json`
**Workflow ID**: `ja97SAbNzpFkG1ZJ`
**State Machine**: **V63/V73.2** (outdated version)

**Log Evidence**:
```
V73.2: Processing CONFIRMATION state
V73.2 FIX: Services 1 or 3 → Going to collect_appointment_date (State 9)
V63.1: Next stage: collect_appointment_date  ← WRONG!
V63.1: Response length: 123
```

### Code Comparison

**V73.2 State Machine (CURRENT - BROKEN)**:
```javascript
// File: n8n/workflows/02_ai_agent_conversation_V74.1_2_FUNCIONANDO.json
// State Machine Logic embedded in workflow

case 'confirmation':
  console.log('V73.2: Processing CONFIRMATION state');

  if (message === '1') {
    const serviceSelected = currentData.service_selected || '1';
    if (serviceSelected === '1' || serviceSelected === '3') {
      // V73.2 FIX: Go to State 9 to collect appointment date, NOT final message!
      console.log('V73.2 FIX: Services 1 or 3 → Going to collect_appointment_date (State 9)');
      responseText = '📅 *Ótimo! Vamos agendar sua visita técnica.*\n\nQual a melhor data para você? (formato DD/MM/AAAA)\n\n💡 _Exemplo: 25/04/2026_';
      nextStage = 'collect_appointment_date';  // ❌ WRONG! Goes to manual date input
    } else {
      // Other services → handoff
      console.log('V73.2: Other services → handoff_comercial');
      responseText = templates.handoff_comercial;
      nextStage = 'handoff_comercial';
      updateData.status = 'handoff';
    }
  }
```

**V78 State Machine (CORRECT - WITH WF06)**:
```javascript
// File: scripts/wf02-v78-state-machine.js
// Standalone State Machine with WF06 integration

case 'confirmation':
  console.log('V78: Processing CONFIRMATION state');

  if (message === '1') {
    const serviceSelected = currentData.service_type || '1';

    if (serviceSelected === '1' || serviceSelected === '3') {
      // V78: Services 1 or 3 → trigger WF06 next_dates call
      console.log('V78: Services 1 or 3 → trigger WF06 next_dates via Switch');

      nextStage = 'trigger_wf06_next_dates';  // ✅ CORRECT! Triggers WF06
      responseText = '⏳ *Buscando próximas datas disponíveis...*\n\n_Aguarde um momento..._';

      updateData.awaiting_wf06_next_dates = true;

    } else {
      // Services 2, 4, 5 → handoff to commercial
      console.log('V78: Services 2, 4, or 5 → handoff to commercial');
      responseText = `Obrigado pelas informações, ${currentData.lead_name}! 👍\n\n` +
                    `Para o serviço de *${getServiceName(serviceSelected)}*, nossa equipe comercial ` +
                    `entrará em contato em breve para alinhar os detalhes.\n\n` +
                    `📞 Caso prefira falar agora: (62) 3092-2900\n\n` +
                    `Tenha um ótimo dia! ✨`;
      nextStage = 'handoff_comercial';
    }
  }
```

---

## 📊 Detailed Flow Comparison

### V73.2 Flow (CURRENT - NO WF06)

```
STATE 8: confirmation
  User: 1
  Service: 1 or 3
  ↓
  nextStage = 'collect_appointment_date'
  responseText = "Qual a melhor data... DD/MM/AAAA"
  ↓
STATE 9: collect_appointment_date
  User: 25/04/2026
  ↓
  Validates date format, business days, future date
  ↓
  nextStage = 'collect_appointment_time'
  responseText = "Qual horário... HH:MM"
  ↓
STATE 10: collect_appointment_time
  User: 09:00
  ↓
  Validates time format, business hours
  ↓
  nextStage = 'appointment_confirmation'
  responseText = "Resumo... Confirma? 1-Sim 2-Não"
  ↓
STATE 11: appointment_confirmation
  User: 1
  ↓
  nextStage = 'scheduling_redirect'
  ↓
  WF05 triggered (Google Calendar insertion)
  ↓
  Completed
```

**❌ Problems with V73.2 Flow:**
1. Manual date input (reactive, error-prone)
2. Manual time input (reactive, error-prone)
3. No proactive UX (user types everything)
4. No WF06 integration
5. No calendar availability check
6. High chance of booking conflicts

### V78 Flow (CORRECT - WITH WF06)

```
STATE 8: confirmation
  User: 1
  Service: 1 or 3
  ↓
  nextStage = 'trigger_wf06_next_dates'
  responseText = "⏳ Buscando próximas datas disponíveis..."
  ↓
STATE 9: trigger_wf06_next_dates (INTERMEDIATE)
  Build Update Queries returns next_stage = 'trigger_wf06_next_dates'
  ↓
  Check If WF06 Next Dates (IF Node) detects trigger
  ↓
  HTTP Request - Get Next Dates executes
  POST http://e2bot-n8n-dev:5678/webhook/calendar-availability
  Body: { action: "next_dates", count: 3, start_date: "2026-04-14", duration_minutes: 120 }
  ↓
  WF06 Response:
  {
    success: true,
    dates: [
      { date: "2026-04-15", display: "Terça, 15/04/2026", total_slots: 8, quality: "high" },
      { date: "2026-04-16", display: "Quarta, 16/04/2026", total_slots: 6, quality: "medium" },
      { date: "2026-04-17", display: "Quinta, 17/04/2026", total_slots: 4, quality: "medium" }
    ]
  }
  ↓
  HTTP Request loops back to State Machine
  ↓
STATE 10: show_available_dates
  Processes WF06 response
  ↓
  responseText = "📅 Próximas datas com horários disponíveis:
                  1️⃣ Terça, 15/04/2026 - 8 horários livres ✨
                  2️⃣ Quarta, 16/04/2026 - 6 horários livres 📅
                  3️⃣ Quinta, 17/04/2026 - 4 horários livres ⚠️

                  💡 Escolha uma opção (1-3)
                  Ou digite uma data específica em DD/MM/AAAA"
  ↓
  nextStage = 'process_date_selection'
  updateData.date_suggestions = [dates from WF06]
  ↓
STATE 11: process_date_selection
  User: 1 (selects first option)
  ↓
  selectedDate = dates[0] = { date: "2026-04-15", display: "Terça, 15/04/2026" }
  updateData.scheduled_date = "2026-04-15"
  updateData.scheduled_date_display = "Terça, 15/04/2026"
  ↓
  nextStage = 'trigger_wf06_available_slots'
  responseText = "⏳ Buscando horários disponíveis..."
  ↓
STATE 12: trigger_wf06_available_slots (INTERMEDIATE)
  Build Update Queries returns next_stage = 'trigger_wf06_available_slots'
  ↓
  Check If WF06 Available Slots (IF Node) detects trigger
  ↓
  HTTP Request - Get Available Slots executes
  POST http://e2bot-n8n-dev:5678/webhook/calendar-availability
  Body: { action: "available_slots", date: "2026-04-15", duration_minutes: 120 }
  ↓
  WF06 Response:
  {
    success: true,
    total_available: 8,
    available_slots: [
      { start_time: "08:00", end_time: "10:00", formatted: "08:00 às 10:00" },
      { start_time: "10:00", end_time: "12:00", formatted: "10:00 às 12:00" },
      { start_time: "14:00", end_time: "16:00", formatted: "14:00 às 16:00" }
      ... (8 total)
    ]
  }
  ↓
  HTTP Request loops back to State Machine
  ↓
STATE 13: show_available_slots
  Processes WF06 response
  ↓
  responseText = "🕐 Horários Disponíveis - Terça, 15/04/2026

                  1️⃣ 08:00 às 10:00 ✅
                  2️⃣ 10:00 às 12:00 ✅
                  3️⃣ 14:00 às 16:00 ✅
                  ... (8 options)

                  💡 Escolha um horário (1-8)
                  Ou digite um horário específico em HH:MM"
  ↓
  nextStage = 'process_slot_selection'
  updateData.available_slots = [slots from WF06]
  ↓
STATE 14: process_slot_selection
  User: 2 (selects second slot)
  ↓
  selectedSlot = slots[1] = { start_time: "10:00", end_time: "12:00", formatted: "10:00 às 12:00" }
  updateData.scheduled_time_start = "10:00"
  updateData.scheduled_time_end = "12:00"
  ↓
  responseText = "✅ Agendamento Confirmado!
                  📅 Data: Terça, 15/04/2026
                  🕐 Horário: 10:00 às 12:00
                  📍 Cidade: cocal
                  ☀️ Serviço: Energia Solar

                  _Processando agendamento..._"
  ↓
  nextStage = 'appointment_final_confirmation'
  ↓
STATE 15: appointment_final_confirmation
  ↓
  responseText = "✅ Agendamento realizado com sucesso!
                  📅 Data: Terça, 15/04/2026
                  🕐 Horário: 10:00 às 12:00
                  📧 Você receberá um email de confirmação em breve.
                  Até lá! ✨"
  ↓
  nextStage = 'completed'
  updateData.appointment_completed = true
  ↓
  WF05 triggered (Google Calendar insertion)
  WF07 triggered (Email confirmation)
  ↓
  Completed
```

**✅ Benefits of V78 Flow:**
1. **Proactive UX**: Bot shows available options instead of asking user to type
2. **WF06 Integration**: Real-time calendar availability check
3. **Error Reduction**: User selects from valid options (no format errors)
4. **Better UX**: Faster booking (2 clicks vs. manual typing)
5. **No Conflicts**: Only shows actually available slots
6. **Graceful Fallback**: Falls back to manual input if WF06 fails

---

## 🔧 Technical Analysis

### State Machine Architecture Differences

**V73.2 States** (11 total):
1. greeting
2. service_selection
3. collect_name
4. collect_phone_whatsapp_confirmation
5. collect_phone_alternative
6. collect_email
7. collect_city
8. confirmation
9. collect_appointment_date (manual input)
10. collect_appointment_time (manual input)
11. appointment_confirmation

**V78 States** (14 total):
1-8. Same as V73.2
9. **trigger_wf06_next_dates** (NEW - intermediate state)
10. **show_available_dates** (NEW - proactive UX)
11. **process_date_selection** (NEW - handle user choice)
12. **trigger_wf06_available_slots** (NEW - intermediate state)
13. **show_available_slots** (NEW - proactive UX)
14. **process_slot_selection** (NEW - handle user choice)
15. appointment_final_confirmation

**New States Purpose**:
- **trigger_wf06_next_dates**: Sets next_stage that IF Node detects to route to HTTP Request 1
- **show_available_dates**: Processes WF06 response and shows proactive date options
- **process_date_selection**: Handles user selecting from suggested dates or custom date
- **trigger_wf06_available_slots**: Sets next_stage that IF Node detects to route to HTTP Request 2
- **show_available_slots**: Processes WF06 response and shows proactive time slot options
- **process_slot_selection**: Handles user selecting from suggested slots or custom time

### Workflow Architecture Requirements

**V79 IF Node Cascade** (required for V78 State Machine):
```
Build Update Queries
  ↓
Check If WF06 Next Dates (IF Node 1)
  Condition: {{ $node["Build Update Queries"].json.next_stage }} === "trigger_wf06_next_dates"
  ├─ TRUE → HTTP Request - Get Next Dates → State Machine Logic (loop)
  └─ FALSE ↓

Check If WF06 Available Slots (IF Node 2)
  Condition: {{ $node["Build Update Queries"].json.next_stage }} === "trigger_wf06_available_slots"
  ├─ TRUE → HTTP Request - Get Available Slots → State Machine Logic (loop)
  └─ FALSE → 5 PARALLEL NODES (fallback):
      ├─ Update Conversation State
      ├─ Save Inbound Message
      ├─ Save Outbound Message
      ├─ Upsert Lead Data
      └─ Send WhatsApp Response
```

**Current V74.1_2 Architecture** (incompatible with V78):
- No IF Node cascade
- No HTTP Request nodes
- No WF06 integration
- State Machine embedded in workflow (not standalone)

---

## 💡 Solution Approaches

### Option 1: Import V79.1 Workflow (RECOMMENDED)

**File**: `n8n/workflows/02_ai_agent_conversation_V79_1_SCHEMA_FIX.json`

**Pros**:
- ✅ Already generated and ready
- ✅ Has V79 IF Node cascade architecture
- ✅ Needs only State Machine update (V78 integration)
- ✅ Has Schema-aligned Build Update Queries (no contact_phone error)
- ✅ WF06 integration infrastructure ready

**Cons**:
- ❌ Needs State Machine Logic node update with V78 code
- ❌ Needs testing before activation

**Steps**:
1. Import V79.1 workflow
2. Update State Machine Logic node with V78 complete code (from V77 + V78 merge)
3. Test execution with services 1 and 3
4. Validate WF06 triggers correctly
5. Activate if tests pass

### Option 2: Create V74.2 with V78 State Machine

**Pros**:
- ✅ Minimal changes to proven V74.1_2
- ✅ Only State Machine replacement needed

**Cons**:
- ❌ V74.1_2 lacks IF Node cascade
- ❌ V74.1_2 lacks HTTP Request nodes
- ❌ Would need workflow architecture rebuild anyway
- ❌ Not worth the effort vs. Option 1

### Option 3: Manual State Machine Code Update in V74.1_2

**Pros**:
- ✅ Quick fix without workflow re-import

**Cons**:
- ❌ V74.1_2 lacks IF Node infrastructure
- ❌ V74.1_2 lacks HTTP Request nodes
- ❌ WF06 triggers won't work without IF Nodes
- ❌ NOT VIABLE - architecture incompatible

---

## ✅ Recommended Solution

**Approach**: **Option 1 - Import V79.1 + Update State Machine**

### Implementation Steps

#### Step 1: Prepare V78 State Machine Complete
```bash
# V78 State Machine currently has placeholders for states 1-7
# Need to merge V74.1_2 states 1-7 with V78 states 8-15

# Extract V74.1_2 states 1-7 from workflow JSON
# Merge with scripts/wf02-v78-state-machine.js states 8-15
# Create scripts/wf02-v78-complete-state-machine.js
```

#### Step 2: Generate V79.1 with Complete V78 State Machine
```bash
# Modify generate-workflow-wf02-v79_1-schema-fix.py
# Add State Machine update function
# Generate complete V79.1 workflow

python3 scripts/generate-workflow-wf02-v79_1-schema-fix.py
```

#### Step 3: Import and Test
```bash
# 1. Import to n8n
# File: n8n/workflows/02_ai_agent_conversation_V79_1_SCHEMA_FIX.json

# 2. Verify nodes
# - Check If WF06 Next Dates: Condition visible and correct
# - Check If WF06 Available Slots: Condition visible and correct
# - HTTP Request - Get Next Dates: Connected to State Machine loop
# - HTTP Request - Get Available Slots: Connected to State Machine loop
# - State Machine Logic: Has V78 complete code

# 3. Test execution
# Service 1 (Solar) → Confirm schedule → Should show WF06 dates
# Service 3 (Projetos) → Confirm schedule → Should show WF06 dates
# Service 2 (Subestação) → Confirm schedule → Should go to handoff

# 4. Validate database
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT phone_number, state_machine_state, scheduled_date, scheduled_time_start FROM conversations ORDER BY updated_at DESC LIMIT 1;"

# Expected: state_machine_state should progress through:
# confirmation → trigger_wf06_next_dates → show_available_dates →
# process_date_selection → trigger_wf06_available_slots →
# show_available_slots → process_slot_selection → appointment_final_confirmation
```

#### Step 4: Activate
```bash
# If all tests pass:
# 1. Deactivate V74.1_2
# 2. Activate V79.1
# 3. Monitor first 10 executions
# 4. Verify WF06 integration working
# 5. Check error rate (target: 0%)
```

---

## 📋 Testing Checklist

### Service 1 (Solar) - WF06 Integration
- [ ] User confirms schedule (message = "1")
- [ ] Bot responds: "⏳ Buscando próximas datas disponíveis..."
- [ ] Build Update Queries returns next_stage = "trigger_wf06_next_dates"
- [ ] Check If WF06 Next Dates (IF Node) TRUE path executes
- [ ] HTTP Request - Get Next Dates calls WF06
- [ ] WF06 returns 3 available dates
- [ ] Bot shows proactive date options (1️⃣ 2️⃣ 3️⃣)
- [ ] User selects option 1
- [ ] Bot responds: "⏳ Buscando horários disponíveis..."
- [ ] Build Update Queries returns next_stage = "trigger_wf06_available_slots"
- [ ] Check If WF06 Available Slots (IF Node) TRUE path executes
- [ ] HTTP Request - Get Available Slots calls WF06
- [ ] WF06 returns available time slots
- [ ] Bot shows proactive time slot options
- [ ] User selects slot
- [ ] Bot confirms appointment
- [ ] Database updated with scheduled_date and scheduled_time_start

### Service 3 (Projetos) - Same as Service 1
- [ ] Same flow as Service 1 (WF06 integration)

### Service 2 (Subestação) - Handoff Flow
- [ ] User confirms schedule (message = "1")
- [ ] Bot responds with handoff message (no WF06 trigger)
- [ ] state_machine_state = "handoff_comercial"
- [ ] Database updated with status = "handoff"

### Fallback Testing (WF06 Failure)
- [ ] Stop WF06 workflow temporarily
- [ ] Test Service 1 schedule
- [ ] Bot detects WF06 failure
- [ ] Bot falls back to manual date input
- [ ] Manual flow completes successfully

---

## 📚 Related Documentation

- **V78 State Machine**: `scripts/wf02-v78-state-machine.js`
- **V77 State Machine** (complete states 1-7): `scripts/wf02-v77-state-machine.js`
- **V79 Workflow**: `docs/WF02_V79_IF_CASCADE_DEPLOYMENT_SUMMARY.md`
- **V79.1 Schema Fix**: `docs/WF02_V79_1_SCHEMA_FIX_SUMMARY.md`
- **WF06 Service**: `docs/implementation/WF06_CALENDAR_AVAILABILITY_SERVICE.md`

---

## 🎯 Success Criteria

- [ ] Service 1 (Solar) triggers WF06 next_dates successfully
- [ ] Service 3 (Projetos) triggers WF06 next_dates successfully
- [ ] WF06 returns 3 date options with quality indicators
- [ ] User can select from suggested dates proactively
- [ ] WF06 available_slots triggered after date selection
- [ ] User can select from suggested time slots proactively
- [ ] Database correctly stores scheduled_date and scheduled_time_start
- [ ] No "contact_phone does not exist" error
- [ ] Error rate = 0% after 10 executions
- [ ] UX improvement: 2 clicks vs. manual typing

---

**Status**: 📝 Analysis Complete - Solution Documented
**Next**: Create complete V78 State Machine → Update V79.1 generator → Import → Test → Activate
**Priority**: 🔴 HIGH - Blocks proactive UX and WF06 integration
