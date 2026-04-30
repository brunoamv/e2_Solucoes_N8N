# BUGFIX WF05 V8 - Missing appointment_reminders Table + Google OAuth Expired

**Date**: 2026-04-28
**Version**: WF05 V8 (V7 + Database Schema + OAuth Fix)
**Severity**: 🔴 CRITICAL - Workflow fails after Google Calendar event creation
**Execution**: http://localhost:5678/workflow/42eG7UpfmZ2PoBlY/executions/10081
**Root Causes**:
1. PostgreSQL table `appointment_reminders` does not exist
2. Google Calendar OAuth credentials invalid/expired
**Status**: 🔴 REQUIRES ACTION

---

## 🎯 Executive Summary

**Problem 1 - PostgreSQL**: WF05 V7 execution 10081 fails at "Create Appointment Reminders" node with error:
```
relation "appointment_reminders" does not exist
```

**Problem 2 - Google OAuth**: "Create Google Calendar Event" node fails with error:
```
The provided authorization grant (e.g., authorization code, resource owner credentials) or refresh token is invalid, expired, revoked, does not match the redirection URI used in the authorization request, or was issued to another client.
```

**V7 Status**: ✅ Workflow logic correct (hardcoded business hours working)

**Real Issue**:
1. Database schema incomplete - `appointment_reminders` table never created
2. Google Calendar OAuth2 credentials expired or misconfigured

**Solution**:
1. Create `appointment_reminders` table with proper schema
2. Re-authenticate Google Calendar OAuth2 credentials in n8n

---

## 🔍 Complete Root Cause Analysis

### Problem 1: Missing appointment_reminders Table

**Error Details**:
```
Problem in node 'Create Appointment Reminders'
relation "appointment_reminders" does not exist
```

**Database Verification**:
```bash
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "\dt appointment*"

            List of relations
 Schema |     Name     | Type  |  Owner
--------+--------------+-------+----------
 public | appointments | table | postgres
(1 row)
```

**Conclusion**: ❌ Table `appointment_reminders` does NOT exist

**Node Configuration** (Line 148):
```sql
INSERT INTO appointment_reminders (
    appointment_id,
    reminder_type,
    reminder_time,
    status,
    created_at
)
SELECT
    '{{ $('Build Calendar Event Data').item.json.appointment_id }}'::uuid,
    'email' as reminder_type,
    a.scheduled_date + (a.scheduled_time_start - interval '24 hours') as reminder_time,
    'pending' as status,
    NOW() as created_at
FROM appointments a
WHERE a.id = '{{ $('Build Calendar Event Data').item.json.appointment_id }}'
  AND a.google_calendar_event_id IS NOT NULL
ON CONFLICT (appointment_id, reminder_type, reminder_time) DO NOTHING
RETURNING id, reminder_type, reminder_time;
```

**Analysis**: Query expects table with:
- `id` (PK, likely UUID or SERIAL)
- `appointment_id` (FK to appointments.id, UUID)
- `reminder_type` (TEXT/VARCHAR)
- `reminder_time` (TIMESTAMP)
- `status` (TEXT/VARCHAR)
- `created_at` (TIMESTAMP)
- UNIQUE constraint on `(appointment_id, reminder_type, reminder_time)`

### Problem 2: Google Calendar OAuth Expired

**Error Details**:
```
The provided authorization grant (e.g., authorization code, resource owner credentials) or refresh token is invalid, expired, revoked, does not match the redirection URI used in the authorization request, or was issued to another client.
```

**Node Configuration** (Lines 86-120):
```json
{
  "name": "Create Google Calendar Event",
  "type": "n8n-nodes-base.googleCalendar",
  "credentials": {
    "googleCalendarOAuth2Api": {
      "id": "1",
      "name": "Google Calendar API"
    }
  },
  "parameters": {
    "calendarId": "={{ $env.GOOGLE_CALENDAR_ID }}",
    "start": "={{ $json.calendar_event.start.dateTime }}",
    "end": "={{ $json.calendar_event.end.dateTime }}"
  }
}
```

**Input Data** (From execution 10081):
```json
{
  "calendar_event": {
    "summary": "E2 Soluções - Agenda",
    "description": "Cliente: bruno rosa\nTelefone: 556181755748\nEmail: clima.cocal.2025@gmail.com\nServiço: Energia Solar\nCidade: cocal-go",
    "location": ", cocal-go,",
    "start": {
      "dateTime": "2026-04-29T11:00:00.000Z",
      "timeZone": "America/Sao_Paulo"
    },
    "end": {
      "dateTime": "2026-04-29T13:00:00.000Z",
      "timeZone": "America/Sao_Paulo"
    },
    "attendees": ["clima.cocal.2025@gmail.com"],
    "reminders": {
      "useDefault": false,
      "overrides": [
        {"method": "email", "minutes": 1440},
        {"method": "popup", "minutes": 30}
      ]
    },
    "colorId": "9"
  }
}
```

**Analysis**:
- ✅ Input data is valid and well-formed
- ✅ Timezone conversion correct (08:00 BRT → 11:00 UTC)
- ❌ OAuth2 credentials are invalid or expired

**Common OAuth Expiration Causes**:
1. Refresh token expired (Google revokes after 6 months of inactivity)
2. OAuth consent screen changed (requires re-authentication)
3. Google Calendar API disabled in Google Cloud Console
4. Credential ID mismatch (workflow expects id "1" but different credential exists)
5. OAuth redirect URI mismatch

---

## 🔧 V8 Solution

### Fix 1: Create appointment_reminders Table

**SQL Migration**:
```sql
-- Create appointment_reminders table
CREATE TABLE IF NOT EXISTS appointment_reminders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    appointment_id UUID NOT NULL REFERENCES appointments(id) ON DELETE CASCADE,
    reminder_type VARCHAR(50) NOT NULL,
    reminder_time TIMESTAMP NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    sent_at TIMESTAMP,
    error_message TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Prevent duplicate reminders
    CONSTRAINT unique_appointment_reminder UNIQUE (appointment_id, reminder_type, reminder_time)
);

-- Create index for efficient querying
CREATE INDEX idx_appointment_reminders_status ON appointment_reminders(status) WHERE status = 'pending';
CREATE INDEX idx_appointment_reminders_time ON appointment_reminders(reminder_time) WHERE status = 'pending';

-- Add comment
COMMENT ON TABLE appointment_reminders IS 'Stores appointment reminder notifications (email, SMS, etc.)';
```

**Field Descriptions**:
- `id`: Primary key (UUID)
- `appointment_id`: Foreign key to appointments table
- `reminder_type`: Type of reminder ('email', 'sms', 'whatsapp')
- `reminder_time`: When reminder should be sent
- `status`: Reminder status ('pending', 'sent', 'failed')
- `sent_at`: Timestamp when reminder was sent
- `error_message`: Error details if reminder failed
- `created_at`: Record creation timestamp
- `updated_at`: Last update timestamp

### Fix 2: Re-authenticate Google Calendar OAuth

**n8n OAuth Re-authentication Steps**:

1. **Open n8n Credentials**:
   - URL: http://localhost:5678/credentials
   - Find "Google Calendar API" (ID: 1)

2. **Delete Expired Credential** (if exists):
   - Click on "Google Calendar API" credential
   - Click "Delete" button
   - Confirm deletion

3. **Create New Google Calendar OAuth2 Credential**:
   - Click "Add Credential"
   - Select "Google Calendar OAuth2 API"
   - Name: "Google Calendar API"

4. **Configure OAuth Settings**:
   ```
   Client ID: [From Google Cloud Console]
   Client Secret: [From Google Cloud Console]
   Scope: https://www.googleapis.com/auth/calendar
   ```

5. **Authenticate**:
   - Click "Connect my account"
   - Sign in with Google account
   - Grant calendar access permissions
   - Verify "Connected" status shows green

6. **Test Connection**:
   - Open WF05 workflow
   - Execute "Create Google Calendar Event" node manually
   - Verify event created successfully

**Google Cloud Console Verification**:

1. **Enable Google Calendar API**:
   - URL: https://console.cloud.google.com/apis/library
   - Search "Google Calendar API"
   - Click "Enable" if not already enabled

2. **Verify OAuth Consent Screen**:
   - URL: https://console.cloud.google.com/apis/credentials/consent
   - Ensure app is not in "Testing" mode (or add test users)
   - Verify redirect URI matches n8n: `http://localhost:5678/rest/oauth2-credential/callback`

3. **Check OAuth 2.0 Client ID**:
   - URL: https://console.cloud.google.com/apis/credentials
   - Verify Client ID and Secret match n8n configuration
   - Ensure redirect URI is configured: `http://localhost:5678/rest/oauth2-credential/callback`

---

## ✅ Success Criteria

After V8 deployment:

### 1. Database Schema Complete
```bash
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "\d appointment_reminders"

# Expected:
#                              Table "public.appointment_reminders"
#      Column      |            Type             | Collation | Nullable |      Default
# -----------------+-----------------------------+-----------+----------+--------------------
#  id              | uuid                        |           | not null | gen_random_uuid()
#  appointment_id  | uuid                        |           | not null |
#  reminder_type   | character varying(50)       |           | not null |
#  reminder_time   | timestamp without time zone |           | not null |
#  status          | character varying(20)       |           | not null | 'pending'::character varying
#  sent_at         | timestamp without time zone |           |          |
#  error_message   | text                        |           |          |
#  created_at      | timestamp without time zone |           | not null | now()
#  updated_at      | timestamp without time zone |           |          | now()
```

### 2. Google OAuth Authenticated
```bash
# Test WF05 execution
curl -X POST http://localhost:5678/webhook-test/appointment-scheduler \
  -H "Content-Type: application/json" \
  -d '{"appointment_id": "valid-uuid-here"}'

# Expected: No OAuth errors, event created successfully
```

### 3. Complete WF05 Flow
```
1. WF02 triggers WF05 with appointment_id ✅
2. "Validate Input Data" validates UUID ✅
3. "Get Appointment & Lead Data" retrieves data ✅
4. "Validate Availability" checks business hours ✅
5. "Build Calendar Event Data" creates event object ✅
6. "Create Google Calendar Event" SUCCEEDS ✅ (NOT OAuth error!)
7. "Update Appointment" sets status to 'confirmado' ✅
8. "Create Appointment Reminders" creates reminder record ✅ (NOT table error!)
9. "Prepare Email Trigger Data" merges data ✅
10. "Send Confirmation Email" (WF07) triggers ✅
```

### 4. Verify Reminder Created
```bash
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT * FROM appointment_reminders ORDER BY created_at DESC LIMIT 1;"

# Expected:
# id | appointment_id | reminder_type | reminder_time | status
# ---+----------------+---------------+---------------+--------
# ... | valid-uuid     | email         | 2026-04-28... | pending
```

---

## 🔄 Deployment Procedure

### Step 1: Create appointment_reminders Table

```bash
# Execute migration SQL
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev <<'EOF'
-- Create appointment_reminders table
CREATE TABLE IF NOT EXISTS appointment_reminders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    appointment_id UUID NOT NULL REFERENCES appointments(id) ON DELETE CASCADE,
    reminder_type VARCHAR(50) NOT NULL,
    reminder_time TIMESTAMP NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    sent_at TIMESTAMP,
    error_message TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT unique_appointment_reminder UNIQUE (appointment_id, reminder_type, reminder_time)
);

CREATE INDEX idx_appointment_reminders_status ON appointment_reminders(status) WHERE status = 'pending';
CREATE INDEX idx_appointment_reminders_time ON appointment_reminders(reminder_time) WHERE status = 'pending';

COMMENT ON TABLE appointment_reminders IS 'Stores appointment reminder notifications (email, SMS, etc.)';
EOF

# Verify table created
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "\d appointment_reminders"
```

### Step 2: Re-authenticate Google Calendar OAuth

1. Open n8n: http://localhost:5678/credentials
2. Find "Google Calendar API" credential (or create new if missing)
3. Delete existing credential if expired
4. Create new "Google Calendar OAuth2 API" credential
5. Configure with Client ID and Secret from Google Cloud Console
6. Click "Connect my account" and authenticate
7. Verify "Connected" status

### Step 3: Verify Google Cloud Console Settings

1. Enable Google Calendar API: https://console.cloud.google.com/apis/library
2. Check OAuth consent screen: https://console.cloud.google.com/apis/credentials/consent
3. Verify OAuth 2.0 Client ID: https://console.cloud.google.com/apis/credentials
4. Ensure redirect URI: `http://localhost:5678/rest/oauth2-credential/callback`

### Step 4: Test WF05 Complete Flow

```bash
# Get a valid appointment_id from database
APPOINTMENT_ID=$(docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -t \
  -c "SELECT id FROM appointments WHERE status = 'agendado' ORDER BY created_at DESC LIMIT 1;")

# Trigger WF05 manually
# Via n8n UI: http://localhost:5678/workflow/42eG7UpfmZ2PoBlY
# Click "Execute Workflow" with test data: {"appointment_id": "$APPOINTMENT_ID"}

# Expected: Complete flow success with:
# - Google Calendar event created ✅
# - Appointment status updated to 'confirmado' ✅
# - Reminder record created ✅
# - Email sent via WF07 ✅
```

### Step 5: Monitor Logs

```bash
# Monitor n8n logs
docker logs -f e2bot-n8n-dev 2>&1 | grep -E "WF05|Google Calendar|appointment_reminders"

# Monitor PostgreSQL logs
docker logs -f e2bot-postgres-dev 2>&1 | grep -E "appointment_reminders"
```

---

## 🔄 Rollback Procedure

If V8 causes unexpected issues:

### Rollback Step 1: Remove appointment_reminders Table (if needed)

```bash
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "DROP TABLE IF EXISTS appointment_reminders CASCADE;"
```

### Rollback Step 2: Revert to V7

1. Keep V7 workflow as-is
2. Note: WF05 will continue to fail at "Create Appointment Reminders" node
3. Option: Add `onlyIf` condition to skip reminder creation temporarily

**Note**: Rollback requires fixing OAuth separately - expired credentials won't auto-recover.

---

## 📁 Related Documentation

- **WF05 V7 Deployment**: `docs/deployment/DEPLOY_WF05_V7_HARDCODED_FINAL.md`
- **WF05 Active Workflow**: `n8n/workflows/05_appointment_scheduler_v7_hardcoded_values.json`
- **Database Setup**: `docs/Setups/SETUP_DATABASE.md` (needs update with appointment_reminders schema)
- **Google OAuth Setup**: `docs/Setups/SETUP_GOOGLE_CALENDAR.md` (to be created)

---

## 🔄 Version History

**V7**: Hardcoded business hours (08:00-18:00, Mon-Fri) - n8n $env block workaround
**V8**: + Database schema fix (appointment_reminders table) + Google OAuth re-authentication ✅ CURRENT

---

**Analysis Date**: 2026-04-28
**Execution**: 10081 (http://localhost:5678/workflow/42eG7UpfmZ2PoBlY/executions/10081)
**Status**: 🔴 REQUIRES ACTION - Two critical fixes needed
**Recommended Action**:
1. Create appointment_reminders table (5 minutes)
2. Re-authenticate Google Calendar OAuth (10 minutes)
**Estimated Time**: 15 minutes total deployment + 10 minutes testing
**Risk Level**: LOW (Schema addition + OAuth re-auth are safe operations)

**Critical Insight**: V7 workflow logic is CORRECT - both failures are infrastructure issues (missing database table + expired OAuth). Once fixed, WF05 will complete successfully and integrate with WF07 for email confirmations.
