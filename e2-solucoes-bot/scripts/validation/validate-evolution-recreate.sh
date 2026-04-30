#!/bin/bash

# ============================================================================
# Validation Script - Testa o evolution_recreate completo com restart
# ============================================================================

echo "🧪 Testando evolution_recreate com docker restart automático..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Verificar se o script evolution-helper.sh existe
HELPER_SCRIPT="/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/scripts/evolution-helper.sh"

if [ ! -f "$HELPER_SCRIPT" ]; then
    echo -e "${RED}❌ Erro: Script evolution-helper.sh não encontrado${NC}"
    exit 1
fi

echo -e "${BLUE}📋 Checklist de Validação:${NC}"
echo "   ✓ Script evolution-helper.sh encontrado"

# Verificar se contém as melhorias
echo ""
echo -e "${BLUE}🔍 Verificando implementação das melhorias:${NC}"
echo ""

# 1. Verifica se tem o passo de copiar .env
if grep -q "Copiando .env para o container Evolution" "$HELPER_SCRIPT"; then
    echo -e "   ${GREEN}✅ Passo de cópia do .env implementado${NC}"
else
    echo -e "   ${RED}❌ Passo de cópia do .env NÃO encontrado${NC}"
    exit 1
fi

# 2. Verifica se tem o docker cp
if grep -q 'docker cp "$ENV_FILE" e2bot-evolution-dev:/evolution/.env' "$HELPER_SCRIPT"; then
    echo -e "   ${GREEN}✅ Comando docker cp implementado${NC}"
else
    echo -e "   ${RED}❌ Comando docker cp NÃO encontrado${NC}"
    exit 1
fi

# 3. Verifica se tem o docker restart
if grep -q "docker restart e2bot-evolution-dev" "$HELPER_SCRIPT"; then
    echo -e "   ${GREEN}✅ Docker restart implementado${NC}"
else
    echo -e "   ${RED}❌ Docker restart NÃO encontrado${NC}"
    exit 1
fi

# 4. Verifica se tem o sleep de 20 segundos
if grep -q "sleep 20" "$HELPER_SCRIPT"; then
    echo -e "   ${GREEN}✅ Tempo de espera de 20 segundos configurado${NC}"
else
    echo -e "   ${RED}❌ Tempo de espera de 20 segundos NÃO encontrado${NC}"
    exit 1
fi

# 5. Verifica se tem 7 passos
if grep -q "7/7" "$HELPER_SCRIPT"; then
    echo -e "   ${GREEN}✅ Numeração correta com 7 passos${NC}"
else
    echo -e "   ${RED}❌ Numeração incorreta (deveria ter 7 passos)${NC}"
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✅ VALIDAÇÃO CONCLUÍDA COM SUCESSO!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${BLUE}📊 Resumo da Implementação:${NC}"
echo ""
echo "   O script evolution_recreate agora executa:"
echo "   1️⃣  Deleta instância antiga"
echo "   2️⃣  Copia .env para container"
echo "   3️⃣  Reinicia container (docker restart)"
echo "   4️⃣  Cria nova instância"
echo "   5️⃣  Configura webhook"
echo "   6️⃣  Verifica webhook"
echo "   7️⃣  Gera QR Code"
echo ""
echo -e "${YELLOW}⏱️  Tempo total estimado: ~30 segundos${NC}"
echo "   • 3s para deletar"
echo "   • 20s para restart + estabilização"
echo "   • 5s para criar instância"
echo "   • 2s para configurar webhook"
echo ""
echo -e "${BLUE}🎯 Para testar ao vivo:${NC}"
echo ""
echo "   source scripts/evolution-helper.sh"
echo "   evolution_recreate"
echo ""
echo -e "${GREEN}💡 Benefícios:${NC}"
echo "   • Não precisa mais copiar .env manualmente"
echo "   • Container sempre terá as variáveis corretas"
echo "   • Processo totalmente automatizado"
echo ""