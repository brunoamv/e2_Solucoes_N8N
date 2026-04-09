# Deploy do Schema PostgreSQL - E2 Bot

> **Versão**: 2.0 | **Atualização**: 2026-04-08
> **Objetivo**: Deploy do schema completo do E2 Bot com todas as tabelas n8n

---

## 📋 Visão Geral

Este documento cobre o deploy do schema PostgreSQL para os workflows n8n do E2 Bot.

**O que será deployado**:
- ✅ 7 tabelas: conversations, messages, leads, appointments, rdstation_sync_log, chat_memory, email_logs
- ✅ Índices de performance para queries otimizadas
- ✅ Triggers de atualização automática de timestamps
- ✅ Funções de utilidade para workflows
- ✅ Extensão UUID para IDs únicos

**Tempo Estimado**: 5 minutos

---

## 🚨 Pré-requisitos

**Infraestrutura rodando**:
```bash
# Verificar containers
docker ps | grep -E "e2bot-postgres-dev|e2bot-n8n-dev"

# Resultado esperado:
# e2bot-postgres-dev   Up
# e2bot-n8n-dev        Up
```

Se os containers NÃO estiverem rodando:
```bash
cd docker
docker-compose -f docker-compose-dev.yml up -d e2bot-postgres-dev e2bot-n8n-dev
sleep 30  # Aguardar inicialização
```

---

## 🎯 Opção A: Deploy Automático via Docker (Recomendado)

**O schema JÁ FOI DEPLOYADO automaticamente** se você iniciou os containers via docker-compose!

### Como funciona?

O `docker-compose-dev.yml` está configurado para executar automaticamente na primeira inicialização:

```yaml
postgres-dev:
  volumes:
    # Script 1: Cria database e2bot_dev
    - ../database/init-e2bot-dev.sh:/docker-entrypoint-initdb.d/00_init_database.sh:ro

    # Script 2: Aplica schema completo (7 tabelas + índices + triggers)
    - ../database/schema.sql:/docker-entrypoint-initdb.d/01_schema.sql:ro

    # Script 3: Funções de appointment
    - ../database/appointment_functions.sql:/docker-entrypoint-initdb.d/02_appointment_functions.sql:ro
```

**Arquivos executados automaticamente**:
1. `database/init-e2bot-dev.sh` - Cria database `e2bot_dev`
2. `database/schema.sql` - Cria 7 tabelas + índices + triggers
3. `database/appointment_functions.sql` - Funções de agendamento

### Verificar se o deploy foi feito

```bash
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "\dt"
```

**✅ Resultado esperado**: Lista de 7 tabelas
```
                  List of relations
 Schema |         Name         | Type  |  Owner
--------+----------------------+-------+----------
 public | appointments         | table | postgres
 public | chat_memory          | table | postgres
 public | conversations        | table | postgres
 public | email_logs           | table | postgres
 public | leads                | table | postgres
 public | messages             | table | postgres
 public | rdstation_sync_log   | table | postgres
(7 rows)
```

**❌ Se as tabelas NÃO aparecerem**, vá para **Opção B: Deploy Manual**

---

## 🔧 Opção B: Deploy Manual (Se Automático Falhou)

### Passo 1: Verificar se database existe

```bash
docker exec e2bot-postgres-dev psql -U postgres -c "\l" | grep e2bot_dev
```

**Se não existir**, criar manualmente:
```bash
docker exec e2bot-postgres-dev psql -U postgres -c "CREATE DATABASE e2bot_dev OWNER postgres;"
```

### Passo 2: Executar Schema SQL

```bash
# Copiar schema.sql para container
docker cp database/schema.sql e2bot-postgres-dev:/tmp/schema.sql

# Executar SQL
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -f /tmp/schema.sql

# Verificar resultado
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "\dt"
```

**✅ Deve mostrar 7 tabelas**

### Passo 3: Executar Funções de Appointment (Opcional)

```bash
# Copiar arquivo
docker cp database/appointment_functions.sql e2bot-postgres-dev:/tmp/appointment_functions.sql

# Executar SQL
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -f /tmp/appointment_functions.sql
```

---

## 📊 Validação Completa do Deploy

### Checklist de Tabelas

Executar teste para cada tabela:

```bash
# Script de validação completo
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev <<-EOSQL
    -- Teste 1: Verificar 7 tabelas
    SELECT
        table_name,
        (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count
    FROM information_schema.tables t
    WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
    ORDER BY table_name;

    -- Teste 2: Verificar índices
    SELECT
        tablename,
        COUNT(indexname) as index_count
    FROM pg_indexes
    WHERE schemaname = 'public'
    GROUP BY tablename
    ORDER BY tablename;

    -- Teste 3: Verificar triggers
    SELECT
        event_object_table as table_name,
        trigger_name
    FROM information_schema.triggers
    WHERE trigger_schema = 'public'
    ORDER BY event_object_table;
EOSQL
```

**✅ Resultado Esperado**:

**Teste 1 - Tabelas**:
```
     table_name      | column_count
---------------------+--------------
 appointments        |           14
 chat_memory         |            3
 conversations       |           14
 email_logs          |           10
 leads               |           28
 messages            |            9
 rdstation_sync_log  |           10
(7 rows)
```

**Teste 2 - Índices** (cada tabela deve ter pelo menos 1 índice):
```
     tablename      | index_count
--------------------+-------------
 appointments       |           5
 chat_memory        |           3
 conversations      |           7
 email_logs         |           5
 leads              |           6
 messages           |           4
 rdstation_sync_log |           3
(7 rows)
```

**Teste 3 - Triggers** (3 triggers UPDATE):
```
   table_name   |           trigger_name
----------------+----------------------------------
 appointments   | update_appointments_updated_at
 conversations  | update_conversations_updated_at
 leads          | update_leads_updated_at
(3 rows)
```

---

## 🧪 Teste de Inserção (Validação Funcional)

### Teste 1: Conversation + Message

```bash
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev <<-EOSQL
    -- Inserir conversation de teste
    INSERT INTO conversations (phone_number, whatsapp_name, service_type, current_state)
    VALUES ('5561999999999', 'Teste User', 'energia_solar', 'novo')
    RETURNING id, phone_number, service_type;

    -- Inserir message de teste
    INSERT INTO messages (conversation_id, direction, content)
    SELECT id, 'inbound', 'Olá, quero informações sobre energia solar'
    FROM conversations WHERE phone_number = '5561999999999'
    RETURNING id, direction, content;

    -- Limpar teste
    DELETE FROM conversations WHERE phone_number = '5561999999999';
EOSQL
```

**✅ Deve retornar**: UUID da conversation + UUID da message, sem erros

### Teste 2: Email Log (WF07)

```bash
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev <<-EOSQL
    -- Inserir email log de teste
    INSERT INTO email_logs (
        recipient_email,
        recipient_name,
        subject,
        template_used,
        status,
        sent_at,
        metadata
    ) VALUES (
        'teste@example.com',
        'Teste User',
        'Confirmação de Agendamento',
        'confirmacao_agendamento',
        'sent',
        NOW(),
        '{"source": "test"}'::jsonb
    )
    RETURNING id, recipient_email, status, sent_at;

    -- Limpar teste
    DELETE FROM email_logs WHERE recipient_email = 'teste@example.com';
EOSQL
```

**✅ Deve retornar**: UUID + email + status + timestamp, sem erros

---

## 📚 Estrutura das Tabelas

### 1. conversations
**Propósito**: Armazena conversas WhatsApp com estado e dados coletados

**Colunas principais**:
- `id` - UUID (primary key)
- `phone_number` - VARCHAR(20) UNIQUE
- `current_state` - Estado da conversa (novo, identificando_servico, etc.)
- `service_type` - Tipo de serviço escolhido
- `collected_data` - JSONB com dados coletados
- `service_id`, `contact_name`, `contact_email`, `city` - Colunas V43 para compatibilidade

**Workflows que usam**: WF01, WF02, WF05

---

### 2. messages
**Propósito**: Histórico completo de mensagens trocadas

**Colunas principais**:
- `id` - UUID
- `conversation_id` - FK para conversations
- `direction` - 'inbound' ou 'outbound'
- `content` - Texto da mensagem
- `message_type` - 'text', 'image', 'document', etc.
- `whatsapp_message_id` - ID único do WhatsApp

**Workflows que usam**: WF01, WF02

---

### 3. leads
**Propósito**: Leads qualificados prontos para atendimento comercial

**Colunas principais**:
- `id` - UUID
- `conversation_id` - FK para conversations
- `name`, `email`, `phone_number` - Dados do lead
- `service_type`, `service_details` - Informações do serviço
- `status` - 'novo', 'em_atendimento', 'agendado', etc.
- `rdstation_contact_id`, `rdstation_deal_id` - IDs CRM

**Workflows que usam**: WF05, WF08 (RD Station)

---

### 4. appointments
**Propósito**: Agendamentos de visitas técnicas

**Colunas principais**:
- `id` - UUID
- `lead_id` - FK para leads
- `conversation_id` - FK para conversations
- `scheduled_date`, `scheduled_time_start`, `scheduled_time_end` - Data/hora
- `google_calendar_event_id` - ID do evento no Google Calendar
- `status` - 'agendado', 'confirmado', 'realizado', etc.
- `reminder_24h_sent`, `reminder_2h_sent` - Controle de lembretes

**Workflows que usam**: WF05 (Appointment Scheduler)

---

### 5. email_logs
**Propósito**: Log de envios de email via WF07

**Colunas principais**:
- `id` - UUID
- `recipient_email`, `recipient_name` - Destinatário
- `subject` - Assunto do email
- `template_used` - Template usado (confirmacao_agendamento, lembrete_24h, etc.)
- `status` - 'pending', 'sent', 'failed', 'bounce'
- `sent_at` - Timestamp de envio
- `metadata` - JSONB com dados adicionais

**Workflows que usam**: WF07 (Send Email)

---

### 6. chat_memory
**Propósito**: Memória de conversação para n8n AI Agent

**Colunas principais**:
- `id` - SERIAL
- `session_id` - ID da sessão (phone_number)
- `message` - JSONB com histórico de mensagens
- `created_at` - Timestamp

**Workflows que usam**: WF02 (AI Agent - opcional)

---

### 7. rdstation_sync_log
**Propósito**: Log de sincronização com RD Station CRM

**Colunas principais**:
- `id` - UUID
- `entity_type`, `entity_id` - Entidade sincronizada
- `rdstation_id` - ID no RD Station
- `operation` - 'create', 'update', 'delete'
- `request_payload`, `response_payload` - JSONB
- `status` - 'pending', 'success', 'failed'

**Workflows que usam**: WF05, WF08 (RD Station Sync)

---

## 🚨 Troubleshooting

### Problema: "database e2bot_dev does not exist"

**Causa**: Database não foi criada automaticamente

**Solução**:
```bash
# Criar database manualmente
docker exec e2bot-postgres-dev psql -U postgres -c "CREATE DATABASE e2bot_dev OWNER postgres;"

# Re-executar schema
docker cp database/schema.sql e2bot-postgres-dev:/tmp/schema.sql
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -f /tmp/schema.sql
```

---

### Problema: "relation 'conversations' already exists"

**Causa**: Tentando executar schema em database que já tem tabelas

**Solução Opção 1 - Verificar tabelas existentes**:
```bash
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "\dt"
```

Se as 7 tabelas já existem, **o deploy está completo**, não precisa fazer nada!

**Solução Opção 2 - Recrear database** (⚠️ APAGA TODOS OS DADOS):
```bash
# Dropar database
docker exec e2bot-postgres-dev psql -U postgres -c "DROP DATABASE e2bot_dev;"

# Criar novamente
docker exec e2bot-postgres-dev psql -U postgres -c "CREATE DATABASE e2bot_dev OWNER postgres;"

# Re-executar schema
docker cp database/schema.sql e2bot-postgres-dev:/tmp/schema.sql
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -f /tmp/schema.sql
```

---

### Problema: "permission denied for relation conversations"

**Causa**: Credencial n8n usando usuário sem permissões

**Solução**: A credencial n8n deve usar:
- **User**: `postgres`
- **Password**: (conforme docker/.env - padrão: `CoraRosa`)
- **Database**: `e2bot_dev`
- **Host**: `e2bot-postgres-dev` (NÃO `localhost`)

---

### Problema: "relation 'email_logs' does not exist"

**Causa**: Schema antigo sem tabela email_logs (adicionada em 2026-04-08)

**Solução**: Executar apenas a criação da tabela email_logs
```bash
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev <<-EOSQL
    CREATE TABLE IF NOT EXISTS email_logs (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        recipient_email VARCHAR(255) NOT NULL,
        recipient_name VARCHAR(255),
        subject VARCHAR(500),
        template_used VARCHAR(100),
        status VARCHAR(20) DEFAULT 'pending',
        sent_at TIMESTAMP WITH TIME ZONE,
        metadata JSONB DEFAULT '{}',
        error_message TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        CONSTRAINT valid_email_status CHECK (status IN ('pending', 'sent', 'failed', 'bounce'))
    );

    CREATE INDEX IF NOT EXISTS idx_email_logs_recipient ON email_logs(recipient_email);
    CREATE INDEX IF NOT EXISTS idx_email_logs_status ON email_logs(status);
    CREATE INDEX IF NOT EXISTS idx_email_logs_template ON email_logs(template_used);
    CREATE INDEX IF NOT EXISTS idx_email_logs_sent_at ON email_logs(sent_at DESC);
EOSQL
```

---

## ✅ Checklist Final de Deploy

Antes de configurar credenciais n8n:

- [ ] Container `e2bot-postgres-dev` rodando (status: Up)
- [ ] Database `e2bot_dev` existe
- [ ] 7 tabelas criadas (conversations, messages, leads, appointments, email_logs, chat_memory, rdstation_sync_log)
- [ ] Índices criados (verificar com `\di` no psql)
- [ ] Triggers criados (3 triggers de UPDATE)
- [ ] Teste de inserção em `conversations` funcionou
- [ ] Teste de inserção em `email_logs` funcionou

**Tudo OK?** 🎉 **Próximo passo**: Configurar credencial PostgreSQL no n8n

---

## 📖 Documentação Relacionada

**Setup**:
- `QUICKSTART.md` - Guia completo de setup do zero
- `SETUP_CREDENTIALS.md` - Configuração de credenciais n8n

**Workflows**:
- `WF02_V76_IMPLEMENTATION_GUIDE.md` - AI Agent conversation
- `WF06_CALENDAR_AVAILABILITY_SERVICE.md` - Calendar availability
- `BUGFIX_WF07_V13_INSERT_SELECT_FIX.md` - Email workflow

**Arquitetura**:
- `ARCHITECTURE.md` - Visão geral do sistema
- `CLAUDE.md` - Contexto completo do projeto

---

**Última Atualização**: 2026-04-08
**Versão**: 2.0 (E2 Bot n8n workflows)
**Mantido por**: E2 Soluções Dev Team
