#!/bin/bash

# Corrige a extração do phone_number e refatora para executeQuery
# Data: $(date)

echo "🔧 Corrigindo extração de phone_number e refatorando para executeQuery"
echo "========================================================================="

# Define os caminhos dos arquivos
WORKFLOW_01_ORIGINAL="/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/01 - WhatsApp Handler (ULTIMATE).json"
WORKFLOW_02_ORIGINAL="/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V1_MENU.json"

WORKFLOW_01_FIXED="/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/01 - WhatsApp Handler (ULTIMATE)_FIXED_PHONE_CORRECT.json"
WORKFLOW_02_FIXED="/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V1_MENU_COMPLETE_REFACTOR.json"

# Função para extrair o telefone corretamente do remoteJid
extract_phone_logic() {
    cat <<'EOF'
// Combined extraction and duplicate check to ensure proper flow
const inputData = $input.item.json;

if (!inputData.body || !inputData.body.data) {
  throw new Error('Invalid webhook payload');
}

const data = inputData.body.data;
const message = data.message || {};
const key = data.key || {};

// Função para extrair o número de telefone corretamente
function extractPhoneNumber(remoteJid) {
  if (!remoteJid) return '';

  // Remove @s.whatsapp.net ou @g.us (grupos)
  let cleaned = remoteJid.replace(/@[sg]\.(?:whatsapp\.net|us)$/, '');

  // Se o número tem o formato brasileiro completo (55 + DDD + número)
  // Exemplo: 556198175548 -> 6198175548
  if (cleaned.startsWith('55') && cleaned.length >= 12) {
    // Remove o código do país (55) e mantém DDD + número
    cleaned = cleaned.substring(2);
  }

  // Validação adicional: deve ter entre 10 e 11 dígitos (DDD + número)
  if (!/^\d{10,11}$/.test(cleaned)) {
    console.log('WARNING: Phone number format unexpected:', cleaned);
  }

  return cleaned;
}

// Build output
const output = {
  phone_number: extractPhoneNumber(key.remoteJid),
  whatsapp_name: data.pushName || '',
  message_id: key.id || `gen_${Date.now()}`,
  message_type: 'text',
  content: '',
  media_url: null,
  // Initialize duplicate flag as false
  is_duplicate: false,
  needs_save: true
};

// Log para debug
console.log('RemoteJid original:', key.remoteJid);
console.log('Phone number extraído:', output.phone_number);

// Extract content based on message type
if (message.conversation) {
  output.content = message.conversation;
} else if (message.extendedTextMessage) {
  output.content = message.extendedTextMessage.text || '';
} else if (message.imageMessage) {
  output.message_type = 'image';
  output.media_url = message.imageMessage.url || '';
  output.content = message.imageMessage.caption || '[Imagem]';
} else if (message.audioMessage) {
  output.message_type = 'audio';
  output.content = '[Áudio]';
} else if (message.documentMessage) {
  output.message_type = 'document';
  output.content = message.documentMessage.fileName || '[Documento]';
}

return output;
EOF
}

# Cria o workflow 01 corrigido
echo "📝 Criando workflow 01 com extração correta do phone_number..."
cat > "$WORKFLOW_01_FIXED" <<EOF
{
  "name": "01 - WhatsApp Handler (ULTIMATE) - Phone Fixed",
  "nodes": [
    {
      "parameters": {
        "httpMethod": "POST",
        "path": "whatsapp-evolution",
        "responseMode": "responseNode",
        "options": {}
      },
      "id": "webhook-whatsapp",
      "name": "Webhook WhatsApp",
      "type": "n8n-nodes-base.webhook",
      "typeVersion": 2,
      "position": [-1400, 300],
      "webhookId": "whatsapp-evolution"
    },
    {
      "parameters": {
        "conditions": {
          "options": {
            "caseSensitive": true,
            "leftValue": "",
            "typeValidation": "strict",
            "version": 1
          },
          "conditions": [
            {
              "id": "event-check",
              "leftValue": "={{ \$json.body.event }}",
              "rightValue": "messages.upsert",
              "operator": {
                "type": "string",
                "operation": "equals",
                "singleValue": true
              }
            },
            {
              "id": "from-me-check",
              "leftValue": "={{ \$json.body.data.key.fromMe }}",
              "rightValue": false,
              "operator": {
                "type": "boolean",
                "operation": "false"
              }
            }
          ],
          "combinator": "and"
        },
        "options": {}
      },
      "id": "filter-messages",
      "name": "Filter Messages",
      "type": "n8n-nodes-base.if",
      "typeVersion": 2,
      "position": [-1200, 300]
    },
    {
      "parameters": {
        "jsCode": "$(extract_phone_logic)"
      },
      "id": "extract-data",
      "name": "Extract Message Data",
      "type": "n8n-nodes-base.code",
      "typeVersion": 2,
      "position": [-1000, 200]
    },
    {
      "parameters": {
        "operation": "executeQuery",
        "query": "=SELECT id FROM messages WHERE whatsapp_message_id = '{{ \$json.message_id.replace(/'/g, \"''\") }}' LIMIT 1",
        "options": {
          "queryBatching": "independent"
        }
      },
      "id": "check-duplicate",
      "name": "Check Duplicate",
      "type": "n8n-nodes-base.postgres",
      "typeVersion": 2.5,
      "position": [-800, 200],
      "credentials": {
        "postgres": {
          "id": "VXA1r8sd0TMIdPvS",
          "name": "PostgreSQL - E2 Bot"
        }
      },
      "alwaysOutputData": true
    },
    {
      "parameters": {
        "jsCode": "// Merge duplicate check result with message data\nconst messageData = \$node[\"Extract Message Data\"].json;\nconst queryResult = \$input.all();\n\n// Check if we have a duplicate\nlet isDuplicate = false;\nif (queryResult && queryResult.length > 0) {\n  // Check if the result has an id field\n  const firstResult = queryResult[0];\n  if (firstResult && firstResult.json && firstResult.json.id) {\n    isDuplicate = true;\n  }\n}\n\n// Return merged data with duplicate status\nreturn {\n  ...messageData,\n  is_duplicate: isDuplicate,\n  needs_save: !isDuplicate\n};"
      },
      "id": "merge-results",
      "name": "Merge Results",
      "type": "n8n-nodes-base.code",
      "typeVersion": 2,
      "position": [-600, 200]
    },
    {
      "parameters": {
        "conditions": {
          "options": {
            "caseSensitive": true,
            "leftValue": "",
            "typeValidation": "strict"
          },
          "conditions": [
            {
              "id": "duplicate-check",
              "leftValue": "={{ \$json.is_duplicate }}",
              "rightValue": "={{ true }}",
              "operator": {
                "type": "boolean",
                "operation": "true",
                "singleValue": true
              }
            }
          ],
          "combinator": "and"
        },
        "options": {}
      },
      "id": "is-duplicate",
      "name": "Is Duplicate?",
      "type": "n8n-nodes-base.if",
      "typeVersion": 2,
      "position": [-400, 200]
    },
    {
      "parameters": {
        "operation": "executeQuery",
        "query": "=INSERT INTO messages (conversation_id, direction, content, message_type, media_url, whatsapp_message_id) VALUES (null, 'inbound', '{{ \$json.content.replace(/'/g, \"''\") }}', '{{ \$json.message_type }}', {{ \$json.media_url ? \"'\" + \$json.media_url.replace(/'/g, \"''\") + \"'\" : \"null\" }}, '{{ \$json.message_id.replace(/'/g, \"''\") }}') RETURNING id, created_at",
        "options": {}
      },
      "id": "save-message",
      "name": "Save Message",
      "type": "n8n-nodes-base.postgres",
      "typeVersion": 2.5,
      "position": [-200, 100],
      "credentials": {
        "postgres": {
          "id": "VXA1r8sd0TMIdPvS",
          "name": "PostgreSQL - E2 Bot"
        }
      }
    },
    {
      "parameters": {
        "conditions": {
          "options": {
            "caseSensitive": true,
            "leftValue": "",
            "typeValidation": "strict"
          },
          "conditions": [
            {
              "id": "image-check",
              "leftValue": "={{ \$node[\"Merge Results\"].json.message_type }}",
              "rightValue": "image",
              "operator": {
                "type": "string",
                "operation": "equals",
                "singleValue": true
              }
            }
          ],
          "combinator": "and"
        },
        "options": {}
      },
      "id": "is-image",
      "name": "Is Image?",
      "type": "n8n-nodes-base.if",
      "typeVersion": 2,
      "position": [0, 100]
    },
    {
      "parameters": {
        "jsCode": "// Prepara os dados para passar ao Workflow 02\nconst messageData = \$node[\"Merge Results\"].json;\n\n// Garantir que o phone_number seja passado corretamente\nconst phone_number = messageData.phone_number || '';\n\nif (!phone_number) {\n  throw new Error('Phone number is required but was not extracted correctly');\n}\n\nconsole.log('Passando para Workflow 02:', {\n  phone_number: phone_number,\n  whatsapp_name: messageData.whatsapp_name\n});\n\nreturn {\n  phone_number: phone_number,\n  whatsapp_name: messageData.whatsapp_name || '',\n  message: messageData.content || '',\n  message_type: messageData.message_type || 'text',\n  media_url: messageData.media_url || null,\n  message_id: messageData.message_id || '',\n  timestamp: new Date().toISOString()\n};"
      },
      "id": "prepare-data",
      "name": "Prepare Data for AI Agent",
      "type": "n8n-nodes-base.code",
      "typeVersion": 2,
      "position": [100, 200]
    },
    {
      "parameters": {
        "workflowId": {
          "__rl": true,
          "value": "77olYrOCl5EJeOkX",
          "mode": "id"
        },
        "options": {}
      },
      "id": "trigger-ai",
      "name": "Trigger AI Agent",
      "type": "n8n-nodes-base.executeWorkflow",
      "typeVersion": 1.1,
      "position": [200, 200]
    },
    {
      "parameters": {
        "workflowId": {
          "__rl": true,
          "value": "4",
          "mode": "id"
        },
        "options": {}
      },
      "id": "trigger-image-analysis",
      "name": "Trigger Image Analysis",
      "type": "n8n-nodes-base.executeWorkflow",
      "typeVersion": 1.1,
      "position": [200, 0]
    },
    {
      "parameters": {
        "respondWith": "allIncomingItems",
        "options": {}
      },
      "id": "webhook-response-success",
      "name": "Webhook Response Success",
      "type": "n8n-nodes-base.respondToWebhook",
      "typeVersion": 1.1,
      "position": [400, 100]
    },
    {
      "parameters": {
        "respondWith": "json",
        "responseBody": "={{ { \"status\": \"duplicate\", \"message\": \"Message already processed\" } }}",
        "options": {}
      },
      "id": "webhook-response-duplicate",
      "name": "Webhook Response Duplicate",
      "type": "n8n-nodes-base.respondToWebhook",
      "typeVersion": 1.1,
      "position": [-200, 400]
    },
    {
      "parameters": {
        "respondWith": "json",
        "responseBody": "={{ { \"status\": \"ignored\", \"message\": \"Not a user message\" } }}",
        "options": {}
      },
      "id": "webhook-response-ignored",
      "name": "Webhook Response Ignored",
      "type": "n8n-nodes-base.respondToWebhook",
      "typeVersion": 1.1,
      "position": [-1200, 500]
    }
  ],
  "pinData": {},
  "connections": {
    "Webhook WhatsApp": {
      "main": [
        [{
          "node": "Filter Messages",
          "type": "main",
          "index": 0
        }]
      ]
    },
    "Filter Messages": {
      "main": [
        [{
          "node": "Extract Message Data",
          "type": "main",
          "index": 0
        }],
        [{
          "node": "Webhook Response Ignored",
          "type": "main",
          "index": 0
        }]
      ]
    },
    "Extract Message Data": {
      "main": [
        [{
          "node": "Check Duplicate",
          "type": "main",
          "index": 0
        }]
      ]
    },
    "Check Duplicate": {
      "main": [
        [{
          "node": "Merge Results",
          "type": "main",
          "index": 0
        }]
      ]
    },
    "Merge Results": {
      "main": [
        [{
          "node": "Is Duplicate?",
          "type": "main",
          "index": 0
        }]
      ]
    },
    "Is Duplicate?": {
      "main": [
        [{
          "node": "Webhook Response Duplicate",
          "type": "main",
          "index": 0
        }],
        [{
          "node": "Save Message",
          "type": "main",
          "index": 0
        }]
      ]
    },
    "Save Message": {
      "main": [
        [{
          "node": "Is Image?",
          "type": "main",
          "index": 0
        }]
      ]
    },
    "Is Image?": {
      "main": [
        [{
          "node": "Trigger Image Analysis",
          "type": "main",
          "index": 0
        }],
        [{
          "node": "Prepare Data for AI Agent",
          "type": "main",
          "index": 0
        }]
      ]
    },
    "Prepare Data for AI Agent": {
      "main": [
        [{
          "node": "Trigger AI Agent",
          "type": "main",
          "index": 0
        }]
      ]
    },
    "Trigger AI Agent": {
      "main": [
        [{
          "node": "Webhook Response Success",
          "type": "main",
          "index": 0
        }]
      ]
    },
    "Trigger Image Analysis": {
      "main": [
        [{
          "node": "Prepare Data for AI Agent",
          "type": "main",
          "index": 0
        }]
      ]
    }
  },
  "active": false,
  "settings": {
    "executionOrder": "v1"
  },
  "versionId": "phone-fix-complete",
  "meta": {
    "instanceId": "be7607dc500d0df7a2cb94e774f3665239bf8a65324d98f4d2534280e5bd21e1"
  },
  "id": "workflow-01-phone-fixed",
  "tags": []
}
EOF

echo "✅ Workflow 01 corrigido criado!"

# Agora vamos criar o script para refatorar completamente o workflow 02
echo ""
echo "📝 Criando workflow 02 com refatoração completa para executeQuery..."

# Primeiro vamos ler o workflow 02 original para preservar a estrutura
python3 << 'PYTHON_SCRIPT'
import json
import sys

workflow_02_path = "/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V1_MENU.json"
output_path = "/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V1_MENU_COMPLETE_REFACTOR.json"

try:
    with open(workflow_02_path, 'r') as f:
        workflow = json.load(f)

    print(f"🔍 Analisando workflow 02: {workflow.get('name', 'Unknown')}")

    # Adiciona nó de validação de entrada no início
    validation_node = {
        "parameters": {
            "jsCode": """// Validação de entrada do Workflow 01
const inputData = $input.first().json;

// Validação crítica do phone_number
if (!inputData.phone_number || inputData.phone_number === 'undefined') {
    throw new Error('Phone number is required but was not received from Workflow 01');
}

// Limpar e validar formato do phone_number
let phone_number = String(inputData.phone_number).replace(/[^0-9]/g, '');

// Validação de formato brasileiro (DDD + número)
if (phone_number.length < 10 || phone_number.length > 11) {
    throw new Error(`Invalid phone number format: ${phone_number} (expected 10-11 digits)`);
}

console.log('Validated input:', {
    phone_number: phone_number,
    whatsapp_name: inputData.whatsapp_name,
    message_type: inputData.message_type
});

return {
    phone_number: phone_number,
    whatsapp_name: inputData.whatsapp_name || '',
    message: inputData.message || '',
    message_type: inputData.message_type || 'text',
    media_url: inputData.media_url || null,
    message_id: inputData.message_id || '',
    timestamp: inputData.timestamp || new Date().toISOString()
};"""
        },
        "id": "validate-input",
        "name": "Validate Input Data",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [-1150, 200]
    }

    # Insere o nó de validação no início da lista de nodes
    if 'nodes' not in workflow:
        workflow['nodes'] = []

    # Adiciona o nó de validação
    workflow['nodes'].insert(1, validation_node)  # Insere depois do trigger

    # Mapeia os estados inglês -> português
    state_mapping = {
        'greeting': 'novo',
        'service_selection': 'identificando_servico',
        'collecting_data': 'coletando_dados',
        'awaiting_photo': 'aguardando_foto',
        'scheduling': 'agendando',
        'scheduled': 'agendado',
        'handoff_comercial': 'handoff_comercial',
        'completed': 'concluido'
    }

    # Contador de nós modificados
    nodes_modified = 0

    # Percorre todos os nós e refatora PostgreSQL operations
    for node in workflow.get('nodes', []):
        if node.get('type') == 'n8n-nodes-base.postgres':
            node_name = node.get('name', '')

            # Refatora para executeQuery
            if node['parameters'].get('operation') in ['insert', 'update', 'upsert']:
                original_op = node['parameters'].get('operation')

                # Conversão baseada no tipo de operação
                if 'Create New Conversation' in node_name or 'create' in node_name.lower():
                    # Create/Insert operation
                    node['parameters'] = {
                        "operation": "executeQuery",
                        "query": """INSERT INTO conversations (phone_number, whatsapp_name, current_state, created_at, updated_at)
VALUES ('{{ $json.phone_number }}', '{{ $json.whatsapp_name }}', 'novo', NOW(), NOW())
ON CONFLICT (phone_number)
DO UPDATE SET
  whatsapp_name = EXCLUDED.whatsapp_name,
  updated_at = NOW(),
  current_state = CASE
    WHEN conversations.current_state = 'concluido' THEN 'novo'
    ELSE conversations.current_state
  END
RETURNING *""",
                        "options": {}
                    }
                    print(f"  ✅ Refatorado: {node_name} (insert → executeQuery com ON CONFLICT)")

                elif 'Update Conversation' in node_name or 'update' in node_name.lower():
                    # Update operation - com mapeamento de estados
                    node['parameters'] = {
                        "operation": "executeQuery",
                        "query": """UPDATE conversations
SET current_state = '{{ $json.new_state }}',
    updated_at = NOW()
WHERE phone_number = '{{ $json.phone_number }}'
RETURNING *""",
                        "options": {}
                    }
                    print(f"  ✅ Refatorado: {node_name} (update → executeQuery)")

                elif 'Check Existing' in node_name or 'check' in node_name.lower():
                    # Select/Check operation
                    node['parameters'] = {
                        "operation": "executeQuery",
                        "query": "SELECT * FROM conversations WHERE phone_number = '{{ $json.phone_number }}' LIMIT 1",
                        "options": {}
                    }
                    print(f"  ✅ Refatorado: {node_name} (select → executeQuery)")

                elif 'save' in node_name.lower() and 'message' in node_name.lower():
                    # Save message operation
                    node['parameters'] = {
                        "operation": "executeQuery",
                        "query": """INSERT INTO messages (conversation_id, direction, content, message_type, whatsapp_message_id)
VALUES (
  (SELECT id FROM conversations WHERE phone_number = '{{ $json.phone_number }}' LIMIT 1),
  'inbound',
  '{{ $json.message.replace(/'/g, "''") }}',
  '{{ $json.message_type }}',
  '{{ $json.message_id }}'
) RETURNING *""",
                        "options": {}
                    }
                    print(f"  ✅ Refatorado: {node_name} (message insert → executeQuery)")

                nodes_modified += 1

        # Também procura por Code nodes que possam ter mapeamento de estado
        elif node.get('type') == 'n8n-nodes-base.code':
            if 'jsCode' in node.get('parameters', {}):
                js_code = node['parameters']['jsCode']

                # Procura e substitui estados em inglês
                for eng_state, pt_state in state_mapping.items():
                    if eng_state in js_code:
                        js_code = js_code.replace(f"'{eng_state}'", f"'{pt_state}'")
                        js_code = js_code.replace(f'"{eng_state}"', f'"{pt_state}"')
                        js_code = js_code.replace(f'state === "{eng_state}"', f'state === "{pt_state}"')
                        js_code = js_code.replace(f"state === '{eng_state}'", f"state === '{pt_state}'")
                        print(f"  ✅ Mapeado estado: {eng_state} → {pt_state} em {node.get('name', 'Code node')}")

                node['parameters']['jsCode'] = js_code

    # Atualiza as conexões para incluir o nó de validação
    if 'connections' in workflow:
        # Encontra o nó trigger
        trigger_node = None
        for node in workflow['nodes']:
            if 'trigger' in node.get('type', '').lower() or node.get('id') == 'workflow-trigger':
                trigger_node = node.get('id')
                break

        if trigger_node and trigger_node in workflow['connections']:
            # Redireciona o trigger para o nó de validação
            old_connection = workflow['connections'][trigger_node]
            workflow['connections'][trigger_node] = {
                "main": [[{
                    "node": "Validate Input Data",
                    "type": "main",
                    "index": 0
                }]]
            }

            # Conecta o nó de validação ao próximo nó original
            if old_connection and 'main' in old_connection and old_connection['main']:
                workflow['connections']['Validate Input Data'] = old_connection

    # Atualiza metadados
    workflow['name'] = workflow.get('name', '') + ' - Complete Refactor'
    workflow['versionId'] = 'complete-refactor-executequery'

    # Salva o workflow refatorado
    with open(output_path, 'w') as f:
        json.dump(workflow, f, indent=2)

    print(f"\n✅ Workflow 02 refatorado salvo em: {output_path}")
    print(f"📊 Total de nós PostgreSQL refatorados: {nodes_modified}")

except Exception as e:
    print(f"❌ Erro ao processar workflow: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
PYTHON_SCRIPT

echo ""
echo "🎉 Scripts de correção criados com sucesso!"
echo ""
echo "📋 Arquivos gerados:"
echo "  1. $WORKFLOW_01_FIXED - Workflow 01 com extração correta do phone_number"
echo "  2. $WORKFLOW_02_FIXED - Workflow 02 com refatoração completa para executeQuery"
echo ""
echo "🚀 Próximos passos:"
echo "  1. Importar o Workflow 01 corrigido no n8n"
echo "  2. Importar o Workflow 02 refatorado no n8n"
echo "  3. Testar com uma mensagem real do WhatsApp"
echo ""
echo "📝 O que foi corrigido:"
echo "  ✅ Extração correta do phone_number (remove 55 do início)"
echo "  ✅ Validação do formato brasileiro (10-11 dígitos)"
echo "  ✅ Passagem correta dos dados entre workflows"
echo "  ✅ Refatoração completa para executeQuery"
echo "  ✅ Mapeamento de estados inglês → português"
echo "  ✅ ON CONFLICT handling para duplicatas"

# Torna o script executável
chmod +x "$0"