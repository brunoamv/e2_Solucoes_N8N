#!/bin/bash

# ============================================================================
# Script para diagnosticar e resolver problemas de execuções travadas no n8n
# ============================================================================

echo "🔍 Diagnóstico e Correção de Execuções Travadas no n8n"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variáveis
N8N_CONTAINER="e2bot-n8n-dev"
POSTGRES_CONTAINER="e2bot-postgres-dev"
DB_NAME="n8n_db"
DB_USER="n8n_user"

echo -e "${BLUE}📋 DIAGNÓSTICO IDENTIFICADO:${NC}"
echo ""
echo "   ❌ Execuções sendo canceladas manualmente repetidamente"
echo "   ⚠️  PostHog tentando conectar mas falhando (timeout)"
echo "   ⚠️  Webhooks recebendo erro: 'execution was cancelled manually'"
echo ""

echo -e "${YELLOW}🔧 APLICANDO CORREÇÕES:${NC}"
echo ""

# 1. Desabilitar PostHog (telemetria)
echo "1️⃣ Desabilitando PostHog (telemetria desnecessária)..."
docker exec $N8N_CONTAINER sh -c 'echo "export N8N_DIAGNOSTICS_ENABLED=false" >> ~/.bashrc'
docker exec $N8N_CONTAINER sh -c 'echo "export N8N_DISABLE_TRACKING=true" >> ~/.bashrc'
echo -e "   ${GREEN}✅ PostHog desabilitado${NC}"

# 2. Limpar execuções travadas no banco
echo ""
echo "2️⃣ Limpando execuções travadas no banco de dados..."
docker exec $POSTGRES_CONTAINER psql -U $DB_USER -d $DB_NAME -c "
UPDATE execution_entity
SET status = 'error',
    stopped_at = NOW()
WHERE status IN ('running', 'waiting')
  AND started_at < NOW() - INTERVAL '1 hour';
" 2>/dev/null

CLEANED=$(docker exec $POSTGRES_CONTAINER psql -U $DB_USER -d $DB_NAME -t -c "
SELECT COUNT(*)
FROM execution_entity
WHERE status = 'error'
  AND stopped_at > NOW() - INTERVAL '1 minute';
" 2>/dev/null | xargs)

echo -e "   ${GREEN}✅ $CLEANED execuções limpas${NC}"

# 3. Limpar cache do n8n
echo ""
echo "3️⃣ Limpando cache e dados temporários..."
docker exec $N8N_CONTAINER rm -rf /home/node/.n8n/cache/* 2>/dev/null
echo -e "   ${GREEN}✅ Cache limpo${NC}"

# 4. Reiniciar n8n para aplicar mudanças
echo ""
echo "4️⃣ Reiniciando n8n para aplicar correções..."
docker restart $N8N_CONTAINER
echo -e "   ${GREEN}✅ Container reiniciado${NC}"

# 5. Aguardar n8n inicializar
echo ""
echo "⏳ Aguardando n8n inicializar (15 segundos)..."
sleep 15

# 6. Verificar se n8n está respondendo
echo ""
echo "5️⃣ Verificando se n8n está respondendo..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5678/healthz)

if [ "$RESPONSE" = "200" ]; then
    echo -e "   ${GREEN}✅ n8n está respondendo normalmente${NC}"
else
    echo -e "   ${RED}❌ n8n ainda não está respondendo (HTTP $RESPONSE)${NC}"
    echo "   Aguarde mais alguns segundos ou verifique os logs"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✅ CORREÇÕES APLICADAS!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${BLUE}📝 O QUE FOI FEITO:${NC}"
echo ""
echo "   1. PostHog desabilitado (evita timeouts)"
echo "   2. Execuções travadas marcadas como erro"
echo "   3. Cache do n8n limpo"
echo "   4. Container reiniciado"
echo ""
echo -e "${YELLOW}⚠️  RECOMENDAÇÕES:${NC}"
echo ""
echo "   • Acesse http://localhost:5678/executions"
echo "   • Delete execuções antigas com erro"
echo "   • Ative apenas os workflows necessários"
echo "   • Evite múltiplas execuções simultâneas do mesmo webhook"
echo ""
echo -e "${BLUE}🔍 PARA MONITORAR:${NC}"
echo ""
echo "   docker logs -f $N8N_CONTAINER 2>&1 | grep -v PostHog"
echo ""
echo -e "${GREEN}💡 DICA:${NC} Se continuar travando, verifique:"
echo "   • Workflows com loops infinitos"
echo "   • Nodes com timeout muito alto"
echo "   • Webhooks duplicados"
echo ""