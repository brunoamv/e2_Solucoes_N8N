# BUGFIX WF02 V102 - Send WhatsApp Response Input Source

**Date**: 2026-04-27
**Problem**: "Send WhatsApp Response" node failing with "Bad request" when receiving data from "Build WF06 Response Message"
**Root Cause**: Node is configured to read from "Build Update Queries" which doesn't have response_text in WF06 flow

---

## 🐛 PROBLEM ANALYSIS

### Current Configuration (BROKEN)

**Send WhatsApp Response node**:
```json
{
  "number": "={{ $node[\"Build Update Queries\"].json[\"phone_number\"] }}",
  "text": "={{ $node[\"Build Update Queries\"].json[\"response_text\"] }}"
}
```

**Problem**:
- WF06 flow: "Build WF06 Response Message" → "Send WhatsApp Response"
- "Build Update Queries" does NOT have `response_text` for WF06 responses
- `response_text` is in the OUTPUT of "Build WF06 Response Message"
- Result: `text` field is EMPTY → Evolution API returns "Bad request"

### Evidence from Execution

**Build WF06 Response Message OUTPUT**:
```json
{
  "phone_number": "556181755748",
  "response_text": "📅 *Agendar Visita Técnica*...",
  "date_suggestions": [...]
}
```

**Build Update Queries** (in WF06 flow):
```json
{
  "phone_number": "556181755748",
  "next_stage": "trigger_wf06_next_dates",
  // ❌ NO response_text field!
}
```

---

## ✅ SOLUTION 1: Use $input (RECOMMENDED)

### Change Send WhatsApp Response Configuration

**BEFORE (BROKEN)**:
```javascript
number: ={{ $node["Build Update Queries"].json["phone_number"] }}
text: ={{ $node["Build Update Queries"].json["response_text"] }}
```

**AFTER (FIXED)**:
```javascript
number: ={{ $input.first().json.phone_number }}
text: ={{ $input.first().json.response_text }}
```

### Why This Works

**Normal Flow** (State Machine → Send WhatsApp):
- State Machine outputs: `{ phone_number, response_text, ... }`
- Send WhatsApp receives via $input ✅

**WF06 Flow** (Build WF06 Response → Send WhatsApp):
- Build WF06 Response outputs: `{ phone_number, response_text, date_suggestions }`
- Send WhatsApp receives via $input ✅

**Both flows work** because the node always reads from its direct predecessor!

### Implementation Steps

1. Open n8n workflow: http://localhost:5678/workflow/QeNgH4gCvF5HSE51
2. Click on node: **"Send WhatsApp Response"**
3. In **Body Parameters**:
   - Change `number` field to: `={{ $input.first().json.phone_number }}`
   - Change `text` field to: `={{ $input.first().json.response_text }}`
4. Save workflow
5. Test both flows:
   - Normal flow: State Machine → Send WhatsApp ✅
   - WF06 flow: Build WF06 → Send WhatsApp ✅

---

## ✅ SOLUTION 2: Create Separate Send WhatsApp Node for WF06

If you want to keep the current "Send WhatsApp Response" unchanged:

### Create New Node

**Node Name**: "Send WhatsApp WF06 Response"

**Configuration**:
```json
{
  "method": "POST",
  "url": "http://e2bot-evolution-dev:8080/message/sendText/e2-solucoes-bot",
  "headers": {
    "apikey": "ae569043cfa169380c378347f91a1141ea572541d2d1cadbed222db519c8a891",
    "Content-Type": "application/json"
  },
  "body": {
    "number": "={{ $input.first().json.phone_number }}",
    "text": "={{ $input.first().json.response_text }}"
  }
}
```

**Connection**:
```
Build WF06 Response Message → Send WhatsApp WF06 Response (NEW)
```

---

## 📊 VALIDATION

### Test Normal Flow
```bash
# User completes data → confirmation state
# Expected: Confirmation summary message sent ✅
# Validation: "Send WhatsApp Response" works with State Machine output
```

### Test WF06 Flow
```bash
# User confirms → trigger_wf06_next_dates
# WF06 returns dates → Build WF06 Response → Send WhatsApp
# Expected: "📅 *Agendar Visita Técnica*\n\n📆 *Próximas datas disponíveis:*..." ✅
# Validation: "Send WhatsApp Response" works with Build WF06 Response output
```

### Check Logs
```bash
docker logs -f e2bot-n8n-dev | grep -E "Send WhatsApp|response_text|Bad request"

# Expected (AFTER FIX):
# ✅ Send WhatsApp Response: number=556181755748, text=📅 *Agendar...
# ❌ Should NOT see "Bad request" errors
```

---

## 🚨 CRITICAL NOTE

**Why "Build Update Queries" doesn't work for WF06**:

In the WF06 flow, "Build Update Queries" executes BEFORE the WF06 HTTP Request:
```
State Machine (trigger_wf06_next_dates)
  → Build Update Queries (prepares HTTP request)
  → WF06 HTTP Request (calls calendar service)
  → Prepare WF06 Next Dates Data
  → Merge WF06 Next Dates with User Data
  → Build WF06 Response Message (creates response_text HERE!)
  → Send WhatsApp Response
```

At the time "Send WhatsApp Response" executes, "Build Update Queries" does NOT have the calendar response message!

---

**Status**: Solution identified - use `$input.first().json` instead of `$node["Build Update Queries"].json`
**Priority**: CRITICAL - blocks WF06 calendar functionality
**Deployment**: Immediate - simple configuration change in n8n UI

