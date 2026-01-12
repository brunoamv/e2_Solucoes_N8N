# 🎯 PLANO: Correção do `collected_data` no State Machine Logic

**Data**: 2026-01-06
**Workflow**: `FGK93uyr4VLtUR8e` (execução 3759)
**Problema**: Variável `collected_data` só retorna `error_count`, perdendo todos os outros campos

---

## 🔍 ANÁLISE DO PROBLEMA

### Situação Atual
O código do **State Machine Logic** JÁ tem a lógica de preservação correta:
```javascript
const preservedData = {
    ...stageData,      // ✅ Preserva dados existentes
    ...updateData,     // ✅ Adiciona novos
    error_count: errorCount
};
```

**MAS** o problema está **ANTES**:
```javascript
const stageData = conversation.collected_data || {};
```

Se `conversation.collected_data` vier como `null` ou vazio do banco, perdemos tudo.

### Causa Raiz
1. **Query SELECT não traz `collected_data` corretamente**
2. **Node "Get Conversation"** não está retornando o JSONB parseado
3. **Tipo JSONB no PostgreSQL** pode vir como string `"{}"`

---

## 📝 TAREFAS PARA EXECUÇÃO

### ✅ Tarefa 1: Verificar Node "Get Conversation" no Workflow
**Objetivo**: Confirmar se o SELECT está trazendo `collected_data` corretamente

**Ações**:
1. Acessar n8n: http://localhost:5678/workflow/FGK93uyr4VLtUR8e
2. Localizar node "Get or Create Conversation" (ou similar)
3. Verificar query SQL:
   ```sql
   SELECT
       id,
       phone_number,
       current_state,
       collected_data,  -- ← DEVE ESTAR AQUI
       created_at,
       updated_at
   FROM conversations
   WHERE phone_number = '{{ $json.phone_number }}'
   LIMIT 1;
   ```
4. Verificar se `collected_data` está sendo selecionado

**Resultado Esperado**: Query deve incluir `collected_data` no SELECT

---

### ✅ Tarefa 2: Adicionar Parsing Seguro no State Machine
**Objetivo**: Garantir que `collected_data` seja sempre um objeto válido

**Ações**:
1. Editar o código do **State Machine Logic**
2. **SUBSTITUIR** estas linhas:
   ```javascript
   const currentStage = conversation.current_state || 'greeting';
   const stageData = conversation.collected_data || {};
   ```

3. **POR** este código com parsing seguro:
   ```javascript
   const currentStage = conversation.current_state || 'greeting';

   // Parse collected_data com segurança
   let stageData = {};
   if (conversation.collected_data) {
       if (typeof conversation.collected_data === 'string') {
           try {
               stageData = JSON.parse(conversation.collected_data);
           } catch (e) {
               console.error('Error parsing collected_data:', e);
               stageData = {};
           }
       } else if (typeof conversation.collected_data === 'object') {
           stageData = conversation.collected_data;
       }
   }

   console.log('=== COLLECTED DATA PARSING ===');
   console.log('Raw collected_data:', conversation.collected_data);
   console.log('Type:', typeof conversation.collected_data);
   console.log('Parsed stageData:', stageData);
   console.log('=== END PARSING ===');
   ```

**Resultado Esperado**: Logs mostrarão exatamente o que vem do banco

---

### ✅ Tarefa 3: Verificar Node "Update Conversation State"
**Objetivo**: Confirmar que o UPDATE está salvando `collected_data` corretamente

**Ações**:
1. Localizar node "Update Conversation State" no workflow
2. Verificar query UPDATE:
   ```sql
   UPDATE conversations
   SET
       current_state = '{{ $json.next_stage }}',
       collected_data = '{{ JSON.stringify($json.collected_data) }}'::jsonb,  -- ← CRUCIAL
       updated_at = NOW()
   WHERE phone_number = '{{ $json.phone_number }}'
   RETURNING *;
   ```
3. Verificar se está usando `::jsonb` no cast

**Resultado Esperado**: UPDATE deve fazer cast para JSONB

---

### ✅ Tarefa 4: Adicionar Logging Extensivo
**Objetivo**: Capturar exatamente onde os dados são perdidos

**Ações**:
1. No **State Machine Logic**, ADICIONAR logging após o switch:
   ```javascript
   // Logo DEPOIS do switch (currentStage) { ... }

   console.log('=== STATE MACHINE COMPLETE DEBUG ===');
   console.log('Current Stage:', currentStage);
   console.log('Next Stage:', nextStage);
   console.log('Original stageData:', stageData);
   console.log('updateData before merge:', updateData);
   console.log('errorCount:', errorCount);
   console.log('preservedData:', preservedData);
   console.log('Final updateData:', updateData);
   console.log('Keys in final updateData:', Object.keys(updateData));
   console.log('=== END DEBUG ===');
   ```

**Resultado Esperado**: Logs completos para cada execução

---

### ✅ Tarefa 5: Testar com Dados Reais
**Objetivo**: Validar correção com fluxo completo

**Ações**:
1. Limpar dados de teste:
   ```sql
   DELETE FROM conversations WHERE phone_number = '5562981755485';
   ```

2. Enviar mensagem teste no WhatsApp:
   ```
   Oi
   ```

3. Verificar logs do n8n:
   ```bash
   docker logs e2bot-n8n-dev --tail 100 | grep "COLLECTED DATA"
   ```

4. Verificar banco:
   ```sql
   SELECT
       phone_number,
       current_state,
       jsonb_pretty(collected_data) as data,
       jsonb_typeof(collected_data->'error_count') as error_count_type
   FROM conversations
   WHERE phone_number = '5562981755485';
   ```

**Resultado Esperado**:
- Logs mostram dados sendo preservados
- `collected_data` contém todos os campos
- `error_count_type` = `'number'` (não `'text'`)

---

### ✅ Tarefa 6: Verificar Integração com "Prepare Update Data"
**Objetivo**: Confirmar que o node seguinte preserva tipos

**Ações**:
1. Localizar node "Prepare Update Data" no workflow
2. Verificar se usa a lógica v5 (preservação de tipos):
   ```javascript
   // DEVE ter algo assim:
   if (typeof value === 'number') {
       cleanedData[key] = value;  // Mantém número
   } else if (typeof value === 'boolean') {
       cleanedData[key] = value;  // Mantém boolean
   }
   ```
3. Se NÃO tiver, aplicar correção do v5

**Resultado Esperado**: "Prepare Update Data" preserva tipos primitivos

---

## 🎯 ORDEM DE EXECUÇÃO

```
1. Verificar Node "Get Conversation" (SELECT)
   ↓
2. Adicionar Parsing Seguro no State Machine
   ↓
3. Adicionar Logging Extensivo
   ↓
4. Verificar Node "Update Conversation" (UPDATE)
   ↓
5. Testar com Dados Reais
   ↓
6. Verificar "Prepare Update Data" (se necessário)
```

---

## 📊 CRITÉRIOS DE SUCESSO

### ✅ Correção Bem-Sucedida Quando:
1. **Logs mostram**: `stageData` vem populado com campos anteriores
2. **Logs mostram**: `preservedData` contém TODOS os campos (não só `error_count`)
3. **Banco mostra**: `collected_data` com múltiplos campos preservados
4. **Tipos corretos**: `error_count` é `number`, não `string`

### ❌ Ainda Tem Problema Se:
1. `stageData` sempre inicia vazio `{}`
2. `collected_data` só tem `error_count` após conversa completa
3. `error_count_type` = `'text'` em vez de `'number'`

---

## 🔧 SCRIPTS AUXILIARES

### Verificar Estado Atual
```bash
# Ver logs recentes
docker logs e2bot-n8n-dev --tail 50 | grep -A5 "STATE MACHINE"

# Ver collected_data no banco
docker exec e2bot-postgres-dev psql -U postgres -d e2_bot -c "
SELECT
    phone_number,
    current_state,
    jsonb_pretty(collected_data)
FROM conversations
ORDER BY updated_at DESC
LIMIT 3;"
```

### Limpar Dados de Teste
```bash
docker exec e2bot-postgres-dev psql -U postgres -d e2_bot -c "
DELETE FROM conversations WHERE phone_number = '5562981755485';"
```

---

## 📞 PRÓXIMOS PASSOS APÓS EXECUÇÃO

1. **Se funcionou**: Documentar solução e marcar como resolvido
2. **Se não funcionou**: Analisar logs detalhados e identificar próximo ponto de falha
3. **Importar workflow v5**: Se o problema for no "Prepare Update Data", importar v5 corrigido

---

**AÇÃO IMEDIATA**: Executar Tarefas 1-3 para diagnóstico completo do fluxo de dados!