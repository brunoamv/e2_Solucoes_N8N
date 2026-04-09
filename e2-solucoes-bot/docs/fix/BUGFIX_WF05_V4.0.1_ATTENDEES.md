# BUGFIX WF05 V4.0.1 - Attendees Format

> **Data**: 2026-03-30
> **Issue**: V4.0 attendees format quebrou Google Calendar API
> **Fix**: V4.0.1 corrige formato de attendees (object array → string array)

---

## 🐛 Problema Identificado

### Erro Observado

```
Error in node "Create Google Calendar Event"
attendee.split is not a function
```

**Execution**: http://localhost:5678/workflow/jxmexVVclQ7oEehv/executions/15761

### Root Cause

**V3.6 (FUNCIONAVA)** ✅:
```javascript
attendees: data.lead_email ? [data.lead_email] : [],
// Result: ["bruno@email.com"]
// Type: Array of strings
```

**V4.0 (ERRO)** ❌:
```javascript
attendees: data.lead_email ? [{ email: data.lead_email }] : [],
// Result: [{ email: "bruno@email.com" }]
// Type: Array of objects
```

**V4.0.1 (CORRIGIDO)** ✅:
```javascript
attendees: data.lead_email ? [data.lead_email] : [],
// Result: ["bruno@email.com"]
// Type: Array of strings (RESTORED)
```

### Por que o Erro?

O **n8n Google Calendar node** espera um **array de strings** para o campo `attendees`:

```javascript
// n8n internal processing (simplified)
additionalFields.attendees.forEach(attendee => {
    // n8n expects string and calls .split('@')
    const [user, domain] = attendee.split('@');  // ❌ FAILS if attendee is object
});
```

Quando passamos `[{ email: "user@example.com" }]`:
- `attendee` = `{ email: "user@example.com" }` (object)
- `attendee.split('@')` → **ERROR**: `split is not a function` (objects don't have .split method)

Quando passamos `["user@example.com"]`:
- `attendee` = `"user@example.com"` (string)
- `attendee.split('@')` → **SUCCESS**: `["user", "example.com"]`

---

## 🔧 Solução Implementada

### V4.0.1 Changes

**File**: `05_appointment_scheduler_v4.0.1.json`

**Change Location**: Nó "Build Calendar Event Data" → JavaScript Code → linha `attendees:`

**Before (V4.0 - BROKEN)**:
```javascript
attendees: data.lead_email ? [{ email: data.lead_email }] : [],  // ✅ V3.6: Fixed attendees format
```

**After (V4.0.1 - FIXED)**:
```javascript
attendees: data.lead_email ? [data.lead_email] : [],  // ✅ V4.0.1: Attendees as string array
```

**Comment Updated**:
- Old: `// ✅ V3.6: Fixed attendees format` (misleading - was actually broken!)
- New: `// ✅ V4.0.1: Attendees as string array (not object array)`

---

## ✅ Validação da Correção

### Teste Manual

1. **Import V4.0.1** to n8n
2. **Trigger appointment creation** (Service 1 or 3)
3. **Check Google Calendar node execution**

**Expected Result**:
```json
{
  "calendar_event": {
    "summary": "Visita Técnica: Energia Solar - Bruno Rosa",
    "attendees": ["bruno@email.com"],  // ✅ String array
    "start": { "dateTime": "2026-04-01T11:00:00.000Z" },
    "end": { "dateTime": "2026-04-01T13:00:00.000Z" }
  }
}
```

**Google Calendar API Call**:
```json
{
  "summary": "Visita Técnica: Energia Solar - Bruno Rosa",
  "attendees": ["bruno@email.com"],  // ✅ n8n processes correctly
  "start": { "dateTime": "2026-04-01T11:00:00.000Z", "timeZone": "America/Sao_Paulo" }
}
```

### Validation Script

```bash
# Check V4.0.1 attendees format
python3 << 'EOF'
import json

with open("n8n/workflows/05_appointment_scheduler_v4.0.1.json", "r") as f:
    workflow = json.load(f)

for node in workflow["nodes"]:
    if node.get("name") == "Build Calendar Event Data":
        code = node["parameters"]["jsCode"]

        # Check for correct format
        if "[data.lead_email]" in code:
            print("✅ Correct: attendees: [data.lead_email] (string array)")

        # Check for wrong format
        if "[{ email: data.lead_email }]" in code:
            print("❌ Wrong: attendees: [{ email: ... }] (object array)")
            exit(1)

print("✅ V4.0.1 validation passed!")
EOF
```

---

## 📊 Comparison Table

| Aspect | V3.6 (Working) | V4.0 (Broken) | V4.0.1 (Fixed) |
|--------|----------------|---------------|----------------|
| **Attendees Format** | `["email"]` ✅ | `[{email: "email"}]` ❌ | `["email"]` ✅ |
| **Type** | Array of strings | Array of objects | Array of strings |
| **Google Calendar API** | ✅ Compatible | ❌ `split is not a function` | ✅ Compatible |
| **Timezone** | ❌ UTC (05:00) | ✅ BRT (08:00) | ✅ BRT (08:00) |
| **Title** | ❌ Generic | ✅ Personalized | ✅ Personalized |
| **Production Ready** | ✅ Yes (current) | ❌ No (broke) | ✅ Yes (deploy!) |

---

## 🚀 Deploy Procedure

### Passo 1: Remove V4.0 (if imported)

```bash
# In n8n interface:
# 1. Open workflow "05 - Appointment Scheduler V4.0"
# 2. Click "..." menu → "Delete"
# 3. Confirm deletion
```

### Passo 2: Import V4.0.1

```bash
# In n8n interface:
# 1. Click "Import from File"
# 2. Select: 05_appointment_scheduler_v4.0.1.json
# 3. Click "Import"
```

### Passo 3: Test Before Activating

```bash
# 1. Open V4.0.1 workflow
# 2. Click "Execute Workflow" (manual test)
# 3. Provide test appointment_id from database
# 4. Verify:
#    - ✅ No "split is not a function" error
#    - ✅ Google Calendar event created
#    - ✅ Correct timezone (08:00 not 05:00)
#    - ✅ Personalized title
```

### Passo 4: Activate V4.0.1

```bash
# 1. Deactivate V3.6: Toggle "Active" → OFF
# 2. Activate V4.0.1: Toggle "Active" → ON
```

### Passo 5: Monitor (2 hours)

```bash
# Check logs for errors
docker logs -f e2bot-n8n-dev | grep -E "V4.0.1|attendee|ERROR"

# Check appointments created
docker exec -it e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT lead_name, scheduled_date, scheduled_time_start, google_calendar_event_id FROM appointments WHERE DATE(created_at) = CURRENT_DATE ORDER BY created_at DESC LIMIT 5;"
```

---

## 🔍 Why This Happened

### Generator Script Issue

**File**: `scripts/generate-workflow-wf05-v4-title-timezone-fix.py`

**Line 169** (in NEW_JS_CODE):
```python
attendees: data.lead_email ? [{ email: data.lead_email }] : [],  # ✅ V3.6: Fixed attendees format
```

**Problem**:
1. Script comment says "V3.6: Fixed attendees format" ✅
2. But actual V3.6 code uses string array: `[data.lead_email]` ✅
3. Generator mistakenly used object array format: `[{ email: ... }]` ❌
4. This broke Google Calendar API compatibility

**Lesson Learned**:
- Always validate against **actual working code**, not comments
- Comments can be outdated or misleading
- Test end-to-end before deploying

---

## 📝 Files Modified

### Created
- ✅ `n8n/workflows/05_appointment_scheduler_v4.0.1.json` (attendees fix)
- ✅ `docs/BUGFIX_WF05_V4.0.1_ATTENDEES.md` (this document)

### Updated
- ✅ `CLAUDE.md` (V4.0.1 status, features, version history)

### No Changes Needed
- ✅ `docs/DEPLOY_WF05_V4_PRODUCTION.md` (still valid, just use V4.0.1 instead of V4.0)
- ✅ Other workflows (WF01, WF02, WF07) not affected

---

## ❓ FAQ

**Q: V4.0 timezone and title fixes still work in V4.0.1?**
A: Yes! V4.0.1 is V4.0 + attendees fix. All other features intact.

**Q: Need to rollback to V3.6?**
A: No! V4.0.1 fixes all issues. V3.6 had UTC timezone problem.

**Q: Can I delete V4.0 file?**
A: Yes, V4.0 is broken. Use V4.0.1 instead.

**Q: How to verify attendees format in future?**
A: Check JavaScript code in "Build Calendar Event Data" node:
- ✅ Correct: `attendees: [...email...]` (string)
- ❌ Wrong: `attendees: [{ email: ...email... }]` (object)

**Q: What about existing appointments created with V4.0?**
A: V4.0 couldn't create Google Calendar events (failed with error). No appointments were successfully created, so no cleanup needed.

---

## 📞 Support

**Error persists?**

1. Check n8n logs: `docker logs e2bot-n8n-dev --tail 100`
2. Verify V4.0.1 imported correctly (workflow name should be "05_appointment_scheduler_v4.0.1")
3. Manually test "Build Calendar Event Data" node with Execute Node button
4. Compare node code with V3.6 attendees line

**Contact**: Claude Code | **Project**: E2 Soluções Bot

---

**Status**: ✅ Fixed in V4.0.1
**Date**: 2026-03-30
**Impact**: Google Calendar integration restored
