# E2 Bot - Context

> **Prod**: WF01 V2.8.3 | WF02 V74.1.2 | WF05 V3.6 | **Ready**: WF02 V75 | WF05 V7 | **WF07 V13** ✅ | Updated: 2026-04-01

## 🎯 Stack

WhatsApp AI Bot | n8n 2.14.2 + Claude 3.5 + PostgreSQL + Evolution API v2.3.7 | PT-BR
**Flow**: WhatsApp → WF01 (dedup) → WF02 (AI) → WF05 (calendar) → WF07 (email)

---

## 📦 Workflows

### WF01: Handler V2.8.3 ✅ PROD
Duplicate detection via PostgreSQL ON CONFLICT → Routes to WF02

### WF02: AI Agent (8-state conversation)
- **Prod**: V74.1.2 | **Ready**: V75 (personalized appointment confirmation)
- **States**: greeting → service → name → phone → email → city → confirm → trigger
- **Services**: 1-Solar 2-Subestação 3-Projetos 4-BESS 5-Análise
- **Flow**: Services 1/3 + confirm → WF05 | Others → Handoff

### WF05: Appointment Scheduler
- **Prod**: V3.6 (no validation) | **Ready**: V7 ✅ (hardcoded business hours)
- **Function**: Google Calendar + DB + WF07 trigger
- **V7 Solution**: Hardcoded constants (08:00-18:00, Mon-Fri) - zero `$env` dependency

### WF07: Send Email
- **Prod**: None | **Ready**: V13 ✅ **INSERT...SELECT Pattern (DEFINITIVE)**
- **Architecture**: nginx (templates) → HTTP Request → Render → SMTP → DB log
- **V13 Fix**: INSERT...SELECT pattern (n8n expressions in query string)
- **Why**: queryReplacement returns [undefined] - use direct `{{ $json.* }}` injection

**V13 Query Pattern**:
```sql
INSERT INTO email_logs (...)
SELECT '{{ $json.to }}' as recipient_email, ...
RETURNING id, recipient_email, sent_at;
```

---

## 📁 Files

### Workflows (n8n/workflows/)
```
WF01: 01_main_whatsapp_handler_V2.8.3_NO_LOOP.json
WF02: 02_ai_agent_conversation_V74.1_2_FUNCIONANDO.json (prod)
      02_ai_agent_conversation_V75_APPOINTMENT_FINAL_MESSAGE.json (ready)
WF05: 05_appointment_scheduler_v3.6.json (prod)
      05_appointment_scheduler_v7_hardcoded_values.json (ready ✅)
WF07: 07_send_email_v13_insert_select.json (ready ✅ DEFINITIVE)
```

### Database Schema
```sql
conversations: phone, lead_name, service, state, next_stage, collected_data
appointments: lead_name/email, service, scheduled_date, google_calendar_event_id
appointment_reminders: appointment_id, type, time, status
email_logs: recipient_email/name, subject, template_used, status, sent_at, metadata
```

---

## 🚀 Deploy

### WF07 V13 (Ready for Production)
```bash
# Import
http://localhost:5678 → Import → 07_send_email_v13_insert_select.json

# Test with execution 18936 data
{
  "lead_email": "clima.cocal.2025@gmail.com",
  "lead_name": "bruno rosa",
  "service_type": "energia_solar",
  "city": "cocal-go",
  "calendar_success": true
}

# Expected:
# ✅ Email sent successfully
# ✅ Database log: RETURNING { id: 1, recipient_email: "...", sent_at: "..." }
# ✅ Template variables replaced: {{address}} = "Cocal, GO"
# ✅ No [undefined] errors

# Verify
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT id, recipient_email, template_used, sent_at FROM email_logs ORDER BY sent_at DESC LIMIT 1;"

# Deploy: Deactivate old versions → Activate V13 → Monitor logs
```

---

## 🔧 Commands

**DB Check**:
```bash
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT phone_number, lead_name, service_type, current_state FROM conversations ORDER BY updated_at DESC LIMIT 5;"
```

**Evolution API**:
```bash
curl -s http://localhost:8080/instance/fetchInstances \
  -H "apikey: ae569043cfa169380c378347f91a1141ea572541d2d1cadbed222db519c8a891" | jq
```

**Logs**:
```bash
docker logs -f e2bot-n8n-dev | grep -E "ERROR|V13|INSERT"
```

---

## 📊 Evolution History

### WF07 Critical Path (V2 → V13)
| Ver | Issue | Error | Fix |
|-----|-------|-------|-----|
| V2-V5 | Template access | fs/path blocked | → V9 |
| V9 | HTTP char array | Format detection | → V9.3 |
| V9.3 | Safe property ✅ | None | → V10 |
| V10 | Credential + service_name | Manual + mapping | → V11 |
| V11 | {{address}} + DB params | Format + queryReplacement | → V12 |
| V12 | queryReplacement [undefined] | n8n doesn't resolve ={{ }} | → V13 |
| **V13** | **✅ DEFINITIVE** | **None** | **INSERT...SELECT** |

**Root Cause V12→V13**: n8n `queryReplacement` parameter treats `={{ }}` as literal string, not expression context. Solution: Direct injection in `query` field with INSERT...SELECT pattern.

### WF05 Critical Path (V3 → V7)
| Ver | Issue | Error | Fix |
|-----|-------|-------|-----|
| V3.6 | No validation ✅ | None | PROD |
| V4-V6 | `$env` access | n8n security blocks ALL env var access | → V7 |
| **V7** | **✅ DEFINITIVE** | **None** | **Hardcoded constants** |

**Root Cause V4-V6**: n8n blocks `$env` in Code nodes AND Set expressions. Solution: Hardcode business hours in workflow generation.

---

## 📚 Documentation

**Main Docs**:
- `README.md` - Project overview and quick start
- `docs/ARCHITECTURE.md` - System architecture and data flow
- `docs/DEPLOYMENT.md` - Production deployment guide

**WF07 Evolution**:
- `docs/BUGFIX_WF07_V13_INSERT_SELECT_FIX.md` - 🎯 DEFINITIVE (INSERT...SELECT pattern)
- `docs/PLAN_NGINX_WF07_IMPLEMENTATION.md` - nginx + HTTP Request architecture
- `docs/SOLUTION_FINAL_HTTP_REQUEST.md` - HTTP Request definitive solution

**WF05 Evolution**:
- `docs/DEPLOY_WF05_V7_HARDCODED_FINAL.md` - Hardcoded business hours solution

**Setup**:
- `docs/Setups/SETUP_EMAIL_WF05_INTEGRATION.md` - Email integration guide

---

## 🎯 Status Summary

### Production (Stable)
- ✅ WF01 V2.8.3 - Deduplication working
- ✅ WF02 V74.1.2 - AI conversation stable
- ✅ WF05 V3.6 - Calendar integration working (no validation)

### Ready for Production
- 🚀 WF02 V75 - Personalized appointment confirmation
- 🚀 WF05 V7 - Business hours validation (hardcoded values)
- 🚀 **WF07 V13** - Email workflow **DEFINITIVE** ✅

### Key Learnings
1. **n8n queryReplacement**: Does NOT resolve `={{ }}` expressions - use INSERT...SELECT
2. **n8n $env access**: Blocked everywhere (Code + Set) - use hardcoded values
3. **n8n filesystem**: Read/Write blocked outside ~/.n8n-files - use HTTP Request + nginx
4. **PostgreSQL patterns**: INSERT...SELECT superior to VALUES for n8n workflows

---

**Project**: E2 Soluções WhatsApp Bot | **Stack**: n8n 2.14.2 | **Maintained**: Claude Code
