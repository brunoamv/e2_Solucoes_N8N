# WF02 V104.2 - Quick Deployment Checklist

**Workflow**: 9tG2gR6KBt6nYyHT
**Time**: 5 minutes
**Risk**: Low

---

## ✅ Pre-Deployment

- [ ] V104 State Machine already deployed (check logs for "V104")
- [ ] PostgreSQL accessible (`docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "SELECT COUNT(*) FROM conversations;"`)
- [ ] n8n workflow accessible (http://localhost:5678/workflow/9tG2gR6KBt6nYyHT)

---

## 🔧 Deployment

### Step 1: Copy V104.2 Code
```bash
cat /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/scripts/wf02-v104_2-build-update-queries-schema-fix.js
```
- [ ] Code copied to clipboard

### Step 2: Update n8n Node
1. [ ] Open: http://localhost:5678/workflow/9tG2gR6KBt6nYyHT
2. [ ] Click node: **"Build Update Queries"**
3. [ ] Current code shows "V58.1" or "V104.1" header
4. [ ] **DELETE** all existing code
5. [ ] **PASTE** V104.2 code
6. [ ] Verify header: `// Build Update Queries - V104.2 (DATABASE STATE + SCHEMA FIX)`
7. [ ] Verify state reading: `collected_data.current_stage ||`
8. [ ] Verify no `contact_phone` in SQL INSERT
9. [ ] Click **Save** on node
10. [ ] Click **Save** on workflow (top-right)

---

## ✅ Post-Deployment Validation

### Test 1: Send Test Message
```bash
# Send WhatsApp: "oi" → complete flow → "1" (agendar) → "1" (select date)
```
- [ ] Bot shows time slots (NOT dates again)
- [ ] No infinite loop

### Test 2: Check Logs
```bash
docker logs -f e2bot-n8n-dev | grep -E "V104.2|schema-compliant"
```
- [ ] Logs show: "V104.2 BUILD UPDATE QUERIES"
- [ ] Logs show: "schema-compliant"
- [ ] NO "contact_phone" errors

### Test 3: Verify Database
```bash
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT state_machine_state, collected_data->'current_stage'
      FROM conversations WHERE phone_number = '556181755748';"
```
- [ ] state_machine_state: "process_date_selection" (or similar WF06 state)
- [ ] current_stage matches state_machine_state
- [ ] NOT stuck at "confirmation"

---

## 🎯 Success Criteria

✅ **All must be true**:
- [ ] No infinite loop when selecting dates
- [ ] No database schema errors in logs
- [ ] Database state updates correctly
- [ ] User can complete scheduling flow
- [ ] Logs show V104.2 version

---

## 🚨 Rollback (If Issues Occur)

```bash
# 1. Open: http://localhost:5678/workflow/9tG2gR6KBt6nYyHT
# 2. Node: "Build Update Queries"
# 3. Restore V58.1 code from backup
# 4. Save node → Save workflow
# 5. Verify rollback: Send "oi" message
```

---

## 📚 Full Documentation

- **Deployment Guide**: `docs/deployment/DEPLOY_WF02_V104_2_BUILD_UPDATE_QUERIES_COMPLETE_FIX.md`
- **Bug Reports**:
  - `docs/fix/BUGFIX_WF02_V104_1_BUILD_UPDATE_QUERIES_STATE_FIX.md`
  - `docs/fix/BUGFIX_WF02_V104_2_SCHEMA_MISMATCH.md`
- **Summary**: `docs/WF02_V104_2_COMPLETE_SUMMARY.md`
