# 🔍 DIAGNÓSTICO COMPLETO: collected_data vazio no State Machine

**Data**: 2026-01-06
**Workflow ID**: FGK93uyr4VLtUR8e (execução 3759)
**Problema**: `collected_data` só retorna `{"error_count": 0}`, perdendo todos os outros campos

---

## ✅ O QUE JÁ VALIDAMOS

### 1. PostgreSQL está CORRETO ✅
```sql
-- Teste realizado:
SELECT pg_typeof(collected_data) FROM conversations; -- RESULTADO: jsonb ✅
SELECT jsonb_typeof(collected_data) FROM conversations; -- RESULTADO: object ✅
SELECT jsonb_typeof(collected_data->'error_count') FROM conversations; -- RESULTADO: number ✅
```

**Conclusão**: O banco de dados armazena e retorna `collected_data` corretamente como JSONB object.

### 2. State Machine Logic está CORRETO ✅
```javascript
const preservedData = {
    ...stageData,      // ✅ Preserva dados existentes
    ...updateData,     // ✅ Adiciona novos
    error_count: errorCount
};
updateData = preservedData;
```

**Conclusão**: A lógica de preservação está correta. O problema é que `stageData` chega VAZIO.

### 3. Problema Identificado: `stageData` inicializa vazio ❌
```javascript
const stageData = conversation.collected_data || {};
```

**Evidência nos logs**:
```
Final preservedData: { error_count: 0 }
Data keys preserved: [ 'error_count' ]
```

Isso significa que `conversation.collected_data` está chegando como:
- `null`
- `undefined`
- `{}`
- Ou string vazia `""`

---

## 🎯 CAUSA RAIZ PROVÁVEL

### Hipótese 1: n8n PostgreSQL node retorna string em vez de object
O node PostgreSQL do n8n pode estar retornando `collected_data` como **string JSON** em vez de **object JavaScript**.

**Exemplo**:
```javascript
// Como PostgreSQL retorna (JSONB):
collected_data = {"error_count": 0, "lead_name": "João"}

// Como n8n pode estar recebendo (string):
conversation.collected_data = '{"error_count": 0, "lead_name": "João"}'

// State Machine tenta usar:
const stageData = conversation.collected_data || {};  // STRING não é objeto!
```

### Hipótese 2: Query SELECT não traz collected_data
Verificamos que a query é `SELECT *` então **deveria** trazer. Mas pode haver:
- Problema no node "Get Conversation Details"
- `collected_data` vindo como `null` do banco
- Erro silencioso no parse

---

## 📋 PLANO DE CORREÇÃO

### ✅ SOLUÇÃO IMEDIATA: Safe JSON Parsing

Adicionar no **State Machine Logic**, ANTES de usar `stageData`:

```javascript
const currentStage = conversation.current_state || 'novo';

// ===== ADICIONAR ESTE CÓDIGO =====
let stageData = {};

if (conversation.collected_data) {
    if (typeof conversation.collected_data === 'string') {
        try {
            console.log('🔍 collected_data is STRING, parsing...');
            stageData = JSON.parse(conversation.collected_data);
            console.log('✅ Parsed successfully:', stageData);
        } catch (e) {
            console.error('❌ Error parsing collected_data:', e);
            console.error('Raw value was:', conversation.collected_data);
            stageData = {};
        }
    } else if (typeof conversation.collected_data === 'object' && conversation.collected_data !== null) {
        console.log('✅ collected_data is OBJECT, using directly');
        stageData = conversation.collected_data;
    } else {
        console.log('⚠️ collected_data is unexpected type:', typeof conversation.collected_data);
        stageData = {};
    }
} else {
    console.log('⚠️ collected_data is null/undefined');
}

console.log('=== COLLECTED DATA DEBUGGING ===');
console.log('Raw conversation.collected_data:', conversation.collected_data);
console.log('Type:', typeof conversation.collected_data);
console.log('Parsed stageData:', stageData);
console.log('Keys in stageData:', Object.keys(stageData));
console.log('=== END DEBUGGING ===');
// ===== FIM DO CÓDIGO ADICIONAL =====

// Resto do código continua igual...
const errorCount = (typeof stageData.error_count === 'number')
    ? stageData.error_count
    : 0;
```

---

## 🧪 TESTES DE VALIDAÇÃO

### Teste 1: Verificar logs após implementação
```bash
docker logs e2bot-n8n-dev 2>&1 | grep "COLLECTED DATA DEBUGGING" -A10
```

**Resultado esperado**:
```
=== COLLECTED DATA DEBUGGING ===
✅ collected_data is OBJECT, using directly
Raw conversation.collected_data: { error_count: 0, lead_name: 'João Silva', phone: '11999999999' }
Type: object
Parsed stageData: { error_count: 0, lead_name: 'João Silva', phone: '11999999999' }
Keys in stageData: [ 'error_count', 'lead_name', 'phone' ]
=== END DEBUGGING ===
```

### Teste 2: Verificar banco após conversa
```bash
docker exec e2bot-postgres-dev psql -U postgres -d e2_bot -c "
SELECT
    phone_number,
    current_state,
    jsonb_pretty(collected_data) as data,
    jsonb_object_keys(collected_data) as campos
FROM conversations
WHERE phone_number = '5562981755485';"
```

**Resultado esperado**: Múltiplos campos preservados (não só `error_count`)

---

## 🚨 PROBLEMAS ADICIONAIS ENCONTRADOS

### 1. Phone Number "undefined" ❌
```sql
-- Encontrado no banco:
phone_number | current_state | collected_data
-------------+---------------+----------------
undefined    | novo          | {}
```

**Causa**: Workflow recebendo `phone_number` inválido do webhook Evolution API

**Correção necessária**: Adicionar validação no node "Validate Input Data":
```javascript
const phoneNumber = $json.key?.remoteJid?.split('@')[0] ||
                    $json.from?.split('@')[0] ||
                    'undefined';

if (phoneNumber === 'undefined' || !phoneNumber) {
    throw new Error('Phone number not found in webhook data');
}
```

### 2. Estados inválidos "undefined" ❌
**Constraint violation**: `valid_state` check failed

**Estados válidos**:
- novo
- identificando_servico
- coletando_dados
- aguardando_foto
- agendando
- agendado
- handoff_comercial
- concluido

**Correção necessária**: Validar `next_state` antes do UPDATE

---

## 📊 CHECKLIST DE EXECUÇÃO

- [ ] 1. Implementar Safe JSON Parsing no State Machine Logic
- [ ] 2. Adicionar logs de debug extensivos
- [ ] 3. Limpar dados de teste do banco: `DELETE FROM conversations WHERE phone_number IN ('undefined', '5511999999999')`
- [ ] 4. Enviar mensagem teste via WhatsApp
- [ ] 5. Verificar logs: `docker logs e2bot-n8n-dev --tail 100 | grep "COLLECTED DATA"`
- [ ] 6. Verificar banco: `SELECT * FROM conversations ORDER BY updated_at DESC LIMIT 1`
- [ ] 7. Validar que múltiplos campos são preservados
- [ ] 8. Corrigir validação de phone_number (problema secundário)
- [ ] 9. Corrigir validação de estados (problema secundário)

---

## 🎯 RESULTADO ESPERADO

**ANTES** (estado atual):
```javascript
preservedData = { error_count: 0 }
```

**DEPOIS** (com correção):
```javascript
preservedData = {
    error_count: 0,
    lead_name: "João Silva",
    phone: "62981755485",
    email: "joao@example.com",
    city: "Goiânia",
    service_type: "energia_solar"
}
```

---

**PRÓXIMA AÇÃO IMEDIATA**: Implementar Safe JSON Parsing no State Machine Logic do workflow ativo!
