#!/bin/bash

# Script para corrigir loop de webhooks entre Evolution API e n8n
# Problema: Evolution API fazendo retry infinito causando múltiplas execuções

echo "🔧 Corrigindo loop de webhooks Evolution API ↔ n8n"
echo ""

# 1. Parar serviços para limpar estado
echo "📌 Passo 1: Parando serviços..."
docker stop e2bot-evolution-dev e2bot-n8n-dev

# 2. Aguardar para garantir que tudo parou
echo "⏳ Aguardando 5 segundos..."
sleep 5

# 3. Limpar Redis cache (onde Evolution guarda fila de webhooks)
echo "📌 Passo 2: Limpando cache Redis..."
docker exec e2bot-evolution-redis redis-cli FLUSHALL

# 4. Verificar configuração de webhook no docker-compose
echo "📌 Passo 3: Verificando configuração de webhook..."

# Webhook URL atual
WEBHOOK_URL="http://e2bot-n8n-dev:5678/webhook/whatsapp-evolution"
echo "   Webhook URL: $WEBHOOK_URL"

# 5. Iniciar n8n primeiro
echo "📌 Passo 4: Iniciando n8n..."
docker start e2bot-n8n-dev

# Aguardar n8n ficar healthy
echo "⏳ Aguardando n8n ficar pronto..."
for i in {1..30}; do
    if docker exec e2bot-n8n-dev wget --spider -q http://localhost:5678/healthz 2>/dev/null; then
        echo "✅ n8n está pronto!"
        break
    fi
    echo -n "."
    sleep 1
done
echo ""

# 6. Iniciar Evolution API
echo "📌 Passo 5: Iniciando Evolution API..."
docker start e2bot-evolution-dev

# Aguardar Evolution API
echo "⏳ Aguardando Evolution API..."
sleep 10

# 7. Verificar status
echo "📌 Passo 6: Verificando status dos serviços..."
docker ps | grep e2bot | grep -E "(n8n|evolution)"

# 8. Configurar webhook com timeout maior
echo "📌 Passo 7: Ajustando configuração de webhook..."

# API Key
API_KEY="ae569043cfa169380c378347f91a1141ea572541d2d1cadbed222db519c8a891"
INSTANCE_NAME="e2-solucoes-bot"

# Desabilitar webhook temporariamente
echo "   Desabilitando webhook temporariamente..."
curl -s -X POST "http://localhost:8080/webhook/set/${INSTANCE_NAME}" \
  -H "apikey: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "webhook": {
      "enabled": false
    }
  }' > /dev/null 2>&1

sleep 2

# Reconfigurar webhook com parâmetros otimizados
echo "   Reconfigurando webhook com timeout maior..."
curl -s -X POST "http://localhost:8080/webhook/set/${INSTANCE_NAME}" \
  -H "apikey: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "webhook": {
      "url": "'${WEBHOOK_URL}'",
      "enabled": true,
      "webhook_by_events": true,
      "webhook_base64": false,
      "events": [
        "MESSAGES_UPSERT",
        "MESSAGES_UPDATE",
        "CONNECTION_UPDATE",
        "QRCODE_UPDATED"
      ]
    }
  }' > /dev/null 2>&1

echo ""
echo "✅ Correção aplicada!"
echo ""
echo "📋 Ações realizadas:"
echo "   1. Serviços reiniciados"
echo "   2. Cache Redis limpo"
echo "   3. Webhook reconfigurado"
echo ""
echo "⚠️  IMPORTANTE:"
echo "   1. Acesse http://localhost:5678"
echo "   2. Verifique se os workflows estão ativos"
echo "   3. Desative workflows duplicados"
echo "   4. Mantenha apenas 1 workflow ativo por vez"
echo ""
echo "🎯 Próximos passos:"
echo "   1. Monitore os logs: docker logs -f e2bot-n8n-dev"
echo "   2. Se houver novo loop, execute este script novamente"
echo ""