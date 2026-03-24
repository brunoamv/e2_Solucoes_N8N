# E2 Bot - Documentation Index

> **Last Updated**: 2026-03-24 | **Project**: E2 Soluções WhatsApp Bot

---

## 📖 Quick Start

| Document | Purpose | Audience |
|----------|---------|----------|
| [CLAUDE.md](../CLAUDE.md) | Main project context for Claude Code | Developers |
| [PROJECT_STATUS.md](PROJECT_STATUS.md) | Current system status and versions | All |
| [README.md](../README.md) | Project overview and setup | New developers |

---

## 🚀 V74 Deployment (Current Priority)

### Implementation
| Document | Purpose |
|----------|---------|
| [PLAN_V74_APPOINTMENT_CONFIRMATION_MESSAGE.md](PLAN_V74_APPOINTMENT_CONFIRMATION_MESSAGE.md) | Technical plan and design |

### Testing & Deployment
| Document | Purpose |
|----------|---------|
| [TEST_V74_END_TO_END.md](TEST_V74_END_TO_END.md) | 4 comprehensive test cases |
| [DEPLOY_V74_PRODUCTION.md](DEPLOY_V74_PRODUCTION.md) | Complete deployment procedure |

---

## 📚 Version Documentation

### V74 (Ready for Deploy)
- [PLAN_V74_APPOINTMENT_CONFIRMATION_MESSAGE.md](PLAN_V74_APPOINTMENT_CONFIRMATION_MESSAGE.md) - Technical design
- [TEST_V74_END_TO_END.md](TEST_V74_END_TO_END.md) - Testing guide
- [DEPLOY_V74_PRODUCTION.md](DEPLOY_V74_PRODUCTION.md) - Deployment guide

### V73 (Appointment Scheduler Integration)
- [PLAN_V73_GOOGLE_CALENDAR_UX.md](PLAN_V73_GOOGLE_CALENDAR_UX.md) - Calendar UX plan
- [PLAN_APPOINTMENT_SCHEDULER_V3_COMPLETE_FIX.md](PLAN_APPOINTMENT_SCHEDULER_V3_COMPLETE_FIX.md) - V3 complete fix

### V72 (State Machine Improvements)
- [V72_COMPLETE_ALL_FIXES_SUMMARY.md](V72_COMPLETE_ALL_FIXES_SUMMARY.md) - All fixes summary
- [V72_COMPLETE_BUG_FIX_SUCCESS.md](V72_COMPLETE_BUG_FIX_SUCCESS.md) - Bug fix success
- [V72_APPOINTMENT_FLOW_FIX.md](V72_APPOINTMENT_FLOW_FIX.md) - Appointment flow fix
- [V72_IF_NODE_DATA_LOSS_FIX.md](V72_IF_NODE_DATA_LOSS_FIX.md) - IF node data loss fix
- [BUG_V72_SKIPPED_STATE8.md](BUG_V72_SKIPPED_STATE8.md) - State 8 skip bug

### V71 (Appointment Features)
- [V71_APPOINTMENT_FIX_COMPLETE.md](V71_APPOINTMENT_FIX_COMPLETE.md) - Complete fix
- [V71_RENAMING_SUMMARY.md](V71_RENAMING_SUMMARY.md) - Renaming summary

### V70-V69 (Bug Fixes)
- [ANALYSIS_V70_PROBLEMS.md](ANALYSIS_V70_PROBLEMS.md) - V70 analysis
- [V69_2_NEXT_STAGE_BUG_FIX.md](../V69_2_NEXT_STAGE_BUG_FIX.md) - V69.2 bug fix
- [V69_1_CONNECTION_BUG_FIX.md](../V69_1_CONNECTION_BUG_FIX.md) - V69.1 connection fix

### Earlier Versions
- [PLAN_V3.1_APPOINTMENT_FIX_MAINTAIN_V69.2.md](PLAN_V3.1_APPOINTMENT_FIX_MAINTAIN_V69.2.md)
- [PLAN_APPOINTMENT_SCHEDULER_REFACTOR_V2_1.md](PLAN_APPOINTMENT_SCHEDULER_REFACTOR_V2_1.md)
- [PLAN_APPOINTMENT_SCHEDULER_REFACTOR.md](PLAN_APPOINTMENT_SCHEDULER_REFACTOR.md)
- [PLAN_SUMMARY.md](PLAN_SUMMARY.md)

---

## 🔧 Setup & Configuration

### Initial Setup
| Document | Purpose |
|----------|---------|
| [Setups/SETUP_GOOGLE_CALENDAR_V2.md](Setups/SETUP_GOOGLE_CALENDAR_V2.md) | Google Calendar OAuth setup |

---

## 📊 System Architecture

### Workflows
1. **WF01**: Main WhatsApp Handler V2.8.3
   - File: `01_main_whatsapp_handler_V2.8.3_NO_LOOP.json`
   - Function: Duplicate detection + routing

2. **WF02**: AI Agent Conversation V74
   - File: `02_ai_agent_conversation_V74_APPOINTMENT_CONFIRMATION.json`
   - Function: 8-state conversation flow with scheduling verification
   - Production: V69.2 (stable, can rollback)

3. **WF05**: Appointment Scheduler V3.6
   - File: `05_appointment_scheduler_v3.6.json`
   - ID: `f6eIJIqfaSs6BSpJ`
   - Function: Google Calendar + Database appointments

### Database Schema
```
conversations: phone_number, lead_name, service_type, current_state, next_stage, collected_data
appointments: lead_name, lead_email, service_type, scheduled_date, google_calendar_event_id
appointment_reminders: appointment_id, reminder_type, reminder_time, status
```

---

## 🎯 Development Workflow

### 1. Planning Phase
- Review [PROJECT_STATUS.md](PROJECT_STATUS.md) for current state
- Check [CLAUDE.md](../CLAUDE.md) for context
- Read relevant version documentation

### 2. Implementation Phase
- Follow technical plans (PLAN_*.md)
- Use scripts in `/scripts` directory
- Test locally before deployment

### 3. Testing Phase
- Follow test guides (TEST_*.md)
- Verify all test cases pass
- Check database and Google Calendar integration

### 4. Deployment Phase
- Follow deployment guides (DEPLOY_*.md)
- Monitor system health
- Keep rollback plan ready

---

## 📝 Document Categories

### Planning Documents (PLAN_*.md)
Technical designs and implementation strategies for new features and versions.

### Test Documents (TEST_*.md)
Comprehensive testing guides with test cases and validation checklists.

### Deployment Documents (DEPLOY_*.md)
Step-by-step deployment procedures with monitoring and rollback plans.

### Analysis Documents (ANALYSIS_*.md, BUG_*.md)
Root cause analysis and bug investigation reports.

### Version Documents (V*.md)
Version-specific documentation for fixes, features, and changes.

### Setup Documents (Setups/SETUP_*.md)
Initial setup and configuration guides for system components.

---

## 🔍 Finding Information

### By Topic
- **Google Calendar**: Search for "calendar", "appointment", "schedule"
- **State Machine**: Search for "state", "flow", "conversation"
- **Bug Fixes**: Look in V*.md files and BUG_*.md files
- **Deployment**: Check DEPLOY_*.md and PROJECT_STATUS.md
- **Testing**: Review TEST_*.md files

### By Version
- Latest version documentation in PROJECT_STATUS.md
- Version-specific docs: V[number]_*.md
- Plan documents: PLAN_V[number]_*.md

### By Workflow
- **WF01**: Main handler, duplicate detection
- **WF02**: AI conversation agent, state machine
- **WF05**: Appointment scheduler, Google Calendar

---

## 🚨 Important Notes

### Critical IDs
- **WF05 Workflow ID**: `f6eIJIqfaSs6BSpJ` (MUST use this ID)
- **Evolution API Key**: Check `.env` file
- **Database**: e2bot_dev on PostgreSQL

### Common Commands
See [CLAUDE.md](../CLAUDE.md) section "Quick Commands" for database checks, API status, and logs.

### Rollback Strategy
Always maintain stable previous version for rollback:
- V74 (ready) → can rollback to V69.2 (production)
- Document rollback procedures in DEPLOY_*.md

---

**Maintained by**: Claude Code | **Project**: E2 Soluções WhatsApp Bot
