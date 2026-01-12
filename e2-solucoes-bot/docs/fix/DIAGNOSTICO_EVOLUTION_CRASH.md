# Diagnóstico Evolution API - Crash Loop

## 🚨 Problema Crítico Identificado

### Sintomas
1. Evolution API está em **crash loop** contínuo
2. Container inicia, roda migrations, tenta startar e recebe `SIGTERM`
3. Log mostra: `npm error signal SIGTERM`
4. Status: `Up X minutes (health: starting)` - nunca fica `healthy`
5. API retorna 401 Unauthorized para todos os endpoints

### Root Cause Analysis

**Análise dos Logs**:
```
create instance {
  instanceName: 'e2-solucoes-bot',
  qrcode: true,
  integration: 'WHATSAPP-BAILEYS'
}
npm error path /evolution
npm error command failed
npm error signal SIGTERM
npm error command sh -c node dist/main
```

**Padrão Observado**:
1. Evolution API inicia migrations ✅
2. Gera Prisma client ✅
3. Executa `node dist/main` ✅
4. Cria instância 'e2-solucoes-bot' ✅
5. **Recebe SIGTERM e crashloop** ❌

### Possíveis Causas

**Hipótese #1: Instância WhatsApp corrompida** (MAIS PROVÁVEL)
- Log mostra: `stream errored out (code 515, 503, 401)`
- Erro: `device_removed` em logs antigos
- Problema: Sessão WhatsApp desconectada ou corrompida

**Hipótese #2: Memória/CPU insuficiente**
- Evolution processando mensagens antigas (`recv 0 chats, 0 contacts, 9848 msgs`)
- Pode estar esgotando recursos

**Hipótese #3: Redis/PostgreSQL instável**
- Menos provável (healthchecks passando)

## ✅ Solução Completa

### Opção A: Recriar Instância Evolution (RECOMENDADO)

**Problema**: A instância `e2-solucoes-bot` está corrompida e causando crashes.

**Solução**: Deletar volume de instâncias e recriar limpa.

```bash
# 1. Parar Evolution
docker-compose -f docker/docker-compose-dev.yml stop evolution-api

# 2. Remover volume de instâncias corrompidas
docker volume rm e2bot_evolution_instances
docker volume rm e2bot_evolution_store

# 3. Reiniciar Evolution
docker-compose -f docker/docker-compose-dev.yml up -d evolution-api

# 4. Monitorar logs
docker logs -f e2bot-evolution-dev

# 5. Aguardar Evolution ficar healthy (60-90s)
watch -n 3 'docker ps --filter "name=evolution" --format "{{.Status}}"'

# 6. Criar nova instância e conectar WhatsApp
# Usar script helper ou API manual
```

**Criar Nova Instância** (após Evolution estabilizar):
```bash
# Via API
curl -X POST "http://localhost:8080/instance/create" \
  -H "apikey: ae569043cfa169380c378347f91a1141ea572541d2d1cadbed222db519c8a891" \
  -H "Content-Type: application/json" \
  -d '{
    "instanceName": "e2-solucoes-bot",
    "qrcode": true,
    "integration": "WHATSAPP-BAILEYS"
  }'

# Gerar QR Code
curl -X GET "http://localhost:8080/instance/connect/e2-solucoes-bot" \
  -H "apikey: ae569043cfa169380c378347f91a1141ea572541d2d1cadbed222db519c8a891"

# Salvar QR Code retornado em qrcode.png e escanear com WhatsApp
```

### Opção B: Aumentar Recursos (se Opção A falhar)

```yaml
# docker-compose-dev.yml
evolution-api:
  deploy:
    resources:
      limits:
        cpus: '2'
        memory: 2G
      reservations:
        cpus: '1'
        memory: 1G
```

### Opção C: Limpar Cache Redis (se ainda crashar)

```bash
# Conectar no Redis
docker exec -it e2bot-evolution-redis redis-cli

# Limpar todas as keys da Evolution
KEYS evolution:*
# Para cada key retornada:
DEL evolution:instances:e2-solucoes-bot
FLUSHDB  # OU limpar tudo se necessário

# Reiniciar Evolution
docker-compose -f docker/docker-compose-dev.yml restart evolution-api
```

## 🔍 Validação Pós-Correção

### 1. Verificar Evolution Healthy
```bash
# Deve mostrar "healthy" após 60-90s
docker ps --filter "name=evolution" --format "{{.Names}}\t{{.Status}}"
```

### 2. Testar API
```bash
curl -f http://localhost:8080
# Deve retornar: {"status":200,"message":"Welcome to the Evolution API..."}
```

### 3. Listar Instâncias
```bash
API_KEY="ae569043cfa169380c378347f91a1141ea572541d2d1cadbed222db519c8a891"
curl -s -X GET "http://localhost:8080/instance/fetchInstances" \
  -H "apikey: $API_KEY" | jq .
```

### 4. Verificar Webhook Global (Correção Aplicada)
```bash
docker exec e2bot-evolution-dev env | grep WEBHOOK_GLOBAL_URL
# Deve mostrar: WEBHOOK_GLOBAL_URL=http://e2bot-n8n-dev:5678/webhook/whatsapp-evolution
```

### 5. Testar Fluxo WhatsApp → n8n
```bash
# 1. Enviar "oi" do WhatsApp para número logado
# 2. Monitorar n8n
docker logs -f e2bot-n8n-dev 2>&1 | grep -E "whatsapp-evolution|Webhook WhatsApp"

# 3. Verificar execuções
# Abrir: http://localhost:5678/home/executions
```

## 📊 Status Atual

- ✅ **Webhook URL Corrigido**: docker-compose linha 178 atualizada para `/webhook/whatsapp-evolution`
- ❌ **Evolution Crashloop**: Instância corrompida causando SIGTERM repetidos
- ⏳ **Próximo Passo**: Aplicar Solução Opção A (recriar instância limpa)

## 🎯 Plano de Ação Imediato

1. **CRÍTICO**: Executar Opção A - Recriar instância Evolution
2. **VALIDAR**: Aguardar Evolution ficar healthy
3. **CRIAR**: Nova instância WhatsApp e escanear QR Code
4. **TESTAR**: Fluxo completo WhatsApp → Webhook → n8n → Bot

---
**Data**: 2026-01-02 18:21
**Webhook**: Corrigido
**Evolution**: Crashloop - Aguardando recriação de instância
