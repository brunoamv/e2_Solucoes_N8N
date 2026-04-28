# BUGFIX WF02 V103 - State Machine Input Data Access Fix

**Date**: 2026-04-27
**Workflow ID**: 9tG2gR6KBt6nYyHT
**Execution**: 8274
**Problem**: State Machine tries to access `$node["Build Update Queries"].json` but node hasn't been executed in this flow path

---

## 🐛 PROBLEM ANALYSIS

### Error Message
```
Problem in node 'State Machine Logic'
Node 'Build Update Queries' hasn't been executed [Line 10]
```

### Execution Flow (From Logs)
```
21:28:25.181 Process New User Data V57 started ✅
21:28:25.181 Process New User Data V57 finished successfully ✅
21:28:25.181 State Machine Logic started
21:28:25.245 State Machine Logic finished with ERROR ❌
  → ExpressionError: Node 'Build Update Queries' hasn't been executed
  → At Line 10: const userData = $node["Build Update Queries"].json;
```

### Workflow Structure Problem

**Current Flow (BROKEN)**:
```
Process New User Data V57
  ↓
State Machine Logic ❌ (tries to access Build Update Queries)
  → ERROR: Build Update Queries hasn't been executed!
```

**Why Build Update Queries Wasn't Executed**:
- "Process New User Data V57" connects DIRECTLY to "State Machine Logic"
- "Build Update Queries" is in a DIFFERENT workflow path (after State Machine)
- State Machine V101 code assumes "Build Update Queries" already ran
- This assumption is WRONG for this execution path

### Root Cause

**State Machine Logic V101 Code** (Line 10):
```javascript
const userData = $node["Build Update Queries"].json;
```

**Problem**: This code is in "Prepare WF06 Next Dates Data" node, NOT in State Machine!

### Actual Problem Identified

Looking at the exported code, the issue is that **"Prepare WF06 Next Dates Data"** node is being used as **"State Machine Logic"** or the State Machine is trying to access Build Update Queries directly.

**Two possibilities**:
1. Wrong node code in "State Machine Logic"
2. Wrong connection path executing wrong nodes

---

## ✅ SOLUTION V103

### Fix 1: Verify State Machine Code

**State Machine Logic** should use `$input.first().json`, NOT `$node["Build Update Queries"].json`

**CORRECT State Machine Pattern**:
```javascript
// Get input data from previous node (whoever called us)
const input = $input.first().json;

// Extract data with fallback chain
const currentData = {
  ...(input.currentData || {}),
  ...(input.collected_data || {}),

  // Fallback chain with root-level access
  lead_name: input.lead_name || input.currentData?.lead_name || input.collected_data?.lead_name,
  email: input.email || input.currentData?.email || input.collected_data?.email,
  phone_number: input.phone_number || input.currentData?.phone_number || input.collected_data?.phone_number,
  // ... other fields
};
```

**NEVER reference specific nodes by name in State Machine!** Use `$input` instead.

### Fix 2: Correct Workflow Connections

**Process New User Data V57** should output data in correct format for State Machine:

```javascript
// Process New User Data V57 OUTPUT
return {
  json: {
    phone_number: phoneNumber,
    conversation_id: conversationId,
    collected_data: {
      lead_name: name,
      email: email,
      city: city,
      service_type: serviceType,
      // ... all collected fields
    },
    current_stage: currentStage,
    // All other required fields
  }
};
```

### Fix 3: State Machine Should ONLY Use $input

**Update State Machine Logic V103**:

```javascript
// WF02 V103 STATE MACHINE - INPUT DATA ACCESS FIX
// CRITICAL: Use $input ONLY, never reference specific nodes

const input = $input.first().json;

console.log('=== STATE MACHINE V103 ===');
console.log('Input source: $input.first().json');
console.log('Input keys:', Object.keys(input));

// NEVER use $node["Build Update Queries"].json
// ALWAYS use $input.first().json

const currentData = {
  ...(input.currentData || {}),
  ...(input.collected_data || {}),

  // V103 FIX: Only use input data, no node references
  lead_name: input.lead_name || input.currentData?.lead_name || input.collected_data?.lead_name || input.contact_name,
  email: input.email || input.currentData?.email || input.collected_data?.email || input.contact_email,
  phone_number: input.phone_number || input.currentData?.phone_number || input.collected_data?.phone_number || input.phone_with_code,
  // ... rest of State Machine logic
};

// Continue with normal State Machine logic...
```

---

## 🔧 IMPLEMENTATION STEPS

### Step 1: Identify Which Node Has Wrong Code

1. Open workflow: http://localhost:5678/workflow/9tG2gR6KBt6nYyHT
2. Click "State Machine Logic" node
3. Check if code contains: `const userData = $node["Build Update Queries"].json;`
4. If YES → This is WRONG code (V101 Prepare WF06 code)

### Step 2: Replace with Correct State Machine Code

**Replace entire "State Machine Logic" code** with V100/V101 State Machine code that uses `$input.first().json`

**File**: `/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/scripts/wf02-v100-collected-data-fix.js`

OR if using V101:
**File**: `/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/scripts/wf02-v101-state-initialization-fix.js`

### Step 3: Verify "Prepare WF06 Next Dates Data" Node

**Check if this node exists separately**:
- Should be AFTER "WF06 HTTP Request Next Dates"
- Should use `$node["Build Update Queries"].json` (CORRECT for this node)
- Should NOT be the same as "State Machine Logic"

### Step 4: Fix Node Names and Connections

**Correct Structure**:
```
Process New User Data V57
  ↓
State Machine Logic (uses $input.first().json) ✅
  ↓
Build Update Queries
  ↓
Check If WF06 Next Dates (IF node)
  → TRUE: WF06 HTTP Request Next Dates
    ↓
  Prepare WF06 Next Dates Data (uses $node["Build Update Queries"].json) ✅
    ↓
  Build WF06 Response Message
    ↓
  Send WhatsApp Response
```

---

## 📊 VALIDATION

### Test Normal Flow (Without WF06)
```bash
# User completes data collection
# Expected: State Machine processes normally ✅
# Validation: No "Build Update Queries hasn't been executed" error
```

### Test WF06 Flow
```bash
# User confirms → trigger_wf06_next_dates
# Expected: WF06 calendar dates returned ✅
# Validation: Both State Machine AND Prepare WF06 work correctly
```

### Check Logs
```bash
docker logs -f e2bot-n8n-dev | grep -E "STATE MACHINE V10|hasn't been executed|Line 10"

# Expected (AFTER FIX):
# ✅ STATE MACHINE V103: Input source: $input.first().json
# ❌ Should NOT see "Build Update Queries hasn't been executed"
```

---

## 🚨 CRITICAL DISCOVERY

**The real issue**: Wrong code was pasted into "State Machine Logic" node!

The code with `const userData = $node["Build Update Queries"].json;` is from **"Prepare WF06 Next Dates Data V101"** script, NOT from State Machine!

**Correct Assignment**:
- **State Machine Logic** → wf02-v100-collected-data-fix.js OR wf02-v101-state-initialization-fix.js
- **Prepare WF06 Next Dates Data** → fix-wf02-v101-prepare-wf06-data-preservation.js

---

**Status**: Root cause identified - wrong code in State Machine node
**Priority**: CRITICAL - blocks all conversation flows
**Deployment**: Immediate - replace State Machine code with correct version

