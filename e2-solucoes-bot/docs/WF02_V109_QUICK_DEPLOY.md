# WF02 V109 - Quick Deploy Guide

**Version**: V109 Flag Initialization Fix
**Fix**: Infinite loop bug from V108 execution #8989
**Time**: ~5 minutes
**Status**: 🔴 CRITICAL FIX

---

## 🎯 What V109 Fixes

**Problem**: V108 infinite loop - bot shows dates repeatedly instead of progressing to time slots

**Root Cause**: Flags output as `undefined` → Database stores NULL → Detection logic fails

**Solution**: Default flags to explicit `false` using `|| false` operator

---

## 🚀 Quick Deploy (5 minutes)

### 1. Copy V109 Code
```bash
cat /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/scripts/wf02-v109-flag-initialization-fix.js
```

### 2. Update n8n Workflow
1. Open: http://localhost:5678/workflow/9tG2gR6KBt6nYyHT
2. Node: **"State Machine Logic"**
3. **DELETE** all existing code
4. **PASTE** V109 code from Step 1
5. Click **"Save"** (node) → **"Save"** (workflow)

### 3. Verify V105 Routing (CRITICAL!)
Check: Build Update Queries → **Update Conversation State** → Check If WF06 Next Dates

✅ CORRECT: Update Conversation State executes BEFORE Check If WF06
❌ WRONG: Update Conversation State executes AFTER Check If WF06

**If WRONG, apply V105 fix**:
1. Disconnect: Build Update Queries → Check If WF06 Next Dates
2. Disconnect: Check If WF06 Available Slots FALSE → Update Conversation State
3. Connect NEW: Build Update Queries → Update Conversation State
4. Connect NEW: Update Conversation State → Check If WF06 Next Dates
5. Save workflow

---

## 🧪 Quick Test (2 minutes)

### Test Flow
```
1. Send: "oi"
2. Complete states 1-8
3. State 8: "1" (agendar)
4. ✅ Expected: Shows 3 dates with slot counts
5. Type: "1" (select first date)
6. ✅ Expected: Shows time slots (NOT dates again!)
7. ✅ Expected: No infinite loop
```

### Database Check
```sql
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT state_machine_state,
             collected_data->'awaiting_wf06_next_dates' as flag
      FROM conversations
      WHERE phone_number = '556181755748';"
```

**Expected after date selection**:
- `state_machine_state`: "trigger_wf06_available_slots" ✅
- `flag`: false (changed from true after processing) ✅

### Log Check
```bash
docker logs -f e2bot-n8n-dev 2>&1 | grep "V109: ✅ WF06 FLAGS:"
```

**Expected**:
```
V109:   awaiting_wf06_next_dates: true  ✅ (after showing dates)
V109:   awaiting_wf06_next_dates: false  ✅ (after processing selection)
```

---

## ✅ Success Criteria

- ✅ User can select date without infinite loop
- ✅ Workflow progresses to time slot selection
- ✅ Flags are boolean (not undefined) in logs
- ✅ Database shows proper flag values (true → false)

---

## 🔄 Rollback (if needed)

```bash
# 1. Copy V108 code
cat /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/scripts/wf02-v108-wf06-complete-fix.js

# 2. Update workflow (same process as deployment)
# Open: http://localhost:5678/workflow/9tG2gR6KBt6nYyHT
# Node: "State Machine Logic"
# DELETE → PASTE V108 code → Save
```

---

## 📚 Detailed Documentation

- **Full Deployment Guide**: `docs/deployment/DEPLOY_WF02_V109_FLAG_INITIALIZATION_FIX.md`
- **Root Cause Analysis**: `docs/fix/BUGFIX_WF02_V108_EXECUTION_8989_COMPLETE_ROOT_CAUSE.md`
- **V109 State Machine**: `scripts/wf02-v109-flag-initialization-fix.js`

---

**Created**: 2026-04-28
**Status**: ✅ READY
**Dependencies**: V105 routing fix (Update Conversation State BEFORE Check If WF06)
