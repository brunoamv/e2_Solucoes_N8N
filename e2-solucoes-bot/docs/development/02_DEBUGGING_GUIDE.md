# Debugging Guide - Practical Troubleshooting

> **Guia prático de debugging** | Atualizado: 2026-04-29
> **Status**: ✅ PRODUCTION - Técnicas validadas em 114 versões do WF02

---

## 📖 Visão Geral

Este documento fornece técnicas práticas de debugging validadas durante 114 deployments do WF02, desde problemas simples até race conditions complexas.

### Características Principais

- **Log Analysis**: Como ler e interpretar logs do n8n e PostgreSQL
- **State Inspection**: Verificar estado de conversações no banco de dados
- **Workflow Execution**: Debugging de execuções n8n passo a passo
- **Real Examples**: Problemas reais encontrados e solucionados em V74-V114
- **Tools & Commands**: Comandos prontos para copiar e usar

---

## 🔍 Log Analysis

### 1. n8n Workflow Logs

**Accessing Logs**:
```bash
# Real-time logs (follow mode)
docker logs -f e2bot-n8n-dev

# Last 100 lines
docker logs e2bot-n8n-dev --tail 100

# Filter by error
docker logs e2bot-n8n-dev 2>&1 | grep -E "ERROR|error"

# Filter by workflow execution
docker logs e2bot-n8n-dev | grep -E "Workflow.*executed"

# Filter by version tags (V111, V113, V114)
docker logs e2bot-n8n-dev | grep -E "V111:|V113:|V114:"
```

**Reading Log Patterns**:
```bash
# Example log output:

# ✅ SUCCESSFUL execution
# [timestamp] Workflow "WF02 AI Agent" (ID: 9tG2gR6KBt6nYyHT) executed successfully

# ❌ ERROR execution
# [timestamp] ERROR: Workflow "WF02 AI Agent" execution failed
# [timestamp] Error: Cannot read properties of undefined (reading 'response_text')

# 🔍 STATE MACHINE logs (V110-V114 enhanced logging)
# V110: Current → Next: collect_city → confirmation  # State transition
# V111: DATABASE ROW LOCKING ENABLED  # V111 fix active
# V111: Row locked, returning empty  # Concurrent execution prevented
# V113: Saving date_suggestions: [...]  # WF06 suggestions persisted
# V114: Extracted TIME fields: start=08:00, end=10:00  # V114 fix active
```

**Common Error Patterns**:
```bash
# 1. undefined response_text (V106.1 issue)
Error: Cannot read properties of undefined (reading 'response_text')

# Diagnosis: Send node references wrong data source
# Solution: Check "Send WhatsApp Response" node configuration
# Fix: Use {{ $node["Build Update Queries"].json.response_text }}

# 2. PostgreSQL column doesn't exist (V104.2 issue)
ERROR: column "contact_phone" does not exist

# Diagnosis: Query references non-existent column
# Solution: Review schema with: \d conversations
# Fix: Use correct column names (phone_number, not contact_phone)

# 3. WF06 HTTP Request timeout
ERROR: HTTP Request to WF06 timed out after 10000ms

# Diagnosis: WF06 workflow not responding or crashed
# Solution: Check WF06 workflow status
# Fix: Ensure WF06 is Active and Google Calendar OAuth valid

# 4. Race condition (V111 issue - BEFORE fix)
# Log shows same state processed multiple times rapidly:
# [12:00:00.100] State: collect_city → confirmation
# [12:00:00.250] State: greeting → service_selection  # Stale read!
# [12:00:00.400] State: confirmation → trigger_wf06

# Diagnosis: Multiple executions reading same conversation
# Solution: V111 database row locking
# Fix: Add FOR UPDATE SKIP LOCKED to SELECT query
```

**Version-Specific Logging**:
```bash
# V111 Row Locking logs
docker logs e2bot-n8n-dev | grep "V111:"

# Expected output when working:
# V111: DATABASE ROW LOCKING ENABLED  ✅
# V111: Row locked, returning empty  ✅ (when concurrent execution prevented)

# V113 WF06 Suggestions logs
docker logs e2bot-n8n-dev | grep "V113:"

# Expected output:
# V113: Saving date_suggestions: [{"date":"2026-05-15","formatted":"15/05/2026",...}]
# V113: Saving slot_suggestions: [{"start_time":"08:00","end_time":"10:00",...}]

# V114 TIME Fields logs
docker logs e2bot-n8n-dev | grep "V114:"

# Expected output:
# V114: ✅ CRITICAL FIX - Extracted TIME fields:
# V114:   start_time: 08:00
# V114:   end_time: 10:00
```

---

### 2. PostgreSQL Logs

**Accessing Logs**:
```bash
# PostgreSQL container logs
docker logs e2bot-postgres-dev --tail 100

# Filter by error
docker logs e2bot-postgres-dev 2>&1 | grep -i "error"

# Filter by specific table
docker logs e2bot-postgres-dev | grep "conversations"

# Filter by query type
docker logs e2bot-postgres-dev | grep -E "UPDATE|INSERT|SELECT"
```

**Common PostgreSQL Issues**:
```bash
# 1. Lock timeout (indicates row locking working)
ERROR: could not obtain lock on row in relation "conversations"

# This is EXPECTED when V111 row locking is working correctly!
# Multiple executions trying to access same conversation
# One succeeds, others receive this error → workflow returns empty

# 2. Deadlock detected
ERROR: deadlock detected

# Diagnosis: Two transactions waiting for each other's locks
# Solution: Review transaction logic, ensure proper ordering
# Prevention: Keep transactions short, use consistent lock order

# 3. Constraint violation
ERROR: duplicate key value violates unique constraint "conversations_pkey"

# Diagnosis: Trying to INSERT row with existing primary key
# Solution: Use INSERT...ON CONFLICT instead
# Example from WF01: ON CONFLICT (phone_number) DO UPDATE

# 4. Data type mismatch
ERROR: column "scheduled_time_start" is of type time without time zone but expression is of type text

# Diagnosis: V114 issue - sending string to TIME column
# Solution: Ensure TIME columns receive HH:MM format
# Fix: Extract start_time and end_time from WF06 slots correctly
```

---

### 3. Evolution API Logs

**Accessing Logs**:
```bash
# Evolution API container logs
docker logs e2bot-evolution-dev --tail 100

# Filter by instance
docker logs e2bot-evolution-dev | grep "cocal_go_bot"

# Filter by message events
docker logs e2bot-evolution-dev | grep "message.upsert"

# Filter by errors
docker logs e2bot-evolution-dev 2>&1 | grep -i "error"
```

**Common Evolution API Issues**:
```bash
# 1. Instance disconnected
ERROR: Instance "cocal_go_bot" is not connected

# Diagnosis: WhatsApp connection lost
# Solution: Reconnect instance via Evolution API
curl -X POST http://localhost:8080/instance/connect/cocal_go_bot \
  -H "apikey: ae569043cfa169380c378347f91a1141ea572541d2d1cadbed222db519c8a891"

# 2. Webhook not triggering
# No message.upsert events in logs

# Diagnosis: Webhook URL not configured or incorrect
# Solution: Verify webhook URL:
curl -s http://localhost:8080/instance/fetchInstances \
  -H "apikey: ae569043cfa169380c378347f91a1141ea572541d2d1cadbed222db519c8a891" | jq

# Expected: webhook.url should be http://e2bot-n8n-dev:5678/webhook/whatsapp-message

# 3. Message send failure
ERROR: Failed to send message to 556181755748

# Diagnosis: Invalid phone number format or user blocked bot
# Solution: Verify phone number format (country code + DDD + number)
```

---

## 🗄️ Database State Inspection

### 1. Check Conversation State

**Basic Inspection**:
```bash
# Current conversation state
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT phone_number, state_machine_state, updated_at
      FROM conversations
      WHERE phone_number = '556181755748'
      ORDER BY updated_at DESC
      LIMIT 1;"

# Expected output:
#  phone_number  | state_machine_state |        updated_at
# ---------------+---------------------+---------------------------
#  556181755748  | awaiting_wf06_dates | 2026-04-29 14:30:15.123456
```

**Detailed Inspection**:
```bash
# Full conversation data including collected_data JSONB
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT
        phone_number,
        lead_name,
        service_type,
        state_machine_state,
        current_state,
        collected_data,
        date_suggestions,
        slot_suggestions,
        updated_at
      FROM conversations
      WHERE phone_number = '556181755748'
      ORDER BY updated_at DESC
      LIMIT 1;"
```

**Extract Specific Fields from JSONB**:
```bash
# Extract name, email, city from collected_data
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT
        phone_number,
        collected_data->>'name' as name,
        collected_data->>'email' as email,
        collected_data->>'city' as city,
        collected_data->>'selected_date' as selected_date,
        collected_data->>'selected_slot' as selected_slot
      FROM conversations
      WHERE phone_number = '556181755748';"
```

**Verify V111 Row Locking**:
```bash
# Check if row is locked (run in separate terminal while workflow executing)
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT * FROM pg_locks WHERE relation::regclass::text = 'conversations';"

# If row locked, you'll see lock entries
# This means V111 fix is working correctly!
```

**Verify V113 Suggestions Persistence**:
```bash
# Check date_suggestions and slot_suggestions columns
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT
        phone_number,
        date_suggestions,
        slot_suggestions
      FROM conversations
      WHERE phone_number = '556181755748';"

# Expected after WF06 next_dates:
# date_suggestions: [{"date":"2026-05-15","formatted":"15/05/2026","slot_count":8,...},...]

# Expected after WF06 available_slots:
# slot_suggestions: [{"start_time":"08:00","end_time":"10:00","formatted":"8h às 10h"},...]
```

**Verify V114 TIME Fields**:
```bash
# Check scheduled_time_start and scheduled_time_end
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT
        phone_number,
        collected_data->>'scheduled_time_start' as start_time,
        collected_data->>'scheduled_time_end' as end_time,
        collected_data->>'scheduled_time_display' as display
      FROM conversations
      WHERE phone_number = '556181755748';"

# Expected after slot selection:
# start_time: "08:00"  ✅ (TIME compatible)
# end_time: "10:00"    ✅ (TIME compatible)
# display: "8h às 10h" ✅ (user-friendly format)
```

---

### 2. Check Appointments

**Recent Appointments**:
```bash
# Last 5 appointments
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT
        id,
        lead_name,
        lead_email,
        service_type,
        scheduled_date,
        scheduled_time_start,
        scheduled_time_end,
        google_calendar_event_id,
        created_at
      FROM appointments
      ORDER BY created_at DESC
      LIMIT 5;"
```

**Verify Appointment Creation**:
```bash
# Check if appointment created for specific conversation
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT
        a.id,
        a.lead_name,
        a.scheduled_date,
        a.scheduled_time_start,
        a.scheduled_time_end,
        a.google_calendar_event_id,
        c.phone_number
      FROM appointments a
      JOIN conversations c ON a.conversation_id = c.id
      WHERE c.phone_number = '556181755748'
      ORDER BY a.created_at DESC
      LIMIT 1;"

# Validation points:
# ✅ Row exists (appointment created)
# ✅ scheduled_time_start/end are TIME values (08:00, not "8h")
# ✅ google_calendar_event_id is NOT NULL
# ✅ All data from collected_data copied correctly
```

---

### 3. Check Email Queue

**Recent Emails**:
```bash
# Last 5 emails
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT
        id,
        recipient_email,
        recipient_name,
        subject,
        template_used,
        status,
        sent_at,
        created_at
      FROM email_queue
      ORDER BY created_at DESC
      LIMIT 5;"
```

**Verify Email Sent**:
```bash
# Check email for specific conversation
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT
        e.id,
        e.recipient_email,
        e.template_used,
        e.status,
        e.sent_at,
        c.phone_number
      FROM email_queue e
      JOIN conversations c ON e.conversation_id = c.id
      WHERE c.phone_number = '556181755748'
      ORDER BY e.created_at DESC
      LIMIT 1;"

# Validation points:
# ✅ Row exists (email queued)
# ✅ status = 'sent'
# ✅ sent_at timestamp populated
# ✅ template_used = 'confirmation'
```

---

## 🔧 n8n Workflow Execution Debugging

### 1. Execution History

**Accessing Execution History**:
```bash
# n8n UI
http://localhost:5678/executions

# Filter by workflow
# Select "WF02 AI Agent" from dropdown

# Filter by status
# - Running: Currently executing
# - Success: Completed without errors
# - Error: Failed execution
# - Waiting: Awaiting external trigger (webhook, etc)
```

**Analyzing Failed Execution**:
```bash
# 1. Click on failed execution (red icon)

# 2. Check error message
# Example: "Error in node 'Build Update Queries'"

# 3. Click on failed node (red highlight)

# 4. View error details
# Example:
# {
#   "message": "column \"contact_phone\" does not exist",
#   "name": "QueryFailedError",
#   "query": "UPDATE conversations SET contact_phone = ..."
# }

# 5. Diagnose issue
# - contact_phone column doesn't exist in schema
# - Should use phone_number instead

# 6. Fix and re-run
# - Update query in node
# - Save workflow
# - Click "Retry" on failed execution
```

---

### 2. Node-by-Node Debugging

**Enabling Debug Mode**:
```bash
# n8n UI workflow editor

# 1. Click on specific node to debug

# 2. Execute workflow in test mode
# Click "Execute Workflow" button (top right)

# 3. View node output
# Click node → View "Output" tab

# Example output from "State Machine Logic":
{
  "response_text": "Olá! 👋 Sou a assistente virtual...",
  "next_stage": "service_selection",
  "collected_data": {
    "name": null,
    "phone": "556181755748",
    "email": null
  },
  "trigger_wf06_next_dates": false,
  "trigger_wf06_available_slots": false
}
```

**Common Debugging Techniques**:
```bash
# 1. Add console.log in Function nodes
# In "State Machine Logic" node:
console.log('=== V115 DEBUG ===');
console.log('Phone:', phone);
console.log('Message:', message);
console.log('Current State:', currentState);
console.log('Collected Data:', JSON.stringify(collectedData));
console.log('Next Stage:', next_stage);
console.log('==================');

# View logs:
docker logs -f e2bot-n8n-dev | grep "V115 DEBUG"

# 2. Use Set nodes to inspect data
# Add Set node after problematic node
# Map all fields to inspect structure
# Execute workflow and view Set node output

# 3. Use If nodes to branch on conditions
# Example: Check if collected_data has email
# TRUE branch: Continue normally
# FALSE branch: Add logging or error handling
```

---

### 3. WF06 Integration Debugging

**HTTP Request Debugging**:
```bash
# 1. Check HTTP Request node configuration
# Node: "HTTP Request - WF06 Next Dates"

# Method: POST ✅
# URL: http://e2bot-n8n-dev:5678/webhook/calendar-availability ✅
# Headers: Content-Type: application/json ✅

# Body:
{
  "action": "next_dates",
  "service_type": "energia_solar",
  "count": 3,
  "duration_minutes": 120
}

# Options:
# - Timeout: 10000ms
# - Retry: enabled (max 2 retries)

# 2. Test HTTP Request independently
curl -X POST http://localhost:5678/webhook/calendar-availability \
  -H "Content-Type: application/json" \
  -d '{
    "action": "next_dates",
    "service_type": "energia_solar",
    "count": 3,
    "duration_minutes": 120
  }'

# Expected response:
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

# 3. Check WF06 workflow status
# n8n UI → Workflows → Filter "WF06"
# Verify "Active" toggle is ON ✅

# 4. Check Google Calendar OAuth
# n8n UI → Credentials → Filter "Google"
# Verify "Google Calendar OAuth2" is connected ✅
# If expired: Click "Reconnect" → Authorize
```

**Merge Node Debugging**:
```bash
# 1. Check Merge node configuration
# Node: "Merge WF06 Next Dates"

# Mode: Combine By Position ✅
# Input 1: Build Update Queries output (trigger_wf06_next_dates = true)
# Input 2: HTTP Request output (WF06 response)

# 2. View Merge node output
# Execute workflow → Click Merge node → View Output

# Expected structure:
{
  // From Input 1 (Build Update Queries):
  "phone_number": "556181755748",
  "response_text": "🔄 Buscando próximas datas...",
  "next_stage": "awaiting_wf06_next_dates",
  "collected_data": {...},
  "trigger_wf06_next_dates": true,

  // From Input 2 (HTTP Request):
  "wf06_next_dates": {
    "dates_with_availability": [...]
  }
}

# 3. Verify State Machine receives merged data
# Node: "State Machine Logic" (after Merge)
# Input should contain BOTH original data AND wf06_next_dates

# 4. Check awaiting_wf06_next_dates state
case 'awaiting_wf06_next_dates':
  // Extract WF06 data
  const datesData = input.wf06_next_dates || {};

  console.log('V115: WF06 dates data:', JSON.stringify(datesData));

  if (!datesData.dates_with_availability || datesData.dates_with_availability.length === 0) {
    console.log('V115: ERROR - No dates from WF06');
    // Handle error case
  }
```

---

## 🚨 Common Problems and Solutions

### Problem 1: Infinite Loop After Date Selection

**Symptoms**:
- User selects date (message "1")
- Receives dates again (not time slots)
- Loop continues indefinitely

**Root Cause** (V104-V105):
- State Machine updates state to `process_date_selection`
- But database still has old state `trigger_wf06_next_dates`
- Check If WF06 node routes BEFORE database update
- Result: Workflow re-triggers WF06 next_dates instead of available_slots

**Debugging Steps**:
```bash
# 1. Check workflow execution
# n8n UI → Executions → Find execution after date selection

# 2. Verify node execution order
# Look for sequence:
# Build Update Queries → Check If WF06 Next Dates (TRUE) → HTTP Request ❌

# Should be:
# Build Update Queries → Update Conversation State → Check If WF06 Dates (FALSE)

# 3. Check database state after date selection
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT state_machine_state, collected_data->'current_stage'
      FROM conversations
      WHERE phone_number = '556181755748';"

# Expected: process_date_selection (NOT trigger_wf06_next_dates)
# If still trigger_wf06_next_dates → database not updated before routing

# 4. Verify logs
docker logs e2bot-n8n-dev | grep -E "V110: Current → Next"

# Expected:
# V110: Current → Next: process_date_selection → trigger_wf06_available_slots ✅

# NOT Expected:
# V110: Current → Next: process_date_selection → trigger_wf06_next_dates ❌
```

**Solution** (V105 Fix):
```bash
# Change workflow connections:

# 1. Disconnect: Build Update Queries → Check If WF06 Next Dates
# 2. Connect: Build Update Queries → Update Conversation State
# 3. Connect: Update Conversation State → Check If WF06 Next Dates
# 4. Save workflow

# Result: Database updates BEFORE Check If WF06 routing
```

---

### Problem 2: Race Condition (Rapid Messages)

**Symptoms**:
- User sends messages very quickly (< 1 second apart)
- Workflow processes messages out of order
- WF06 triggers unexpectedly
- State doesn't advance correctly

**Root Cause** (V111):
- Multiple workflow executions start simultaneously
- All read same conversation from database
- Process stale state before commits complete
- Result: Wrong state transitions and WF06 triggers

**Debugging Steps**:
```bash
# 1. Reproduce issue
# Send 3 rapid messages in WhatsApp:
# Message 1: "cocal-go" (city)
# Message 2: "1" (agendar)
# Message 3: "test"

# 2. Check logs for multiple state transitions
docker logs e2bot-n8n-dev | grep -E "V110: Current → Next" | tail -20

# Expected (WITH V111 fix):
# V110: Current → Next: collect_city → confirmation
# V111: Row locked, returning empty  ← Message 2 skipped
# V111: Row locked, returning empty  ← Message 3 skipped

# NOT Expected (WITHOUT V111 fix):
# V110: Current → Next: collect_city → confirmation
# V110: Current → Next: greeting → service_selection  ← Stale read!
# V110: Current → Next: confirmation → trigger_wf06

# 3. Check database locks
# While workflow executing, run:
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT * FROM pg_locks WHERE relation::regclass::text = 'conversations';"

# Expected: Lock entries present (V111 fix working)

# 4. Verify final state
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT state_machine_state FROM conversations WHERE phone_number = '556181755748';"

# Expected: trigger_wf06_next_dates (NOT greeting or service_selection)
```

**Solution** (V111 Fix):
```bash
# Update "Build SQL Queries" node:

# Before:
SELECT * FROM conversations
WHERE phone_number = '{{ $json.phone_number }}'
LIMIT 1;

# After (V111):
SELECT * FROM conversations
WHERE phone_number = '{{ $json.phone_number }}'
LIMIT 1
FOR UPDATE SKIP LOCKED;  ← Prevents race conditions

# Result:
# - First execution: Acquires row lock
# - Second execution: Row locked → returns empty → workflow returns "Processando..."
# - Third execution: Same as second
# - Lock released when first execution commits
```

---

### Problem 3: undefined in WhatsApp Message

**Symptoms**:
- User receives WhatsApp message with "undefined" text
- Problem only on certain routes (WF06 integration)
- Logs show correct response_text but message broken

**Root Cause** (V106.1):
- Send WhatsApp Response node uses `{{ $input.first().json.response_text }}`
- Works for normal flow (input from Build Update Queries)
- Fails for WF06 routes (input from Merge, structure different)
- Result: response_text not found → undefined sent to user

**Debugging Steps**:
```bash
# 1. Check Send node configuration
# n8n UI → "Send WhatsApp Response" node

# Current value:
{{ $input.first().json.response_text }}

# 2. View node input during WF06 route
# Execute workflow → WF06 route → Click "Send WhatsApp Response"
# View Input tab

# Example broken structure:
{
  // Merge node output
  "wf06_next_dates": {...},
  // response_text missing! ❌
}

# 3. Check logs
docker logs e2bot-n8n-dev | grep "response_text"

# Expected in State Machine output:
# response_text: "📅 Datas disponíveis..."

# NOT Expected in Send node:
# response_text: undefined

# 4. Test different routes
# Route 1 (Normal): Service 5 → Confirm → Check message ✅
# Route 2 (WF06 dates): Service 1 → Dates → Check message ❌ undefined
# Route 3 (WF06 slots): Date selected → Slots → Check message ❌ undefined
```

**Solution** (V106.1 Fix):
```bash
# Option 1: Explicit node reference (works for all routes)
# "Send WhatsApp Response" node:
{{ $node["Build Update Queries"].json.response_text }}

# Option 2: Route-specific Send nodes (cleaner)
# Create separate Send nodes for each route:

# "Send Normal Response" (after Build Update Queries):
{{ $input.first().json.response_text }}

# "Send Message with Dates" (after Merge WF06 Next Dates):
{{ $input.first().json.response_text }}  ← From Merge output

# "Send Message with Slots" (after Merge WF06 Slots):
{{ $input.first().json.response_text }}  ← From Merge output

# Route connections accordingly
```

---

## 📚 Debugging Command Reference

### Quick Commands

```bash
# === LOGS ===
# n8n real-time
docker logs -f e2bot-n8n-dev

# PostgreSQL errors
docker logs e2bot-postgres-dev 2>&1 | grep -i "error"

# Evolution API
docker logs e2bot-evolution-dev | grep "message.upsert"

# === DATABASE ===
# Current conversation state
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT * FROM conversations WHERE phone_number = '556181755748';"

# Recent appointments
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT * FROM appointments ORDER BY created_at DESC LIMIT 5;"

# Email queue status
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT * FROM email_queue WHERE status = 'pending' LIMIT 5;"

# === WORKFLOW STATUS ===
# Check all workflows active
curl -s http://localhost:5678/rest/workflows | jq '.data[] | {name, active}'

# === EVOLUTION API ===
# Instance status
curl -s http://localhost:8080/instance/fetchInstances \
  -H "apikey: ae569043cfa169380c378347f91a1141ea572541d2d1cadbed222db519c8a891" | jq
```

---

## 🔗 Related Documentation

- **Testing**: `/docs/guidelines/05_TESTING_VALIDATION.md` (validation strategies)
- **Deployment**: `/docs/guidelines/06_DEPLOYMENT_GUIDE.md` (deployment process)
- **State Machine**: `/docs/guidelines/02_STATE_MACHINE_PATTERNS.md` (state patterns)
- **Database**: `/docs/guidelines/03_DATABASE_PATTERNS.md` (PostgreSQL patterns)
- **n8n Best Practices**: `/docs/guidelines/01_N8N_BEST_PRACTICES.md` (limitations and workarounds)

---

**Última Atualização**: 2026-04-29
**Baseado em**: 114 deployments de produção do WF02 (V74→V114)
**Status**: ✅ COMPLETO - Técnicas de debugging validadas em produção
