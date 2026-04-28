# BUGFIX WF02 V89 - WF06 Data Access Fix

**Data**: 2026-04-20
**Versão**: WF02 V89
**Problema**: State Machine segunda execução retorna ao greeting em vez de mostrar opções WF06
**Causa Raiz**: State Machine acessando WF06 data apenas de `input.wf06_next_dates` (localização única)

---

## Problema Identificado

### Sintoma no WF02 V88 (Segunda Execução)
**Execution**: http://localhost:5678/workflow/1vT4DqEPjlb4prgF/executions/4139

**Run 2 of 2 output**:
```
response_text: "🤖 *Olá! Bem-vindo à E2 Soluções!*..." (GREETING)
next_stage: "service_selection"
```

❌ **Esperado**: Mostrar opções de datas do WF06
❌ **Recebido**: Reset para greeting state

### Comportamento Observado
- **Primeira execução** (states 1-8): ✅ Funciona corretamente
- **State Machine** após WF06: Espera `show_available_dates` mas cai no `default` case
- **Resultado**: State Machine reseta para `greeting` em vez de processar resposta WF06

---

## Root Cause Analysis

### V88 Code (Broken)
```javascript
case 'show_available_dates':
  const nextDatesResponse = input.wf06_next_dates || {};
  //                       ^^^^^^^^^^^^^^^^^^^^^^
  //                       PROBLEMA: Acesso único de localização

  if (nextDatesResponse.success && nextDatesResponse.dates) {
    // Mostrar datas...
  } else {
    // Fallback manual...
  }
```

### Data Flow Problem

```
HTTP Request - Get Next Dates
  ↓ Returns: {phone_number, conversation_id, message, wf06_next_dates: [...]}

Prepare WF06 Next Dates Data (V88)
  ↓ Returns: {...inputData, wf06_next_dates: [...]} ✅ Preserva dados

Merge WF06 Next Dates with User Data (append mode)
  Input 0: {...inputData, wf06_next_dates: [...]}  // From Prepare
  Input 1: {phone_number, lead_name, service_type, collected_data: {...}}  // From Get Conversation
  ↓ Outputs 2 items (append mode)

State Machine Logic (Second Execution)
  Receives: $input.all()[0].json  // Could be Item 0 OR Item 1

  IF Item 0 from Prepare:
    ✅ input.wf06_next_dates exists → Show dates

  IF Item 1 from Get Conversation:
    ❌ input.wf06_next_dates = undefined
    ❌ Condition fails → Falls through to default case
    ❌ Resets to greeting ❌
```

### Why V88 Failed on Second Execution

**Merge Node Behavior** (append mode):
- Creates 2 separate items
- n8n might pass Item 1 (Get Conversation Details) to State Machine
- Item 1 does NOT have `wf06_next_dates` property
- State Machine checks ONLY `input.wf06_next_dates` → undefined
- Condition `if (nextDatesResponse.success && nextDatesResponse.dates)` → false
- Falls to `else` (manual fallback) OR default case → Reset to greeting

---

## Solução Implementada: V89

### V89 Fix: Multi-Location WF06 Data Access

**Principle**: Check ALL possible locations where WF06 data could be

#### State `show_available_dates` (V89)

**Before** (V88 - Single Location Check):
```javascript
const nextDatesResponse = input.wf06_next_dates || {};
// ❌ Only checks input.wf06_next_dates
```

**After** (V89 - Multi-Location Check):
```javascript
let nextDatesResponse = null;

// Priority 1: Direct from Prepare node (most common after V88 fix)
if (input.wf06_next_dates) {
  nextDatesResponse = input.wf06_next_dates;
  console.log('V89: ✅ Found WF06 data in input.wf06_next_dates');
}
// Priority 2: From currentData (after Merge)
else if (currentData.wf06_next_dates) {
  nextDatesResponse = currentData.wf06_next_dates;
  console.log('V89: ✅ Found WF06 data in currentData.wf06_next_dates');
}
// Priority 3: Nested in input.currentData
else if (input.currentData && input.currentData.wf06_next_dates) {
  nextDatesResponse = input.currentData.wf06_next_dates;
  console.log('V89: ✅ Found WF06 data in input.currentData.wf06_next_dates');
}
// No WF06 data found
else {
  nextDatesResponse = {};
  console.error('V89: ❌ WF06 data NOT found in any location');
  console.error('V89: ❌ input keys:', Object.keys(input));
  console.error('V89: ❌ currentData keys:', Object.keys(currentData));
}
```

#### State `show_available_slots` (V89)

**Same fix applied**:
```javascript
let slotsResponse = null;

// Priority 1: Direct from Prepare node
if (input.wf06_available_slots) {
  slotsResponse = input.wf06_available_slots;
  console.log('V89: ✅ Found WF06 slots in input.wf06_available_slots');
}
// Priority 2: From currentData
else if (currentData.wf06_available_slots) {
  slotsResponse = currentData.wf06_available_slots;
  console.log('V89: ✅ Found WF06 slots in currentData.wf06_available_slots');
}
// Priority 3: Nested in input.currentData
else if (input.currentData && input.currentData.wf06_available_slots) {
  slotsResponse = input.currentData.wf06_available_slots;
  console.log('V89: ✅ Found WF06 slots in input.currentData.wf06_available_slots');
}
// No WF06 slots data found
else {
  slotsResponse = {};
  console.error('V89: ❌ WF06 slots NOT found in any location');
}
```

### V89 Enhanced Logging

**Debug Data Structure**:
```javascript
console.log('=== V89 STATE MACHINE START ===');
console.log('V89: Current stage:', currentStage);
console.log('V89: Input keys:', Object.keys(input));
console.log('V89: CurrentData keys:', Object.keys(currentData));
console.log('V89: Has input.wf06_next_dates:', !!input.wf06_next_dates);
console.log('V89: Has currentData.wf06_next_dates:', !!currentData.wf06_next_dates);
console.log('V89: Has input.wf06_available_slots:', !!input.wf06_available_slots);
console.log('V89: Has currentData.wf06_available_slots:', !!currentData.wf06_available_slots);
```

**Debug WF06 States**:
```javascript
console.log('V89: DEBUG - Checking all possible locations for WF06 data');
console.log('V89: DEBUG - input.wf06_next_dates:', JSON.stringify(input.wf06_next_dates || null));
console.log('V89: DEBUG - currentData.wf06_next_dates:', JSON.stringify(currentData.wf06_next_dates || null));
```

---

## Deploy WF02 V89

### 1. Update State Machine Logic Node

```bash
# 1. Copy V89 State Machine code
cat /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/scripts/wf02-v89-state-machine.js

# 2. Update n8n Workflow
# Open: http://localhost:5678/workflow/1vT4DqEPjlb4prgF
# Node: "State Machine Logic" (Function node)
# Action: DELETE existing code → PASTE V89 code → Save
```

### 2. Keep V88 Prepare Nodes (Already Fixed)

**No changes needed** to Prepare nodes - V88 fix is correct:
- ✅ "Prepare WF06 Next Dates Data" (V88)
- ✅ "Prepare WF06 Available Slots Data" (V88)

### 3. Test V89 Complete Flow

**Test 1: Service 1 (Solar) - Full Flow**
```bash
# 1. Start WhatsApp conversation
# 2. Select service 1 (Solar)
# 3. Complete data collection (name, phone, email, city)
# 4. Confirm agendamento (option 1)
# 5. Expected: State Machine shows 3 dates from WF06 ✅
# 6. Select date option (1, 2, or 3)
# 7. Expected: State Machine shows available time slots ✅
# 8. Select time slot
# 9. Expected: Confirmation message ✅
```

**Test 2: Check n8n Logs**
```bash
docker logs -f e2bot-n8n-dev | grep -E "V89|wf06_next_dates|wf06_available_slots"

# Expected logs:
# V89: ✅ Found WF06 data in input.wf06_next_dates
# V89: ✅ SUCCESS - Displaying 3 dates to user
# V89: ✅ Found WF06 slots in input.wf06_available_slots
# V89: ✅ SUCCESS - Displaying 8 slots to user
```

---

## Validation Complete

### Checklist
- [x] Analyzed V88 second execution failure
- [x] Root cause: Single-location WF06 data access
- [x] Created V89 State Machine with multi-location data access
- [x] Enhanced logging for data structure debugging
- [x] Documentation created
- [ ] Deploy V89 State Machine to n8n
- [ ] Test Service 1 (Solar) complete flow
- [ ] Test Service 3 (Projetos) complete flow
- [ ] Validate logs show successful WF06 data access

### Expected Logs (V89 Success)
```
=== V89 STATE MACHINE START ===
V89: Current stage: show_available_dates
V89: Input keys: [phone_number, conversation_id, message, wf06_next_dates, ...]
V89: Has input.wf06_next_dates: true ✅
V89: DEBUG - Checking all possible locations for WF06 data
V89: ✅ Found WF06 data in input.wf06_next_dates
V89: ✅ SUCCESS - Displaying 3 dates to user

[User selects date]

=== V89 STATE MACHINE START ===
V89: Current stage: show_available_slots
V89: Has input.wf06_available_slots: true ✅
V89: DEBUG - Checking all possible locations for WF06 slots data
V89: ✅ Found WF06 slots in input.wf06_available_slots
V89: ✅ SUCCESS - Displaying 8 slots to user
```

---

## Lessons Learned

### n8n Data Flow Principles
1. **Merge Node Behavior**: Append mode creates multiple items, not combined object
2. **State Machine Input**: `$input.all()[0].json` might receive different items across executions
3. **Defensive Data Access**: Always check multiple locations for critical data
4. **Explicit Logging**: Log data structure keys for debugging complex flows

### Best Practices for State Machine WF06 Integration
```javascript
// ❌ BAD: Single location check
const wf06Data = input.wf06_next_dates || {};

// ✅ GOOD: Multi-location check with priority
let wf06Data = null;
if (input.wf06_next_dates) {
  wf06Data = input.wf06_next_dates;
} else if (currentData.wf06_next_dates) {
  wf06Data = currentData.wf06_next_dates;
} else if (input.currentData && input.currentData.wf06_next_dates) {
  wf06Data = input.currentData.wf06_next_dates;
}
```

### Debugging Multi-Node Flows
1. **Log ALL data keys**: `console.log('Keys:', Object.keys(data))`
2. **Check boolean existence**: `console.log('Has field:', !!data.field)`
3. **Stringify nested objects**: `JSON.stringify(data, null, 2)`
4. **Test both flows**: next_dates AND available_slots workflows
5. **Monitor multiple executions**: First run vs second run behavior

---

## Referências

**Related Fixes**:
- WF06 V2.2: `docs/fix/BUGFIX_WF06_V2_2_RESPONSE_MODE.md` (HTTP Request responseMode)
- WF02 V88: `docs/fix/BUGFIX_WF02_V88_PHONE_NUMBER_PRESERVATION.md` (Prepare nodes data preservation)
- WF02 V80: `docs/deployment/DEPLOY_WF02_V80_COMPLETE_STATE_MACHINE.md` (Complete State Machine)

**Project Files**:
- WF02 V87: `n8n/workflows/02_ai_agent_conversation_V87_RESPONSE_FORMAT_FIX.json` (base)
- WF02 V88 Prepare Scripts:
  - `scripts/fix-wf02-v88-prepare-node.js` (next_dates) ✅
  - `scripts/fix-wf02-v88-prepare-slots-node.js` (available_slots) ✅
- WF02 V89 State Machine: `scripts/wf02-v89-state-machine.js` ✅

**Root Cause Analyses**:
- HTTP Issue: `docs/analysis/WF02_WF06_HTTP_REQUEST_PROBLEM_ROOT_CAUSE.md`
- State Machine: `docs/analysis/WF02_STATE_MACHINE_WF06_INTEGRATION_PROBLEM.md`

---

**Conclusão**: V88 → V89 fix completo. State Machine agora acessa WF06 data de múltiplas localizações (input direto, currentData, input.currentData). Logging aprimorado para debugging. Prepare nodes V88 preservam dados do usuário. Integration WF06 completa e robusta.

**Status**: ✅ Fix implementado | ⏳ Aguardando deploy e validação end-to-end
**Next**: Deploy V89 → Testar flow completo → Validar logs → Production ready
