# E2 Bot - Configuração de Credenciais

> **Versão**: 2.0 | **Última Atualização**: 2026-04-08
> **Objetivo**: Configurar todas as credenciais necessárias para execução dos workflows n8n

---

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Credenciais n8n (Obrigatórias)](#credenciais-n8n-obrigatórias)
3. [Variáveis de Ambiente](#variáveis-de-ambiente)
4. [Validação e Testes](#validação-e-testes)
5. [Troubleshooting](#troubleshooting)

---

## Visão Geral

### Tabela de Credenciais por Workflow

| Workflow | PostgreSQL | Google Calendar | SMTP | RD Station | Evolution API |
|----------|------------|-----------------|------|------------|---------------|
| **WF01** (Handler) | ✅ | ❌ | ❌ | ❌ | ✅ (webhook) |
| **WF02** (AI Agent) | ✅ | ❌ | ❌ | ❌ | ❌ |
| **WF05** (Scheduler) | ✅ | ✅ | ❌ | ✅ (API) | ❌ |
| **WF06** (Availability) | ❌ | ✅ | ❌ | ❌ | ❌ |
| **WF07** (Email) | ✅ | ❌ | ✅ | ❌ | ❌ |
| **WF08** (RD Sync) | ✅ | ❌ | ❌ | ✅ (OAuth) | ❌ |

### Credenciais Consolidadas

**Obrigatórias**:
1. **PostgreSQL** - Banco de dados principal (WF01, WF02, WF05, WF07, WF08)
2. **Google Calendar OAuth2** - Agendamentos (WF05, WF06)
3. **SMTP** - Envio de emails (WF07)

**Opcionais** (mas recomendadas):
4. **RD Station CRM** - Integração CRM (WF05, WF08)
5. **Evolution API** - WhatsApp (WF01 webhook)

---

## Credenciais n8n (Obrigatórias)

### 1. PostgreSQL Database

**Utilizado por**: WF01, WF02, WF05, WF07, WF08
**Credential ID**: `VXA1r8sd0TMIdPvS` (WF01/WF02) e `1` (WF05/WF07/WF08)
**Nome**: `PostgreSQL - E2 Bot`

#### Passo a Passo (n8n UI)

1. **Acessar n8n**: `http://localhost:5678`

2. **Criar Credencial**:
   - Menu lateral → **Credentials**
   - **New credential** → Buscar **"PostgreSQL"**
   - Preencher dados:

```yaml
Host: e2bot-postgres-dev  # Nome do container Docker
Database: e2bot_dev
User: postgres
Password: CoraRosa
Port: 5432
SSL Mode: disable  # Desenvolvimento local
```

3. **Testar Conexão**:
   - Clicar em **"Test"** (botão inferior)
   - Deve retornar: ✅ **"Connection tested successfully"**

4. **Salvar**:
   - Nome da credencial: `PostgreSQL - E2 Bot`
   - Clicar em **"Save"**

#### Configuração Docker

Verificar se PostgreSQL está rodando:

```bash
docker ps | grep postgres
# Deve mostrar: e2bot-postgres-dev ... Up X minutes ... 5432/tcp

# Testar conexão diretamente
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "SELECT 1;"
# Output esperado: 1
```

---

### 2. Google Calendar OAuth2 API

**Utilizado por**: WF05 (Appointment Scheduler), WF06 (Calendar Availability)
**Credential ID**: `VXA1r8sd0TMIdPvS`
**Nome**: `Google Calendar API - E2 Bot`

📘 **Guia completo com passo a passo detalhado**: **[SETUP_GOOGLE_CALENDAR.md](SETUP_GOOGLE_CALENDAR.md)**

#### Resumo de Configuração

**Etapas principais**:
1. Criar projeto no Google Cloud Console
2. Habilitar Google Calendar API
3. Criar OAuth2 Client Credentials
4. Configurar credencial no n8n
5. Autenticar via OAuth2 flow
6. Obter Calendar ID e Credential ID
7. Configurar variáveis de ambiente

#### Quick Setup (Resumido)

**Google Cloud Console**:
1. Criar projeto: "E2 Bot n8n Integration"
2. Habilitar API: Google Calendar API
3. Criar OAuth2 Client ID:
   - Type: Web application
   - Redirect URI: `http://localhost:5678/rest/oauth2-credential/callback`
4. Copiar Client ID e Client Secret

**n8n**:
1. Credentials → New → **Google Calendar OAuth2 API**
2. Preencher Client ID + Secret
3. Connect my account → Autorizar permissões
4. Save com nome: `Google Calendar API - E2 Bot`

**Variáveis de Ambiente** (`docker/.env`):
```bash
GOOGLE_CALENDAR_ID=seu-calendar-id@gmail.com
GOOGLE_CALENDAR_CREDENTIAL_ID=VXA1r8sd0TMIdPvS
GOOGLE_TECHNICIAN_EMAIL=tecnico@e2solucoes.com.br
CALENDAR_TIMEZONE=America/Sao_Paulo
```

**Reiniciar n8n**:
```bash
docker-compose -f docker/docker-compose-dev.yml restart e2bot-n8n-dev
```

#### Validação

```bash
# Teste WF06 (Calendar Availability)
curl -X POST "http://localhost:5678/webhook/calendar-availability" \
  -H "Content-Type: application/json" \
  -d '{"action": "next_dates", "count": 3}' | jq
```

**✅ Deve retornar**: 3 datas disponíveis

#### Troubleshooting Comum

**Erro "invalid_grant"**:
- Refresh Token expirou → Deletar e recriar credencial

**Erro "Calendar not found"**:
- Verificar `GOOGLE_CALENDAR_ID` no docker/.env
- Verificar conta OAuth é a mesma que tem o calendário

📘 **Para detalhes completos, troubleshooting extenso e testes**: Veja **[SETUP_GOOGLE_CALENDAR.md](SETUP_GOOGLE_CALENDAR.md)**

---

### 3. SMTP - Email Service

**Utilizado por**: WF07 (Send Email)
**Credential ID**: `1`
**Nome**: `SMTP - E2 Email`

📘 **Guia completo com passo a passo detalhado**: **[SETUP_EMAIL.md](SETUP_EMAIL.md)**

#### ✅ RECOMENDADO: Port 465 + SSL/TLS

**Gmail SMTP Ports**:
- **Port 465**: SSL/TLS direto → Usar `Secure: true` ✅ **(RECOMENDADO)**
- **Port 587**: STARTTLS → Usar `Secure: false` (configuração alternativa)

**Configuração testada e aprovada**:
```yaml
Port: 465
SSL/TLS: habilitado (marcar checkbox)
Secure: true
```

**Configuração alternativa (Port 587)**:
- Usar apenas se Port 465 não funcionar no seu ambiente
- Requer `Secure: false` (STARTTLS)
- Erro comum se usar Port 587 + SSL/TLS habilitado:
  ```
  error:0A00010B:SSL routines:tls_validate_record_header:wrong version number
  ```

---

#### Quick Setup (Gmail App Password)

1. **Habilitar 2-Step Verification**:
   - https://myaccount.google.com/security → 2-Step Verification → Enable
   - Aguardar 10 minutos para propagação

2. **Criar App Password**:
   - https://myaccount.google.com/security → App passwords
   - App: **Mail** | Device: **Other** ("E2 Bot n8n")
   - **Generate** → Copiar senha de 16 caracteres: `abcd efgh ijkl mnop`

3. **Configurar n8n**:
   - **Credentials** → **New** → **SMTP**
   - Preencher:

```yaml
Credential Name: SMTP - E2 Email
Host: smtp.gmail.com
Port: 465
Secure: true  # ✅ SSL/TLS (MARCAR checkbox)
User: bruno.amv@gmail.com
Password: abcdefghijklmnop  # App Password SEM ESPAÇOS
From Email: E2 Soluções <bruno.amv@gmail.com>
```

**✅ CONFIGURAÇÃO RECOMENDADA**:
- **Port 465** → **Secure: true** (SSL/TLS) ✅
- Marcar checkbox "SSL/TLS" no n8n
- Password SEM ESPAÇOS: `abcdefghijklmnop` ✅ (não `abcd efgh ijkl mnop` ❌)

**Configuração Alternativa**:
- **Port 587** → **Secure: false** (STARTTLS)
- Desmarcar checkbox "SSL/TLS"
- Usar apenas se Port 465 não funcionar

4. **Save**

#### Validação

**Teste via WF07**:
```json
{
  "lead_email": "bruno.amv@gmail.com",
  "lead_name": "Teste SMTP",
  "service_type": "energia_solar",
  "city": "goiania-go",
  "calendar_success": true,
  "scheduled_date": "2026-04-15",
  "scheduled_time_start": "09:00:00",
  "scheduled_time_end": "11:00:00"
}
```

**Verificar**:
- ✅ Node "Send Email" → SUCCESS (verde)
- ✅ Email recebido em `bruno.amv@gmail.com`
- ✅ Database log criado:
  ```sql
  SELECT * FROM email_logs ORDER BY sent_at DESC LIMIT 1;
  ```

#### Troubleshooting Comum

**Erro "Couldn't connect with these settings"**:
- **Causa**: Configuração incorreta de Port + SSL/TLS
- **Solução Recomendada**: Editar credencial → Port 465 + Secure: true ✅
- **Solução Alternativa**: Port 587 + Secure: false (STARTTLS)

**Erro "Authentication failed"**:
- **Causa 1**: App Password com espaços → Remover espaços
- **Causa 2**: 2-Step Verification não habilitada → Habilitar e aguardar 10 min

📘 **Para detalhes completos, troubleshooting extenso e testes**: Veja **[SETUP_EMAIL.md](SETUP_EMAIL.md)**

---

#### Opção 2: SMTP Dedicado (Produção)

Para produção, use serviço SMTP dedicado:

- **SendGrid**: 100 emails/dia grátis
- **Mailgun**: 5.000 emails/mês grátis
- **Amazon SES**: $0.10/1000 emails

Exemplo SendGrid:

```yaml
Host: smtp.sendgrid.net
Port: 587
Secure: false
User: apikey
Password: SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
From Email: bot@e2solucoes.com.br
```

---

### 4. RD Station CRM (Opcional)

**Utilizado por**: WF05 (criar tasks), WF08 (sincronizar contacts/deals)
**Tipo**: HTTP Request com Bearer Token

#### Passo 1: Obter Access Token

1. **RD Station** → Configurações → Integrações
2. **API** → Gerar **Access Token**
3. Copiar token: `xxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

#### Passo 2: Configurar Variáveis de Ambiente

```bash
# Adicionar ao docker/.env
RDSTATION_API_URL=https://api.rdstation.com/platform/v1
RDSTATION_ACCESS_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
RDSTATION_USER_TECNICO=12345  # ID do usuário técnico
RDSTATION_CLIENT_ID=xxxxxxxxxx  # OAuth (WF08)
RDSTATION_CLIENT_SECRET=xxxxxxxxxx  # OAuth (WF08)
RDSTATION_REFRESH_TOKEN=xxxxxxxxxx  # OAuth (WF08)

# IDs de stages e sources
RDSTATION_STAGE_NOVO_LEAD=1
RDSTATION_SOURCE_BOT=2
```

#### Passo 3: Validar

```bash
curl -X GET "https://api.rdstation.com/platform/v1/contacts" \
  -H "Authorization: Bearer $RDSTATION_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

**Nota**: WF05 usa HTTP Request sem credencial n8n (Bearer token direto no header).
WF08 pode usar credencial OAuth2 se preferir autenticação automática.

---

### 5. Evolution API - WhatsApp (Webhook)

**Utilizado por**: WF01 (recebe mensagens via webhook)
**Tipo**: Não requer credencial n8n (autenticação via `apikey` no header HTTP)

#### Configuração Evolution API

A Evolution API está rodando em container separado:

```bash
docker ps | grep evolution
# e2bot-evolution-dev ... Up ... 8080/tcp
```

#### Webhook Configuration

WF01 expõe endpoint webhook:
```
http://e2bot-n8n-dev:5678/webhook/whatsapp-evolution
```

Configurar no Evolution API:

```bash
# Via Evolution API
curl -X POST "http://localhost:8080/webhook/set/e2-solucoes-bot" \
  -H "apikey: ae569043cfa169380c378347f91a1141ea572541d2d1cadbed222db519c8a891" \
  -H "Content-Type: application/json" \
  -d '{
    "webhook": {
      "url": "http://e2bot-n8n-dev:5678/webhook/whatsapp-evolution",
      "enabled": true,
      "webhook_by_events": false,
      "webhook_base64": false,
      "events": [
        "MESSAGES_UPSERT",
        "MESSAGES_UPDATE",
        "MESSAGES_DELETE",
        "SEND_MESSAGE",
        "CONNECTION_UPDATE"
      ]
    }
  }'
```

#### Validação

```bash
# Verificar webhook configurado
curl -s http://localhost:8080/instance/fetchInstances \
  -H "apikey: ae569043cfa169380c378347f91a1141ea572541d2d1cadbed222db519c8a891" | jq '.[] | .webhook'
```

---

## Variáveis de Ambiente

### Arquivo: `docker/.env`

Copiar template e preencher:

```bash
cp docker/.env.dev.example docker/.env
```

### Variáveis Obrigatórias

```bash
# ============================================================================
# PostgreSQL (Container Docker)
# ============================================================================
POSTGRES_DB=e2bot_dev
POSTGRES_USER=postgres
POSTGRES_PASSWORD=e2botpass_dev
POSTGRES_HOST=e2bot-postgres-dev
POSTGRES_PORT=5432

# ============================================================================
# n8n Configuration
# ============================================================================
N8N_HOST=localhost:5678
N8N_PORT=5678
N8N_PROTOCOL=http
N8N_BASIC_AUTH_ACTIVE=false
WEBHOOK_URL=http://localhost:5678/

# ============================================================================
# Google Calendar
# ============================================================================
GOOGLE_CALENDAR_ID=primary  # ou ID específico
CALENDAR_TIMEZONE=America/Sao_Paulo

# ============================================================================
# SMTP / Email
# ============================================================================
SMTP_HOST=smtp.gmail.com
SMTP_PORT=465
SMTP_SECURE=true
SMTP_USER=seu-email@gmail.com
SMTP_PASSWORD=abcd efgh ijkl mnop  # App Password
EMAIL_FROM=E2 Soluções Bot <seu-email@gmail.com>

# ============================================================================
# Evolution API - WhatsApp
# ============================================================================
EVOLUTION_API_URL=http://localhost:8080
EVOLUTION_API_KEY=ae569043cfa169380c378347f91a1141ea572541d2d1cadbed222db519c8a891
EVOLUTION_INSTANCE_NAME=e2-solucoes-bot

# ============================================================================
# n8n Workflow IDs (Internos)
# ============================================================================
WORKFLOW_ID_EMAIL_CONFIRMATION=7  # WF07

# ============================================================================
# OPCIONAL: RD Station CRM
# ============================================================================
RDSTATION_API_URL=https://api.rdstation.com/platform/v1
RDSTATION_ACCESS_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
RDSTATION_USER_TECNICO=12345
RDSTATION_CLIENT_ID=xxxxxxxxxx
RDSTATION_CLIENT_SECRET=xxxxxxxxxx
RDSTATION_REFRESH_TOKEN=xxxxxxxxxx
RDSTATION_STAGE_NOVO_LEAD=1
RDSTATION_SOURCE_BOT=2

# ============================================================================
# OPCIONAL: OpenAI / Supabase (RAG - Sprint 1.1)
# ============================================================================
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
SUPABASE_URL=https://xxxxxxxxxxxxxxxxxxxx.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xxxxxx
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xxxxxx
```

### Carregar Variáveis de Ambiente

```bash
# Docker Compose recarrega automaticamente ao reiniciar
docker-compose -f docker/docker-compose.dev.yml down
docker-compose -f docker/docker-compose.dev.yml up -d

# Verificar se variáveis foram carregadas no n8n
docker exec e2bot-n8n-dev env | grep GOOGLE_CALENDAR_ID
docker exec e2bot-n8n-dev env | grep SMTP_HOST
```

---

## Validação e Testes

### 1. PostgreSQL

```bash
# Teste via Docker
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT COUNT(*) FROM conversations;"

# Deve retornar número de conversas (ou 0 se banco vazio)
```

**n8n Test**:
1. WF01 → Node "Save Message" → Execute Node
2. Verificar output: deve mostrar `affectedRows: 1`

---

### 2. Google Calendar

**n8n Test**:
1. WF06 → Activate
2. Testar endpoint:

```bash
curl -X POST "http://localhost:5678/webhook/calendar-availability" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "next_dates",
    "count": 3
  }'

# Output esperado:
# {
#   "dates": [
#     { "date": "2026-04-09", "dayOfWeek": "Quarta", "available": true },
#     { "date": "2026-04-10", "dayOfWeek": "Quinta", "available": true },
#     { "date": "2026-04-11", "dayOfWeek": "Sexta", "available": true }
#   ]
# }
```

---

### 3. SMTP / Email

**n8n Test** (WF07):
1. Importar WF07
2. Trigger manual com dados de teste:

```json
{
  "lead_email": "seu-email-teste@gmail.com",
  "lead_name": "Teste Manual",
  "service_type": "energia_solar",
  "city": "goiania-go",
  "calendar_success": true,
  "scheduled_date": "2026-04-15",
  "scheduled_time_start": "09:00"
}
```

3. Execute
4. Verificar:
   - ✅ Email recebido na caixa de entrada
   - ✅ Database log em `email_logs` table:
     ```sql
     SELECT * FROM email_logs ORDER BY sent_at DESC LIMIT 1;
     ```

---

### 4. RD Station (Opcional)

```bash
# Testar API
curl -X GET "https://api.rdstation.com/platform/v1/contacts" \
  -H "Authorization: Bearer $RDSTATION_ACCESS_TOKEN" \
  -H "Content-Type: application/json" | jq

# Deve retornar lista de contatos ou {}
```

**n8n Test** (WF08):
1. Ativar WF08 (Schedule Trigger)
2. Execute Manual
3. Verificar logs:
   ```sql
   SELECT * FROM rdstation_sync_log ORDER BY created_at DESC LIMIT 5;
   ```

---

### 5. Evolution API

```bash
# Verificar instância WhatsApp
curl -s http://localhost:8080/instance/fetchInstances \
  -H "apikey: ae569043cfa169380c378347f91a1141ea572541d2d1cadbed222db519c8a891" | jq

# Output esperado:
# {
#   "instance_name": "e2-solucoes-bot",
#   "status": "open",
#   "webhook": {
#     "url": "http://e2bot-n8n-dev:5678/webhook/whatsapp-evolution",
#     "enabled": true
#   }
# }
```

**Test Message Flow**:
1. Enviar mensagem WhatsApp para bot
2. Verificar WF01 executou (Executions → Ver histórico)
3. Verificar database:
   ```sql
   SELECT phone_number, lead_name, current_state
   FROM conversations
   ORDER BY updated_at DESC LIMIT 1;
   ```

---

## Troubleshooting

### Erro: "Credential not found"

**Causa**: ID de credencial no workflow não corresponde ao ID salvo no n8n

**Solução**:
1. n8n → Credentials → Verificar ID da credencial
2. Workflow → Node com erro → Credential dropdown → Re-selecionar credencial
3. Save workflow

---

### Erro: Google Calendar "invalid_grant"

**Causa**: Refresh token expirou ou foi revogado

**Solução**:
1. n8n → Credentials → Google Calendar OAuth2 API
2. Delete credencial
3. Criar nova credencial (refazer OAuth flow)
4. Workflows vão pedir para re-selecionar credencial

---

### Erro: SMTP "Authentication failed"

**Causa 1**: App Password incorreto

**Solução**:
1. Gerar novo App Password no Google
2. Atualizar credencial n8n (sem espaços na senha)

**Causa 2**: 2-Step Verification não habilitada

**Solução**:
1. Google Account → Security → Enable 2-Step Verification
2. Aguardar 10 minutos para propagação
3. Criar App Password

---

### Erro: PostgreSQL "Connection refused"

**Causa**: Container PostgreSQL não está rodando

**Solução**:
```bash
# Verificar status
docker ps | grep postgres

# Se não estiver rodando
docker-compose -f docker/docker-compose.dev.yml up -d e2bot-postgres-dev

# Verificar logs
docker logs e2bot-postgres-dev
```

---

### Erro: Evolution API Webhook não recebe mensagens

**Causa**: URL do webhook incorreta ou n8n não acessível

**Solução**:
1. Verificar webhook configurado:
   ```bash
   curl -s http://localhost:8080/instance/fetchInstances \
     -H "apikey: $EVOLUTION_API_KEY" | jq '.[].webhook'
   ```

2. Reconfigurar webhook:
   ```bash
   curl -X POST "http://localhost:8080/webhook/set/e2-solucoes-bot" \
     -H "apikey: $EVOLUTION_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"webhook": {"url": "http://e2bot-n8n-dev:5678/webhook/whatsapp-evolution", "enabled": true}}'
   ```

3. Testar webhook manualmente:
   ```bash
   curl -X POST "http://localhost:5678/webhook/whatsapp-evolution" \
     -H "Content-Type: application/json" \
     -d '{"key": "test"}'
   ```

---

### Erro: `$env.GOOGLE_CALENDAR_ID` undefined

**Causa**: Variável de ambiente não carregada no container n8n

**Solução**:
1. Verificar `docker/.env` contém a variável
2. Restart container:
   ```bash
   docker-compose -f docker/docker-compose.dev.yml restart e2bot-n8n-dev
   ```
3. Verificar variável dentro do container:
   ```bash
   docker exec e2bot-n8n-dev env | grep GOOGLE_CALENDAR_ID
   ```

---

## Checklist de Validação Final

Antes de colocar workflows em produção, validar:

- [ ] **PostgreSQL**: Conexão testada com sucesso
- [ ] **Google Calendar**: OAuth2 autenticado + Calendar ID configurado
- [ ] **SMTP**: Email de teste enviado e recebido
- [ ] **Evolution API**: Webhook configurado + instância WhatsApp conectada
- [ ] **RD Station** (opcional): Access Token válido + API respondendo
- [ ] **Variáveis de Ambiente**: Todas configuradas em `docker/.env`
- [ ] **n8n Workflows**: Importados e credenciais vinculadas
- [ ] **Database Schema**: Tabelas criadas (conversations, appointments, email_logs)
- [ ] **Teste E2E**: Mensagem WhatsApp → WF01 → WF02 → WF05 → WF07 → Email recebido

---

## Referências

- [n8n Credentials Documentation](https://docs.n8n.io/credentials/)
- [Google Calendar API Setup](https://developers.google.com/calendar/api/guides/auth)
- [Gmail SMTP Settings](https://support.google.com/mail/answer/7126229)
- [RD Station API Docs](https://developers.rdstation.com/)
- [Evolution API Docs](https://doc.evolution-api.com/)

---

**Última Atualização**: 2026-04-08
**Mantido por**: E2 Soluções Dev Team
