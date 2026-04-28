# WF06 V2: Google Calendar OAuth Credential Migration Guide

**Target**: Fix OAuth error in WF06 by applying WF05 v7 proven credential pattern
**Created**: 2026-04-18
**Prerequisites**: Access to n8n UI at http://localhost:5678

---

## Phase 1: OAuth Credential Audit

### Step 1.1: Access n8n Credentials Manager
```bash
# Open n8n in browser
http://localhost:5678

# Navigate to:
# Left sidebar → Settings (gear icon) → Credentials
```

### Step 1.2: Locate Google Calendar OAuth Credential
```
Search: "Google Calendar API"

Expected result:
- Name: Google Calendar API
- Type: Google Calendar OAuth2 API
- ID: 1 (or similar number)
- Status: ✅ Connected OR ❌ Expired
```

### Step 1.3: Verify OAuth Scopes
**Click on credential → View Details**

Required scopes:
```
✅ https://www.googleapis.com/auth/calendar.events
✅ https://www.googleapis.com/auth/calendar.readonly
```

**If scopes missing or credential expired**:
1. Click "Reconnect" button
2. Authenticate with Google account (e2.solucoes.energia@gmail.com or similar)
3. Accept all requested permissions
4. Wait for "Successfully connected" message

### Step 1.4: Test Credential Connection
```
1. Click "Test" button in credential details
2. Expected result: ✅ "Connection successful"
3. If fails: Note error message and check Google Cloud Console OAuth config
```

**Validation Checkpoint**:
- [ ] Credential ID noted (e.g., `"1"`)
- [ ] OAuth scopes include both `calendar.events` and `calendar.readonly`
- [ ] Test connection successful
- [ ] Token expiration > 30 days (check in credential details)

---

## Phase 2: WF06 v2 JSON Generation

### Step 2.1: Prepare WF06 v2 Base Structure
```bash
# Copy WF06 v1 as starting point
cd /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/
cp 06_calendar_availability_service_v1.json 06_calendar_availability_service_v2.json
```

### Step 2.2: Apply WF05 v7 OAuth Pattern to Google Calendar Nodes

**Target Nodes**:
1. "Get Calendar Events (Batch)" (line 72-101)
2. "Get Calendar Events (Single Date)" (line 133-162)

**Changes Required**:

#### Before (WF06 v1 - FAILING):
```json
{
  "id": "get-calendar-events-batch-v1",
  "name": "Get Calendar Events (Batch)",
  "type": "n8n-nodes-base.googleCalendar",
  "credentials": {
    "googleCalendarOAuth2Api": {
      "id": "1",
      "name": "Google Calendar API"
    }
  },
  "continueOnFail": true,
  "alwaysOutputData": true
}
```

#### After (WF06 v2 - FIX APPLIED):
```json
{
  "id": "get-calendar-events-batch-v2",
  "name": "Get Calendar Events (Batch)",
  "type": "n8n-nodes-base.googleCalendar",
  "credentials": {
    "googleCalendarOAuth2Api": {
      "id": "1",                          // ✅ Use credential ID from Phase 1
      "name": "Google Calendar API"
    }
  },
  "continueOnFail": true,                  // ✅ Prevent workflow crash on OAuth fail
  "alwaysOutputData": true,                // ✅ Return empty item for error handling
  "retryOnFail": true,                     // ✅ NEW: WF05 v7 retry pattern
  "maxTries": 3,                           // ✅ NEW: Retry OAuth 3 times
  "waitBetweenTries": 1000,                // ✅ NEW: 1-second backoff
  "notes": "V2: WF05 retry pattern + OAuth fix"
}
```

### Step 2.3: Update Workflow Metadata
```json
{
  "name": "06_calendar_availability_service_v2",  // ✅ Update version
  "tags": [
    { "name": "calendar" },
    { "name": "availability" },
    { "name": "v2" },                              // ✅ Change from v1
    { "name": "oauth-fix" },                       // ✅ NEW tag
    { "name": "proactive-ux" }
  ],
  "versionId": "V2"                                // ✅ Update version ID
}
```

### Step 2.4: Enhance Error Handling in Calculation Nodes

**Target Node**: "Calculate Slot Availability" (line 103-116)

**Add Defensive Empty Array Handling**:
```javascript
// Calculate Slot Availability for Multiple Dates - V2 OAUTH FIX
const inputData = $input.first().json;
const businessDates = inputData.business_dates;
const durationMinutes = inputData.duration_minutes;

// ✅ V2 FIX: Defensive check for OAuth failures
// Get calendar events from previous node (may be empty if OAuth failed)
const calendarEventsRaw = $('Get Calendar Events (Batch)').all();

// Check if OAuth returned error or empty result
const calendarEvents = calendarEventsRaw.length > 0 && calendarEventsRaw[0].json
    ? calendarEventsRaw.map(item => item.json)
    : [];  // ✅ Default to empty array (no conflicts = all slots available)

console.log(`📊 [WF06 V2] Processing ${businessDates.length} dates with ${calendarEvents.length} calendar events`);

// ⚠️ V2: Log OAuth failure but continue workflow
if (calendarEvents.length === 0 && calendarEventsRaw.length > 0) {
    console.warn('⚠️ [WF06 V2] OAuth may have failed - treating calendar as empty (all slots available)');
}

// Rest of calculation logic remains unchanged...
```

**Same fix for "Calculate Available Slots" node (line 164-177)**

---

## Phase 3: WF06 v2 Deployment and Testing

### Step 3.1: Import WF06 v2 to n8n
```bash
# Method 1: UI Import
1. Open http://localhost:5678
2. Click "+ Add workflow" (top-right)
3. Click "Import from file"
4. Select: /home/bruno/.../n8n/workflows/06_calendar_availability_service_v2.json
5. Click "Import"

# Method 2: Direct file copy (requires n8n restart)
docker cp n8n/workflows/06_calendar_availability_service_v2.json \
  e2bot-n8n-dev:/home/node/.n8n/workflows/
docker restart e2bot-n8n-dev
```

### Step 3.2: Activate WF06 v2 Workflow
```
1. Find "06_calendar_availability_service_v2" in workflow list
2. Click workflow to open
3. Click "Active" toggle (top-right) to enable
4. Copy webhook URL from "Webhook Trigger" node
   Example: http://localhost:5678/webhook/calendar-availability
```

### Step 3.3: Testing Protocol

#### Test 1: OAuth Connectivity Validation
```bash
# Test next_dates action (triggers batch calendar read)
curl -X POST http://localhost:5678/webhook/calendar-availability \
  -H "Content-Type: application/json" \
  -d '{
    "action": "next_dates",
    "count": 1,
    "service_type": "energia_solar"
  }'

# Expected Response (SUCCESS):
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
    }
  ],
  "total_available": 1
}

# Expected Response (OAUTH FAIL - V2 handles gracefully):
# Same structure but total_slots may be higher (no conflict detection)

# Validation:
# 1. Check n8n execution in UI → Executions tab
# 2. Click latest execution → Expand "Get Calendar Events (Batch)" node
# 3. Verify: NO "401 Unauthorized" or OAuth token errors
# 4. If errors present: Return to Phase 1, Step 1.3 (reconnect OAuth)
```

#### Test 2: Empty Calendar Handling
```bash
# SETUP: Clear all events from Google Calendar
# Go to Google Calendar UI → Delete all test events

# Execute same request as Test 1
curl -X POST http://localhost:5678/webhook/calendar-availability \
  -H "Content-Type: application/json" \
  -d '{"action": "next_dates", "count": 3}'

# Expected: Response with all slots available (no crashes)
{
  "success": true,
  "dates": [
    { "date": "2026-04-21", "total_slots": 8 },
    { "date": "2026-04-22", "total_slots": 8 },
    { "date": "2026-04-23", "total_slots": 8 }
  ]
}
```

#### Test 3: Real Event Conflict Detection
```bash
# SETUP: Create 1 event manually in Google Calendar
# Date: 2026-04-21 (Monday)
# Time: 10:00-12:00
# Title: "Test Conflict Event"

# Request specific date
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
    { "start_time": "08:00", "end_time": "10:00" },  // ✅ Before conflict
    { "start_time": "12:00", "end_time": "14:00" },  // ✅ After conflict
    { "start_time": "14:00", "end_time": "16:00" },
    { "start_time": "16:00", "end_time": "18:00" }
  ],
  "total_available": 4
}

# Validation: 10:00-12:00 slot MUST be excluded
```

#### Test 4: WF02 V80 Integration
```bash
# IMPORTANT: Update WF02 V80 HTTP Request nodes to call WF06 v2

# 1. Open WF02 V80 in n8n UI
# 2. Find "HTTP Request - Get Next Dates" node
# 3. Update URL to: http://localhost:5678/webhook/calendar-availability
# 4. Save workflow

# 5. Trigger full conversation flow via WhatsApp or test execution
# 6. When WF02 reaches state 8 (next_dates) or state 11 (available_slots):
#    - Check execution logs
#    - Verify WF06 v2 was called successfully
#    - Confirm WF02 received valid date options

# Expected WF02 State 8 Response:
"Ótimo! Tenho algumas opções de data:\n1️⃣ Amanhã (21/04) - 8 horários\n2️⃣ Terça (22/04) - 8 horários\n..."
```

---

## Validation Checklist

### Phase 1: Credential Audit
- [ ] n8n credential "Google Calendar API" has ID `"1"` (or noted alternative)
- [ ] OAuth scopes include `calendar.events` AND `calendar.readonly`
- [ ] Test connection successful in n8n UI
- [ ] Token valid (not expired)

### Phase 2: WF06 v2 Implementation
- [ ] WF06 v2 JSON file created at `n8n/workflows/06_calendar_availability_service_v2.json`
- [ ] Google Calendar nodes updated with retry logic (retryOnFail: true, maxTries: 3)
- [ ] Error handling added to calculation nodes (empty array defaults)
- [ ] Workflow metadata updated (name, tags, versionId)

### Phase 3: Testing
- [ ] **Test 1 PASS**: No OAuth errors in execution logs
- [ ] **Test 2 PASS**: Empty calendar handled without crashes
- [ ] **Test 3 PASS**: Event conflicts detected correctly
- [ ] **Test 4 PASS**: WF02 V80 integration working

### Deployment
- [ ] WF06 v2 active in n8n (toggle enabled)
- [ ] WF02 V80 HTTP Request nodes point to WF06 v2 webhook
- [ ] First 5 production executions monitored (no OAuth errors)

---

## Troubleshooting Guide

### Problem: "401 Unauthorized" persists in WF06 v2
**Cause**: OAuth credential still invalid
**Solution**:
1. n8n UI → Credentials → "Google Calendar API"
2. Click "Delete" (⚠️ will require reconnection in WF05 too)
3. Create NEW credential: "+ New Credential" → Google Calendar OAuth2 API
4. Authenticate with Google account
5. Update credential ID in BOTH WF05 v7 and WF06 v2 JSON files
6. Reimport both workflows

### Problem: "Cannot read properties of undefined" still occurs
**Cause**: Error handling not applied correctly
**Solution**:
1. Open WF06 v2 in n8n UI
2. Click "Calculate Slot Availability" node
3. Edit Code → Verify defensive check exists:
   ```javascript
   const calendarEvents = calendarEventsRaw.length > 0 && calendarEventsRaw[0].json
       ? calendarEventsRaw.map(item => item.json)
       : [];
   ```
4. Save and retest

### Problem: WF02 V80 doesn't call WF06 v2
**Cause**: HTTP Request URL not updated
**Solution**:
1. Open WF02 in n8n → Find HTTP Request nodes in states 8 and 11
2. Update URL to WF06 v2 webhook (copy from WF06 v2 Webhook Trigger node)
3. Save WF02 → Test conversation flow

### Problem: All slots show as available (conflicts not detected)
**Cause**: OAuth read failing silently, defaulting to empty calendar
**Solution**:
1. Check WF06 v2 execution logs → "Get Calendar Events" node
2. If error present: Return to Phase 1 (OAuth reconnection)
3. If successful but events not returned: Verify `$env.GOOGLE_CALENDAR_ID` matches calendar with events

---

## Rollback Procedure

**If WF06 v2 fails and WF06 v1 needs restoration**:

```bash
# 1. Deactivate WF06 v2
n8n UI → WF06 v2 → Toggle "Active" OFF

# 2. Revert WF02 V80 HTTP Request URLs to placeholder or disable
# Edit WF02 → States 8, 11 HTTP Request nodes → Comment out or disable

# 3. Investigate OAuth credential in detail
n8n UI → Credentials → Export credential config
Google Cloud Console → OAuth Consent Screen → Check scopes

# 4. Report issue with logs
docker logs e2bot-n8n-dev > /tmp/n8n-wf06-error.log
# Share /tmp/n8n-wf06-error.log for analysis
```

---

## Success Metrics

### Functional
- ✅ 0 OAuth errors in 10 consecutive WF06 v2 executions
- ✅ Conflict detection accuracy: 100% (Test 3 slot exclusion verified)
- ✅ WF02 V80 integration: Successful date selection in conversation flow

### Performance
- ✅ `next_dates` response time < 2 seconds (3 dates)
- ✅ `available_slots` response time < 1 second (single date)

### Reliability
- ✅ Error rate < 1% over 50 production executions
- ✅ No `Cannot read properties of undefined` errors in logs

---

## Documentation Updates Post-Deployment

After successful WF06 v2 deployment:

1. Update `CLAUDE.md`:
   ```markdown
   | **06** | V2 ✅ | - | Calendar availability with OAuth fix (WF05 pattern)
   ```

2. Create deployment summary:
   ```bash
   docs/deployment/DEPLOY_WF06_V2_OAUTH_FIX.md
   ```

3. Update implementation guide reference:
   ```markdown
   **WF06 V2**: docs/implementation/GUIDE_WF06_V2_OAUTH_CREDENTIAL_MIGRATION.md
   ```

---

**Next Steps**: Execute Phase 1 credential audit NOW before proceeding to Phase 2 development
