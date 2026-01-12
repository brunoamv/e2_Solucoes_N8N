#!/bin/bash

# Script para corrigir integração webhook Evolution API + n8n
# Resolve: Erro 404, webhook não registrado, sessão corrompida

echo "🔧 Correção Completa: Evolution API + n8n Integration"
echo "======================================================"
echo ""

# 1. Parar serviços para reset completo
echo "📌 Passo 1: Parando serviços para reset..."
docker stop e2bot-evolution-dev e2bot-n8n-dev
sleep 3

# 2. Limpar dados de sessão corrompidos
echo "📌 Passo 2: Limpando dados de sessão do WhatsApp..."
docker exec e2bot-evolution-dev rm -rf /evolution/instances/e2-solucoes-bot/session 2>/dev/null || true
docker exec e2bot-evolution-dev rm -rf /evolution/store/e2-solucoes-bot 2>/dev/null || true

# 3. Limpar cache Redis
echo "📌 Passo 3: Limpando cache Redis..."
docker exec e2bot-evolution-redis redis-cli FLUSHALL 2>/dev/null || echo "Redis não acessível"

# 4. Reiniciar Evolution API
echo "📌 Passo 4: Reiniciando Evolution API..."
docker start e2bot-evolution-dev

# Aguardar Evolution API ficar pronto
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

# 5. Reiniciar n8n
echo "📌 Passo 5: Reiniciando n8n..."
docker start e2bot-n8n-dev

# Aguardar n8n ficar pronto
echo "⏳ Aguardando n8n inicializar..."
for i in {1..30}; do
    if docker exec e2bot-n8n-dev wget --spider -q http://localhost:5678/healthz 2>/dev/null; then
        echo "✅ n8n está pronto!"
        break
    fi
    echo -n "."
    sleep 1
done
echo ""

# 6. Recriar instância no Evolution API
echo "📌 Passo 6: Recriando instância no Evolution API..."

API_KEY="ae569043cfa169380c378347f91a1141ea572541d2d1cadbed222db519c8a891"
INSTANCE_NAME="e2-solucoes-bot"

# Deletar instância se existir
echo "   Removendo instância antiga..."
curl -s -X DELETE "http://localhost:8080/instance/delete/${INSTANCE_NAME}" \
  -H "apikey: ${API_KEY}" > /dev/null 2>&1

sleep 2

# Criar nova instância
echo "   Criando nova instância..."
curl -s -X POST "http://localhost:8080/instance/create" \
  -H "apikey: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "instanceName": "'${INSTANCE_NAME}'",
    "qrcode": true,
    "integration": "WHATSAPP-BAILEYS"
  }' > /dev/null 2>&1

sleep 3

# 7. Configurar webhook correto
echo "📌 Passo 7: Configurando webhook para Workflow 01..."

# Webhook deve apontar para Workflow 01, não para um webhook genérico
WEBHOOK_URL="http://e2bot-n8n-dev:5678/webhook-test/whatsapp-handler"

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

echo "✅ Webhook configurado: ${WEBHOOK_URL}"

# 8. Verificar status
echo ""
echo "📌 Passo 8: Verificando status dos serviços..."
echo ""

# Status Evolution API
echo "🔹 Evolution API:"
curl -s http://localhost:8080/manager/status | jq '.version' 2>/dev/null && echo "   Status: ✅ Online" || echo "   Status: ❌ Offline"

# Status n8n
echo ""
echo "🔹 n8n:"
if curl -s http://localhost:5678/healthz 2>/dev/null | grep -q "OK"; then
    echo "   Status: ✅ Online"
else
    echo "   Status: ❌ Offline"
fi

# Status da instância
echo ""
echo "🔹 Instância WhatsApp:"
STATUS=$(curl -s "http://localhost:8080/instance/connectionState/${INSTANCE_NAME}" \
  -H "apikey: ${API_KEY}" 2>/dev/null | jq -r '.state' 2>/dev/null)

if [ "$STATUS" = "open" ]; then
    echo "   Status: ✅ Conectado"
else
    echo "   Status: ⏳ Aguardando conexão (escaneie o QR Code)"
fi

echo ""
echo "=============================================="
echo "✅ Correção aplicada com sucesso!"
echo "=============================================="
echo ""
echo "⚠️  IMPORTANTE - Próximos passos:"
echo ""
echo "1️⃣  ATIVAR WORKFLOW NO N8N:"
echo "   • Acesse: http://localhost:5678"
echo "   • Importe o workflow: 01_main_whatsapp_handler.json"
echo "   • ATIVE o workflow (toggle no canto superior direito)"
echo "   • O webhook path deve ser: /webhook-test/whatsapp-handler"
echo ""
echo "2️⃣  CONECTAR WHATSAPP:"
echo "   • Execute: ./scripts/evolution-helper.sh"
echo "   • Use o comando: evolution_qrcode"
echo "   • Escaneie o QR Code com seu WhatsApp"
echo ""
echo "3️⃣  MONITORAR LOGS:"
echo "   • n8n: docker logs -f e2bot-n8n-dev"
echo "   • Evolution: docker logs -f e2bot-evolution-dev"
echo ""
echo "4️⃣  TESTAR:"
echo "   • Envie uma mensagem para o número do bot"
echo "   • Verifique se aparece no n8n"
echo ""