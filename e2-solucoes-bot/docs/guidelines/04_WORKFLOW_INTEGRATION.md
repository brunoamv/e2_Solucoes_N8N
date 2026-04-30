# Workflow Integration Patterns

> **Comunicação entre workflows** | Atualizado: 2026-04-29
> **Status**: ✅ PRODUCTION - Microservices architecture em produção

---

## 📖 Visão Geral

O E2 Bot usa arquitetura de microservices onde workflows independentes se comunicam via HTTP Request nodes. Este padrão permite escalabilidade, testabilidade e manutenção independente de cada serviço.

### Características Principais

- **HTTP Request Communication**: Workflows se comunicam via webhook endpoints
- **Microservices Architecture**: Cada workflow é independente e testável
- **Async Pattern**: WF02 dispara WF05/WF07, não aguarda resposta
- **Sync Pattern**: WF02 ↔ WF06 comunicação síncrona com response data
- **Error Handling**: Retry logic e fallbacks para robustez
- **Data Passing**: JSON payload com dados mínimos necessários

---

## 🔄 Padrões de Comunicação

### 1. Synchronous Pattern (WF02 ↔ WF06)

**Uso**: Quando WF02 precisa de dados do WF06 para continuar fluxo.

```yaml
Flow:
  WF02:
    State: trigger_wf06_next_dates
    Action: HTTP Request → WF06 webhook
    Aguarda: Response com date_suggestions array
    Next State: awaiting_wf06_next_dates (processa dates)

  WF06:
    Recebe: { action: "next_dates", service_type: "energia_solar", count: 3 }
    Processa: Busca no Google Calendar
    Retorna: { dates_with_availability: [...] }

  WF02:
    Recebe Response: date_suggestions array
    Mostra para usuário: "1️⃣ - 15/05/2026 (8 horários)"
```

**HTTP Request Node Configuration** (WF02 → WF06):
```javascript
// Node: "HTTP Request - WF06 Next Dates"
{
  "method": "POST",
  "url": "http://e2bot-n8n-dev:5678/webhook/calendar-availability",
  "headers": {
    "Content-Type": "application/json"
  },
  "body": {
    "action": "next_dates",
    "service_type": "{{ $json.service_type }}",
    "count": 3,
    "duration_minutes": 120
  },
  "options": {
    "timeout": 10000,  // 10 segundos
    "retry": {
      "enabled": true,
      "maxRetries": 2,
      "retryInterval": 1000
    }
  }
}
```

**WF06 Webhook Response Format**:
```json
{
  "dates_with_availability": [
    {
      "date": "2026-05-15",
      "formatted": "15/05/2026",
      "slot_count": 8,
      "weekday": "Sexta-feira"
    },
    {
      "date": "2026-05-16",
      "formatted": "16/05/2026",
      "slot_count": 10,
      "weekday": "Sábado"
    }
  ]
}
```

### 2. Asynchronous Pattern (WF02 → WF05, WF07)

**Uso**: Quando WF02 dispara ação mas não precisa de response.

```yaml
Flow:
  WF02:
    State: scheduling
    Action 1: HTTP Request → WF05 (create appointment)
    Action 2: HTTP Request → WF07 (send email)
    Next State: completed (não aguarda responses)

  WF05:
    Recebe: { lead_name, lead_email, scheduled_date, ... }
    Processa: Cria appointment no Google Calendar + DB
    (WF02 não aguarda este resultado)

  WF07:
    Recebe: { lead_name, lead_email, template: "confirmation" }
    Processa: Envia email de confirmação
    (WF02 não aguarda este resultado)
```

**Benefícios do Async**:
- ✅ WF02 responde rápido ao usuário (não aguarda email/calendar)
- ✅ WF05/WF07 processam em background
- ✅ Falha em WF07 não afeta confirmação do agendamento

**HTTP Request Node Configuration** (WF02 → WF05):
```javascript
// Node: "HTTP Request - Trigger WF05"
{
  "method": "POST",
  "url": "http://e2bot-n8n-dev:5678/webhook/create-appointment",
  "headers": {
    "Content-Type": "application/json"
  },
  "body": {
    "lead_name": "{{ $json.collected_data.name }}",
    "lead_email": "{{ $json.collected_data.email }}",
    "service_type": "{{ $json.service_type }}",
    "scheduled_date": "{{ $json.collected_data.selected_date }}",
    "scheduled_time_start": "{{ $json.collected_data.scheduled_time_start }}",
    "scheduled_time_end": "{{ $json.collected_data.scheduled_time_end }}"
  },
  "options": {
    "ignoreResponseCode": true,  // Não falha se WF05 retorna erro
    "timeout": 5000
  }
}
```

---

## 🎯 Integration Workflows

### WF02 → WF06 (Calendar Availability Service)

**Objetivo**: Buscar datas e horários disponíveis no Google Calendar.

**Endpoints WF06**:
```yaml
next_dates:
  url: /webhook/calendar-availability
  method: POST
  payload:
    action: "next_dates"
    service_type: string
    count: number
    duration_minutes: number
  response:
    dates_with_availability: array

available_slots:
  url: /webhook/calendar-availability
  method: POST
  payload:
    action: "available_slots"
    service_type: string
    date: string (YYYY-MM-DD)
    duration_minutes: number
  response:
    available_slots: array
```

**Exemplo Completo**:
```javascript
// WF02 State Machine Logic: trigger_wf06_next_dates
case 'trigger_wf06_next_dates':
  response_text = `Buscando datas disponíveis...\n\n⏳ Aguarde...`;
  next_stage = 'awaiting_wf06_next_dates';
  trigger_wf06_next_dates = true;  // Flag para Check If WF06 node
  break;

// WF02 Check If WF06 Next Dates node
if (item.json.trigger_wf06_next_dates) {
  // Dispara HTTP Request para WF06
  return [{
    json: {
      action: "next_dates",
      service_type: item.json.service_type,
      count: 3,
      duration_minutes: 120
    }
  }];
}

// WF02 Merge WF06 Next Dates Response
const wf06Response = $input.item(1).json;  // HTTP Request response
const stateData = $input.item(0).json;     // State Machine data

return [{
  json: {
    ...stateData,
    date_suggestions: wf06Response.dates_with_availability  // Adiciona dates
  }
}];
```

### WF02 → WF05 (Appointment Scheduler)

**Objetivo**: Criar agendamento no Google Calendar e banco de dados.

**Endpoint WF05**:
```yaml
create_appointment:
  url: /webhook/create-appointment
  method: POST
  payload:
    lead_name: string
    lead_email: string
    service_type: string
    scheduled_date: string (YYYY-MM-DD)
    scheduled_time_start: string (HH:MM)
    scheduled_time_end: string (HH:MM)
    phone_number: string
  response:
    appointment_id: number
    google_calendar_event_id: string
```

**WF05 Processing**:
1. Cria evento no Google Calendar
2. Salva appointment no banco de dados
3. Dispara WF07 para enviar email de confirmação

### WF02 → WF07 (Email Sender)

**Objetivo**: Enviar email de confirmação de agendamento.

**Endpoint WF07**:
```yaml
send_email:
  url: /webhook/send-email
  method: POST
  payload:
    lead_name: string
    lead_email: string
    service_type: string
    template: string ("confirmation")
    scheduled_date: string
    scheduled_time: string
  response:
    email_id: number
    status: string ("sent" | "failed")
```

**WF07 Processing**:
1. Busca template HTML via nginx (HTTP Request)
2. Substitui variáveis no template
3. Envia email via SMTP (Port 465 SSL/TLS)
4. Salva log no banco de dados (INSERT...SELECT pattern)

---

## 🔧 HTTP Request Best Practices

### 1. Timeout Configuration

```javascript
// ✅ CORRETO: Sempre definir timeout
{
  "timeout": 10000,  // 10 segundos para operações síncronas
  "retry": {
    "enabled": true,
    "maxRetries": 2,
    "retryInterval": 1000
  }
}

// ❌ ERRADO: Sem timeout (pode travar workflow)
{
  "url": "...",
  "method": "POST"
  // Sem timeout definido
}
```

**Timeouts Recomendados**:
- WF06 (sync): 10 segundos
- WF05 (async): 5 segundos
- WF07 (async): 5 segundos

### 2. Error Handling

```javascript
// ✅ CORRETO: Handle errors gracefully
{
  "options": {
    "ignoreResponseCode": true,  // Não falha em 4xx/5xx
    "continueOnFail": true        // Continua workflow mesmo com erro
  }
}

// WF02: Check error no próximo node
const httpResponse = $input.first().json;
if (httpResponse.error || !httpResponse.dates_with_availability) {
  // Fallback: mostrar mensagem de erro amigável
  response_text = `Desculpe, não consegui buscar datas disponíveis.\n\n` +
                 `Nossa equipe entrará em contato em breve. 📞`;
  next_stage = 'completed';
}
```

### 3. Data Passing

```javascript
// ✅ CORRETO: Minimal payload (apenas dados necessários)
{
  "body": {
    "lead_name": "{{ $json.collected_data.name }}",
    "lead_email": "{{ $json.collected_data.email }}",
    "scheduled_date": "{{ $json.collected_data.selected_date }}"
  }
}

// ❌ ERRADO: Enviar objeto completo (dados desnecessários)
{
  "body": {
    "all_data": "{{ JSON.stringify($json) }}"
  }
}
```

### 4. Response Validation

```javascript
// ✅ CORRETO: Validar response antes de usar
const wf06Response = $input.item(1).json;

if (!wf06Response || !wf06Response.dates_with_availability) {
  // Response inválida ou erro
  return [{
    json: {
      error: "WF06 response invalid",
      fallback_message: "Erro ao buscar datas"
    }
  }];
}

// Usar response válida
return [{
  json: {
    date_suggestions: wf06Response.dates_with_availability
  }
}];
```

---

## 🏗️ Microservices Architecture

### Benefícios

1. **Independent Testing**: WF06 pode ser testado isoladamente
2. **Scalability**: Cada workflow pode escalar independentemente
3. **Maintenance**: Mudanças em WF06 não afetam WF02 (desde que API contrato seja mantido)
4. **Reusability**: WF06 pode ser usado por outros workflows no futuro

### WF06 as Independent Service

**Características**:
- **Stateless**: Não mantém estado entre requests
- **Single Responsibility**: Apenas calendar availability logic
- **API Contract**: Stable interface com versioning
- **Error Isolation**: Falhas em WF06 não quebram WF02

**API Versioning**:
```yaml
v2.0:
  - Empty calendar fix ✅
  - OAuth credential fix ✅
v2.1:
  - Input data source fix ✅
v2.2:
  - Response mode fix ✅
```

### Integration Testing

```bash
# 1. Test WF06 Independently
curl -X POST http://localhost:5678/webhook/calendar-availability \
  -H "Content-Type: application/json" \
  -d '{
    "action": "next_dates",
    "service_type": "energia_solar",
    "count": 3,
    "duration_minutes": 120
  }'

# Expected: dates_with_availability array com 3 datas

# 2. Test WF02 → WF06 Integration
# WhatsApp: "oi" → complete → "1" (agendar)
# Expected: WF02 shows 3 dates from WF06

# 3. Monitor Integration Logs
docker logs -f e2bot-n8n-dev 2>&1 | grep -E "WF02|WF06|HTTP"
```

---

## 🚨 Common Integration Issues

### Issue 1: WF06 Not Called (V105 Bug)

**Symptoms**:
- trigger_wf06_next_dates = true, mas WF06 não é chamado
- Estado avança sem chamar WF06

**Root Cause**: Update Conversation State executado DEPOIS de Check If WF06.

**Solution**: V105 Routing Fix
```
ANTES:
State Machine → Check If WF06 → Update State → Loop

DEPOIS (V105):
State Machine → Update State → Check If WF06 → Loop
```

**Verification**:
```bash
# Verificar ordem de execução nos logs
docker logs -f e2bot-n8n-dev | grep -E "V105:|Check If WF06"

# Expected:
# Update Conversation State: Saved state = trigger_wf06_next_dates
# Check If WF06: Flag detected = true  ✅
```

### Issue 2: Empty WF06 Response (V2 Bug)

**Symptoms**:
- WF06 crashes com "Cannot read properties of undefined"
- No dates returned

**Root Cause**: Empty Google Calendar (no events) → calendar.data undefined.

**Solution**: WF06 V2 Empty Calendar Fix
```javascript
// ANTES:
const events = calendar.data.items;  // ❌ Crash se calendar vazio

// DEPOIS (V2):
const events = calendar?.data?.items || [];  // ✅ Sempre array
```

### Issue 3: Timeout Errors

**Symptoms**:
- HTTP Request timeout após 60 segundos
- Workflow não completa

**Root Cause**: Default timeout muito alto ou operação bloqueante.

**Solution**:
```javascript
// Reduzir timeout e adicionar retry
{
  "timeout": 10000,  // 10 segundos
  "retry": {
    "enabled": true,
    "maxRetries": 2
  }
}
```

### Issue 4: Response Data Not Merged

**Symptoms**:
- WF06 retorna dados, mas WF02 não os vê
- date_suggestions undefined

**Root Cause**: Merge node configurado incorretamente.

**Solution**:
```javascript
// Merge WF06 Response Node
const stateData = $input.item(0).json;      // From State Machine
const wf06Data = $input.item(1).json;       // From HTTP Request

return [{
  json: {
    ...stateData,                           // Preserva todos os campos
    date_suggestions: wf06Data.dates_with_availability  // Adiciona WF06 data
  }
}];
```

---

## 📊 Integration Patterns Summary

### Synchronous (Request-Response)

```yaml
Pattern: WF02 ↔ WF06
Use Case: Need data from WF06 to continue
Timeout: 10 seconds
Retry: 2 attempts
Error Handling: Fallback to manual handoff
```

### Asynchronous (Fire-and-Forget)

```yaml
Pattern: WF02 → WF05, WF07
Use Case: Trigger action, don't wait for result
Timeout: 5 seconds
Retry: 0 attempts (optional)
Error Handling: Log error, continue WF02
```

### Data Flow

```
WF01 (Dedup)
  ↓
WF02 (AI Agent)
  ├─→ WF06 (Calendar) ← Sync (aguarda response)
  ├─→ WF05 (Appointment) ← Async (não aguarda)
  └─→ WF07 (Email) ← Async (não aguarda)
```

---

## 🎯 Best Practices

### 1. Minimal Payloads

```javascript
// ✅ CORRETO: Apenas dados necessários
{
  "lead_name": "João Silva",
  "lead_email": "joao@email.com",
  "scheduled_date": "2026-05-15"
}

// ❌ ERRADO: Dados desnecessários
{
  "all_conversation_data": {...},  // Muito grande
  "all_collected_data": {...}      // Desnecessário
}
```

### 2. Stable API Contracts

```yaml
# WF06 API Contract (não quebrar compatibilidade)
next_dates:
  request:
    action: string (required)
    service_type: string (required)
    count: number (optional, default: 3)
  response:
    dates_with_availability: array (required)
```

### 3. Error Handling at Boundaries

```javascript
// WF02: Sempre validar WF06 response
const dates = wf06Response?.dates_with_availability || [];
if (dates.length === 0) {
  // Fallback: mensagem amigável para usuário
  response_text = "Desculpe, não há datas disponíveis no momento.";
}
```

### 4. Monitoring and Logging

```javascript
// Adicionar logs em integration points
console.log('WF02: Calling WF06 next_dates');
console.log('WF02: WF06 response:', JSON.stringify(wf06Response));
console.log('WF02: Merged date_suggestions count:', dates.length);
```

---

## 📚 Referências

### Deployment Docs

- **WF02 V105 Routing Fix**: `/docs/deployment/wf02/v100-v114/DEPLOY_WF02_V105_WF06_ROUTING_FIX.md`
- **WF06 V2.1 Complete**: `/docs/deployment/wf06/DEPLOY_WF06_V2_1_COMPLETE_FIX.md`
- **WF05 V7 Hardcoded**: `/docs/deployment/wf05/DEPLOY_WF05_V7_HARDCODED_FINAL.md`
- **WF07 V13 INSERT...SELECT**: `/docs/fix/wf07/BUGFIX_WF07_V13_INSERT_SELECT_FIX.md`

### Bugfix Reports

- **V105 WF06 Routing**: `/docs/fix/wf02/v100-v114/BUGFIX_WF02_V105_WF06_ROUTING_STATE_UPDATE.md`
- **WF06 V2 Empty Calendar**: `/docs/fix/wf06/BUGFIX_WF06_V2_EMPTY_CALENDAR_FIX.md`
- **WF06 V2.1 Input Data**: `/docs/fix/wf06/BUGFIX_WF06_V2_1_INPUT_DATA_SOURCE.md`

### Workflows

- **WF02 V114**: `/n8n/workflows/production/wf02/02_ai_agent_conversation_V114_FUNCIONANDO.json`
- **WF06 V2.2**: `/n8n/workflows/production/wf06/06_calendar_availability_service_v2_2.json`
- **WF05 V7**: `/n8n/workflows/production/wf05/05_appointment_scheduler_v7_hardcoded_values.json`
- **WF07 V13**: `/n8n/workflows/production/wf07/07_send_email_v13_insert_select.json`

---

**Última Atualização**: 2026-04-29
**Versão em Produção**: WF02 V114, WF05 V7, WF06 V2.2, WF07 V13
**Status**: ✅ COMPLETO - Microservices architecture em produção
