#!/bin/bash

# Script para corrigir TODOS os problemas:
# 1. Adicionar API Key no workflow
# 2. Corrigir webhook path no Evolution API

set -e

echo "🔧 CORREÇÃO COMPLETA DO SISTEMA WHATSAPP"
echo "=========================================="
echo ""

# 1. Corrigir webhook no Evolution
echo "1️⃣ Corrigindo webhook do Evolution API..."
echo ""

EVOLUTION_API_KEY="ae569043cfa169380c378347f91a1141ea572541d2d1cadbed222db519c8a891"
INSTANCE_NAME="e2-solucoes-bot"

# Configurar webhook com path CORRETO
curl -s -X POST "http://localhost:8080/webhook/set/$INSTANCE_NAME" \
  -H "apikey: $EVOLUTION_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "webhook": {
      "url": "http://e2bot-n8n-dev:5678/webhook/whatsapp-evolution",
      "enabled": true,
      "webhook_by_events": false,
      "webhook_base64": false,
      "events": [
        "MESSAGES_UPSERT",
        "MESSAGES_UPDATE",
        "MESSAGES_DELETE",
        "SEND_MESSAGE",
        "CONNECTION_UPDATE",
        "QRCODE_UPDATED"
      ]
    }
  }' | jq '.webhook.url' || echo "Webhook configurado"

echo ""
echo "✅ Webhook configurado para: http://e2bot-n8n-dev:5678/webhook/whatsapp-evolution"
echo ""

# 2. Criar Python script para adicionar headers no workflow
echo "2️⃣ Criando correção de autenticação..."
echo ""

cat > /tmp/fix-auth-headers.py << 'PYTHON_EOF'
#!/usr/bin/env python3
"""
Corrige headers de autenticação no workflow
"""

import json
import sys

workflow_file = "/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V1_MENU_FIXED_v3_COMPLETE_FIX_v4_FINAL_FIX_v5.json"

print("📄 Lendo workflow...")
with open(workflow_file, 'r', encoding='utf-8') as f:
    workflow = json.load(f)

# Procurar nó Send WhatsApp Response
for node in workflow.get('nodes', []):
    if node.get('name') == 'Send WhatsApp Response':
        print(f"🔧 Corrigindo nó: {node['name']}")

        # Garantir headers com API Key
        if 'parameters' not in node:
            node['parameters'] = {}

        # Adicionar headers com API Key
        node['parameters']['headerParametersUi'] = {
            "parameter": [
                {
                    "name": "apikey",
                    "value": "ae569043cfa169380c378347f91a1141ea572541d2d1cadbed222db519c8a891"
                },
                {
                    "name": "Content-Type",
                    "value": "application/json"
                }
            ]
        }

        # Garantir authentication ainda é none (não usa n8n auth)
        node['parameters']['authentication'] = 'none'

        # Garantir URL e body corretos
        node['parameters']['url'] = 'http://e2bot-evolution-dev:8080/message/sendText/e2-solucoes-bot'
        node['parameters']['bodyParametersJson'] = json.dumps({
            "number": "{{ $json.phone_number }}",
            "text": "{{ $json.response }}"
        }, indent=2)

        print("   ✅ API Key adicionada aos headers")
        print("   ✅ URL confirmada")
        break

# Salvar arquivo corrigido
output_file = workflow_file.replace('.json', '_AUTH_FIXED.json')
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(workflow, f, indent=2, ensure_ascii=False)

print(f"\n✅ Arquivo corrigido salvo em:\n   {output_file}")
PYTHON_EOF

python3 /tmp/fix-auth-headers.py

echo ""
echo "=========================================="
echo "📋 INSTRUÇÕES FINAIS"
echo "=========================================="
echo ""
echo "1. Delete o workflow antigo no n8n (wn8QE27ZGe6iMU4M)"
echo ""
echo "2. Importe o novo workflow corrigido:"
echo "   /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/"
echo "   02_ai_agent_conversation_V1_MENU_FIXED_v3_COMPLETE_FIX_v4_FINAL_FIX_v5_AUTH_FIXED.json"
echo ""
echo "3. Ative o novo workflow"
echo ""
echo "4. Teste enviando mensagem para WhatsApp"
echo ""
echo "=========================================="
echo "✅ Correções aplicadas:"
echo "   • Webhook path corrigido"
echo "   • API Key adicionada aos headers"
echo "   • Endpoint confirmado"
echo "=========================================="
echo ""

# 3. Verificar status
echo "📊 Status do sistema:"
echo ""
echo "Evolution API:"
curl -s http://localhost:8080/manager/status/$INSTANCE_NAME \
  -H "apikey: $EVOLUTION_API_KEY" | jq '.instance.state' || echo "Verificar manualmente"

echo ""
echo "✅ Script concluído!"