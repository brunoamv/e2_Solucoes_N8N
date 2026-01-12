# Guia de Deploy em Produção - Evolution API

> **⚠️ CRÍTICO**: Este guia inclui o workaround necessário para Issue #1474
>
> Leia completamente antes de executar em produção!

---

## 📋 Pré-requisitos

### Infraestrutura Necessária

- [ ] Servidor Linux (Ubuntu 22.04 LTS recomendado)
- [ ] Docker Engine 24.0+ instalado
- [ ] Docker Compose 2.0+ instalado
- [ ] 2 CPU cores mínimo (4 recomendado)
- [ ] 4GB RAM mínimo (8GB recomendado)
- [ ] 20GB disco mínimo (SSD recomendado)
- [ ] Portas abertas: 80, 443, 8080

### Credenciais Necessárias

- [ ] Domínio configurado (ex: `whatsapp.e2solucoes.com.br`)
- [ ] Email para Let's Encrypt SSL
- [ ] API Key da Evolution API (gerada aleatoriamente)
- [ ] Credenciais do banco de dados PostgreSQL

---

## 🚀 Passo 1: Preparar Ambiente

### 1.1. Clonar Repositório

```bash
cd /opt
git clone https://github.com/sua-empresa/e2-solucoes-bot.git
cd e2-solucoes-bot
```

### 1.2. Configurar .env de Produção

```bash
# Copiar template
cp docker/.env.example docker/.env.production

# Editar com credenciais reais
nano docker/.env.production
```

**Variáveis CRÍTICAS para Evolution API**:

```bash
# ============================================================================
# Evolution API - Configuração de Produção
# ============================================================================

# Server
SERVER_TYPE=http
SERVER_PORT=8080
SERVER_URL=https://whatsapp.e2solucoes.com.br

# Database (PostgreSQL)
DATABASE_ENABLED=true
DATABASE_PROVIDER=postgresql
DATABASE_CONNECTION_URI=postgresql://evolution:SENHA_FORTE_AQUI@evolution-postgres:5432/evolution?schema=public
DATABASE_CONNECTION_CLIENT_NAME=evolution_exchange
DATABASE_SAVE_DATA_INSTANCE=true
DATABASE_SAVE_DATA_NEW_MESSAGE=true
DATABASE_SAVE_MESSAGE_UPDATE=true
DATABASE_SAVE_DATA_CONTACTS=true
DATABASE_SAVE_DATA_CHATS=true
DATABASE_SAVE_DATA_LABELS=true
DATABASE_SAVE_DATA_HISTORIC=true

# Authentication
AUTHENTICATION_TYPE=apikey
AUTHENTICATION_API_KEY=$(openssl rand -hex 32)  # Gerar chave aleatória
AUTHENTICATION_EXPOSE_IN_FETCH_INSTANCES=true

# Redis Cache
CACHE_REDIS_ENABLED=true
CACHE_REDIS_URI=redis://evolution-redis:6379
CACHE_REDIS_PREFIX_KEY=evolution
CACHE_REDIS_SAVE_INSTANCES=true
CACHE_LOCAL_ENABLED=false

# Webhook para n8n
WEBHOOK_GLOBAL_ENABLED=true
WEBHOOK_GLOBAL_URL=https://n8n.e2solucoes.com.br/webhook/whatsapp-messages
WEBHOOK_GLOBAL_WEBHOOK_BY_EVENTS=true

# Webhook Events
WEBHOOK_EVENTS_QRCODE_UPDATED=true
WEBHOOK_EVENTS_MESSAGES_SET=true
WEBHOOK_EVENTS_MESSAGES_UPSERT=true
WEBHOOK_EVENTS_MESSAGES_UPDATE=true
WEBHOOK_EVENTS_CONNECTION_UPDATE=true

# Logging (Produção)
LOG_LEVEL=ERROR,WARN
LOG_COLOR=false
LOG_BAILEYS=error

# Disabled Services
RABBITMQ_ENABLED=false
SQS_ENABLED=false
WEBSOCKET_ENABLED=false
PUSHER_ENABLED=false
```

### 1.3. Gerar API Key Segura

```bash
# Gerar API Key aleatória
openssl rand -hex 32

# Copiar output e adicionar ao .env.production
# Exemplo: AUTHENTICATION_API_KEY=9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b
```

---

## 🐳 Passo 2: Criar docker-compose.prod.yml

```yaml
# docker/docker-compose.prod.yml
version: '3.8'

services:
  # ============================================================================
  # PostgreSQL - Evolution API Database
  # ============================================================================
  evolution-postgres:
    image: postgres:15-alpine
    container_name: evolution-postgres-prod
    restart: always

    environment:
      POSTGRES_USER: evolution
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}  # Do .env.production
      POSTGRES_DB: evolution

    volumes:
      - evolution_postgres_data:/var/lib/postgresql/data
      - ./postgres-backups:/backups

    networks:
      - evolution-network

    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U evolution"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ============================================================================
  # Redis - Cache
  # ============================================================================
  evolution-redis:
    image: redis:7-alpine
    container_name: evolution-redis-prod
    restart: always

    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}

    volumes:
      - evolution_redis_data:/data

    networks:
      - evolution-network

    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ============================================================================
  # Evolution API com Workaround Issue #1474
  # ============================================================================
  evolution-api:
    image: atendai/evolution-api:v2.2.3
    container_name: evolution-api-prod
    restart: always

    depends_on:
      evolution-postgres:
        condition: service_healthy
      evolution-redis:
        condition: service_healthy

    # WORKAROUND CRÍTICO para Issue #1474
    # O container ignora env_file, então usamos entrypoint customizado
    entrypoint: /bin/bash -c "
      if [ -f /tmp/.env ]; then
        cp /tmp/.env /evolution/.env && echo '✅ .env copiado com sucesso';
      else
        echo '❌ ERRO: .env não encontrado em /tmp/.env' && exit 1;
      fi &&
      exec /bin/bash -c '. ./Docker/docker-entrypoint.sh'
    "

    volumes:
      # Montar .env em /tmp (será copiado pelo entrypoint)
      - ../docker/.env.production:/tmp/.env:ro

      # Dados persistentes
      - evolution_instances:/evolution/instances
      - evolution_store:/evolution/store

      # Backups
      - ./evolution-backups:/backups

    networks:
      - evolution-network
      - traefik-network

    labels:
      # Traefik configuração
      - "traefik.enable=true"
      - "traefik.http.routers.evolution-api.rule=Host(`whatsapp.e2solucoes.com.br`)"
      - "traefik.http.routers.evolution-api.entrypoints=websecure"
      - "traefik.http.routers.evolution-api.tls.certresolver=letsencrypt"
      - "traefik.http.services.evolution-api.loadbalancer.server.port=8080"

    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

  # ============================================================================
  # Traefik - Reverse Proxy com SSL
  # ============================================================================
  traefik:
    image: traefik:v2.10
    container_name: traefik-prod
    restart: always

    command:
      - "--api.dashboard=true"
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.letsencrypt.acme.email=${TRAEFIK_ACME_EMAIL}"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
      - "--certificatesresolvers.letsencrypt.acme.httpchallenge.entrypoint=web"

    ports:
      - "80:80"
      - "443:443"

    volumes:
      - "/var/run/docker.sock:/var/run/docker.sock:ro"
      - "traefik_letsencrypt:/letsencrypt"

    networks:
      - traefik-network

    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.traefik.rule=Host(`traefik.e2solucoes.com.br`)"
      - "traefik.http.routers.traefik.service=api@internal"
      - "traefik.http.routers.traefik.entrypoints=websecure"
      - "traefik.http.routers.traefik.tls.certresolver=letsencrypt"

# ============================================================================
# Volumes
# ============================================================================
volumes:
  evolution_postgres_data:
    driver: local
    name: evolution_postgres_prod_data

  evolution_redis_data:
    driver: local
    name: evolution_redis_prod_data

  evolution_instances:
    driver: local
    name: evolution_instances_prod

  evolution_store:
    driver: local
    name: evolution_store_prod

  traefik_letsencrypt:
    driver: local
    name: traefik_letsencrypt_prod

# ============================================================================
# Networks
# ============================================================================
networks:
  evolution-network:
    driver: bridge
    name: evolution-network-prod

  traefik-network:
    driver: bridge
    name: traefik-network-prod
```

---

## 🔧 Passo 3: Deploy

### 3.1. Iniciar Serviços

```bash
cd /opt/e2-solucoes-bot

# Iniciar todos os serviços
docker-compose -f docker/docker-compose.prod.yml up -d

# Aguardar inicialização (60s)
sleep 60

# Verificar status
docker-compose -f docker/docker-compose.prod.yml ps
```

### 3.2. Validar Workaround

```bash
# Verificar que .env foi copiado corretamente
docker exec evolution-api-prod head -20 /evolution/.env

# Deve mostrar conteúdo do .env.production
```

### 3.3. Testar API

```bash
# Testar HTTPS
curl https://whatsapp.e2solucoes.com.br

# Deve retornar HTML da Evolution API
```

---

## 📊 Passo 4: Monitoramento

### 4.1. Healthchecks

```bash
# Ver status de health de todos os containers
docker ps --format "table {{.Names}}\t{{.Status}}"
```

**Output esperado**:
```
NAMES                     STATUS
evolution-api-prod        Up (healthy)
evolution-postgres-prod   Up (healthy)
evolution-redis-prod      Up (healthy)
traefik-prod              Up
```

### 4.2. Logs

```bash
# Logs em tempo real
docker-compose -f docker/docker-compose.prod.yml logs -f evolution-api

# Últimas 100 linhas
docker logs evolution-api-prod --tail 100
```

### 4.3. Métricas

```bash
# Uso de recursos
docker stats evolution-api-prod evolution-postgres-prod evolution-redis-prod
```

---

## 🔄 Passo 5: Backup Automático

### 5.1. Script de Backup

Criar `/opt/e2-solucoes-bot/scripts/backup-production.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/opt/e2-solucoes-bot/docker/evolution-backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup PostgreSQL
docker exec evolution-postgres-prod pg_dump -U evolution evolution | \
  gzip > "$BACKUP_DIR/postgres_$DATE.sql.gz"

# Backup Evolution Instances
docker run --rm -v evolution_instances_prod:/data -v "$BACKUP_DIR":/backup \
  alpine tar czf /backup/instances_$DATE.tar.gz -C /data .

# Manter apenas últimos 7 dias
find "$BACKUP_DIR" -name "*.gz" -mtime +7 -delete

echo "✅ Backup concluído: $DATE"
```

### 5.2. Cron para Backup Diário

```bash
# Adicionar ao crontab
crontab -e

# Backup diário às 3h
0 3 * * * /opt/e2-solucoes-bot/scripts/backup-production.sh >> /var/log/evolution-backup.log 2>&1
```

---

## 🔐 Passo 6: Segurança

### 6.1. Firewall (UFW)

```bash
# Permitir apenas portas necessárias
ufw allow 22/tcp   # SSH
ufw allow 80/tcp   # HTTP (redireciona para HTTPS)
ufw allow 443/tcp  # HTTPS
ufw enable
```

### 6.2. Fail2Ban para Proteção

```bash
# Instalar fail2ban
apt install fail2ban -y

# Configurar proteção Evolution API
cat > /etc/fail2ban/filter.d/evolution-api.conf <<EOF
[Definition]
failregex = ^.*Unauthorized.*<HOST>.*$
ignoreregex =
EOF

cat > /etc/fail2ban/jail.d/evolution-api.conf <<EOF
[evolution-api]
enabled = true
port = 80,443
filter = evolution-api
logpath = /var/lib/docker/containers/*/*.log
maxretry = 5
bantime = 3600
EOF

systemctl restart fail2ban
```

### 6.3. Rotação de API Keys

```bash
# Rotacionar API Key trimestralmente
# 1. Gerar nova key
NEW_KEY=$(openssl rand -hex 32)

# 2. Adicionar ao .env.production
sed -i "s/AUTHENTICATION_API_KEY=.*/AUTHENTICATION_API_KEY=$NEW_KEY/" docker/.env.production

# 3. Aplicar workaround novamente
docker cp docker/.env.production evolution-api-prod:/evolution/.env
docker restart evolution-api-prod

# 4. Atualizar n8n e outros clientes com nova key
```

---

## 📈 Passo 7: Escalabilidade

### 7.1. Múltiplas Instâncias (Load Balancing)

Para alta disponibilidade, rode múltiplas instâncias Evolution API:

```yaml
# docker-compose.prod.yml (adicionar)
services:
  evolution-api-1:
    # ... configuração idêntica
    container_name: evolution-api-prod-1

  evolution-api-2:
    # ... configuração idêntica
    container_name: evolution-api-prod-2

  # Traefik faz load balancing automaticamente
```

### 7.2. Aumentar Recursos PostgreSQL

```yaml
evolution-postgres:
  # ... configuração existente
  command: >
    postgres
    -c max_connections=200
    -c shared_buffers=256MB
    -c effective_cache_size=1GB
    -c work_mem=16MB
```

---

## 🚨 Troubleshooting Produção

### Problema 1: Container reinicia constantemente

```bash
# Ver logs de erro
docker logs evolution-api-prod --tail 200

# Validar .env foi copiado
docker exec evolution-api-prod cat /evolution/.env | head -10

# Se .env não foi copiado, aplicar workaround manualmente
docker cp docker/.env.production evolution-api-prod:/evolution/.env
docker restart evolution-api-prod
```

### Problema 2: Instâncias vão para "close"

```bash
# 1. Verificar .env dentro do container
docker exec evolution-api-prod grep DATABASE_CONNECTION_URI /evolution/.env

# Deve mostrar credenciais corretas, não "user:pass@postgres"

# 2. Se estiver errado, copiar novamente
docker cp docker/.env.production evolution-api-prod:/evolution/.env
docker restart evolution-api-prod
```

### Problema 3: SSL não funciona

```bash
# Verificar certificado Let's Encrypt
docker exec traefik-prod cat /letsencrypt/acme.json

# Renovar certificado manualmente
docker exec traefik-prod rm /letsencrypt/acme.json
docker restart traefik-prod
```

---

## ✅ Checklist Final de Deploy

- [ ] Servidor provisionado com requisitos mínimos
- [ ] Docker e Docker Compose instalados
- [ ] `.env.production` configurado com credenciais seguras
- [ ] API Key gerada aleatoriamente (32 bytes hex)
- [ ] Domínio apontado para o servidor
- [ ] Firewall configurado (UFW)
- [ ] docker-compose.prod.yml criado com workaround
- [ ] Containers iniciados com sucesso
- [ ] Healthchecks passando (all healthy)
- [ ] Workaround validado (.env copiado corretamente)
- [ ] API acessível via HTTPS
- [ ] SSL certificado Let's Encrypt válido
- [ ] Backup automático configurado (cron)
- [ ] Fail2Ban configurado
- [ ] Monitoramento ativo (logs, métricas)
- [ ] Documentação de runbook criada para equipe

---

## 📞 Suporte

**Documentação Técnica**: `/opt/e2-solucoes-bot/docs/EVOLUTION_API_ISSUE_1474_WORKAROUND.md`

**Logs Produção**:
- Evolution API: `docker logs evolution-api-prod -f`
- PostgreSQL: `docker logs evolution-postgres-prod -f`
- Redis: `docker logs evolution-redis-prod -f`
- Traefik: `docker logs traefik-prod -f`

**Contato Emergência**: [adicionar contato da equipe]

---

**🎯 Última atualização**: 2025-12-16
**📝 Versão**: 1.0
**👤 Autor**: Equipe E2 Soluções
