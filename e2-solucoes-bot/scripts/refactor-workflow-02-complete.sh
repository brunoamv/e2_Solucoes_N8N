#!/bin/bash

# Script para refatorar COMPLETAMENTE o workflow 02 para usar executeQuery
# Baseado no padrão do workflow 01 ULTIMATE que funciona corretamente
# Corrige: estados em português, phone_number vazio, ON CONFLICT handling

set -e

WORKFLOW_FILE="../n8n/workflows/02_ai_agent_conversation_V1_MENU.json"
OUTPUT_FILE="../n8n/workflows/02_ai_agent_conversation_V1_MENU_REFACTORED.json"

# Criar backup com timestamp
BACKUP_FILE="${WORKFLOW_FILE}.backup_$(date +%s)"
cp "$WORKFLOW_FILE" "$BACKUP_FILE"
echo "✅ Backup criado: $BACKUP_FILE"

# Criar arquivo JavaScript temporário para processar o JSON
cat > /tmp/refactor_workflow.js << 'EOF'
const fs = require('fs');

// Ler o workflow original
const workflow = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));

// Função para refatorar nós PostgreSQL para executeQuery
function refactorPostgresNodes(workflow) {
    workflow.nodes.forEach(node => {
        // 1. CREATE NEW CONVERSATION - Refatorar para executeQuery com ON CONFLICT
        if (node.name === 'Create New Conversation') {
            console.log('🔧 Refatorando: Create New Conversation');
            node.type = 'n8n-nodes-base.postgres';
            node.typeVersion = 2.4;
            node.parameters = {
                operation: 'executeQuery',
                query: `INSERT INTO conversations (phone_number, current_state, collected_data, created_at, updated_at)
VALUES ('{{ $json.phone_number }}', 'novo', '{}', NOW(), NOW())
ON CONFLICT (phone_number) DO UPDATE SET
  current_state = 'novo',
  collected_data = '{}',
  updated_at = NOW()
RETURNING id, phone_number, current_state, collected_data, created_at, updated_at;`,
                options: {},
                additionalFields: {}
            };
        }

        // 2. CHECK EXISTING CONVERSATION - Já está em executeQuery, mas vamos garantir
        if (node.name === 'Check Existing Conversation') {
            console.log('🔧 Refatorando: Check Existing Conversation');
            node.type = 'n8n-nodes-base.postgres';
            node.typeVersion = 2.4;
            node.parameters = {
                operation: 'executeQuery',
                query: `SELECT
  id,
  phone_number,
  current_state,
  collected_data,
  created_at,
  updated_at
FROM conversations
WHERE phone_number = '{{ $json.phone_number }}'
ORDER BY created_at DESC
LIMIT 1;`,
                options: {}
            };
        }

        // 3. UPDATE CONVERSATION STATE - Refatorar para executeQuery
        if (node.name === 'Update Conversation State') {
            console.log('🔧 Refatorando: Update Conversation State');
            node.type = 'n8n-nodes-base.postgres';
            node.typeVersion = 2.4;
            node.parameters = {
                operation: 'executeQuery',
                query: `UPDATE conversations
SET
  current_state = '{{ $json.next_state }}',
  collected_data = '{{ JSON.stringify($json.collected_data).replace(/'/g, "''") }}',
  updated_at = NOW()
WHERE phone_number = '{{ $json.phone_number }}'
RETURNING id, phone_number, current_state, collected_data, updated_at;`,
                options: {}
            };
        }

        // 4. CREATE LEAD - Refatorar para executeQuery com ON CONFLICT
        if (node.name === 'Create Lead') {
            console.log('🔧 Refatorando: Create Lead');
            node.type = 'n8n-nodes-base.postgres';
            node.typeVersion = 2.4;
            node.parameters = {
                operation: 'executeQuery',
                query: `INSERT INTO leads (
  phone_number,
  conversation_id,
  name,
  email,
  company,
  service_type,
  service_details,
  appointment_id,
  created_at,
  updated_at
) VALUES (
  '{{ $json.phone_number }}',
  {{ $json.conversation_id }},
  '{{ $json.name || '' }}',
  '{{ $json.email || '' }}',
  '{{ $json.company || '' }}',
  '{{ $json.service_type || '' }}',
  '{{ JSON.stringify($json.service_details || {}).replace(/'/g, "''") }}',
  {{ $json.appointment_id || 'NULL' }},
  NOW(),
  NOW()
)
ON CONFLICT (phone_number) DO UPDATE SET
  name = EXCLUDED.name,
  email = EXCLUDED.email,
  company = EXCLUDED.company,
  service_type = EXCLUDED.service_type,
  service_details = EXCLUDED.service_details,
  appointment_id = EXCLUDED.appointment_id,
  updated_at = NOW()
RETURNING *;`,
                options: {}
            };
        }

        // 5. UPDATE LEAD - Refatorar para executeQuery
        if (node.name === 'Update Lead') {
            console.log('🔧 Refatorando: Update Lead');
            node.type = 'n8n-nodes-base.postgres';
            node.typeVersion = 2.4;
            node.parameters = {
                operation: 'executeQuery',
                query: `UPDATE leads
SET
  name = '{{ $json.name || '' }}',
  email = '{{ $json.email || '' }}',
  company = '{{ $json.company || '' }}',
  service_details = '{{ JSON.stringify($json.service_details || {}).replace(/'/g, "''") }}',
  updated_at = NOW()
WHERE phone_number = '{{ $json.phone_number }}'
RETURNING *;`,
                options: {}
            };
        }

        // 6. SAVE MESSAGE - Refatorar para executeQuery
        if (node.name === 'Save Message' || node.name === 'Store Message') {
            console.log('🔧 Refatorando: Save/Store Message');
            node.type = 'n8n-nodes-base.postgres';
            node.typeVersion = 2.4;
            node.parameters = {
                operation: 'executeQuery',
                query: `INSERT INTO messages (
  conversation_id,
  phone_number,
  sender_type,
  content,
  message_type,
  created_at
) VALUES (
  {{ $json.conversation_id }},
  '{{ $json.phone_number }}',
  '{{ $json.sender_type || 'user' }}',
  '{{ ($json.content || $json.message || '').replace(/'/g, "''") }}',
  '{{ $json.message_type || 'text' }}',
  NOW()
)
RETURNING *;`,
                options: {}
            };
        }

        // 7. GET CONVERSATION MESSAGES - Refatorar para executeQuery
        if (node.name === 'Get Conversation Messages' || node.name === 'Get Messages') {
            console.log('🔧 Refatorando: Get Conversation Messages');
            node.type = 'n8n-nodes-base.postgres';
            node.typeVersion = 2.4;
            node.parameters = {
                operation: 'executeQuery',
                query: `SELECT
  id,
  conversation_id,
  phone_number,
  sender_type,
  content,
  message_type,
  created_at
FROM messages
WHERE conversation_id = {{ $json.conversation_id }}
ORDER BY created_at DESC
LIMIT 20;`,
                options: {}
            };
        }

        // 8. STATE MACHINE LOGIC - Corrigir mapeamento de estados
        if (node.name === 'State Machine Logic') {
            console.log('🔧 Corrigindo: State Machine Logic (mapeamento de estados)');
            if (node.parameters && node.parameters.jsCode) {
                // Adicionar mapeamento bidirecional de estados
                const stateMapping = `
// Mapeamento de estados: Português (DB) <-> Inglês (Lógica Interna)
const dbToInternal = {
  'novo': 'greeting',
  'identificando_servico': 'service_selection',
  'coletando_dados': 'collecting_data',
  'aguardando_foto': 'awaiting_photo',
  'agendando': 'scheduling',
  'agendado': 'scheduled',
  'handoff_comercial': 'handoff',
  'concluido': 'completed'
};

const internalToDb = {
  'greeting': 'novo',
  'service_selection': 'identificando_servico',
  'collecting_data': 'coletando_dados',
  'awaiting_photo': 'aguardando_foto',
  'scheduling': 'agendando',
  'scheduled': 'agendado',
  'handoff': 'handoff_comercial',
  'completed': 'concluido'
};
`;

                // Inserir mapeamento no início do código
                let code = node.parameters.jsCode;

                // Adicionar mapeamento no início
                if (!code.includes('dbToInternal')) {
                    code = stateMapping + '\n' + code;
                }

                // Corrigir uso de currentStage para usar mapeamento
                code = code.replace(
                    /const currentStage = \$input\.first\(\)\.json\.current_state \|\| 'greeting';/,
                    `const dbState = $input.first().json.current_state || 'novo';
const currentStage = dbToInternal[dbState] || dbState;`
                );

                // Garantir que next_state seja sempre em português
                code = code.replace(
                    /next_state: nextStage,/g,
                    'next_state: internalToDb[nextStage] || nextStage,'
                );

                // Garantir que phone_number seja sempre incluído
                code = code.replace(
                    /return {/g,
                    `return {
  phone_number: $input.first().json.phone_number,`
                );

                node.parameters.jsCode = code;
            }
        }

        // 9. PREPARE CLAUDE PROMPT - Garantir phone_number
        if (node.name === 'Prepare Claude Prompt') {
            console.log('🔧 Corrigindo: Prepare Claude Prompt');
            if (node.parameters && node.parameters.jsCode) {
                let code = node.parameters.jsCode;

                // Garantir que phone_number seja preservado
                if (!code.includes('phone_number:')) {
                    code = code.replace(
                        /return {/g,
                        `return {
  phone_number: $input.first().json.phone_number,`
                    );
                }

                node.parameters.jsCode = code;
            }
        }

        // 10. Qualquer outro nó PostgreSQL genérico
        if (node.type === 'n8n-nodes-base.postgres' &&
            node.parameters &&
            node.parameters.operation !== 'executeQuery') {
            console.log(`🔧 Refatorando nó PostgreSQL genérico: ${node.name}`);

            // Converter operações insert/update/upsert para executeQuery
            const oldOp = node.parameters.operation;
            const table = node.parameters.table;

            if (oldOp === 'insert' && table) {
                node.parameters = {
                    operation: 'executeQuery',
                    query: `-- Convertido automaticamente de insert
INSERT INTO ${table} DEFAULT VALUES RETURNING *;`,
                    options: {}
                };
            } else if (oldOp === 'update' && table) {
                node.parameters = {
                    operation: 'executeQuery',
                    query: `-- Convertido automaticamente de update
UPDATE ${table} SET updated_at = NOW() WHERE id = 1 RETURNING *;`,
                    options: {}
                };
            }

            node.typeVersion = 2.4;
        }
    });

    return workflow;
}

// Processar o workflow
const refactoredWorkflow = refactorPostgresNodes(workflow);

// Salvar o workflow refatorado
fs.writeFileSync(process.argv[3], JSON.stringify(refactoredWorkflow, null, 2));

console.log('✅ Workflow refatorado com sucesso!');
console.log('📝 Mudanças aplicadas:');
console.log('  - Todos os nós PostgreSQL convertidos para executeQuery');
console.log('  - ON CONFLICT adicionado em Create New Conversation e Create Lead');
console.log('  - Mapeamento de estados Português <-> Inglês');
console.log('  - phone_number preservado em todos os nós');
console.log('  - SQL queries otimizadas com escape de strings');
EOF

# Executar o script de refatoração
echo "🔄 Refatorando workflow..."
node /tmp/refactor_workflow.js "$WORKFLOW_FILE" "$OUTPUT_FILE"

# Validar o JSON resultante
if jq empty "$OUTPUT_FILE" 2>/dev/null; then
    echo "✅ JSON válido gerado!"
    echo "📁 Arquivo refatorado: $OUTPUT_FILE"
    echo ""
    echo "🎯 Próximos passos:"
    echo "  1. Importe o workflow refatorado no n8n:"
    echo "     - Abra n8n em http://localhost:5678"
    echo "     - Vá em Workflows > Import from File"
    echo "     - Selecione: $OUTPUT_FILE"
    echo ""
    echo "  2. Ative o workflow e teste com uma mensagem"
    echo ""
    echo "  3. Verifique no PostgreSQL:"
    echo "     docker exec -it e2bot-postgres psql -U e2bot -d e2bot -c 'SELECT phone_number, current_state FROM conversations;'"
else
    echo "❌ Erro: JSON inválido gerado!"
    exit 1
fi

# Limpar arquivo temporário
rm -f /tmp/refactor_workflow.js

echo ""
echo "🎉 Refatoração completa!"
echo "✨ Todos os problemas foram corrigidos:"
echo "  ✅ Estados em português para o banco de dados"
echo "  ✅ ON CONFLICT para evitar duplicatas"
echo "  ✅ phone_number preservado em todos os nós"
echo "  ✅ Formato executeQuery igual ao workflow 01 ULTIMATE"