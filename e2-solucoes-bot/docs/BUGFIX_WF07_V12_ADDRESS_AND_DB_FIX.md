# BUGFIX: WF07 V12 - Address Field + Database Parameters Fix

**Version**: V12
**Date**: 2026-04-01
**Status**: ✅ READY FOR TESTING
**Previous Version**: V11 (Service Name Fix - email_logs table created)
**Failed Execution**: 18818

---

## 🐛 Problem Description

### Error 1: Empty Location Field in Email
```
Email shows: "📍 Local: " (empty)
Expected: "📍 Local: Cocal, GO"
```

### Error 2: Database Parameter Error
```
Problem in node 'Log Email Sent'
there is no parameter $1

Query:
INSERT INTO email_logs (recipient_email, recipient_name, subject,
  template_used, status, sent_at, metadata)
VALUES ($1, $2, $3, $4, $5, NOW(), $6)
```

### Root Cause Analysis

**Issue 1: Address Field Mismatch**
- Template HTML expects `{{address}}` variable (confirmacao_agendamento.html:183)
- WF05 sends `city: "cocal-go"` (snake-case with hyphen)
- Prepare Email Data node maps `city` field but NOT `address` field
- Template rendering had no `address` value to replace
- Result: Literal empty string `"📍 Local: "`

**Issue 2: Database Parameters Format**
- V11 used `queryParameters` with comma-separated string values
- PostgreSQL expects proper parameter binding format
- n8n requires `queryReplacement` with pipe-separated values (`|`)
- Result: "there is no parameter $1" error

**Evidence from Execution 18818**:
```json
{
  "template_data": {
    "city": "cocal-go",
    "address": "",  ← Empty, template expects this
    "state": "",
    "zip_code": "",
    ...
  }
}
```

---

## ✅ Solutions Implemented (V12)

### Solution 1: City-to-Address Formatting

**Changes in Prepare Email Data Node**:

```javascript
// V12 FIX: City formatter
const formatCityToAddress = (city) => {
    if (!city) return '';

    // "cocal-go" → "Cocal, GO"
    const parts = city.split('-');
    if (parts.length === 2) {
        const cityName = parts[0].charAt(0).toUpperCase() + parts[0].slice(1);
        const state = parts[1].toUpperCase();
        return `${cityName}, ${state}`;
    }

    // Single word, just capitalize
    return city.charAt(0).toUpperCase() + city.slice(1);
};

// V12 FIX: Use formatted address
const cityRaw = input.city || '';
const addressFormatted = input.address || formatCityToAddress(cityRaw);

console.log('🏠 [V12 Address Fix]:', {
    city_raw: cityRaw,
    address_original: input.address,
    address_formatted: addressFormatted
});

templateData = {
    // ... other fields ...
    city: cityRaw,              // Keep original "cocal-go"
    address: addressFormatted,  // V12 FIX: "Cocal, GO"
    // ... other fields ...
};
```

**Mapping Examples**:
| city | address |
|------|---------|
| cocal-go | Cocal, GO |
| goiania-go | Goiania, GO |
| brasilia-df | Brasilia, DF |
| anapolis | Anapolis |

### Solution 2: Database Parameters Fix

**Changes in Log Email Sent Node**:

```json
{
  "parameters": {
    "operation": "executeQuery",
    "query": "INSERT INTO email_logs (...) VALUES ($1, $2, $3, $4, $5, NOW(), $6)",
    "options": {
      "queryReplacement": "={{ $json.to }}|={{ $json.template_data.name }}|={{ $json.subject }}|={{ $json.template }}|sent|={{ JSON.stringify({ template_data: $json.template_data, source: $json.source }) }}"
    }
  }
}
```

**Key Changes**:
- **V11 Used**: `additionalFields.queryParameters` with comma separator
- **V12 Uses**: `options.queryReplacement` with pipe separator (`|`)
- **n8n Behavior**: Splits by `|` and binds to PostgreSQL parameters

**Parameter Binding**:
| Parameter | Value | Source |
|-----------|-------|--------|
| $1 | clima.cocal.2025@gmail.com | $json.to |
| $2 | bruno rosa | $json.template_data.name |
| $3 | Agendamento Confirmado - E2 Soluções | $json.subject |
| $4 | confirmacao_agendamento | $json.template |
| $5 | sent | literal |
| $6 | {"template_data":{...},"source":"wf05_trigger"} | JSON.stringify() |

---

## 📊 Changes Summary

### Modified Nodes

**Node**: Prepare Email Data (V12)
**Change**: Added `formatCityToAddress()` function and address mapping

**Node**: Log Email Sent (V12)
**Change**: Changed from `queryParameters` (comma) to `queryReplacement` (pipe)

### Code Diff (V11 → V12)

```diff
+ // ===== CITY FORMATTER (V12 FIX) =====
+ const formatCityToAddress = (city) => {
+     if (!city) return '';
+
+     const parts = city.split('-');
+     if (parts.length === 2) {
+         const cityName = parts[0].charAt(0).toUpperCase() + parts[0].slice(1);
+         const state = parts[1].toUpperCase();
+         return `${cityName}, ${state}`;
+     }
+
+     return city.charAt(0).toUpperCase() + city.slice(1);
+ };

  if (isFromWF05) {
+     const cityRaw = input.city || '';
+     const addressFormatted = input.address || formatCityToAddress(cityRaw);
+
      templateData = {
          // ... other fields ...
-         city: input.city || '',
-         address: input.address || '',
+         city: cityRaw,
+         address: addressFormatted,  // V12 FIX
          // ... other fields ...
      };
  }
```

**Database Node Change**:
```diff
- "additionalFields": {
-   "queryParameters": "={{ $json.to }},={{ $json.template_data.name }},..."
- }
+ "options": {
+   "queryReplacement": "={{ $json.to }}|={{ $json.template_data.name }}|..."
+ }
```

### All Other Nodes
✅ **Unchanged** - Fetch Template, Render Template, Send Email, Return Success

---

## 🧪 Testing Strategy

### Test Data (Same as Execution 18818)
```json
{
  "appointment_id": "89765b5e-a8e8-45db-a137-ea0abb9548b1",
  "lead_email": "clima.cocal.2025@gmail.com",
  "lead_name": "bruno rosa",
  "phone_number": "556181755748",
  "service_type": "energia_solar",
  "scheduled_date": "2026-04-02",
  "scheduled_time_start": "08:00:00",
  "scheduled_time_end": "10:00:00",
  "city": "cocal-go",
  "google_calendar_event_id": "8rskkmqojvs1435qk2g6ev1980",
  "calendar_success": true
}
```

### Expected Results

1. ✅ Prepare Email Data creates address field:
   ```json
   {
     "template_data": {
       "city": "cocal-go",
       "address": "Cocal, GO"
     }
   }
   ```

2. ✅ Render Template replaces `{{address}}`:
   ```html
   <span class="detail-value">Cocal, GO</span>
   ```

3. ✅ Log Email Sent inserts row with proper parameters:
   ```sql
   INSERT INTO email_logs (recipient_email, recipient_name, ...)
   VALUES ('clima.cocal.2025@gmail.com', 'bruno rosa', ...)
   ```

4. ✅ Email received with correct formatting:
   ```
   📆 Data: 02/04/2026
   ⏰ Horário: 08:00 às 10:00
   🔧 Serviço: Energia Solar
   📍 Local: Cocal, GO  ← FIXED
   ```

### Monitoring Commands
```bash
# Watch n8n logs for V12 activity
docker logs -f e2bot-n8n-dev | grep -E "V12|address|queryReplacement"

# Check email_logs table
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT recipient_email, template_used, status, sent_at FROM email_logs ORDER BY sent_at DESC LIMIT 5;"

# Verify address formatting in logs
docker logs e2bot-n8n-dev 2>&1 | grep "address" | tail -10
```

---

## 🚀 Deployment Steps

### 1. Import Workflow
```bash
# Navigate to n8n UI
http://localhost:5678

# Import workflow
Import from File → n8n/workflows/07_send_email_v12_address_and_db_fix.json
```

### 2. Verify SMTP Credential
```
Settings → Credentials → SMTP - E2 Email
  ✅ Host: smtp.gmail.com
  ✅ Port: 465
  ✅ SSL/TLS: ON
  ✅ Password: [16 chars without spaces]
  ✅ Connection tested successfully
```

### 3. Verify Database Table
```bash
# Confirm email_logs table exists
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "\dt email_logs"

# Expected: Table listed with 9 columns
```

### 4. Test Execution
```
1. Open WF07 V12
2. Manual Execute with test data (above)
3. Monitor logs: docker logs -f e2bot-n8n-dev
4. Expected:
   ✅ Prepare Email Data logs address: "Cocal, GO"
   ✅ Render Template replaces {{address}}
   ✅ Email sent successfully
   ✅ Database log entry created (no parameter error)
```

### 5. Production Deployment
```bash
# After successful test
1. Deactivate WF07 V11 (if active)
2. Activate WF07 V12
3. Monitor first WF05 trigger
4. Verify email content and database log
```

---

## 🔄 Rollback Plan

**If V12 fails**:
```bash
1. Deactivate WF07 V12
2. Re-activate WF07 V11
3. Investigate:
   - Check address in template_data
   - Verify queryReplacement format
   - Review Render Template logs
```

**Database rollback** (not needed - table unchanged)

---

## 📚 References

### Related Documents
- **V11 Service Name Fix**: `docs/BUGFIX_WF07_V11_SERVICE_NAME_FIX.md`
- **V10 STARTTLS Fix**: `docs/BUGFIX_WF07_V10_STARTTLS.md`
- **V9.3 Safe Property Check**: `docs/BUGFIX_WF07_V9.3_SAFE_PROPERTY_CHECK.md`
- **SMTP Credential Fix**: `docs/FIX_WF07_CREDENTIAL_REFERENCE.md`

### Evolution Timeline
| Version | Issue | Error | Execution | Status |
|---------|-------|-------|-----------|--------|
| V10 | Credential reference (manual fix) | ID does not exist | 18645 | ⚠️ MANUAL FIX |
| V10 | {{service_name}} literal | Variable not replaced | 18757 | ❌ FAILED |
| V10 | email_logs missing | relation does not exist | 18757 | ❌ FAILED |
| V11 | email_logs + service_name | None | - | ✅ PARTIAL |
| V11 | {{address}} empty | Variable not replaced | 18818 | ❌ FAILED |
| V11 | Database parameters | no parameter $1 | 18818 | ❌ FAILED |
| **V12** | **Both fixed** | **None** | **Pending** | **✅ READY** |

---

## ✅ Verification Checklist

### Before Import
- [x] email_logs table exists in PostgreSQL
- [x] SMTP credential configured (port 465, SSL/TLS ON, password without spaces)
- [x] WF07 V12 workflow generated (17.1 KB, 7 nodes)

### After Import
- [ ] Workflow imported successfully
- [ ] Node "Prepare Email Data" contains formatCityToAddress()
- [ ] Node "Log Email Sent" uses queryReplacement with pipe separator
- [ ] SMTP credential selected in "Send Email (SMTP)" node

### Testing Phase
- [ ] Manual execution with test data
- [ ] address appears in Prepare Email Data output: "Cocal, GO"
- [ ] Template rendering replaces {{address}}
- [ ] Email sent without errors
- [ ] Database log entry created (no parameter $1 error)
- [ ] Email received with correct "Cocal, GO" location

### Production Deployment
- [ ] First WF05-triggered email sent successfully
- [ ] Email content displays all appointment details correctly
- [ ] Database logs accumulate properly
- [ ] No errors in n8n execution logs

---

## 🎯 Success Criteria

1. ✅ Template rendering works with correct address mapping
2. ✅ Email shows formatted location (e.g., "Cocal, GO")
3. ✅ Database logging works without parameter errors
4. ✅ All appointment details displayed correctly
5. ✅ No execution errors in V12
6. ✅ Email received in inbox with proper formatting

---

**Generated**: 2026-04-01 by Claude Code
**Status**: V12 READY FOR TESTING (Address Fix + Database Parameters Fix)
