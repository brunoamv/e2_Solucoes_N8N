# E2 Bot Documentation Index

> **Complete documentation catalog** | Updated: 2026-04-08

---

## 📖 Core Documentation

### Project Overview
- **README.md** - Quick start guide, architecture, configuration
- **CLAUDE.md** - Technical context for Claude Code (ultra-compact)

---

## 🚀 Deployment Guides

### WF02 (AI Agent)
- **WF02_V76_IMPLEMENTATION_GUIDE.md** - Proactive UX implementation (READY ✅)
  - Location: `/docs/implementation/`
  - Status: Ready for Production
  - Changes: Proactive date/time selection (12 states)

- **WF02_V76_DEPLOYMENT_SUMMARY.md** - V76 deployment checklist
  - Location: `/docs/implementation/`
  - Strategy: Canary deployment (20% → 100%)

### WF05 (Appointment Scheduler)
- **DEPLOY_WF05_V7_HARDCODED_FINAL.md** - Hardcoded business hours (DEFINITIVE ✅)
  - Location: `/docs/deployment/`
  - Status: Ready for Production
  - Changes: Zero `$env` dependency, pure JavaScript constants

### WF06 (Calendar Availability Service)
- **WF06_CALENDAR_AVAILABILITY_SERVICE.md** - Availability microservice (READY ✅)
  - Location: `/docs/implementation/`
  - Status: Ready for Production
  - Function: Provides available dates/slots for WF02 V76

### WF07 (Email Sender)
- **BUGFIX_WF07_V13_INSERT_SELECT_FIX.md** - INSERT...SELECT pattern (DEFINITIVE ✅)
  - Location: `/docs/fix/`
  - Status: Ready for Production
  - Changes: INSERT...SELECT pattern, zero queryReplacement dependency

- **PLAN_NGINX_WF07_IMPLEMENTATION.md** - nginx + HTTP Request architecture
  - Location: `/docs/PLAN/`
  - Status: Implemented in V9+

---

## 🐛 Bugfix Documentation

### WF07 Evolution (V2 → V13)

**Early Versions (Template Access Issues)**:
- **BUGFIX_WF07_V8_MIME_TYPE_FIX.md** - Read/Write File failures
- **BUGFIX_WF07_V8_N8N_VERSION_COMPATIBILITY.md** - n8n 2.14.2 limitations
- **BUGFIX_WF07_V8_READ_TEMPLATE_BINARY_FIX.md** - Binary encoding attempts
- **DEPLOY_WF07_V6.1_COMPLETE_FIX.md** - Docker volume mount approach
- **DEPLOY_WF07_V8.1_READ_IN_CODE.md** - fs.readFileSync blocked
- **DEPLOY_WF07_V8_NO_FS_MODULE_FINAL.md** - Node.js module restrictions

**HTTP Request Solution (V9)**:
- **SOLUTION_FINAL_HTTP_REQUEST.md** - Definitive nginx + HTTP Request solution
- **SOLUTION_WF07_FINAL_BINARY_TO_STRING.md** - V8/V8.1 failed attempts analysis

**Format Detection Issues (V9.1 - V9.3)**:
- **BUGFIX_WF07_V9.1_ARRAY_TO_STRING.md** - Execution 17999 (3-case detection)
- **BUGFIX_WF07_V9.2_ROBUST_FORMAT_DETECTION.md** - Execution 18072 (8-case detection)
- **BUGFIX_WF07_V9.3_SAFE_PROPERTY_CHECK.md** - Execution 18273 (safe property check)

**Credential & Service Name (V10 - V11)**:
- **BUGFIX_WF07_V10_STARTTLS.md** - Manual credential reference fix
- **BUGFIX_WF07_V11_SERVICE_NAME_FIX.md** - Execution 18757 (service_name mapping + email_logs)

**Address & Database (V12 - V13)**:
- **BUGFIX_WF07_V12_ADDRESS_AND_DB_FIX.md** - Execution 18818 (address format + queryReplacement)
- **BUGFIX_WF07_V13_INSERT_SELECT_FIX.md** - Execution 18936 (INSERT...SELECT pattern) ✅ DEFINITIVE

### WF05 Evolution (Environment Variable Access)
- **BUGFIX_WF05_V4.0.4_EMAIL_DATA_PASSING.md** - $env access denied
- **FIX_WF05_ENV_VAR_ACCESS.md** - process.env undefined
- **DEPLOY_WF05_V5_PROCESS_ENV_FIX.md** - V5 attempt analysis
- **DEPLOY_WF05_V6_EXPRESSION_ENV_FIX.md** - Set node $env blocked
- **SUMMARY_ENV_FIX_COMPLETE.md** - Initial env var analysis

---

## 📊 Analysis & Planning

### n8n Platform Analysis
- **ANALYSIS_N8N_VERSION_UPGRADE_VS_WORKAROUNDS.md** - Version 2.14.2 limitations + 3 solution approaches
- **ANALYSIS_GMAIL_SMTP_N8N_2.14.2_COMPATIBILITY.md** - SMTP configuration analysis

### WF07 Analysis (Deep Dives)
- **ANALYSIS_WF07_V9.2_COMPLETE.md** - Complete V9.2 analysis
- **NEXT_STEPS_WF07_V9.md** - Post-V9 roadmap

### Planning Documents
- **PLAN_WF05_V5_ENV_VAR_FIX.md** - Environment variable access strategy
- **PLAN_WF07_V6.1_COMPLETE_FIX.md** - Template access planning
- **PLAN_V6_DOCKER_TEMPLATE_ACCESS.md** - Docker volume mount strategy

---

## 🔧 Quick Reference Summaries

### WF05 Summaries
- **QUICK_START_WF05_V6.md** - V6 quick start guide
- **SUMMARY_WF05_V6_DEFINITIVE_SOLUTION.md** - V6 solution summary
- **SUMMARY_WF07_V6.1_COMPLETE.md** - V6.1 complete summary

### WF07 Summaries
- **SUMMARY_WF07_FINAL_BINARY_TO_STRING.md** - Binary encoding summary

---

## ⚙️ Setup Guides

### Integration Setups (docs/Setups/)
- **QUICKSTART.md** - Complete setup guide (30-45 min) ✅
  - Location: `/docs/Setups/QUICKSTART.md`
  - Docker setup, Evolution API, n8n configuration
  - Port 465 SSL/TLS SMTP (verified working)
  - Database setup and workflow import

- **SETUP_EMAIL.md** - SMTP configuration guide (V3.0 DEFINITIVA)
  - Gmail App Password + SMTP dedicado
  - Port 465 SSL/TLS configuration (RECOMENDADO)
  - n8n credential setup
  - Troubleshooting SSL/TLS errors

- **SETUP_GOOGLE_CALENDAR.md** - Google Calendar OAuth2 setup
  - OAuth2 credential configuration
  - Calendar API integration

- **SETUP_CREDENTIALS.md** - All n8n credentials configuration
  - PostgreSQL, SMTP, Google Calendar
  - Evolution API credentials

---

## 🎯 Workflow Generators

### Active Generators (scripts/)
- **generate-workflow-v75-appointment-confirmation.py** - WF02 V75
- **generate-workflow-wf05-v7-hardcoded-values.py** - WF05 V7 ✅
- **generate-workflow-wf07-v13-insert-select.py** - WF07 V13 ✅

### Historical Generators (Reference Only)
**WF05**: v5 (process.env), v6 (Set expression), v7 (FINAL)
**WF07**: v6.1, v8, v8.1, v9, v9.1, v9.2, v9.3, v10, v11, v12, v13 (FINAL)

---

## 📋 Documentation Categories

### By Status
**✅ READY FOR PRODUCTION**:
- WF02 V76: Proactive UX with zero-error appointment scheduling
- WF05 V7: Hardcoded business hours validation
- WF06 V1: Calendar availability microservice
- WF07 V13: INSERT...SELECT database pattern

**✅ PRODUCTION STABLE**:
- WF01 V2.8.3: WhatsApp deduplication
- WF02 V74.1.2: AI conversation (reactive)
- WF05 V3.6: Calendar integration (no validation)

**📚 ARCHIVED** (in `/n8n/workflows/old/`):
- 57 obsolete workflow versions (V68-V75, V2-V12)
- Historical reference only

### By Topic
**Email Workflows**: V6-V13 docs, SMTP setup, template integration
**Environment Variables**: V4-V7 docs, n8n limitations, hardcoded solution
**Database Operations**: V12-V13 docs, INSERT...SELECT pattern
**Testing**: V9 testing guide, integration procedures

---

## 🔍 Quick Navigation

### Find Documentation By Error
| Error Type | Documentation |
|------------|---------------|
| Template access denied | SOLUTION_FINAL_HTTP_REQUEST.md |
| $env access denied | DEPLOY_WF05_V7_HARDCODED_FINAL.md |
| queryReplacement [undefined] | BUGFIX_WF07_V13_INSERT_SELECT_FIX.md |
| Module 'fs' is disallowed | ANALYSIS_N8N_VERSION_UPGRADE_VS_WORKAROUNDS.md |
| there is no parameter $N | BUGFIX_WF07_V13_INSERT_SELECT_FIX.md |

### Find Documentation By Workflow
| Workflow | Latest Docs | Status |
|----------|-------------|--------|
| WF01 | README.md + n8n/workflows/README.md | Stable (V2.8.3) ✅ |
| WF02 | WF02_V76_IMPLEMENTATION_GUIDE.md | Ready (V76) ✅ |
| WF05 | DEPLOY_WF05_V7_HARDCODED_FINAL.md | Ready (V7) ✅ |
| WF06 | WF06_CALENDAR_AVAILABILITY_SERVICE.md | Ready (V1) ✅ |
| WF07 | BUGFIX_WF07_V13_INSERT_SELECT_FIX.md | Ready (V13) ✅ |

---

## 📝 Documentation Standards

### Naming Convention
```
CATEGORY_SUBJECT_VERSION_DESCRIPTION.md

Categories:
- BUGFIX: Error resolution documentation
- DEPLOY: Deployment procedures
- ANALYSIS: Deep technical analysis
- PLAN: Implementation planning
- SUMMARY: Quick reference summaries
- SETUP: Integration guides

Examples:
- BUGFIX_WF07_V13_INSERT_SELECT_FIX.md
- DEPLOY_V75_PRODUCTION.md
- ANALYSIS_N8N_VERSION_UPGRADE_VS_WORKAROUNDS.md
```

### Document Sections (Standard)
1. **Overview**: Version, date, status, previous failure
2. **Problem Analysis**: Root cause, error details
3. **Solution**: Architecture, implementation, key changes
4. **Implementation**: Code details, node configuration
5. **Testing**: Phase-by-phase procedures
6. **Success Criteria**: Validation checklist
7. **Lessons Learned**: Takeaways for future work

---

## 🎓 Learning Resources

### n8n Limitations
- Read **ANALYSIS_N8N_VERSION_UPGRADE_VS_WORKAROUNDS.md** for complete platform limitations
- Understand why filesystem, environment variables, and modules are restricted

### Best Practices
- **Template Access**: Use nginx + HTTP Request (not filesystem)
- **Environment Variables**: Hardcode in Code nodes (not $env)
- **Database Parameters**: Use INSERT...SELECT (not queryReplacement)
- **Error Handling**: Safe property checks before operations

---

**Last Updated**: 2026-04-08
**Documentation Structure**: Reorganized with `/docs/implementation/`, `/docs/fix/`, `/docs/deployment/`, `/docs/Setups/`
**Workflows**: 7 active in `/n8n/workflows/`, 57 archived in `/n8n/workflows/old/`
**Setup Guide**: `/docs/Setups/QUICKSTART.md` (Port 465 SSL/TLS verified working)
**Critical Paths**: WF02 V76, WF05 V7, WF06 V1, WF07 V13 (all READY FOR PRODUCTION ✅)
