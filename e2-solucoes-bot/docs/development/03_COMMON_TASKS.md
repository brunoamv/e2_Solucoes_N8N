# Common Development Tasks

> **Tarefas comuns de desenvolvimento** | Atualizado: 2026-04-29
> **Status**: ✅ PRODUCTION - Procedimentos validados em produção

---

## 📖 Visão Geral

Guia prático com step-by-step para tarefas comuns de desenvolvimento baseado em experiência real de 114 versões do WF02.

---

## 🔄 Workflow Version Management

### Creating New Workflow Version

**When**: Sempre que você faz mudanças em workflow de produção

```bash
# Step 1: Export Current Production (Backup)
# n8n UI → Workflows → WF02 AI Agent → ⋮ → Download
# Save as: n8n/workflows/production/wf02/02_ai_agent_conversation_V114_FUNCIONANDO.json

# Step 2: Git Backup Commit
cd /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot
git add n8n/workflows/production/wf02/02_ai_agent_conversation_V114_FUNCIONANDO.json
git commit -m "chore: backup WF02 V114 before V115 deployment"

# Step 3: Create Development Version
# n8n UI → Duplicate workflow → Name: "02_ai_agent_conversation_V115_DEVELOPMENT"
# Make your changes in development version
# Test thoroughly

# Step 4: Export Development Version
# Download V115_DEVELOPMENT → Save to development/wf02/

git add n8n/workflows/development/wf02/02_ai_agent_conversation_V115_DEVELOPMENT.json
git commit -m "feat: WF02 V115 development version with [feature description]"

# Step 5: Promote to Production (when ready)
# See "Deploying to Production" section below
```

**Version Naming Convention**:
```
WFXX_VYY_DESCRIPTION.json

Examples:
- 02_ai_agent_conversation_V114_FUNCIONANDO.json (production)
- 02_ai_agent_conversation_V115_DEVELOPMENT.json (development)
- 02_ai_agent_conversation_V115_NEW_FEATURE.json (feature branch)
```

---

## 📝 Adding New State to State Machine

**When**: Adicionar novo passo ao fluxo de conversa

```bash
# Example: Adding "collect_company" state

# Step 1: Update State Machine Logic
# n8n UI → WF02 → "State Machine Logic" node

# Add state definition:
case 'collect_company':
  const companyInput = message.trim();

  // Validation
  if (companyInput.length < 2) {
    response_text = "⚠️ Por favor, informe o nome da empresa:";
    next_stage = 'collect_company';
    break;
  }

  // Save data
  collectedData.company = companyInput;
  response_text = `✅ Empresa registrada: ${companyInput}\n\n` +
                 "Agora vamos confirmar seus dados...";
  next_stage = 'confirmation';
  break;

# Step 2: Update Previous State to Point to New State
case 'collect_city':
  // ... validation logic ...
  collectedData.city = cityInput;
  response_text = `✅ Cidade registrada: ${cityInput}\n\n` +
                 "Qual é o nome da sua empresa?";
  next_stage = 'collect_company';  // Changed from 'confirmation'
  break;

# Step 3: Update Database (if needed)
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "ALTER TABLE conversations ADD COLUMN IF NOT EXISTS company_name VARCHAR(200);"

# Step 4: Update Build Update Queries (if saving to column)
const updateQuery = `
  UPDATE conversations SET
    -- ... existing columns ...
    company_name = '{{ $json.collected_data.company }}',
    -- ... rest of query ...
`;

# Step 5: Test Complete Flow
# WhatsApp: "oi" → complete → verify company collection works
```

**Checklist**:
- [ ] Add state case in State Machine Logic
- [ ] Update previous state's next_stage
- [ ] Add validation logic for user input
- [ ] Save to collected_data
- [ ] Update database schema (if needed)
- [ ] Update Build Update Queries (if needed)
- [ ] Test happy path and error cases
- [ ] Verify database saves correctly

---

## 🔌 Integrating New External Service

**When**: Adicionar integração com novo serviço externo (ex: SMS, Payment API)

```bash
# Example: Adding SMS notification service

# Step 1: Add HTTP Request Node
# n8n UI → Add Node → HTTP Request
# Name: "HTTP Request - SMS Service"
# Method: POST
# URL: https://api.smsservice.com/send
# Headers:
#   Authorization: Bearer {{ $credentials.smsServiceApiKey }}
#   Content-Type: application/json
# Body:
{
  "to": "{{ $json.phone_number }}",
  "message": "{{ $json.sms_message }}"
}

# Step 2: Add Credentials
# n8n UI → Credentials → Create New Credential
# Type: Header Auth
# Name: SMS Service API Key
# Header Name: Authorization
# Header Value: Bearer YOUR_API_KEY_HERE

# Step 3: Add Trigger State in State Machine
case 'send_sms_confirmation':
  trigger_sms_send = true;
  sms_message = "Seu agendamento foi confirmado!";
  response_text = "📱 Enviando SMS de confirmação...";
  next_stage = 'awaiting_sms_confirmation';
  break;

# Step 4: Add Check If Node
# n8n UI → Add Node → If
# Name: "Check If Send SMS"
# Condition: {{ $json.trigger_sms_send }} = true

# Step 5: Add Merge Node
# n8n UI → Add Node → Merge
# Name: "Merge SMS Response"
# Input 1: Build Update Queries (trigger_sms_send = true)
# Input 2: HTTP Request - SMS Service (response)

# Step 6: Add Awaiting State
case 'awaiting_sms_confirmation':
  const smsData = input.sms_response || {};

  if (smsData.status === 'sent') {
    response_text = "✅ SMS enviado com sucesso!\n\n" +
                   "Você receberá uma confirmação no seu telefone.";
    next_stage = 'completed';
  } else {
    response_text = "⚠️ Erro ao enviar SMS.\n\n" +
                   "Mas não se preocupe, seu agendamento foi confirmado.";
    next_stage = 'completed';
  }
  break;

# Step 7: Connect Workflow Nodes
# Build Update Queries → Check If Send SMS
# Check If Send SMS (TRUE) → HTTP Request - SMS Service
# HTTP Request → Merge SMS Response
# Merge SMS Response → State Machine Logic (2nd execution)
# State Machine Logic → Process SMS result

# Step 8: Test Integration
# Complete flow → Trigger SMS → Verify sent
# Check logs:
docker logs -f e2bot-n8n-dev | grep -i "sms"
```

**Checklist**:
- [ ] Add HTTP Request node with correct endpoint
- [ ] Configure credentials securely
- [ ] Add trigger flag in State Machine
- [ ] Add Check If node for routing
- [ ] Add Merge node for response
- [ ] Add awaiting state to process response
- [ ] Connect workflow nodes correctly
- [ ] Test successful case
- [ ] Test error case (API down)
- [ ] Document integration in comments

---

## 📊 Modifying Database Schema

**When**: Adicionar ou modificar colunas no PostgreSQL

```bash
# Example: Adding "lead_source" column

# Step 1: Create Migration SQL
cat > migrations/001_add_lead_source.sql << 'EOF'
-- Add lead_source column to conversations
ALTER TABLE conversations
ADD COLUMN IF NOT EXISTS lead_source VARCHAR(50);

-- Add index for performance
CREATE INDEX IF NOT EXISTS idx_conversations_lead_source
ON conversations(lead_source);

-- Add comment for documentation
COMMENT ON COLUMN conversations.lead_source IS
'Source of lead: whatsapp, website, referral, etc';
EOF

# Step 2: Apply Migration
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -f /path/to/migrations/001_add_lead_source.sql

# Or inline:
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "ALTER TABLE conversations ADD COLUMN IF NOT EXISTS lead_source VARCHAR(50);"

# Step 3: Verify Schema
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "\d conversations"

# Expected output should include:
# lead_source | character varying(50) |

# Step 4: Update State Machine (if collecting from user)
case 'collect_lead_source':
  const sourceInput = message.trim().toLowerCase();
  const validSources = ['whatsapp', 'website', 'referral', 'facebook'];

  if (!validSources.includes(sourceInput)) {
    response_text = "⚠️ Por favor, escolha uma opção:\n" +
                   validSources.map((s, i) => `${i+1}. ${s}`).join('\n');
    next_stage = 'collect_lead_source';
    break;
  }

  collectedData.lead_source = sourceInput;
  next_stage = 'next_state';
  break;

# Step 5: Update Build Update Queries
const updateQuery = `
  UPDATE conversations SET
    lead_source = '{{ $json.collected_data.lead_source }}',
    -- ... other columns ...
  WHERE phone_number = '{{ $json.phone_number }}'
  RETURNING *;
`.trim();

# Step 6: Git Commit Migration
git add migrations/001_add_lead_source.sql
git commit -m "db: add lead_source column to conversations table

- Added lead_source VARCHAR(50) column
- Added index for query performance
- Updated State Machine to collect source
- Updated Build Update Queries for persistence"

# Step 7: Test End-to-End
# Complete flow → Verify lead_source saved:
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT phone_number, lead_source FROM conversations WHERE phone_number = '556181755748';"
```

**Migration Best Practices**:
- Always use `IF NOT EXISTS` for safety
- Add indexes for frequently queried columns
- Add comments for documentation
- Test on development database first
- Keep migrations in version control
- Never modify existing migrations (create new ones)

---

## 🧪 Testing Workflow Changes Locally

**When**: Antes de deploy para produção

```bash
# Step 1: Clear Test Data
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "DELETE FROM conversations WHERE phone_number = '556181755748';"

# Step 2: Test Happy Path (Complete Flow)
# WhatsApp: "oi"
# Expected: Greeting message with options

# Follow complete flow:
# 1. Service selection
# 2. Name collection
# 3. Phone collection
# 4. Email collection
# 5. State collection
# 6. City collection
# 7. Data confirmation
# 8. WF06 next_dates (if applicable)
# 9. Date selection
# 10. WF06 available_slots
# 11. Slot selection
# 12. Final confirmation

# Step 3: Test Error Cases
# Invalid phone: "123"
# Invalid email: "invalid"
# Invalid service: "99"

# Step 4: Test Race Conditions
# Send 3 rapid messages (< 1 second apart):
# Message 1: "cocal-go"
# Message 2: "1"
# Message 3: "test"

# Expected with V111:
# Message 1: Processed normally
# Message 2-3: "Processando..." (row locked)

# Step 5: Verify Database State
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT * FROM conversations WHERE phone_number = '556181755748';"

# Validation points:
# - state_machine_state correct
# - collected_data complete
# - date_suggestions populated (if WF06 called)
# - slot_suggestions populated (if WF06 called)

# Step 6: Check Appointment Creation
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT * FROM appointments WHERE conversation_id = (
        SELECT id FROM conversations WHERE phone_number = '556181755748'
      );"

# Validation points:
# - Appointment created
# - scheduled_time_start/end are TIME values
# - google_calendar_event_id populated

# Step 7: Check Email Queue
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT * FROM email_queue WHERE conversation_id = (
        SELECT id FROM conversations WHERE phone_number = '556181755748'
      );"

# Validation points:
# - Email queued
# - status = 'sent'
# - sent_at timestamp present

# Step 8: Monitor Logs During Testing
# Terminal 1: n8n logs
docker logs -f e2bot-n8n-dev | grep -E "V115|ERROR"

# Terminal 2: PostgreSQL logs
docker logs -f e2bot-postgres-dev | grep -i "error"

# Terminal 3: Evolution API logs
docker logs -f e2bot-evolution-dev | grep "message.upsert"
```

**Testing Checklist**:
- [ ] Clear test data before starting
- [ ] Test complete happy path
- [ ] Test all validation error cases
- [ ] Test race conditions (rapid messages)
- [ ] Verify database state after each step
- [ ] Check appointment creation
- [ ] Check email queue
- [ ] Monitor logs for errors
- [ ] Test WF06 integration (if applicable)
- [ ] Test rollback if needed

---

## 🚀 Deploying to Production

**When**: Depois de testar mudanças localmente

```bash
# Step 1: Pre-Deployment Checklist
# - All tests passed locally ✅
# - Database migration applied ✅
# - Backup created ✅
# - Documentation updated ✅
# - Rollback plan ready ✅

# Step 2: Backup Current Production
# n8n UI → WF02 V114 → Download
# Save as: n8n/workflows/production/wf02/02_ai_agent_conversation_V114_FUNCIONANDO.json

git add n8n/workflows/production/wf02/02_ai_agent_conversation_V114_FUNCIONANDO.json
git commit -m "chore: backup WF02 V114 before V115 deployment"

# Step 3: Import Development to Production
# n8n UI → Import from file
# Select: n8n/workflows/development/wf02/02_ai_agent_conversation_V115_DEVELOPMENT.json

# Step 4: Rename and Activate
# After import, rename:
# From: "02_ai_agent_conversation_V115_DEVELOPMENT"
# To: "02_ai_agent_conversation_V115_FUNCIONANDO"

# Deactivate V114:
# WF02 V114 → Active toggle → OFF

# Activate V115:
# WF02 V115 → Active toggle → ON

# Step 5: Production Validation (10 minutes)
# Test complete flow in production
# WhatsApp: "oi" → complete flow → verify

# Monitor logs:
docker logs -f e2bot-n8n-dev | grep -E "V115|ERROR"

# Check database:
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT * FROM conversations ORDER BY updated_at DESC LIMIT 1;"

# Step 6: Export Final Production Version
# n8n UI → WF02 V115 → Download
# Save as: n8n/workflows/production/wf02/02_ai_agent_conversation_V115_FUNCIONANDO.json

# Step 7: Move Old to Historical
mv n8n/workflows/production/wf02/02_ai_agent_conversation_V114_FUNCIONANDO.json \
   n8n/workflows/historical/wf02/

# Step 8: Git Commit Production
git add n8n/workflows/production/wf02/02_ai_agent_conversation_V115_FUNCIONANDO.json
git add n8n/workflows/historical/wf02/02_ai_agent_conversation_V114_FUNCIONANDO.json
git commit -m "chore: promote WF02 V115 to production

- V115 deployed to production environment
- V114 moved to historical archive
- Validated with complete flow test
- No errors in 10-minute monitoring period

Features:
- [List new features]

Deployment date: $(date -u +%Y-%m-%d)
Deployed by: $(git config user.name) <$(git config user.email)>"

# Step 9: Update Documentation
# Update CLAUDE.md with new production version
# Update deployment guide if needed
```

**Deployment Checklist**:
- [ ] Pre-deployment validation complete
- [ ] Production backup created
- [ ] Development version imported
- [ ] Workflow renamed correctly
- [ ] Old version deactivated
- [ ] New version activated
- [ ] Production validation (10 min)
- [ ] No errors in monitoring
- [ ] Final version exported
- [ ] Old moved to historical
- [ ] Git commits created
- [ ] Documentation updated

---

## 🔙 Rolling Back to Previous Version

**When**: Problemas críticos encontrados em produção

```bash
# Step 1: Identify Issue
# - Critical bug detected
# - Workflow crashes repeatedly
# - User complaints
# - Data corruption

# Step 2: Deactivate Current Version
# n8n UI → WF02 V115 → Active: OFF

# Step 3: Restore Previous Version
# n8n UI → Import from file
# Select: n8n/workflows/historical/wf02/02_ai_agent_conversation_V114_FUNCIONANDO.json

# Step 4: Activate Previous Version
# After import → Active: ON

# Step 5: Verify Rollback
# Test complete flow
# Monitor logs for 10 minutes
# Check database state

# Step 6: Git Commit Rollback
git commit -m "chore: ROLLBACK WF02 from V115 to V114

Reason: [Detailed reason for rollback]
Issue: [Specific issue encountered]
Impact: [User/system impact]

Rollback date: $(date -u +%Y-%m-%d)
Performed by: $(git config user.name) <$(git config user.email)>"

# Step 7: Document Issue
# Create bug report in docs/fix/wf02/v100-v114/
# Include: root cause, impact, rollback steps, fix plan

# Step 8: Fix Development Version
# Update V115 with fix
# Re-test thoroughly
# Plan re-deployment when ready
```

**Rollback Checklist**:
- [ ] Issue clearly identified
- [ ] Deactivate broken version
- [ ] Import previous version from historical
- [ ] Activate previous version
- [ ] Verify rollback successful
- [ ] Monitor for 10 minutes
- [ ] Git commit with reason
- [ ] Document issue thoroughly
- [ ] Plan fix for development version

---

## 🗄️ Database Maintenance Tasks

### Cleaning Test Data

```bash
# Delete test conversations
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "DELETE FROM conversations WHERE phone_number LIKE '%test%';"

# Delete old incomplete conversations (> 30 days)
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "DELETE FROM conversations
      WHERE state_machine_state != 'completed'
        AND created_at < NOW() - INTERVAL '30 days';"
```

### Backing Up Database

```bash
# Full database backup
docker exec e2bot-postgres-dev pg_dump -U postgres e2bot_dev > backup_$(date +%Y%m%d_%H%M%S).sql

# Compressed backup
docker exec e2bot-postgres-dev pg_dump -U postgres e2bot_dev | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz

# Specific table backup
docker exec e2bot-postgres-dev pg_dump -U postgres -t conversations e2bot_dev > conversations_backup.sql
```

### Restoring Database

```bash
# Restore from backup
docker exec -i e2bot-postgres-dev psql -U postgres -d e2bot_dev < backup_20260429_140000.sql

# Restore from compressed backup
gunzip < backup_20260429_140000.sql.gz | docker exec -i e2bot-postgres-dev psql -U postgres -d e2bot_dev
```

---

## 📋 Quick Reference Commands

```bash
# === WORKFLOW MANAGEMENT ===
# Export workflow
# n8n UI → Workflow → ⋮ → Download

# Import workflow
# n8n UI → Workflows → Import from file

# Activate/Deactivate
# n8n UI → Workflow → Active toggle

# === DATABASE ===
# Check conversation
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT * FROM conversations WHERE phone_number = '556181755748';"

# Clear test data
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "DELETE FROM conversations WHERE phone_number = '556181755748';"

# === LOGS ===
# n8n logs
docker logs -f e2bot-n8n-dev

# PostgreSQL logs
docker logs e2bot-postgres-dev

# Evolution API logs
docker logs e2bot-evolution-dev

# === GIT ===
# Backup commit
git add n8n/workflows/production/wf02/*.json
git commit -m "chore: backup WF02 V114 before V115 deployment"

# Deployment commit
git commit -m "chore: promote WF02 V115 to production"

# Rollback commit
git commit -m "chore: ROLLBACK WF02 from V115 to V114"
```

---

## 🔗 Related Documentation

- **Workflow Modification**: `/docs/development/01_WORKFLOW_MODIFICATION.md`
- **Debugging**: `/docs/development/02_DEBUGGING_GUIDE.md`
- **Deployment Guide**: `/docs/guidelines/06_DEPLOYMENT_GUIDE.md`
- **Testing Guide**: `/docs/guidelines/05_TESTING_VALIDATION.md`
- **Database Patterns**: `/docs/guidelines/03_DATABASE_PATTERNS.md`

---

**Última Atualização**: 2026-04-29
**Baseado em**: 114 deployments de produção do WF02 (V74→V114)
**Status**: ✅ COMPLETO - Procedimentos validados em produção
