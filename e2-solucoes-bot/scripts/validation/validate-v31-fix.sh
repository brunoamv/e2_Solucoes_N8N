#!/bin/bash

# Script de validação para V31 Comprehensive Fix
# Testa se o bug do validador foi corrigido

echo "=========================================="
echo "   VALIDAÇÃO V31 - COMPREHENSIVE FIX     "
echo "=========================================="

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para verificar serviço
check_service() {
    local service=$1
    if docker ps | grep -q "$service"; then
        echo -e "${GREEN}✓${NC} $service está rodando"
        return 0
    else
        echo -e "${RED}✗${NC} $service NÃO está rodando"
        return 1
    fi
}

echo -e "\n${YELLOW}1. Verificando serviços Docker...${NC}"
check_service "e2bot-n8n-dev"
check_service "e2bot-postgres-dev"
check_service "e2bot-evolution-dev"

echo -e "\n${YELLOW}2. Verificando versão do Evolution API...${NC}"
EVOLUTION_VERSION=$(docker exec e2bot-evolution-dev curl -s http://localhost:8080/manager/status 2>/dev/null | grep -o '"version":"[^"]*"' | cut -d'"' -f4)
if [[ "$EVOLUTION_VERSION" == "2.3"* ]]; then
    echo -e "${GREEN}✓${NC} Evolution API v$EVOLUTION_VERSION (correto)"
else
    echo -e "${RED}✗${NC} Evolution API v$EVOLUTION_VERSION (esperado v2.3.x)"
fi

echo -e "\n${YELLOW}3. Verificando arquivo V31...${NC}"
if [ -f "n8n/workflows/02_ai_agent_conversation_V31_COMPREHENSIVE_FIX.json" ]; then
    echo -e "${GREEN}✓${NC} Workflow V31 existe"
    FILE_SIZE=$(stat -c%s "n8n/workflows/02_ai_agent_conversation_V31_COMPREHENSIVE_FIX.json")
    echo "   Tamanho: $FILE_SIZE bytes"
else
    echo -e "${RED}✗${NC} Workflow V31 NÃO encontrado!"
fi

echo -e "\n${YELLOW}4. Instruções para importar V31:${NC}"
echo "   1. Acesse http://localhost:5678"
echo "   2. Vá em Workflows"
echo "   3. DESATIVE todos os workflows V27-V30"
echo "   4. Clique em 'Import from File'"
echo "   5. Selecione: 02_ai_agent_conversation_V31_COMPREHENSIVE_FIX.json"
echo "   6. Após importar, ATIVE o workflow V31"

echo -e "\n${YELLOW}5. Comandos úteis para monitoramento:${NC}"
echo ""
echo "# Monitor V31 logs em tempo real:"
echo -e "${GREEN}docker logs -f e2bot-n8n-dev 2>&1 | grep -E 'V31|ERROR|CRITICAL'${NC}"
echo ""
echo "# Ver último stage no banco:"
echo -e "${GREEN}docker exec e2bot-postgres-dev psql -U postgres -d e2_bot -c \"SELECT phone_number, conversation_stage, updated_at FROM conversations ORDER BY updated_at DESC LIMIT 1;\"${NC}"
echo ""
echo "# Monitor contínuo do banco:"
echo -e "${GREEN}watch -n 1 'docker exec e2bot-postgres-dev psql -U postgres -d e2_bot -c \"SELECT phone_number, conversation_stage, updated_at FROM conversations ORDER BY updated_at DESC LIMIT 1;\"'${NC}"

echo -e "\n${YELLOW}6. Sequência de teste:${NC}"
echo "   1. No WhatsApp, envie: ${GREEN}1${NC}"
echo "      - Deve ver logs: 'V31 STAGE: service_selection'"
echo "      - Deve ver: 'V31 CRITICAL: Setting nextStage to: collect_name'"
echo ""
echo "   2. Quando pedir nome, envie: ${GREEN}Bruno Rosa${NC}"
echo "      - ${GREEN}CRÍTICO:${NC} Deve ver: 'V31 STAGE EXECUTION: collect_name'"
echo "      - Deve ver: 'V31 VALIDATOR EXECUTED: text_min_3_chars'"
echo "      - Deve ver: 'V31 SUCCESS: Name accepted'"
echo "      - Bot deve pedir telefone (não voltar ao menu!)"
echo ""
echo "   3. Continue com telefone: ${GREEN}62981755485${NC}"
echo "      - Deve aceitar e pedir email"

echo -e "\n${YELLOW}7. Verificação de sucesso:${NC}"
echo "   ${GREEN}✓${NC} Se o bot aceitar 'Bruno Rosa' e pedir telefone = SUCESSO!"
echo "   ${RED}✗${NC} Se voltar ao menu após 'Bruno Rosa' = BUG ainda presente"

echo -e "\n${YELLOW}8. Em caso de problemas:${NC}"
echo "   - Verifique se APENAS V31 está ativo"
echo "   - Limpe cache do n8n: Settings → Executions → Delete All"
echo "   - Reinicie containers se necessário:"
echo "     docker-compose -f docker/docker-compose-dev.yml restart"

echo -e "\n=========================================="
echo -e "${GREEN}Script de validação V31 concluído!${NC}"
echo "=========================================="