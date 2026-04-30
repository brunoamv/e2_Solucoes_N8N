# Testing and Validation Strategies

> **Estratégias de teste e validação** | Atualizado: 2026-04-29
> **Status**: ✅ PRODUCTION - Estratégias validadas em 114 versões do WF02

---

## 📖 Visão Geral

Este documento documenta todas as estratégias de teste manual, validação de workflows, debugging techniques, e procedimentos de quality assurance usados no desenvolvimento do E2 Bot.

### Características Principais

- **Manual Testing**: Testes end-to-end via WhatsApp real
- **Race Condition Testing**: Mensagens rápidas para testar concorrência
- **Database Validation**: Verificação de estado no PostgreSQL
- **Log Analysis**: Debugging via Docker logs
- **Integration Testing**: Validação de comunicação entre workflows
- **Production Validation**: Checklist pré-deployment

---

## 🧪 Manual Testing Procedures

### 1. Complete Flow Test (Happy Path)

**Objetivo**: Validar fluxo completo de greeting até confirmed appointment.

```bash
# Test Steps
1. WhatsApp: "oi"
   Expected: Greeting message com opções 1/2

2. WhatsApp: "1" (agendar)
   Expected: "Por favor, informe seu nome completo:"

3. WhatsApp: "João Silva"
   Expected: "Prazer em conhecê-lo, João! Informe seu telefone:"

4. WhatsApp: "62999999999"
   Expected: "Perfeito! Agora preciso do seu e-mail:"

5. WhatsApp: "joao@email.com"
   Expected: "Ótimo! Qual é o seu estado (UF)?"

6. WhatsApp: "GO"
   Expected: "Perfeito! Agora informe sua cidade:"

7. WhatsApp: "Goiânia"
   Expected: Confirmação dos dados com opções ✅/❌

8. WhatsApp: "sim" (confirmar)
   Expected: "Buscando próximas datas disponíveis... ⏳"

9. Wait for WF06 response
   Expected: 3 dates com número de slots disponíveis

10. WhatsApp: "1" (select first date)
    Expected: "Buscando horários disponíveis... ⏳"

11. Wait for WF06 response
    Expected: Time slots (08:00-10:00, 10:00-12:00, etc)

12. WhatsApp: "1" (select first slot)
    Expected: "✅ AGENDAMENTO CONFIRMADO!" message

# Validation Points
✅ All 15 states traversed correctly
✅ No error messages during flow
✅ WF06 called twice (dates → slots)
✅ Final confirmation message shown
```

### 2. Service Selection Test

**Objetivo**: Validar routing para diferentes serviços.

```bash
# Test Service 1 (Solar) - WF06 Integration
WhatsApp: "oi" → "1" (agendar)
Expected: Complete flow with WF06 calls

# Test Service 2 (Subestação) - Handoff Comercial
WhatsApp: "oi" → "2" (comercial)
Expected: "Perfeito! Vou transferir você..." → handoff message

# Test Service 5 (Análise) - Handoff Comercial
# (Após completar coleta de dados)
WhatsApp: Complete data → "1" (confirmar)
Expected: Handoff to comercial (NOT WF06)
```

### 3. Data Validation Test

**Objetivo**: Validar validação inline de dados.

```bash
# Test Invalid Phone
WhatsApp: "123" (invalid phone)
Expected: "Por favor, informe um telefone válido com DDD."

# Test Invalid Email
WhatsApp: "invalid-email" (no @)
Expected: "Por favor, informe um e-mail válido."

# Test Single Word Name
WhatsApp: "João" (single word)
Expected: "Por favor, informe seu nome completo (nome e sobrenome):"

# Test Invalid Service Selection
WhatsApp: "3" (invalid option at service_selection)
Expected: "Por favor, escolha uma das opções: 1️⃣ - Agendar..."
```

---

## ⚡ Race Condition Testing

### Critical Test: Rapid Messages

**Objetivo**: Validar V111 row locking preventing stale state.

```bash
# Setup: Clear conversation first
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "DELETE FROM conversations WHERE phone_number = '556181755748';"

# Test Rapid Messages (< 1 second apart)
# Send these messages as fast as possible:
Message 1: "cocal-go" (city)
Message 2: "1" (confirmar)
Message 3: "test" (random)

# Expected Behavior (V111 Row Locking):
# - Message 1: Processes normally → UPDATE conversation
# - Message 2: Row locked by Message 1 → Returns empty → "Processando..."
# - Message 3: Row locked → Returns empty → "Processando..."

# Verify in Database:
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT phone_number, state_machine_state, updated_at
      FROM conversations
      WHERE phone_number = '556181755748'
      ORDER BY updated_at DESC LIMIT 1;"

# Expected: state_machine_state = "trigger_wf06_next_dates" (NOT stuck in earlier state)
```

### V111 Validation

```bash
# Check logs for V111 row locking messages
docker logs -f e2bot-n8n-dev 2>&1 | grep "V111:"

# Expected:
# V111: DATABASE ROW LOCKING ENABLED  ✅
# V111: Row locked, returning empty  ✅
```

---

## 🗄️ Database Validation

### 1. Check Conversation State

```sql
-- After each test step, verify database state
SELECT
  phone_number,
  state_machine_state,
  collected_data->>'name' as name,
  collected_data->>'email' as email,
  collected_data->>'city' as city,
  collected_data->>'selected_date' as date,
  collected_data->>'selected_slot' as slot,
  date_suggestions,
  slot_suggestions,
  updated_at
FROM conversations
WHERE phone_number = '556181755748'
ORDER BY updated_at DESC
LIMIT 1;
```

**Validation Points**:
- ✅ state_machine_state matches expected state
- ✅ collected_data contains all entered data
- ✅ date_suggestions populated after WF06 next_dates (V113)
- ✅ slot_suggestions populated after WF06 available_slots (V113)

### 2. Check Appointment Creation

```sql
-- After final confirmation, verify appointment created
SELECT
  a.id,
  a.lead_name,
  a.lead_email,
  a.service_type,
  a.scheduled_date,
  a.scheduled_time_start,     -- V114: Should be TIME (08:00)
  a.scheduled_time_end,       -- V114: Should be TIME (10:00)
  a.google_calendar_event_id,
  a.created_at
FROM appointments a
JOIN conversations c ON a.conversation_id = c.id
WHERE c.phone_number = '556181755748'
ORDER BY a.created_at DESC
LIMIT 1;
```

**Validation Points**:
- ✅ Appointment row created
- ✅ scheduled_time_start/end are valid TIME values (V114)
- ✅ google_calendar_event_id is NOT NULL
- ✅ All collected_data copied correctly

### 3. Check Email Queue

```sql
-- Verify email queued for sending
SELECT
  id,
  recipient_email,
  recipient_name,
  subject,
  template_used,
  status,
  sent_at,
  created_at
FROM email_queue
WHERE recipient_email = 'joao@email.com'
ORDER BY created_at DESC
LIMIT 1;
```

**Validation Points**:
- ✅ Email row created with status 'sent'
- ✅ template_used = 'confirmation'
- ✅ sent_at timestamp populated

---

## 📊 Log Analysis

### 1. n8n Workflow Logs

```bash
# Follow logs in real-time
docker logs -f e2bot-n8n-dev

# Filter by version tags
docker logs -f e2bot-n8n-dev | grep -E "V111:|V113:|V114:"

# Filter by workflow
docker logs -f e2bot-n8n-dev | grep -E "WF02|WF06|WF05|WF07"

# Filter by state
docker logs -f e2bot-n8n-dev | grep "state_machine_state"
```

**Key Log Patterns**:
```
V111: DATABASE ROW LOCKING ENABLED
V113: Saving date_suggestions: [...]
V114: Extracted TIME fields: start=08:00, end=10:00
WF06: Calling calendar availability service
WF05: Creating appointment with Google Calendar
WF07: Sending email via SMTP
```

### 2. PostgreSQL Logs

```bash
# PostgreSQL query logs
docker logs e2bot-postgres-dev | tail -100

# Filter by table
docker logs e2bot-postgres-dev | grep "conversations"
docker logs e2bot-postgres-dev | grep "appointments"
```

### 3. Evolution API Logs

```bash
# Evolution API instance logs
docker logs e2bot-evolution-dev | tail -100

# Filter by message events
docker logs e2bot-evolution-dev | grep "message.upsert"
```

---

## 🔄 Integration Testing

### WF02 ↔ WF06 Integration

```bash
# 1. Test WF06 Independently
curl -X POST http://localhost:5678/webhook/calendar-availability \
  -H "Content-Type: application/json" \
  -d '{
    "action": "next_dates",
    "service_type": "energia_solar",
    "count": 3,
    "duration_minutes": 120
  }'

# Expected Response:
{
  "dates_with_availability": [
    {
      "date": "2026-05-15",
      "formatted": "15/05/2026",
      "slot_count": 8,
      "weekday": "Sexta-feira"
    },
    ...
  ]
}

# 2. Test WF02 → WF06 Integration
# WhatsApp: "oi" → complete → "1" (agendar) → confirm data
# Expected: 3 dates shown with slot counts

# 3. Verify Logs
docker logs -f e2bot-n8n-dev | grep -E "WF02|WF06|HTTP"

# Expected:
# WF02: Calling WF06 next_dates
# WF06: Processing calendar availability request
# WF02: Received WF06 response with 3 dates
```

### WF02 → WF05 Integration

```bash
# 1. Complete appointment flow via WhatsApp
# WhatsApp: "oi" → ... → select date → select slot

# 2. Verify WF05 created appointment
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT * FROM appointments ORDER BY created_at DESC LIMIT 1;"

# 3. Check Google Calendar
# Login to google calendar and verify event created

# 4. Verify Logs
docker logs -f e2bot-n8n-dev | grep "WF05"
# Expected: "WF05: Appointment created successfully"
```

### WF02 → WF07 Integration

```bash
# 1. Complete appointment flow via WhatsApp

# 2. Check email queue
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT * FROM email_queue WHERE status = 'sent' ORDER BY created_at DESC LIMIT 1;"

# 3. Check email inbox
# Login to email and verify confirmation email received

# 4. Verify Logs
docker logs -f e2bot-n8n-dev | grep "WF07"
# Expected: "WF07: Email sent successfully via SMTP"
```

---

## ✅ Production Validation Checklist

### Pre-Deployment Checks

```bash
# 1. Verify All Workflows Active
curl -s http://localhost:5678/rest/workflows \
  -H "X-N8N-API-KEY: your-api-key" | jq '.data[] | {name, active}'

# Expected: All workflows active: true

# 2. Verify Database Schema
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "\d conversations"

# Expected: All columns present (including V113 date_suggestions, slot_suggestions)

# 3. Test Critical Path
# WhatsApp: "oi" → complete flow → verify appointment created
# All steps should complete without errors

# 4. Verify Credentials
# n8n UI → Credentials → Check all credentials connected:
# - Evolution API ✅
# - PostgreSQL ✅
# - Google Calendar OAuth2 ✅
# - SMTP Email ✅

# 5. Check Logs for Errors
docker logs e2bot-n8n-dev 2>&1 | grep -i "error" | tail -20
# Expected: No recent critical errors
```

### Post-Deployment Validation

```bash
# 1. Test Complete Flow (Happy Path)
# See "Complete Flow Test" section above

# 2. Test Race Conditions
# See "Race Condition Testing" section above

# 3. Verify Database State
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT COUNT(*) FROM conversations;"
# Expected: Count increases after test

# 4. Monitor Logs for 10 Minutes
docker logs -f e2bot-n8n-dev | grep -E "ERROR|WARN"
# Expected: No unexpected errors

# 5. Test Rollback Procedure
# Import previous workflow version (e.g., V113)
# Verify system still works
# Re-import V114
```

---

## 🐛 Debugging Techniques

### 1. State Machine Debugging

```javascript
// Add logging to State Machine Logic node
console.log('=== STATE MACHINE DEBUG ===');
console.log('Phone:', phone);
console.log('Message:', message);
console.log('Current State:', currentState);
console.log('Collected Data:', JSON.stringify(collectedData));
console.log('Next Stage:', next_stage);
console.log('===========================');
```

### 2. HTTP Request Debugging

```javascript
// Enable verbose logging in HTTP Request node
{
  "options": {
    "fullResponse": true,  // Get complete response object
    "ignoreResponseCode": true
  }
}

// Log request/response
console.log('HTTP Request:', JSON.stringify(requestBody));
console.log('HTTP Response:', JSON.stringify(response));
```

### 3. Database Query Debugging

```sql
-- Enable query timing
\timing on

-- Explain query execution plan
EXPLAIN ANALYZE
SELECT * FROM conversations
WHERE phone_number = '556181755748'
FOR UPDATE SKIP LOCKED;

-- Check locks
SELECT * FROM pg_locks WHERE relation::regclass::text = 'conversations';
```

### 4. Node Execution Tracking

```javascript
// Add tracking to each critical node
const nodeStart = Date.now();

// ... node logic ...

const nodeEnd = Date.now();
console.log(`Node execution time: ${nodeEnd - nodeStart}ms`);
```

---

## 🔍 Common Issues & Solutions

### Issue 1: Workflow Not Triggered

**Symptoms**:
- WhatsApp message sent, no response

**Debug Steps**:
```bash
# 1. Check Evolution API logs
docker logs e2bot-evolution-dev | grep "message.upsert"

# 2. Check n8n webhook logs
docker logs e2bot-n8n-dev | grep "webhook"

# 3. Verify workflow active
curl http://localhost:5678/rest/workflows | jq '.data[] | select(.name | contains("WF01")) | .active'
```

**Common Causes**:
- Workflow inactive
- Webhook URL incorrect
- Evolution API disconnected

### Issue 2: State Not Advancing

**Symptoms**:
- User stuck in same state, not progressing

**Debug Steps**:
```sql
-- Check current state
SELECT state_machine_state, collected_data
FROM conversations
WHERE phone_number = '556181755748';

-- Check recent updates
SELECT state_machine_state, updated_at
FROM conversations
WHERE phone_number = '556181755748'
ORDER BY updated_at DESC;
```

**Common Causes**:
- Validation logic incorrect
- State not updating in database (V104 bug)
- Row locked by concurrent execution (V111)

### Issue 3: WF06 Not Called

**Symptoms**:
- trigger_wf06_next_dates = true, but no dates shown

**Debug Steps**:
```bash
# Check Check If WF06 node execution
docker logs -f e2bot-n8n-dev | grep "Check If WF06"

# Verify routing order (V105)
# Should be: State Machine → Update State → Check If WF06
```

**Common Causes**:
- V105 routing bug (Update after Check)
- WF06 credential expired (OAuth)
- WF06 timeout

### Issue 4: Appointment Not Created

**Symptoms**:
- Confirmation message shown, but no appointment in database

**Debug Steps**:
```sql
-- Check appointments table
SELECT * FROM appointments ORDER BY created_at DESC LIMIT 5;

-- Check WF05 execution logs
docker logs e2bot-n8n-dev | grep "WF05"
```

**Common Causes**:
- WF05 not triggered (async pattern failure)
- Google Calendar OAuth expired
- V114 TIME field format error

---

## 📚 Referências

### Testing Scripts

- **Complete Test**: `/scripts/testing/test-complete-flow.sh`
- **Race Condition Test**: `/scripts/testing/test-race-conditions.sh`
- **Integration Test**: `/scripts/testing/test-wf06-integration.sh`

### Validation Docs

- **V111 Validation**: `/docs/deployment/wf02/v100-v114/DEPLOY_WF02_V111_DATABASE_ROW_LOCKING.md`
- **V114 Validation**: `/docs/WF02_V114_QUICK_DEPLOY.md`
- **Production Checklist**: `/docs/status/PRODUCTION_V1_DEPLOYMENT.md`

### Debugging Guides

- **Log Analysis**: `/docs/guidelines/01_N8N_BEST_PRACTICES.md` (Debugging section)
- **Database Patterns**: `/docs/guidelines/03_DATABASE_PATTERNS.md` (Troubleshooting section)

---

**Última Atualização**: 2026-04-29
**Versão em Produção**: WF02 V114 com todas as validações implementadas
**Status**: ✅ COMPLETO - Estratégias testadas e validadas em produção
