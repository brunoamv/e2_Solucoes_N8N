#!/usr/bin/env python3
"""
Workflow ultra-simples sem autenticação genérica
"""

import json

def create_ultra_simple():
    """Cria workflow mais simples possível"""

    workflow = {
        "name": "Ultra Simple Test",
        "nodes": [
            {
                "parameters": {},
                "id": "manual-trigger",
                "name": "Manual",
                "type": "n8n-nodes-base.manualTrigger",
                "typeVersion": 1,
                "position": [250, 300]
            },
            {
                "parameters": {
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
                                "value": "5561981755748"
                            },
                            {
                                "name": "text",
                                "value": "🚀 TESTE ULTRA SIMPLES FUNCIONOU!"
                            }
                        ]
                    },
                    "options": {}
                },
                "id": "http-request",
                "name": "Send WhatsApp",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 3,
                "position": [450, 300]
            }
        ],
        "connections": {
            "Manual": {
                "main": [[{"node": "Send WhatsApp", "type": "main", "index": 0}]]
            }
        },
        "active": False,
        "settings": {},
        "versionId": "ultra-simple",
        "id": "ultra",
        "meta": {
            "instanceId": "e2-solucoes-bot"
        },
        "tags": []
    }

    # Salvar
    output_path = "/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/ultra_simple_test.json"

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print("✅ Workflow ULTRA SIMPLES criado!")
    print(f"📄 Arquivo: {output_path}")
    print("\nDiferenças importantes:")
    print("- SEM authentication genericCredentialType")
    print("- SEM genericAuthType")
    print("- Headers diretos e simples")
    print("- HTTP Request v3 padrão")
    print("\n📋 TESTE:")
    print("1. Importe 'ultra_simple_test.json'")
    print("2. Execute o workflow")
    print("3. Verifique WhatsApp 5561981755748")

if __name__ == "__main__":
    create_ultra_simple()