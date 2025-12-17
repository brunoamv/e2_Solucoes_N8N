# Sprint 1.3 - Cenários de Teste End-to-End

> **Sistema de Notificações Multi-Canal**
> **Data**: 2025-12-15
> **Status**: Documentação completa de testes E2E

---

## 📋 Índice

1. [Cenário 1: Novo Lead Qualificado](#cenário-1-novo-lead-qualificado)
2. [Cenário 2: Agendamento de Visita](#cenário-2-agendamento-de-visita)
3. [Cenário 3: Lembretes Automáticos](#cenário-3-lembretes-automáticos)
4. [Cenário 4: Handoff para Humano](#cenário-4-handoff-para-humano)
5. [Cenário 5: Sincronização RD Station](#cenário-5-sincronização-rd-station)
6. [Cenário 6: Falha e Retry](#cenário-6-falha-e-retry)
7. [Cenário 7: Opt-Out LGPD](#cenário-7-opt-out-lgpd)
8. [Cenário 8: Múltiplos Canais Simultâneos](#cenário-8-múltiplos-canais-simultâneos)

---

## Cenário 1: Novo Lead Qualificado

### 🎯 Objetivo
Validar que um novo lead qualificado via WhatsApp dispara notificações em todos os canais (Email, Discord, WhatsApp para time comercial).

### 📝 Pré-condições
- Sistema iniciado (`./scripts/start-dev.sh`)
- WhatsApp conectado (Evolution API)
- Discord webhooks configurados
- SMTP configurado (opcional)
- n8n workflows importados e ativados

### 🔄 Fluxo de Teste

#### Passo 1: Iniciar Conversa no WhatsApp
```
Usuário: Olá
Bot: Olá! Sou assistente virtual E2 Soluções...
```

#### Passo 2: Qualificar Lead
```
Usuário: Quero orçamento de energia solar
Bot: Ótimo! Para preparar orçamento, preciso alguns dados...

[Bot coleta: Nome, Endereço, Consumo kWh]

Usuário: João Silva
Usuário: Rua Teste 123, Goiânia-GO
Usuário: 500 kWh
```

#### Passo 3: Agendamento Aceito
```
Bot: Gostaria de agendar visita técnica?
Usuário: Sim
Bot: Disponibilidade: [lista datas/horários]
Usuário: Quinta 10h
Bot: ✅ Visita agendada para quinta 10h
```

#### Passo 4: Validar Banco de Dados
```sql
-- Verificar lead criado
SELECT id, name, phone, service_type, status
FROM leads
WHERE phone = '+5562999999999';

-- Verificar agendamento
SELECT id, scheduled_at, status
FROM appointments
WHERE lead_id = (SELECT id FROM leads WHERE phone = '+5562999999999');

-- Verificar notificações criadas
SELECT id, channel, notification_type, status, subject
FROM notifications
WHERE lead_id = (SELECT id FROM leads WHERE phone = '+5562999999999')
ORDER BY created_at DESC;
```

**Resultado Esperado**:
- ✅ 1 lead criado com status `qualified`
- ✅ 1 appointment criado com status `scheduled`
- ✅ 4+ notificações criadas:
  - `new_lead` (email/discord/whatsapp)
  - `appointment_confirmation` (email/whatsapp)

#### Passo 5: Validar Notificações Enviadas

**5.1 Discord (#leads)**:
- Acesse canal `#leads` no Discord
- Verifique mensagem com:
  - Título: "🎯 Novo Lead Qualificado"
  - Nome: João Silva
  - Telefone: +55 62 99999-9999
  - Serviço: Energia Solar

**5.2 Discord (#agendamentos)**:
- Acesse canal `#agendamentos`
- Verifique mensagem com:
  - Título: "📅 Nova Visita Agendada"
  - Data/Hora: Quinta 10h
  - Cliente: João Silva

**5.3 Email (Comercial)**:
```bash
# Verificar logs SMTP (se configurado)
docker logs n8n | grep "Email sent"
```

**5.4 WhatsApp (Cliente)**:
- Verificar mensagem de confirmação no WhatsApp do cliente

#### Passo 6: Validar Execuções n8n

Acesse n8n: `http://localhost:5678`

**Workflows que devem ter executado**:
1. **Workflow 01** - Main WhatsApp Handler (múltiplas execuções)
2. **Workflow 02** - AI Agent Conversation (múltiplas)
3. **Workflow 05** - Appointment Scheduler (1 execução)
4. **Workflow 11** - Notification Processor (polling, ~3-5 execuções)
5. **Workflow 12** - Multi-Channel Notifications (1 execução)
6. **Workflow 13** - Discord Notifications (2 execuções)

**Como validar**:
- Clique em cada workflow → "Executions"
- Verifique status: ✅ Success (verde)
- Se houver erros vermelhos: clique para ver detalhes

### ✅ Critérios de Aceitação

- [ ] Lead criado no PostgreSQL com dados corretos
- [ ] Appointment criado e linkado ao lead
- [ ] Notificações criadas na tabela `notifications`
- [ ] Mensagem recebida no Discord (#leads)
- [ ] Mensagem recebida no Discord (#agendamentos)
- [ ] Email enviado para time comercial (se SMTP configurado)
- [ ] Mensagem de confirmação enviada para cliente WhatsApp
- [ ] Todos os workflows n8n executaram com sucesso
- [ ] Nenhum erro nos logs Docker

### 🐛 Troubleshooting

**Problema**: Notificações criadas mas não enviadas (status `pending`)

**Causa**: Workflow 11 (Notification Processor) não está executando

**Solução**:
```bash
# 1. Verificar se workflow está ativo
# n8n UI → Workflow 11 → Settings → Active: ON

# 2. Forçar execução manual
# n8n UI → Workflow 11 → Execute Workflow

# 3. Verificar logs
docker logs n8n | grep "Notification Processor"
```

---

**Problema**: Discord não recebeu mensagem

**Causa**: Webhook URL incorreta ou canal deletado

**Solução**:
```bash
# 1. Testar webhook manualmente
curl -X POST "$DISCORD_WEBHOOK_LEADS" \
  -H "Content-Type: application/json" \
  -d '{"content": "Teste manual"}'

# 2. Se retornar 404: Recriar webhook
# Discord → Server Settings → Integrations → Webhooks → Create New

# 3. Atualizar .env com nova URL
nano docker/.env
# DISCORD_WEBHOOK_LEADS=nova_url_aqui

# 4. Reiniciar n8n
docker restart n8n
```

---

**Problema**: WhatsApp desconectado

**Solução**:
```bash
# 1. Verificar status
curl "$EVOLUTION_API_URL/instance/connectionState/e2-solucoes-bot" \
  -H "apikey: $EVOLUTION_API_KEY"

# 2. Se "close": Gerar novo QR Code
curl "$EVOLUTION_API_URL/instance/connect/e2-solucoes-bot" \
  -H "apikey: $EVOLUTION_API_KEY"

# 3. Escanear QR Code com WhatsApp no celular
```

---

## Cenário 2: Agendamento de Visita

### 🎯 Objetivo
Validar agendamento de visita técnica com sincronização Google Calendar e criação automática de lembretes (24h e 2h antes).

### 📝 Pré-condições
- Lead já existe no sistema
- Google Calendar integrado
- Calendário com disponibilidade

### 🔄 Fluxo de Teste

#### Passo 1: Solicitar Agendamento via SQL
```sql
-- Criar agendamento via função SQL
SELECT schedule_appointment_notification(
    (SELECT id FROM leads WHERE phone = '+5562999999999' LIMIT 1),
    'technical_visit',
    '2025-12-20 10:00:00-03'::timestamptz,
    'Rua Teste 123, Goiânia-GO',
    jsonb_build_object(
        'lead_name', 'João Silva',
        'phone', '+5562999999999',
        'service_name', 'Energia Solar'
    )
);
```

#### Passo 2: Validar Banco de Dados
```sql
-- Verificar appointment criado
SELECT id, scheduled_at, type, status, google_event_id
FROM appointments
WHERE lead_id = (SELECT id FROM leads WHERE phone = '+5562999999999')
ORDER BY created_at DESC
LIMIT 1;

-- Verificar lembretes automáticos criados
SELECT id, notification_type, scheduled_for, status
FROM notifications
WHERE appointment_id = (
    SELECT id FROM appointments
    WHERE lead_id = (SELECT id FROM leads WHERE phone = '+5562999999999')
    ORDER BY created_at DESC
    LIMIT 1
)
ORDER BY scheduled_for ASC;
```

**Resultado Esperado**:
- ✅ 1 appointment com status `scheduled`
- ✅ 2 notificações de lembrete:
  - `reminder_24h`: scheduled_for = 24h antes da visita
  - `reminder_2h`: scheduled_for = 2h antes da visita

#### Passo 3: Validar Google Calendar

**Opção A: Via API**
```bash
# Listar eventos do calendário
curl "https://www.googleapis.com/calendar/v3/calendars/$GOOGLE_CALENDAR_ID/events" \
  -H "Authorization: Bearer $GOOGLE_ACCESS_TOKEN"
```

**Opção B: Via Interface Web**
- Acesse Google Calendar: https://calendar.google.com
- Verifique evento criado com:
  - Título: "Visita Técnica - João Silva"
  - Data/Hora: 2025-12-20 10:00
  - Local: Rua Teste 123, Goiânia-GO

#### Passo 4: Validar Notificação de Confirmação

**Discord (#agendamentos)**:
- Verifique mensagem com:
  - Título: "📅 Nova Visita Agendada"
  - Cliente: João Silva
  - Data: 20/12/2025 10:00
  - Endereço: Rua Teste 123

**WhatsApp (Cliente)**:
- Mensagem de confirmação enviada
- Template: `confirmacao_agendamento.txt`

#### Passo 5: Aguardar Lembretes Automáticos

**Lembrete 24h antes**:
- Aguardar até 19/12/2025 10:00
- Workflow 06 executa automaticamente
- Cliente recebe WhatsApp/Email com lembrete

**Lembrete 2h antes**:
- Aguardar até 20/12/2025 08:00
- Workflow 06 executa automaticamente
- Cliente recebe WhatsApp/Email final

**Como simular (não aguardar 24h)**:
```sql
-- Alterar scheduled_for dos lembretes para NOW() + 2 minutos
UPDATE notifications
SET scheduled_for = NOW() + INTERVAL '2 minutes'
WHERE appointment_id = (
    SELECT id FROM appointments WHERE lead_id = (
        SELECT id FROM leads WHERE phone = '+5562999999999'
    )
    ORDER BY created_at DESC LIMIT 1
)
AND notification_type IN ('reminder_24h', 'reminder_2h');

-- Aguardar 2 minutos
-- Workflow 06 vai processar automaticamente
```

### ✅ Critérios de Aceitação

- [ ] Appointment criado com `google_event_id` preenchido
- [ ] Evento criado no Google Calendar
- [ ] 2 notificações de lembrete criadas (24h + 2h)
- [ ] Notificação de confirmação enviada imediatamente
- [ ] Lembrete 24h enviado no horário correto
- [ ] Lembrete 2h enviado no horário correto
- [ ] Status dos lembretes: `pending` → `sent`
- [ ] Workflows 05 e 06 executaram com sucesso

---

## Cenário 3: Lembretes Automáticos

### 🎯 Objetivo
Validar que lembretes de visita são enviados automaticamente 24h e 2h antes do agendamento.

### 📝 Pré-condições
- Appointment já agendado (Cenário 2)
- Workflow 06 ativado com polling 5min

### 🔄 Fluxo de Teste

#### Passo 1: Verificar Lembretes Pendentes
```sql
-- Listar lembretes que serão enviados nas próximas 24h
SELECT
    n.id,
    n.notification_type,
    n.scheduled_for,
    n.status,
    l.name AS lead_name,
    a.scheduled_at AS appointment_time
FROM notifications n
JOIN appointments a ON n.appointment_id = a.id
JOIN leads l ON n.lead_id = l.id
WHERE n.notification_type IN ('reminder_24h', 'reminder_2h')
AND n.status = 'pending'
AND n.scheduled_for BETWEEN NOW() AND NOW() + INTERVAL '25 hours'
ORDER BY n.scheduled_for ASC;
```

#### Passo 2: Simular Lembrete 24h (Teste Rápido)
```sql
-- Alterar scheduled_for para NOW() + 1 minuto
UPDATE notifications
SET scheduled_for = NOW() + INTERVAL '1 minute'
WHERE notification_type = 'reminder_24h'
AND status = 'pending'
AND appointment_id = (
    SELECT id FROM appointments
    WHERE lead_id = (SELECT id FROM leads WHERE phone = '+5562999999999')
    ORDER BY created_at DESC LIMIT 1
);
```

#### Passo 3: Aguardar Execução Workflow 06
```bash
# Monitorar logs n8n em tempo real
docker logs -f n8n | grep "Appointment Reminders"

# Aguardar ~5 minutos (intervalo de polling)
# Deve aparecer: "Processing reminder_24h for appointment_id: xxx"
```

#### Passo 4: Validar Envio
```sql
-- Verificar status atualizado
SELECT id, notification_type, status, sent_at, error_message
FROM notifications
WHERE notification_type = 'reminder_24h'
AND appointment_id = (
    SELECT id FROM appointments
    WHERE lead_id = (SELECT id FROM leads WHERE phone = '+5562999999999')
    ORDER BY created_at DESC LIMIT 1
);
```

**Resultado Esperado**:
- ✅ `status = 'sent'`
- ✅ `sent_at` preenchido
- ✅ `error_message = NULL`

#### Passo 5: Validar Mensagem Recebida

**WhatsApp**:
- Cliente recebe mensagem usando template `lembrete_24h.txt`
- Conteúdo: "Olá {{CUSTOMER_NAME}}, lembramos que sua visita técnica está agendada para amanhã..."

**Email**:
- Cliente recebe email usando template `lembrete_24h.html`
- Subject: "Lembrete: Visita Técnica Amanhã - E2 Soluções"

#### Passo 6: Repetir para Lembrete 2h
```sql
-- Alterar scheduled_for do lembrete 2h
UPDATE notifications
SET scheduled_for = NOW() + INTERVAL '1 minute'
WHERE notification_type = 'reminder_2h'
AND status = 'pending'
AND appointment_id = (
    SELECT id FROM appointments
    WHERE lead_id = (SELECT id FROM leads WHERE phone = '+5562999999999')
    ORDER BY created_at DESC LIMIT 1
);

-- Aguardar 5 minutos
-- Validar status = 'sent'
```

### ✅ Critérios de Aceitação

- [ ] Workflow 06 executa a cada 5 minutos (verificar executions)
- [ ] Lembrete 24h enviado no horário correto
- [ ] Lembrete 2h enviado no horário correto
- [ ] Ambos os lembretes marcados como `sent`
- [ ] Mensagens recebidas no WhatsApp e Email
- [ ] Sem erros nos logs do Workflow 06

---

## Cenário 4: Handoff para Humano

### 🎯 Objetivo
Validar transferência de conversa para atendente humano com notificação em Discord (#alertas).

### 📝 Pré-condições
- Conversa ativa no WhatsApp
- Discord webhook #alertas configurado

### 🔄 Fluxo de Teste

#### Passo 1: Solicitar Atendimento Humano
```
Usuário: Quero falar com atendente
Bot: Entendi. Vou transferir você para nosso time comercial...
```

#### Passo 2: Validar Banco de Dados
```sql
-- Verificar conversa com status handoff
SELECT id, current_state, last_human_handoff_at
FROM conversations
WHERE phone = '+5562999999999';

-- Verificar notificação de handoff criada
SELECT id, notification_type, channel, status, subject, body
FROM notifications
WHERE lead_id = (SELECT id FROM leads WHERE phone = '+5562999999999')
AND notification_type = 'handoff_to_human'
ORDER BY created_at DESC
LIMIT 1;
```

**Resultado Esperado**:
- ✅ `current_state = 'handoff_comercial'`
- ✅ `last_human_handoff_at` preenchido
- ✅ 1 notificação `handoff_to_human` criada

#### Passo 3: Validar Discord (#alertas)

Verificar mensagem no canal `#alertas`:
```
🚨 HANDOFF: Atendimento Humano Necessário

👤 Cliente: João Silva
📞 Telefone: +55 62 99999-9999
💼 Serviço: Energia Solar
💬 Mensagem: "Quero falar com atendente"

🔗 Abrir WhatsApp: https://wa.me/5562999999999
```

#### Passo 4: Validar Workflow 10

Acesse n8n: `http://localhost:5678`
- Workflow 10 - Handoff to Human
- Última execução: ✅ Success
- Verifique nós executados:
  - PostgreSQL: Create notification
  - Discord: Send webhook
  - WhatsApp: Send handoff message

### ✅ Critérios de Aceitação

- [ ] Conversa marcada como `handoff_comercial`
- [ ] `last_human_handoff_at` registrado
- [ ] Notificação criada e enviada
- [ ] Alerta recebido no Discord (#alertas)
- [ ] Workflow 10 executou com sucesso
- [ ] Cliente recebe mensagem de confirmação

---

## Cenário 5: Sincronização RD Station

### 🎯 Objetivo
Validar sincronização bidirecional com RD Station CRM (contacts + deals).

### 📝 Pré-condições
- RD Station credentials configuradas
- Workflow 08 (RD Station Sync) ativado
- Workflow 09 (RD Station Webhook Handler) ativado

### 🔄 Fluxo de Teste

#### Passo 1: Criar Lead no Sistema
```sql
-- Inserir lead sem rdstation_contact_id
INSERT INTO leads (
    phone, name, email, address, city, state,
    service_type, status, notification_preferences
) VALUES (
    '+5562988887777',
    'Maria Santos',
    'maria.santos@exemplo.com',
    'Av Central 456',
    'Goiânia',
    'GO',
    'subestacao',
    'new',
    jsonb_build_object('email', true, 'whatsapp', true, 'discord', false)
);
```

#### Passo 2: Aguardar Sincronização (Workflow 08)

Workflow 08 executa a cada 15 minutos automaticamente.

**Como forçar execução imediata**:
- n8n UI → Workflow 08 → Execute Workflow

**Validar execução**:
```sql
-- Verificar que rdstation_contact_id foi preenchido
SELECT id, name, rdstation_contact_id, rdstation_deal_id
FROM leads
WHERE phone = '+5562988887777';

-- Verificar log de sincronização
SELECT operation, status, response_data, error_message
FROM rdstation_sync_log
WHERE lead_phone = '+5562988887777'
ORDER BY created_at DESC;
```

**Resultado Esperado**:
- ✅ `rdstation_contact_id` preenchido (UUID RD Station)
- ✅ `rdstation_deal_id` preenchido
- ✅ Log sync: `operation = 'create_contact'`, `status = 'success'`

#### Passo 3: Validar no RD Station CRM

**Via Interface Web**:
1. Acesse: https://crm.rdstation.com
2. Menu: Contatos → Buscar "Maria Santos"
3. Verificar:
   - Nome: Maria Santos
   - Email: maria.santos@exemplo.com
   - Telefone: +55 62 98888-7777
   - Tags: lead_bot, energia_solar

**Via API**:
```bash
# Obter token de acesso
ACCESS_TOKEN=$(curl -X POST "https://api.rd.services/auth/token" \
  -H "Content-Type: application/json" \
  -d "{
    \"client_id\": \"$RDSTATION_CLIENT_ID\",
    \"client_secret\": \"$RDSTATION_CLIENT_SECRET\",
    \"refresh_token\": \"$RDSTATION_REFRESH_TOKEN\"
  }" | jq -r '.access_token')

# Buscar contato
CONTACT_ID=$(psql $DATABASE_URL -t -c "
SELECT rdstation_contact_id FROM leads WHERE phone = '+5562988887777';
" | xargs)

curl "https://api.rd.services/platform/contacts/$CONTACT_ID" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq .
```

#### Passo 4: Atualizar no RD Station → Sincronizar para Bot

**No RD Station CRM**:
1. Editar contato "Maria Santos"
2. Alterar campo customizado: `status_bot = 'qualified'`
3. Salvar alterações

**Webhook Automático** (Workflow 09):
- RD Station dispara webhook para n8n
- Workflow 09 recebe e atualiza PostgreSQL

**Validar sincronização reversa**:
```sql
SELECT id, name, status, updated_at
FROM leads
WHERE phone = '+5562988887777';

-- Verificar log
SELECT operation, status, webhook_payload
FROM rdstation_sync_log
WHERE lead_phone = '+5562988887777'
AND operation = 'webhook_received'
ORDER BY created_at DESC
LIMIT 1;
```

**Resultado Esperado**:
- ✅ `status` atualizado para valor do RD Station
- ✅ `updated_at` modificado
- ✅ Log: `operation = 'webhook_received'`, `status = 'success'`

### ✅ Critérios de Aceitação

- [ ] Lead criado no bot → Contact criado no RD Station
- [ ] `rdstation_contact_id` preenchido automaticamente
- [ ] Deal criado automaticamente no RD Station
- [ ] Alteração no RD Station → Atualização no bot via webhook
- [ ] Logs de sincronização sem erros
- [ ] Workflows 08 e 09 executaram com sucesso

---

## Cenário 6: Falha e Retry

### 🎯 Objetivo
Validar mecanismo de retry automático para notificações falhadas.

### 📝 Pré-condições
- Sistema funcionando normalmente
- Capacidade de simular falhas

### 🔄 Fluxo de Teste

#### Passo 1: Simular Falha no Discord

**Desativar temporariamente webhook**:
```bash
# Salvar webhook original
ORIGINAL_WEBHOOK=$DISCORD_WEBHOOK_LEADS

# Substituir por URL inválida
export DISCORD_WEBHOOK_LEADS="https://discord.com/api/webhooks/INVALID_URL"

# Reiniciar n8n para aplicar
docker restart n8n
```

#### Passo 2: Criar Notificação (vai falhar)
```sql
SELECT create_notification(
    (SELECT id FROM leads WHERE phone = '+5562999999999' LIMIT 1),
    NULL,
    'discord',
    'test',
    '',
    'Teste de Falha',
    'Esta notificação deve falhar no primeiro envio',
    json_build_object('lead_name', 'João Silva')::jsonb,
    3, -- max_retries = 3
    NOW()
);
```

#### Passo 3: Aguardar Falha
```bash
# Monitorar logs
docker logs -f n8n | grep "Notification failed"

# Aguardar Workflow 11 tentar enviar (~1 minuto)
```

#### Passo 4: Validar Falha Registrada
```sql
-- Verificar status failed
SELECT id, status, retry_count, max_retries, error_message, last_retry_at
FROM notifications
WHERE subject = 'Teste de Falha'
ORDER BY created_at DESC
LIMIT 1;
```

**Resultado Esperado**:
- ✅ `status = 'failed'`
- ✅ `retry_count = 1` (primeira tentativa)
- ✅ `max_retries = 3`
- ✅ `error_message` contém detalhes do erro
- ✅ `last_retry_at` preenchido

#### Passo 5: Restaurar Webhook (permitir retry)
```bash
# Restaurar webhook válido
export DISCORD_WEBHOOK_LEADS=$ORIGINAL_WEBHOOK

# Atualizar .env permanentemente
sed -i "s|DISCORD_WEBHOOK_LEADS=.*|DISCORD_WEBHOOK_LEADS=$ORIGINAL_WEBHOOK|" docker/.env

# Reiniciar n8n
docker restart n8n
```

#### Passo 6: Aguardar Retry Automático

Workflow 11 consulta notificações falhadas a cada 1 minuto e tenta reenviar.

```sql
-- Monitorar status da notificação
SELECT id, status, retry_count, last_retry_at, sent_at
FROM notifications
WHERE subject = 'Teste de Falha'
ORDER BY created_at DESC
LIMIT 1;
```

**Progressão Esperada**:
```
Tentativa 1 (t=0s):   status=failed, retry_count=1
Tentativa 2 (t=60s):  status=failed, retry_count=2 (se falhar novamente)
Tentativa 3 (t=120s): status=sent, retry_count=2 (sucesso após correção)
```

#### Passo 7: Validar Sucesso após Retry
```sql
-- Verificar status final
SELECT id, status, retry_count, sent_at, error_message
FROM notifications
WHERE subject = 'Teste de Falha';
```

**Resultado Esperado**:
- ✅ `status = 'sent'`
- ✅ `sent_at` preenchido
- ✅ `error_message = NULL`
- ✅ Mensagem recebida no Discord

### ✅ Critérios de Aceitação

- [ ] Primeira tentativa falha e registra erro
- [ ] `retry_count` incrementado corretamente
- [ ] Sistema tenta reenviar automaticamente
- [ ] Após correção, notificação é enviada com sucesso
- [ ] Status final: `failed` → `sent`
- [ ] `max_retries` respeitado (não excede 3 tentativas)

---

## Cenário 7: Opt-Out LGPD

### 🎯 Objetivo
Validar conformidade LGPD com respeito às preferências de notificação do lead.

### 📝 Pré-condições
- Lead existente no sistema
- Função `check_notification_allowed()` implementada

### 🔄 Fluxo de Teste

#### Passo 1: Configurar Opt-Out de Email
```sql
-- Atualizar preferências: opt-out de email, aceita WhatsApp
UPDATE leads
SET notification_preferences = jsonb_build_object(
    'email', false,
    'whatsapp', true,
    'discord', false
)
WHERE phone = '+5562999999999';
```

#### Passo 2: Tentar Enviar Email (deve falhar)
```sql
-- Tentar criar notificação por email
SELECT create_notification(
    (SELECT id FROM leads WHERE phone = '+5562999999999' LIMIT 1),
    NULL,
    'email',
    'test',
    'test_template',
    'Teste Opt-Out Email',
    'Este email NÃO deve ser enviado',
    '{}'::jsonb,
    3,
    NOW()
);
```

**Resultado Esperado**:
- ❌ Função retorna `NULL` (notificação não criada)
- ❌ Nenhum registro criado na tabela `notifications`

**Validar**:
```sql
SELECT COUNT(*) as count_must_be_zero
FROM notifications
WHERE lead_id = (SELECT id FROM leads WHERE phone = '+5562999999999')
AND channel = 'email'
AND subject = 'Teste Opt-Out Email';
-- Deve retornar: count_must_be_zero = 0
```

#### Passo 3: Enviar WhatsApp (deve funcionar)
```sql
-- Criar notificação por WhatsApp (permitido)
SELECT create_notification(
    (SELECT id FROM leads WHERE phone = '+5562999999999' LIMIT 1),
    NULL,
    'whatsapp',
    'test',
    'test_template',
    'Teste Opt-In WhatsApp',
    'Este WhatsApp DEVE ser enviado',
    '{}'::jsonb,
    3,
    NOW()
);
```

**Resultado Esperado**:
- ✅ Função retorna UUID da notificação
- ✅ Registro criado na tabela `notifications`
- ✅ `status = 'pending'`

**Validar**:
```sql
SELECT id, channel, status, subject
FROM notifications
WHERE lead_id = (SELECT id FROM leads WHERE phone = '+5562999999999')
AND channel = 'whatsapp'
AND subject = 'Teste Opt-In WhatsApp';
-- Deve retornar 1 registro com status 'pending'
```

#### Passo 4: Validar Logs de Bloqueio

```sql
-- Verificar se há registros de tentativas bloqueadas
-- (se implementado sistema de audit log)
SELECT *
FROM notification_audit_log
WHERE lead_id = (SELECT id FROM leads WHERE phone = '+5562999999999')
AND action = 'blocked_by_lgpd'
ORDER BY created_at DESC;
```

#### Passo 5: Workflow Multi-Canal com LGPD

**Criar evento que dispara notificações em todos os canais**:
```sql
-- Exemplo: Novo lead qualificado
-- Sistema deve enviar apenas WhatsApp (email bloqueado)

SELECT create_notification(
    (SELECT id FROM leads WHERE phone = '+5562999999999' LIMIT 1),
    NULL,
    'email',
    'new_lead',
    'novo_lead',
    'Novo Lead Qualificado',
    'Email bloqueado por LGPD',
    '{}'::jsonb,
    3,
    NOW()
);

SELECT create_notification(
    (SELECT id FROM leads WHERE phone = '+5562999999999' LIMIT 1),
    NULL,
    'whatsapp',
    'new_lead',
    'novo_lead',
    'Novo Lead Qualificado',
    'WhatsApp permitido',
    '{}'::jsonb,
    3,
    NOW()
);

SELECT create_notification(
    (SELECT id FROM leads WHERE phone = '+5562999999999' LIMIT 1),
    NULL,
    'discord',
    'new_lead',
    '',
    'Novo Lead Qualificado',
    'Discord bloqueado por LGPD',
    '{}'::jsonb,
    3,
    NOW()
);
```

**Validar resultado**:
```sql
SELECT channel, COUNT(*) as notifications_created
FROM notifications
WHERE lead_id = (SELECT id FROM leads WHERE phone = '+5562999999999')
AND notification_type = 'new_lead'
AND created_at > NOW() - INTERVAL '1 minute'
GROUP BY channel;
```

**Resultado Esperado**:
```
channel  | notifications_created
---------+----------------------
whatsapp |                    1
```

**Não deve aparecer**:
- ❌ email (bloqueado por opt-out)
- ❌ discord (bloqueado por opt-out)

### ✅ Critérios de Aceitação

- [ ] Função `check_notification_allowed()` valida preferências
- [ ] Notificações bloqueadas não são criadas
- [ ] Notificações permitidas são criadas normalmente
- [ ] Workflows respeitam preferências LGPD
- [ ] Logs registram tentativas bloqueadas (se implementado)
- [ ] Sem erros ao tentar enviar para canal bloqueado

---

## Cenário 8: Múltiplos Canais Simultâneos

### 🎯 Objetivo
Validar envio simultâneo de notificações em múltiplos canais (Email + WhatsApp + Discord) para um único evento.

### 📝 Pré-condições
- Lead com todos os canais habilitados
- Workflows 11, 12, 13 ativos
- Todos os serviços (SMTP, Evolution, Discord) funcionando

### 🔄 Fluxo de Teste

#### Passo 1: Configurar Lead com Todos os Canais
```sql
-- Atualizar preferências: todos os canais habilitados
UPDATE leads
SET notification_preferences = jsonb_build_object(
    'email', true,
    'whatsapp', true,
    'discord', true
)
WHERE phone = '+5562999999999';
```

#### Passo 2: Disparar Evento Multi-Canal

**Via SQL** (simulação):
```sql
-- Criar notificações para os 3 canais
DO $$
DECLARE
    test_lead_id UUID;
    template_vars JSONB;
BEGIN
    -- Obter lead_id
    SELECT id INTO test_lead_id
    FROM leads
    WHERE phone = '+5562999999999';

    -- Preparar template variables
    template_vars := json_build_object(
        'lead_name', 'João Silva',
        'phone', '+5562999999999',
        'service_name', 'Energia Solar',
        'address', 'Rua Teste 123',
        'city', 'Goiânia',
        'state', 'GO'
    )::jsonb;

    -- Email
    PERFORM create_notification(
        test_lead_id, NULL, 'email', 'new_lead', 'novo_lead',
        'Novo Lead Qualificado - E2 Soluções',
        'Um novo lead foi qualificado pelo bot',
        template_vars, 3, NOW()
    );

    -- WhatsApp
    PERFORM create_notification(
        test_lead_id, NULL, 'whatsapp', 'new_lead', 'novo_lead',
        'Novo Lead',
        'Novo lead qualificado',
        template_vars, 3, NOW()
    );

    -- Discord
    PERFORM create_notification(
        test_lead_id, NULL, 'discord', 'new_lead', '',
        'Novo Lead Qualificado',
        'Lead qualificado via bot WhatsApp',
        template_vars, 3, NOW()
    );
END $$;
```

**Via Workflow** (real):
- Completar conversa WhatsApp até status `qualified`
- Sistema cria automaticamente notificações multi-canal

#### Passo 3: Aguardar Processamento

```bash
# Monitorar logs em tempo real
docker logs -f n8n | grep -E "(Notification|Discord|Email|WhatsApp)"

# Aguardar ~2 minutos para todos os workflows executarem
```

#### Passo 4: Validar Criação das Notificações
```sql
-- Listar todas as notificações criadas
SELECT
    id,
    channel,
    notification_type,
    status,
    subject,
    created_at,
    sent_at
FROM notifications
WHERE lead_id = (SELECT id FROM leads WHERE phone = '+5562999999999')
AND notification_type = 'new_lead'
AND created_at > NOW() - INTERVAL '5 minutes'
ORDER BY channel, created_at DESC;
```

**Resultado Esperado**:
```
channel  | status | created_at           | sent_at
---------+--------+----------------------+---------------------
discord  | sent   | 2025-12-15 10:00:00  | 2025-12-15 10:00:30
email    | sent   | 2025-12-15 10:00:01  | 2025-12-15 10:00:45
whatsapp | sent   | 2025-12-15 10:00:02  | 2025-12-15 10:01:00
```

#### Passo 5: Validar Recebimento em Cada Canal

**Discord (#leads)**:
- Verifique mensagem com embed formatado
- Título: "🎯 Novo Lead Qualificado"
- Campos: Nome, Telefone, Serviço, Endereço

**Email**:
- Verifique inbox do email configurado
- Subject: "Novo Lead Qualificado - E2 Soluções"
- Corpo HTML renderizado corretamente (template `novo_lead.html`)

**WhatsApp**:
- Verifique mensagem no número do time comercial
- Texto formatado com template `novo_lead.txt`

#### Passo 6: Validar Workflows Executados

**n8n UI** (`http://localhost:5678`):

**Workflow 11 - Notification Processor**:
- ✅ 3 execuções (uma para cada canal)
- Cada execução processou 1 notificação

**Workflow 12 - Multi-Channel Notifications**:
- ✅ 1 execução
- Roteou notificações para canais específicos

**Workflow 13 - Discord Notifications**:
- ✅ 1 execução
- Enviou mensagem para webhook #leads

**Workflow 07 - Send Email**:
- ✅ 1 execução (se SMTP configurado)
- Email enviado com sucesso

#### Passo 7: Validar Timing

```sql
-- Calcular diferença de tempo entre criação e envio
SELECT
    channel,
    sent_at - created_at AS processing_time
FROM notifications
WHERE lead_id = (SELECT id FROM leads WHERE phone = '+5562999999999')
AND notification_type = 'new_lead'
AND created_at > NOW() - INTERVAL '5 minutes'
ORDER BY channel;
```

**Resultado Esperado**:
- ✅ Discord: ~30-60 segundos (mais rápido)
- ✅ WhatsApp: ~30-90 segundos
- ✅ Email: ~30-120 segundos (depende do SMTP)

**Tolerância**: Até 5 minutos (polling interval)

### ✅ Critérios de Aceitação

- [ ] 3 notificações criadas (email, whatsapp, discord)
- [ ] Todas as notificações com status `sent`
- [ ] Mensagem recebida no Discord (#leads)
- [ ] Email recebido na caixa de entrada
- [ ] WhatsApp recebido pelo time comercial
- [ ] Workflows 11, 12, 13, 07 executaram com sucesso
- [ ] Tempo de processamento < 5 minutos
- [ ] Sem erros nos logs Docker

---

## 📊 Resumo de Cobertura de Testes

| Cenário | Funcionalidade Testada | Status |
|---------|------------------------|--------|
| 1 | Novo lead qualificado + notificações multi-canal | ✅ Completo |
| 2 | Agendamento de visita + Google Calendar | ✅ Completo |
| 3 | Lembretes automáticos (24h + 2h) | ✅ Completo |
| 4 | Handoff para atendente humano | ✅ Completo |
| 5 | Sincronização bidirecional RD Station | ✅ Completo |
| 6 | Retry automático em falhas | ✅ Completo |
| 7 | Conformidade LGPD (opt-out) | ✅ Completo |
| 8 | Envio simultâneo múltiplos canais | ✅ Completo |

---

## 🚀 Script de Execução Automática

Para executar todos os cenários automaticamente:

```bash
# Executar script de teste completo
./scripts/test-notifications.sh

# Executar apenas testes SQL
psql $DATABASE_URL < database/tests/test_notification_functions.sql

# Executar apenas testes de API
./scripts/test-api-integration.sh
```

---

## 📝 Checklist Final de Validação

- [ ] **Cenário 1**: Novo lead → notificações multi-canal ✅
- [ ] **Cenário 2**: Agendamento → Google Calendar ✅
- [ ] **Cenário 3**: Lembretes automáticos funcionando ✅
- [ ] **Cenário 4**: Handoff → alerta no Discord ✅
- [ ] **Cenário 5**: RD Station sync bidirecional ✅
- [ ] **Cenário 6**: Retry automático funciona ✅
- [ ] **Cenário 7**: LGPD respeitado ✅
- [ ] **Cenário 8**: Múltiplos canais simultâneos ✅

---

**Última Atualização**: 2025-12-15
**Sprint**: 1.3 - Sistema de Notificações Multi-Canal
**Cobertura**: 8 cenários E2E documentados
