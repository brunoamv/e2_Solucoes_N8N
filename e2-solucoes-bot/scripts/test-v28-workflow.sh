#!/bin/bash

echo "=== Teste do Workflow V28 - Array Return Fix ==="
echo ""
echo "1. Verificando se o V28 foi criado..."
if [ -f "n8n/workflows/02_ai_agent_conversation_V28_ARRAY_RETURN_FIX.json" ]; then
    echo "✅ Arquivo V28 encontrado"
else
    echo "❌ Arquivo V28 não encontrado"
    exit 1
fi

echo ""
echo "2. Monitorando logs do n8n para mensagens V28..."
echo "   (Aguardando mensagens de debug V28...)"
echo ""
echo "Para testar:"
echo "1. Importe o workflow V28 no n8n"
echo "2. Desative o workflow V27"
echo "3. Ative o workflow V28"
echo "4. Envie mensagem '1' no WhatsApp"
echo ""
echo "Logs V28 (tempo real):"
echo "========================================"
docker logs -f e2bot-n8n-dev 2>&1 | grep -E "(V28|Merge Queries|Code doesn't return|ARRAY)"