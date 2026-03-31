# E2 Bot - Context

> **Prod**: WF01 V2.8.3 | WF02 V74.1.2 | WF05 V3.6 | **Ready**: WF02 V75 | WF05 V4.0.4 | WF07 V6 | Updated: 2026-03-31

## 🎯 Stack

WhatsApp AI Bot (E2 Soluções) | n8n + Claude 3.5 + PostgreSQL + Evolution API v2.3.7 | PT-BR

**Flow**: WhatsApp → WF01 (dedup) → WF02 (AI 8 states) → [WF05 calendar → WF07 email | Handoff]

---

## 📦 Workflows

### WF01: Handler V2.8.3 ✅
- Duplicate detection via PostgreSQL ON CONFLICT
- Routes to WF02

### WF02: AI Agent
- **Prod**: V74.1.2 (stable)
- **Ready**: V75 🚀 (personalized appointment confirmation)
- **States**: greeting → service → name → phone → email → city → confirm → trigger
- **Services**: 1-Solar 2-Subestação 3-Projetos 4-BESS 5-Análise
- **Triggers**: Services 1/3+confirm → WF05 | Others → Handoff

**V75 Changes**:
- Personalized final message with real data (date DD/MM/YYYY, time HH:MM, client info)
- Service formatting: `energia_solar` → `Energia Solar`
- 9 template variables: date, time_start/end, service_emoji/name, name, city, email, calendar_link
- Replaces generic "vamos agendar" with "Agendamento Confirmado!"

### WF05: Appointment Scheduler
- **Prod**: V3.6 (stable)
- **Ready**: V4.0.4 🚀 (email data fix)
- **ID**: `f6eIJIqfaSs6BSpJ` (CRITICAL)
- **Function**: Google Calendar + DB + WF07 trigger

**V4.0.4 Fixes** (all from V4.0.3):
- ✅ V4.0: Brazil timezone (-03:00)
- ✅ V4.0.1: Attendees array format `[email]`
- ✅ V4.0.2: Title "E2 Soluções - Agenda"
- ✅ V4.0.3: Summary in additionalFields
- ✅ V4.0.4: Email data passing (4 → 16 fields to WF07)

**V4.0.4 Root Cause**: V4.0.3 "Send Email" node → empty `options: {}` → only 4 fields passed

**V4.0.4 Solution**: New "Prepare Email Trigger Data" node merges appointment data before WF07 trigger

### WF07: Send Email
- **Prod**: None (all broken)
- **Ready**: V6 🚀 (Docker volume fix - COMPLETE)

**Evolution Timeline**:
| Ver | Issue | Fix |
|-----|-------|-----|
| V2.0 | Missing 6 fields | → V3 |
| V3 | Docker `$env.HOME` path | → V4 |
| V4 | Read File empty output | → V4.1 |
| V4.1 | Missing dataPropertyName | → V5 |
| V5 | Templates not in container | → V6 |
| **V6** | **✅ ALL FIXED** | **Docker volume mount** |

**V6 Complete Solution**:
1. Template/sender config centralized
2. Read/Write Files node (not bash)
3. Encoding: `utf8`
4. Data property: `data`
5. **Container path**: `/email-templates/` (not host path)
6. **Docker mount**: `../email-templates:/email-templates:ro` (CRITICAL)

**V6 Pending**:
1. Update `docker-compose-dev.yml` (add volume mount)
2. Restart: `docker-compose down && up -d`
3. Verify: `docker exec e2bot-n8n-dev ls /email-templates/`
4. Import WF07 V6
5. Test WF05 → WF07 flow

---

## 📁 Files

**Workflows** (n8n/workflows/):
```
01_main_whatsapp_handler_V2.8.3_NO_LOOP.json           # WF01 prod
02_ai_agent_conversation_V74.1_2_FUNCIONANDO.json      # WF02 prod
02_ai_agent_conversation_V75_APPOINTMENT_FINAL_MESSAGE.json  # WF02 ready
05_appointment_scheduler_v3.6.json                     # WF05 prod
05_appointment_scheduler_v4.0.4.json                   # WF05 ready
07_send_email_v6_docker_volume_fix.json                # WF07 ready
```

**Generators** (scripts/):
```
generate-workflow-v75-appointment-confirmation.py      # V75
generate-workflow-wf05-v4.0.4-email-data-fix.py       # V4.0.4
generate-workflow-wf07-v6-docker-volume-fix.py        # V6
```

**DB Schema**:
```sql
conversations: phone, lead_name, service, state, next_stage, collected_data
appointments: lead_name/email, service, scheduled_date, google_calendar_event_id
appointment_reminders: appointment_id, type, time, status
```

---

## 🚀 Deploy

### V75 (WF02)
```bash
# Import
http://localhost:5678 → Import → 02_ai_agent_conversation_V75_APPOINTMENT_FINAL_MESSAGE.json

# Test: Service 1/3 → complete flow → verify personalized final message

# Deploy: docs/DEPLOY_V75_PRODUCTION.md
# Backup V74.1.2 → Deactivate → Activate V75 → Monitor

# Rollback: Deactivate V75 → Activate V74.1.2
```

### V4.0.4 (WF05)
```bash
# Import: 05_appointment_scheduler_v4.0.4.json
# Test: Service 1/3 → verify 16 fields passed to WF07
# Verify: "Prepare Email Trigger Data" node output
# Monitor: Email logs for successful sends
```

### V6 (WF07) - CRITICAL DOCKER CONFIG
```bash
# 1. Update docker-compose-dev.yml (n8n-dev volumes):
volumes:
  - n8n_dev_data:/home/node/.n8n
  - ../n8n/workflows:/workflows:ro
  - ../email-templates:/email-templates:ro  # ← ADD THIS

# 2. Restart Docker
docker-compose -f docker/docker-compose-dev.yml down
docker-compose -f docker/docker-compose-dev.yml up -d

# 3. Verify mount
docker exec e2bot-n8n-dev ls -la /email-templates/
# Expected: 4 HTML files

# 4. Import: 07_send_email_v6_docker_volume_fix.json
# 5. Test: WF05 V4.0.4 → WF07 V6 → verify email sent
```

---

## 🔧 Commands

**DB Check**:
```bash
docker exec -it e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT phone_number, lead_name, service_type, current_state FROM conversations ORDER BY updated_at DESC LIMIT 5;"
```

**Appointments**:
```bash
docker exec -it e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT lead_name, service_type, scheduled_date FROM appointments ORDER BY created_at DESC LIMIT 5;"
```

**Evolution API**:
```bash
curl -s http://localhost:8080/instance/fetchInstances \
  -H "apikey: ae569043cfa169380c378347f91a1141ea572541d2d1cadbed222db519c8a891" | jq -r '.[] | .instance.instanceName + ": " + .instance.state'
```

**Logs**:
```bash
docker logs -f e2bot-n8n-dev | grep -E "ERROR|V75"
```

---

## 📊 History

| WF | Ver | Date | Status | Change |
|----|-----|------|--------|--------|
| WF02 | V74.1 | 2026-03-25 | ✅ PROD | Scheduling check fix |
| WF02 | **V75** | **2026-03-31** | **🚀 READY** | **Personalized confirmation** |
| WF05 | V3.6 | 2026-03-24 | ✅ PROD | Attendees + WF07 trigger |
| WF05 | **V4.0.4** | **2026-03-30** | **🚀 READY** | **16 fields → WF07** |
| WF07 | **V6** | **2026-03-30** | **🚀 READY** | **Docker volume (complete)** |

---

## 🎯 Status

### WF02 V75
- ✅ Generated (104.1 KB, 34 nodes)
- ✅ Validated
- ⏳ Import + test + deploy
- Success: Personalized message with real data

### WF05 V4.0.4
- ✅ Generated (38 nodes)
- ✅ Data fix validated (16 fields)
- ⏳ Import + test WF05→WF07
- Success: No "email recipient not found"

### WF07 V6
- ✅ Generated (9 nodes, container path)
- ✅ All 9 bugs fixed (V2.0→V6)
- ⏳ **CRITICAL**: Docker volume mount
- ⏳ Import + test
- Success: Templates accessible, email sent

---

## 📚 Docs

**Deploy**: `docs/DEPLOY_V75_PRODUCTION.md`
**Bugfixes**:
- `docs/BUGFIX_WF05_V4.0.4_EMAIL_DATA_PASSING.md`
- `docs/PLAN_V6_DOCKER_TEMPLATE_ACCESS.md`
**Setup**: `docs/Setups/SETUP_EMAIL_WF05_INTEGRATION.md`

---

**Project**: E2 Soluções WhatsApp Bot | **Maintained**: Claude Code
