# Diagnóstico Completo - Workflow não executa

## 🔍 Problema Identificado

### Sintomas
1. ✅ Webhook recebe mensagens do Evolution (`whatsapp-evolution`)
2. ✅ Workflow 01 **inicia** corretamente
3. ❌ Workflow 01 **termina prematuramente** após node "Filter Messages"
4. ❌ Workflow 02 **nunca é chamado**
5. ❌ Nenhuma execução aparece em `http://localhost:5678/home/executions`

### Logs Detalhados

**18:11:47 - Execução típica:**
```
START  → Running node "Webhook WhatsApp" started
PASS   → Running node "Webhook WhatsApp" finished successfully
START  → Start executing node "Filter Messages"
STOP   → Workflow execution finished successfully  ⚠️ TERMINA AQUI
```

**Problema**: O workflow termina **imediatamente após Filter Messages**, sem executar os próximos nodes.

## 🎯 Root Cause Analysis

### Causa #1: Filtro "Filter Messages" bloqueando tudo

**Node configurado para:**
```json
{
  "conditions": {
    "string": [{
      "value1": "={{ $json.body.event }}",
      "operation": "equal",
      "value2": "messages.upsert"
    }]
  }
}
```

**Hipótese**: O payload do Evolution API **NÃO** contém `body.event === "messages.upsert"` ou a estrutura está diferente.

**Resultado**: Todos os webhooks falham no filtro → workflow termina com "sucesso" mas **sem passar mensagens adiante**.

### Causa #2: Node "Create Conversation" com schema incorreto

**Erro no workflow 02 (quando consegue executar):**
```
NodeOperationError: Column 'count' does not exist in selected table
  at node: "Create New Conversation"
```

**Problema**: O node "Create New Conversation" está configurado com `dataMode: "autoMapInputData"`, que tenta inserir **todos os campos** do JSON de entrada, incluindo `count` (que vem do node "Get Conversation Count").

## ✅ Soluções

### Solução #1: Corrigir filtro do workflow 01

**Verificar payload real:**
1. Acessar n8n → Workflow "01 - WhatsApp Handler (FIXED v3)"
2. Clicar em **"Execute Workflow"** manualmente
3. Enviar mensagem WhatsApp
4. Ver o JSON em **"Webhook WhatsApp"** node
5. Identificar caminho correto para `event`

**Opções de correção:**

**A) Se event está em outro caminho:**
```json
// Tentar:
"value1": "={{ $json.event }}"  // ou
"value1": "={{ $json.data.event }}"  // ou
"value1": "={{ $json.body.data.event }}"
```

**B) Se Evolution mudou formato:**
```json
// Remover filtro temporariamente ou usar:
{
  "conditions": {
    "string": [{
      "value1": "={{ $json.body }}",
      "operation": "notEmpty"
    }]
  }
}
```

**C) Validar todos os eventos (sem filtro):**
- Mudar o IF node para **sempre passar** (true)
- Testar se próximos nodes executam
- Depois refinar o filtro

### Solução #2: Corrigir node "Create New Conversation"

**No workflow 02:**
1. Abrir node **"Create New Conversation"**
2. Mudar `Data Mode` de **"Auto-map Input Data"** para **"Define Below"**
3. Configurar campos manualmente:
```
Columns: phone_number, current_state, collected_data
Values:
  phone_number: {{ $json.phone_number }}
  current_state: 'novo'
  collected_data: '{}'
```

**Ou no JSON:**
```json
{
  "parameters": {
    "operation": "insert",
    "schema": { "__rl": true, "value": "public" },
    "table": { "__rl": true, "value": "conversations" },
    "dataMode": "defineBelow",
    "columns": "phone_number,current_state,collected_data",
    "additionalFields": {
      "values": "={{ $json.phone_number }},'novo','{}'"
    }
  }
}
```

### Solução #3: Verificar webhook do Evolution

**Confirmar configuração:**
```bash
# Ver webhook configurado
docker exec e2bot-evolution curl -s \
  -X GET "http://localhost:8080/webhook/find/e2-solucoes-bot" \
  -H "apikey: ${EVOLUTION_API_KEY}"

# Deve retornar:
{
  "webhook": {
    "url": "http://e2bot-n8n-dev:5678/webhook/whatsapp-evolution",
    "enabled": true,
    "events": ["MESSAGES_UPSERT", ...]
  }
}
```

## 📋 Plano de Ação Prioritário

### 1️⃣ URGENTE: Remover filtro temporariamente
- Abrir workflow 01 no n8n
- Node "Filter Messages" → mudar condição para `true` (sempre passa)
- Salvar e ativar
- Testar mensagem WhatsApp
- **Verificar se execução aparece e passa para próximo node**

### 2️⃣ Corrigir node "Create Conversation"
- Workflow 02 → node "Create New Conversation"
- Mudar para `dataMode: "defineBelow"`
- Mapear apenas campos necessários (sem `count`)

### 3️⃣ Analisar payload real
- Com filtro removido, ver JSON completo em execução
- Ajustar condição do filtro corretamente
- Reativar filtro com caminho correto

### 4️⃣ Validação final
- Testar mensagem "oi"
- Verificar execução em `http://localhost:5678/home/executions`
- Confirmar resposta no WhatsApp

## 🔧 Comandos de Debug

```bash
# Ver últimas execuções
docker logs e2bot-n8n-dev 2>&1 | grep "Workflow execution" | tail -20

# Ver payloads recebidos
docker logs e2bot-n8n-dev 2>&1 | grep -A10 "Webhook WhatsApp.*finished"

# Ver erros do PostgreSQL
docker logs e2bot-n8n-dev 2>&1 | grep -i "postgres\|column"

# Ver chamadas de Execute Workflow
docker logs e2bot-n8n-dev 2>&1 | grep "Execute.*Workflow\|Trigger AI Agent"
```

## 📊 Status Atual

- ✅ Evolution API funcionando
- ✅ Webhook recebendo mensagens
- ✅ Workflow 01 ativo
- ✅ Workflow 02 importado
- ❌ **Filtro bloqueando tudo**
- ❌ **Schema PostgreSQL incorreto**
- ❌ Sem execuções visíveis

---
**Data**: 2026-01-02 18:29
**Próximo passo**: Remover filtro temporariamente para validar fluxo
