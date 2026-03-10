#!/bin/bash

# ============================================================================
# Test Script - Valida cópia do .env para o container Evolution
# ============================================================================

echo "🔍 Testando cópia do .env para container Evolution..."
echo ""

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Variáveis
ENV_FILE="/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/docker/.env"
CONTAINER_NAME="e2bot-evolution-dev"

echo "1️⃣ Verificando se o arquivo .env existe localmente..."
if [ -f "$ENV_FILE" ]; then
    echo -e "   ${GREEN}✅ Arquivo encontrado: $ENV_FILE${NC}"
else
    echo -e "   ${RED}❌ Arquivo não encontrado: $ENV_FILE${NC}"
    exit 1
fi

echo ""
echo "2️⃣ Verificando se o container Evolution está rodando..."
if docker ps | grep -q "$CONTAINER_NAME"; then
    echo -e "   ${GREEN}✅ Container está rodando: $CONTAINER_NAME${NC}"
else
    echo -e "   ${YELLOW}⚠️  Container não está rodando. Iniciando...${NC}"
    cd /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/docker
    docker-compose -f docker-compose-dev.yml up -d evolution-api
    sleep 5
fi

echo ""
echo "3️⃣ Copiando .env para o container..."
docker cp "$ENV_FILE" "$CONTAINER_NAME:/evolution/.env"
if [ $? -eq 0 ]; then
    echo -e "   ${GREEN}✅ Arquivo copiado com sucesso${NC}"
else
    echo -e "   ${RED}❌ Falha ao copiar arquivo${NC}"
    exit 1
fi

echo ""
echo "4️⃣ Verificando se o arquivo existe dentro do container..."
docker exec "$CONTAINER_NAME" ls -la /evolution/.env > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo -e "   ${GREEN}✅ Arquivo existe dentro do container${NC}"

    echo ""
    echo "5️⃣ Verificando conteúdo do arquivo (primeiras linhas)..."
    echo "   Local:"
    head -n 3 "$ENV_FILE" | sed 's/^/      /'
    echo ""
    echo "   Container:"
    docker exec "$CONTAINER_NAME" head -n 3 /evolution/.env | sed 's/^/      /'
else
    echo -e "   ${RED}❌ Arquivo não existe dentro do container${NC}"
    exit 1
fi

echo ""
echo "6️⃣ Verificando se EVOLUTION_API_KEY está presente..."
LOCAL_KEY=$(grep "EVOLUTION_API_KEY=" "$ENV_FILE" | head -1)
CONTAINER_KEY=$(docker exec "$CONTAINER_NAME" grep "EVOLUTION_API_KEY=" /evolution/.env 2>/dev/null | head -1)

if [ -n "$CONTAINER_KEY" ]; then
    echo -e "   ${GREEN}✅ EVOLUTION_API_KEY encontrada no container${NC}"
    echo "      Local: ${LOCAL_KEY:0:40}..."
    echo "      Container: ${CONTAINER_KEY:0:40}..."
else
    echo -e "   ${RED}❌ EVOLUTION_API_KEY não encontrada no container${NC}"
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✅ TESTE CONCLUÍDO COM SUCESSO!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 Resumo:"
echo "   • Arquivo .env existe localmente"
echo "   • Container Evolution está rodando"
echo "   • Arquivo foi copiado com sucesso"
echo "   • EVOLUTION_API_KEY está presente no container"
echo ""
echo "🎯 Próximo passo:"
echo "   source scripts/evolution-helper.sh"
echo "   evolution_recreate"
echo ""