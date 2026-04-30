# BUGFIX WF02 V99 - Update Data Field Name Mismatch

**Problem**: Database shows empty `collected_data: {}` despite State Machine collecting user information.

**Root Cause**: Field name mismatch between State Machine output and Build Update Queries node.

---

## 🐛 BUG ANALYSIS

### Evidence

**Database Query:**
```sql
SELECT collected_data, service_type, contact_name, contact_email, city
FROM conversations
WHERE phone_number = '556181755748';
```

**Result:**
```
collected_data: {}              ❌ EMPTY
service_type: [null]            ❌ NULL
contact_name: [null]            ❌ NULL
contact_email: [null]           ❌ NULL
city: [null]                    ❌ NULL
```

**Expected Result:**
```
collected_data: {
  "lead_name": "Bruno Rosa",
  "email": "clima.cocal.2025@gmail.com",
  "phone_number": "556181755748",
  "service_type": "energia_solar",
  "service_selected": "1",
  "city": "Cocal-GO"
}
service_type: "energia_solar"
contact_name: "Bruno Rosa"
contact_email: "clima.cocal.2025@gmail.com"
city: "Cocal-GO"
```

### Root Cause

**State Machine Output (V99):**
```javascript
return {
  response_text: "...",
  update_data: {              // ✅ Outputs "update_data"
    lead_name: "Bruno Rosa",
    email: "clima.cocal.2025@gmail.com",
    service_type: "energia_solar",
    // ...
  },
  // ...
};
```

**Build Update Queries Node:**
```javascript
const collected_data = inputData.collected_data || {};  // ❌ Expects "collected_data"
```

**Result:** `collected_data = {}` (empty object)

---

## ✅ SOLUTION

### Option 1: Change State Machine Output (RECOMMENDED)

Rename `update_data` → `collected_data` in State Machine output.

**File**: `scripts/wf02-v99-state-resolution-fix.js`

**Change:**
```javascript
// OLD (line 795-820)
const output = {
  response_text: responseText,
  conversation_id: input.conversation_id || input.id || input.currentData?.conversation_id || null,

  update_data: {  // ❌ WRONG field name
    ...updateData,
    lead_name: updateData.lead_name || currentData.lead_name,
    // ...
  },

  next_stage: nextStage,
  current_stage: nextStage,
  phone_number: input.phone_number || input.phone_with_code,
  previous_stage: currentStage,
  version: 'V99',
  timestamp: new Date().toISOString()
};

// NEW (V100 FIX)
const output = {
  response_text: responseText,
  conversation_id: input.conversation_id || input.id || input.currentData?.conversation_id || null,

  // V100 FIX: Rename to collected_data to match Build Update Queries expectation
  collected_data: {  // ✅ CORRECT field name
    ...updateData,
    lead_name: updateData.lead_name || currentData.lead_name,
    email: updateData.email || currentData.email,
    phone_number: updateData.phone_number || currentData.phone_number,
    contact_phone: updateData.contact_phone || currentData.contact_phone,
    service_type: updateData.service_type || currentData.service_type,
    service_selected: updateData.service_selected || currentData.service_selected,
    city: updateData.city || currentData.city,

    // Preserve scheduling data
    scheduled_date: updateData.scheduled_date || currentData.scheduled_date,
    scheduled_date_display: updateData.scheduled_date_display || currentData.scheduled_date_display,
    scheduled_time: updateData.scheduled_time || currentData.scheduled_time,
    scheduled_time_display: updateData.scheduled_time_display || currentData.scheduled_time_display,
    scheduled_end_time: updateData.scheduled_end_time || currentData.scheduled_end_time,

    // Preserve suggestions
    date_suggestions: updateData.date_suggestions || currentData.date_suggestions,
    slot_suggestions: updateData.slot_suggestions || currentData.slot_suggestions
  },

  next_stage: nextStage,
  current_stage: nextStage,
  phone_number: input.phone_number || input.phone_with_code,
  previous_stage: currentStage,
  version: 'V100',  // V100: Field name fix
  timestamp: new Date().toISOString()
};
```

**Also update currentData merge (line 53-86):**
```javascript
// OLD
const currentData = {
  ...(input.currentData || {}),
  ...(input.update_data || {}),  // ❌ WRONG
  // ...
};

// NEW (V100 FIX)
const currentData = {
  ...(input.currentData || {}),
  ...(input.collected_data || {}),  // ✅ CORRECT

  // Individual field preservation with multiple fallbacks
  lead_name: input.lead_name || input.currentData?.lead_name || input.collected_data?.lead_name,
  email: input.email || input.currentData?.email || input.collected_data?.email,
  phone_number: input.phone_number || input.currentData?.phone_number || input.collected_data?.phone_number,
  // ... rest of fields
};
```

### Option 2: Change Build Update Queries Node (NOT RECOMMENDED)

Change `collected_data` → `update_data` in SQL query builder.

**Why not recommended**: Other workflows may depend on `collected_data` field name.

---

## 🚀 DEPLOYMENT V100

### 1. Generate V100 State Machine

```bash
# Copy V99 and apply field name fix
cp /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/scripts/wf02-v99-state-resolution-fix.js \
   /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/scripts/wf02-v100-collected-data-fix.js

# Apply changes:
# 1. Line 65: ...(input.update_data || {}) → ...(input.collected_data || {})
# 2. Line 70-85: input.update_data?.field → input.collected_data?.field
# 3. Line 798: update_data: { → collected_data: {
# 4. Line 830: version: 'V99' → version: 'V100'
# 5. Line 837-843: Update logging to use collected_data
```

### 2. Update Workflow

```bash
# Open n8n workflow
http://localhost:5678/workflow/W7alitUQEdVxYeJK

# Node: "State Machine Logic V98" (or V99)
# Action:
#   1. DELETE all existing code
#   2. PASTE V100 code from scripts/wf02-v100-collected-data-fix.js
#   3. Save workflow

# Verify node name updated to "State Machine Logic V100"
```

### 3. Test Complete Flow

```bash
# Test conversation from greeting to confirmation
# Expected database state after confirmation:

docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT phone_number, collected_data, service_type, contact_name, contact_email, city
      FROM conversations
      WHERE phone_number = '556181755748';"

# Expected result:
# collected_data: {"lead_name":"Bruno Rosa","email":"clima.cocal.2025@gmail.com",...}  ✅
# service_type: energia_solar  ✅
# contact_name: Bruno Rosa  ✅
# contact_email: clima.cocal.2025@gmail.com  ✅
# city: Cocal-GO  ✅
```

### 4. Validate Confirmation Summary

**User conversation:**
```
User: 1 (select service)
Bot: Nome?
User: Bruno Rosa
Bot: Telefone OK?
User: 1 (yes)
Bot: Email?
User: clima.cocal.2025@gmail.com
Bot: Cidade?
User: Cocal-GO
Bot: [SHOWS SUMMARY]
```

**Expected confirmation summary:**
```
✅ Perfeito! Veja o resumo dos seus dados:

👤 Nome: Bruno Rosa          ✅ (not "não informado")
📱 Telefone: (61) 81755-748  ✅
📧 E-mail: clima.cocal.2025@gmail.com  ✅ (not "não informado")
📍 Cidade: Cocal-GO          ✅
☀️ Serviço: Energia Solar   ✅ (not "Não informado")
```

---

## 📊 VALIDATION CHECKLIST

- [ ] V100 code generated with field name changes
- [ ] Workflow updated with V100 State Machine code
- [ ] Test greeting → service → name → phone → email → city → confirmation
- [ ] Database shows `collected_data` populated (not empty `{}`)
- [ ] Database shows `service_type`, `contact_name`, `contact_email`, `city` populated
- [ ] Confirmation summary shows all fields correctly (no "não informado")
- [ ] Service 1 (Solar) triggers WF06 correctly after confirmation
- [ ] WF06 returns dates correctly to WF02
- [ ] Complete flow: greeting → confirmation → WF06 → scheduling works

---

## 🔗 RELATED ISSUES

- **V98**: State Machine routing to wrong state (fixed in V99)
- **V99**: Data preservation between states (fixed data merging)
- **V100**: Field name mismatch causing database persistence failure ✅ THIS FIX

---

**Date**: 2026-04-27
**Version**: V100 Collected Data Field Name Fix
**Impact**: CRITICAL - Prevents all user data from being saved to database
