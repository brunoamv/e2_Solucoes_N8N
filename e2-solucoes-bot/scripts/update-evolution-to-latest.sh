#!/bin/bash

# Script para atualizar Evolution API para versão mais recente disponível
# Data: $(date)

echo "🔄 Atualizando Evolution API para versão mais recente"
echo "======================================================"
echo ""

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Verificar se há uma versão mais recente construída da fonte
echo -e "${YELLOW}📦 Verificando opções de atualização...${NC}"
echo ""

# Opção 1: Usar imagem da comunidade/fork mais recente
echo -e "${BLUE}Opção 1: Usar imagem evolutionapi/evolution-api (repositório oficial)${NC}"
echo "Verificando versões disponíveis..."

# Verificar versões disponíveis do repositório oficial
docker pull evolutionapi/evolution-api:latest 2>/dev/null

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Imagem oficial disponível!${NC}"
    EVOLUTION_IMAGE="evolutionapi/evolution-api:latest"
else
    echo -e "${YELLOW}⚠️ Imagem oficial não encontrada, tentando alternativas...${NC}"

    # Opção 2: Construir localmente a partir do código fonte
    echo ""
    echo -e "${BLUE}Opção 2: Clonar e construir a partir do código fonte${NC}"

    # Criar diretório temporário
    TEMP_DIR="/tmp/evolution-api-build"
    rm -rf $TEMP_DIR
    mkdir -p $TEMP_DIR
    cd $TEMP_DIR

    # Clonar repositório
    echo "Clonando repositório..."
    git clone https://github.com/EvolutionAPI/evolution-api.git
    cd evolution-api

    # Verificar última tag
    LATEST_TAG=$(git describe --tags --abbrev=0)
    echo -e "${BLUE}Última versão disponível: ${LATEST_TAG}${NC}"

    # Fazer checkout da última tag
    git checkout $LATEST_TAG

    # Construir imagem
    echo -e "${YELLOW}Construindo imagem Docker...${NC}"
    docker build -t evolution-api:local-latest .

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Imagem construída localmente!${NC}"
        EVOLUTION_IMAGE="evolution-api:local-latest"
    else
        echo -e "${RED}❌ Erro ao construir imagem${NC}"
        exit 1
    fi

    # Voltar ao diretório original
    cd - > /dev/null
fi

# Parar container antigo
echo ""
echo -e "${YELLOW}📦 Parando container antigo...${NC}"
docker-compose -f docker/docker-compose-dev.yml stop evolution-api
docker-compose -f docker/docker-compose-dev.yml rm -f evolution-api

# Atualizar docker-compose com nova imagem
echo ""
echo -e "${YELLOW}📦 Atualizando docker-compose-dev.yml...${NC}"

# Fazer backup
cp docker/docker-compose-dev.yml docker/docker-compose-dev.yml.backup.$(date +%Y%m%d_%H%M%S)

# Atualizar imagem no docker-compose
if [ "$EVOLUTION_IMAGE" == "evolutionapi/evolution-api:latest" ]; then
    sed -i 's|image: atendai/evolution-api:.*|image: evolutionapi/evolution-api:latest|g' docker/docker-compose-dev.yml
else
    sed -i 's|image: atendai/evolution-api:.*|image: evolution-api:local-latest|g' docker/docker-compose-dev.yml
fi

echo -e "${GREEN}✅ docker-compose atualizado${NC}"

# Subir novo container
echo ""
echo -e "${YELLOW}📦 Iniciando novo container...${NC}"
docker-compose -f docker/docker-compose-dev.yml up -d evolution-api

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Container iniciado com sucesso${NC}"
else
    echo -e "${RED}❌ Erro ao iniciar container${NC}"
    exit 1
fi

# Aguardar inicialização
echo ""
echo -e "${YELLOW}⏳ Aguardando Evolution API inicializar (30 segundos)...${NC}"
sleep 30

# Verificar status e versão
echo ""
echo -e "${YELLOW}📦 Verificando status e versão...${NC}"
echo ""

# Verificar logs
echo -e "${BLUE}Últimas linhas do log:${NC}"
docker logs e2bot-evolution-dev --tail 20

# Verificar se está rodando
echo ""
echo -e "${BLUE}Status do container:${NC}"
docker ps | grep evolution

# Testar endpoint
echo ""
echo -e "${BLUE}Testando endpoint:${NC}"
curl -s http://localhost:8080 | head -5 || echo "Endpoint não respondendo ainda"

echo ""
echo -e "${GREEN}🎉 Processo concluído!${NC}"
echo ""
echo "📋 Próximos passos:"
echo "  1. Verificar se o campo 'senderPn' está disponível no webhook"
echo "  2. Atualizar workflow para usar o novo campo"
echo "  3. Testar extração do phone_number"
echo ""
echo "💡 Para verificar os campos disponíveis:"
echo "  - Envie uma mensagem teste pelo WhatsApp"
echo "  - Verifique os logs: docker logs e2bot-evolution-dev -f"
echo "  - Ou monitore o webhook no n8n"