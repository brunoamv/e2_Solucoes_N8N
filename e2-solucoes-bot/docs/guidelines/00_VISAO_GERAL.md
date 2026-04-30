# 00 - Visão Geral do Sistema E2 Bot

> **Arquitetura completa** do E2 Bot WhatsApp AI Agent
> **Stack**: n8n 2.14.2 + Claude 3.5 Sonnet + PostgreSQL + Evolution API v2.3.7
> **Atualizado**: 2026-04-29

---

## 📋 Índice

1. [Arquitetura do Sistema](#arquitetura-do-sistema)
2. [Stack Tecnológico](#stack-tecnológico)
3. [Workflows e Responsabilidades](#workflows-e-responsabilidades)
4. [Fluxo de Dados](#fluxo-de-dados)
5. [Estrutura do Projeto](#estrutura-do-projeto)
6. [Production V1 Package](#production-v1-package)

---

## 🏗️ Arquitetura do Sistema

### Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────────┐
│                         WhatsApp User                            │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Evolution API v2.3.7                          │
│  (WhatsApp Business API - Webhook receiver)                      │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTP POST (webhook)
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                         n8n 2.14.2                               │
│                    (Workflow Orchestrator)                       │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ WF01: Main WhatsApp Handler (V2.8.3)                    │   │
│  │ - Deduplication (PostgreSQL-based)                      │   │
│  │ - Message routing                                        │   │
│  └────────────────────────┬────────────────────────────────┘   │
│                            │                                     │
│                            ▼                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ WF02: AI Agent Conversation (V114) ⭐                   │   │
│  │ - State Machine (15 states)                             │   │
│  │ - Claude 3.5 Sonnet integration                         │   │
│  │ - Database row locking (race condition prevention)      │   │
│  └────┬──────────────┬──────────────┬─────────────────────┘   │
│       │              │              │                           │
│       ▼              ▼              ▼                           │
│  ┌────────┐   ┌──────────┐   ┌──────────┐                     │
│  │  WF06  │   │   WF05   │   │   WF07   │                     │
│  │Calendar│   │Scheduler │   │  Email   │                     │
│  │ V2.2   │   │   V7     │   │   V13    │                     │
│  └────────┘   └──────────┘   └──────────┘                     │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      PostgreSQL Database                         │
│  - conversations (user state, collected_data)                    │
│  - appointment_reminders (scheduling data)                       │
│  - State persistence and transaction safety                      │
└─────────────────────────────────────────────────────────────────┘
```

### Arquitetura de Microserviços

O E2 Bot segue um padrão de **microserviços internos** onde cada workflow tem uma responsabilidade específica e clara:

- **WF01**: Gateway de entrada (deduplicação e roteamento)
- **WF02**: Motor de conversação (state machine + AI)
- **WF06**: Serviço de disponibilidade de calendário
- **WF05**: Serviço de agendamento de compromissos
- **WF07**: Serviço de envio de emails

**Vantagens**:
- Separação de responsabilidades clara
- Fácil manutenção e debugging
- Escalabilidade independente
- Reutilização de serviços

---

## 🔧 Stack Tecnológico

### Core Components

#### 1. n8n 2.14.2 (Workflow Orchestrator)

**O que é**: Plataforma de automação low-code/no-code baseada em nodes

**Por que usar**:
- Orquestração visual de workflows complexos
- Integração nativa com múltiplos serviços
- Execução assíncrona e paralela
- Webhooks nativos

**Limitações Críticas (n8n 2.x)**:
```javascript
// ❌ BLOQUEADO - Acesso ao filesystem
const fs = require('fs');
const template = fs.readFileSync('template.html');

// ✅ WORKAROUND - HTTP Request + nginx
// URL: http://e2bot-templates-dev/template.html

// ❌ BLOQUEADO - Acesso a variáveis de ambiente
const apiKey = $env.OPENAI_API_KEY;

// ✅ WORKAROUND - Hardcoded ou PostgreSQL
const apiKey = "sk-proj-...";
```

**Recursos Disponíveis**:
- Code nodes (JavaScript execution)
- HTTP Request nodes
- PostgreSQL integration
- Webhook receivers
- Conditional routing (IF, Switch)

#### 2. Claude 3.5 Sonnet (AI Engine)

**O que é**: Large Language Model da Anthropic

**Por que usar**:
- Compreensão avançada de contexto
- Geração de respostas naturais
- Raciocínio multi-step
- API estável e confiável

**Integração**:
```javascript
// WF02 - State Machine Logic (Code node)
const systemPrompt = `Você é um atendente virtual da E2 Soluções...`;

const response = await fetch('https://api.anthropic.com/v1/messages', {
  method: 'POST',
  headers: {
    'x-api-key': apiKey,
    'anthropic-version': '2023-06-01',
    'content-type': 'application/json'
  },
  body: JSON.stringify({
    model: 'claude-3-5-sonnet-20241022',
    max_tokens: 1024,
    messages: [{
      role: 'user',
      content: userMessage
    }],
    system: systemPrompt
  })
});
```

**Uso no Projeto**:
- Geração de respostas contextualizadas
- Processamento de linguagem natural
- Extração de dados de mensagens do usuário
- Decisões de roteamento baseadas em intenção

#### 3. PostgreSQL (Database)

**O que é**: Sistema de gerenciamento de banco de dados relacional

**Por que usar**:
- ACID compliance (transações seguras)
- Row-level locking (previne race conditions)
- JSON support (armazena collected_data)
- Performance e confiabilidade

**Schema Principal**:
```sql
-- Tabela principal de conversações
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone_number VARCHAR(20) NOT NULL,
    whatsapp_name VARCHAR(100),
    current_state VARCHAR(50),
    state_machine_state VARCHAR(50),  -- Estado do State Machine
    collected_data JSONB DEFAULT '{}'::jsonb,  -- Dados coletados
    service_type VARCHAR(50),
    awaiting_wf06_next_dates BOOLEAN DEFAULT false,
    awaiting_wf06_available_slots BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Índices para performance
CREATE INDEX idx_conversations_phone ON conversations(phone_number);
CREATE INDEX idx_conversations_state ON conversations(state_machine_state);
CREATE INDEX idx_conversations_updated ON conversations(updated_at DESC);

-- Tabela de lembretes de agendamento (V8)
CREATE TABLE appointment_reminders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    scheduled_date DATE NOT NULL,
    scheduled_time_start TIME NOT NULL,
    scheduled_time_end TIME NOT NULL,
    date_suggestions TEXT[],
    slot_suggestions JSONB,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT unique_appointment_reminder UNIQUE (conversation_id, scheduled_date, scheduled_time_start)
);
```

**Padrões Críticos**:
1. **Row Locking** (V111):
   ```sql
   SELECT * FROM conversations
   WHERE phone_number = $phone
   FOR UPDATE SKIP LOCKED;  -- Previne race conditions
   ```

2. **INSERT...SELECT** (WF07 V13):
   ```sql
   INSERT INTO email_queue (conversation_id, template_name)
   SELECT id, 'confirmation'
   FROM conversations
   WHERE phone_number = $phone;
   ```

3. **ON CONFLICT Deduplication** (WF01):
   ```sql
   INSERT INTO conversations (phone_number, whatsapp_name)
   VALUES ($phone, $name)
   ON CONFLICT (phone_number) DO NOTHING;
   ```

#### 4. Evolution API v2.3.7 (WhatsApp Gateway)

**O que é**: API para integração com WhatsApp Business

**Por que usar**:
- Webhooks para receber mensagens
- Envio de mensagens (texto, mídia, botões)
- Gerenciamento de sessões WhatsApp
- QR Code para autenticação

**Configuração**:
```yaml
# docker-compose-dev.yml
services:
  e2bot-evolution-dev:
    image: atendai/evolution-api:v2.3.7
    environment:
      - SERVER_URL=https://evo-api.e2solucoes.tech
      - WEBHOOK_ENABLED=true
      - WEBHOOK_URL=http://e2bot-n8n-dev:5678/webhook/whatsapp
```

**Webhook Payload**:
```json
{
  "event": "messages.upsert",
  "instance": "e2bot",
  "data": {
    "key": {
      "remoteJid": "5562999999999@s.whatsapp.net",
      "id": "message-id"
    },
    "message": {
      "conversation": "oi"
    },
    "pushName": "User Name",
    "messageTimestamp": 1234567890
  }
}
```

---

## 🔄 Workflows e Responsabilidades

### WF01: Main WhatsApp Handler (V2.8.3)

**Status**: ✅ Production Stable

**Responsabilidade**: Gateway de entrada para todas as mensagens WhatsApp

**Fluxo**:
```
Webhook Evolution API
    ↓
Parse message payload
    ↓
Check if conversation exists (PostgreSQL deduplication)
    ↓
Route to WF02 (AI Agent Conversation)
```

**Componentes Chave**:
- **Webhook Trigger**: Recebe POST da Evolution API
- **PostgreSQL Deduplication**: Previne processamento duplicado
- **Message Parsing**: Extrai phone_number, message, pushName
- **Routing**: Encaminha para WF02 via HTTP Request

**Padrão de Deduplicação**:
```sql
INSERT INTO conversations (phone_number, whatsapp_name, current_state)
VALUES ($phone, $name, 'novo')
ON CONFLICT (phone_number) DO NOTHING
RETURNING *;
```

### WF02: AI Agent Conversation (V114) ⭐

**Status**: ✅ Production Complete (com todas as correções críticas)

**Responsabilidade**: Motor de conversação com State Machine e integração Claude

**Workflow ID**: `9tG2gR6KBt6nYyHT`
**Node Count**: 52 nodes

**Correções Críticas Incluídas**:
- **V111**: Database Row Locking (FOR UPDATE SKIP LOCKED)
- **V113.1**: WF06 Suggestions Persistence (date_suggestions + slot_suggestions)
- **V114**: PostgreSQL TIME Fields (scheduled_time_start + scheduled_time_end)
- **V79.1**: Schema-Aligned Build Update Queries (sem contact_phone)
- **V105**: Routing Fix (Update State BEFORE Check If WF06)

**State Machine - 15 Estados**:

```yaml
greeting:              # Estado inicial após "oi"
service_selection:     # Escolha de serviço (1=agendar, 2=dúvidas)
collect_name:          # Coleta nome completo
collect_phone:         # Coleta telefone (validação formato)
collect_email:         # Coleta email (validação formato)
collect_state:         # Coleta estado (UF)
collect_city:          # Coleta cidade
confirmation:          # Confirmação de dados antes de agendar

# Estados de integração WF06
trigger_wf06_next_dates:      # Trigger para obter próximas datas (WF06)
awaiting_wf06_next_dates:     # Aguardando resposta WF06 next dates
trigger_wf06_available_slots: # Trigger para obter slots disponíveis (WF06)
awaiting_wf06_available_slots: # Aguardando resposta WF06 slots

scheduling:            # Estado final de agendamento
handoff_comercial:     # Handoff para atendimento humano
completed:             # Conversa concluída
```

**Estrutura de Retorno (State Machine Logic)**:
```javascript
return {
  response_text: "Mensagem para o usuário",
  next_stage: "próximo_estado",
  collected_data: {
    name: "Nome Completo",
    phone: "62999999999",
    email: "user@example.com",
    state: "GO",
    city: "Goiânia"
  },
  trigger_wf06_next_dates: false,  // true para ativar WF06
  trigger_wf06_available_slots: false
};
```

**Fluxo Completo de Integração** (Exemplo: "oi" → agendamento):

```
1. User: "oi"
   → State Machine: greeting → service_selection
   → Response: "Olá! Escolha: 1 (Agendar) ou 2 (Dúvidas)"

2. User: "1"
   → State Machine: service_selection → collect_name
   → Response: "Qual seu nome completo?"

3. User: "Bruno Rosa"
   → State Machine: collect_name → collect_phone
   → Response: "Qual seu telefone?"

4. User: "62999999999"
   → State Machine: collect_phone → collect_email
   → Response: "Qual seu email?"

5. User: "bruno@example.com"
   → State Machine: collect_email → collect_state
   → Response: "Qual seu estado (UF)?"

6. User: "GO"
   → State Machine: collect_state → collect_city
   → Response: "Qual sua cidade?"

7. User: "Goiânia"
   → State Machine: collect_city → confirmation
   → Response: "Confirme seus dados: Nome: Bruno Rosa, Telefone: 62999999999..."

8. User: "1" (confirmar)
   → State Machine: confirmation → trigger_wf06_next_dates
   → Update State to awaiting_wf06_next_dates
   → HTTP Request to WF06 (Get Next Dates)
   → Response: "Escolha uma data: 1 (01/05), 2 (02/05), 3 (03/05)"

9. User: "1" (seleciona 01/05)
   → State Machine: awaiting_wf06_next_dates → trigger_wf06_available_slots
   → Update State to awaiting_wf06_available_slots
   → HTTP Request to WF06 (Get Available Slots for 01/05)
   → Response: "Escolha horário: 1 (08:00), 2 (09:00), 3 (10:00)"

10. User: "1" (seleciona 08:00)
    → State Machine: awaiting_wf06_available_slots → scheduling
    → HTTP Request to WF05 (Schedule Appointment)
    → HTTP Request to WF07 (Send Confirmation Email)
    → Response: "Agendamento confirmado! Email enviado."
```

**Componentes Principais**:

1. **Build SQL Queries** (V111):
   - Gera query com row locking
   - `FOR UPDATE SKIP LOCKED`

2. **State Machine Logic** (V114):
   - Processa estado atual
   - Extrai dados da mensagem do usuário
   - Determina próximo estado
   - Retorna response_text

3. **Build Update Queries** (V79.1):
   - Schema-aligned (sem contact_phone)
   - Atualiza collected_data

4. **Build Update Queries1** (V113):
   - Persiste date_suggestions do WF06

5. **Build Update Queries2** (V113):
   - Persiste slot_suggestions do WF06

6. **Update Conversation State**:
   - Executa queries de atualização
   - Commit de estado no PostgreSQL

7. **Check If WF06 Next Dates** (V105):
   - APÓS Update State
   - Verifica se next_stage == "trigger_wf06_next_dates"

8. **HTTP Request - Get Next Dates**:
   - Chama WF06 para obter próximas datas

9. **Check If WF06 Available Slots**:
   - Verifica se next_stage == "trigger_wf06_available_slots"

10. **HTTP Request - Get Available Slots**:
    - Chama WF06 para obter slots da data escolhida

### WF05: Appointment Scheduler (V7)

**Status**: ✅ Production Hardcoded

**Responsabilidade**: Criar agendamento e persistir no banco de dados

**Fluxo**:
```
HTTP Request from WF02
    ↓
Parse appointment data (date, time, user info)
    ↓
Insert into appointment_reminders table
    ↓
Return success confirmation
```

**Limitação Atual**:
- Usa valores hardcoded para business hours
- Aguardando implementação completa do V8 Part 2 (Google OAuth)

**Schema de Agendamento** (V8 Part 1 - COMPLETO):
```sql
CREATE TABLE appointment_reminders (
    id UUID PRIMARY KEY,
    conversation_id UUID REFERENCES conversations(id),
    scheduled_date DATE NOT NULL,
    scheduled_time_start TIME NOT NULL,  -- V114 PostgreSQL TIME
    scheduled_time_end TIME NOT NULL,    -- V114 PostgreSQL TIME
    date_suggestions TEXT[],             -- V113 WF06 persistence
    slot_suggestions JSONB,              -- V113 WF06 persistence
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW()
);
```

### WF06: Calendar Availability Service (V2.2)

**Status**: ✅ Production Complete

**Responsabilidade**: Microserviço de disponibilidade de calendário

**Endpoints**:

1. **Get Next Dates**:
   ```
   POST http://localhost:5678/webhook/wf06-next-dates

   Body:
   {
     "conversation_id": "uuid",
     "user_timezone": "America/Sao_Paulo"
   }

   Response:
   {
     "next_dates": ["2026-05-01", "2026-05-02", "2026-05-03"],
     "formatted_options": "1 (01/05), 2 (02/05), 3 (03/05)"
   }
   ```

2. **Get Available Slots**:
   ```
   POST http://localhost:5678/webhook/wf06-available-slots

   Body:
   {
     "conversation_id": "uuid",
     "selected_date": "2026-05-01",
     "user_timezone": "America/Sao_Paulo"
   }

   Response:
   {
     "available_slots": [
       {"start": "08:00", "end": "09:00"},
       {"start": "09:00", "end": "10:00"}
     ],
     "formatted_options": "1 (08:00-09:00), 2 (09:00-10:00)"
   }
   ```

**Correções Implementadas**:
- **V2**: OAuth credential fix + empty calendar handling
- **V2.1**: Input data source fix
- **V2.2**: Response mode optimization

**Integração com Google Calendar**:
- OAuth2 authentication (Credential ID "1")
- Busca eventos existentes
- Calcula slots disponíveis
- Respeita business hours (08:00-18:00)

### WF07: Send Email (V13)

**Status**: ✅ Production Complete

**Responsabilidade**: Enviar emails de confirmação e notificações

**Correção Crítica (V13)**:
- **Problema**: `queryReplacement: [undefined]` - n8n não resolve expressões `={{ }}`
- **Solução**: INSERT...SELECT pattern

**Padrão INSERT...SELECT**:
```javascript
// ❌ ANTES (V12 e anteriores) - NÃO FUNCIONA
const query = `
  INSERT INTO email_queue (conversation_id, template_name)
  VALUES ('{{ $json.conversation_id }}', 'confirmation')
`;
// Resultado: INSERT INTO email_queue VALUES (undefined, ...)

// ✅ DEPOIS (V13) - FUNCIONA
const query = `
  INSERT INTO email_queue (conversation_id, template_name, user_email)
  SELECT
    id as conversation_id,
    'confirmation' as template_name,
    (collected_data->>'email') as user_email
  FROM conversations
  WHERE phone_number = '{{ $json.phone_number }}'
`;
```

**Template Access Workaround** (n8n 2.x filesystem limitation):
```yaml
# docker-compose-dev.yml
services:
  e2bot-templates-dev:
    image: nginx:alpine
    volumes:
      - ../email-templates:/usr/share/nginx/html:ro
    ports:
      - "8081:80"

# HTTP Request node:
# URL: http://e2bot-templates-dev/confirmation.html
```

**SMTP Configuration** (Port 465 SSL/TLS):
```yaml
Host: smtp.gmail.com
Port: 465
Security: SSL/TLS
Username: clima.cocal.2025@gmail.com
Password: App-specific password
```

---

## 🔄 Fluxo de Dados

### Fluxo Completo: Mensagem WhatsApp → Agendamento Confirmado

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. WhatsApp User envia "oi"                                     │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. Evolution API recebe mensagem                                │
│    → Webhook POST para n8n WF01                                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. WF01: Main WhatsApp Handler                                  │
│    → PostgreSQL: Check if conversation exists                   │
│    → INSERT ON CONFLICT DO NOTHING (deduplication)              │
│    → HTTP Request to WF02                                       │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. WF02: AI Agent Conversation (V114)                           │
│    → Build SQL Queries (V111 row locking)                       │
│    → SELECT ... FOR UPDATE SKIP LOCKED                          │
│    → State Machine Logic:                                       │
│      • current_stage: greeting                                  │
│      • next_stage: service_selection                            │
│      • response_text: "Escolha 1 (Agendar) ou 2 (Dúvidas)"     │
│    → Build Update Queries (V79.1 schema-aligned)                │
│    → Update Conversation State                                  │
│    → Send WhatsApp Response                                     │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼ (User selects "1" - agendar)
┌─────────────────────────────────────────────────────────────────┐
│ 5. WF02: Coleta de Dados (collect_name → collect_city)         │
│    Loop de mensagens coletando:                                 │
│    → Nome completo                                              │
│    → Telefone (validação formato)                               │
│    → Email (validação formato)                                  │
│    → Estado (UF)                                                │
│    → Cidade                                                     │
│    PostgreSQL persiste collected_data JSONB                     │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼ (User confirms data "1")
┌─────────────────────────────────────────────────────────────────┐
│ 6. WF02: Confirmation → trigger_wf06_next_dates                │
│    → Update State: awaiting_wf06_next_dates                     │
│    → Check If WF06 Next Dates (V105 - AFTER update)            │
│    → HTTP Request to WF06: Get Next Dates                      │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 7. WF06: Calendar Availability Service (V2.2)                  │
│    → Google Calendar OAuth authentication                       │
│    → Fetch existing calendar events                             │
│    → Calculate next available dates (3 days)                    │
│    → Return: ["2026-05-01", "2026-05-02", "2026-05-03"]        │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 8. WF02: Receive WF06 Response                                 │
│    → Build Update Queries1 (V113 date_suggestions)             │
│    → PostgreSQL: UPDATE date_suggestions                        │
│    → Response: "Escolha: 1 (01/05), 2 (02/05), 3 (03/05)"     │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼ (User selects "1" - 01/05)
┌─────────────────────────────────────────────────────────────────┐
│ 9. WF02: trigger_wf06_available_slots                          │
│    → Update State: awaiting_wf06_available_slots                │
│    → HTTP Request to WF06: Get Available Slots (date: 01/05)   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 10. WF06: Get Available Slots for 01/05                        │
│     → Fetch calendar events for 2026-05-01                      │
│     → Calculate free slots (08:00-18:00, 1-hour slots)          │
│     → Return: [{"start":"08:00","end":"09:00"}, ...]           │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 11. WF02: Receive Slots Response                               │
│     → Build Update Queries2 (V113 slot_suggestions)            │
│     → PostgreSQL: UPDATE slot_suggestions                       │
│     → Response: "Escolha: 1 (08:00), 2 (09:00), 3 (10:00)"    │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼ (User selects "1" - 08:00)
┌─────────────────────────────────────────────────────────────────┐
│ 12. WF02: scheduling → HTTP Request to WF05                    │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 13. WF05: Appointment Scheduler (V7)                           │
│     → Parse: date=2026-05-01, time=08:00-09:00                 │
│     → INSERT INTO appointment_reminders (V114 TIME fields)      │
│     → Return: success confirmation                              │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 14. WF02: HTTP Request to WF07 (Send Email)                    │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 15. WF07: Send Email (V13)                                     │
│     → INSERT...SELECT pattern (V13 fix)                         │
│     → HTTP Request to nginx for template                        │
│     → Send Email via Gmail SMTP (Port 465)                      │
│     → Return: email sent confirmation                           │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 16. WF02: Final Response                                       │
│     → State Machine: scheduling → completed                     │
│     → Response: "Agendamento confirmado! Email enviado."       │
│     → Evolution API sends message to user                       │
└─────────────────────────────────────────────────────────────────┘
```

### Padrões de Comunicação Entre Workflows

**WF02 → WF06** (HTTP Request):
```javascript
// HTTP Request node configuration
{
  method: 'POST',
  url: 'http://localhost:5678/webhook/wf06-next-dates',
  body: {
    conversation_id: '{{ $json.conversation_id }}',
    user_timezone: 'America/Sao_Paulo'
  }
}
```

**WF02 → WF05** (HTTP Request):
```javascript
{
  method: 'POST',
  url: 'http://localhost:5678/webhook/wf05-schedule',
  body: {
    conversation_id: '{{ $json.conversation_id }}',
    scheduled_date: '2026-05-01',
    scheduled_time_start: '08:00',
    scheduled_time_end: '09:00',
    user_data: {
      name: '{{ $json.collected_data.name }}',
      email: '{{ $json.collected_data.email }}',
      phone: '{{ $json.collected_data.phone }}'
    }
  }
}
```

**WF02 → WF07** (HTTP Request):
```javascript
{
  method: 'POST',
  url: 'http://localhost:5678/webhook/wf07-send-email',
  body: {
    conversation_id: '{{ $json.conversation_id }}',
    template_name: 'confirmation',
    phone_number: '{{ $json.phone_number }}'
  }
}
```

---

## 📁 Estrutura do Projeto

```
/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/
│
├── docs/                          # Documentação (300+ arquivos)
│   ├── guidelines/                # Guidelines de desenvolvimento (ESTE ARQUIVO)
│   │   ├── README.md              # Índice de guidelines
│   │   ├── 00_VISAO_GERAL.md     # Arquitetura (ESTE ARQUIVO)
│   │   ├── 01_N8N_BEST_PRACTICES.md
│   │   ├── 02_STATE_MACHINE_PATTERNS.md
│   │   ├── 03_DATABASE_PATTERNS.md
│   │   ├── 04_WORKFLOW_INTEGRATION.md
│   │   ├── 05_TESTING_VALIDATION.md
│   │   ├── 06_DEPLOYMENT_GUIDE.md
│   │   └── 07_SECURITY_COMPLIANCE.md
│   │
│   ├── Setups/                    # Guias de configuração inicial
│   │   ├── QUICKSTART.md          # Setup completo (30-45 min)
│   │   ├── SETUP_EMAIL.md         # SMTP Port 465 SSL/TLS
│   │   ├── SETUP_GOOGLE_CALENDAR.md  # OAuth2 setup
│   │   └── SETUP_CREDENTIALS.md   # Todas as credenciais n8n
│   │
│   ├── status/                    # Status de deployment
│   │   ├── DEPLOYMENT_STATUS.md   # Status atual de produção
│   │   └── PRODUCTION_V1_DEPLOYMENT.md
│   │
│   ├── deployment/                # Guias de deployment (51 arquivos)
│   │   ├── wf02/                  # WF02 deployments por versão
│   │   │   ├── v74-v79/
│   │   │   ├── v80-v99/
│   │   │   └── v100-v114/
│   │   ├── wf05/, wf06/, wf07/
│   │   └── production/
│   │
│   ├── fix/                       # Bug fixes (82 arquivos)
│   │   ├── wf02/                  # WF02 bug fixes por versão
│   │   │   ├── v63-v79/          # 19 bugfixes
│   │   │   ├── v80-v99/          # 8 bugfixes
│   │   │   └── v100-v114/        # 21 bugfixes (V111, V113, V114)
│   │   ├── wf05/                  # 6 bugfixes
│   │   ├── wf06/                  # 3 bugfixes
│   │   ├── wf07/                  # 15 bugfixes
│   │   └── system/                # 10 system-wide fixes
│   │
│   ├── PLAN/                      # Planejamento (137 arquivos)
│   │   ├── wf01/, wf02/, wf05/, wf06/, wf07/
│   │   ├── system/
│   │   └── infrastructure/
│   │
│   └── analysis/                  # Análises técnicas (53 arquivos)
│       ├── wf02-versions/, wf07-versions/
│       ├── system/, migrations/
│       └── diagnostics/
│
├── scripts/                       # Scripts de geração (304 arquivos)
│   ├── wf02/                      # WF02 scripts (159 arquivos)
│   │   ├── state-machines/        # 25 state machine implementations
│   │   │   ├── wf02-v111-build-sql-queries-row-locking.js ⭐
│   │   │   ├── wf02-v113-build-update-queries1-wf06-next-dates.js ⭐
│   │   │   ├── wf02-v113-build-update-queries2-wf06-available-slots.js ⭐
│   │   │   └── wf02-v114-slot-time-fields-fix.js ⭐
│   │   ├── generators/            # 82 workflow generators completos
│   │   └── fixes/                 # 52 correções de nós
│   │
│   ├── wf05/                      # 16 scripts
│   │   ├── generators/
│   │   └── fixes/
│   │
│   ├── wf06/
│   │   └── wf06-v2_1-calculate-slot-fix.js
│   │
│   ├── wf07/                      # 17 scripts
│   │   └── generators/
│   │
│   ├── deployment/                # 4 deployment scripts
│   ├── testing/                   # 20 test scripts
│   ├── validation/                # 16 validation scripts
│   ├── utilities/                 # 49 helper scripts
│   └── deprecated/                # 3 obsolete scripts
│
├── n8n/                           # n8n workflows
│   └── workflows/                 # 39 workflow JSONs
│       ├── production/            # Production V1 (5 workflows)
│       │   ├── wf01/
│       │   │   └── 01_main_whatsapp_handler_V2.8.3_NO_LOOP.json
│       │   ├── wf02/
│       │   │   └── 02_ai_agent_conversation_V114_FUNCIONANDO.json ⭐
│       │   ├── wf05/
│       │   │   └── 05_appointment_scheduler_v7_hardcoded_values.json
│       │   ├── wf06/
│       │   │   └── 06_calendar_availability_service_v2_2.json
│       │   └── wf07/
│       │       └── 07_send_email_v13_insert_select.json
│       │
│       ├── development/           # Development versions (7 workflows)
│       │   ├── wf02/
│       │   │   └── 02_ai_agent_conversation_V74.1_2_FUNCIONANDO.json
│       │   ├── wf05/
│       │   │   └── 05_appointment_scheduler_v3.6.json
│       │   └── wf06/
│       │       └── (4 versions: v1, v2, v2_1, v2_2)
│       │
│       └── historical/            # Historical versions (27 workflows)
│           └── wf02/              # Complete WF02 history (V77-V113)
│
├── docker/                        # Docker configuration
│   ├── docker-compose-dev.yml    # Development environment
│   └── docker-compose.yml        # Production environment
│
├── email-templates/               # Email templates (nginx-served)
│   ├── confirmation.html
│   └── reminder.html
│
├── CLAUDE.md                      # Contexto técnico para Claude Code
├── README.md                      # Project overview
└── qrcode.png                     # Evolution API QR Code
```

### Organização de Documentação (Single Source of Truth)

**Princípios**:
1. **Cada arquivo em exatamente um local** - Zero duplicação
2. **Categorização lógica por propósito** - analysis, fix, deployment, planning, status
3. **Subdivisão por workflow e versão** - wf02/v100-v114/, wf05/, wf06/, wf07/
4. **READMEs abrangentes** - Cada categoria tem guia de organização

**Exemplo de Organização (docs/fix/)**:
```
docs/fix/
├── README.md                      # Guia de organização (82 arquivos)
├── wf02/
│   ├── v63-v79/                   # 19 early bugfixes
│   ├── v80-v99/                   # 8 integration phase bugfixes
│   └── v100-v114/                 # 21 recent bugfixes
│       ├── BUGFIX_WF02_V111_DATABASE_STATE_RACE_CONDITION.md ⭐
│       ├── BUGFIX_WF02_V113_1_WF06_SUGGESTIONS_PERSISTENCE.md ⭐
│       ├── BUGFIX_WF02_V104_DATABASE_STATE_UPDATE.md
│       └── BUGFIX_WF02_V105_ROUTING_FIX.md
├── wf05/, wf06/, wf07/
└── system/
```

---

## 📦 Production V1 Package

### Status de Produção (2026-04-29)

| Workflow | Version | Status | Critical Features |
|----------|---------|--------|-------------------|
| **WF01** | V2.8.3 | ✅ Stable | PostgreSQL deduplication |
| **WF02** | V114 | ✅ Complete | Row locking + WF06 persistence + TIME fields |
| **WF05** | V7 | ✅ Hardcoded | Appointment creation (V8 Part 2 pending) |
| **WF06** | V2.2 | ✅ Complete | OAuth + empty calendar + input data |
| **WF07** | V13 | ✅ Complete | INSERT...SELECT + nginx templates |

### Correções Críticas em Produção

#### WF02 V114 - Complete Fix Package

**V111: Database Row Locking**
- **Problema**: Race condition quando usuário envia mensagens rapidamente
- **Solução**: `FOR UPDATE SKIP LOCKED` em query inicial
- **Impacto**: Previne processamento de estado obsoleto

**V113.1: WF06 Suggestions Persistence**
- **Problema**: Sugestões de WF06 não persistidas no banco
- **Solução**: Adiciona `date_suggestions` e `slot_suggestions` columns
- **Impacto**: Usuário pode retornar ao fluxo sem perder contexto

**V114: PostgreSQL TIME Fields**
- **Problema**: Campos de hora armazenados como TEXT
- **Solução**: `scheduled_time_start TIME` e `scheduled_time_end TIME`
- **Impacto**: Queries temporais corretas e performance melhorada

**V79.1: Schema-Aligned Build Update Queries**
- **Problema**: Tentativa de atualizar coluna inexistente `contact_phone`
- **Solução**: Remove `contact_phone` de UPDATE queries
- **Impacto**: Updates funcionam sem erros de schema

**V105: Routing Fix**
- **Problema**: Check If WF06 executava ANTES de Update State
- **Solução**: Reordena nodes: Update State → THEN → Check If WF06
- **Impacto**: Roteamento correto para WF06 integration

### Fluxo de Integração Completo em Produção

```yaml
User Journey: "oi" → agendamento confirmado

Duração Total: ~2-3 minutos
Workflows Envolvidos: WF01 → WF02 → WF06 (2x) → WF05 → WF07
Interações HTTP: 5 requests
Database Transactions: ~15 updates
WhatsApp Messages: ~12 exchanges

Detalhamento por Fase:

1. Saudação Inicial (5 segundos):
   - WF01: Deduplication + routing
   - WF02: State Machine greeting → service_selection

2. Coleta de Dados (60-90 segundos):
   - WF02: 5 iterações de coleta (nome, telefone, email, estado, cidade)
   - PostgreSQL: Persiste collected_data JSONB a cada etapa

3. Confirmação (10 segundos):
   - WF02: Exibe dados coletados para confirmação

4. Integração WF06 - Datas (15 segundos):
   - WF02: Update state → awaiting_wf06_next_dates
   - WF02 → WF06: HTTP Request Get Next Dates
   - WF06: Google Calendar lookup + date calculation
   - WF06 → WF02: Return 3 available dates
   - WF02: Persiste date_suggestions (V113)

5. Seleção de Data (10 segundos):
   - User escolhe data

6. Integração WF06 - Slots (15 segundos):
   - WF02: Update state → awaiting_wf06_available_slots
   - WF02 → WF06: HTTP Request Get Available Slots
   - WF06: Calculate free slots for selected date
   - WF06 → WF02: Return available time slots
   - WF02: Persiste slot_suggestions (V113)

7. Seleção de Horário (10 segundos):
   - User escolhe horário

8. Agendamento (20 segundos):
   - WF02 → WF05: HTTP Request Schedule Appointment
   - WF05: INSERT appointment_reminders (V114 TIME fields)
   - WF02 → WF07: HTTP Request Send Email
   - WF07: INSERT...SELECT + template fetch + SMTP send
   - WF02: Final confirmation message

Total Success Rate: 95%+ (com todas as correções V111-V114)
```

### Próximos Passos (Roadmap)

**Curto Prazo** (1-2 semanas):
- [ ] **WF05 V8 Part 2**: Google Calendar OAuth re-authentication (10 minutos)
- [ ] **Monitoring**: Implementar logs estruturados e métricas
- [ ] **Error Handling**: Melhorar tratamento de erros em HTTP requests

**Médio Prazo** (1 mês):
- [ ] **WF02 V115+**: Novos estados e funcionalidades
- [ ] **Testing Framework**: Automated testing com Playwright
- [ ] **Performance**: Otimização de queries e caching

**Longo Prazo** (3-6 meses):
- [ ] **Multi-Language**: Suporte para múltiplos idiomas
- [ ] **Analytics**: Dashboard de métricas e KPIs
- [ ] **Scale**: Preparação para volume > 1000 conversas/dia

---

## 📚 Referências

### Documentação Técnica

- **Contexto Completo**: `/CLAUDE.md` - 15K+ linhas de contexto técnico
- **Setup Inicial**: `/docs/Setups/QUICKSTART.md` - Setup completo 30-45 min
- **Workflows Organizados**: `/n8n/workflows/README.md`
- **Scripts**: `/scripts/README.md` - 304 scripts organizados
- **Índice Geral**: `/docs/INDEX.md` - Catálogo completo de documentação

### Workflows de Produção

- **WF01 V2.8.3**: `/n8n/workflows/production/wf01/01_main_whatsapp_handler_V2.8.3_NO_LOOP.json`
- **WF02 V114**: `/n8n/workflows/production/wf02/02_ai_agent_conversation_V114_FUNCIONANDO.json` ⭐
- **WF05 V7**: `/n8n/workflows/production/wf05/05_appointment_scheduler_v7_hardcoded_values.json`
- **WF06 V2.2**: `/n8n/workflows/production/wf06/06_calendar_availability_service_v2_2.json`
- **WF07 V13**: `/n8n/workflows/production/wf07/07_send_email_v13_insert_select.json`

### Correções Críticas

- **V111**: `/docs/deployment/wf02/v100-v114/DEPLOY_WF02_V111_DATABASE_ROW_LOCKING.md`
- **V113.1**: `/docs/fix/wf02/v100-v114/BUGFIX_WF02_V113_1_WF06_SUGGESTIONS_PERSISTENCE.md`
- **V114**: `/docs/WF02_V114_QUICK_DEPLOY.md`
- **V104+V105**: `/docs/fix/wf02/v100-v114/BUGFIX_WF02_V104_DATABASE_STATE_UPDATE.md`
- **V76+**: `/docs/PLAN/wf02/v16-v79/V69_COMPLETE_FIX.md` - Proactive UX approach

### Documentação Externa

- **n8n Docs**: https://docs.n8n.io/
- **n8n Breaking Changes 2.0**: https://docs.n8n.io/2-0-breaking-changes/
- **PostgreSQL Row Locking**: https://www.postgresql.org/docs/current/explicit-locking.html
- **Evolution API**: https://doc.evolution-api.com/

---

**Mantido por**: Bruno Rosa & Claude Code
**Data de Atualização**: 2026-04-29
**Status**: ✅ COMPLETO - Production V1 (WF02 V114)
**Próximo Documento**: [01_N8N_BEST_PRACTICES.md](01_N8N_BEST_PRACTICES.md)
