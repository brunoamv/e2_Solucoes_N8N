#!/bin/bash
# ============================================================================
# Fix Docker Stuck Containers - Emergency Recovery Script
# ============================================================================
#
# Problema: Containers não param com docker-compose down (permission denied)
# Solução: Reiniciar Docker daemon para limpar estado travado
#
# USO: sudo bash scripts/fix-docker-stuck.sh
# ============================================================================

set -e

echo "=========================================="
echo "Docker Emergency Recovery - Starting"
echo "=========================================="
echo ""

# 1. Listar containers antes
echo "📋 Containers ANTES do recovery:"
docker ps --format "table {{.Names}}\t{{.Status}}"
echo ""

# 2. Tentar parada normal primeiro
echo "🔄 Tentando parada normal (provavelmente vai falhar)..."
docker-compose -f docker/docker-compose-dev.yml down 2>&1 || echo "❌ Parada normal falhou (esperado)"
echo ""

# 3. Reiniciar Docker daemon (SOLUÇÃO)
echo "🚨 SOLUÇÃO: Reiniciando Docker daemon..."
echo "⚠️  Isso vai parar TODOS os containers do sistema!"
echo ""
read -p "Confirmar reinício do Docker daemon? (s/N): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Ss]$ ]]; then
    echo "🔄 Reiniciando Docker..."
    systemctl restart docker

    # Aguardar Docker subir
    echo "⏳ Aguardando Docker daemon inicializar..."
    sleep 5

    # Verificar status
    echo "✅ Docker daemon status:"
    systemctl is-active docker
    echo ""

    # 4. Listar containers depois
    echo "📋 Containers DEPOIS do recovery:"
    docker ps --format "table {{.Names}}\t{{.Status}}" || echo "Nenhum container rodando (esperado)"
    echo ""

    # 5. Limpar networks órfãs
    echo "🧹 Limpando networks órfãs..."
    docker network prune -f
    echo ""

    # 6. Limpar volumes não usados (CUIDADO)
    echo "⚠️  Pular limpeza de volumes (para preservar dados)"
    # docker volume prune -f
    echo ""

    # 7. Subir stack novamente
    echo "=========================================="
    echo "✅ Recovery completo!"
    echo "=========================================="
    echo ""
    echo "Próximos passos:"
    echo "1. Subir stack: docker-compose -f docker/docker-compose-dev.yml up -d"
    echo "2. Verificar: docker ps"
    echo "3. Testar mount: docker exec e2bot-n8n-dev ls -la /email-templates/"
    echo ""
else
    echo "❌ Recovery cancelado pelo usuário"
    exit 1
fi
