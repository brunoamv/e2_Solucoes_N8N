# E2 Soluções - Workflow Organization

**Last Updated**: 2026-04-29
**Status**: ✅ Organized and Production V1 Ready

## Directory Structure

```
n8n/workflows/
├── production/          # Production-ready workflows (SINGLE SOURCE OF TRUTH)
│   ├── wf01/           # WhatsApp Handler
│   ├── wf02/           # AI Agent Conversation
│   ├── wf05/           # Appointment Scheduler
│   ├── wf06/           # Calendar Availability Service
│   └── wf07/           # Send Email
├── development/        # Development and testing versions
│   ├── wf02/          # WF02 development iterations
│   ├── wf05/          # WF05 experimental versions
│   └── wf06/          # WF06 development versions
└── historical/         # Historical versions for reference
    └── wf02/          # WF02 V77-V114 development history
```

**IMPORTANT**: No workflow JSON files exist in the root directory. All workflows are organized in their appropriate subfolders.

---

## Production V1 Workflows

**Deployment Package**: 4 workflows ready for production deployment

| Workflow | Version | File Location | Workflow ID | n8n URL |
|----------|---------|---------------|-------------|---------|
| **WF01** | V2.8.3 | `production/wf01/01_main_whatsapp_handler_V2.8.3_NO_LOOP.json` | DCUYzu4nxjvmIVRw | http://localhost:5678/workflow/DCUYzu4nxjvmIVRw |
| **WF02** | V114 | `production/wf02/02_ai_agent_conversation_V114_FUNCIONANDO.json` | 9tG2gR6KBt6nYyHT | http://localhost:5678/workflow/9tG2gR6KBt6nYyHT |
| **WF05** | V7 Hardcoded | `production/wf05/05_appointment_scheduler_v7_hardcoded_values.json` | 42eG7UpfmZ2PoBlY | http://localhost:5678/workflow/42eG7UpfmZ2PoBlY |
| **WF06** | V2.2 | `production/wf06/06_calendar_availability_service_v2_2.json` | - | - |
| **WF07** | V13 | `production/wf07/07_send_email_v13_insert_select.json` | 0PuyG3BvR2Hpfpix | http://localhost:5678/workflow/0PuyG3BvR2Hpfpix |

---

## Integration Flow

```
User Message (WhatsApp)
    ↓
WF01: WhatsApp Handler V2.8.3
    → Deduplica mensagens
    → Valida webhook Evolution API
    ↓
WF02: AI Agent Conversation V114 ⭐ PRODUCTION
    → Claude 3.5 Sonnet integration
    → State machine com PostgreSQL
    → Row locking (FOR UPDATE SKIP LOCKED)
    → WF06 suggestions persistence
    → PostgreSQL TIME fields extraction
    ↓
WF06: Calendar Availability Service V2.2
    → Google Calendar OAuth integration
    → Empty calendar handling
    → Retorna datas e horários disponíveis
    ↓
WF05: Appointment Scheduler V7
    → Hardcoded values para validação
    → Agendamento de consultas
    ↓
WF07: Send Email V13
    → INSERT...SELECT pattern
    → Email confirmation
    → Appointment reminders
```

---

## WF02 V114 - Production Complete

**Workflow ID**: 9tG2gR6KBt6nYyHT
**Node Count**: 52 nodes
**Status**: ✅ PRODUCTION READY WITH ALL CRITICAL FIXES

### Complete Fix Package
WF02 V114 includes ALL critical fixes deployed to production:

1. **V111: Database Row Locking** (FOR UPDATE SKIP LOCKED)
   - Prevents race conditions in concurrent executions
   - Eliminates stale state processing

2. **V113.1: WF06 Suggestions Persistence**
   - Saves `date_suggestions` from WF06 next_dates
   - Saves `slot_suggestions` from WF06 available_slots

3. **V114: PostgreSQL TIME Fields** (scheduled_time_start + scheduled_time_end)
   - Extracts TIME fields from WF06 slot structure
   - Database-compatible TIME format ("08:00", "10:00")

4. **V79.1: Schema-Aligned Build Update Queries**
   - No `contact_phone` references
   - Fully compliant with database schema

5. **V105: Routing Fix**
   - Update Conversation State BEFORE Check If WF06
   - Prevents infinite loop scenarios

### Production Scripts
- State Machine: `scripts/wf02-v114-slot-time-fields-fix.js` (1054 lines)
- SQL Queries: `scripts/wf02-v111-build-sql-queries-row-locking.js`
- WF06 Dates: `scripts/wf02-v113-build-update-queries1-wf06-next-dates.js`
- WF06 Slots: `scripts/wf02-v113-build-update-queries2-wf06-available-slots.js`

### Complete Integration Test
```bash
# Test complete flow: "oi" → agendamento → confirmação
# 1. Send "oi" → Complete user info → Service selection
# 2. Select "1" (agendar) → WF06 next_dates → Show 3 dates
# 3. Select date "1" → WF06 available_slots → Show time slots
# 4. Select slot "1" → Appointment created → Email sent

# Expected: Full flow completes without errors
# Database: All fields saved correctly (TIME fields included)
```

---

## File Organization Principles

### 🎯 Single Source of Truth
- **Production workflows** exist ONLY in `production/wfXX/` subfolders
- **No duplicate files** anywhere in the repository
- Each workflow version has ONE authoritative location

### 📁 Categorization Rules

**production/**:
- Currently deployed or deployment-ready workflows
- Fully tested and validated
- Production V1 package workflows

**development/**:
- Active development versions
- Testing and experimental iterations
- Not yet production-ready

**historical/**:
- Complete development history (WF02 V77-V114)
- Reference for rollback scenarios
- Preserves evolution of workflows

---

## Version Management

### WF01 - WhatsApp Handler
- **Production**: V2.8.3 (No Loop Fix)
- **Location**: `production/wf01/`
- **Status**: ✅ Production Ready

### WF02 - AI Agent Conversation
- **Production**: V114 (Complete Fix) ⭐
- **Historical**: V77-V113 in `historical/wf02/`
- **Status**: ✅ Production Ready with ALL critical fixes

### WF05 - Appointment Scheduler
- **Production**: V7 Hardcoded Values
- **Development**: V3.6, V8 Part 1, V8 Part 2
- **Status**: ✅ Production Ready

### WF06 - Calendar Availability Service
- **Production**: V2.2 (Response Mode)
- **Development**: V2, V2.1 iterations
- **Status**: ✅ Production Ready

### WF07 - Send Email
- **Production**: V13 (INSERT...SELECT Pattern)
- **Location**: `production/wf07/`
- **Status**: ✅ Production Ready

---

## Deployment Workflow

### Production V1 Deployment
1. **Review workflows** in `production/` subfolders
2. **Validate workflow IDs** match n8n deployment
3. **Import workflows** via n8n UI:
   - Import from file → Select JSON from `production/wfXX/`
   - Verify workflow ID matches table above
4. **Configure credentials**:
   - Evolution API: WhatsApp webhook
   - Claude API: AI agent integration
   - PostgreSQL: Database connection
   - Google OAuth: Calendar access
   - SMTP: Email sending
5. **Test integration flow** end-to-end
6. **Monitor production** via n8n logs and database

### Development Workflow
1. **Create development version** in `development/wfXX/`
2. **Test thoroughly** in development environment
3. **Validate integration** with dependent workflows
4. **Move to production/** when stable
5. **Archive previous version** to `historical/` if needed

---

## Documentation References

- **Production V1 Deployment**: `../../docs/status/PRODUCTION_V1_DEPLOYMENT.md`
- **Deployment Status**: `../../docs/status/DEPLOYMENT_STATUS.md`
- **WF02 V114 Production**: `../../docs/WF02_V114_PRODUCTION_DEPLOYMENT.md`
- **Deployment Guides**: `../../docs/deployment/`
- **Quick Deploy Guides**: `../../docs/deployment/quick/`
- **Analysis Documents**: `../../docs/analysis/`
- **Bugfix Reports**: `../../docs/fix/`

---

## Maintenance

- **Regular cleanup**: Archive old development versions
- **Documentation updates**: Keep README current
- **Version tracking**: Maintain clear version numbers
- **Integration testing**: Validate dependencies after updates

---

**Project**: E2 Soluções WhatsApp Bot
**Stack**: n8n 2.14.2 + Claude 3.5 + PostgreSQL + Evolution API v2.3.7
**Maintained by**: E2 Dev Team
**Last Organization**: 2026-04-29 - Single source of truth structure implemented
