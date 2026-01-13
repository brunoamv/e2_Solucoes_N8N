#!/bin/bash

# Script para limpar execuções antigas do n8n e melhorar performance
# Data: 2025-01-12

echo "=== Limpeza de Execuções n8n ==="
echo ""

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Verificar status atual
echo -e "${YELLOW}📊 Status atual do banco de dados n8n:${NC}"
docker exec e2bot-postgres-dev psql -U postgres -d n8n_db -c "
SELECT
    'Total de execuções' as metric,
    COUNT(*) as value
FROM execution_entity
UNION ALL
SELECT
    'Execuções com erro' as metric,
    COUNT(*) as value
FROM execution_entity
WHERE finished = true AND stopped_at IS NOT NULL
UNION ALL
SELECT
    'Tamanho total (MB)' as metric,
    ROUND(pg_total_relation_size('execution_entity')::numeric / 1048576, 2) as value
FROM pg_class
WHERE relname = 'execution_entity';
"

echo ""
echo -e "${YELLOW}📅 Distribuição de execuções por data:${NC}"
docker exec e2bot-postgres-dev psql -U postgres -d n8n_db -c "
SELECT
    DATE(started_at) as date,
    COUNT(*) as executions,
    COUNT(CASE WHEN finished = true AND stopped_at IS NOT NULL THEN 1 END) as errors
FROM execution_entity
WHERE started_at > NOW() - INTERVAL '7 days'
GROUP BY DATE(started_at)
ORDER BY date DESC;
"

# 2. Backup antes da limpeza (opcional)
echo ""
echo -e "${YELLOW}💾 Criando backup das últimas 100 execuções...${NC}"
docker exec e2bot-postgres-dev psql -U postgres -d n8n_db -c "
CREATE TABLE IF NOT EXISTS execution_backup_$(date +%Y%m%d) AS
SELECT * FROM execution_entity
ORDER BY started_at DESC
LIMIT 100;
"

# 3. Limpar execuções antigas
echo ""
echo -e "${GREEN}🧹 Removendo execuções antigas...${NC}"

# Remover execuções com erro mais antigas que 1 dia
echo "  - Removendo execuções com erro (> 1 dia)..."
docker exec e2bot-postgres-dev psql -U postgres -d n8n_db -c "
DELETE FROM execution_entity
WHERE finished = true
  AND stopped_at IS NOT NULL
  AND started_at < NOW() - INTERVAL '1 day';
"

# Remover execuções bem-sucedidas mais antigas que 3 dias
echo "  - Removendo execuções bem-sucedidas (> 3 dias)..."
docker exec e2bot-postgres-dev psql -U postgres -d n8n_db -c "
DELETE FROM execution_entity
WHERE finished = true
  AND stopped_at IS NULL
  AND started_at < NOW() - INTERVAL '3 days';
"

# Manter apenas as últimas 1000 execuções
echo "  - Mantendo apenas as últimas 1000 execuções..."
docker exec e2bot-postgres-dev psql -U postgres -d n8n_db -c "
DELETE FROM execution_entity
WHERE id NOT IN (
    SELECT id FROM execution_entity
    ORDER BY started_at DESC
    LIMIT 1000
);
"

# 4. Vacuum e reindex para recuperar espaço
echo ""
echo -e "${GREEN}♻️ Otimizando banco de dados...${NC}"
docker exec e2bot-postgres-dev psql -U postgres -d n8n_db -c "VACUUM FULL ANALYZE execution_entity;"
docker exec e2bot-postgres-dev psql -U postgres -d n8n_db -c "REINDEX TABLE execution_entity;"

# 5. Status após limpeza
echo ""
echo -e "${GREEN}✅ Status após limpeza:${NC}"
docker exec e2bot-postgres-dev psql -U postgres -d n8n_db -c "
SELECT
    'Total de execuções' as metric,
    COUNT(*) as value
FROM execution_entity
UNION ALL
SELECT
    'Tamanho total (MB)' as metric,
    ROUND(pg_total_relation_size('execution_entity')::numeric / 1048576, 2) as value
FROM pg_class
WHERE relname = 'execution_entity';
"

# 6. Configurar variáveis de ambiente para performance
echo ""
echo -e "${YELLOW}⚙️ Aplicando configurações de performance...${NC}"

# Criar arquivo de configuração de performance
cat > /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/docker/.env.performance << 'EOF'
# n8n Performance Configuration
# Adicione estas variáveis ao seu .env.dev

# Desabilitar telemetria e diagnósticos
N8N_DIAGNOSTICS_ENABLED=false
N8N_VERSION_NOTIFICATIONS_ENABLED=false

# Limitar retenção de execuções
EXECUTIONS_DATA_MAX_AGE=24
EXECUTIONS_DATA_PRUNE=true
EXECUTIONS_DATA_SAVE_ON_ERROR=all
EXECUTIONS_DATA_SAVE_ON_SUCCESS=none
EXECUTIONS_DATA_SAVE_ON_PROGRESS=false
EXECUTIONS_DATA_SAVE_MANUAL_EXECUTIONS=false

# Performance
N8N_PAYLOAD_SIZE_MAX=64
DB_LOGGING_ENABLED=false

# Memória Node.js
NODE_OPTIONS="--max-old-space-size=2048"
EOF

echo -e "${GREEN}✅ Configurações salvas em: docker/.env.performance${NC}"
echo ""
echo -e "${YELLOW}📝 Para aplicar as configurações de performance:${NC}"
echo "1. Adicione o conteúdo de docker/.env.performance ao seu docker/.env.dev"
echo "2. Reinicie o n8n: docker-compose -f docker/docker-compose-dev.yml restart n8n"
echo ""
echo -e "${GREEN}✅ Limpeza concluída com sucesso!${NC}"