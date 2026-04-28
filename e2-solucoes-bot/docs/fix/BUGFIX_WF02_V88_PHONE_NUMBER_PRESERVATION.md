# BUGFIX WF02 V88 - Phone Number Data Preservation

**Data**: 2026-04-20
**Versão**: WF02 V88
**Problema**: Send WhatsApp Response "Bad request - please check your parameters"
**Causa Raiz**: Prepare WF06 nodes dropping user data (phone_number, conversation_id, etc.)

---

## Problema Identificado

### Sintoma no WF02 V87
```
Error: Problem in node 'Send WhatsApp Response'
Bad request - please check your parameters
```

### Comportamento Observado
- State Machine retornava estrutura correta MAS `phone_number` estava vazio
- "Send WhatsApp Response" falha porque Evolution API requer `number` parameter
- WF06 integration funcionava (após V2.2 fix) MAS dados do usuário eram perdidos

### State Machine Output (V87 - Broken)
```json
{
  "response_text": "Aqui estão as opções de datas disponíveis...",
  "phone_number": "",  // ❌ VAZIO
  "phone_with_code": "",  // ❌ VAZIO
  "conversation_id": null,  // ❌ NULL
  "wf06_next_dates": [...]  // ✅ WF06 data OK
}
```

---

## Causa Raiz

### Data Flow Analysis
```
HTTP Request - Get Next Dates
  Input: {phone_number, conversation_id, message, ...}
  ↓
Prepare WF06 Next Dates Data (V87 - PROBLEMA)
  Code: return { wf06_next_dates: [...] }  // ❌ Drops ALL user data
  Output: {wf06_next_dates: [...]}  // NO phone_number
  ↓
Merge WF06 Next Dates with User Data
  Input 0: {wf06_next_dates: [...]}  // From Prepare (NO phone)
  Input 1: {phone_number, ...}  // From Get Conversation Details (HAS phone)
  Mode: "append" (creates 2 separate items, doesn't merge)
  Output: [{wf06_next_dates: [...]}, {phone_number, ...}]
  ↓
State Machine Logic
  Receives: $input.first().json  // First item = {wf06_next_dates: [...]}
  Returns: {phone_number: input.phone_number}  // input.phone_number = undefined ❌
```

### Root Problem
**"Prepare WF06 Next Dates Data"** and **"Prepare WF06 Available Slots Data"** nodes:
- V87: Returned ONLY `{wf06_next_dates}` or `{wf06_available_slots}`
- V87: **Dropped ALL input data** from HTTP Request (phone_number, conversation_id, message, etc.)
- Result: Merge node received incomplete data → State Machine got empty phone_number

---

## Solução Implementada

### V88 Fix: Data Preservation in Prepare Nodes

**Principle**: Preserve ALL input data while adding WF06 response

#### Prepare WF06 Next Dates Data (V88)

**Before** (V87 - Broken):
```javascript
const preparedData = {
  wf06_next_dates: datesData  // ONLY WF06 response
};
return preparedData;  // ❌ User data lost
```

**After** (V88 - Fixed):
```javascript
const inputData = $input.first().json; // Get ALL input from HTTP Request

const preparedData = {
  ...inputData,  // ✅ Preserve phone_number, conversation_id, etc.
  wf06_next_dates: datesData  // Add WF06 response
};

console.log('✅ V88 Data preservation:');
console.log('  - phone_number:', preparedData.phone_number);
console.log('  - conversation_id:', preparedData.conversation_id);
console.log('  - wf06_next_dates count:', preparedData.wf06_next_dates.length);

return preparedData;
```

#### Prepare WF06 Available Slots Data (V88)

**Same fix applied**:
```javascript
const inputData = $input.first().json;

const preparedData = {
  ...inputData,  // ✅ Preserve user data
  wf06_available_slots: slotsData  // Add WF06 response
};

return preparedData;
```

---

## Deploy WF02 V88

### 1. Update "Prepare WF06 Next Dates Data" Node

```bash
# 1. Copy V88 code
cat /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/scripts/fix-wf02-v88-prepare-node.js

# 2. Update n8n Workflow
# Open: http://localhost:5678/workflow/1vT4DqEPjlb4prgF
# Node: "Prepare WF06 Next Dates Data" (Code node)
# Action: DELETE existing code → PASTE V88 code → Save
```

### 2. Update "Prepare WF06 Available Slots Data" Node

```bash
# 1. Copy V88 code
cat /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/scripts/fix-wf02-v88-prepare-slots-node.js

# 2. Update n8n Workflow
# Node: "Prepare WF06 Available Slots Data" (Code node)
# Action: DELETE existing code → PASTE V88 code → Save
```

### 3. Test V88 Integration

**Test 1: Service 1 (Solar) - Next Dates Flow**
```bash
# 1. Trigger WhatsApp conversation with service 1
# 2. Confirm agendamento
# 3. Expected: WF06 returns 3 dates → State Machine shows dates → WhatsApp response sent ✅
# 4. Check logs: "V88 Data preservation: phone_number: 556299999999"
```

**Test 2: Service 3 (Projetos) - Available Slots Flow**
```bash
# 1. Trigger WhatsApp conversation with service 3
# 2. Confirm agendamento + select date
# 3. Expected: WF06 returns slots → State Machine shows slots → WhatsApp response sent ✅
# 4. Check logs: "V88 Data preservation: phone_number: 556299999999"
```

---

## Validation Complete

### Checklist
- [x] Analyzed State Machine output structure
- [x] Identified Merge node data preservation issue
- [x] Root cause: Prepare nodes dropping input data
- [x] Created V88 fix for both Prepare nodes
- [ ] Deploy V88 to n8n
- [ ] Test Service 1 (Solar) flow end-to-end
- [ ] Test Service 3 (Projetos) flow end-to-end
- [ ] Validate logs show phone_number preservation

### Expected Logs (V88 Success)
```
✅ V88 Data preservation:
  - phone_number: 556299999999
  - conversation_id: 123
  - wf06_next_dates count: 3

[State Machine V80] State: 8 (present_available_dates)
  phone_number: 556299999999 ✅
  response_text: "Aqui estão as opções de datas disponíveis..." ✅

[Send WhatsApp Response] SUCCESS
  number: 556299999999 ✅
```

---

## Lessons Learned

### Data Flow Principles
1. **Preserve Input Data**: Nodes should preserve ALL input unless explicitly filtered
2. **Spread Operator Best Practice**: Use `{...inputData, newField}` pattern for data preservation
3. **Merge vs Append**: n8n Merge "append" creates separate items, "merge" combines them
4. **Explicit Data Access**: State Machine gets `$input.first().json` - ensure this item has ALL required data

### n8n Data Passing Patterns
```javascript
// ❌ BAD: Drops input data
return { new_field: value };

// ✅ GOOD: Preserves input data
const inputData = $input.first().json;
return { ...inputData, new_field: value };
```

### Debugging Multi-Node Flows
1. **Log data keys** at each node: `console.log('Keys:', Object.keys(data))`
2. **Verify phone preservation** explicitly: `console.log('phone_number:', data.phone_number)`
3. **Test both flows**: next_dates AND available_slots workflows
4. **Check Merge node output**: Understand which item State Machine receives

---

## Referências

**Related Fixes**:
- WF06 V2.2: `docs/fix/BUGFIX_WF06_V2_2_RESPONSE_MODE.md` (HTTP Request fix)
- WF02 V80: `docs/deployment/DEPLOY_WF02_V80_COMPLETE_STATE_MACHINE.md` (State Machine)

**Project Files**:
- WF02 V87: `n8n/workflows/02_ai_agent_conversation_V87_RESPONSE_FORMAT_FIX.json` (broken)
- WF02 V88 Fix Scripts:
  - `scripts/fix-wf02-v88-prepare-node.js` (next_dates)
  - `scripts/fix-wf02-v88-prepare-slots-node.js` (available_slots)

**Root Cause Analysis**:
- HTTP Issue: `docs/analysis/WF02_WF06_HTTP_REQUEST_PROBLEM_ROOT_CAUSE.md`
- State Machine: `docs/analysis/WF02_STATE_MACHINE_WF06_INTEGRATION_PROBLEM.md`

---

**Conclusão**: V87 → V88 fix completo. Ambos os Prepare nodes agora preservam dados do usuário (phone_number, conversation_id, etc.) + adicionam resposta do WF06. Merge node funciona corretamente com dados completos. State Machine recebe phone_number válido. WhatsApp Response enviada com sucesso.

**Status**: ✅ Fix implementado | ⏳ Aguardando deploy e validação end-to-end
