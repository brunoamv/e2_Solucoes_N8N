#!/bin/bash
# ============================================================================
# Reimport Workflow 01 to n8n
# ============================================================================
# ATENÇÃO: Este script apenas prepara o workflow modificado.
# VOCÊ DEVE reimportar manualmente no n8n:
# 1. Abrir http://localhost:5678
# 2. Abrir workflow "01 - WhatsApp Handler (FIXED v3)"
# 3. Clicar em "⚙️" (Settings) → "Import from File"
# 4. Selecionar: /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/01_main_whatsapp_handler.json
# 5. Clicar "Save" e "Activate"
# ============================================================================

echo "📋 Workflow 01 modificado está pronto para reimport"
echo ""
echo "📂 Arquivo: /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/01_main_whatsapp_handler.json"
echo ""
echo "🔧 Modificação aplicada: Filtro DESABILITADO (sempre passa)"
echo "   ANTES: value1 = {{ \$json.body.event }}, operation = equal, value2 = messages.upsert"
echo "   AGORA: value1 = true, operation = equal, value2 = true"
echo ""
echo "⚠️  IMPORTANTE: Este filtro permite TODOS os webhooks passarem (inclusive heartbeats)"
echo "   Use apenas para DEBUG - depois devemos restaurar o filtro correto"
echo ""
echo "📝 PRÓXIMOS PASSOS:"
echo "   1. Abrir http://localhost:5678 no navegador"
echo "   2. Workflow '01 - WhatsApp Handler (FIXED v3)'"
echo "   3. ⚙️ Settings → Import from File"
echo "   4. Selecionar o arquivo JSON"
echo "   5. Salvar e Ativar"
echo "   6. Enviar 'oi' do WhatsApp"
echo "   7. Ver execução em http://localhost:5678/home/executions"
echo ""
echo "✅ Pronto para reimport manual!"
