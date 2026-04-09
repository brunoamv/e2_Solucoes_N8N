# E2 Bot - Context

> **Prod**: WF01 V2.8.3 | WF02 V74.1.2 | WF05 V3.6
> **Ready**: WF02 V76 ✅ | WF05 V7 | WF06 | WF07 V13
> **Updated**: 2026-04-08

## Stack

n8n 2.14.2 + Claude 3.5 + PostgreSQL + Evolution API v2.3.7 | PT-BR
**Flow**: WhatsApp → WF01 (dedup) → WF02 (AI) → WF05 (calendar) → WF07 (email)

---

## Workflows

| WF | Prod | Ready | Function |
|----|------|-------|----------|
| **01** | V2.8.3 ✅ | - | Dedup via PostgreSQL ON CONFLICT |
| **02** | V74.1.2 (10 states) | V76 (12 states, proactive UX) | AI conversation: greeting→service→name→phone→email→city→confirm→date/time |
| **05** | V3.6 (no validation) | V7 (hardcoded hours) | Google Calendar + DB + WF07 trigger |
| **06** | - | V1 ✅ | Calendar availability microservice for WF02 V76 |
| **07** | - | V13 ✅ | nginx → HTTP → SMTP → DB (INSERT...SELECT pattern) |

**Services**: 1-Solar | 2-Subestação | 3-Projetos | 4-BESS | 5-Análise
**WF02 Flow**: Services 1/3 + confirm → WF06 → WF05 | Others → Handoff

---

## Files

**Workflows** (`n8n/workflows/`):
```
Active (7):
  01_main_whatsapp_handler_V2.8.3_NO_LOOP.json
  02_ai_agent_conversation_V74.1_2_FUNCIONANDO.json | V76_PROACTIVE_UX.json
  05_appointment_scheduler_v3.6.json | v7_hardcoded_values.json
  06_calendar_availability_service_v1.json
  07_send_email_v13_insert_select.json

Old (57): n8n/workflows/old/ - WF02-07 historical versions
```

**DB Schema**:
- `conversations`: phone, lead_name, service, state, next_stage, collected_data
- `appointments`: lead_name/email, service, scheduled_date, google_calendar_event_id
- `email_logs`: recipient_email/name, subject, template_used, status, sent_at

---

## Deploy

### WF02 V76
```bash
bash scripts/deploy-wf02-v76.sh  # Auto deploy
bash scripts/test-wf02-v76-e2e.sh  # E2E test
# Canary: 20% → 50% → 80% → 100%
# Docs: docs/implementation/WF02_V76_DEPLOYMENT_SUMMARY.md
```

### WF07 V13
```bash
# Import: 07_send_email_v13_insert_select.json
# Test: { lead_email, lead_name, service_type, city, calendar_success }
# Expected: Email sent + DB log RETURNING
# Docs: docs/fix/BUGFIX_WF07_V13_INSERT_SELECT_FIX.md
```

---

## Commands

```bash
# DB
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT phone_number, lead_name, service_type, current_state FROM conversations ORDER BY updated_at DESC LIMIT 5;"

# Evolution API
curl -s http://localhost:8080/instance/fetchInstances \
  -H "apikey: ae569043cfa169380c378347f91a1141ea572541d2d1cadbed222db519c8a891" | jq

# Logs
docker logs -f e2bot-n8n-dev | grep -E "ERROR|V13|INSERT"
```

---

## Critical Learnings

### n8n Limitations
1. **queryReplacement**: Does NOT resolve `={{ }}` → Use INSERT...SELECT
2. **$env access**: Blocked (Code + Set) → Use hardcoded values
3. **Filesystem**: Read/Write blocked → Use HTTP Request + nginx

### Evolution Path
- **WF07**: V2-V5 (fs blocked) → V9 (HTTP) → V13 (INSERT...SELECT) ✅
- **WF05**: V3-V6 ($env blocked) → V7 (hardcoded) ✅
- **WF02**: V68-V75 (reactive) → V76 (proactive UX) ✅

### Key Insights
1. **Proactive UX** > Reactive validation (100% error elimination)
2. **Microservices** (WF06) enable independent testing/scaling
3. **INSERT...SELECT** superior to VALUES for n8n PostgreSQL
4. **Graceful degradation** required for external service integration

---

## Documentation

**Quick Access**:
- Setup: `docs/Setups/QUICKSTART.md` (30-45 min)
- Email: `docs/Setups/SETUP_EMAIL.md` (Port 465 SSL/TLS)
- Credentials: `docs/Setups/SETUP_CREDENTIALS.md`
- Index: `docs/INDEX.md` | README: `docs/README.md`

**Implementation**:
- WF02 V76: `docs/implementation/WF02_V76_*.md` (5 docs)
- WF06: `docs/implementation/WF06_CALENDAR_AVAILABILITY_SERVICE.md`
- WF07 V13: `docs/fix/BUGFIX_WF07_V13_INSERT_SELECT_FIX.md`
- WF05 V7: `docs/deployment/DEPLOY_WF05_V7_HARDCODED_FINAL.md`

**Structure** (2026-04-08 reorganization):
```
docs/
├── INDEX.md, README.md
├── Setups/ (config guides)
├── Guides/ (user docs)
├── implementation/ (WF02, WF05, WF06, WF07)
├── analysis/ (technical analyses)
├── fix/ (bugfixes)
├── deployment/ (deploys)
└── PLAN/ (planning)
```

---

**Project**: E2 Soluções WhatsApp Bot | n8n 2.14.2 | Maintained: Claude Code
