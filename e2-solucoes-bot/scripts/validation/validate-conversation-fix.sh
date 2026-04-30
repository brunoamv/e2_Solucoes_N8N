#!/bin/bash

# Script de validação da correção de conversation_id
# Data: 2026-01-12

echo "═══════════════════════════════════════════════════════════════"
echo "   🔍 VALIDAÇÃO DA CORREÇÃO DE CONVERSATION_ID"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Cores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 1. Verificar se o arquivo corrigido existe
echo "📁 Verificando arquivo corrigido..."
echo ""

if [ -f "/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V19_CONVERSATION_ID_FIXED.json" ]; then
    echo -e "${GREEN}✅ Workflow V19 corrigido encontrado${NC}"
else
    echo -e "${RED}❌ Workflow V19 corrigido NÃO encontrado${NC}"
    exit 1
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "📊 Verificando banco de dados..."
echo ""

# 2. Verificar conversas existentes
CONVERSATION_COUNT=$(docker exec e2bot-postgres-dev psql -U postgres -d e2_bot -t -c "SELECT COUNT(*) FROM conversations;" | xargs)
echo -e "📊 Total de conversas no banco: ${YELLOW}$CONVERSATION_COUNT${NC}"

# 3. Verificar última conversa
echo ""
echo "🔍 Última conversa registrada:"
docker exec e2bot-postgres-dev psql -U postgres -d e2_bot -c "
SELECT
    id,
    phone_number,
    current_state,
    state_machine_state,
    created_at,
    updated_at
FROM conversations
ORDER BY updated_at DESC
LIMIT 1;
"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "🔍 Verificando logs de erro recentes..."
echo ""

# 4. Verificar erros de conversation_id
ERROR_COUNT=$(docker logs e2bot-n8n-dev 2>&1 | tail -200 | grep -c "conversation_id.*null" || echo "0")

if [ "$ERROR_COUNT" -eq "0" ]; then
    echo -e "${GREEN}✅ Nenhum erro de conversation_id null nos últimos logs${NC}"
else
    echo -e "${YELLOW}⚠️ Ainda há $ERROR_COUNT menções de conversation_id null${NC}"
    echo "   (Pode ser de execuções anteriores)"
fi

# 5. Verificar estado do n8n
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "📈 Status dos containers..."
echo ""

docker ps --format "table {{.Names}}\t{{.Status}}" | grep e2bot

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "✅ RESUMO DA CORREÇÃO:"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "1. ✅ State Machine Logic: Corrigido para receber múltiplos inputs"
echo "2. ✅ Merge Node: Adicionado para combinar dados corretamente"
echo "3. ✅ Connections: Reconfiguradas para fluxo adequado"
echo "4. ✅ Debug Logs: Adicionados para rastreamento"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "📋 PRÓXIMAS AÇÕES:"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "1. Importe o workflow corrigido no n8n (http://localhost:5678)"
echo "   Arquivo: 02_ai_agent_conversation_V19_CONVERSATION_ID_FIXED.json"
echo ""
echo "2. Desative o workflow V19 antigo"
echo ""
echo "3. Ative o novo workflow corrigido"
echo ""
echo "4. Teste enviando '1' após receber o menu"
echo ""
echo "5. Verifique os logs:"
echo "   docker logs -f e2bot-n8n-dev 2>&1 | grep -E '(conversation_id|Conversation ID)'"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "📂 CAMINHO COMPLETO DO ARQUIVO:"
echo "/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V19_CONVERSATION_ID_FIXED.json"
echo ""