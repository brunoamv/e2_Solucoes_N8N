# WF02 V107 Quick Deploy - WF06 Loop + Upsert Undefined Fix

**Date**: 2026-04-27
**Status**: 🔴 READY FOR DEPLOYMENT
**Critical**: Production Blocking - Fix MUST be deployed immediately

---

## ⚡ What V107 Fixes

1. **SQL "undefined" Error**: Upsert Lead Data fails with `Syntax error at line 1 near "undefined"`
2. **WF06 Date Loop**: User selects "1" for date but gets SAME dates again (infinite loop)

---

## 📦 Deployment (15 minutes)

### Part 1: Fix Upsert Lead Data Node (5 minutes)

**Manual Steps** (n8n UI required):

1. Open: http://localhost:5678/workflow/9tG2gR6KBt6nYyHT
2. Find node: "Upsert Lead Data"
3. Click edit
4. Find parameter: `query`
5. Change FROM:
   ```
   ={{ $json.query_upsert_lead }}
   ```
6. Change TO:
   ```
   ={{ $node['Build Update Queries'].json.query_upsert_lead }}
   ```
7. Save node
8. Save workflow

**Why This Works**:
- `$json` only accesses previous node (unreliable)
- `$node['Build Update Queries'].json` explicitly references correct node
- Guarantees query_upsert_lead is always accessible

---

### Part 2: Fix State Machine WF06 Loop (10 minutes)

**The Problem**:
```
Database State: awaiting_wf06_next_dates = true
User types: "1"
Expected: process_date_selection (show slots)
Actual: trigger_wf06_next_dates AGAIN (infinite loop) ❌
```

**The Solution** - Add EARLY detection BEFORE state resolution:

Open n8n workflow:
1. http://localhost:5678/workflow/9tG2gR6KBt6nYyHT
2. Find node with State Machine code
3. Find this section (around line 77-82):

```javascript
// V100: State resolution with preservation
const currentStage = input.current_stage ||
                     input.next_stage ||
                     input.currentData?.current_stage ||
                     input.currentData?.next_stage ||
                     'greeting';
```

4. **INSERT BEFORE** that section (CRITICAL - must be BEFORE state resolution):

```javascript
// ===================================================
// V107 CRITICAL FIX: WF06 LOOP PREVENTION
// ===================================================
// Detect awaiting_wf06_* flags BEFORE state resolution to break infinite loop
let forcedStage = null;

// Check if user is responding to WF06 next dates
if (currentData.awaiting_wf06_next_dates === true) {
  console.log('🔄 V107: User responding to WF06 dates → FORCE process_date_selection');
  forcedStage = 'process_date_selection';

  // Clear flag to prevent re-entry
  currentData.awaiting_wf06_next_dates = false;
}
// Check if user is responding to WF06 available slots
else if (currentData.awaiting_wf06_available_slots === true) {
  console.log('🔄 V107: User responding to WF06 slots → FORCE process_slot_selection');
  forcedStage = 'process_slot_selection';

  // Clear flag to prevent re-entry
  currentData.awaiting_wf06_available_slots = false;
}

// V100: State resolution with preservation (V107: use forcedStage if set)
const currentStage = forcedStage ||
                     input.current_stage ||
                     input.next_stage ||
                     input.currentData?.current_stage ||
                     input.currentData?.next_stage ||
                     'greeting';
```

5. Find this line (around line 885):

```javascript
  version: 'V104',  // V104: Database state update fix
```

6. Change to:

```javascript
  version: 'V107',  // V107: WF06 loop fix + upsert undefined fix
```

7. Save node
8. Save workflow

---

## ✅ Validation

### Test 1: Upsert Lead Data (Undefined Fix)
```bash
# Complete conversation flow (states 1-8)
# Expected: No SQL errors in logs

docker logs e2bot-n8n-dev 2>&1 | grep -i "undefined" | tail -10
# Should see: NO "Syntax error at line 1 near undefined" ✅
```

### Test 2: WF06 Date Selection Loop Fix
```bash
# Start conversation
# Complete states 1-8
# At state 8 (confirmation): Type "1" (agendar)
# System shows dates:
# 1️⃣ Amanhã (28/04) - 9 horários livres ✨
# 2️⃣ Depois de amanhã (29/04) - 9 horários livres ✨
# 3️⃣ 30/04 (30/04) - 9 horários livres ✨
#
# Type: "1"
#
# Expected: Shows TIME SLOTS (NOT dates again) ✅
# 🕐 Horários Disponíveis - Amanhã (28/04)
# 1️⃣ 08:00 - 10:00 ✅
# 2️⃣ 10:00 - 12:00 ✅
# ...

# Database verification:
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT state_machine_state, collected_data->'awaiting_wf06_next_dates' as flag
      FROM conversations
      WHERE phone_number = '556181755748';"

# Expected:
# state_machine_state: "trigger_wf06_available_slots"  ✅
# flag: null or "false"  ✅ (cleared after processing)
```

### Test 3: WF06 Slot Selection
```bash
# Continue from Test 2
# Type: "1" (select first slot)
#
# Expected: Confirmation message ✅
# ✅ Agendamento Confirmado!
# 👤 Cliente: [name]
# ...
```

---

## 🔍 How V107 Works

### Before V107
```
User types "1" →
State Machine reads: input.current_stage = "trigger_wf06_next_dates" →
Database: awaiting_wf06_next_dates = true (ignored!) ❌ →
State remains: "trigger_wf06_next_dates" →
Shows dates AGAIN (infinite loop) ❌
```

### After V107
```
User types "1" →
State Machine checks: collected_data.awaiting_wf06_next_dates = true? YES! ✅ →
FORCE currentStage = "process_date_selection" ✅ →
Clear flag: awaiting_wf06_next_dates = false ✅ →
Process date selection →
Shows time slots ✅
```

---

## 📊 Impact

### Before V107
- ❌ Upsert Lead Data fails with SQL undefined
- ❌ WF06 date selection creates infinite loop
- ❌ Users cannot complete scheduling
- ❌ Production blocked for Services 1 & 3

### After V107
- ✅ Upsert Lead Data executes successfully
- ✅ WF06 date selection advances to slots
- ✅ WF06 slot selection advances to confirmation
- ✅ Complete scheduling flow works end-to-end
- ✅ Production unblocked

---

## 📁 Files

**Documentation**:
- Quick Deploy: `docs/WF02_V107_QUICK_DEPLOY.md` (this file)
- Bug Report: `docs/fix/BUGFIX_WF02_V107_WF06_LOOP_AND_UNDEFINED_COMPLETE_FIX.md`

**Workflows**:
- Production: `02_ai_agent_conversation_V74.1_2_FUNCIONANDO.json` (UPDATE THIS)
- Version marker: Change `version: 'V104'` to `version: 'V107'` in code

---

## ⚠️ Critical Notes

1. **Two-Part Fix Required**: BOTH Upsert Lead Data AND State Machine must be updated
2. **Order Matters**: V107 WF06 detection MUST be BEFORE state resolution (not after)
3. **Flag Management**: `awaiting_wf06_*` flags MUST be cleared to prevent re-entry
4. **Manual UI Changes**: Both fixes require n8n UI changes (no script deployment)
5. **Testing Required**: Complete WF06 flow validation (dates → slots → confirmation)

---

**Deployed**: TBD
**Version**: V107
**Author**: Claude Code Analysis
**Status**: 🔴 READY FOR IMMEDIATE DEPLOYMENT
