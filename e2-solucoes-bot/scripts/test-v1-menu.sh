#!/bin/bash
# Teste do Workflow 02 - AI Agent Conversation V1 (Menu-Based)

set -e

N8N_URL="http://localhost:5678"
EVOLUTION_URL="http://localhost:8080"
API_KEY="ae569043cfa169380c378347f91a1141ea572541d2d1cadbed222db519c8a891"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🧪 Teste do Workflow 02 - AI Agent Conversation V1"
echo "======================================================================="

# 1. Verificar serviços
echo "🔍 Verificando serviços..."
if ! curl -s "$N8N_URL/healthz" > /dev/null 2>&1; then
    echo -e "${RED}❌ n8n não está rodando${NC}"
    exit 1
fi
echo -e "${GREEN}✅ n8n acessível${NC}"

if ! curl -s "$EVOLUTION_URL" > /dev/null 2>&1; then
    echo -e "${RED}❌ Evolution API não está rodando${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Evolution API acessível${NC}"

# 2. Limpar dados de teste anteriores
echo ""
echo "🧹 Limpando dados de teste anteriores..."
docker exec e2bot-postgres-dev psql -U postgres -d e2_bot -c "DELETE FROM messages WHERE phone_number = '5562999999999';" 2>/dev/null || true
docker exec e2bot-postgres-dev psql -U postgres -d e2_bot -c "DELETE FROM conversations WHERE phone_number = '5562999999999';" 2>/dev/null || true
echo -e "${GREEN}✅ Dados limpos${NC}"

# 3. Enviar mensagem de teste
echo ""
echo "📱 Enviando mensagem de teste para WhatsApp..."
PHONE_TEST="5562999999999"
MESSAGE_TEST="Olá"

# Simular webhook do WhatsApp
PAYLOAD=$(cat <<EOF
{
  "phone_number": "$PHONE_TEST",
  "content": "$MESSAGE_TEST",
  "from": "$PHONE_TEST",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%S.000Z)"
}
EOF
)

# Chamar webhook do Workflow 01
RESPONSE=$(curl -s -X POST \
  "$N8N_URL/webhook/whatsapp-messages" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD")

echo -e "${GREEN}✅ Mensagem enviada${NC}"
echo "   Resposta: $RESPONSE"

# 4. Aguardar processamento
echo ""
echo "⏳ Aguardando processamento (5 segundos)..."
sleep 5

# 5. Verificar dados no banco
echo ""
echo "🔍 Verificando dados no PostgreSQL..."

# Verificar conversation criada
CONV_COUNT=$(docker exec e2bot-postgres-dev psql -U postgres -d e2_bot -t -c \
  "SELECT COUNT(*) FROM conversations WHERE phone_number = '$PHONE_TEST';")

if [ "$CONV_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✅ Conversation criada${NC}"
    
    # Mostrar detalhes
    docker exec e2bot-postgres-dev psql -U postgres -d e2_bot -c \
      "SELECT phone_number, current_state, collected_data, created_at FROM conversations WHERE phone_number = '$PHONE_TEST';"
else
    echo -e "${RED}❌ Conversation NÃO foi criada${NC}"
fi

# Pegar conversation_id primeiro
CONV_ID=$(docker exec e2bot-postgres-dev psql -U postgres -d e2_bot -t -c \
  "SELECT id FROM conversations WHERE phone_number = '$PHONE_TEST';" | xargs)

# Verificar mensagens salvas (usando conversation_id)
if [ -n "$CONV_ID" ]; then
    MSG_COUNT=$(docker exec e2bot-postgres-dev psql -U postgres -d e2_bot -t -c \
      "SELECT COUNT(*) FROM messages WHERE conversation_id = '$CONV_ID';")
else
    MSG_COUNT=0
    echo -e "${RED}⚠️  Sem conversation_id - não foi possível verificar mensagens${NC}"
fi

echo ""
if [ "$MSG_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✅ Mensagens salvas ($MSG_COUNT)${NC}"

    # Mostrar mensagens (usando conversation_id)
    if [ -n "$CONV_ID" ]; then
        docker exec e2bot-postgres-dev psql -U postgres -d e2_bot -c \
          "SELECT direction, content, created_at FROM messages WHERE conversation_id = '$CONV_ID' ORDER BY created_at;"
    fi
else
    echo -e "${RED}❌ Mensagens NÃO foram salvas${NC}"
fi

# 6. Verificar logs do n8n
echo ""
echo "📋 Últimas execuções do n8n:"
echo "   Acesse: $N8N_URL/executions"
echo ""
echo "======================================================================="
echo -e "${YELLOW}📝 PRÓXIMOS PASSOS:${NC}"
echo "1. Acesse http://localhost:5678/executions para ver detalhes da execução"
echo "2. Verifique se a mensagem de boas-vindas foi enviada no WhatsApp"
echo "3. Se houver erros, verifique os logs detalhados no n8n"
echo "======================================================================="
