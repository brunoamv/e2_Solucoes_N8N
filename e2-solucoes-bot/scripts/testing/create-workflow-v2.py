#!/usr/bin/env python3
"""
Criação do Workflow V2 - Versão DEFINITIVA
Corrige todos os problemas identificados:
1. Método HTTP GET → POST
2. Variáveis não sendo substituídas
3. Headers com API Key
4. Estrutura JSON correta
"""

import json
from pathlib import Path

def create_workflow_v2():
    """Cria o workflow V2 com todas as correções definitivas"""

    workflow = {
        "name": "02 - AI Agent Conversation V2",
        "nodes": [],
        "connections": {},
        "active": False,
        "settings": {},
        "versionId": "v2-definitive-fix",
        "id": "2",
        "meta": {
            "instanceId": "e2-solucoes-bot"
        },
        "tags": [
            {
                "name": "v2",
                "createdAt": "2026-01-08T00:00:00.000Z",
                "updatedAt": "2026-01-08T00:00:00.000Z",
                "id": "1"
            }
        ]
    }

    # 1. Execute Workflow Trigger
    workflow['nodes'].append({
        "parameters": {"options": {}},
        "id": "trigger",
        "name": "Execute Workflow Trigger",
        "type": "n8n-nodes-base.executeWorkflowTrigger",
        "typeVersion": 1,
        "position": [250, 300]
    })

    # 2. Validate Input
    workflow['nodes'].append({
        "parameters": {
            "jsCode": """// Validar entrada do Workflow 01
const inputData = $input.first().json;

// Validação crítica
if (!inputData.phone_number) {
    throw new Error('phone_number is required');
}

// Limpar phone_number
let phone_number = String(inputData.phone_number).replace(/[^0-9]/g, '');

// Adicionar 55 se necessário
if (phone_number && !phone_number.startsWith('55')) {
    phone_number = '55' + phone_number;
}

console.log('Validated:', {
    phone_number: phone_number,
    message: inputData.message
});

return {
    phone_number: phone_number,
    message: inputData.message || '',
    whatsapp_name: inputData.whatsapp_name || '',
    message_type: inputData.message_type || 'text',
    timestamp: new Date().toISOString()
};"""
        },
        "id": "validate",
        "name": "Validate Input",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [450, 300]
    })

    # 3. Get Conversation
    workflow['nodes'].append({
        "parameters": {
            "operation": "executeQuery",
            "query": "SELECT * FROM conversations WHERE phone_number = '{{ $json.phone_number }}' ORDER BY updated_at DESC LIMIT 1;",
            "options": {}
        },
        "id": "get_conversation",
        "name": "Get Conversation",
        "type": "n8n-nodes-base.postgres",
        "typeVersion": 2.5,
        "position": [650, 300],
        "credentials": {
            "postgres": {
                "id": "1",
                "name": "PostgreSQL E2"
            }
        }
    })

    # 4. Check New User
    workflow['nodes'].append({
        "parameters": {
            "conditions": {
                "number": [
                    {
                        "value1": "={{ $json.length }}",
                        "operation": "equal",
                        "value2": 0
                    }
                ]
            }
        },
        "id": "check_new",
        "name": "Check New User",
        "type": "n8n-nodes-base.if",
        "typeVersion": 1,
        "position": [850, 300]
    })

    # 5. Create Conversation
    workflow['nodes'].append({
        "parameters": {
            "operation": "executeQuery",
            "query": """INSERT INTO conversations (phone_number, whatsapp_name, current_state, created_at, updated_at)
VALUES ('{{ $node["Validate Input"].json.phone_number }}', '{{ $node["Validate Input"].json.whatsapp_name }}', 'greeting', NOW(), NOW())
ON CONFLICT (phone_number) DO UPDATE SET updated_at = NOW()
RETURNING *;""",
            "options": {}
        },
        "id": "create_conversation",
        "name": "Create Conversation",
        "type": "n8n-nodes-base.postgres",
        "typeVersion": 2.5,
        "position": [1050, 200],
        "credentials": {
            "postgres": {
                "id": "1",
                "name": "PostgreSQL E2"
            }
        }
    })

    # 6. Simple State Machine
    workflow['nodes'].append({
        "parameters": {
            "jsCode": """// Simple State Machine for testing
const phone_number = $node["Validate Input"].json.phone_number;
const message = $node["Validate Input"].json.message || '';
const conversation = $input.first().json;
const currentState = conversation.current_state || 'greeting';

let response = '';
let nextState = currentState;

// Simple logic for testing
if (currentState === 'greeting') {
    response = '🤖 Olá! Bem-vindo à E2 Soluções!\\n\\nEscolha o serviço:\\n1 - Energia Solar\\n2 - Subestação\\n3 - Projetos Elétricos';
    nextState = 'service_selection';
} else if (currentState === 'service_selection') {
    if (message === '1' || message === '2' || message === '3') {
        response = '✅ Serviço selecionado! Qual seu nome completo?';
        nextState = 'collect_name';
    } else {
        response = '❌ Por favor, escolha 1, 2 ou 3';
    }
} else {
    response = 'Digite NOVO para recomeçar';
    nextState = 'greeting';
}

return {
    phone_number: phone_number,
    response: response,
    nextState: nextState,
    currentState: currentState
};"""
        },
        "id": "state_machine",
        "name": "State Machine",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [1250, 300]
    })

    # 7. Update Database
    workflow['nodes'].append({
        "parameters": {
            "operation": "executeQuery",
            "query": """UPDATE conversations
SET current_state = '{{ $json.nextState }}', updated_at = NOW()
WHERE phone_number = '{{ $json.phone_number }}'
RETURNING *;""",
            "options": {}
        },
        "id": "update_db",
        "name": "Update Database",
        "type": "n8n-nodes-base.postgres",
        "typeVersion": 2.5,
        "position": [1450, 300],
        "alwaysOutputData": True,
        "credentials": {
            "postgres": {
                "id": "1",
                "name": "PostgreSQL E2"
            }
        }
    })

    # 8. Send WhatsApp - CORREÇÃO DEFINITIVA
    workflow['nodes'].append({
        "parameters": {
            "method": "POST",  # CRÍTICO: Método POST
            "url": "http://e2bot-evolution-dev:8080/message/sendText/e2-solucoes-bot",
            "authentication": "genericCredentialType",
            "genericAuthType": "httpHeaderAuth",
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
                        "value": "={{ $node[\"State Machine\"].json[\"phone_number\"] }}"
                    },
                    {
                        "name": "text",
                        "value": "={{ $node[\"State Machine\"].json[\"response\"] }}"
                    }
                ]
            },
            "options": {}
        },
        "id": "send_whatsapp",
        "name": "Send WhatsApp",
        "type": "n8n-nodes-base.httpRequest",
        "typeVersion": 3,  # Versão 3 do HTTP Request
        "position": [1650, 300]
    })

    # Connections
    workflow['connections'] = {
        "Execute Workflow Trigger": {
            "main": [[{"node": "Validate Input", "type": "main", "index": 0}]]
        },
        "Validate Input": {
            "main": [[{"node": "Get Conversation", "type": "main", "index": 0}]]
        },
        "Get Conversation": {
            "main": [[{"node": "Check New User", "type": "main", "index": 0}]]
        },
        "Check New User": {
            "main": [
                [{"node": "Create Conversation", "type": "main", "index": 0}],
                [{"node": "State Machine", "type": "main", "index": 0}]
            ]
        },
        "Create Conversation": {
            "main": [[{"node": "State Machine", "type": "main", "index": 0}]]
        },
        "State Machine": {
            "main": [[{"node": "Update Database", "type": "main", "index": 0}]]
        },
        "Update Database": {
            "main": [[{"node": "Send WhatsApp", "type": "main", "index": 0}]]
        }
    }

    # Salvar workflow
    output_path = "/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V2.json"

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print("✅ Workflow V2 criado com sucesso!")
    print(f"📄 Arquivo: {output_path}")

    return output_path

def main():
    print("🚀 CRIANDO WORKFLOW V2 DEFINITIVO")
    print("=" * 60)
    print("Correções aplicadas:")
    print("1. ✅ Método HTTP: POST (não GET)")
    print("2. ✅ Headers com API Key configurados")
    print("3. ✅ Variáveis referenciando nós anteriores")
    print("4. ✅ Estrutura simplificada para teste")
    print("=" * 60)

    output = create_workflow_v2()

    print("\n📋 INSTRUÇÕES:")
    print("1. Delete TODOS os workflows antigos no n8n")
    print("2. Importe o novo workflow V2")
    print("3. Verifique o nó 'Send WhatsApp':")
    print("   - Método deve ser POST")
    print("   - Headers deve ter apikey")
    print("   - Body deve referenciar State Machine")
    print("4. Ative o workflow")
    print("5. Teste enviando mensagem")
    print("=" * 60)

if __name__ == "__main__":
    main()