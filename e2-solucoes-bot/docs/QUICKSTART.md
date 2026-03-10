# E2 Bot - Quick Start Guide

> **Fast Setup** | V63 Ready | Updated: 2026-03-10

---

## 🚀 Quick Setup (5 min)

### 1. Start Services
```bash
cd /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot
docker-compose up -d
```

**Services**:
- n8n: http://localhost:5678
- PostgreSQL: localhost:5432
- Evolution API: http://localhost:8080

### 2. Import Workflows
```bash
# Access n8n
open http://localhost:5678

# Import workflows (in order):
# 1. WF01: n8n/workflows/01_main_whatsapp_handler_V2.8.3_NO_LOOP.json
# 2. WF02: n8n/workflows/02_ai_agent_conversation_V63_COMPLETE_REDESIGN.json
# 3. Activate BOTH workflows
```

### 3. Setup Evolution API
```bash
# Get QR Code
./scripts/evolution-helper.sh evolution_qrcode

# Scan with WhatsApp → Connected ✅
```

### 4. Test Bot
```
WhatsApp → Send "oi" → Bot responds with menu ✅
```

---

## 🎯 Test V63 Flows

### Flow A: Happy Path (WhatsApp Confirmation)
```
User: "oi"
Bot: Menu (5 services)

User: "1" (Solar)
Bot: "Qual é o seu nome completo?"

User: "Bruno Rosa"
Bot: "Vi que você usa (62) 98175-5748 - este é o melhor número?"
     [1-Sim | 2-Não]

User: "1"
Bot: "Qual é o seu e-mail?"

User: "bruno@email.com"
Bot: "Em qual cidade você está?"

User: "Goiânia - GO"
Bot: Shows complete summary with all data
     [sim | não]

User: "sim"
Bot: "Agendamento de Visita Técnica" ✅

# ✅ Verify: No manual phone prompt, direct WhatsApp confirmation
# ✅ Check DB: contact_phone = "62981755748", service_type = "solar"
```

### Flow B: Alternative Phone
```
User: "oi" → "2" (Subestação) → "Maria Silva"
Bot: "Vi que você usa (62) 98175-5748 - este é o melhor número?"

User: "2" (alternative)
Bot: "Qual número prefere para contato?"

User: "(62) 3092-2900"
Bot: "Qual é o seu e-mail?" → continue flow

# ✅ Verify: Alternative phone collected
# ✅ Check DB: contact_phone = "6230922900"
```

### Flow C: Data Correction
```
Complete flow to confirmation → User: "não"
Bot: Shows correction menu (1-Nome, 2-Telefone, 3-Email, 4-Cidade, 5-Serviço)

User: "3" (correct email)
Bot: "Qual é o seu e-mail?"

User: "newemail@test.com"
Bot: Returns to city collection → confirmation with NEW email ✅

# ✅ Verify: Field corrected, other fields preserved
```

---

## 🔧 Essential Commands

### Database Check
```bash
# Check recent conversations
docker exec -it e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT phone_number, lead_name, service_type, contact_phone, current_state FROM conversations ORDER BY updated_at DESC LIMIT 10;"

# Count by state
docker exec -it e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT current_state, COUNT(*) FROM conversations GROUP BY current_state;"
```

### Logs
```bash
# n8n logs (filter V63)
docker logs -f e2bot-n8n-dev | grep -E "V63|State Machine"

# Evolution logs
docker logs -f e2bot-evolution-dev

# PostgreSQL logs
docker logs -f e2bot-postgres-dev
```

### Evolution API
```bash
# Check status
curl -s http://localhost:8080/instance/fetchInstances \
  -H "apikey: ae569043cfa169380c378347f91a1141ea572541d2d1cadbed222db519c8a891" | jq

# Get QR code (if disconnected)
./scripts/evolution-helper.sh evolution_qrcode
```

---

## 🐛 Troubleshooting

### Bot not responding
```bash
# 1. Check workflows are ACTIVE in n8n (http://localhost:5678)
# 2. Check Evolution connected
./scripts/evolution-helper.sh evolution_status

# 3. Check n8n logs for errors
docker logs -f e2bot-n8n-dev | tail -50
```

### Evolution disconnected
```bash
# Reconnect
./scripts/evolution-helper.sh evolution_qrcode
# Scan QR code with WhatsApp → Wait 10s → Test "oi"
```

### Database connection issues
```bash
# Test connection
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "SELECT 1;"

# Check schema
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "\d conversations"

# View recent errors
docker logs e2bot-postgres-dev | tail -20
```

### V63 specific issues
```bash
# Check if State Machine has V63 code
docker logs e2bot-n8n-dev | grep "V63: Current stage"

# If not found, workflow import failed
# Solution: Re-import 02_ai_agent_conversation_V63_COMPLETE_REDESIGN.json
```

---

## 📊 Current Version

**WF01**: V2.8.3 ✅ (atomic duplicate detection)
**WF02**: V63 🚀 (complete flow redesign)

**V63 Key Features**:
- ✅ 8 states (removed collect_phone)
- ✅ 12 templates (optimized from 16)
- ✅ Direct WhatsApp confirmation (no manual phone)
- ✅ ~24% code reduction
- ✅ Validated triggers (scheduling + handoff)

---

## 📚 Documentation

**Main Context**: `CLAUDE.md` (compressed, optimized)
**V63 Plan**: `docs/PLAN/V63_COMPLETE_FLOW_REDESIGN.md`
**V63 Validation**: `docs/PLAN/V63_VALIDATION_REPORT.md`
**Generator Script**: `scripts/generate-workflow-v63-complete-redesign.py`

---

## 🔄 Rollback Plan

```bash
# If V63 has issues, rollback to stable version:

# Option 1: V58.1 (stable, simple templates)
# Deactivate V63 → Activate V58.1
# File: 02_ai_agent_conversation_V58_1_UX_REFACTOR_COMPLETE.json

# Option 2: V62.3 (if V58.1 not available)
# Deactivate V63 → Activate V62.3
# File: 02_ai_agent_conversation_V62_3_THREE_CRITICAL_BUGS_FIX.json
```

---

## 🎯 Next Steps

1. ✅ Import V63 workflows
2. 🧪 Test 3 flows (A, B, C above)
3. 📊 Monitor 10 conversations
4. ✅ Deploy 100% if successful

**Priority**: 🟢 HIGH - Breaks bug cycle, simplifies maintenance

---

**Support**: Check `CLAUDE.md` for complete technical context
**Updated**: 2026-03-10 | **Version**: V63 READY
