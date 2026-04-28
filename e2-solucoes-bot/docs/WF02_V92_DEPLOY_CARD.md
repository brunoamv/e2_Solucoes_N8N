# WF02 V92 - Quick Deploy Card

**Date**: 2026-04-20
**Priority**: 🔴 CRITICAL
**Time**: 5 minutes

---

## What's New

**V92** = V91 code + Database Refresh node

### The Fix
```
OLD (V91 - BROKEN):
  State Machine gets STALE data from T0 ❌

NEW (V92 - FIXED):
  State Machine gets FRESH data from T5 ✅
```

---

## Deploy Steps

### 1. Import Workflow (2 min)
```
1. Open n8n: http://localhost:5678
2. Click "+" → "Import from file"
3. Select: n8n/workflows/02_ai_agent_conversation_V92.json
4. Click "Import"
```

### 2. Activate (30 sec)
```
1. Open imported workflow
2. Toggle "Active" (top right)
3. Verify green checkmark
```

### 3. Test (2 min)
```
WhatsApp:
  Service: 1 (Solar)
  Confirm: 1 (agendar)

Expected: 3 dates displayed ✅
Wrong: service_selection menu ❌
```

### 4. Verify Logs (30 sec)
```bash
docker logs -f e2bot-n8n-dev | grep "RESOLVED currentStage"

Expected:
V91: RESOLVED currentStage: trigger_wf06_next_dates ✅

Wrong:
V91: RESOLVED currentStage: greeting ❌
```

---

## Validation Checklist

- [ ] Workflow imported successfully
- [ ] Workflow activated (green toggle)
- [ ] Test shows 3 dates (not service menu)
- [ ] Logs show "trigger_wf06_next_dates" (not "greeting")
- [ ] User completes flow successfully

---

## Key Nodes

| Node | Status |
|------|--------|
| State Machine Logic | ✅ V91 code |
| Get Conversation Details (Refresh) | ✅ NEW! |
| Merge WF06 Next Dates | ✅ Uses fresh data |

---

## Rollback

If V92 fails:
1. Deactivate V92 workflow
2. Activate V74.1_2 workflow (production backup)
3. Report issue

---

## Files

- **Workflow**: `n8n/workflows/02_ai_agent_conversation_V92.json`
- **Summary**: `docs/WF02_V92_GENERATION_SUMMARY.md`
- **Full Guide**: `docs/deployment/DEPLOY_WF02_V92_DATABASE_REFRESH.md`

---

**Status**: ✅ Ready
**Risk**: 🔴 CRITICAL
**Deploy**: NOW
