# BUGFIX WF02 V103 - Parallel Execution Conflict

**Date**: 2026-04-27
**Workflow ID**: 9tG2gR6KBt6nYyHT
**Execution**: 8294
**Root Cause**: Get Conversation Details connects to BOTH State Machine Logic AND Merge WF06 causing parallel execution conflict
**Discovered By**: User analysis of execution flow

---

## 🐛 PROBLEM ANALYSIS

### User Report
```
"Eu achei o erro. Existe uma conexao entre Get Conversation Details e o
Merge WF06 Next Dates with User Data em http://localhost:5678/workflow/9tG2gR6KBt6nYyHT/executions/8294
que executa toda vez o merge antes de passar no state machine logic (paralelo)"
```

### Observed Behavior (WhatsApp Conversation)
```
[18:35] User: "oi"
[18:35] Bot: "🤖 Olá! Bem-vindo à E2 Soluções!" ✅

[18:35] User: "1" (selects service)
[18:35] Bot: "Perfeito! Qual é o seu nome completo?" ✅

[18:35] Bot: "🤖 Olá! Bem-vindo à E2 Soluções!" ❌ DUPLICATE GREETING
[18:35] Bot: "⚠️ Não encontramos horários disponíveis no momento" ❌ PREMATURE WF06

[18:36] User: "Bruno Rosa"
[18:36] Bot: "❌ Opção inválida" ❌ WRONG RESPONSE
[18:36] Bot: "🤖 Olá! Bem-vindo à E2 Soluções!" ❌ DUPLICATE GREETING AGAIN
```

### Root Cause Architecture

**CURRENT (BROKEN) - Parallel Execution**:
```
Get Conversation Details
  ├─→ State Machine Logic ✅ (intended path)
  └─→ Merge WF06 Next Dates with User Data ❌ (parallel execution BUG)
      └─→ State Machine Logic ❌ (executes AGAIN with empty data)
```

**Impact**:
- **EVERY message** triggers TWO parallel executions:
  1. Normal flow: Get Conversation Details → State Machine Logic ✅
  2. Parallel bug: Get Conversation Details → Merge WF06 → State Machine Logic ❌

- Merge WF06 executes with EMPTY wf06_next_dates
- Second State Machine execution sees NO conversation_id → defaults to greeting
- User receives duplicate greetings and premature error messages

---

## ✅ SOLUTION V103 - Remove Parallel Connection

### Fix 1: Delete Incorrect Connection

**Action**: Remove connection from "Get Conversation Details" to "Merge WF06 Next Dates with User Data"

**Why**: This connection causes Merge to execute in parallel BEFORE State Machine completes its logic

### Fix 2: Correct Workflow Architecture

**CORRECT Flow (V103)**:
```
Get Conversation Details
  └─→ State Machine Logic ONLY
      └─→ Build Update Queries
          └─→ Check If WF06 Next Dates (IF node)
              ├─→ TRUE: WF06 HTTP Request Next Dates
              │   └─→ Prepare WF06 Next Dates Data
              │       └─→ Merge WF06 Next Dates with User Data
              │           └─→ Build WF06 Response Message
              │               └─→ Send WhatsApp Response
              └─→ FALSE: Continue normal flow
```

### Fix 3: Ensure State Machine V101 Code

**Verify State Machine Logic** has correct code from `wf02-v101-wf06-switch-fix.js`:
- Uses `$input.first().json` (NOT `$node["Build Update Queries"].json`)
- Lines 326-333: WF06 trigger logic for services 1 & 3

---

## 🔧 IMPLEMENTATION STEPS

### Step 1: Backup Current Workflow
```bash
# Export current state before changes
docker exec -it e2bot-n8n-dev n8n export:workflow --id=9tG2gR6KBt6nYyHT \
  --output=/data/backup_wf02_v102_before_v103.json
```

### Step 2: Open Workflow in n8n UI
1. Navigate to: http://localhost:5678/workflow/9tG2gR6KBt6nYyHT
2. Enable edit mode

### Step 3: Delete Parallel Connection
1. Click on node: **"Get Conversation Details"**
2. Find connection to: **"Merge WF06 Next Dates with User Data"**
3. **DELETE this connection** (click on connection line → Delete)
4. Verify only ONE output remains: → State Machine Logic

### Step 4: Verify State Machine Logic Code
1. Click on node: **"State Machine Logic"**
2. Check if code starts with:
   ```javascript
   // WF02 V101 - STATE MACHINE WITH WF06 SWITCH EXECUTION FIX
   const input = $input.all()[0].json;
   ```
3. If NOT, replace entire code with content from:
   `/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/scripts/wf02-v101-wf06-switch-fix.js`

### Step 5: Verify Send WhatsApp Response Configuration
1. Click on node: **"Send WhatsApp Response"**
2. Check Body Parameters:
   - `number`: Should be `={{ $input.first().json.phone_number }}`
   - `text`: Should be `={{ $input.first().json.response_text }}`
3. If using `$node["Build Update Queries"].json`, change to `$input.first().json`

### Step 6: Save and Test
1. Click **Save** in n8n UI
2. Test complete flow:
   - Send "oi" → Should receive greeting ONCE ✅
   - Send "1" → Should ask for name ✅
   - Send name → Should continue normally ✅
   - Complete data → Should trigger WF06 for services 1 & 3 ✅

---

## 📊 VALIDATION

### Test Normal Flow (Service 2 - No WF06)
```
User: "oi"
Expected: Single greeting message ✅

User: "2" (selects service 2 - sistema_fotovoltaico)
Expected: Ask for name, NO WF06 execution ✅

Complete all data
Expected: Confirmation message, NO calendar dates ✅
```

### Test WF06 Flow (Service 1 or 3)
```
User: "oi"
Expected: Single greeting message ✅

User: "1" or "3" (energia_solar or projeto_eletrico)
Expected: Ask for name, NO premature WF06 ✅

Complete all data → confirmation
Expected: "⏳ Buscando próximas datas disponíveis..." ✅

WF06 returns dates
Expected: Calendar dates message, NO duplicate greeting ✅
```

### Check Logs
```bash
docker logs -f e2bot-n8n-dev | grep -E "STATE MACHINE V10|Merge WF06|greeting"

# Expected (AFTER FIX):
# ✅ STATE MACHINE V101: Processing stage: greeting
# ✅ STATE MACHINE V101: Processing stage: collect_name
# ✅ STATE MACHINE V101: Processing stage: confirmation
# ✅ STATE MACHINE V101: Next stage: trigger_wf06_next_dates
# ❌ Should NOT see duplicate "STATE MACHINE V101: Processing stage: greeting"
# ❌ Should NOT see "Merge WF06" before State Machine completes
```

---

## 🚨 CRITICAL DIFFERENCES

### Before V103 (BROKEN)
```
Every message triggers:
  1. Get Conversation Details → State Machine Logic (correct)
  2. Get Conversation Details → Merge WF06 → State Machine Logic (parallel bug)

Result: Double State Machine execution, duplicate greetings
```

### After V103 (FIXED)
```
Every message triggers:
  1. Get Conversation Details → State Machine Logic ONLY

WF06 flow only when State Machine decides:
  State Machine → Build Update Queries → Check WF06 → HTTP Request → Merge → Response

Result: Single execution, correct flow control
```

---

## 📁 RELATED FIXES

**V102 Fixes** (Prerequisites):
1. ✅ Send WhatsApp Response uses `$input.first().json` (BUGFIX_WF02_V102_SEND_WHATSAPP_INPUT.md)
2. ✅ Build WF06 Response Message node created (wf02-v102-build-wf06-response.js)
3. ✅ State Machine uses correct V101 code (BUGFIX_WF02_V103_STATE_MACHINE_INPUT_FIX.md)

**V103 Fix** (This Document):
4. ✅ Remove parallel connection causing duplicate executions

---

**Status**: Solution identified - delete parallel connection from Get Conversation Details to Merge WF06
**Priority**: CRITICAL - blocks all conversation flows with duplicate messages
**Deployment**: Immediate - simple connection deletion in n8n UI
