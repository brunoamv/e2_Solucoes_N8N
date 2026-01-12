#!/bin/bash

# Script para corrigir o problema de phone_number não sendo passado entre workflows
# Problema: Workflow 01 não passa phone_number para Workflow 02, causando valores vazios/undefined no banco

set -e

echo "🔍 Análise do Problema de Phone Number"
echo "======================================"
echo ""
echo "📋 Problema Identificado:"
echo "  - Workflow 01 (WhatsApp Handler) extrai phone_number mas não o passa para Workflow 02"
echo "  - Resultado: phone_number vazio ou 'undefined' no banco de dados"
echo "  - Erro subsequente: violação de constraint ao atualizar estado"
echo ""

# Criar backup dos workflows
TIMESTAMP=$(date +%s)
WORKFLOW_01="/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/01 - WhatsApp Handler (ULTIMATE).json"
WORKFLOW_02="/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V1_MENU_REFACTORED.json"

echo "📁 Criando backups..."
cp "$WORKFLOW_01" "${WORKFLOW_01}.backup_${TIMESTAMP}"
cp "$WORKFLOW_02" "${WORKFLOW_02}.backup_${TIMESTAMP}"

# Criar script para corrigir Workflow 01
cat > /tmp/fix_workflow_01.js << 'EOF'
const fs = require('fs');
const workflow = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));

// Encontrar o nó "Trigger AI Agent"
let triggerAINode = null;
let triggerAIIndex = -1;

workflow.nodes.forEach((node, index) => {
  if (node.name === 'Trigger AI Agent') {
    triggerAINode = node;
    triggerAIIndex = index;
    console.log('✅ Encontrado nó "Trigger AI Agent" no índice', index);
  }
});

if (!triggerAINode) {
  console.error('❌ Nó "Trigger AI Agent" não encontrado!');
  process.exit(1);
}

// Adicionar um nó Code antes do Trigger AI Agent para preparar os dados
const prepareDataNode = {
  "parameters": {
    "jsCode": `// Preparar dados para o Workflow 02 (AI Agent)
// IMPORTANTE: Garantir que phone_number seja passado corretamente

const messageData = $node["Merge Results"].json;

// Extrair e validar phone_number
let phone_number = messageData.phone_number || '';

// Remover formatação e garantir que não seja undefined
if (!phone_number || phone_number === 'undefined' || phone_number === 'null') {
  // Tentar extrair do nó anterior
  const extractData = $node["Extract Message Data"].json;
  phone_number = extractData.phone_number || '';
}

// Garantir formato correto (remover @s.whatsapp.net se presente)
phone_number = phone_number.replace('@s.whatsapp.net', '').replace(/[^0-9+]/g, '');

if (!phone_number) {
  throw new Error('Phone number is required but was not found in the message data');
}

// Preparar payload completo para o workflow 02
return {
  phone_number: phone_number,
  whatsapp_name: messageData.whatsapp_name || '',
  message: messageData.content || '',
  message_type: messageData.message_type || 'text',
  media_url: messageData.media_url || null,
  message_id: messageData.message_id || '',
  timestamp: new Date().toISOString()
};`
  },
  "id": "prepare-data-for-ai",
  "name": "Prepare Data for AI Agent",
  "type": "n8n-nodes-base.code",
  "typeVersion": 2,
  "position": [150, 200]
};

// Inserir o novo nó antes do Trigger AI Agent
workflow.nodes.splice(triggerAIIndex, 0, prepareDataNode);

// Atualizar conexões para incluir o novo nó
// Encontrar conexão que leva ao Trigger AI Agent
const connections = workflow.connections;

// Encontrar quem se conecta ao Trigger AI Agent
for (const [nodeName, nodeConnections] of Object.entries(connections)) {
  if (nodeConnections.main) {
    nodeConnections.main.forEach((connectionArray, mainIndex) => {
      connectionArray.forEach((connection, connIndex) => {
        if (connection.node === "Trigger AI Agent") {
          console.log(`✅ Atualizando conexão de "${nodeName}" para passar por "Prepare Data for AI Agent"`);
          // Redirecionar para o novo nó
          connection.node = "Prepare Data for AI Agent";
        }
      });
    });
  }
}

// Adicionar conexão do novo nó para o Trigger AI Agent
connections["Prepare Data for AI Agent"] = {
  "main": [[{
    "node": "Trigger AI Agent",
    "type": "main",
    "index": 0
  }]]
};

// Salvar workflow atualizado
fs.writeFileSync(process.argv[3], JSON.stringify(workflow, null, 2));
console.log('✅ Workflow 01 atualizado com sucesso!');
EOF

# Criar script para verificar/corrigir Workflow 02
cat > /tmp/fix_workflow_02.js << 'EOF'
const fs = require('fs');
const workflow = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));

// Encontrar o primeiro nó que deve receber os dados (geralmente um trigger ou start node)
let startNode = null;
let hasManualTrigger = false;

workflow.nodes.forEach(node => {
  if (node.type === 'n8n-nodes-base.manualTrigger' ||
      node.type === 'n8n-nodes-base.executeWorkflowTrigger' ||
      node.name === 'Start' ||
      node.name === 'Manual Trigger' ||
      node.name === 'Workflow Trigger') {
    startNode = node;
    console.log('✅ Encontrado nó inicial:', node.name);
  }
});

// Verificar se os nós que usam phone_number estão corretos
let fixCount = 0;

workflow.nodes.forEach(node => {
  // Verificar nós PostgreSQL
  if (node.type === 'n8n-nodes-base.postgres' && node.parameters && node.parameters.query) {
    let query = node.parameters.query;

    // Verificar se usa phone_number
    if (query.includes('phone_number')) {
      // Garantir que use $json.phone_number e não outras variações
      const originalQuery = query;

      // Corrigir referências incorretas
      query = query.replace(/\{\{ \$json\.phone_number\.replace/g, '{{ $json.phone_number.replace');
      query = query.replace(/undefined/g, '$json.phone_number');

      if (query !== originalQuery) {
        node.parameters.query = query;
        fixCount++;
        console.log(`✅ Corrigido query no nó "${node.name}"`);
      }
    }
  }

  // Verificar nós Code/Function
  if ((node.type === 'n8n-nodes-base.code' || node.type === 'n8n-nodes-base.function') &&
      node.parameters && node.parameters.jsCode) {
    let code = node.parameters.jsCode;

    if (code.includes('phone_number')) {
      const originalCode = code;

      // Garantir que phone_number seja extraído corretamente do input
      if (!code.includes('// Phone number validation')) {
        // Adicionar validação no início do código
        const validation = `// Phone number validation
const phone_number = $json.phone_number || $input.first().json.phone_number || '';
if (!phone_number || phone_number === 'undefined') {
  throw new Error('Phone number is required but not found');
}

`;
        if (code.includes('const ')) {
          // Adicionar antes da primeira const
          code = code.replace(/const /, validation + 'const ');
        } else {
          // Adicionar no início
          code = validation + code;
        }

        node.parameters.jsCode = code;
        fixCount++;
        console.log(`✅ Adicionada validação de phone_number no nó "${node.name}"`);
      }
    }
  }
});

// Adicionar nó de validação inicial se não existir
const validationNode = {
  "parameters": {
    "jsCode": `// Validação inicial dos dados recebidos do Workflow 01
const inputData = $input.first().json;

// Validar phone_number
if (!inputData.phone_number || inputData.phone_number === 'undefined' || inputData.phone_number === 'null') {
  throw new Error('Phone number is required but was not received from Workflow 01');
}

// Garantir formato correto
const phone_number = String(inputData.phone_number).replace(/[^0-9+]/g, '');

if (!phone_number) {
  throw new Error('Invalid phone number format');
}

// Retornar dados validados
return {
  phone_number: phone_number,
  whatsapp_name: inputData.whatsapp_name || '',
  message: inputData.message || inputData.content || '',
  message_type: inputData.message_type || 'text',
  media_url: inputData.media_url || null,
  message_id: inputData.message_id || '',
  timestamp: inputData.timestamp || new Date().toISOString()
};`
  },
  "id": "validate-input-data",
  "name": "Validate Input Data",
  "type": "n8n-nodes-base.code",
  "typeVersion": 2,
  "position": [-400, 200]
};

// Verificar se já existe um nó de validação
let hasValidation = workflow.nodes.some(node =>
  node.name === "Validate Input Data" ||
  node.name === "Input Validation"
);

if (!hasValidation && startNode) {
  console.log('✅ Adicionando nó de validação de entrada');
  workflow.nodes.unshift(validationNode);
  fixCount++;

  // Atualizar conexões
  if (!workflow.connections["Workflow Trigger"]) {
    workflow.connections["Workflow Trigger"] = {};
  }

  // Conectar trigger ao nó de validação
  workflow.connections["Workflow Trigger"]["main"] = [[{
    "node": "Validate Input Data",
    "type": "main",
    "index": 0
  }]];

  // Conectar validação ao próximo nó
  workflow.connections["Validate Input Data"] = {
    "main": [[{
      "node": workflow.nodes[1].name, // Próximo nó após validação
      "type": "main",
      "index": 0
    }]]
  };
}

// Salvar workflow
fs.writeFileSync(process.argv[3], JSON.stringify(workflow, null, 2));
console.log(`✅ Workflow 02: ${fixCount} correções aplicadas`);
EOF

echo ""
echo "🔧 Corrigindo Workflow 01 (WhatsApp Handler)..."
node /tmp/fix_workflow_01.js "$WORKFLOW_01" "${WORKFLOW_01%.json}_FIXED_PHONE.json"

echo ""
echo "🔧 Corrigindo Workflow 02 (AI Agent)..."
node /tmp/fix_workflow_02.js "$WORKFLOW_02" "${WORKFLOW_02%.json}_FIXED_PHONE.json"

echo ""
echo "🧪 Criando script de teste..."
cat > /tmp/test_phone_flow.sh << 'EOFTEST'
#!/bin/bash

echo "🧪 Teste do fluxo de phone_number"
echo "================================="
echo ""

# Testar se os campos estão corretos no banco
docker exec e2bot-postgres-dev psql -U postgres -d e2_bot -c "
SELECT
  phone_number,
  CASE
    WHEN phone_number IS NULL THEN 'NULL ❌'
    WHEN phone_number = '' THEN 'EMPTY ❌'
    WHEN phone_number = 'undefined' THEN 'UNDEFINED ❌'
    ELSE 'OK ✅'
  END as status,
  current_state,
  created_at
FROM conversations
ORDER BY created_at DESC
LIMIT 5;
"

echo ""
echo "📊 Resumo de problemas:"
docker exec e2bot-postgres-dev psql -U postgres -d e2_bot -t -c "
SELECT
  COUNT(*) FILTER (WHERE phone_number IS NULL) as nulls,
  COUNT(*) FILTER (WHERE phone_number = '') as empty,
  COUNT(*) FILTER (WHERE phone_number = 'undefined') as undefined,
  COUNT(*) FILTER (WHERE phone_number IS NOT NULL AND phone_number != '' AND phone_number != 'undefined') as valid
FROM conversations;
" | awk '{print "  NULL: " $1 "\n  Empty: " $2 "\n  Undefined: " $3 "\n  Valid: " $4}'
EOFTEST

chmod +x /tmp/test_phone_flow.sh

echo ""
echo "📋 Executando teste inicial..."
/tmp/test_phone_flow.sh

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ CORREÇÃO APLICADA!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📁 Arquivos gerados:"
echo "  1. ${WORKFLOW_01%.json}_FIXED_PHONE.json"
echo "     → Workflow 01 com nó 'Prepare Data for AI Agent'"
echo ""
echo "  2. ${WORKFLOW_02%.json}_FIXED_PHONE.json"
echo "     → Workflow 02 com validação de phone_number"
echo ""
echo "🎯 Próximos passos:"
echo "  1. Importar os workflows corrigidos no n8n:"
echo "     - Workflow 01: ${WORKFLOW_01%.json}_FIXED_PHONE.json"
echo "     - Workflow 02: ${WORKFLOW_02%.json}_FIXED_PHONE.json"
echo ""
echo "  2. Testar com uma mensagem real do WhatsApp"
echo ""
echo "  3. Verificar no banco:"
echo "     /tmp/test_phone_flow.sh"
echo ""
echo "⚠️ IMPORTANTE: O phone_number agora é OBRIGATÓRIO"
echo "  Se faltar, o workflow 02 irá falhar com erro explícito"
echo "  Isso é melhor que salvar valores vazios/undefined no banco"

# Limpar arquivos temporários
rm -f /tmp/fix_workflow_01.js /tmp/fix_workflow_02.js