#!/bin/bash

# ============================================================================
# E2 Soluções Bot - Setup Validation Script
# ============================================================================
# Valida configuração do ambiente de desenvolvimento Sprint 1.1
# ============================================================================

set -e

# Cores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variáveis
ERRORS=0
WARNINGS=0

echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}E2 Soluções Bot - Validação de Setup (Sprint 1.1)${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""

# ============================================================================
# 1. Verificar Estrutura de Arquivos
# ============================================================================
echo -e "${BLUE}[1/6] Verificando estrutura de arquivos...${NC}"

check_file() {
    if [ -f "$1" ]; then
        echo -e "  ${GREEN}✓${NC} $1"
    else
        echo -e "  ${RED}✗${NC} $1 ${RED}(AUSENTE)${NC}"
        ((ERRORS++))
    fi
}

check_dir() {
    if [ -d "$1" ]; then
        echo -e "  ${GREEN}✓${NC} $1/"
    else
        echo -e "  ${RED}✗${NC} $1/ ${RED}(AUSENTE)${NC}"
        ((ERRORS++))
    fi
}

check_dir "docker"
check_file "docker/docker-compose-dev.yml"
check_file "docker/docker-compose.yml"
check_file "docker/.env"
check_file "docker/.env.dev.example"
check_file "docker/README.md"
check_file "QUICKSTART.md"
check_dir "docs/validation"
check_dir "n8n/workflows"
check_dir "database"
check_dir "scripts"

echo ""

# ============================================================================
# 2. Verificar Credenciais (.env)
# ============================================================================
echo -e "${BLUE}[2/6] Verificando credenciais...${NC}"

if [ ! -f "docker/.env" ]; then
    echo -e "  ${RED}✗ docker/.env não encontrado${NC}"
    ((ERRORS++))
else
    # Carregar credenciais principais (evitando multiline)
    OPENAI_API_KEY=$(grep "^OPENAI_API_KEY=" docker/.env | cut -d= -f2)
    SUPABASE_URL=$(grep "^SUPABASE_URL=" docker/.env | cut -d= -f2)
    SUPABASE_SERVICE_KEY=$(grep "^SUPABASE_SERVICE_KEY=" docker/.env | cut -d= -f2)
    SUPABASE_ANON_KEY=$(grep "^SUPABASE_ANON_KEY=" docker/.env | cut -d= -f2)
    
    # OpenAI
    if [ -z "$OPENAI_API_KEY" ] || [[ "$OPENAI_API_KEY" == *"XXXX"* ]]; then
        echo -e "  ${RED}✗ OPENAI_API_KEY não configurada${NC}"
        ((ERRORS++))
    else
        echo -e "  ${GREEN}✓${NC} OPENAI_API_KEY configurada"
    fi
    
    # Supabase URL
    if [ -z "$SUPABASE_URL" ] || [[ "$SUPABASE_URL" == *"XXXX"* ]]; then
        echo -e "  ${RED}✗ SUPABASE_URL não configurada${NC}"
        ((ERRORS++))
    else
        echo -e "  ${GREEN}✓${NC} SUPABASE_URL configurada"
    fi
    
    # Supabase Service Key
    if [ -z "$SUPABASE_SERVICE_KEY" ] || [[ "$SUPABASE_SERVICE_KEY" == *"XXXX"* ]]; then
        echo -e "  ${RED}✗ SUPABASE_SERVICE_KEY não configurada${NC}"
        ((ERRORS++))
    else
        echo -e "  ${GREEN}✓${NC} SUPABASE_SERVICE_KEY configurada"
    fi
    
    # Supabase Anon Key
    if [ -z "$SUPABASE_ANON_KEY" ] || [[ "$SUPABASE_ANON_KEY" == *"XXXX"* ]]; then
        echo -e "  ${YELLOW}⚠${NC} SUPABASE_ANON_KEY não configurada ${YELLOW}(opcional para Sprint 1.1)${NC}"
        ((WARNINGS++))
    else
        echo -e "  ${GREEN}✓${NC} SUPABASE_ANON_KEY configurada"
    fi
fi

echo ""

# ============================================================================
# 3. Validar Conectividade OpenAI
# ============================================================================
echo -e "${BLUE}[3/6] Validando conectividade OpenAI...${NC}"

if command -v curl &> /dev/null; then
    if [ ! -z "$OPENAI_API_KEY" ]; then
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
            https://api.openai.com/v1/models \
            -H "Authorization: Bearer $OPENAI_API_KEY" \
            --max-time 10)
        
        if [ "$HTTP_CODE" = "200" ]; then
            echo -e "  ${GREEN}✓${NC} OpenAI API conectando (HTTP 200)"
        else
            echo -e "  ${RED}✗${NC} OpenAI API falhou (HTTP $HTTP_CODE)"
            ((ERRORS++))
        fi
    else
        echo -e "  ${YELLOW}⚠${NC} Pulando teste (OPENAI_API_KEY não configurada)"
    fi
else
    echo -e "  ${YELLOW}⚠${NC} curl não disponível, pulando teste"
    ((WARNINGS++))
fi

echo ""

# ============================================================================
# 4. Validar Conectividade Supabase
# ============================================================================
echo -e "${BLUE}[4/6] Validando conectividade Supabase...${NC}"

if command -v curl &> /dev/null; then
    if [ ! -z "$SUPABASE_URL" ] && [ ! -z "$SUPABASE_SERVICE_KEY" ]; then
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
            "${SUPABASE_URL}/rest/v1/" \
            -H "apikey: ${SUPABASE_SERVICE_KEY}" \
            --max-time 10)
        
        if [ "$HTTP_CODE" = "200" ]; then
            echo -e "  ${GREEN}✓${NC} Supabase conectando (HTTP 200)"
        else
            echo -e "  ${RED}✗${NC} Supabase falhou (HTTP $HTTP_CODE)"
            ((ERRORS++))
        fi
    else
        echo -e "  ${YELLOW}⚠${NC} Pulando teste (credenciais não configuradas)"
    fi
else
    echo -e "  ${YELLOW}⚠${NC} curl não disponível, pulando teste"
fi

echo ""

# ============================================================================
# 5. Verificar Docker
# ============================================================================
echo -e "${BLUE}[5/6] Verificando Docker...${NC}"

if command -v docker &> /dev/null; then
    echo -e "  ${GREEN}✓${NC} Docker instalado ($(docker --version | cut -d' ' -f3 | tr -d ','))"
    
    if docker info &> /dev/null; then
        echo -e "  ${GREEN}✓${NC} Docker daemon rodando"
    else
        echo -e "  ${RED}✗${NC} Docker daemon não está rodando"
        ((ERRORS++))
    fi
else
    echo -e "  ${RED}✗${NC} Docker não instalado"
    ((ERRORS++))
fi

if command -v docker-compose &> /dev/null; then
    echo -e "  ${GREEN}✓${NC} Docker Compose instalado ($(docker-compose --version | cut -d' ' -f4 | tr -d ','))"
else
    echo -e "  ${RED}✗${NC} Docker Compose não instalado"
    ((ERRORS++))
fi

echo ""

# ============================================================================
# 6. Verificar Dependências Scripts
# ============================================================================
echo -e "${BLUE}[6/6] Verificando dependências de scripts...${NC}"

check_cmd() {
    if command -v $1 &> /dev/null; then
        echo -e "  ${GREEN}✓${NC} $1 instalado"
    else
        echo -e "  ${YELLOW}⚠${NC} $1 não instalado ${YELLOW}(recomendado para scripts)${NC}"
        ((WARNINGS++))
    fi
}

check_cmd "curl"
check_cmd "jq"
check_cmd "grep"

echo ""

# ============================================================================
# Resumo
# ============================================================================
echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}RESUMO DA VALIDAÇÃO${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ SETUP VALIDADO COM SUCESSO!${NC}"
    echo ""
    echo -e "Próximos passos:"
    echo -e "  1. Iniciar n8n: ${BLUE}docker-compose -f docker/docker-compose-dev.yml up -d${NC}"
    echo -e "  2. Acessar n8n: ${BLUE}http://localhost:5678${NC}"
    echo -e "  3. Deploy SQL: Seguir ${BLUE}docs/validation/DEPLOY_SQL.md${NC}"
    echo -e "  4. Executar ingest: ${BLUE}./scripts/ingest-knowledge.sh${NC}"
    echo ""
    
    if [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}⚠ $WARNINGS avisos encontrados (não impedem execução)${NC}"
    fi
    
    exit 0
else
    echo -e "${RED}❌ VALIDAÇÃO FALHOU: $ERRORS erros encontrados${NC}"
    
    if [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}⚠ $WARNINGS avisos encontrados${NC}"
    fi
    
    echo ""
    echo -e "Corrija os erros acima antes de prosseguir."
    echo -e "Consulte: ${BLUE}QUICKSTART.md${NC} ou ${BLUE}docs/validation/SETUP_CREDENTIALS.md${NC}"
    echo ""
    exit 1
fi
