# WF02 V114 - PostgreSQL TIME Fields Fix Quick Deploy

**Version**: V114 Slot Time Fields Fix
**Fix**: Extract start_time and end_time from WF06 slots for PostgreSQL TIME columns
**Time**: ~5 minutes deployment + 10 minutes testing
**Status**: 🔴 CRITICAL FIX

---

## 🎯 What V114 Fixes

**Problem**: User sees WF06 slots successfully and selects one, but appointment creation fails with PostgreSQL error: `invalid input syntax for type time: "null"`.

**Root Cause**: After user selects slot, State Machine saves `scheduled_time_display: "8h às 10h"` for WhatsApp formatting, but DOESN'T extract and save `scheduled_time_start` and `scheduled_time_end` from WF06 slot structure. PostgreSQL TIME columns reject null values.

**Solution**: V114 State Machine extracts start_time and end_time fields from selectedSlot and saves as scheduled_time_start and scheduled_time_end for PostgreSQL compatibility.

---

## 🚀 Quick Deploy (5 minutes)

### Step 1: Update State Machine Logic Code

1. Open workflow: http://localhost:5678/workflow/9tG2gR6KBt6nYyHT
2. Find **"State Machine Logic"** Code node
3. Delete all existing code
4. Copy code from: `scripts/wf02-v114-slot-time-fields-fix.js`
5. Paste new V114 code (1054 lines)
6. Save node

**Critical Code Section V114 Adds** (State 14, lines 888-894):
```javascript
// ===================================================
// V114 CRITICAL FIX: Extract TIME fields from slot
// ===================================================
// WF06 slot structure: { start_time: "08:00", end_time: "10:00", formatted: "8h às 10h" }
// PostgreSQL TIME columns need "HH:MM:SS" format

const startTime = selectedSlot.start_time || selectedSlot.start || null;
const endTime = selectedSlot.end_time || selectedSlot.end || null;

console.log('V114: ✅ CRITICAL FIX - Extracted TIME fields:');
console.log('V114:   start_time:', startTime);
console.log('V114:   end_time:', endTime);
console.log('V114:   formatted display:', selectedSlot.formatted);

// V114 CRITICAL: Save TIME fields for database
updateData.scheduled_time = startTime;  // Backward compatibility
updateData.scheduled_time_display = selectedSlot.formatted;  // For WhatsApp
updateData.scheduled_end_time = endTime;  // Backward compatibility

// V114 NEW: Explicit TIME fields for PostgreSQL
updateData.scheduled_time_start = startTime;  // PostgreSQL TIME column
updateData.scheduled_time_end = endTime;      // PostgreSQL TIME column
```

### Step 2: Save Workflow

1. Click **Save** button in workflow editor
2. Verify node shows green status
3. Workflow is now V114

---

## ✅ Validation (10 minutes)

### Test 1: Complete WF06 Flow

```bash
# User conversation:
# 1. "oi" → greeting
# 2. "1" → Solar service
# 3. "Test Name"
# 4. "1" → confirm phone
# 5. "test@email.com"
# 6. "Goiânia-GO"
# 7. "1" → agendar (triggers WF06 next dates)

# Expected: Bot shows 3 dates ✅

# 8. User types "1" (selects first date)
# Expected: Bot shows time slots ✅

# 9. User types "1" (selects first slot - 8h às 10h)
# Expected: Bot confirms appointment ✅ (NOT PostgreSQL error!)

# Check database was updated with TIME fields:
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT phone_number, state_machine_state,
             collected_data->'scheduled_date' as date,
             collected_data->'scheduled_time_start' as start_time,
             collected_data->'scheduled_time_end' as end_time,
             collected_data->'scheduled_time_display' as display
      FROM conversations
      WHERE phone_number = '556181755748';"

# Expected:
# state_machine_state: trigger_create_appointment  ✅
# date: "2026-04-29"  ✅
# start_time: "08:00"  ✅
# end_time: "10:00"  ✅
# display: "8h às 10h"  ✅
```

### Test 2: Verify Logs

```bash
docker logs -f e2bot-n8n-dev 2>&1 | grep -E "V114|TIME"
```

**Expected**:
```
=== State Machine Logic (V114) ===
Input received: process_slot_selection
Selected slot index: 0
V114: Slot selected: 8h às 10h
V114: ✅ CRITICAL FIX - Extracted TIME fields:
V114:   start_time: 08:00
V114:   end_time: 10:00
V114:   formatted display: 8h às 10h
V114: TIME fields: 08:00 to 10:00
Next stage: trigger_create_appointment
```

### Test 3: Verify Appointment Created

```bash
# Check appointments table
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT lead_name, service_type, scheduled_date,
             scheduled_time_start, scheduled_time_end
      FROM appointments
      ORDER BY created_at DESC LIMIT 1;"

# Expected: New appointment with valid TIME values
```

---

## 🔄 Rollback Procedure

If V114 causes unexpected issues:

1. Open workflow: http://localhost:5678/workflow/9tG2gR6KBt6nYyHT
2. Find "State Machine Logic" Code node
3. Restore V113.1 code from: `scripts/wf02-v110-intermediate-state-message-handler.js`
4. Save workflow

**Note**: Rollback returns to buggy state where appointments fail with PostgreSQL TIME error.

---

## 📁 Related Documentation

- **Complete Analysis**: `docs/WF02_V114_COMPLETE_SUMMARY.md`
- **V114 Code**: `scripts/wf02-v114-slot-time-fields-fix.js`
- **V113.1 Analysis**: `docs/fix/BUGFIX_WF02_V113_1_DATE_SUGGESTIONS_PERSISTENCE.md`
- **V113 Quick Deploy**: `docs/WF02_V113_QUICK_DEPLOY.md`
- **Active Workflow**: `n8n/workflows/wk02_v102_1.json`

---

**Created**: 2026-04-28
**Status**: ✅ READY FOR DEPLOYMENT
**Risk Level**: LOW (Simple field extraction with known WF06 structure)
**Estimated Time**: 5 minutes deployment + 10 minutes testing
**Impact**: Fixes PostgreSQL TIME column error, enables appointment creation
