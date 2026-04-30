#!/bin/bash

# ============================================================================
# Evolution API - Fix de Inicialização Completo
# ============================================================================

set -e

PROJECT_ROOT="/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot"
ENV_FILE="$PROJECT_ROOT/docker/.env"
DOCKER_COMPOSE_FILE="$PROJECT_ROOT/docker/docker-compose-dev.yml"

echo "============================================================================="
echo "Evolution API - Fix de Inicialização Completo"
echo "============================================================================="
echo ""

# 1. Verificar .env
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Arquivo .env não encontrado em: $ENV_FILE"
    exit 1
fi
echo "✅ Arquivo .env encontrado"
echo ""

# 2. Parar e remover TODOS os containers relacionados
echo "🛑 Parando todos os containers Evolution..."
docker stop e2bot-evolution-dev e2bot-evolution-postgres e2bot-evolution-redis 2>/dev/null || true
echo ""

echo "🗑️  Removendo containers órfãos..."
docker rm -f e2bot-evolution-dev e2bot-evolution-postgres e2bot-evolution-redis 2>/dev/null || true
echo ""

# 3. Remover volumes órfãos
echo "🗑️  Removendo volumes órfãos..."
docker volume rm e2bot-evolution-postgres-data e2bot-evolution-redis-data 2>/dev/null || true
echo ""

# 4. Verificar variáveis críticas no .env
echo "🔍 Verificando configurações críticas..."
DATABASE_PROVIDER=$(grep "^DATABASE_PROVIDER=" "$ENV_FILE" | cut -d'=' -f2)
echo "   DATABASE_PROVIDER: $DATABASE_PROVIDER"

if [ -z "$DATABASE_PROVIDER" ]; then
    echo "❌ DATABASE_PROVIDER está vazio no .env!"
    exit 1
fi
echo "✅ Configurações válidas"
echo ""

# 5. Recriar containers usando docker-compose
echo "📦 Recriando containers Evolution API com docker-compose..."
cd "$PROJECT_ROOT/docker"
docker-compose -f docker-compose-dev.yml up -d evolution-postgres evolution-redis evolution-api
echo ""

# 6. Aguardar inicialização
echo "⏳ Aguardando Evolution API inicializar (30s)..."
sleep 30
echo ""

# 7. Testar conectividade
echo "🔍 Testando conectividade da API..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/manager/instances || echo "000")

if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "401" ]; then
    echo "✅ Evolution API respondendo! (HTTP $HTTP_CODE)"
    echo ""
    echo "🎉 Sucesso! Evolution API iniciada corretamente"
    echo ""
    echo "📋 Próximos passos:"
    echo "   1. Acesse: http://localhost:8080/manager"
    echo "   2. Use API_KEY do .env para autenticação"
    echo "   3. Crie instância WhatsApp"
    echo ""
else
    echo "❌ Evolution API ainda não está respondendo (HTTP $HTTP_CODE)"
    echo ""
    echo "📋 Troubleshooting:"
    echo "   1. Verificar logs: docker logs e2bot-evolution-dev"
    echo "   2. Verificar status: docker ps | grep evolution"
    echo "   3. Verificar .env: grep DATABASE_PROVIDER $ENV_FILE"
    echo ""
    exit 1
fi

# 8. Mostrar logs finais
echo "📋 Últimas linhas dos logs (verificar erros):"
docker logs e2bot-evolution-dev --tail 20
