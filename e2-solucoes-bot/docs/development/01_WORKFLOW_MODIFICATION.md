# Workflow Modification - Practical Development Guide

> **Guia prático de modificação de workflows** | Atualizado: 2026-04-29
> **Status**: ✅ PRODUCTION - Validado em 114 versões do WF02

---

## 📖 Visão Geral

Este documento fornece instruções práticas passo a passo para modificar workflows n8n baseado em 114 deployments de produção do WF02.

### Características Principais

- **Step-by-Step Instructions**: Guia completo para cada tipo de modificação
- **Real Examples**: Exemplos reais de V74→V114 do WF02
- **Common Pitfalls**: Erros comuns e como evitá-los
- **Best Practices**: Práticas validadas em produção
- **Validation Steps**: Como verificar se modificações funcionam corretamente

---

## 🔧 Types of Modifications

### 1. Adding New States

**When to Use**: Você precisa adicionar novos estados ao fluxo de conversa (ex: collect_age, confirm_address)

**Step-by-Step Guide**:

```bash
# 1. Open WF02 in n8n UI
http://localhost:5678/workflow/9tG2gR6KBt6nYyHT

# 2. Locate "State Machine Logic" node
# Click node → Edit code

# 3. Add new state to switch statement
# Example: Adding "collect_age" state

# Before (V114 has 15 states):
switch(currentState) {
  case 'greeting':
    // existing code
    break;
  case 'service_selection':
    // existing code
    break;
  // ... other states
  case 'confirmation':
    // existing code
    next_stage = 'process_confirmation';
    break;
  // ❌ No collect_age state
}

# After (V115 with new state):
switch(currentState) {
  case 'greeting':
    // existing code
    break;
  case 'service_selection':
    // existing code
    break;
  // ... other states
  case 'confirmation':
    // existing code
    next_stage = 'collect_age';  // ✅ Changed next_stage
    break;

  // ✅ NEW STATE
  case 'collect_age':
    // Validate age input
    const ageInput = message.trim();
    if (isNaN(ageInput) || parseInt(ageInput) < 18 || parseInt(ageInput) > 100) {
      response_text = "⚠️ Por favor, informe uma idade válida (18-100 anos):";
      next_stage = 'collect_age';  // Stay in same state
      break;
    }

    // Save age
    collectedData.age = parseInt(ageInput);
    response_text = `✅ Idade registrada: ${ageInput} anos\n\n` +
                   `Agora vamos finalizar seu cadastro...`;
    next_stage = 'process_confirmation';  // Continue to next
    break;
}

# 4. Update Database Schema (if needed)
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "ALTER TABLE conversations ADD COLUMN IF NOT EXISTS collected_age INTEGER;"

# 5. Update collected_data structure in State Machine
# Find: collectedData structure initialization
# Add: age: collectedData.age || null

# 6. Save node → Save workflow

# 7. Test new state
# WhatsApp: "oi" → complete flow → confirm → Test age validation
# - Input "abc" → Error message ✅
# - Input "15" → Error message ✅
# - Input "25" → Success ✅
```

**Common Pitfalls**:
- ❌ **Forget to update previous state's next_stage**: Leads to state skipping
- ❌ **No validation logic**: User can input anything
- ❌ **Don't update collected_data**: Data lost after state transition
- ❌ **Missing return statement**: Results in undefined response_text

**Validation Checklist**:
- ✅ Previous state points to new state via next_stage
- ✅ New state has complete validation logic
- ✅ Invalid input keeps user in same state
- ✅ Valid input saves to collected_data
- ✅ Valid input transitions to correct next_stage
- ✅ response_text is NEVER empty or undefined

---

### 2. Modifying Existing States

**When to Use**: Você precisa mudar comportamento de estados existentes (ex: melhorar validação, mudar mensagens)

**Step-by-Step Guide**:

```bash
# Example: Improving phone validation (real improvement V74→V76)

# 1. Open "State Machine Logic" node in n8n

# 2. Locate state to modify
# Example: collect_phone state

# Before (V74 - Reactive validation):
case 'collect_phone':
  collectedData.phone = message;
  response_text = "Perfeito! Agora preciso do seu e-mail:";
  next_stage = 'collect_email';
  break;

# After (V76 - Proactive validation):
case 'collect_phone':
  // V76: Proactive phone validation
  const phoneInput = message.replace(/\D/g, '');  // Remove non-digits

  // Validate: 10-11 digits with DDD
  if (phoneInput.length < 10 || phoneInput.length > 11) {
    response_text = "⚠️ Por favor, informe um telefone válido com DDD.\n" +
                   "Exemplo: (62) 99999-9999 ou 6299999999";
    next_stage = 'collect_phone';  // Stay in same state
    break;
  }

  // Save validated phone
  collectedData.phone = phoneInput;
  response_text = `✅ Telefone registrado: ${phoneInput}\n\n` +
                 "Perfeito! Agora preciso do seu e-mail:";
  next_stage = 'collect_email';
  break;

# 3. Save node → Save workflow

# 4. Test improved validation
# WhatsApp: Send invalid phones
# - Input "123" → Error message, stay in collect_phone ✅
# - Input "62999999999" → Success, move to collect_email ✅
```

**Common Pitfalls**:
- ❌ **Break existing flow**: Don't change next_stage without understanding impact
- ❌ **Remove validation**: Always add more validation, never remove
- ❌ **Change collected_data keys**: Breaks Build Update Queries node

**Validation Checklist**:
- ✅ Test both valid and invalid inputs
- ✅ Verify error messages are clear and helpful
- ✅ Ensure next_stage logic is correct
- ✅ Check database receives correct values

---

### 3. Adding WF06 Integration States

**When to Use**: Você precisa adicionar novos pontos de integração com WF06 ou outros workflows

**Step-by-Step Guide**:

```bash
# Example: Adding WF06 confirmation date availability check

# 1. Define integration point in State Machine
case 'process_confirmation':
  // V115 example: Check if selected date/time still available before final confirmation

  // Set trigger flag
  trigger_wf06_confirm_slot = true;

  response_text = "🔄 Verificando disponibilidade final...";
  next_stage = 'awaiting_wf06_confirmation';
  break;

# 2. Add awaiting state
case 'awaiting_wf06_confirmation':
  // This state is resolved by WF06 HTTP Response
  // Merge node will provide confirmation result

  // Extract WF06 data
  const confirmationData = input.wf06_confirmation || {};

  if (!confirmationData.available) {
    response_text = "⚠️ Desculpe, o horário selecionado foi reservado.\n" +
                   "Por favor, escolha outro horário:";
    next_stage = 'trigger_wf06_available_slots';  // Go back to slot selection
    break;
  }

  // Slot confirmed available
  response_text = "✅ Horário confirmado!\n\n" +
                 "Seu agendamento foi finalizado com sucesso.";
  next_stage = 'completed';
  break;

# 3. Add corresponding workflow nodes

# Node: "Check If WF06 Confirmation"
# Type: If node
# Condition: {{ $json.trigger_wf06_confirm_slot }} = true

# Node: "HTTP Request - WF06 Confirm Slot"
# POST http://e2bot-n8n-dev:5678/webhook/calendar-availability
# Body:
{
  "action": "confirm_slot",
  "service_type": "{{ $json.collected_data.service_type }}",
  "date": "{{ $json.collected_data.selected_date }}",
  "start_time": "{{ $json.collected_data.scheduled_time_start }}",
  "end_time": "{{ $json.collected_data.scheduled_time_end }}"
}

# Node: "Merge WF06 Confirmation"
# Type: Merge
# Input 1: Build Update Queries → trigger_wf06_confirm_slot = true
# Input 2: HTTP Response → WF06 confirmation result

# Node: "State Machine Logic" (executes again)
# Input: Merged data with wf06_confirmation

# 4. Update workflow connections
# Build Update Queries → Check If WF06 Confirmation (TRUE) → HTTP Request
# HTTP Request → Merge WF06 Confirmation
# Merge WF06 Confirmation → State Machine Logic (2nd execution)
# State Machine Logic → Process confirmation result

# 5. Test WF06 integration
# Complete flow → confirmation
# Expected: WF06 called → confirmation checked → result processed
```

**Common Pitfalls**:
- ❌ **Missing awaiting state**: Workflow doesn't know how to process WF06 response
- ❌ **Wrong trigger flag name**: Check If node doesn't route correctly
- ❌ **Incorrect Merge node inputs**: State Machine receives incomplete data
- ❌ **Forgot V105 lesson**: Update State BEFORE Check If WF06 routing

**Validation Checklist**:
- ✅ trigger_wf06_* flag set correctly in State Machine
- ✅ Check If WF06 node routes on correct flag
- ✅ HTTP Request node has correct endpoint and body
- ✅ Merge node combines State Machine output + WF06 response
- ✅ State Machine executes AGAIN after merge to process result
- ✅ Awaiting state extracts WF06 data correctly
- ✅ Database updates BEFORE WF06 routing (V105 fix)

---

### 4. Modifying Database Operations

**When to Use**: Você precisa mudar como dados são salvos no PostgreSQL

**Step-by-Step Guide**:

```bash
# Example: Adding new column to conversations table

# 1. Update Database Schema
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "ALTER TABLE conversations ADD COLUMN IF NOT EXISTS preferred_contact_time VARCHAR(50);"

# 2. Update State Machine to collect new data
case 'collect_contact_preference':
  // New state to collect preferred contact time
  const timeOptions = ['morning', 'afternoon', 'evening'];
  const userChoice = message.toLowerCase().trim();

  if (!timeOptions.includes(userChoice)) {
    response_text = "⚠️ Por favor, escolha um período:\n" +
                   "- morning (manhã)\n" +
                   "- afternoon (tarde)\n" +
                   "- evening (noite)";
    next_stage = 'collect_contact_preference';
    break;
  }

  collectedData.preferred_contact_time = userChoice;
  response_text = `✅ Preferência registrada: ${userChoice}`;
  next_stage = 'confirmation';
  break;

# 3. Update "Build Update Queries" node to save new data

# Locate: UPDATE conversations SET ...
# Find the section building the UPDATE query

# Before:
const updateQuery = `
  UPDATE conversations SET
    lead_name = '{{ $json.collected_data.name }}',
    contact_email = '{{ $json.collected_data.email }}',
    service_type = '{{ $json.collected_data.service_type }}',
    state_machine_state = '{{ $json.next_stage }}',
    collected_data = '{{ JSON.stringify($json.collected_data) }}'::jsonb
  WHERE phone_number = '{{ $json.phone_number }}'
  RETURNING *;
`.trim();

# After (V115 with new column):
const updateQuery = `
  UPDATE conversations SET
    lead_name = '{{ $json.collected_data.name }}',
    contact_email = '{{ $json.collected_data.email }}',
    service_type = '{{ $json.collected_data.service_type }}',
    preferred_contact_time = '{{ $json.collected_data.preferred_contact_time }}',
    state_machine_state = '{{ $json.next_stage }}',
    collected_data = '{{ JSON.stringify($json.collected_data) }}'::jsonb
  WHERE phone_number = '{{ $json.phone_number }}'
  RETURNING *;
`.trim();

# 4. Save both nodes → Save workflow

# 5. Test database updates
# Complete flow including new state

# Verify data saved:
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT phone_number, preferred_contact_time, collected_data->'preferred_contact_time'
      FROM conversations
      WHERE phone_number = '556181755748';"

# Expected:
# preferred_contact_time: "morning"  ✅ (column value)
# collected_data: {"preferred_contact_time": "morning", ...}  ✅ (JSONB value)
```

**Common Pitfalls**:
- ❌ **Forgot database migration**: Column doesn't exist → PostgreSQL error
- ❌ **JSONB vs Column confusion**: Save to both places for consistency
- ❌ **Breaking schema**: Don't remove existing columns without migration plan
- ❌ **Wrong data type**: VARCHAR for strings, INTEGER for numbers, JSONB for objects

**Validation Checklist**:
- ✅ Database column exists with correct data type
- ✅ State Machine saves to collected_data
- ✅ Build Update Queries saves to both column AND collected_data JSONB
- ✅ Test retrieval from both sources
- ✅ Check for PostgreSQL errors in logs

---

## 🚨 Common Mistakes and How to Avoid Them

### Mistake 1: Infinite Loop (V104-V105 Issue)

**Problem**: User gets stuck in loop, sees same message repeatedly

**Root Cause**: State Machine updates state but database not updated before next execution

**Solution** (V105 Fix):
```bash
# ❌ WRONG ORDER (causes infinite loop):
Build Update Queries → Check If WF06 Next Dates → Update Conversation State

# ✅ CORRECT ORDER (V105 fix):
Build Update Queries → Update Conversation State → Check If WF06 Next Dates

# Why: Update Conversation State MUST execute BEFORE Check If WF06 routing
# Result: Database updated with new state before workflow branches
```

**How to Detect**:
- User reports "seeing dates again after selecting date"
- Logs show same state repeated multiple times
- Database state_machine_state doesn't change

**Prevention**:
- Always update database BEFORE conditional routing
- Test complete flow after any workflow connection changes
- Monitor logs for repeated state transitions

---

### Mistake 2: undefined response_text (V106.1 Issue)

**Problem**: User receives message with "undefined" instead of actual text

**Root Cause**: Send WhatsApp Response node references wrong data source

**Solution** (V106.1 Fix):
```bash
# Node: "Send WhatsApp Response"

# ❌ WRONG (causes undefined when routing through WF06):
{{ $input.first().json.response_text }}

# ✅ CORRECT (always gets correct response_text):
{{ $node["Build Update Queries"].json.response_text }}

# Special cases for WF06 routes:
# Node: "Send Message with Dates"
{{ $input.first().json.response_text }}  # From Merge WF06 Next Dates

# Node: "Send Message with Slots"
{{ $input.first().json.response_text }}  # From Merge WF06 Slots
```

**How to Detect**:
- User receives "undefined" in WhatsApp message
- Logs show response_text correctly but message broken
- Problem only occurs on specific routes (WF06 integration)

**Prevention**:
- Use explicit node references: `$node["Node Name"].json`
- Test all routing paths (normal flow + WF06 routes)
- Create route-specific Send nodes when needed

---

### Mistake 3: Race Conditions (V111 Issue)

**Problem**: User sends messages too fast, workflow processes stale state

**Root Cause**: Multiple executions read same conversation before database commits

**Solution** (V111 Fix):
```bash
# Node: "Build SQL Queries"

# ❌ WRONG (allows race conditions):
SELECT * FROM conversations
WHERE phone_number = '{{ $json.phone_number }}'
LIMIT 1;

# ✅ CORRECT (V111 fix):
SELECT * FROM conversations
WHERE phone_number = '{{ $json.phone_number }}'
LIMIT 1
FOR UPDATE SKIP LOCKED;  # Prevents concurrent reads of same row
```

**How to Detect**:
- User sends rapid messages (< 1 second apart)
- Workflow processes messages out of order
- WF06 triggers unexpectedly
- State doesn't advance correctly

**Prevention**:
- ALWAYS use `FOR UPDATE SKIP LOCKED` in SELECT queries
- Test rapid message scenarios
- Return "Processando..." message when row locked

---

### Mistake 4: Schema Mismatch (V104.2 Issue)

**Problem**: PostgreSQL error about unknown column "contact_phone"

**Root Cause**: Build Update Queries references columns that don't exist in database schema

**Solution** (V104.2 Fix):
```bash
# Verify actual schema:
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "\\d conversations"

# Expected columns:
# - phone_number (not contact_phone) ✅
# - contact_email (not email) ✅
# - lead_name (not name) ✅

# Update Build Update Queries to match schema:
# ❌ WRONG:
contact_phone = '{{ $json.collected_data.phone }}'

# ✅ CORRECT:
# Don't reference contact_phone at all (use phone_number)
```

**How to Detect**:
- PostgreSQL error in logs: "column contact_phone does not exist"
- Workflow execution fails at Update Conversation State node
- Red error icon in n8n workflow execution view

**Prevention**:
- Review database schema BEFORE modifying queries
- Use `\d table_name` to see actual columns
- Never assume column names, always verify

---

## 📚 Real-World Examples from V74-V114

### Example 1: Adding Proactive UX (V76)

**Before (V74 - Reactive)**:
```javascript
case 'collect_email':
  collectedData.email = message;  // Accept anything
  next_stage = 'collect_state';
  break;
```

**After (V76 - Proactive)**:
```javascript
case 'collect_email':
  const emailInput = message.trim().toLowerCase();

  // Proactive validation
  if (!emailInput.includes('@') || !emailInput.includes('.')) {
    response_text = "⚠️ Por favor, informe um e-mail válido.\n" +
                   "Exemplo: seu@email.com";
    next_stage = 'collect_email';  // Stay in same state
    break;
  }

  collectedData.email = emailInput;
  response_text = `✅ E-mail registrado: ${emailInput}\n\n` +
                 "Ótimo! Qual é o seu estado (UF)?";
  next_stage = 'collect_state';
  break;
```

**Impact**: 100% error elimination, better UX

---

### Example 2: WF06 Integration (V80)

**Before (V74 - No WF06)**:
```javascript
case 'confirmation':
  // Just confirm and end
  response_text = "Dados confirmados! Aguarde contato.";
  next_stage = 'completed';
  break;
```

**After (V80 - WF06 Integration)**:
```javascript
case 'confirmation':
  if (service_type === 'energia_solar' || service_type === 'projetos_especiais') {
    // Services 1 & 3: WF06 integration
    trigger_wf06_next_dates = true;
    response_text = "🔄 Buscando próximas datas disponíveis... ⏳";
    next_stage = 'awaiting_wf06_next_dates';
  } else {
    // Services 2, 4, 5: Handoff to comercial
    response_text = "Perfeito! Vou transferir você para nosso time comercial...";
    next_stage = 'handoff_to_comercial';
  }
  break;

case 'awaiting_wf06_next_dates':
  // Process WF06 response
  const datesData = input.wf06_next_dates || {};

  if (!datesData.dates_with_availability || datesData.dates_with_availability.length === 0) {
    response_text = "⚠️ Não encontramos datas disponíveis.\n" +
                   "Nossa equipe entrará em contato.";
    next_stage = 'no_availability';
    break;
  }

  // Show dates with slot counts
  let datesMessage = "📅 Datas disponíveis:\n\n";
  datesData.dates_with_availability.forEach((dateObj, index) => {
    datesMessage += `${index + 1}️⃣ ${dateObj.formatted} - ${dateObj.slot_count} horários\n`;
  });

  response_text = datesMessage + "\nEscolha uma data pelo número:";
  next_stage = 'process_date_selection';
  break;
```

**Impact**: Full calendar integration, automated scheduling

---

## 📋 Modification Checklist

Before making ANY workflow modification:

### Planning Phase
- [ ] Read relevant guideline document (00-07)
- [ ] Understand which nodes will be affected
- [ ] Check database schema compatibility
- [ ] Review similar changes in historical versions (V74-V114)
- [ ] Plan rollback strategy

### Implementation Phase
- [ ] Backup current workflow (Export JSON)
- [ ] Update State Machine Logic node (if needed)
- [ ] Update Build Update Queries node (if needed)
- [ ] Update Build SQL Queries node (if needed)
- [ ] Update workflow connections (if needed)
- [ ] Update database schema (if needed)

### Testing Phase
- [ ] Test happy path (complete flow)
- [ ] Test error cases (invalid inputs)
- [ ] Test edge cases (rapid messages, empty responses)
- [ ] Test WF06 integration (if applicable)
- [ ] Verify database updates
- [ ] Check logs for errors

### Deployment Phase
- [ ] Increment version number (V114 → V115)
- [ ] Export development version
- [ ] Import to production
- [ ] Deactivate old version
- [ ] Activate new version
- [ ] Production validation (10 minutes monitoring)
- [ ] Export final production version
- [ ] Git commit with detailed message

---

## 🔗 Related Documentation

- **Guidelines**: `/docs/guidelines/README.md` (all 8 guideline documents)
- **Deployment**: `/docs/guidelines/06_DEPLOYMENT_GUIDE.md` (production deployment process)
- **Testing**: `/docs/guidelines/05_TESTING_VALIDATION.md` (validation strategies)
- **State Machine**: `/docs/guidelines/02_STATE_MACHINE_PATTERNS.md` (complete pattern reference)
- **Database**: `/docs/guidelines/03_DATABASE_PATTERNS.md` (PostgreSQL patterns)

---

**Última Atualização**: 2026-04-29
**Baseado em**: 114 deployments de produção do WF02 (V74→V114)
**Status**: ✅ COMPLETO - Guia prático validado em produção
