# Deploy WF02 V89 COMPLETE - WF06 Data Access Fix

**Data**: 2026-04-20
**Versão**: WF02 V89 COMPLETE
**Arquivo**: `02_ai_agent_conversation_V89_COMPLETE.json`
**Fixes**: V89 State Machine (multi-location WF06 data access) + V88 Prepare nodes (user data preservation)

---

## Componentes V89

### 1. State Machine Logic (V89) ✅
**Fix**: Multi-location WF06 data access
- Checks `input.wf06_next_dates` (Priority 1)
- Checks `currentData.wf06_next_dates` (Priority 2)
- Checks `input.currentData.wf06_next_dates` (Priority 3)
- Enhanced logging for debugging

### 2. Prepare WF06 Next Dates Data (V88) ✅
**Fix**: User data preservation
- Returns `{...inputData, wf06_next_dates: [...]}`
- Preserves phone_number, conversation_id, message, etc.

### 3. Prepare WF06 Available Slots Data (V88) ✅
**Fix**: User data preservation
- Returns `{...inputData, wf06_available_slots: [...]}`
- Preserves phone_number, conversation_id, message, etc.

---

## Deploy Steps

### Method 1: Import Complete V89 JSON (Recommended)

```bash
# 1. Backup current workflow
# n8n UI: http://localhost:5678/workflow/1vT4DqEPjlb4prgF
# Download current workflow as backup

# 2. Import V89 COMPLETE
# n8n UI → Menu (☰) → Import from file
# Select: n8n/workflows/02_ai_agent_conversation_V89_COMPLETE.json

# 3. Activate workflow
# Click "Active" toggle → Green ✅

# 4. Verify nodes updated
# Open "State Machine Logic" → Should see V89 comments
# Open "Prepare WF06 Next Dates Data" → Should see V88 comments
# Open "Prepare WF06 Available Slots Data" → Should see V88 comments
```

### Method 2: Manual Node Updates

```bash
# Update State Machine Logic
cat /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/scripts/wf02-v89-state-machine.js

# n8n UI → Node "State Machine Logic"
# DELETE existing code → PASTE V89 code → Save

# Update Prepare WF06 Next Dates Data
cat /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/scripts/fix-wf02-v88-prepare-node.js

# n8n UI → Node "Prepare WF06 Next Dates Data"
# DELETE existing code → PASTE V88 code → Save

# Update Prepare WF06 Available Slots Data
cat /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/scripts/fix-wf02-v88-prepare-slots-node.js

# n8n UI → Node "Prepare WF06 Available Slots Data"
# DELETE existing code → PASTE V88 code → Save
```

---

## Test Plan V89

### Test 1: Service 1 (Solar) - Next Dates Flow

**Execution Steps**:
```
1. Send WhatsApp message: "menu"
2. Select: 1 (Energia Solar)
3. Enter name: "Test User V89"
4. Confirm WhatsApp number: 1
5. Enter email: "test@v89.com"
6. Enter city: "Goiânia"
7. Confirm agendamento: 1 (Sim, quero agendar)

EXPECTED:
✅ State Machine: trigger_wf06_next_dates
✅ HTTP Request → WF06 V2.2
✅ Prepare WF06 Next Dates Data (V88) → Preserves user data
✅ Merge → Combines WF06 + user data
✅ State Machine: show_available_dates (V89) → Finds WF06 data in input.wf06_next_dates
✅ WhatsApp Response: Shows 3 dates with quality indicators
```

**n8n Logs Validation**:
```bash
docker logs -f e2bot-n8n-dev | grep -E "V89|V88|wf06_next_dates"

# Expected:
# [Prepare] V88 Data preservation: phone_number: 556299999999
# [State Machine] V89: Current stage: show_available_dates
# [State Machine] V89: Has input.wf06_next_dates: true
# [State Machine] V89: ✅ Found WF06 data in input.wf06_next_dates
# [State Machine] V89: ✅ SUCCESS - Displaying 3 dates to user
```

### Test 2: Service 3 (Projetos) - Available Slots Flow

**Execution Steps**:
```
1-7. Same as Test 1, but select service 3 (Projetos Elétricos)
8. Select date: 1 (Primeira opção)

EXPECTED:
✅ State Machine: process_date_selection → scheduled_date saved
✅ State Machine: trigger_wf06_available_slots
✅ HTTP Request → WF06 V2.2 (available_slots action)
✅ Prepare WF06 Available Slots Data (V88) → Preserves user data
✅ Merge → Combines WF06 + user data
✅ State Machine: show_available_slots (V89) → Finds WF06 data in input.wf06_available_slots
✅ WhatsApp Response: Shows 8 time slots
```

**n8n Logs Validation**:
```bash
docker logs -f e2bot-n8n-dev | grep -E "V89|V88|wf06_available_slots"

# Expected:
# [Prepare] V88 Data preservation: phone_number: 556299999999
# [State Machine] V89: Current stage: show_available_slots
# [State Machine] V89: Has input.wf06_available_slots: true
# [State Machine] V89: ✅ Found WF06 slots in input.wf06_available_slots
# [State Machine] V89: ✅ SUCCESS - Displaying 8 slots to user
```

### Test 3: Complete End-to-End Flow

**Full Flow**:
```
1-8. Same as Test 2
9. Select time slot: 1 (Primeiro horário)

EXPECTED:
✅ State Machine: process_slot_selection → scheduled_time_start/end saved
✅ State Machine: appointment_final_confirmation
✅ WhatsApp Response: Confirmation message with date + time
✅ PostgreSQL conversations table: Updated with appointment data
✅ Trigger WF05 (appointment scheduler)
```

### Test 4: Error Handling - No WF06 Data

**Simulate WF06 failure**:
```
1. Temporarily disable WF06 V2.2 workflow
2. Execute Service 1 flow until confirmation
3. Confirm agendamento: 1

EXPECTED:
✅ State Machine: trigger_wf06_next_dates
❌ HTTP Request fails (WF06 disabled)
✅ Prepare node: Handles missing WF06 data
✅ State Machine: show_available_dates (V89) → Detects no WF06 data
✅ WhatsApp Response: Fallback message asking for manual date input
```

**n8n Logs Validation**:
```bash
docker logs -f e2bot-n8n-dev | grep -E "V89.*ERROR|WF06 data NOT found"

# Expected:
# [State Machine] V89: ❌ WF06 data NOT found in any location
# [State Machine] V89: ❌ input keys: [...]
# [State Machine] V89: Fallback to manual date input
```

---

## Validation Checklist

### Pre-Deploy
- [x] V89 State Machine created with multi-location data access
- [x] V88 Prepare nodes verified (user data preservation)
- [x] Complete V89 JSON generated (44 nodes)
- [x] Documentation created (BUGFIX + DEPLOY)

### Deploy
- [ ] Backup current WF02 workflow
- [ ] Import V89 COMPLETE JSON to n8n
- [ ] Activate V89 workflow
- [ ] Verify 3 nodes updated (State Machine + 2 Prepare nodes)

### Post-Deploy Tests
- [ ] Test 1: Service 1 next_dates flow ✅
- [ ] Test 2: Service 3 available_slots flow ✅
- [ ] Test 3: Complete end-to-end with appointment ✅
- [ ] Test 4: Error handling with WF06 failure ✅
- [ ] Logs show V89/V88 success messages ✅
- [ ] No "greeting reset" on second State Machine execution ✅

### Production Validation
- [ ] Real WhatsApp conversation: Service 1 complete flow
- [ ] Real WhatsApp conversation: Service 3 complete flow
- [ ] PostgreSQL appointments table: Verify data inserted
- [ ] Evolution API: Verify WhatsApp responses sent
- [ ] n8n executions: No errors in last 10 executions

---

## Rollback Plan

### If V89 Fails

```bash
# 1. Stop V89 workflow
# n8n UI → Deactivate V89

# 2. Restore backup
# n8n UI → Import backup JSON from pre-deploy

# 3. Activate backup workflow
# Verify old workflow works

# 4. Check logs for V89 failure reason
docker logs e2bot-n8n-dev | grep -E "ERROR|V89" | tail -50

# 5. Fix identified issue
# Update V89 scripts → Re-generate JSON → Re-deploy
```

---

## Expected Improvements V89

### Fixes
- ✅ **No more greeting reset**: State Machine finds WF06 data in multiple locations
- ✅ **User data preserved**: phone_number flows correctly through all nodes
- ✅ **Robust WF06 integration**: Works with different Merge node output structures
- ✅ **Better debugging**: Enhanced logging for data structure analysis

### Performance
- ✅ **Zero additional latency**: Multi-location check is instant (priority-based)
- ✅ **Same user experience**: No changes to WhatsApp messages or flow
- ✅ **Improved reliability**: Handles edge cases in Merge node behavior

### Maintainability
- ✅ **Clear logging**: V89/V88 version markers in all logs
- ✅ **Defensive coding**: Multiple fallback locations for critical data
- ✅ **Complete documentation**: Root cause analysis + fix documentation + deployment guide

---

## Known Limitations

### Merge Node Behavior
- **Append mode** creates 2 separate items
- **Solution**: V89 checks ALL items for WF06 data
- **Alternative**: Change Merge to "merge" mode (not recommended without testing)

### Future Improvements
1. **Refactor Merge node**: Consider changing "append" to "merge" mode to combine items
2. **Explicit item selection**: Use `$node["Prepare WF06 Next Dates Data"].json` instead of `$input.all()[0].json`
3. **WF06 data in PostgreSQL**: Store WF06 response in conversations.collected_data for persistence

---

## Referências

**Related Fixes**:
- WF06 V2.2: `docs/fix/BUGFIX_WF06_V2_2_RESPONSE_MODE.md`
- WF02 V88: `docs/fix/BUGFIX_WF02_V88_PHONE_NUMBER_PRESERVATION.md`
- WF02 V89: `docs/fix/BUGFIX_WF02_V89_WF06_DATA_ACCESS.md`
- WF02 V80: `docs/deployment/DEPLOY_WF02_V80_COMPLETE_STATE_MACHINE.md`

**Project Files**:
- WF02 V89 JSON: `n8n/workflows/02_ai_agent_conversation_V89_COMPLETE.json` ✅
- State Machine V89: `scripts/wf02-v89-state-machine.js` ✅
- Prepare Next Dates V88: `scripts/fix-wf02-v88-prepare-node.js` ✅
- Prepare Slots V88: `scripts/fix-wf02-v88-prepare-slots-node.js` ✅

**Root Cause Analyses**:
- HTTP Issue: `docs/analysis/WF02_WF06_HTTP_REQUEST_PROBLEM_ROOT_CAUSE.md`
- Phone Preservation: `docs/fix/BUGFIX_WF02_V88_PHONE_NUMBER_PRESERVATION.md`
- WF06 Data Access: `docs/fix/BUGFIX_WF02_V89_WF06_DATA_ACCESS.md`

---

**Conclusão**: WF02 V89 COMPLETE é a versão definitiva com todos os fixes:
- ✅ V2.2: WF06 responseMode (HTTP Request fix)
- ✅ V88: Prepare nodes user data preservation (phone_number fix)
- ✅ V89: State Machine multi-location WF06 data access (greeting reset fix)

**Status**: ✅ V89 COMPLETE pronto para deploy
**Next**: Import JSON → Activate → Test 4 scenarios → Production validation
