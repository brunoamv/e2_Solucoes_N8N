#!/bin/bash

# ============================================================================
# Nuclear Cleanup - Remove TUDO relacionado ao Evolution API
# ============================================================================

set -e

echo "============================================================================="
echo "🧹 Limpeza Nuclear - Evolution API"
echo "============================================================================="
echo ""

echo "⚠️  ATENÇÃO: Este script vai:"
echo "   - Parar TODOS os containers do projeto"
echo "   - Remover TODOS os containers (inclusive órfãos)"
echo "   - Remover TODOS os volumes"
echo "   - Limpar cache de imagens danificadas"
echo ""
read -p "Continuar? (s/N): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Ss]$ ]]; then
    echo "❌ Operação cancelada"
    exit 1
fi

echo ""
echo "🛑 Passo 1/6: Parando TODOS os containers do projeto..."
cd /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/docker
docker-compose -f docker-compose-dev.yml down 2>&1 | grep -v "WARNING" || true
echo "✅ Containers parados"
echo ""

echo "🗑️  Passo 2/6: Removendo containers Evolution por NOME..."
docker rm -f \
    e2bot-evolution-dev \
    e2bot-evolution-postgres \
    e2bot-evolution-redis \
    2>&1 | grep -v "No such container" || true
echo "✅ Containers removidos"
echo ""

echo "🗑️  Passo 3/6: Removendo containers órfãos por FILTRO..."
ORPHAN_IDS=$(docker ps -a --filter "name=e2bot-evolution" --format "{{.ID}}" 2>/dev/null || true)
if [ -n "$ORPHAN_IDS" ]; then
    echo "   Encontrados órfãos: $ORPHAN_IDS"
    echo "$ORPHAN_IDS" | xargs docker rm -f 2>&1 | grep -v "No such container" || true
    echo "✅ Órfãos removidos"
else
    echo "✅ Nenhum órfão encontrado"
fi
echo ""

echo "🗑️  Passo 4/6: Removendo TODOS os volumes Evolution..."
docker volume rm \
    e2bot-evolution-postgres-data \
    e2bot-evolution-redis-data \
    2>&1 | grep -v "No such volume" || true
echo "✅ Volumes removidos"
echo ""

echo "🧹 Passo 5/6: Limpando cache Docker (containers parados, volumes órfãos)..."
docker system prune -f --volumes 2>&1 | tail -3
echo "✅ Cache limpo"
echo ""

echo "🔍 Passo 6/6: Verificando limpeza..."
REMAINING=$(docker ps -a --filter "name=e2bot-evolution" --format "{{.Names}}" 2>/dev/null || true)
if [ -z "$REMAINING" ]; then
    echo "✅ NENHUM container Evolution encontrado"
else
    echo "⚠️  Ainda existem containers:"
    echo "$REMAINING"
    echo ""
    echo "❌ Limpeza incompleta. Verifique manualmente:"
    echo "   docker ps -a | grep evolution"
    exit 1
fi
echo ""

echo "============================================================================="
echo "🎉 Limpeza concluída com sucesso!"
echo "============================================================================="
echo ""
echo "📋 Próximo passo:"
echo "   cd /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/docker"
echo "   docker-compose -f docker-compose-dev.yml up -d evolution-postgres evolution-redis evolution-api"
echo ""
