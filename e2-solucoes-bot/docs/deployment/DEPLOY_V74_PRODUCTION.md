# DEPLOY V74: Production Deployment Procedure

> **Date**: 2026-03-24
> **Workflow**: 02_ai_agent_conversation_V74_APPOINTMENT_CONFIRMATION
> **Environment**: Production
> **Risk Level**: Medium (new scheduling logic, triggers external workflow)

---

## 🎯 Deployment Overview

### What's Being Deployed
- **Workflow**: WF02 V74 (AI Agent Conversation with scheduling verification)
- **Key Change**: Add "Check If Scheduling" logic to trigger WF05 V3.6 correctly
- **Impact**: All users confirming service 1 or 3 will trigger appointment scheduler
- **Rollback**: V73.5_WORKFLOW_ID_FIX available as stable fallback

### Critical Dependencies
1. ✅ WF05 V3.6 must be active and working
2. ✅ Google Calendar credentials valid
3. ✅ Database schema up-to-date (appointments + appointment_reminders tables)
4. ✅ Evolution API connected and stable

---

## 📋 Pre-Deployment Checklist

### 1. Environment Health Check
```bash
# Verify all containers running
docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "n8n|postgres|evolution"

# Expected output:
# e2bot-n8n-dev       Up X hours (healthy)
# e2bot-postgres-dev  Up X hours (healthy)
# evolution-api       Up X hours
```

### 2. Dependency Validation
```bash
# Check Evolution API status
curl -s http://localhost:8080/instance/fetchInstances \
  -H "apikey: ae569043cfa169380c378347f91a1141ea572541d2d1cadbed222db519c8a891" | jq -r '.[] | "\(.instance.instanceName): \(.instance.state)"'

# Expected: e2-solucoes-bot: open
```

```bash
# Verify database connectivity
docker exec -it e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "SELECT COUNT(*) FROM conversations;"

# Expected: Connection successful with count
```

```bash
# Check WF05 V3.6 active
# Access http://localhost:5678/workflows
# Find: "05 - Appointment Scheduler V3.6"
# Status: Active (green toggle)
# Workflow ID: f6eIJIqfaSs6BSpJ
```

### 3. Backup Current State
```bash
# Backup database
docker exec -it e2bot-postgres-dev pg_dump -U postgres e2bot_dev > backup_v74_pre_deploy_$(date +%Y%m%d_%H%M%S).sql

# Expected: SQL dump file created
```

```bash
# Export V73.5 workflow (current production)
# Access http://localhost:5678/workflow/LS2EakwfZkKyqeb4
# Click "..." menu → Download
# Save as: backup_WF02_V73.5_$(date +%Y%m%d).json
```

### 4. Test Environment Validation
Ensure all 4 test cases from `TEST_V74_END_TO_END.md` have passed:
- ✅ Test Case 1: Service 1 scheduling → WF05 triggered
- ✅ Test Case 2: Service 3 scheduling → WF05 triggered
- ✅ Test Case 3: Service 2 handoff → handoff flow executed
- ✅ Test Case 4: Option 2 → handoff flow executed

---

## 🚀 Deployment Steps

### Step 1: Schedule Maintenance Window (Optional)
**Recommended**: Deploy during low-traffic period (late night or early morning)

**Notification** (if needed):
```
Subject: E2 Bot Maintenance - Brief Update

We'll be deploying an improvement to our WhatsApp bot's scheduling system.

Time: [Date] [Time] (5-10 minutes)
Impact: Minimal - existing conversations continue normally
New Feature: Improved appointment scheduling flow

Thank you for your patience.
- E2 Soluções Team
```

### Step 2: Import V74 Workflow

**Access n8n**:
```
URL: http://localhost:5678
Navigate to: Workflows
```

**Import Process**:
1. Click "Import from File" button (top right)
2. Select file: `n8n/workflows/02_ai_agent_conversation_V74_APPOINTMENT_CONFIRMATION.json`
3. Click "Import"
4. Wait for confirmation: "Workflow imported successfully"

**Verification**:
- New workflow appears in list: "02 - AI Agent Conversation V74"
- Status: Inactive (gray toggle)
- ID: Will be auto-assigned by n8n

### Step 3: Pre-Activation Verification

**Inspect V74 Workflow**:
1. Click on "02 - AI Agent Conversation V74"
2. Visual verification:
   - ✅ "Check If Scheduling" node exists (IF type)
   - ✅ Connections: Send WhatsApp Response → Check If Scheduling
   - ✅ TRUE branch: Check If Scheduling → Trigger Appointment Scheduler
   - ✅ FALSE branch: Check If Scheduling → Check If Handoff

**Verify Trigger Node Configuration**:
1. Click "Trigger Appointment Scheduler" node
2. Parameters panel:
   - ✅ Workflow: "05 - Appointment Scheduler V3.6"
   - ✅ Workflow ID: `f6eIJIqfaSs6BSpJ`
   - ✅ Input Fields: 7 fields configured (phone_number, lead_name, lead_email, service_type, city, service_selected, triggered_from)

### Step 4: Activate V74

**Deactivation of V73.5**:
1. Find "02 - AI Agent Conversation V73.5" in workflow list
2. Click toggle switch to deactivate (gray)
3. Confirm deactivation

**Activation of V74**:
1. Find "02 - AI Agent Conversation V74" in workflow list
2. Click toggle switch to activate (green)
3. Verify status: Active

**Wait 10 seconds** for n8n to register the activation.

### Step 5: Smoke Test (Quick Validation)

**Quick Test Flow**:
```bash
# Use test phone number or your own
# Send via WhatsApp:

1. "oi"
   → Should receive menu

2. "1" (Energia Solar)
   → Should request name

3. "Deploy Test V74"
   → Should confirm WhatsApp

4. "1" (Yes)
   → Should request email

5. "deploy-test@example.com"
   → Should request city

6. "goiania"
   → Should show confirmation

7. "1" (Sim, quero agendar)
   → Should receive scheduling message
```

**Verification**:
```bash
# Check execution in n8n
# URL: http://localhost:5678/workflow/[V74_ID]/executions
# Latest execution should show:
# ✅ All nodes green
# ✅ "Trigger Appointment Scheduler" executed
# ✅ WF05 V3.6 triggered (check http://localhost:5678/workflow/f6eIJIqfaSs6BSpJ/executions)
```

---

## 📊 Post-Deployment Monitoring

### Immediate Monitoring (First 2 Hours)

**n8n Executions**:
```bash
# Monitor execution logs in real-time
# Access: http://localhost:5678/workflow/[V74_ID]/executions
# Refresh every 5 minutes
# Look for:
#   - Execution status: Success (green)
#   - No error nodes (red)
#   - "Trigger Appointment Scheduler" executing for service 1 & 3
```

**Database Monitoring**:
```bash
# Check conversation flow
docker exec -it e2bot-postgres-dev psql -U postgres -d e2bot_dev -c \
  "SELECT phone_number, lead_name, service_type, current_state, next_stage, updated_at
   FROM conversations
   WHERE updated_at > NOW() - INTERVAL '2 hours'
   ORDER BY updated_at DESC
   LIMIT 10;"
```

```bash
# Check appointment creation rate
docker exec -it e2bot-postgres-dev psql -U postgres -d e2bot_dev -c \
  "SELECT COUNT(*), service_type
   FROM appointments
   WHERE created_at > NOW() - INTERVAL '2 hours'
   GROUP BY service_type;"
```

**Evolution API Health**:
```bash
# Every 30 minutes for first 2 hours
curl -s http://localhost:8080/instance/fetchInstances \
  -H "apikey: ae569043cfa169380c378347f91a1141ea572541d2d1cadbed222db519c8a891" | jq

# Expected: state: "open", status: "active"
```

### Extended Monitoring (First 24 Hours)

**Metrics to Track**:
1. **Execution Success Rate**: Should be >95%
2. **Trigger Execution Rate**: Services 1 & 3 with option 1 should trigger WF05
3. **Google Calendar Event Creation**: Should match appointment records
4. **Response Time**: Average < 3 seconds per message
5. **Error Rate**: Should be <2%

**Query Execution Metrics**:
```bash
# Total conversations in last 24h
docker exec -it e2bot-postgres-dev psql -U postgres -d e2bot_dev -c \
  "SELECT COUNT(*) as total_conversations
   FROM conversations
   WHERE updated_at > NOW() - INTERVAL '24 hours';"
```

```bash
# Scheduling confirmations (next_stage = scheduling_redirect)
docker exec -it e2bot-postgres-dev psql -U postgres -d e2bot_dev -c \
  "SELECT COUNT(*) as scheduling_confirmations,
          COUNT(CASE WHEN service_type = 'Energia Solar' THEN 1 END) as solar,
          COUNT(CASE WHEN service_type = 'Projetos Elétricos' THEN 1 END) as projetos
   FROM conversations
   WHERE next_stage = 'scheduling_redirect'
     AND updated_at > NOW() - INTERVAL '24 hours';"
```

```bash
# Appointments created (should match scheduling confirmations)
docker exec -it e2bot-postgres-dev psql -U postgres -d e2bot_dev -c \
  "SELECT COUNT(*) as appointments_created,
          service_type
   FROM appointments
   WHERE created_at > NOW() - INTERVAL '24 hours'
   GROUP BY service_type;"
```

**Expected**: appointments_created ≈ scheduling_confirmations

```bash
# Handoff executions (option 2 or services 2,4,5)
docker exec -it e2bot-postgres-dev psql -U postgres -d e2bot_dev -c \
  "SELECT COUNT(*) as handoff_executions
   FROM conversations
   WHERE next_stage = 'handoff_comercial'
     AND updated_at > NOW() - INTERVAL '24 hours';"
```

### Google Calendar Validation
```bash
# Every 6 hours for first 24h
# Access Google Calendar (configured in WF05)
# Verify:
#   - Events created match appointment records
#   - Event details correct (date, time, attendees)
#   - No duplicate events
```

---

## 🚨 Rollback Procedure

### Trigger Conditions
Rollback immediately if:
1. **Critical Error Rate >5%**: Multiple execution failures in n8n
2. **WF05 Not Triggering**: "Trigger Appointment Scheduler" not executing for service 1/3
3. **Data Loss**: Conversations not saving to database
4. **Evolution API Down**: WhatsApp disconnection or message failures
5. **Google Calendar Failures**: Events not creating despite appointments in DB

### Rollback Steps

**1. Deactivate V74**:
```
Access: http://localhost:5678/workflows
Find: "02 - AI Agent Conversation V74"
Action: Click toggle to deactivate (gray)
```

**2. Reactivate V73.5**:
```
Find: "02 - AI Agent Conversation V73.5"
Action: Click toggle to activate (green)
```

**3. Verify Rollback**:
```bash
# Send test message via WhatsApp
# Verify V73.5 flow executing correctly
# Check: http://localhost:5678/workflow/[V73.5_ID]/executions
```

**4. Investigate Root Cause**:
```bash
# Export V74 execution logs
# Access: http://localhost:5678/workflow/[V74_ID]/executions
# Click failed execution → Export to analyze

# Check n8n container logs
docker logs -f e2bot-n8n-dev --since 30m | grep -E "ERROR|V74|Trigger"

# Database investigation
docker exec -it e2bot-postgres-dev psql -U postgres -d e2bot_dev -c \
  "SELECT * FROM conversations WHERE updated_at > NOW() - INTERVAL '30 minutes' ORDER BY updated_at DESC LIMIT 5;"
```

**5. Document Issue**:
Create file: `docs/ROLLBACK_V74_[YYYYMMDD].md`
```markdown
# Rollback V74 - [Date]

## Issue Description
[What went wrong]

## Trigger Condition
[What metric/error triggered rollback]

## Execution Logs
[Attach n8n execution screenshots]

## Database State
[Query results showing issue]

## Root Cause Analysis
[Technical analysis of failure]

## Fix Required
[What needs to be fixed before re-deploy]
```

---

## ✅ Success Criteria

### Deployment Success
Deploy considered successful when:
1. ✅ V74 activated without errors
2. ✅ Smoke test passed (all nodes green)
3. ✅ First real conversation completed successfully
4. ✅ No critical errors in first 2 hours
5. ✅ Execution success rate >95% after 24 hours

### Production Readiness
System ready for full production use when:
1. ✅ 24-hour monitoring shows stable performance
2. ✅ Trigger execution rate matches expectations (service 1/3 → WF05)
3. ✅ Google Calendar events creating correctly
4. ✅ No data loss or corruption detected
5. ✅ Response times within SLA (<3 seconds)
6. ✅ Error rate below threshold (<2%)

---

## 📞 Escalation & Support

### Issue Escalation Path

**Level 1 - Monitoring Detection**:
- Automated alerts (if configured)
- Manual monitoring identifies issue
- Check severity against rollback triggers

**Level 2 - Investigation**:
- Review execution logs in n8n
- Check database for data integrity
- Verify external dependencies (Evolution API, Google Calendar)

**Level 3 - Decision**:
- If critical: Execute rollback immediately
- If non-critical: Document issue, monitor closely
- If intermittent: Increase monitoring frequency

**Level 4 - Resolution**:
- Fix root cause in development
- Test fix thoroughly
- Schedule re-deployment

### Contact Information
```
Technical Lead: [Name]
Phone: [Number]
Email: [Email]

DevOps: [Name]
Phone: [Number]
Email: [Email]

Emergency Rollback Authority: [Name]
```

---

## 📝 Post-Deployment Tasks

### After 24 Hours
- ✅ Review all metrics collected
- ✅ Document any anomalies or unexpected behavior
- ✅ Update monitoring thresholds if needed
- ✅ Conduct team retrospective

### After 7 Days
- ✅ Full performance analysis
- ✅ Compare V74 vs V73.5 metrics
- ✅ Identify optimization opportunities
- ✅ Update documentation based on learnings

### After 30 Days
- ✅ Decommission V73.5 (if V74 fully stable)
- ✅ Archive deployment documentation
- ✅ Update production runbook
- ✅ Plan next iteration (V75)

---

## 🔐 Security Checklist

Before deployment:
- ✅ No credentials in workflow JSON
- ✅ Environment variables properly configured
- ✅ OAuth tokens valid (Google Calendar)
- ✅ API keys secure (Evolution API)
- ✅ Database passwords not exposed
- ✅ Webhook endpoints secured

---

## 📊 Deployment Metrics Template

```markdown
# V74 Deployment Metrics - [Date]

## Execution Statistics (24h)
- Total Executions: [count]
- Success Rate: [%]
- Average Execution Time: [seconds]
- Peak Execution Time: [seconds]

## Trigger Performance
- Total Scheduling Confirmations: [count]
  - Service 1 (Solar): [count]
  - Service 3 (Projetos): [count]
- WF05 Trigger Success Rate: [%]
- Google Calendar Event Creation: [count]/[expected]

## Handoff Performance
- Total Handoff Redirects: [count]
  - Via Option 2: [count]
  - Via Services 2/4/5: [count]
- Handoff Success Rate: [%]

## Error Analysis
- Total Errors: [count]
- Error Rate: [%]
- Top Errors:
  1. [Error type]: [count]
  2. [Error type]: [count]

## Performance
- Average Response Time: [ms]
- P95 Response Time: [ms]
- P99 Response Time: [ms]

## Database
- New Conversations: [count]
- Appointments Created: [count]
- Reminders Set: [count]

## Issues Encountered
[List any issues, even minor ones]

## Recommendations
[Any suggestions for optimization or next steps]
```

---

**Deployment Guide Version**: 1.0
**Created**: 2026-03-24
**Workflow**: V74_APPOINTMENT_CONFIRMATION
**Status**: Ready for production deployment
**Approved by**: [Name] - [Date]
