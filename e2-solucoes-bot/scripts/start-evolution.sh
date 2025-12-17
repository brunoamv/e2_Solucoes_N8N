#!/bin/bash

# ============================================================================
# Evolution API - Inicialização CORRETA usando docker-compose
# ============================================================================
#
# IMPORTANTE: SEMPRE use docker-compose, NUNCA docker run standalone!
# O workaround da Issue #1474 NÃO funciona de forma confiável.
# ============================================================================

set -e

PROJECT_ROOT="/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot"
COMPOSE_FILE="$PROJECT_ROOT/docker/docker-compose-dev.yml"

cd "$PROJECT_ROOT/docker"

echo "============================================================================="
echo "Evolution API - Inicialização (docker-compose)"
echo "============================================================================="
echo ""

# 1. Verificar se já está rodando
RUNNING=$(docker ps --filter "name=e2bot-evolution-dev" --format "{{.Names}}" 2>/dev/null || true)
if [ -n "$RUNNING" ]; then
    echo "⚠️  Evolution API já está rodando!"
    echo ""
    echo "Status atual:"
    docker ps --filter "name=e2bot-evolution" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    echo ""
    echo "Para reiniciar:"
    echo "   docker-compose -f docker-compose-dev.yml restart evolution-api"
    echo ""
    exit 0
fi

# 2. Iniciar containers
echo "📦 Iniciando Evolution API via docker-compose..."
docker-compose -f docker-compose-dev.yml up -d evolution-postgres evolution-redis evolution-api
echo ""

# 3. Aguardar inicialização
echo "⏳ Aguardando Evolution API inicializar (30s)..."
sleep 30
echo ""

# 4. Verificar status
echo "🔍 Verificando status dos containers..."
docker ps --filter "name=e2bot-evolution" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""

# 5. Testar conectividade
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/manager/instances 2>/dev/null || echo "000")

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Evolution API respondendo! (HTTP $HTTP_CODE)"
    echo ""
    echo "============================================================================="
    echo "🎉 Evolution API inicializada com sucesso!"
    echo "============================================================================="
    echo ""
    echo "📋 Próximos passos:"
    echo "   1. Acesse: http://localhost:8080/manager"
    echo "   2. Use EVOLUTION_API_KEY do .env para autenticação"
    echo "   3. Crie instância WhatsApp"
    echo ""
    echo "Comandos úteis:"
    echo "   Ver logs:      docker logs -f e2bot-evolution-dev"
    echo "   Ver status:    docker ps | grep evolution"
    echo "   Parar tudo:    docker-compose -f docker-compose-dev.yml stop"
    echo ""
else
    echo "⚠️  Evolution API não está respondendo (HTTP $HTTP_CODE)"
    echo ""
    echo "📋 Troubleshooting:"
    echo "   docker logs e2bot-evolution-dev --tail 50"
    echo ""
fi
