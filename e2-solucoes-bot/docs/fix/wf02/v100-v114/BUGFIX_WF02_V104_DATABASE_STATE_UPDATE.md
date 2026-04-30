# BUGFIX WF02 V104 - Database State Not Updating After WF06

**Date**: 2026-04-27
**Workflow ID**: 9tG2gR6KBt6nYyHT
**Execution**: 8477
**Problem**: User stuck in infinite loop selecting dates - database state not updating after WF06
**Root Cause**: Build Update Queries node not receiving `current_stage` from State Machine output

---

## 🐛 PROBLEM ANALYSIS

### Observed Behavior
```
User sends "1" to select date → Bot sends same message again (infinite loop)

WhatsApp conversation:
[19:09] User: "1"
[19:09] Bot: "📅 Agendar Visita Técnica..." (shows dates)
[19:09] User: "1"
[19:09] Bot: "📅 Agendar Visita Técnica..." (SAME MESSAGE - LOOP!)
[19:09] User: "1"
[19:09] Bot: "📅 Agendar Visita Técnica..." (LOOP CONTINUES!)
```

### Database State (WRONG!)
```sql
state_machine_state: "confirmation"  ← STUCK HERE!
current_state: "coletando_dados"
```

### State Machine Output (CORRECT!)
```json
{
  "current_stage": "trigger_wf06_next_dates",  ✅
  "next_stage": "trigger_wf06_next_dates",     ✅
  "response_text": "⏳ Buscando próximas datas...",
  "collected_data": { ... }
}
```

### Root Cause

**Flow after confirmation "1"**:
```
1. State Machine → current_stage: "trigger_wf06_next_dates" ✅
2. Build Update Queries → SHOULD update database with new state ❌
3. WF06 HTTP Request → Get calendar dates ✅
4. Build WF06 Response → Show dates to user ✅
5. User sends "1" → Get Conversation Details reads from database
6. Database STILL has state_machine_state: "confirmation" ❌
7. State Machine thinks we're in confirmation → shows dates again
8. LOOP!
```

**The Issue**: Build Update Queries is receiving:
- `collected_data` with all user data ✅
- `phone_number` ✅
- But **NOT** receiving `current_stage` or `next_stage` ❌

So when it runs UPDATE query, it doesn't update `state_machine_state` column!

---

## ✅ SOLUTION V104 - Pass current_stage to Build Update Queries

### Fix 1: Update State Machine V101 Output

**Current V101 output** (line 460-495):
```javascript
const output = {
  response_text: responseText,
  conversation_id: input.conversation_id || input.id || input.currentData?.conversation_id || null,

  collected_data: {
    ...updateData,
    lead_name: updateData.lead_name || currentData.lead_name,
    // ... other fields
  },

  next_stage: nextStage,
  current_stage: nextStage,  // ← This is OUTPUT but not in collected_data!
  phone_number: input.phone_number || input.phone_with_code,
  previous_stage: currentStage,
  version: 'V101',
  timestamp: new Date().toISOString()
};
```

**Problem**: `current_stage` is at root level, but Build Update Queries might be looking for it in `collected_data`!

**Fix V104**:
```javascript
const output = {
  response_text: responseText,
  conversation_id: input.conversation_id || input.id || input.currentData?.conversation_id || null,

  collected_data: {
    ...updateData,

    // PRESERVE all existing data
    lead_name: updateData.lead_name || currentData.lead_name,
    email: updateData.email || currentData.email,
    phone_number: updateData.phone_number || currentData.phone_number,
    contact_phone: updateData.contact_phone || currentData.contact_phone,
    service_type: updateData.service_type || currentData.service_type,
    service_selected: updateData.service_selected || currentData.service_selected,
    city: updateData.city || currentData.city,

    // PRESERVE scheduling data
    scheduled_date: updateData.scheduled_date || currentData.scheduled_date,
    scheduled_date_display: updateData.scheduled_date_display || currentData.scheduled_date_display,
    scheduled_time: updateData.scheduled_time || currentData.scheduled_time,
    scheduled_time_display: updateData.scheduled_time_display || currentData.scheduled_time_display,
    scheduled_end_time: updateData.scheduled_end_time || currentData.scheduled_end_time,

    // PRESERVE suggestions
    date_suggestions: updateData.date_suggestions || currentData.date_suggestions,
    slot_suggestions: updateData.slot_suggestions || currentData.slot_suggestions,

    // V104 FIX: CRITICAL - Include state information in collected_data
    current_stage: nextStage,
    next_stage: nextStage,
    previous_stage: currentStage
  },

  // V104: ALSO keep at root level for compatibility
  next_stage: nextStage,
  current_stage: nextStage,
  phone_number: input.phone_number || input.phone_with_code,
  previous_stage: currentStage,
  version: 'V104',
  timestamp: new Date().toISOString()
};
```

### Fix 2: Verify Build Update Queries SQL

**Check if Build Update Queries** is using `current_stage` in UPDATE:

```sql
UPDATE conversations
SET
  state_machine_state = $1,  -- ← Should be {{ $json.current_stage }} or {{ $json.collected_data.current_stage }}
  current_state = $2,
  collected_data = $3,
  ...
WHERE phone_number = $N;
```

**Need to verify**: What field name is Build Update Queries using for state?

---

## 🔧 IMPLEMENTATION STEPS

### Step 1: Update State Machine V101 → V104

1. Open workflow: http://localhost:5678/workflow/9tG2gR6KBt6nYyHT
2. Click on node: **"State Machine Logic"**
3. Find lines 465-487 (collected_data object)
4. Add after `slot_suggestions` line:

```javascript
    // V104 FIX: CRITICAL - Include state information in collected_data
    current_stage: nextStage,
    next_stage: nextStage,
    previous_stage: currentStage
```

5. Change version line from `'V101'` to `'V104'`
6. Click **Save**

### Step 2: Check Build Update Queries Node

1. Click on node: **"Build Update Queries"**
2. Check **Parameters** → SQL Query
3. Verify UPDATE statement has:
   ```sql
   state_machine_state = {{ $json.current_stage }} OR
   state_machine_state = {{ $json.collected_data.current_stage }} OR
   state_machine_state = {{ $json.next_stage }}
   ```

### Step 3: Test Complete Flow

```bash
# Send WhatsApp: "oi" → go through full flow
# At confirmation: "1" (agendar)

# Wait for dates to appear
# Send: "1" (select first date)

# Expected:
# ✅ Should trigger WF06 available_slots
# ✅ Should show time slots, NOT dates again
# ❌ Should NOT loop on dates
```

### Step 4: Verify Database Update

```bash
# After selecting date "1"
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT state_machine_state, current_state FROM conversations WHERE phone_number = '556181755748';"

# Expected:
# state_machine_state: "process_date_selection"  ✅ (or trigger_wf06_available_slots)
# ❌ Should NOT be "confirmation"
```

---

## 📊 VALIDATION

### Test 1: Normal Date Selection
```
User: "oi" → complete flow → "1" (agendar)
Expected: Shows 3 dates ✅

User: "1" (select date 1)
Expected:
  ✅ Database updates: state_machine_state = "process_date_selection" or "trigger_wf06_available_slots"
  ✅ Shows time slots for selected date
  ❌ Should NOT show dates again
```

### Test 2: Invalid Date Selection
```
User selects date → sends "4" (invalid option)
Expected:
  ✅ "❌ Opção inválida - Escolha 1-3"
  ✅ Stays in process_date_selection state
```

### Test 3: Custom Date Entry
```
User sends "28/04/2026" instead of 1-3
Expected:
  ✅ Validates date
  ✅ Triggers WF06 available_slots
  ✅ Shows time slots
```

---

## 🚨 CRITICAL DISCOVERY

**The loop happens because**:
1. State Machine outputs `current_stage: "trigger_wf06_next_dates"` ✅
2. But this is at ROOT level, not in `collected_data`
3. Build Update Queries might only read from `collected_data` or `$json.current_stage`
4. Database UPDATE doesn't include new state
5. Next message → Get Conversation Details reads OLD state from database
6. State Machine processes OLD state again → LOOP!

**Solution**: Put `current_stage`, `next_stage`, `previous_stage` INSIDE `collected_data` object so Build Update Queries can access it!

---

**Status**: Solution identified - add state fields to collected_data object
**Priority**: CRITICAL - blocks all WF06 calendar selection
**Deployment**: Quick code change in State Machine node
