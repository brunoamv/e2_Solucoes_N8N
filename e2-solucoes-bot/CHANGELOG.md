# Changelog - E2 Bot

> **Format**: Semantic versioning for workflows | **Latest**: 2026-03-31

---

## [Unreleased - Ready for Deploy] 🚀

### WF02 V75 - Personalized Appointment Messages
**Date**: 2026-03-30
**Status**: ✅ Ready for Production

**Added**:
- Personalized appointment confirmation with real data
- Dynamic message builder with 9 template variables
- Service name formatting (energia_solar → Energia Solar)
- Date/time formatting (DD/MM/YYYY, HH:MM às HH:MM)
- Google Calendar link placeholder

**Changed**:
- Template `scheduling_redirect`: Generic → Personalized with {{variables}}
- Final message: "vamos agendar" → "Agendamento Confirmado com Sucesso!"

**Files**:
- `02_ai_agent_conversation_V75_APPOINTMENT_FINAL_MESSAGE.json`
- Base: V74.1.2 (stable, can rollback)

**Docs**: `docs/DEPLOY_V75_PRODUCTION.md`

---

### WF05 V4.0.4 - Email Data Fix
**Date**: 2026-03-30
**Status**: ✅ Ready for Production

**Fixed**:
- Email data passing: 4 fields → 16 fields to WF07
- "Email recipient not found" error (WF07 V3 integration)
- Data forwarding from "Get Appointment & Lead Data"

**Added**:
- "Prepare Email Trigger Data" node (merges appointment data)
- Complete 16-field object for WF07 integration

**Changed**:
- Node count: 37 → 38 nodes
- Connection flow: RD Station → Prepare Email Data → Send Email

**Maintains**:
- ✅ Timezone fix (-03:00 Brazil)
- ✅ Title fix ("E2 Soluções - Agenda")
- ✅ Attendees fix (string array format)
- ✅ Summary node fix (additionalFields)

**Files**: `05_appointment_scheduler_v4.0.4.json`
**Docs**: `docs/BUGFIX_WF05_V4.0.4_EMAIL_DATA_PASSING.md`

---

### WF07 V6 - Docker Volume Fix (Complete Solution)
**Date**: 2026-03-30
**Status**: ✅ Ready for Production

**Fixed** (All 9 bugs from V2.0 → V6):
1. ✅ Template file mapping [V3]
2. ✅ Email metadata (subject, sender, reply_to) [V3]
3. ✅ Error messages [V3]
4. ✅ Execute Workflow Trigger cleanup [V3]
5. ✅ Read/Write Files from Disk node [V4]
6. ✅ `encoding: "utf8"` [V4.1]
7. ✅ `dataPropertyName: "data"` [V5]
8. ✅ Docker volume mount [V6]
9. ✅ Container path `/email-templates/` [V6]

**Added**:
- Docker volume mount requirement: `../email-templates:/email-templates:ro`
- Container-compatible path: `/email-templates/{{template_file}}`
- Complete template accessibility from Docker container

**Changed**:
- Read File path: `/home/bruno/.../` → `/email-templates/` (container)
- Template access: Host filesystem → Docker volume mount
- Workflow execution: Complete (Read → Render → Send) ✅

**Docker Config Required**:
```yaml
# docker/docker-compose-dev.yml - Add to n8n-dev volumes:
- ../email-templates:/email-templates:ro
```

**Files**: `07_send_email_v6_docker_volume_fix.json`
**Docs**: `docs/PLAN_V6_DOCKER_TEMPLATE_ACCESS.md`

---

## [V74.1.2] - 2026-03-25 ✅ PRODUCTION

### WF02 V74.1.2 - Scheduling Check Fix
**Status**: ✅ In Production (Current Stable)

**Fixed**:
- Check If Scheduling node: incorrect comparison logic
- value2: `$json.next_stage` → `{{ $json.next_stage }}`
- operation: isEmpty → equals

**Result**:
- Services 1/3 + confirm → WF05 triggers correctly
- Services 2/4/5 → Handoff triggers correctly

**Files**: `02_ai_agent_conversation_V74.1_2_FUNCIONANDO.json`

---

## [V74.1] - 2026-03-24

### WF02 V74.1 - Scheduling Verification
**Status**: Superseded by V74.1.2

**Added**:
- "Check If Scheduling" node before WF05 trigger
- Conditional routing: scheduling vs handoff

**Issue**: value2 and operation incorrect (fixed in V74.1.2)

---

## [V3.6] - 2026-03-24 ✅ PRODUCTION

### WF05 V3.6 - Attendees Fix
**Status**: ✅ In Production (Current Stable)

**Fixed**:
- Attendees array format: object → string array
- WF07 trigger integration

**Files**: `05_appointment_scheduler_v3.6.json`

---

## [V4.0.3] - 2026-03-30

### WF05 V4.0.3 - Summary Node Fix
**Status**: ⚠️ Superseded by V4.0.4

**Fixed**:
- Summary parameter: node level → additionalFields
- Google Calendar API receives summary parameter

**Issue**: Empty `options: {}` in "Send Email" → only 4 fields to WF07

**Files**: `05_appointment_scheduler_v4.0.3.json`
**Docs**: `docs/BUGFIX_WF05_V4.0.3_SUMMARY_NODE.md`

---

## [V4.0.2] - 2026-03-30

### WF05 V4.0.2 - Title Fix
**Status**: ⚠️ Superseded by V4.0.3

**Fixed**:
- Event title: empty → "E2 Soluções - Agenda"

**Issue**: Summary not sent to API (fixed in V4.0.3)

**Files**: `05_appointment_scheduler_v4.0.2.json`
**Docs**: `docs/PLAN_V4.0.2_TITLE_FIX.md`

---

## [V4.0.1] - 2026-03-30

### WF05 V4.0.1 - Attendees Fix
**Status**: ⚠️ Superseded by V4.0.2

**Fixed**:
- Attendees format: object array → string array

**Issue**: Title empty (fixed in V4.0.2)

**Files**: `05_appointment_scheduler_v4.0.1.json`
**Docs**: `docs/BUGFIX_WF05_V4.0.1_ATTENDEES.md`

---

## [V4.0] - 2026-03-30

### WF05 V4.0 - Timezone and Title
**Status**: ⚠️ Superseded by V4.0.1

**Fixed**:
- Timezone: UTC → Brazil (-03:00)
- Event times: correct (08:00 instead of 05:00 UTC)

**Issue**: Attendees object array (fixed in V4.0.1)

---

## [V5] - 2026-03-30

### WF07 V5 - Data Property Fix
**Status**: ⚠️ Superseded by V6

**Fixed**:
- Added `dataPropertyName: "data"` to Read File node

**Issue**: Templates not accessible from Docker container

**Files**: `07_send_email_v5_data_property_fix.json`
**Docs**: `docs/BUGFIX_WF07_V5_DATA_PROPERTY_FIX.md`

---

## [V4.1] - 2026-03-30

### WF07 V4.1 - Encoding Fix
**Status**: ⚠️ Superseded by V5

**Fixed**:
- Added `encoding: "utf8"` to Read File node
- Text file reading for HTML templates

**Issue**: Missing `dataPropertyName` (fixed in V5)

**Files**: `07_send_email_v4.1_encoding_fix.json`
**Docs**: `docs/BUGFIX_WF07_V4.1_ENCODING_FIX.md`

---

## [V4] - 2026-03-30

### WF07 V4 - Docker Path Fix
**Status**: ⚠️ Superseded by V4.1

**Fixed**:
- Read/Write Files from Disk node (instead of Execute Command)
- Absolute path: `/home/bruno/.../email-templates/`
- No `$env.HOME` dependency

**Issue**: Empty output (fixed in V4.1)

**Files**: `07_send_email_v4_read_file_fix.json`
**Docs**: `docs/BUGFIX_WF07_V4_READ_FILE_FIX.md`

---

## [V3] - 2026-03-30

### WF07 V3 - Complete Fix
**Status**: ⚠️ Superseded by V4

**Fixed**:
- Template file mapping (4 templates)
- Email metadata (subject, sender, reply_to)
- Complete output (5 → 11 fields)
- Error messages improved
- Execute Workflow Trigger cleaned

**Issue**: Docker `$env.HOME` path error (fixed in V4)

**Files**: `07_send_email_v3_complete_fix.json`
**Docs**: `docs/BUGFIX_WF07_V3_COMPLETE_FIX.md`

---

## [V2.0] - 2026-03-26

### WF07 V2.0 - WF05 Integration
**Status**: ⚠️ Broken (Superseded by V3)

**Added**:
- WF05 integration attempt
- Basic email sending logic

**Issues**:
- Missing 6 critical fields (fixed in V3)
- No template mapping (fixed in V3)
- No sender configuration (fixed in V3)

**Files**: `07_send_email_v2_wf05_integration.json`

---

## [V2.8.3] - 2026-03-24 ✅ PRODUCTION

### WF01 V2.8.3 - Main Handler
**Status**: ✅ In Production (Current Stable)

**Function**:
- Duplicate detection (PostgreSQL ON CONFLICT)
- Message routing to WF02

**Files**: `01_main_whatsapp_handler_V2.8.3_NO_LOOP.json`

---

## Infrastructure - 2026-03-31

### Docker Fixes
**Date**: 2026-03-31

**Fixed**:
- n8n container startup: `KeyError: 'ContainerConfig'`
- Solution: Removed corrupted image, pulled fresh n8nio/n8n:latest

**Resolved**:
- Evolution API "unhealthy" status (cosmetic - API fully functional)
- Cause: Webhook 404 errors (endpoints not yet active)
- Status: No fix needed, will resolve when workflows activated

---

## Documentation - 2026-03-31

### Documentation Update
**Date**: 2026-03-31

**Updated**:
- ✅ CLAUDE.md: 572 → 226 lines (~60% compression)
- ✅ README.md: 424 → 272 lines (modernized, current status)
- ✅ QUICKSTART.md: New file (10-step guide)
- ✅ CHANGELOG.md: New file (version history)

**Strategy**:
- Reference-based architecture
- Compact table formats
- Symbol systems for status
- Removal of duplicate content

---

## Version History Table

| Workflow | Version | Date | Status | Key Change |
|----------|---------|------|--------|------------|
| WF01 | V2.8.3 | 2026-03-24 | ✅ PROD | Duplicate detection |
| WF02 | V74.1.2 | 2026-03-25 | ✅ PROD | Scheduling check fix |
| WF02 | **V75** | **2026-03-30** | **🚀 READY** | **Personalized messages** |
| WF05 | V3.6 | 2026-03-24 | ✅ PROD | Attendees array fix |
| WF05 | **V4.0.4** | **2026-03-30** | **🚀 READY** | **Email data fix** |
| WF07 | **V6** | **2026-03-30** | **🚀 READY** | **Docker volume fix** |

---

**Maintained by**: Claude Code | **Project**: E2 Soluções WhatsApp Bot
