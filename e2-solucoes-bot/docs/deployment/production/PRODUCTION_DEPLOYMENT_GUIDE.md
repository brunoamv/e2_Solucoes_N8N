# Guia de Deployment em Produção - E2 Soluções Bot

> **Versão**: Production V1.4 (First Live Deployment Completo)
> **Data**: 2026-05-04
> **Ambiente**: https://n8n.climacocal.com.br
> **Status**: ✅ Deployment funcional | V1.4 documenta todos os erros encontrados e corrigidos no primeiro teste real em produção (2026-05-04)

---

## Índice

1. [Pré-Requisitos](#1-pré-requisitos)
2. [Criação de Contas e Credenciais Base](#2-criação-de-contas-e-credenciais-base)
3. [Configuração de Ambiente](#3-configuração-de-ambiente)
4. [Credenciais e Segurança](#4-credenciais-e-segurança)
5. [Deploy da Infraestrutura](#5-deploy-da-infraestrutura)
6. [Deploy dos Workflows](#6-deploy-dos-workflows)
7. [Validação e Testes](#7-validação-e-testes)
8. [Monitoramento](#8-monitoramento)
9. [Troubleshooting](#9-troubleshooting)

---

## 1. Pré-Requisitos

### 1.1 Servidor de Produção

**Requisitos Mínimos**:
- OS: Ubuntu 22.04 LTS
- CPU: 2 vCPUs
- RAM: 4GB
- Disco: 40GB SSD
- Docker: 24.0+
- Docker Compose: 2.20+

### 1.2 Domínios e DNS

**Domínios Configurados** (subdomínios reais de produção):
- `n8n.climacocal.com.br` → n8n UI (HTTPS)
- `e2solucoeswhatsapp.climacocal.com.br` → Evolution API (HTTPS) ⚠️ **NÃO é `whatsapp`!**
- Traefik: serviço compartilhado (não tem subdomínio próprio neste servidor)

**Configuração DNS via Cloudflare Tunnel** (⚠️ este servidor usa Cloudflare Tunnel, NÃO A records diretos):

O Cloudflare Tunnel ID é: `3483e46e-fcb9-470f-959c-65b73266c79c`

```
# No Cloudflare Dashboard → climacocal.com.br → DNS:
n8n                    CNAME  3483e46e-fcb9-470f-959c-65b73266c79c.cfargotunnel.com  [proxy ON]
e2solucoeswhatsapp     CNAME  3483e46e-fcb9-470f-959c-65b73266c79c.cfargotunnel.com  [proxy ON]
```

> **IMPORTANTE**: Sem o registro CNAME para `e2solucoeswhatsapp` no Cloudflare, o Evolution API
> não terá URL externa. O bot ainda funciona via URLs internas Docker, mas acesso externo falha.
> Verificar: se `e2solucoeswhatsapp.climacocal.com.br` retornar NXDOMAIN (proxy OFF) ou 404 (proxy ON)
> → o registro CNAME está faltando ou errado.

### 1.3 Acessos Necessários

- [ ] Acesso SSH ao servidor de produção (usuário com sudo)
- [ ] Acesso ao repositório Git do projeto
- [ ] Acesso ao Google Workspace Admin (para criar conta bot@climacocal.com.br)
- [ ] Acesso ao Google Cloud Console (mesmo usuário admin)
- [ ] Cartão de crédito válido (para Google Cloud Console - não será cobrado)

---

## 2. Criação de Contas e Credenciais Base

### 2.1 Conta Gmail/Workspace para o Bot

**Objetivo**: Criar conta `bot@climacocal.com.br` que será usada para:
- Envio de emails (SMTP)
- Google Calendar API (OAuth)
- Todas as integrações Google

#### Passo 1: Criar Conta no Google Workspace

**Se usar Google Workspace** (domínio próprio):
1. Acesse: https://admin.google.com
2. Login: Conta de administrador do domínio `climacocal.com.br`
3. Menu: "Usuários" → "Adicionar novo usuário"
4. Preencha:
   - Nome: `E2 Bot`
   - Sobrenome: `Production`
   - Endereço de email principal: `bot`
   - Domínio: `climacocal.com.br`
   - Senha temporária: (gere uma senha forte)
5. **Desmarque**: "Pedir para alterar a senha no próximo login"
6. Click "Adicionar novo usuário"
7. **Anote a senha**: Esta será sua senha de acesso (NÃO é o App Password)

**Se usar Gmail gratuito**:
1. Acesse: https://accounts.google.com/signup
2. Crie conta com alias: `bot.climacocal@gmail.com`
3. Complete verificação de telefone
4. **Anote a senha**: Senha principal da conta

#### Passo 2: Ativar Autenticação de Dois Fatores (2FA)

**OBRIGATÓRIO para criar App Password!**

1. Acesse: https://myaccount.google.com/security
2. Login: `bot@climacocal.com.br` (ou alias Gmail)
3. Seção "Como fazer login no Google"
4. Click em "Verificação em duas etapas" → "Começar"
5. Escolha método de verificação:
   - **Recomendado**: App autenticador (Google Authenticator, Authy)
   - Alternativa: SMS para número de telefone
6. Complete o processo de configuração
7. **Verificar**: Status deve mostrar "Ativada" em azul ✅

#### Passo 3: Criar Gmail App Password

1. Acesse: https://myaccount.google.com/apppasswords
2. Login: `bot@climacocal.com.br`
3. **Se aparecer "Esta configuração não está disponível"**:
   - Verifique se 2FA está ativado (passo 2)
   - Aguarde 10 minutos e tente novamente
4. Click "Selecionar app" → "Mail"
5. Click "Selecionar dispositivo" → "Other (custom name)"
6. Digite: `E2 Bot Production`
7. Click "Gerar"
8. **Copie a senha de 16 caracteres** (formato: `xxxx xxxx xxxx xxxx`)
9. **Importante**:
   - Esta senha NÃO tem espaços quando usar no .env (remova espaços)
   - Exemplo exibido: `abcd efgh ijkl mnop`
   - Usar no .env: `abcdefghijklmnop`

**Teste do App Password**:
```bash
# Testar autenticação SMTP
curl -v --url 'smtps://smtp.gmail.com:587' \
  --ssl-reqd \
  --mail-from 'bot@climacocal.com.br' \
  --mail-rcpt 'your-test@email.com' \
  --user 'bot@climacocal.com.br:abcdefghijklmnop' \
  -T - <<EOF
From: "E2 Bot" <bot@climacocal.com.br>
To: <your-test@email.com>
Subject: Test SMTP

This is a test email.
EOF

# Esperado: 250 2.0.0 OK
```

### 2.2 Google Calendar OAuth Credentials

#### Passo 1: Criar Projeto no Google Cloud Console

1. **Acesse**: https://console.cloud.google.com
2. **Login**: `bot@climacocal.com.br`
3. **Criar Projeto**:
   - Click no seletor de projeto (topo, ao lado de "Google Cloud")
   - Click "Novo Projeto"
   - Nome do projeto: `E2 Bot Production`
   - ID do projeto: `e2-bot-prod-XXXXX` (gerado automaticamente)
   - Organização: (deixe em branco se não tiver)
   - Click "Criar"
4. **Aguarde**: Projeto será criado em ~30 segundos
5. **Selecione o projeto**: Click no seletor e escolha "E2 Bot Production"

#### Passo 2: Habilitar Google Calendar API

1. **No projeto E2 Bot Production**:
2. Menu lateral → "APIs e serviços" → "Biblioteca"
3. Buscar: `Google Calendar API`
4. Click no resultado "Google Calendar API"
5. Click "Ativar"
6. Aguarde ativação (~10 segundos)

#### Passo 3: Criar OAuth Consent Screen

**OBRIGATÓRIO antes de criar credentials!**

1. Menu lateral → "APIs e serviços" → "Tela de permissão OAuth"
2. **Tipo de usuário**:
   - Se Google Workspace: Selecione "Interno"
   - Se Gmail gratuito: Selecione "Externo"
3. Click "Criar"
4. **Informações do app**:
   - Nome do app: `E2 Bot Production`
   - Email de suporte do usuário: `bot@climacocal.com.br`
   - Logotipo do app: (opcional - pode pular)
5. **Domínio do app**: (pode pular)
6. **Informações de contato do desenvolvedor**:
   - Email: `bot@climacocal.com.br`
7. Click "Salvar e continuar"
8. **Escopos**: Click "Adicionar ou remover escopos"
   - Buscar e selecionar:
     - `Google Calendar API` → `.../auth/calendar`
     - `Google Calendar API` → `.../auth/calendar.events`
   - Click "Atualizar"
9. Click "Salvar e continuar"
10. **Usuários de teste** (apenas se Externo):
    - Click "Adicionar usuários"
    - Email: `bot@climacocal.com.br`
    - Click "Adicionar"
11. Click "Salvar e continuar"
12. Click "Voltar para o painel"

#### Passo 4: Criar OAuth Client ID

1. Menu lateral → "APIs e serviços" → "Credenciais"
2. Click "+ Criar credenciais" → "ID do cliente OAuth"
3. **Tipo de aplicativo**: "Aplicativo da Web"
4. **Nome**: `n8n Production`
5. **Origens JavaScript autorizadas**: (deixe vazio)
6. **URIs de redirecionamento autorizados**:
   - Click "+ Adicionar URI"
   - Cole: `https://n8n.climacocal.com.br/rest/oauth2-credential/callback`
7. Click "Criar"
8. **COPIE e SALVE**:
   - Client ID: `<GOOGLE_OAUTH_CLIENT_ID>.apps.googleusercontent.com`
   - Client Secret: `<GOOGLE_OAUTH_CLIENT_SECRET>`
9. Click "OK"

**Arquivo de Backup** (recomendado):
```bash
# Criar arquivo seguro com credenciais OAuth
cat > /opt/google-oauth-credentials.txt <<EOF
Project: E2 Bot Production
Client ID: <COPIAR_CLIENT_ID>
Client Secret: <COPIAR_CLIENT_SECRET>
Created: $(date)
EOF

# Proteger arquivo
chmod 600 /opt/google-oauth-credentials.txt
```

### 2.3 PostgreSQL Database Account

**Objetivo**: Configurar autenticação e permissões do PostgreSQL

**Nota**: O PostgreSQL no Docker já vem com usuário `postgres` configurado via variáveis de ambiente. Não precisa criar manualmente.

**Verificação Pós-Deploy**:
```bash
# Após containers iniciados (seção 5), verificar acesso:
docker exec e2bot-postgres-prd psql -U postgres -d e2bot_prod -c "\conninfo"

# Esperado:
# You are connected to database "e2bot_prod" as user "postgres" via socket in "/var/run/postgresql" at port "5432".
```

**Database para Evolution API**:
```bash
# ✅ NÃO é necessário criar manualmente!
# init.sql cria evolution_db automaticamente no primeiro startup:
#   CREATE DATABASE evolution_db OWNER postgres;

# Verificar após containers iniciados
docker exec e2bot-postgres-prd psql -U postgres -c "\l"

# Esperado: e2bot_prod e evolution_db listados (NÃO evolution_prod!)
```

---

## 3. Configuração de Ambiente

### 3.1 Clone do Repositório

```bash
# SSH no servidor de produção
ssh user@servidor-producao

# Instalar dependências básicas
sudo apt-get update
sudo apt-get install -y git curl jq apache2-utils

# Clone do repositório
cd /opt
sudo git clone https://github.com/your-org/e2-solucoes-bot.git
cd e2-solucoes-bot

# Ajustar permissões
sudo chown -R $(whoami):$(whoami) /opt/e2-solucoes-bot

# Checkout da versão de produção
git checkout production-v1
```

### 3.2 Criação do Arquivo .env de Produção

```bash
# Copiar template de produção
cp docker/.env.prod.example docker/.env.production

# Editar arquivo .env.production
nano docker/.env.production
```

**Valores Obrigatórios para Preencher**:

```bash
# ============================================================================
# DOMAIN & SSL
# ============================================================================
DOMAIN=climacocal.com.br
N8N_SUBDOMAIN=n8n
EVOLUTION_SUBDOMAIN=e2solucoeswhatsapp   # ⚠️ NÃO é "whatsapp"! Nome real do subdomínio em prod
# TRAEFIK_SUBDOMAIN: não usado, Traefik é compartilhado no servidor climacocal
ACME_EMAIL=admin@climacocal.com.br

# ============================================================================
# POSTGRESQL
# ============================================================================
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<GERAR_SENHA_FORTE>  # Ver seção 4.1
POSTGRES_DB=e2bot_prod

# ============================================================================
# N8N
# ============================================================================
N8N_BASIC_AUTH_ACTIVE=true
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=CoraRosa  # Senha fornecida pelo cliente
N8N_ENCRYPTION_KEY=<GERAR_KEY>  # Ver seção 4.1

# ============================================================================
# REDIS
# ============================================================================
REDIS_PASSWORD=<GERAR_SENHA_FORTE>  # Ver seção 4.1

# ============================================================================
# EVOLUTION API
# ============================================================================
EVOLUTION_API_KEY=<GERAR_KEY>  # Ver seção 4.1
EVOLUTION_DB=evolution_db                 # ⚠️ Nome real usado em prod (NÃO evolution_prod)
EVOLUTION_INSTANCE_NAME=e2-bot-production
# EVOLUTION_SERVER_URL e EVOLUTION_WEBHOOK_URL são definidos no docker-compose via EVOLUTION_SUBDOMAIN + DOMAIN
# Resultado: SERVER_URL=https://e2solucoeswhatsapp.climacocal.com.br
#            WEBHOOK_GLOBAL_URL=https://n8n.climacocal.com.br/webhook/whatsapp-evolution  ← ⚠️ path real!

# ============================================================================
# TRAEFIK
# ============================================================================
TRAEFIK_DASHBOARD_USER=admin
TRAEFIK_DASHBOARD_PASSWORD=<GERAR_HASH_HTPASSWD>  # Ver seção 4.1

# ============================================================================
# EMAIL / SMTP (Gmail)
# ============================================================================
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_SECURE=false
SMTP_USER=bot@climacocal.com.br
SMTP_PASSWORD=<GMAIL_APP_PASSWORD>  # Copiar da seção 2.1 (SEM espaços!)
EMAIL_FROM=E2 Soluções Bot <bot@climacocal.com.br>

# ============================================================================
# MONITORING (OPCIONAL)
# ============================================================================
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=<GERAR_SENHA_FORTE>  # Ver seção 4.1
GRAFANA_SECRET_KEY=<GERAR_KEY>  # Ver seção 4.1
```

### 3.3 Criação do Evolution API .env

```bash
# Criar diretório para Evolution API
mkdir -p docker/evolution

# Criar arquivo .env específico do Evolution API
nano docker/evolution/.env
```

**Conteúdo do docker/evolution/.env**:

```bash
# ============================================================================
# Evolution API v2.3.7 - Production Configuration
# ============================================================================
# IMPORTANTE: Este arquivo é OBRIGATÓRIO devido ao Issue #1474
# Container ignora env_file - requer custom entrypoint

# API Configuration
# ⚠️ SERVER_URL usa o subdomínio real "e2solucoeswhatsapp" (não "whatsapp")
SERVER_URL=https://e2solucoeswhatsapp.climacocal.com.br
AUTHENTICATION_API_KEY=<COPIAR_EVOLUTION_API_KEY_DO_.env.production>

# Database
DATABASE_ENABLED=true
DATABASE_PROVIDER=postgresql
# ⚠️ Em prod usa DATABASE_CONNECTION_URI completa (não campos separados)
DATABASE_CONNECTION_URI=postgresql://<POSTGRES_USER>:<POSTGRES_PASSWORD>@postgres:5432/evolution_db?schema=evolution_api

# Webhook
# ⚠️ Path real em produção: whatsapp-evolution (NÃO whatsapp!)
WEBHOOK_GLOBAL_URL=https://n8n.climacocal.com.br/webhook/whatsapp-evolution
WEBHOOK_GLOBAL_ENABLED=true

# Session
CONFIG_SESSION_PHONE_CLIENT=E2 Bot Production
QRCODE_LIMIT=30

# Logging
LOG_LEVEL=ERROR
LOG_COLOR=false
TIMEZONE=America/Sao_Paulo
```

---

## 4. Credenciais e Segurança

### 4.1 Geração de Todas as Credenciais

Execute cada comando e anote os valores gerados:

```bash
# PostgreSQL Password
echo "POSTGRES_PASSWORD=$(openssl rand -base64 32)"
# Exemplo output: POSTGRES_PASSWORD=Kx7mP9vR2wQ8nF3jL5hT1yC4bV6gS0zA

# n8n Encryption Key
echo "N8N_ENCRYPTION_KEY=$(openssl rand -hex 32)"
# Exemplo output: N8N_ENCRYPTION_KEY=1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f

# Redis Password
echo "REDIS_PASSWORD=$(openssl rand -base64 32)"
# Exemplo output: REDIS_PASSWORD=N8pL5mQ3vR7wX2jK9hF4yT1bC6gS0zA8

# Evolution API Key
echo "EVOLUTION_API_KEY=$(openssl rand -hex 32)"
# Exemplo output: EVOLUTION_API_KEY=9f8e7d6c5b4a3g2h1i0j9k8l7m6n5o4p3q2r1s0t9u8v7w6x5y4z3a2b1c0d9e8f

# Grafana Admin Password
echo "GRAFANA_ADMIN_PASSWORD=$(openssl rand -base64 32)"
# Exemplo output: GRAFANA_ADMIN_PASSWORD=mK3pL9vR7wQ2nF8jL5hT4yC1bV6gS0zA

# Grafana Secret Key
echo "GRAFANA_SECRET_KEY=$(openssl rand -hex 32)"
# Exemplo output: GRAFANA_SECRET_KEY=7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f

# Traefik Dashboard Password (htpasswd format)
# Gere uma senha forte primeiro, depois crie o hash:
TRAEFIK_PASS="SuaSenhaForteAqui123!"
echo "TRAEFIK_DASHBOARD_PASSWORD=$(htpasswd -nb admin $TRAEFIK_PASS)"
# Exemplo output: TRAEFIK_DASHBOARD_PASSWORD=admin:$apr1$ruca84Hq$mbjdMZBAG.KWn7vfN/SNK/
```

**Arquivo Seguro para Armazenar Credenciais**:

```bash
# Criar arquivo com todas as credenciais geradas
cat > /opt/e2-solucoes-bot/.credentials <<EOF
# E2 Bot Production Credentials
# Generated: $(date)
# DO NOT COMMIT THIS FILE!

POSTGRES_PASSWORD=<COLAR_VALOR_GERADO>
N8N_ENCRYPTION_KEY=<COLAR_VALOR_GERADO>
REDIS_PASSWORD=<COLAR_VALOR_GERADO>
EVOLUTION_API_KEY=<COLAR_VALOR_GERADO>
GRAFANA_ADMIN_PASSWORD=<COLAR_VALOR_GERADO>
GRAFANA_SECRET_KEY=<COLAR_VALOR_GERADO>
TRAEFIK_DASHBOARD_PASSWORD=<COLAR_HASH_HTPASSWD_COMPLETO>

# Gmail App Password (da seção 2.1 - SEM espaços)
SMTP_PASSWORD=<COLAR_16_CARACTERES_SEM_ESPACOS>

# Google OAuth (da seção 2.2)
GOOGLE_CLIENT_ID=<COLAR_CLIENT_ID>
GOOGLE_CLIENT_SECRET=<COLAR_CLIENT_SECRET>
EOF

# Proteger arquivo (somente owner pode ler)
chmod 600 /opt/e2-solucoes-bot/.credentials

# Adicionar ao .gitignore
echo ".credentials" >> /opt/e2-solucoes-bot/.gitignore
```

### 4.2 Aplicar Credenciais no .env.production

```bash
# Substituir placeholders no .env.production
# Use os valores gerados na seção 4.1

cd /opt/e2-solucoes-bot

# Editar e colar valores manualmente
nano docker/.env.production

# OU usar sed para substituir (se tiver arquivo .credentials)
source .credentials

sed -i "s/POSTGRES_PASSWORD=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX/POSTGRES_PASSWORD=${POSTGRES_PASSWORD}/" docker/.env.production
sed -i "s/N8N_ENCRYPTION_KEY=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX/N8N_ENCRYPTION_KEY=${N8N_ENCRYPTION_KEY}/" docker/.env.production
sed -i "s/REDIS_PASSWORD=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX/REDIS_PASSWORD=${REDIS_PASSWORD}/" docker/.env.production
sed -i "s/EVOLUTION_API_KEY=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX/EVOLUTION_API_KEY=${EVOLUTION_API_KEY}/" docker/.env.production
sed -i "s|TRAEFIK_DASHBOARD_PASSWORD=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX|TRAEFIK_DASHBOARD_PASSWORD=${TRAEFIK_DASHBOARD_PASSWORD}|" docker/.env.production
sed -i "s/SMTP_PASSWORD=XXXX XXXX XXXX XXXX/SMTP_PASSWORD=${SMTP_PASSWORD}/" docker/.env.production
sed -i "s/GRAFANA_ADMIN_PASSWORD=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX/GRAFANA_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}/" docker/.env.production
sed -i "s/GRAFANA_SECRET_KEY=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX/GRAFANA_SECRET_KEY=${GRAFANA_SECRET_KEY}/" docker/.env.production
```

### 4.3 Aplicar Credenciais no docker/evolution/.env

```bash
# Editar Evolution API .env
nano docker/evolution/.env

# Substituir:
# AUTHENTICATION_API_KEY=<COPIAR_EVOLUTION_API_KEY>
# Para:
AUTHENTICATION_API_KEY=9f8e7d6c5b4a3g2h1i0j9k8l7m6n5o4p3q2r1s0t9u8v7w6x5y4z3a2b1c0d9e8f

# DATABASE_PASSWORD=<COPIAR_POSTGRES_PASSWORD>
# Para:
DATABASE_PASSWORD=Kx7mP9vR2wQ8nF3jL5hT1yC4bV6gS0zA

# (Use valores da seção 4.1)
```

### 4.4 Validação de Credenciais

```bash
# Verificar se TODOS os placeholders foram substituídos
grep -E "XXXX|<COPIAR|<GERAR" docker/.env.production docker/evolution/.env

# ❌ Se retornar algo: Ainda há placeholders não preenchidos!
# ✅ Se não retornar nada: Todas as credenciais foram configuradas corretamente
```

---

## 5. Deploy da Infraestrutura

### 5.1 Validação da Configuração

```bash
# Validar sintaxe do docker-compose
cd /opt/e2-solucoes-bot
docker-compose -f docker/docker-compose-prd.yml --env-file docker/.env.production config

# Se houver erros: Verificar .env.production e corrigir
# Se sucesso: Prosseguir para deploy
```

### 5.2 Iniciar Serviços

```bash
# Iniciar serviços básicos (SEM monitoring)
docker-compose -f docker/docker-compose-prd.yml --env-file docker/.env.production up -d

# OU: Iniciar COM monitoring stack (Prometheus + Grafana)
docker-compose -f docker/docker-compose-prd.yml --env-file docker/.env.production --profile monitoring up -d
```

### 5.3 Verificar Status dos Containers

```bash
# Verificar todos os containers rodando
docker-compose -f docker/docker-compose-prd.yml ps

# Esperado: Todos os containers com status "Up" e "healthy"
# NAME                          STATUS
# traefik                       Up        ← Traefik compartilhado (NÃO é e2bot-traefik-prd)
# cloudflare-climacocal-tunnel  Up        ← Tunnel Cloudflare compartilhado
# e2bot-postgres-prd            Up (healthy)
# e2bot-redis-prd               Up (healthy)
# e2bot-n8n-prd                 Up (healthy)
# e2bot-n8n-worker-prd          Up        ← Worker para execuções em queue mode
# e2bot-evolution-prd           Up (healthy)
# e2bot-templates-prd           Up        ← nginx servindo templates HTML para WF07
# e2bot-prometheus-prd          Up (healthy)  # Se --profile monitoring
# e2bot-grafana-prd             Up (healthy)  # Se --profile monitoring
```

**Troubleshooting de Containers Unhealthy**:
```bash
# Ver logs de container problemático
docker logs e2bot-<SERVICE>-prd --tail 50

# Restart se necessário
docker restart e2bot-<SERVICE>-prd

# Aguardar healthcheck (30-60 segundos)
watch -n 5 'docker ps --format "table {{.Names}}\t{{.Status}}" | grep e2bot'
```

### 5.4 Verificar SSL/TLS Certificates

```bash
# Verificar logs do Traefik (certificados Let's Encrypt)
docker logs e2bot-traefik-prd 2>&1 | grep -i "certificate"

# Esperado:
# "Obtained certificate for domain n8n.climacocal.com.br"
# "Obtained certificate for domain whatsapp.climacocal.com.br"
# "Obtained certificate for domain traefik.climacocal.com.br"

# Testar endpoints HTTPS
curl -I https://n8n.climacocal.com.br
# Esperado: HTTP/2 200 OK (com certificado SSL válido)

curl -I https://whatsapp.climacocal.com.br/health
# Esperado: HTTP/2 200 OK

# Se certificados NÃO foram obtidos:
# 1. Verificar DNS está configurado corretamente (seção 1.2)
# 2. Aguardar propagação DNS (até 24 horas)
# 3. Verificar portas 80 e 443 abertas no firewall
```

### 5.5 Verificar Database Initialization

```bash
# Verificar se o banco foi inicializado
docker exec e2bot-postgres-prd psql -U postgres -d e2bot_prod \
  -c "\dt"

# Esperado: Tabelas criadas (conversations, appointments, email_logs)

# Verificar schema da tabela conversations
docker exec e2bot-postgres-prd psql -U postgres -d e2bot_prod \
  -c "\d conversations"

# Esperado: Colunas incluindo phone_number, lead_name, service_type, current_state, collected_data

# evolution_db é criado AUTOMATICAMENTE pelo init.sql (não precisa criar manualmente)
# Verificar que ambos existem:
docker exec e2bot-postgres-prd psql -U postgres -c "\l" | grep -E "e2bot_prod|evolution_db"
```

---

## 6. Deploy dos Workflows

### 6.1 Acesso ao n8n UI

1. **Abra o navegador**: https://n8n.climacocal.com.br
2. **Login**:
   - Usuário: `admin`
   - Senha: `CoraRosa`
3. **Verificar**: Dashboard do n8n deve carregar

### 6.2 Configurar Credenciais no n8n UI

**FAZER ANTES de importar workflows!**

Acesse: https://n8n.climacocal.com.br → Login: admin / CoraRosa

#### 6.2.1 Configurar SMTP Account

1. **n8n UI** → Menu lateral → "Projects" → "E2 Bot Production" (ou projeto ativo)
2. Aba "Credentials" → Click "+ Add Credential"
3. Buscar: `SMTP`
4. Selecionar: **"SMTP Account"** (não "Gmail")
5. **Preencher campos**:

```
Credential Name: Gmail SMTP Production
User: bot@climacocal.com.br
Password: [Gmail App Password de 16 caracteres da seção 2.1]
Host: smtp.gmail.com
Port: 465
SSL/TLS: ✅ Ativado (toggle verde)
Client Host Name: Bruno
```

6. **Testar Conexão**:
   - Click "Test connection" (botão inferior)
   - Aguarde mensagem: "Connection tested successfully ✅"
7. Click "Save"

**Valores Importantes**:
- ⚠️ **Port 465** com **SSL/TLS ativo** (não port 587!)
- ⚠️ **Password** = Gmail App Password (16 caracteres SEM espaços)
- ⚠️ **User** = Email completo `bot@climacocal.com.br`
- ℹ️ **Client Host Name** = Qualquer nome (ex: "Bruno", "E2Bot", "Production")

**Troubleshooting SMTP**:
```
Erro: "Invalid login"
Solução 1: Verificar App Password está correto (sem espaços)
Solução 2: Regenerar App Password na seção 2.1
Solução 3: Verificar 2FA está ativado no Gmail

Erro: "Connection timeout"
Solução: Trocar Port 587 para Port 465 com SSL/TLS ativo

Erro: "Authentication failed"
Solução: Usar Gmail App Password, NÃO senha principal da conta
```

#### 6.2.2 Configurar PostgreSQL Account

1. **n8n UI** → Menu lateral → "Projects" → "E2 Bot Production"
2. Aba "Credentials" → Click "+ Add Credential"
3. Buscar: `Postgres`
4. Selecionar: **"Postgres Account"**
5. **Aba "Connection"** - Preencher campos:

```
Credential Name: PostgreSQL Production
Host: e2bot-postgres-prd
Database: e2bot_prod
User: postgres
Password: [POSTGRES_PASSWORD gerado na seção 4.1]
```

6. **Aba "Details"** - Configurações adicionais:

```
Maximum Number of Connections: 100
Ignore SSL Issues (Insecure): ❌ Desativado
SSL: Disable
Port: 5432
SSH Tunnel: ❌ Desativado
```

7. **Testar Conexão**:
   - Click "Test connection" (botão inferior)
   - Aguarde mensagem: "Connection tested successfully ✅"
8. Click "Save"

**Valores Importantes**:
- ⚠️ **Host** = `e2bot-postgres-prd` (nome do container Docker)
- ⚠️ **Database** = `e2bot_prod` (database principal do bot)
- ⚠️ **Port** = `5432` (porta padrão PostgreSQL)
- ⚠️ **SSL** = Disable (comunicação interna Docker não precisa SSL)

**Troubleshooting PostgreSQL**:
```
Erro: "Connection refused"
Solução: Verificar container postgres está rodando:
  docker ps | grep postgres

Erro: "Authentication failed"
Solução: Verificar POSTGRES_PASSWORD está correto (.env.production)

Erro: "Database does not exist"
Solução: Criar database conforme seção 2.3:
  docker exec e2bot-postgres-prd psql -U postgres -c "CREATE DATABASE e2bot_prod;"
```

#### 6.2.3 Configurar Google Calendar Credential

1. **n8n UI** → Menu lateral → "Projects" → "E2 Bot Production"
2. Aba "Credentials" → Click "+ Add Credential"
3. Buscar: `Google Calendar OAuth2 API`
4. Click no resultado
5. **Preencher**:
   - Credential Name: `Google Calendar Production`
   - Client ID: (copiar da seção 2.2 - Google Cloud Console)
   - Client Secret: (copiar da seção 2.2 - Google Cloud Console)
6. Click "Connect my account"
7. **Autorizar**:
   - Será redirecionado para Google
   - Login: `bot@climacocal.com.br`
   - Click "Allow" para permissões do Google Calendar
8. **Verificar**: Deve retornar para n8n com "Connected" em verde ✅
9. Click "Save"

**Troubleshooting OAuth**:
```
Erro: "redirect_uri_mismatch"
Solução: Verificar URI de redirect no Google Cloud Console:
  https://n8n.climacocal.com.br/rest/oauth2-credential/callback

Erro: "access_denied"
Solução: Verificar usuário bot@climacocal.com.br está em "Test users" (se app Externo)

Erro: "invalid_client"
Solução: Verificar Client ID e Secret estão corretos
```

### 6.3 Importar Workflows de Produção

**Localização dos Workflows**:
```
n8n/workflows/production/
├── wf01/ → 01_main_whatsapp_handler_V2.8.3_NO_LOOP.json
├── wf02/ → 02_ai_agent_conversation_V114_FUNCIONANDO.json
├── wf05/ → 05_appointment_scheduler_v7_hardcoded_values.json
├── wf06/ → 06_calendar_availability_service_v2_2.json
└── wf07/ → 07_send_email_v13_insert_select.json
```

**Ordem de Importação** (importante para dependências):

#### 6.3.1 WF06 - Calendar Availability Service

1. n8n UI → Click no **+ icon** (top right) → "Import from File"
2. Selecione: `n8n/workflows/production/wf06/06_calendar_availability_service_v2_2.json`
3. Click "Import"
4. **Configurar Credential Google Calendar**:
   - Abra o workflow importado
   - Localize node "Google Calendar" (dentro do "Calculate Next Dates")
   - Click no dropdown "Credential to connect with"
   - Selecione: `Google Calendar Production` (criado na seção 6.2)
5. Click "Save" (top right)
6. **Ativar Workflow**: Toggle "Active" (top right) → Verde ✅

#### 6.3.2 WF07 - Send Email Service

1. Import: `n8n/workflows/production/wf07/07_send_email_v13_insert_select.json`
2. **Verificar SMTP Configuration**:
   - Abra o workflow
   - Localize node "Send Email (Gmail SMTP)"
   - Verifique configurações:
     - Host: `smtp.gmail.com`
     - Port: `587`
     - Authentication: Habilitado
     - User: `{{$env.SMTP_USER}}` → Deve resolver para `bot@climacocal.com.br`
     - Password: `{{$env.SMTP_PASSWORD}}` → Deve usar Gmail App Password
3. **Testar SMTP** (opcional):
   - Click em "Execute Node" no node "Send Email"
   - Verificar email de teste recebido
4. Save workflow
5. **Ativar Workflow**: Toggle "Active" → Verde ✅

#### 6.3.3 WF05 - Appointment Scheduler

1. Import: `n8n/workflows/production/wf05/05_appointment_scheduler_v7_hardcoded_values.json`
2. **Verificar Google Calendar Credential**:
   - Node "Create Calendar Event"
   - Credential: `Google Calendar Production`
3. **🔴 CRÍTICO: Verificar Trigger do WF07 (workflowId hardcoded)**:
   - Node "Send Confirmation Email" (Execute Workflow node)
   - Procure pelo campo `workflowId`
   - ⚠️ Se estiver como `={{ $env.WORKFLOW_ID_EMAIL_CONFIRMATION || '7' }}` → **ERRO!**
   - `N8N_BLOCK_ENV_ACCESS_IN_NODE=true` bloqueia `$env` → fallback `'7'` não é um ID válido
   - **Solução**: Trocar para o ID real do WF07 no n8n (formato: `ZQJt2RjPwziBEVET`)
   - Como encontrar o ID do WF07: n8n UI → Abrir WF07 → copiar da URL do navegador

   **Se o editor mostrar o valor correto mas a execução ainda falhar**:
   O n8n 2.x em queue mode tem dois armazenamentos distintos:
   - `workflow_entity.nodes` = Rascunho (o que você vê no editor)
   - `workflow_history[activeVersionId].nodes` = O que o worker executa
   Editar pelo editor às vezes não propaga para `workflow_history`. Fix via SQL:
   ```bash
   # 1. Descobrir o activeVersionId do WF05
   docker exec e2bot-postgres-prd psql -U postgres -d e2bot_prod \
     -c "SELECT id, name, \"activeVersionId\" FROM workflow_entity WHERE name LIKE '%WF05%' OR name LIKE '%appointment%';"

   # 2. Verificar o que o worker realmente executa
   docker exec e2bot-postgres-prd psql -U postgres -d e2bot_prod \
     -c "SELECT nodes::text FROM workflow_history WHERE \"versionId\" = '<activeVersionId_do_WF05>';" | \
     grep -o '"workflowId":"[^"]*"'

   # 3. Se workflowId estiver errado, corrigir:
   docker exec e2bot-postgres-prd psql -U postgres -d e2bot_prod -c "
     UPDATE workflow_history
     SET nodes = REPLACE(nodes::text,
       '\$env.WORKFLOW_ID_EMAIL_CONFIRMATION || ''7''',
       '<ID_REAL_DO_WF07>')::jsonb
     WHERE \"versionId\" = '<activeVersionId_do_WF05>';"
   ```

4. Save workflow
5. **NÃO ativar ainda** (ativar após WF02)

#### 6.3.4 WF02 - AI Agent Conversation

1. Import: `n8n/workflows/production/wf02/02_ai_agent_conversation_V114_FUNCIONANDO.json`
2. **Verificar Componentes Críticos**:

   **a) Build SQL Queries Node** (V111 - Row Locking):
   ```javascript
   // Verificar linha contém:
   FOR UPDATE SKIP LOCKED
   ```

   **b) State Machine Logic Node** (V114 - TIME fields):
   ```javascript
   // Verificar extração de start_time e end_time:
   const scheduled_time_start = selectedSlot.start_time;
   const scheduled_time_end = selectedSlot.end_time;
   ```

   **c) Build Update Queries Node** (V104.2 - Schema-aligned):
   ```javascript
   // Verificar que NÃO contém:
   contact_phone  // ❌ Não deve existir!
   ```

   **d) Workflow Connections** (V105 - Routing Fix):
   - Verify: Build Update Queries → Update Conversation State → Check If WF06
   - ✅ Update State executa ANTES do Check If WF06

   **e) Send WhatsApp Response Node** (V106.1 - response_text):
   ```
   text: {{ $node["Build Update Queries"].json.response_text }}
   ```

3. **🔴 CRÍTICO: Verificar URLs Internas do WF02** (divergência dev→prod frequente):

   **Abrir cada nó HTTP Request e verificar:**

   | Nó | URL Errada (DEV) | URL Correta (PROD) |
   |----|-----------------|--------------------|
   | Enviar mensagem WhatsApp | `http://e2bot-evolution-dev:8080/message/sendText/e2-solucoes-bot` | `http://e2bot-evolution-prd:8080/message/sendText/e2-bot-production` |
   | Chamar WF06 (datas) | `http://e2bot-n8n-dev:5678/webhook/calendar-availability` | `http://e2bot-n8n-prd:5678/webhook/calendar-availability` |
   | Chamar WF06 (slots) | `http://e2bot-n8n-dev:5678/webhook/calendar-availability` | `http://e2bot-n8n-prd:5678/webhook/calendar-availability` |

   > **Por que usar URL interna?** O n8n worker está na rede `e2bot-backend` que NÃO tem acesso
   > à rede externa. Deve usar o nome do container Docker, não o domínio público.
   > Container Evolution: `e2bot-evolution-prd` | n8n: `e2bot-n8n-prd`

4. **Verificar Triggers do WF06** (usar URL interna, não externa):
   - Node "Trigger WF06 Next Dates" → URL: `http://e2bot-n8n-prd:5678/webhook/calendar-availability`
   - Node "Trigger WF06 Available Slots" → URL: `http://e2bot-n8n-prd:5678/webhook/calendar-availability`

4. Save workflow
5. **NÃO ativar ainda** (ativar após WF01)

#### 6.3.5 WF01 - Main WhatsApp Handler

1. Import: `n8n/workflows/production/wf01/01_main_whatsapp_handler_V2.8.3_NO_LOOP.json`
2. **Verificar Webhook Path**:
   - Node "Webhook" (trigger)
   - HTTP Method: POST
   - Path: `whatsapp-evolution`  ⚠️ **NÃO é `whatsapp`!**
   - Full URL: `https://n8n.climacocal.com.br/webhook/whatsapp-evolution`
3. **Verificar Trigger do WF02**:
   - Node "Trigger WF02"
   - Verifique que aponta para workflow WF02 correto
4. Save workflow
5. **ATIVAR WORKFLOW** ✅ (crítico para receber mensagens WhatsApp)

#### 6.3.6 Ativar Workflows Restantes

**Ordem de Ativação**:
1. ✅ WF06 (já ativo)
2. ✅ WF07 (já ativo)
3. ✅ WF05 → **Ativar agora**
4. ✅ WF02 → **Ativar agora**
5. ✅ WF01 (já ativo)

### 6.4 Verificar Evolution API Instance

> **NOTA**: A Evolution API não tem URL externa funcional até o CNAME Cloudflare ser configurado (seção 1.2).
> Use a porta local `127.0.0.1:8082` que está exposta no host para gerenciamento.

```bash
# ✅ Via localhost (sempre disponível no servidor)
curl -s http://localhost:8082/instance/fetchInstances \
  -H "apikey: <EVOLUTION_API_KEY>" | python3 -m json.tool

# Verificar status da instância
curl -s http://localhost:8082/instance/connectionState/e2-bot-production \
  -H "apikey: <EVOLUTION_API_KEY>"

# Esperado: connectionStatus: "open" (WhatsApp conectado)
```

**Verificar e Corrigir Webhook da Instância**:
```bash
# Ver webhook atual
curl -s http://localhost:8082/webhook/find/e2-bot-production \
  -H "apikey: <EVOLUTION_API_KEY>"

# ✅ Esperado: "url": "https://n8n.climacocal.com.br/webhook/whatsapp-evolution"

# Se errado, corrigir:
curl -s -X POST "http://localhost:8082/webhook/set/e2-bot-production" \
  -H "apikey: <EVOLUTION_API_KEY>" \
  -H "Content-Type: application/json" \
  --data-raw '{"webhook":{"url":"https://n8n.climacocal.com.br/webhook/whatsapp-evolution","enabled":true,"events":["MESSAGES_UPSERT","MESSAGES_UPDATE","CONNECTION_UPDATE","QRCODE_UPDATED"],"webhookByEvents":false,"webhookBase64":false}}'
```

**Criar Instância do WhatsApp** (se necessário):

```bash
# Criar instância (via localhost)
curl -X POST http://localhost:8082/instance/create \
  -H "Content-Type: application/json" \
  -H "apikey: <EVOLUTION_API_KEY>" \
  -d '{
    "instanceName": "e2-bot-production",
    "qrcode": true,
    "integration": "WHATSAPP-BAILEYS"
  }'

# Verificar QR Code (conectar WhatsApp)
curl -s http://localhost:8082/instance/connect/e2-bot-production \
  -H "apikey: <EVOLUTION_API_KEY>" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('qrcode',{}).get('base64','')[:50])"

# Escanear QR Code com WhatsApp Business do cliente
# 1. Abra WhatsApp Business no celular
# 2. Configurações → Dispositivos conectados
# 3. Conectar um dispositivo
# 4. Escanear QR Code exibido
```

---

## 7. Validação e Testes

### 7.1 Teste de Integração Completa

**Fluxo End-to-End**:

1. **Enviar mensagem no WhatsApp**: "oi"
2. **Esperado**:
   ```
   Olá! Sou a assistente virtual da E2 Soluções.

   Escolha um serviço:
   1️⃣ Sistema Solar Fotovoltaico
   2️⃣ Subestação de Média Tensão
   3️⃣ Projetos Elétricos
   4️⃣ BESS (Armazenamento)
   5️⃣ Análise de Projetos Existentes
   ```

3. **Responder**: "1" (Sistema Solar)
4. **Esperado**: Confirmação → "Para confirmar: Sistema Solar Fotovoltaico?"

5. **Responder**: "1" (confirmar)
6. **Esperado**: Request para WF06 → Lista de 3 datas disponíveis

7. **Responder**: "1" (primeira data)
8. **Esperado**: Request para WF06 → Lista de horários disponíveis

9. **Responder**: "1" (primeiro horário)
10. **Esperado**: Confirmação de agendamento + Trigger do WF05 + Email enviado

### 7.2 Validação de Banco de Dados

```bash
# Verificar conversação criada
docker exec e2bot-postgres-prd psql -U postgres -d e2bot_prod \
  -c "SELECT phone_number, lead_name, service_type, current_state, state_machine_state
      FROM conversations
      WHERE phone_number = '<NUMERO_TESTE>'
      ORDER BY updated_at DESC LIMIT 1;"

# Esperado:
# state_machine_state: "confirmation_received" ou "scheduling_complete"
# current_state: "agendado"

# Verificar agendamento criado
docker exec e2bot-postgres-prd psql -U postgres -d e2bot_prod \
  -c "SELECT lead_name, lead_email, service_type, scheduled_date, scheduled_time_start, scheduled_time_end, google_calendar_event_id
      FROM appointments
      WHERE created_at > NOW() - INTERVAL '1 hour'
      ORDER BY created_at DESC LIMIT 1;"

# Esperado: Registro com dados completos e google_calendar_event_id preenchido

# Verificar email enviado
docker exec e2bot-postgres-prd psql -U postgres -d e2bot_prod \
  -c "SELECT recipient_email, recipient_name, subject, status, sent_at
      FROM email_logs
      WHERE created_at > NOW() - INTERVAL '1 hour'
      ORDER BY created_at DESC LIMIT 1;"

# Esperado: status: 'sent', sent_at com timestamp recente
```

### 7.3 Validação de Logs

```bash
# n8n logs
docker logs -f e2bot-n8n-prd 2>&1 | grep -E "ERROR|V114|V111"

# Evolution API logs
docker logs -f e2bot-evolution-prd 2>&1 | grep -E "ERROR|webhook"

# PostgreSQL logs (queries lentas)
docker logs e2bot-postgres-prd 2>&1 | grep "duration:" | tail -20

# Redis logs
docker logs e2bot-redis-prd 2>&1 | tail -50
```

---

## 8. Monitoramento

### 8.1 Healthchecks

```bash
# Verificar health de todos os serviços
docker ps --format "table {{.Names}}\t{{.Status}}" | grep e2bot

# Esperado: Todos com "(healthy)" no status
```

### 8.2 Acesso ao Monitoring Stack (se ativo)

**Prometheus**:
- URL: https://prometheus.climacocal.com.br
- Login: admin / `<TRAEFIK_DASHBOARD_PASSWORD>`
- **Nota**: Use a senha do Traefik (htpasswd)

**Grafana**:
- URL: https://grafana.climacocal.com.br
- Login: admin / `<GRAFANA_ADMIN_PASSWORD>`
- **Primeiro Acesso**:
  1. Login com credenciais acima
  2. Add Data Source → Prometheus
  3. URL: `http://prometheus:9090`
  4. Click "Save & Test"
  5. Import Dashboards:
     - Dashboard ID: 1860 (Node Exporter Full)
     - Dashboard ID: 7362 (PostgreSQL Database)
     - Dashboard ID: 11074 (Redis Dashboard)

**Dashboards Recomendados**:
- n8n Workflow Executions
- PostgreSQL Performance
- Redis Cache Hit Rate
- Evolution API Requests

### 8.3 Backup Automático

**Configurar Cron para Backup Diário**:

```bash
# Criar script de backup
cat > /opt/e2-solucoes-bot/scripts/backup-production.sh <<'EOF'
#!/bin/bash
BACKUP_DIR=/opt/e2-solucoes-bot/docker/backups/postgres
DATE=$(date +%Y%m%d_%H%M%S)

# Criar diretório de backup se não existir
mkdir -p ${BACKUP_DIR}

# Backup PostgreSQL
docker exec e2bot-postgres-prd pg_dump -U postgres e2bot_prod | gzip > \
  ${BACKUP_DIR}/e2bot_prod_${DATE}.sql.gz

# Backup Evolution API database
docker exec e2bot-postgres-prd pg_dump -U postgres evolution_db | gzip > \
  ${BACKUP_DIR}/evolution_db_${DATE}.sql.gz

# Cleanup backups older than 30 days
find ${BACKUP_DIR} -name "*.sql.gz" -mtime +30 -delete

echo "[$(date)] Backup completed: e2bot_prod_${DATE}.sql.gz and evolution_db_${DATE}.sql.gz"
EOF

# Tornar executável
chmod +x /opt/e2-solucoes-bot/scripts/backup-production.sh

# Testar backup manual
/opt/e2-solucoes-bot/scripts/backup-production.sh

# Verificar backup criado
ls -lh /opt/e2-solucoes-bot/docker/backups/postgres/

# Adicionar ao crontab (3AM diariamente)
(crontab -l 2>/dev/null; echo "0 3 * * * /opt/e2-solucoes-bot/scripts/backup-production.sh >> /var/log/e2bot-backup.log 2>&1") | crontab -

# Verificar cron configurado
crontab -l | grep backup
```

**Backup Manual**:
```bash
# Executar backup imediatamente
/opt/e2-solucoes-bot/scripts/backup-production.sh

# Restaurar backup (se necessário)
gunzip < /opt/e2-solucoes-bot/docker/backups/postgres/e2bot_prod_20260504_030000.sql.gz | \
  docker exec -i e2bot-postgres-prd psql -U postgres -d e2bot_prod
```

---

## 9. Troubleshooting

### 9.1 Workflow WF01 Não Recebe Mensagens

**Sintoma**: Mensagens WhatsApp não chegam ao n8n; logs mostram `"POST whatsapp" is not registered`

**Diagnóstico**:
```bash
# Verificar webhook configurado no Evolution API (via localhost)
curl -s http://localhost:8082/webhook/find/e2-bot-production \
  -H "apikey: <EVOLUTION_API_KEY>"

# ✅ Correto: "url": "https://n8n.climacocal.com.br/webhook/whatsapp-evolution"
# ❌ Errado: "url": "https://n8n.climacocal.com.br/webhook/whatsapp"

# Verificar webhook registrado no n8n (banco de dados)
docker exec e2bot-postgres-prd psql -U postgres -d e2bot_prod \
  -c "SELECT \"webhookPath\", method, \"workflowId\" FROM webhook_entity;"

# ✅ Correto: webhookPath = "whatsapp-evolution" (path real do WF01)

# Testar webhook manualmente (usar path correto!)
curl -X POST https://n8n.climacocal.com.br/webhook/whatsapp-evolution \
  -H "Content-Type: application/json" \
  -d '{
    "instance": "e2-bot-production",
    "data": {
      "key": {
        "remoteJid": "5561999999999@s.whatsapp.net",
        "fromMe": false
      },
      "message": {
        "conversation": "teste"
      }
    }
  }'

# Esperado: HTTP 200 OK e execução enfileirada nos logs n8n
```

**Solução**:
1. Ativar WF01 no n8n UI se estiver inativo
2. Corrigir webhook no Evolution API para usar path `whatsapp-evolution`:
   ```bash
   curl -s -X POST "http://localhost:8082/webhook/set/e2-bot-production" \
     -H "apikey: <EVOLUTION_API_KEY>" \
     -H "Content-Type: application/json" \
     --data-raw '{"webhook":{"url":"https://n8n.climacocal.com.br/webhook/whatsapp-evolution","enabled":true,"events":["MESSAGES_UPSERT","MESSAGES_UPDATE","CONNECTION_UPDATE","QRCODE_UPDATED"],"webhookByEvents":false,"webhookBase64":false}}'
   ```
3. Verificar n8n logs: `docker logs e2bot-n8n-prd --since 5m | grep -v "^$"`

### 9.2 Bot Recebe Mensagens mas NÃO Responde (WF02 falha silenciosamente)

**Sintoma**: WF01 executa com sucesso, mas nenhuma resposta é enviada ao usuário

**Causa raiz mais comum**: WF02 foi exportado do DEV com URLs hardcoded dos containers de desenvolvimento.

**Diagnóstico**:
```bash
# Ver execuções recentes de WF02 e seus status
docker exec e2bot-postgres-prd psql -U postgres -d e2bot_prod \
  -c "SELECT id, status, \"startedAt\", \"stoppedAt\" FROM execution_entity ORDER BY \"startedAt\" DESC LIMIT 10;"

# Checar se os containers DEV existem (não devem existir em prod!)
docker ps | grep evolution-dev   # ← NÃO deve aparecer nada
docker ps | grep n8n-dev         # ← NÃO deve aparecer nada
```

**Verificação no n8n UI**:
1. Abra `https://n8n.climacocal.com.br` → workflow `wk02_v114`
2. Procure por todos os nós HTTP Request
3. Verifique URLs — qualquer URL com `-dev` está errada

**URLs que devem existir em PROD** (vs o que pode estar errado):
| O que procurar | Errado (DEV) | Correto (PROD) |
|---|---|---|
| Envio WhatsApp | `e2bot-evolution-dev:8080` | `e2bot-evolution-prd:8080` |
| Instance name | `e2-solucoes-bot` | `e2-bot-production` |
| WF06 webhook | `e2bot-n8n-dev:5678` | `e2bot-n8n-prd:5678` |
| Templates | `e2bot-templates-dev` | *(verificar se existe container equivalente)* |

**Solução**: Editar cada nó no n8n UI e corrigir as URLs. Salvar e re-ativar o workflow.

### 9.4 WF06 Retorna Erro "Cannot read properties of undefined"

**Sintoma**: WF02 falha ao chamar WF06

**Diagnóstico**:
```bash
# Testar WF06 diretamente
curl -X POST https://n8n.climacocal.com.br/webhook/calendar-availability \
  -H "Content-Type: application/json" \
  -d '{
    "action": "next_dates",
    "count": 3,
    "service_type": "energia_solar",
    "duration_minutes": 120
  }'

# Esperado: JSON com dates_with_availability array
```

**Solução**:
1. Verificar credential Google Calendar está autorizada
2. Re-autorizar se expirada: Settings → Credentials → Google Calendar Production → Reconnect
3. Verificar WF06 está ativo

### 9.5 PostgreSQL TIME Field Error

**Sintoma**: Erro ao salvar agendamento: "invalid input syntax for type time"

**Diagnóstico**:
```bash
# Verificar State Machine V114
# n8n UI → WF02 → "State Machine Logic" node
# Procurar por:
const scheduled_time_start = selectedSlot.start_time;  // Deve existir!
const scheduled_time_end = selectedSlot.end_time;      // Deve existir!
```

**Solução**:
1. Verificar WF02 V114 foi importado corretamente
2. Se código antigo: Substituir por V114 (ver seção 6.3.4)

### 9.6 Email Não Enviado

**Sintoma**: WF07 falha ao enviar email

**Diagnóstico**:
```bash
# Verificar logs do WF07
docker logs e2bot-n8n-prd 2>&1 | grep -A 10 "WF07"

# Testar SMTP manualmente
docker exec -it e2bot-n8n-prd sh
apk add curl
curl -v --url 'smtps://smtp.gmail.com:587' \
  --ssl-reqd \
  --mail-from 'bot@climacocal.com.br' \
  --mail-rcpt 'test@example.com' \
  --user 'bot@climacocal.com.br:<GMAIL_APP_PASSWORD>'
```

**Solução**:
1. Verificar `SMTP_PASSWORD` é Gmail App Password (16 caracteres SEM espaços)
2. Verificar 2FA está ativado na conta Gmail (seção 2.1)
3. Regenerar App Password se necessário (seção 2.1)
4. Verificar WF07 está ativo

### 9.7 Containers Unhealthy

**Sintoma**: `docker ps` mostra containers com status "unhealthy"

**Diagnóstico**:
```bash
# Verificar healthcheck específico
docker inspect e2bot-postgres-prd | jq '.[0].State.Health'
docker inspect e2bot-redis-prd | jq '.[0].State.Health'
docker inspect e2bot-n8n-prd | jq '.[0].State.Health'
docker inspect e2bot-evolution-prd | jq '.[0].State.Health'
```

**Solução**:
```bash
# Restart container problemático
docker restart e2bot-<SERVICE>-prd

# Se persistir: Verificar logs
docker logs e2bot-<SERVICE>-prd 2>&1 | tail -100

# Último recurso: Recrear container
docker-compose -f docker/docker-compose-prd.yml --env-file docker/.env.production up -d --force-recreate <SERVICE>
```

### 9.8 Google OAuth "redirect_uri_mismatch"

**Sintoma**: Erro ao conectar Google Calendar no n8n

**Solução**:
```bash
# Verificar URI configurado no Google Cloud Console
# Deve ser EXATAMENTE:
https://n8n.climacocal.com.br/rest/oauth2-credential/callback

# Se diferente:
# 1. Google Cloud Console → APIs & Services → Credentials
# 2. Click no OAuth Client ID "n8n Production"
# 3. Editar "Authorized redirect URIs"
# 4. Adicionar: https://n8n.climacocal.com.br/rest/oauth2-credential/callback
# 5. Salvar
# 6. Tentar reconectar no n8n
```

### 9.3 WF05 Falha no Google Calendar: DNS Error

**Sintoma**: Execução 139 do WF05 falha com `The DNS server returned an error` no node "Create Calendar Event"

**Causa raiz**: O n8n em **queue mode** tem arquitetura dual:
- `e2bot-n8n-prd` (main): Recebe webhooks → tem acesso à internet
- `e2bot-n8n-worker-prd` (worker): Processa execuções → **estava só na rede interna `e2bot-backend`**

O worker não consegue resolver `googleapis.com` por estar isolado da rede externa.

**Diagnóstico**:
```bash
# Verificar redes do worker
docker inspect e2bot-n8n-worker-prd | jq '.[0].NetworkSettings.Networks | keys'
# Se retornar apenas ["docker_e2bot-backend"]: Worker está isolado!
# Correto (após fix): ["docker_e2bot-backend", "proxy"]

# Testar resolução DNS do worker
docker exec e2bot-n8n-worker-prd nslookup googleapis.com
# Se falhar: Worker sem internet
```

**Solução (container em execução)**:
```bash
# Conectar worker à rede com internet
docker network connect proxy e2bot-n8n-worker-prd

# Verificar
docker exec e2bot-n8n-worker-prd nslookup googleapis.com
# Esperado: Server: ..., Address: ...
```

**Solução permanente**: O `docker-compose-prd.yml` já está corrigido com:
```yaml
n8n-worker:
  networks:
    - e2bot-frontend   # necessário para acesso à internet (Google Calendar, etc.)
    - e2bot-backend
```

> **Importante**: Webhooks (WF06 via webhook trigger) funcionam via `e2bot-n8n-prd` (main).
> Execute Workflow (WF05 → WF07) roda no worker. São contextos de rede diferentes!

### 9.10 WF05 Dispara WF07 mas $env Bloqueado (workflowId)

**Sintoma**: WF05 execution 139 falha com `access to env vars denied` no node "Send Confirmation Email"

**Causa raiz**: `N8N_BLOCK_ENV_ACCESS_IN_NODE=true` bloqueia `$env.WORKFLOW_ID_EMAIL_CONFIRMATION`.
O fallback `|| '7'` não é um ID de workflow válido em produção.

**Diagnóstico**:
```bash
# Ver qual workflowId o worker está executando (não o draft do editor!)
docker exec e2bot-postgres-prd psql -U postgres -d e2bot_prod \
  -c "SELECT \"activeVersionId\" FROM workflow_entity WHERE name LIKE '%WF05%';" \
  -t | xargs -I{} docker exec e2bot-postgres-prd psql -U postgres -d e2bot_prod \
  -c "SELECT nodes::text FROM workflow_history WHERE \"versionId\" = '{}'" | \
  grep -o '"workflowId":"[^"]*"'
```

**Solução**:
1. Abrir WF07 no n8n UI → copiar ID da URL: `https://n8n.climacocal.com.br/workflow/ZQJt2RjPwziBEVET`
2. No n8n UI, abrir WF05 → node "Send Confirmation Email" → trocar `workflowId` para o ID real
3. Salvar → Verificar que `workflow_history` foi atualizado (ver seção 6.3.3)

> **Lição aprendida**: Em n8n 2.x queue mode, sempre verificar `workflow_history` além do editor.
> O editor mostra o rascunho; o worker executa de `workflow_history[activeVersionId]`.

### 9.11 WF07 Falha em "Fetch Template (HTTP)": Connection Cannot Be Established

**Sintoma**: WF07 execution 297 falha no node "Fetch Template (HTTP)" com
`The connection cannot be established... http://e2bot-templates-prd/confirmacao_agendamento.html`

**Causa raiz**: O container `e2bot-templates-prd` (nginx servindo templates HTML) não existia.

**Diagnóstico**:
```bash
# Verificar se o container existe
docker ps | grep templates
# Se vazio: Container não existe!

# Verificar se templates existem no host
ls -la email-templates/
# Deve conter: confirmacao_agendamento.html, lembrete_24h.html, etc.
```

**Solução**:
```bash
# O docker-compose-prd.yml já inclui o serviço templates
# Para iniciar sem recriar tudo:
docker compose -f docker/docker-compose-prd.yml up -d templates

# Verificar que está acessível do worker
docker exec e2bot-n8n-worker-prd wget -qO- http://e2bot-templates-prd/confirmacao_agendamento.html | head -3
```

**Templates disponíveis**:
- `confirmacao_agendamento.html` → Email de confirmação de agendamento
- `lembrete_24h.html` → Lembrete 24h antes
- `lembrete_2h.html` → Lembrete 2h antes
- `apos_visita.html` → Email pós-visita
- `novo_lead.html` → Notificação de novo lead

### 9.9 Evolution API Container Não Inicia

**Sintoma**: `e2bot-evolution-prd` continua em restart loop

**Diagnóstico**:
```bash
# Ver logs de erro
docker logs e2bot-evolution-prd 2>&1 | tail -50

# Verificar se .env existe
docker exec e2bot-evolution-prd ls -la /evolution/.env

# Se erro: ".env not found"
# Verificar /tmp/.env
docker exec e2bot-evolution-prd ls -la /tmp/.env
```

**Solução**:
```bash
# Verificar docker/evolution/.env foi criado (seção 3.3)
ls -la docker/evolution/.env

# Se não existir: Criar conforme seção 3.3

# Recrear container
docker-compose -f docker/docker-compose-prd.yml --env-file docker/.env.production up -d --force-recreate evolution-api
```

---

## Checklist Final de Deployment

### Pré-Deployment
- [ ] Servidor preparado com Docker e Docker Compose
- [ ] DNS Cloudflare: CNAME `n8n` → `<tunnel-id>.cfargotunnel.com` (proxy ON)
- [ ] DNS Cloudflare: CNAME `e2solucoeswhatsapp` → `<tunnel-id>.cfargotunnel.com` (proxy ON) ⚠️
- [ ] Conta Gmail `bot@climacocal.com.br` criada
- [ ] 2FA ativado na conta Gmail
- [ ] Gmail App Password gerado (16 caracteres)
- [ ] Google Cloud Console: Projeto criado
- [ ] Google Calendar API: Habilitada
- [ ] OAuth Consent Screen: Configurado
- [ ] OAuth Client ID: Criado com redirect URI correto

### Configuração
- [ ] Arquivo `.env.production` criado e preenchido
- [ ] Arquivo `docker/evolution/.env` criado
- [ ] Todas as credenciais geradas (PostgreSQL, Redis, Evolution API, n8n, Grafana)
- [ ] Gmail App Password aplicado no .env (SEM espaços)
- [ ] Validação: Nenhum placeholder XXXX restante

### Infraestrutura
- [ ] Containers iniciados e status "healthy"
- [ ] Certificados SSL obtidos (Let's Encrypt via Cloudflare Tunnel)
- [ ] PostgreSQL: Database `e2bot_prod` criado (pelo init.sql automático)
- [ ] PostgreSQL: Database `evolution_db` criado (pelo init.sql automático — NÃO `evolution_prod`)
- [ ] PostgreSQL: Tabela `appointment_reminders` existe (criada pelo init.sql)
- [ ] Container `e2bot-templates-prd` rodando (nginx para templates WF07)
- [ ] Redis: Autenticação funcionando
- [ ] n8n Worker: Acesso à internet verificado (Google Calendar): `docker exec e2bot-n8n-worker-prd nslookup googleapis.com`

### Credenciais n8n UI
- [ ] SMTP Account: Criado e testado com sucesso ("Connection tested successfully")
- [ ] PostgreSQL Account: Criado e testado com sucesso ("Connection tested successfully")
- [ ] Google Calendar Credential: Autorizado e conectado (verde "Connected")

### Workflows
- [ ] WF06 importado e ativo (Google Calendar credential OK)
- [ ] WF07 importado e ativo (SMTP credential OK)
- [ ] WF05 importado e ativo
- [ ] **🔴 WF05: workflowId do WF07 hardcoded** (sem `$env` — ver seção 6.3.3)
- [ ] WF02 importado e ativo (V114 com todos os fixes, PostgreSQL credential OK)
- [ ] **🔴 WF02: URLs internas verificadas** (sem `-dev` nas URLs HTTP Request)
  - [ ] Evolution API: `http://e2bot-evolution-prd:8080/message/sendText/e2-bot-production`
  - [ ] WF06 webhook: `http://e2bot-n8n-prd:5678/webhook/calendar-availability`
- [ ] WF01 importado e ativo ✅ CRÍTICO
- [ ] **🔴 WF01: Webhook path verificado** = `whatsapp-evolution` (não `whatsapp`)

### Integração
- [ ] Evolution API instance criada e conectada (`connectionStatus: open`)
- [ ] **🔴 Evolution webhook** apontando para `/webhook/whatsapp-evolution`
- [ ] Teste end-to-end completo (WhatsApp → n8n → Calendar → Email)
- [ ] Banco de dados validado (conversations, appointments, email_logs)
- [ ] Email de teste recebido

### Operações
- [ ] Backup automático configurado (cron diário)
- [ ] Monitoramento configurado (opcional: Prometheus + Grafana)
- [ ] Logs de todos os serviços sem erros críticos
- [ ] Documentação de credenciais em local seguro

---

## Contatos de Suporte

**Projeto**: E2 Soluções Bot
**Versão**: Production V1.4 (First Live Deployment Completo — 2026-05-04)
**Documentação**: `/opt/e2-solucoes-bot/docs/`
**Logs**: `/opt/e2-solucoes-bot/docker/logs/`
**Backups**: `/opt/e2-solucoes-bot/docker/backups/`
**Credentials**: `/opt/e2-solucoes-bot/.credentials` (protegido - chmod 600)

**Referências Rápidas**:
- n8n UI: https://n8n.climacocal.com.br (admin / CoraRosa)
- Evolution API: https://e2solucoeswhatsapp.climacocal.com.br ⚠️ (NÃO `whatsapp`)
- Evolution API local: `http://localhost:8082` (sempre disponível via port bind)
- Prometheus: https://prometheus.climacocal.com.br (se monitoring ativo)
- Grafana: https://grafana.climacocal.com.br (se monitoring ativo)

**Histórico de Versões**:
- V1.4 (2026-05-04): Primeiro teste real em produção — 5 erros encontrados e corrigidos
- V1.3 (2026-05-04): Corrigidas divergências críticas DEV→PRD (webhooks, DNS, containers)
- V1.2 (2026-04-29): Adicionada documentação de Cloudflare Tunnel e CNAME
- V1.1 (2026-04-29): Refactoring completo do guia de deployment

---

**Última Atualização**: 2026-05-04
**Versão**: 1.3 (Divergences Dev→Prd Corrigidas)
**Deployed By**: Claude Code SuperClaude Framework

**Changelog**:
- **V1.3** (2026-05-04): Correção de divergências críticas descobertas no primeiro deploy de produção
  - **CRÍTICO**: Webhook path corrigido: `whatsapp` → `whatsapp-evolution` (seções 1.2, 3.3, 6.3.5, 9.1)
  - **CRÍTICO**: EVOLUTION_SUBDOMAIN corrigido: `whatsapp` → `e2solucoeswhatsapp` (seção 1.2, 3.2)
  - **CRÍTICO**: WF02 URLs internas: `-dev` → `-prd` e instância `e2-solucoes-bot` → `e2-bot-production` (seção 6.3.4)
  - DNS: Documentado uso de Cloudflare Tunnel (CNAME) em vez de A records diretos
  - Container names: Removido `e2bot-traefik-prd` (não existe); adicionado `e2bot-n8n-worker-prd`
  - Evolution API: Todos os comandos agora usam `localhost:8082` (não URL externa que pode não funcionar)
  - EVOLUTION_DB: Corrigido para `evolution_db` (não `evolution_prod`)
  - Nova seção 9.2: Troubleshooting "Bot recebe mas não responde" (URLs DEV hardcoded)
  - Checklist: Adicionadas verificações críticas de webhook path e URLs internas
- **V1.2** (2026-05-04): Adicionada seção 6.2 com configuração completa de credenciais no n8n UI
- **V1.1** (2026-05-04): Refactored com todas as credenciais base (Gmail, OAuth, PostgreSQL, Monitoring)
- **V1.0** (2026-05-04): Versão inicial do guia de deployment
