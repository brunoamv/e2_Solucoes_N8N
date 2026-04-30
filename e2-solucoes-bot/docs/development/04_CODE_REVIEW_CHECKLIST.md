# Code Review Checklist for WF02

> **Checklist de revisão de código** | Atualizado: 2026-04-29
> **Status**: ✅ PRODUCTION - Validado em 114 versões do WF02

---

## 📖 Visão Geral

Checklist completo de revisão de código para modificações no WF02 baseado em lessons learned de 114 deployments (V74→V114).

---

## ✅ Pre-Review Checklist

Antes de iniciar code review:

- [ ] **Backup criado**: Workflow atual exportado e commitado no git
- [ ] **Branch criada**: Mudanças em development version, não production
- [ ] **Objetivo claro**: Entendo o que a mudança deve fazer
- [ ] **Documentação lida**: Li guidelines relevantes (00-07)

---

## 🧩 State Machine Logic Review

### General Structure

- [ ] **Switch statement completo**: Todos os estados têm `case` e `break`
- [ ] **No fall-through**: Cada `case` termina com `break`
- [ ] **Default case**: Existe `default` case para estados desconhecidos
- [ ] **Consistent return**: Todos os paths retornam estrutura completa

```javascript
// ✅ GOOD: Complete structure
switch(currentState) {
  case 'greeting':
    response_text = "Olá! 👋";
    next_stage = 'service_selection';
    break;

  case 'service_selection':
    // ... logic ...
    break;

  default:
    response_text = "Desculpe, ocorreu um erro. Digite 'oi' para recomeçar.";
    next_stage = 'greeting';
    break;
}

// ❌ BAD: Missing break (fall-through)
switch(currentState) {
  case 'greeting':
    response_text = "Olá! 👋";
    next_stage = 'service_selection';
    // ❌ Missing break!

  case 'service_selection':
    // Will execute immediately after greeting!
}
```

---

### State Validation

- [ ] **Input validation**: Todos os inputs do usuário são validados
- [ ] **Error messages clear**: Mensagens de erro são claras e específicas
- [ ] **Stay in state on error**: Estados inválidos mantêm usuário no mesmo estado
- [ ] **Collected data saved**: Dados válidos são salvos em `collected_data`

```javascript
// ✅ GOOD: Complete validation
case 'collect_phone':
  const phoneInput = message.replace(/\D/g, '');

  // Validation
  if (phoneInput.length < 10 || phoneInput.length > 11) {
    response_text = "⚠️ Por favor, informe um telefone válido com DDD.\n" +
                   "Exemplo: (62) 99999-9999 ou 6299999999";
    next_stage = 'collect_phone';  // Stay in same state
    break;
  }

  // Save validated data
  collectedData.phone = phoneInput;
  response_text = `✅ Telefone registrado: ${phoneInput}`;
  next_stage = 'collect_email';
  break;

// ❌ BAD: No validation
case 'collect_phone':
  collectedData.phone = message;  // Accept anything!
  next_stage = 'collect_email';
  break;
```

---

### Response Text

- [ ] **Never empty**: `response_text` NUNCA é vazio ou undefined
- [ ] **Never placeholder**: Sem "TODO" ou placeholders em produção
- [ ] **Clear formatting**: Mensagens bem formatadas com emojis apropriados
- [ ] **User-friendly**: Linguagem clara e amigável (PT-BR)

```javascript
// ✅ GOOD: Complete response_text
response_text = `✅ Dados confirmados!\n\n` +
               `📋 Resumo:\n` +
               `Nome: ${collectedData.name}\n` +
               `Telefone: ${collectedData.phone}\n\n` +
               `Buscando datas disponíveis... ⏳`;

// ❌ BAD: Empty or undefined
response_text = "";  // ❌ Empty
response_text = undefined;  // ❌ Undefined
response_text = "TODO: Add confirmation message";  // ❌ Placeholder
```

---

### State Transitions

- [ ] **next_stage always set**: Sempre define `next_stage`
- [ ] **Valid state names**: `next_stage` aponta para estado que existe
- [ ] **Logical flow**: Transições fazem sentido no fluxo do usuário
- [ ] **No dead ends**: Todos os estados têm saída (exceto 'completed')

```javascript
// ✅ GOOD: Proper transition
case 'confirmation':
  if (message === '1') {
    // User confirmed
    trigger_wf06_next_dates = true;
    response_text = "🔄 Buscando datas disponíveis...";
    next_stage = 'awaiting_wf06_next_dates';  // Valid state
  } else {
    // User wants to edit
    response_text = "Qual dado deseja corrigir?";
    next_stage = 'collect_name';  // Back to beginning
  }
  break;

// ❌ BAD: Invalid state
case 'confirmation':
  next_stage = 'process_dates';  // ❌ State doesn't exist!
  break;
```

---

### collected_data Management

- [ ] **Initialized properly**: `collected_data` tem valores padrão
- [ ] **No undefined keys**: Todas as chaves têm valores (null se vazio)
- [ ] **Consistent keys**: Nomes de chaves consistentes em todo o código
- [ ] **Schema aligned**: Chaves correspondem ao schema do banco de dados

```javascript
// ✅ GOOD: Proper initialization
const collectedData = item.json.collected_data || {
  name: null,
  phone: null,
  email: null,
  state: null,
  city: null,
  service_type: null,
  selected_date: null,
  selected_slot: null,
  scheduled_time_start: null,  // V114 fix
  scheduled_time_end: null      // V114 fix
};

// ❌ BAD: Missing initialization
const collectedData = item.json.collected_data;  // Can be undefined!
```

---

## 🗄️ Build Update Queries Review

### Schema Compliance

- [ ] **Correct column names**: Usa nomes de colunas que existem no schema
- [ ] **No contact_phone**: Não referencia `contact_phone` (V104.2 fix)
- [ ] **Uses phone_number**: Usa `phone_number` para telefone
- [ ] **JSONB for collected_data**: `collected_data` é JSONB, não text

```sql
-- ✅ GOOD: Schema-compliant (V104.2)
UPDATE conversations SET
  lead_name = '{{ $json.collected_data.name }}',
  contact_email = '{{ $json.collected_data.email }}',
  service_type = '{{ $json.collected_data.service_type }}',
  state_machine_state = '{{ $json.next_stage }}',
  collected_data = '{{ JSON.stringify($json.collected_data) }}'::jsonb
WHERE phone_number = '{{ $json.phone_number }}'
RETURNING *;

-- ❌ BAD: Schema mismatch
UPDATE conversations SET
  contact_phone = '{{ $json.collected_data.phone }}',  -- ❌ Column doesn't exist!
  email = '{{ $json.collected_data.email }}',          -- ❌ Column is contact_email!
```

---

### V113 WF06 Suggestions Persistence

- [ ] **date_suggestions saved**: V113 salva sugestões de datas do WF06
- [ ] **slot_suggestions saved**: V113 salva sugestões de horários do WF06
- [ ] **JSONB format**: Ambos são salvos como JSONB arrays

```javascript
// ✅ GOOD: V113 WF06 suggestions persistence
const updateQueries = [];

// Build Update Queries 1 (date_suggestions)
if ($json.wf06_next_dates && $json.wf06_next_dates.dates_with_availability) {
  const dateSuggestions = $json.wf06_next_dates.dates_with_availability;

  updateQueries.push({
    query: `
      UPDATE conversations SET
        date_suggestions = '${JSON.stringify(dateSuggestions)}'::jsonb
      WHERE phone_number = '{{ $json.phone_number }}'
      RETURNING *;
    `.trim()
  });
}

// Build Update Queries 2 (slot_suggestions)
if ($json.wf06_available_slots && $json.wf06_available_slots.available_slots) {
  const slotSuggestions = $json.wf06_available_slots.available_slots;

  updateQueries.push({
    query: `
      UPDATE conversations SET
        slot_suggestions = '${JSON.stringify(slotSuggestions)}'::jsonb
      WHERE phone_number = '{{ $json.phone_number }}'
      RETURNING *;
    `.trim()
  });
}
```

---

### Query Safety

- [ ] **Parameterized**: Usa variáveis n8n, não string concatenation
- [ ] **SQL injection safe**: Não concatena user input diretamente
- [ ] **RETURNING clause**: Queries de UPDATE usam `RETURNING *`
- [ ] **Transaction safe**: Queries críticas em transações se necessário

```javascript
// ✅ GOOD: Parameterized query
const updateQuery = `
  UPDATE conversations SET
    lead_name = '{{ $json.collected_data.name }}',
    contact_email = '{{ $json.collected_data.email }}'
  WHERE phone_number = '{{ $json.phone_number }}'
  RETURNING *;
`.trim();

// ❌ BAD: String concatenation (SQL injection risk)
const updateQuery = `
  UPDATE conversations SET
    lead_name = '${collectedData.name}',  // ❌ Direct concatenation!
    contact_email = '${collectedData.email}'
  WHERE phone_number = '${phone_number}'
  RETURNING *;
`.trim();
```

---

## 🔒 Build SQL Queries Review

### V111 Row Locking

- [ ] **FOR UPDATE SKIP LOCKED**: Query de SELECT usa row locking (V111)
- [ ] **Prevents race conditions**: Evita processamento de estado obsoleto
- [ ] **Returns empty when locked**: Query retorna vazio se row está locked

```sql
-- ✅ GOOD: V111 row locking
SELECT
  *,
  COALESCE(state_machine_state, 'greeting') as state_for_machine
FROM conversations
WHERE phone_number IN (
  '{{ $json.phone_with_code }}',
  '{{ $json.phone_without_code }}'
)
ORDER BY updated_at DESC
LIMIT 1
FOR UPDATE SKIP LOCKED;  -- V111 CRITICAL FIX

-- ❌ BAD: No row locking (race conditions!)
SELECT * FROM conversations
WHERE phone_number = '{{ $json.phone_number }}'
LIMIT 1;
```

---

## 🔌 Workflow Connections Review

### V105 Routing Fix

- [ ] **Update BEFORE Check**: Update Conversation State executes BEFORE Check If WF06
- [ ] **Prevents infinite loop**: V105 fix evita loop infinito
- [ ] **Correct order**: Build Update Queries → Update State → Check If WF06

```bash
# ✅ GOOD: V105 correct routing
Build Update Queries → Update Conversation State → Check If WF06 Next Dates

# ❌ BAD: Wrong order (causes infinite loop)
Build Update Queries → Check If WF06 Next Dates → Update Conversation State
```

---

### WF06 Integration

- [ ] **Trigger flags correct**: `trigger_wf06_next_dates` e `trigger_wf06_available_slots`
- [ ] **Check If nodes**: Nodes verificam flags corretamente
- [ ] **HTTP Request nodes**: Chamam WF06 com payload correto
- [ ] **Merge nodes**: Combinam State Machine output + WF06 response
- [ ] **Awaiting states**: Processam resposta do WF06 corretamente

```javascript
// ✅ GOOD: Complete WF06 integration

// State Machine sets flag:
case 'confirmation':
  trigger_wf06_next_dates = true;
  response_text = "🔄 Buscando datas...";
  next_stage = 'awaiting_wf06_next_dates';
  break;

// Check If node routes on flag:
// {{ $json.trigger_wf06_next_dates }} = true

// HTTP Request calls WF06:
// POST http://e2bot-n8n-dev:5678/webhook/calendar-availability
// Body: { "action": "next_dates", ... }

// Merge combines responses:
// Input 1: Build Update Queries output
// Input 2: HTTP Request response

// State Machine processes merged data:
case 'awaiting_wf06_next_dates':
  const datesData = input.wf06_next_dates || {};
  // Process WF06 response...
  break;
```

---

### V106.1 response_text Routing

- [ ] **Explicit node reference**: Send nodes usam `$node["Node Name"].json`
- [ ] **Route-specific Send nodes**: Different Send nodes para different routes
- [ ] **No undefined messages**: Todos os Send nodes têm response_text válido

```javascript
// ✅ GOOD: V106.1 explicit reference
// Normal flow Send node:
{{ $node["Build Update Queries"].json.response_text }}

// WF06 dates Send node:
{{ $input.first().json.response_text }}  // From Merge WF06 Next Dates

// WF06 slots Send node:
{{ $input.first().json.response_text }}  // From Merge WF06 Slots

// ❌ BAD: Generic reference (causes undefined on WF06 routes)
{{ $input.first().json.response_text }}  // Wrong for all routes!
```

---

## 🧪 Testing Review

### Test Coverage

- [ ] **Happy path tested**: Fluxo completo funciona sem erros
- [ ] **Error cases tested**: Validações de entrada funcionam
- [ ] **Edge cases tested**: Mensagens rápidas, valores extremos
- [ ] **WF06 integration tested**: Se aplicável, WF06 integração funciona

```bash
# Test checklist:

# 1. Happy path (complete flow)
WhatsApp: "oi" → complete → "1" (agendar) → dates → slots → confirmation
Expected: All 15 states execute correctly ✅

# 2. Error cases (invalid inputs)
WhatsApp: Invalid phone "123", Invalid email "invalid", etc
Expected: Clear error messages, stay in same state ✅

# 3. Edge cases (race conditions)
Send 3 rapid messages (< 1 second apart)
Expected: V111 row locking prevents stale state processing ✅

# 4. WF06 integration
Service 1 → WF06 next_dates → select date → WF06 slots → select slot
Expected: Both WF06 calls work, suggestions saved (V113) ✅
```

---

### Database Validation

- [ ] **State saved correctly**: `state_machine_state` corresponde ao esperado
- [ ] **Data persisted**: `collected_data` contém todos os dados coletados
- [ ] **Suggestions saved**: V113 `date_suggestions` e `slot_suggestions` populados
- [ ] **TIME fields saved**: V114 `scheduled_time_start` e `scheduled_time_end` corretos

```bash
# Verify database after testing:
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT
        phone_number,
        state_machine_state,
        collected_data,
        date_suggestions,
        slot_suggestions
      FROM conversations
      WHERE phone_number = '556181755748';"

# Expected validation points:
# - state_machine_state: 'completed' or expected state ✅
# - collected_data: All fields populated correctly ✅
# - date_suggestions: JSONB array with WF06 dates (if applicable) ✅
# - slot_suggestions: JSONB array with WF06 slots (if applicable) ✅
# - scheduled_time_start/end: "08:00", "10:00" format (V114) ✅
```

---

## 📝 Documentation Review

### Code Comments

- [ ] **Critical sections commented**: V111, V113, V114 fixes têm comentários
- [ ] **Version tags present**: Mudanças marcadas com version (ex: "V115:")
- [ ] **Logic explained**: Lógica complexa tem explicação
- [ ] **No TODOs in production**: Sem placeholders em código de produção

```javascript
// ✅ GOOD: Clear comments with version tags
// V115: Enhanced phone validation with international format support
case 'collect_phone':
  // Remove all non-digit characters
  const phoneInput = message.replace(/\D/g, '');

  // V115: Support both 10-digit (landline) and 11-digit (mobile) numbers
  if (phoneInput.length < 10 || phoneInput.length > 11) {
    response_text = "⚠️ Por favor, informe um telefone válido com DDD.";
    next_stage = 'collect_phone';
    break;
  }

  // Save validated phone
  collectedData.phone = phoneInput;
  next_stage = 'collect_email';
  break;

// ❌ BAD: No comments or TODOs in production
case 'collect_phone':
  // TODO: Add better validation
  collectedData.phone = message;
  next_stage = 'collect_email';
  break;
```

---

### Deployment Documentation

- [ ] **README updated**: Se novos estados ou features, atualizar README
- [ ] **CLAUDE.md updated**: Versão de produção atualizada
- [ ] **Deployment guide created**: Se mudança significativa, criar guia de deployment

---

## 🚀 Deployment Review

### Pre-Deployment

- [ ] **Backup created**: Workflow atual exportado e commitado
- [ ] **Version incremented**: Versão nova (V114 → V115)
- [ ] **Git commits ready**: Commits preparados para deployment

### Post-Deployment

- [ ] **Production validation**: 10 minutos de monitoramento após deploy
- [ ] **No errors in logs**: Logs limpos sem erros críticos
- [ ] **Database state correct**: Estado do banco de dados correto
- [ ] **Rollback plan ready**: Sabe como fazer rollback se necessário

---

## 📋 Final Checklist

Antes de aprovar code review:

### Functionality
- [ ] All states work correctly
- [ ] All validations function properly
- [ ] WF06 integration works (if applicable)
- [ ] Database updates correctly
- [ ] No infinite loops or race conditions

### Code Quality
- [ ] No hardcoded values (use variables)
- [ ] No SQL injection vulnerabilities
- [ ] No undefined or empty response_text
- [ ] Proper error handling throughout
- [ ] Code follows existing patterns

### Critical Fixes
- [ ] V111 row locking present (FOR UPDATE SKIP LOCKED)
- [ ] V113 WF06 suggestions saved (if applicable)
- [ ] V114 TIME fields extracted (if applicable)
- [ ] V104.2 schema compliance (no contact_phone)
- [ ] V105 routing fix (Update BEFORE Check If WF06)
- [ ] V106.1 response_text routing (explicit node references)

### Testing
- [ ] Happy path tested
- [ ] Error cases tested
- [ ] Edge cases tested
- [ ] Database validated
- [ ] Logs checked

### Documentation
- [ ] Code commented appropriately
- [ ] Version tags added
- [ ] README updated (if needed)
- [ ] Deployment guide created (if significant)

### Deployment
- [ ] Backup created
- [ ] Version incremented
- [ ] Git commits prepared
- [ ] Rollback plan ready

---

## 🔗 Related Documentation

- **Workflow Modification**: `/docs/development/01_WORKFLOW_MODIFICATION.md`
- **Debugging Guide**: `/docs/development/02_DEBUGGING_GUIDE.md`
- **Common Tasks**: `/docs/development/03_COMMON_TASKS.md`
- **Testing Guide**: `/docs/guidelines/05_TESTING_VALIDATION.md`
- **Deployment Guide**: `/docs/guidelines/06_DEPLOYMENT_GUIDE.md`

---

**Última Atualização**: 2026-04-29
**Baseado em**: 114 deployments de produção do WF02 (V74→V114)
**Status**: ✅ COMPLETO - Checklist validado em produção
