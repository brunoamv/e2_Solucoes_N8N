# Plano de Refatoração: 05_appointment_scheduler.json

**Data**: 2026-03-11
**Versão**: V1.0 → V2.0
**Status**: PLANEJAMENTO
**Padrão**: Seguindo modelo de implementação V69.2

---

## 📋 Análise do Workflow Atual

### Estrutura Existente (V1.0)
```
Execute Workflow Trigger
  → Get Appointment
    → Get Lead Data
      → Build Calendar Event (Code Node - 57 linhas)
        → Create Google Event
          → Update Appointment
            → Create Appointment Reminders
              → Create RD Station Task
                → Send Confirmation Email
```

### Problemas Identificados

#### 🔴 CRÍTICOS
1. **Hard-coded durations**: Duração fixa em JavaScript (120-180min)
2. **Missing error handling**: Nenhum tratamento de erros do Google Calendar
3. **No validation**: Não valida disponibilidade antes de criar evento
4. **Credential ID hardcoded**: `"id": "1"` em múltiplos nodes
5. **Complex Code Node**: 57 linhas de JavaScript sem validação
6. **Missing rollback**: Se Google falhar, appointment já foi criado

#### 🟡 MODERADOS
7. **No retry logic**: Falhas do Google API não têm retry
8. **Missing timezone validation**: `America/Sao_Paulo` hardcoded
9. **Service name mapping**: Hardcoded em JavaScript
10. **No logging**: Debug impossível em produção
11. **RD Station URL**: Variável `$env.RDSTATION_URL` não documentada
12. **Email workflow ID**: `"workflowId": "7"` hardcoded

#### 🟢 MELHORIAS
13. **Code splitting**: Code node pode ser modularizado
14. **Database schema**: Não usa campos `scheduled_time_start/end` corretamente
15. **Template integration**: Poderia usar templates como V69.2

---

## 🎯 Objetivos da Refatoração

### Padrão V69.2 Aplicado

**Características do padrão estabelecido**:
- ✅ Validação de entrada robusta (Validate Input Data)
- ✅ Preparação de dados (Prepare Phone Formats)
- ✅ Queries SQL dinâmicas geradas em Code Nodes
- ✅ Error handling com `alwaysOutputData: true`
- ✅ Logging estruturado (`console.log`)
- ✅ Atomicidade (UPDATE + JSONB em única query)
- ✅ Nomes de nodes descritivos e padronizados

### Melhorias Planejadas

1. **Validação de entrada** (V69.2 pattern)
2. **Error handling robusto** (try/catch + fallback)
3. **Modularização** (Code nodes especializados)
4. **Retry logic** (Google Calendar API)
5. **Database atomicity** (single transaction)
6. **Logging estruturado** (debug + production)
7. **Template system** (mensagens padronizadas)
8. **Configuration centralization** (env vars)

---

## 🏗️ Nova Arquitetura (V2.0)

### Estrutura Refatorada
```
Execute Workflow Trigger
  → Validate Input Data                      [NOVO]
    → Get Appointment & Lead Data            [MERGED]
      → Validate Availability                [NOVO]
        → Build Calendar Event Data          [REFACTORED]
          → Create Google Calendar Event     [ERROR HANDLING]
            ├─ Success → Update Appointment  [ATOMIC]
            │            → Create Reminders
            │              → Create RD Task
            │                → Send Confirmation
            └─ Error → Log Error & Notify    [NOVO]
```

### Novos Nodes

#### 1. Validate Input Data
```javascript
// Similar ao V69.2 - validação de appointment_id
const inputData = $input.first().json;

if (!inputData.appointment_id) {
    throw new Error('appointment_id is required');
}

// Validar UUID format
const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
if (!uuidRegex.test(inputData.appointment_id)) {
    throw new Error('Invalid appointment_id format');
}

console.log('✅ Input validated:', inputData.appointment_id);

return {
    appointment_id: inputData.appointment_id,
    source: inputData.source || 'workflow_trigger',
    timestamp: new Date().toISOString()
};
```

#### 2. Get Appointment & Lead Data [MERGED]
```sql
-- Single query com JOIN (performance)
SELECT
    a.id as appointment_id,
    a.scheduled_date,
    a.scheduled_time_start,
    a.scheduled_time_end,
    a.service_type,
    a.notes,
    a.status,
    l.id as lead_id,
    l.name as lead_name,
    l.email as lead_email,
    l.phone_number,
    l.address,
    l.city,
    l.state,
    l.zip_code,
    l.service_details,
    l.rdstation_deal_id,
    c.whatsapp_name
FROM appointments a
INNER JOIN leads l ON a.lead_id = l.id
LEFT JOIN conversations c ON l.conversation_id = c.id
WHERE a.id = $1
  AND a.status IN ('agendado', 'reagendado')
LIMIT 1;
```

**Parameters**: `={{ $json.appointment_id }}`

#### 3. Validate Availability [NOVO]
```javascript
// Validar se horário ainda está disponível
const data = $input.first().json;

const scheduledDate = data.scheduled_date;
const timeStart = data.scheduled_time_start;
const timeEnd = data.scheduled_time_end;

// Check business hours
const startHour = parseInt(timeStart.split(':')[0]);
const endHour = parseInt(timeEnd.split(':')[0]);

const workStart = parseInt($env.CALENDAR_WORK_START.split(':')[0]);
const workEnd = parseInt($env.CALENDAR_WORK_END.split(':')[0]);

if (startHour < workStart || endHour > workEnd) {
    throw new Error(`Horário fora do expediente: ${timeStart}-${timeEnd}`);
}

// Check weekend
const dayOfWeek = new Date(scheduledDate).getDay();
const workDays = $env.CALENDAR_WORK_DAYS.split(',').map(d => parseInt(d));

if (!workDays.includes(dayOfWeek)) {
    throw new Error(`Dia não útil: ${scheduledDate} (${dayOfWeek})`);
}

console.log('✅ Availability validated');

return {
    ...data,
    validation_status: 'approved',
    validated_at: new Date().toISOString()
};
```

#### 4. Build Calendar Event Data [REFACTORED]
```javascript
// Modular and maintainable version
const data = $input.first().json;

// --- Configuration ---
const SERVICE_CONFIG = {
    'energia_solar': {
        name: 'Energia Solar',
        duration: 120,
        color: '9' // Blue
    },
    'subestacao': {
        name: 'Subestação',
        duration: 180,
        color: '11' // Red
    },
    'projeto_eletrico': {
        name: 'Projeto Elétrico',
        duration: 90,
        color: '5' // Yellow
    },
    'armazenamento_energia': {
        name: 'BESS',
        duration: 120,
        color: '10' // Green
    },
    'analise_laudo': {
        name: 'Análise/Laudo',
        duration: 120,
        color: '8' // Gray
    }
};

// --- Get Service Config ---
const serviceConfig = SERVICE_CONFIG[data.service_type] || {
    name: data.service_type,
    duration: 90,
    color: '1'
};

// --- Build DateTime ---
const startDateTime = new Date(`${data.scheduled_date}T${data.scheduled_time_start}`);
const endDateTime = new Date(`${data.scheduled_date}T${data.scheduled_time_end}`);

// --- Build Event Title ---
const eventTitle = `[E2] Visita ${serviceConfig.name} - ${data.lead_name}`;

// --- Build Description ---
let description = `=== VISITA TÉCNICA E2 SOLUÇÕES ===\n\n`;
description += `CLIENTE: ${data.lead_name}\n`;
description += `TELEFONE: ${data.phone_number}\n`;
description += `EMAIL: ${data.lead_email || 'Não informado'}\n`;
description += `ENDEREÇO: ${data.address}, ${data.city}/${data.state}\n`;
description += `\nSERVIÇO: ${serviceConfig.name}\n`;

// Service details (if JSONB exists)
if (data.service_details) {
    const details = typeof data.service_details === 'string'
        ? JSON.parse(data.service_details)
        : data.service_details;

    description += `\n--- DADOS DO SERVIÇO ---\n`;

    for (const [key, value] of Object.entries(details)) {
        if (value) {
            description += `${key}: ${value}\n`;
        }
    }
}

// Appointment notes
if (data.notes) {
    description += `\n--- OBSERVAÇÕES ---\n${data.notes}\n`;
}

// Links
description += `\n--- LINKS ---\n`;
if (data.rdstation_deal_id) {
    description += `RD Station Deal: ${$env.RDSTATION_URL}/deals/${data.rdstation_deal_id}\n`;
}
description += `WhatsApp: https://wa.me/${data.phone_number.replace(/\D/g, '')}\n`;

// --- Build Attendees ---
const attendees = [
    { email: $env.GOOGLE_TECHNICIAN_EMAIL }
];

if (data.lead_email && data.lead_email.includes('@')) {
    attendees.push({ email: data.lead_email });
}

// --- Build Location ---
const location = `${data.address}, ${data.city} - ${data.state}${data.zip_code ? ', ' + data.zip_code : ''}`;

// --- Build Reminders ---
const reminders = {
    useDefault: false,
    overrides: [
        { method: 'email', minutes: 1440 }, // 24h
        { method: 'popup', minutes: 120 },  // 2h
        { method: 'email', minutes: 120 }   // 2h
    ]
};

// --- Return Event Data ---
console.log('✅ Calendar event built:', eventTitle);

return {
    // Event data for Google Calendar
    calendar_event: {
        summary: eventTitle,
        description: description,
        location: location,
        start: {
            dateTime: startDateTime.toISOString(),
            timeZone: $env.CALENDAR_TIMEZONE || 'America/Sao_Paulo'
        },
        end: {
            dateTime: endDateTime.toISOString(),
            timeZone: $env.CALENDAR_TIMEZONE || 'America/Sao_Paulo'
        },
        attendees: attendees,
        reminders: reminders,
        colorId: serviceConfig.color
    },

    // Metadata for next nodes
    appointment_id: data.appointment_id,
    lead_id: data.lead_id,
    lead_name: data.lead_name,
    service_type: data.service_type,
    rdstation_deal_id: data.rdstation_deal_id,
    phone_number: data.phone_number
};
```

#### 5. Create Google Calendar Event [ERROR HANDLING]
```json
{
  "parameters": {
    "calendarId": "={{ $env.GOOGLE_CALENDAR_ID }}",
    "operation": "create",
    "event": "={{ JSON.stringify($json.calendar_event) }}",
    "options": {
      "sendUpdates": "all",
      "conferenceDataVersion": 0
    }
  },
  "id": "create-google-event-v2",
  "name": "Create Google Calendar Event",
  "type": "n8n-nodes-base.googleCalendar",
  "typeVersion": 2,
  "continueOnFail": true,
  "alwaysOutputData": true,
  "retryOnFail": true,
  "maxTries": 3,
  "waitBetweenTries": 1000,
  "credentials": {
    "googleCalendarOAuth2Api": {
      "id": "{{ $env.GOOGLE_CALENDAR_CREDENTIAL_ID }}",
      "name": "Google Calendar API"
    }
  }
}
```

#### 6. Update Appointment [ATOMIC]
```sql
-- Atomic update com CASE para success/error
UPDATE appointments
SET
    google_calendar_event_id = CASE
        WHEN $2 IS NOT NULL THEN $2
        ELSE google_calendar_event_id
    END,
    status = CASE
        WHEN $2 IS NOT NULL THEN 'confirmado'
        ELSE 'erro_calendario'
    END,
    notes = CASE
        WHEN $2 IS NULL THEN COALESCE(notes, '') || '\n[ERRO] Falha ao criar evento no Google Calendar: ' || $3
        ELSE notes
    END,
    updated_at = NOW()
WHERE id = $1
RETURNING
    id,
    status,
    google_calendar_event_id,
    CASE
        WHEN google_calendar_event_id IS NOT NULL THEN true
        ELSE false
    END as calendar_success;
```

**Parameters**:
```javascript
"={{ $json.appointment_id }},{{ $json.calendar_event_id || null }},{{ $json.error || '' }}"
```

#### 7. Log Error & Notify [NOVO]
```javascript
// Error logging and notification
const error = $input.first().json.error;
const appointmentId = $input.first().json.appointment_id;

console.error('❌ Google Calendar Error:', {
    appointment_id: appointmentId,
    error: error,
    timestamp: new Date().toISOString()
});

// Send notification to admin
return {
    error_type: 'google_calendar_failure',
    appointment_id: appointmentId,
    error_message: error,
    notify_admin: true,
    retry_scheduled: false
};
```

---

## 📝 Configuração de Variáveis (.env)

### Variáveis Atualizadas

```bash
# --- Google Calendar Configuration ---
GOOGLE_CALENDAR_ID=xxxxx@group.calendar.google.com
GOOGLE_CALENDAR_CREDENTIAL_ID=VXA1r8sd0TMIdPvS
GOOGLE_SERVICE_ACCOUNT_EMAIL=e2-bot-calendar@e2-solucoes-bot-xxxxx.iam.gserviceaccount.com
GOOGLE_TECHNICIAN_EMAIL=tecnico@e2solucoes.com.br

# Timezone
CALENDAR_TIMEZONE=America/Sao_Paulo

# Business Hours (24h format)
CALENDAR_WORK_START=08:00
CALENDAR_WORK_END=18:00
CALENDAR_WORK_DAYS=1,2,3,4,5  # Segunda a Sexta

# Service Durations (minutes) - DEPRECATED (moved to code)
# CALENDAR_DEFAULT_DURATION=90

# Reminders
CALENDAR_REMINDER_24H=true
CALENDAR_REMINDER_2H=true

# --- RD Station Configuration ---
RDSTATION_URL=https://crm.rdstation.com
RDSTATION_API_URL=https://api.rd.services/platform
RDSTATION_ACCESS_TOKEN=xxxxx
RDSTATION_USER_TECNICO=xxxxx

# --- N8n Workflow IDs ---
WORKFLOW_ID_EMAIL_CONFIRMATION=7
WORKFLOW_ID_APPOINTMENT_REMINDERS=6
```

---

## 🗄️ Database Schema Updates

### Campo `scheduled_time_end` já existe ✅
```sql
-- Já existe na estrutura atual
-- scheduled_time_start: time without time zone
-- scheduled_time_end: time without time zone
```

### Novo Status
```sql
-- Adicionar novo status para error handling
ALTER TABLE appointments
DROP CONSTRAINT IF EXISTS valid_status;

ALTER TABLE appointments
ADD CONSTRAINT valid_status
CHECK (status IN (
    'agendado',
    'confirmado',
    'em_andamento',
    'realizado',
    'cancelado',
    'reagendado',
    'no_show',
    'erro_calendario'  -- NOVO
));
```

### Índice para Google Event ID
```sql
-- Adicionar índice para queries por google_calendar_event_id
CREATE INDEX IF NOT EXISTS idx_appointments_google_event
ON appointments(google_calendar_event_id)
WHERE google_calendar_event_id IS NOT NULL;
```

---

## 📊 Comparação: V1.0 vs V2.0

| Aspecto | V1.0 Atual | V2.0 Refatorado |
|---------|-----------|-----------------|
| **Nodes** | 8 nodes | 10 nodes (+2) |
| **Code Nodes** | 1 (57 linhas) | 3 (modular) |
| **Error Handling** | ❌ None | ✅ Complete |
| **Retry Logic** | ❌ None | ✅ 3 retries |
| **Validation** | ❌ None | ✅ Input + Availability |
| **Database Queries** | 2 SELECT + 2 UPDATE | 1 SELECT + 1 UPDATE (atomic) |
| **Hardcoded Values** | ✅ Many | ❌ Env vars |
| **Logging** | ❌ None | ✅ Structured |
| **Rollback** | ❌ None | ✅ Atomic transaction |
| **Maintainability** | 🟡 Medium | ✅ High |
| **Pattern Compliance** | ❌ No | ✅ V69.2 pattern |

---

## 🚀 Implementação

### Fase 1: Preparação
1. ✅ Análise do workflow atual
2. ✅ Definição do padrão V69.2
3. ✅ Planejamento da nova arquitetura
4. ⏳ Atualização do `.env` com novas variáveis
5. ⏳ Migration SQL para novo status

### Fase 2: Desenvolvimento
1. ⏳ Criar script Python gerador (v2.0)
2. ⏳ Implementar nodes de validação
3. ⏳ Refatorar Build Calendar Event
4. ⏳ Adicionar error handling
5. ⏳ Implementar retry logic

### Fase 3: Testes
1. ⏳ Teste unitário (cada node)
2. ⏳ Teste de integração (fluxo completo)
3. ⏳ Teste de error scenarios
4. ⏳ Teste de rollback
5. ⏳ Validação de logging

### Fase 4: Deploy
1. ⏳ Backup do workflow V1.0
2. ⏳ Import do workflow V2.0
3. ⏳ Testes em DEV
4. ⏳ Deploy em PROD
5. ⏳ Monitoramento pós-deploy

---

## 🧪 Casos de Teste

### 1. Fluxo Normal (Happy Path)
```
Input: appointment_id válido
Expected:
  - Google event criado
  - Status 'confirmado'
  - Reminders criados
  - RD Task criada
  - Email enviado
```

### 2. Google Calendar Error
```
Input: appointment_id válido + Google API down
Expected:
  - Status 'erro_calendario'
  - Error logged
  - Admin notified
  - No reminders/email sent
```

### 3. Invalid Availability
```
Input: appointment_id com horário fora do expediente
Expected:
  - Error thrown
  - Status não alterado
  - No Google event created
```

### 4. Missing Input
```
Input: appointment_id vazio
Expected:
  - Error thrown no Validate Input
  - Workflow stopped
```

### 5. Database Failure
```
Input: appointment_id válido + DB connection lost
Expected:
  - Error logged
  - Retry attempted
  - Graceful failure
```

---

## 📚 Documentação Atualizada

### SETUP_GOOGLE_CALENDAR.md Refatoração

#### Seção 5: Variáveis de Ambiente
```bash
# Atualizar com novas variáveis
GOOGLE_CALENDAR_CREDENTIAL_ID=VXA1r8sd0TMIdPvS  # NOVO
CALENDAR_WORK_START=08:00                        # NOVO
CALENDAR_WORK_END=18:00                          # NOVO
CALENDAR_WORK_DAYS=1,2,3,4,5                     # NOVO
```

#### Seção 9: Fluxo Completo
```
Atualizar diagrama com:
- Validação de entrada
- Validação de disponibilidade
- Error handling
- Retry logic
```

#### Seção 10: Troubleshooting
```
Adicionar novos cenários:
- "Status erro_calendario"
- "Retry exhausted"
- "Invalid business hours"
```

---

## ⚠️ Riscos e Mitigações

### Risco 1: Breaking Changes
**Impacto**: Alto
**Mitigação**:
- Manter V1.0 como fallback
- Testes extensivos em DEV
- Rollback plan documentado

### Risco 2: Google API Rate Limits
**Impacto**: Médio
**Mitigação**:
- Retry com backoff exponencial
- Monitoring de quotas
- Error handling robusto

### Risco 3: Database Migration
**Impacto**: Baixo
**Mitigação**:
- Migration backwards compatible
- Novo status opcional
- Dados existentes não afetados

---

## 📋 Checklist de Deploy

- [ ] `.env` atualizado com todas as variáveis
- [ ] Migration SQL executada com sucesso
- [ ] Script Python V2.0 gerado workflow
- [ ] Workflow V2.0 importado no n8n
- [ ] Credenciais Google Calendar configuradas
- [ ] Testes unitários executados
- [ ] Testes de integração executados
- [ ] Testes de error scenarios executados
- [ ] Backup do workflow V1.0 realizado
- [ ] Documentação atualizada
- [ ] Workflow V1.0 desativado
- [ ] Workflow V2.0 ativado
- [ ] Monitoramento configurado
- [ ] Testes em produção executados
- [ ] Validação de logs verificada

---

## 🎯 Próximos Passos

1. **Revisar e aprovar este plano**
2. **Atualizar `.env.dev` com novas variáveis**
3. **Executar migration SQL**
4. **Desenvolver script Python gerador V2.0**
5. **Testar em ambiente DEV**
6. **Deploy em PROD**

---

**Documento criado por**: Claude Code
**Padrão seguido**: V69.2 (WF02)
**Próxima revisão**: Após aprovação do plano
