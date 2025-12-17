# Sprint 1.3 - Guia de Validação Completo

> **Sistema de Notificações Multi-Canal**
> **Data**: 2025-12-15
> **Status**: Guia de validação completo para aceite do sprint

---

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Pré-Requisitos](#pré-requisitos)
3. [Validação Fase 1: Banco de Dados](#validação-fase-1-banco-de-dados)
4. [Validação Fase 2: Workflows n8n](#validação-fase-2-workflows-n8n)
5. [Validação Fase 3: Templates](#validação-fase-3-templates)
6. [Validação Fase 4: Configurações](#validação-fase-4-configurações)
7. [Validação Fase 5: Testes](#validação-fase-5-testes)
8. [Testes End-to-End](#testes-end-to-end)
9. [Checklist Final de Aceite](#checklist-final-de-aceite)
10. [Troubleshooting](#troubleshooting)

---

## Visão Geral

### 🎯 Objetivo do Sprint 1.3
Implementar sistema completo de notificações multi-canal (Email, WhatsApp, Discord) com:
- Gerenciamento centralizado via PostgreSQL
- Processamento automático via n8n workflows
- Templates personalizados para cada canal
- Retry automático em falhas
- Conformidade LGPD

### 📊 Escopo de Validação
Este guia valida **6 fases** de implementação:
1. **Banco de Dados**: 4 funções SQL + 2 triggers
2. **Workflows n8n**: 3 novos + 3 atualizados
3. **Templates**: 4 WhatsApp + 5 Email
4. **Configurações**: Discord (3 webhooks) + Evolution API
5. **Testes**: SQL unit tests + bash scripts + cenários E2E
6. **Documentação**: Guias de setup + documentação técnica

### ⏱️ Tempo Estimado de Validação
- **Validação Rápida**: 30 minutos (checklist básico)
- **Validação Completa**: 2 horas (todos os testes E2E)
- **Validação Automática**: 10 minutos (script `test-notifications.sh`)

---

## Pré-Requisitos

### ✅ Ambiente Técnico

1. **Docker Compose** rodando com 11 serviços:
   ```bash
   cd /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot
   ./scripts/start-dev.sh

   # Verificar serviços ativos
   docker ps | grep -E "(n8n|postgres|evolution)"
   ```

2. **PostgreSQL** acessível:
   ```bash
   psql $DATABASE_URL -c "SELECT 1;"
   ```

3. **n8n** acessível:
   ```bash
   curl -s http://localhost:5678/ | grep -q "n8n" && echo "✅ n8n OK"
   ```

4. **Evolution API** (WhatsApp) conectada:
   ```bash
   curl -s "$EVOLUTION_API_URL/instance/connectionState/e2-solucoes-bot" \
     -H "apikey: $EVOLUTION_API_KEY" | jq .state
   # Deve retornar: "open"
   ```

### ✅ Configurações Obrigatórias

**Arquivo `.env`** com variáveis:
```bash
# Verificar variáveis críticas
grep -E "^(DISCORD_WEBHOOK_|EVOLUTION_|DATABASE_URL)" docker/.env

# Deve conter:
DISCORD_WEBHOOK_LEADS=https://discord.com/api/webhooks/...
DISCORD_WEBHOOK_APPOINTMENTS=https://discord.com/api/webhooks/...
DISCORD_WEBHOOK_ALERTS=https://discord.com/api/webhooks/...
EVOLUTION_API_URL=https://...
EVOLUTION_API_KEY=...
DATABASE_URL=postgresql://...
```

### ✅ Dados de Teste

**Lead de teste** criado:
```sql
INSERT INTO leads (phone, name, email, address, city, state, service_type, status, notification_preferences)
VALUES (
    '+5562999999998',
    'Lead Validação Sprint 1.3',
    'validacao@e2solucoes.com.br',
    'Rua Teste 123',
    'Goiânia',
    'GO',
    'energia_solar',
    'qualified',
    jsonb_build_object('email', true, 'whatsapp', true, 'discord', true)
)
ON CONFLICT (phone) DO NOTHING;
```

---

## Validação Fase 1: Banco de Dados

### 📦 Objetivo
Validar que schema, funções SQL e triggers estão instalados corretamente.

### 🔍 Checklist de Validação

#### 1.1 Schema e Tabelas

```bash
# Executar via terminal
psql $DATABASE_URL <<EOF
-- Verificar tabela notifications existe
SELECT EXISTS (
    SELECT FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_name = 'notifications'
);

-- Verificar colunas obrigatórias
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'public'
AND table_name = 'notifications'
ORDER BY ordinal_position;

-- Verificar índices
SELECT indexname, indexdef
FROM pg_indexes
WHERE schemaname = 'public'
AND tablename = 'notifications';
EOF
```

**Resultado Esperado**:
- ✅ Tabela `notifications` existe
- ✅ 20 colunas presentes (id, lead_id, appointment_id, channel, ...)
- ✅ 6 índices criados (idx_notifications_status, idx_notifications_channel, ...)

#### 1.2 Funções SQL

```bash
psql $DATABASE_URL <<EOF
-- Listar funções do Sprint 1.3
SELECT
    p.proname AS function_name,
    pg_get_function_arguments(p.oid) AS arguments,
    pg_get_function_result(p.oid) AS return_type
FROM pg_proc p
JOIN pg_namespace n ON p.pronamespace = n.oid
WHERE n.nspname = 'public'
AND p.proname IN (
    'create_notification',
    'check_notification_allowed',
    'update_notification_status',
    'get_pending_notifications',
    'get_failed_notifications',
    'get_notification_stats',
    'create_appointment_reminders'
)
ORDER BY p.proname;
EOF
```

**Resultado Esperado**:
- ✅ 7 funções encontradas
- ✅ `create_notification` retorna UUID
- ✅ `check_notification_allowed` retorna BOOLEAN
- ✅ `get_pending_notifications` retorna TABLE
- ✅ `get_notification_stats` retorna TABLE

#### 1.3 Triggers

```bash
psql $DATABASE_URL <<EOF
-- Verificar triggers instalados
SELECT
    tgname AS trigger_name,
    tgrelid::regclass AS table_name,
    pg_get_triggerdef(oid) AS trigger_definition
FROM pg_trigger
WHERE tgname LIKE '%notification%'
AND tgisinternal = false;
EOF
```

**Resultado Esperado**:
- ✅ 2 triggers encontrados:
  - `trigger_update_notification_updated_at`
  - `trigger_create_appointment_reminders` (se implementado)

#### 1.4 Teste Funcional Básico

```bash
psql $DATABASE_URL <<EOF
-- Teste: Criar notificação válida
SELECT create_notification(
    (SELECT id FROM leads WHERE phone = '+5562999999998' LIMIT 1),
    NULL,
    'email',
    'test',
    '',
    'Teste Validação Fase 1',
    'Corpo do teste',
    json_build_object('test', true)::jsonb,
    3,
    NOW()
) AS notification_id;

-- Verificar que foi criada
SELECT COUNT(*) AS count_must_be_1
FROM notifications
WHERE subject = 'Teste Validação Fase 1';

-- Limpar teste
DELETE FROM notifications WHERE subject = 'Teste Validação Fase 1';
EOF
```

**Resultado Esperado**:
- ✅ `notification_id` retornado (UUID válido)
- ✅ `count_must_be_1 = 1`
- ✅ Registro deletado com sucesso

### ✅ Critérios de Aceite Fase 1

- [ ] Tabela `notifications` existe com 20 colunas
- [ ] 6 índices criados corretamente
- [ ] 7 funções SQL instaladas e retornam tipos corretos
- [ ] 2 triggers instalados e funcionando
- [ ] Teste funcional básico passa sem erros

---

## Validação Fase 2: Workflows n8n

### 📦 Objetivo
Validar que workflows foram importados, estão ativos e executam corretamente.

### 🔍 Checklist de Validação

#### 2.1 Workflows Importados

**Acesse n8n**: `http://localhost:5678`

**Verificar existência dos workflows**:
- [ ] **Workflow 11** - Notification Processor
- [ ] **Workflow 12** - Multi-Channel Notifications
- [ ] **Workflow 13** - Discord Notifications

**Workflows atualizados**:
- [ ] **Workflow 02** - AI Agent Conversation (com integração notification)
- [ ] **Workflow 05** - Appointment Scheduler (com integração notification)
- [ ] **Workflow 10** - Handoff to Human (com integração notification)

#### 2.2 Workflows Ativos

**Verificar status**:
```bash
# Via arquivo JSON (verificar "active": true)
grep '"active"' n8n/workflows/11_notification_processor.json
grep '"active"' n8n/workflows/12_multi_channel_notifications.json
grep '"active"' n8n/workflows/13_discord_notifications.json
```

**Via n8n UI**:
- Cada workflow deve ter um **toggle verde** (ativo) no canto superior direito
- Se aparecer "Inactive", clicar para ativar

#### 2.3 Teste de Execução Manual

**Workflow 11 - Notification Processor**:
1. n8n UI → Workflow 11
2. Clicar em **"Execute Workflow"**
3. Observar execução (deve buscar notificações pending)
4. Verificar que execução termina com ✅ Success

**Workflow 13 - Discord Notifications**:
1. Criar notificação de teste Discord:
   ```sql
   SELECT create_notification(
       (SELECT id FROM leads WHERE phone = '+5562999999998' LIMIT 1),
       NULL,
       'discord',
       'test',
       '',
       'Teste Workflow 13',
       'Validação manual',
       json_build_object('lead_name', 'Teste')::jsonb,
       3,
       NOW()
   );
   ```
2. Aguardar 1-2 minutos (polling interval)
3. Verificar execução no n8n (Workflow 11 → 12 → 13)
4. Verificar mensagem no Discord

#### 2.4 Validar Integrações Entre Workflows

**Fluxo esperado**:
```
Workflow 11 (Polling) →
    Busca notifications pending →
    Chama Workflow 12 (Router) →
        Se channel = discord → Workflow 13
        Se channel = email → Workflow 07
        Se channel = whatsapp → Evolution API direct
```

**Teste de integração**:
```bash
# Criar notificação Discord
psql $DATABASE_URL -c "
SELECT create_notification(
    (SELECT id FROM leads LIMIT 1), NULL, 'discord', 'test', '',
    'Teste Integração', '', '{}'::jsonb, 3, NOW()
);
"

# Aguardar 2 minutos

# Verificar execuções n8n
# UI → Executions → Verificar:
# - Workflow 11 executou
# - Workflow 12 executou
# - Workflow 13 executou
# - Notificação marcada como 'sent'
```

### ✅ Critérios de Aceite Fase 2

- [ ] 3 novos workflows importados (11, 12, 13)
- [ ] 3 workflows atualizados (02, 05, 10)
- [ ] Todos os workflows estão ativos (toggle verde)
- [ ] Execução manual do Workflow 11 funciona
- [ ] Integração entre workflows (11 → 12 → 13) funciona
- [ ] Notificação de teste enviada e recebida no Discord

---

## Validação Fase 3: Templates

### 📦 Objetivo
Validar que templates WhatsApp e Email existem e têm sintaxe correta.

### 🔍 Checklist de Validação

#### 3.1 Templates WhatsApp

```bash
# Listar templates WhatsApp
ls -lh templates/whatsapp/

# Deve conter:
# - lembrete_24h.txt
# - lembrete_2h.txt
# - confirmacao_agendamento.txt
# - apos_visita.txt
```

**Validar sintaxe placeholders**:
```bash
# Verificar uso correto de {{VARIABLE}}
for file in templates/whatsapp/*.txt; do
    echo "=== $file ==="
    grep -E '{{[A-Z_]+}}' "$file" || echo "Sem placeholders"
done
```

**Resultado Esperado**:
- ✅ 4 arquivos `.txt` presentes
- ✅ Placeholders no formato `{{CUSTOMER_NAME}}`, `{{COMPANY_NAME}}`, etc.
- ✅ Sem expressões n8n (`{{ $json.` não deve aparecer)

#### 3.2 Templates Email

```bash
# Listar templates Email
ls -lh templates/emails/

# Deve conter:
# - novo_lead.html
# - lembrete_24h.html
# - lembrete_2h.html
# - confirmacao_agendamento.html
# - apos_visita.html
```

**Validar sintaxe n8n**:
```bash
# Verificar uso correto de {{ $json.variable }}
for file in templates/emails/*.html; do
    echo "=== $file ==="
    grep -oE '\{\{ \$json\.[a-z_]+ \}\}' "$file" | head -5
done
```

**Resultado Esperado**:
- ✅ 5 arquivos `.html` presentes
- ✅ Expressões n8n no formato `{{ $json.lead_name }}`
- ✅ HTML válido (abrir em navegador para verificar)

#### 3.3 Teste de Renderização

**WhatsApp Template**:
```bash
# Substituir placeholders manualmente (teste visual)
cat templates/whatsapp/lembrete_24h.txt | \
  sed 's/{{CUSTOMER_NAME}}/João Silva/g' | \
  sed 's/{{APPOINTMENT_DATE}}/Quinta-feira, 20\/12\/2025/g' | \
  sed 's/{{APPOINTMENT_TIME}}/10:00/g' | \
  sed 's/{{COMPANY_PHONE}}/(62) 3092-2900/g'
```

**Email Template**:
```bash
# Abrir no navegador
firefox templates/emails/novo_lead.html
# ou
google-chrome templates/emails/novo_lead.html

# Verificar:
# - CSS renderizado corretamente
# - Layout responsivo
# - Expressões {{ $json.* }} visíveis (serão substituídas pelo n8n)
```

### ✅ Critérios de Aceite Fase 3

- [ ] 4 templates WhatsApp criados (`.txt`)
- [ ] 5 templates Email criados (`.html`)
- [ ] Templates WhatsApp usam placeholders `{{VARIABLE}}`
- [ ] Templates Email usam expressões n8n `{{ $json.variable }}`
- [ ] HTML válido e renderiza corretamente
- [ ] Substituição de placeholders funciona visualmente

---

## Validação Fase 4: Configurações

### 📦 Objetivo
Validar configurações de Discord (webhooks) e Evolution API (WhatsApp).

### 🔍 Checklist de Validação

#### 4.1 Discord Webhooks

**Teste de conectividade**:
```bash
# Carregar variáveis de ambiente
source docker/.env

# Testar webhook LEADS
curl -X POST "$DISCORD_WEBHOOK_LEADS" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "✅ Validação Sprint 1.3 - Webhook LEADS funcionando!"
  }'

# Verificar resposta: HTTP 204 (sucesso)
# Verificar mensagem no canal Discord #leads
```

**Repetir para os outros webhooks**:
```bash
# Webhook APPOINTMENTS
curl -X POST "$DISCORD_WEBHOOK_APPOINTMENTS" \
  -H "Content-Type: application/json" \
  -d '{"content": "✅ Validação - Webhook APPOINTMENTS OK!"}'

# Webhook ALERTS
curl -X POST "$DISCORD_WEBHOOK_ALERTS" \
  -H "Content-Type: application/json" \
  -d '{"content": "✅ Validação - Webhook ALERTS OK!"}'
```

**Resultado Esperado**:
- ✅ HTTP 204 para todos os 3 webhooks
- ✅ 3 mensagens recebidas no Discord (canais #leads, #agendamentos, #alertas)

#### 4.2 Evolution API (WhatsApp)

**Verificar status da instância**:
```bash
curl -s "$EVOLUTION_API_URL/instance/connectionState/e2-solucoes-bot" \
  -H "apikey: $EVOLUTION_API_KEY" | jq .
```

**Resultado Esperado**:
```json
{
  "instance": {
    "instanceName": "e2-solucoes-bot",
    "state": "open"
  }
}
```

**Se `state = "close"`** (desconectado):
```bash
# Gerar QR Code
curl -s "$EVOLUTION_API_URL/instance/connect/e2-solucoes-bot" \
  -H "apikey: $EVOLUTION_API_KEY" | jq -r '.qrcode.base64' | base64 -d > qr.png

# Abrir qr.png e escanear com WhatsApp no celular
firefox qr.png

# Aguardar 10 segundos

# Verificar novamente
curl -s "$EVOLUTION_API_URL/instance/connectionState/e2-solucoes-bot" \
  -H "apikey: $EVOLUTION_API_KEY" | jq .state
# Deve retornar: "open"
```

**Teste de envio WhatsApp**:
```bash
# Enviar mensagem de teste
curl -X POST "$EVOLUTION_API_URL/message/sendText/e2-solucoes-bot" \
  -H "Content-Type: application/json" \
  -H "apikey: $EVOLUTION_API_KEY" \
  -d '{
    "number": "5562999999998",
    "text": "✅ Validação Sprint 1.3 - WhatsApp conectado!"
  }'

# Verificar no WhatsApp se mensagem foi recebida
```

#### 4.3 Variáveis de Ambiente

```bash
# Validar que todas as variáveis críticas estão configuradas
cat docker/.env | grep -E "^(DISCORD_WEBHOOK_|EVOLUTION_|NOTIFICATION_)" | \
  while IFS= read -r line; do
    key=$(echo "$line" | cut -d'=' -f1)
    value=$(echo "$line" | cut -d'=' -f2)
    if [ -z "$value" ] || [[ "$value" == *"XXXX"* ]]; then
      echo "❌ $key não configurado"
    else
      echo "✅ $key configurado"
    fi
  done
```

**Resultado Esperado**:
```
✅ DISCORD_WEBHOOK_LEADS configurado
✅ DISCORD_WEBHOOK_APPOINTMENTS configurado
✅ DISCORD_WEBHOOK_ALERTS configurado
✅ EVOLUTION_API_URL configurado
✅ EVOLUTION_API_KEY configurado
✅ NOTIFICATION_RETRY_MAX configurado
✅ NOTIFICATION_BATCH_SIZE configurado
```

### ✅ Critérios de Aceite Fase 4

- [ ] 3 webhooks Discord testados e funcionando
- [ ] 3 mensagens recebidas nos canais Discord
- [ ] Evolution API status = "open" (conectada)
- [ ] Mensagem de teste WhatsApp enviada e recebida
- [ ] Todas as variáveis de ambiente configuradas
- [ ] Sem valores `XXXX` ou vazios no `.env`

---

## Validação Fase 5: Testes

### 📦 Objetivo
Executar testes automatizados: SQL unit tests, bash scripts e validação E2E.

### 🔍 Checklist de Validação

#### 5.1 Testes SQL Unitários

```bash
# Executar todos os testes SQL
psql $DATABASE_URL < database/tests/test_notification_functions.sql

# Verificar saída
# Deve aparecer:
# ✅ PASSOU: Notificação criada com sucesso
# ✅ PASSOU: Status inicial correto (pending)
# ...
# TESTES CONCLUÍDOS COM SUCESSO!
```

**Resultado Esperado**:
- ✅ 12 testes executados
- ✅ Todos os testes passaram (mensagens `✅ PASSOU`)
- ✅ Nenhuma mensagem `❌ FALHOU`
- ✅ Mensagem final: "TESTES CONCLUÍDOS COM SUCESSO!"

#### 5.2 Script Bash de Integração

```bash
# Executar script de teste completo
cd /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot
./scripts/test-notifications.sh

# Script executa 7 testes:
# 1. Conectividade PostgreSQL
# 2. Discord Webhooks (3 testes)
# 3. Evolution API
# 4. Funções SQL Unitárias
# 5. Criação de Notificação E2E
# 6. Validação Workflows n8n
# 7. Validação Templates
```

**Resultado Esperado**:
```
========================================
✅ TODOS OS TESTES PASSARAM!
========================================

Total de Testes: 25
Testes Passaram: 25
Testes Falharam: 0
```

**Se houver falhas**:
- Script exibe mensagens de erro detalhadas
- Seguir recomendações do script (configurar .env, iniciar docker, etc.)

#### 5.3 Cenários End-to-End

**Documentação completa em**: `docs/validation/SPRINT_1.3_E2E_SCENARIOS.md`

**Execução rápida dos 3 cenários principais**:

**Cenário 1: Novo Lead + Notificações Multi-Canal**
```bash
# 1. Criar lead qualificado
psql $DATABASE_URL <<EOF
INSERT INTO leads (phone, name, email, address, city, state, service_type, status, notification_preferences)
VALUES ('+5562999999997', 'E2E Cenário 1', 'cenario1@teste.com', 'Rua 1', 'Goiânia', 'GO', 'energia_solar', 'qualified',
jsonb_build_object('email', true, 'whatsapp', true, 'discord', true))
ON CONFLICT (phone) DO UPDATE SET status = 'qualified';

SELECT create_notification(
    (SELECT id FROM leads WHERE phone = '+5562999999997'),
    NULL, 'discord', 'new_lead', '', 'Novo Lead E2E', 'Teste cenário 1',
    json_build_object('lead_name', 'E2E Cenário 1')::jsonb, 3, NOW()
);
EOF

# 2. Aguardar 2 minutos

# 3. Verificar Discord recebeu mensagem

# 4. Verificar banco
psql $DATABASE_URL -c "
SELECT channel, status FROM notifications
WHERE lead_id = (SELECT id FROM leads WHERE phone = '+5562999999997')
ORDER BY created_at DESC LIMIT 3;
"
# Deve retornar status = 'sent'
```

**Cenário 2: Agendamento + Lembretes**
```bash
# 1. Criar appointment
psql $DATABASE_URL <<EOF
INSERT INTO appointments (lead_id, scheduled_at, type, status, location)
VALUES (
    (SELECT id FROM leads WHERE phone = '+5562999999997'),
    NOW() + INTERVAL '25 hours',
    'technical_visit',
    'scheduled',
    'Endereço teste'
);

SELECT create_appointment_reminders(
    (SELECT id FROM appointments ORDER BY created_at DESC LIMIT 1)
);
EOF

# 2. Verificar 2 lembretes criados
psql $DATABASE_URL -c "
SELECT notification_type, scheduled_for, status
FROM notifications
WHERE appointment_id = (SELECT id FROM appointments ORDER BY created_at DESC LIMIT 1)
ORDER BY scheduled_for;
"
# Deve retornar: reminder_24h e reminder_2h
```

**Cenário 3: Handoff para Humano**
```bash
# 1. Marcar conversa como handoff
psql $DATABASE_URL <<EOF
UPDATE conversations
SET current_state = 'handoff_comercial',
    last_human_handoff_at = NOW()
WHERE phone = '+5562999999997';

SELECT create_notification(
    (SELECT id FROM leads WHERE phone = '+5562999999997'),
    NULL, 'discord', 'handoff_to_human', '', 'Handoff E2E',
    'Cliente solicitou atendente',
    json_build_object('lead_name', 'E2E Cenário 1')::jsonb, 5, NOW()
);
EOF

# 2. Verificar Discord (#alertas) recebeu alerta
# 3. Verificar banco
psql $DATABASE_URL -c "
SELECT current_state, last_human_handoff_at FROM conversations
WHERE phone = '+5562999999997';
"
```

### ✅ Critérios de Aceite Fase 5

- [ ] Testes SQL unitários: 12/12 passaram
- [ ] Script bash: 25/25 testes passaram
- [ ] Cenário 1 (Novo Lead): Notificações enviadas ✅
- [ ] Cenário 2 (Agendamento): 2 lembretes criados ✅
- [ ] Cenário 3 (Handoff): Alerta Discord recebido ✅
- [ ] Sem erros nos logs Docker durante testes

---

## Testes End-to-End

### 📦 Teste E2E Completo (Validação Final)

Este teste simula o **fluxo completo** de um lead do início ao fim.

#### Passo 1: Conversa WhatsApp → Lead Qualificado

**Via WhatsApp** (manual):
1. Enviar mensagem: "Olá" para o bot
2. Responder perguntas do bot
3. Solicitar agendamento de visita
4. Confirmar horário

**OU via Simulação SQL** (automático):
```bash
psql $DATABASE_URL <<EOF
-- Criar lead qualificado
INSERT INTO leads (phone, name, email, address, city, state, service_type, status, notification_preferences)
VALUES (
    '+5562999999996',
    'E2E Completo',
    'e2e@teste.com',
    'Rua E2E 123',
    'Goiânia',
    'GO',
    'energia_solar',
    'qualified',
    jsonb_build_object('email', true, 'whatsapp', true, 'discord', true)
)
ON CONFLICT (phone) DO UPDATE SET status = 'qualified';

-- Criar appointment
INSERT INTO appointments (lead_id, scheduled_at, type, status, location, google_event_id)
VALUES (
    (SELECT id FROM leads WHERE phone = '+5562999999996'),
    NOW() + INTERVAL '25 hours',
    'technical_visit',
    'scheduled',
    'Rua E2E 123',
    'test_event_e2e'
);
EOF
```

#### Passo 2: Sistema Cria Notificações Automaticamente

**Validar que notificações foram criadas**:
```bash
psql $DATABASE_URL -c "
SELECT
    notification_type,
    channel,
    status,
    subject,
    created_at
FROM notifications
WHERE lead_id = (SELECT id FROM leads WHERE phone = '+5562999999996')
ORDER BY created_at DESC;
"
```

**Resultado Esperado** (6+ notificações):
```
notification_type         | channel  | status  | subject
--------------------------+----------+---------+--------------------------------
reminder_24h              | email    | pending | Lembrete: Visita Amanhã
reminder_24h              | whatsapp | pending | Lembrete Visita
reminder_2h               | email    | pending | Lembrete: Visita em 2 Horas
reminder_2h               | whatsapp | pending | Lembrete Visita
appointment_confirmation  | email    | pending | Confirmação de Agendamento
new_lead                  | discord  | pending | Novo Lead Qualificado
```

#### Passo 3: Workflows Processam Notificações

**Aguardar 3 minutos** (polling intervals):
- Workflow 11 busca notificações pending a cada 1min
- Workflow 12 roteia para canais específicos
- Workflow 13 envia para Discord

**Monitorar processamento**:
```bash
# Logs em tempo real
docker logs -f n8n | grep -E "(Notification|Processing)"

# Ctrl+C para sair após ver mensagens de processamento
```

#### Passo 4: Validar Envios

**4.1 Discord**:
- Acesse canal `#leads` → Verificar mensagem "Novo Lead Qualificado"
- Acesse canal `#agendamentos` → Verificar "Nova Visita Agendada"

**4.2 Banco de Dados**:
```bash
psql $DATABASE_URL -c "
SELECT
    channel,
    COUNT(*) FILTER (WHERE status = 'sent') AS sent_count,
    COUNT(*) FILTER (WHERE status = 'pending') AS pending_count,
    COUNT(*) FILTER (WHERE status = 'failed') AS failed_count
FROM notifications
WHERE lead_id = (SELECT id FROM leads WHERE phone = '+5562999999996')
GROUP BY channel;
"
```

**Resultado Esperado**:
```
channel  | sent_count | pending_count | failed_count
---------+------------+---------------+-------------
discord  |         1  |             0 |            0
email    |         0  |             3 |            0  (lembretes futuros)
whatsapp |         0  |             2 |            0  (lembretes futuros)
```

**4.3 n8n Executions**:
- Acesse `http://localhost:5678`
- Menu: Executions
- Verificar últimas 10 execuções:
  - ✅ Workflow 11: Success (múltiplas execuções)
  - ✅ Workflow 12: Success
  - ✅ Workflow 13: Success

#### Passo 5: Simular Lembretes (24h e 2h)

```bash
# Alterar scheduled_for para NOW() + 1 minuto
psql $DATABASE_URL <<EOF
UPDATE notifications
SET scheduled_for = NOW() + INTERVAL '1 minute'
WHERE appointment_id = (
    SELECT id FROM appointments
    WHERE lead_id = (SELECT id FROM leads WHERE phone = '+5562999999996')
    ORDER BY created_at DESC LIMIT 1
)
AND notification_type IN ('reminder_24h', 'reminder_2h');
EOF

# Aguardar 2 minutos

# Verificar que foram enviados
psql $DATABASE_URL -c "
SELECT notification_type, channel, status, sent_at
FROM notifications
WHERE appointment_id = (
    SELECT id FROM appointments
    WHERE lead_id = (SELECT id FROM leads WHERE phone = '+5562999999996')
    ORDER BY created_at DESC LIMIT 1
)
ORDER BY notification_type, channel;
"
```

**Resultado Esperado**:
- ✅ 4 notificações: reminder_24h (email + whatsapp) + reminder_2h (email + whatsapp)
- ✅ Todas com `status = 'sent'`
- ✅ `sent_at` preenchido

### ✅ Critérios de Aceite E2E

- [ ] Lead criado com status `qualified`
- [ ] Appointment criado com status `scheduled`
- [ ] 6+ notificações criadas automaticamente
- [ ] Notificações Discord enviadas e recebidas
- [ ] Lembretes 24h e 2h enviados (simulação)
- [ ] Workflows executaram com sucesso
- [ ] Sem erros nos logs Docker

---

## Checklist Final de Aceite

### 🎯 Critérios de Aceite do Sprint 1.3

| # | Critério | Status | Evidência |
|---|----------|--------|-----------|
| 1 | Tabela `notifications` criada com schema completo | [ ] | SQL: `\d notifications` |
| 2 | 7 funções SQL instaladas e testadas | [ ] | Testes unitários 12/12 ✅ |
| 3 | 3 novos workflows n8n importados e ativos | [ ] | n8n UI: Workflows 11, 12, 13 |
| 4 | 3 workflows existentes atualizados | [ ] | n8n UI: Workflows 02, 05, 10 |
| 5 | 4 templates WhatsApp criados | [ ] | `ls templates/whatsapp/` |
| 6 | 5 templates Email criados | [ ] | `ls templates/emails/` |
| 7 | 3 Discord webhooks configurados e testados | [ ] | Mensagens recebidas no Discord |
| 8 | Evolution API conectada e testando | [ ] | Status = "open" |
| 9 | Testes SQL unitários passam (12/12) | [ ] | `psql < test_notification_functions.sql` |
| 10 | Script bash passa todos os testes (25/25) | [ ] | `./test-notifications.sh` |
| 11 | Cenário E2E completo funciona | [ ] | Lead → Appointment → Notificações ✅ |
| 12 | Documentação completa criada | [ ] | 8 arquivos markdown |
| 13 | LGPD: Opt-out funciona | [ ] | Teste Cenário 7 ✅ |
| 14 | Retry automático funciona | [ ] | Teste Cenário 6 ✅ |
| 15 | Múltiplos canais simultâneos | [ ] | Teste Cenário 8 ✅ |

### 📊 Resultado Final

**Para APROVAR o Sprint 1.3, todos os 15 critérios devem estar marcados ✅**

**Cálculo de Cobertura**:
```
Critérios Aprovados / Total = _____ / 15 = _____% de cobertura
```

**Decisão**:
- ✅ **APROVADO**: 15/15 critérios (100%)
- ⚠️ **APROVADO COM RESSALVAS**: 13-14/15 (86-93%)
- ❌ **REPROVADO**: < 13/15 (<86%)

---

## Troubleshooting

### Problema 1: Notificações Criadas mas Não Enviadas

**Sintomas**:
- Registros em `notifications` com `status = 'pending'`
- Nenhuma mensagem recebida no Discord/WhatsApp
- Workflow 11 não executa

**Diagnóstico**:
```bash
# 1. Verificar se Workflow 11 está ativo
# n8n UI → Workflow 11 → Settings → Active: ON

# 2. Verificar últimas execuções
# n8n UI → Workflow 11 → Executions
# Deve haver execuções recentes (última 1-2 minutos)

# 3. Verificar logs
docker logs n8n | grep "Notification Processor" | tail -20
```

**Solução**:
```bash
# Ativar Workflow 11 manualmente
# n8n UI → Workflow 11 → Toggle ativo (verde)

# Executar manualmente para testar
# n8n UI → Workflow 11 → Execute Workflow

# Se erro persistir: Reiniciar n8n
docker restart n8n
```

---

### Problema 2: Discord Webhook Retorna 404

**Sintomas**:
- Workflow 13 falha com erro "404 Not Found"
- Notificações marcadas como `failed`
- `error_message` contém "webhook not found"

**Diagnóstico**:
```bash
# Testar webhook manualmente
curl -X POST "$DISCORD_WEBHOOK_LEADS" \
  -H "Content-Type: application/json" \
  -d '{"content": "teste"}' \
  -w "\nHTTP Status: %{http_code}\n"

# Se retornar 404: Webhook foi deletado
```

**Solução**:
```bash
# 1. Criar novo webhook no Discord
# Discord → Server Settings → Integrations → Webhooks → Create Webhook

# 2. Copiar URL do novo webhook

# 3. Atualizar .env
nano docker/.env
# DISCORD_WEBHOOK_LEADS=nova_url_aqui

# 4. Reiniciar n8n
docker restart n8n

# 5. Reprocessar notificações falhadas
psql $DATABASE_URL -c "
UPDATE notifications
SET status = 'pending', retry_count = 0, error_message = NULL
WHERE status = 'failed'
AND channel = 'discord'
AND error_message LIKE '%404%';
"
```

---

### Problema 3: Evolution API Desconectada

**Sintomas**:
- Status retorna `"state": "close"`
- Mensagens WhatsApp não são enviadas
- Notificações WhatsApp ficam `pending`

**Solução**:
```bash
# 1. Gerar novo QR Code
curl -s "$EVOLUTION_API_URL/instance/connect/e2-solucoes-bot" \
  -H "apikey: $EVOLUTION_API_KEY" \
  | jq -r '.qrcode.base64' \
  | base64 -d > qr.png

# 2. Abrir QR Code
firefox qr.png

# 3. Escanear com WhatsApp no celular
# WhatsApp → Configurações → Aparelhos conectados → Conectar aparelho

# 4. Aguardar 10-15 segundos

# 5. Verificar status
curl -s "$EVOLUTION_API_URL/instance/connectionState/e2-solucoes-bot" \
  -H "apikey: $EVOLUTION_API_KEY" | jq .state
# Deve retornar: "open"
```

---

### Problema 4: Testes SQL Falhando

**Sintomas**:
- Mensagens `❌ FALHOU` ao executar `test_notification_functions.sql`
- Funções SQL retornam erros

**Diagnóstico**:
```bash
# Verificar se schema foi aplicado
psql $DATABASE_URL -c "
SELECT tablename FROM pg_tables
WHERE schemaname = 'public'
AND tablename = 'notifications';
"

# Se não retornar nada: schema não foi aplicado
```

**Solução**:
```bash
# Aplicar schema completo
psql $DATABASE_URL < database/schema.sql

# Aplicar funções de notificação
psql $DATABASE_URL < database/appointment_functions.sql

# Executar testes novamente
psql $DATABASE_URL < database/tests/test_notification_functions.sql
```

---

### Problema 5: Workflow Executa mas Notificação Não Muda Status

**Sintomas**:
- Workflow 11/12/13 executam com sucesso (verde)
- Notificações continuam `pending`
- Sem erros aparentes

**Diagnóstico**:
```bash
# Verificar última execução do Workflow 11
# n8n UI → Workflow 11 → Executions → Click na última
# Verificar nó "Update Notification Status"
# Deve ter executado e afetado 1+ rows
```

**Solução Comum**:
```bash
# Problema: Conexão PostgreSQL no workflow está incorreta

# 1. Verificar credentials no n8n
# n8n UI → Credentials → PostgreSQL
# Host: postgres-main (não localhost!)
# Port: 5432
# Database: e2_solucoes_bot
# User: postgres
# Password: (do .env)

# 2. Testar conexão
# n8n UI → Credentials → Test

# 3. Reimportar workflows se necessário
```

---

### Problema 6: Templates Não Renderizando Variáveis

**Sintomas**:
- Email/WhatsApp recebido com `{{ $json.lead_name }}` ao invés do nome
- Placeholders não substituídos

**Diagnóstico**:
```bash
# Verificar se template_variables está sendo passado
psql $DATABASE_URL -c "
SELECT id, subject, template_variables
FROM notifications
WHERE status = 'sent'
ORDER BY created_at DESC
LIMIT 5;
"

# Se template_variables = {} ou NULL: problema na criação
```

**Solução**:
```bash
# Ao criar notificação, sempre passar template_variables
psql $DATABASE_URL <<EOF
SELECT create_notification(
    (SELECT id FROM leads LIMIT 1),
    NULL,
    'email',
    'test',
    'novo_lead',
    'Teste',
    'Corpo',
    json_build_object(
        'lead_name', 'Nome Real',
        'phone', '+5562999999999',
        'service_name', 'Energia Solar'
    )::jsonb,  -- ← IMPORTANTE: passar variáveis aqui
    3,
    NOW()
);
EOF
```

---

## 📚 Referências Adicionais

### Documentação do Sprint 1.3

1. **Status de Implementação**: `docs/status/SPRINT_1.3_IMPLEMENTATION_STATUS.md`
2. **Cenários E2E**: `docs/validation/SPRINT_1.3_E2E_SCENARIOS.md`
3. **Setup Discord**: `docs/Setups/SETUP_DISCORD.md`
4. **Setup Evolution API**: `docs/Setups/SETUP_EVOLUTION_API.md`

### Scripts de Teste

- **SQL Unit Tests**: `database/tests/test_notification_functions.sql`
- **Bash Integration**: `scripts/test-notifications.sh`

### Workflows Relacionados

- `n8n/workflows/11_notification_processor.json`
- `n8n/workflows/12_multi_channel_notifications.json`
- `n8n/workflows/13_discord_notifications.json`

---

**Última Atualização**: 2025-12-15
**Sprint**: 1.3 - Sistema de Notificações Multi-Canal
**Autor**: Claude Code + E2 Soluções Team
**Versão**: 1.0.0
