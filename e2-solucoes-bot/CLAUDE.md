# E2 Bot - Claude Code Context

> **Production**: WF01 V2.8.3 ✅ | WF02 V69.2 ✅ | Updated: 2026-03-11

---

## 🎯 System

**Type**: WhatsApp AI Bot (E2 Soluções - Engenharia Elétrica)
**Stack**: n8n + Claude 3.5 + PostgreSQL + Evolution API v2.3.7
**Language**: PT-BR

**Architecture**:
```
WhatsApp → WF01 (duplicate detection) → WF02 (AI agent: 8 states, 12 templates)
```

---

## ✅ Production

### WF01: Handler V2.8.3 ✅
- **File**: `01_main_whatsapp_handler_V2.8.3_NO_LOOP.json`
- **Function**: Duplicate detection + routing (PostgreSQL ON CONFLICT)

### WF02: AI Agent V69.2 ✅ DEPLOYED
- **File**: `02_ai_agent_conversation_V69_2_NEXT_STAGE_FIX.json` (80.2 KB)
- **States**: 8 (greeting → confirmation)
- **Templates**: 12 total
- **Services**: 1-Solar | 2-Subestação | 3-Projetos | 4-BESS | 5-Análise

**V69.2 Fixes** (all bugs resolved):
- ✅ Triggers execute (next_stage reference fixed)
- ✅ Name populated (trimmedCorrectedName)
- ✅ Returning user (getServiceName function)
- ✅ Workflow connected (node name preserved)

---

## 🔄 Flow

**8 States**:
1. greeting → Menu (5 services)
2. service_selection → Capture (1-5)
3. collect_name → Get name + WhatsApp confirm
4. collect_phone_whatsapp_confirmation → Confirm/alternative
5. collect_phone_alternative → Alternative phone
6. collect_email → Email or skip
7. collect_city → City
8. confirmation → Summary + triggers
   - "sim" + service 1/3 → **Trigger Appointment Scheduler** ✅
   - "sim" + other → **Trigger Human Handoff** ✅

---

## 🚀 Deploy

```bash
# Import V69.2
# http://localhost:5678 → Import:
# n8n/workflows/02_ai_agent_conversation_V69_2_NEXT_STAGE_FIX.json

# Deactivate old → Activate V69.2 → Test
```

**Test**: WhatsApp "oi" → service 1 → complete → verify Trigger Appointment Scheduler executes

**Rollback**: V69.2 → V68.3 (stable fallback)

---

## 📂 Key Files

```
workflows/
  ├── 01_main_whatsapp_handler_V2.8.3_NO_LOOP.json              ✅ Production
  └── 02_ai_agent_conversation_V69_2_NEXT_STAGE_FIX.json        ✅ Production

scripts/
  ├── generate-workflow-v69_1-fixed-connections.py              V69.1
  └── generate-workflow-v69_2-next-stage-fix.py                 V69.2

docs/
  ├── V69_1_CONNECTION_BUG_FIX.md                               V69.1 analysis
  ├── V69_2_NEXT_STAGE_BUG_FIX.md                               V69.2 analysis
  └── PROJECT_STATUS.md                                         Current status
```

---

## 🐛 Version History (Compressed)

**WF01**: V2.8.3 ✅ (atomic duplicate detection)

**WF02**:
- V64-V67: Evolution + bug fixes
- V68.3: Syntax fixes (base)
- V69: getServiceName (broke connections)
- V69.1: Fixed connections (triggers broken)
- **V69.2** ✅: Fixed triggers (ALL RESOLVED)

---

## 🔧 Commands

**Database**:
```bash
docker exec -it e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT phone_number, lead_name, service_type, current_state FROM conversations ORDER BY updated_at DESC LIMIT 5;"
```

**Evolution**:
```bash
curl -s http://localhost:8080/instance/fetchInstances \
  -H "apikey: ae569043cfa169380c378347f91a1141ea572541d2d1cadbed222db519c8a891" | jq
```

**Logs**:
```bash
docker logs -f e2bot-n8n-dev | grep -E "V69|Trigger"
```

---

## 🎯 Status

✅ **V69.2 DEPLOYED** - All features working:
- Triggers: Both execute correctly ✅
- Workflow: Connected and executes ✅
- Data: All fields populated ✅
- Production: 100% ready ✅

**Next**: Monitor production, track trigger execution rate

---

**Maintained by**: Claude Code | **Last Review**: 2026-03-11
