# WF02 V92 - Database Refresh Solution

**Date**: 2026-04-20
**Priority**: 🔴 CRITICAL
**Status**: Planning

---

## Problem

Logs from execution 4258 confirm V91 root cause:
- **Merge node Input 1** uses "Get Conversation Details" from workflow START (stale data)
- **First State Machine** updates database with `current_state: 'trigger_wf06_next_dates'`
- **HTTP Request** executes WF06
- **Second State Machine** receives STALE data from Merge (current_state: 'confirmation')
- **Result**: ALL stage sources undefined → defaults to 'greeting' ❌

**Why V91 4-Level Fallback Cannot Work**:
- `input.current_stage`: Not passed by Merge node
- `input.next_stage`: Not accessible (first State Machine output not in Merge)
- `currentData.current_stage`: OLD value ('confirmation' not 'trigger_wf06_next_dates')
- `currentData.next_stage`: Doesn't exist (database only has `current_state`)

---

## V92 Solution: Database Refresh After HTTP Request

### Approach

Add **"Get Conversation Details (Refresh)"** node after HTTP Request to re-query database with latest state.

**New Workflow Flow**:
```
HTTP Request - Get Next Dates
  ↓
Prepare WF06 Next Dates Data
  ↓
Get Conversation Details (Refresh) ← NEW! Re-query database
  ↓
Merge WF06 Next Dates with User Data (Input 0: Prepare, Input 1: Refresh)
  ↓
State Machine Logic (receives FRESH currentData)
```

### Implementation Steps

#### 1. Add "Get Conversation Details (Refresh)" Node

**Node Configuration**:
```json
{
  "parameters": {
    "operation": "executeQuery",
    "query": "=SELECT \n  phone_number,\n  lead_name,\n  contact_name,\n  contact_phone,\n  email,\n  city,\n  service_type,\n  service_selected,\n  current_state,\n  collected_data::text as collected_data_text,\n  created_at,\n  updated_at\nFROM conversations\nWHERE phone_number = '{{ $node[\"Prepare WF06 Next Dates Data\"].json.phone_number }}'\nLIMIT 1;",
    "additionalFields": {}
  },
  "id": "[NEW_UUID]",
  "name": "Get Conversation Details (Refresh)",
  "type": "n8n-nodes-base.postgres",
  "typeVersion": 1,
  "position": [1140, 200],
  "alwaysOutputData": true
}
```

**Why This Works**:
- Uses `$node["Prepare WF06 Next Dates Data"].json.phone_number` for phone lookup
- Executes AFTER "Update Conversation DB" has written `current_state: 'trigger_wf06_next_dates'`
- Returns FRESH database state with latest `current_state` and `collected_data`

#### 2. Update Merge Node Connections

**Change Merge Input 1**:
```json
// BEFORE (V91 - STALE DATA):
"connections": {
  "main": [[
    {"node": "Merge WF06 Next Dates with User Data", "type": "main", "index": 1}
  ]]
}
// Source: "Get Conversation Details" (executed at START)

// AFTER (V92 - FRESH DATA):
"connections": {
  "main": [[
    {"node": "Merge WF06 Next Dates with User Data", "type": "main", "index": 1}
  ]]
}
// Source: "Get Conversation Details (Refresh)" (executed AFTER HTTP Request)
```

#### 3. Update State Machine Code (V92)

**Enhanced State Initialization**:
```javascript
// V92: Add collected_data.next_stage to fallback chain
const collectedData = currentData.collected_data || {};

let currentStage = input.current_stage ||               // 1. Direct from previous node
                   input.next_stage ||                  // 2. From previous State Machine
                   currentData.current_stage ||         // 3. From FRESH database query
                   collectedData.next_stage ||          // 4. From collected_data JSONB ← NEW!
                   'greeting';                          // 5. Default fallback
```

#### 4. (Optional) Store next_stage in collected_data

**Modify "Build Update Queries" Node**:
```javascript
// Build collected_data JSONB update
const collectedDataUpdate = {
  ...currentData.collected_data,
  ...stateData.update_data,
  next_stage: stateData.next_stage  // V92: Store next_stage in collected_data
};

const updateQuery = `
UPDATE conversations
SET
  current_state = '${stateData.next_stage}',
  collected_data = '${JSON.stringify(collectedDataUpdate)}'::jsonb,
  updated_at = NOW()
WHERE phone_number = '${phoneNumber}'
RETURNING *;
`;
```

---

## Expected Result

### With V92 Database Refresh

**Second State Machine Execution**:
```
Input from Merge:
  {
    wf06_next_dates: [...],
    currentData: {
      phone_number: "556181755748",
      city: "Goiânia",
      email: "bruno@example.com",
      current_state: "trigger_wf06_next_dates", ← FRESH! (not 'confirmation')
      collected_data: {
        next_stage: "show_available_dates"  ← NEW! (if stored)
      }
    }
  }

V92 State Resolution:
  input.current_stage: undefined
  input.next_stage: undefined
  currentData.current_state: "trigger_wf06_next_dates" ✅ FRESH!
  collectedData.next_stage: "show_available_dates" ✅ NEW!

  RESOLVED: "trigger_wf06_next_dates" ✅

Switch Statement:
  case 'trigger_wf06_next_dates':
    nextStage = 'show_available_dates' ✅
    responseText = '' ✅ (intermediate state)
```

**Result**: State 10 (show_available_dates) shows 3 dates ✅

---

## Deployment Plan

### Phase 1: Add Refresh Node (Minimal Change)

**Goal**: Get V92 working WITHOUT modifying Build Update Queries

1. **Add Node**: "Get Conversation Details (Refresh)"
2. **Update Connections**: Merge Input 1 → Refresh node
3. **Test**: Verify fresh `current_state` is retrieved

**Pros**: Minimal changes, no SQL modification
**Cons**: Doesn't store `next_stage` in database (relies on switch logic)

### Phase 2: Store next_stage in collected_data (Optional Enhancement)

**Goal**: Make state transitions more explicit

1. **Modify**: "Build Update Queries" to store `next_stage` in `collected_data`
2. **Update**: State Machine V92 to use `collectedData.next_stage`
3. **Test**: Verify `next_stage` survives database round-trip

**Pros**: Explicit state passing, easier debugging
**Cons**: More complex, requires SQL changes

---

## Testing Checklist

**V92 Phase 1 Validation**:
- [ ] "Get Conversation Details (Refresh)" node added
- [ ] Merge Input 1 connects to Refresh node
- [ ] Refresh query uses correct phone_number from Prepare node
- [ ] Logs show fresh `current_state: 'trigger_wf06_next_dates'`
- [ ] Second State Machine resolves to correct state
- [ ] State 10 (show_available_dates) displays 3 dates
- [ ] No "greeting" or "service_selection" fallback

**V92 Phase 2 Validation** (Optional):
- [ ] `collected_data.next_stage` stored in database
- [ ] State Machine V92 accesses `collectedData.next_stage`
- [ ] Logs show `collectedData.next_stage: 'show_available_dates'`

---

## Risk Assessment

**V92 Phase 1**:
- **Risk**: Low (just adds new query node)
- **Impact**: High (fixes critical WF06 integration bug)
- **Rollback**: Easy (remove Refresh node, restore Merge connection)

**V92 Phase 2**:
- **Risk**: Medium (modifies SQL and state machine logic)
- **Impact**: High (better state persistence)
- **Rollback**: Medium (need to revert both SQL and code changes)

---

## Recommendation

**Immediate**: Deploy V92 Phase 1 (Refresh node only)
- Fixes critical bug with minimal changes
- No SQL modification required
- Easy to test and rollback

**Future**: Consider V92 Phase 2 after Phase 1 validation
- More robust long-term solution
- Better debugging with explicit `next_stage` storage

---

## Files to Create

1. **`docs/deployment/DEPLOY_WF02_V92_DATABASE_REFRESH.md`** - Deployment guide
2. **`n8n/workflows/02_ai_agent_conversation_V92.json`** - Workflow with Refresh node
3. **`scripts/wf02-v92-state-machine-with-refresh.js`** - Optional Phase 2 code

---

**Status**: ✅ Ready for V92 Phase 1 implementation
**Next Step**: Create workflow JSON with Refresh node
**Timeline**: Can be deployed immediately (30 minutes)
