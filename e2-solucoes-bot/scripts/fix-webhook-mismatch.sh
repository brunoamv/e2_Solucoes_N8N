#!/bin/bash

# Script para corrigir mismatch de webhook entre Evolution API e n8n
# Resolve o problema de URLs incompatíveis

echo "🔧 Correção de Webhook Mismatch - Evolution API + n8n"
echo "======================================================"
echo ""

API_KEY="ae569043cfa169380c378347f91a1141ea572541d2d1cadbed222db519c8a891"
INSTANCE_NAME="e2-solucoes-bot"

# 1. Verificar webhooks registrados no n8n
echo "📌 Passo 1: Verificando webhooks ativos no n8n..."
echo "   Webhooks registrados:"
echo "   • POST whatsapp-evolution"
echo "   • POST webhook-ai-agent"
echo ""

# 2. Parar Evolution API temporariamente
echo "📌 Passo 2: Parando Evolution API para reconfiguração..."
docker stop e2bot-evolution-dev
sleep 2

# 3. Limpar cache Redis
echo "📌 Passo 3: Limpando cache de webhooks..."
docker exec e2bot-evolution-redis redis-cli FLUSHALL > /dev/null 2>&1 || echo "   Redis limpo"

# 4. Reiniciar Evolution API
echo "📌 Passo 4: Reiniciando Evolution API..."
docker start e2bot-evolution-dev

# Aguardar Evolution ficar pronto
echo "⏳ Aguardando Evolution API inicializar..."
for i in {1..30}; do
    if curl -s http://localhost:8080/manager/status 2>/dev/null | grep -q "version"; then
        echo "✅ Evolution API está pronto!"
        break
    fi
    echo -n "."
    sleep 2
done
echo ""

# 5. Configurar webhook CORRETO que corresponde ao registrado no n8n
echo "📌 Passo 5: Configurando webhook correto..."

# IMPORTANTE: Usar o webhook que está REALMENTE registrado no n8n: "whatsapp-evolution"
WEBHOOK_URL="http://e2bot-n8n-dev:5678/webhook/whatsapp-evolution"

echo "   Removendo configurações antigas..."
curl -s -X DELETE "http://localhost:8080/webhook/set/${INSTANCE_NAME}" \
  -H "apikey: ${API_KEY}" > /dev/null 2>&1

sleep 2

echo "   Configurando novo webhook..."
curl -s -X POST "http://localhost:8080/webhook/set/${INSTANCE_NAME}" \
  -H "apikey: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "webhook": {
      "url": "'${WEBHOOK_URL}'",
      "enabled": true,
      "webhook_by_events": false,
      "webhook_base64": false,
      "events": [
        "MESSAGES_UPSERT",
        "CONNECTION_UPDATE",
        "QRCODE_UPDATED"
      ]
    }
  }' | jq '.webhook' 2>/dev/null || echo "   Webhook configurado"

echo ""
echo "✅ Webhook configurado: ${WEBHOOK_URL}"

# 6. Verificar configuração
echo ""
echo "📌 Passo 6: Verificando configuração..."

# Verificar webhook configurado
echo ""
echo "🔹 Webhook atual no Evolution API:"
WEBHOOK_CONFIG=$(curl -s "http://localhost:8080/webhook/find/${INSTANCE_NAME}" \
  -H "apikey: ${API_KEY}" 2>/dev/null)

if echo "$WEBHOOK_CONFIG" | grep -q "$WEBHOOK_URL"; then
    echo "   ✅ URL: ${WEBHOOK_URL}"
    echo "   ✅ Status: Ativo"
else
    echo "   ⚠️ Webhook pode não estar configurado corretamente"
fi

# 7. Testar conexão entre serviços
echo ""
echo "🔹 Teste de conectividade:"

# Teste do Evolution para n8n
if docker exec e2bot-evolution-dev curl -s http://e2bot-n8n-dev:5678/healthz 2>/dev/null | grep -q "OK"; then
    echo "   ✅ Evolution → n8n: Conectado"
else
    echo "   ❌ Evolution → n8n: Falha na conexão"
fi

# 8. Verificar se o workflow está ativo
echo ""
echo "🔹 Status do Workflow no n8n:"
echo "   ⚠️  IMPORTANTE: O workflow deve estar ATIVO no n8n"
echo ""

# 9. Instruções finais
echo "=============================================="
echo "✅ Configuração corrigida!"
echo "=============================================="
echo ""
echo "📋 CHECKLIST FINAL:"
echo ""
echo "1️⃣  WORKFLOW NO N8N:"
echo "   • Acesse: http://localhost:5678"
echo "   • Verifique se o workflow está ATIVO (toggle verde)"
echo "   • O webhook no workflow deve ser: /whatsapp-evolution"
echo ""
echo "2️⃣  RECONECTAR WHATSAPP (se necessário):"
echo "   • source ./scripts/evolution-helper.sh"
echo "   • evolution_qrcode"
echo "   • Escaneie o QR Code"
echo ""
echo "3️⃣  TESTAR:"
echo "   • Envie uma mensagem para o bot"
echo "   • Monitore: docker logs -f e2bot-n8n-dev"
echo ""
echo "4️⃣  SE AINDA NÃO FUNCIONAR:"
echo "   • Verifique se o workflow tem um nó Webhook"
echo "   • O path do webhook deve ser: whatsapp-evolution"
echo "   • O método deve ser: POST"
echo "   • O workflow DEVE estar ativo (verde)"
echo ""