#!/bin/bash
# Reimportar Workflow 02 - AI Agent Conversation (com correções de schema)

set -e

echo "🔄 Reimportando Workflow 02 - AI Agent Conversation V1 (Menu-Based)"
echo "======================================================================="

WORKFLOW_FILE="n8n/workflows/02_ai_agent_conversation_V1_MENU.json"
N8N_URL="http://localhost:5678"

# Verificar se o arquivo existe
if [ ! -f "$WORKFLOW_FILE" ]; then
    echo "❌ Arquivo não encontrado: $WORKFLOW_FILE"
    exit 1
fi

# Validar JSON
echo "📝 Validando JSON..."
if ! python3 -m json.tool "$WORKFLOW_FILE" > /dev/null 2>&1; then
    echo "❌ JSON inválido!"
    exit 1
fi
echo "✅ JSON válido"

# Verificar se n8n está rodando
echo "🔍 Verificando se n8n está acessível..."
if ! curl -s "$N8N_URL/healthz" > /dev/null 2>&1; then
    echo "❌ n8n não está acessível em $N8N_URL"
    echo "   Execute: ./scripts/start-dev.sh"
    exit 1
fi
echo "✅ n8n acessível"

# Instruções para reimport manual
echo ""
echo "📋 INSTRUÇÕES PARA REIMPORTAR:"
echo "======================================================================="
echo "1. Acesse: http://localhost:5678"
echo "2. Vá em 'Workflows' no menu lateral"
echo "3. Encontre '02 - AI Agent Conversation V1 (Menu-Based)'"
echo "4. Clique nos 3 pontos (...) → 'Delete'"
echo "5. Confirme a exclusão"
echo "6. Clique em '+ Add workflow' ou 'Import from file'"
echo "7. Selecione o arquivo: $WORKFLOW_FILE"
echo "8. Clique em 'Save' para salvar o workflow reimportado"
echo ""
echo "✅ Workflow corrigido com as seguintes alterações:"
echo "   - current_stage → current_state"
echo "   - stage_data → collected_data"
echo "   - lead_id → phone_number"
echo "   - Novo nó: 'Get Conversation Details'"
echo "   - Query COUNT no 'Get Conversation Count'"
echo ""
echo "📁 Arquivo pronto para importação:"
echo "   $(pwd)/$WORKFLOW_FILE"
echo "======================================================================="
