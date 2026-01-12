#!/usr/bin/env python3
"""
Criação de workflow ultra-simples para teste direto
Versão compatível com n8n
"""

import json

def create_simple_test():
    """Cria workflow de teste simplificado"""

    workflow = {
        "name": "Simple WhatsApp Test",
        "nodes": [
            {
                "parameters": {},
                "id": "uuid-1",
                "name": "Manual",
                "type": "n8n-nodes-base.manualTrigger",
                "typeVersion": 1,
                "position": [250, 300]
            },
            {
                "parameters": {
                    "authentication": "genericCredentialType",
                    "genericAuthType": "httpHeaderAuth",
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
                    "contentType": "json",
                    "bodyParameters": {
                        "parameters": [
                            {
                                "name": "number",
                                "value": "5561981755748"
                            },
                            {
                                "name": "text",
                                "value": "✅ TESTE FUNCIONOU! Mensagem enviada com sucesso!"
                            }
                        ]
                    }
                },
                "id": "uuid-2",
                "name": "Send Test",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 3,
                "position": [450, 300]
            }
        ],
        "connections": {
            "Manual": {
                "main": [[{"node": "Send Test", "type": "main", "index": 0}]]
            }
        },
        "active": False,
        "settings": {},
        "versionId": "test-simple",
        "id": "test",
        "meta": {
            "instanceId": "e2-solucoes-bot"
        },
        "tags": []
    }

    # Salvar
    output_path = "/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/simple_test.json"

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print("✅ Workflow criado com sucesso!")
    print(f"📄 Arquivo: {output_path}")
    print(f"📱 Número: 5561981755748")
    print("\n📋 INSTRUÇÕES:")
    print("1. Importe o arquivo 'simple_test.json' no n8n")
    print("2. Abra o workflow 'Simple WhatsApp Test'")
    print("3. Clique em 'Execute Workflow'")
    print("4. Verifique o WhatsApp")

    return output_path

if __name__ == "__main__":
    create_simple_test()