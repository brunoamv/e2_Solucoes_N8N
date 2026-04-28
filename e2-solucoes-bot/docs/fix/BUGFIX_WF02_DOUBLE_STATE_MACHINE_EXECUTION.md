# BUGFIX WF02 - Double State Machine Execution

**Date**: 2026-04-27
**Workflow ID**: QeNgH4gCvF5HSE51
**Execution**: 8222
**Problem**: State Machine executes TWICE - first with data, second WITHOUT data (greeting reset)

---

## 🐛 PROBLEM ANALYSIS

### Evidence from Execution 8222

**Execution Flow**:
```
20:41:14.331 - State Machine (RUN 1) ✅
  Input: Process Existing User Data V57
  conversation_id: 79f6d5da-62f7-4a2e-8aac-e96d19cb1e2f
  Current stage: confirmation
  Output: trigger_wf06_next_dates

20:41:19.099 - State Machine (RUN 2) ❌
  Input: Merge WF06 Next Dates with User Data
  conversation_id: NULL
  Current stage: greeting
  Output: greeting message (WRONG!)
```

### Root Cause

The workflow has **TWO paths** to State Machine:

**Path 1 (CORRECT)**:
```
Process Existing User Data V57 → State Machine Logic
✅ Has conversation_id
✅ Has collected_data
✅ Correct state execution
```

**Path 2 (BUG - DUPLICATE EXECUTION)**:
```
Merge WF06 Next Dates with User Data → State Machine Logic
❌ NO conversation_id
❌ NO collected_data
❌ Triggers GREETING state (resets conversation!)
```

### Why It Happens

1. State Machine (RUN 1) executes correctly, outputs `trigger_wf06_next_dates`
2. Build Update Queries processes the output
3. WF06 HTTP Request fetches calendar data
4. **Prepare WF06 Next Dates Data** processes WF06 response
5. **Merge WF06 Next Dates with User Data** merges WF06 + user data
6. **BUG**: Merge node connects DIRECTLY to State Machine
7. State Machine (RUN 2) executes with EMPTY input:
   - `conversation_id`: NULL (Merge doesn't have it)
   - `collected_data`: {} (Merge doesn't preserve it)
   - `current_stage`: defaults to 'greeting'
8. Result: Greeting message sent INSTEAD of WF06 dates!

---

## ✅ SOLUTION

### Fix 1: Remove Direct Connection from Merge to State Machine

**Problem**: `Merge WF06 Next Dates with User Data` → `State Machine Logic` (WRONG!)

**Solution**: Merge should NOT connect directly to State Machine.

**Correct Flow**:
```
State Machine → Build Update Queries → Check If WF06 Next Dates
  → TRUE: HTTP Request → Prepare WF06 → Merge WF06 → **STOP HERE**
  → FALSE: Continue normal flow
```

The Merge node should ONLY prepare data for the **next user message**, not trigger immediate State Machine execution.

### Fix 2: WF06 Return Flow Should Wait for User Input

**Current (BROKEN)**:
```
User confirms → State Machine → trigger_wf06_next_dates
→ WF06 HTTP Request → Merge data → State Machine (IMMEDIATE) ❌
```

**Correct Flow**:
```
User confirms → State Machine → trigger_wf06_next_dates
→ WF06 HTTP Request → Prepare data → **Send to WhatsApp** ✅
→ **WAIT for user selection** → State Machine (with user choice)
```

---

## 🔧 IMPLEMENTATION STEPS

### Step 1: Export Current Production Workflow

```bash
# Access n8n UI
http://localhost:5678/workflow/QeNgH4gCvF5HSE51

# Export workflow JSON
# Menu → Download → Save as: 02_ai_agent_conversation_V99_CURRENT_PRODUCTION.json
```

### Step 2: Remove Incorrect Connection

**In n8n UI**:
1. Open workflow `QeNgH4gCvF5HSE51`
2. Find node: **"Merge WF06 Next Dates with User Data"**
3. **DELETE connection** from Merge → State Machine Logic
4. Save workflow

### Step 3: Add Correct Flow - Send WF06 Response Directly

**New Flow**:
```
Merge WF06 Next Dates with User Data
  → Build WF06 Response Message (NEW Function node)
  → Send WhatsApp Response
  → STOP (wait for user input)
```

**New Function Node: "Build WF06 Response Message"**:
```javascript
// Process WF06 next_dates response and build WhatsApp message
const input = $input.first().json;
const dates = input.wf06_next_dates || [];

if (!dates || dates.length === 0) {
  return {
    json: {
      phone_number: input.phone_number,
      response_text: '⚠️ Não encontramos horários disponíveis. Entre em contato: (62) 3092-2900'
    }
  };
}

// Build date options
let dateOptions = '';
dates.forEach((dateObj, index) => {
  const number = index + 1;
  const qualityEmoji = dateObj.quality === 'high' ? '✨' :
                      dateObj.quality === 'medium' ? '📅' : '⚠️';
  dateOptions += `${number}️⃣ *${dateObj.display}*\n   🕐 ${dateObj.total_slots} horários livres ${qualityEmoji}\n\n`;
});

const responseText = `📅 *Agendar Visita Técnica*\n\n` +
                    `📆 *Próximas datas disponíveis:*\n\n` +
                    dateOptions +
                    `💡 *Escolha uma opção (1-3)*\n` +
                    `_Digite o número da data desejada_`;

return {
  json: {
    phone_number: input.phone_number,
    response_text: responseText,
    date_suggestions: dates
  }
};
```

### Step 4: Similar Fix for WF06 Available Slots

Apply same pattern for **"Merge WF06 Available Slots with User Data"**:
- Remove connection to State Machine
- Add "Build WF06 Slots Response Message" function
- Connect to Send WhatsApp Response

---

## 📊 EXPECTED BEHAVIOR

### Before Fix (BROKEN)

```
User: "1" (confirm)
→ State Machine: trigger_wf06_next_dates ✅
→ WF06 returns dates ✅
→ Merge WF06 data ✅
→ State Machine EXECUTES AGAIN (BUG!) ❌
→ State Machine sees: conversation_id=NULL, stage=greeting
→ User receives: GREETING MESSAGE ❌ (WRONG!)
```

### After Fix (CORRECT)

```
User: "1" (confirm)
→ State Machine: trigger_wf06_next_dates ✅
→ WF06 returns dates ✅
→ Merge WF06 data ✅
→ Build WF06 Response ✅
→ Send WhatsApp: "📅 Choose date 1-3" ✅
→ WAIT for user response ✅
→ User: "1" (selects date)
→ State Machine: process_date_selection ✅
```

---

## 🚨 CRITICAL IMPACT

**Severity**: CRITICAL
**Scope**: ALL WF06 calendar scheduling flows (Services 1 & 3)
**User Impact**: Users see GREETING instead of available dates
**Business Impact**: Cannot schedule appointments, complete conversation loss

---

## 🔗 RELATED ISSUES

- **V100**: Collected data field name fix ✅ DEPLOYED
- **V101**: WF06 switch execution fix ✅ READY
- **V102**: Double State Machine execution ← THIS FIX

---

**Status**: Fix identified, ready for implementation
**Deployment**: Immediate - critical production bug
