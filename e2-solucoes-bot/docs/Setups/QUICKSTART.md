# 🚀 E2 Bot - Quick Start Guide

> **Versão**: 3.0 | **Atualização**: 2026-04-08
> **Objetivo**: Iniciar sistema E2 Bot completo do zero em 30-45 minutos

---

## 📋 Índice

1. [Pré-requisitos](#pré-requisitos)
2. [Fluxo de Setup](#fluxo-de-setup)
3. [Passo 1: Iniciar Infraestrutura Docker](#passo-1-iniciar-infraestrutura-docker)
4. [Passo 2: Configurar Credenciais n8n](#passo-2-configurar-credenciais-n8n)
5. [Passo 3: Importar Workflows](#passo-3-importar-workflows)
6. [Passo 4: Configurar Evolution API (Opcional)](#passo-4-configurar-evolution-api-opcional)
7. [Validação Final](#validação-final)
8. [Próximos Passos](#próximos-passos)

---

## Pré-requisitos

**Software Obrigatório**:
- ✅ Docker 20.10+ instalado
- ✅ Docker Compose 2.0+ instalado
- ✅ Git (para clonar repositório)

**Verificar instalação**:
```bash
docker --version  # Deve mostrar 20.10+
docker-compose --version  # Deve mostrar 2.0+
```

**Credenciais Externas** (obter antes de começar):
- Google Calendar OAuth2 (Client ID + Secret)
- SMTP Email (Gmail App Password ou SendGrid)
- RD Station Access Token (opcional)

📘 **Guia completo de credenciais**: `SETUP_CREDENTIALS.md`

---

## Fluxo de Setup

```
┌─────────────────────────────────────────────┐
│ 1️⃣ Iniciar Infraestrutura Docker           │
│    ├─ PostgreSQL                            │
│    ├─ n8n                                   │
│    └─ nginx (templates)                     │
│                                             │
│ 2️⃣ Configurar Credenciais n8n              │
│    ├─ PostgreSQL connection                 │
│    ├─ Google Calendar OAuth2                │
│    ├─ SMTP email                            │
│    └─ RD Station (opcional)                 │
│                                             │
│ 3️⃣ Importar Workflows                      │
│    ├─ WF01: WhatsApp Handler                │
│    ├─ WF02: AI Agent                        │
│    ├─ WF05: Appointment Scheduler           │
│    ├─ WF06: Calendar Availability           │
│    └─ WF07: Send Email                      │
│                                             │
│ 4️⃣ Configurar Evolution API (Opcional)     │
│    ├─ Iniciar containers WhatsApp           │
│    ├─ Conectar instância WhatsApp           │
│    └─ Configurar webhook para n8n           │
│                                             │
│ 5️⃣ Validação Final                         │
│    └─ Teste end-to-end completo             │
└─────────────────────────────────────────────┘
```

**Tempo Estimado**: 30-45 minutos (primeira vez)

---

## Passo 1: Iniciar Infraestrutura Docker

### 1.1 - Preparar Ambiente

**Clone o repositório** (se ainda não fez):
```bash
git clone https://github.com/seu-usuario/e2-solucoes-bot.git
cd e2-solucoes-bot
```

**Configurar variáveis de ambiente**:
```bash
# Copiar template

############# CUIDADO SE JA TIVER CONFIGURADO.
cp docker/.env.dev.example docker/.env

# Editar com suas credenciais
nano docker/.env
# OU
vim docker/.env
```

**Variáveis obrigatórias mínimas**:
```bash
# PostgreSQL (já vem configurado no template)
POSTGRES_DB=e2bot_dev
POSTGRES_USER=postgres
POSTGRES_PASSWORD=CHANGE_ME_TO_STRONG_PASSWORD

# n8n (já vem configurado)
N8N_HOST=localhost:5678
N8N_PORT=5678

# Google Calendar (VOCÊ PRECISA OBTER)
GOOGLE_CALENDAR_ID=primary  # ou seu calendar ID

# SMTP (VOCÊ PRECISA OBTER)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=465
SMTP_USER=seu-email@gmail.com
SMTP_PASSWORD=CHANGE_ME_TO_STRONG_PASSWORD  # App Password
```

📘 **Como obter credenciais**: `SETUP_CREDENTIALS.md` seções 2 e 3

---

### 1.2 - Iniciar Containers Essenciais

**Iniciar PostgreSQL + n8n + nginx**:
```bash
cd docker
docker-compose -f docker-compose.dev.yml up -d e2bot-postgres-dev e2bot-n8n-dev e2bot-templates-dev
```

**Aguardar inicialização** (30 segundos):
```bash
sleep 30
```

**Verificar status**:
```bash
docker-compose -f docker-compose.dev.yml ps
```

**✅ Resultado esperado**:
```
NAME                 STATUS    PORTS
e2bot-postgres-dev   Up        0.0.0.0:5432->5432/tcp
e2bot-n8n-dev        Up        0.0.0.0:5678->5678/tcp
e2bot-templates-dev  Up        0.0.0.0:8081->80/tcp
```

**❌ Se algum container está "Restarting"**:
```bash
# Ver logs do container problemático
docker logs e2bot-postgres-dev
docker logs e2bot-n8n-dev

# Causas comuns:
# - Porta já em uso (5432 ou 5678)
# - .env com erro de sintaxe
```

---

### 1.3 - Validar Infraestrutura

**Testar PostgreSQL**:
```bash
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "SELECT version();"
```

**✅ Deve mostrar**: Versão PostgreSQL 15.x

**Verificar schema criado automaticamente**:
```bash
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "\dt"
```

**✅ Deve mostrar**: 7 tabelas (conversations, messages, leads, appointments, email_logs, chat_memory, rdstation_sync_log)

**Testar n8n**:
```bash
curl -I http://localhost:5678
```

**✅ Deve retornar**: HTTP 200 OK ou redirecionamento

**Acessar n8n no navegador**:
```
http://localhost:5678
```

**✅ Deve carregar**: Interface n8n sem autenticação (desenvolvimento)

---

**📋 Referência rápida - Deploy do schema**:

O schema PostgreSQL é deployado **automaticamente** na primeira inicialização do container via:
- `database/init-e2bot-dev.sh` - Cria database `e2bot_dev`
- `database/schema.sql` - Cria 7 tabelas + índices + triggers + tabela email_logs
- `database/appointment_functions.sql` - Funções de agendamento

Se o database não foi criado, veja troubleshooting em `DEPLOY_SQL.md`

---

## Passo 2: Configurar Credenciais n8n

### 2.1 - Criar Credencial PostgreSQL

**🚨 PRÉ-REQUISITO**: PostgreSQL container rodando (Passo 1.2 concluído) + Database `e2bot_dev` criada automaticamente

**Verificar se database existe**:
```bash
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "\dt" | head -5
```

**✅ Deve mostrar**: Lista de 7 tabelas (conversations, messages, leads, appointments, email_logs, chat_memory, rdstation_sync_log)

**❌ Se mostrar erro "database e2bot_dev does not exist"**:
```bash
# O schema é criado automaticamente na primeira vez que o container inicia
# Se você já tinha um container antigo, precisa recriar:

cd docker
docker-compose -f docker-compose-dev.yml down -v  # Remove volumes antigos
docker-compose -f docker-compose-dev.yml up -d e2bot-postgres-dev
sleep 30  # Aguardar criação automática do database

# Verificar novamente
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "\dt"
```

📘 **Detalhes**: Veja `DEPLOY_SQL.md` para troubleshooting completo

---

**Configurar credencial no n8n**:

1. **Acessar n8n**: http://localhost:5678

2. **Menu lateral** → **Credentials**

3. **New credential** → Buscar **"Postgres"**

4. **Preencher**:
   ```yaml
   Credential Name: PostgreSQL - E2 Bot
   Host: e2bot-postgres-dev  # Nome do container (NÃO usar localhost!)
   Database: e2bot_dev        # Database correto (NÃO e2_bot!)
   User: postgres
   Password: CoraRosa         # Padrão ou conforme docker/.env
   Port: 5432
   SSL Mode: disable
   ```

5. **Testar**: Clicar em **"Test"**
   - ✅ **"Connection successful"** → Tudo certo!
   - ❌ **"Connection refused"** → Você usou `localhost` ao invés de `e2bot-postgres-dev`
   - ❌ **"Authentication failed"** → Senha incorreta (verificar docker/.env)
   - ❌ **"database e2bot_dev does not exist"** → Seguir instruções acima para recriar container

6. **Save**

💡 **Por quê `e2bot-postgres-dev` e não `localhost`?**
- n8n está **dentro do Docker**
- `localhost` = próprio container n8n (não funciona)
- `e2bot-postgres-dev` = nome do container PostgreSQL na mesma rede Docker ✅

💡 **Por quê `e2bot_dev` e não `e2_bot`?**
- O docker-compose cria automaticamente o database `e2bot_dev`
- Scripts de inicialização usam `e2bot_dev`
- Se tentar usar `e2_bot`, n8n não conectará

---

### 2.2 - Criar Credencial Google Calendar

**🚨 PRÉ-REQUISITO**: OAuth2 Client ID + Secret (obter em Google Cloud Console)

📘 **Guia completo**: **[SETUP_GOOGLE_CALENDAR.md](SETUP_GOOGLE_CALENDAR.md)**

**Resumo rápido**:

1. **Criar projeto no Google Cloud Console** e habilitar Google Calendar API

2. **Criar OAuth2 Client ID**:
   - Application type: Web application
   - Redirect URI: `http://localhost:5678/rest/oauth2-credential/callback`

3. **n8n** → **Credentials** → **New** → **Google Calendar OAuth2 API**

4. **Preencher**:
   ```yaml
   Client ID: xxxxxxxx.apps.googleusercontent.com
   Client Secret: GOCSPX-xxxxxxxxxxxxx
   Scope: https://www.googleapis.com/auth/calendar
   ```

5. **Connect my account**:
   - Pop-up do Google abre
   - Selecionar conta com acesso ao calendário
   - Autorizar permissões
   - n8n recebe Access Token + Refresh Token

6. **Save** com nome: `Google Calendar API - E2 Bot`

**Obter Calendar ID**:
1. Google Calendar → Configurações → Calendário específico → "Integrate calendar"
2. Copiar "Calendar ID"
3. Adicionar ao `docker/.env`:
   ```bash
   GOOGLE_CALENDAR_ID=seu-calendar-id@gmail.com
   GOOGLE_CALENDAR_CREDENTIAL_ID=VXA1r8sd0TMIdPvS  # ID da credencial n8n
   ```
4. Reiniciar n8n para carregar variável:
   ```bash
   docker-compose -f docker/docker-compose-dev.yml restart e2bot-n8n-dev
   ```

💡 **Detalhes completos**: Veja **[SETUP_GOOGLE_CALENDAR.md](SETUP_GOOGLE_CALENDAR.md)** para instruções passo a passo com screenshots e troubleshooting

---

### 2.3 - Criar Credencial SMTP

**🚨 PRÉ-REQUISITO**: Gmail App Password (obter em Google Account → Security)

📘 **Guia completo**: **[SETUP_EMAIL.md](SETUP_EMAIL.md)**

**✅ RECOMENDADO**: Port 465 + SSL/TLS (configuração testada e aprovada)

**Erro comum se usar Port 587**: Port 587 + SSL/TLS habilitado causa:
```
error:0A00010B:SSL routines:tls_validate_record_header:wrong version number
```

**Solução**: Port 465 + SSL/TLS ✅ | Alternativa: Port 587 + `Secure: false` (STARTTLS)

---

**Resumo rápido - Gmail App Password**:

1. **Habilitar 2-Step Verification**:
   - https://myaccount.google.com/security → 2-Step Verification → Enable
   - Aguardar 10 minutos

2. **Criar App Password**:
   - https://myaccount.google.com/security → App passwords
   - App: Mail | Device: Other ("E2 Bot n8n")
   - Copiar senha de 16 caracteres: `abcd efgh ijkl mnop`

3. **n8n** → **Credentials** → **New** → **SMTP**

4. **Preencher**:
   ```yaml
   Credential Name: SMTP - E2 Email
   Host: smtp.gmail.com
   Port: 465
   Secure: true  # ✅ SSL/TLS (MARCAR checkbox)
   User: bruno.amv@gmail.com
   Password: abcdefghijklmnop  # App Password SEM ESPAÇOS
   From Email: E2 Soluções <bruno.amv@gmail.com>
   ```

5. **Save**

6. **Verificar configuração**:
   - Port 465 + Secure: true (SSL/TLS) ✅
   - Password sem espaços ✅
   - Alternativa: Port 587 + Secure: false (apenas se Port 465 não funcionar)

**Testar após importar WF07**: Execute workflow com dados de teste para verificar envio

💡 **Detalhes completos com troubleshooting**: Veja **[SETUP_EMAIL.md](SETUP_EMAIL.md)**

---

### 2.4 - Criar Credencial RD Station (Opcional)

**🚨 Opcional**: Apenas se usar integração CRM

📘 **Guia completo**: `SETUP_CREDENTIALS.md` seção 4

**Passo rápido**:
1. RD Station → Configurações → Integrações → API → Gerar Access Token
2. Copiar token para `docker/.env`:
   ```bash
   RDSTATION_API_URL=https://api.rdstation.com/platform/v1
   RDSTATION_ACCESS_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```
3. Reiniciar n8n:
   ```bash
   docker-compose -f docker/docker-compose.dev.yml restart e2bot-n8n-dev
   ```

---

## Passo 3: Importar Workflows

### 3.1 - Importar Workflows Essenciais

**Workflows obrigatórios**:
- ✅ **WF01**: `01_main_whatsapp_handler_V2.8.3_NO_LOOP.json`
- ✅ **WF02**: `02_ai_agent_conversation_V76_PROACTIVE_UX.json` (ou V74.1.2 prod)
- ✅ **WF05**: `05_appointment_scheduler_v7_hardcoded_values.json` (ou v3.6 prod)
- ✅ **WF06**: `06_calendar_availability_service_v1.json`
- ✅ **WF07**: `07_send_email_v13_insert_select.json`

**Workflow opcional**:
- ⏸️ **WF08**: `08_rdstation_sync.json` (apenas se usar RD Station)

---

### 3.2 - Processo de Importação

**Para cada workflow**:

1. **n8n** → **Workflows** → **Import from File**

2. **Selecionar arquivo** da pasta `n8n/workflows/`

3. **Workflow importado** → Aparecerá na lista com status "Inactive"

4. **Abrir workflow** → Clicar no nome do workflow

5. **Verificar nodes com erro** (ícone vermelho ⚠️)
   - Geralmente são nodes PostgreSQL, Google Calendar ou SMTP

6. **Para cada node com erro**:
   - Clicar no node
   - Seção "Credential to connect with"
   - Dropdown: Selecionar credencial criada no Passo 2
   - Exemplo: Node PostgreSQL → Selecionar "PostgreSQL - E2 Bot"

7. **Salvar workflow** (Ctrl+S ou botão Save)

8. **Ativar workflow**:
   - Toggle "Inactive" (cinza) → "Active" (verde)
   - ✅ Status muda para **"Active"**

---

### 3.3 - Mapeamento de Credenciais por Workflow

| Workflow | Nodes PostgreSQL | Google Calendar | SMTP | HTTP Request |
|----------|------------------|-----------------|------|--------------|
| **WF01** | Save Message | ❌ | ❌ | ❌ |
| **WF02** | Get State, Update State, Save Messages (7 nodes) | ❌ | ❌ | ❌ |
| **WF05** | Get Appointment, Update Appointment, Log | Create Event | ❌ | RD Station (opcional) |
| **WF06** | ❌ | Get Events, Get Calendars | ❌ | ❌ |
| **WF07** | Insert Email Log | ❌ | Send Email | HTTP (templates) |

**Dica**: Use Ctrl+F no workflow para buscar nodes por tipo (ex: "Postgres", "Google Calendar")

---

### 3.4 - Validação dos Workflows

**Teste rápido** (executar manualmente cada workflow):

1. **WF06** (Calendar Availability):
   - Ativar workflow
   - Testar endpoint:
     ```bash
     curl -X POST "http://localhost:5678/webhook/calendar-availability" \
       -H "Content-Type: application/json" \
       -d '{"action": "next_dates", "count": 3"}' | jq
     ```
   - ✅ Deve retornar 3 datas disponíveis

2. **WF07** (Send Email):
   - Executar manualmente com dados de teste
   - Verificar email recebido
   - Verificar registro em `email_logs` database table

---

## Passo 4: Configurar Evolution API (Opcional)

**🚨 Opcional**: Apenas se quiser integração WhatsApp

**Se você NÃO precisa de WhatsApp agora**, pule para [Passo 5: Validação Final](#passo-5-validação-final)

---

**Se você QUER WhatsApp**:

📘 **Siga o guia dedicado**: **[QUICKSTART_EVOLUTION_API.md](QUICKSTART_EVOLUTION_API.md)**

Este guia específico cobre:
- Iniciar containers Evolution API (PostgreSQL + Redis + API)
- Aplicar workaround Issue #1474
- Gerar QR Code e conectar WhatsApp
- Configurar webhook para n8n
- Testar envio/recebimento de mensagens

**Tempo estimado**: 10-15 minutos

**Após completar**, volte aqui para **Passo 5: Validação Final**

---

## Passo 5: Validação Final

### 5.1 - Checklist de Infraestrutura

```bash
# Verificar todos containers rodando
docker-compose -f docker/docker-compose.dev.yml ps
```

**✅ Resultado esperado**:
```
e2bot-postgres-dev   Up
e2bot-n8n-dev        Up
e2bot-templates-dev  Up
```

**Se configurou Evolution API**:
```
e2bot-evolution-dev          Up
e2bot-evolution-postgres-dev Up
e2bot-evolution-redis-dev    Up
```

---

### 5.2 - Checklist de Credenciais

**n8n** → **Credentials** → Verificar:
- [ ] **PostgreSQL - E2 Bot** (testada com sucesso)
- [ ] **Google Calendar API** (OAuth2 conectado)
- [ ] **SMTP - E2 Email** (configurada)
- [ ] **Evolution API** (se configurou WhatsApp)

---

### 5.3 - Checklist de Workflows

**n8n** → **Workflows** → Verificar todos **ATIVOS**:
- [ ] **01_main_whatsapp_handler** → Status: Active ✅
- [ ] **02_ai_agent_conversation** → Status: Active ✅
- [ ] **05_appointment_scheduler** → Status: Active ✅
- [ ] **06_calendar_availability** → Status: Active ✅
- [ ] **07_send_email** → Status: Active ✅

---

### 5.4 - Teste End-to-End (Sem WhatsApp)

**Teste direto de agendamento** (simulando WF02):

1. **Criar lead manualmente no banco**:
   ```sql
   -- Via psql ou DBeaver
   INSERT INTO conversations (phone_number, lead_name, service_type, current_state)
   VALUES ('5561981755748', 'Teste Manual', 'energia_solar', 'confirmation');
   ```

2. **Triggerar WF05** (Appointment Scheduler):
   ```bash
   # Via n8n UI: Workflow WF05 → Execute Workflow
   # Usar execution ID de teste
   ```

3. **Verificar**:
   - ✅ Evento criado no Google Calendar
   - ✅ Email enviado (verificar inbox)
   - ✅ Registro em `email_logs` database table

---

### 5.5 - Teste End-to-End (Com WhatsApp)

**Se você configurou Evolution API**:

1. **Enviar mensagem WhatsApp** para número conectado:
   ```
   Oi
   ```

2. **Você deve receber**:
   ```
   Olá! Bem-vindo à E2 Soluções! 👋

   Escolha um serviço:
   1️⃣ Energia Solar
   2️⃣ Subestação
   3️⃣ Projetos Elétricos
   4️⃣ Armazenamento de Energia
   5️⃣ Análise e Laudos
   ```

3. **Responder**: `1`

4. **Bot deve continuar conversação**, pedindo:
   - Nome
   - Telefone
   - Email
   - Cidade
   - Confirmação
   - Data/horário (WF02 V76 com seleção proativa)

5. **Após confirmação**:
   - ✅ Evento criado no Google Calendar
   - ✅ Email de confirmação recebido
   - ✅ Dados salvos no banco

**✅ Teste completo end-to-end funcionando!**

---

## Próximos Passos

### ✅ Ambiente Completo Configurado!

Você completou:
- ✅ Infraestrutura Docker rodando
- ✅ Credenciais n8n configuradas
- ✅ Workflows importados e ativos
- ✅ Evolution API (se configurou WhatsApp)

---

### 🎯 Roadmap de Evolução

**Fase 1 - Core Workflows** (✅ VOCÊ ESTÁ AQUI):
- Workflows WF01-WF07 operacionais
- Integração WhatsApp + Google Calendar + Email

**Fase 2 - Deploy WF02 V76** (Próximo):
- WF02 V76: UX proativa com seleção de datas/horários
- Deploy canário: 20% → 50% → 80% → 100%
- 📘 **Guia**: `docs/WF02_V76_DEPLOYMENT_SUMMARY.md`

**Fase 3 - Otimizações**:
- WF05 V7: Validação de horários comerciais
- WF07 V13: Email templates com INSERT...SELECT
- Performance tuning PostgreSQL

**Fase 4 - Integrações Avançadas**:
- WF08: Sincronização RD Station CRM
- Anthropic Claude API (substituir/complementar OpenAI)
- Google Drive para armazenamento de documentos

---

### 📚 Documentação Relacionada

**Configuração**:
- `SETUP_CREDENTIALS.md` - Guia completo de credenciais
- `QUICKSTART_EVOLUTION_API.md` - Setup WhatsApp específico
- `SETUP_GOOGLE_CALENDAR.md` - Detalhes Google Calendar
- `SETUP_EMAIL.md` - Configuração avançada SMTP

**Workflows**:
- `WF02_V76_IMPLEMENTATION_GUIDE.md` - WF02 V76 UX proativa
- `WF06_CALENDAR_AVAILABILITY_SERVICE.md` - Microservice calendário
- `BUGFIX_WF07_V13_INSERT_SELECT_FIX.md` - Email workflow

**Arquitetura**:
- `ARCHITECTURE.md` - Visão geral do sistema
- `CLAUDE.md` - Contexto completo do projeto

---

## 🐛 Troubleshooting

### Container "Restarting"

```bash
# Ver logs
docker logs e2bot-postgres-dev
docker logs e2bot-n8n-dev

# Causas comuns:
# 1. Porta em uso (5432, 5678, 8080)
lsof -i :5432
lsof -i :5678

# 2. .env com erro de sintaxe
cat docker/.env | grep -E "^[^#].*=.*"

# 3. Falta de permissão
sudo chmod 666 /var/run/docker.sock
```

---

### Credencial PostgreSQL "Connection refused"

**Causa**: Usou `localhost` ao invés do nome do container

**Solução**: Editar credencial no n8n:
- Host: `e2bot-postgres-dev` ✅ (NÃO `localhost` ❌)

---

### Workflow retorna "403 Forbidden"

**Causa**: Workflow está **inativo**

**Solução**:
1. n8n → Workflows
2. Abrir workflow
3. Toggle "Inactive" → "Active"
4. ✅ Status verde

---

### Email não envia (WF07)

**Causa 1**: SMTP credencial incorreta

**Solução**: Gmail App Password sem espaços:
- ✅ `abcdefghijklmnop`
- ❌ `abcd efgh ijkl mnop`

**Causa 2**: 2-Step Verification não habilitada

**Solução**: Google Account → Security → Enable 2-Step → Aguardar 10 min → Criar App Password

---

### Google Calendar retorna "invalid_grant"

**Causa**: Refresh Token expirou

**Solução**:
1. n8n → Credentials → Google Calendar OAuth2 API
2. Delete credencial
3. Criar nova (refazer OAuth flow)
4. Workflows re-selecionar credencial

---

## ✅ Checklist Final

Antes de considerar setup completo:

- [ ] Todos containers "Up" (não "Restarting")
- [ ] n8n acessível em http://localhost:5678
- [ ] PostgreSQL testado com sucesso (psql ou n8n credential test)
- [ ] 3 credenciais criadas: PostgreSQL, Google Calendar, SMTP
- [ ] 5 workflows importados e ativos (WF01, WF02, WF05, WF06, WF07)
- [ ] WF06 responde com datas disponíveis (teste curl)
- [ ] WF07 envia email de teste com sucesso
- [ ] Se WhatsApp: Evolution API conectada + webhook configurado
- [ ] Teste E2E completo funcionando

**Tudo OK?** 🎉 **Setup completo com sucesso!**

---

**Última Atualização**: 2026-04-08
**Mantido por**: E2 Soluções Dev Team
**Próximo Guia**: `QUICKSTART_EVOLUTION_API.md` (WhatsApp) ou `WF02_V76_DEPLOYMENT_SUMMARY.md` (Deploy V76)
