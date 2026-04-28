# BUGFIX WF02 V100 - WF06 Return Switch Execution

**Problem**: State Machine processes `switch (currentStage)` AFTER auto-correcting state when WF06 response detected, causing it to execute greeting state and lose user data.

**Root Cause**: Condition at line 159 allows switch execution when `hasWF06Response = true` AND `currentStage !== 'show_available_dates'`.

---

## 🐛 BUG ANALYSIS

### Evidence from Logs

**Execution 8174** (20:14:37):
```
V100: conversation_id: NULL  ❌
V100: Current stage: greeting  ❌
V100: User message:   ❌ (empty!)
V100: Input keys: [ 'success', 'action', 'dates', 'total_available', 'wf06_next_dates' ]  ✅
V100: Has WF06 response: true  ✅
V100: Has next_dates data  ✅
V100: AUTO-CORRECTING state to show_available_dates  ✅
V100: Processing GREETING state  ❌ BUG!
```

### Code Flow Analysis

**Lines 134-144** - WF06 Auto-Correction:
```javascript
if (hasWF06Response) {
  if (hasWF06NextDates && currentStage !== 'show_available_dates') {
    console.log('V100: AUTO-CORRECTING state to show_available_dates');
    nextStage = 'show_available_dates';

    // Build responseText with WF06 dates
    responseText = `📅 *Agendar Visita Técnica...*`;
    updateData.date_suggestions = nextDatesResponse.dates;
    nextStage = 'process_date_selection';  // ✅ Correct nextStage set
  }
}
```

**Line 159** - Switch Execution Condition:
```javascript
else if (!hasWF06Response || (currentStage !== 'show_available_dates' && currentStage !== 'show_available_slots')) {
  switch (currentStage) {
    case 'greeting':  // ❌ This gets executed!
      responseText = `🤖 *Olá! Bem-vindo à E2 Soluções!*...`;
      nextStage = 'service_selection';  // ❌ OVERWRITES correct nextStage!
```

**Why it fails**:
1. `currentStage = 'greeting'` (from empty state)
2. `hasWF06Response = true`
3. Auto-correction sets `nextStage = 'process_date_selection'` ✅
4. Auto-correction sets `responseText = "📅 dates..."` ✅
5. Condition: `!true OR ('greeting' !== 'show_available_dates' AND 'greeting' !== 'show_available_slots')`
6. Result: `false OR (true AND true)` = `false OR true` = **TRUE**
7. **Enters switch** → executes `case 'greeting'` ❌
8. **OVERWRITES** `responseText` with greeting message ❌
9. **OVERWRITES** `nextStage` with `'service_selection'` ❌

### Database Impact

**Merge Node Output** (CORRECT):
```json
{
  "success": true,
  "action": "next_dates",
  "dates": [...],  // ✅ WF06 data preserved
  "phone_number": "556181755748",  // ✅ User data from Get Conversation Details
  "conversation_id": "5aa8191d-b8f4-4ff2-a644-76851e88fcb8",  // ✅
  "collected_data": {...},  // ✅ All user data
  "wf06_next_dates": [...]  // ✅ From Prepare WF06 node
}
```

**State Machine Input currentData** (BUG - Empty!):
```javascript
currentData = {
  ...(input.currentData || {}),  // ❌ input.currentData = undefined
  ...(input.collected_data || {}),  // ❌ input.collected_data = undefined

  // All fields undefined:
  lead_name: undefined,
  phone_number: undefined,
  // ...
}
```

**Why currentData is empty**:
- Merge node output has `phone_number`, `conversation_id`, etc. at **root level**
- State Machine expects them in `input.currentData` or `input.collected_data` **nested properties**
- Since nested properties don't exist, all currentData fields become `undefined`

---

## ✅ SOLUTION V101

### Fix 1: Skip Switch When WF06 Auto-Correction Applied

**Change Line 159**:

**BEFORE (V100)**:
```javascript
else if (!hasWF06Response || (currentStage !== 'show_available_dates' && currentStage !== 'show_available_slots')) {
  switch (currentStage) {
    // ... states
  }
}
```

**AFTER (V101)**:
```javascript
// V101 FIX: Track if we already handled WF06 response in auto-correction
let wf06HandledByAutoCorrection = false;

// V101: Auto-correct state if we have WF06 response but wrong state
if (hasWF06Response) {
  if (hasWF06NextDates && currentStage !== 'show_available_dates') {
    console.log('V101: AUTO-CORRECTING state to show_available_dates');
    // ... build response
    wf06HandledByAutoCorrection = true;  // ✅ Mark as handled
  } else if (hasWF06Slots && currentStage !== 'show_available_slots') {
    console.log('V101: AUTO-CORRECTING state to show_available_slots');
    // ... build response
    wf06HandledByAutoCorrection = true;  // ✅ Mark as handled
  }
}

// V101 FIX: Only enter switch if NOT handled by auto-correction
if (!wf06HandledByAutoCorrection && !isIntermediateState) {
  switch (currentStage) {
    // ... states
  }
}
```

### Fix 2: Preserve User Data from Merge Node

**Problem**: `input.currentData` and `input.collected_data` are undefined because Merge node puts data at root level.

**Solution**: Add root-level fallbacks in currentData merge (Line 45-71):

**BEFORE (V100)**:
```javascript
const currentData = {
  ...(input.currentData || {}),
  ...(input.collected_data || {}),

  lead_name: input.lead_name || input.currentData?.lead_name || input.collected_data?.lead_name,
  // ...
};
```

**AFTER (V101)**:
```javascript
const currentData = {
  ...(input.currentData || {}),
  ...(input.collected_data || {}),

  // V101 FIX: Also check root level (Merge node puts data there!)
  lead_name: input.lead_name || input.currentData?.lead_name || input.collected_data?.lead_name || input.contact_name,
  email: input.email || input.currentData?.email || input.collected_data?.email || input.contact_email,
  phone_number: input.phone_number || input.currentData?.phone_number || input.collected_data?.phone_number || input.phone_with_code,
  // ... add root fallbacks for all fields
};
```

---

## 🚀 DEPLOYMENT V101

### 1. Generate V101 State Machine

```bash
# Apply V101 fixes to V100 code
# 1. Add wf06HandledByAutoCorrection tracking
# 2. Skip switch when WF06 handled by auto-correction
# 3. Add root-level fallbacks in currentData merge
```

### 2. Update Workflow

```bash
# Open n8n workflow
http://localhost:5678/workflow/QeNgH4gCvF5HSE51

# Node: "State Machine Logic" Function
# Action:
#   1. DELETE all existing V100 code
#   2. PASTE V101 code
#   3. Save workflow

# Verify node name updated to "State Machine Logic V101"
```

### 3. Test Complete Flow

```bash
# Test conversation from confirmation through WF06 return:
# 1. Complete data collection (name, phone, email, city)
# 2. Confirmation state → select "1" (agendar)
# 3. State Machine → trigger_wf06_next_dates
# 4. WF06 HTTP Request → returns dates
# 5. Merge node → combines WF06 + user data ✅
# 6. State Machine receives merged data → should NOT process greeting ✅
# 7. State Machine should display WF06 dates ✅
# 8. User should see 3 available dates ✅

# Expected logs:
# V101: Has WF06 response: true
# V101: AUTO-CORRECTING state to show_available_dates
# V101: WF06 handled by auto-correction, skipping switch
# V101: Preserved lead_name: bruno rosa
# V101: Preserved phone_number: 556181755748
# V101: Output next_stage: process_date_selection
```

### 4. Validate Database

```bash
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT phone_number, collected_data, current_state, state_machine_state
      FROM conversations
      WHERE phone_number = '556181755748';"

# Expected result:
# phone_number: 556181755748  ✅
# collected_data: {all user data}  ✅
# state_machine_state: process_date_selection  ✅ (NOT greeting!)
```

---

## 📊 EXPECTED BEHAVIOR

### Before V101 (BROKEN)

```
User confirms → trigger_wf06_next_dates → WF06 returns dates
→ Merge combines data ✅
→ State Machine receives:
  - hasWF06Response = true ✅
  - currentData = {} (empty) ❌
  - currentStage = 'greeting' ❌
→ Auto-correction sets nextStage = 'process_date_selection' ✅
→ Auto-correction sets responseText = "📅 dates..." ✅
→ ENTERS SWITCH (BUG!) ❌
→ Executes case 'greeting' ❌
→ OVERWRITES nextStage = 'service_selection' ❌
→ OVERWRITES responseText = "🤖 Olá! Bem-vindo..." ❌
→ User sees greeting (WRONG!) ❌
```

### After V101 (FIXED)

```
User confirms → trigger_wf06_next_dates → WF06 returns dates
→ Merge combines data ✅
→ State Machine receives:
  - hasWF06Response = true ✅
  - currentData from root fallbacks = {all user data} ✅
  - currentStage = 'greeting' (OK, will be corrected)
→ Auto-correction sets nextStage = 'process_date_selection' ✅
→ Auto-correction sets responseText = "📅 dates..." ✅
→ wf06HandledByAutoCorrection = true ✅
→ SKIPS SWITCH (FIX!) ✅
→ nextStage preserved = 'process_date_selection' ✅
→ responseText preserved = "📅 dates..." ✅
→ User sees available dates (CORRECT!) ✅
```

---

## 🔗 RELATED ISSUES

- **V100**: Field name mismatch (`update_data` vs `collected_data`) ✅ FIXED
- **V101**: Switch execution after WF06 auto-correction + root-level data fallbacks ← THIS FIX

---

**Date**: 2026-04-27
**Version**: V101 WF06 Switch Execution Fix
**Impact**: CRITICAL - Prevents WF06 integration from working, causes state reset to greeting
**Status**: Fix identified, ready for implementation
