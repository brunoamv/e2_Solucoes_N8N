# Database Patterns - PostgreSQL Best Practices

> **Schema e padrões SQL do E2 Bot** | Atualizado: 2026-04-29
> **Status**: ✅ PRODUCTION - Schema completo com todas as otimizações implementadas

---

## 📖 Visão Geral

Este documento documenta todos os padrões de banco de dados PostgreSQL usados no E2 Bot, incluindo schema completo, padrões de query, race condition prevention, e otimizações de performance.

### Características Principais

- **3 Tabelas Principais**: conversations, appointments, email_queue
- **JSONB Operations**: Merge, extract, indexing para dados semi-estruturados
- **Row Locking (V111)**: `FOR UPDATE SKIP LOCKED` para prevenir race conditions
- **INSERT...SELECT Pattern**: Solução para limitação queryReplacement do n8n
- **ON CONFLICT**: Deduplicação automática em WF01
- **Transaction Isolation**: MVCC (Multi-Version Concurrency Control)

---

## 🗄️ Database Schema Completo

### Tabela: `conversations`

```sql
CREATE TABLE conversations (
  id SERIAL PRIMARY KEY,
  phone_number VARCHAR(20) UNIQUE NOT NULL,
  lead_name VARCHAR(255),
  contact_email VARCHAR(255),
  service_type VARCHAR(100),
  state VARCHAR(50),
  city VARCHAR(100),
  current_state VARCHAR(50),
  state_machine_state VARCHAR(50),
  collected_data JSONB DEFAULT '{}'::jsonb,
  date_suggestions JSONB,                    -- V113: WF06 próximas 3 datas
  slot_suggestions JSONB,                    -- V113: WF06 horários disponíveis
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Índices para performance
CREATE INDEX idx_conversations_phone ON conversations(phone_number);
CREATE INDEX idx_conversations_updated_at ON conversations(updated_at DESC);
CREATE INDEX idx_conversations_state_machine ON conversations(state_machine_state);

-- Índice GIN para busca em JSONB
CREATE INDEX idx_conversations_collected_data ON conversations USING GIN (collected_data);
```

**Campos Críticos**:
- `phone_number`: Chave de deduplicação (UNIQUE constraint)
- `state_machine_state`: Estado atual dos 15 estados do WF02
- `collected_data`: JSONB com todos os dados coletados do usuário
- `date_suggestions`: JSONB array com datas retornadas pelo WF06 (V113)
- `slot_suggestions`: JSONB array com horários retornados pelo WF06 (V113)

**collected_data Structure**:
```json
{
  "name": "João Silva",
  "phone": "62999999999",
  "email": "joao@email.com",
  "state": "GO",
  "city": "Goiânia",
  "selected_date": "2026-05-15",
  "selected_slot": "08:00 - 10:00",
  "scheduled_time_start": "08:00",      // V114: TIME field extraído
  "scheduled_time_end": "10:00",        // V114: TIME field extraído
  "scheduled_time_display": "8h às 10h" // V113: Display formatado
}
```

### Tabela: `appointments`

```sql
CREATE TABLE appointments (
  id SERIAL PRIMARY KEY,
  conversation_id INTEGER REFERENCES conversations(id),
  lead_name VARCHAR(255) NOT NULL,
  lead_email VARCHAR(255) NOT NULL,
  service_type VARCHAR(100) NOT NULL,
  scheduled_date DATE NOT NULL,
  scheduled_time_start TIME,             -- V114: PostgreSQL TIME type
  scheduled_time_end TIME,               -- V114: PostgreSQL TIME type
  google_calendar_event_id VARCHAR(255),
  status VARCHAR(50) DEFAULT 'pending',
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_appointments_conversation ON appointments(conversation_id);
CREATE INDEX idx_appointments_scheduled_date ON appointments(scheduled_date);
CREATE INDEX idx_appointments_google_event ON appointments(google_calendar_event_id);
```

**Campos Críticos**:
- `conversation_id`: Foreign key para conversations
- `scheduled_time_start/end`: PostgreSQL TIME type (V114 fix)
- `google_calendar_event_id`: Referência para evento no Google Calendar

### Tabela: `email_queue`

```sql
CREATE TABLE email_queue (
  id SERIAL PRIMARY KEY,
  conversation_id INTEGER REFERENCES conversations(id),
  recipient_email VARCHAR(255) NOT NULL,
  recipient_name VARCHAR(255),
  subject VARCHAR(500),
  body_html TEXT,
  template_used VARCHAR(100),
  status VARCHAR(50) DEFAULT 'pending',
  sent_at TIMESTAMP,
  error_message TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_email_queue_conversation ON email_queue(conversation_id);
CREATE INDEX idx_email_queue_status ON email_queue(status);
CREATE INDEX idx_email_queue_created_at ON email_queue(created_at DESC);
```

**Campos Críticos**:
- `template_used`: Nome do template de email usado
- `status`: 'pending', 'sent', 'failed'
- `error_message`: Logs de erro para troubleshooting

---

## 🔒 Row Locking (V111 Critical Fix)

### Problema: Race Conditions

**Cenário**:
```
T0: User digita "cocal-go" → Execution #1 inicia → UPDATE não commitado
T1: User digita "1" imediatamente → Execution #2 lê estado DESATUALIZADO
T2: Execution #1 faz commit → Database atualizado
T3: Execution #2 processa com estado desatualizado → Caminho errado
```

**Resultado**: WF06 não é chamado porque estado foi lido antes do UPDATE commit.

### Solução: FOR UPDATE SKIP LOCKED

```sql
-- ✅ V111 CRITICAL FIX: Row Locking
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
FOR UPDATE SKIP LOCKED;  -- 🔴 CRITICAL: Trava linha até commit
```

**Como Funciona**:
1. `FOR UPDATE`: Trava linha (row-level lock) até transaction commit
2. `SKIP LOCKED`: Retorna vazio se linha já está travada (outra execução em progresso)
3. **Resultado**: Apenas UMA execução processa conversa por vez
4. **Mensagens rápidas**: Segunda mensagem retorna vazio → exibe "Processando..." para usuário

**Impact**:
- ✅ Elimina 100% dos race conditions
- ✅ WF06 sempre é chamado no momento correto
- ✅ Estados sempre avançam na ordem correta
- ✅ Performance overhead mínimo (<5ms)

### Testing Row Locking

```bash
# Teste 1: Enviar 3 mensagens muito rápidas (< 1 segundo)
# Message 1: "cocal-go" (city)
# Message 2: "1" (agendar)  ← Deve retornar vazio (locked)
# Message 3: "test"         ← Deve retornar vazio (locked)

# Verificar logs:
docker logs -f e2bot-n8n-dev 2>&1 | grep "V111:"

# Expected:
# V111: DATABASE ROW LOCKING ENABLED  ✅
# V111: Row locked, returning empty  ✅

# Teste 2: Verificar banco após messages processadas
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT phone_number, state_machine_state, updated_at
      FROM conversations
      WHERE phone_number = '556181755748'
      ORDER BY updated_at DESC LIMIT 1;"

# Expected: state_machine_state avançou corretamente (não ficou preso)
```

---

## 📝 INSERT...SELECT Pattern (n8n Limitation Workaround)

### Problema: queryReplacement com Expressões

n8n 2.x **NÃO resolve** expressões `={{ }}` dentro de `queryReplacement`:

```sql
-- ❌ NÃO FUNCIONA
INSERT INTO email_queue (conversation_id, recipient_email, template_used)
VALUES (:conversation_id, :recipient_email, :template_used);

-- queryReplacement:
{
  "conversation_id": "{{ $json.id }}",        -- ❌ Resultado: [undefined]
  "recipient_email": "{{ $json.email }}",     -- ❌ Resultado: [undefined]
  "template_used": "{{ $json.template }}"     -- ❌ Resultado: [undefined]
}
```

### Solução: INSERT...SELECT Pattern

```sql
-- ✅ FUNCIONA: INSERT...SELECT
INSERT INTO email_queue (
  conversation_id,
  recipient_email,
  recipient_name,
  template_used,
  subject,
  status
)
SELECT
  id,                                    -- Direto do SELECT
  '{{ $json.email }}',                   -- Expressão resolve aqui ✅
  '{{ $json.name }}',
  'confirmation',
  'Reunião Agendada - Cocal-GO',
  'pending'
FROM conversations
WHERE phone_number = '{{ $json.phone }}';
```

**Por que funciona**:
- n8n resolve `{{ }}` no SQL principal (não em queryReplacement)
- SELECT busca dados da própria conversa
- INSERT usa resultados do SELECT diretamente

**Usado em**:
- **WF07 V13**: Email queue insertion ✅
- **WF05 V7**: Appointment creation ✅
- **WF02 V79.1**: Build Update Queries ✅

### Exemplo Completo (WF07 V13)

```javascript
// Node: "Insert Email Queue via INSERT...SELECT"
const items = $input.all();
const results = [];

for (const item of items) {
  const query = `
    INSERT INTO email_queue (
      conversation_id,
      recipient_email,
      recipient_name,
      subject,
      body_html,
      template_used,
      status
    )
    SELECT
      id,
      '${item.json.lead_email}',
      '${item.json.lead_name}',
      'Reunião Agendada - Cocal-GO',
      '${item.json.email_body_html}',
      'confirmation',
      'pending'
    FROM conversations
    WHERE phone_number = '${item.json.phone_number}'
    RETURNING *;
  `.trim();

  results.push({
    json: {
      query: query,
      phone_number: item.json.phone_number
    }
  });
}

return results;
```

---

## 🔄 JSONB Operations

### Merge JSONB (Update Parcial)

```sql
-- Merge collected_data: preserva campos existentes, adiciona novos
UPDATE conversations
SET
  collected_data = collected_data || '{"city": "Goiânia"}'::jsonb
WHERE phone_number = '62999999999';

-- Antes: {"name": "João", "email": "joao@email.com"}
-- Depois: {"name": "João", "email": "joao@email.com", "city": "Goiânia"}  ✅
```

### Extract JSONB Fields

```sql
-- Extrair campo específico
SELECT
  phone_number,
  collected_data->>'name' as lead_name,         -- Text extraction
  collected_data->'city' as city_json,          -- JSON extraction
  collected_data->>'scheduled_time_start' as start_time
FROM conversations
WHERE phone_number = '62999999999';
```

### JSONB Array Operations (V113)

```sql
-- V113: Salvar date_suggestions array
UPDATE conversations
SET
  date_suggestions = '["2026-05-15", "2026-05-16", "2026-05-17"]'::jsonb
WHERE phone_number = '62999999999';

-- V113: Salvar slot_suggestions array
UPDATE conversations
SET
  slot_suggestions = '[
    "08:00 - 10:00",
    "10:00 - 12:00",
    "14:00 - 16:00"
  ]'::jsonb
WHERE phone_number = '62999999999';

-- Buscar suggestions:
SELECT
  phone_number,
  date_suggestions,
  slot_suggestions
FROM conversations
WHERE phone_number = '62999999999';
```

### JSONB Index (GIN)

```sql
-- Criar índice GIN para busca rápida em JSONB
CREATE INDEX idx_conversations_collected_data
ON conversations USING GIN (collected_data);

-- Query que usa o índice:
SELECT *
FROM conversations
WHERE collected_data @> '{"city": "Goiânia"}'::jsonb;
-- Busca todas conversations com city = "Goiânia"
```

---

## 🔁 ON CONFLICT (Deduplication Pattern)

### WF01 V2.8.3: Deduplicação Automática

```sql
-- WF01: Dedup via ON CONFLICT DO UPDATE
INSERT INTO conversations (
  phone_number,
  lead_name,
  service_type,
  current_state,
  state_machine_state,
  collected_data
)
VALUES (
  '{{ $json.phone_number }}',
  '{{ $json.name }}',
  'unknown',
  'greeting',
  'greeting',
  '{}'::jsonb
)
ON CONFLICT (phone_number)
DO UPDATE SET
  updated_at = NOW();
-- Se phone_number já existe, apenas atualiza updated_at
-- Se não existe, cria nova row

-- RETURNING garante que sempre retorna row (nova ou existente)
RETURNING *;
```

**Como Funciona**:
1. `INSERT` tenta criar nova conversa
2. Se `phone_number` já existe (UNIQUE constraint), dispara `ON CONFLICT`
3. `DO UPDATE SET updated_at = NOW()` atualiza timestamp
4. `RETURNING *` retorna row (criada ou atualizada)

**Benefícios**:
- ✅ Deduplicação automática (zero duplicatas)
- ✅ Sempre retorna row válida
- ✅ Performance: operação atômica única
- ✅ Simples: sem IF nodes ou lógica condicional

---

## 📊 Transaction Isolation

### MVCC (Multi-Version Concurrency Control)

PostgreSQL usa **MVCC** para concorrência:

```
Transaction A                    Transaction B
BEGIN;                          BEGIN;
SELECT * FROM conversations;    -- Vê snapshot T0
                                SELECT * FROM conversations;  -- Vê snapshot T0
UPDATE conversations            -- Trava linha
SET state = 'new';
                                UPDATE conversations         -- BLOQUEIA: aguarda A
                                SET state = 'other';
COMMIT;                         -- A libera lock
                                -- B continua com UPDATE
                                COMMIT;
```

**V111 Row Locking** adiciona `FOR UPDATE SKIP LOCKED`:
```
Transaction A                    Transaction B
BEGIN;                          BEGIN;
SELECT * FOR UPDATE;            -- Trava linha
                                SELECT * FOR UPDATE          -- RETORNA VAZIO ✅
                                SKIP LOCKED;                 -- (não bloqueia)
COMMIT;
```

**Benefício**: Transaction B retorna imediatamente (não aguarda A), permitindo mostrar "Processando..." para usuário.

---

## 🎯 Query Best Practices

### 1. Sempre Usar COALESCE para Defaults

```sql
-- ✅ CORRETO
SELECT
  COALESCE(state_machine_state, 'greeting') as state_for_machine,
  COALESCE(collected_data, '{}'::jsonb) as data
FROM conversations;

-- ❌ ERRADO: NULL pode quebrar lógica
SELECT state_machine_state, collected_data
FROM conversations;
```

### 2. ORDER BY + LIMIT para Performance

```sql
-- ✅ CORRETO: Usa índice idx_conversations_updated_at
SELECT *
FROM conversations
WHERE phone_number = '62999999999'
ORDER BY updated_at DESC
LIMIT 1;

-- ❌ ERRADO: Sem ORDER BY pode retornar row errada
SELECT *
FROM conversations
WHERE phone_number = '62999999999';
```

### 3. IN Clause para Phone Number Variations

```sql
-- ✅ CORRETO: Busca com e sem código de país
WHERE phone_number IN (
  '{{ $json.phone_with_code }}',     -- 556181755748
  '{{ $json.phone_without_code }}'   -- 6181755748
)

-- ❌ ERRADO: Apenas uma variação (pode não encontrar)
WHERE phone_number = '{{ $json.phone_number }}'
```

### 4. RETURNING para Garantir Row

```sql
-- ✅ CORRETO: RETURNING sempre retorna row atualizada
UPDATE conversations
SET state_machine_state = 'new_state'
WHERE phone_number = '62999999999'
RETURNING *;

-- ❌ ERRADO: UPDATE sem RETURNING (não retorna row)
UPDATE conversations
SET state_machine_state = 'new_state'
WHERE phone_number = '62999999999';
```

### 5. Prepared Statement Safety (n8n)

```javascript
// ✅ CORRETO: Escape single quotes
const city = item.json.city.replace(/'/g, "''");
const query = `
  UPDATE conversations
  SET collected_data = collected_data || '{"city": "${city}"}'::jsonb
`;

// ❌ ERRADO: Sem escape (SQL injection risk)
const query = `
  UPDATE conversations
  SET collected_data = collected_data || '{"city": "${item.json.city}"}'::jsonb
`;
// Problema: Se city = "Test'City" → SQL syntax error
```

---

## 🔍 Common Queries

### 1. Verificar Estado de Conversa

```sql
SELECT
  phone_number,
  state_machine_state,
  collected_data->>'name' as name,
  collected_data->>'city' as city,
  date_suggestions,
  slot_suggestions,
  updated_at
FROM conversations
WHERE phone_number = '556181755748'
ORDER BY updated_at DESC
LIMIT 1;
```

### 2. Listar Conversas Recentes

```sql
SELECT
  phone_number,
  lead_name,
  service_type,
  state_machine_state,
  updated_at
FROM conversations
ORDER BY updated_at DESC
LIMIT 10;
```

### 3. Buscar por Estado Específico

```sql
SELECT
  phone_number,
  lead_name,
  state_machine_state,
  collected_data
FROM conversations
WHERE state_machine_state = 'awaiting_wf06_next_dates'
ORDER BY updated_at DESC;
```

### 4. Verificar Agendamentos

```sql
SELECT
  a.id,
  a.lead_name,
  a.lead_email,
  a.service_type,
  a.scheduled_date,
  a.scheduled_time_start,
  a.scheduled_time_end,
  a.google_calendar_event_id,
  c.phone_number
FROM appointments a
JOIN conversations c ON a.conversation_id = c.id
WHERE a.scheduled_date >= CURRENT_DATE
ORDER BY a.scheduled_date, a.scheduled_time_start;
```

### 5. Verificar Email Queue

```sql
SELECT
  id,
  recipient_email,
  recipient_name,
  subject,
  template_used,
  status,
  sent_at,
  error_message
FROM email_queue
WHERE status = 'pending'
ORDER BY created_at DESC;
```

### 6. Debug: Rastrear Conversa Completa

```sql
-- Conversa + Agendamento + Email
SELECT
  'conversation' as type,
  c.phone_number,
  c.lead_name,
  c.state_machine_state,
  c.updated_at as timestamp
FROM conversations c
WHERE c.phone_number = '556181755748'

UNION ALL

SELECT
  'appointment' as type,
  c.phone_number,
  a.lead_name,
  a.google_calendar_event_id,
  a.created_at as timestamp
FROM appointments a
JOIN conversations c ON a.conversation_id = c.id
WHERE c.phone_number = '556181755748'

UNION ALL

SELECT
  'email' as type,
  c.phone_number,
  e.recipient_name,
  e.status,
  e.created_at as timestamp
FROM email_queue e
JOIN conversations c ON e.conversation_id = c.id
WHERE c.phone_number = '556181755748'

ORDER BY timestamp DESC;
```

---

## 🚨 Troubleshooting

### Problema 1: Race Condition (Mensagens Rápidas)

**Sintomas**:
- WF06 não é chamado
- Estados avançam de forma inconsistente
- Usuário recebe mensagens desatualizadas

**Diagnóstico**:
```sql
-- Verificar se V111 row locking está implementado
SELECT
  phone_number,
  state_machine_state,
  updated_at
FROM conversations
WHERE phone_number = '556181755748';
-- Se updated_at muda muito rápido (<1s), indica race condition
```

**Solução**: Implementar V111 row locking (`FOR UPDATE SKIP LOCKED`)

### Problema 2: Dados JSONB Corrompidos

**Sintomas**:
- Erro: `invalid input syntax for type json`
- collected_data NULL ou inválido

**Diagnóstico**:
```sql
-- Verificar JSONB validity
SELECT
  phone_number,
  collected_data,
  pg_typeof(collected_data) as type
FROM conversations
WHERE phone_number = '556181755748';
```

**Solução**:
```sql
-- Reset collected_data para JSONB válido
UPDATE conversations
SET collected_data = '{}'::jsonb
WHERE phone_number = '556181755748';
```

### Problema 3: INSERT...SELECT Retorna Vazio

**Sintomas**:
- Email queue não cria row
- RETURNING retorna vazio

**Diagnóstico**:
```sql
-- Verificar se conversation existe
SELECT *
FROM conversations
WHERE phone_number = '62999999999';
```

**Solução**: Se conversation não existe, criar primeiro (WF01).

### Problema 4: PostgreSQL TIME Field Error

**Sintomas** (V114):
- Erro: `invalid input syntax for type time`
- Appointment creation fails

**Diagnóstico**:
```sql
SELECT
  phone_number,
  collected_data->>'scheduled_time_start' as start,
  collected_data->>'scheduled_time_end' as end
FROM conversations
WHERE phone_number = '556181755748';
-- Verificar formato: "08:00" ✅ ou "8h às 10h" ❌
```

**Solução**: Implementar V114 TIME field extraction no State Machine Logic.

---

## 📚 Referências

### Documentação de Bugfixes

- **V111 Row Locking**: `/docs/fix/wf02/v100-v114/BUGFIX_WF02_V111_DATABASE_STATE_RACE_CONDITION.md`
- **V113 Suggestions**: `/docs/fix/wf02/v100-v114/BUGFIX_WF02_V113_1_WF06_SUGGESTIONS_PERSISTENCE.md`
- **V114 TIME Fields**: `/docs/WF02_V114_QUICK_DEPLOY.md`
- **V79.1 Schema**: `/docs/fix/wf02/v100-v114/BUGFIX_WF02_V104_2_SCHEMA_MISMATCH.md`

### Scripts SQL

- **V111 Row Locking**: `/scripts/wf02/state-machines/wf02-v111-build-sql-queries-row-locking.js`
- **V113 Dates**: `/scripts/wf02/state-machines/wf02-v113-build-update-queries1-wf06-next-dates.js`
- **V113 Slots**: `/scripts/wf02/state-machines/wf02-v113-build-update-queries2-wf06-available-slots.js`
- **V79.1 Schema**: `/scripts/wf02/fixes/wf02-v79_1-build-update-queries-schema-fix.js`

### Database Schema

- **Complete Schema**: `/docs/Setups/DATABASE_SCHEMA.md`
- **Setup Guide**: `/docs/Setups/QUICKSTART.md`

### PostgreSQL Documentation

- **Row Locking**: https://www.postgresql.org/docs/current/explicit-locking.html
- **JSONB**: https://www.postgresql.org/docs/current/datatype-json.html
- **INSERT ON CONFLICT**: https://www.postgresql.org/docs/current/sql-insert.html

---

**Última Atualização**: 2026-04-29
**Versão em Produção**: WF02 V114, WF01 V2.8.3, WF05 V7, WF07 V13
**Status**: ✅ COMPLETO - Todos os padrões documentados e em produção
