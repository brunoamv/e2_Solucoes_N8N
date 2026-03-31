# Quick Start Guide - E2 Bot

> **Time**: ~10 minutes | **Difficulty**: Easy

## Prerequisites

- ✅ Docker + Docker Compose installed
- ✅ Git
- ✅ API Keys ready (see below)

---

## 1. Clone Repository

```bash
git clone <repo-url>
cd e2-solucoes-bot
```

---

## 2. Configure Environment

```bash
# Copy template
cp docker/.env.example docker/.env

# Edit configuration
nano docker/.env
```

### Required API Keys

```bash
# Anthropic (Claude AI)
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx

# Evolution API (WhatsApp)
EVOLUTION_API_URL=https://your-evolution-instance.com
EVOLUTION_API_KEY=your_api_key_here
EVOLUTION_INSTANCE_NAME=e2-solucoes-bot

# Google Services
GOOGLE_SERVICE_ACCOUNT_EMAIL=your-service-account@project.iam.gserviceaccount.com
GOOGLE_CALENDAR_ID=your-calendar-id@group.calendar.google.com

# PostgreSQL
POSTGRES_PASSWORD=SecurePassword123
```

---

## 3. Start Docker Stack

```bash
docker-compose -f docker/docker-compose-dev.yml up -d
```

### Verify Containers

```bash
docker ps --format "table {{.Names}}\t{{.Status}}"
```

Expected output:
```
NAMES                      STATUS
e2bot-n8n-dev             Up X seconds (healthy)
e2bot-evolution-dev       Up X seconds
e2bot-postgres-dev        Up X seconds (healthy)
e2bot-evolution-redis     Up X seconds (healthy)
e2bot-evolution-postgres  Up X seconds
```

---

## 4. Access Services

| Service | URL | Credentials |
|---------|-----|-------------|
| **n8n** | http://localhost:5678 | No auth (dev mode) |
| **Evolution API** | http://localhost:8080 | API key from .env |

---

## 5. Import Workflows

### Option A: Import Production Workflows
```bash
# Access n8n
open http://localhost:5678

# Import workflows (in order):
1. n8n/workflows/01_main_whatsapp_handler_V2.8.3_NO_LOOP.json
2. n8n/workflows/02_ai_agent_conversation_V74.1_2_FUNCIONANDO.json
3. n8n/workflows/05_appointment_scheduler_v3.6.json

# Activate all workflows
```

### Option B: Import Latest (Ready for Deploy)
```bash
# Import ready workflows:
1. 01_main_whatsapp_handler_V2.8.3_NO_LOOP.json
2. 02_ai_agent_conversation_V75_APPOINTMENT_FINAL_MESSAGE.json
3. 05_appointment_scheduler_v4.0.4.json
4. 07_send_email_v6_docker_volume_fix.json  # See WF07 setup below
```

---

## 6. Setup WF07 Email (If Using V6)

**CRITICAL**: WF07 V6 requires Docker volume mount

### Update docker-compose-dev.yml

Edit `docker/docker-compose-dev.yml`, find `n8n-dev` service, add to `volumes`:

```yaml
volumes:
  - n8n_dev_data:/home/node/.n8n
  - ../n8n/workflows:/workflows:ro
  - ../email-templates:/email-templates:ro  # ← ADD THIS LINE
```

### Restart Docker

```bash
docker-compose -f docker/docker-compose-dev.yml down
docker-compose -f docker/docker-compose-dev.yml up -d
```

### Verify Mount

```bash
docker exec e2bot-n8n-dev ls -la /email-templates/
```

Expected: 4 HTML files listed

---

## 7. Connect WhatsApp

### Get QR Code

```bash
# Using helper script
./scripts/evolution-helper.sh qrcode

# Or direct API call
curl -s http://localhost:8080/instance/connect/e2-solucoes-bot \
  -H "apikey: YOUR_API_KEY" | jq -r '.qrcode.base64' | base64 -d > qrcode.png
```

### Scan QR Code

1. Open WhatsApp on your phone
2. Go to: Settings → Linked Devices → Link a Device
3. Scan the QR code from `qrcode.png`

### Verify Connection

```bash
curl -s http://localhost:8080/instance/fetchInstances \
  -H "apikey: YOUR_API_KEY" | jq -r '.[] | .instance.instanceName + ": " + .instance.state'
```

Expected: `e2-solucoes-bot: open`

---

## 8. Test the Bot

### Send Test Message

Send a WhatsApp message to the connected number:
```
Olá
```

### Expected Bot Response

```
Olá! 👋 Bem-vindo à E2 Soluções!

Somos especialistas em Engenharia Elétrica com mais de 15 anos de experiência.

Como posso ajudar você hoje? Por favor, escolha um dos nossos serviços:

1️⃣ Energia Solar
2️⃣ Subestação
3️⃣ Projetos Elétricos
4️⃣ BESS (Armazenamento de Energia)
5️⃣ Análise e Laudos

Envie o número do serviço desejado.
```

### Test Full Flow (Services 1 or 3)

```
1  # Select Solar Energy
```

Bot will collect:
- Name
- Phone (WhatsApp confirmation)
- Email
- City
- Confirmation

If you select appointment → Google Calendar event created → Email sent (if WF07 V6 configured)

---

## 9. Verify Database

```bash
# Check conversations
docker exec -it e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT phone_number, lead_name, service_type, current_state FROM conversations ORDER BY updated_at DESC LIMIT 5;"

# Check appointments (if created)
docker exec -it e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT lead_name, service_type, scheduled_date FROM appointments ORDER BY created_at DESC LIMIT 5;"
```

---

## 10. Monitor Logs

```bash
# n8n logs
docker logs -f e2bot-n8n-dev

# Evolution API logs
docker logs -f e2bot-evolution-dev

# PostgreSQL logs
docker logs -f e2bot-postgres-dev
```

---

## Troubleshooting

### Evolution API "Unhealthy"

**Symptom**: Container shows "unhealthy" but works
**Cause**: Webhook endpoints don't exist yet (n8n workflows not imported)
**Fix**: Import and activate WF01 workflow → status becomes "healthy"

### n8n Container Won't Start

**Symptom**: `KeyError: 'ContainerConfig'`
**Cause**: Corrupted Docker image
**Fix**:
```bash
docker-compose -f docker/docker-compose-dev.yml rm -f n8n-dev
docker rmi -f n8nio/n8n:latest
docker-compose -f docker/docker-compose-dev.yml pull n8n-dev
docker-compose -f docker/docker-compose-dev.yml up -d
```

### WF07 Email Not Sending

**Symptom**: "File not found" or empty template output
**Cause**: Docker volume mount not configured
**Fix**: See step 6 above (Docker volume mount setup)

### Database Connection Error

**Symptom**: n8n can't connect to PostgreSQL
**Cause**: Database not ready or wrong credentials
**Fix**:
```bash
# Check database is running
docker exec e2bot-postgres-dev pg_isready -U postgres -d e2bot_dev

# Verify credentials in .env match docker-compose-dev.yml
```

---

## Next Steps

After successful setup:

1. ✅ Test all 5 service types
2. ✅ Test appointment flow (Services 1 & 3)
3. ✅ Verify email confirmations (if WF07 V6 configured)
4. ✅ Check Google Calendar events
5. 📋 Deploy production version (see `CLAUDE.md`)

---

## Useful Commands

```bash
# Restart all containers
docker-compose -f docker/docker-compose-dev.yml restart

# Stop all containers
docker-compose -f docker/docker-compose-dev.yml down

# View container logs
docker-compose -f docker/docker-compose-dev.yml logs -f

# Check Evolution API instances
curl -s http://localhost:8080/instance/fetchInstances \
  -H "apikey: YOUR_API_KEY" | jq

# Database query
docker exec -it e2bot-postgres-dev psql -U postgres -d e2bot_dev
```

---

## Support

- 📘 **Full Context**: `CLAUDE.md`
- 📚 **Documentation**: `docs/` folder
- 🐛 **Issues**: Check `docs/BUGFIX_*.md` files
- 🚀 **Deploy**: See `docs/DEPLOY_*.md` files

---

**Setup Time**: ~10 minutes
**Status**: Ready to use
**Version**: 4.0 (2026-03-31)
