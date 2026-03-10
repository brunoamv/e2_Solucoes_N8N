# E2 Bot - Context for Claude Code

> **Status**: WF01 V2.8.3 ✅ | WF02 V63 🚀 READY | Updated: 2026-03-10

---

## 🎯 System Overview

**Type**: WhatsApp AI Bot (E2 Soluções - Engenharia Elétrica)
**Stack**: n8n + Claude 3.5 + PostgreSQL + Evolution API v2.3.7
**Language**: PT-BR

---

## ✅ Production Status

### WF01: Handler V2.8.3 ✅ DEPLOYED
- **Function**: Duplicate detection + routing
- **Method**: PostgreSQL ON CONFLICT atomic operation
- **File**: `01_main_whatsapp_handler_V2.8.3_NO_LOOP.json`

### WF02: AI Agent V63 🚀 READY FOR DEPLOYMENT
- **Status**: Generated, ready for import
- **File**: `02_ai_agent_conversation_V63_COMPLETE_REDESIGN.json` (60.5 KB)
- **Generator**: `scripts/generate-workflow-v63-complete-redesign.py`

**V63 Key Improvements** (vs V62.3):
- ✅ **Removed** manual phone collection (redundant state)
- ✅ **Direct flow**: name → WhatsApp confirmation (uses webhook phone)
- ✅ **Optimized**: 8 states (was 9), 12 templates (was 16)
- ✅ **Code**: ~24% reduction (~950 lines from ~1260)
- ✅ **Validated**: Triggers for scheduling + handoff_comercial

**Plan Documentation**:
- `docs/PLAN/V63_COMPLETE_FLOW_REDESIGN.md` - Complete technical plan
- `docs/PLAN/V63_VALIDATION_REPORT.md` - Requirements validation

---

## 📊 Architecture

```
WhatsApp (Evolution API v2.3.7)
  ↓
WF01 V2.8.3: Handler
  ├─ Extract phone/message
  ├─ Save (ON CONFLICT DO NOTHING)
  └─ Route (duplicate/new) → WF02
  ↓
WF02 V63: AI Agent
  ├─ State Machine (8 states)
  ├─ Templates (12 total)
  ├─ Database (PostgreSQL)
  └─ Claude AI + RAG
```

---

## 🔄 V63 Flow States (8 Total)

```
1. greeting               → Show menu (5 services)
2. service_selection      → Capture service (1-5)
3. collect_name           → Get name + DIRECT to WhatsApp confirm
4. collect_phone_whatsapp_confirmation → Confirm or alternative
5. collect_phone_alternative → If user chose option 2
6. collect_email          → Email or skip
7. collect_city           → City
8. confirmation           → Show summary + trigger workflows
   ├─ Option "sim" + service 1/3 → scheduling (Appointment Scheduler)
   └─ Option "sim" + other services → handoff_comercial (Human Handoff)
```

**Key Optimization**: Removed `collect_phone` state - uses `input.phone_number` from Evolution webhook

**Services**: 1-Solar | 2-Subestação | 3-Projetos | 4-BESS | 5-Análise

---

## 🚀 Deploy V63

### Quick Deploy (5 steps)
```bash
# 1. Import workflow
# http://localhost:5678 → Import:
# n8n/workflows/02_ai_agent_conversation_V63_COMPLETE_REDESIGN.json

# 2. Deactivate old (V62.3 or V60.2)
# Find old workflow → Toggle: Inactive

# 3. Activate V63
# Find "V63 COMPLETE REDESIGN" → Toggle: Active

# 4. Test happy path
# WhatsApp: "oi" → "1" → "Bruno" → "1" (confirm WhatsApp) → email → city → "sim"
# Expected: Scheduling message ✅

# 5. Monitor
docker logs -f e2bot-n8n-dev | grep -E "V63|confirmation"
```

### Test Scenarios
```bash
# A) Happy path (WhatsApp confirmed)
"oi" → "1" → "Bruno Rosa" → "1" → "bruno@email.com" → "Goiânia" → "sim"
# ✅ Verify: Direct flow, no manual phone prompt

# B) Alternative phone
"oi" → "2" → "Maria" → "2" → "(62)3092-2900" → email → city → "sim"
# ✅ Verify: Alternative phone collected

# C) Data correction
Complete flow → "não" → "3" (email) → new email → city → "sim"
# ✅ Verify: Field corrected, summary updated
```

### Rollback
```bash
# If issues: Deactivate V63 → Activate V62.3 or V58.1 (stable)
```

---

## 📂 Key Files

```
workflows/
  ├── 01_main_whatsapp_handler_V2.8.3_NO_LOOP.json       ✅ Production
  └── 02_ai_agent_conversation_V63_COMPLETE_REDESIGN.json 🚀 Ready

scripts/
  └── generate-workflow-v63-complete-redesign.py         Generator

docs/
  ├── QUICKSTART.md                         Quick setup
  └── PLAN/
      ├── V63_COMPLETE_FLOW_REDESIGN.md     Technical plan
      └── V63_VALIDATION_REPORT.md          Validation
```

---

## 🐛 Version History (Compressed)

**WF01**: V2.8.0-2 (evolution) → V2.8.3 ✅ (atomic duplicate detection)

**WF02**:
- V27-V56: Evolution phases
- V57.2: Object fix
- V58.1: UX refactor (stable fallback)
- V60.2: Complete flow + rich templates
- V62.3: Bug fixes (but introduced template timing issues)
- **V63**: 🚀 Complete redesign (simplified, optimized)

---

## 🔧 Essential Commands

### Database Check
```bash
docker exec -it e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT phone_number, lead_name, service_type, current_state FROM conversations ORDER BY updated_at DESC LIMIT 5;"
```

### Evolution Status
```bash
curl -s http://localhost:8080/instance/fetchInstances \
  -H "apikey: ae569043cfa169380c378347f91a1141ea572541d2d1cadbed222db519c8a891" | jq
```

### Logs (Real-time)
```bash
# All logs with V63 markers
docker logs -f e2bot-n8n-dev | grep -E "V63|State Machine|confirmation"
```

---

## 📚 External References

- **n8n**: https://docs.n8n.io
- **Claude**: https://docs.anthropic.com
- **Evolution API**: https://github.com/EvolutionAPI
- **Detailed Setup**: `docs/QUICKSTART.md`

---

## 🎯 Next Steps

1. ✅ V63 workflow generated
2. 🚀 **Import V63** to n8n (http://localhost:5678)
3. 🧪 **Test 3 scenarios** (happy path, alt phone, correction)
4. 📊 **Monitor** for 10 conversations
5. ✅ **Deploy** 100% if successful

**Priority**: 🟢 HIGH - Breaks bug cycle, simplifies maintenance

---

**Maintained by**: Claude Code | **Last Review**: 2026-03-10
