#!/bin/bash

# Script para importar workflow corrigido no n8n
# Problema: Workflow antigo usa endpoint incorreto /message/send/text
# Solução: Importar workflow com endpoint correto /message/sendText/e2-solucoes-bot

set -e

WORKFLOW_FILE="/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V1_MENU_FIXED_v3_COMPLETE_FIX_v4_FINAL_FIX_v5.json"
N8N_URL="http://localhost:5678"

echo "🔧 IMPORTAÇÃO DO WORKFLOW CORRIGIDO"
echo "===================================="
echo ""

# Verificar se o arquivo existe
if [ ! -f "$WORKFLOW_FILE" ]; then
    echo "❌ Arquivo não encontrado! Gerando..."
    python3 /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/scripts/fix-workflow-final-v5.py
fi

# Verificar endpoint correto
echo "📋 Verificando configuração:"
echo "   Arquivo: $(basename $WORKFLOW_FILE)"
echo ""

ENDPOINT=$(jq -r '.nodes[] | select(.name == "Send WhatsApp Response") | .parameters.url' "$WORKFLOW_FILE" 2>/dev/null || echo "")
BODY=$(jq -r '.nodes[] | select(.name == "Send WhatsApp Response") | .parameters.bodyParametersJson' "$WORKFLOW_FILE" 2>/dev/null || echo "")

echo "✅ Endpoint configurado:"
echo "   $ENDPOINT"
echo ""
echo "✅ Body format:"
echo "$BODY" | head -5
echo ""

# Instruções para importação manual
echo "📤 INSTRUÇÕES DE IMPORTAÇÃO:"
echo "============================"
echo ""
echo "1️⃣  Acesse n8n: http://localhost:5678"
echo ""
echo "2️⃣  DESATIVE workflows antigos:"
echo "   • Procure workflows com nome 'AI Agent' ou 'Workflow 02'"
echo "   • Desative TODOS antes de importar o novo"
echo ""
echo "3️⃣  Importe o novo workflow:"
echo "   • Clique no menu ☰"
echo "   • Selecione 'Workflows'"
echo "   • Clique em 'Import from File'"
echo "   • Navegue até:"
echo "     $WORKFLOW_FILE"
echo ""
echo "4️⃣  Configure o novo workflow:"
echo "   • Após importar, abra o workflow"
echo "   • Verifique o nó 'Send WhatsApp Response'"
echo "   • Confirme URL: http://e2bot-evolution-dev:8080/message/sendText/e2-solucoes-bot"
echo ""
echo "5️⃣  ATIVE o workflow:"
echo "   • Clique no toggle para ativar"
echo "   • Verifique se está 'Active'"
echo ""
echo "============================================"
echo "⚠️  IMPORTANTE: Apenas UM workflow deve estar"
echo "   ativo por vez para evitar conflitos!"
echo "============================================"
echo ""

# Mostrar comando de teste
echo "🧪 TESTE APÓS IMPORTAÇÃO:"
echo "========================"
echo ""
echo "Execute o teste com:"
echo "  ./scripts/test-v1-menu.sh"
echo ""
echo "Ou envie mensagem manual para: 556299175548"
echo ""
echo "✅ Script concluído!"