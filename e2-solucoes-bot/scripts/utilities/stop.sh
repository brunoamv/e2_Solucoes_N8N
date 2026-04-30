#!/bin/bash

# Stop all development containers

echo "🛑 Parando todos os containers..."
docker-compose -f docker/docker-compose-dev.yml --env-file docker/.env.dev down

echo "✅ Containers parados"
