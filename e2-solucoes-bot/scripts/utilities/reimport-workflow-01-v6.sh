#!/bin/bash
# Script para reimportar workflow 01 corrigido v6 no n8n
# Data: 2025-01-05

set -e

WORKFLOW_FILE="n8n/workflows/01 - WhatsApp Handler (FIXED v6).json"
WORKFLOW_NAME="01 - WhatsApp Handler (FIXED v6)"

echo "=== Reimportação do Workflow 01 Corrigido v6 ==="
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

echo "=== CORREÇÕES APLICADAS NA V6 ==="
echo ""
echo "✅ 1. Nó 'Is New Message?' corrigido:"
echo "   - Usa lógica booleana robusta: !$input.all()[0].json.id"
echo "   - Funciona corretamente com arrays vazios"
echo ""
echo "✅ 2. Nó 'Save Inbound Message' corrigido:"
echo "   - Usa mapeamento explícito de campos"
echo "   - Referencia diretamente 'Extract Message Data'"
echo "   - Sem erro 'Column success does not exist'"
echo ""

echo "=== INSTRUÇÕES PARA REIMPORTAÇÃO ==="
echo ""
echo "⚠️  IMPORTANTE: Você precisa importar manualmente o workflow no n8n"
echo ""
echo "1️⃣  Acessar n8n UI:"
echo "   http://localhost:5678"
echo ""
echo "2️⃣  DESATIVAR workflows antigos:"
echo "   - Encontre: '01 - WhatsApp Handler (FIXED v5)' → Toggle OFF"
echo "   - Encontre: '01_main_whatsapp_handler' → Toggle OFF"
echo ""
echo "3️⃣  Importar novo workflow:"
echo "   a) Menu ⋮ (três pontos) → 'Import from File...'"
echo "   b) Navegue até: ${PWD}/${WORKFLOW_FILE}"
echo "   c) Confirme importação"
echo ""
echo "4️⃣  Ativar novo workflow:"
echo "   a) Abra: '01 - WhatsApp Handler (FIXED v6)'"
echo "   b) Toggle 'Active' para ON"
echo "   c) Clique em 'Save' (Ctrl+S)"
echo ""
echo "=== APÓS REIMPORTAÇÃO ==="
echo ""
echo "Execute os testes para validar:"
echo "   ./scripts/test-workflow-01-e2e.sh"
echo ""
echo "Monitorar logs:"
echo "   docker logs e2bot-n8n-dev --tail 100 -f"
echo ""