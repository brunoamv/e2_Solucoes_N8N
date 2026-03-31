#!/bin/bash
# ============================================================================
# Force Remove Stuck Docker Containers - Nuclear Option
# ============================================================================
#
# Problema: Containers não param nem com restart do Docker daemon
# Solução: Remover containers forçadamente (SEM parar)
#
# USO: sudo bash scripts/force-remove-containers.sh
# ============================================================================

set -e

echo "=========================================="
echo "Docker Force Remove - NUCLEAR OPTION"
echo "=========================================="
echo ""
echo "⚠️  ATENÇÃO: Esta operação vai REMOVER containers sem parar!"
echo "⚠️  Dados NÃO persistidos em volumes serão PERDIDOS!"
echo "⚠️  Volumes nomeados serão PRESERVADOS."
echo ""

# Lista de containers do E2 Bot
CONTAINERS=(
    "e2bot-n8n-dev"
    "e2bot-evolution-dev"
    "e2bot-postgres-dev"
    "414184ddf52f_e2bot-evolution-redis"
    "b31eca759bb3_e2bot-evolution-postgres"
)

echo "📋 Containers que serão removidos:"
for container in "${CONTAINERS[@]}"; do
    echo "  - $container"
done
echo ""

read -p "Confirmar remoção forçada? (s/N): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Ss]$ ]]; then
    echo "❌ Operação cancelada"
    exit 1
fi

echo "🚨 Iniciando remoção forçada..."
echo ""

# Remover cada container COM FORÇA
for container in "${CONTAINERS[@]}"; do
    echo "🔥 Removendo $container..."
    docker rm -f "$container" 2>&1 || echo "   ⚠️  Falhou (container pode não existir)"
done

echo ""
echo "🧹 Limpando networks órfãs..."
docker network prune -f

echo ""
echo "📋 Containers restantes:"
docker ps -a --format "table {{.Names}}\t{{.Status}}"

echo ""
echo "=========================================="
echo "✅ Remoção forçada completa!"
echo "=========================================="
echo ""
echo "Próximos passos:"
echo "1. Subir stack limpo: docker-compose -f docker/docker-compose-dev.yml up -d"
echo "2. Verificar: docker ps"
echo "3. Testar mount: docker exec e2bot-n8n-dev ls -la /email-templates/"
echo ""
