# Análise Profunda e Plano de Correção: Workflow 01 - WhatsApp Handler

**Data**: 2025-01-05 20:00
**Status**: 🔍 ANÁLISE COMPLETA - AGUARDANDO EXECUÇÃO
**Severidade**: 🔴 CRÍTICO - Workflow completamente quebrado

---

## 🎯 Resumo Executivo

O workflow "01 - WhatsApp Handler (FIXED v5)" possui **2 problemas críticos** que impedem seu funcionamento:

1. **"Column 'success' does not exist"**: O nó "Save Inbound Message" usa `autoMapInputData` que tenta mapear campos inexistentes
2. **"Is New Message?" retorna vazio**: Lógica de verificação incompatível com estrutura de dados do PostgreSQL

---

## 📊 Análise dos Workflows

### Identificação dos Workflows

| Workflow | ID | Status | Problema |
|----------|-----|--------|----------|
| 01_main_whatsapp_handler.json | 4SwPV89rN2sM8ygM | ❌ Falha parcial | Erro "Column 'success' does not exist" |
| 01 - WhatsApp Handler (FIXED v5).json | Xd7D60MVRs8M9nQS | ❌ Para silenciosamente | "Is New Message?" retorna vazio |

### Evidências dos Logs

```log
# Workflow 4SwPV89rN2sM8ygM (antigo)
19:45:28.422   Extract Message Data finished successfully
19:45:28.468   NodeOperationError: Column 'success' does not exist in selected table
                at Save Inbound Message node with dataMode: "autoMapInputData"

# Workflow Xd7D60MVRs8M9nQS (FIXED v5)
19:47:20.295   Extract Message Data finished successfully
19:47:20.306   Workflow execution finished successfully ❌ INCORRETO - para sem processar
```

---

## 🔍 Análise Detalhada dos Problemas

### PROBLEMA 1: "Column 'success' does not exist"

#### Causa Raiz

O nó "Save Inbound Message" no workflow antigo está configurado com:

```json
{
  "parameters": {
    "operation": "insert",
    "table": "messages",
    "dataMode": "autoMapInputData"  // ⚠️ PROBLEMA
  }
}
```

O modo `autoMapInputData` tenta mapear **TODOS** os campos do input para colunas da tabela, mas o input contém campos extras que não existem no schema.

#### Fluxo de Dados Problemático

```
1. Extract Message Data
   ↓ Retorna: {phone_number, whatsapp_name, message_id, content, ...}
2. Check Duplicate
   ↓ Adiciona: metadados do PostgreSQL, campo 'success', etc.
3. Is New Message?
   ↓ Propaga TODOS os dados anteriores
4. Save Inbound Message (autoMapInputData)
   ❌ Tenta mapear campo 'success' inexistente na tabela
```

#### Solução Proposta

Usar mapeamento explícito de campos como no workflow antigo funcional:

```json
{
  "parameters": {
    "operation": "insert",
    "table": "messages",
    "columns": "conversation_id, direction, content, message_type, media_url, whatsapp_message_id",
    "additionalFields": {
      "values": "null, 'inbound', '{{ $node[\"Extract Message Data\"].json.content }}', ..."
    }
  }
}
```

---

### PROBLEMA 2: "Is New Message?" Retorna Vazio

#### Causa Raiz

O nó "Is New Message?" no FIXED v5 usa:

```json
{
  "conditions": [
    {
      "leftValue": "={{ $input.all()[0].json.id }}",
      "operator": {
        "type": "any",
        "operation": "isEmpty"
      }
    }
  ]
}
```

Quando não há duplicata, o "Check Duplicate" retorna array VAZIO `[]`, então:
- `$input.all()[0]` → undefined
- `undefined.json.id` → ERRO SILENCIOSO
- Workflow para sem mensagem de erro

#### Comparação com Workflow Antigo (Funcional)

```json
{
  "conditions": {
    "boolean": [
      {
        "value1": "={{ !$input.all()[0].json.id }}",
        "value2": true
      }
    ]
  }
}
```

Esta abordagem funciona porque:
- Array vazio: `!undefined` = `true` (é nova mensagem) ✅
- Array com resultado: `!id` = `false` (é duplicata) ✅

#### Solução Proposta

Opção 1 - Verificar comprimento do array:
```json
{
  "leftValue": "={{ $input.all().length }}",
  "rightValue": 0,
  "operator": {
    "type": "number",
    "operation": "equals"
  }
}
```

Opção 2 - Usar lógica booleana do workflow antigo (mais confiável)

---

## 🛠️ Plano de Correção Detalhado

### Fase 1: Correção do "Is New Message?"

**Arquivo**: `01 - WhatsApp Handler (FIXED v5).json:99-130`

**De**:
```json
"conditions": [
  {
    "leftValue": "={{ $input.all()[0].json.id }}",
    "operator": {
      "operation": "isEmpty"
    }
  }
]
```

**Para**:
```json
"conditions": {
  "boolean": [
    {
      "value1": "={{ !$input.all()[0].json.id }}",
      "value2": true
    }
  ]
}
```

### Fase 2: Correção do "Save Inbound Message"

**Arquivo**: `01 - WhatsApp Handler (FIXED v5).json:131-151`

**De**:
```json
{
  "parameters": {
    "operation": "executeQuery",
    "query": "=INSERT INTO messages ...",
    "options": {}
  }
}
```

**Para** (usando mapeamento explícito):
```json
{
  "parameters": {
    "operation": "insert",
    "table": "messages",
    "columns": "conversation_id, direction, content, message_type, media_url, whatsapp_message_id",
    "additionalFields": {
      "values": "null, 'inbound', '{{ $node[\"Extract Message Data\"].json.content }}', '{{ $node[\"Extract Message Data\"].json.message_type }}', {{ $node[\"Extract Message Data\"].json.media_url ? \"'\" + $node[\"Extract Message Data\"].json.media_url + \"'\" : \"null\" }}, '{{ $node[\"Extract Message Data\"].json.message_id }}'"
    }
  }
}
```

### Fase 3: Validação do "Extract Message Data"

Garantir que retorna APENAS os campos esperados:
- phone_number
- whatsapp_name
- message_id
- message_type
- content
- media_url
- timestamp

Remover qualquer campo adicional como 'success' ou metadados.

---

## 📋 Workflow Corrigido Completo (v6)

```json
{
  "name": "01 - WhatsApp Handler (FIXED v6)",
  "nodes": [
    // ... outros nós permanecem iguais ...

    {
      "parameters": {
        "conditions": {
          "boolean": [
            {
              "value1": "={{ !$input.all()[0].json.id }}",
              "value2": true
            }
          ]
        }
      },
      "id": "7907ea4f-cbed-4d09-ac1e-750ec0bcc482",
      "name": "Is New Message?",
      "type": "n8n-nodes-base.if",
      "typeVersion": 1,
      "position": [-608, 208]
    },

    {
      "parameters": {
        "operation": "insert",
        "table": "messages",
        "columns": "conversation_id, direction, content, message_type, media_url, whatsapp_message_id",
        "additionalFields": {
          "values": "null, 'inbound', '{{ $node[\"Extract Message Data\"].json.content }}', '{{ $node[\"Extract Message Data\"].json.message_type }}', {{ $node[\"Extract Message Data\"].json.media_url ? \"'\" + $node[\"Extract Message Data\"].json.media_url + \"'\" : \"null\" }}, '{{ $node[\"Extract Message Data\"].json.message_id }}'"
        }
      },
      "id": "73005c79-6782-4811-9ea0-8c69861980f5",
      "name": "Save Inbound Message",
      "type": "n8n-nodes-base.postgres",
      "typeVersion": 2,
      "position": [-400, 112],
      "credentials": {
        "postgres": {
          "id": "VXA1r8sd0TMIdPvS",
          "name": "PostgreSQL - E2 Bot"
        }
      }
    }
  ]
}
```

---

## 🚀 Instruções de Execução para /sc:task

### Passo 1: Backup
```bash
cp "n8n/workflows/01 - WhatsApp Handler (FIXED v5).json" \
   "n8n/workflows/01 - WhatsApp Handler (FIXED v5).json.backup-$(date +%Y%m%d-%H%M%S)"
```

### Passo 2: Aplicar Correções
1. Editar o arquivo JSON com as correções propostas
2. Validar sintaxe JSON
3. Criar versão v6 do workflow

### Passo 3: Reimportar no n8n
1. Acessar n8n UI (http://localhost:5678)
2. Importar o workflow corrigido v6
3. Desativar workflows antigos
4. Ativar apenas o v6

### Passo 4: Testar
```bash
# Usar script de teste existente
./scripts/test-workflow-01-e2e.sh

# Verificar logs
docker logs e2bot-n8n-dev --tail 100 -f | grep -E "Workflow|Message|Duplicate|Save"
```

---

## ✅ Critérios de Sucesso

1. **"Is New Message?" funciona corretamente**:
   - Array vazio → true (nova mensagem)
   - Array com resultado → false (duplicata)

2. **"Save Inbound Message" executa sem erros**:
   - Sem erro "Column 'success' does not exist"
   - Mensagem salva corretamente no banco

3. **Workflow completo executa até o fim**:
   - Webhook → Filter → Extract → Check → IsNew → Save → Trigger AI

---

## 📝 Lições Aprendidas

### Problemas Identificados
1. **autoMapInputData é perigoso**: Sempre usar mapeamento explícito de campos
2. **Verificação de arrays vazios**: Usar lógica booleana robusta, não isEmpty em undefined
3. **Propagação de dados no n8n**: Dados se acumulam através dos nós, causando problemas

### Melhores Práticas
1. **Sempre referenciar nós específicos**: Use `$node["Nome do Nó"].json`
2. **Validar estrutura de dados**: Verificar o que cada nó retorna
3. **Usar mapeamento explícito**: Especificar exatamente quais campos salvar
4. **Testar com dados reais**: Validar fluxo completo end-to-end

---

## 🆘 Suporte

**Documentação Relacionada**:
- `docs/PLAN/WORKFLOW_01_DIAGNOSTIC_PLAN.md` - Análise inicial
- `docs/PLAN/WORKFLOW_01_CORRECTION_SUMMARY.md` - Correções anteriores
- `scripts/test-workflow-01-e2e.sh` - Script de teste

**Comandos Úteis**:
```bash
# Verificar schema da tabela
docker exec e2bot-postgres-dev psql -U postgres -d e2_bot -c "\d messages"

# Contar mensagens
docker exec e2bot-postgres-dev psql -U postgres -d e2_bot -c "SELECT COUNT(*) FROM messages;"

# Ver logs detalhados
docker logs e2bot-n8n-dev --tail 200 -f
```

---

**Autor**: Claude Code SuperClaude
**Versão**: 2.0 - Análise Profunda
**Próximo Passo**: Executar correções com /sc:task