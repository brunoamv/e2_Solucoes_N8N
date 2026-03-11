# V66 Correction States - Production-Ready Plan

> **Objective**: Add complete data correction flow (5 new states + SQL UPDATE logic)
> **Status**: 📝 Planning | **Date**: 2026-03-11
> **Base Version**: V65 UX Complete Fix | **Target**: Production Ready

---

## 🎯 Executive Summary

**V66 completes the V65 vision** by implementing the missing data correction functionality, allowing users to selectively fix their information without restarting the entire conversation.

**Impact**:
- 📈 **Reduce Abandonment**: Users can fix typos instead of giving up
- 📊 **Improve Data Quality**: Corrections are tracked and auditable
- ✅ **Complete UX Flow**: All 3 confirmation options fully functional
- 🚀 **Production Ready**: Comprehensive testing and validation

**Risk Level**: 🟡 **Medium** (adds new states but preserves working V65 logic)

---

## 📊 V66 Scope Analysis

### What V65 Delivered ✅
- **Templates**: 14 total (12 base + 2 redirects)
- **States**: 8 (greeting → confirmation)
- **Confirmation UX**: 3 clear options with emojis
- **Option 1**: Agendar (triggers scheduling/handoff) ✅ WORKING
- **Option 2**: Não agora (triggers handoff) ✅ WORKING
- **Option 3**: Corrigir ⚠️ **SHOWS MESSAGE BUT NO FUNCTIONALITY**

### What V66 Must Add 🎯
- **States**: +5 correction states (13 total)
- **Templates**: +11 correction templates (25 total)
- **SQL Logic**: UPDATE queries for each field
- **Validation**: Reuse existing validators
- **Loop Protection**: Prevent infinite correction cycles

---

## 🔄 V66 Complete Flow States (13 Total)

### Existing States (8) - Preserved from V65
```
1. greeting               → Show menu (5 services)
2. service_selection      → Capture service (1-5)
3. collect_name           → Get name
4. collect_phone_whatsapp_confirmation → Confirm WhatsApp
5. collect_phone_alternative → Alternative phone (if option 2)
6. collect_email          → Email or skip
7. collect_city           → City
8. confirmation           → Summary + 3 options
   ├─ "1" → scheduling/handoff ✅
   ├─ "2" → handoff ✅
   └─ "3" → correction_field_selection ⏳ V66
```

### New Correction States (5) - V66 Addition
```
9. correction_field_selection    → Choose field to correct (1-4)
   ├─ "1" → correction_name
   ├─ "2" → correction_phone
   ├─ "3" → correction_email
   └─ "4" → correction_city

10. correction_name              → Collect corrected name
    → UPDATE PostgreSQL → Return to confirmation

11. correction_phone             → Collect corrected phone
    → UPDATE PostgreSQL → Return to confirmation

12. correction_email             → Collect corrected email
    → UPDATE PostgreSQL → Return to confirmation

13. correction_city              → Collect corrected city
    → UPDATE PostgreSQL → Return to confirmation
```

---

## 📝 V66 Template Inventory (25 Total)

### From V65 (14) - No Changes
1. `greeting` - Welcome menu
2. `invalid_service` - Invalid service option
3. `service_acknowledged` - Service selected, ask name
4. `invalid_name` - Invalid name format
5. `phone_whatsapp_confirm` - Confirm WhatsApp number
6. `phone_alternative` - Ask alternative phone
7. `invalid_phone` - Invalid phone format
8. `email_request` - Ask email
9. `invalid_email` - Invalid email format
10. `city_request` - Ask city
11. `invalid_city` - Invalid city format
12. `confirmation` - Summary with 3 options ✅
13. `invalid_confirmation` - Invalid confirmation option
14. `scheduling_redirect` - Before scheduling trigger
15. `handoff_comercial` - Before handoff trigger

### V66 New Templates (11) - Correction Flow
16. `ask_correction_field` - Menu to select field (1-4)
17. `invalid_correction_field` - Invalid field selection
18. `correction_prompt_name` - Prompt for new name
19. `correction_prompt_phone` - Prompt for new phone
20. `correction_prompt_email` - Prompt for new email
21. `correction_prompt_city` - Prompt for new city
22. `correction_success_name` - Confirmation message for name
23. `correction_success_phone` - Confirmation message for phone
24. `correction_success_email` - Confirmation message for email
25. `correction_success_city` - Confirmation message for city

**Note**: Using individual success messages per field for better UX personalization

---

## 🔨 V66 Template Specifications

### Correction Field Selection Menu
```javascript
ask_correction_field: `🔧 *Sem problemas! Vamos corrigir.*

Qual dado você quer alterar?

1️⃣ *Nome* (atual: {{name}})
2️⃣ *Telefone* (atual: {{phone}})
3️⃣ *E-mail* (atual: {{email}})
4️⃣ *Cidade* (atual: {{city}})

_Digite o número do campo que deseja corrigir:_`,

invalid_correction_field: `❌ *Opção inválida*

Por favor, escolha um número de 1 a 4 para o campo que deseja corrigir.`
```

### Correction Prompts (4)
```javascript
correction_prompt_name: `👤 *Corrigindo Nome*

Nome atual: *{{name}}*

Digite o nome correto:
_Exemplo: Maria Silva Santos_`,

correction_prompt_phone: `📱 *Corrigindo Telefone*

Telefone atual: *{{phone}}*

Digite o telefone correto (com DDD):
_Exemplo: (62) 98765-4321_`,

correction_prompt_email: `📧 *Corrigindo E-mail*

E-mail atual: *{{email}}*

Digite o e-mail correto:
_Exemplo: maria@email.com_

Ou digite *pular* se não quiser informar.`,

correction_prompt_city: `📍 *Corrigindo Cidade*

Cidade atual: *{{city}}*

Digite a cidade correta:
_Exemplo: Goiânia_`
```

### Success Messages (4)
```javascript
correction_success_name: `✅ *Nome corrigido com sucesso!*

Nome anterior: {{old_value}}
Nome novo: *{{new_value}}*

Voltando para a confirmação...`,

correction_success_phone: `✅ *Telefone corrigido com sucesso!*

Telefone anterior: {{old_value}}
Telefone novo: *{{new_value}}*

Voltando para a confirmação...`,

correction_success_email: `✅ *E-mail corrigido com sucesso!*

E-mail anterior: {{old_value}}
E-mail novo: *{{new_value}}*

Voltando para a confirmação...`,

correction_success_city: `✅ *Cidade corrigida com sucesso!*

Cidade anterior: {{old_value}}
Cidade nova: *{{new_value}}*

Voltando para a confirmação...`
```

---

## 🗃️ V66 Database UPDATE Queries

### Field Mapping
```javascript
const fieldMapping = {
  '1': {
    db_field: 'lead_name',
    jsonb_key: 'lead_name',
    display: 'Nome',
    validator: validateName
  },
  '2': {
    db_field: 'contact_phone',
    jsonb_key: 'contact_phone',
    display: 'Telefone',
    validator: validatePhone
  },
  '3': {
    db_field: 'contact_email',
    jsonb_key: 'email',
    display: 'E-mail',
    validator: validateEmail
  },
  '4': {
    db_field: 'city',
    jsonb_key: 'city',
    display: 'Cidade',
    validator: validateCity
  }
};
```

### SQL UPDATE Template
```sql
-- Template for field correction with JSONB update
UPDATE conversations
SET
    -- Update direct column (for indexed queries)
    ${FIELD_NAME} = $1,

    -- Update collected_data JSONB (for state machine)
    collected_data = jsonb_set(
        collected_data,
        '{${JSONB_KEY}}',
        to_jsonb($1)
    ),

    -- Return to confirmation state
    current_state = 'coletando_dados',
    state_machine_state = 'confirmation',

    -- Update timestamp
    updated_at = NOW()

WHERE conversation_id = $2
  AND phone_number = $3

RETURNING
    conversation_id,
    phone_number,
    collected_data,
    current_state,
    state_machine_state,
    updated_at;
```

### Example: Correct Name
```sql
UPDATE conversations
SET
    contact_name = 'Bruno Rosa Silva',
    collected_data = jsonb_set(
        collected_data,
        '{lead_name}',
        to_jsonb('Bruno Rosa Silva')
    ),
    current_state = 'coletando_dados',
    state_machine_state = 'confirmation',
    updated_at = NOW()
WHERE conversation_id = 'conv_123'
  AND phone_number = '556299999999'
RETURNING *;
```

### Example: Correct Phone
```sql
UPDATE conversations
SET
    contact_phone = '62999998888',
    phone_number = '5562999998888',  -- Also update main phone if needed
    collected_data = jsonb_set(
        collected_data,
        '{contact_phone}',
        to_jsonb('62999998888')
    ),
    current_state = 'coletando_dados',
    state_machine_state = 'confirmation',
    updated_at = NOW()
WHERE conversation_id = 'conv_123'
RETURNING *;
```

---

## 🔍 V66 State Machine Logic

### State 8: Confirmation (Modified)
```javascript
case 'confirmation':
  console.log('V66: Processing CONFIRMATION state');

  // Option 1: Agendar visita
  if (message === '1') {
    const serviceSelected = currentData.service_selected || '1';

    if (serviceSelected === '1' || serviceSelected === '3') {
      responseText = templates.scheduling_redirect;
      nextStage = 'scheduling';
      updateData.status = 'scheduling';
    } else {
      responseText = templates.handoff_comercial;
      nextStage = 'handoff_comercial';
      updateData.status = 'handoff';
    }
  }

  // Option 2: Falar com pessoa
  else if (message === '2') {
    responseText = templates.handoff_comercial;
    nextStage = 'handoff_comercial';
    updateData.status = 'handoff';
  }

  // Option 3: Corrigir dados ← V66 NEW FUNCTIONALITY
  else if (message === '3') {
    console.log('V66: User chose correction option');

    // Build correction menu with current data
    const leadName = currentData.lead_name || 'não informado';
    const phoneNumber = currentData.contact_phone || currentData.phone_number || 'não informado';
    const email = currentData.email || 'não informado';
    const city = currentData.city || 'não informado';

    responseText = templates.ask_correction_field
      .replace('{{name}}', leadName)
      .replace('{{phone}}', formatPhoneDisplay(phoneNumber))
      .replace('{{email}}', email)
      .replace('{{city}}', city);

    nextStage = 'correction_field_selection';

    // V66: Store correction context
    updateData.correction_in_progress = true;
    updateData.correction_attempts = (currentData.correction_attempts || 0) + 1;

    // V66: Loop protection - max 5 corrections per conversation
    if (updateData.correction_attempts > 5) {
      console.warn('V66: Maximum correction attempts reached');
      responseText = `⚠️ *Você já corrigiu dados 5 vezes.*\n\n` +
                    `Para sua segurança, vou encaminhar para nossa equipe.\n\n` +
                    templates.handoff_comercial;
      nextStage = 'handoff_comercial';
      updateData.status = 'handoff';
      updateData.correction_in_progress = false;
    }
  }

  // Invalid option
  else {
    responseText = templates.invalid_confirmation;
    nextStage = 'confirmation';
  }
  break;
```

### State 9: Correction Field Selection (NEW)
```javascript
case 'correction_field_selection':
  console.log('V66: Processing CORRECTION_FIELD_SELECTION state');

  if (/^[1-4]$/.test(message)) {
    const selectedField = message;
    console.log('V66: User wants to correct field:', selectedField);

    // Get current values for prompts
    const currentName = currentData.lead_name || 'não informado';
    const currentPhone = formatPhoneDisplay(currentData.contact_phone || currentData.phone_number || '');
    const currentEmail = currentData.email || 'não informado';
    const currentCity = currentData.city || 'não informado';

    // Store which field is being corrected
    updateData.correcting_field = selectedField;
    updateData.correction_field_name = fieldMapping[selectedField].display;

    switch (selectedField) {
      case '1': // Name
        responseText = templates.correction_prompt_name
          .replace('{{name}}', currentName);
        nextStage = 'correction_name';
        break;

      case '2': // Phone
        responseText = templates.correction_prompt_phone
          .replace('{{phone}}', currentPhone);
        nextStage = 'correction_phone';
        break;

      case '3': // Email
        responseText = templates.correction_prompt_email
          .replace('{{email}}', currentEmail);
        nextStage = 'correction_email';
        break;

      case '4': // City
        responseText = templates.correction_prompt_city
          .replace('{{city}}', currentCity);
        nextStage = 'correction_city';
        break;
    }

  } else {
    console.log('V66: Invalid correction field selection');
    responseText = templates.invalid_correction_field;
    nextStage = 'correction_field_selection';
  }
  break;
```

### State 10-13: Correction States (NEW)
```javascript
// ===== STATE 10: CORRECTION NAME =====
case 'correction_name':
  console.log('V66: Processing CORRECTION_NAME state');

  const trimmedName = message.trim();

  // Reuse existing name validation
  if (trimmedName.length >= 2 && !/^[0-9]+$/.test(trimmedName)) {
    console.log('V66: Valid corrected name:', trimmedName);

    const oldName = currentData.lead_name || 'não informado';

    // Store in updateData for SQL UPDATE
    updateData.lead_name = trimmedName;
    updateData.contact_name = trimmedName;
    updateData.correction_old_value = oldName;
    updateData.correction_new_value = trimmedName;
    updateData.needs_db_update = true;  // ← TRIGGER UPDATE QUERY
    updateData.update_field = 'lead_name';

    // Show success message
    responseText = templates.correction_success_name
      .replace('{{old_value}}', oldName)
      .replace('{{new_value}}', trimmedName);

    nextStage = 'confirmation';
    updateData.correction_in_progress = false;

  } else {
    console.log('V66: Invalid corrected name format');
    responseText = `${templates.invalid_name}\n\n${templates.correction_prompt_name.replace('{{name}}', currentData.lead_name || '')}`;
    nextStage = 'correction_name';
  }
  break;

// ===== STATE 11: CORRECTION PHONE =====
case 'correction_phone':
  console.log('V66: Processing CORRECTION_PHONE state');

  const phoneRegex = /^\\(?\\d{2}\\)?\\s?9?\\d{4}[-\\s]?\\d{4}$/;

  if (phoneRegex.test(message)) {
    console.log('V66: Valid corrected phone:', message);

    const cleanedPhone = message.replace(/\\D/g, '');
    const phoneWithCode = cleanedPhone.startsWith('55') ? cleanedPhone : '55' + cleanedPhone;
    const oldPhone = currentData.contact_phone || currentData.phone_number || 'não informado';

    updateData.contact_phone = cleanedPhone;
    updateData.phone_number = phoneWithCode;
    updateData.correction_old_value = formatPhoneDisplay(oldPhone);
    updateData.correction_new_value = formatPhoneDisplay(cleanedPhone);
    updateData.needs_db_update = true;
    updateData.update_field = 'contact_phone';

    responseText = templates.correction_success_phone
      .replace('{{old_value}}', formatPhoneDisplay(oldPhone))
      .replace('{{new_value}}', formatPhoneDisplay(cleanedPhone));

    nextStage = 'confirmation';
    updateData.correction_in_progress = false;

  } else {
    console.log('V66: Invalid corrected phone format');
    responseText = `${templates.invalid_phone}\n\n${templates.correction_prompt_phone.replace('{{phone}}', formatPhoneDisplay(currentData.contact_phone || ''))}`;
    nextStage = 'correction_phone';
  }
  break;

// ===== STATE 12: CORRECTION EMAIL =====
case 'correction_email':
  console.log('V66: Processing CORRECTION_EMAIL state');

  if (message === 'pular') {
    const oldEmail = currentData.email || 'não informado';

    updateData.email = 'não informado';
    updateData.correction_old_value = oldEmail;
    updateData.correction_new_value = 'não informado';
    updateData.needs_db_update = true;
    updateData.update_field = 'email';

    responseText = templates.correction_success_email
      .replace('{{old_value}}', oldEmail)
      .replace('{{new_value}}', 'não informado');

    nextStage = 'confirmation';
    updateData.correction_in_progress = false;

  } else {
    const emailRegex = /^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/;

    if (emailRegex.test(message)) {
      console.log('V66: Valid corrected email:', message);

      const oldEmail = currentData.email || 'não informado';

      updateData.email = message;
      updateData.contact_email = message;
      updateData.correction_old_value = oldEmail;
      updateData.correction_new_value = message;
      updateData.needs_db_update = true;
      updateData.update_field = 'email';

      responseText = templates.correction_success_email
        .replace('{{old_value}}', oldEmail)
        .replace('{{new_value}}', message);

      nextStage = 'confirmation';
      updateData.correction_in_progress = false;

    } else {
      console.log('V66: Invalid corrected email format');
      responseText = `${templates.invalid_email}\n\n${templates.correction_prompt_email.replace('{{email}}', currentData.email || '')}`;
      nextStage = 'correction_email';
    }
  }
  break;

// ===== STATE 13: CORRECTION CITY =====
case 'correction_city':
  console.log('V66: Processing CORRECTION_CITY state');

  if (message.length >= 2) {
    console.log('V66: Valid corrected city:', message);

    const oldCity = currentData.city || 'não informado';

    updateData.city = message;
    updateData.correction_old_value = oldCity;
    updateData.correction_new_value = message;
    updateData.needs_db_update = true;
    updateData.update_field = 'city';

    responseText = templates.correction_success_city
      .replace('{{old_value}}', oldCity)
      .replace('{{new_value}}', message);

    nextStage = 'confirmation';
    updateData.correction_in_progress = false;

  } else {
    console.log('V66: Invalid corrected city (too short)');
    responseText = `${templates.invalid_city}\n\n${templates.correction_prompt_city.replace('{{city}}', currentData.city || '')}`;
    nextStage = 'correction_city';
  }
  break;
```

---

## 🔄 V66 Build Update Queries Logic

### Add Correction UPDATE Query Builder
```javascript
// In Build Update Queries node - V66 Addition

// Check if correction UPDATE is needed
if (inputData.needs_db_update && inputData.update_field) {
  console.log('V66: Building correction UPDATE query for field:', inputData.update_field);

  const fieldConfig = {
    'lead_name': {
      db_column: 'contact_name',
      jsonb_key: 'lead_name'
    },
    'contact_phone': {
      db_column: 'contact_phone',
      jsonb_key: 'contact_phone',
      also_update: 'phone_number'  // Also update main phone
    },
    'email': {
      db_column: 'contact_email',
      jsonb_key: 'email'
    },
    'city': {
      db_column: 'city',
      jsonb_key: 'city'
    }
  };

  const config = fieldConfig[inputData.update_field];
  const newValue = escapeSql(inputData[inputData.update_field] || '');

  // Build UPDATE query
  let query_correction_update = `
  UPDATE conversations
  SET
    ${config.db_column} = '${newValue}',
    ${config.also_update ? config.also_update + " = '" + (inputData[config.also_update] || newValue) + "'," : ''}
    collected_data = jsonb_set(
      collected_data,
      '{${config.jsonb_key}}',
      to_jsonb('${newValue}')
    ),
    current_state = 'coletando_dados',
    state_machine_state = 'confirmation',
    updated_at = NOW()
  WHERE conversation_id = '${conversation_id}'
    AND phone_number IN ('${phone_with_code}', '${phone_without_code}')
  RETURNING
    conversation_id,
    phone_number,
    collected_data,
    ${config.db_column} as corrected_field,
    current_state,
    state_machine_state,
    updated_at
  `.trim();

  console.log('V66: Correction UPDATE query built for', config.db_column);

  // Add to return object
  return {
    ...standardQueries,
    query_correction_update,
    correction_field_updated: inputData.update_field,
    correction_applied: true
  };
}
```

---

## 🧪 V66 Test Plan (15 Scenarios)

### Category A: Correction Happy Path (5 tests)

#### Test 1: Correct Name
```
Input: Complete flow → "3" at confirmation → "1" → "Bruno Rosa Silva"
Expected:
  ✅ Shows correction menu with current name
  ✅ Prompts for new name
  ✅ Validates name format
  ✅ UPDATE query updates contact_name AND collected_data.lead_name
  ✅ Shows success message with old → new values
  ✅ Returns to confirmation with UPDATED name visible
  ✅ User can choose option 1 or 2 to proceed
```

#### Test 2: Correct Phone
```
Input: Complete flow → "3" → "2" → "(62)99999-8888"
Expected:
  ✅ Validates phone format
  ✅ UPDATE query updates contact_phone, phone_number, AND collected_data
  ✅ Shows success message
  ✅ Returns to confirmation with UPDATED phone
```

#### Test 3: Correct Email
```
Input: Complete flow → "3" → "3" → "novo@email.com"
Expected:
  ✅ Validates email format
  ✅ UPDATE query updates contact_email AND collected_data.email
  ✅ Returns to confirmation with UPDATED email
```

#### Test 4: Skip Email Correction
```
Input: Complete flow → "3" → "3" → "pular"
Expected:
  ✅ Accepts "pular" as valid
  ✅ Updates email to "não informado"
  ✅ Returns to confirmation
```

#### Test 5: Correct City
```
Input: Complete flow → "3" → "4" → "Aparecida de Goiânia"
Expected:
  ✅ Validates city (min 2 chars)
  ✅ UPDATE query updates city AND collected_data.city
  ✅ Returns to confirmation with UPDATED city
```

### Category B: Multiple Corrections (2 tests)

#### Test 6: Sequential Corrections
```
Input: flow → "3" → "3" → "email@test.com" → "3" → "4" → "Goiânia" → "1"
Expected:
  ✅ First correction (email) succeeds
  ✅ Returns to confirmation with updated email
  ✅ Second correction (city) succeeds
  ✅ Returns to confirmation with updated city AND email
  ✅ Final confirmation option 1 triggers scheduling
  ✅ Both UPDATEs persisted in PostgreSQL
```

#### Test 7: Correction Loop Protection
```
Input: Complete flow → Attempt 6 corrections in sequence
Expected:
  ✅ First 5 corrections work normally
  ✅ 6th attempt shows warning message
  ✅ Automatically triggers handoff_comercial
  ✅ correction_attempts counter incremented correctly
```

### Category C: Validation Errors (4 tests)

#### Test 8: Invalid Field Selection
```
Input: flow → "3" → "5"
Expected:
  ✅ Shows invalid_correction_field message
  ✅ Remains in correction_field_selection state
  ✅ Re-shows menu with current values
```

#### Test 9: Invalid Name Format
```
Input: flow → "3" → "1" → "B"  (too short)
Expected:
  ✅ Shows invalid_name message
  ✅ Remains in correction_name state
  ✅ Prompts again with current name
```

#### Test 10: Invalid Phone Format
```
Input: flow → "3" → "2" → "123"
Expected:
  ✅ Shows invalid_phone message
  ✅ Remains in correction_phone state
  ✅ Prompts again with current phone
```

#### Test 11: Invalid Email Format
```
Input: flow → "3" → "3" → "not_an_email"
Expected:
  ✅ Shows invalid_email message
  ✅ Remains in correction_email state
  ✅ Allows "pular" as fallback
```

### Category D: Edge Cases (4 tests)

#### Test 12: Correction with Empty Current Data
```
Setup: User has "não informado" for some fields
Input: flow (skip email) → "3" → "3" → "new@email.com"
Expected:
  ✅ Shows "não informado" as current value
  ✅ Accepts new email
  ✅ Updates from "não informado" to actual email
```

#### Test 13: Phone Correction Updates WhatsApp Number
```
Input: flow → "3" → "2" → "(62)99999-7777"
Expected:
  ✅ Updates contact_phone field
  ✅ ALSO updates phone_number field (with country code 55)
  ✅ Future messages use new phone number
```

#### Test 14: Database Consistency Check
```
After any correction:
Expected:
  ✅ conversations.contact_name matches collected_data.lead_name
  ✅ conversations.contact_phone matches collected_data.contact_phone
  ✅ conversations.contact_email matches collected_data.email
  ✅ conversations.city matches collected_data.city
  ✅ updated_at timestamp is current
```

#### Test 15: Correction After Option 1 Previously Failed
```
Input: flow → "1" (agendar) → [scheduling fails] → "3" → correct data → "1" again
Expected:
  ✅ Correction works after failed scheduling attempt
  ✅ Retry with corrected data succeeds
```

---

## 📦 Implementation Checklist

### Phase 1: Generator Script Development
- [ ] Create `scripts/generate-workflow-v66-correction-states.py`
- [ ] Base on V65 generator (simplified approach)
- [ ] Add 5 new state cases to switch statement
- [ ] Add 11 new templates to templates object
- [ ] Add field mapping configuration
- [ ] Add correction UPDATE query builder
- [ ] Add loop protection logic (max 5 corrections)
- [ ] Validate syntax with markers (8 V66-specific strings)

### Phase 2: Workflow Generation
- [ ] Execute generator script
- [ ] Validate JSON syntax (`jq empty workflow.json`)
- [ ] Verify file size (~80-85 KB expected)
- [ ] Count states (should be 13)
- [ ] Count templates (should be 25)
- [ ] Check correction logic presence
- [ ] Manual code review of State Machine Logic node

### Phase 3: Database Preparation
- [ ] Backup production database (`pg_dump`)
- [ ] Test UPDATE queries in dev environment
- [ ] Verify JSONB updates work correctly
- [ ] Check indexes on corrected fields
- [ ] Ensure triggers don't interfere
- [ ] Test rollback scenario

### Phase 4: n8n Import and Configuration
- [ ] Import V66 workflow to n8n UI
- [ ] Verify all 27 nodes present
- [ ] Check PostgreSQL credentials configured
- [ ] Verify Evolution API connection
- [ ] Test workflow in n8n editor (no activation yet)
- [ ] Review State Machine Logic code visually

### Phase 5: Testing - Category A (Happy Path)
- [ ] Test 1: Correct Name
- [ ] Test 2: Correct Phone
- [ ] Test 3: Correct Email
- [ ] Test 4: Skip Email
- [ ] Test 5: Correct City
- [ ] Verify PostgreSQL updates for each

### Phase 6: Testing - Category B (Multiple)
- [ ] Test 6: Sequential Corrections
- [ ] Test 7: Loop Protection (6 attempts)
- [ ] Monitor correction_attempts counter

### Phase 7: Testing - Category C (Validation)
- [ ] Test 8: Invalid Field Selection
- [ ] Test 9: Invalid Name
- [ ] Test 10: Invalid Phone
- [ ] Test 11: Invalid Email
- [ ] Verify error messages match templates

### Phase 8: Testing - Category D (Edge Cases)
- [ ] Test 12: Empty Current Data
- [ ] Test 13: Phone Update Propagation
- [ ] Test 14: Database Consistency
- [ ] Test 15: Retry After Failed Scheduling

### Phase 9: Performance and Monitoring
- [ ] Monitor response times (<2s per message)
- [ ] Check UPDATE query performance (<100ms)
- [ ] Verify no memory leaks (10+ conversations)
- [ ] Test concurrent correction requests
- [ ] Monitor n8n logs for errors

### Phase 10: Documentation and Deployment
- [ ] Update CLAUDE.md with V66 status
- [ ] Create deployment runbook
- [ ] Document rollback procedure
- [ ] Update test scenarios documentation
- [ ] Create V66 success metrics dashboard

### Phase 11: Production Deployment
- [ ] Deactivate V65 in n8n
- [ ] Activate V66 in n8n
- [ ] Monitor first 5 conversations
- [ ] Check PostgreSQL for UPDATE queries
- [ ] Verify correction flow works end-to-end
- [ ] 100% deployment after 20 successful corrections

---

## 🚨 Risk Mitigation

### Risk 1: Infinite Correction Loop
**Likelihood**: Medium | **Impact**: High

**Mitigation**:
- Implement max 5 corrections per conversation
- Counter stored in `collected_data.correction_attempts`
- After 5 attempts, force handoff to human agent
- Log warning in n8n console

**Detection**:
```sql
SELECT phone_number, correction_attempts
FROM conversations
WHERE collected_data->>'correction_attempts' > '5';
```

### Risk 2: UPDATE Query Fails
**Likelihood**: Low | **Impact**: High

**Mitigation**:
- Test all UPDATE queries in dev first
- Add error logging in Build Update Queries node
- Fallback: Show error message and trigger handoff
- Database has updated_at timestamp for audit trail

**Recovery**:
- Manual SQL UPDATE if needed
- User data preserved in PostgreSQL
- Can retry correction after investigation

### Risk 3: Database Inconsistency
**Likelihood**: Low | **Impact**: Medium

**Mitigation**:
- UPDATE both direct column AND collected_data JSONB in same transaction
- Use RETURNING clause to verify update
- Add consistency check in Test 14

**Detection**:
```sql
-- Find inconsistencies
SELECT conversation_id, contact_name, collected_data->>'lead_name'
FROM conversations
WHERE contact_name != collected_data->>'lead_name';
```

### Risk 4: Performance Degradation
**Likelihood**: Low | **Impact**: Medium

**Mitigation**:
- UPDATE queries use indexed phone_number
- JSONB updates are efficient (<100ms)
- Test with 50+ concurrent corrections

**Monitoring**:
```sql
-- Monitor slow UPDATE queries
SELECT query, mean_exec_time
FROM pg_stat_statements
WHERE query LIKE '%UPDATE conversations%correction%'
ORDER BY mean_exec_time DESC;
```

---

## 📊 Success Metrics

### Functional Metrics
- ✅ **Correction Success Rate**: >95% of correction attempts succeed
- ✅ **Data Consistency**: 100% match between columns and JSONB
- ✅ **Validation Accuracy**: 100% invalid inputs rejected correctly
- ✅ **Loop Protection**: 0 conversations exceed 5 correction attempts

### Performance Metrics
- ✅ **Response Time**: <2s per message (including DB UPDATE)
- ✅ **UPDATE Query Speed**: <100ms per correction
- ✅ **No Memory Leaks**: Stable memory over 100+ corrections
- ✅ **No Error Spikes**: <0.1% error rate

### User Experience Metrics
- ✅ **Abandonment Reduction**: Measure before/after V66
- ✅ **Correction Usage**: Track how many users correct data
- ✅ **Most Corrected Field**: Identify UX improvement opportunities
- ✅ **Conversion Rate**: Users who correct → complete flow

### Business Metrics
- ✅ **Data Quality**: Reduction in invalid/missing data
- ✅ **Support Tickets**: Reduction in "wrong data" complaints
- ✅ **Lead Quality**: More accurate lead information for sales team

---

## 🔄 Rollback Plan

### Immediate Rollback (if V66 critical issues)
```bash
# 1. Deactivate V66
# n8n UI → Toggle V66: Inactive

# 2. Activate V65 (stable)
# n8n UI → Toggle V65: Active

# 3. Verify V65 working
# WhatsApp: "oi" → Verify menu appears

# Time: <2 minutes
```

### Database Rollback (if data corruption)
```bash
# ONLY IF UPDATE queries cause corruption (extremely unlikely)

# 1. Restore from backup
docker exec -i e2bot-postgres-dev psql -U postgres -d e2bot_dev < backup_pre_v66.sql

# 2. Verify restoration
docker exec -it e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT COUNT(*) FROM conversations;"

# Time: ~5-10 minutes
```

### Partial Rollback (disable corrections only)
```bash
# If corrections problematic but V65 features work

# 1. Edit V66 workflow in n8n
# 2. Change confirmation case 'message === "3"' to:
#    responseText = "⚠️ Correção temporariamente indisponível. " + templates.handoff_comercial;
#    nextStage = 'handoff_comercial';
# 3. Save workflow

# Time: <5 minutes
```

---

## 📚 Technical Specifications

### File Structure
```
scripts/
  ├── generate-workflow-v66-correction-states.py  (NEW - 600-700 lines)
  └── generate-workflow-v65-ux-complete-fix.py    (Base template)

n8n/workflows/
  ├── 02_ai_agent_conversation_V66_CORRECTION_STATES.json  (NEW - ~82 KB)
  ├── 02_ai_agent_conversation_V65_UX_COMPLETE_FIX.json    (Rollback)
  └── 02_ai_agent_conversation_V64_COMPLETE_REFACTOR.json  (Stable fallback)

docs/
  ├── PLAN/
  │   ├── V66_CORRECTION_STATES_COMPLETE.md  (This file)
  │   ├── V65_UX_COMPLETE_FIX.md             (Base spec)
  │   └── V64_COMPLETE_REFACTOR.md           (Reference)
  └── V66_GENERATION_SUCCESS.md  (Will be created after generation)
```

### Workflow Size Estimate
- **V64**: 67 KB (8 states, 12 templates)
- **V65**: 67 KB (8 states, 14 templates)
- **V66**: ~82 KB (+15 KB)
  - +5 states ≈ +8 KB
  - +11 templates ≈ +5 KB
  - +UPDATE query logic ≈ +2 KB

### Generator Script Complexity
- **V65 Generator**: 346 lines (templates only)
- **V66 Generator**: 600-700 lines (estimated)
  - +150 lines for 5 correction state cases
  - +100 lines for 11 new templates
  - +80 lines for field mapping and UPDATE query builder
  - +50 lines for loop protection logic
  - +20 lines for additional validation

---

## 🎯 V66 vs V65 Comparison

| Aspect | V65 (Current) | V66 (Target) | Change |
|--------|---------------|--------------|--------|
| **States** | 8 | 13 | +5 (correction) |
| **Templates** | 14 | 25 | +11 (correction) |
| **Confirmation Options** | 3 (option 3 broken) | 3 (all working) | ✅ Fixed |
| **Data Correction** | ❌ Not implemented | ✅ Full implementation | ✅ NEW |
| **SQL UPDATE Queries** | ❌ No | ✅ Yes (4 fields) | ✅ NEW |
| **Loop Protection** | N/A | Max 5 corrections | ✅ NEW |
| **Validation** | Collection only | Collection + Correction | ✅ Enhanced |
| **Workflow Size** | 67 KB | ~82 KB | +15 KB |
| **Risk Level** | Low (templates only) | Medium (new logic) | Higher |
| **Production Ready** | ✅ Yes (partial UX) | ✅ Yes (complete UX) | ✅ Complete |

---

## 📝 Post-Deployment Actions

### Week 1: Intensive Monitoring
- Monitor 100% of correction attempts
- Log all UPDATE queries and results
- Track correction_attempts counter
- Review n8n execution logs daily
- Check for any error patterns

### Week 2-4: Data Analysis
- Identify most corrected fields
- Calculate correction success rate
- Measure abandonment reduction
- Analyze correction → conversion rate
- Identify UX improvement opportunities

### Month 2+: Optimization
- Consider adding "cancel correction" option
- Add correction preview before UPDATE
- Implement correction analytics dashboard
- A/B test different correction prompts
- Optimize most-corrected field collection UX

---

## ✅ Definition of Done

V66 is production-ready when ALL criteria are met:

### Functional Completeness
- ✅ All 15 test scenarios pass
- ✅ All 5 correction states work correctly
- ✅ All 11 new templates render properly
- ✅ UPDATE queries persist to PostgreSQL
- ✅ Database consistency maintained (Test 14)
- ✅ Loop protection prevents >5 corrections

### Quality Standards
- ✅ Response time <2s per message
- ✅ UPDATE query time <100ms
- ✅ Zero data corruption incidents
- ✅ Error rate <0.1%
- ✅ All validation rules working

### Documentation
- ✅ Generator script documented
- ✅ Deployment runbook created
- ✅ Rollback procedure tested
- ✅ CLAUDE.md updated with V66 status
- ✅ Success report generated

### Stakeholder Approval
- ✅ Technical review approved
- ✅ Test results reviewed
- ✅ Deployment plan approved
- ✅ Monitoring plan in place
- ✅ Support team trained

---

## 🚀 Next Steps

1. **Review this plan** with stakeholders
2. **Create generator script** (`generate-workflow-v66-correction-states.py`)
3. **Generate V66 workflow** and validate JSON
4. **Execute testing plan** (all 15 scenarios)
5. **Monitor performance** (response times, UPDATE queries)
6. **Deploy to production** after all tests pass
7. **Monitor first week** intensively
8. **Analyze results** and optimize

---

**Author**: Claude Code
**Date**: 2026-03-11
**Version**: 1.0 (Production-Ready Complete Plan)
**Status**: ✅ Ready for Implementation

