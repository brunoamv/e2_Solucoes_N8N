# E2 Bot - Claude Code Context

> **Production**: WF01 V2.8.3 | WF02 **V74 Ready** 🚀 | WF05 V3.6 ✅ | Updated: 2026-03-24

---

## 🎯 System

**Type**: WhatsApp AI Bot (E2 Soluções - Engenharia Elétrica)
**Stack**: n8n + Claude 3.5 + PostgreSQL + Evolution API v2.3.7
**Language**: PT-BR

**Flow**: WhatsApp → WF01 (duplicate detection) → WF02 (AI: 8 states) → [WF05 schedule | Handoff]

---

## ✅ Production

### WF01: Handler V2.8.3
- **File**: `01_main_whatsapp_handler_V2.8.3_NO_LOOP.json`
- **Function**: Duplicate detection + routing (PostgreSQL ON CONFLICT)

### WF02: AI Agent V74 ✅ READY FOR DEPLOY
- **File**: `02_ai_agent_conversation_V74_APPOINTMENT_CONFIRMATION.json`
- **Current Production**: V69.2 (stable, can rollback)
- **States**: 8 (greeting → confirmation)
- **Services**: 1-Solar | 2-Subestação | 3-Projetos | 4-BESS | 5-Análise
- **V74 Features**: Scheduling verification + correct WF05 trigger
- **Status**: All validations pass, ready for testing

### WF05: Appointment Scheduler V3.6
- **File**: `05_appointment_scheduler_v3.6.json`
- **ID**: `f6eIJIqfaSs6BSpJ` (CRITICAL - use this ID)
- **Function**: Google Calendar + DB appointments
- **Tech**: Direct INSERT reminders, array attendees

---

## 🚀 V74 Ready for Deploy

**File**: `02_ai_agent_conversation_V74_APPOINTMENT_CONFIRMATION.json`

**What's New**:
- "Check If Scheduling" verification node
- Correct WF05 V3.6 trigger (ID: f6eIJIqfaSs6BSpJ)
- Smart routing: service 1/3 + confirm → WF05 | other → handoff
- 7 input fields configured (phone, name, email, service, city, etc.)

**Documentation**:
- `docs/TEST_V74_END_TO_END.md` - 4 test cases (service 1/3 schedule, service 2/4/5 handoff)
- `docs/DEPLOY_V74_PRODUCTION.md` - Complete deploy procedure
- `docs/PLAN_V74_APPOINTMENT_CONFIRMATION_MESSAGE.md` - Technical plan

---

## 🔄 Conversation Flow

**8 States**:
1. greeting → Menu
2. service_selection → Capture
3. collect_name → Name + WhatsApp confirm
4. collect_phone_whatsapp_confirmation → Confirm/alternative
5. collect_phone_alternative → Alternative phone
6. collect_email → Email or skip
7. collect_city → City
8. confirmation → Summary + triggers

**V74 Enhancement** (state 8 - confirmation):
```
Send WhatsApp Response
    ↓
Check If Scheduling (NEW NODE)
    ↓
    ├─ TRUE (next_stage = 'scheduling_redirect') → Trigger WF05 V3.6
    └─ FALSE (other states) → Check If Handoff → Trigger Human Handoff
```

**Trigger Rules**:
- **WF05**: Services 1 (Solar) or 3 (Projetos) + option 1 → schedule appointment
- **Handoff**: Services 2/4/5 OR option 2 → human contact

---

## 📂 Key Files

**Production Workflows**:
```
n8n/workflows/
  ├── 01_main_whatsapp_handler_V2.8.3_NO_LOOP.json              # WF01
  ├── 02_ai_agent_conversation_V69_2_NEXT_STAGE_FIX.json        # WF02 current
  ├── 02_ai_agent_conversation_V74_APPOINTMENT_CONFIRMATION.json # WF02 ready
  └── 05_appointment_scheduler_v3.6.json                         # WF05
```

**V74 Script**:
```
scripts/generate-workflow-v74-appointment-confirmation.py       # V74 generator
```

**Database Schema**:
```sql
conversations: phone_number, lead_name, service_type, current_state, next_stage, collected_data
appointments: lead_name, lead_email, service_type, scheduled_date, google_calendar_event_id
appointment_reminders: appointment_id, reminder_type, reminder_time, status
```

---

## 🚀 V74 Deploy Guide

**Step 1 - Import**:
```
http://localhost:5678 → Import from File
→ n8n/workflows/02_ai_agent_conversation_V74_APPOINTMENT_CONFIRMATION.json
```

**Step 2 - Test**: Follow `docs/TEST_V74_END_TO_END.md`
- Test Case 1: Service 1 (Solar) + confirm → WF05 triggers
- Test Case 2: Service 3 (Projetos) + confirm → WF05 triggers
- Test Case 3: Service 2 (Subestação) + confirm → Handoff
- Test Case 4: Option 2 (any service) → Handoff

**Step 3 - Deploy**: Follow `docs/DEPLOY_V74_PRODUCTION.md`
- Deactivate V69.2
- Activate V74
- Monitor 2h → 24h → 7d

**Rollback**: Deactivate V74 → Activate V69.2

---

## 🔧 Quick Commands

**Database Check**:
```bash
docker exec -it e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT phone_number, lead_name, service_type, current_state, next_stage FROM conversations ORDER BY updated_at DESC LIMIT 5;"
```

**Appointments**:
```bash
docker exec -it e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT lead_name, service_type, scheduled_date, google_calendar_event_id FROM appointments ORDER BY created_at DESC LIMIT 5;"
```

**Evolution API**:
```bash
curl -s http://localhost:8080/instance/fetchInstances \
  -H "apikey: ae569043cfa169380c378347f91a1141ea572541d2d1cadbed222db519c8a891" | jq -r '.[] | "\(.instance.instanceName): \(.instance.state)"'
```

**Logs**:
```bash
docker logs -f e2bot-n8n-dev | grep -E "V74|Trigger|ERROR"
```

---

## 📊 Version History

| Version | Date | Status | Key Change |
|---------|------|--------|------------|
| V68.3 | 2026-03-09 | Stable | Base syntax fixes |
| V69.2 | 2026-03-11 | ✅ PROD | Trigger fix, all bugs resolved |
| **V74** | **2026-03-24** | **🚀 READY** | **Scheduling verification + correct WF05 ID** |

---

## 🎯 V74 Status

**Implementation**:
- ✅ Script generated (all validations pass)
- ✅ Workflow created (35 nodes, 2 new)
- ✅ Test guide ready (4 comprehensive cases)
- ✅ Deploy guide ready (full procedure)

**Pending**:
- ⏳ Tests execution (TEST_V74_END_TO_END.md)
- ⏳ Production deployment (DEPLOY_V74_PRODUCTION.md)

**Success Criteria**:
- Execution success >95%
- Response time <3s
- Services 1/3 + confirm → WF05 triggers
- Google Calendar events match appointments
- Error rate <2%

---

**Maintained by**: Claude Code | **Project**: E2 Soluções WhatsApp Bot
