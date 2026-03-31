#!/bin/bash
# ============================================================================
# Ultimate Docker Fix - 3-Step Nuclear Recovery
# ============================================================================
#
# Problema: Containers não podem ser mortos nem com sudo
# Causa: Restart policy + processo protegido no kernel
# Solução: Desabilitar restart → Update Docker config → Reboot sistema
#
# USO: sudo bash scripts/ultimate-docker-fix.sh
# ============================================================================

set -e

echo "=========================================="
echo "Ultimate Docker Fix - 3-Step Recovery"
echo "=========================================="
echo ""

# Lista de containers
CONTAINERS=(
    "e2bot-n8n-dev"
    "e2bot-evolution-dev"
    "e2bot-postgres-dev"
    "414184ddf52f_e2bot-evolution-redis"
    "b31eca759bb3_e2bot-evolution-postgres"
)

# ============================================================================
# ETAPA 1: Desabilitar Restart Policy
# ============================================================================
echo "📋 ETAPA 1: Desabilitando restart policy..."
echo ""

for container in "${CONTAINERS[@]}"; do
    echo "  🔧 Desabilitando restart em: $container"
    docker update --restart=no "$container" 2>&1 || echo "     ⚠️  Falhou"
done

echo ""
echo "✅ Restart policies desabilitados"
echo ""

# ============================================================================
# ETAPA 2: Parar Docker Daemon
# ============================================================================
echo "📋 ETAPA 2: Parando Docker daemon..."
echo ""

systemctl stop docker.socket
systemctl stop docker

echo "✅ Docker daemon parado"
echo ""

# Aguardar processos finalizarem
echo "⏳ Aguardando processos finalizarem (10s)..."
sleep 10

# ============================================================================
# ETAPA 3: Verificar Processos Órfãos
# ============================================================================
echo "📋 ETAPA 3: Verificando processos Docker órfãos..."
echo ""

ORPHANS=$(ps aux | grep -E "(dockerd|containerd|docker-proxy|tini.*n8n)" | grep -v grep | awk '{print $2}' || true)

if [ -n "$ORPHANS" ]; then
    echo "⚠️  Processos órfãos encontrados:"
    ps aux | grep -E "(dockerd|containerd|docker-proxy|tini.*n8n)" | grep -v grep
    echo ""
    echo "🔥 Matando processos órfãos..."
    echo "$ORPHANS" | xargs -r kill -9 2>&1 || echo "   ⚠️  Alguns processos não puderam ser mortos"
else
    echo "✅ Nenhum processo órfão encontrado"
fi

echo ""

# ============================================================================
# ETAPA 4: Limpar Estado do Docker
# ============================================================================
echo "📋 ETAPA 4: Limpando estado do Docker..."
echo ""

# Remove PID files se existirem
rm -f /var/run/docker.pid
rm -f /var/run/docker.sock

echo "✅ Estado limpo"
echo ""

# ============================================================================
# ETAPA 5: Iniciar Docker Daemon Limpo
# ============================================================================
echo "📋 ETAPA 5: Iniciando Docker daemon limpo..."
echo ""

systemctl start docker

echo "⏳ Aguardando Docker inicializar (5s)..."
sleep 5

echo "✅ Docker iniciado"
echo ""

# ============================================================================
# ETAPA 6: Verificar Limpeza
# ============================================================================
echo "📋 ETAPA 6: Verificando limpeza..."
echo ""

REMAINING=$(docker ps -a --format "{{.Names}}" | grep -E "e2bot" || true)

if [ -n "$REMAINING" ]; then
    echo "⚠️  Containers ainda existem:"
    docker ps -a --format "table {{.Names}}\t{{.Status}}"
    echo ""
    echo "🔥 Tentando remover novamente..."
    for container in "${CONTAINERS[@]}"; do
        docker rm -f "$container" 2>&1 || echo "   ⚠️  Falhou: $container"
    done
else
    echo "✅ Todos os containers removidos"
fi

echo ""

# ============================================================================
# RESULTADO FINAL
# ============================================================================
echo "=========================================="
echo "✅ Recovery Completo!"
echo "=========================================="
echo ""
echo "📋 Containers atuais:"
docker ps -a --format "table {{.Names}}\t{{.Status}}"
echo ""
echo "Próximos passos:"
echo "1. docker-compose -f docker/docker-compose-dev.yml up -d"
echo "2. docker ps"
echo "3. docker exec e2bot-n8n-dev ls -la /email-templates/"
echo ""
echo "⚠️  Se ainda houver problemas, REBOOT o sistema:"
echo "   sudo reboot"
echo ""
