#!/bin/bash
# ============================================================================
# Fix Docker Snap Installation
# ============================================================================
#
# Problema: Docker daemon não inicia após kill de processos
# Causa: Snap Docker em estado corrompido
# Solução: Restart completo do snap Docker
#
# USO: sudo bash scripts/fix-docker-snap.sh
# ============================================================================

set -e

echo "=========================================="
echo "Docker Snap Recovery"
echo "=========================================="
echo ""

# ETAPA 1: Parar todos os serviços Docker Snap
echo "📋 ETAPA 1: Parando serviços Docker Snap..."
echo ""

snap stop docker 2>&1 || echo "⚠️  Snap já parado"
sleep 3

echo "✅ Serviços Snap parados"
echo ""

# ETAPA 2: Verificar processos órfãos
echo "📋 ETAPA 2: Verificando processos órfãos..."
echo ""

ORPHANS=$(ps aux | grep -E "/snap/docker.*/(containerd|dockerd|docker-proxy)" | grep -v grep | awk '{print $2}' || true)

if [ -n "$ORPHANS" ]; then
    echo "⚠️  Processos órfãos encontrados, matando..."
    echo "$ORPHANS" | xargs -r kill -9 2>&1 || true
    sleep 2
else
    echo "✅ Nenhum processo órfão"
fi

echo ""

# ETAPA 3: Limpar sockets e PIDs
echo "📋 ETAPA 3: Limpando sockets e PIDs..."
echo ""

rm -f /run/snap.docker/docker.pid 2>&1 || true
rm -f /run/snap.docker/docker.sock 2>&1 || true
rm -f /var/run/docker.sock 2>&1 || true
rm -f /var/run/docker.pid 2>&1 || true

echo "✅ Sockets limpos"
echo ""

# ETAPA 4: Iniciar Docker Snap
echo "📋 ETAPA 4: Iniciando Docker Snap..."
echo ""

snap start docker

echo "⏳ Aguardando Docker inicializar (10s)..."
sleep 10

echo ""

# ETAPA 5: Verificar status
echo "📋 ETAPA 5: Verificando status..."
echo ""

if docker ps >/dev/null 2>&1; then
    echo "✅ Docker funcionando!"
    echo ""
    docker ps -a --format "table {{.Names}}\t{{.Status}}"
else
    echo "❌ Docker ainda não está respondendo"
    echo ""
    echo "Tentando mais uma vez..."
    snap restart docker
    sleep 10

    if docker ps >/dev/null 2>&1; then
        echo "✅ Docker funcionando após restart!"
        echo ""
        docker ps -a --format "table {{.Names}}\t{{.Status}}"
    else
        echo "❌ Docker não responde. Logs do sistema:"
        journalctl -u snap.docker.dockerd -n 50 --no-pager
    fi
fi

echo ""
echo "=========================================="
echo "Recovery Completo"
echo "=========================================="
echo ""
echo "Próximos passos:"
echo "1. Verificar containers: docker ps -a"
echo "2. Remover containers órfãos: docker rm -f e2bot-n8n-dev e2bot-evolution-dev e2bot-postgres-dev"
echo "3. Subir stack limpo: docker-compose -f docker/docker-compose-dev.yml up -d"
echo "4. Testar mount: docker exec e2bot-n8n-dev ls -la /email-templates/"
echo ""
