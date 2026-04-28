# Deploy WF06 V2: Empty Calendar Fix

**Version**: V2
**Date**: 2026-04-18
**Status**: Ready for Deployment
**Target**: Fix `Cannot read properties of undefined` error from empty calendar responses

---

## Pre-Deployment Checklist

### Environment Validation
- [ ] n8n running: `docker ps | grep e2bot-n8n-dev`
- [ ] OAuth credentials updated and valid (from previous Phase 1 work)
- [ ] Google Calendar accessible: Test credential in n8n UI
- [ ] PostgreSQL database operational
- [ ] WF05 v7 working (confirms Google Calendar credentials valid)

### Backup Current State
```bash
# 1. Export WF06 v1 (current production) as backup
# n8n UI → Workflows → WF06 v1 → Download
# Save to: n8n/workflows/old/06_calendar_availability_service_v1_backup_20260418.json

# 2. Note current webhook URL
# WF06 v1 → Webhook Trigger node → Copy URL
# Example: http://localhost:5678/webhook/calendar-availability
```

---

## Deployment Steps

### Step 1: Import WF06 V2 to n8n

**Method 1: UI Import** (Recommended):
```bash
# 1. Open n8n
http://localhost:5678

# 2. Navigate to Workflows
# Left sidebar → Workflows

# 3. Import WF06 v2
# Click "+ Add workflow" (top-right corner)
# Click "Import from file"
# Select: /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/06_calendar_availability_service_v2.json
# Click "Import"

# 4. Verify import success
# Workflow should open automatically
# Check: All 11 nodes visible (Webhook → Parse → Route → 2 paths → Response)
```

**Method 2: Docker Copy** (Alternative):
```bash
# Copy file directly to n8n container
docker cp n8n/workflows/06_calendar_availability_service_v2.json \
  e2bot-n8n-dev:/home/node/.n8n/workflows/

# Restart n8n to detect new workflow
docker restart e2bot-n8n-dev

# Wait 10-15 seconds for restart
sleep 15

# Verify n8n accessible
curl -s http://localhost:5678 | grep -q "n8n" && echo "✅ n8n running" || echo "❌ n8n not accessible"
```

### Step 2: Activate WF06 V2

```bash
# 1. In n8n UI, open WF06 v2 workflow
# 2. Click "Active" toggle (top-right, next to workflow name)
# 3. Verify toggle turns green: "Active"

# 4. Copy webhook URL from "Webhook Trigger" node
# Click "Webhook Trigger" node
# URL displayed in node details (e.g., http://localhost:5678/webhook/calendar-availability)
# Save this URL for testing
```

### Step 3: Initial Smoke Test

**Test 1: Empty Calendar Validation** (Primary Fix):
```bash
# SETUP: Ensure Google Calendar has NO events in next 7 days
# (If events exist, this is fine - just note them for Test 2)

# Execute request
curl -X POST http://localhost:5678/webhook/calendar-availability \
  -H "Content-Type: application/json" \
  -d '{
    "action": "next_dates",
    "count": 3,
    "service_type": "energia_solar",
    "duration_minutes": 120
  }'

# Expected Response (V2 SUCCESS):
{
  "success": true,
  "action": "next_dates",
  "dates": [
    {
      "date": "2026-04-21",
      "display": "Amanhã (21/04)",
      "day_of_week": "Segunda",
      "total_slots": 8,
      "quality": "high",
      "slots": [
        { "start_time": "08:00", "end_time": "10:00" },
        { "start_time": "10:00", "end_time": "12:00" },
        // ... 6 more slots
      ]
    },
    // ... 2 more dates
  ],
  "total_available": 3
}

# Validation:
# ✅ No "Cannot read properties of undefined" error
# ✅ Response contains 3 dates
# ✅ Each date has total_slots between 1-8
# ✅ HTTP status 200

# Check n8n execution logs:
# n8n UI → Executions tab → Click latest execution
# Expand "Calculate Slot Availability" node
# Look for: "ℹ️ [WF06 V2] Empty calendar detected - all slots will be available"
```

**Test 2: Event Conflict Detection** (Regression Check):
```bash
# SETUP: Create 1 test event in Google Calendar
# Date: Next Monday (e.g., 2026-04-21)
# Time: 10:00-12:00
# Title: "Test Event - WF06 v2 Validation"

# Execute request for specific date
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
    { "start_time": "14:00", "end_time": "16:00", "formatted": "14h às 16h" },
    { "start_time": "16:00", "end_time": "18:00", "formatted": "16h às 18h" }
  ],
  "total_available": 4
}

# Validation:
# ✅ 10:00 slot EXCLUDED (conflict with test event)
# ✅ 08:00, 12:00, 14:00, 16:00 slots PRESENT
# ✅ total_available = 4 (not 8, confirms conflict detection works)

# Check logs:
# Expand "Calculate Available Slots" node
# Look for:
# - "📊 [WF06 V2] Calculating slots for 2026-04-21 with 1 events"
# - "❌ [WF06 V2] Occupied: 10:00-12:00"
# - "✅ [WF06 V2] Available: 08:00-10:00"
```

---

## Integration with WF02 V80

### Step 4: Update WF02 V80 HTTP Request URLs

**WF02 V80 has 2 HTTP Request nodes that call WF06**:

1. **State 8 (next_dates)**: "HTTP Request - Get Next Dates"
2. **State 11 (available_slots)**: "HTTP Request - Get Available Slots"

**Update Procedure**:
```bash
# 1. Open WF02 V80 in n8n UI
http://localhost:5678/workflow/ja97SAbNzpFkG1ZJ

# 2. Find HTTP Request nodes (search for "HTTP Request")
# There should be 2 nodes with URLs like:
# - http://localhost:5678/webhook/calendar-availability (current)

# 3. Verify URLs already point to correct webhook
# WF06 v1 and v2 use SAME webhook path: /webhook/calendar-availability
# No URL change needed! ✅

# 4. Test WF02 integration (next step)
```

**Important Note**: WF06 v1 and v2 use the **same webhook path** (`calendar-availability`). When you activate v2 and deactivate v1, the webhook automatically routes to v2. No URL updates needed in WF02!

### Step 5: End-to-End WF02 Integration Test

**Test 3: WF02 V80 → WF06 V2 Flow** (Full Integration):
```bash
# 1. Deactivate WF06 v1 (if still active)
# n8n UI → WF06 v1 → Toggle "Active" OFF

# 2. Ensure WF06 v2 active
# n8n UI → WF06 v2 → Verify "Active" toggle GREEN

# 3. Trigger WF02 via WhatsApp or manual execution
# Option A: Send WhatsApp message to bot
# Option B: Manual execution in n8n UI with test data:
{
  "phone_number": "5562999999999",
  "lead_name": "Test User",
  "service_type": "energia_solar",
  "current_state": 7
}

# 4. Monitor execution flow
# WF02 should reach state 8 (next_dates request)
# Check WF02 execution → HTTP Request node output
# Verify dates received from WF06 v2

# Expected WF02 State 8 Response:
"Ótimo! Tenho algumas opções de data para sua visita técnica:

1️⃣ Amanhã (21/04) - 8 horários disponíveis
2️⃣ Terça (22/04) - 8 horários disponíveis
3️⃣ Quarta (23/04) - 8 horários disponíveis

Qual data prefere? (Digite o número)"

# 5. Continue conversation to state 11 (available_slots)
# User selects date → WF02 calls WF06 v2 for slots
# Expected: List of specific time slots (08:00-10:00, etc.)
```

---

## Post-Deployment Validation

### Validation Checklist

**Functional Requirements**:
- [ ] **Test 1 PASS**: Empty calendar returns all slots (no crashes)
- [ ] **Test 2 PASS**: Event conflicts detected correctly (10:00 slot excluded)
- [ ] **Test 3 PASS**: WF02 V80 integration working (dates displayed in conversation)
- [ ] **No undefined errors** in 5 consecutive executions

**Performance Requirements**:
- [ ] `next_dates` response time < 2 seconds (3 dates)
- [ ] `available_slots` response time < 1 second (single date)
- [ ] n8n execution logs show no errors or warnings

**Operational Requirements**:
- [ ] WF06 v2 active in n8n (green toggle)
- [ ] WF06 v1 deactivated (gray toggle) OR deleted
- [ ] No orphaned webhook executions in n8n error logs

### Monitor First 10 Production Executions

```bash
# 1. Check n8n execution history
# n8n UI → Executions → Filter by "06_calendar_availability_service_v2"

# 2. For each execution, verify:
# - Status: SUCCESS (green checkmark)
# - Duration: < 2s for next_dates, < 1s for available_slots
# - Output: Valid JSON response with dates/slots

# 3. Check for error patterns
docker logs e2bot-n8n-dev | grep -E "WF06 V2|Cannot read properties|undefined" | tail -20

# Expected: Only "ℹ️ [WF06 V2]" info logs, NO errors

# 4. If errors found:
# - Note execution ID
# - Check execution details in n8n UI
# - Verify OAuth credentials still valid
# - Check Google Calendar API quota (should be <1% used)
```

---

## Rollback Procedure

**If WF06 v2 fails and rollback required**:

```bash
# 1. Deactivate WF06 v2
# n8n UI → WF06 v2 → Toggle "Active" OFF

# 2. Reactivate WF06 v1 (if not deleted)
# n8n UI → WF06 v1 → Toggle "Active" ON

# OR: Re-import backup
# n8n UI → Import from file
# Select: n8n/workflows/old/06_calendar_availability_service_v1_backup_20260418.json

# 3. Verify WF06 v1 operational
curl -X POST http://localhost:5678/webhook/calendar-availability \
  -H "Content-Type: application/json" \
  -d '{"action": "next_dates", "count": 1}'

# 4. Investigate WF06 v2 failure
# Collect execution logs, error messages, OAuth status
# Create issue report with details for analysis
```

---

## Cleanup (After 48h Successful Operation)

```bash
# After WF06 v2 runs successfully for 48 hours:

# 1. Archive WF06 v1
# n8n UI → WF06 v1 → Delete (or Export and delete)

# 2. Move backup to archive
mv n8n/workflows/old/06_calendar_availability_service_v1_backup_20260418.json \
   n8n/workflows/old/archive/

# 3. Update documentation
# Update CLAUDE.md with v2 status
# Archive old implementation guides
```

---

## Documentation Updates

### Update CLAUDE.md

```markdown
| **06** | V2 ✅ | - | Calendar availability + empty calendar fix | WF02 integration

**Implementation**:
- **WF06 V2**: docs/deployment/DEPLOY_WF06_V2_EMPTY_CALENDAR_FIX.md (Empty calendar handling)
```

### Create Deployment Summary

File: `docs/deployment/DEPLOY_WF06_V2_EMPTY_CALENDAR_FIX.md` (this file)

Key sections:
- Pre-deployment checklist ✅
- Step-by-step deployment procedure ✅
- Testing protocol (3 tests) ✅
- Post-deployment validation ✅
- Rollback procedure ✅

---

## Success Criteria

### Functional
- ✅ 0 `Cannot read properties of undefined` errors in 10 consecutive executions
- ✅ Empty calendar handling graceful (all slots available)
- ✅ Event conflict detection accuracy: 100% (Test 2 slot exclusion verified)
- ✅ WF02 V80 integration successful (states 8 and 11 working)

### Performance
- ✅ `next_dates` response time < 2 seconds (3 dates)
- ✅ `available_slots` response time < 1 second (single date)
- ✅ No execution timeouts or retry failures

### Operational
- ✅ WF06 v2 active and stable for 48 hours
- ✅ No manual interventions required
- ✅ Error rate < 1% over 50 executions

---

## Key Learnings

### Technical Insights
1. **n8n Empty Calendar Behavior**: Returns `[{ json: {} }]` not `[]` for empty calendars
2. **Filter Strategy**: Check for meaningful properties (id, start) instead of `.length > 0`
3. **Defensive Programming**: Multi-layer validation prevents cascading failures

### Deployment Best Practices
1. **Same Webhook Path**: v1 and v2 can share path, simplifies integration updates
2. **Incremental Testing**: 3-test protocol catches both fixes and regressions
3. **Production Monitoring**: First 10 executions critical for early issue detection

---

**Deployment Status**: READY FOR PRODUCTION
**Estimated Time**: 30-45 minutes (import + testing)
**Risk Level**: LOW (OAuth already fixed, single-node logic change)
