#!/bin/bash

# ============================================================================
# V33 DEFINITIVE FIX VALIDATION SCRIPT
# ============================================================================
# Tests the critical fix for "stateNameMapping is not defined" error
# ============================================================================

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║         V33 DEFINITIVE FIX - VALIDATION SCRIPT                 ║"
echo "║              CRITICAL ERROR RESOLUTION TEST                    ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${RED}🚨 CRITICAL VALIDATION:${NC}"
echo "This script validates that the 'stateNameMapping is not defined' error is FIXED"
echo ""

echo -e "${BLUE}📋 PRE-REQUISITOS:${NC}"
echo ""
echo "  1. V33 workflow importado e ativo no n8n"
echo "  2. Workflows V31/V32 DESATIVADOS"
echo "  3. Evolution API conectada"
echo "  4. Containers rodando"
echo ""

# Verificar containers
echo -e "${BLUE}🐳 Verificando containers...${NC}"
if docker ps | grep -q "e2bot-n8n-dev"; then
    echo -e "  ${GREEN}✅ n8n rodando${NC}"
else
    echo -e "  ${RED}❌ n8n não está rodando${NC}"
    echo -e "  ${YELLOW}Execute: docker-compose -f docker/docker-compose-dev.yml up -d${NC}"
    exit 1
fi

if docker ps | grep -q "e2bot-evolution-dev"; then
    echo -e "  ${GREEN}✅ Evolution API rodando${NC}"
else
    echo -e "  ${RED}❌ Evolution API não está rodando${NC}"
    exit 1
fi

if docker ps | grep -q "e2bot-postgres-dev"; then
    echo -e "  ${GREEN}✅ PostgreSQL rodando${NC}"
else
    echo -e "  ${RED}❌ PostgreSQL não está rodando${NC}"
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${RED}🔍 TESTE CRÍTICO: stateNameMapping Definition${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Verificando logs para o erro crítico..."
echo ""

# Verificar se ainda existe o erro
echo "Buscando por erros nos últimos 100 logs..."
ERRORS=$(docker logs e2bot-n8n-dev 2>&1 | tail -100 | grep -c "stateNameMapping is not defined")

if [ "$ERRORS" -gt 0 ]; then
    echo -e "${RED}❌ ERRO AINDA PRESENTE!${NC}"
    echo "   Encontradas $ERRORS ocorrências de 'stateNameMapping is not defined'"
    echo ""
    echo -e "${YELLOW}⚠️ AÇÃO NECESSÁRIA:${NC}"
    echo "   1. Verifique se V33 foi importado corretamente"
    echo "   2. Certifique-se que V33 está ATIVO"
    echo "   3. Desative TODOS os workflows V31/V32"
    echo ""
else
    echo -e "${GREEN}✅ ERRO NÃO ENCONTRADO!${NC}"
    echo "   Nenhuma ocorrência de 'stateNameMapping is not defined' nos logs recentes"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${YELLOW}🔬 TESTE 1: V33 Initialization${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Verificando se V33 está ativo..."
echo ""

# Verificar V33 nos logs
V33_ACTIVE=$(docker logs e2bot-n8n-dev 2>&1 | tail -100 | grep -c "V33 DEFINITIVE FIX ACTIVE")

if [ "$V33_ACTIVE" -gt 0 ]; then
    echo -e "${GREEN}✅ V33 ESTÁ ATIVO!${NC}"
    echo "   Encontradas $V33_ACTIVE inicializações do V33"
    echo ""
    echo "Últimas mensagens V33:"
    docker logs e2bot-n8n-dev 2>&1 | tail -100 | grep "V33" | tail -5
else
    echo -e "${RED}❌ V33 NÃO ESTÁ ATIVO!${NC}"
    echo "   Não encontrado 'V33 DEFINITIVE FIX ACTIVE' nos logs"
    echo ""
    echo -e "${YELLOW}⚠️ AÇÃO NECESSÁRIA:${NC}"
    echo "   1. Importe o workflow V33 no n8n"
    echo "   2. Ative o workflow V33"
    echo "   3. Desative workflows anteriores"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${YELLOW}🔬 TESTE 2: State Mapping${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📱 Para testar o mapeamento de estados:"
echo ""
echo "1. Envie '1' para o WhatsApp"
echo "2. Verifique os logs:"
echo -e "${GREEN}docker logs -f e2bot-n8n-dev 2>&1 | grep -E 'V33|STATE|ERROR'${NC}"
echo ""
echo "✅ SUCESSO se aparecer:"
echo "   • V33 STATE MAPPING: Initialized with 18 mappings"
echo "   • V33 FIX: stateNameMapping is now defined BEFORE line 130"
echo "   • Processamento continua SEM erros"
echo ""
echo "❌ FALHA se aparecer:"
echo "   • stateNameMapping is not defined"
echo "   • ERROR na linha 130"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${BLUE}📊 MONITORAMENTO EM TEMPO REAL${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Monitor V33 (erros e inicialização):"
echo -e "${GREEN}docker logs -f e2bot-n8n-dev 2>&1 | grep -E 'V33|stateNameMapping|ERROR|CRITICAL'${NC}"
echo ""
echo "Monitor conversação completa:"
echo -e "${GREEN}docker logs -f e2bot-n8n-dev 2>&1${NC}"
echo ""
echo "Verificar estado no banco:"
echo -e "${GREEN}docker exec e2bot-postgres-dev psql -U e2bot_user -d e2bot_db -c \"SELECT lead_id, current_state, updated_at FROM conversations ORDER BY updated_at DESC LIMIT 1;\"${NC}"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${BLUE}🚀 COMANDOS DE EMERGÊNCIA${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Se o erro persistir após importar V33:"
echo ""
echo "1. Reiniciar n8n:"
echo -e "${GREEN}docker restart e2bot-n8n-dev${NC}"
echo ""
echo "2. Limpar cache de execuções:"
echo "   - Acesse http://localhost:5678/executions"
echo "   - Delete execuções com erro"
echo ""
echo "3. Verificar workflow ativo:"
echo "   - Acesse http://localhost:5678/workflows"
echo "   - Apenas V33 deve estar ATIVO (toggle verde)"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✅ CRITÉRIOS DE SUCESSO V33:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. ✅ SEM erro 'stateNameMapping is not defined'"
echo "2. ✅ V33 aparece nos logs como ACTIVE"
echo "3. ✅ Estado 'identificando_servico' é mapeado corretamente"
echo "4. ✅ Nome 'Bruno Rosa' é aceito"
echo "5. ✅ Fluxo completo funciona"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${YELLOW}📝 STATUS ATUAL:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ "$ERRORS" -eq 0 ] && [ "$V33_ACTIVE" -gt 0 ]; then
    echo -e "${GREEN}🎉 V33 FIX APARENTEMENTE FUNCIONANDO!${NC}"
    echo ""
    echo "• Erro crítico não detectado nos logs recentes"
    echo "• V33 está inicializado e ativo"
    echo ""
    echo "Faça o teste manual enviando '1' para confirmar."
else
    echo -e "${RED}⚠️ V33 NECESSITA ATENÇÃO!${NC}"
    echo ""
    if [ "$ERRORS" -gt 0 ]; then
        echo "• Erro 'stateNameMapping is not defined' ainda presente"
    fi
    if [ "$V33_ACTIVE" -eq 0 ]; then
        echo "• V33 não está ativo ou não foi importado"
    fi
    echo ""
    echo "Siga as instruções acima para resolver."
fi

echo ""
echo "Documentação completa em:"
echo "  docs/PLAN/V33_DEFINITIVE_FIX.md"
echo ""