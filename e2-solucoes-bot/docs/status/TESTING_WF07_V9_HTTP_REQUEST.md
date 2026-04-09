# TESTING WF07 V9 - HTTP Request + nginx

**Date**: 2026-03-31
**Status**: 🧪 **TESTING GUIDE - PHASE 3**

---

## ✅ Prerequisites (COMPLETE)

- [x] nginx container deployed and healthy (Phase 1)
- [x] All 5 templates accessible via HTTP
- [x] WF07 V9 workflow generated (7 nodes, 11.4 KB)
- [x] JSON validated and ready for import

**nginx Status**:
```
Container: e2bot-templates-dev
Status: UP (healthy)
Templates: 5/5 accessible
URL: http://e2bot-templates-dev/[template_file]
```

---

## 📋 Phase 3: Import and Testing

### 🎯 Test Objectives

1. **HTTP Request Validation**: Verify nginx template fetching works
2. **Template Rendering**: Confirm variable replacement logic
3. **Email Sending**: Test SMTP integration
4. **Database Logging**: Verify email_logs table updates
5. **Integration**: WF05 → WF07 trigger with real appointment data

---

## 🔧 Passo 3.1: Import Workflow to n8n

### Import Instructions

```bash
# 1. Open n8n UI
open http://localhost:5678

# OR
google-chrome http://localhost:5678
```

**Import Steps**:
1. Click **Workflows** menu (top-left)
2. Click **Import from File**
3. Navigate to: `/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/`
4. Select: `07_send_email_v9_http_request.json`
5. Click **Import**

**Verification**:
- ✅ 7 nodes appear on canvas
- ✅ Workflow name: "07 - Send Email V9 (HTTP Request)"
- ✅ Tags: wf05-integration, v9, http-request

**Node List** (left to right):
```
1. Execute Workflow Trigger [250, 300]
2. Prepare Email Data [450, 300]
3. Fetch Template (HTTP) [650, 300]
4. Render Template [850, 300]
5. Send Email (SMTP) [1050, 300]
6. Log Email Sent [1250, 300]
7. Return Success [1450, 300]
```

---

## 🧪 Passo 3.2: Unit Test 1 - HTTP Request Isolated

**Objective**: Verify nginx template fetching without full workflow

### Test Configuration

1. Click on **"Fetch Template (HTTP)"** node
2. Click **"Execute Node"** button (top-right)
3. Provide test input data:

```json
{
  "template_file": "confirmacao_agendamento.html"
}
```

### Expected Results

**Success Indicators**:
- ✅ Status: `200 OK`
- ✅ Output: `{ data: "<!DOCTYPE html>..." }`
- ✅ HTML length: ~7494 characters
- ✅ Contains: `<title>Agendamento Confirmado</title>`

**Output Example**:
```json
{
  "data": "<!DOCTYPE html>\n<html lang=\"pt-BR\">\n<head>\n    <meta charset=\"UTF-8\">\n    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n    <title>Agendamento Confirmado - E2 Soluções</title>..."
}
```

### Validation Commands (from terminal)

```bash
# Verify template accessible from nginx
docker exec e2bot-templates-dev wget -q -O - \
  http://localhost/confirmacao_agendamento.html | wc -l

# Expected: 231 lines

# Check n8n logs during test
docker logs -f e2bot-n8n-dev | grep -E "HTTP Request|Fetch Template"
```

### ❌ Troubleshooting

**Issue**: HTTP Request returns 404 Not Found

**Solution**:
```bash
# Verify nginx container running
docker ps | grep e2bot-templates-dev

# Verify templates mounted
docker exec e2bot-templates-dev ls -la /usr/share/nginx/html/

# Expected output:
# confirmacao_agendamento.html
# lembrete_2h.html
# lembrete_24h.html
# novo_lead.html
# apos_visita.html
```

**Issue**: HTTP Request timeout

**Solution**:
```bash
# Check network connectivity
docker exec e2bot-n8n-dev ping e2bot-templates-dev

# Verify containers in same network
docker network inspect e2bot-dev-network
```

---

## 🧪 Passo 3.3: Unit Test 2 - Render Template

**Objective**: Verify template variable replacement logic

### Test Configuration

1. Execute workflow until **"Render Template"** node
2. Use this test input data:

```json
{
  "to": "clima.cocal.2025@gmail.com",
  "template": "confirmacao_agendamento",
  "template_file": "confirmacao_agendamento.html",
  "subject": "Agendamento Confirmado - E2 Soluções",
  "template_data": {
    "name": "João Silva",
    "email": "clima.cocal.2025@gmail.com",
    "phone_number": "62999887766",
    "service_type": "Energia Solar",
    "city": "Goiânia",
    "scheduled_date": "2026-04-05",
    "formatted_date": "05/04/2026",
    "formatted_time": "14:00 às 15:00",
    "google_event_link": "https://calendar.google.com/calendar/event?eid=abc123",
    "appointment_id": "TEST123"
  },
  "from_email": "contato@e2solucoes.com.br",
  "from_name": "E2 Soluções",
  "reply_to": "contato@e2solucoes.com.br"
}
```

### Expected Results

**Success Indicators**:
- ✅ `html_body` contains rendered HTML (>7000 chars)
- ✅ Variables replaced: `{{name}}` → `João Silva`
- ✅ Variables replaced: `{{service_type}}` → `Energia Solar`
- ✅ Variables replaced: `{{formatted_date}}` → `05/04/2026`
- ✅ `text_body` generated (plain text, no HTML tags)
- ✅ `text_body` length >500 chars

**Validation Checklist**:
```javascript
// html_body should NOT contain:
"{{name}}"          // ❌ Unreplaced variable
"{{service_type}}"  // ❌ Unreplaced variable

// html_body SHOULD contain:
"João Silva"        // ✅ Replaced name
"Energia Solar"     // ✅ Replaced service
"05/04/2026"        // ✅ Replaced date
"14:00 às 15:00"    // ✅ Replaced time
```

### Logs Monitoring

```bash
# Watch n8n logs during render
docker logs -f e2bot-n8n-dev | grep -E "Render Template|V9"

# Expected log output:
# 📝 [Render Template V9] Template data received: { has_template_html: true, template_length: 7494 }
# ✅ [Render V9] Template rendered successfully: { html_length: 7494, text_length: 567 }
```

---

## 🧪 Passo 3.4: Unit Test 3 - Email Completo (Manual)

**Objective**: Test complete email sending flow without WF05 integration

### Test Configuration

1. Click **"Execute Workflow Trigger"** node
2. Click **"Execute Workflow"** button
3. Provide complete test data:

```json
{
  "appointment_id": "TEST_V9_001",
  "lead_email": "clima.cocal.2025@gmail.com",
  "lead_name": "João Silva (Teste V9)",
  "service_type": "energia_solar",
  "phone_number": "62999887766",
  "whatsapp_name": "João Silva",
  "city": "Goiânia",
  "address": "Rua Teste 123",
  "state": "GO",
  "zip_code": "74000-000",
  "scheduled_date": "2026-04-05",
  "scheduled_time_start": "14:00:00",
  "scheduled_time_end": "15:00:00",
  "google_calendar_event_id": "test_abc123",
  "status": "confirmado",
  "calendar_success": true
}
```

### Expected Results

**Success Indicators**:
- ✅ All 7 nodes execute successfully (green checkmarks)
- ✅ Email sent to `clima.cocal.2025@gmail.com`
- ✅ Database log created in `email_logs` table
- ✅ Return Success node output: `{ success: true, message: "Email sent successfully", ... }`

**Email Verification**:
1. Open Gmail: https://mail.google.com
2. Login: clima.cocal.2025@gmail.com
3. Check inbox for: **"Agendamento Confirmado - E2 Soluções"**

**Expected Email Content**:
- Subject: "Agendamento Confirmado - E2 Soluções"
- From: "E2 Soluções <contato@e2solucoes.com.br>"
- To: "clima.cocal.2025@gmail.com"
- Body contains:
  - "João Silva (Teste V9)"
  - "Energia Solar" (formatted from energia_solar)
  - "05/04/2026"
  - "14:00 às 15:00"
  - Google Calendar link

---

## 🧪 Passo 3.5: Database Verification

### Check Email Log Created

```bash
docker exec -it e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT recipient_email, recipient_name, subject, template_used, status, sent_at FROM email_logs ORDER BY sent_at DESC LIMIT 1;"
```

**Expected Output**:
```
   recipient_email        | recipient_name          |              subject              |    template_used        | status |         sent_at
--------------------------+-------------------------+-----------------------------------+-------------------------+--------+-------------------------
 clima.cocal.2025@gmail.com | João Silva (Teste V9) | Agendamento Confirmado - E2 Soluções | confirmacao_agendamento | sent   | 2026-03-31 14:30:45.123
```

### Check Metadata JSON

```bash
docker exec -it e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT metadata FROM email_logs ORDER BY sent_at DESC LIMIT 1;"
```

**Expected Output** (formatted JSON):
```json
{
  "template_data": {
    "name": "João Silva (Teste V9)",
    "email": "clima.cocal.2025@gmail.com",
    "phone_number": "62999887766",
    "service_type": "Energia Solar",
    "city": "Goiânia",
    "scheduled_date": "2026-04-05",
    "formatted_date": "05/04/2026",
    "formatted_time": "14:00 às 15:00",
    "google_event_link": "https://calendar.google.com/calendar/event?eid=test_abc123",
    "appointment_id": "TEST_V9_001"
  }
}
```

---

## 🧪 Passo 3.6: Integration Test - WF05 → WF07

**Objective**: Test complete appointment flow triggering email

### Prerequisites

1. Get WF07 V9 workflow ID from n8n URL
2. Update WF05 "Send Confirmation Email" node with new workflow ID

### WF07 V9 Workflow ID Discovery

```bash
# Method 1: From n8n UI URL
# After opening WF07 V9, URL will be:
# http://localhost:5678/workflow/[WORKFLOW_ID]
# Example: http://localhost:5678/workflow/abc123def456

# Method 2: From PostgreSQL (if needed)
docker exec -it e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT id, name FROM workflows WHERE name LIKE '%Send Email V9%';"
```

### Update WF05 Configuration

1. Open WF05 workflow in n8n
2. Find **"Send Confirmation Email"** node (Execute Workflow)
3. Update **"Workflow ID"** field to WF07 V9 ID
4. Save WF05 workflow

### Integration Test Execution

**Option 1: Simulate via WhatsApp** (recommended)
```
1. Send WhatsApp message to E2 bot
2. Complete conversation flow:
   - Service: 1 (Energia Solar) or 3 (Projetos Elétricos)
   - Name: João Silva Teste V9
   - Phone: 62999887766
   - Email: clima.cocal.2025@gmail.com
   - City: Goiânia
   - Confirmation: sim
3. Verify email received in Gmail
```

**Option 2: Manual WF05 Execution**
```
1. Open WF05 in n8n
2. Click "Execute Workflow"
3. Provide complete test data (see Passo 3.4)
4. Verify WF07 triggered automatically
5. Check email and database log
```

### Expected Flow

```
WF01 (Handler)
  → WF02 (AI Agent - collect data)
    → WF05 (Appointment Scheduler)
      → Google Calendar (create event)
      → PostgreSQL (save appointment)
      → **WF07 V9 (Send Email via HTTP Request + nginx)** ← NEW
        → Fetch template from nginx
        → Render with appointment data
        → Send email via SMTP
        → Log to database
```

### Success Criteria

- ✅ WF05 executes successfully
- ✅ Google Calendar event created
- ✅ Appointment saved to database
- ✅ WF07 V9 triggered automatically
- ✅ Email sent and received
- ✅ Email log created in database
- ✅ No errors in n8n execution logs

---

## 📊 Monitoring and Logs

### Real-Time Monitoring

```bash
# Watch all n8n logs
docker logs -f e2bot-n8n-dev

# Filter V9-specific logs
docker logs -f e2bot-n8n-dev | grep -E "V9|HTTP Request|Render Template|Fetch Template"

# Watch email-related logs
docker logs -f e2bot-n8n-dev | grep -E "email|smtp|send"

# Watch database logs
docker logs -f e2bot-postgres-dev | grep -E "email_logs|INSERT"
```

### Error Detection

```bash
# Check for errors in last 100 lines
docker logs e2bot-n8n-dev --tail 100 | grep -E "ERROR|error|fail|Error"

# Check nginx access logs
docker logs e2bot-templates-dev --tail 50

# Expected nginx logs:
# 172.x.x.x - - [31/Mar/2026:14:30:45 +0000] "GET /confirmacao_agendamento.html HTTP/1.1" 200 7494
```

---

## ✅ Test Completion Checklist

### Unit Tests
- [ ] HTTP Request isolated test passed
- [ ] Template rendering test passed
- [ ] Email sending test passed
- [ ] Database logging test passed

### Integration Tests
- [ ] WF05 → WF07 trigger works
- [ ] Complete appointment flow tested
- [ ] Email received in Gmail
- [ ] Database logs verified

### Quality Validation
- [ ] No errors in n8n logs
- [ ] nginx healthy and responsive
- [ ] All 5 templates accessible
- [ ] Variable replacement works correctly
- [ ] SMTP credentials validated
- [ ] PostgreSQL connections stable

---

## 🚀 Next Steps After Testing

### If All Tests Pass ✅

1. **Proceed to Phase 4**: Production Deployment
2. **Update WF05 Production**: Point to WF07 V9 workflow ID
3. **Monitor Production**: Watch logs for 1 hour
4. **Document Success**: Update CLAUDE.md with production status

### If Tests Fail ❌

1. **Analyze Logs**: Check n8n, nginx, PostgreSQL logs
2. **Debug Issue**: Identify root cause
3. **Fix and Retry**: Apply fix and re-test
4. **Document Issue**: Add to troubleshooting section

---

## 📋 Troubleshooting Guide

### Issue: HTTP Request 404 Not Found

**Symptoms**:
- Node "Fetch Template (HTTP)" fails with 404
- nginx container running but template not found

**Diagnosis**:
```bash
# Check template exists
docker exec e2bot-templates-dev ls -la /usr/share/nginx/html/

# Test direct access
docker exec e2bot-templates-dev wget -q -O - \
  http://localhost/confirmacao_agendamento.html | wc -l
```

**Fix**:
```bash
# Restart nginx if needed
docker restart e2bot-templates-dev

# Verify mount point
docker inspect e2bot-templates-dev | grep -A 10 Mounts
```

### Issue: Template Variables Not Replaced

**Symptoms**:
- Email contains `{{name}}` instead of actual name
- Template rendering incomplete

**Diagnosis**:
```bash
# Check Render Template node logs
docker logs e2bot-n8n-dev | grep "Render Template"

# Verify input data structure
# template_data should be an object with all variables
```

**Fix**:
- Verify "Prepare Email Data" node output structure
- Ensure `template_data` object contains all required fields
- Check JavaScript regex patterns in Render Template node

### Issue: Email Not Sent

**Symptoms**:
- "Send Email (SMTP)" node fails
- No email received in Gmail

**Diagnosis**:
```bash
# Check SMTP credentials
# n8n UI → Credentials → SMTP - E2 Email

# Test SMTP connection
docker exec e2bot-n8n-dev telnet smtp.gmail.com 587
```

**Fix**:
- Verify SMTP credentials are correct
- Check Gmail app password (not regular password)
- Verify `from_email` and `to` fields populated correctly

### Issue: Database Log Not Created

**Symptoms**:
- Email sent but no entry in `email_logs` table
- "Log Email Sent" node fails

**Diagnosis**:
```bash
# Check PostgreSQL connection
docker exec -it e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT COUNT(*) FROM email_logs;"

# Check credentials
# n8n UI → Credentials → PostgreSQL - E2 Bot
```

**Fix**:
- Verify PostgreSQL credentials in n8n
- Check database connection from n8n container
- Verify `email_logs` table exists and has correct schema

---

## 📚 Reference Documentation

**Implementation Plan**: `docs/PLAN_NGINX_WF07_IMPLEMENTATION.md`
**Version Analysis**: `docs/ANALYSIS_N8N_VERSION_UPGRADE_VS_WORKAROUNDS.md`
**HTTP Solution**: `docs/SOLUTION_FINAL_HTTP_REQUEST.md`
**Main Context**: `CLAUDE.md`

**Generated Files**:
- Workflow: `n8n/workflows/07_send_email_v9_http_request.json`
- Generator: `scripts/generate-workflow-wf07-v9-http-request.py`

---

**Date**: 2026-03-31
**Status**: ✅ **TESTING GUIDE READY**
**Phase**: Phase 3 (Import + Testing)
**Next**: Import WF07 V9 → Unit Tests → Integration Tests → Production
