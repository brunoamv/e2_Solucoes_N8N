# E2 Bot - WhatsApp AI Assistant

> **Production-ready WhatsApp automation** | n8n + Claude AI + PostgreSQL + Evolution API | Brazilian Portuguese

Intelligent bot for E2 Soluções handling customer inquiries, appointment scheduling, and automated email confirmations.

---

## 🚀 Quick Start

### Prerequisites
- Docker + Docker Compose
- WhatsApp Business number
- Google Calendar API credentials
- Gmail SMTP account
- Anthropic API key (Claude)

### 1. Clone & Configure
```bash
git clone <repository-url>
cd e2-solucoes-bot
cp docker/.env.example docker/.env
# Edit docker/.env with your credentials
```

### 2. Deploy Infrastructure
```bash
cd docker
docker-compose -f docker-compose-dev.yml up -d
```

### 3. Import Workflows
```bash
# Access n8n at http://localhost:5678
# Import workflows from n8n/workflows/:
# - 01_main_whatsapp_handler_V2.8.3_NO_LOOP.json
# - 02_ai_agent_conversation_V74.1_2_FUNCIONANDO.json
# - 05_appointment_scheduler_v3.6.json
# - 07_send_email_v13_insert_select.json (LATEST ✅)
```

### 4. Connect WhatsApp
```bash
# Generate QR code
curl http://localhost:8080/instance/connect/e2-solucoes-bot \
  -H "apikey: YOUR_API_KEY"
# Scan QR code with WhatsApp
```

---

## 📊 System Architecture

### Flow Overview
```
WhatsApp Message
    ↓
WF01: Main Handler (deduplication)
    ↓
WF02: AI Agent (8-state conversation)
    ↓
    ├─→ WF05: Appointment Scheduler → WF07: Email Confirmation
    └─→ Human Handoff (complex cases)
```

### Workflow Versions (Production)
| ID | Name | Version | Function |
|----|------|---------|----------|
| WF01 | Main Handler | V2.8.3 | Duplicate detection, routing |
| WF02 | AI Agent | V74.1.2 | 8-state conversation flow |
| WF05 | Scheduler | V3.6 | Google Calendar + DB |
| WF07 | Email | V13 ✅ | SMTP + PostgreSQL logging |

### State Machine (WF02)
```
greeting → service_selection → name → phone → email → city → confirmation → trigger_actions
```

**Services**: 1-Solar | 2-Subestação | 3-Projetos | 4-BESS | 5-Análise
**Triggers**: Services 1/3 + confirm → WF05 | Others → Handoff

---

## 🔧 Configuration

### Environment Variables (docker/.env)
```bash
# Evolution API
EVOLUTION_API_KEY=your_evolution_key
EVOLUTION_INSTANCE_NAME=e2-solucoes-bot

# n8n
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=secure_password
N8N_ENCRYPTION_KEY=generate_random_key

# Anthropic (Claude AI)
ANTHROPIC_API_KEY=sk-ant-...

# Google Calendar
GOOGLE_CALENDAR_ID=your_calendar@gmail.com
# Upload credentials JSON via n8n UI

# SMTP (Gmail)
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=app_specific_password
SMTP_FROM=E2 Soluções <your_email@gmail.com>

# Business Hours (Hardcoded in WF05 V7)
WORK_START=08:00
WORK_END=18:00
WORK_DAYS=1,2,3,4,5  # Mon-Fri
```

### Database Schema
```sql
-- Core tables
conversations: phone_number, lead_name, service_type, current_state
appointments: id, lead_email, scheduled_date, google_calendar_event_id
email_logs: recipient_email, template_used, status, sent_at
appointment_reminders: appointment_id, reminder_type, status
```

---

## 📁 Project Structure

```
e2-solucoes-bot/
├── docker/
│   ├── docker-compose-dev.yml    # Infrastructure
│   └── .env                      # Configuration
├── n8n/
│   ├── workflows/                # Production workflows
│   └── email-templates/          # HTML email templates
├── scripts/
│   ├── generate-workflow-*.py    # Workflow generators
│   └── evolution-helper.sh       # WhatsApp management
├── docs/
│   ├── BUGFIX_*.md              # Version evolution
│   ├── DEPLOY_*.md              # Deployment guides
│   └── Setups/                  # Integration guides
├── CLAUDE.md                     # Technical context (compact)
└── README.md                     # This file
```

---

## 🛠️ Common Operations

### Check System Status
```bash
# All containers
docker ps | grep e2bot

# Database conversations
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT phone_number, lead_name, service_type, current_state FROM conversations ORDER BY updated_at DESC LIMIT 5;"

# WhatsApp connection
curl http://localhost:8080/instance/fetchInstances \
  -H "apikey: YOUR_API_KEY" | jq '.[] | .instance.state'
```

### Monitor Workflows
```bash
# n8n logs
docker logs -f e2bot-n8n-dev | grep -E "ERROR|workflow"

# Evolution API logs
docker logs -f e2bot-evolution-dev | grep -E "ERROR|message"
```

### Restart Services
```bash
# Individual service
docker restart e2bot-n8n-dev

# All services
cd docker && docker-compose -f docker-compose-dev.yml restart
```

---

## 📚 Documentation

### Deployment Guides
- **WF02 V75**: `docs/DEPLOY_V75_PRODUCTION.md` - Personalized confirmations
- **WF05 V7**: `docs/DEPLOY_WF05_V7_HARDCODED_FINAL.md` - Business hours fix
- **WF07 V13**: `docs/BUGFIX_WF07_V13_INSERT_SELECT_FIX.md` - Database logging fix ✅

### Technical Analysis
- **n8n Limitations**: `docs/ANALYSIS_N8N_VERSION_UPGRADE_VS_WORKAROUNDS.md`
- **HTTP Request Solution**: `docs/SOLUTION_FINAL_HTTP_REQUEST.md`
- **Email Setup**: `docs/Setups/SETUP_EMAIL_WF05_INTEGRATION.md`

### Evolution Timeline
See `CLAUDE.md` for complete workflow evolution history (V1 → V13).

---

## 🔍 Troubleshooting

### WhatsApp Not Connecting
```bash
# Regenerate QR code
./scripts/evolution-helper.sh evolution_qrcode

# Check instance status
./scripts/evolution-helper.sh evolution_status

# Recreate instance (last resort)
./scripts/evolution-helper.sh evolution_recreate
```

### Workflows Not Executing
```bash
# Check n8n health
curl http://localhost:5678/healthz

# Verify PostgreSQL connection
docker exec e2bot-postgres-dev psql -U postgres -c "\l"

# Check workflow activation
# Access http://localhost:5678 → Workflows → Verify "Active" toggle
```

### Email Not Sending (WF07)
```bash
# Check SMTP credentials in n8n UI
# Verify email templates accessible:
docker exec e2bot-templates-dev ls -la /usr/share/nginx/html/

# Test template fetch:
curl http://localhost/confirmacao_agendamento.html

# Check email_logs table:
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT * FROM email_logs ORDER BY sent_at DESC LIMIT 5;"
```

---

## 🎓 Key Technical Learnings

### n8n Version 2.14.2 Limitations
1. **Environment Variables**: `$env` access blocked in Code nodes and Set expressions
2. **Filesystem**: Read/Write File restricted to `~/.n8n-files` directory
3. **Node.js Modules**: `fs`, `path` blocked in Code nodes
4. **Query Parameters**: `queryReplacement` does NOT resolve `={{ }}` expressions

### Solutions Applied
- **Business Hours**: Hardcoded constants in Code node (WF05 V7)
- **Email Templates**: nginx container + HTTP Request node (WF07 V9+)
- **Database Logging**: INSERT...SELECT pattern with direct expression injection (WF07 V13 ✅)

---

## 🚀 Upcoming Features

### Ready for Testing
- **WF02 V75**: Personalized appointment confirmations with real date/time/location data
- **WF05 V7**: Hardcoded business hours validation (eliminates env var dependency)

### Deployment Order
1. Import WF07 V13 (fixes database logging) ✅
2. Test WF05 V7 (business hours validation)
3. Test WF02 V75 (personalized messages)
4. Production deployment in sequence

---

## 📊 Stack

| Component | Technology | Version |
|-----------|------------|---------|
| Orchestration | n8n | latest |
| AI | Claude 3.5 Sonnet | 20241022 |
| Database | PostgreSQL | 15 |
| WhatsApp | Evolution API | v2.3.7 |
| Calendar | Google Calendar | API v3 |
| Email Templates | nginx | alpine |

---

## 📞 Support

**Technical Context**: See `CLAUDE.md` for detailed workflow specifications and evolution history.

**Project**: E2 Soluções WhatsApp Bot
**Maintained**: Claude Code + Human Review
**Last Update**: 2026-04-01
