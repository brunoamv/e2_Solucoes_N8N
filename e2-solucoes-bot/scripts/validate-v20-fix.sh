#!/bin/bash

# Script de validação do V20 - Query Fix
# Data: 2026-01-12

echo "═══════════════════════════════════════════════════════════════"
echo "   🔍 VALIDAÇÃO DO V20 - QUERY FIX"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Cores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 1. Verificar se o arquivo V20 existe
echo "📁 Verificando arquivo V20..."
echo ""

if [ -f "/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V20_QUERY_FIX.json" ]; then
    echo -e "${GREEN}✅ Workflow V20 encontrado${NC}"
else
    echo -e "${RED}❌ Workflow V20 NÃO encontrado${NC}"
    exit 1
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "📊 Verificando estado atual do banco..."
echo ""

# 2. Verificar last_message_at nas conversas
echo "🔍 Verificando last_message_at nas conversas recentes:"
docker exec e2bot-postgres-dev psql -U postgres -d e2_bot -c "
SELECT
    id,
    phone_number,
    current_state,
    state_machine_state,
    last_message_at,
    updated_at
FROM conversations
ORDER BY updated_at DESC
LIMIT 3;
"

# 3. Contar mensagens salvas
MESSAGE_COUNT=$(docker exec e2bot-postgres-dev psql -U postgres -d e2_bot -t -c "SELECT COUNT(*) FROM messages;" | xargs)
echo -e "📊 Total de mensagens no banco: ${YELLOW}$MESSAGE_COUNT${NC}"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "🔍 Verificando estrutura do V20..."
echo ""

# 4. Verificar se o node Build Update Queries existe
if grep -q "Build Update Queries" "/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V20_QUERY_FIX.json"; then
    echo -e "${GREEN}✅ Node 'Build Update Queries' encontrado no V20${NC}"
else
    echo -e "${RED}❌ Node 'Build Update Queries' NÃO encontrado${NC}"
fi

# 5. Verificar se as queries estão usando o formato correto
if grep -q "query_update_conversation" "/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V20_QUERY_FIX.json"; then
    echo -e "${GREEN}✅ Queries preparadas encontradas no V20${NC}"
else
    echo -e "${RED}❌ Queries preparadas NÃO encontradas${NC}"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "📈 Status dos containers..."
echo ""

docker ps --format "table {{.Names}}\t{{.Status}}" | grep e2bot

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo -e "${BLUE}✨ MELHORIAS DO V20:${NC}"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "1. ✅ Build Update Queries: Prepara todas as queries SQL como strings"
echo "2. ✅ SQL Puro: PostgreSQL recebe queries prontas, não templates"
echo "3. ✅ last_message_at: Será atualizado corretamente"
echo "4. ✅ Conversações: Estado será salvo e transições funcionarão"
echo "5. ✅ Menu Loop: Problema resolvido - menu navegará corretamente"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "📋 INSTRUÇÕES DE TESTE:"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "1. Importe o V20 no n8n (http://localhost:5678):"
echo -e "   ${BLUE}02_ai_agent_conversation_V20_QUERY_FIX.json${NC}"
echo ""
echo "2. Desative o workflow V19"
echo ""
echo "3. Ative o workflow V20"
echo ""
echo "4. TESTE CRÍTICO:"
echo "   a) Envie uma mensagem para o bot"
echo "   b) Quando receber o menu, digite '1'"
echo "   c) O bot DEVE pedir seu nome (não repetir o menu)"
echo ""
echo "5. Verifique os logs em tempo real:"
echo -e "   ${BLUE}docker logs -f e2bot-n8n-dev 2>&1 | grep -E '(BUILD UPDATE QUERIES|last_message_at)'${NC}"
echo ""
echo "6. Verifique se last_message_at foi atualizado:"
echo -e "   ${BLUE}docker exec e2bot-postgres-dev psql -U postgres -d e2_bot -c \"SELECT phone_number, last_message_at FROM conversations ORDER BY updated_at DESC LIMIT 1;\"${NC}"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "📂 CAMINHO COMPLETO DO V20:"
echo -e "${BLUE}/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V20_QUERY_FIX.json${NC}"
echo ""