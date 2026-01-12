#!/bin/bash

# Script para atualizar Evolution API para versão 2.3+
# Data: $(date)

echo "🔄 Atualizando Evolution API para v2.3+"
echo "========================================"
echo ""

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Passo 1: Parar o container Evolution API
echo -e "${YELLOW}📦 Passo 1: Parando container Evolution API...${NC}"
docker-compose -f docker/docker-compose-dev.yml stop evolution-api
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Container parado com sucesso${NC}"
else
    echo -e "${RED}⚠️ Aviso: Container pode não estar rodando${NC}"
fi

# Passo 2: Remover container antigo
echo ""
echo -e "${YELLOW}📦 Passo 2: Removendo container antigo...${NC}"
docker-compose -f docker/docker-compose-dev.yml rm -f evolution-api

# Passo 3: Listar imagens antigas
echo ""
echo -e "${YELLOW}📦 Passo 3: Listando imagens antigas do Evolution API...${NC}"
docker images | grep evolution

# Passo 4: Remover imagens antigas
echo ""
echo -e "${YELLOW}📦 Passo 4: Removendo imagens antigas...${NC}"

# Remove todas as imagens do Evolution API
docker images | grep 'atendai/evolution-api' | awk '{print $1":"$2}' | xargs -r docker rmi -f

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Imagens antigas removidas${NC}"
else
    echo -e "${YELLOW}⚠️ Algumas imagens podem estar em uso${NC}"
fi

# Passo 5: Atualizar docker-compose para forçar pull
echo ""
echo -e "${YELLOW}📦 Passo 5: Atualizando docker-compose-dev.yml...${NC}"

# Fazer backup do arquivo original
cp docker/docker-compose-dev.yml docker/docker-compose-dev.yml.backup

# Atualizar para usar versão específica v2.3.0 ou superior
sed -i 's|image: atendai/evolution-api:.*|image: atendai/evolution-api:v2.3.0|g' docker/docker-compose-dev.yml

echo -e "${GREEN}✅ docker-compose atualizado para usar v2.3.0${NC}"

# Passo 6: Pull da nova imagem
echo ""
echo -e "${YELLOW}📦 Passo 6: Baixando Evolution API v2.3.0...${NC}"
docker pull atendai/evolution-api:v2.3.0

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Imagem v2.3.0 baixada com sucesso${NC}"
else
    echo -e "${RED}❌ Erro ao baixar imagem. Tentando com latest...${NC}"
    docker pull atendai/evolution-api:latest
fi

# Passo 7: Verificar versão baixada
echo ""
echo -e "${YELLOW}📦 Passo 7: Verificando versão baixada...${NC}"
docker images | grep evolution

# Passo 8: Subir novo container
echo ""
echo -e "${YELLOW}📦 Passo 8: Iniciando novo container...${NC}"
docker-compose -f docker/docker-compose-dev.yml up -d evolution-api

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Container iniciado com sucesso${NC}"
else
    echo -e "${RED}❌ Erro ao iniciar container${NC}"
    exit 1
fi

# Passo 9: Aguardar inicialização
echo ""
echo -e "${YELLOW}⏳ Aguardando Evolution API inicializar (30 segundos)...${NC}"
sleep 30

# Passo 10: Verificar logs e status
echo ""
echo -e "${YELLOW}📦 Passo 10: Verificando status...${NC}"
echo ""
echo -e "${BLUE}Últimas linhas do log:${NC}"
docker logs e2bot-evolution-api --tail 20

echo ""
echo -e "${BLUE}Verificando versão no container:${NC}"
docker exec e2bot-evolution-api cat package.json | grep '"version"' || echo "Não foi possível verificar versão"

echo ""
echo -e "${GREEN}🎉 Atualização concluída!${NC}"
echo ""
echo "📋 Resumo:"
echo "  - Imagens antigas removidas"
echo "  - Nova versão v2.3.0 instalada"
echo "  - Container reiniciado"
echo ""
echo "🔍 Próximos passos:"
echo "  1. Verificar se o webhook está recebendo o campo 'senderPn'"
echo "  2. Atualizar o workflow para usar o novo campo"
echo "  3. Testar extração do phone_number"
echo ""
echo "💡 Dica: Use 'docker logs e2bot-evolution-api -f' para monitorar os logs"