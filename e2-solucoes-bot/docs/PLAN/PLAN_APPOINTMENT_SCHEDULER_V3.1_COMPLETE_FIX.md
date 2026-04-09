# Plan: Appointment Scheduler V3.1 - Complete Comprehensive Fix

> **Date**: 2026-03-24
> **Purpose**: Fix ALL remaining issues in workflow 05
> **Status**: Planning Complete

---

## 🎯 Critical Problems Identified

### Problem #1: Validate Availability - TypeError ⚠️ CRITICAL
**Error**: `Cannot read properties of undefined (reading 'split') [line 12]`

**Root Cause**: PostgreSQL returns `TIME` type as object, not string

**Current Code** (BROKEN):
```javascript
const timeStart = data.scheduled_time_start;
const startHour = parseInt(timeStart.split(':')[0]);  // ❌ .split() doesn't exist
```

**Fix**:
```javascript
// PostgreSQL TIME can be string OR Time object
const timeStart = data.scheduled_time_start?.toString() || data.scheduled_time_start;
const timeEnd = data.scheduled_time_end?.toString() || data.scheduled_time_end;

// Validate they exist
if (!timeStart || !timeEnd) {
    throw new Error('Horários não encontrados nos dados do agendamento');
}

// Safe split
const startHour = parseInt(timeStart.split(':')[0]);
const endHour = parseInt(timeEnd.split(':')[0]);
```

---

### Problem #2: Google Calendar Credentials - Invalid Expression ⚠️ CRITICAL
**Current** (INVALID):
```json
"credentials": {
  "googleCalendarOAuth2Api": {
    "id": "={{ $env.GOOGLE_CALENDAR_CREDENTIAL_ID }}",  // ❌ Expression not allowed in ID
    "name": "Google Calendar API"
  }
}
```

**Fix**: Use static credential reference
```json
"credentials": {
  "googleCalendarOAuth2Api": {
    "id": "1",  // ✅ Static ID
    "name": "Google Calendar API"
  }
}
```

---

### Problem #3: Environment Variables - Missing Validation ⚠️ WARNING
**Current**: Assumes all env vars exist

**Fix**: Add validation for required env vars
```javascript
// In Validate Availability node - BEFORE using env vars
if (!$env.CALENDAR_WORK_START || !$env.CALENDAR_WORK_END || !$env.CALENDAR_WORK_DAYS) {
    console.warn('⚠️  Calendar env vars not configured - skipping availability check');
    return {
        ...data,
        validation_status: 'skipped',
        validated_at: new Date().toISOString()
    };
}
```

---

### Problem #4: Build Calendar Event - Date Parsing Issue 🔍
**Potential Issue**: `scheduled_date` may be Date object or string

**Fix**:
```javascript
// Before building DateTime
const scheduledDate = data.scheduled_date;
const dateString = scheduledDate instanceof Date
    ? scheduledDate.toISOString().split('T')[0]
    : scheduledDate;

// Build DateTime with proper format
const startDateTime = new Date(`${dateString}T${timeStart}`);
const endDateTime = new Date(`${dateString}T${timeEnd}`);
```

---

## 🔧 Refactoring Strategy

### Step 1: Fix Validate Availability (CRITICAL)
**File**: Node "Validate Availability" jsCode

**Changes**:
1. Convert TIME objects to strings with `.toString()`
2. Add null/undefined checks before `.split()`
3. Validate env vars exist before use
4. Add comprehensive error handling

---

### Step 2: Fix Google Calendar Credentials (CRITICAL)
**File**: Node "Create Google Calendar Event" credentials

**Changes**:
1. Replace expression `{{ $env.GOOGLE_CALENDAR_CREDENTIAL_ID }}` with static `"1"`
2. Use n8n's credential selector, not dynamic expression

---

### Step 3: Fix Build Calendar Event Data (PREVENTIVE)
**File**: Node "Build Calendar Event Data" jsCode

**Changes**:
1. Add type safety for DATE and TIME PostgreSQL types
2. Normalize date/time to strings before parsing
3. Add validation for required fields

---

### Step 4: Add Comprehensive Error Logging
**File**: All Code nodes

**Changes**:
1. Wrap critical operations in try/catch
2. Log actual data types and values on error
3. Provide actionable error messages

---

## 📦 V3.1 Implementation

### Code Fix #1: Validate Availability (Complete Rewrite)
```javascript
// Validate Availability - V3.1 FIX
const data = $input.first().json;

try {
    // ===== VALIDATE INPUT DATA =====
    const scheduledDate = data.scheduled_date;
    const timeStartRaw = data.scheduled_time_start;
    const timeEndRaw = data.scheduled_time_end;

    if (!scheduledDate || !timeStartRaw || !timeEndRaw) {
        throw new Error('Dados de agendamento incompletos: ' + JSON.stringify({
            scheduledDate: !!scheduledDate,
            timeStart: !!timeStartRaw,
            timeEnd: !!timeEndRaw
        }));
    }

    // ===== NORMALIZE TIME VALUES =====
    // PostgreSQL TIME type may be object or string
    const timeStart = typeof timeStartRaw === 'string'
        ? timeStartRaw
        : timeStartRaw?.toString() || '';

    const timeEnd = typeof timeEndRaw === 'string'
        ? timeEndRaw
        : timeEndRaw?.toString() || '';

    console.log('⏰ [Validate Availability] Times:', { timeStart, timeEnd });

    // ===== CHECK ENV VARS EXIST =====
    if (!$env.CALENDAR_WORK_START || !$env.CALENDAR_WORK_END || !$env.CALENDAR_WORK_DAYS) {
        console.warn('⚠️  Calendar env vars not configured - skipping validation');
        return {
            ...data,
            validation_status: 'skipped',
            validation_reason: 'env_vars_missing',
            validated_at: new Date().toISOString()
        };
    }

    // ===== CHECK BUSINESS HOURS =====
    const startHour = parseInt(timeStart.split(':')[0]);
    const endHour = parseInt(timeEnd.split(':')[0]);

    const workStart = parseInt($env.CALENDAR_WORK_START.split(':')[0]);
    const workEnd = parseInt($env.CALENDAR_WORK_END.split(':')[0]);

    if (startHour < workStart || endHour > workEnd) {
        throw new Error(`Horário fora do expediente: ${timeStart}-${timeEnd} (expediente: ${$env.CALENDAR_WORK_START}-${$env.CALENDAR_WORK_END})`);
    }

    // ===== CHECK WEEKEND =====
    const dateObj = scheduledDate instanceof Date
        ? scheduledDate
        : new Date(scheduledDate);

    const dayOfWeek = dateObj.getDay();
    const workDays = $env.CALENDAR_WORK_DAYS.split(',').map(d => parseInt(d.trim()));

    if (!workDays.includes(dayOfWeek)) {
        throw new Error(`Dia não útil: ${scheduledDate} (dia da semana: ${dayOfWeek})`);
    }

    console.log('✅ [Validate Availability] Approved:', scheduledDate, timeStart);

    return {
        ...data,
        validation_status: 'approved',
        validated_at: new Date().toISOString()
    };

} catch (error) {
    console.error('❌ [Validate Availability] Error:', error.message);
    console.error('Data received:', JSON.stringify(data, null, 2));
    throw error;
}
```

---

### Code Fix #2: Build Calendar Event Data (Type Safety)
```javascript
// Build Calendar Event Data - V3.1 FIX (excerpt)

// ===== NORMALIZE DATE AND TIME =====
const scheduledDateRaw = data.scheduled_date;
const timeStartRaw = data.scheduled_time_start;
const timeEndRaw = data.scheduled_time_end;

// Convert to strings if needed
const dateString = scheduledDateRaw instanceof Date
    ? scheduledDateRaw.toISOString().split('T')[0]
    : scheduledDateRaw;

const timeStart = typeof timeStartRaw === 'string'
    ? timeStartRaw
    : timeStartRaw?.toString() || '00:00:00';

const timeEnd = typeof timeEndRaw === 'string'
    ? timeEndRaw
    : timeEndRaw?.toString() || '00:00:00';

console.log('📅 [Build Calendar] Date/Time:', { dateString, timeStart, timeEnd });

// ===== BUILD DATETIME =====
const startDateTime = new Date(`${dateString}T${timeStart}`);
const endDateTime = new Date(`${dateString}T${timeEnd}`);

if (isNaN(startDateTime.getTime()) || isNaN(endDateTime.getTime())) {
    throw new Error('Invalid date/time format: ' + JSON.stringify({ dateString, timeStart, timeEnd }));
}

// ... rest of code
```

---

### Fix #3: Google Calendar Credentials (Static ID)
```json
{
  "parameters": {
    "resource": "event",
    "operation": "create",
    "calendarId": "={{ $env.GOOGLE_CALENDAR_ID }}",
    "start": "={{ $json.calendar_event.start.dateTime }}",
    "end": "={{ $json.calendar_event.end.dateTime }}",
    "summary": "={{ $json.calendar_event.summary }}",
    "additionalFields": {
      "description": "={{ $json.calendar_event.description }}",
      "location": "={{ $json.calendar_event.location }}",
      "attendees": "={{ JSON.stringify($json.calendar_event.attendees) }}",
      "colorId": "={{ $json.calendar_event.colorId }}",
      "reminders": "={{ JSON.stringify($json.calendar_event.reminders) }}"
    }
  },
  "id": "create-google-event-v3.1",
  "name": "Create Google Calendar Event",
  "type": "n8n-nodes-base.googleCalendar",
  "typeVersion": 2,
  "position": [1250, 300],
  "credentials": {
    "googleCalendarOAuth2Api": {
      "id": "1",
      "name": "Google Calendar API"
    }
  },
  "continueOnFail": true,
  "alwaysOutputData": true,
  "retryOnFail": true,
  "maxTries": 3,
  "waitBetweenTries": 1000
}
```

---

## ✅ Validation Checklist

### Pre-Implementation
- [x] Identify all type conversion issues
- [x] Document PostgreSQL type mappings
- [x] Plan env var validation
- [x] Design error handling strategy

### Post-Implementation
- [ ] Test with real appointment data
- [ ] Verify TIME type handling
- [ ] Confirm Google Calendar creation
- [ ] Validate error messages
- [ ] Check env var fallback behavior

---

## 🚀 Expected Results

**Before V3.1**:
```
❌ Error: Cannot read properties of undefined (reading 'split')
❌ Workflow stops at Validate Availability
❌ No calendar event created
```

**After V3.1**:
```
✅ TIME objects converted to strings
✅ Availability validation passes
✅ Calendar event created successfully
✅ Comprehensive error logging
✅ Graceful env var handling
```

---

**Plan Status**: ✅ Complete - Ready for Implementation
**Next**: Generate V3.1 workflow with all fixes
