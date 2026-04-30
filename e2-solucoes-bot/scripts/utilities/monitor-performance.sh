#!/bin/bash

# Script para monitorar performance do sistema E2 Bot
# Data: 2025-01-12

echo "=== Monitor de Performance E2 Bot ==="
echo "Data: $(date)"
echo ""

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 1. Status dos containers
echo -e "${BLUE}🐳 Status dos Containers:${NC}"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Size}}" | grep e2bot

echo ""
# 2. Uso de recursos
echo -e "${BLUE}💻 Uso de Recursos:${NC}"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" | grep e2bot

echo ""
# 3. Status do banco de dados principal
echo -e "${BLUE}🗄️ Status do Banco de Dados (e2_bot):${NC}"
docker exec e2bot-postgres-dev psql -U postgres -d e2_bot -c "
SELECT
    'Conversas ativas' as metric,
    COUNT(*) as value
FROM conversations
WHERE updated_at > NOW() - INTERVAL '24 hours'
UNION ALL
SELECT
    'Mensagens hoje' as metric,
    COUNT(*) as value
FROM messages
WHERE created_at > CURRENT_DATE
UNION ALL
SELECT
    'Total de mensagens' as metric,
    COUNT(*) as value
FROM messages;
"

echo ""
# 4. Verificar erros recentes no n8n
echo -e "${YELLOW}⚠️ Erros Recentes (últimos 50 logs):${NC}"
docker logs e2bot-n8n-dev 2>&1 | tail -50 | grep -E "(ERROR|duplicate|conflict)" | tail -10 || echo "Nenhum erro encontrado nos últimos logs"

echo ""
# 5. Verificar mensagens duplicadas
echo -e "${BLUE}🔍 Verificando Mensagens Duplicadas:${NC}"
docker exec e2bot-postgres-dev psql -U postgres -d e2_bot -t -c "
SELECT COUNT(*)
FROM messages
WHERE whatsapp_message_id IN (
    SELECT whatsapp_message_id
    FROM messages
    WHERE whatsapp_message_id IS NOT NULL
    GROUP BY whatsapp_message_id
    HAVING COUNT(*) > 1
);
" | xargs echo "Mensagens duplicadas encontradas:"

echo ""
# 6. Status da Evolution API
echo -e "${BLUE}📱 Status Evolution API:${NC}"
curl -s http://localhost:8080/manager/status 2>/dev/null | jq -r '.version' | xargs echo "Versão:"
curl -s http://localhost:8080/instance/fetchInstances \
  -H "apikey: ${EVOLUTION_API_KEY:-B4B6C8D2A5E7F3B1D9E2A4C6E8B3F5D7A1C3E5B7D9F2A4E6C8B1D3F5A7E9C2B4}" 2>/dev/null | \
  jq -r '.[] | "\(.instance.instanceName): \(.instance.status)"' 2>/dev/null || echo "Não foi possível obter status das instâncias"

echo ""
# 7. Recomendações
echo -e "${GREEN}📋 Recomendações:${NC}"

# Verificar se há mensagens duplicadas
DUPLICATES=$(docker exec e2bot-postgres-dev psql -U postgres -d e2_bot -t -c "SELECT COUNT(*) FROM messages WHERE whatsapp_message_id IN (SELECT whatsapp_message_id FROM messages WHERE whatsapp_message_id IS NOT NULL GROUP BY whatsapp_message_id HAVING COUNT(*) > 1);" | xargs)

if [ "$DUPLICATES" -gt "0" ]; then
    echo -e "${RED}❌ Encontradas $DUPLICATES mensagens duplicadas!${NC}"
    echo "   Execute: ./scripts/cleanup-duplicates.sql"
else
    echo -e "${GREEN}✅ Nenhuma mensagem duplicada encontrada${NC}"
fi

# Verificar se o workflow correto está sendo usado
if docker logs e2bot-n8n-dev 2>&1 | tail -100 | grep -q "Parameter 'query' must be a text string"; then
    echo -e "${RED}❌ Erro de query SQL detectado - atualize para workflow V17${NC}"
    echo "   1. Importe: 02_ai_agent_conversation_V17.json"
    echo "   2. Ative o workflow V17"
else
    echo -e "${GREEN}✅ Nenhum erro de query SQL detectado${NC}"
fi

# Verificar uso de memória
MEM_USAGE=$(docker stats --no-stream --format "{{.MemPerc}}" e2bot-n8n-dev | sed 's/%//')
if (( $(echo "$MEM_USAGE > 80" | bc -l) )); then
    echo -e "${YELLOW}⚠️ Alto uso de memória do n8n (${MEM_USAGE}%)${NC}"
    echo "   Execute: ./scripts/clean-n8n-executions.sh"
else
    echo -e "${GREEN}✅ Uso de memória normal${NC}"
fi

echo ""
echo -e "${BLUE}📊 Monitor completo - $(date)${NC}"