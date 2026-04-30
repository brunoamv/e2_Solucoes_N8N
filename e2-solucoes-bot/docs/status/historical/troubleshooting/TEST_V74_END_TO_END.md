# TEST V74: End-to-End Validation Guide

> **Date**: 2026-03-24
> **Workflow**: 02_ai_agent_conversation_V74_APPOINTMENT_CONFIRMATION.json
> **Purpose**: Complete testing protocol for V74 scheduling verification logic

---

## 🎯 Test Objectives

1. ✅ Verify "Check If Scheduling" node executes correctly
2. ✅ Confirm WF05 V3.6 triggers when `next_stage === 'scheduling_redirect'`
3. ✅ Validate handoff flow executes for non-scheduling confirmations
4. ✅ Ensure all data fields pass correctly between workflows
5. ✅ Confirm Google Calendar event creation works end-to-end

---

## 📋 Pre-Test Checklist

### Environment Validation
```bash
# 1. Check containers running
docker ps | grep -E "n8n|postgres|evolution"

# Expected: e2bot-n8n-dev, e2bot-postgres-dev, evolution-api running
```

```bash
# 2. Verify Evolution API connected
curl -s http://localhost:8080/instance/fetchInstances \
  -H "apikey: ae569043cfa169380c378347f91a1141ea572541d2d1cadbed222db519c8a891" | jq -r '.[] | "\(.instance.instanceName): \(.instance.state)"'

# Expected: e2-solucoes-bot: open
```

```bash
# 3. Check database connectivity
docker exec -it e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "SELECT COUNT(*) FROM conversations;"

# Expected: Connection successful with row count
```

### Workflow Preparation
1. Access n8n: http://localhost:5678
2. Import V74 workflow:
   - Click "Import from File"
   - Select: `n8n/workflows/02_ai_agent_conversation_V74_APPOINTMENT_CONFIRMATION.json`
   - Import successful message should appear
3. Deactivate V73.5:
   - Find "02 - AI Agent Conversation V73.5"
   - Toggle to inactive (gray)
4. Activate V74:
   - Find "02 - AI Agent Conversation V74"
   - Toggle to active (green)
5. Verify WF05 V3.6 is active:
   - Find "05 - Appointment Scheduler V3.6"
   - Should be active (green)
   - Workflow ID should be: `f6eIJIqfaSs6BSpJ`

---

## 🧪 Test Case 1: Scheduling Confirmation (Service 1 - Energia Solar)

### Goal
Verify that confirming scheduling for service 1 (Energia Solar) triggers WF05 V3.6 and creates Google Calendar event.

### Test Data
- **Service**: 1 (Energia Solar)
- **Name**: Teste V74 Solar
- **Email**: teste-v74-solar@example.com
- **City**: goiania
- **Expected Flow**: greeting → service 1 → collect data → confirm → **Trigger WF05 V3.6**

### Execution Steps

**Step 1**: Send initial greeting
```
WhatsApp: oi
```

**Expected Response**:
```
🌟 Olá! Bem-vindo(a) à *E2 Soluções em Engenharia Elétrica*!

Somos especialistas em:
☀️ Energia Solar
⚡ Subestações
📐 Projetos Elétricos
🔋 BESS
📊 Análise Energética

Como posso ajudá-lo(a) hoje?

1️⃣ Energia Solar
2️⃣ Subestação de Energia
3️⃣ Projetos Elétricos
4️⃣ BESS (Armazenamento)
5️⃣ Análise de Consumo

Digite o número da opção desejada:
```

**Step 2**: Select service
```
WhatsApp: 1
```

**Expected Response**:
```
☀️ *Energia Solar* - Excelente escolha!

Para prosseguir, preciso de algumas informações.

Por favor, me informe seu *nome completo*:
```

**Step 3**: Provide name
```
WhatsApp: Teste V74 Solar
```

**Expected Response**:
```
Olá, *Teste V74 Solar*! 👋

Este número de WhatsApp *(62) XXXX-XXXX* é o melhor para entrarmos em contato?

1️⃣ Sim
2️⃣ Não, vou informar outro
```

**Step 4**: Confirm WhatsApp
```
WhatsApp: 1
```

**Expected Response**:
```
Por favor, informe seu *e-mail* para enviarmos informações detalhadas:

(Ou digite "pular" se preferir não informar)
```

**Step 5**: Provide email
```
WhatsApp: teste-v74-solar@example.com
```

**Expected Response**:
```
Por favor, informe sua *cidade*:
```

**Step 6**: Provide city
```
WhatsApp: goiania
```

**Expected Response**:
```
📋 *Confirmação de Dados*

Nome: *Teste V74 Solar*
WhatsApp: *(62) XXXX-XXXX*
E-mail: *teste-v74-solar@example.com*
Cidade: *goiania*
Serviço: *☀️ Energia Solar*

Os dados estão corretos?

1️⃣ Sim, quero agendar uma visita técnica
2️⃣ Não, quero falar com uma pessoa
```

**Step 7**: Confirm scheduling
```
WhatsApp: 1
```

**Expected Response**:
```
⏰ *Agendamento de Visita Técnica*

Perfeito! Agora vamos agendar sua visita técnica.

Nossa equipe entrará em contato em breve para:
✅ Confirmar melhor data e horário
✅ Esclarecer detalhes técnicos
✅ Preparar documentação necessária

🕐 *Horário de atendimento:*
Segunda a Sexta: 8h às 18h
Sábado: 8h às 12h

📱 *Contato direto:* (62) 3092-2900

_Obrigado por escolher a E2 Soluções!_
```

### Validation Checklist

**n8n Execution Verification**:
1. Access http://localhost:5678/workflow/LS2EakwfZkKyqeb4/executions
2. Find latest execution (should be recent timestamp)
3. Click to expand execution details
4. Verify these nodes executed successfully (green):
   - ✅ State Machine
   - ✅ Build Update Queries
   - ✅ Send WhatsApp Response
   - ✅ Check If Scheduling (TRUE branch taken)
   - ✅ **Trigger Appointment Scheduler** (WF05 V3.6)

**WF05 V3.6 Execution Verification**:
1. Access http://localhost:5678/workflow/f6eIJIqfaSs6BSpJ/executions
2. Find execution triggered by WF02 V74
3. Verify successful execution (green status)
4. Check nodes executed:
   - ✅ Webhook (received data from WF02)
   - ✅ Build Calendar Event Data
   - ✅ Create Google Calendar Event
   - ✅ Insert Appointment (database)
   - ✅ Insert Reminders (database)

**Database Verification**:
```bash
# Check conversation record
docker exec -it e2bot-postgres-dev psql -U postgres -d e2bot_dev -c \
  "SELECT phone_number, lead_name, service_type, current_state, next_stage
   FROM conversations
   WHERE lead_name = 'Teste V74 Solar'
   ORDER BY updated_at DESC LIMIT 1;"
```

**Expected**:
- phone_number: (62) XXXX-XXXX
- lead_name: Teste V74 Solar
- service_type: Energia Solar
- current_state: confirmation
- next_stage: scheduling_redirect

```bash
# Check appointment created
docker exec -it e2bot-postgres-dev psql -U postgres -d e2bot_dev -c \
  "SELECT lead_name, lead_email, service_type, scheduled_date, google_calendar_event_id
   FROM appointments
   WHERE lead_email = 'teste-v74-solar@example.com'
   ORDER BY created_at DESC LIMIT 1;"
```

**Expected**:
- lead_name: Teste V74 Solar
- lead_email: teste-v74-solar@example.com
- service_type: Energia Solar
- scheduled_date: (user-provided date)
- google_calendar_event_id: (non-null value)

**Google Calendar Verification**:
1. Access Google Calendar (calendar configured in WF05)
2. Find event with title containing "Teste V74 Solar" or "Energia Solar"
3. Verify event details:
   - ✅ Date matches scheduled_date
   - ✅ Attendee: teste-v74-solar@example.com
   - ✅ Description includes service details

---

## 🧪 Test Case 2: Scheduling Confirmation (Service 3 - Projetos Elétricos)

### Goal
Verify that service 3 (Projetos Elétricos) also triggers scheduling flow correctly.

### Test Data
- **Service**: 3 (Projetos Elétricos)
- **Name**: Teste V74 Projetos
- **Email**: teste-v74-projetos@example.com
- **City**: anapolis

### Execution Steps

Follow same steps as Test Case 1, but use:
- Step 2: `3` (instead of `1`)
- Step 3: `Teste V74 Projetos`
- Step 5: `teste-v74-projetos@example.com`
- Step 6: `anapolis`

### Validation
Same validation checklist as Test Case 1, but verify:
- service_type: Projetos Elétricos
- WF05 V3.6 executes for service 3

---

## 🧪 Test Case 3: Handoff Flow (Service 2 - Subestação)

### Goal
Verify that non-scheduling services (2, 4, 5) trigger handoff flow instead of scheduling.

### Test Data
- **Service**: 2 (Subestação de Energia)
- **Name**: Teste V74 Handoff
- **Email**: teste-v74-handoff@example.com
- **City**: goiania
- **Expected Flow**: greeting → service 2 → collect data → confirm → **Trigger Human Handoff**

### Execution Steps

**Steps 1-6**: Same as Test Case 1, but use service `2` in Step 2

**Step 7**: Confirm (option 1 - want to proceed)
```
WhatsApp: 1
```

**Expected Response**:
```
👔 *Transferência para Atendimento Comercial*

Entendi! Vou transferir você para nossa equipe comercial.

Eles entrarão em contato em breve para:
✅ Oferecer atendimento personalizado
✅ Elaborar proposta comercial
✅ Esclarecer todas as suas dúvidas

🕐 *Horário de atendimento:*
Segunda a Sexta: 8h às 18h
Sábado: 8h às 12h

📱 *Contato direto:* (62) 3092-2900

_Obrigado por escolher a E2 Soluções!_
```

### Validation Checklist

**n8n Execution Verification**:
1. Verify "Check If Scheduling" node executed FALSE branch
2. Verify "Check If Handoff" node executed TRUE branch
3. Verify "Trigger Human Handoff" executed successfully
4. Verify **Trigger Appointment Scheduler did NOT execute**

**Database Verification**:
```bash
docker exec -it e2bot-postgres-dev psql -U postgres -d e2bot_dev -c \
  "SELECT phone_number, lead_name, service_type, current_state, next_stage
   FROM conversations
   WHERE lead_name = 'Teste V74 Handoff'
   ORDER BY updated_at DESC LIMIT 1;"
```

**Expected**:
- next_stage: handoff_comercial (NOT scheduling_redirect)

```bash
# Verify NO appointment created for handoff flow
docker exec -it e2bot-postgres-dev psql -U postgres -d e2bot_dev -c \
  "SELECT COUNT(*) FROM appointments WHERE lead_email = 'teste-v74-handoff@example.com';"
```

**Expected**: COUNT = 0 (no appointment)

---

## 🧪 Test Case 4: Handoff via Option 2

### Goal
Verify that choosing option 2 in confirmation (talk to person) triggers handoff regardless of service.

### Test Data
- **Service**: 1 (Energia Solar)
- **Name**: Teste V74 Option2
- **Email**: teste-v74-option2@example.com
- **Expected Flow**: confirmation option 2 → **Trigger Human Handoff**

### Execution Steps

**Steps 1-6**: Same as Test Case 1

**Step 7**: Choose option 2
```
WhatsApp: 2
```

**Expected Response**:
```
👔 *Transferência para Atendimento Comercial*
...
```

### Validation
- Verify "Check If Scheduling" executed FALSE branch (because user chose option 2, not 1)
- Verify "Trigger Human Handoff" executed
- Verify NO appointment created

---

## 🔍 Common Issues & Troubleshooting

### Issue 1: "Trigger Appointment Scheduler" Not Executing

**Symptoms**:
- User confirms scheduling (option 1, service 1 or 3)
- "Check If Scheduling" executes but TRUE branch not taken
- WF05 V3.6 never triggers

**Diagnosis**:
```bash
# Check Build Update Queries output
# In n8n execution, inspect "Build Update Queries" node output
# Look for: next_stage field
```

**Expected**: `"next_stage": "scheduling_redirect"`

**Possible Causes**:
1. State Machine not setting `next_stage` correctly
2. Build Update Queries not including `next_stage` in output
3. "Check If Scheduling" condition syntax error

**Solution**:
1. Review State Machine logic for service 1 and 3 + option 1
2. Verify Build Update Queries includes `next_stage: data.next_stage`
3. Check IF condition: `{{ $node["Build Update Queries"].json.next_stage }} === 'scheduling_redirect'`

### Issue 2: WF05 V3.6 Executes but No Google Calendar Event

**Symptoms**:
- WF05 V3.6 executes successfully
- Database records created
- But no Google Calendar event appears

**Diagnosis**:
```bash
# Check WF05 execution logs
# In n8n, view "Create Google Calendar Event" node
# Look for error messages
```

**Possible Causes**:
1. Google Calendar credentials expired
2. Attendees field format incorrect
3. Calendar ID not configured

**Solution**:
1. Reconnect Google Calendar OAuth in WF05
2. Verify attendees is array of strings: `["email@example.com"]`
3. Check Calendar ID in "Create Google Calendar Event" node parameters

### Issue 3: Handoff Flow Not Executing

**Symptoms**:
- User chooses option 2 or service 2/4/5
- "Check If Scheduling" should go FALSE
- But "Check If Handoff" not executing

**Diagnosis**:
Check "Check If Scheduling" node connections in n8n visual editor:
- TRUE branch → Trigger Appointment Scheduler
- FALSE branch → Check If Handoff

**Solution**:
Verify connections in workflow JSON:
```json
"Check If Scheduling": {
  "main": [
    [{"node": "Trigger Appointment Scheduler", "type": "main", "index": 0}],
    [{"node": "Check If Handoff", "type": "main", "index": 0}]
  ]
}
```

### Issue 4: Missing Data Fields in WF05

**Symptoms**:
- WF05 executes
- But missing fields: lead_name, email, city, etc.

**Diagnosis**:
```bash
# Check WF05 Webhook input
# In n8n execution, inspect Webhook node input data
```

**Expected fields**:
- phone_number
- lead_name
- lead_email
- service_type
- city
- service_selected
- triggered_from

**Solution**:
Verify "Trigger Appointment Scheduler" fieldsUi configuration:
```json
"fieldsUi": {
  "values": [
    {"name": "phone_number", "value": "={{ $node['Build Update Queries'].json.phone_number }}"},
    {"name": "lead_name", "value": "={{ $node['Build Update Queries'].json.collected_data.lead_name }}"},
    ...
  ]
}
```

---

## 📊 Success Criteria

**Test Pass Requirements**:
1. ✅ Test Case 1 (Service 1 scheduling): All validations pass
2. ✅ Test Case 2 (Service 3 scheduling): All validations pass
3. ✅ Test Case 3 (Service 2 handoff): All validations pass
4. ✅ Test Case 4 (Option 2 handoff): All validations pass
5. ✅ Google Calendar events created for cases 1 & 2
6. ✅ NO appointments created for cases 3 & 4
7. ✅ All database records correct
8. ✅ No execution errors in n8n logs

**Performance Requirements**:
- Total execution time < 10 seconds per conversation
- No duplicate executions
- No data loss between nodes
- Response time < 3 seconds per WhatsApp message

---

## 🚀 Deployment Approval

After all test cases pass, V74 is ready for production deployment.

**Final Verification**:
```bash
# Test one more complete flow with real phone number
# Monitor for 24 hours in production
# Track execution metrics:
#   - Success rate
#   - Trigger execution rate (scheduling vs handoff)
#   - Google Calendar event creation rate
#   - Average execution time
```

**Rollback Trigger**:
If any critical issue appears:
1. Deactivate V74
2. Activate V73.5
3. Review execution logs
4. Fix issues and re-deploy

---

**Test Guide Version**: 1.0
**Created**: 2026-03-24
**Workflow**: V74_APPOINTMENT_CONFIRMATION
**Status**: Ready for execution
