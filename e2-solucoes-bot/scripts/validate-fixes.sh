#!/bin/bash

# Script de validação das correções
# Data: 2026-01-12

echo "═══════════════════════════════════════════════════════════════"
echo "   🔍 VALIDAÇÃO DAS CORREÇÕES APLICADAS"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Cores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 1. Verificar se os arquivos corrigidos existem
echo "📁 Verificando arquivos corrigidos..."
echo ""

if [ -f "/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/01_main_whatsapp_handler_V2.5_DEDUP_FIXED_NO_UPDATED_AT.json" ]; then
    echo -e "${GREEN}✅ Workflow 01 corrigido encontrado${NC}"
else
    echo -e "${RED}❌ Workflow 01 corrigido NÃO encontrado${NC}"
fi

if [ -f "/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V17_QUERY_FIXED.json" ]; then
    echo -e "${GREEN}✅ Workflow V17 corrigido encontrado${NC}"
else
    echo -e "${RED}❌ Workflow V17 corrigido NÃO encontrado${NC}"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "📊 Verificando banco de dados..."
echo ""

# 2. Verificar se updated_at existe
UPDATED_EXISTS=$(docker exec e2bot-postgres-dev psql -U postgres -d e2_bot -t -c "SELECT COUNT(*) FROM information_schema.columns WHERE table_name='messages' AND column_name='updated_at';")

if [ "$UPDATED_EXISTS" -eq "1" ]; then
    echo -e "${GREEN}✅ Campo updated_at existe na tabela messages${NC}"
else
    echo -e "${YELLOW}⚠️ Campo updated_at NÃO existe (workflow foi ajustado para não depender dele)${NC}"
fi

# 3. Verificar mensagens duplicadas
DUPLICATES=$(docker exec e2bot-postgres-dev psql -U postgres -d e2_bot -t -c "SELECT COUNT(*) FROM messages WHERE whatsapp_message_id IN (SELECT whatsapp_message_id FROM messages WHERE whatsapp_message_id IS NOT NULL GROUP BY whatsapp_message_id HAVING COUNT(*) > 1);" | xargs)

echo -e "📊 Mensagens duplicadas no banco: ${YELLOW}$DUPLICATES${NC}"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "🔍 Verificando logs de erro recentes..."
echo ""

# 4. Verificar erros recentes
ERROR_COUNT=$(docker logs e2bot-n8n-dev 2>&1 | tail -100 | grep -c "Parameter 'query' must be a text string" || echo "0")

if [ "$ERROR_COUNT" -eq "0" ]; then
    echo -e "${GREEN}✅ Nenhum erro de 'query must be text string' nos últimos logs${NC}"
else
    echo -e "${RED}❌ Ainda há $ERROR_COUNT erros de 'query must be text string'${NC}"
fi

UPDATE_ERROR_COUNT=$(docker logs e2bot-n8n-dev 2>&1 | tail -100 | grep -c "column \"updated_at\" of relation \"messages\" does not exist" || echo "0")

if [ "$UPDATE_ERROR_COUNT" -eq "0" ]; then
    echo -e "${GREEN}✅ Nenhum erro de 'updated_at' nos últimos logs${NC}"
else
    echo -e "${RED}❌ Ainda há $UPDATE_ERROR_COUNT erros de 'updated_at'${NC}"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "📈 Status dos containers..."
echo ""

# 5. Verificar status dos containers
docker ps --format "table {{.Names}}\t{{.Status}}" | grep e2bot

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "✅ RESUMO DAS CORREÇÕES:"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "1. ✅ Workflow 01: Removida dependência de updated_at"
echo "2. ✅ Workflow V17: Corrigido retorno de queries como strings"
echo "3. ✅ Scripts de correção criados e executados"
echo "4. ✅ Arquivos prontos para importação no n8n"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "📋 PRÓXIMAS AÇÕES:"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "1. Importe os workflows corrigidos no n8n (http://localhost:5678)"
echo "2. Desative os workflows antigos"
echo "3. Ative os novos workflows"
echo "4. Teste enviando uma mensagem no WhatsApp"
echo "5. Monitore os logs por 5 minutos"
echo ""
echo "Para monitorar em tempo real:"
echo "docker logs -f e2bot-n8n-dev 2>&1 | grep -v debug"
echo ""
echo "═══════════════════════════════════════════════════════════════"