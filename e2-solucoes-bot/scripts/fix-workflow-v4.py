#!/usr/bin/env python3
"""
Fix workflow V4 - Aplica a solução funcionando ao workflow completo
"""

import json

# Ler o workflow v4 atual
with open('/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V1_MENU_FIXED_v4.json', 'r') as f:
    workflow = json.load(f)

# Encontrar o nó Send WhatsApp Response
for node in workflow['nodes']:
    if node['id'] == 'node_send_whatsapp':
        print(f"Corrigindo nó: {node['name']}")

        # Substituir COMPLETAMENTE com a configuração que funciona
        node['parameters'] = {
            "method": "POST",
            "url": "http://e2bot-evolution-dev:8080/message/sendText/e2-solucoes-bot",
            "sendHeaders": True,
            "headerParameters": {
                "parameters": [
                    {
                        "name": "apikey",
                        "value": "ae569043cfa169380c378347f91a1141ea572541d2d1cadbed222db519c8a891"
                    },
                    {
                        "name": "Content-Type",
                        "value": "application/json"
                    }
                ]
            },
            "sendBody": True,
            "bodyParameters": {
                "parameters": [
                    {
                        "name": "number",
                        "value": "={{ $node[\"Prepare Update Data\"].json[\"phone_number\"] }}"
                    },
                    {
                        "name": "text",
                        "value": "={{ $node[\"State Machine Logic\"].json[\"response_text\"] }}"
                    }
                ]
            },
            "options": {}
        }

        # Atualizar versão do node para v3
        node['typeVersion'] = 3

        # Remover credenciais que causam problema
        if 'credentials' in node:
            del node['credentials']

# Atualizar nome e versionId
workflow['name'] = "02 - AI Agent Conversation V4 (Working)"
workflow['versionId'] = "v4-working-solution"

# Salvar novo workflow
output_path = '/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V4.json'
with open(output_path, 'w') as f:
    json.dump(workflow, f, indent=2, ensure_ascii=False)

print("✅ Workflow V4 corrigido e salvo!")
print(f"📄 Arquivo: {output_path}")
print("\nMudanças aplicadas:")
print("1. ✅ Removida autenticação genérica que causava erro")
print("2. ✅ Método POST configurado corretamente")
print("3. ✅ Headers simples sem configurações extras")
print("4. ✅ HTTP Request v3 (atualizado de v1)")
print("5. ✅ Referências corretas aos campos phone_number e response_text")