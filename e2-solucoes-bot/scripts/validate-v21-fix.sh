#!/bin/bash

# Script de validação do V21 - Data Flow Fix
# Data: 2026-01-12

echo "═══════════════════════════════════════════════════════════════"
echo "   🔍 VALIDAÇÃO DO V21 - DATA FLOW FIX"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Cores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 1. Verificar se o arquivo V21 existe
echo "📁 Verificando arquivo V21..."
echo ""

if [ -f "/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V21_DATA_FLOW_FIXED.json" ]; then
    echo -e "${GREEN}✅ Workflow V21 encontrado${NC}"
else
    echo -e "${RED}❌ Workflow V21 NÃO encontrado${NC}"
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
echo "🔍 Verificando estrutura do V21..."
echo ""

# 4. Verificar se o node Build Update Queries existe e recebe dados diretamente
if grep -q "V21 BUILD UPDATE QUERIES DEBUG" "/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V21_DATA_FLOW_FIXED.json"; then
    echo -e "${GREEN}✅ Node 'Build Update Queries' V21 encontrado${NC}"
else
    echo -e "${RED}❌ Node 'Build Update Queries' V21 NÃO encontrado${NC}"
fi

# 5. Verificar se Prepare Update Data foi removido
if grep -q "Prepare Update Data" "/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V21_DATA_FLOW_FIXED.json"; then
    echo -e "${YELLOW}⚠️ Node 'Prepare Update Data' ainda existe (deveria ter sido removido)${NC}"
else
    echo -e "${GREEN}✅ Node 'Prepare Update Data' removido como esperado${NC}"
fi

# 6. Verificar conexão direta State Machine → Build Update Queries
if grep -q '"State Machine Logic".*"Build Update Queries"' "/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V21_DATA_FLOW_FIXED.json"; then
    echo -e "${GREEN}✅ Conexão direta State Machine → Build Update Queries${NC}"
else
    echo -e "${YELLOW}⚠️ Verificar conexões no workflow${NC}"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "📈 Status dos containers..."
echo ""

docker ps --format "table {{.Names}}\t{{.Status}}" | grep e2bot

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo -e "${BLUE}✨ MELHORIAS DO V21:${NC}"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "1. ✅ Fluxo direto: State Machine → Build Update Queries"
echo "2. ✅ Remoção do Prepare Update Data (desnecessário)"
echo "3. ✅ Build Update Queries recebe TODOS os campos necessários"
echo "4. ✅ SQL queries construídas com dados completos"
echo "5. ✅ Send WhatsApp usa caminhos de dados corretos"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "📋 INSTRUÇÕES DE TESTE:"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "1. Importe o V21 no n8n (http://localhost:5678):"
echo -e "   ${BLUE}02_ai_agent_conversation_V21_DATA_FLOW_FIXED.json${NC}"
echo ""
echo "2. Desative o workflow V20"
echo ""
echo "3. Ative o workflow V21"
echo ""
echo "4. TESTE COMPLETO:"
echo "   a) Envie uma mensagem para o bot"
echo "   b) Quando receber o menu, digite '1'"
echo "   c) O bot DEVE pedir seu nome (não repetir o menu)"
echo "   d) Continue a conversa até o final"
echo ""
echo "5. Verifique os logs em tempo real:"
echo -e "   ${BLUE}docker logs -f e2bot-n8n-dev 2>&1 | grep -E '(V21|last_message_at|BUILD UPDATE)'${NC}"
echo ""
echo "6. Verifique se last_message_at foi atualizado:"
echo -e "   ${BLUE}docker exec e2bot-postgres-dev psql -U postgres -d e2_bot -c \\\"SELECT phone_number, last_message_at FROM conversations ORDER BY updated_at DESC LIMIT 1;\\\"${NC}"
echo ""
echo "7. Verifique se as mensagens foram salvas:"
echo -e "   ${BLUE}docker exec e2bot-postgres-dev psql -U postgres -d e2_bot -c \\\"SELECT COUNT(*) FROM messages;\\\"${NC}"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "📂 CAMINHO COMPLETO DO V21:"
echo -e "${BLUE}/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V21_DATA_FLOW_FIXED.json${NC}"
echo ""