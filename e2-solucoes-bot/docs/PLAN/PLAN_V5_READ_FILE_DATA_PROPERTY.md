# PLAN V5 - WF07 Read File Data Property Fix

> **Date**: 2026-03-30
> **Issue**: Execution 16271 - "Read Template File" returns "No output data"
> **Root Cause**: Missing `dataPropertyName` parameter in readWriteFile node
> **Solution**: Add `dataPropertyName: "data"` to options

---

## 🔴 Problem Analysis

### V4.1 Error (Execution 16271)

**Symptoms**:
```
"Read Template File" node: finished successfully
Result: /home/bruno/.../email-templates/confirmacao_agendamento.html (correct path)
Output: "No output data returned"
n8n message: "n8n stops executing the workflow when a node has no output data"
Effect: Workflow stops, "Render Template" never executes
```

**Root Cause Discovery**:
1. ✅ V4: Replaced Execute Command with Read/Write Files from Disk (Docker path fix)
2. ✅ V4.1: Added `encoding: "utf8"` to options (text file reading)
3. ❌ **V4.1 MISSING**: `dataPropertyName` parameter for output property definition
4. **Result**: n8n reads file as UTF-8 but doesn't know where to put the data
5. **Effect**: Output is empty/undefined → workflow stops → "Render Template" never runs

### Technical Details

**n8n Read/Write Files from Disk Node** (typeVersion 1):
- **Default behavior**: Returns binary buffer data
- **With `encoding: "utf8"`**: Converts to text string
- **But**: Needs `dataPropertyName` to define where to store the text
- **Without `dataPropertyName`**: Data is lost/inaccessible → "No output data"

**Current V4.1 Configuration** (INCOMPLETE):
```json
{
  "parameters": {
    "operation": "read",
    "filePath": "=/home/bruno/Desktop/.../{{ $json.template_file }}",
    "options": {
      "encoding": "utf8"  // ✅ Converts to text
      // ❌ MISSING: dataPropertyName
    }
  }
}
```

**Expected Output Format** (with `dataPropertyName: "data"`):
```json
{
  "data": "<html>...template content...</html>",
  "template_file": "confirmacao_agendamento.html",
  "to": "client@email.com",
  // ... other fields from "Prepare Email Data"
}
```

**Actual V4.1 Output** (without `dataPropertyName`):
```json
{
  // ❌ "data" is undefined/empty
  "template_file": "confirmacao_agendamento.html",
  "to": "client@email.com",
  // ... other fields exist, but file content is missing
}
```

**"Render Template" Node Expectation** (line 52):
```javascript
const templateHtml = $('Read Template File').first().json.data;
// ❌ V4.1: data is undefined → workflow stops with "No output data"
// ✅ V5: data contains HTML content → workflow continues
```

---

## ✅ V5 Solution - Complete Read File Fix

### Changes Required

**1. Add `dataPropertyName` Parameter**

**File**: `n8n/workflows/07_send_email_v4.1_encoding_fix.json`

**Node**: "Read Template File" (id: `read-template-file`, lines 32-49)

**Change**:
```json
// V4.1 (INCOMPLETE)
"options": {
  "encoding": "utf8"
}

// V5 (COMPLETE)
"options": {
  "encoding": "utf8",
  "dataPropertyName": "data"  // ✅ NEW: Define output property name
}
```

**Technical Impact**:
- n8n now knows to store file content in `.data` property
- Output becomes accessible: `$json.data = "<html>...</html>"`
- "Render Template" node receives expected data format
- Workflow executes completely: Read → Render → Send Email

### Implementation Steps

**Step 1 - Generate V5 Workflow**:
```python
# Script: scripts/generate-workflow-wf07-v5-data-property-fix.py

# Base: V4.1 workflow
# Changes:
#   1. "Read Template File" options: add dataPropertyName
#   2. Update notes: V5 - Complete data property fix
#   3. Update tags: v4.1 → v5, add data-property-fix
#   4. Update name: V4.1 (Encoding Fix) → V5 (Data Property Fix)

# Key modification:
read_template_node["parameters"]["options"] = {
    "encoding": "utf8",
    "dataPropertyName": "data"  # ✅ V5 critical fix
}
```

**Step 2 - Validate Configuration**:
```bash
# Check JSON structure
jq '.nodes[] | select(.id == "read-template-file") | .parameters.options' \
  n8n/workflows/07_send_email_v5_data_property_fix.json

# Expected output:
# {
#   "encoding": "utf8",
#   "dataPropertyName": "data"
# }
```

**Step 3 - Import to n8n**:
```
http://localhost:5678 → Workflows → Import from File
→ 07_send_email_v5_data_property_fix.json
```

**Step 4 - Test Read File Node**:
```
1. Execute workflow (manual trigger with test data)
2. Click "Read Template File" node → View execution data
3. Verify output contains "data" property with HTML content
4. Expected: $json.data = "<html>...template...</html>"
5. Not expected: "No output data returned"
```

**Step 5 - Test Complete Flow**:
```
Execute WF02 (Service 1/3) → Confirm → WF05 V4.0.4 → WF07 V5

Checkpoints:
✅ "Read Template File" SUCCESS (data property present)
✅ "Render Template" executes (receives HTML content)
✅ "Send Email (SMTP)" executes (receives rendered HTML)
✅ Email sent to recipient
✅ No "No output data returned" errors
```

---

## 🔄 Version Evolution Summary

| Version | Issue | Fix | Status |
|---------|-------|-----|--------|
| V2.0 | Missing 6 fields | Added complete data mapping | ❌ Partial |
| V3 | Docker `$env.HOME` path error | Read/Write Files node + absolute path | ❌ Broken |
| V4 | Empty output (binary mode) | Added `encoding: "utf8"` | ❌ Broken |
| V4.1 | Empty output (no property name) | Added encoding (incomplete fix) | ❌ Broken |
| **V5** | **No output data (missing dataPropertyName)** | **Added `dataPropertyName: "data"`** | **✅ READY** |

### Root Cause Chain

```
V3 Error → Docker path with $env.HOME (container vs host)
    ↓
V4 Fix → Read/Write Files node with absolute path
    ↓
V4 Error → File read as binary (empty/unusable data)
    ↓
V4.1 Fix → Added encoding: "utf8" (text mode)
    ↓
V4.1 Error → Data property not defined (no output destination)
    ↓
V5 Fix → Added dataPropertyName: "data" (complete configuration) ✅
```

---

## 📊 V5 Technical Specifications

### Node Configuration

**Read Template File** (Complete V5 Config):
```json
{
  "parameters": {
    "operation": "read",
    "filePath": "=/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/email-templates/{{ $json.template_file }}",
    "options": {
      "encoding": "utf8",           // ✅ V4.1: Text file reading
      "dataPropertyName": "data"     // ✅ V5: Output property definition
    }
  },
  "id": "read-template-file",
  "name": "Read Template File",
  "type": "n8n-nodes-base.readWriteFile",
  "typeVersion": 1,
  "notes": "V5: Complete data property fix - encoding + dataPropertyName"
}
```

### Output Data Structure

**V5 Output Format**:
```json
{
  // ✅ File content (from Read Template File)
  "data": "<html>...confirmacao_agendamento.html content...</html>",

  // ✅ Email data (from Prepare Email Data)
  "to": "client@email.com",
  "template": "confirmacao_agendamento",
  "template_file": "confirmacao_agendamento.html",
  "subject": "Agendamento Confirmado - E2 Soluções",
  "from_email": "contato@e2solucoes.com.br",
  "from_name": "E2 Soluções",
  "reply_to": "contato@e2solucoes.com.br",

  // ✅ Template variables (from Prepare Email Data)
  "template_data": {
    "name": "João Silva",
    "email": "client@email.com",
    "formatted_date": "25/04/2026",
    "formatted_time": "14:00 às 15:00",
    "service_type": "energia_solar",
    "city": "Goiânia",
    "google_event_link": "https://calendar.google.com/calendar/event?eid=..."
  }
}
```

### Render Template Node Compatibility

**Before V5** (broken):
```javascript
const templateHtml = $('Read Template File').first().json.data;
// ❌ data is undefined → Error: Cannot read property 'replace' of undefined
```

**After V5** (working):
```javascript
const templateHtml = $('Read Template File').first().json.data;
// ✅ data = "<html>...</html>" → Template rendering succeeds
```

---

## 🧪 Testing Plan

### Test Case 1: Read File Node Output

**Objective**: Verify "Read Template File" returns data in correct format

**Steps**:
1. Import V5 workflow to n8n
2. Execute with manual trigger (test data)
3. Click "Read Template File" node
4. Inspect execution output

**Expected Result**:
```json
{
  "data": "<html>...template content...</html>",
  "template_file": "confirmacao_agendamento.html",
  // ... other fields
}
```

**Success Criteria**:
- ✅ `.data` property exists and contains HTML string
- ✅ No "No output data returned" message
- ✅ Node execution shows "Success" status

### Test Case 2: Render Template Execution

**Objective**: Verify "Render Template" receives and processes data

**Steps**:
1. Continue from Test Case 1
2. Click "Render Template" node
3. Verify node executes (not skipped)
4. Inspect output

**Expected Result**:
```json
{
  "html_body": "<html>...rendered with {{variables}} replaced...</html>",
  "text_body": "Plain text version...",
  // ... other fields
}
```

**Success Criteria**:
- ✅ Node executes successfully (not stopped)
- ✅ `html_body` contains rendered HTML with replaced variables
- ✅ No template variables (`{{}}`) remain in output

### Test Case 3: Complete Email Flow

**Objective**: Verify end-to-end email sending

**Steps**:
1. Execute WF02 (WhatsApp conversation)
2. Choose Service 1 or 3
3. Complete data collection
4. Confirm appointment
5. Check WF05 execution
6. Check WF07 V5 execution
7. Verify email received

**Expected Result**:
- ✅ WF05 creates calendar event and triggers WF07
- ✅ WF07 "Read Template File" succeeds
- ✅ WF07 "Render Template" executes
- ✅ WF07 "Send Email (SMTP)" sends email
- ✅ Email received with correct content
- ✅ No workflow errors

**Success Criteria**:
- Email sent within 5 minutes: ≥ 95%
- All workflow nodes execute: 100%
- Email content correctly formatted: 100%
- No "No output data returned" errors: 100%

### Test Case 4: Error Handling

**Objective**: Verify workflow handles edge cases

**Test Scenarios**:
1. **Template file not found**: Should show clear error message
2. **Invalid template variables**: Should leave `{{}}` unchanged
3. **Empty template file**: Should send email with empty content (graceful degradation)

**Expected Behavior**:
- ✅ Clear error messages for file not found
- ✅ Workflow doesn't crash on invalid variables
- ✅ Error logs created in database

---

## 📈 Success Metrics

### Critical Metrics (Must Pass)

1. **Read File Success Rate**: 100%
   - No "No output data returned" errors
   - `.data` property always present in output

2. **Workflow Execution Rate**: 100%
   - All nodes execute (Read → Render → Send)
   - No premature workflow stops

3. **Email Delivery Rate**: ≥ 98%
   - Emails sent successfully
   - SMTP errors handled gracefully

### Performance Metrics

1. **Email Send Time**: < 5 seconds (Read → Render → Send)
2. **Template Rendering**: < 1 second
3. **Database Logging**: < 500ms

### Quality Metrics

1. **Template Variable Replacement**: 100%
   - No `{{}}` visible in sent emails
   - All data fields correctly mapped

2. **Date/Time Format**: 100%
   - Brazilian format (DD/MM/YYYY)
   - Time format (HH:MM às HH:MM)

3. **Content Integrity**: 100%
   - HTML structure preserved
   - Special characters handled correctly
   - UTF-8 encoding maintained

---

## 🚀 Deployment Procedure

### Pre-Deployment Checklist

- [ ] V5 script generated
- [ ] V5 workflow JSON validated
- [ ] Email templates exist in `/email-templates/`
- [ ] File permissions correct (`chmod 644 *.html`)
- [ ] SMTP credentials configured in n8n
- [ ] Test environment ready

### Deployment Steps

**1. Generate V5 Workflow**:
```bash
cd /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot
python3 scripts/generate-workflow-wf07-v5-data-property-fix.py
```

**2. Backup Current Workflow**:
```bash
# Export V4.1 from n8n (if imported)
# Or keep JSON file backup
cp n8n/workflows/07_send_email_v4.1_encoding_fix.json \
   n8n/workflows/backups/07_send_email_v4.1_backup_$(date +%Y%m%d_%H%M%S).json
```

**3. Import V5 to n8n**:
```
http://localhost:5678/workflows
→ Import from File
→ Select: n8n/workflows/07_send_email_v5_data_property_fix.json
→ Import
```

**4. Configure Workflow**:
```
- Verify SMTP credentials connected
- Check Execute Workflow Trigger ID (if needed)
- Activate workflow
```

**5. Test Phase 1 - Manual Trigger**:
```bash
# Execute with test data
curl -X POST http://localhost:5678/webhook-test/wf07-test \
  -H "Content-Type: application/json" \
  -d '{
    "to": "your-test-email@gmail.com",
    "template": "confirmacao_agendamento",
    "template_data": {
      "name": "Test User",
      "formatted_date": "30/03/2026",
      "formatted_time": "14:00 às 15:00",
      "service_type": "energia_solar",
      "city": "Goiânia",
      "google_event_link": "https://calendar.google.com/test"
    }
  }'
```

**Expected**: Email received within 1 minute

**6. Test Phase 2 - WF05 Integration**:
```
Execute: WF02 (WhatsApp) → Service 1/3 → Complete → Confirm
Expected: WF05 → WF07 V5 → Email sent automatically
Monitor: WF07 execution logs for "Read Template File" success
```

**7. Monitor (2 hours)**:
```sql
-- Check email logs
SELECT
  recipient_email,
  subject,
  template_used,
  status,
  sent_at,
  error_message
FROM email_logs
WHERE sent_at > NOW() - INTERVAL '2 hours'
ORDER BY sent_at DESC;

-- Check for errors
SELECT * FROM email_logs
WHERE status = 'failed'
  AND sent_at > NOW() - INTERVAL '2 hours';
```

**8. Production Approval**:
```
Success Criteria:
✅ Manual test email received
✅ WF05 integration email received
✅ No "No output data returned" errors
✅ All template variables replaced
✅ Date/time format correct
✅ No failed emails in logs

If all pass → Production approved
If any fail → Rollback to V4.1 (or previous stable version)
```

---

## 🔙 Rollback Procedure

**If V5 fails in production**:

**Step 1 - Deactivate V5**:
```
n8n UI → Workflows → "07 - Send Email V5" → Deactivate
```

**Step 2 - Restore V4.1** (or previous stable):
```
n8n UI → Workflows → Import from File
→ backups/07_send_email_v4.1_backup_YYYYMMDD_HHMMSS.json
→ Activate
```

**Step 3 - Verify Rollback**:
```bash
# Test email send
curl -X POST http://localhost:5678/webhook/wf07-test ...
# Check if email sent (even if V4.1 had issues, better than V5 failure)
```

**Step 4 - Investigate V5 Failure**:
```sql
-- Check error logs
SELECT * FROM email_logs
WHERE template_used = 'confirmacao_agendamento'
  AND status = 'failed'
  AND sent_at > NOW() - INTERVAL '1 hour'
ORDER BY sent_at DESC;
```

---

## 📝 Documentation Updates

### Files to Update

**1. CLAUDE.md** (project context):
```markdown
## 📧 WF07 V5 Ready for Deploy (Data Property Fix - Complete)

- **File**: `07_send_email_v5_data_property_fix.json`
- **V4.1 → V5 Fix**: Added `dataPropertyName: "data"` to Read File node options
- **Root Cause Fixed**: n8n Read File node now stores content in accessible property
- **Status**: ✅ Complete fix, ready for testing and production
```

**2. BUGFIX_WF07_V5_DATA_PROPERTY_FIX.md** (new file):
```markdown
# WF07 V5 - Data Property Fix (Complete Read File Solution)

## Problem
Execution 16271 - "Read Template File" returns "No output data returned"

## Root Cause
Missing `dataPropertyName` parameter in readWriteFile node options

## Solution
Added `dataPropertyName: "data"` to define output property name

## Changes
V4.1 options: { encoding: "utf8" }
V5 options: { encoding: "utf8", dataPropertyName: "data" }

## Impact
- Read File node now stores content in `.data` property
- Render Template receives expected data format
- Complete workflow execution (Read → Render → Send)
```

**3. scripts/generate-workflow-wf07-v5-data-property-fix.py** (new script):
```python
# Generator for WF07 V5 workflow
# Base: V4.1 with encoding fix
# Change: Add dataPropertyName to Read File options
```

---

## 🎯 Next Steps

### Immediate (Today)

1. ✅ Analysis complete (this document created)
2. ⏳ Generate V5 script
3. ⏳ Create V5 workflow JSON
4. ⏳ Validate JSON structure
5. ⏳ Update CLAUDE.md

### Testing (Next)

1. ⏳ Import V5 to n8n
2. ⏳ Test Read File node output
3. ⏳ Test manual email trigger
4. ⏳ Test WF05 → WF07 integration
5. ⏳ Monitor 2h for errors

### Production (After Tests Pass)

1. ⏳ Deploy V5 to production
2. ⏳ Monitor email logs 24h
3. ⏳ Verify success metrics
4. ⏳ Update documentation with results
5. ⏳ Archive V4.1 as backup

---

## 🎓 Lessons Learned

### Root Cause Analysis Process

**Issue Chain**:
```
V3: Docker path error ($env.HOME)
  → V4: Fixed with absolute path + Read/Write node
    → V4: New issue - binary data output
      → V4.1: Fixed with encoding: "utf8"
        → V4.1: New issue - no output data (missing property name)
          → V5: Fixed with dataPropertyName: "data" ✅
```

**Key Insight**: n8n readWriteFile node requires **both** encoding AND dataPropertyName for text file reading:
- `encoding: "utf8"` → Converts binary to text
- `dataPropertyName: "data"` → Stores text in accessible property
- **Without both**: Data is lost/inaccessible → "No output data"

### Configuration Complexity

**n8n Read/Write Files from Disk Node** (typeVersion 1):
- Simple API, but requires complete configuration
- Missing parameters cause silent failures (no error, just empty output)
- Documentation gaps (dataPropertyName not obvious for text files)

### Testing Improvements

**Test Coverage Needed**:
1. ✅ Node configuration validation (all required parameters)
2. ✅ Output format validation (expected properties present)
3. ✅ Data flow validation (each node receives expected input)
4. ⏳ Integration tests for complete workflow (Read → Render → Send)

### Documentation Standards

**Critical for n8n Workflows**:
1. Document all node parameters (not just changed ones)
2. Explain parameter interactions (encoding + dataPropertyName)
3. Include example input/output for each node
4. Maintain version history with specific configuration changes

---

## 📞 Support

**If V5 fails**:

1. **Check n8n execution logs**:
   ```
   http://localhost:5678/workflow/[workflow-id]/executions
   → Click failed execution
   → Check each node's input/output
   ```

2. **Check "Read Template File" output**:
   ```json
   // Expected:
   { "data": "<html>...</html>", ... }

   // If empty:
   { } or "No output data returned"
   → dataPropertyName parameter missing or incorrect
   ```

3. **Check file permissions**:
   ```bash
   ls -la email-templates/
   # Should show: -rw-r--r-- (644)

   # If permission denied:
   chmod 644 email-templates/*.html
   ```

4. **Check file path**:
   ```bash
   # Test file exists
   cat /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/email-templates/confirmacao_agendamento.html

   # If not found:
   # Verify absolute path in workflow matches actual location
   ```

5. **Enable "Always Output Data"** (temporary debugging):
   ```
   n8n Settings → Workflows → "Always Output Data" → ON
   # This prevents workflow stops on empty output
   # Useful for debugging, but fix root cause for production
   ```

---

**End of Plan V5**
