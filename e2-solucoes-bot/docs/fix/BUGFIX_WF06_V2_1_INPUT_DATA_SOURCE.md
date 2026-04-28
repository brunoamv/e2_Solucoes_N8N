# BUGFIX WF06 V2.1: Input Data Source Correction

**Problem**: `Cannot read properties of undefined (reading 'length')` on line 3
**Root Cause**: `$input.first().json` receives data from wrong node in n8n flow
**Fix**: Use `$node["Calculate Next Business Days"].json` for request data

---

## Problem Analysis

### Error Details
```
Node: Calculate Slot Availability (line 3)
Error: Cannot read properties of undefined (reading 'length')
Code: const businessDates = inputData.business_dates;
```

### n8n Workflow Flow (Connections)
```
[Calculate Next Business Days] → [Get Calendar Events (Batch)] → [Calculate Slot Availability]
```

### Data Flow Problem

**Calculate Next Business Days** outputs:
```json
{
  "action": "next_dates",
  "count": 3,
  "start_date": "2026-04-18",
  "service_type": "energia_solar",
  "duration_minutes": 120,
  "business_dates": [
    { "date": "2026-04-21", "day_of_week": 1 },
    { "date": "2026-04-22", "day_of_week": 2 },
    { "date": "2026-04-23", "day_of_week": 3 }
  ],
  "dates_to_check": 3
}
```

**Get Calendar Events (Batch)** outputs (EMPTY CALENDAR):
```json
{
  "json": {}  // ← THIS IS WHAT $input.first().json RECEIVES!
}
```

**Calculate Slot Availability** tries to access:
```javascript
const inputData = $input.first().json;  // ← WRONG: receives empty object from Google Calendar!
const businessDates = inputData.business_dates;  // ← UNDEFINED!
const durationMinutes = inputData.duration_minutes;  // ← UNDEFINED!
```

### Why V2 Code Fails

**V2 Assumption** (WRONG):
```javascript
// Assumes $input.first().json contains request data
const inputData = $input.first().json;
```

**n8n Reality**:
- `$input.first().json` = output from **previous node** in flow
- Previous node = "Get Calendar Events (Batch)"
- Empty calendar = `{ json: {} }` → no `business_dates` or `duration_minutes`

---

## V2.1 Fix: Correct Node Reference

### Solution Architecture

**Use explicit node reference** instead of relying on `$input`:

```javascript
// ✅ CORRECT: Get request data from the node that has it
const requestData = $node["Calculate Next Business Days"].json;
const businessDates = requestData.business_dates;
const durationMinutes = requestData.duration_minutes;

// ✅ CORRECT: Get calendar events from Google Calendar node
const rawItems = $('Get Calendar Events (Batch)').all();
const calendarEvents = rawItems
    .map(item => item.json)
    .filter(event => event && (event.id || event.start));
```

### Why This Works

1. **Two Data Sources**:
   - Request data: `$node["Calculate Next Business Days"].json`
   - Calendar events: `$('Get Calendar Events (Batch)').all()`

2. **Independent Access**:
   - `$node["node-name"].json` → access ANY node by name
   - `$('node-name').all()` → access items array from ANY node
   - Not limited to `$input` (previous node only)

3. **Flow-Independent**:
   - Works regardless of workflow connection order
   - Explicitly states data dependencies

---

## Implementation Plan

### Step 1: Update "Calculate Slot Availability" Node

**Location**: WF06 v2, node "Calculate Slot Availability"

**Change**:
```javascript
// OLD (V2 - BROKEN)
const inputData = $input.first().json;
const businessDates = inputData.business_dates;
const durationMinutes = inputData.duration_minutes;

// NEW (V2.1 - FIXED)
const requestData = $node["Calculate Next Business Days"].json;
const businessDates = requestData.business_dates;
const durationMinutes = requestData.duration_minutes;
```

**Full Code**: `/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/scripts/wf06-v2_1-calculate-slot-fix.js`

### Step 2: Apply Same Fix to "Calculate Available Slots" Node

**Location**: WF06 v2, node "Calculate Available Slots"

**Current Code** (MAY have same issue):
```javascript
const inputData = $input.first().json;
const dateStr = inputData.date;
const durationMinutes = inputData.duration_minutes;
```

**Analysis**: This node is in **different path** (available_slots action):
```
[Route by Action] → [Get Calendar Events (Single Date)] → [Calculate Available Slots]
```

**Flow source**: "Route by Action" → data comes from "Parse & Validate Request"

**Check if broken**: If "Get Calendar Events (Single Date)" returns empty object, this node will also fail.

**Fix** (if needed):
```javascript
const requestData = $node["Parse & Validate Request"].json;
const dateStr = requestData.date;
const durationMinutes = requestData.duration_minutes;
```

---

## Testing Protocol

### Test 1: Empty Calendar Validation (Primary Fix)
```bash
# SETUP: Ensure Google Calendar has NO events in next 7 days

curl -X POST http://localhost:5678/webhook/calendar-availability \
  -H "Content-Type: application/json" \
  -d '{
    "action": "next_dates",
    "count": 3,
    "service_type": "energia_solar",
    "duration_minutes": 120
  }'

# Expected Response (V2.1 FIX):
{
  "success": true,
  "action": "next_dates",
  "dates": [
    {
      "date": "2026-04-21",
      "display": "Amanhã (21/04)",
      "day_of_week": "Segunda",
      "total_slots": 8,
      "quality": "high"
    },
    // ... 2 more dates
  ],
  "total_available": 3
}

# Validation:
# ✅ No "Cannot read properties of undefined" error
# ✅ Response contains 3 dates with 8 slots each
# ✅ HTTP status 200

# Check n8n execution logs:
# Expand "Calculate Slot Availability" node
# Look for: "📊 [WF06 V2.1] Processing 3 dates with 0 calendar events"
# Look for: "ℹ️ [WF06 V2.1] Empty calendar detected - all slots will be available"
```

### Test 2: Calendar with Events (Regression Check)
```bash
# SETUP: Create 1 event in Google Calendar
# Date: 2026-04-21 10:00-12:00

curl -X POST http://localhost:5678/webhook/calendar-availability \
  -H "Content-Type: application/json" \
  -d '{
    "action": "next_dates",
    "count": 3,
    "duration_minutes": 120
  }'

# Expected Response:
{
  "success": true,
  "action": "next_dates",
  "dates": [
    {
      "date": "2026-04-21",
      "display": "Amanhã (21/04)",
      "day_of_week": "Segunda",
      "total_slots": 4,  // ✅ 10:00 slot EXCLUDED (conflict with event)
      "quality": "medium"
    },
    {
      "date": "2026-04-22",
      "display": "Terça (22/04)",
      "day_of_week": "Terça",
      "total_slots": 8,  // ✅ No events on this date
      "quality": "high"
    }
    // ...
  ],
  "total_available": 3
}

# Validation:
# ✅ 2026-04-21 has 4 slots (not 8) - conflict detected correctly
# ✅ 2026-04-22 has 8 slots - no conflicts
# ✅ Calendar event filtering working
```

### Test 3: Single Date Endpoint
```bash
curl -X POST http://localhost:5678/webhook/calendar-availability \
  -H "Content-Type: application/json" \
  -d '{
    "action": "available_slots",
    "date": "2026-04-21",
    "duration_minutes": 120
  }'

# Expected Response:
{
  "success": true,
  "action": "available_slots",
  "date": "2026-04-21",
  "available_slots": [
    { "start_time": "08:00", "end_time": "10:00", "formatted": "8h às 10h" },
    { "start_time": "12:00", "end_time": "14:00", "formatted": "meio-dia às 14h" },
    // ... more slots
  ],
  "total_available": 4
}

# Validation:
# ✅ No undefined errors in "Calculate Available Slots" node
# ✅ If "Calculate Available Slots" also had issue, fix it too
```

---

## Deployment Guide

### Quick Fix (In-Place Update)

```bash
# 1. Open n8n UI
http://localhost:5678/workflow/XA0Klbnd29Z28W5D

# 2. Click "Calculate Slot Availability" node

# 3. Replace lines 1-3:
# FROM:
const inputData = $input.first().json;
const businessDates = inputData.business_dates;
const durationMinutes = inputData.duration_minutes;

# TO:
const requestData = $node["Calculate Next Business Days"].json;
const businessDates = requestData.business_dates;
const durationMinutes = requestData.duration_minutes;

# 4. Save workflow

# 5. Test with Test 1 curl command

# 6. If "Calculate Available Slots" also fails:
#    Click that node → Check if same issue → Apply similar fix:
const requestData = $node["Parse & Validate Request"].json;
const dateStr = requestData.date;
const durationMinutes = requestData.duration_minutes;
```

### Full Code Replacement

**Alternative**: Copy entire fixed code from:
```
/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/scripts/wf06-v2_1-calculate-slot-fix.js
```

**Steps**:
1. Open node in n8n UI
2. **Select All** (Ctrl+A) in code editor
3. **Delete** all code
4. **Paste** code from `wf06-v2_1-calculate-slot-fix.js`
5. **Save** workflow
6. **Test** with Test 1

---

## Validation Checklist

### Fix Applied
- [ ] "Calculate Slot Availability" node updated with `$node["Calculate Next Business Days"].json`
- [ ] "Calculate Available Slots" node checked and fixed if needed
- [ ] Console logs changed to `[WF06 V2.1]` for version tracking

### Testing Complete
- [ ] **Test 1 PASS**: Empty calendar returns all slots (no undefined errors)
- [ ] **Test 2 PASS**: Calendar with events correctly excludes conflicted slots
- [ ] **Test 3 PASS**: Single date endpoint working (if it was also broken)

### Production Ready
- [ ] No `Cannot read properties of undefined` errors in 10 consecutive executions
- [ ] WF02 V80 integration tested (calls WF06 successfully)
- [ ] n8n execution logs show `[WF06 V2.1]` version markers

---

## Why This Fix Works

### n8n Data Access Patterns

**`$input` Limitation**:
- `$input.first().json` = output from **previous node in connection**
- Cannot access data from nodes earlier in workflow
- Workflow: A → B → C, in node C: `$input` = output from B only

**`$node[name]` Solution**:
- `$node["Node Name"].json` = access ANY node by exact name
- Not limited to previous node in connection
- Works for ANY node in workflow, regardless of position

**`$(name)` for Items**:
- `$('Node Name').all()` = get items array from any node
- Used for Google Calendar events (returns item array, not single json)

### Data Source Clarity

**V2.1 Pattern** (EXPLICIT):
```javascript
// Request data from specific node
const requestData = $node["Calculate Next Business Days"].json;

// Calendar events from Google Calendar node
const rawItems = $('Get Calendar Events (Batch)').all();
```

**Benefit**: Code clearly states where each piece of data comes from.

---

## Root Cause Summary

1. **Workflow Connection**: n8n passes data node-to-node via connections
2. **Multiple Data Sources**: Some nodes need data from TWO different nodes
3. **V2 Assumption**: Code assumed `$input` would have request data
4. **n8n Reality**: `$input` only contains previous node output (Google Calendar empty object)
5. **V2.1 Fix**: Explicitly reference correct nodes for each data piece

---

**Fix Status**: READY FOR DEPLOYMENT
**Estimated Time**: 5-10 minutes (quick fix in n8n UI)
**Risk Level**: VERY LOW (single line change, well-tested pattern)
