# WF06: Calendar Availability Service

> **Version**: V1 | **Status**: Ready for Testing | **Created**: 2026-04-06

## Overview

WF06 é um serviço webhook n8n dedicado que calcula disponibilidade de horários na Google Calendar e retorna opções pré-validadas para o usuário. Implementa o paradigma **PROATIVO** da UX V76, onde o sistema **propõe** opções em vez de **receber** input manual.

**Arquitetura**: Webhook trigger → Dual-path routing → Google Calendar API → Slot calculation → Formatted response

**Endpoints**:
- `POST /webhook/calendar-availability?action=next_dates` - Retorna próximas N datas com disponibilidade
- `POST /webhook/calendar-availability?action=available_slots` - Retorna horários livres em data específica

---

## Arquitetura

### Fluxo de Dados

```
┌─────────────────────────────────────────────────────────────┐
│ WF02 (AI Agent)                                             │
│ User seleciona serviço → Trigger WF06 request              │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ Node 1: Webhook Trigger                                     │
│ POST /webhook/calendar-availability                         │
│ Body: { action, count?, date?, duration_minutes? }         │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ Node 2: Parse & Validate Request                           │
│ - Validate action field                                     │
│ - Extract parameters with defaults                          │
│ - Route to appropriate path                                 │
└──────────────────┬──────────────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
┌──────────────────┐  ┌──────────────────┐
│ PATH 1:          │  │ PATH 2:          │
│ next_dates       │  │ available_slots  │
│ (Nodes 4-7)      │  │ (Nodes 8-10)     │
└──────────────────┘  └──────────────────┘
        │                     │
        └──────────┬──────────┘
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ Node 11: Respond to Webhook                                 │
│ JSON response with formatted availability data              │
└─────────────────────────────────────────────────────────────┘
```

### Nodes (11 total)

| Node | Type | Purpose |
|------|------|---------|
| 1 | Webhook | Recebe POST requests em `/webhook/calendar-availability` |
| 2 | Code | Valida request e extrai parâmetros |
| 3 | IF | Roteamento por action (`next_dates` vs `available_slots`) |
| 4 | Code | Calcula próximos N dias úteis |
| 5 | Google Calendar | Busca eventos (batch - múltiplas datas) |
| 6 | Code | Calcula slots disponíveis por data |
| 7 | Code | Formata resposta next_dates com labels PT-BR |
| 8 | Google Calendar | Busca eventos (single date) |
| 9 | Code | Calcula slots disponíveis para data específica |
| 10 | Code | Formata resposta available_slots com horários PT-BR |
| 11 | Webhook Response | Retorna JSON formatado |

---

## API Reference

### Endpoint 1: next_dates

**Propósito**: Retorna próximas N datas com disponibilidade, priorizando dias úteis.

**Request**:
```bash
curl -X POST http://localhost:5678/webhook/calendar-availability \
  -H "Content-Type: application/json" \
  -d '{
    "action": "next_dates",
    "count": 3,
    "start_date": "2026-04-06",
    "duration_minutes": 120
  }'
```

**Parameters**:
| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| action | string | ✅ Yes | - | Deve ser "next_dates" |
| count | integer | ❌ No | 3 | Número de datas a retornar (1-10) |
| start_date | string | ❌ No | hoje | Data inicial (YYYY-MM-DD) |
| duration_minutes | integer | ❌ No | 120 | Duração do agendamento em minutos |

**Response**:
```json
{
  "success": true,
  "action": "next_dates",
  "dates": [
    {
      "date": "2026-04-07",
      "display": "Amanhã (07/04)",
      "day_of_week": "Segunda",
      "total_slots": 3,
      "quality": "medium"
    },
    {
      "date": "2026-04-08",
      "display": "Quarta (08/04)",
      "day_of_week": "Quarta",
      "total_slots": 5,
      "quality": "high"
    },
    {
      "date": "2026-04-09",
      "display": "Quinta (09/04)",
      "day_of_week": "Quinta",
      "total_slots": 2,
      "quality": "low"
    }
  ]
}
```

**Response Fields**:
| Field | Type | Description |
|-------|------|-------------|
| success | boolean | Indica sucesso da operação |
| action | string | Eco do action solicitado |
| dates | array | Lista de datas disponíveis |
| dates[].date | string | Data ISO (YYYY-MM-DD) |
| dates[].display | string | Label amigável PT-BR ("Amanhã", "Quarta (08/04)") |
| dates[].day_of_week | string | Nome do dia da semana |
| dates[].total_slots | integer | Total de slots disponíveis nesta data |
| dates[].quality | string | Indicador de qualidade: "high" (≥5), "medium" (≥3), "low" (<3) |

### Endpoint 2: available_slots

**Propósito**: Retorna todos os horários disponíveis em uma data específica.

**Request**:
```bash
curl -X POST http://localhost:5678/webhook/calendar-availability \
  -H "Content-Type: application/json" \
  -d '{
    "action": "available_slots",
    "date": "2026-04-08",
    "duration_minutes": 120
  }'
```

**Parameters**:
| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| action | string | ✅ Yes | - | Deve ser "available_slots" |
| date | string | ✅ Yes | - | Data específica (YYYY-MM-DD) |
| duration_minutes | integer | ❌ No | 120 | Duração do agendamento em minutos |

**Response**:
```json
{
  "success": true,
  "action": "available_slots",
  "date": "2026-04-08",
  "available_slots": [
    {
      "start_time": "09:00",
      "end_time": "11:00",
      "formatted": "9h às 11h"
    },
    {
      "start_time": "14:00",
      "end_time": "16:00",
      "formatted": "14h às 16h"
    }
  ],
  "total_available": 2
}
```

**Response Fields**:
| Field | Type | Description |
|-------|------|-------------|
| success | boolean | Indica sucesso da operação |
| action | string | Eco do action solicitado |
| date | string | Data consultada (YYYY-MM-DD) |
| available_slots | array | Lista de horários disponíveis |
| available_slots[].start_time | string | Hora início (HH:MM) |
| available_slots[].end_time | string | Hora fim (HH:MM) |
| available_slots[].formatted | string | Label PT-BR ("9h às 11h") |
| total_available | integer | Total de slots disponíveis |

---

## Algoritmos Core

### 1. Business Day Calculation

**Propósito**: Calcular próximos N dias úteis (Segunda-Sexta), ignorando finais de semana.

**Implementação** (Node 4):
```javascript
// Hardcoded business rules (V7 pattern)
const WORK_DAYS = [1, 2, 3, 4, 5];  // Monday-Friday (0=Sunday, 6=Saturday)
const MAX_SEARCH_DAYS = 30;          // Limite de busca

const businessDates = [];
let daysChecked = 0;

while (businessDates.length < count && daysChecked < MAX_SEARCH_DAYS) {
    const checkDate = new Date(startDate);
    checkDate.setDate(startDate.getDate() + daysChecked + 1);  // Start from tomorrow

    const dayOfWeek = checkDate.getDay();

    if (WORK_DAYS.includes(dayOfWeek)) {
        const dateStr = checkDate.toISOString().split('T')[0];
        businessDates.push({
            date: dateStr,
            day_of_week: dayOfWeek,
            iso_date: dateStr
        });
    }
    daysChecked++;
}
```

**Características**:
- ✅ Ignora Sábado (6) e Domingo (0) automaticamente
- ✅ Limite de 30 dias de busca (evita loops infinitos)
- ✅ Retorna exatamente `count` datas úteis
- ⚠️ NÃO considera feriados (feature futura)

### 2. Conflict Detection Algorithm

**Propósito**: Detectar se um slot de tempo conflita com eventos existentes na Google Calendar.

**Implementação** (Nodes 6 e 9):
```javascript
function hasConflict(slotStart, slotEnd, events) {
    for (const event of events) {
        const eventStart = new Date(event.start.dateTime);
        const eventEnd = new Date(event.end.dateTime);

        // Overlap detection: slot overlaps event if:
        // slotStart < eventEnd AND slotEnd > eventStart
        if (slotStart < eventEnd && slotEnd > eventStart) {
            return true;  // Conflict found
        }
    }
    return false;  // No conflicts
}
```

**Lógica de Overlap**:
```
Case 1: Overlap total
Event:    [========]
Slot:      [====]
Result: CONFLICT

Case 2: Overlap parcial (início)
Event:    [========]
Slot:  [====]
Result: CONFLICT

Case 3: Overlap parcial (fim)
Event: [========]
Slot:         [====]
Result: CONFLICT

Case 4: Sem overlap
Event: [====]
Slot:         [====]
Result: OK
```

### 3. Slot Generation Algorithm

**Propósito**: Gerar todos os slots possíveis em horário comercial e filtrar conflitos.

**Implementação** (Nodes 6 e 9):
```javascript
// Hardcoded business hours (V7 pattern)
const WORK_START = 8;   // 08:00
const WORK_END = 18;    // 18:00
const SLOT_INTERVAL = 60;  // 1-hour intervals

function calculateSlotsForDate(dateStr, events, durationMinutes) {
    const allSlots = [];

    for (let hour = WORK_START; hour < WORK_END; hour += (SLOT_INTERVAL / 60)) {
        const startTime = `${String(hour).padStart(2, '0')}:00`;
        const endHour = hour + (durationMinutes / 60);

        // Check if slot fits within business hours
        if (endHour <= WORK_END) {
            const endTime = `${String(endHour).padStart(2, '0')}:00`;

            // Create Date objects with Brazil timezone
            const slotStart = new Date(`${dateStr}T${startTime}:00-03:00`);
            const slotEnd = new Date(`${dateStr}T${endTime}:00-03:00`);

            // Check for conflicts
            if (!hasConflict(slotStart, slotEnd, events)) {
                allSlots.push({
                    start_time: startTime,
                    end_time: endTime
                });
            }
        }
    }

    return allSlots;
}
```

**Características**:
- ✅ Intervalos de 1 hora (08:00, 09:00, ..., 17:00)
- ✅ Valida se slot completo cabe no horário comercial
- ✅ Respeita `duration_minutes` (120min = 2h, 60min = 1h)
- ✅ Timezone explícito: `-03:00` (America/Sao_Paulo)

**Exemplo de Geração** (duration_minutes=120):
```
WORK_START=8, WORK_END=18, DURATION=120min (2h)

Slots gerados:
08:00-10:00 ✅
09:00-11:00 ✅
10:00-12:00 ✅
11:00-13:00 ✅
12:00-14:00 ✅
13:00-15:00 ✅
14:00-16:00 ✅
15:00-17:00 ✅
16:00-18:00 ✅
17:00-19:00 ❌ (endHour 19 > WORK_END 18)
```

### 4. Friendly Date Labeling (Portuguese)

**Propósito**: Converter datas ISO em labels amigáveis em português.

**Implementação** (Node 7):
```javascript
// Day names in Portuguese
const dayNames = {
    0: 'Domingo', 1: 'Segunda', 2: 'Terça', 3: 'Quarta',
    4: 'Quinta', 5: 'Sexta', 6: 'Sábado'
};

function getFriendlyDateLabel(dateStr) {
    const targetDate = new Date(dateStr + 'T12:00:00-03:00');
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const diffDays = Math.floor((targetDate - today) / (1000 * 60 * 60 * 24));

    if (diffDays === 1) return 'Amanhã';
    if (diffDays === 2) return 'Depois de amanhã';

    return formatDateDisplay(dateStr);
}

function formatDateDisplay(dateStr) {
    const date = new Date(dateStr + 'T12:00:00-03:00');
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const dayName = dayNames[date.getDay()];

    return `${dayName} (${day}/${month})`;
}
```

**Exemplos**:
| Data ISO | Contexto | Output |
|----------|----------|--------|
| 2026-04-07 | Amanhã | "Amanhã (07/04)" |
| 2026-04-08 | Depois de amanhã | "Depois de amanhã (08/04)" |
| 2026-04-10 | +4 dias | "Quinta (10/04)" |

### 5. Quality Indicator

**Propósito**: Classificar disponibilidade de datas para priorização UX.

**Implementação** (Node 7):
```javascript
function getQualityIndicator(totalSlots) {
    if (totalSlots >= 5) return 'high';
    if (totalSlots >= 3) return 'medium';
    return 'low';
}
```

**Uso no WF02 V76**:
- **high** (≥5 slots): "📅 **Muita disponibilidade!**"
- **medium** (≥3 slots): "📅 Boa disponibilidade"
- **low** (<3 slots): "⚠️ Poucos horários"

---

## Google Calendar Integration

### Authentication

**Método**: OAuth2 via n8n Credential System

**Configuração**:
1. n8n → Credentials → Add Credential → Google Calendar OAuth2
2. Provide: Client ID, Client Secret, Scopes
3. Required scopes:
   - `https://www.googleapis.com/auth/calendar.readonly` (read events)
   - `https://www.googleapis.com/auth/calendar.events` (create events - usado no WF05)

**Referência no Workflow**:
```json
{
  "credentials": {
    "googleCalendarOAuth2Api": {
      "id": "...",
      "name": "Google Calendar E2 Soluções"
    }
  }
}
```

### API Operations

#### Operation 1: Get All Events (Batch - next_dates)

**Node 5 Configuration**:
```json
{
  "parameters": {
    "operation": "getAll",
    "calendarId": "={{ $env.GOOGLE_CALENDAR_ID }}",
    "options": {
      "timeMin": "={{ $json.business_dates[0].iso_date }}T00:00:00-03:00",
      "timeMax": "={{ $json.business_dates[$json.business_dates.length - 1].iso_date }}T23:59:59-03:00",
      "maxResults": 2500
    }
  }
}
```

**Otimização**: Single API call para múltiplas datas (batch retrieval).

**Exemplo**:
```
Request: next_dates com count=3
Datas: 2026-04-07, 2026-04-08, 2026-04-09

API call:
timeMin = 2026-04-07T00:00:00-03:00
timeMax = 2026-04-09T23:59:59-03:00

Retorna: Todos eventos nos 3 dias em uma única chamada
```

#### Operation 2: Get All Events (Single Date - available_slots)

**Node 8 Configuration**:
```json
{
  "parameters": {
    "operation": "getAll",
    "calendarId": "={{ $env.GOOGLE_CALENDAR_ID }}",
    "options": {
      "timeMin": "={{ $json.date }}T00:00:00-03:00",
      "timeMax": "={{ $json.date }}T23:59:59-03:00",
      "maxResults": 100
    }
  }
}
```

**Propósito**: Buscar eventos de um único dia específico.

### Event Structure

**Google Calendar Event Format**:
```json
{
  "id": "event123",
  "summary": "Visita Técnica - João Silva",
  "start": {
    "dateTime": "2026-04-08T09:00:00-03:00"
  },
  "end": {
    "dateTime": "2026-04-08T11:00:00-03:00"
  },
  "status": "confirmed"
}
```

**Campos Utilizados**:
- `start.dateTime`: Timestamp início (usado em conflict detection)
- `end.dateTime`: Timestamp fim (usado em conflict detection)

---

## Configuration

### Hardcoded Business Rules (V7 Pattern)

**Por quê hardcoded?** n8n bloqueia acesso a `$env` em Code nodes e Set expressions (documentado em WF05 V7 notes).

**Values**:
```javascript
// Business Hours
const WORK_START = 8;    // 08:00
const WORK_END = 18;     // 18:00
const SLOT_INTERVAL = 60; // 1-hour intervals

// Business Days
const WORK_DAYS = [1, 2, 3, 4, 5];  // Monday-Friday

// Timezone
const BRAZIL_OFFSET = '-03:00';  // America/Sao_Paulo

// Limits
const MAX_SEARCH_DAYS = 30;  // Max days to search for business days
```

**Future Enhancement**: Se n8n permitir `$env` access no futuro, migrar para:
```bash
CALENDAR_WORK_START=08:00
CALENDAR_WORK_END=18:00
CALENDAR_WORK_DAYS=1,2,3,4,5
CALENDAR_TIMEZONE=-03:00
```

### Environment Variables (n8n level)

**Required**:
```bash
GOOGLE_CALENDAR_ID=<calendar-id-from-google>
```

**Usage in Workflow**:
```json
{
  "calendarId": "={{ $env.GOOGLE_CALENDAR_ID }}"
}
```

**⚠️ Important**: `$env.GOOGLE_CALENDAR_ID` funciona em n8n nodes nativos (Google Calendar node), mas NÃO funciona em Code nodes.

---

## Testing

### Test Script

**Location**: `/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/scripts/test-wf06-endpoints.sh`

**Execution**:
```bash
cd /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot
chmod +x scripts/test-wf06-endpoints.sh
./scripts/test-wf06-endpoints.sh
```

**Test Coverage** (10 tests):
1. ✅ next_dates com parâmetros default (3 datas)
2. ✅ next_dates com count customizado (5 datas)
3. ✅ next_dates validação de estrutura de data
4. ✅ next_dates labels em português
5. ✅ available_slots com data válida
6. ✅ available_slots validação de estrutura de slot
7. ✅ available_slots faltando parâmetro date (error handling)
8. ✅ action inválido (error handling)
9. ✅ action faltando (error handling)
10. ✅ duration customizado (60 minutos)

### Manual Testing

**Test next_dates**:
```bash
curl -X POST http://localhost:5678/webhook/calendar-availability \
  -H "Content-Type: application/json" \
  -d '{"action":"next_dates","count":3}' | jq
```

**Expected Output**:
```json
{
  "success": true,
  "action": "next_dates",
  "dates": [
    {
      "date": "2026-04-07",
      "display": "Amanhã (07/04)",
      "day_of_week": "Segunda",
      "total_slots": 3,
      "quality": "medium"
    }
  ]
}
```

**Test available_slots**:
```bash
curl -X POST http://localhost:5678/webhook/calendar-availability \
  -H "Content-Type: application/json" \
  -d '{"action":"available_slots","date":"2026-04-08"}' | jq
```

**Expected Output**:
```json
{
  "success": true,
  "action": "available_slots",
  "date": "2026-04-08",
  "available_slots": [
    {
      "start_time": "09:00",
      "end_time": "11:00",
      "formatted": "9h às 11h"
    }
  ],
  "total_available": 1
}
```

---

## Deployment

### Prerequisites

1. ✅ n8n running: `docker ps | grep e2bot-n8n-dev`
2. ✅ Google Calendar credentials configured in n8n
3. ✅ Environment variable `GOOGLE_CALENDAR_ID` set
4. ✅ Workflow file: `n8n/workflows/06_calendar_availability_service_v1.json`

### Import to n8n

**Steps**:
```bash
# 1. Access n8n UI
http://localhost:5678

# 2. Import workflow
Workflows → Import → Select file:
/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/06_calendar_availability_service_v1.json

# 3. Configure credentials
Open workflow → Click Google Calendar nodes → Select credential "Google Calendar E2 Soluções"

# 4. Activate workflow
Toggle "Active" switch to ON

# 5. Verify webhook URL
Copy webhook URL from Webhook Trigger node
Expected: http://localhost:5678/webhook/calendar-availability
```

### Validation

**Test activation**:
```bash
# Check if webhook is responding
curl -X POST http://localhost:5678/webhook/calendar-availability \
  -H "Content-Type: application/json" \
  -d '{"action":"next_dates","count":1}'

# Expected: JSON response with dates array
# If error: Check n8n logs
docker logs e2bot-n8n-dev | tail -50
```

**Run test suite**:
```bash
./scripts/test-wf06-endpoints.sh
```

### Monitoring

**n8n Logs**:
```bash
docker logs -f e2bot-n8n-dev | grep -E "calendar-availability|WF06"
```

**Execution History**:
- n8n UI → Executions → Filter by "06_calendar_availability_service"
- Check for errors or slow responses

---

## Integration with WF02 V76

### Conversation Flow (Planned)

**Current V75** (REACTIVE):
```
State 9: "Digite a data (DD/MM/AAAA)"
User: "15/04/2026"
State 10: "Digite o horário (HH:MM)"
User: "14:30"
Bot: "Horário ocupado" ❌
[loop de frustração]
```

**New V76** (PROACTIVE):
```
State 9-NEW: Trigger WF06 next_dates
Bot: "📅 *Próximas Datas Disponíveis:*
     1️⃣ Amanhã (07/04) - 3 horários 📅
     2️⃣ Quarta (08/04) - 5 horários ✨
     3️⃣ Quinta (09/04) - 2 horários ⚠️

     Responda com o número da data preferida."

User: "2"

State 10-NEW: Trigger WF06 available_slots com date=2026-04-08
Bot: "🕐 *Horários Livres - Quarta (08/04):*
     1️⃣ 9h às 11h ✅
     2️⃣ 14h às 16h ✅

     Responda com o número do horário preferido."

User: "2"

State 11-NEW: Trigger WF05 com date=2026-04-08, time=14:00
Bot: "✅ *Visita agendada!*
     📅 Quarta, 08/04/2026
     🕐 14h às 16h
     📍 Cocal, GO"
```

### WF02 State Machine Changes (V76)

**New States**:
- **State 9**: `awaiting_date_selection` → Call WF06 next_dates → Present options
- **State 10**: `awaiting_time_selection` → Call WF06 available_slots → Present options
- **State 11**: `confirming_appointment` → Call WF05 schedule → Send confirmation

**HTTP Request Node** (in WF02):
```json
{
  "parameters": {
    "method": "POST",
    "url": "http://localhost:5678/webhook/calendar-availability",
    "jsonParameters": true,
    "options": {
      "bodyParametersJson": "={{ JSON.stringify({\n  action: 'next_dates',\n  count: 3,\n  duration_minutes: 120\n}) }}"
    }
  }
}
```

**Response Parsing** (in WF02):
```javascript
// Parse WF06 response
const wf06Response = $json.body;
const dates = wf06Response.dates;

// Build interactive message
let message = "📅 *Próximas Datas Disponíveis:*\n\n";
dates.forEach((date, index) => {
    const emoji = date.quality === 'high' ? '✨' :
                  date.quality === 'medium' ? '📅' : '⚠️';
    message += `${index + 1}️⃣ ${date.display} - ${date.total_slots} horários ${emoji}\n`;
});
message += "\nResponda com o número da data preferida.";

// Update conversation state
return {
    message: message,
    next_state: 'awaiting_date_selection',
    available_dates: dates  // Store for next state
};
```

---

## Performance Considerations

### API Call Optimization

**Batch vs Single Queries**:
```
REACTIVE (V75):
- User digita data → API call para verificar → Erro? → Repeat
- Worst case: 5-10 API calls por agendamento

PROACTIVE (V76):
- next_dates: 1 API call (batch) para 3 datas
- available_slots: 1 API call para data selecionada
- schedule: 1 API call para criar evento
- Total: 3 API calls por agendamento (67% reduction)
```

### Response Time

**Target**:
- next_dates: < 2 segundos
- available_slots: < 1 segundo

**Actual** (measured):
- ⏱️ TBD após testes com Google Calendar real

**Bottlenecks**:
1. Google Calendar API latency (~500ms)
2. Slot calculation (linear O(n*m), n=hours, m=events)

**Optimization Opportunities**:
- Cache calendar events por 5 minutos (reduce API calls)
- Limit `maxResults` to 100 events per day (sufficient for normal usage)

### Scalability

**Current Architecture** (Webhook per request):
- ✅ Stateless (cada request independente)
- ✅ Horizontal scaling via n8n workers
- ⚠️ Google Calendar API quota: 1M requests/day (suficiente para 333K agendamentos/dia)

**Future Enhancement**:
- Implementar cache Redis para eventos recentes
- Batch processing para múltiplos usuários simultâneos

---

## Error Handling

### Validation Errors

**Missing action**:
```json
Request: {}
Response: {
  "error": "Missing required field: action",
  "code": "MISSING_ACTION"
}
```

**Invalid action**:
```json
Request: {"action": "invalid"}
Response: {
  "error": "Invalid action. Must be 'next_dates' or 'available_slots'",
  "code": "INVALID_ACTION"
}
```

**Missing date (available_slots)**:
```json
Request: {"action": "available_slots"}
Response: {
  "error": "Missing required field: date",
  "code": "MISSING_DATE"
}
```

### Google Calendar Errors

**Credential Error**:
```javascript
try {
    const events = await googleCalendar.getAll();
} catch (error) {
    if (error.code === 401) {
        return {
            error: "Google Calendar authentication failed. Re-authenticate credentials.",
            code: "AUTH_ERROR"
        };
    }
}
```

**API Quota Exceeded**:
```javascript
if (error.code === 429) {
    return {
        error: "Google Calendar API quota exceeded. Try again later.",
        code: "QUOTA_EXCEEDED",
        retry_after: 60
    };
}
```

### Business Logic Errors

**No business days found**:
```javascript
if (businessDates.length === 0) {
    return {
        success: false,
        error: "No business days available in next 30 days",
        code: "NO_AVAILABILITY"
    };
}
```

**No available slots**:
```json
{
  "success": true,
  "action": "available_slots",
  "date": "2026-04-08",
  "available_slots": [],
  "total_available": 0,
  "message": "Sem horários disponíveis nesta data"
}
```

---

## Troubleshooting

### Issue 1: Webhook não responde

**Symptom**: `curl` timeout ou connection refused

**Debug**:
```bash
# Check if n8n is running
docker ps | grep e2bot-n8n-dev

# Check if workflow is active
curl http://localhost:5678/rest/workflows | jq '.data[] | select(.name | contains("calendar"))'

# Check n8n logs
docker logs e2bot-n8n-dev | tail -100
```

**Solution**:
1. Activate workflow in n8n UI
2. Restart n8n: `docker restart e2bot-n8n-dev`
3. Re-import workflow if corrupted

### Issue 2: Google Calendar authentication failed

**Symptom**: Error 401 in execution logs

**Debug**:
```bash
# Check credential status
n8n UI → Credentials → Google Calendar E2 Soluções → Test

# Check scopes
Required: calendar.readonly, calendar.events
```

**Solution**:
1. Re-authenticate Google Calendar credential
2. Verify scopes in Google Cloud Console
3. Grant offline access for refresh token

### Issue 3: Empty slots array

**Symptom**: `available_slots: []` mesmo com calendar vazia

**Debug**:
```javascript
// Add logging to Node 9
console.log('Events:', events);
console.log('Date:', dateStr);
console.log('Duration:', durationMinutes);
console.log('Generated slots:', allSlots);
```

**Possible Causes**:
1. **Timezone mismatch**: Verificar `-03:00` offset
2. **Business hours**: Verificar WORK_START=8, WORK_END=18
3. **Duration too long**: 120min em dia cheio = poucos slots

**Solution**:
1. Test with `duration_minutes: 60` (1-hour slots = more availability)
2. Verify timezone in Google Calendar settings
3. Check if calendar has all-day events blocking slots

### Issue 4: Portuguese labels não aparecem

**Symptom**: `display: "undefined"` ou `formatted: "NaN às NaN"`

**Debug**:
```javascript
// Node 7 - Check date parsing
const testDate = new Date('2026-04-08T12:00:00-03:00');
console.log('Parsed date:', testDate);
console.log('Day of week:', testDate.getDay());
```

**Solution**:
1. Verify date format is `YYYY-MM-DD` (ISO)
2. Check timezone offset `-03:00` is appended
3. Validate `dayNames` object has all 7 days

---

## Future Enhancements

### Phase 2: WF02 V76 Integration
- [ ] Refactor States 9-10 with proactive UX
- [ ] Implement HTTP Request nodes calling WF06
- [ ] Add interactive message formatting (numbered options)
- [ ] Store selected date/time in conversation context

### Phase 3: Advanced Features
- [ ] Holiday calendar integration (skip feriados nacionais/estaduais)
- [ ] Multiple calendar support (different services = different calendars)
- [ ] Conflict resolution intelligence (suggest nearest alternative)
- [ ] User preference learning (preferred times, avoid lunch hours)

### Phase 4: Performance Optimization
- [ ] Redis cache for calendar events (5-minute TTL)
- [ ] Batch processing for concurrent requests
- [ ] Predictive pre-loading (pre-fetch next 7 days at midnight)

### Phase 5: Analytics
- [ ] Track quality indicator distribution (how often high/medium/low)
- [ ] Monitor API call efficiency (batch vs single)
- [ ] User selection patterns (preferred times, days)

---

## References

### Documentation
- **Main Plan**: `/docs/PLAN_V76_GOOGLE_CALENDAR_UX.md` (V73 original)
- **UX Analysis**: `/docs/ANALYSIS_V76_UX_OPTIMIZATION.md` (V76 comprehensive)
- **WF05 V7 Notes**: Hardcoded business hours pattern
- **Google Calendar API**: https://developers.google.com/calendar/api/v3/reference

### Related Workflows
- **WF01 V2.8.3**: Main WhatsApp handler (deduplication)
- **WF02 V75**: AI Agent conversation (current REACTIVE)
- **WF02 V76**: AI Agent conversation (planned PROACTIVE) - depends on WF06
- **WF05 V7**: Appointment scheduler (creates Google Calendar events)

### Files
- **Workflow**: `/n8n/workflows/06_calendar_availability_service_v1.json`
- **Test Script**: `/scripts/test-wf06-endpoints.sh`
- **Documentation**: `/docs/WF06_CALENDAR_AVAILABILITY_SERVICE.md` (this file)

---

**Version**: V1 | **Status**: Ready for Testing | **Next**: Import to n8n and run test suite
