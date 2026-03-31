# 🤖 E2 Bot - WhatsApp AI Assistant

> **Prod**: WF01 V2.8.3 | WF02 V74.1.2 | WF05 V3.6
> **Ready**: WF02 V75 | WF05 V4.0.4 | WF07 V6
> **Updated**: 2026-03-31

Bot inteligente WhatsApp com Claude AI para E2 Soluções (Engenharia Elétrica).

---

## ⚡ Quick Start

### Pré-requisitos
- Docker + Docker Compose
- Git
- API Keys: Anthropic, Evolution API, Google Services

### Setup (5 min)
```bash
# Clone
git clone <repo-url>
cd e2-solucoes-bot

# Configure
cp docker/.env.example docker/.env
nano docker/.env  # Add API keys

# Start
docker-compose -f docker/docker-compose-dev.yml up -d

# Access
open http://localhost:5678  # n8n
```

📘 **Full Guide**: See `QUICKSTART.md`

---

## 🎯 Features

**Intelligent Conversation** (8 states):
- 🤖 Claude 3.5 Sonnet NLP
- 💬 Context-aware dialogues
- 🧠 Persistent memory
- 📊 Service-specific data collection

**Services** (5 types):
- ☀️ Solar Energy (residential/commercial/industrial)
- ⚡ Substations (maintenance/construction)
- 📐 Electrical Projects (design/permits)
- 🔋 BESS (battery storage)
- 📊 Analysis & Reports

**Automation**:
- 📅 Google Calendar integration
- ✉️ Automated email confirmations
- 📱 WhatsApp notifications
- 🔄 RD Station CRM sync

---

## 🏗️ Architecture

```
WhatsApp → Evolution API
    ↓
n8n Workflows (3 main)
    ↓
WF01: Handler (deduplication)
    ↓
WF02: AI Agent (8 states, Claude 3.5)
    ↓
WF05: Appointment Scheduler (Google Calendar)
    ↓
WF07: Email Sender (automated confirmations)
    ↓
PostgreSQL + Evolution API DB
```

---

## 📦 Current Status

### Production
- ✅ **WF01 V2.8.3**: WhatsApp handler (dedup via PostgreSQL)
- ✅ **WF02 V74.1.2**: AI agent (8 states, working)
- ✅ **WF05 V3.6**: Appointment scheduler (stable)

### Ready for Deploy
- 🚀 **WF02 V75**: Personalized appointment confirmations
- 🚀 **WF05 V4.0.4**: Email data fix (16 fields → WF07)
- 🚀 **WF07 V6**: Complete email solution (Docker volume fix)

### Recent Fixes
- ✅ Docker n8n container corruption (2026-03-31)
- ✅ Evolution API webhook errors resolved
- ✅ WF07 V2-V6 evolution (all bugs fixed)
- ✅ WF05 timezone, attendees, email data fixes

---

## 📁 Project Structure

```
e2-solucoes-bot/
├── CLAUDE.md                 # Claude Code context (compressed)
├── README.md                 # This file
├── QUICKSTART.md            # Quick setup guide
├── CHANGELOG.md             # Version history
│
├── docker/
│   ├── docker-compose-dev.yml
│   └── .env.example
│
├── database/
│   ├── schema.sql
│   └── appointment_functions.sql
│
├── n8n/workflows/
│   ├── 01_main_whatsapp_handler_V2.8.3_NO_LOOP.json
│   ├── 02_ai_agent_conversation_V74.1_2_FUNCIONANDO.json
│   ├── 02_ai_agent_conversation_V75_APPOINTMENT_FINAL_MESSAGE.json
│   ├── 05_appointment_scheduler_v3.6.json
│   ├── 05_appointment_scheduler_v4.0.4.json
│   └── 07_send_email_v6_docker_volume_fix.json
│
├── email-templates/          # 4 HTML templates
├── scripts/                  # Automation scripts
└── docs/                     # Documentation
    ├── BUGFIX_*.md
    ├── DEPLOY_*.md
    └── Setups/
```

---

## 🚀 Deploy Guide

### WF02 V75
```bash
# 1. Import workflow
http://localhost:5678 → Import → 02_ai_agent_conversation_V75_APPOINTMENT_FINAL_MESSAGE.json

# 2. Test with Service 1 or 3
# Expected: Personalized final message with real appointment data

# 3. Deploy
# Backup V74.1.2 → Deactivate → Activate V75

# Rollback if needed
# Deactivate V75 → Activate V74.1.2
```

### WF05 V4.0.4
```bash
# Import
05_appointment_scheduler_v4.0.4.json

# Test
# Service 1/3 → verify 16 fields passed to WF07
```

### WF07 V6 (CRITICAL - Docker Config Required)
```bash
# 1. Update docker-compose-dev.yml
# Add to n8n-dev volumes:
  - ../email-templates:/email-templates:ro

# 2. Restart Docker
docker-compose -f docker/docker-compose-dev.yml down
docker-compose -f docker/docker-compose-dev.yml up -d

# 3. Verify mount
docker exec e2bot-n8n-dev ls /email-templates/

# 4. Import workflow
07_send_email_v6_docker_volume_fix.json

# 5. Test
# Service 1/3 → verify email sent
```

---

## 🔧 Common Commands

```bash
# Container status
docker ps --format "table {{.Names}}\t{{.Status}}"

# Database check
docker exec -it e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT phone_number, lead_name, service_type, current_state FROM conversations ORDER BY updated_at DESC LIMIT 5;"

# Evolution API status
curl -s http://localhost:8080/instance/fetchInstances \
  -H "apikey: YOUR_API_KEY" | jq

# Logs
docker logs -f e2bot-n8n-dev
docker logs -f e2bot-evolution-dev
```

---

## 🛠️ Stack

| Component | Technology | Version |
|-----------|------------|---------|
| Orchestration | n8n | latest |
| AI | Claude 3.5 Sonnet | 20241022 |
| Database | PostgreSQL | 15 |
| WhatsApp | Evolution API | v2.3.7 |
| Calendar | Google Calendar | API v3 |

---

## 📚 Documentation

**Essential**:
- `CLAUDE.md` - Claude Code context (compressed)
- `QUICKSTART.md` - Quick setup guide
- `CHANGELOG.md` - Version history

**Deploy**:
- `docs/DEPLOY_V75_PRODUCTION.md`
- `docs/BUGFIX_WF05_V4.0.4_EMAIL_DATA_PASSING.md`
- `docs/PLAN_V6_DOCKER_TEMPLATE_ACCESS.md`

**Setup**:
- `docs/Setups/SETUP_EMAIL_WF05_INTEGRATION.md`
- `docker/.env.example`

---

## 🎯 Next Steps

1. ✅ Deploy WF07 V6 (update docker-compose + test)
2. ✅ Deploy WF05 V4.0.4 (test email integration)
3. ✅ Deploy WF02 V75 (test personalized messages)
4. 📋 Production deployment with monitoring

---

## 🤝 Contributing

```bash
# Development
./scripts/start-dev.sh
# Access: http://localhost:5678

# Edit workflows
# Modify JSONs in n8n/workflows/
# Re-import in n8n UI

# Test
# Use test phone numbers
# Verify database updates
```

---

## 📄 License

Proprietary - E2 Soluções

---

**Project**: E2 Soluções WhatsApp Bot
**Maintained**: Claude Code
**Version**: 4.0 (2026-03-31)
