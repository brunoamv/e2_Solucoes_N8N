# WF02 V113 - Missing State Update After WF06 Quick Deploy

**Version**: V113 WF06 State Update Fix
**Fix**: Add database UPDATE nodes after showing WF06 responses
**Time**: ~15 minutes deployment + 10 minutes testing
**Status**: 🔴 CRITICAL FIX

---

## 🎯 What V113 Fixes

**Problem**: User sees dates from WF06 successfully, but when they select a date, they receive error "Ops! Algo deu errado..."

**Root Cause**: After showing WF06 dates, workflow ENDS without updating database to `show_available_dates`. When user sends next message, State Machine still sees `trigger_wf06_next_dates` (trigger state) instead of `show_available_dates` (response state).

**Solution**: Add database UPDATE nodes after showing WF06 responses to properly set state for next user message.

---

## 🚀 Quick Deploy (15 minutes)

### Part 1: WF06 Next Dates Flow

#### Step 1: Add "Build Update Queries1" Code Node

1. Open workflow: http://localhost:5678/workflow/9tG2gR6KBt6nYyHT
2. Find "Send WhatsApp Response1" node
3. Add new **Code** node after it
4. Name: **"Build Update Queries1"**
5. Paste code from: `scripts/wf02-v113-build-update-queries1-wf06-next-dates.js`

**Key Code Section**:
```javascript
// Get phone number AND date_suggestions from explicit node reference
const responseData = $node["Build WF06 NEXT DATE Response Message"].json;
const phone_number = responseData.phone_number;
const date_suggestions = responseData.date_suggestions || [];

// Serialize date_suggestions for PostgreSQL JSONB
const dateSuggestionsJson = JSON.stringify(date_suggestions).replace(/'/g, "''");

// Build UPDATE query - ✅ CRITICAL: Saves date_suggestions to database!
const update_query = `
UPDATE conversations
SET
  state_machine_state = 'show_available_dates',
  collected_data = jsonb_set(
    jsonb_set(
      jsonb_set(
        collected_data,
        '{current_stage}',
        '"show_available_dates"'
      ),
      '{awaiting_wf06_next_dates}',
      'true'
    ),
    '{date_suggestions}',
    '${dateSuggestionsJson}'::jsonb
  ),
  updated_at = NOW()
WHERE phone_number = '${phone_number.replace(/'/g, "''")}'
RETURNING *;
`.trim();

return [{
  json: {
    update_query: update_query,
    phone_number: phone_number,
    state_update_type: 'wf06_next_dates_shown',
    target_state: 'show_available_dates'
  }
}];
```

6. Save node

#### Step 2: Add "Update Conversation State1" PostgreSQL Node

1. Add new **PostgreSQL** node after "Build Update Queries1"
2. Name: **"Update Conversation State1"**
3. Operation: **Execute Query**
4. Query: `={{ $json.update_query }}`
5. Save node

#### Step 3: Update Connections

**Current**:
```
Send WhatsApp Response1 → [workflow ends]
```

**New**:
```
Send WhatsApp Response1 → Build Update Queries1 → Update Conversation State1 → [workflow ends]
```

1. Connect: Send WhatsApp Response1 → Build Update Queries1
2. Connect: Build Update Queries1 → Update Conversation State1
3. Save workflow

---

### Part 2: WF06 Available Slots Flow (Same Pattern)

#### Step 4: Add "Build Update Queries2" Code Node

1. Find "Send WhatsApp Response2" node (slots flow)
2. Add new **Code** node after it
3. Name: **"Build Update Queries2"**
4. Paste code from: `scripts/wf02-v113-build-update-queries2-wf06-available-slots.js`

**Key Difference**: Uses `show_available_slots` state and `awaiting_wf06_available_slots` flag

5. Save node

#### Step 5: Add "Update Conversation State2" PostgreSQL Node

1. Add new **PostgreSQL** node after "Build Update Queries2"
2. Name: **"Update Conversation State2"**
3. Operation: **Execute Query**
4. Query: `={{ $json.update_query }}`
5. Save node

#### Step 6: Update Connections

**New Flow**:
```
Send WhatsApp Response2 → Build Update Queries2 → Update Conversation State2 → [workflow ends]
```

1. Connect: Send WhatsApp Response2 → Build Update Queries2
2. Connect: Build Update Queries2 → Update Conversation State2
3. Save workflow

---

## ✅ Validation (10 minutes)

### Test 1: Complete WF06 Next Dates Flow

```bash
# User conversation:
# 1. "oi" → greeting
# 2. "1" → Solar service
# 3. "Test Name"
# 4. "1" → confirm phone
# 5. "test@email.com"
# 6. "Goiânia-GO"
# 7. "1" → agendar (triggers WF06 next dates)

# Expected: Bot shows 3 dates ✅

# Check database was updated:
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT phone_number, state_machine_state,
             collected_data->'current_stage' as stage,
             collected_data->'awaiting_wf06_next_dates' as awaiting
      FROM conversations
      WHERE phone_number = '556181755748';"

# Expected:
# state_machine_state: show_available_dates  ✅
# stage: "show_available_dates"  ✅
# awaiting: true  ✅

# 8. User types "1" (selects first date)
# Expected: Bot shows time slots ✅ (NOT error!)
```

### Test 2: Complete WF06 Available Slots Flow

```bash
# Continue from Test 1, after user selects date "1"

# Expected: Bot shows time slots ✅

# Check database was updated:
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT phone_number, state_machine_state,
             collected_data->'current_stage' as stage,
             collected_data->'awaiting_wf06_available_slots' as awaiting
      FROM conversations
      WHERE phone_number = '556181755748';"

# Expected:
# state_machine_state: show_available_slots  ✅
# stage: "show_available_slots"  ✅
# awaiting: true  ✅

# User types "1" (selects first slot)
# Expected: Bot confirms appointment ✅
```

### Test 3: Verify Logs

```bash
docker logs -f e2bot-n8n-dev 2>&1 | grep -E "V113|Build Update Queries"
```

**Expected**:
```
=== Build Update Queries1 (V113) ===
Phone number: 556181755748
Setting state to: show_available_dates
Setting awaiting_wf06_next_dates: true
Data source: Build WF06 NEXT DATE Response Message node

=== Build Update Queries2 (V113) ===
Phone number: 556181755748
Setting state to: show_available_slots
Setting awaiting_wf06_available_slots: true
Data source: Build WF06 Available SLOTS Response Message node
```

---

## 🔄 Rollback Procedure

If V113 causes unexpected issues:

1. Open workflow: http://localhost:5678/workflow/9tG2gR6KBt6nYyHT
2. Delete "Build Update Queries1" node
3. Delete "Update Conversation State1" node
4. Delete "Build Update Queries2" node
5. Delete "Update Conversation State2" node
6. Save workflow

**Note**: Rollback returns to buggy state where dates show but selection fails.

---

## 📁 Related Documentation

- **Complete Analysis**: `docs/fix/BUGFIX_WF02_V113_WF06_STATE_UPDATE_MISSING.md`
- **V113 Code - Next Dates**: `scripts/wf02-v113-build-update-queries1-wf06-next-dates.js`
- **V113 Code - Available Slots**: `scripts/wf02-v113-build-update-queries2-wf06-available-slots.js`
- **Previous Investigation**: `docs/fix/BUGFIX_WF02_V112_WF06_RESPONSE_RACE_CONDITION.md`
- **Active Workflow**: `/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/wk02_v102_1.json`

---

**Created**: 2026-04-28
**Status**: ✅ READY FOR DEPLOYMENT
**Risk Level**: LOW (Simple SQL UPDATE with known state values)
**Estimated Time**: 15 minutes deployment + 10 minutes testing
**Impact**: Fixes WF06 date/slot selection errors completely
