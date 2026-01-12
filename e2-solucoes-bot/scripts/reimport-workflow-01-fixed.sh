#!/bin/bash
# Script para reimportar workflow 01 corrigido no n8n
# Usa volume mount para copiar arquivo e instrui usuário

set -e

WORKFLOW_FILE="n8n/workflows/01 - WhatsApp Handler (FIXED v5).json"
WORKFLOW_NAME="01 - WhatsApp Handler (FIXED v5)"

echo "=== Reimportação do Workflow 01 Corrigido ==="
echo ""
echo "📋 Workflow: ${WORKFLOW_NAME}"
echo "📁 Arquivo: ${WORKFLOW_FILE}"
echo ""

# Verificar se arquivo existe
if [ ! -f "$WORKFLOW_FILE" ]; then
  echo "❌ Arquivo não encontrado: ${WORKFLOW_FILE}"
  exit 1
fi

echo "✅ Arquivo de workflow encontrado"
echo ""

# Verificar se n8n está rodando
if ! curl -f -s http://localhost:5678/healthz > /dev/null 2>&1; then
  echo "❌ n8n não está acessível em http://localhost:5678"
  echo "   Execute: ./scripts/start-dev.sh"
  exit 1
fi

echo "✅ n8n está rodando"
echo ""

# Validar JSON
if ! jq empty "$WORKFLOW_FILE" 2>/dev/null; then
  echo "❌ Arquivo JSON inválido"
  exit 1
fi

echo "✅ JSON válido"
echo ""

# Extrair informações do workflow
WORKFLOW_ID=$(jq -r '.id' "$WORKFLOW_FILE")
NODES_COUNT=$(jq '.nodes | length' "$WORKFLOW_FILE")

echo "📊 Informações do Workflow:"
echo "   ID: ${WORKFLOW_ID}"
echo "   Número de nós: ${NODES_COUNT}"
echo ""

echo "=== INSTRUÇÕES PARA REIMPORTAÇÃO ==="
echo ""
echo "O n8n não possui API pública para atualizar workflows via HTTP."
echo "Para aplicar as correções, siga os passos:"
echo ""
echo "1️⃣  Acessar n8n UI:"
echo "   http://localhost:5678"
echo ""
echo "2️⃣  Localizar workflow:"
echo "   - Na lista de workflows, encontre: '${WORKFLOW_NAME}'"
echo "   - Ou busque por ID: ${WORKFLOW_ID}"
echo ""
echo "3️⃣  Abrir o workflow para edição"
echo ""
echo "4️⃣  Importar versão corrigida:"
echo "   a) Clique no menu ⋮ (três pontos) no canto superior direito"
echo "   b) Selecione 'Import from File...'"
echo "   c) Navegue até: ${PWD}/${WORKFLOW_FILE}"
echo "   d) Confirme a substituição"
echo ""
echo "5️⃣  Salvar e Ativar:"
echo "   a) Clique em 'Save' (Ctrl+S)"
echo "   b) Toggle 'Active' para ON (se estiver OFF)"
echo ""
echo "=== CORREÇÕES APLICADAS NO ARQUIVO ==="
echo ""
echo "✅ 1. Condição vazia removida do nó 'Is New Message?'"
echo "✅ 2. Query SQL com escape seguro de aspas no 'Check Duplicate'"
echo "✅ 3. Validação robusta adicionada ao 'Extract Message Data'"
echo ""
echo "=== APÓS REIMPORTAÇÃO ==="
echo ""
echo "Execute os testes para validar:"
echo "   ./scripts/test-workflow-01-e2e.sh"
echo ""
echo "Ou continue com a Fase 5 do plano de correção."
echo ""
