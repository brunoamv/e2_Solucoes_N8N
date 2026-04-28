# WF02 V92 - Quick Deployment Guide

**Date**: 2026-04-20
**Priority**: 🔴 CRITICAL
**Status**: Ready for immediate deployment

---

## What V92 Fixes

**Problem**: V91 code is correct but Merge node uses STALE database data from workflow start
**Solution**: Add database refresh node AFTER HTTP Request to get FRESH current_state

---

## 5-Minute Deployment

### Step 1: Open n8n Workflow
```
URL: http://localhost:5678/workflow/fpMUFXvBulYXX4OX
```

### Step 2: Add Refresh Node

1. Click **"+"** after "Prepare WF06 Next Dates Data" node
2. Search for **"Postgres"** → Select "Postgres"
3. Configure:
   - **Name**: `Get Conversation Details (Refresh)`
   - **Operation**: `Execute Query`
   - **Query**:
   ```sql
   SELECT
     phone_number,
     lead_name,
     contact_name,
     contact_phone,
     email,
     city,
     service_type,
     service_selected,
     current_state,
     collected_data::text as collected_data_text,
     created_at,
     updated_at
   FROM conversations
   WHERE phone_number = '{{ $node["Prepare WF06 Next Dates Data"].json.phone_number }}'
   LIMIT 1;
   ```
   - **Always Output Data**: ✅ TRUE

### Step 3: Update Connections

**Add new connection**:
- From: "Get Conversation Details (Refresh)"
- To: "Merge WF06 Next Dates with User Data" → **Input 1**

**Remove old connection**:
- Find "Get Conversation Details" → "Merge WF06 Next Dates with User Data" (Input 1)
- Click connection → Press DELETE

### Step 4: Save
Click **"Save"** (top right)

---

## Testing (2 minutes)

### Test Message
Send WhatsApp message:
```
Service: 1 (energia solar)
Confirmation: 1 (agendar)
```

### Expected Logs
```bash
docker logs -f e2bot-n8n-dev | grep -E "V91|RESOLVED currentStage|show_available_dates"
```

**Should see**:
```
V91: currentData.current_stage: trigger_wf06_next_dates ✅ (NOT 'confirmation')
V91: RESOLVED currentStage: trigger_wf06_next_dates ✅ (NOT 'greeting')
```

### Expected Result
User receives: **3 dates with available slots** (NOT service_selection menu)

---

## Validation Checklist

- [ ] Refresh node added after "Prepare WF06 Next Dates Data"
- [ ] Refresh node connects to Merge Input 1
- [ ] Old "Get Conversation Details" → Merge connection REMOVED
- [ ] Workflow saved successfully
- [ ] Test execution shows fresh current_state in logs
- [ ] No "ALL stage sources undefined" warning
- [ ] User sees 3 dates (NOT service_selection)

---

## Rollback (if needed)

1. Delete "Get Conversation Details (Refresh)" node
2. Reconnect "Get Conversation Details" → "Merge WF06 Next Dates with User Data" (Input 1)
3. Save workflow
4. Returns to V91 behavior (broken but safe)

---

## Files Reference

- **Full Analysis**: `docs/WF02_V91_V92_COMPLETE_ANALYSIS.md`
- **Root Cause**: `docs/analysis/WF02_V91_ROOT_CAUSE_NODE_CONNECTION_ISSUE.md`
- **Detailed Plan**: `docs/PLAN/PLAN_WF02_V92_DATABASE_REFRESH_FIX.md`

---

**Status**: ✅ Ready for deployment
**Risk**: 🔴 CRITICAL - WF06 integration broken until deployed
**Complexity**: 🟢 LOW - One node + one connection change
**Time**: 5 minutes
