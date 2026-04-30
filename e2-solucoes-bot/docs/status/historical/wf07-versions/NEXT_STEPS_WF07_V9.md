# NEXT STEPS - WF07 V9 Testing

**Date**: 2026-03-31
**Current Phase**: Phase 3 - Ready to Import and Test

---

## 🎯 Quick Start - Import WF07 V9

### 1. Open n8n UI
```bash
# Option 1: Direct link
open http://localhost:5678

# Option 2: Browser command
google-chrome http://localhost:5678
```

### 2. Import Workflow
1. Click **Workflows** menu (top-left)
2. Click **Import from File**
3. Navigate to: `/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/`
4. Select: **`07_send_email_v9_http_request.json`**
5. Click **Import**

### 3. Verify Import Success
**Expected**:
- ✅ 7 nodes appear on canvas
- ✅ Workflow name: "07 - Send Email V9 (HTTP Request)"
- ✅ Tags: wf05-integration, v9, http-request

**Node List** (left to right):
```
1. Execute Workflow Trigger
2. Prepare Email Data
3. Fetch Template (HTTP) ← Key node using nginx
4. Render Template
5. Send Email (SMTP)
6. Log Email Sent
7. Return Success
```

---

## 🧪 Quick Test - Verify Everything Works

### Test 1: HTTP Request Isolated (2 minutes)

**Purpose**: Verify nginx template fetching works

**Steps**:
1. Click **"Fetch Template (HTTP)"** node
2. Click **"Execute Node"** button
3. Provide test input:
```json
{
  "template_file": "confirmacao_agendamento.html"
}
```

**Expected Output**:
```json
{
  "data": "<!DOCTYPE html>\n<html lang=\"pt-BR\">\n<head>..."
}
```

**Success**: HTML length ~7494 characters, Status 200 OK

---

### Test 2: Complete Email Flow (5 minutes)

**Purpose**: Test end-to-end email sending

**Steps**:
1. Click **"Execute Workflow Trigger"** node
2. Click **"Execute Workflow"** button
3. Provide test data:

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

**Expected Results**:
- ✅ All 7 nodes execute successfully (green checkmarks)
- ✅ Email sent to clima.cocal.2025@gmail.com
- ✅ Database log created

**Verify Email**:
1. Open Gmail: https://mail.google.com
2. Login: clima.cocal.2025@gmail.com
3. Check inbox for: **"Agendamento Confirmado - E2 Soluções"**

**Verify Database**:
```bash
docker exec -it e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT recipient_email, subject, status FROM email_logs ORDER BY sent_at DESC LIMIT 1;"
```

**Expected**:
```
   recipient_email        |              subject              | status
--------------------------+-----------------------------------+--------
 clima.cocal.2025@gmail.com | Agendamento Confirmado - E2 Soluções | sent
```

---

## ✅ Success Criteria

**If all tests pass**:
- [ ] HTTP Request fetches template successfully (Test 1)
- [ ] Template variables replaced correctly
- [ ] Email sent and received in Gmail (Test 2)
- [ ] Database log created with correct data
- [ ] No errors in n8n execution logs

**Proceed to**: Integration testing (WF05 → WF07 trigger)

---

## 🚨 Troubleshooting Quick Reference

### Issue: HTTP Request 404 Not Found

**Check nginx running**:
```bash
docker ps | grep e2bot-templates-dev
# Expected: UP and healthy
```

**Check templates accessible**:
```bash
docker exec e2bot-templates-dev ls -la /usr/share/nginx/html/
# Expected: 5 HTML files listed
```

**Fix if needed**:
```bash
docker restart e2bot-templates-dev
```

---

### Issue: Email Not Sent

**Check SMTP credentials**:
- n8n UI → Credentials → SMTP - E2 Email
- Verify Gmail app password configured

**Check logs**:
```bash
docker logs e2bot-n8n-dev | grep -E "ERROR|email|smtp"
```

---

### Issue: Database Log Not Created

**Check PostgreSQL connection**:
```bash
docker exec -it e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT COUNT(*) FROM email_logs;"
```

**Check n8n credentials**:
- n8n UI → Credentials → PostgreSQL - E2 Bot

---

## 📚 Full Documentation

**Complete Testing Guide**: `docs/TESTING_WF07_V9_HTTP_REQUEST.md`
- Detailed unit tests
- Integration test procedures
- Comprehensive troubleshooting
- Monitoring and logging commands

**Master Implementation Plan**: `docs/PLAN_NGINX_WF07_IMPLEMENTATION.md`
- Phase 1: nginx setup (✅ COMPLETE)
- Phase 2: Workflow generation (✅ COMPLETE)
- Phase 3: Testing procedures (⏳ CURRENT)
- Phase 4: Production deployment (⏳ NEXT)

**Main Context**: `CLAUDE.md`
- Current status and history
- Complete workflow evolution timeline
- All deployment commands

---

## 🎯 After Testing Success

**Next Phase**: Integration Testing (WF05 → WF07)

1. Get WF07 V9 workflow ID from n8n URL
2. Update WF05 "Send Confirmation Email" node
3. Test complete appointment flow via WhatsApp
4. Verify email sent and database updated

**Final Phase**: Production Deployment
- Backup current workflows
- Deploy to production environment
- Monitor for 1 hour
- Document success

---

**Date**: 2026-03-31
**Status**: ✅ **READY TO TEST**
**Phase**: Phase 3 - Import and Unit Testing
**Estimated Time**: 15-30 minutes for complete testing
