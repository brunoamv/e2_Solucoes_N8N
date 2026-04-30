# Solução Completa - Webhook Evolution API

## 🎯 Problemas Identificados

### Problema #1: Discrepância de URLs de Webhook ❌

**No docker-compose (linha 178):**
```yaml
WEBHOOK_GLOBAL_URL=http://e2bot-n8n-dev:5678/webhook/whatsapp-messages
```

**No workflow 01 (linha 7):**
```json
"path": "whatsapp-evolution"
```

**Resultado**: Evolution envia para `/webhook/whatsapp-messages`, mas n8n escuta em `/webhook/whatsapp-evolution`

### Problema #2: Evolution API Unhealthy ⚠️

**Status**: `Up 32 minutes (unhealthy)`

**Causa**: Evolution está crashando após criar instância:
```
create instance { instanceName: 'e2-solucoes-bot', qrcode: true }
stream errored out (code 515)
```

**Motivo**: Conexão WhatsApp instável ou configuração de webhook incorreta causando crashes

### Problema #3: Webhook Duplicate ❓

Existem **dois** sistemas de webhook configuráveis no Evolution API v2.2.3:

1. **WEBHOOK_GLOBAL**: Webhook para TODAS as instâncias (docker-compose)
2. **Instance Webhook**: Webhook PER-INSTANCE (via API)

## ✅ Solução Completa

### Opção A: Usar Webhook Global (RECOMENDADO)

**Vantagens:**
- Mais simples
- Configurado uma vez
- Funciona para múltiplas instâncias

**Passo 1: Corrigir docker-compose**

Editar `/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/docker/docker-compose-dev.yml`:

```yaml
# Linha 178 - ANTES:
- WEBHOOK_GLOBAL_URL=http://e2bot-n8n-dev:5678/webhook/whatsapp-messages

# DEPOIS:
- WEBHOOK_GLOBAL_URL=http://e2bot-n8n-dev:5678/webhook/whatsapp-evolution
```

**Passo 2: Reiniciar Evolution**

```bash
docker-compose -f docker/docker-compose-dev.yml restart evolution-api
```

**Passo 3: Validar**

```bash
# Ver logs do Evolution
docker logs -f e2bot-evolution-dev

# Enviar mensagem "oi" do WhatsApp
# Ver se webhook aparece nos logs do n8n
docker logs -f e2bot-n8n-dev | grep "whatsapp-evolution"
```

### Opção B: Configurar Webhook por Instância

**Vantagens:**
- Mais controle granular
- Pode ter webhooks diferentes por instância

**Passo 1: Desabilitar Webhook Global**

```yaml
# docker-compose-dev.yml linha 179:
- WEBHOOK_GLOBAL_ENABLED=false
```

**Passo 2: Configurar Webhook na Instância**

Criar script `scripts/setup-evolution-webhook.sh`:

```bash
#!/bin/bash

EVOLUTION_API_URL="http://localhost:8080"
EVOLUTION_API_KEY="${EVOLUTION_API_KEY}"
INSTANCE_NAME="e2-solucoes-bot"
N8N_WEBHOOK_URL="http://e2bot-n8n-dev:5678/webhook/whatsapp-evolution"

# Configurar webhook da instância
curl -X POST "${EVOLUTION_API_URL}/webhook/set/${INSTANCE_NAME}" \
  -H "apikey: ${EVOLUTION_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "webhook": {
      "url": "'"${N8N_WEBHOOK_URL}"'",
      "enabled": true,
      "webhook_by_events": true,
      "webhook_base64": false,
      "events": [
        "MESSAGES_UPSERT",
        "MESSAGES_UPDATE",
        "CONNECTION_UPDATE"
      ]
    }
  }'
```

**Passo 3: Executar**

```bash
chmod +x scripts/setup-evolution-webhook.sh
./scripts/setup-evolution-webhook.sh
```

## 🔍 Diagnóstico e Validação

### Verificar Webhook Configurado

```bash
# Opção A: Webhook Global
docker exec e2bot-evolution-dev env | grep WEBHOOK

# Opção B: Webhook da Instância
curl -X GET "http://localhost:8080/webhook/find/e2-solucoes-bot" \
  -H "apikey: ${EVOLUTION_API_KEY}"
```

### Testar Webhook Manualmente

```bash
# Enviar teste diretamente para o n8n
curl -X POST "http://localhost:5678/webhook/whatsapp-evolution" \
  -H "Content-Type: application/json" \
  -d '{
    "event": "messages.upsert",
    "instance": "e2-solucoes-bot",
    "data": {
      "key": {
        "remoteJid": "5562999887766@s.whatsapp.net",
        "id": "TEST123"
      },
      "message": {
        "conversation": "oi"
      }
    }
  }'

# Ver se n8n processou:
docker logs e2bot-n8n-dev 2>&1 | grep -A5 "whatsapp-evolution"
```

### Verificar Health do Evolution

```bash
# Status atual
docker ps --filter "name=evolution" --format "{{.Names}}\t{{.Status}}"

# Logs recentes
docker logs --tail 100 e2bot-evolution-dev

# Healthcheck
curl -f http://localhost:8080/ && echo "OK" || echo "FAIL"
```

## 🚀 Plano de Ação Recomendado

### 1️⃣ URGENTE: Corrigir Webhook Global (Opção A)

```bash
# 1. Parar Evolution
docker-compose -f docker/docker-compose-dev.yml stop evolution-api

# 2. Editar docker-compose-dev.yml
# Alterar linha 178:
# WEBHOOK_GLOBAL_URL=http://e2bot-n8n-dev:5678/webhook/whatsapp-evolution

# 3. Reiniciar
docker-compose -f docker/docker-compose-dev.yml up -d evolution-api

# 4. Verificar logs
docker logs -f e2bot-evolution-dev
```

### 2️⃣ Validar Instância WhatsApp

```bash
# Verificar status da instância
curl -s -X GET "http://localhost:8080/instance/fetchInstances" \
  -H "apikey: ${EVOLUTION_API_KEY}" | jq .

# Verificar conexão
curl -s -X GET "http://localhost:8080/instance/connectionState/e2-solucoes-bot" \
  -H "apikey: ${EVOLUTION_API_KEY}" | jq .

# Se desconectado, reconectar:
curl -X GET "http://localhost:8080/instance/connect/e2-solucoes-bot" \
  -H "apikey: ${EVOLUTION_API_KEY}"
```

### 3️⃣ Testar Fluxo Completo

```bash
# 1. Enviar "oi" do WhatsApp para o número logado

# 2. Ver webhook sendo recebido
docker logs -f e2bot-n8n-dev 2>&1 | grep "whatsapp-evolution"

# 3. Ver workflow executando
docker logs -f e2bot-n8n-dev 2>&1 | grep -E "Workflow execution|Extract Message"

# 4. Verificar execuções no n8n
# Abrir: http://localhost:5678/home/executions
```

## 📊 Checklist de Validação

- [ ] Evolution API status: `healthy`
- [ ] Webhook global configurado: `http://e2bot-n8n-dev:5678/webhook/whatsapp-evolution`
- [ ] Instância WhatsApp conectada: `state.connection = 'open'`
- [ ] n8n recebe webhook: logs mostram `Received webhook POST for path "whatsapp-evolution"`
- [ ] Workflow 01 executa: logs mostram `Extract Message Data`, `Save Inbound Message`
- [ ] Workflow 02 é chamado: logs mostram `Trigger AI Agent`, execução do workflow 02
- [ ] Resposta retorna: mensagem do bot aparece no WhatsApp

## 🔧 Troubleshooting

### Se Evolution continuar unhealthy:

```bash
# Verificar logs de erro
docker logs e2bot-evolution-dev 2>&1 | grep -i error

# Reiniciar completamente
docker-compose -f docker/docker-compose-dev.yml down
docker-compose -f docker/docker-compose-dev.yml up -d

# Verificar conectividade Redis
docker exec e2bot-evolution-redis redis-cli ping

# Verificar conectividade PostgreSQL
docker exec e2bot-evolution-postgres pg_isready
```

### Se webhook não chegar:

```bash
# 1. Verificar se Evolution está enviando
docker logs e2bot-evolution-dev | grep -i webhook

# 2. Verificar rede Docker
docker network inspect e2bot-dev-network

# 3. Testar conectividade Evolution → n8n
docker exec e2bot-evolution-dev curl -v http://e2bot-n8n-dev:5678/webhook/whatsapp-evolution
```

### Se workflow não executar:

```bash
# Ver erro específico no n8n
docker logs e2bot-n8n-dev 2>&1 | grep -i error | tail -20

# Verificar se webhook está ativo
# Abrir: http://localhost:5678 → Workflow 01 → Webhook node → Test URL
```

---
**Data**: 2026-01-02 18:45
**Status**: Aguardando aplicação da correção do webhook global
**Próximo passo**: Editar docker-compose-dev.yml e reiniciar Evolution
