# BUGFIX WF02 V104.2 - Database Schema Mismatch Fix

**Date**: 2026-04-27
**Workflow ID**: 9tG2gR6KBt6nYyHT
**Execution**: 8571
**Problem**: V104.1 deployment fails with "column contact_phone does not exist"
**Root Cause**: V104.1 code references column that doesn't exist in database schema

---

## 🐛 PROBLEM ANALYSIS

### V104.1 Deployment Failure
**Error Message**:
```
column "contact_phone" of relation "conversations" does not exist

Failed query: INSERT INTO conversations (
  ...
  contact_phone,  -- ❌ Column does not exist!
  ...
)
```

**Execution**: http://localhost:5678/workflow/9tG2gR6KBt6nYyHT/executions/8571

### Root Cause
**V104.1 Code** (lines 130, 142):
```javascript
// Extract contact_phone with priority fallback
const contact_phone = collected_data?.contact_phone ||
                     collected_data?.phone_primary ||
                     collected_data?.phone ||
                     '';

// SQL INSERT
INSERT INTO conversations (
  ...
  contact_phone,  // ❌ Column does NOT exist!
  ...
) VALUES (
  ...
  '${escapeSql(contact_phone)}',
  ...
)

// SQL UPDATE
DO UPDATE SET
  ...
  contact_phone = COALESCE(EXCLUDED.contact_phone, conversations.contact_phone),  // ❌ Column does NOT exist!
  ...
```

**Database Schema**:
```sql
Table "public.conversations"
    Column        |           Type
------------------+--------------------------
 id               | uuid
 phone_number     | character varying(20)    ✅
 whatsapp_name    | character varying(255)
 current_state    | character varying(50)
 state_machine_state | character varying(50)
 collected_data   | jsonb
 service_type     | character varying(50)
 contact_name     | character varying(255)   ✅
 contact_email    | character varying(255)   ✅
 city             | character varying(100)   ✅
 -- contact_phone does NOT exist! ❌
```

**Key Finding**:
- Database HAS: `contact_name`, `contact_email`, `city`
- Database MISSING: `contact_phone`
- Phone data stored in: `phone_number` column + `collected_data` JSONB field

---

## ✅ SOLUTION V104.2 - Remove contact_phone Column References

### Changes Required
1. **Remove** `contact_phone` variable extraction
2. **Remove** `contact_phone` from INSERT column list
3. **Remove** `contact_phone` from INSERT VALUES list
4. **Remove** `contact_phone` from UPDATE SET clause
5. **Remove** `contact_phone` from correction query fieldConfig

### V104.2 Implementation

**REMOVED** (lines 62-66):
```javascript
// Extract contact_phone with priority fallback
const contact_phone = collected_data?.contact_phone ||
                     collected_data?.phone_primary ||
                     collected_data?.phone ||
                     '';
```

**ADDED** (lines 65-66):
```javascript
// V104.2 NOTE: contact_phone column does NOT exist in conversations table
// Phone number is stored in phone_number column and collected_data JSONB field only
```

**FIXED SQL INSERT** (lines 99-127):
```sql
INSERT INTO conversations (
  phone_number,
  whatsapp_name,
  current_state,
  state_machine_state,
  collected_data,
  service_type,
  contact_name,
  contact_email,
  -- contact_phone REMOVED ✅
  city,
  status,
  last_message_at,
  created_at,
  updated_at
) VALUES (
  '${phone_with_code}',
  '${escapeSql(collected_data?.lead_name || '')}',
  '${db_state}',
  '${next_stage}',
  '${collected_data_json}'::jsonb,
  ${service_type ? "'" + escapeSql(service_type) + "'" : 'NULL'},
  '${escapeSql(collected_data?.lead_name || '')}',
  '${escapeSql(collected_data?.email || '')}',
  -- '${escapeSql(contact_phone)}', REMOVED ✅
  '${escapeSql(collected_data?.city || '')}',
  'active',
  NOW(),
  NOW(),
  NOW()
)
```

**FIXED SQL UPDATE** (lines 129-140):
```sql
ON CONFLICT (phone_number)
DO UPDATE SET
  current_state = EXCLUDED.current_state,
  state_machine_state = EXCLUDED.state_machine_state,
  collected_data = conversations.collected_data || EXCLUDED.collected_data,
  service_type = COALESCE(EXCLUDED.service_type, conversations.service_type),
  contact_name = COALESCE(NULLIF(EXCLUDED.contact_name, ''), conversations.contact_name),
  contact_email = COALESCE(NULLIF(EXCLUDED.contact_email, ''), conversations.contact_email),
  -- contact_phone = COALESCE(...) REMOVED ✅
  city = COALESCE(NULLIF(EXCLUDED.city, ''), conversations.city),
  whatsapp_name = COALESCE(NULLIF(EXCLUDED.whatsapp_name, ''), conversations.whatsapp_name),
  last_message_at = NOW(),
  updated_at = NOW()
```

**FIXED Correction fieldConfig** (lines 240-245):
```javascript
const fieldConfig = {
  'lead_name': { db_column: 'contact_name', jsonb_key: 'lead_name' },
  // V104.2: contact_phone removed - column does not exist in conversations table
  'email': { db_column: 'contact_email', jsonb_key: 'email' },
  'city': { db_column: 'city', jsonb_key: 'city' }
};
```

---

## 🔧 IMPLEMENTATION STEPS

### Step 1: Copy V104.2 Build Update Queries Code
```bash
cat /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/scripts/wf02-v104_2-build-update-queries-schema-fix.js
```

### Step 2: Update n8n Workflow Node
1. Open: http://localhost:5678/workflow/9tG2gR6KBt6nYyHT
2. Click on node: **"Build Update Queries"**
3. **DELETE** all existing code (V104.1 with schema error)
4. **PASTE** complete V104.2 code from Step 1
5. Verify code starts with:
   ```javascript
   // Build Update Queries - V104.2 (DATABASE STATE UPDATE FIX + SCHEMA FIX)
   ```
6. Click **Save** on the node
7. Click **Save** button (top-right of workflow canvas)

### Step 3: Test Deployment
```bash
# Send test WhatsApp message
# Expected: No more "contact_phone" column errors

# Check logs
docker logs -f e2bot-n8n-dev | grep -E "V104.2|schema-compliant"

# Expected:
# === V104.2 BUILD UPDATE QUERIES - DATABASE STATE + SCHEMA FIX ===
# ✅ V104.2: Building queries with state from collected_data
# ✅ V104.2: UPSERT query with state from collected_data.current_stage (schema-compliant)
# ✅ V104.2 BUILD UPDATE QUERIES COMPLETE - State from collected_data + schema-compliant
```

---

## ✅ POST-DEPLOYMENT VALIDATION

### Test 1: Database Insert Success
```bash
# Send WhatsApp message to trigger workflow

# Check n8n execution
# http://localhost:5678/workflow/9tG2gR6KBt6nYyHT/executions

# Expected:
# ✅ "Update Conversation State" node succeeds (no errors)
# ✅ Database INSERT/UPDATE executes successfully
# ❌ NO "column contact_phone does not exist" errors
```

### Test 2: Verify Database Data
```bash
# Check conversations table after message
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT phone_number, contact_name, contact_email, city, state_machine_state
      FROM conversations
      WHERE phone_number = '556181755748';"

# Expected:
# phone_number: 556181755748  ✅
# contact_name: [user name]  ✅
# contact_email: [user email]  ✅
# city: [user city]  ✅
# state_machine_state: [current state]  ✅
# No contact_phone column shown (does not exist)  ✅
```

### Test 3: Phone Number in collected_data
```bash
# Verify phone number is stored in collected_data JSONB
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT collected_data->'phone_number' as phone_in_data,
      collected_data->'contact_phone' as contact_phone_in_data
      FROM conversations
      WHERE phone_number = '556181755748';"

# Expected:
# phone_in_data: "556181755748"  ✅ (stored in JSONB)
# contact_phone_in_data: [value if exists]  (optional in JSONB)
```

---

## 📊 EXPECTED IMPROVEMENTS

### Before V104.2 (BROKEN)
```
User sends message → WF02 triggers

Build Update Queries executes SQL:
  INSERT INTO conversations (..., contact_phone, ...)

PostgreSQL ERROR:
  column "contact_phone" of relation "conversations" does not exist ❌

Result:
  Workflow execution FAILS ❌
  Database NOT updated ❌
  User gets NO response ❌
```

### After V104.2 (FIXED)
```
User sends message → WF02 triggers

Build Update Queries executes SQL:
  INSERT INTO conversations (..., contact_name, contact_email, city, ...)
  -- contact_phone removed ✅

PostgreSQL SUCCESS:
  Row inserted/updated successfully ✅

Result:
  Workflow execution COMPLETES ✅
  Database updated correctly ✅
  User gets expected response ✅
```

### Metrics
- **Database schema compliance**: 0% → 100% ✅
- **Workflow execution success**: 0% → 100% ✅
- **SQL errors**: 100% → 0% ✅
- **User experience**: Broken → Working ✅

---

## 📁 RELATED DOCUMENTATION

**Bug Report**:
- This file - V104.2 schema mismatch analysis

**Code Files**:
- `/scripts/wf02-v104_2-build-update-queries-schema-fix.js` - V104.2 fixed code
- `/scripts/wf02-v104-database-state-update-fix.js` - V104 State Machine (still valid!)

**Previous Versions**:
- `/docs/fix/BUGFIX_WF02_V104_1_BUILD_UPDATE_QUERIES_STATE_FIX.md` - V104.1 analysis (had schema bug)
- `/docs/deployment/DEPLOY_WF02_V104_1_BUILD_UPDATE_QUERIES_FIX.md` - V104.1 deployment (superseded by V104.2)

---

## 🎓 KEY LEARNINGS

### Database Schema Validation Critical
1. **Always verify schema** before writing SQL INSERT/UPDATE statements
2. **Don't assume columns exist** based on similar field names
3. **Use `\d table_name`** in psql to verify exact column names
4. **Test SQL queries** against actual database before deployment

### n8n Code-Database Synchronization
1. **Code must match schema**: Every column in SQL must exist in database
2. **Phone storage pattern**: Phone in `phone_number` column + `collected_data` JSONB (not separate `contact_phone` column)
3. **JSONB flexibility**: Additional data can be in `collected_data` without schema changes
4. **Schema changes require migration**: Don't add columns to SQL that don't exist

### V104 Evolution Path
- **V104**: State Machine - adds state to collected_data ✅
- **V104.1**: Build Update Queries - reads state from collected_data ❌ (had schema bug)
- **V104.2**: Build Update Queries - schema-compliant version ✅

---

**Status**: V104.2 bugfix complete and ready for deployment
**Deployment Time**: 5 minutes
**Risk Level**: Low (simple column removal)
**Recommended**: Deploy immediately to fix V104.1 schema error
**Critical**: Both V104 State Machine AND V104.2 Build Update Queries required for complete fix!
