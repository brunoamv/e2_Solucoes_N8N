#!/bin/bash

# ============================================================================
# Validation Script for V32 State Mapping Fix
# ============================================================================
# Tests the state normalization and phone validation features
# ============================================================================

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║           V32 STATE MAPPING FIX - VALIDATION SCRIPT            ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}📋 PRE-REQUISITOS:${NC}"
echo ""
echo "  1. V32 workflow importado e ativo no n8n"
echo "  2. V31 e workflows anteriores desativados"
echo "  3. Evolution API conectada (instância e2-solucoes-bot)"
echo "  4. Containers rodando (docker ps)"
echo ""

# Verificar containers
echo -e "${BLUE}🐳 Verificando containers...${NC}"
if docker ps | grep -q "e2bot-n8n-dev"; then
    echo -e "  ${GREEN}✅ n8n rodando${NC}"
else
    echo -e "  ${RED}❌ n8n não está rodando${NC}"
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
echo -e "${YELLOW}🔬 TESTE 1: STATE MAPPING${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📱 Envie para o WhatsApp:"
echo "   Mensagem: '1' (escolher serviço)"
echo ""
echo "🔍 Verificar nos logs:"
echo -e "${GREEN}docker logs -f e2bot-n8n-dev 2>&1 | grep -E 'V32|STATE'${NC}"
echo ""
echo "✅ SUCESSO se aparecer:"
echo "   • V32 STATE NORMALIZATION:"
echo "   • Raw state from DB: identificando_servico"
echo "   • Normalized state: service_selection"
echo "   • Mapping applied: YES ✓"
echo ""
echo "❌ FALHA se aparecer:"
echo "   • State not in mapping"
echo "   • ERROR ou undefined"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${YELLOW}🔬 TESTE 2: NOME ACEITO${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📱 Depois de escolher serviço, envie:"
echo "   Mensagem: 'Bruno Rosa'"
echo ""
echo "✅ SUCESSO se:"
echo "   • Bot aceita o nome"
echo "   • Bot pergunta sobre telefone WhatsApp"
echo "   • Aparece: 'Este é seu telefone principal?'"
echo ""
echo "❌ FALHA se:"
echo "   • Bot volta ao menu de serviços"
echo "   • Bot rejeita o nome"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${YELLOW}🔬 TESTE 3: PHONE VALIDATION${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📱 Quando bot perguntar sobre telefone:"
echo ""
echo "CENÁRIO A - Confirmar WhatsApp:"
echo "   Envie: '1' ou 'sim'"
echo "   ✅ Bot deve pedir email"
echo ""
echo "CENÁRIO B - Outro telefone:"
echo "   Envie: '2' ou 'não'"
echo "   ✅ Bot deve pedir para digitar o telefone"
echo "   Envie: '(62) 98175-5548'"
echo "   ✅ Bot deve pedir email"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${YELLOW}🔬 TESTE 4: FLUXO COMPLETO${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Sequência completa de teste:"
echo "  1. '1' → Escolhe serviço"
echo "  2. 'Bruno Rosa' → Nome"
echo "  3. '1' → Confirma telefone WhatsApp"
echo "  4. 'teste@email.com' → Email"
echo "  5. 'Brasília' → Cidade"
echo "  6. Verificar confirmação com dados corretos"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${BLUE}📊 MONITORAMENTO${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Monitor V32 logs:"
echo -e "${GREEN}docker logs -f e2bot-n8n-dev 2>&1 | grep -E 'V32|STATE|PHONE'${NC}"
echo ""
echo "Monitor database state:"
echo -e "${GREEN}docker exec e2bot-postgres-dev psql -U e2bot_user -d e2bot_db -c \"SELECT lead_id, current_state, collected_data FROM conversations ORDER BY updated_at DESC LIMIT 1;\"${NC}"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${BLUE}🚀 COMANDOS ÚTEIS${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Limpar conversa para novo teste:"
echo -e "${GREEN}docker exec e2bot-postgres-dev psql -U e2bot_user -d e2bot_db -c \"DELETE FROM conversations WHERE lead_id = 'SEU_NUMERO_AQUI';\"${NC}"
echo ""
echo "Ver execuções no n8n:"
echo -e "${GREEN}http://localhost:5678/executions${NC}"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✅ CRITÉRIOS DE SUCESSO V32:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. ✅ Estado 'identificando_servico' é mapeado para 'service_selection'"
echo "2. ✅ Nome 'Bruno Rosa' é aceito (não volta ao menu)"
echo "3. ✅ Telefone WhatsApp é confirmado ou alterado"
echo "4. ✅ Dados são salvos corretamente no banco"
echo "5. ✅ Fluxo completo funciona sem erros"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${YELLOW}📝 NOTAS IMPORTANTES:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "• V32 corrige o bug crítico de mapeamento de estados"
echo "• Adiciona validação de telefone WhatsApp"
echo "• Mantém compatibilidade com entrada direta de telefone"
echo "• Logs V32 são mais verbosos para debug"
echo ""
echo "Documentação completa em:"
echo "  docs/PLAN/V32_STATE_MAPPING_FIX.md"
echo ""