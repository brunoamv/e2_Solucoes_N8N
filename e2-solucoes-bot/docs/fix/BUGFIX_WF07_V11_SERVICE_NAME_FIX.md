# BUGFIX: WF07 V11 - Service Name Fix

**Version**: V11
**Date**: 2026-04-01
**Status**: ✅ READY FOR TESTING
**Previous Version**: V10 (STARTTLS - credential reference fixed manually)
**Failed Execution**: 18757

---

## 🐛 Problem Description

### Error 1: Template Variable Not Replaced
```
Email shows literal text: "🔧 Serviço: {{service_name}}"
Expected: "🔧 Serviço: Energia Solar"
```

### Error 2: Database Table Missing
```
Problem in node 'Log Email Sent'
relation "email_logs" does not exist

Query:
INSERT INTO email_logs (recipient_email, recipient_name, subject,
  template_used, status, sent_at, metadata)
VALUES ($1, $2, $3, $4, $5, NOW(), $6)
```

### Root Cause Analysis

**Issue 1: Variable Mismatch**
- Template HTML expects `{{service_name}}` variable
- WF05 sends `service_type: "energia_solar"` (snake_case)
- Prepare Email Data node created `template_data` with only `service_type`
- Template rendering had no `service_name` to replace
- Result: Literal `{{service_name}}` displayed in email

**Issue 2: Missing Database Table**
- Workflow assumes `email_logs` table exists
- Table was never created during initial setup
- INSERT operation failed with "relation does not exist"

**Evidence from Execution 18757**:
```json
{
  "template_data": {
    "name": "brunpo",
    "email": "clima.cocal.2025@gmail.com",
    "phone_number": "556181755748",
    "service_type": "energia_solar",  ← Only service_type present
    "city": "cocal...",
    "scheduled_date": "2026-04-01",
    "formatted_date": "01/04/2026",
    "formatted_time": "08:00 às 10:00"
  }
}
```

---

## ✅ Solutions Implemented (V11)

### Solution 1: Add Service Name Formatting

**Changes in Prepare Email Data Node**:

```javascript
// V11 FIX: Format service name
const formatServiceName = (serviceType) => {
    if (!serviceType) return 'Serviço';

    // Special cases with proper Portuguese formatting
    const specialCases = {
        'bess': 'BESS',
        'energia_solar': 'Energia Solar',
        'subestacao': 'Subestação',
        'projetos_eletricos': 'Projetos Elétricos',
        'analise_rede': 'Análise de Rede'
    };

    if (specialCases[serviceType]) {
        return specialCases[serviceType];
    }

    // Default: capitalize each word
    return serviceType
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
};

const serviceType = input.service_type || 'servico';
const serviceName = formatServiceName(serviceType);

templateData = {
    // ... other fields ...
    service_type: serviceType,        // Keep original
    service_name: serviceName,        // ✅ V11 FIX: Add formatted name
    // ... other fields ...
};
```

**Mapping Examples**:
| service_type | service_name |
|--------------|--------------|
| energia_solar | Energia Solar |
| subestacao | Subestação |
| projetos_eletricos | Projetos Elétricos |
| bess | BESS |
| analise_rede | Análise de Rede |

### Solution 2: Create email_logs Table

**Database Schema Created**:
```sql
CREATE TABLE IF NOT EXISTS email_logs (
  id SERIAL PRIMARY KEY,
  recipient_email VARCHAR(255) NOT NULL,
  recipient_name VARCHAR(255),
  subject VARCHAR(500),
  template_used VARCHAR(100),
  status VARCHAR(50),
  sent_at TIMESTAMP DEFAULT NOW(),
  metadata JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);
```

**Verification**:
```bash
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "\d email_logs"

# Output:
                                           Table "public.email_logs"
     Column      |            Type             | Collation | Nullable |                Default
-----------------+-----------------------------+-----------+----------+----------------------------------------
 id              | integer                     |           | not null | nextval('email_logs_id_seq'::regclass)
 recipient_email | character varying(255)      |           | not null |
 recipient_name  | character varying(255)      |           |          |
 subject         | character varying(500)      |           |          |
 template_used   | character varying(100)      |           |          |
 status          | character varying(50)       |           |          |
 sent_at         | timestamp without time zone |           |          | now()
 metadata        | jsonb                       |           |          |
 created_at      | timestamp without time zone |           |          | now()
Indexes:
    "email_logs_pkey" PRIMARY KEY, btree (id)
```

---

## 📊 Changes Summary

### Modified Nodes
**Node**: Prepare Email Data (V11)
**Change**: Added `formatServiceName()` function and `service_name` field

**Node**: Log Email Sent (V11)
**Change**: No code change, but table dependency now satisfied

### Code Diff (V10 → V11)

```diff
+ // ===== SERVICE NAME FORMATTER (V11 FIX) =====
+ const formatServiceName = (serviceType) => {
+     if (!serviceType) return 'Serviço';
+
+     const specialCases = {
+         'bess': 'BESS',
+         'energia_solar': 'Energia Solar',
+         'subestacao': 'Subestação',
+         'projetos_eletricos': 'Projetos Elétricos',
+         'analise_rede': 'Análise de Rede'
+     };
+
+     if (specialCases[serviceType]) {
+         return specialCases[serviceType];
+     }
+
+     return serviceType
+         .split('_')
+         .map(word => word.charAt(0).toUpperCase() + word.slice(1))
+         .join(' ');
+ };

  if (isFromWF05) {
+     const serviceType = input.service_type || 'servico';
+     const serviceName = formatServiceName(serviceType);
+
      templateData = {
          name: input.lead_name || 'Cliente',
          email: emailRecipient,
-         service_type: input.service_type || 'Serviço',
+         service_type: serviceType,
+         service_name: serviceName,  // ✅ V11 FIX
          // ... other fields ...
      };
  }
```

### All Other Nodes
✅ **Unchanged** - Render Template, Fetch Template, Send Email, Return Success

---

## 🧪 Testing Strategy

### Test Data (Same as Execution 18757)
```json
{
  "appointment_id": "test-id",
  "lead_email": "clima.cocal.2025@gmail.com",
  "lead_name": "bruno",
  "phone_number": "556181755748",
  "service_type": "energia_solar",
  "scheduled_date": "2026-04-01",
  "scheduled_time_start": "08:00:00",
  "scheduled_time_end": "10:00:00",
  "city": "cocal-go",
  "google_calendar_event_id": "test-event-id",
  "calendar_success": true
}
```

### Expected Results
1. ✅ Prepare Email Data creates both fields:
   ```json
   {
     "template_data": {
       "service_type": "energia_solar",
       "service_name": "Energia Solar"
     }
   }
   ```

2. ✅ Render Template replaces `{{service_name}}`:
   ```html
   <p>🔧 Serviço: Energia Solar</p>
   ```

3. ✅ Log Email Sent inserts row:
   ```sql
   INSERT INTO email_logs (recipient_email, recipient_name, ...)
   VALUES ('clima.cocal.2025@gmail.com', 'bruno', ...)
   ```

4. ✅ Email received with correct formatting:
   ```
   📆 Data: 01/04/2026
   ⏰ Horário: 08:00 às 10:00
   🔧 Serviço: Energia Solar  ← FIXED
   📍 Local: cocal-go
   ```

### Monitoring Commands
```bash
# Watch n8n logs for V11 activity
docker logs -f e2bot-n8n-dev | grep -E "V11|service_name"

# Check email_logs table
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT recipient_email, template_used, status, sent_at FROM email_logs ORDER BY sent_at DESC LIMIT 5;"

# Verify service name in logs
docker logs e2bot-n8n-dev 2>&1 | grep "service_name" | tail -10
```

---

## 🚀 Deployment Steps

### 1. Import Workflow
```bash
# Navigate to n8n UI
http://localhost:5678

# Import workflow
Import from File → n8n/workflows/07_send_email_v11_service_name_fix.json
```

### 2. Verify Database Table
```bash
# Confirm email_logs table exists
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "\dt email_logs"

# Expected: Table listed with columns
```

### 3. Verify SMTP Credential
```
Settings → Credentials → SMTP - E2 Email
  ✅ Host: smtp.gmail.com
  ✅ Port: 465
  ✅ SSL/TLS: ON
  ✅ Password: [16 chars without spaces]
  ✅ Connection tested successfully
```

### 4. Test Execution
```
1. Open WF07 V11
2. Manual Execute with test data (above)
3. Monitor logs: docker logs -f e2bot-n8n-dev
4. Expected:
   ✅ Prepare Email Data logs service_name: "Energia Solar"
   ✅ Render Template replaces {{service_name}}
   ✅ Email sent successfully
   ✅ Database log entry created
```

### 5. Production Deployment
```bash
# After successful test
1. Deactivate WF07 V10 (if active)
2. Activate WF07 V11
3. Monitor first WF05 trigger
4. Verify email content and database log
```

---

## 🔄 Rollback Plan

**If V11 fails**:
```bash
1. Deactivate WF07 V11
2. Re-activate WF07 V10 (or V9.3)
3. Investigate:
   - Check service_name in template_data
   - Verify email_logs table exists
   - Review Render Template logs
```

**Database rollback** (if needed):
```sql
-- Drop table if corrupted (CAUTION)
DROP TABLE IF EXISTS email_logs;
```

---

## 📚 References

### Related Documents
- **V10 STARTTLS Fix**: `docs/BUGFIX_WF07_V10_STARTTLS.md`
- **V9.3 Safe Property Check**: `docs/BUGFIX_WF07_V9.3_SAFE_PROPERTY_CHECK.md`
- **SMTP Credential Fix**: `docs/FIX_WF07_CREDENTIAL_REFERENCE.md`
- **Gmail SMTP Analysis**: `docs/ANALYSIS_GMAIL_SMTP_N8N_2.14.2_COMPATIBILITY.md`

### Evolution Timeline
| Version | Issue | Error | Execution | Status |
|---------|-------|-------|-----------|--------|
| V9.3 | SMTP SSL version mismatch | wrong version number | 18445 | ❌ FAILED |
| V10 | Credential reference | ID does not exist | 18645 | ⚠️ MANUAL FIX |
| V10 | Template + DB | {{service_name}} literal + email_logs missing | 18757 | ❌ FAILED |
| **V11** | **Both fixed** | **None** | **Pending** | **✅ READY** |

---

## ✅ Verification Checklist

### Before Import
- [x] email_logs table created in PostgreSQL
- [x] SMTP credential configured (port 465, SSL/TLS ON, password without spaces)
- [x] WF07 V11 workflow generated (15.2 KB, 7 nodes)

### After Import
- [ ] Workflow imported successfully
- [ ] Node "Prepare Email Data" contains formatServiceName()
- [ ] Node "Log Email Sent" references email_logs table
- [ ] SMTP credential selected in "Send Email (SMTP)" node

### Testing Phase
- [ ] Manual execution with test data
- [ ] service_name appears in Prepare Email Data output
- [ ] Template rendering replaces {{service_name}}
- [ ] Email sent without errors
- [ ] Database log entry created
- [ ] Email received with correct "Energia Solar" text

### Production Deployment
- [ ] First WF05-triggered email sent successfully
- [ ] Email content displays all appointment details correctly
- [ ] Database logs accumulate properly
- [ ] No errors in n8n execution logs

---

## 🎯 Success Criteria

1. ✅ Template rendering works with correct service_name mapping
2. ✅ Email shows formatted service name (e.g., "Energia Solar")
3. ✅ Database logging works without errors
4. ✅ All appointment details displayed correctly
5. ✅ No execution errors in V11
6. ✅ Email received in inbox with proper formatting

---

**Generated**: 2026-04-01 by Claude Code
**Status**: V11 READY FOR TESTING (Service Name Fix + email_logs Table)
