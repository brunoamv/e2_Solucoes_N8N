# WF02 V91 Root Cause Analysis - Node Connection Issue

**Date**: 2026-04-20
**Status**: 🔴 CRITICAL - V91 Deployed but Still Failing
**Finding**: Workflow architecture issue, not code logic issue

---

## Problem Summary

V91's 4-level fallback chain and explicit `current_stage` return are **CORRECT IN LOGIC** but **CANNOT WORK** due to n8n workflow node connection architecture.

The State Machine executes TWICE, but the second execution **CANNOT ACCESS** the first execution's output due to how Merge nodes work in n8n.

---

## Complete Workflow Flow Analysis

### First State Machine Execution (21:21:07.094)

```
1. User sends message "1" (agendar)
   ↓
2. "Get Conversation Details" (PostgreSQL)
   → Queries DB for phone_number
   → Returns: {city, email, lead_name, service_type, current_state: 'confirmation'}
   ↓
3. "State Machine Logic" (FIRST EXECUTION)
   → Input: currentData = {city, email, lead_name, ...}
   → Processes: State 8 (confirmation)
   → Returns: {
       response_text: "⏳ Buscando próximas datas...",
       next_stage: "trigger_wf06_next_dates",
       current_stage: "trigger_wf06_next_dates"  // V91 NEW
     }
   ↓
4. "Build Update Queries"
   → Generates SQL: UPDATE conversations SET current_state = 'trigger_wf06_next_dates'
   ↓
5. "Update Conversation DB" (PostgreSQL)
   → Executes UPDATE
   → DB now has: current_state = 'trigger_wf06_next_dates'
   ↓
6. "Switch on next_stage"
   → Checks: next_stage === 'trigger_wf06_next_dates'
   → Routes to: "HTTP Request - Get Next Dates"
   ↓
7. "HTTP Request - Get Next Dates" (WF06)
   → Calls: http://e2bot-n8n-dev:5678/webhook/calendar-availability
   → Returns: {success: true, dates: [...]}
   ↓
8. "Prepare WF06 Next Dates Data"
   → Adds: wf06_next_dates to output
   ↓
9. "Merge WF06 Next Dates with User Data"
   → Input 0: From "Prepare WF06 Next Dates Data" (has wf06_next_dates)
   → Input 1: From "Get Conversation Details" ← 🔴 PROBLEM HERE!
   ↓
```

### The Critical Issue: Merge Node Input 1

**Merge Node Configuration**:
- **Input 0**: Latest data from "Prepare WF06 Next Dates Data"
- **Input 1**: **OLD DATA** from "Get Conversation Details" (queried at start, never re-executed)

**"Get Conversation Details" executed ONCE at the beginning**:
```sql
SELECT * FROM conversations WHERE phone_number = '556181755748'
```

This returned:
```json
{
  "city": "Goiânia",
  "email": "bruno@example.com",
  "lead_name": "Bruno",
  "service_type": "energia_solar",
  "current_state": "confirmation",  // ← OLD STATE (before first State Machine)
  "collected_data": {...}  // ← Does NOT have next_stage from first State Machine
}
```

The Merge node combines:
- Input 0: `{wf06_next_dates: [...], ...}`
- Input 1: `{city, email, lead_name, current_state: "confirmation"}` ← OLD DATA

### Second State Machine Execution (21:21:07.774)

```
10. "State Machine Logic" (SECOND EXECUTION)
    → Input received from Merge:
      {
        wf06_next_dates: [...],
        city: "Goiânia",
        email: "bruno@example.com",
        current_state: "confirmation" ← OLD STATE!
        // NO next_stage from first State Machine
        // NO current_stage: "show_available_dates" from first State Machine
      }

    → V91 State Resolution:
      input.current_stage: undefined  // Merge didn't pass this
      input.next_stage: undefined     // Merge didn't pass this
      currentData.current_stage: "confirmation" ← OLD!
      currentData.next_stage: undefined  // DB has current_state only

    → Result: Defaults to 'greeting' ❌
    → Next stage: 'service_selection' ❌
```

---

## Why V91 Cannot Work

**V91 Assumptions (Incorrect)**:
1. ❌ `input.current_stage` would be passed from first State Machine execution
   - **Reality**: Merge node doesn't pass this field
2. ❌ `input.next_stage` would be accessible from first State Machine
   - **Reality**: Merge node doesn't have access to first State Machine output
3. ❌ `currentData.next_stage` would be in database
   - **Reality**: Database only has `current_state`, not `next_stage`
4. ❌ "Get Conversation Details" would re-query after State Machine updates
   - **Reality**: It executes ONCE at workflow start, never again

**What Actually Happens**:
- First State Machine returns `{current_stage: "show_available_dates"}` ✅
- But this data goes to "Build Update Queries" node, NOT to Merge node ❌
- Merge node Input 1 is hardcoded to "Get Conversation Details" which ran at the START ❌
- Second State Machine receives OLD database state with NO next_stage information ❌

---

## The Fundamental Architecture Issue

**n8n Workflow Limitation**:
- Nodes connect in a DAG (Directed Acyclic Graph)
- "Get Conversation Details" → "Merge" connection is STATIC
- Even though State Machine updates database, Merge still uses OLD data
- No way for Merge Input 1 to "refresh" or "re-query" the database

**Execution Timeline**:
```
T0: "Get Conversation Details" executes → Snapshot A (current_state: 'confirmation')
T1: First "State Machine Logic" executes → Updates DB to 'trigger_wf06_next_dates'
T2: HTTP Request executes
T3: Merge combines: New WF06 data + Snapshot A (STALE!)
T4: Second "State Machine Logic" receives Snapshot A → FAILS ❌
```

---

## V92 Solution Options

### Option 1: Explicit Node Reference (Recommended)
Modify Merge node to use explicit reference to first State Machine output:

```javascript
// In second State Machine execution
const firstStateMachineOutput = $node["State Machine Logic"].json;
const currentStage = firstStateMachineOutput.next_stage ||
                     input.current_stage ||
                     'greeting';
```

**Pros**: No workflow structure changes
**Cons**: Requires State Machine code modification to detect which execution it is

### Option 2: Re-query Database After HTTP Request
Add new "Get Conversation Details (Refresh)" node between HTTP Request and Merge:

```
HTTP Request → Prepare Data → NEW: Get Conv Details (Refresh) → Merge → State Machine
```

**Pros**: Clean architecture, always has latest DB state
**Cons**: Extra database query (performance impact)

### Option 3: Pass State Through HTTP Request Path
Store `next_stage` in HTTP Request body and return it in response:

```
HTTP Request sends: {action: "next_dates", return_to_state: "show_available_dates"}
WF06 returns: {dates: [...], return_to_state: "show_available_dates"}
```

**Pros**: No extra DB query, explicit state passing
**Cons**: Requires WF06 modification

### Option 4: Use collected_data JSONB Field
Store `next_stage` in `collected_data` JSONB field in database:

```sql
UPDATE conversations
SET collected_data = jsonb_set(collected_data, '{next_stage}', '"show_available_dates"')
```

Then "Get Conversation Details (Refresh)" can retrieve it.

**Pros**: No workflow structure changes, database already supports it
**Cons**: Requires SQL query modification + refresh node

---

## Recommended Solution: V92 Hybrid Approach

**Combine Option 1 + Option 4**:

1. **Store `next_stage` in Database** (Option 4):
   - Modify "Build Update Queries" to store `next_stage` in `collected_data`
   - SQL: `UPDATE conversations SET collected_data = jsonb_set(..., '{next_stage}', ...)`

2. **Add Refresh Node** (Option 2):
   - Insert "Get Conversation Details (Refresh)" after HTTP Request
   - Query: `SELECT * FROM conversations WHERE phone_number = ...`
   - This retrieves fresh `collected_data` with `next_stage`

3. **Update State Machine** (Option 1):
   - Add fallback to `collected_data.next_stage`
   - Full chain: `input.current_stage → input.next_stage → currentData.collected_data.next_stage → 'greeting'`

**Why This Works**:
- Database UPDATE happens BEFORE HTTP Request
- Refresh query AFTER HTTP Request gets updated `collected_data`
- State Machine receives fresh data with `next_stage` preserved
- No hardcoded states, clean architecture

---

## Files to Modify for V92

1. **`scripts/wf02-v92-state-initialization-with-refresh.js`** (NEW)
   - State Machine code with `collected_data.next_stage` fallback

2. **`n8n/workflows/02_ai_agent_conversation_V92.json`** (NEW)
   - Add "Get Conversation Details (Refresh)" node
   - Position: After "Prepare WF06 Next Dates Data", before "Merge"

3. **Modify "Build Update Queries" node**:
   - Add: `UPDATE ... SET collected_data = jsonb_set(collected_data, '{next_stage}', ...)`

---

## Next Steps

1. ✅ **Analysis Complete**: Root cause identified (Merge node uses stale data)
2. 🔴 **V92 Implementation**: Create solution with database refresh
3. 🔴 **Testing**: Validate V92 with execution logs
4. 🔴 **Documentation**: Update deployment guides

---

**Status**: Ready for V92 implementation
**Risk**: 🔴 CRITICAL - Production workflow broken until V92 deployed
**Timeline**: V92 solution can be implemented immediately
