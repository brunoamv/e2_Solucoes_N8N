# BUGFIX WF02 V111 - Database State Race Condition Fix

**Date**: 2026-04-28
**Version**: WF02 V111
**Severity**: 🔴 CRITICAL - Database state race condition causing stale data processing
**Root Cause**: PostgreSQL transaction isolation + rapid message timing
**Status**: SOLUTION READY FOR IMPLEMENTATION

---

## 🎯 Executive Summary

**Problem**: WF06 HTTP Request never executes because workflow processes STALE database state from previous execution.

**Root Cause**: Database race condition - when user sends message while previous workflow execution is still updating database, the new execution reads OLD state before database commit completes.

**Evidence from Logs**:
- **18:52:46**: Workflow processes `collect_city` state (STALE from previous message)
- **18:52:49**: Workflow processes `confirmation` state (CORRECT for current message "1")
- **Result**: First execution takes wrong path → Check If WF06 evaluates FALSE → No HTTP Request

**Solution**: Add proper synchronization to ensure database updates complete BEFORE next workflow reads state.

---

## 🔍 Complete Root Cause Analysis

### Evidence from Execution Logs

**Execution #1 (18:52:46) - STALE STATE PROCESSING**:
```
=== V110 STATE MACHINE START ===
V110: conversation_id: e2a712bc-0946-4dba-82e6-0ec3b97209d7
V110: Current stage: collect_city  ← ❌ WRONG! Should be "confirmation"
V110: Is intermediate state: false
V110: Forced stage from awaiting flag: null
=== V110 STATE MACHINE END ===

Node Execution Sequence:
1. State Machine Logic ✅ (processes collect_city)
2. Build Update Queries ✅ (gets next_stage for collect_city → confirmation transition)
3. Update Conversation State ✅ (updates DB to confirmation)
4. Check If WF06 Next Dates ✅ (evaluates condition)
   - Condition: $node['Build Update Queries'].json.next_stage == "trigger_wf06_next_dates"
   - Actual value: "confirmation" (from collect_city → confirmation transition)
   - Result: FALSE ❌
5. Check If WF06 Available Slots ✅ (FALSE path taken)
6. Check If Scheduling ✅ (FALSE path)
7. Check If Handoff ✅ (FALSE path)
8. Workflow continues to Send WhatsApp Response (sends confirmation message)
```

**Execution #2 (18:52:49) - CORRECT STATE PROCESSING**:
```
=== V110 STATE MACHINE START ===
V110: conversation_id: e2a712bc-0946-4dba-82e6-0ec3b97209d7
V110: Current stage: confirmation  ← ✅ CORRECT! User typed "1" at confirmation
V110: Is intermediate state: false
V110: Forced stage from awaiting flag: null
=== V110 STATE MACHINE END ===

Node Execution Sequence:
1. State Machine Logic ✅ (processes confirmation + message "1")
2. Build Update Queries ✅ (gets next_stage: "trigger_wf06_next_dates")
3. Update Conversation State ✅ (updates DB to trigger_wf06_next_dates)
4. Check If WF06 Next Dates ✅ (evaluates condition)
   - Condition: $node['Build Update Queries'].json.next_stage == "trigger_wf06_next_dates"
   - Actual value: "trigger_wf06_next_dates" ✅
   - Result: TRUE ✅
5. BUT: User already in intermediate state from this execution!
6. V110 Handler: Detects intermediate state + message → Shows error message
```

### The Race Condition Explained

**Timeline of Events**:

```
T0: User types city name "cocal-go"
    - Workflow execution #1 starts
    - State Machine: collect_city → confirmation
    - Database UPDATE starts (but not committed yet)

T1: User types "1" (agendar) IMMEDIATELY
    - Workflow execution #2 starts
    - Query database for current state
    - Database still shows: collect_city (UPDATE from T0 not visible yet!)

T2: Execution #1 database commit completes
    - Database now shows: confirmation
    - But execution #2 already read old state!

T3: Execution #2 processes with stale state
    - State Machine thinks current stage is collect_city
    - Processes city name input again
    - next_stage becomes confirmation (not trigger_wf06_next_dates)
    - Check If WF06 evaluates FALSE
    - No HTTP Request executed

T4: User sends another message "1" OR rapid messages trigger execution #3
    - Now database shows confirmation (from T2)
    - State Machine correctly processes confirmation → trigger_wf06_next_dates
    - But now user is stuck in intermediate state!
```

**Why This Happens**:

1. **PostgreSQL Transaction Isolation**: Default isolation level is READ COMMITTED, but n8n might be using REPEATABLE READ or there's a timing issue with transaction commits

2. **Rapid User Messages**: User sends messages faster than database can commit updates

3. **n8n Parallel Execution**: n8n might process multiple webhook calls in parallel, causing concurrent reads of same database state

4. **No Synchronization**: No locking mechanism to prevent reading state while update is in progress

---

## 🔧 V111 Solution Strategy

### Solution 1: Add Database Row Locking (RECOMMENDED)

**Concept**: Use PostgreSQL row-level locking to ensure only ONE workflow execution can process a conversation at a time.

**Implementation**: Update "Get User Context" node (the node that reads from database at workflow start) to use `FOR UPDATE SKIP LOCKED`:

```sql
SELECT
  id,
  phone_number,
  whatsapp_name,
  current_state,
  state_machine_state,
  collected_data,
  service_type,
  created_at,
  updated_at
FROM conversations
WHERE phone_number = '{{ $json.phone_number }}'
FOR UPDATE SKIP LOCKED;  -- ← ADD THIS
```

**How It Works**:
- `FOR UPDATE`: Locks the row until transaction commits
- `SKIP LOCKED`: If row is already locked (another execution in progress), skip and return nothing
- Result: Only ONE execution can process a conversation at a time

**Pros**:
- ✅ Prevents race conditions completely
- ✅ Minimal code changes (just add to SQL query)
- ✅ PostgreSQL native solution (fast and reliable)
- ✅ Works for all concurrent scenarios

**Cons**:
- ⚠️ If SKIP LOCKED returns nothing, workflow might fail
- ⚠️ Need to handle case where row is locked

### Solution 2: Add Workflow Execution Deduplication

**Concept**: Use n8n's built-in deduplication to prevent multiple executions for same user in short time window.

**Implementation**: Add "Wait" node after webhook with short delay + execution ID check:

```javascript
// In a Code node after webhook
const executionId = $executionId;
const conversationId = $input.first().json.conversation_id;
const lockKey = `wf02_${conversationId}`;

// Check if another execution is in progress
const lockExists = $workflow.getStaticData('global')[lockKey];

if (lockExists) {
  console.log('V111: Execution already in progress, skipping duplicate');
  return [];  // Skip this execution
}

// Set lock
$workflow.getStaticData('global')[lockKey] = executionId;

// Continue workflow...
```

**Pros**:
- ✅ Prevents duplicate executions
- ✅ No database changes needed
- ✅ Works at n8n level

**Cons**:
- ⚠️ Requires careful lock cleanup
- ⚠️ More complex logic
- ⚠️ Still has race condition window (very small)

### Solution 3: Implement Optimistic Locking

**Concept**: Add version number to database, check it hasn't changed before committing updates.

**Implementation**: Add `version` column to conversations table, increment on each update:

```sql
-- Update query becomes:
UPDATE conversations
SET
  state_machine_state = '{{ $json.next_stage }}',
  collected_data = '{{ $json.collected_data }}'::jsonb,
  version = version + 1,  -- ← Increment version
  updated_at = NOW()
WHERE phone_number = '{{ $json.phone_number }}'
  AND version = {{ $json.current_version }}  -- ← Check version hasn't changed
RETURNING *;
```

**Pros**:
- ✅ Detects concurrent updates
- ✅ Application-level solution
- ✅ Clear failure mode (update fails if version mismatch)

**Cons**:
- ⚠️ Requires schema migration (add version column)
- ⚠️ Need to handle update failures
- ⚠️ More complex implementation

---

## 🚀 V111 Implementation Plan (RECOMMENDED: Solution 1)

### Step 1: Identify Node That Builds Initial Query

**Node Found**: "Build SQL Queries" (Code/JavaScript node)
- **Type**: n8n-nodes-base.code
- **ID**: 0e0404b8-f48d-4b74-a607-ac231d950fe4
- **Location**: Early in workflow (after Prepare Phone Formats)
- **Function**: Builds all SQL queries including `query_details` for conversation lookup

```bash
# Verify node exists in workflow:
jq '.nodes[] | select(.name == "Build SQL Queries") | {name, type, id}' /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/wk02_v102_1.json
```

### Step 2: Update query_details SQL to Add Row Locking

Open workflow in n8n UI: http://localhost:5678/workflow/9tG2gR6KBt6nYyHT

Find node: **"Build SQL Queries"** (JavaScript Code node)

Locate the `query_details` variable definition (around line 30) and add `FOR UPDATE SKIP LOCKED`:

**Before** (Current V28):
```javascript
// Query para buscar detalhes da conversa
const query_details = `
  SELECT
    *,
    COALESCE(state_machine_state,
      CASE current_state
        WHEN 'novo' THEN 'greeting'
        WHEN 'identificando_servico' THEN 'service_selection'
        WHEN 'coletando_dados' THEN 'collect_name'
        WHEN 'agendando' THEN 'scheduling'
        WHEN 'handoff_comercial' THEN 'handoff_comercial'
        WHEN 'concluido' THEN 'completed'
        ELSE 'greeting'
      END
    ) as state_for_machine
  FROM conversations
  WHERE phone_number IN ('${escapeSql(phone_with_code)}', '${escapeSql(phone_without_code)}')
  ORDER BY updated_at DESC
  LIMIT 1
`.trim();
```

**After** (V111 Fix):
```javascript
// Query para buscar detalhes da conversa
// V111 CRITICAL: Adiciona FOR UPDATE SKIP LOCKED para prevenir race conditions
const query_details = `
  SELECT
    *,
    COALESCE(state_machine_state,
      CASE current_state
        WHEN 'novo' THEN 'greeting'
        WHEN 'identificando_servico' THEN 'service_selection'
        WHEN 'coletando_dados' THEN 'collect_name'
        WHEN 'agendando' THEN 'scheduling'
        WHEN 'handoff_comercial' THEN 'handoff_comercial'
        WHEN 'concluido' THEN 'completed'
        ELSE 'greeting'
      END
    ) as state_for_machine
  FROM conversations
  WHERE phone_number IN ('${escapeSql(phone_with_code)}', '${escapeSql(phone_without_code)}')
  ORDER BY updated_at DESC
  LIMIT 1
  FOR UPDATE SKIP LOCKED
`.trim();
```

**Critical Change**: Add `FOR UPDATE SKIP LOCKED` before the closing `.trim()`

**Optional V111 Logging** (Add after query_details definition):
```javascript
// V111: Log para debug
console.log('=== V111 DATABASE ROW LOCKING ENABLED ===');
console.log('V111: FOR UPDATE SKIP LOCKED added to query_details');
```

### Step 3: Handle Empty Result (Row Locked)

Add an IF node after "Get User Context" to check if result is empty:

```javascript
// IF node condition
{{ $json.id !== undefined }}
```

**TRUE path**: Continue normal workflow (row acquired, no concurrent execution)

**FALSE path**: Send message to user and end workflow:
```
⏳ *Processando sua mensagem anterior...*

Por favor, aguarde um momento enquanto processamos sua solicitação anterior.

_Se demorar mais de 10 segundos, tente novamente._
```

### Step 4: Test Race Condition Scenarios

**Test 1: Rapid Messages**
```bash
# Send 3 messages rapidly (< 1 second apart)
# Message 1: "cocal-go" (city)
# Message 2: "1" (agendar)  ← Should NOT process with stale state
# Message 3: "test"

# Expected: Only first message processed, others get "Processando" message
```

**Test 2: Concurrent Requests**
```bash
# Simulate two users with same phone number (shouldn't happen, but test anyway)
# Both send messages at exact same time

# Expected: One processes, other gets "Processando" message
```

**Test 3: Normal Flow**
```bash
# Normal conversation flow with 2-3 second gaps between messages
# Message 1: "cocal-go" → Wait 2s
# Message 2: "1" → Wait 2s
# Message 3: Select date

# Expected: All messages process normally (no "Processando" messages)
```

### Step 5: Verify Database Locking

```sql
-- Check for locked rows during execution
SELECT
  pid,
  usename,
  pg_blocking_pids(pid) as blocked_by,
  query,
  state
FROM pg_stat_activity
WHERE datname = 'e2bot_dev'
  AND query LIKE '%conversations%FOR UPDATE%';
```

Expected during concurrent executions:
- One process holding lock (state: active)
- Other processes skipped (SKIP LOCKED returned empty result)

---

## 📋 Alternative Quick Fix (If Solution 1 Not Feasible)

If row locking is not feasible, implement a simpler workaround:

### Add Message Rate Limiting in n8n

Add a "Wait" node at the very beginning of the workflow (after webhook):

```javascript
// Code node: Check Message Rate
const conversationId = $input.first().json.conversation_id;
const messageTimestamp = Date.now();

// Get last message timestamp
const lastTimestamp = $workflow.getStaticData('global')[`last_msg_${conversationId}`] || 0;

// If message came too quickly (< 1 second), delay it
if (messageTimestamp - lastTimestamp < 1000) {
  console.log('V111: Rate limiting - message too quick, delaying 1 second');
  await new Promise(resolve => setTimeout(resolve, 1000));
}

// Update last message timestamp
$workflow.getStaticData('global')[`last_msg_${conversationId}`] = messageTimestamp;

return $input.all();
```

**Pros**:
- ✅ Simple to implement
- ✅ No database changes
- ✅ Reduces race condition window

**Cons**:
- ⚠️ Doesn't eliminate race condition completely
- ⚠️ Adds delay to all rapid messages (even intentional ones)
- ⚠️ Temporary workaround, not a real fix

---

## ✅ Success Criteria

After implementing V111:

1. **No Stale State Processing**:
   - ✅ Workflow always reads most recent database state
   - ✅ No execution processes with state from 2+ messages ago

2. **WF06 HTTP Request Executes**:
   - ✅ When user types "1" at confirmation, Check If WF06 evaluates TRUE
   - ✅ HTTP Request - Get Next Dates executes immediately after
   - ✅ User receives dates within 2-3 seconds

3. **No Duplicate Executions**:
   - ✅ Only one workflow execution processes a conversation at a time
   - ✅ Concurrent messages either queued or informed to wait

4. **Database Consistency**:
   - ✅ Database state always reflects most recent completed workflow execution
   - ✅ No partial updates visible to subsequent executions

5. **User Experience**:
   - ✅ Normal message timing (2-3 seconds between messages) works perfectly
   - ✅ Rapid messages handled gracefully (either queued or informed to wait)
   - ✅ No more V110 error messages for intermediate state scenarios

---

## 🔄 Rollback Procedure

If V111 causes issues:

1. **Remove Row Locking**:
   - Open workflow: http://localhost:5678/workflow/9tG2gR6KBt6nYyHT
   - Find "Get User Context" node
   - Remove `FOR UPDATE SKIP LOCKED` from SQL query
   - Save workflow

2. **Verify Rollback**:
   - Test normal conversation flow
   - Confirm messages process (even if with race condition bug)

**Note**: Rollback returns to V110 state - race condition persists but V110 error handling protects user experience.

---

## 📁 Related Documentation

- **V111 Quick Deploy Guide**: `docs/WF02_V111_QUICK_DEPLOY.md` ⭐ START HERE
- **V111 Build SQL Queries Code**: `scripts/wf02-v111-build-sql-queries-row-locking.js`
- **V110 Root Cause Analysis**: `docs/fix/BUGFIX_WF02_V110_EXECUTION_9045_COMPLETE_ROOT_CAUSE.md`
- **V110 State Machine Code**: `scripts/wf02-v110-intermediate-state-message-handler.js`
- **Active Workflow File**: `/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/wk02_v102_1.json`
- **Database Schema**: `docs/Setups/DATABASE_SCHEMA.md`

---

**Analysis Date**: 2026-04-28 07:00 BRT
**Analyst**: Claude Code Analysis System
**Status**: ✅ SOLUTION READY FOR IMPLEMENTATION
**Recommended Solution**: Solution 1 (Database Row Locking with FOR UPDATE SKIP LOCKED)
**Next Action**: Implement V111 database row locking in "Get User Context" node
**Estimated Implementation Time**: 15-20 minutes
**Risk Level**: LOW (PostgreSQL row locking is well-tested and reliable)
