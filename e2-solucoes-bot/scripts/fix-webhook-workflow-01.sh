#!/bin/bash

# Script para configurar corretamente o webhook para Workflow 01
# Resolve o problema de webhook não encontrado (404)

echo "🔧 Configuração Correta do Webhook para Workflow 01"
echo "===================================================="
echo ""

API_KEY="ae569043cfa169380c378347f91a1141ea572541d2d1cadbed222db519c8a891"
INSTANCE_NAME="e2-solucoes-bot"

# IMPORTANTE: O webhook correto para Workflow 01 é webhook-test
# Baseado no erro visto nos logs e na estrutura do workflow
WEBHOOK_URL="http://e2bot-n8n-dev:5678/webhook-test/whatsapp-handler"

echo "📌 Passo 1: Verificando status da Evolution API..."
if curl -s http://localhost:8080/manager/status 2>/dev/null | grep -q "version"; then
    echo "✅ Evolution API está rodando"
else
    echo "⚠️ Evolution API ainda está inicializando, aguardando..."
    for i in {1..30}; do
        if curl -s http://localhost:8080/manager/status 2>/dev/null | grep -q "version"; then
            echo "✅ Evolution API está pronto!"
            break
        fi
        echo -n "."
        sleep 2
    done
fi

echo ""
echo "📌 Passo 2: Removendo webhook antigo..."
curl -s -X DELETE "http://localhost:8080/webhook/set/${INSTANCE_NAME}" \
  -H "apikey: ${API_KEY}" > /dev/null 2>&1

sleep 2

echo "📌 Passo 3: Configurando novo webhook..."
echo "   URL: ${WEBHOOK_URL}"

RESPONSE=$(curl -s -X POST "http://localhost:8080/webhook/set/${INSTANCE_NAME}" \
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
  }')

if echo "$RESPONSE" | grep -q "webhook"; then
    echo "✅ Webhook configurado com sucesso!"
    echo "$RESPONSE" | jq '.webhook' 2>/dev/null || echo "$RESPONSE"
else
    echo "❌ Erro ao configurar webhook:"
    echo "$RESPONSE"
fi

echo ""
echo "📌 Passo 4: Verificando configuração..."

WEBHOOK_CONFIG=$(curl -s "http://localhost:8080/webhook/find/${INSTANCE_NAME}" \
  -H "apikey: ${API_KEY}" 2>/dev/null)

if echo "$WEBHOOK_CONFIG" | grep -q "$WEBHOOK_URL"; then
    echo "✅ Webhook configurado corretamente!"
    echo "   URL: ${WEBHOOK_URL}"
else
    echo "⚠️ Webhook pode não estar configurado corretamente"
    echo "$WEBHOOK_CONFIG" | jq '.webhook.url' 2>/dev/null
fi

echo ""
echo "📌 Passo 5: Verificando conexão do WhatsApp..."
STATUS=$(curl -s "http://localhost:8080/instance/connectionState/${INSTANCE_NAME}" \
  -H "apikey: ${API_KEY}" 2>/dev/null | jq -r '.state' 2>/dev/null)

if [ "$STATUS" = "open" ]; then
    echo "✅ WhatsApp conectado!"
else
    echo "⏳ WhatsApp desconectado. Estado: $STATUS"
    echo ""
    echo "Para conectar o WhatsApp:"
    echo "1. Execute: source ./scripts/evolution-helper.sh"
    echo "2. Execute: evolution_qrcode"
    echo "3. Escaneie o QR Code com seu WhatsApp"
fi

echo ""
echo "=============================================="
echo "✅ Configuração concluída!"
echo "=============================================="
echo ""
echo "⚠️ IMPORTANTE - Verifique no n8n:"
echo ""
echo "1. Acesse: http://localhost:5678"
echo "2. Abra o Workflow 01 - Main WhatsApp Handler"
echo "3. Verifique se o nó Webhook tem:"
echo "   • Path: webhook-test/whatsapp-handler"
echo "   • Method: POST"
echo "4. ATIVE o workflow (toggle verde)"
echo ""
echo "Para testar:"
echo "• Envie uma mensagem para o bot no WhatsApp"
echo "• Monitore: docker logs -f e2bot-n8n-dev"
echo ""