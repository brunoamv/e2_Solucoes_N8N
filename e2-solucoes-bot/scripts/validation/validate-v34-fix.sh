#!/bin/bash

# ============================================================================
# V34 NAME VALIDATION FIX - VALIDATION SCRIPT
# ============================================================================
# Tests that name validation is working correctly with proper validator
# ============================================================================

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║         V34 NAME VALIDATION FIX - VALIDATION SCRIPT            ║"
echo "║                Testing Name Acceptance Fix                     ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${RED}🚨 CRITICAL VALIDATION:${NC}"
echo "Testing that 'Bruno Rosa' is ACCEPTED as a valid name"
echo ""

echo -e "${BLUE}📋 PRE-REQUISITOS:${NC}"
echo ""
echo "  1. V34 workflow importado e ativo no n8n"
echo "  2. V33 workflow DESATIVADO"
echo "  3. Evolution API conectada"
echo "  4. Containers rodando"
echo ""

# Verificar containers
echo -e "${BLUE}🐳 Verificando containers...${NC}"
if docker ps | grep -q "e2bot-n8n-dev"; then
    echo -e "  ${GREEN}✅ n8n rodando${NC}"
else
    echo -e "  ${RED}❌ n8n não está rodando${NC}"
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${YELLOW}🔬 TESTE 1: V34 Initialization${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Verificar V34 nos logs
V34_ACTIVE=$(docker logs e2bot-n8n-dev 2>&1 | tail -200 | grep -c "V34 NAME VALIDATION FIX ACTIVE")

if [ "$V34_ACTIVE" -gt 0 ]; then
    echo -e "${GREEN}✅ V34 ESTÁ ATIVO!${NC}"
    echo "   Encontradas $V34_ACTIVE inicializações do V34"
else
    echo -e "${RED}❌ V34 NÃO ESTÁ ATIVO!${NC}"
    echo ""
    echo -e "${YELLOW}⚠️ AÇÃO NECESSÁRIA:${NC}"
    echo "   1. Importe o workflow V34 no n8n"
    echo "   2. Ative o workflow V34"
    echo "   3. Desative V33"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${YELLOW}🔬 TESTE 2: Name Rejection Check${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Verificar se ainda há erro de "Opção inválida" para nomes
INVALID_OPTION=$(docker logs e2bot-n8n-dev 2>&1 | tail -200 | grep -A2 "Bruno Rosa" | grep -c "Opção inválida")

if [ "$INVALID_OPTION" -gt 0 ]; then
    echo -e "${RED}❌ PROBLEMA AINDA PRESENTE!${NC}"
    echo "   'Bruno Rosa' ainda está sendo rejeitado como 'Opção inválida'"
    echo ""
    echo -e "${YELLOW}Verificando detalhes...${NC}"
    docker logs e2bot-n8n-dev 2>&1 | tail -200 | grep -A5 "Bruno Rosa" | tail -10
else
    echo -e "${GREEN}✅ SEM REJEIÇÃO DE NOME!${NC}"
    echo "   'Bruno Rosa' não está mais sendo rejeitado como 'Opção inválida'"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${YELLOW}🔬 TESTE 3: V34 Validation Logs${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Verificar logs específicos do V34
echo "Buscando logs de validação V34..."
V34_VALIDATION=$(docker logs e2bot-n8n-dev 2>&1 | tail -200 | grep -c "V34 Name Validation")
V34_ACCEPTED=$(docker logs e2bot-n8n-dev 2>&1 | tail -200 | grep -c "V34: Name accepted successfully")

if [ "$V34_VALIDATION" -gt 0 ]; then
    echo -e "${GREEN}✅ Validação V34 encontrada!${NC}"
    echo "   $V34_VALIDATION ocorrências de validação V34"

    if [ "$V34_ACCEPTED" -gt 0 ]; then
        echo -e "${GREEN}✅ Nomes aceitos pelo V34!${NC}"
        echo "   $V34_ACCEPTED nomes aceitos com sucesso"

        echo ""
        echo "Últimas aceitações:"
        docker logs e2bot-n8n-dev 2>&1 | tail -200 | grep "V34: Name accepted successfully" | tail -3
    fi
else
    echo -e "${YELLOW}⚠️ Logs V34 não encontrados${NC}"
    echo "   Pode ser que o teste ainda não foi executado"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${CYAN}📱 TESTE MANUAL NECESSÁRIO${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Para validar completamente o V34, envie no WhatsApp:"
echo ""
echo "  1️⃣ Envie: '1'"
echo "     ✅ Esperado: Bot pergunta seu nome"
echo ""
echo "  2️⃣ Envie: 'Bruno Rosa'"
echo "     ✅ Esperado: Bot ACEITA e pergunta telefone"
echo "     ❌ NÃO esperado: 'Opção inválida' ou voltar ao menu"
echo ""
echo "  3️⃣ Monitor em tempo real:"
echo -e "     ${GREEN}docker logs -f e2bot-n8n-dev 2>&1 | grep -E 'V34|Bruno|collect_name'${NC}"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${BLUE}📊 COMANDOS ÚTEIS${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Monitor completo V34:"
echo -e "${GREEN}docker logs -f e2bot-n8n-dev 2>&1 | grep V34${NC}"
echo ""
echo "Ver última conversa:"
echo -e "${GREEN}docker logs e2bot-n8n-dev 2>&1 | tail -100 | grep -A5 -B5 'Bruno'${NC}"
echo ""
echo "Verificar estado no banco:"
echo -e "${GREEN}docker exec e2bot-postgres-dev psql -U e2bot_user -d e2bot_db -c \"SELECT lead_id, current_state, collected_data->>'lead_name' as name FROM conversations ORDER BY updated_at DESC LIMIT 1;\"${NC}"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✅ CRITÉRIOS DE SUCESSO V34:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. ✅ V34 aparece como ACTIVE nos logs"
echo "2. ✅ 'Bruno Rosa' NÃO é rejeitado como 'Opção inválida'"
echo "3. ✅ Logs mostram 'V34: Name validation PASSED'"
echo "4. ✅ Logs mostram 'V34: Name accepted successfully'"
echo "5. ✅ Bot prossegue para pedir telefone"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${YELLOW}📝 STATUS RESUMIDO:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ "$V34_ACTIVE" -gt 0 ] && [ "$INVALID_OPTION" -eq 0 ]; then
    echo -e "${GREEN}🎉 V34 APARENTEMENTE FUNCIONANDO!${NC}"
    echo ""
    echo "• V34 está ativo"
    echo "• Sem rejeições de 'Opção inválida' recentes"
    echo ""
    echo "Faça o teste manual para confirmar completamente."
elif [ "$V34_ACTIVE" -eq 0 ]; then
    echo -e "${RED}⚠️ V34 NÃO ESTÁ ATIVO!${NC}"
    echo ""
    echo "Você precisa:"
    echo "1. Importar o workflow V34 no n8n"
    echo "2. Ativar V34 e desativar V33"
else
    echo -e "${YELLOW}⚠️ V34 ATIVO MAS PROBLEMA PERSISTE!${NC}"
    echo ""
    echo "V34 está rodando mas nomes ainda são rejeitados."
    echo "Verifique se o workflow correto está ativo."
fi

echo ""
echo "Documentação completa:"
echo "  docs/PLAN/V34_NAME_VALIDATION_DEFINITIVE_FIX.md"
echo ""