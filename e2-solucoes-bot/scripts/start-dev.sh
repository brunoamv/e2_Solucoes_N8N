#!/bin/bash

# ==========================================
# E2 SOLUÇÕES BOT - STARTUP DEVELOPMENT
# ==========================================

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "=========================================="
echo "  E2 SOLUÇÕES BOT - DESENVOLVIMENTO"
echo "=========================================="
echo -e "${NC}"

# Check if running from project root
if [ ! -f "docker/docker-compose-dev.yml" ]; then
    echo -e "${RED}❌ Erro: Execute este script da raiz do projeto${NC}"
    echo "   cd e2-solucoes-bot && ./scripts/start-dev.sh"
    exit 1
fi

# Check if .env.dev exists
if [ ! -f "docker/.env.dev" ]; then
    echo -e "${YELLOW}⚠️  Arquivo .env.dev não encontrado${NC}"
    echo ""
    echo "Criando a partir do template..."
    cp docker/.env.dev.example docker/.env.dev
    echo -e "${GREEN}✓${NC} Arquivo docker/.env.dev criado"
    echo ""
    echo -e "${YELLOW}📝 AÇÃO NECESSÁRIA:${NC}"
    echo "   Edite docker/.env.dev e preencha as chaves obrigatórias:"
    echo "   - ANTHROPIC_API_KEY"
    echo "   - OPENAI_API_KEY"
    echo "   - EVOLUTION_API_URL e EVOLUTION_API_KEY"
    echo "   - RDSTATION_CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN"
    echo ""
    echo "   Depois execute novamente: ./scripts/start-dev.sh"
    exit 0
fi

# Check for required API keys
echo -e "${BLUE}🔍 Verificando configuração...${NC}"

source docker/.env.dev

MISSING_KEYS=0

if [[ "$ANTHROPIC_API_KEY" == *"SUBSTITUA"* ]] || [ -z "$ANTHROPIC_API_KEY" ]; then
    echo -e "${RED}❌ ANTHROPIC_API_KEY não configurada${NC}"
    MISSING_KEYS=1
fi

if [[ "$OPENAI_API_KEY" == *"SUBSTITUA"* ]] || [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${RED}❌ OPENAI_API_KEY não configurada${NC}"
    MISSING_KEYS=1
fi

if [[ "$EVOLUTION_API_URL" == *"seudominio"* ]] || [ -z "$EVOLUTION_API_URL" ]; then
    echo -e "${RED}❌ EVOLUTION_API_URL não configurada${NC}"
    MISSING_KEYS=1
fi

if [[ "$RDSTATION_CLIENT_ID" == *"SUBSTITUA"* ]] || [ -z "$RDSTATION_CLIENT_ID" ]; then
    echo -e "${YELLOW}⚠️  RD Station não configurado (opcional para testes)${NC}"
fi

if [ $MISSING_KEYS -eq 1 ]; then
    echo ""
    echo -e "${RED}❌ Configure as chaves obrigatórias em docker/.env.dev${NC}"
    echo "   Ver: docker/.env.dev.example para instruções"
    exit 1
fi

echo -e "${GREEN}✓${NC} Configuração verificada"
echo ""

# Check Docker
echo -e "${BLUE}🐋 Verificando Docker...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker não está instalado${NC}"
    echo "   Instale: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Docker não está rodando${NC}"
    echo "   Inicie o Docker Desktop/Engine"
    exit 1
fi

echo -e "${GREEN}✓${NC} Docker está rodando"
echo ""

# Stop existing containers
echo -e "${BLUE}🛑 Parando containers existentes...${NC}"
docker-compose -f docker/docker-compose-dev.yml --env-file docker/.env.dev down 2>/dev/null || true
echo ""

# Pull images
echo -e "${BLUE}📥 Baixando imagens Docker...${NC}"
docker-compose -f docker/docker-compose-dev.yml --env-file docker/.env.dev pull
echo ""

# Start containers
echo -e "${BLUE}🚀 Iniciando serviços...${NC}"
docker-compose -f docker/docker-compose-dev.yml --env-file docker/.env.dev up -d

echo ""
echo -e "${BLUE}⏳ Aguardando serviços ficarem prontos...${NC}"
echo "   (isso pode levar 30-60 segundos)"
echo ""

# Wait for services
sleep 10

# Check health
echo -e "${BLUE}🏥 Verificando saúde dos serviços...${NC}"
echo ""

# PostgreSQL
if docker exec e2-postgres-dev pg_isready -U e2solucoes &> /dev/null; then
    echo -e "${GREEN}✓${NC} PostgreSQL (porta 5432)"
else
    echo -e "${YELLOW}⏳${NC} PostgreSQL ainda inicializando..."
fi

# Supabase DB
if docker exec e2-supabase-db-dev pg_isready -U supabase_admin &> /dev/null; then
    echo -e "${GREEN}✓${NC} Supabase DB (porta 5433)"
else
    echo -e "${YELLOW}⏳${NC} Supabase DB ainda inicializando..."
fi

# Redis
if docker exec e2-redis-dev redis-cli ping &> /dev/null; then
    echo -e "${GREEN}✓${NC} Redis (porta 6379)"
else
    echo -e "${YELLOW}⏳${NC} Redis ainda inicializando..."
fi

# n8n (wait a bit more)
sleep 5
if curl -s http://localhost:5678 > /dev/null; then
    echo -e "${GREEN}✓${NC} n8n (http://localhost:5678)"
else
    echo -e "${YELLOW}⏳${NC} n8n ainda inicializando..."
fi

# Supabase Studio
if curl -s http://localhost:3000 > /dev/null; then
    echo -e "${GREEN}✓${NC} Supabase Studio (http://localhost:3000)"
else
    echo -e "${YELLOW}⏳${NC} Supabase Studio ainda inicializando..."
fi

# Traefik
if curl -s http://localhost:8080 > /dev/null; then
    echo -e "${GREEN}✓${NC} Traefik Dashboard (http://localhost:8080)"
else
    echo -e "${YELLOW}⏳${NC} Traefik ainda inicializando..."
fi

# Mailhog
if curl -s http://localhost:8025 > /dev/null; then
    echo -e "${GREEN}✓${NC} Mailhog (http://localhost:8025)"
else
    echo -e "${YELLOW}⏳${NC} Mailhog ainda inicializando..."
fi

echo ""
echo -e "${GREEN}"
echo "=========================================="
echo "  ✅ AMBIENTE PRONTO!"
echo "=========================================="
echo -e "${NC}"
echo ""
echo "📋 PRÓXIMOS PASSOS:"
echo ""
echo "1. Acesse n8n:"
echo "   ${BLUE}http://localhost:5678${NC}"
echo ""
echo "2. Importe workflows:"
echo "   • n8n/workflows/01_main_whatsapp_handler.json"
echo "   • n8n/workflows/02_ai_agent_conversation.json"
echo ""
echo "3. Configure credenciais no n8n:"
echo "   • Anthropic API (Claude)"
echo "   • Evolution API (WhatsApp)"
echo "   • RD Station CRM"
echo "   • PostgreSQL (já configurado)"
echo ""
echo "4. Acesse outros serviços:"
echo "   • Supabase Studio: ${BLUE}http://localhost:3000${NC}"
echo "   • Traefik Dashboard: ${BLUE}http://localhost:8080${NC}"
echo "   • Mailhog (emails): ${BLUE}http://localhost:8025${NC}"
echo ""
echo "📖 DOCUMENTAÇÃO:"
echo "   • Setup completo: docs/Setups/README.md"
echo "   • RD Station CRM: docs/Setups/SETUP_RDSTATION.md"
echo "   • Workflows: docs/implementation/README.md"
echo ""
echo "🔧 COMANDOS ÚTEIS:"
echo "   • Ver logs: ./scripts/logs.sh"
echo "   • Parar: docker-compose -f docker/docker-compose-dev.yml down"
echo "   • Restart: ./scripts/restart.sh"
echo ""
echo -e "${GREEN}Bom desenvolvimento! 🚀${NC}"
echo ""
