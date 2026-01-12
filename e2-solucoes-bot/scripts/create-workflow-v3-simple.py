#!/usr/bin/env python3
"""
Workflow V3 - Ultra simplificado para teste direto
Número hardcoded para teste: 5561981755748
"""

import json
from pathlib import Path

def create_workflow_v3():
    """Cria workflow V3 ultra-simplificado"""

    workflow = {
        "name": "02 - Test WhatsApp Send V3",
        "nodes": [],
        "connections": {},
        "active": False,
        "settings": {},
        "versionId": "v3-ultra-simple",
        "id": "2",
        "meta": {
            "instanceId": "e2-solucoes-bot"
        },
        "tags": []
    }

    # 1. Manual Trigger (para teste manual)
    workflow['nodes'].append({
        "parameters": {},
        "id": "manual",
        "name": "Manual Trigger",
        "type": "n8n-nodes-base.manualTrigger",
        "typeVersion": 1,
        "position": [250, 300]
    })

    # 2. Set Data (dados fixos para teste)
    workflow['nodes'].append({
        "parameters": {
            "keepOnlySet": False,
            "values": {
                "values": [
                    {
                        "name": "phone_number",
                        "value": "5561981755748"
                    },
                    {
                        "name": "text",
                        "value": "🤖 Teste V3 - Mensagem enviada com sucesso!"
                    }
                ]
            }
        },
        "id": "set_data",
        "name": "Set Test Data",
        "type": "n8n-nodes-base.set",
        "typeVersion": 1,
        "position": [450, 300]
    })

    # 3. HTTP Request - Formato mais simples possível
    workflow['nodes'].append({
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
            "specifyBody": "json",
            "jsonBody": "={\"number\": \"{{$json[\"phone_number\"]}}\", \"text\": \"{{$json[\"text\"]}}\"}"
        },
        "id": "http",
        "name": "Send WhatsApp",
        "type": "n8n-nodes-base.httpRequest",
        "typeVersion": 4.2,
        "position": [650, 300]
    })

    # Connections
    workflow['connections'] = {
        "Manual Trigger": {
            "main": [[{"node": "Set Test Data", "type": "main", "index": 0}]]
        },
        "Set Test Data": {
            "main": [[{"node": "Send WhatsApp", "type": "main", "index": 0}]]
        }
    }

    # Salvar
    output_path = "/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_test_whatsapp_send_V3.json"

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print("✅ Workflow V3 criado!")
    print(f"📄 Arquivo: {output_path}")
    print(f"📱 Número configurado: 5561981755748")

    return output_path

def main():
    print("🚀 CRIANDO WORKFLOW V3 - TESTE SIMPLES")
    print("=" * 60)
    print("Este workflow:")
    print("1. Usa trigger manual (clique no botão Execute)")
    print("2. Define dados fixos com Set node")
    print("3. Envia via HTTP Request v4.2")
    print("4. Número hardcoded: 5561981755748")
    print("=" * 60)

    output = create_workflow_v3()

    print("\n📋 INSTRUÇÕES DE TESTE:")
    print("1. Importe o workflow no n8n")
    print("2. Abra o workflow")
    print("3. Clique em 'Execute Workflow' (botão no canto)")
    print("4. Verifique se a mensagem chegou no WhatsApp")
    print("\n⚠️  Se funcionar, o problema está na estrutura complexa")
    print("Se falhar, o problema é na configuração do HTTP Request")
    print("=" * 60)

if __name__ == "__main__":
    main()