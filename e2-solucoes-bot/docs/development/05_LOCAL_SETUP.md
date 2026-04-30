# Configuração do Ambiente Local

> **Objetivo**: Configurar ambiente de desenvolvimento local completo
> **Tempo estimado**: 30-60 minutos
> **Última atualização**: 2026-04-29

## Pré-requisitos

### Software Necessário

```bash
# 1. Docker e Docker Compose
docker --version  # >= 20.10
docker compose version  # >= 2.0

# 2. Node.js (para scripts auxiliares)
node --version  # >= 18.x

# 3. PostgreSQL Client (psql)
psql --version  # >= 14.x

# 4. Git
git --version  # >= 2.x

# 5. curl e jq (para testes de API)
curl --version
jq --version
```

### Portas Necessárias

```bash
# Verificar portas disponíveis
lsof -i :5678  # n8n
lsof -i :5432  # PostgreSQL
lsof -i :8080  # Evolution API
lsof -i :80    # nginx

# Liberar portas se necessário
sudo kill $(lsof -t -i :5678)
```

---

## 1. Clonar Repositório

```bash
# Clone do repositório
git clone <repository-url> e2-solucoes-bot
cd e2-solucoes-bot

# Verificar estrutura
tree -L 2 -d
# Esperado:
# .
# ├── docker/          # Docker configs
# ├── docs/            # Documentação
# ├── n8n/             # Workflows
# ├── nginx/           # nginx configs
# ├── scripts/         # Scripts auxiliares
# └── migrations/      # DB migrations
```

---

## 2. Configurar Variáveis de Ambiente

### 2.1. Criar Arquivo .env

```bash
# Copiar template
cp .env.example .env

# Editar com suas credenciais
nano .env
```

### 2.2. Configurações Essenciais

```bash
# PostgreSQL
POSTGRES_USER=postgres
POSTGRES_PASSWORD=sua_senha_segura_aqui
POSTGRES_DB=e2bot_dev
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# n8n
N8N_BASIC_AUTH_ACTIVE=true
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=sua_senha_n8n_aqui
N8N_HOST=localhost
N8N_PORT=5678
N8N_PROTOCOL=http

# Evolution API
EVOLUTION_API_KEY=sua_api_key_evolution_aqui
EVOLUTION_INSTANCE_NAME=e2bot-instance
EVOLUTION_URL=http://evolution-api:8080

# Claude AI
CLAUDE_API_KEY=sk-ant-api03-...sua_chave_anthropic_aqui...
CLAUDE_MODEL=claude-3-5-sonnet-20241022

# Gmail SMTP (n8n 2.14.2 compatible)
GMAIL_SMTP_USER=seu_email@gmail.com
GMAIL_SMTP_PASSWORD=sua_senha_app_gmail_aqui
GMAIL_SMTP_HOST=smtp.gmail.com
GMAIL_SMTP_PORT=465
GMAIL_SMTP_SECURE=true  # SSL/TLS (não STARTTLS!)

# Google Calendar OAuth
GOOGLE_CALENDAR_CLIENT_ID=seu_client_id_aqui
GOOGLE_CALENDAR_CLIENT_SECRET=seu_client_secret_aqui
GOOGLE_CALENDAR_REFRESH_TOKEN=seu_refresh_token_aqui

# Timezone
TZ=America/Sao_Paulo

# Ambiente
NODE_ENV=development
```

### 2.3. Obter Credenciais

#### Gmail App Password

```bash
# 1. Acessar Google Account Security
# https://myaccount.google.com/security

# 2. Ativar 2-Step Verification

# 3. Gerar App Password
# https://myaccount.google.com/apppasswords
# App: Mail
# Device: Custom (n8n E2Bot)

# 4. Copiar senha de 16 caracteres
# Usar em GMAIL_SMTP_PASSWORD
```

#### Claude API Key

```bash
# 1. Acessar Anthropic Console
# https://console.anthropic.com/

# 2. Create API Key
# Name: E2 Bot Development

# 3. Copiar chave sk-ant-api03-...
# Usar em CLAUDE_API_KEY
```

#### Evolution API Key

```bash
# 1. Iniciar Evolution API
docker compose up -d evolution-api

# 2. Gerar API Key
curl -X POST http://localhost:8080/instance/create \
  -H "Content-Type: application/json" \
  -d '{"instanceName": "e2bot-instance"}'

# 3. Copiar apikey do response
# Usar em EVOLUTION_API_KEY
```

---

## 3. Iniciar Serviços Docker

### 3.1. Build e Start

```bash
# Build de imagens
docker compose build

# Iniciar todos os serviços
docker compose up -d

# Verificar status
docker compose ps
# Esperado:
# NAME                    STATUS
# e2bot-postgres-dev      Up
# e2bot-n8n-dev           Up
# e2bot-evolution-dev     Up
# e2bot-nginx-dev         Up
```

### 3.2. Verificar Logs

```bash
# Logs de todos os serviços
docker compose logs -f

# Logs específicos
docker logs -f e2bot-n8n-dev
docker logs -f e2bot-postgres-dev
docker logs -f e2bot-evolution-dev

# Verificar erros
docker compose logs | grep -i error
```

---

## 4. Configurar Banco de Dados

### 4.1. Criar Schema

```bash
# Conectar ao PostgreSQL
docker exec -it e2bot-postgres-dev psql -U postgres -d e2bot_dev

# Executar migrations
\i /docker-entrypoint-initdb.d/001_create_schema.sql

# Verificar tabelas criadas
\dt
# Esperado:
# conversations
# appointments
# email_logs
# appointment_reminders

# Verificar schema conversations
\d conversations
# Esperado:
# id, phone_number, lead_name, email, service_type,
# city, current_state, state_machine_state, next_stage,
# collected_data (JSONB), created_at, updated_at
```

### 4.2. Seed Data (Opcional)

```bash
# Inserir dados de teste
cat > /tmp/seed.sql << 'EOF'
INSERT INTO conversations (phone_number, lead_name, service_type, city, current_state)
VALUES
  ('5561999999991', 'Test User 1', 'energia_solar', 'brasilia', 'greeting'),
  ('5561999999992', 'Test User 2', 'subestacao', 'goiania', 'greeting');
EOF

docker exec -i e2bot-postgres-dev psql -U postgres -d e2bot_dev < /tmp/seed.sql

# Verificar
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT phone_number, lead_name, service_type FROM conversations;"
```

---

## 5. Configurar n8n

### 5.1. Acessar Interface

```bash
# Abrir navegador
xdg-open http://localhost:5678
# Ou manualmente: http://localhost:5678

# Login
# User: admin (ou valor de N8N_BASIC_AUTH_USER)
# Password: sua_senha_n8n_aqui
```

### 5.2. Configurar Credentials

#### PostgreSQL Credential

```
1. Settings → Credentials → Add Credential
2. Type: Postgres
3. Name: E2 Bot PostgreSQL Dev
4. Connection:
   - Host: postgres
   - Database: e2bot_dev
   - User: postgres
   - Password: sua_senha_segura_aqui
   - Port: 5432
   - SSL: Disabled
5. Test → Save
```

#### Gmail SMTP Credential

```
1. Settings → Credentials → Add Credential
2. Type: SMTP
3. Name: E2 Bot Gmail SMTP
4. Connection:
   - Host: smtp.gmail.com
   - Port: 465
   - Security: SSL/TLS (NOT STARTTLS!)
   - User: seu_email@gmail.com
   - Password: sua_senha_app_gmail_aqui
5. Test → Save
```

#### Claude AI Credential

```
1. Settings → Credentials → Add Credential
2. Type: HTTP Header Auth
3. Name: Claude AI API
4. Header:
   - Name: x-api-key
   - Value: sk-ant-api03-...sua_chave...
5. Additional Headers:
   - anthropic-version: 2023-06-01
   - content-type: application/json
6. Save
```

#### Google Calendar OAuth

```
1. Settings → Credentials → Add Credential
2. Type: Google OAuth2 API
3. Name: E2 Bot Google Calendar
4. OAuth2 Configuration:
   - Client ID: seu_client_id_aqui
   - Client Secret: seu_client_secret_aqui
   - Scopes: https://www.googleapis.com/auth/calendar
5. Connect My Account → Autorizar
6. Test → Save
```

### 5.3. Importar Workflows

```bash
# 1. Via Interface n8n
# Workflows → Import from File
# Selecionar: n8n/workflows/production/wf02/02_ai_agent_conversation_V114_FUNCIONANDO.json

# 2. Via CLI (alternativa)
docker exec e2bot-n8n-dev n8n import:workflow \
  --input=/data/workflows/production/wf02/02_ai_agent_conversation_V114_FUNCIONANDO.json

# 3. Ativar Workflow
# Workflows → WF02 V114 → Toggle "Active" → Verde ✅
```

---

## 6. Configurar Evolution API

### 6.1. Criar Instância WhatsApp

```bash
# 1. Criar instância
curl -X POST http://localhost:8080/instance/create \
  -H "Content-Type: application/json" \
  -d '{
    "instanceName": "e2bot-instance",
    "qrcode": true,
    "integration": "WHATSAPP-BAILEYS"
  }'

# Response:
# {
#   "instance": {
#     "instanceName": "e2bot-instance",
#     "status": "created"
#   },
#   "qrcode": {
#     "base64": "data:image/png;base64,..."
#   }
# }

# 2. Conectar WhatsApp
# - Abrir WhatsApp no celular
# - Configurações → Dispositivos Conectados → Conectar Dispositivo
# - Escanear QR Code da resposta

# 3. Verificar conexão
curl -s http://localhost:8080/instance/connectionState/e2bot-instance \
  -H "apikey: sua_api_key_evolution_aqui" | jq

# Esperado:
# {
#   "instance": "e2bot-instance",
#   "state": "open"
# }
```

### 6.2. Configurar Webhook

```bash
# Configurar webhook para n8n
curl -X POST http://localhost:8080/webhook/set/e2bot-instance \
  -H "Content-Type: application/json" \
  -H "apikey: sua_api_key_evolution_aqui" \
  -d '{
    "url": "http://n8n:5678/webhook/whatsapp",
    "webhook_by_events": false,
    "webhook_base64": false,
    "events": [
      "MESSAGES_UPSERT"
    ]
  }'

# Verificar configuração
curl -s http://localhost:8080/webhook/find/e2bot-instance \
  -H "apikey: sua_api_key_evolution_aqui" | jq

# Esperado:
# {
#   "webhook": {
#     "url": "http://n8n:5678/webhook/whatsapp",
#     "events": ["MESSAGES_UPSERT"]
#   }
# }
```

---

## 7. Validar Configuração

### 7.1. Teste de Conectividade

```bash
# PostgreSQL
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "SELECT NOW();"
# Esperado: timestamp atual ✅

# n8n
curl -s http://localhost:5678/healthz | jq
# Esperado: { "status": "ok" } ✅

# Evolution API
curl -s http://localhost:8080/instance/fetchInstances \
  -H "apikey: sua_api_key_evolution_aqui" | jq
# Esperado: array com e2bot-instance ✅

# nginx
curl -s http://localhost/health
# Esperado: OK ✅
```

### 7.2. Teste End-to-End

```bash
# 1. Enviar mensagem WhatsApp de teste
# Enviar para número conectado: "oi"

# 2. Verificar logs n8n
docker logs -f e2bot-n8n-dev | grep -E "Workflow|Message"
# Esperado: Execução de WF01 → WF02 ✅

# 3. Verificar banco de dados
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT phone_number, current_state FROM conversations ORDER BY updated_at DESC LIMIT 1;"
# Esperado: Novo registro com estado 'greeting' ✅

# 4. Verificar resposta WhatsApp
# Esperado: Mensagem de boas-vindas recebida no WhatsApp ✅
```

### 7.3. Teste de Workflow Completo

```bash
# Fluxo completo de teste (10-15 minutos)

# 1. Iniciar conversa
# WhatsApp: "oi"
# Esperado: Mensagem de boas-vindas com serviços

# 2. Preencher dados
# WhatsApp: "Bruno Rosa"  # Nome
# WhatsApp: "bruno@example.com"  # Email
# WhatsApp: "1"  # Energia Solar
# WhatsApp: "brasilia"  # Cidade

# 3. Confirmar serviço
# WhatsApp: "1"  # Agendar
# Esperado: 3 datas disponíveis com contagem de slots

# 4. Selecionar data
# WhatsApp: "1"  # Primeira data
# Esperado: Horários disponíveis para data selecionada

# 5. Selecionar horário
# WhatsApp: "1"  # Primeiro horário
# Esperado: Confirmação de agendamento + email enviado

# 6. Verificar database
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT lead_name, service_type, scheduled_date FROM appointments ORDER BY created_at DESC LIMIT 1;"
# Esperado: Agendamento criado ✅

# 7. Verificar email
# Check inbox: Email de confirmação recebido ✅

# 8. Verificar Google Calendar
# Abrir Google Calendar → Evento criado ✅
```

---

## 8. Troubleshooting

### 8.1. Docker

```bash
# Container não inicia
docker compose down
docker compose up -d --force-recreate

# Verificar logs de erro
docker compose logs | grep -i error

# Limpar volumes (CUIDADO: apaga dados)
docker compose down -v
docker compose up -d
```

### 8.2. PostgreSQL

```bash
# Conexão recusada
docker exec e2bot-postgres-dev pg_isready -U postgres
# Esperado: accepting connections ✅

# Verificar configuração
docker exec e2bot-postgres-dev cat /var/lib/postgresql/data/postgresql.conf | grep listen

# Reset password (se necessário)
docker exec -it e2bot-postgres-dev psql -U postgres \
  -c "ALTER USER postgres WITH PASSWORD 'nova_senha';"
```

### 8.3. n8n

```bash
# Workflow não executa
# 1. Verificar Active toggle (deve estar verde)
# 2. Verificar Webhook URL correto
# 3. Testar manualmente: Execute Workflow button

# Credential inválido
# Settings → Credentials → Test Connection
# Se falhar: Delete + Recriar

# Logs detalhados
docker logs -f e2bot-n8n-dev --tail 100
```

### 8.4. Evolution API

```bash
# Instância desconectada
curl -X POST http://localhost:8080/instance/connect/e2bot-instance \
  -H "apikey: sua_api_key_evolution_aqui"

# QR Code expirado
curl -X POST http://localhost:8080/instance/restart/e2bot-instance \
  -H "apikey: sua_api_key_evolution_aqui"

# Logs
docker logs -f e2bot-evolution-dev
```

### 8.5. Problemas Comuns

#### "Gmail SMTP Authentication Failed"

```bash
# Causa: STARTTLS usado ao invés de SSL/TLS
# Solução:
# 1. n8n Credential → SMTP
# 2. Port: 465 (não 587!)
# 3. Security: SSL/TLS (não STARTTLS!)
# 4. Test → Save
```

#### "FOR UPDATE SKIP LOCKED syntax error"

```bash
# Causa: PostgreSQL < 9.5
# Solução: Verificar versão
docker exec e2bot-postgres-dev psql -U postgres -c "SELECT version();"
# Mínimo: PostgreSQL 14.x ✅
```

#### "Cannot read properties of undefined (reading 'wf06_next_dates')"

```bash
# Causa: WF06 V2.1 não implantado
# Solução:
# 1. Importar: 06_calendar_availability_service_v2_1.json
# 2. Ativar workflow
# 3. Testar: curl -X POST http://localhost:5678/webhook/calendar-availability
```

---

## 9. Dicas de Desenvolvimento

### 9.1. Workflow Testing

```bash
# Testar workflow isoladamente
# n8n → Workflow → Execute Workflow
# Usar dados de teste fixos

# Simular webhook
curl -X POST http://localhost:5678/webhook/whatsapp \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "5561999999999",
    "message": "oi"
  }'
```

### 9.2. Database Queries

```bash
# Queries úteis para debug

# 1. Último estado de conversação
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT phone_number, state_machine_state, collected_data->>'current_stage'
      FROM conversations
      WHERE phone_number = '5561999999999';"

# 2. Agendamentos do dia
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT lead_name, service_type, scheduled_date, scheduled_time_start
      FROM appointments
      WHERE scheduled_date = CURRENT_DATE;"

# 3. Logs de email recentes
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT recipient_email, status, sent_at
      FROM email_logs
      ORDER BY sent_at DESC
      LIMIT 10;"
```

### 9.3. Hot Reload

```bash
# n8n workflows: Auto-reload ao salvar ✅
# Docker compose: Restart manual necessário

# Restart serviço específico
docker compose restart n8n

# Restart todos os serviços
docker compose restart
```

---

## 10. Próximos Passos

Após configuração bem-sucedida:

1. **Ler Documentação**:
   - `docs/development/01_WORKFLOW_MODIFICATION.md` - Como modificar workflows
   - `docs/development/02_DEBUGGING_GUIDE.md` - Técnicas de debugging
   - `docs/development/03_COMMON_TASKS.md` - Tarefas comuns

2. **Explorar Workflows**:
   - WF01: Deduplicação de mensagens
   - WF02: Conversação AI com state machine
   - WF05: Agendamento via Google Calendar
   - WF06: Serviço de disponibilidade de calendário
   - WF07: Envio de emails de confirmação

3. **Configurar IDE**:
   - VSCode com extensões: PostgreSQL, Docker, n8n
   - GitKraken ou SourceTree para Git visual
   - Postman para testes de API

4. **Familiarizar com Estrutura**:
   ```bash
   # Explorar projeto
   tree -L 3 -d

   # Ler código de exemplo
   cat scripts/wf02/state-machines/wf02-v114-slot-time-fields-fix.js

   # Estudar schema de banco
   docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
     -c "\d+ conversations"
   ```

---

## Checklist de Configuração

- [ ] Docker e Docker Compose instalados
- [ ] Repositório clonado
- [ ] Arquivo `.env` criado e configurado
- [ ] Credenciais Gmail, Claude, Google Calendar obtidas
- [ ] Serviços Docker iniciados (`docker compose up -d`)
- [ ] PostgreSQL schema criado e validado
- [ ] n8n acessível em http://localhost:5678
- [ ] Credentials configurados em n8n
- [ ] Workflows importados e ativados
- [ ] Evolution API conectada ao WhatsApp
- [ ] Webhook configurado
- [ ] Teste end-to-end realizado com sucesso
- [ ] Database possui registro de teste
- [ ] Email de confirmação recebido
- [ ] Google Calendar possui evento criado

**Tempo Total**: ~45 minutos para configuração completa

**Suporte**: Consultar `docs/development/02_DEBUGGING_GUIDE.md` para troubleshooting avançado
