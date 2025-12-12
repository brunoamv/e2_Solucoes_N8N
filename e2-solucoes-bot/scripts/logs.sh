#!/bin/bash

# View logs from all services or specific service

SERVICE=${1:-""}

if [ -z "$SERVICE" ]; then
    echo "📋 Logs de todos os serviços (Ctrl+C para sair)"
    echo ""
    docker-compose -f docker/docker-compose-dev.yml logs -f
else
    echo "📋 Logs de: $SERVICE"
    echo ""
    docker-compose -f docker/docker-compose-dev.yml logs -f $SERVICE
fi
