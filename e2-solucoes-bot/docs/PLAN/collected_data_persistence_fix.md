# 🔍 Análise: Problema de Persistência do collected_data

**Data**: 2025-01-06
**Problema**: `error_count` sempre retornando 0 e valores sendo convertidos incorretamente para string

---

## 🔴 Diagnóstico do Problema

### 1. Sintomas Observados
```json
// Output atual (INCORRETO)
{
  "error_count": "0",           // ❌ String em vez de número
  "last_processed_message": "", // ❌ String vazia em vez de null
  "last_state": "greeting"      // ✅ String correta
}
```

### 2. Raiz do Problema

#### Node: "Prepare Update Data" (Linha 146-156)
```javascript
// PROBLEMA IDENTIFICADO - Linha ~15 do código:
cleanedData[key] = typeof value === 'object' ?
    JSON.stringify(value) :
    String(value);  // ❌ AQUI! Converte TUDO para string
```

Este código está convertendo **TODOS** os valores primitivos para string, incluindo:
- Números (`error_count: 0` vira `"0"`)
- Booleanos (`wants_appointment: true` vira `"true"`)
- Null values (viram strings vazias `""`)

### 3. Fluxo do Problema

```
State Machine Logic
    ↓
    Gera: { error_count: 0 } (número correto)
    ↓
Prepare Update Data
    ↓
    Converte para: { error_count: "0" } (string incorreta)
    ↓
Database (JSONB)
    ↓
    Armazena como string "0"
    ↓
Próxima Execução
    ↓
State Machine recebe "0" como string
    ↓
Number.isInteger("0") = false
    ↓
Reset para 0 sempre!
```

---

## ✅ Solução Proposta

### Correção 1: Prepare Update Data (CRÍTICA)

```javascript
// Prepare data for database update
const input = $input.first().json;

// Safely handle collected_data
let collectedData = input.collected_data || {};

// Ensure collected_data is a valid object
if (typeof collectedData !== 'object' || collectedData === null) {
    collectedData = {};
}

// Clean data preserving types
const cleanedData = {};
for (const [key, value] of Object.entries(collectedData)) {
    if (value !== undefined) {
        // CORREÇÃO: Preservar tipos nativos
        if (value === null) {
            cleanedData[key] = null;
        } else if (typeof value === 'number') {
            cleanedData[key] = value;  // Manter como número
        } else if (typeof value === 'boolean') {
            cleanedData[key] = value;  // Manter como boolean
        } else if (typeof value === 'string') {
            cleanedData[key] = value;  // Manter como string
        } else if (typeof value === 'object') {
            cleanedData[key] = value;  // Manter objeto (será stringificado pelo JSON.stringify depois)
        } else {
            cleanedData[key] = String(value);  // Converter apenas tipos desconhecidos
        }
    }
}

// Safely stringify the cleaned data
let collectedDataJson = '{}';
try {
    collectedDataJson = JSON.stringify(cleanedData);
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
};
```

### Correção 2: State Machine Logic (MELHORIAS)

```javascript
// No início do State Machine, após carregar conversation:
const currentStage = conversation.current_state || 'greeting';

// Parse collected_data corretamente se vier como string
let stageData;
if (typeof conversation.collected_data === 'string') {
    try {
        stageData = JSON.parse(conversation.collected_data);
    } catch (e) {
        stageData = {};
    }
} else {
    stageData = conversation.collected_data || {};
}

// Garantir tipos corretos para campos críticos
stageData.error_count = typeof stageData.error_count === 'number'
    ? stageData.error_count
    : 0;

stageData.last_processed_message = stageData.last_processed_message || null;
stageData.last_state = stageData.last_state || null;
```

---

## 🔧 Script de Correção Automática

```python
#!/usr/bin/env python3
"""
Fix collected_data type preservation in Prepare Update Data node
"""
import json

def fix_prepare_update_data():
    # Read workflow
    with open('n8n/workflows/02_ai_agent_conversation_V1_MENU_FIXED_v3.json', 'r') as f:
        workflow = json.load(f)

    # Find and fix Prepare Update Data node
    for node in workflow['nodes']:
        if node['id'] == 'node_prepare_update_data':
            node['parameters']['jsCode'] = '''// Prepare data for database update
const input = $input.first().json;

// Safely handle collected_data
let collectedData = input.collected_data || {};

// Ensure collected_data is a valid object
if (typeof collectedData !== 'object' || collectedData === null) {
    collectedData = {};
}

// Clean data preserving types
const cleanedData = {};
for (const [key, value] of Object.entries(collectedData)) {
    if (value !== undefined) {
        // Preserve native types
        if (value === null) {
            cleanedData[key] = null;
        } else if (typeof value === 'number') {
            cleanedData[key] = value;  // Keep as number
        } else if (typeof value === 'boolean') {
            cleanedData[key] = value;  // Keep as boolean
        } else if (typeof value === 'string') {
            cleanedData[key] = value;  // Keep as string
        } else if (typeof value === 'object') {
            cleanedData[key] = value;  // Keep object
        } else {
            cleanedData[key] = String(value);  // Convert only unknown types
        }
    }
}

// Safely stringify the cleaned data
let collectedDataJson = '{}';
try {
    collectedDataJson = JSON.stringify(cleanedData);
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
            print("✅ Fixed Prepare Update Data node")
            break

    # Save fixed workflow
    with open('n8n/workflows/02_ai_agent_conversation_V1_MENU_FIXED_v4.json', 'w') as f:
        json.dump(workflow, f, indent=2)

    print("✅ Saved as 02_ai_agent_conversation_V1_MENU_FIXED_v4.json")

if __name__ == "__main__":
    fix_prepare_update_data()
```

---

## 📊 Testes de Validação

### Teste 1: Verificar Tipos no Banco
```sql
-- Verificar o tipo do erro_count no banco
SELECT
    phone_number,
    current_state,
    collected_data,
    jsonb_typeof(collected_data->'error_count') as error_count_type,
    collected_data->'error_count' as error_count_value
FROM conversations
WHERE phone_number = '5562981755485';
```

### Teste 2: Simular Incremento de Erros
1. Enviar mensagem: "Oi"
2. Enviar opção inválida: "9" (deve incrementar error_count para 1)
3. Verificar no banco se error_count = 1
4. Enviar outra inválida: "abc" (deve incrementar para 2)
5. Verificar se error_count = 2

### Resultado Esperado
```json
{
  "error_count": 1,        // ✅ Número, não string
  "last_processed_message": "9",
  "last_state": "service_selection"
}
```

---

## 🎯 Checklist de Implementação

- [ ] Aplicar correção no Prepare Update Data
- [ ] Aplicar melhorias no State Machine Logic
- [ ] Reimportar workflow no n8n
- [ ] Testar incremento de error_count
- [ ] Verificar tipos no banco de dados
- [ ] Confirmar que outros campos numéricos/booleanos funcionam

---

## 💡 Lições Aprendidas

### Por que isso aconteceu?
1. **Conversão agressiva para string**: O código original tentava "limpar" dados convertendo tudo para string
2. **Perda de tipo**: PostgreSQL JSONB preserva tipos, mas estávamos enviando strings
3. **Validação falha**: `Number.isInteger("0")` sempre retorna false

### Melhores Práticas
1. **Preservar tipos nativos** ao trabalhar com JSON
2. **Validar tipos na entrada e saída**
3. **Usar JSONB corretamente** - ele preserva tipos!
4. **Testar com dados reais** incluindo erros e edge cases

---

**Status**: 🔧 PRONTO PARA IMPLEMENTAÇÃO
**Próximo Passo**: Executar script de correção ou aplicar manualmente no n8n