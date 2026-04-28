# WF02 V105 - WF06 Routing State Update Fix Deployment

**Date**: 2026-04-27
**Workflow ID**: 9tG2gR6KBt6nYyHT
**Type**: Workflow connection change (no code deployment)
**Risk**: Low
**Time**: 5 minutes
**Prerequisite**: V104+V104.2 must be deployed first

---

## 🎯 DEPLOYMENT OBJECTIVE

Fix infinite loop when WF06 routes (Check If WF06 Next Dates, Check If WF06 Available Slots) are taken by ensuring Update Conversation State node executes BEFORE conditional routing instead of only on FALSE branches.

**Root Cause**: When Check If WF06 nodes evaluate to TRUE, workflow takes WF06 HTTP Request route and SKIPS Update Conversation State node, leaving database in old state.

**Solution**: Move Update Conversation State to execute immediately AFTER Build Update Queries, BEFORE any Check If WF06 conditional routing.

---

## ✅ PRE-DEPLOYMENT CHECKLIST

### Verify Prerequisites
- [ ] V104 State Machine already deployed in "State Machine Logic" node
- [ ] V104.2 Build Update Queries already deployed in "Build Update Queries" node
- [ ] n8n workflow accessible: http://localhost:5678/workflow/9tG2gR6KBt6nYyHT
- [ ] Database accessible for validation queries

### Backup Current State
```bash
# 1. Backup current workflow state
# Open n8n UI → Workflow 9tG2gR6KBt6nYyHT → Click "..." menu → Download
# Save as: n8n/workflows/backup/02_ai_agent_conversation_PRE_V105_backup.json

# 2. Verify current database state
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT state_machine_state, current_state, collected_data->'current_stage' as stage_in_data
      FROM conversations
      WHERE phone_number = '556181755748';"
```
- [ ] Workflow backup downloaded
- [ ] Database state documented

---

## 🔧 DEPLOYMENT STEPS

### Step 1: Open Workflow in n8n UI
```bash
# Open in browser
http://localhost:5678/workflow/9tG2gR6KBt6nYyHT
```
- [ ] Workflow opened in n8n UI

### Step 2: Locate Current Node Positions

**Current workflow structure** (BROKEN):
```
Build Update Queries
  ↓
Check If WF06 Next Dates
  ├─ TRUE → WF06 HTTP Request (Get Next 3 Dates)
  │          ↓
  │       Merge WF06 Next Dates with User Data
  │          ↓
  │       Send Message with Dates
  │       (❌ Update Conversation State NEVER executed!)
  │
  └─ FALSE → Check If WF06 Available Slots
               ├─ TRUE → WF06 HTTP Request (Get Available Slots)
               │          ↓
               │       Merge WF06 Slots with User Data
               │          ↓
               │       Send Message with Slots
               │       (❌ Update Conversation State NEVER executed!)
               │
               └─ FALSE → Update Conversation State ✅ (only executed here)
                           ↓
                        Send Message
```

Find these nodes:
- [ ] **Build Update Queries** (source node)
- [ ] **Update Conversation State** (node to move)
- [ ] **Check If WF06 Next Dates** (first conditional)
- [ ] **Check If WF06 Available Slots** (second conditional)

### Step 3: Disconnect Update Conversation State

1. Click on **Update Conversation State** node
2. Note all INCOMING connections (so you can delete them):
   - Currently: Connected from "Check If WF06 Available Slots" FALSE branch
3. Note all OUTGOING connections (so you can recreate them later):
   - Currently: Connects to "Send Message" or similar final node
4. Delete INCOMING connections:
   - Click connection line from "Check If WF06 Available Slots" FALSE to "Update Conversation State"
   - Press Delete or click trash icon
5. Keep node selected for next step

- [ ] Current connections documented
- [ ] Incoming connections deleted
- [ ] Node ready to reconnect

### Step 4: Connect Update Conversation State After Build Update Queries

1. Find **Build Update Queries** node
2. Note its current OUTGOING connection:
   - Currently: Connects to "Check If WF06 Next Dates"
3. Delete this connection:
   - Click connection line from "Build Update Queries" to "Check If WF06 Next Dates"
   - Press Delete or click trash icon
4. Create NEW connection:
   - Click and drag from **Build Update Queries** output port
   - Connect to **Update Conversation State** input port
5. Verify connection created successfully

- [ ] Old connection deleted
- [ ] New connection created: Build Update Queries → Update Conversation State

### Step 5: Connect Update Conversation State to Check If WF06 Next Dates

1. Click and drag from **Update Conversation State** output port
2. Connect to **Check If WF06 Next Dates** input port
3. Verify connection created successfully

- [ ] Connection created: Update Conversation State → Check If WF06 Next Dates

### Step 6: Verify New Workflow Structure

**New workflow structure** (FIXED):
```
Build Update Queries
  ↓
Update Conversation State ✅ (MOVED HERE - ALWAYS executes first!)
  ↓
Check If WF06 Next Dates
  ├─ TRUE → WF06 HTTP Request (Get Next 3 Dates)
  │          ↓
  │       Merge WF06 Next Dates with User Data
  │          ↓
  │       Send Message with Dates
  │
  └─ FALSE → Check If WF06 Available Slots
               ├─ TRUE → WF06 HTTP Request (Get Available Slots)
               │          ↓
               │       Merge WF06 Slots with User Data
               │          ↓
               │       Send Message with Slots
               │
               └─ FALSE → Send Message (normal flow)
```

Visual verification:
- [ ] Build Update Queries connects to Update Conversation State
- [ ] Update Conversation State connects to Check If WF06 Next Dates
- [ ] Check If WF06 Next Dates TRUE branch connects to WF06 HTTP Request (Get Next 3 Dates)
- [ ] Check If WF06 Next Dates FALSE branch connects to Check If WF06 Available Slots
- [ ] No other connections to Update Conversation State (it only executes once now, before routing)

### Step 7: Save Workflow

1. Click **Save** button (top-right corner)
2. Wait for "Workflow saved" confirmation message
3. Verify workflow is active (toggle should be green)

- [ ] Workflow saved successfully
- [ ] Workflow is active

---

## ✅ POST-DEPLOYMENT VALIDATION

### Test 1: Complete Date Selection Flow (CRITICAL)
```bash
# Send WhatsApp conversation:
# 1. Send "oi" → complete flow → "1" (agendar)
# 2. Bot shows 3 available dates with slot counts
# 3. Send "1" (select first date)

# Expected behavior:
# ✅ Bot shows time slots for selected date (NOT dates again)
# ❌ Should NOT loop back to showing dates repeatedly
```
- [ ] User can select date without infinite loop
- [ ] Bot advances to time slot selection after date selection
- [ ] No repeated date messages

### Test 2: Verify Database Update BEFORE WF06 Call
```bash
# After user sends "1" to select date, check database IMMEDIATELY
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT state_machine_state, current_state, collected_data->'current_stage' as stage_in_data
      FROM conversations
      WHERE phone_number = '556181755748';"

# Expected (BEFORE WF06 completes):
# state_machine_state: "trigger_wf06_next_dates" or "process_date_selection"  ✅ UPDATED!
# stage_in_data: "trigger_wf06_next_dates" or "process_date_selection"  ✅ UPDATED!
# current_state: "agendando"  ✅

# ❌ Should NOT be:
# state_machine_state: "confirmation"  (this means Update still not executing)
```
- [ ] Database state updates to "trigger_wf06_next_dates" or "process_date_selection"
- [ ] Database state is NOT stuck at "confirmation"
- [ ] collected_data.current_stage matches state_machine_state

### Test 3: Verify Logs Show Update BEFORE WF06
```bash
# Monitor logs during date selection
docker logs -f e2bot-n8n-dev | grep -E "Update Conversation State|WF06|Check If"

# Expected log sequence:
# 1. "Update Conversation State" executes ✅
# 2. "Check If WF06 Next Dates" evaluates ✅
# 3. "WF06 HTTP Request" executes ✅
# (Update happens BEFORE WF06 call!)

# ❌ Should NOT see:
# "Check If WF06" before "Update Conversation State"
```
- [ ] Logs show Update Conversation State executes before Check If WF06
- [ ] Logs show correct execution sequence
- [ ] No errors in logs

### Test 4: Complete Scheduling Flow
```bash
# Continue workflow after date selection:
# 1. User selects date → sees time slots ✅
# 2. User selects time → sees confirmation ✅
# 3. User confirms → booking created ✅

# No infinite loops at any stage
```
- [ ] User can complete entire scheduling flow
- [ ] No infinite loops at date selection stage
- [ ] No infinite loops at time selection stage
- [ ] Booking successfully created in database

---

## 📊 SUCCESS CRITERIA

### All Must Be True
- [ ] No infinite loop when selecting dates (Test 1)
- [ ] Database state updates BEFORE WF06 routes (Test 2)
- [ ] Logs show correct execution sequence (Test 3)
- [ ] User can complete full scheduling flow (Test 4)
- [ ] Update Conversation State executes exactly ONCE per message, before routing

### Expected Improvements
- **Infinite loops on WF06 routes**: 100% → 0% ✅
- **Database updates on ALL routes**: 0% (WF06 routes) → 100% ✅
- **State sync reliability**: Inconsistent → Guaranteed ✅
- **Successful scheduling completions**: ~0% → 100% ✅

---

## 🚨 ROLLBACK PROCEDURE

If infinite loop persists or new issues appear:

### Step 1: Restore Old Connections
```bash
# 1. Open: http://localhost:5678/workflow/9tG2gR6KBt6nYyHT
# 2. Disconnect: Update Conversation State from its new position
# 3. Reconnect: Build Update Queries → Check If WF06 Next Dates (old connection)
# 4. Reconnect: Check If WF06 Available Slots FALSE → Update Conversation State (old connection)
# 5. Save workflow
```

### Step 2: Verify Rollback
```bash
# Send test message "oi" → verify workflow executes without errors
# (Will have infinite loop again, but confirms rollback successful)
```

### Step 3: Import Backup (if needed)
```bash
# 1. Open n8n UI
# 2. Click "..." menu → Import from file
# 3. Select: n8n/workflows/backup/02_ai_agent_conversation_PRE_V105_backup.json
# 4. Confirm import
# 5. Activate workflow
```

---

## 📁 RELATED DOCUMENTATION

**This Deployment**:
- Bugfix Analysis: `docs/fix/BUGFIX_WF02_V105_WF06_ROUTING_STATE_UPDATE.md`
- This Deployment Guide: `docs/deployment/DEPLOY_WF02_V105_WF06_ROUTING_FIX.md`

**Previous Deployments** (MUST be completed first):
- V104 State Machine: `docs/deployment/DEPLOY_WF02_V104_STATE_MACHINE.md`
- V104.2 Build Update Queries: `docs/deployment/DEPLOY_WF02_V104_2_BUILD_UPDATE_QUERIES_COMPLETE_FIX.md`

**Code Files** (No changes needed for V105):
- V104 State Machine: `scripts/wf02-v104-database-state-update-fix.js` (already deployed)
- V104.2 Build Update Queries: `scripts/wf02-v104_2-build-update-queries-schema-fix.js` (already deployed)

---

## 🎓 KEY LEARNINGS

### n8n Conditional Routing Patterns
1. **State Updates Must Be Unconditional**: Place state updates BEFORE any conditional routing, not on specific branches
2. **Database Persistence First**: Always persist state changes before branching logic that depends on that state
3. **TRUE/FALSE Branch Coverage**: Ensure critical operations like database updates execute on ALL branches, or better yet, BEFORE branching
4. **Workflow Connection Order Matters**: Order of node connections determines execution flow - disconnecting and reconnecting changes behavior

### Multi-Path Workflow Architecture
1. **Common Path First**: Execute shared operations (like state updates) before conditional splits
2. **State Guarantees**: Database state must be updated regardless of which route is taken
3. **Route Independence**: Each route should assume state is already persisted, not responsible for persisting it
4. **Visual Verification**: Workflow diagram should clearly show update happens first, then routing decisions

### Debugging Workflow Routing Issues
1. **Check Execution Logs**: Verify which nodes actually executed, in what order
2. **Database Timing**: Check database state at different points in execution to see when updates happen
3. **Branch Coverage Testing**: Test ALL conditional branches to ensure state persistence works everywhere
4. **Connection Flow Tracing**: Trace node connections visually in n8n UI to understand execution path

---

**Status**: V105 workflow routing fix ready for deployment
**Deployment Type**: n8n workflow connection change (no code changes)
**Deployment Time**: 5 minutes
**Risk Level**: Low (simple connection reordering)
**Impact**: Eliminates infinite loop on WF06 routes by ensuring database updates before routing
**Recommended**: Deploy immediately after V104+V104.2 to complete the infinite loop fix

**Evolution**:
- V104 (state in collected_data) →
- V104.2 (schema fix) →
- V105 (routing fix) = Complete solution
