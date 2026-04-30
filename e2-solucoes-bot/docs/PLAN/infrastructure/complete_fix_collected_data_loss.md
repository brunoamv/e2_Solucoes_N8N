# 🔴 CRITICAL FIX: Perda de Dados no collected_data

**Data**: 2025-01-06
**Status**: CRÍTICO - Sistema perdendo dados
**Workflow**: `02_ai_agent_conversation_V1_MENU_FIXED_v3.json`

---

## 🔍 Problemas Identificados

### Problema 1: Conversão de Tipos (Prepare Update Data)
```javascript
// LINHA 147 - PROBLEMA CRÍTICO
cleanedData[key] = typeof value === 'object' ?
    JSON.stringify(value) :
    String(value);  // ❌ Converte TUDO para string
```

### Problema 2: Perda de Dados no UPDATE
```sql
-- O que está sendo executado:
UPDATE conversations
SET collected_data = '{"error_count":0}'::jsonb  -- ❌ Apenas error_count!
WHERE phone_number = '6181755748'

-- O que deveria ser:
UPDATE conversations
SET collected_data = '{"error_count":0,"last_processed_message":"9","last_state":"service_selection","lead_name":"João","phone":"(61) 8175-5748"}'::jsonb
WHERE phone_number = '6181755748'
```

### Problema 3: Lógica de Limpeza Removendo Dados
```javascript
// No Prepare Update Data - LINHA 145-156
// Remove undefined values and ensure all values are strings or primitives
const cleanedData = {};
for (const [key, value] of Object.entries(collectedData)) {
    if (value !== undefined && value !== null) {  // ❌ Está filtrando demais!
        cleanedData[key] = typeof value === 'object' ?
            JSON.stringify(value) :
            String(value);
    }
}
```

---

## 🎯 Solução Completa

### Fix 1: Prepare Update Data (PRESERVAR TODOS OS DADOS)
```javascript
// Prepare data for database update with FULL data preservation
const input = $input.first().json;

// Get ALL collected data from state machine
let collectedData = input.collected_data || {};

// Ensure collected_data is a valid object
if (typeof collectedData !== 'object' || collectedData === null) {
    collectedData = {};
}

// CRITICAL FIX: Preserve ALL data with correct types
const cleanedData = {};
for (const [key, value] of Object.entries(collectedData)) {
    // Include ALL values, even if empty string
    if (value === undefined) {
        continue; // Skip only undefined
    }

    // PRESERVE NATIVE TYPES
    if (value === null) {
        cleanedData[key] = null;
    } else if (typeof value === 'number') {
        cleanedData[key] = value;  // Keep as number
    } else if (typeof value === 'boolean') {
        cleanedData[key] = value;  // Keep as boolean
    } else if (typeof value === 'string') {
        cleanedData[key] = value;  // Keep as string (even empty)
    } else if (typeof value === 'object') {
        cleanedData[key] = value;  // Keep object (will be stringified)
    } else {
        cleanedData[key] = String(value);  // Convert only unknown types
    }
}

// Debug logging
console.log('Input collected_data:', collectedData);
console.log('Cleaned data:', cleanedData);

// Safely stringify the cleaned data
let collectedDataJson = '{}';
try {
    collectedDataJson = JSON.stringify(cleanedData);
    console.log('Final JSON string:', collectedDataJson);
} catch (e) {
    console.error('Error stringifying collected_data:', e);
    collectedDataJson = '{}';
}

// Return all necessary data for the update
return {
    phone_number: input.phone_number || '',
    next_stage: input.next_stage || input.current_state || 'greeting',
    collected_data_json: collectedDataJson,  // Full data preserved
    response_text: input.response_text || '',
    message: input.message || '',
    message_type: input.message_type || 'text',
    message_id: input.message_id || '',
    timestamp: input.timestamp || new Date().toISOString()
};
```

### Fix 2: State Machine Logic (GARANTIR DADOS COMPLETOS)
No State Machine Logic, após linha 432, adicionar verificação:

```javascript
// Update error count
updateData.error_count = errorCount;

// CRITICAL: Preserve ALL existing data
updateData = {
    ...stageData,  // Keep all existing data
    ...updateData, // Apply new updates
    error_count: errorCount  // Ensure error_count is updated
};

console.log('State Machine updateData:', updateData);
```

### Fix 3: Update Conversation State (QUERY MAIS SEGURA)
Mudar o node "Update Conversation State" para usar parametrização segura:

```sql
-- Usar parâmetros seguros em vez de interpolação
UPDATE conversations
SET
    current_state = $1,
    collected_data = $2::jsonb,
    updated_at = NOW()
WHERE phone_number = $3
RETURNING *
```

Ou manter a query atual mas garantir que o JSON está correto:
```sql
UPDATE conversations
SET
    current_state = '{{ $json.next_stage }}',
    collected_data = COALESCE(
        '{{ $json.collected_data_json }}'::jsonb,
        '{}'::jsonb
    ),
    updated_at = NOW()
WHERE phone_number = '{{ $json.phone_number }}'
RETURNING *
```

---

## 🔧 Script de Correção Automática

```python
#!/usr/bin/env python3
"""
Fix complete data loss in collected_data for V3 workflow
"""
import json
import sys
from datetime import datetime

def fix_workflow_complete():
    # Read workflow
    workflow_path = '/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V1_MENU_FIXED_v3.json'

    with open(workflow_path, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    # Fix 1: Update Prepare Update Data node
    for node in workflow['nodes']:
        if node.get('id') == 'node_prepare_update_data':
            print("📋 Fixing Prepare Update Data node...")
            node['parameters']['jsCode'] = '''// Prepare data for database update with FULL data preservation
const input = $input.first().json;

// Get ALL collected data from state machine
let collectedData = input.collected_data || {};

// Ensure collected_data is a valid object
if (typeof collectedData !== 'object' || collectedData === null) {
    collectedData = {};
}

// CRITICAL FIX: Preserve ALL data with correct types
const cleanedData = {};
for (const [key, value] of Object.entries(collectedData)) {
    // Include ALL values except undefined
    if (value === undefined) {
        continue;
    }

    // PRESERVE NATIVE TYPES
    if (value === null) {
        cleanedData[key] = null;
    } else if (typeof value === 'number') {
        cleanedData[key] = value;  // Keep as number
    } else if (typeof value === 'boolean') {
        cleanedData[key] = value;  // Keep as boolean
    } else if (typeof value === 'string') {
        cleanedData[key] = value;  // Keep as string (even empty)
    } else if (typeof value === 'object') {
        cleanedData[key] = value;  // Keep object
    } else {
        cleanedData[key] = String(value);
    }
}

// Debug logging
console.log('Input collected_data:', collectedData);
console.log('Cleaned data:', cleanedData);

// Safely stringify the cleaned data
let collectedDataJson = '{}';
try {
    collectedDataJson = JSON.stringify(cleanedData);
    console.log('Final JSON string:', collectedDataJson);
} catch (e) {
    console.error('Error stringifying collected_data:', e);
    collectedDataJson = '{}';
}

// Return all necessary data for the update
return {
    phone_number: input.phone_number || '',
    next_stage: input.next_stage || input.current_state || 'greeting',
    collected_data_json: collectedDataJson,
    response_text: input.response_text || '',
    message: input.message || '',
    message_type: input.message_type || 'text',
    message_id: input.message_id || '',
    timestamp: input.timestamp || new Date().toISOString()
};'''

    # Fix 2: Update State Machine to preserve all data
    for node in workflow['nodes']:
        if node.get('id') == 'node_state_machine':
            print("📋 Fixing State Machine Logic...")
            # Find the line with updateData.error_count = errorCount
            code = node['parameters']['functionCode']
            # Add preservation logic
            code = code.replace(
                "// Update error count\nupdateData.error_count = errorCount;",
                """// Update error count
updateData.error_count = errorCount;

// CRITICAL: Preserve ALL existing data
updateData = {
    ...stageData,  // Keep all existing data
    ...updateData, // Apply new updates
    error_count: errorCount  // Ensure error_count is updated
};

console.log('State Machine final updateData:', updateData);"""
            )
            node['parameters']['functionCode'] = code

    # Save fixed workflow
    output_path = '/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V1_MENU_FIXED_v5.json'

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print(f"✅ Fixed workflow saved to: {output_path}")
    return output_path

if __name__ == "__main__":
    fix_workflow_complete()
```

---

## 📊 Diagnóstico de Verificação

### Teste 1: Verificar JSON Completo
```sql
-- Após aplicar o fix, executar:
SELECT
    phone_number,
    current_state,
    collected_data,
    jsonb_pretty(collected_data) as formatted
FROM conversations
WHERE phone_number = '6181755748';

-- Resultado esperado:
-- {
--   "error_count": 0,
--   "last_processed_message": "9",
--   "last_state": "service_selection",
--   "lead_name": "João Silva",
--   "phone": "(61) 8175-5748",
--   "email": "joao@email.com",
--   "city": "Brasília",
--   "service_type": "energia_solar"
-- }
```

### Teste 2: Verificar Tipos Preservados
```sql
SELECT
    jsonb_typeof(collected_data->'error_count') as error_count_type,
    jsonb_typeof(collected_data->'last_processed_message') as message_type,
    jsonb_typeof(collected_data->'wants_appointment') as bool_type
FROM conversations;

-- Esperado:
-- error_count_type: "number" (não "text")
-- message_type: "string"
-- bool_type: "boolean" (quando existir)
```

---

## ⚠️ Ações Imediatas

1. **BACKUP DO WORKFLOW ATUAL**
   ```bash
   cp n8n/workflows/02_ai_agent_conversation_V1_MENU_FIXED_v3.json \
      n8n/workflows/02_ai_agent_conversation_V1_MENU_FIXED_v3.backup.json
   ```

2. **APLICAR O FIX**
   ```bash
   python3 scripts/fix-complete-data-loss.py
   ```

3. **IMPORTAR NO N8N**
   - Desativar workflow v3
   - Importar workflow v5
   - Testar com mensagens reais

4. **MONITORAR LOGS**
   ```bash
   docker logs e2bot-n8n-dev -f | grep "collected_data"
   ```

---

## 🔴 Root Cause Analysis

### Por que isso aconteceu?
1. **Filtro agressivo**: `if (value !== undefined && value !== null)` remove strings vazias
2. **Conversão para string**: Perde tipos nativos do JavaScript
3. **Não preservação de dados existentes**: State Machine não mantém dados anteriores
4. **Template interpolation**: Possível problema no n8n com JSONs complexos

### Lições Aprendidas
1. SEMPRE preservar dados existentes em updates incrementais
2. NUNCA converter tipos desnecessariamente
3. SEMPRE logar dados críticos para debug
4. TESTAR com dados reais, não apenas casos simples

---

**Status**: 🚨 CRÍTICO - Aplicar fix imediatamente!