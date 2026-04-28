# WF02 V105 - Quick Deployment Checklist

**Workflow**: 9tG2gR6KBt6nYyHT
**Type**: Workflow connection change (no code)
**Time**: 5 minutes
**Risk**: Low

---

## ✅ Pre-Deployment

- [ ] V104+V104.2 already deployed (check CLAUDE.md Ready section)
- [ ] n8n workflow accessible (http://localhost:5678/workflow/9tG2gR6KBt6nYyHT)
- [ ] Workflow backup downloaded (Save as backup before starting)

---

## 🔧 Deployment Steps

### Step 1: Open Workflow
1. [ ] Open: http://localhost:5678/workflow/9tG2gR6KBt6nYyHT
2. [ ] Locate nodes: "Build Update Queries", "Update Conversation State", "Check If WF06 Next Dates"

### Step 2: Disconnect Update Conversation State
1. [ ] Click **Update Conversation State** node
2. [ ] Delete connection FROM "Check If WF06 Available Slots" FALSE branch
3. [ ] Leave node ready to reconnect

### Step 3: Reconnect Before Check If WF06
1. [ ] Delete connection: Build Update Queries → Check If WF06 Next Dates
2. [ ] Create NEW: Build Update Queries → **Update Conversation State**
3. [ ] Create NEW: **Update Conversation State** → Check If WF06 Next Dates

### Step 4: Visual Verification
```
Build Update Queries
  ↓
Update Conversation State ✅ (executes FIRST now!)
  ↓
Check If WF06 Next Dates
  ├─ TRUE → WF06 routes
  └─ FALSE → Check If WF06 Available Slots
```

- [ ] Connections match diagram above
- [ ] Update Conversation State has ONE input, ONE output
- [ ] Update executes BEFORE any Check If WF06 routing

### Step 5: Save
- [ ] Click **Save** (top-right)
- [ ] Wait for "Workflow saved" confirmation
- [ ] Workflow active (green toggle)

---

## ✅ Post-Deployment Validation

### Test 1: Date Selection (CRITICAL)
```bash
# Send WhatsApp: "oi" → complete → "1" (agendar) → "1" (select date)
```
- [ ] Shows time slots (NOT dates again) ✅
- [ ] No infinite loop ✅

### Test 2: Database Update Before WF06
```bash
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT state_machine_state, collected_data->'current_stage'
      FROM conversations WHERE phone_number = '556181755748';"
```
- [ ] state_machine_state: "trigger_wf06_next_dates" or "process_date_selection" ✅
- [ ] NOT "confirmation" ❌

### Test 3: Logs Show Correct Order
```bash
docker logs -f e2bot-n8n-dev | grep -E "Update Conversation State|Check If WF06"
```
- [ ] "Update Conversation State" appears BEFORE "Check If WF06" ✅

---

## 🎯 Success Criteria

✅ **All must be true**:
- [ ] No infinite loop when selecting dates
- [ ] Database updates BEFORE WF06 routes
- [ ] User can complete scheduling flow
- [ ] Logs show Update executes before routing

---

## 🚨 Rollback (If Issues)

```bash
# 1. Open: http://localhost:5678/workflow/9tG2gR6KBt6nYyHT
# 2. Reconnect: Build Update Queries → Check If WF06 Next Dates (old way)
# 3. Reconnect: Check If WF06 Available Slots FALSE → Update Conversation State (old way)
# 4. Save workflow
# 5. Or import backup file
```

---

## 📚 Full Documentation

- **Complete Guide**: `docs/deployment/DEPLOY_WF02_V105_WF06_ROUTING_FIX.md`
- **Bug Analysis**: `docs/fix/BUGFIX_WF02_V105_WF06_ROUTING_STATE_UPDATE.md`
- **Prerequisites**: V104 State Machine + V104.2 Build Update Queries must be deployed first
