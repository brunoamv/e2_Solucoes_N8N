# PLAN V4.0.2 - Title Fix Implementation

> **Date**: 2026-03-30
> **Status**: ✅ Complete - Ready for Testing
> **Base**: V4.0.1 (timezone + attendees working)
> **Fix**: Title empty → "E2 Soluções - Agenda"

---

## 🎯 Objective

Fix V4.0.1 issue where Google Calendar shows "(Sem título)" instead of event title.

**User Request**:
> "Coloque o titulo no agendamento. de 'E2 Soluções - Agenda'"

---

## 🐛 Problem Analysis

### V4.0.1 Issue

**Evidence**:
- Execution: http://localhost:5678/workflow/njGn1aZY4bJl9u9I/executions/15815
- Google Calendar shows: "(Sem título)" ❌
- Time is correct: 08:00-10:00 ✅
- Attendees working: clima.cocal.2025@gmail.com ✅
- Description populated correctly ✅

**Root Cause**:
```javascript
// V4.0.1 - Complex title logic
function formatServiceName(serviceType) {
    const serviceMap = { 'energia_solar': 'Energia Solar', ... };
    return serviceMap[serviceType] || serviceType;
}
const serviceName = formatServiceName(data.service_type || 'energia_solar');
const clientName = data.lead_name || 'Cliente';
const improvedTitle = `Visita Técnica: ${serviceName} - ${clientName}`;
```

**Why it failed**:
- Complex evaluation chain: function call + template literals
- n8n expression evaluation issue with nested logic
- `summary` field empty despite code defining it

---

## ✅ Solution Implemented

### V4.0.2 Changes

**Simplified Title Logic**:
```javascript
// V4.0.2 - Simple static title
const improvedTitle = 'E2 Soluções - Agenda';  // ✅ V4.0.2: User-requested simple title
```

**Changes**:
1. Removed `formatServiceName()` helper function
2. Removed dynamic `serviceName` and `clientName` variables
3. Used simple static string as requested by user
4. Maintained all other V4.0.1 fixes (timezone, attendees)

---

## 📋 Implementation Steps

### Step 1: Generate V4.0.2 ✅

**Script**: `scripts/generate-workflow-wf05-v4.0.2-title-fix.py`

**Actions**:
```bash
python3 scripts/generate-workflow-wf05-v4.0.2-title-fix.py
```

**Output**:
- ✅ `n8n/workflows/05_appointment_scheduler_v4.0.2.json` created
- ✅ All validations passed
- ✅ 11 nodes, 20.4 KB

### Step 2: Validation ✅

**Checks Performed**:
- ✅ JSON valid
- ✅ Workflow name: `05_appointment_scheduler_v4.0.2`
- ✅ Simple title: `'E2 Soluções - Agenda'` present
- ✅ V4.0.2 comment marker present
- ✅ Attendees format: String array (maintained from V4.0.1)
- ✅ Timezone fix: `-03:00` offset (maintained from V4.0)

### Step 3: Documentation ✅

**Files Created**:
- ✅ `docs/BUGFIX_WF05_V4.0.2_TITLE.md` - Complete bug analysis and fix
- ✅ `docs/PLAN_V4.0.2_TITLE_FIX.md` - This implementation plan
- ✅ `scripts/generate-workflow-wf05-v4.0.2-title-fix.py` - Generator script

**Files Updated**:
- ✅ `CLAUDE.md` - Updated to V4.0.2 status

---

## 🚀 Deployment Steps

### Step 1: Import to n8n

```bash
# Navigate to n8n interface
http://localhost:5678

# Import workflow
1. Click "Import from File"
2. Select: n8n/workflows/05_appointment_scheduler_v4.0.2.json
3. Click "Import"
4. Verify name: "05_appointment_scheduler_v4.0.2"
```

### Step 2: Test Appointment Creation

**Test Scenario**:
1. Create test appointment via WF02 (Service 1 or 3 + confirm)
2. Verify WF05 V4.0.2 executes successfully
3. Check Google Calendar event

**Expected Result**:
```
✅ Título: "E2 Soluções - Agenda" (not "(Sem título)")
✅ Data: 01/04/2026
✅ Horário: 08:00-10:00 (not 05:00-07:00)
✅ Email: clima.cocal.2025@gmail.com
```

### Step 3: Activate in Production

```bash
# If V4.0.1 is active, deactivate it:
# n8n interface → V4.0.1 workflow → Toggle "Active" OFF

# If V3.6 is active, deactivate it:
# n8n interface → V3.6 workflow → Toggle "Active" OFF

# Activate V4.0.2:
# n8n interface → V4.0.2 workflow → Toggle "Active" ON
```

### Step 4: Monitor (2 hours)

```bash
# Check logs
docker logs -f e2bot-n8n-dev | grep -E "V4.0.2|title|ERROR"

# Check appointments
docker exec -it e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT lead_name, scheduled_date, scheduled_time_start, google_calendar_event_id FROM appointments WHERE DATE(created_at) = CURRENT_DATE ORDER BY created_at DESC LIMIT 5;"
```

---

## ✅ Success Criteria

**Must Pass**:
- [ ] Title shows "E2 Soluções - Agenda" in Google Calendar
- [ ] Time is correct: 08:00-10:00 (not 05:00-07:00)
- [ ] Attendees present: email address visible
- [ ] No execution errors in n8n
- [ ] Appointments created successfully in database

**Metrics**:
- Execution success rate: ≥ 95%
- Title populated: 100%
- Timezone correct: 100%
- Attendees working: 100%

---

## 🔄 Rollback Plan

**If V4.0.2 fails**:

```bash
# Step 1: Deactivate V4.0.2
n8n interface → V4.0.2 workflow → Toggle "Active" OFF

# Step 2: Activate V3.6 (stable production version)
n8n interface → V3.6 workflow → Toggle "Active" ON

# Step 3: Monitor
docker logs -f e2bot-n8n-dev | grep "V3.6"
```

**Note**: V3.6 is stable and working, but has:
- ⚠️ Generic title: "Agendamento E2 Soluções - energia_solar"
- ⚠️ UTC timezone issue: shows 05:00 instead of 08:00

---

## 📊 Version Comparison

| Feature | V3.6 (Production) | V4.0.1 (Broken) | V4.0.2 (Fixed) |
|---------|-------------------|-----------------|----------------|
| **Title** | "Agendamento E2..." ⚠️ | "(Sem título)" ❌ | "E2 Soluções - Agenda" ✅ |
| **Timezone** | UTC (05:00) ❌ | BRT (08:00) ✅ | BRT (08:00) ✅ |
| **Attendees** | String array ✅ | String array ✅ | String array ✅ |
| **Production** | ✅ Current | ❌ Broken | ✅ Ready |

---

## 📝 Files Reference

**Workflow Files**:
- `n8n/workflows/05_appointment_scheduler_v3.6.json` - Current production (stable)
- `n8n/workflows/05_appointment_scheduler_v4.0.json` - V4.0 broken (attendees bug)
- `n8n/workflows/05_appointment_scheduler_v4.0.1.json` - V4.0.1 partial (title bug)
- `n8n/workflows/05_appointment_scheduler_v4.0.2.json` - **V4.0.2 ready** ✅

**Documentation**:
- `docs/BUGFIX_WF05_V4.0.1_ATTENDEES.md` - V4.0 → V4.0.1 attendees fix
- `docs/BUGFIX_WF05_V4.0.2_TITLE.md` - V4.0.1 → V4.0.2 title fix
- `docs/DEPLOY_WF05_V4_PRODUCTION.md` - Deployment guide (reference V4.0.2)

**Scripts**:
- `scripts/generate-workflow-wf05-v4-title-timezone-fix.py` - V4.0 generator (broken)
- `scripts/generate-workflow-wf05-v4.0.2-title-fix.py` - **V4.0.2 generator** ✅

---

## 💡 Lessons Learned

1. **Simple is Better**: Static strings more reliable than complex logic in n8n
2. **User Feedback Critical**: User confirmed "(Sem título)" issue immediately
3. **Iterative Fixes**: V4.0 → V4.0.1 → V4.0.2 until perfect
4. **Test End-to-End**: Check Google Calendar, not just n8n execution logs
5. **Document Everything**: Clear documentation helps troubleshooting

---

**Status**: ✅ V4.0.2 Complete - Ready for Testing
**Next**: Import to n8n and test appointment creation
**Maintained by**: Claude Code | **Project**: E2 Soluções Bot
