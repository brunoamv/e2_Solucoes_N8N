# Plan: Appointment Scheduler V3 - Complete Fix

> **Date**: 2026-03-24
> **Purpose**: Fix all parameter binding issues in workflow 05
> **Status**: Planning Complete

---

## 🎯 Problems Identified

### Problem #1: Get Appointment & Lead Data (CRITICAL)
**Node**: `Get Appointment & Lead Data` (line 33-56)
**Error**: `there is no parameter $1`

**Current (INCORRECT)**:
```json
"queryParameters": "={{ $json.appointment_id }}"
```

**Issue**: PostgreSQL node expects **array** format, not string.

**Solution**:
```json
"queryParameters": {
  "parameters": [
    {
      "name": "appointment_id",
      "value": "={{ $json.appointment_id }}"
    }
  ]
}
```

**Alternative (simpler)**:
Replace `$1` with direct expression: `WHERE a.id = {{ $json.appointment_id }}`

---

### Problem #2: Update Appointment (line 125-148)
**Current (INCORRECT)**:
```json
"queryParameters": "={{ $('Build Calendar Event Data').item.json.appointment_id }},={{ $('Create Google Calendar Event').item.json.id || null }},={{ $('Create Google Calendar Event').item.json.error || null }}"
```

**Issue**: Same - expects array, got comma-separated string.

**Solution**:
```json
"queryParameters": {
  "parameters": [
    {
      "name": "appointment_id",
      "value": "={{ $('Build Calendar Event Data').item.json.appointment_id }}"
    },
    {
      "name": "calendar_event_id",
      "value": "={{ $('Create Google Calendar Event').item.json.id || null }}"
    },
    {
      "name": "error_message",
      "value": "={{ $('Create Google Calendar Event').item.json.error || null }}"
    }
  ]
}
```

---

### Problem #3: Create Appointment Reminders (line 150-173)
**Current (INCORRECT)**:
```json
"queryParameters": "={{ $('Build Calendar Event Data').item.json.appointment_id }}"
```

**Solution**: Same as #1 - use array format or direct expression.

---

## 🔧 Refactoring Strategy

### Option A: Direct Expression Replacement (SIMPLER)
- Replace `$1, $2, $3` with `{{ expressions }}`
- No queryParameters needed
- Easier to read and debug
- **RECOMMENDED for V3**

### Option B: Proper Parameter Binding (BEST PRACTICE)
- Use correct array format for queryParameters
- Maintains SQL parameter safety
- More verbose but safer
- Consider for V4

---

## 📦 V3 Implementation Plan

### Step 1: Fix Get Appointment & Lead Data
```sql
-- FROM:
WHERE a.id = $1
  AND a.status IN ('agendado', 'reagendado')

-- TO:
WHERE a.id = {{ $json.appointment_id }}
  AND a.status IN ('agendado', 'reagendado')
```

Remove `queryParameters` field entirely.

---

### Step 2: Fix Update Appointment
```sql
-- FROM:
UPDATE appointments
SET
    google_calendar_event_id = CASE
        WHEN $2 IS NOT NULL THEN $2
        ELSE google_calendar_event_id
    END,
    status = CASE
        WHEN $2 IS NOT NULL THEN 'confirmado'
        ELSE 'erro_calendario'
    END,
    notes = CASE
        WHEN $2 IS NULL AND $3 IS NOT NULL
        THEN COALESCE(notes, '') || '\n[ERRO] Falha ao criar evento no Google Calendar: ' || $3
        ELSE notes
    END,
    updated_at = NOW()
WHERE id = $1

-- TO:
UPDATE appointments
SET
    google_calendar_event_id = CASE
        WHEN {{ $('Create Google Calendar Event').item.json.id || 'NULL' }} != 'NULL'
        THEN {{ $('Create Google Calendar Event').item.json.id || 'NULL' }}
        ELSE google_calendar_event_id
    END,
    status = CASE
        WHEN {{ $('Create Google Calendar Event').item.json.id || 'NULL' }} != 'NULL'
        THEN 'confirmado'
        ELSE 'erro_calendario'
    END,
    notes = CASE
        WHEN {{ $('Create Google Calendar Event').item.json.id || 'NULL' }} = 'NULL'
             AND {{ $('Create Google Calendar Event').item.json.error || 'NULL' }} != 'NULL'
        THEN COALESCE(notes, '') || '\n[ERRO] Falha ao criar evento no Google Calendar: '
             || {{ $('Create Google Calendar Event').item.json.error || '' }}
        ELSE notes
    END,
    updated_at = NOW()
WHERE id = {{ $('Build Calendar Event Data').item.json.appointment_id }}
```

Remove `queryParameters` field.

---

### Step 3: Fix Create Appointment Reminders
```sql
-- FROM:
SELECT create_appointment_reminders($1);

-- TO:
SELECT create_appointment_reminders({{ $('Build Calendar Event Data').item.json.appointment_id }});
```

Remove `queryParameters` field.

---

## ✅ Validation Checklist

### Pre-Implementation
- [x] Identify all nodes using queryParameters
- [x] Document current vs new SQL
- [x] Plan expression syntax

### Post-Implementation
- [ ] Test with real appointment_id
- [ ] Verify PostgreSQL query execution
- [ ] Confirm all 3 queries work
- [ ] Check error handling paths
- [ ] Validate Google Calendar creation
- [ ] Verify email confirmation trigger

---

## 🚀 Deployment Steps

1. **Generate V3 JSON**
   ```bash
   python3 scripts/generate-appointment-scheduler-v3.py
   ```

2. **Import to n8n**
   - URL: http://localhost:5678
   - File: `n8n/workflows/05_appointment_scheduler_v3.json`

3. **Test Execution**
   - Trigger from WF02 (V73.5)
   - Monitor execution logs
   - Verify Google Calendar event creation

4. **Production Activation**
   - Deactivate V2.1
   - Activate V3
   - Monitor for 24h

---

## 📊 Expected Results

**Before V3**:
```
❌ Error: there is no parameter $1
❌ Query fails at Get Appointment & Lead Data
❌ Workflow stops, no calendar event
```

**After V3**:
```
✅ Query executes with appointment_id
✅ Lead data retrieved successfully
✅ Google Calendar event created
✅ Appointment updated to 'confirmado'
✅ Email confirmation sent
```

---

## 🔄 Rollback Plan

If V3 fails:
1. Deactivate V3
2. Activate V2.1
3. Revert WF02 trigger to use V2.1 workflow ID
4. Analyze V3 execution logs
5. Fix and re-test

---

**Plan Status**: ✅ Complete - Ready for Implementation
**Next**: Generate V3 workflow with fixes
