#!/bin/bash
# Script para validar credencial PostgreSQL no n8n
# Testa conexão usando workflow manual

set -e

N8N_URL="http://localhost:5678"
WORKFLOW_ID="Xd7D60MVRs8M9nQS"  # ID do workflow 01 - WhatsApp Handler (FIXED v5)

echo "=== Testando Credencial PostgreSQL no n8n ==="
echo ""
echo "1. Verificando se n8n está acessível..."
if curl -f -s "${N8N_URL}/healthz" > /dev/null 2>&1; then
  echo "✅ n8n está rodando"
else
  echo "❌ n8n não está acessível"
  exit 1
fi

echo ""
echo "2. Verificando workflow ativo..."
WORKFLOW_STATUS=$(curl -s "${N8N_URL}/api/v1/workflows/${WORKFLOW_ID}" 2>/dev/null | grep -o '"active":[^,]*' || echo "")
if [[ "$WORKFLOW_STATUS" == *"true"* ]]; then
  echo "✅ Workflow está ativo"
elif [[ "$WORKFLOW_STATUS" == *"false"* ]]; then
  echo "⚠️  Workflow está inativo (mas configurado)"
else
  echo "⚠️  Não foi possível verificar status do workflow (API pode estar protegida)"
fi

echo ""
echo "3. Testando conexão PostgreSQL direta do container n8n..."
docker exec e2bot-n8n-dev sh -c '
  if command -v psql > /dev/null 2>&1; then
    PGPASSWORD=CoraRosa psql -h postgres-dev -U postgres -d e2_bot -c "SELECT COUNT(*) FROM messages LIMIT 1;" 2>&1
  else
    echo "psql não disponível no container n8n (esperado)"
    echo "Testando conectividade de rede..."
    nc -zv postgres-dev 5432 2>&1 | tail -1
  fi
'

echo ""
echo "4. Credenciais corretas para n8n:"
echo "   Host: postgres-dev (ou e2bot-postgres-dev)"
echo "   Database: e2_bot"
echo "   User: postgres"
echo "   Password: CoraRosa"
echo "   Port: 5432"
echo "   SSL: Disable"

echo ""
echo "=== Próximos Passos ==="
echo "1. Acessar n8n UI: http://localhost:5678"
echo "2. Menu → Credentials → Buscar 'PostgreSQL - E2 Bot'"
echo "3. Verificar/atualizar configurações acima"
echo "4. Clicar em 'Test connection'"
