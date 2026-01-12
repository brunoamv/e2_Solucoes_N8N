# Correção do Workflow ID - Workflow 01

**Data**: 2025-12-30 21:15
**Problema Identificado**: Workflow 01 referencia ID "2" inexistente
**Solução**: Atualizar para ID correto do Workflow 02

---

## 🎯 Problema Identificado

### Análise dos Logs do n8n

Os logs mostram erro repetido:

```
21:03:05.376   debug   Running node "Trigger AI Agent" finished with error
21:03:05.376   debug   Workflow execution finished with error {
  "error": {
    "cause": {
      "name": "SubworkflowOperationError",
      "message": "Missing node to start execution"
    },
    "description": "Please make sure the workflow you're calling contains an Execute Workflow Trigger node"
  }
}
```

### Causa Raiz

**Workflow 01 (arquivo JSON)**:
```json
{
  "parameters": {
    "workflowId": "2",
    "options": {}
  },
  "id": "trigger-ai-agent",
  "name": "Trigger AI Agent",
  "type": "n8n-nodes-base.executeWorkflow"
}
```

❌ **Problema**: `"workflowId": "2"` não existe no n8n
✅ **IDs Reais**:
- Workflow 01 (WhatsApp Handler): `JD0hi3Z2B6sNhEm9`
- Workflow 02 (AI Agent): `xq3AP1QTtqj46SY3`

---

## 📋 Solução: Passos para Correção

### Passo 1: Abrir Workflow 01 no n8n

1. Acesse: http://localhost:5678
2. Clique em **"Workflows"** no menu lateral
3. Localize: **"01 - WhatsApp Handler FIXED v3"**
4. Clique para abrir o workflow

### Passo 2: Localizar o Node "Trigger AI Agent"

1. No canvas do workflow, procure o node: **"Trigger AI Agent"**
2. Ele está aproximadamente no meio do fluxo
3. Deve ter tipo: `Execute Workflow`

### Passo 3: Configurar o Workflow ID Correto

1. **Clique no node** "Trigger AI Agent"
2. No painel lateral direito, você verá:
   ```
   Workflow Selection
   ┌─────────────────────────────┐
   │ Source                       │
   │ ○ Database                   │  ← Esta opção deve estar selecionada
   │ ○ Parameter                  │
   │ ○ URL                        │
   └─────────────────────────────┘

   Workflow ID
   ┌─────────────────────────────┐
   │ 2                            │  ← VALOR INCORRETO
   └─────────────────────────────┘
   ```

3. **ALTERE** o campo "Workflow ID" de:
   - ❌ Valor Atual: `2`
   - ✅ Valor Novo: `xq3AP1QTtqj46SY3`

4. **Método alternativo** (se disponível):
   - Se houver dropdown de workflows, selecione: `02 - AI Agent Conversation`

### Passo 4: Salvar as Alterações

1. Clique no botão **"Save"** (verde, canto superior direito)
2. Confirme a mensagem: "Workflow saved successfully"

### Passo 5: Verificar que Workflow 02 está ATIVO

1. Volte para a lista de workflows: http://localhost:5678/workflows
2. Localize: **"02 - AI Agent Conversation"**
3. Verifique o toggle de ativação:
   - ✅ **Deve estar VERDE** com texto "Active"
   - ❌ Se estiver cinza/vermelho "Inactive", clique no toggle para ativar

4. Faça o mesmo para Workflow 01:
   - **"01 - WhatsApp Handler FIXED v3"** → deve estar **Active** (verde)

---

## ✅ Validação da Correção

### Teste 1: Verificar Configuração do Node

No n8n, abra Workflow 01 → clique em "Trigger AI Agent" → confirme:

```
Workflow Selection: Database
Workflow ID: xq3AP1QTtqj46SY3
```

### Teste 2: Teste End-to-End

1. **Do seu celular** (5561981755748), envie:
   ```
   Oi
   ```

2. **Aguarde 2-5 segundos**

3. **Resultado esperado**:
   ```
   Olá! Bem-vindo à E2 Soluções! 👋

   Escolha um serviço:
   1️⃣ Energia Solar
   2️⃣ Subestação
   3️⃣ Projetos Elétricos
   4️⃣ Armazenamento de Energia
   5️⃣ Análise e Laudos
   ```

### Teste 3: Verificar Logs do n8n

```bash
docker logs -f e2bot-n8n-dev
```

Envie "Oi" novamente e observe:

**✅ Logs esperados (BOM)**:
```
Received webhook POST whatsapp-evolution
Running node "Webhook WhatsApp" started
Running node "Filter Messages" started
Running node "Trigger AI Agent" started
Running node "Execute Workflow Trigger" started  ← Workflow 02 iniciou!
Running node "Get Conversation" started
Running node "Claude AI Agent" started
```

**❌ Logs de erro (RUIM)**:
```
Workflow does not exist. {"workflowId": "2"}
SubworkflowOperationError: Missing node to start execution
```

---

## 🔍 Debug: Se Ainda Não Funcionar

### Verificação 1: IDs dos Workflows

Confirme os IDs corretos via browser:

1. Workflow 01: http://localhost:5678/workflow/JD0hi3Z2B6sNhEm9
2. Workflow 02: http://localhost:5678/workflow/xq3AP1QTtqj46SY3

Se ambos os URLs abrirem corretamente, os IDs estão corretos.

### Verificação 2: Estado de Ativação

```bash
# Listar workflows e seus estados
curl -s http://localhost:5678/rest/workflows | python3 -m json.tool | grep -E '"id"|"name"|"active"'
```

Ambos devem ter `"active": true`.

### Verificação 3: Webhook Evolution API

```bash
source ./scripts/evolution-helper.sh
curl -s -X GET "http://localhost:8080/webhook/find/e2-solucoes-bot" \
  -H "apikey: $EVOLUTION_API_KEY" | python3 -m json.tool
```

Deve mostrar:
```json
{
  "url": "http://e2bot-n8n-dev:5678/webhook/whatsapp-evolution",
  "enabled": true
}
```

### Verificação 4: Conectividade Docker Network

```bash
# De dentro do container Evolution, testar acesso ao n8n
docker exec e2bot-evolution-dev ping -c 2 e2bot-n8n-dev

# Testar webhook endpoint
docker exec e2bot-n8n-dev wget -O- http://localhost:5678/webhook/whatsapp-evolution 2>&1 | grep -E "HTTP|404|200"
```

**Esperado**: `HTTP/1.1 200 OK` (webhook registrado e ativo)

---

## 📊 Resumo da Correção

| Item | Antes | Depois |
|------|-------|--------|
| **Webhook URL** | `http://n8n-dev:5678/...` | ✅ `http://e2bot-n8n-dev:5678/...` |
| **Workflow 01 ID** | Desconhecido | ✅ `JD0hi3Z2B6sNhEm9` |
| **Workflow 02 ID** | Desconhecido | ✅ `xq3AP1QTtqj46SY3` |
| **Trigger AI Agent → workflowId** | ❌ `"2"` | ✅ `"xq3AP1QTtqj46SY3"` |
| **Workflow 01 Status** | Desconhecido | ✅ Active (verde) |
| **Workflow 02 Status** | Desconhecido | ✅ Active (verde) |

---

## 🎯 Próximos Passos Após Correção

Após **confirmar que o teste E2E funciona**:

1. **Validar Sprint 1.1 (RAG)**:
   ```bash
   cat docs/validation/README.md
   ```

2. **Validar Sprint 1.2 (Agendamento)**:
   ```bash
   cat docs/validation/SPRINT_1.2_VALIDATION.md
   ```

3. **Executar testes completos**:
   ```bash
   ./scripts/test-v1-menu.sh --quick
   ```

---

**Criado por**: Claude Code - Análise Sistemática
**Referência**: Logs do n8n (execuções 2136 e 2137)
**Próximo**: Teste E2E após correção
