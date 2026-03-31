# WF05 Integration - Email Confirmation Setup

> **Version**: 2.0 | **Date**: 2026-03-26 | **Purpose**: Document WF05 → WF07 integration for automatic appointment confirmation emails

---

## 📋 Overview

This document explains how **WF05 V3.6 (Appointment Scheduler)** triggers **WF07 V2.0 (Send Email)** to automatically send appointment confirmation emails after successful Google Calendar event creation.

---

## 🔄 Integration Flow

```
WF02 (AI Agent) → Services 1/3 + Confirm Appointment
    ↓
WF05 V3.6 (Appointment Scheduler)
    ↓
[Create Google Calendar Event] → SUCCESS
    ↓
[Update Appointment] → calendar_success = true
    ↓
[Send Confirmation Email] → Execute Workflow (WF07 V2.0)
    ↓
WF07 V2.0 (Send Email) → Automatic template selection + data mapping
    ↓
[SMTP Send] → confirmacao_agendamento.html → lead_email
```

---

## 📊 WF05 Output Data Structure

**Source Node**: `Build Calendar Event Data` (ID: `build-calendar-event-v2`)

**Available Data** (passed to WF07):

```javascript
{
  // Appointment Information
  appointment_id: "123e4567-e89b-12d3-a456-426614174000",  // UUID
  scheduled_date: "2026-04-25" or "2026-04-25T00:00:00.000Z",  // DATE or ISO string
  scheduled_time_start: "09:00:00",  // TIME
  scheduled_time_end: "11:00:00",    // TIME
  service_type: "Energia Solar",
  notes: "Cliente interessado em sistema residencial",
  status: "confirmado" or "erro_calendario",

  // Lead Information
  lead_id: 123,
  lead_name: "João Silva",
  lead_email: "joao@example.com",
  phone_number: "5562999999999",
  whatsapp_name: "João Silva",

  // Address Information
  address: "Rua Exemplo, 123",
  city: "Goiânia",
  state: "GO",
  zip_code: "74000-000",

  // Calendar Integration
  google_calendar_event_id: "abc123xyz456",  // From Update Appointment node
  calendar_success: true,  // Boolean from Update Appointment node

  // RD Station (optional)
  rdstation_deal_id: "12345"
}
```

---

## 🎯 WF07 V2.0 Automatic Detection

**How WF07 detects WF05 input**:

```javascript
// In "Prepare Email Data" node
const isFromWF05 = !!(input.appointment_id && input.calendar_success !== undefined);

if (isFromWF05) {
  // WF05 trigger detected → automatic configuration
  emailRecipient = input.lead_email;
  emailTemplate = 'confirmacao_agendamento';
  // ... data mapping
} else {
  // Manual trigger → use provided configuration
  emailRecipient = input.to || input.email;
  emailTemplate = input.template || input.email_template;
}
```

**Detection Criteria**:
1. `appointment_id` exists (UUID format)
2. `calendar_success` field is present (boolean)

If both conditions are met → **WF05 integration mode activated**

---

## 🔧 Data Mapping (WF05 → WF07)

### Date/Time Formatting

**WF05 Output** → **WF07 Template Variables**:

```javascript
// 1. Extract date from ISO string (if needed)
let dateString = input.scheduled_date;
if (typeof dateString === 'string' && dateString.includes('T')) {
  dateString = dateString.split('T')[0];  // "2026-04-25"
}

// 2. Format to Brazilian standard (DD/MM/YYYY)
const [year, month, day] = dateString.split('-');
const formattedDate = `${day}/${month}/${year}`;  // "25/04/2026"

// 3. Format time (remove seconds, add "às")
const timeStart = input.scheduled_time_start?.split(':').slice(0, 2).join(':') || '00:00';
const timeEnd = input.scheduled_time_end?.split(':').slice(0, 2).join(':') || '00:00';
const formattedTime = `${timeStart} às ${timeEnd}`;  // "09:00 às 11:00"
```

### Google Calendar Link

```javascript
const googleEventLink = input.google_calendar_event_id
  ? `https://calendar.google.com/calendar/event?eid=${input.google_calendar_event_id}`
  : '';
```

### Complete Template Data Object

```javascript
templateData = {
  // Lead information
  name: input.lead_name || 'Cliente',
  email: input.lead_email,
  phone_number: input.phone_number || '',
  whatsapp_name: input.whatsapp_name || input.lead_name || 'Cliente',

  // Service information
  service_type: input.service_type || 'Serviço',
  city: input.city || '',
  address: input.address || '',
  state: input.state || '',
  zip_code: input.zip_code || '',

  // Appointment information
  scheduled_date: dateString,           // YYYY-MM-DD
  formatted_date: formattedDate,        // DD/MM/YYYY
  formatted_time: formattedTime,        // HH:MM às HH:MM

  // Calendar integration
  google_event_link: googleEventLink,
  google_calendar_event_id: input.google_calendar_event_id || '',

  // Status
  appointment_id: input.appointment_id,
  status: input.status || 'confirmado'
};
```

---

## 📧 Email Template: confirmacao_agendamento.html

**Template Variables** (automatically populated from WF05 data):

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Confirmação de Agendamento - E2 Soluções</title>
</head>
<body>
  <h1>✅ Visita Técnica Agendada</h1>

  <p>Olá, <strong>{{name}}</strong>!</p>

  <p>Sua visita técnica foi confirmada com sucesso!</p>

  <div class="info-box">
    <h3>📋 Detalhes do Agendamento:</h3>
    <p><strong>📅 Data:</strong> {{formatted_date}}</p>
    <p><strong>🕐 Horário:</strong> {{formatted_time}}</p>
    <p><strong>📍 Endereço:</strong> {{address}}, {{city}} - {{state}}</p>
    <p><strong>⚡ Serviço:</strong> {{service_type}}</p>
  </div>

  {{#if google_event_link}}
  <a href="{{google_event_link}}" class="button">
    📅 Adicionar ao Google Calendar
  </a>
  {{/if}}

  <h3>📱 Precisa reagendar?</h3>
  <p>Entre em contato: (62) 3092-2900</p>

  <div class="footer">
    <p><strong>E2 Soluções - Engenharia Elétrica</strong></p>
    <p>Goiânia - GO | www.e2solucoes.com.br</p>
  </div>
</body>
</html>
```

**Variable Mapping**:
- `{{name}}` → `lead_name`
- `{{formatted_date}}` → "25/04/2026" (DD/MM/YYYY)
- `{{formatted_time}}` → "09:00 às 11:00"
- `{{address}}`, `{{city}}`, `{{state}}` → Address components
- `{{service_type}}` → "Energia Solar"
- `{{google_event_link}}` → Calendar event URL (if available)

---

## 🚀 Deployment Steps

### Step 1: Import WF07 V2.0

```bash
# File location
n8n/workflows/07_send_email_v2_wf05_integration.json

# Import in n8n
http://localhost:5678 → Workflows → Import from File
```

### Step 2: Configure SMTP Credentials

**In n8n UI**:
1. Go to: **Credentials → SMTP**
2. Verify configuration:
   - Host: `smtp.gmail.com` (or your SMTP server)
   - Port: `587`
   - User: `e2solucoes.bot@gmail.com`
   - Password: App Password (16 chars, no spaces)
   - From: `E2 Soluções <e2solucoes.bot@gmail.com>`

### Step 3: Verify WF05 Connection

**Check WF05 "Send Confirmation Email" node**:

```javascript
// Node configuration (line 203-217 in WF05 V3.6)
{
  "parameters": {
    "workflowId": "={{ $env.WORKFLOW_ID_EMAIL_CONFIRMATION || '7' }}"
  },
  "name": "Send Confirmation Email",
  "type": "n8n-nodes-base.executeWorkflow",
  "onlyIf": "{{ $json.calendar_success === true }}"
}
```

**Environment Variable** (`.env.dev`):
```bash
WORKFLOW_ID_EMAIL_CONFIRMATION=7  # WF07 ID in n8n
```

### Step 4: Test Integration

**Test Scenario 1**: Service 1 (Energia Solar) + Confirm Appointment

```bash
# 1. Start conversation
User: "oi"
Bot: Menu

# 2. Select service 1
User: "1"
Bot: "Ótimo! Para um orçamento de Energia Solar..."

# 3. Complete data collection
[Provide: name, phone, email, city]

# 4. Confirm appointment
User: "1" (Sim, quero agendar)
[Provide: date, time]
User: "1" (Confirmar agendamento)

# Expected Flow:
WF02 → WF05 → Google Calendar Event Created → WF07 Triggered → Email Sent
```

**Verification**:
```bash
# Check email sent
docker exec -it e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT recipient, subject, status, sent_at FROM email_logs ORDER BY sent_at DESC LIMIT 1;"

# Expected output:
#   recipient   |           subject           | status |        sent_at
# --------------+-----------------------------+--------+------------------------
#  joao@email.com | Confirmação de Agendamento | sent   | 2026-03-26 10:30:00
```

---

## 🔍 Debugging

### Check WF05 Execution

```bash
# In n8n UI
http://localhost:5678/workflow/f6eIJIqfaSs6BSpJ/executions

# Look for:
# 1. "Create Google Calendar Event" → SUCCESS
# 2. "Update Appointment" → calendar_success = true
# 3. "Send Confirmation Email" → Workflow triggered
```

### Check WF07 Execution

```bash
# In n8n UI
http://localhost:5678/workflow/7/executions

# Verify "Prepare Email Data" node output:
{
  "to": "joao@example.com",
  "template": "confirmacao_agendamento",
  "template_data": {
    "name": "João Silva",
    "formatted_date": "25/04/2026",
    "formatted_time": "09:00 às 11:00",
    ...
  },
  "source": "wf05_trigger"  // ← Confirms WF05 detection
}
```

### Common Issues

#### Issue 1: Email not sent

**Symptom**: WF05 success, but no email sent

**Check**:
```bash
# 1. Verify WF07 was triggered
docker logs -f e2bot-n8n-dev | grep -E "Send Confirmation Email|WF07"

# 2. Check calendar_success value
# In WF05 execution → "Update Appointment" node → output
{
  "calendar_success": true  // Must be true
}
```

**Fix**:
- If `calendar_success = false` → Google Calendar creation failed
- Check WF05 "Create Google Calendar Event" node for errors

#### Issue 2: Template variables not replaced

**Symptom**: Email shows `{{name}}` instead of "João Silva"

**Check**:
```bash
# WF07 execution → "Prepare Email Data" node → verify template_data
{
  "template_data": {
    "name": "João Silva",  // ← Must have actual value
    ...
  }
}
```

**Fix**:
- Verify WF05 output includes `lead_name`, `lead_email`, etc.
- Check "Build Calendar Event Data" node in WF05

#### Issue 3: Wrong date/time format

**Symptom**: Email shows "2026-04-25" instead of "25/04/2026"

**Check**:
```javascript
// In WF07 "Prepare Email Data" node → verify formatting logic
const [year, month, day] = dateString.split('-');
const formattedDate = `${day}/${month}/${year}`;  // Must be DD/MM/YYYY
```

**Fix**:
- Ensure WF07 V2.0 is deployed (has automatic formatting)
- Check `formatted_date` value in template_data output

---

## 📊 Success Metrics

**WF05 → WF07 Integration Health**:

```sql
-- Email sent after calendar event creation
SELECT
  DATE(a.created_at) as dia,
  COUNT(DISTINCT a.id) as appointments_created,
  COUNT(DISTINCT e.id) as emails_sent,
  ROUND(100.0 * COUNT(DISTINCT e.id) / COUNT(DISTINCT a.id), 2) as email_rate
FROM appointments a
LEFT JOIN email_logs e ON a.lead_id = e.lead_id
  AND e.template_used = 'confirmacao_agendamento'
  AND e.sent_at BETWEEN a.created_at AND a.created_at + INTERVAL '5 minutes'
WHERE a.status = 'confirmado'
  AND a.created_at >= NOW() - INTERVAL '7 days'
GROUP BY DATE(a.created_at)
ORDER BY dia DESC;

-- Expected: email_rate ≥ 95%
```

**Target Metrics**:
- Email sent within 5 minutes of appointment creation: **≥ 95%**
- Email delivery rate (status = 'sent'): **≥ 98%**
- Template variable replacement: **100%**
- Date/time format correct (DD/MM/YYYY): **100%**

---

## 🔄 Backward Compatibility

**WF07 V2.0 maintains backward compatibility** with manual triggers:

```javascript
// Manual trigger example (still works)
{
  "to": "cliente@email.com",
  "template": "confirmacao_agendamento",
  "template_data": {
    "name": "Manual Test",
    "formatted_date": "26/03/2026",
    "formatted_time": "14:00 às 16:00",
    ...
  }
}
```

**Automatic Detection**: WF07 checks for `appointment_id` and `calendar_success` to distinguish WF05 triggers from manual triggers.

---

## 📋 Checklist

- [ ] WF07 V2.0 imported and activated in n8n
- [ ] SMTP credentials configured and tested
- [ ] `WORKFLOW_ID_EMAIL_CONFIRMATION=7` set in `.env.dev`
- [ ] Test case 1 executed (Service 1 + Confirm)
- [ ] Email received with correct data:
  - [ ] Date in DD/MM/YYYY format
  - [ ] Time in HH:MM às HH:MM format
  - [ ] Google Calendar link present and functional
  - [ ] All template variables replaced (no `{{}}` visible)
- [ ] Email not in spam folder
- [ ] `email_logs` table shows `status = 'sent'`
- [ ] Success metrics ≥ 95% integration rate

---

**Integration Ready!** WF05 V3.6 now automatically triggers WF07 V2.0 to send professional appointment confirmation emails with properly formatted Brazilian dates and Google Calendar integration.
