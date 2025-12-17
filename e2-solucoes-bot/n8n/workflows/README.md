# n8n Workflows - E2 Soluções Bot

> **Sistema de Automação com n8n**
> **Última Atualização**: 2025-12-15
> **Total de Workflows**: 13

---

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Workflows Principais](#workflows-principais)
3. [Workflows de Suporte](#workflows-de-suporte)
4. [Fluxo de Integração](#fluxo-de-integração)
5. [Importação e Configuração](#importação-e-configuração)
6. [Troubleshooting](#troubleshooting)

---

## Visão Geral

### 🎯 Propósito
Os workflows n8n orquestram **toda a lógica** do E2 Soluções Bot:
- Conversação AI com Claude
- RAG (Retrieval-Augmented Generation)
- Agendamento de visitas
- Sincronização CRM (RD Station)
- Sistema de notificações multi-canal
- Handoff para humanos

### 🏗️ Arquitetura
```
WhatsApp (Evolution API)
    ↓
[01] Main WhatsApp Handler
    ↓
[02] AI Agent Conversation ──→ [03] RAG Knowledge Query
    ↓                           [04] Image Analysis (Vision AI)
    ↓
[05] Appointment Scheduler ──→ Google Calendar
    ↓
[06] Appointment Reminders (polling)
    ↓
[11] Notification Processor (polling) ──→ [12] Multi-Channel Router
                                                ↓
                                        ┌───────┼───────┐
                                        ↓       ↓       ↓
                                    [13]    [07]    Evolution
                                  Discord  Email   WhatsApp
```

### 📊 Status dos Workflows

| ID | Nome | Status | Sprint | Polling | Webhook |
|----|------|--------|--------|---------|---------|
| 01 | Main WhatsApp Handler | ✅ Ativo | 1.0 | - | Evolution |
| 02 | AI Agent Conversation | ✅ Ativo | 1.0 | - | Internal |
| 03 | RAG Knowledge Query | ✅ Ativo | 1.1 | - | Internal |
| 04 | Image Analysis | ✅ Ativo | 1.2 | - | Internal |
| 05 | Appointment Scheduler | ✅ Ativo | 1.2 | - | Internal |
| 06 | Appointment Reminders | ✅ Ativo | 1.2 | 5 min | - |
| 07 | Send Email | ✅ Ativo | 1.3 | - | Internal |
| 08 | RD Station Sync | ✅ Ativo | 1.5 | 15 min | - |
| 09 | RD Station Webhook Handler | ✅ Ativo | 1.5 | - | RD Station |
| 10 | Handoff to Human | ✅ Ativo | 1.0 | - | Internal |
| 11 | Notification Processor | ✅ Ativo | 1.3 | 1 min | - |
| 12 | Multi-Channel Notifications | ✅ Ativo | 1.3 | - | Internal |
| 13 | Discord Notifications | ✅ Ativo | 1.3 | - | Internal |

---

## Workflows Principais

### 📱 Workflow 01 - Main WhatsApp Handler

**Arquivo**: `01_main_whatsapp_handler.json`

**Trigger**: Webhook Evolution API (mensagens WhatsApp recebidas)

**Função**: Ponto de entrada para todas as mensagens WhatsApp

**Fluxo**:
1. Recebe webhook do Evolution API
2. Valida estrutura da mensagem
3. Extrai: `phone`, `message_text`, `message_type`
4. Chama Workflow 02 (AI Agent) via webhook interno

**Variáveis Importantes**:
- `EVOLUTION_API_URL`: URL da Evolution API
- `EVOLUTION_API_KEY`: Chave de autenticação

**Debugging**:
```bash
# Testar webhook manualmente
curl -X POST "http://localhost:5678/webhook/whatsapp-incoming" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "key": {"remoteJid": "5562999999999@s.whatsapp.net"},
      "message": {"conversation": "Olá"}
    }
  }'
```

---

### 🤖 Workflow 02 - AI Agent Conversation

**Arquivo**: `02_ai_agent_conversation.json`

**Trigger**: Webhook interno (chamado por Workflow 01)

**Função**: Orquestra conversação com Claude AI e state machine

**Fluxo**:
1. **Load State**: Busca conversa no PostgreSQL
2. **RAG Query**: Chama Workflow 03 para buscar conhecimento
3. **AI Generation**: Envia prompt + contexto para Claude API
4. **State Update**: Atualiza state machine baseado em resposta AI
5. **Data Collection**: Extrai dados estruturados (nome, endereço, etc.)
6. **Response**: Envia resposta via Evolution API
7. **Notifications**: Cria notificações se lead qualificado (Sprint 1.3)

**Estados da Conversa**:
- `greeting`: Saudação inicial
- `identifying_service`: Identificando serviço desejado
- `collecting_data`: Coletando dados específicos do serviço
- `scheduling`: Agendando visita técnica
- `completed`: Conversa concluída
- `handoff_comercial`: Transferido para atendente
- `awaiting_documents`: Aguardando documentos do cliente

**Integração Claude AI**:
```javascript
// System Prompt (resumido)
{
  "role": "Você é assistente virtual da E2 Soluções",
  "capabilities": [
    "Informar sobre serviços (energia solar, subestações, projetos elétricos)",
    "Coletar dados estruturados",
    "Agendar visitas técnicas",
    "Analisar imagens (contas de luz, fotos de instalações)"
  ],
  "behavior": [
    "Conversacional (sem menus numerados)",
    "Perguntar uma coisa por vez",
    "Validar dados antes de avançar"
  ]
}
```

**Integração Sprint 1.3**:
- Ao qualificar lead (`status = 'qualified'`): cria notificação `new_lead`
- Ao agendar visita: cria notificação `appointment_confirmation`

---

### 📚 Workflow 03 - RAG Knowledge Query

**Arquivo**: `03_rag_knowledge_query.json`

**Trigger**: Webhook interno (chamado por Workflow 02)

**Função**: Busca conhecimento relevante via RAG (Retrieval-Augmented Generation)

**Fluxo**:
1. Recebe query do usuário
2. **Generate Embedding**: OpenAI `text-embedding-ada-002` (1536 dims)
3. **Vector Search**: Supabase `match_documents` function
4. **Rank Results**: Cosine similarity > 0.75
5. **Return Context**: Top 5 resultados mais relevantes

**Configuração RAG**:
```yaml
embedding_model: text-embedding-ada-002
dimensions: 1536
similarity_threshold: 0.75
max_results: 5
```

**Knowledge Base**:
- `knowledge/servicos/energia_solar.md`
- `knowledge/servicos/subestacao.md`
- `knowledge/servicos/projetos_eletricos.md`
- `knowledge/servicos/armazenamento_energia.md`
- `knowledge/servicos/analise_laudos.md`

**Debugging**:
```bash
# Testar RAG manualmente
curl -X POST "http://localhost:5678/webhook/rag-query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Quanto custa um sistema de energia solar residencial?"
  }'
```

---

### 📸 Workflow 04 - Image Analysis

**Arquivo**: `04_image_analysis.json`

**Trigger**: Webhook interno (chamado por Workflow 02 quando imagem recebida)

**Função**: Análise de imagens com Claude Vision AI

**Casos de Uso**:
1. **Conta de Luz**: Extrai `kWh consumido`, `valor R$`, `tensão`
2. **Foto de Telhado**: Estima área, tipo de telhado, orientação
3. **Foto de Instalação**: Identifica equipamentos, condições

**Fluxo**:
1. Recebe URL da imagem (Evolution API)
2. Download imagem (base64)
3. **Claude Vision**: Envia imagem + prompt de análise
4. **Extract Data**: Parseia resposta estruturada
5. **Store**: Salva dados extraídos no lead
6. **Response**: Retorna análise para Workflow 02

**Exemplo de Análise**:
```json
{
  "document_type": "conta_de_luz",
  "consumption_kwh": 500,
  "value_brl": 350.00,
  "voltage": "220V",
  "recommended_kwp": 4.5,
  "estimated_roi_months": 36
}
```

---

### 📅 Workflow 05 - Appointment Scheduler

**Arquivo**: `05_appointment_scheduler.json`

**Trigger**: Webhook interno (chamado por Workflow 02 quando agendamento solicitado)

**Função**: Agendar visitas técnicas no Google Calendar

**Fluxo**:
1. Recebe dados: `lead_id`, `preferred_date`, `preferred_time`
2. **Check Availability**: Verifica agenda Google Calendar
3. **Create Event**: Cria evento no calendário
4. **Store Appointment**: Salva no PostgreSQL
5. **Create Reminders**: Chama função SQL `create_appointment_reminders()`
6. **Notifications**: Cria notificação `appointment_confirmation` (Sprint 1.3)
7. **Response**: Retorna confirmação

**Integração Google Calendar**:
```javascript
{
  "summary": "Visita Técnica - {lead_name}",
  "location": "{lead_address}",
  "description": "Serviço: {service_type}\nTelefone: {phone}",
  "start": {"dateTime": "{scheduled_at}"},
  "end": {"dateTime": "{scheduled_at + 1 hour}"},
  "reminders": {
    "useDefault": false,
    "overrides": [
      {"method": "email", "minutes": 1440},  // 24h
      {"method": "popup", "minutes": 120}     // 2h
    ]
  }
}
```

**Integração Sprint 1.3**:
- Cria automaticamente 2 lembretes: `reminder_24h` e `reminder_2h`
- Lembretes agendados para `scheduled_at - 24 hours` e `scheduled_at - 2 hours`

---

### ⏰ Workflow 06 - Appointment Reminders

**Arquivo**: `06_appointment_reminders.json`

**Trigger**: Polling (a cada 5 minutos)

**Função**: Processar lembretes de visitas agendadas

**Fluxo**:
1. **Query Database**: Busca notificações `reminder_24h` e `reminder_2h` com `scheduled_for <= NOW()`
2. **For Each Reminder**:
   - Verifica appointment ainda está `scheduled` (não cancelado)
   - Envia lembrete via canal configurado (WhatsApp/Email)
   - Marca notificação como `sent`
3. **Update Status**: Atualiza status no PostgreSQL

**SQL Query**:
```sql
SELECT *
FROM notifications
WHERE notification_type IN ('reminder_24h', 'reminder_2h')
AND status = 'pending'
AND scheduled_for <= NOW()
ORDER BY priority DESC, scheduled_for ASC
LIMIT 10;
```

**Templates Utilizados**:
- WhatsApp: `templates/whatsapp/lembrete_24h.txt`, `lembrete_2h.txt`
- Email: `templates/emails/lembrete_24h.html`, `lembrete_2h.html`

---

### 📧 Workflow 07 - Send Email

**Arquivo**: `07_send_email.json`

**Trigger**: Webhook interno (chamado por Workflow 12)

**Função**: Enviar emails via SMTP

**Fluxo**:
1. Recebe: `notification_id`, `to_email`, `subject`, `template_name`, `template_variables`
2. **Load Template**: Lê arquivo HTML de `templates/emails/`
3. **Replace Variables**: Substitui `{{ $json.variable }}` por valores reais
4. **Send Email**: SMTP
5. **Update Status**: Marca notificação como `sent` ou `failed`

**Configuração SMTP** (`.env`):
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_SECURE=false
SMTP_USER=bot@e2solucoes.com.br
SMTP_PASSWORD=xxxx xxxx xxxx xxxx
EMAIL_FROM=E2 Soluções Bot <bot@e2solucoes.com.br>
```

**Templates Disponíveis**:
- `novo_lead.html`: Novo lead qualificado
- `lembrete_24h.html`: Lembrete 24h antes da visita
- `lembrete_2h.html`: Lembrete 2h antes da visita
- `confirmacao_agendamento.html`: Confirmação de agendamento
- `apos_visita.html`: Follow-up pós-visita

---

### 🔄 Workflow 08 - RD Station Sync

**Arquivo**: `08_rdstation_sync.json`

**Trigger**: Polling (a cada 15 minutos)

**Função**: Sincronizar leads do PostgreSQL → RD Station CRM

**Fluxo**:
1. **Query Leads**: Busca leads sem `rdstation_contact_id` OR atualizados recentemente
2. **For Each Lead**:
   - **Create/Update Contact**: RD Station API `/platform/contacts`
   - **Create Deal**: RD Station API `/platform/deals`
   - **Update Lead**: Salva `rdstation_contact_id` e `rdstation_deal_id` no PostgreSQL
   - **Log**: Registra sync em `rdstation_sync_log`
3. **Error Handling**: Retry automático em falhas temporárias

**RD Station API**:
```javascript
// Create Contact
POST /platform/contacts
{
  "name": "{lead_name}",
  "email": "{email}",
  "mobile_phone": "{phone}",
  "cf_custom_field_address": "{address}",
  "cf_custom_field_service": "{service_type}",
  "tags": ["lead_bot", "{service_type}"]
}

// Create Deal
POST /platform/deals
{
  "contact_id": "{rdstation_contact_id}",
  "deal_stage_id": "inicial",
  "name": "Lead WhatsApp - {lead_name}",
  "deal_custom_fields": [
    {"custom_field_id": "service", "value": "{service_type}"}
  ]
}
```

---

### 📲 Workflow 09 - RD Station Webhook Handler

**Arquivo**: `09_rdstation_webhook_handler.json`

**Trigger**: Webhook RD Station (eventos de CRM)

**Função**: Sincronização reversa RD Station → PostgreSQL

**Eventos Suportados**:
- `DEAL.WON`: Deal fechado → atualizar `status = 'closed_won'`
- `DEAL.LOST`: Deal perdido → atualizar `status = 'closed_lost'`
- `DEAL.STAGE_UPDATED`: Mudança de estágio → atualizar `stage`
- `CONTACT.UPDATED`: Dados atualizados → sincronizar campos

**Fluxo**:
1. Recebe webhook do RD Station
2. **Validate Signature**: Verifica autenticidade (HMAC-SHA256)
3. **Parse Event**: Extrai `event_type`, `contact_id`, `deal_id`
4. **Find Lead**: Busca lead por `rdstation_contact_id`
5. **Update Database**: Atualiza campos relevantes
6. **Log**: Registra em `rdstation_sync_log`

**Configuração Webhook no RD Station**:
```
URL: https://seu-dominio.com/webhook/rdstation
Events: DEAL.*, CONTACT.UPDATED
```

---

### 👤 Workflow 10 - Handoff to Human

**Arquivo**: `10_handoff_to_human.json`

**Trigger**: Webhook interno (chamado por Workflow 02 quando handoff solicitado)

**Função**: Transferir conversa para atendente humano

**Fluxo**:
1. Recebe: `lead_id`, `conversation_id`, `reason`
2. **Update Conversation**: `current_state = 'handoff_comercial'`, `last_human_handoff_at = NOW()`
3. **Create Notification**: Notificação `handoff_to_human` para Discord (`#alertas`)
4. **Alert Team**: Mensagem no Discord com link WhatsApp Web
5. **Response**: Confirma handoff para cliente

**Integração Sprint 1.3**:
- Cria notificação Discord com prioridade `5` (urgente)
- Alerta aparece no canal `#alertas`
- Inclui: Nome, Telefone, Serviço, Última mensagem, Link WhatsApp Web

**Template Discord Handoff**:
```
🚨 HANDOFF: Atendimento Humano Necessário

👤 Cliente: {lead_name}
📞 Telefone: {phone}
💼 Serviço: {service_type}
💬 Mensagem: "{last_message}"

🔗 Abrir WhatsApp: https://wa.me/{phone_clean}
```

---

### 🔔 Workflow 11 - Notification Processor (Sprint 1.3)

**Arquivo**: `11_notification_processor.json`

**Trigger**: Polling (a cada 1 minuto)

**Função**: Processar notificações pending e failed (com retry)

**Fluxo**:
1. **Query Pending Notifications**:
   ```sql
   SELECT * FROM get_pending_notifications('all', 10);
   ```
2. **Query Failed Notifications** (retry elegíveis):
   ```sql
   SELECT * FROM get_failed_notifications('all', 10);
   ```
3. **For Each Notification**:
   - Validar LGPD: `check_notification_allowed(lead_id, channel)`
   - Chamar Workflow 12 (Multi-Channel Router)
   - Aguardar resposta (sucesso/falha)
   - Atualizar status via `update_notification_status()`
4. **Batch Processing**: Processa até 10 notificações por execução

**Configuração Polling**:
- Intervalo: 1 minuto
- Batch size: 10 (variável `NOTIFICATION_BATCH_SIZE`)
- Retry max: 3 (variável `NOTIFICATION_RETRY_MAX`)

**Retry Logic**:
- Tentativa 1: Imediatamente (já feita ao criar)
- Tentativa 2: Após 1 minuto (próximo polling)
- Tentativa 3: Após 2 minutos
- Se falhar 3 vezes: `status = 'failed'` permanente

---

### 🎯 Workflow 12 - Multi-Channel Notifications (Sprint 1.3)

**Arquivo**: `12_multi_channel_notifications.json`

**Trigger**: Webhook interno (chamado por Workflow 11)

**Função**: Roteador de notificações para canais específicos

**Fluxo**:
1. Recebe: `notification_id`, `channel`, `notification_type`, `template_variables`
2. **Switch on Channel**:
   - `channel = 'discord'` → Chama Workflow 13
   - `channel = 'email'` → Chama Workflow 07
   - `channel = 'whatsapp'` → Envia via Evolution API direto
3. **Return Result**: `{status: 'sent'|'failed', message: '...', error: null}`

**Canais Suportados**:
```yaml
discord:
  workflow: 13_discord_notifications.json
  webhooks:
    - DISCORD_WEBHOOK_LEADS (novo lead)
    - DISCORD_WEBHOOK_APPOINTMENTS (agendamento)
    - DISCORD_WEBHOOK_ALERTS (handoff, erros)

email:
  workflow: 07_send_email.json
  smtp_config: .env (SMTP_*)

whatsapp:
  api: Evolution API
  endpoint: /message/sendText/{instance}
  auth: EVOLUTION_API_KEY
```

**Template Mapping**:
```javascript
{
  "new_lead": {
    "discord": "embed_novo_lead",
    "email": "novo_lead.html",
    "whatsapp": "novo_lead.txt"
  },
  "appointment_confirmation": {
    "email": "confirmacao_agendamento.html",
    "whatsapp": "confirmacao_agendamento.txt"
  },
  "reminder_24h": {
    "email": "lembrete_24h.html",
    "whatsapp": "lembrete_24h.txt"
  },
  "reminder_2h": {
    "email": "lembrete_2h.html",
    "whatsapp": "lembrete_2h.txt"
  },
  "handoff_to_human": {
    "discord": "embed_handoff"
  }
}
```

---

### 💬 Workflow 13 - Discord Notifications (Sprint 1.3)

**Arquivo**: `13_discord_notifications.json`

**Trigger**: Webhook interno (chamado por Workflow 12)

**Função**: Enviar notificações formatadas para Discord

**Fluxo**:
1. Recebe: `notification_id`, `notification_type`, `template_variables`, `webhook_url`
2. **Build Embed**: Cria embed Discord formatado
3. **Send Webhook**: POST para webhook Discord
4. **Return Result**: Sucesso/falha

**Tipos de Embed**:

**Novo Lead (`new_lead`)**:
```json
{
  "embeds": [{
    "title": "🎯 Novo Lead Qualificado",
    "description": "Um novo lead foi qualificado pelo bot WhatsApp",
    "color": 5814783,
    "fields": [
      {"name": "👤 Nome", "value": "{lead_name}", "inline": true},
      {"name": "📞 Telefone", "value": "{phone}", "inline": true},
      {"name": "🔧 Serviço", "value": "{service_name}", "inline": false},
      {"name": "📍 Endereço", "value": "{address}, {city}/{state}", "inline": false}
    ],
    "footer": {"text": "E2 Soluções Bot • Sprint 1.3"},
    "timestamp": "{now}"
  }]
}
```

**Novo Agendamento (`appointment_confirmation`)**:
```json
{
  "embeds": [{
    "title": "📅 Nova Visita Agendada",
    "description": "Visita técnica agendada com sucesso",
    "color": 3066993,
    "fields": [
      {"name": "👤 Cliente", "value": "{lead_name}", "inline": true},
      {"name": "📅 Data/Hora", "value": "{appointment_date} {appointment_time}", "inline": true},
      {"name": "📍 Local", "value": "{address}", "inline": false}
    ]
  }]
}
```

**Handoff (`handoff_to_human`)**:
```json
{
  "embeds": [{
    "title": "🚨 HANDOFF: Atendimento Humano Necessário",
    "description": "Cliente solicitou transferência para atendente",
    "color": 15158332,
    "fields": [
      {"name": "👤 Cliente", "value": "{lead_name}", "inline": true},
      {"name": "📞 Telefone", "value": "{phone}", "inline": true},
      {"name": "💬 Última Mensagem", "value": "{last_message}", "inline": false}
    ],
    "footer": {"text": "🔗 Link: https://wa.me/{phone_clean}"}
  }]
}
```

**Cores Discord**:
- `5814783` (azul): Novo lead
- `3066993` (verde): Agendamento
- `15158332` (vermelho): Alertas/Handoff

---

## Fluxo de Integração

### 🔄 Fluxo Completo: Novo Lead

```
1. Cliente envia "Olá" no WhatsApp
    ↓
2. Evolution API → Webhook → [01] Main Handler
    ↓
3. [01] → [02] AI Agent (webhook interno)
    ↓
4. [02] Claude AI processa mensagem
    ├─→ [03] RAG Query (busca conhecimento)
    └─→ [04] Image Analysis (se imagem enviada)
    ↓
5. [02] Identifica intenção: "quer orçamento energia solar"
    ↓
6. [02] Coleta dados: nome, endereço, consumo kWh
    ↓
7. [02] Atualiza lead status = 'qualified'
    ↓
8. [02] Cria notificação 'new_lead' (Discord)
    ↓
9. [11] Notification Processor (polling 1min)
    ↓
10. [11] → [12] Multi-Channel Router
    ↓
11. [12] → [13] Discord Notifications
    ↓
12. [13] Envia embed Discord (#leads)
    ↓
13. Time comercial visualiza no Discord ✅
```

### 🔄 Fluxo Completo: Agendamento + Lembretes

```
1. Cliente: "Quero agendar visita"
    ↓
2. [02] AI Agent → "Disponibilidade: Quinta 10h, Sexta 14h..."
    ↓
3. Cliente: "Quinta 10h"
    ↓
4. [02] → [05] Appointment Scheduler
    ↓
5. [05] Cria evento Google Calendar
    ↓
6. [05] Salva appointment no PostgreSQL
    ↓
7. [05] Chama função SQL create_appointment_reminders()
    ↓
8. Função cria 2 notificações:
    - reminder_24h (scheduled_for = Quarta 10h)
    - reminder_2h (scheduled_for = Quinta 08h)
    ↓
9. [05] Cria notificação 'appointment_confirmation' (Discord + WhatsApp)
    ↓
10. [11] Processa 'appointment_confirmation' imediatamente
    ↓
11. Cliente recebe confirmação WhatsApp ✅
12. Discord #agendamentos recebe alerta ✅
    ↓
--- 24 HORAS DEPOIS ---
    ↓
13. [06] Appointment Reminders (polling 5min)
    ↓
14. [06] Detecta reminder_24h scheduled_for <= NOW()
    ↓
15. [06] → [12] → [07] Email + Evolution WhatsApp
    ↓
16. Cliente recebe lembrete 24h ✅
    ↓
--- 2 HORAS ANTES ---
    ↓
17. [06] Detecta reminder_2h scheduled_for <= NOW()
    ↓
18. Cliente recebe lembrete 2h ✅
```

---

## Importação e Configuração

### 📥 Importar Workflows no n8n

**Via Interface**:
1. Acesse n8n: `http://localhost:5678`
2. Menu: Workflows → Import from File
3. Selecione arquivo JSON
4. Click "Import"
5. Ativar workflow: Toggle no canto superior direito (verde)

**Via Script** (todos de uma vez):
```bash
# Não há script oficial n8n para import bulk
# Importar manualmente via UI é recomendado
```

**Ordem de Importação** (recomendada):
1. Workflows de base: 01, 02, 03, 04
2. Workflows de suporte: 05, 06, 07, 10
3. Workflows RD Station: 08, 09
4. Workflows notificações: 11, 12, 13

### ⚙️ Configuração de Credentials

**PostgreSQL** (usado por: 02, 05, 06, 08, 11):
```yaml
Credential Type: PostgreSQL
Name: "PostgreSQL - E2 Bot"
Host: postgres-main  # ⚠️ NÃO usar 'localhost'
Port: 5432
Database: e2_solucoes_bot
User: postgres
Password: (do .env)
SSL: disable
```

**Supabase** (usado por: 03):
```yaml
Credential Type: Supabase API
Name: "Supabase - E2 Bot"
Host: {SUPABASE_URL}
Service Role Key: {SUPABASE_SERVICE_KEY}
```

**Anthropic Claude** (usado por: 02, 04):
```yaml
Credential Type: HTTP Header Auth
Name: "Anthropic Claude API"
Header Name: x-api-key
Value: {ANTHROPIC_API_KEY}
```

**Evolution API** (usado por: 01, 02):
```yaml
Credential Type: HTTP Header Auth
Name: "Evolution API"
Header Name: apikey
Value: {EVOLUTION_API_KEY}
```

**Google Calendar** (usado por: 05):
```yaml
Credential Type: Google Calendar OAuth2
Name: "Google Calendar - E2"
Service Account Email: {GOOGLE_SERVICE_ACCOUNT_EMAIL}
Private Key: {GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY}
```

**RD Station** (usado por: 08, 09):
```yaml
Credential Type: HTTP Header Auth
Name: "RD Station CRM"
Header Name: Authorization
Value: Bearer {ACCESS_TOKEN}
# Nota: ACCESS_TOKEN precisa ser refreshed periodicamente
```

### 🔧 Variáveis de Ambiente Necessárias

Adicione ao `docker/.env`:
```bash
# Claude AI
ANTHROPIC_API_KEY=sk-ant-xxx

# Evolution API (WhatsApp)
EVOLUTION_API_URL=https://evolution.xxx
EVOLUTION_API_KEY=xxx
EVOLUTION_INSTANCE_NAME=e2-solucoes-bot

# PostgreSQL
DATABASE_URL=postgresql://postgres:password@postgres-main:5432/e2_solucoes_bot

# Supabase (RAG)
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=xxx

# Google Calendar
GOOGLE_SERVICE_ACCOUNT_EMAIL=xxx@xxx.iam.gserviceaccount.com
GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nxxx\n-----END PRIVATE KEY-----\n"
GOOGLE_CALENDAR_ID=primary

# RD Station CRM
RDSTATION_CLIENT_ID=xxx
RDSTATION_CLIENT_SECRET=xxx
RDSTATION_REFRESH_TOKEN=xxx

# Discord (Sprint 1.3)
DISCORD_WEBHOOK_LEADS=https://discord.com/api/webhooks/xxx
DISCORD_WEBHOOK_APPOINTMENTS=https://discord.com/api/webhooks/xxx
DISCORD_WEBHOOK_ALERTS=https://discord.com/api/webhooks/xxx

# Notificações (Sprint 1.3)
NOTIFICATION_RETRY_MAX=3
NOTIFICATION_BATCH_SIZE=10

# Email (opcional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_SECURE=false
SMTP_USER=bot@e2solucoes.com.br
SMTP_PASSWORD=xxxx
EMAIL_FROM=E2 Soluções Bot <bot@e2solucoes.com.br>
```

---

## Troubleshooting

### Problema: Workflow não executando

**Sintomas**: Workflow ativo (verde) mas não executa

**Diagnóstico**:
1. Verificar triggers:
   - **Polling**: Verificar intervalo configurado
   - **Webhook**: Testar URL manualmente com curl
2. Verificar credentials: n8n UI → Credentials → Test

**Solução**:
```bash
# Para workflows com webhook:
curl -X POST "http://localhost:5678/webhook/{webhook-path}" \
  -H "Content-Type: application/json" \
  -d '{"test": true}'

# Para workflows com polling:
# Executar manualmente: n8n UI → Workflow → Execute Workflow
```

---

### Problema: Erro "Cannot find module"

**Sintomas**: Workflow falha com erro de módulo não encontrado

**Causa**: Dependência npm faltando no n8n

**Solução**:
```bash
# Instalar dependência no container n8n
docker exec -it n8n npm install {package-name}

# Reiniciar n8n
docker restart n8n
```

---

### Problema: PostgreSQL connection refused

**Sintomas**: Workflows falham ao conectar PostgreSQL

**Causa**: Host incorreto nas credentials (usando `localhost` ao invés de `postgres-main`)

**Solução**:
1. n8n UI → Credentials → PostgreSQL
2. Alterar `Host: localhost` para `Host: postgres-main`
3. Test → Save
4. Executar workflow novamente

---

### Problema: Workflow 11 não processa notificações

**Sintomas**: Notificações ficam `pending` indefinidamente

**Diagnóstico**:
```sql
-- Verificar notificações pending
SELECT COUNT(*) FROM notifications WHERE status = 'pending';

-- Verificar última execução Workflow 11
-- n8n UI → Workflow 11 → Executions
```

**Solução**:
1. Verificar que Workflow 11 está ativo (toggle verde)
2. Forçar execução manual: n8n UI → Workflow 11 → Execute Workflow
3. Verificar logs: `docker logs n8n | grep "Notification Processor"`
4. Se erro de credentials PostgreSQL: reconfigurar credential

---

### Problema: Discord não recebe mensagens

**Sintomas**: Workflow 13 executa com sucesso mas sem mensagem Discord

**Diagnóstico**:
```bash
# Testar webhook manualmente
curl -X POST "$DISCORD_WEBHOOK_LEADS" \
  -H "Content-Type: application/json" \
  -d '{"content": "Teste"}'

# Se retornar 404: Webhook foi deletado
```

**Solução**:
1. Recriar webhook no Discord: Server Settings → Integrations → Webhooks
2. Copiar nova URL
3. Atualizar `.env`: `DISCORD_WEBHOOK_LEADS=nova_url`
4. Reiniciar n8n: `docker restart n8n`

---

## 📚 Referências

### Documentação Relacionada
- **Setup Evolution API**: `docs/Setups/SETUP_EVOLUTION_API.md`
- **Setup Discord**: `docs/Setups/SETUP_DISCORD.md`
- **Setup RD Station**: `docs/Setups/SETUP_RDSTATION.md`
- **Sprint 1.3 Validation**: `docs/validation/SPRINT_1.3_VALIDATION.md`

### Links Externos
- **n8n Docs**: https://docs.n8n.io
- **Evolution API Docs**: https://doc.evolution-api.com
- **Discord Webhooks**: https://discord.com/developers/docs/resources/webhook
- **RD Station CRM API**: https://developers.rdstation.com/pt-BR/reference/crm

---

**Última Atualização**: 2025-12-15
**Versão**: 1.3.0 (Sprint 1.3 completo)
**Autor**: E2 Soluções Team
