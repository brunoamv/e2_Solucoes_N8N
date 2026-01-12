#!/bin/bash
# Script de teste end-to-end do Workflow 01 - WhatsApp Handler
# Valida processamento de mensagens e detecção de duplicatas

set -e

N8N_URL="http://localhost:5678"
WEBHOOK_PATH="/webhook/whatsapp-evolution"
WEBHOOK_URL="${N8N_URL}${WEBHOOK_PATH}"

# Cores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=== Teste End-to-End: Workflow 01 - WhatsApp Handler ==="
echo ""

# Função para verificar tabela messages
check_message_in_db() {
  local msg_id=$1
  docker exec e2bot-postgres-dev psql -U postgres -d e2_bot -t -c \
    "SELECT COUNT(*) FROM messages WHERE whatsapp_message_id = '${msg_id}';" 2>/dev/null | tr -d ' '
}

# Teste 1: Mensagem Nova
echo "📝 TESTE 1: Processamento de Mensagem Nova"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

TEST_MESSAGE_ID="TEST_E2E_$(date +%s)_001"
PAYLOAD_1=$(cat <<EOF
{
  "event": "messages.upsert",
  "data": {
    "key": {
      "remoteJid": "5562999887766@s.whatsapp.net",
      "fromMe": false,
      "id": "${TEST_MESSAGE_ID}"
    },
    "pushName": "Usuario Teste E2E",
    "message": {
      "conversation": "Olá, gostaria de informações sobre energia solar residencial."
    }
  }
}
EOF
)

echo "Enviando mensagem para webhook..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${WEBHOOK_URL}" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD_1")

if [ "$HTTP_CODE" == "200" ] || [ "$HTTP_CODE" == "201" ]; then
  echo -e "${GREEN}✅ Webhook respondeu: HTTP ${HTTP_CODE}${NC}"
else
  echo -e "${RED}❌ Webhook falhou: HTTP ${HTTP_CODE}${NC}"
  echo "   URL: ${WEBHOOK_URL}"
  exit 1
fi

echo "Aguardando processamento (3 segundos)..."
sleep 3

# Verificar se mensagem foi salva
MSG_COUNT=$(check_message_in_db "$TEST_MESSAGE_ID")
if [ "$MSG_COUNT" -eq 1 ]; then
  echo -e "${GREEN}✅ Mensagem salva no banco de dados${NC}"

  # Mostrar dados salvos
  echo ""
  echo "Dados salvos:"
  docker exec e2bot-postgres-dev psql -U postgres -d e2_bot -c \
    "SELECT id, direction, LEFT(content, 50) as content, message_type, whatsapp_message_id
     FROM messages
     WHERE whatsapp_message_id = '${TEST_MESSAGE_ID}';" 2>/dev/null
else
  echo -e "${RED}❌ Mensagem NÃO foi salva (esperado: 1, encontrado: ${MSG_COUNT})${NC}"
  exit 1
fi

echo ""

# Teste 2: Mensagem Duplicada
echo "📝 TESTE 2: Detecção de Duplicata"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo "Reenviando MESMA mensagem (ID: ${TEST_MESSAGE_ID})..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${WEBHOOK_URL}" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD_1")

if [ "$HTTP_CODE" == "200" ] || [ "$HTTP_CODE" == "201" ]; then
  echo -e "${GREEN}✅ Webhook respondeu: HTTP ${HTTP_CODE}${NC}"
else
  echo -e "${RED}❌ Webhook falhou: HTTP ${HTTP_CODE}${NC}"
  exit 1
fi

echo "Aguardando processamento (3 segundos)..."
sleep 3

# Verificar se continua com apenas 1 registro
MSG_COUNT=$(check_message_in_db "$TEST_MESSAGE_ID")
if [ "$MSG_COUNT" -eq 1 ]; then
  echo -e "${GREEN}✅ Duplicata detectada corretamente (ainda 1 registro)${NC}"
else
  echo -e "${RED}❌ Duplicata NÃO foi detectada (encontrado: ${MSG_COUNT} registros)${NC}"
  exit 1
fi

echo ""

# Teste 3: Mensagem com Imagem
echo "📝 TESTE 3: Mensagem com Imagem (tipo diferente)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

TEST_IMAGE_ID="TEST_E2E_$(date +%s)_002"
PAYLOAD_3=$(cat <<EOF
{
  "event": "messages.upsert",
  "data": {
    "key": {
      "remoteJid": "5562999887766@s.whatsapp.net",
      "fromMe": false,
      "id": "${TEST_IMAGE_ID}"
    },
    "pushName": "Usuario Teste E2E",
    "message": {
      "imageMessage": {
        "url": "https://example.com/conta-energia.jpg",
        "caption": "Minha conta de energia para análise"
      }
    }
  }
}
EOF
)

echo "Enviando mensagem com imagem..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${WEBHOOK_URL}" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD_3")

if [ "$HTTP_CODE" == "200" ] || [ "$HTTP_CODE" == "201" ]; then
  echo -e "${GREEN}✅ Webhook respondeu: HTTP ${HTTP_CODE}${NC}"
else
  echo -e "${RED}❌ Webhook falhou: HTTP ${HTTP_CODE}${NC}"
  exit 1
fi

echo "Aguardando processamento (3 segundos)..."
sleep 3

# Verificar se mensagem de imagem foi salva
MSG_COUNT=$(check_message_in_db "$TEST_IMAGE_ID")
if [ "$MSG_COUNT" -eq 1 ]; then
  echo -e "${GREEN}✅ Mensagem com imagem salva no banco${NC}"

  echo ""
  echo "Dados da imagem:"
  docker exec e2bot-postgres-dev psql -U postgres -d e2_bot -c \
    "SELECT id, message_type, LEFT(content, 40) as content, media_url
     FROM messages
     WHERE whatsapp_message_id = '${TEST_IMAGE_ID}';" 2>/dev/null
else
  echo -e "${RED}❌ Mensagem com imagem NÃO foi salva${NC}"
  exit 1
fi

echo ""
echo ""

# Sumário Final
echo "=== SUMÁRIO DOS TESTES ==="
echo ""
echo -e "${GREEN}✅ TESTE 1: Mensagem nova processada e salva${NC}"
echo -e "${GREEN}✅ TESTE 2: Duplicata detectada corretamente${NC}"
echo -e "${GREEN}✅ TESTE 3: Mensagem com imagem processada${NC}"
echo ""

# Estatísticas do banco
echo "📊 Estatísticas do Banco de Dados:"
echo ""
docker exec e2bot-postgres-dev psql -U postgres -d e2_bot -c \
  "SELECT
     COUNT(*) as total_mensagens,
     COUNT(DISTINCT whatsapp_message_id) as mensagens_unicas,
     COUNT(CASE WHEN message_type = 'text' THEN 1 END) as texto,
     COUNT(CASE WHEN message_type = 'image' THEN 1 END) as imagens
   FROM messages;" 2>/dev/null

echo ""
echo "=== TODOS OS TESTES PASSARAM ✅ ==="
echo ""
echo "O workflow está funcionando corretamente!"
echo ""
echo "Próximos passos:"
echo "1. Verificar logs do n8n: docker logs e2bot-n8n-dev --tail 50"
echo "2. Testar com WhatsApp real via Evolution API"
echo "3. Atualizar docs/PROJECT_STATUS.md"
