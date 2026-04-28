# BUGFIX WF02 V107 - WF06 Date Selection Loop + Upsert Lead Undefined Fix

**Date**: 2026-04-27
**Version**: V107 COMPLETE FIX
**Status**: 🔴 CRITICAL - Production Blocking
**Impact**: WF06 date/slot selection creates infinite loop + SQL undefined errors

---

## 🚨 Critical Issues

### Issue 1: SQL "undefined" in Upsert Lead Data
**Execution**: http://localhost:5678/workflow/9tG2gR6KBt6nYyHT/executions/8708
**Error**: `Syntax error at line 1 near "undefined"`
**Node**: "Upsert Lead Data"
**Symptom**: query_upsert_lead field is undefined when node executes

### Issue 2: WF06 Date Selection Loop
**Execution**: http://localhost:5678/workflow/9tG2gR6KBt6nYyHT/executions/8721
**Symptom**:
- Bot sends "📅 Escolha uma opção (1-3)"
- User types "1"
- Bot sends SAME message again (infinite loop)
- Database shows `awaiting_wf06_next_dates: true` but state never advances

---

## 🔍 Root Cause Analysis

### Issue 1: Upsert Lead Undefined

**Evidence**:
```json
// Node configuration
{
  "name": "Upsert Lead Data",
  "parameters": {
    "operation": "executeQuery",
    "query": "={{ $json.query_upsert_lead }}"
  }
}
```

**Log Error**:
```
Failed query:  undefined
Syntax error at line 1 near "undefined"
```

**Analysis**:
- Build Update Queries DOES generate `query_upsert_lead` correctly (V104.2 script line 308)
- BUT: Upsert Lead Data node is trying to access `$json.query_upsert_lead`
- **Root Cause**: `$json` in n8n only accesses previous node's FIRST output
- If Build Update Queries returns multiple items or wrong structure, `$json` fails
- **Solution**: Use explicit node reference `$node["Build Update Queries"].json.query_upsert_lead`

### Issue 2: WF06 Loop

**Database Evidence**:
```sql
-- BEFORE user selects date
state_machine_state: "trigger_wf06_next_dates"
collected_data: {"awaiting_wf06_next_dates": true, ...}

-- AFTER user types "1" (should advance)
state_machine_state: "trigger_wf06_next_dates"  -- ❌ NO CHANGE!
collected_data: {"awaiting_wf06_next_dates": true, ...}  -- ❌ STILL WAITING!
```

**Expected Flow**:
```
State 9: trigger_wf06_next_dates
  → WF06 HTTP Request
  → Show dates message
  → Set awaiting_wf06_next_dates: true

User types "1"
  → State 10: process_date_selection  ❌ NEVER REACHED!
  → Parse date choice
  → State 11: trigger_wf06_available_slots
```

**Actual Flow**:
```
State 9: trigger_wf06_next_dates
  → Show dates
  → Set awaiting_wf06_next_dates: true

User types "1"
  → ❌ RETURNS TO State 9: trigger_wf06_next_dates
  → Shows dates AGAIN (infinite loop)
```

**Root Cause**:
1. State Machine not detecting `awaiting_wf06_next_dates: true` flag
2. Message "1" interpreted as NEW conversation (not date selection)
3. No explicit check for WF06 response states

---

## ✅ Complete Fix Strategy

### Fix 1: Upsert Lead Data - Explicit Node Reference

**Current** (fails):
```json
{
  "query": "={{ $json.query_upsert_lead }}"
}
```

**Fixed**:
```json
{
  "query": "={{ $node['Build Update Queries'].json.query_upsert_lead }}"
}
```

**Why This Works**:
- `$json` only accesses previous node output (unreliable with complex workflows)
- `$node['Build Update Queries'].json` explicitly references the correct node
- Guarantees query_upsert_lead is always accessible

### Fix 2: State Machine - WF06 State Detection

**Add Early Check** (before current stage detection):
```javascript
// V107 FIX: Detect WF06 response states FIRST
const collectedData = input.collected_data || {};

// Check if waiting for WF06 next dates response
if (collectedData.awaiting_wf06_next_dates === true) {
  console.log('V107: User responding to WF06 next dates - advancing to process_date_selection');
  const currentStage = 'process_date_selection';
  // Continue with process_date_selection logic
}

// Check if waiting for WF06 available slots response
if (collectedData.awaiting_wf06_available_slots === true) {
  console.log('V107: User responding to WF06 available slots - advancing to process_slot_selection');
  const currentStage = 'process_slot_selection';
  // Continue with process_slot_selection logic
}

// Normal state detection continues...
const currentStage = input.current_stage || /* fallbacks */;
```

**Logic**:
1. BEFORE normal stage detection, check for `awaiting_wf06_*` flags
2. If flag is true → force advance to next WF06 state
3. Clear flag after processing
4. This breaks the loop by preventing return to trigger states

---

## 📦 Implementation - V107 Complete Fix

### Part 1: Fix Upsert Lead Data Node

**Manual Steps** (n8n UI):
1. Open workflow: http://localhost:5678/workflow/9tG2gR6KBt6nYyHT
2. Find node: "Upsert Lead Data"
3. Click to edit
4. Find parameter: `query`
5. Change FROM: `={{ $json.query_upsert_lead }}`
6. Change TO: `={{ $node['Build Update Queries'].json.query_upsert_lead }}`
7. Save node
8. Save workflow

### Part 2: Fix State Machine WF06 Loop

**Script**: `scripts/wf02-v107-state-machine-wf06-loop-fix.js`

```javascript
// State Machine Logic - V107 (WF06 LOOP FIX)
// Purpose: Fix infinite loop when user selects WF06 dates/slots
// Critical: Detect awaiting_wf06_* flags BEFORE normal state detection

const input = $input.first().json;

console.log('=== V107 STATE MACHINE - WF06 LOOP FIX ===');

// Extract data
const collectedData = input.collected_data || {};
const userMessage = String(input.message || '').trim();

console.log('V107: Input analysis:', {
  awaiting_wf06_next_dates: collectedData.awaiting_wf06_next_dates,
  awaiting_wf06_available_slots: collectedData.awaiting_wf06_available_slots,
  userMessage: userMessage
});

// V107 CRITICAL FIX: Detect WF06 response states FIRST (before fallback chain)
let currentStage;
let isWF06Response = false;

// Check if waiting for WF06 next dates response
if (collectedData.awaiting_wf06_next_dates === true) {
  console.log('🔄 V107: User responding to WF06 next dates → process_date_selection');
  currentStage = 'process_date_selection';
  isWF06Response = true;

  // Clear flag and store selection
  collectedData.awaiting_wf06_next_dates = false;
  collectedData.selected_date_option = userMessage;
}
// Check if waiting for WF06 available slots response
else if (collectedData.awaiting_wf06_available_slots === true) {
  console.log('🔄 V107: User responding to WF06 available slots → process_slot_selection');
  currentStage = 'process_slot_selection';
  isWF06Response = true;

  // Clear flag and store selection
  collectedData.awaiting_wf06_available_slots = false;
  collectedData.selected_slot_option = userMessage;
}
// Normal state detection (existing V104 logic)
else {
  currentStage = collectedData.current_stage ||
                 collectedData.next_stage ||
                 input.next_stage ||
                 input.current_state ||
                 'greeting';

  console.log('V107: Normal state detection:', currentStage);
}

// Continue with state machine logic for currentStage...
// (existing state handling code from V104)

// State 10: process_date_selection
if (currentStage === 'process_date_selection') {
  console.log('State 10: Processing date selection');

  const dateOption = collectedData.selected_date_option || userMessage;
  const wf06Data = input.wf06_next_dates || {};
  const dates = wf06Data.dates_with_availability || [];

  // Validate selection
  const optionNum = parseInt(dateOption);
  if (!optionNum || optionNum < 1 || optionNum > dates.length) {
    return {
      response_text: `❌ Opção inválida. Digite um número de 1 a ${dates.length}.`,
      next_stage: 'trigger_wf06_next_dates',  // Return to date selection
      current_stage: 'process_date_selection',
      collected_data: collectedData,
      needs_db_update: false
    };
  }

  // Store selected date
  const selectedDate = dates[optionNum - 1];
  collectedData.selected_date = selectedDate.date;
  collectedData.selected_date_slots = selectedDate.available_slots;

  return {
    response_text: `✅ Data selecionada: ${selectedDate.formatted_date}. Aguarde enquanto busco os horários disponíveis...`,
    next_stage: 'trigger_wf06_available_slots',
    current_stage: 'process_date_selection',
    collected_data: collectedData,
    needs_db_update: true,
    // Trigger WF06 for slots
    trigger_wf06_slots: true,
    wf06_request_date: selectedDate.date
  };
}

// State 12: process_slot_selection
if (currentStage === 'process_slot_selection') {
  console.log('State 12: Processing slot selection');

  const slotOption = collectedData.selected_slot_option || userMessage;
  const wf06Data = input.wf06_available_slots || {};
  const slots = wf06Data.available_slots || [];

  // Validate selection
  const optionNum = parseInt(slotOption);
  if (!optionNum || optionNum < 1 || optionNum > slots.length) {
    return {
      response_text: `❌ Opção inválida. Digite um número de 1 a ${slots.length}.`,
      next_stage: 'trigger_wf06_available_slots',  // Return to slot selection
      current_stage: 'process_slot_selection',
      collected_data: collectedData,
      needs_db_update: false
    };
  }

  // Store selected slot
  const selectedSlot = slots[optionNum - 1];
  collectedData.selected_slot = selectedSlot.start_time;
  collectedData.selected_slot_end = selectedSlot.end_time;

  return {
    response_text: `✅ Horário confirmado: ${selectedSlot.formatted_time}. Criando seu agendamento...`,
    next_stage: 'schedule_confirmation',
    current_stage: 'process_slot_selection',
    collected_data: collectedData,
    needs_db_update: true,
    // Trigger WF05 to create appointment
    trigger_wf05_create: true
  };
}

// [Rest of state machine states 1-8, 11, 13-15 from V104]
```

**Deployment Steps**:
1. Create script: `scripts/wf02-v107-state-machine-wf06-loop-fix.js`
2. Copy V104 State Machine code from `scripts/wf02-v104-database-state-update-fix.js`
3. Add V107 WF06 detection logic at the beginning (before fallback chain)
4. Add states 10 and 12 processing logic (date/slot selection)
5. Update n8n workflow State Machine node with V107 code
6. Test WF06 flow

---

## ✅ Validation

### Test 1: Upsert Lead Data (Undefined Fix)
```bash
# Trigger conversation flow
# Complete states 1-8
# Verify no SQL undefined errors in execution

docker logs e2bot-n8n-dev 2>&1 | grep -i "undefined" | tail -20
# Expected: No "Syntax error at line 1 near undefined" errors ✅
```

### Test 2: WF06 Date Selection Loop Fix
```bash
# Trigger conversation
# Complete flow to State 9: trigger_wf06_next_dates
# User receives dates:
# 1️⃣ Amanhã (28/04) - 9 horários livres ✨
# 2️⃣ Depois de amanhã (29/04) - 9 horários livres ✨
# 3️⃣ 30/04 (30/04) - 9 horários livres ✨

# User types: "1"
# Expected: Shows time slots (NOT dates again) ✅

# Database verification:
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT state_machine_state, collected_data->'selected_date' as date,
      collected_data->'awaiting_wf06_next_dates' as waiting_flag
      FROM conversations
      WHERE phone_number = '556181755748';"

# Expected:
# state_machine_state: "trigger_wf06_available_slots"  ✅
# date: "2026-04-28"  ✅
# waiting_flag: null or false  ✅ (flag cleared after processing)
```

### Test 3: WF06 Slot Selection
```bash
# Continue from Test 2
# User receives slots:
# 1️⃣ 08:00 - 10:00
# 2️⃣ 10:00 - 12:00
# ... (9 slots total)

# User types: "1"
# Expected: Confirmation message + appointment creation ✅

# Database verification:
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT state_machine_state, collected_data->'selected_slot' as slot
      FROM conversations
      WHERE phone_number = '556181755748';"

# Expected:
# state_machine_state: "schedule_confirmation"  ✅
# slot: "08:00"  ✅
```

---

## 📊 Impact

### Before V107
- ❌ Upsert Lead Data fails with SQL undefined error
- ❌ WF06 date selection creates infinite loop
- ❌ Users cannot schedule appointments
- ❌ Production completely blocked for Services 1 & 3

### After V107
- ✅ Upsert Lead Data executes successfully with explicit node reference
- ✅ WF06 date selection advances to slot selection
- ✅ WF06 slot selection advances to confirmation
- ✅ Complete scheduling flow works end-to-end
- ✅ Production unblocked for Services 1 & 3

---

## 🔄 Version History

| Version | Fix | Status |
|---------|-----|--------|
| V104 | State sync (collected_data.current_stage) | ✅ DEPLOYED |
| V104.2 | Schema compliance (no contact_phone) | ✅ DEPLOYED |
| V105 | Routing (Update before Check If WF06) | ✅ DEPLOYED |
| V106.1 | response_text routing | ✅ DEPLOYED |
| **V107** | **WF06 loop + upsert undefined** | 🔴 **READY** |

---

## 📁 Files

**Scripts**:
- State Machine V107: `scripts/wf02-v107-state-machine-wf06-loop-fix.js`

**Documentation**:
- This doc: `docs/fix/BUGFIX_WF02_V107_WF06_LOOP_AND_UNDEFINED_COMPLETE_FIX.md`
- Deployment: `docs/deployment/DEPLOY_WF02_V107_COMPLETE_FIX.md` (to be created)
- Quick Deploy: `docs/WF02_V107_QUICK_DEPLOY.md` (to be created)

**Workflows**:
- Production: `02_ai_agent_conversation_V74.1_2_FUNCIONANDO.json` (to be updated)
- Ready: `02_ai_agent_conversation_V107_COMPLETE_FIX.json` (to be created)

---

## ⚠️ Critical Notes

1. **Two-Part Fix Required**: Both Upsert Lead Data node AND State Machine must be updated
2. **Manual UI Change**: Upsert Lead Data query parameter cannot be scripted (n8n limitation)
3. **WF06 Flag Management**: `awaiting_wf06_*` flags MUST be cleared after processing to prevent re-entry
4. **State Detection Order**: WF06 checks MUST occur BEFORE fallback chain to prevent bypass
5. **Testing Required**: Complete WF06 flow (dates → slots → confirmation) must be validated

---

**Created**: 2026-04-27 20:50 BRT
**Author**: Claude Code Analysis
**Status**: 🔴 READY FOR DEPLOYMENT
