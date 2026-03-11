# E2 Bot - Claude Code Context

> **Status**: WF01 V2.8.3 ✅ | WF02 V67 ✅ DEPLOYED | Updated: 2026-03-11

---

## 🎯 System

**Type**: WhatsApp AI Bot (E2 Soluções - Engenharia Elétrica)
**Stack**: n8n + Claude 3.5 + PostgreSQL + Evolution API v2.3.7
**Language**: PT-BR

**Architecture**:
```
WhatsApp → WF01 (duplicate detection) → WF02 (AI agent: 13 states, 25 templates, correction flow)
```

---

## ✅ Production

### WF01: Handler V2.8.3 ✅
- **Function**: Duplicate detection + routing (PostgreSQL ON CONFLICT)
- **File**: `01_main_whatsapp_handler_V2.8.3_NO_LOOP.json`

### WF02: AI Agent V67 ✅ DEPLOYED
- **File**: `02_ai_agent_conversation_V67_SERVICE_DISPLAY_FIX.json` (76.7 KB)
- **States**: 13 (8 base + 5 correction)
- **Templates**: 25 (14 base + 11 correction)
- **Services**: 1-Solar | 2-Subestação | 3-Projetos | 4-BESS | 5-Análise

**V67 Fixes** (cumulative):
- ✅ Service display bug (all 5 services show correctly)
- ✅ V66 Bug #1: trimmedCorrectedName (duplicate variable)
- ✅ V66 Bug #2: query_correction_update (scope error)

**Features**:
- Full correction flow (name, phone, email, city)
- SQL UPDATE queries (atomic: column + JSONB)
- Loop protection (max 5 corrections → handoff)

---

## 🔄 Flow

**Base States (8)**:
1. greeting → Menu (5 services)
2. service_selection → Capture (1-5)
3. collect_name → Get name + WhatsApp confirm
4. collect_phone_whatsapp_confirmation → Confirm/alternative
5. collect_phone_alternative → Alternative phone
6. collect_email → Email or skip
7. collect_city → City
8. confirmation → Summary + trigger workflows

**Correction States (5)**:
9. correction_field_selection → Choose field (1-4)
10-13. correction_[name|phone|email|city] → Correct + UPDATE → return

**Confirmation Options**:
- "1" (sim/agendar) → Scheduling OR handoff_comercial
- "2" (não agora) → handoff_comercial
- "3" (corrigir) → Correction flow

---

## 🚀 Deploy

```bash
# Import V67
# http://localhost:5678 → Import:
# n8n/workflows/02_ai_agent_conversation_V67_SERVICE_DISPLAY_FIX.json

# Deactivate old → Activate V67 → Test
```

**Test**: Verify all 5 services display correctly in confirmation message.

**Rollback**: V67 → V66 FIXED V2 (service bug) OR V65 (stable, no correction)

---

## 📂 Key Files

```
workflows/
  ├── 01_main_whatsapp_handler_V2.8.3_NO_LOOP.json              ✅ Production
  ├── 02_ai_agent_conversation_V67_SERVICE_DISPLAY_FIX.json     ✅ Production
  ├── 02_ai_agent_conversation_V66_*_FIXED_V2.json              (rollback)
  └── 02_ai_agent_conversation_V65_UX_COMPLETE_FIX.json         (stable fallback)

scripts/
  ├── fix-v67-service-display-keys.py                           V67 fix
  ├── generate-workflow-v66-correction-states.py                V66 generator
  ├── fix-v66-duplicate-variable.py                             V66 fix #1
  └── fix-v66-query-correction-update.py                        V66 fix #2

docs/
  ├── V67_SERVICE_DISPLAY_FIX.md                                V67 bug report
  ├── V66_FIXED_V2_READY_FOR_DEPLOYMENT.md                      V66 guide
  └── PLAN/
      ├── V67_SERVICE_DISPLAY_FIX.md                            V67 plan
      └── V66_CORRECTION_STATES_COMPLETE.md                     V66 spec (1100+ lines)
```

---

## 🐛 Version History

**WF01**: V2.8.3 ✅ (atomic duplicate detection)

**WF02**:
- V64 → V65 → V66 (correction states, 2 bugs)
- V66 FIXED V2 (2 bugs fixed, service display bug)
- **V67** ✅ (service display fix, all bugs resolved)

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
docker logs -f e2bot-n8n-dev | grep -E "V67|service_type|correction"
```

---

## 🎯 Current Status

✅ **V67 DEPLOYED** - All features working:
- Service display: All 5 services correct
- Correction flow: All 4 fields working
- V66 bug fixes: Both preserved
- Production ready: 100%

**Next**: Monitor production usage, collect user feedback

---

**Maintained by**: Claude Code | **Last Review**: 2026-03-11
