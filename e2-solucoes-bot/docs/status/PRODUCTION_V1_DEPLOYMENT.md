# E2 Bot - Production V1 Deployment

**Date**: 2026-04-29
**Status**: ✅ READY FOR PRODUCTION V1
**Environment**: n8n 2.14.2 + Claude 3.5 + PostgreSQL + Evolution API v2.3.7

---

## 🎯 Executive Summary

Production V1 consists of **5 validated workflows** ready for deployment:

| Workflow | Version | URL | Location | Status |
|----------|---------|-----|----------|--------|
| **WF01** | V2.8.3 | http://localhost:5678/workflow/DCUYzu4nxjvmIVRw | `production/wf01/` | ✅ WhatsApp Handler with Dedup |
| **WF02** | V114 | http://localhost:5678/workflow/9tG2gR6KBt6nYyHT | `production/wf02/` | ✅ AI Agent Conversation COMPLETE |
| **WF05** | V7 Hardcoded | http://localhost:5678/workflow/42eG7UpfmZ2PoBlY | `production/wf05/` | ✅ Appointment Scheduler |
| **WF06** | V2.2 | - | `production/wf06/` | ✅ Calendar Microservice |
| **WF07** | V13 | http://localhost:5678/workflow/0PuyG3BvR2Hpfpix | `production/wf07/` | ✅ Email Service |

**Critical Achievement**: All workflows tested and working in development environment. ✅ **ORGANIZED** - Single source of truth structure implemented (2026-04-29). This represents the complete E2 Bot system ready for production deployment.

---

## 📋 Workflow Details

### WF01 - WhatsApp Handler V2.8.3 (No Loop Fix)

**Workflow ID**: `DCUYzu4nxjvmIVRw`
**File**: `production/wf01/01_main_whatsapp_handler_V2.8.3_NO_LOOP.json`
**Function**: Message deduplication and routing to WF02

**Key Features**:
- PostgreSQL `ON CONFLICT` deduplication
- Routes messages to WF02 AI Agent
- Prevents duplicate message processing
- Stable production version

**Validation**:
```bash
# Test message deduplication
# Send same message twice rapidly
# Expected: Only processes once ✅
```

---

### WF02 - AI Agent Conversation V114 COMPLETE

**Workflow ID**: `9tG2gR6KBt6nYyHT`
**File**: `production/wf02/02_ai_agent_conversation_V114_FUNCIONANDO.json`
**Function**: AI-powered conversation with complete WF06 calendar integration
**Node Count**: 52 nodes

**Includes ALL Critical Fixes**:
- ✅ **V111**: Database Row Locking (`FOR UPDATE SKIP LOCKED`) - Race condition fix
- ✅ **V113.1**: WF06 Suggestions Persistence (`date_suggestions` + `slot_suggestions`)
- ✅ **V114**: PostgreSQL TIME Fields (`scheduled_time_start` + `scheduled_time_end`)
- ✅ **V79.1**: Schema-Aligned Build Update Queries (no `contact_phone`)
- ✅ **V105**: Routing Fix (Update Conversation State BEFORE Check If WF06)

**Complete Integration Flow**:
```
User: "oi" → Complete conversation flow
→ User completes service + contact info
→ User: "1" (agendar consulta)
→ V111: Row locking prevents race conditions ✅
→ WF06 next_dates → V113: Saves date_suggestions ✅
→ User: "1" (selects date)
→ V111: Row locking active ✅
→ WF06 available_slots → V113: Saves slot_suggestions ✅
→ User: "1" (selects slot - e.g., 8h às 10h)
→ V114: Extracts start_time="08:00", end_time="10:00" ✅
→ V114: Saves to PostgreSQL TIME columns ✅
→ Appointment confirmed AND saved ✅
→ Triggers WF05 for calendar scheduling ✅
```

**Documentation**:
- Production Deployment: `docs/WF02_V114_PRODUCTION_DEPLOYMENT.md`
- Quick Deploy: `docs/WF02_V114_QUICK_DEPLOY.md`
- Complete Summary: `docs/WF02_V114_COMPLETE_SUMMARY.md`

**Validation**:
```bash
# Verify TIME fields saved correctly
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT phone_number,
             collected_data->'scheduled_time_start' as start,
             collected_data->'scheduled_time_end' as end
      FROM conversations WHERE phone_number = '556181755748';"
# Expected: start: "08:00", end: "10:00" ✅
```

---

### WF05 - Appointment Scheduler V7 Hardcoded Values

**Workflow ID**: `42eG7UpfmZ2PoBlY`
**File**: `production/wf05/05_appointment_scheduler_v7_hardcoded_values.json`
**Function**: Google Calendar integration and email trigger

**Key Features**:
- Creates Google Calendar events
- Updates appointment status to 'confirmado'
- Triggers WF07 for confirmation email
- Uses hardcoded values for environment variables

**Known Limitations**:
- ⚠️ Google OAuth may need re-authentication
- ⚠️ Uses hardcoded credentials (not $env)

**Post-Deployment Action Required**:
```bash
# After deployment, re-authenticate Google Calendar OAuth:
# 1. Open n8n credentials: http://localhost:5678/credentials
# 2. Find "Google Calendar API" credential
# 3. Click "Connect my account" and authenticate
# 4. Verify "Connected" status shows green
```

**Validation**:
```bash
# Test complete WF05 flow after OAuth
# Trigger WF05 manually via n8n UI with valid appointment_id
# Expected:
# - Google Calendar event created ✅
# - Appointment status = 'confirmado' ✅
# - Email sent via WF07 ✅
```

---

### WF06 - Calendar Availability Service V2.2 (Response Mode)

**Workflow ID**: N/A (Webhook-based microservice)
**File**: `production/wf06/06_calendar_availability_service_v2_2.json`
**Function**: Calendar availability microservice with Google Calendar OAuth integration

**Key Features**:
- Google Calendar OAuth integration with empty calendar handling
- Response mode for optimal data structure compatibility
- Returns available dates with slot counts
- Returns available time slots for selected dates
- Handles empty calendars gracefully without crashes

**Complete Fix Package**:
- ✅ **V2**: Google Calendar OAuth integration
- ✅ **V2.1**: Empty calendar handling + input data source fix
- ✅ **V2.2**: Response mode for better WF02 integration

**Validation**:
```bash
# Test empty calendar handling
curl -X POST http://localhost:5678/webhook/calendar-availability \
  -H "Content-Type: application/json" \
  -d '{"action": "next_dates", "count": 3, "service_type": "energia_solar", "duration_minutes": 120}'
# Expected: 3 dates with 8 slots each (no crashes!) ✅
```

---

### WF07 - Send Email V13 (INSERT...SELECT Pattern)

**Workflow ID**: `0PuyG3BvR2Hpfpix`
**File**: `production/wf07/07_send_email_v13_insert_select.json`
**Function**: Email sending service with database logging

**Key Features**:
- nginx reverse proxy → HTTP Request → SMTP
- PostgreSQL database logging with `INSERT...SELECT`
- Template-based email generation
- Automatic email tracking

**Technical Implementation**:
- Uses `INSERT...SELECT` pattern (n8n limitation workaround)
- nginx configuration for SMTP port access
- Comprehensive error handling and logging

**Validation**:
```bash
# Check email logs after sending
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT recipient_email, subject, status, sent_at
      FROM email_logs ORDER BY sent_at DESC LIMIT 5;"
# Expected: Recent email entries with status 'sent' ✅
```

---

## 🚀 Deployment Checklist

### Pre-Deployment Verification

```bash
# 1. Verify all workflows are active in n8n
# Open n8n: http://localhost:5678
# Check each workflow:
# - WF01: http://localhost:5678/workflow/DCUYzu4nxjvmIVRw ✅
# - WF02: http://localhost:5678/workflow/9tG2gR6KBt6nYyHT ✅
# - WF05: http://localhost:5678/workflow/42eG7UpfmZ2PoBlY ✅
# - WF07: http://localhost:5678/workflow/0PuyG3BvR2Hpfpix ✅

# 2. Verify database schema
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "\d conversations"
# Expected: All required columns present ✅

docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "\d appointments"
# Expected: Table with google_calendar_event_id column ✅

docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "\d email_logs"
# Expected: Table with complete email tracking schema ✅

# 3. Verify Evolution API connection
curl -s http://localhost:8080/instance/fetchInstances \
  -H "apikey: ae569043cfa169380c378347f91a1141ea572541d2d1cadbed222db519c8a891" | jq
# Expected: Instance status "open" ✅

# 4. Test complete user journey
# Send WhatsApp: "oi"
# Complete entire flow:
# - Service selection (1-5)
# - Contact information collection
# - Confirmation (1 = agendar, 2 = confirmar, 3 = editar)
# - If agendar: Date selection → Time slot selection
# Expected: Complete flow without errors ✅
```

### Deployment Steps

```bash
# 1. Export Production Workflows from n8n UI
# For each workflow:
# - Open workflow in n8n
# - Click "..." menu → Download
# - Save to production backup directory

# 2. Document Production Workflow IDs
WF01_ID="DCUYzu4nxjvmIVRw"
WF02_ID="9tG2gR6KBt6nYyHT"
WF05_ID="42eG7UpfmZ2PoBlY"
WF07_ID="0PuyG3BvR2Hpfpix"

# 3. Create Production Environment Variables
# Copy .env.example to .env.production
# Update with production credentials

# 4. Deploy to Production Server
# (Deployment method depends on hosting strategy)
# - Docker Compose deployment
# - Kubernetes deployment
# - Manual server deployment

# 5. Post-Deployment: Re-authenticate Google OAuth
# Access production n8n: https://your-production-url/credentials
# Re-authenticate Google Calendar credential
# Verify "Connected" status

# 6. Production Smoke Tests
# Test complete user journey in production
# Verify all integrations working
# Check database logs for errors
```

---

## 🔍 Post-Deployment Validation

### Complete Integration Test

```bash
# Test 1: Message Reception and Deduplication (WF01)
# Send WhatsApp message: "oi"
# Expected: Single response, no duplicates ✅

# Test 2: AI Conversation Flow (WF02)
# Complete service selection and contact info
# Expected: Smooth conversation with appropriate prompts ✅

# Test 3: Calendar Scheduling (WF02 + WF06 + WF05)
# Select option "1" (agendar consulta)
# Choose date and time slot
# Expected:
# - Date selection shows available dates ✅
# - Slot selection shows available times ✅
# - Appointment confirmed message ✅
# - Database updated with TIME fields ✅

# Test 4: Email Confirmation (WF07)
# After appointment confirmation
# Expected:
# - Confirmation email received ✅
# - Email log created in database ✅

# Test 5: Database Integrity
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT COUNT(*) FROM conversations WHERE updated_at > NOW() - INTERVAL '1 hour';"
# Expected: Test conversation count ✅

docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT COUNT(*) FROM appointments WHERE created_at > NOW() - INTERVAL '1 hour';"
# Expected: Test appointment count ✅

docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT COUNT(*) FROM email_logs WHERE sent_at > NOW() - INTERVAL '1 hour';"
# Expected: Test email log count ✅
```

---

## 📊 Monitoring and Observability

### Key Metrics to Monitor

```bash
# 1. Workflow Execution Success Rate
# Monitor n8n execution logs for errors
docker logs -f e2bot-n8n-dev 2>&1 | grep -E "ERROR|WARN"

# 2. Database Query Performance
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT query, calls, total_time, mean_time
      FROM pg_stat_statements
      ORDER BY total_time DESC LIMIT 10;"

# 3. WhatsApp Message Volume
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT DATE(created_at) as date, COUNT(*) as messages
      FROM conversations
      GROUP BY DATE(created_at)
      ORDER BY date DESC LIMIT 7;"

# 4. Appointment Scheduling Success Rate
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT status, COUNT(*) as count
      FROM appointments
      GROUP BY status;"

# 5. Email Delivery Success Rate
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT status, COUNT(*) as count
      FROM email_logs
      GROUP BY status;"
```

---

## 🚨 Known Issues and Workarounds

### Issue 1: Google OAuth Expiration (WF05)

**Symptom**: Google Calendar events not created, OAuth error in logs

**Solution**:
```bash
# Re-authenticate Google Calendar OAuth
# 1. Access n8n credentials: http://localhost:5678/credentials
# 2. Find "Google Calendar API" credential
# 3. Delete expired credential
# 4. Create new "Google Calendar OAuth2 API" credential
# 5. Configure with Client ID/Secret from Google Cloud Console
# 6. Click "Connect my account" and authenticate
# 7. Verify "Connected" status shows green
```

**Prevention**: Monitor OAuth token expiration, set up renewal reminders

---

### Issue 2: Race Condition During Rapid Messages

**Symptom**: WF06 shows dates again instead of time slots

**Solution**: Already fixed in WF02 V111 with database row locking

**Validation**:
```bash
# Test rapid message sending (< 1 second apart)
# Expected: No race condition, proper state management ✅
```

---

### Issue 3: PostgreSQL TIME Field Validation

**Symptom**: `invalid input syntax for type time` errors

**Solution**: Already fixed in WF02 V114 with proper TIME field extraction

**Validation**:
```bash
# Verify TIME fields saved correctly
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT phone_number,
             collected_data->'scheduled_time_start' as start,
             collected_data->'scheduled_time_end' as end
      FROM conversations
      WHERE collected_data ? 'scheduled_time_start'
      LIMIT 5;"
# Expected: Valid TIME values like "08:00", "10:00" ✅
```

---

## 📁 Related Documentation

**Deployment Guides**:
- WF01: Development only (stable production version)
- WF02 V114: `docs/WF02_V114_PRODUCTION_DEPLOYMENT.md` ⭐
- WF05 V7: `docs/deployment/DEPLOY_WF05_V7_HARDCODED_FINAL.md`
- WF07 V13: `docs/fix/BUGFIX_WF07_V13_INSERT_SELECT_FIX.md`

**Quick References**:
- WF02 Quick Deploy: `docs/WF02_V114_QUICK_DEPLOY.md`
- Deployment Status: `docs/DEPLOYMENT_STATUS.md`

**Bug Reports and Fixes**:
- WF02 V111: `docs/fix/BUGFIX_WF02_V111_DATABASE_STATE_RACE_CONDITION.md`
- WF02 V113: `docs/fix/BUGFIX_WF02_V113_1_DATE_SUGGESTIONS_PERSISTENCE.md`
- WF05 OAuth: `docs/fix/BUGFIX_WF05_V8_APPOINTMENT_REMINDERS_GOOGLE_OAUTH.md`

**Setup Guides**:
- Quickstart: `docs/Setups/QUICKSTART.md` (30-45 min)
- Email Setup: `docs/Setups/SETUP_EMAIL.md`
- Credentials: `docs/Setups/SETUP_CREDENTIALS.md`

---

## 🎯 Success Criteria

Production V1 deployment is successful when:

- ✅ All 5 workflows active and responding (WF01, WF02, WF05, WF06, WF07)
- ✅ WhatsApp messages processed without duplicates
- ✅ AI conversation flows complete without errors
- ✅ Calendar appointments created successfully
- ✅ Confirmation emails delivered
- ✅ Database logs show successful operations
- ✅ No critical errors in n8n execution logs
- ✅ User journey completes end-to-end

---

## 🔄 Rollback Plan

If critical issues arise in production:

```bash
# 1. Deactivate problematic workflow in n8n UI
# Click workflow → Toggle "Active" to OFF

# 2. If needed, restore from backup
# Import previous working version from backup directory

# 3. Investigate issue in development environment
# Use copied production data for debugging

# 4. Fix and re-deploy when validated
```

---

## 📞 Support and Escalation

**Critical Issues**:
- Database connection failures
- Evolution API disconnection
- Complete workflow failure

**Important Issues**:
- Google OAuth expiration
- Email delivery problems
- Partial workflow failures

**Minor Issues**:
- Individual message processing errors
- Temporary service delays

---

**Project**: E2 Soluções WhatsApp Bot
**Version**: Production V1
**Deployment Date**: 2026-04-29
**Maintained**: Claude Code
**Status**: ✅ READY FOR PRODUCTION DEPLOYMENT
