# PLAN WF06 V2: Google Calendar OAuth Fix

**Status**: Strategic Plan
**Created**: 2026-04-18
**Target**: WF06 v2 with Working OAuth Credentials

---

## Root Cause Analysis

### Error Summary
- **Primary Error**: OAuth token invalid/expired in WF06 v1 "Get Calendar Events (Batch)" node
- **Secondary Error**: `Cannot read properties of undefined (reading 'length')` in "Calculate Slot Availability"
- **Root Cause**: WF06 v1 uses credential ID `"1"` which is different/expired compared to WF05 v7's working credential

### Comparative Analysis: WF05 v7 (✅ Working) vs WF06 v1 (❌ Failing)

#### WF05 v7 - Create Google Calendar Event (Line 86-121)
```json
{
  "id": "create-google-event-v2",
  "name": "Create Google Calendar Event",
  "type": "n8n-nodes-base.googleCalendar",
  "credentials": {
    "googleCalendarOAuth2Api": {
      "id": "1",                          // ✅ SAME ID BUT WORKS
      "name": "Google Calendar API"
    }
  },
  "parameters": {
    "resource": "event",
    "operation": "create",                // ✅ WRITE OPERATION
    "calendarId": "={{ $env.GOOGLE_CALENDAR_ID }}"
  }
}
```

#### WF06 v1 - Get Calendar Events (Batch) (Line 72-101)
```json
{
  "id": "get-calendar-events-batch-v1",
  "name": "Get Calendar Events (Batch)",
  "type": "n8n-nodes-base.googleCalendar",
  "credentials": {
    "googleCalendarOAuth2Api": {
      "id": "1",                          // ❌ SAME ID BUT FAILS
      "name": "Google Calendar API"
    }
  },
  "parameters": {
    "resource": "event",
    "operation": "getAll",                // ❌ READ OPERATION
    "calendarId": "={{ $env.GOOGLE_CALENDAR_ID }}"
  }
}
```

### Critical Insights

1. **Credential ID Mismatch Theory INVALID**: Both workflows use credential ID `"1"` with same name
2. **OAuth Scope Hypothesis**: WF05 creates events (write), WF06 reads events (read) → **Possible insufficient OAuth scopes**
3. **Token Expiration**: OAuth token may have expired AFTER WF05 v7 deployment but BEFORE WF06 v1 testing
4. **Credential Configuration Drift**: n8n credential ID `"1"` may have been reconfigured without updating WF06

### Why WF05 Works and WF06 Fails

**Hypothesis 1: OAuth Scope Mismatch**
- WF05 v7 only requires `https://www.googleapis.com/auth/calendar.events` (write events)
- WF06 v1 requires `https://www.googleapis.com/auth/calendar.readonly` (read events)
- Current credential may lack read scope

**Hypothesis 2: Token Expiration After WF05 Deployment**
- WF05 v7 was deployed when token was valid
- Token expired before WF06 v1 testing
- n8n cached valid token for WF05, but refreshes for WF06 failed

**Hypothesis 3: n8n Credential Refresh Bug**
- WF05 write operations succeed (cached token or different refresh mechanism)
- WF06 read operations fail (token refresh fails silently)

---

## WF06 v2 Strategic Plan

### Objective
Fix Google Calendar OAuth authentication using proven WF05 v7 credential pattern

### Strategy: 3-Phase OAuth Validation Approach

#### Phase 1: Credential Audit (Pre-Development)
**Actions**:
1. Access n8n UI → Settings → Credentials
2. Find credential ID `"1"` ("Google Calendar API")
3. Verify OAuth scopes include:
   - `https://www.googleapis.com/auth/calendar.events` (read/write events)
   - `https://www.googleapis.com/auth/calendar.readonly` (read calendar)
4. Check token expiration status
5. If expired: **Reconnect OAuth** (re-authenticate via Google)

**Validation Gate**:
- ✅ OAuth token valid (tested via n8n credential test)
- ✅ Scopes include both read and write permissions
- ✅ Token expiration > 30 days

#### Phase 2: WF06 v2 Implementation (Copy WF05 Pattern)
**Actions**:
1. Clone WF06 v1 → WF06 v2
2. Update Google Calendar nodes to match WF05 v7 pattern:
   - Use EXACT credential configuration from WF05 v7
   - Add `continueOnFail: true` + `alwaysOutputData: true` (WF05 pattern)
   - Add retry logic: `retryOnFail: true, maxTries: 3, waitBetweenTries: 1000`
3. Add defensive error handling in "Calculate Slot Availability":
   ```javascript
   // V2 FIX: Defensive check for empty calendar events
   const calendarEvents = $('Get Calendar Events (Batch)').all().length > 0
       ? $('Get Calendar Events (Batch)').all().map(item => item.json)
       : [];  // ✅ Default to empty array if OAuth fails
   ```

**Validation Gate**:
- ✅ WF06 v2 JSON syntax valid
- ✅ All Google Calendar nodes use credential ID from Phase 1
- ✅ Error handling prevents undefined access

#### Phase 3: Incremental Testing (Validation Protocol)
**Test Sequence**:
1. **Test 1: OAuth Connectivity**
   - Trigger: Webhook with `{ "action": "next_dates", "count": 1 }`
   - Expected: No OAuth errors in "Get Calendar Events (Batch)"
   - Validation: Check n8n execution logs for `401 Unauthorized` or token errors

2. **Test 2: Empty Calendar Handling**
   - Setup: Clear all events from test calendar
   - Trigger: Same request as Test 1
   - Expected: WF06 v2 returns `{ dates: [], total_available: 0 }` (no crash)

3. **Test 3: Real Event Conflict Detection**
   - Setup: Create 1 event manually at 10:00-12:00 via Google Calendar UI
   - Trigger: Request `{ "action": "available_slots", "date": "2026-04-21" }`
   - Expected: Response excludes 10:00 slot, includes 08:00 and 13:00+

4. **Test 4: WF02 V80 Integration**
   - Trigger: Complete conversation flow in WF02 V80 (service 1 or 3)
   - Expected: WF02 calls WF06 v2 successfully, receives valid dates

**Validation Gate**:
- ✅ All 4 tests pass without OAuth errors
- ✅ WF02 V80 integration successful
- ✅ Error logs show no undefined access

---

## Implementation Checklist

### Pre-Development
- [ ] Audit n8n credential ID `"1"` OAuth scopes
- [ ] Verify token expiration and refresh if needed
- [ ] Document current credential configuration

### Development
- [ ] Create `/home/bruno/.../n8n/workflows/06_calendar_availability_service_v2.json`
- [ ] Copy WF06 v1 structure as base
- [ ] Update all Google Calendar nodes with WF05 v7 credential pattern
- [ ] Add defensive error handling in calculation nodes
- [ ] Add retry logic (3x) to Google Calendar nodes

### Testing
- [ ] Test 1: OAuth connectivity validated
- [ ] Test 2: Empty calendar handling confirmed
- [ ] Test 3: Event conflict detection working
- [ ] Test 4: WF02 V80 integration successful

### Deployment
- [ ] Import WF06 v2 to n8n (http://localhost:5678)
- [ ] Update WF02 V80 HTTP Request nodes to call WF06 v2 webhook URL
- [ ] Monitor first 5 production executions for OAuth errors
- [ ] Document final credential configuration in README

---

## Risk Assessment

### High Risk (Must Address)
1. **OAuth Scope Insufficient**: Current credential lacks `calendar.readonly` scope
   - **Mitigation**: Phase 1 audit verifies scopes BEFORE development

2. **Token Refresh Failure**: n8n cannot refresh expired token
   - **Mitigation**: Manual OAuth reconnection in Phase 1

### Medium Risk (Monitor)
1. **Credential ID Confusion**: n8n credential ID `"1"` may not be stable across restarts
   - **Mitigation**: Document exact credential name and ID for verification

2. **$env.GOOGLE_CALENDAR_ID Mismatch**: WF05 and WF06 may target different calendars
   - **Mitigation**: Verify both use same environment variable value

### Low Risk (Acceptable)
1. **Calendar API Rate Limits**: Google Calendar API has 1M requests/day limit
   - **Mitigation**: WF06 batch optimization (1 request per date range vs N requests per date)

---

## Success Criteria

### Functional Requirements
- ✅ WF06 v2 successfully reads Google Calendar events without OAuth errors
- ✅ Slot availability calculation handles empty calendars gracefully
- ✅ WF02 V80 integration calls WF06 v2 and receives valid responses
- ✅ No `Cannot read properties of undefined` errors in production

### Performance Requirements
- ✅ Response time < 2 seconds for `next_dates` (3 dates)
- ✅ Response time < 1 second for `available_slots` (single date)
- ✅ Error rate < 1% for OAuth token refresh operations

### Documentation Requirements
- ✅ OAuth credential configuration documented in deployment guide
- ✅ Testing protocol with 4 validation tests documented
- ✅ WF06 v2 architecture diagram showing credential flow

---

## Next Steps

1. **Execute Phase 1**: Audit n8n OAuth credential immediately
2. **Create Implementation Guide**: Detailed step-by-step credential migration
3. **Generate WF06 v2 JSON**: Apply WF05 v7 pattern to WF06 v1 base
4. **Execute Testing Protocol**: Run all 4 validation tests before production

**Estimated Timeline**: 2-3 hours (1h audit + 1h development + 1h testing)
