#!/bin/bash

# Script para corrigir o endpoint de envio de mensagens da Evolution API
# Resolve o erro: "Cannot GET /message/sendText/e2-solucoes-bot"
# Corrige para o endpoint correto da v2.3.7: /message/send/text

echo "🔧 Correção do Endpoint de Envio - Evolution API v2.3.7"
echo "======================================================="
echo ""

# O problema está no Workflow 02 - nó "Send WhatsApp Response"
# A URL está como: http://e2bot-evolution-dev:8080/message/sendText/e2-solucoes-bot
# Deveria ser: http://e2bot-evolution-dev:8080/message/send/text

echo "📌 O erro está no Workflow 02 - nó 'Send WhatsApp Response'"
echo ""
echo "❌ URL ATUAL (incorreta):"
echo "   http://e2bot-evolution-dev:8080/message/sendText/e2-solucoes-bot"
echo ""
echo "✅ URL CORRETA (v2.3.7):"
echo "   http://e2bot-evolution-dev:8080/message/send/text"
echo ""
echo "📝 INSTRUÇÕES PARA CORRIGIR:"
echo ""
echo "1. Acesse o n8n: http://localhost:5678"
echo ""
echo "2. Abra o Workflow: '02 - AI Agent Conversation'"
echo ""
echo "3. Encontre o nó: 'Send WhatsApp Response' (HTTP Request)"
echo ""
echo "4. Altere a URL de:"
echo "   http://e2bot-evolution-dev:8080/message/sendText/e2-solucoes-bot"
echo ""
echo "5. Para:"
echo "   http://e2bot-evolution-dev:8080/message/send/text"
echo ""
echo "6. Altere o método de GET para POST"
echo ""
echo "7. Configure o Body (JSON) com:"
echo '   {'
echo '     "instance": "e2-solucoes-bot",'
echo '     "to": "{{ $json.phone_number }}",'
echo '     "text": "{{ $json.response }}"'
echo '   }'
echo ""
echo "8. Salve o workflow"
echo ""
echo "=============================================="
echo "⚠️ IMPORTANTE: Esta correção deve ser feita manualmente no n8n"
echo "=============================================="
echo ""
echo "Para testar após a correção:"
echo "• Envie uma mensagem para o bot no WhatsApp"
echo "• Verifique se a resposta é enviada corretamente"
echo ""