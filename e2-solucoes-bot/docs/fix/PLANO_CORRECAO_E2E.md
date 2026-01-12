# Plano de Correção: Teste End-to-End Não Funcionando

**Data**: 2025-12-30
**Problema**: Enviar mensagem "Oi" pelo WhatsApp não gera resposta do bot
**Status**: 🔍 Análise completa - 3 problemas identificados

---

## 📊 Diagnóstico

### ✅ O Que Está Funcionando
1. ✅ Evolution API conectada (`state: "open"`)
2. ✅ Bot consegue **enviar** mensagens (teste com `evolution_send` funcionou)
3. ✅ Webhook está configurado na Evolution API
4. ✅ n8n está rodando e healthy
5. ✅ PostgreSQL está rodando
6. ✅ Webhooks **estão sendo recebidos** pelo n8n (logs mostram "Received webhook POST")

### ❌ O Que NÃO Está Funcionando
1. ❌ **Webhook URL com hostname errado** (`n8n-dev` → deve ser `e2bot-n8n-dev`)
2. ❌ **Workflow ID "2" não existe** (Workflow 01 tenta chamar workflow inexistente)
3. ⚠️ **Campo `media_analysis` com tipo errado** (recebe URL ao invés de objeto)

---

## 🎯 Tarefas de Correção (Prioridade Alta)

### **Tarefa 1: Corrigir Webhook URL da Evolution API**
**Prioridade**: 🔴 CRÍTICA
**Tempo estimado**: 2 minutos
**Dependências**: Nenhuma

**Problema**:
```json
{
  "url": "http://n8n-dev:5678/webhook/whatsapp-evolution"
                 ^^^^^^^^
                 INCORRETO - Container n8n se chama "e2bot-n8n-dev"
}
```

**Solução**:
```bash
cd /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot

# Carregar helper com EVOLUTION_API_KEY
source ./scripts/evolution-helper.sh

# Reconfigurar webhook com hostname correto
curl -X POST "http://localhost:8080/webhook/set/e2-solucoes-bot" \
  -H "apikey: $EVOLUTION_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "webhook": {
      "url": "http://e2bot-n8n-dev:5678/webhook/whatsapp-evolution",
      "enabled": true,
      "webhook_by_events": false,
      "webhook_base64": false,
      "events": [
        "MESSAGES_UPSERT",
        "MESSAGES_UPDATE",
        "MESSAGES_DELETE",
        "SEND_MESSAGE",
        "CONNECTION_UPDATE"
      ]
    }
  }'
```

**Validação**:
```bash
# Verificar se hostname foi atualizado
curl -X GET "http://localhost:8080/webhook/find/e2-solucoes-bot" \
  -H "apikey: $EVOLUTION_API_KEY" | python3 -m json.tool

# Deve mostrar:
# "url": "http://e2bot-n8n-dev:5678/webhook/whatsapp-evolution"
```

**Impacto**: 🔴 **SEM ISSO, WEBHOOKS NÃO CHEGAM NO N8N**

---

### **Tarefa 2: Identificar Workflows Importados no n8n**
**Prioridade**: 🔴 CRÍTICA
**Tempo estimado**: 3 minutos
**Dependências**: Acesso ao n8n UI

**Problema**:
```
Error: Workflow does not exist. {"workflowId": "2"}
```

O Workflow 01 está configurado para chamar Workflow ID "2", mas este workflow não existe ou não foi importado.

**Solução**:

**Opção A: Via Browser (RECOMENDADO)**
1. Acessar: http://localhost:5678
2. Ir em **Workflows** (menu lateral)
3. Listar todos workflows e seus IDs
4. Anotar:
   - Nome: "01 - WhatsApp Handler" → ID: `_______`
   - Nome: "02 - AI Agent Conversation V1 (Menu-Based)" → ID: `_______`

**Opção B: Via API (se n8n tem autenticação básica desabilitada)**
```bash
# Listar workflows
curl -s http://localhost:5678/rest/workflows | python3 -m json.tool | grep -E '"id"|"name"'

# Resultado esperado:
# {
#   "id": "abc123...",
#   "name": "01 - WhatsApp Handler",
#   ...
# },
# {
#   "id": "def456...",
#   "name": "02 - AI Agent Conversation V1 (Menu-Based)",
#   ...
# }
```

**Documentar IDs encontrados**:
```
Workflow 01 (WhatsApp Handler): ID = __________
Workflow 02 (AI Agent V1 Menu): ID = __________
```

---

### **Tarefa 3: Corrigir Referências ao Workflow ID no Workflow 01**
**Prioridade**: 🔴 CRÍTICA
**Tempo estimado**: 5 minutos
**Dependências**: Tarefa 2 (precisa do ID correto do Workflow 02)

**Problema**:
No Workflow 01, o node "Trigger AI Agent" está configurado para chamar Workflow ID "2", mas este ID não existe.

**Solução**:

1. **Acesse o n8n**: http://localhost:5678
2. **Abra o Workflow 01**: "01 - WhatsApp Handler"
3. **Localize o node**: "Trigger AI Agent" (tipo "Execute Workflow")
4. **Clique no node** para abrir configurações
5. **Procure campo**: "Workflow to Execute" ou "Workflow ID"
6. **Verifique valor atual**: Provavelmente está "2" ou algum ID inválido
7. **Corrija para**: O ID real do Workflow 02 (obtido na Tarefa 2)
8. **Salve o node** (botão verde no canto superior direito do node)
9. **Salve o workflow** (botão "Save" no topo da página)

**Validação**:
- Após salvar, o node "Trigger AI Agent" não deve mostrar erros (ícone ⚠️)
- Executar teste manual do workflow deve funcionar

---

### **Tarefa 4: Verificar se Workflows Estão ATIVOS**
**Prioridade**: 🔴 CRÍTICA
**Tempo estimado**: 2 minutos
**Dependências**: Nenhuma

**Problema**:
Workflows **inativos** retornam HTTP 403 Forbidden quando recebem webhooks, e mensagens não são processadas.

**Solução**:

1. **Acesse**: http://localhost:5678/workflows
2. **Verifique cada workflow**:
   - "01 - WhatsApp Handler" → Toggle deve estar **verde** "Active"
   - "02 - AI Agent Conversation V1 (Menu-Based)" → Toggle deve estar **verde** "Active"
3. **Se algum estiver INATIVO** (toggle cinza/vermelho):
   - Clique no workflow
   - Clique no toggle "Inactive" → muda para "Active" (verde)
   - Salve

**Validação**:
```bash
# Ambos workflows devem estar ativos:
# http://localhost:5678/workflows
# Visual: Ambos com toggle verde e texto "Active"
```

**Impacto**: 🔴 **SEM ISSO, WEBHOOKS RETORNAM 403 E BOT NÃO RESPONDE**

---

### **Tarefa 5: Testar End-to-End**
**Prioridade**: 🟢 VALIDAÇÃO
**Tempo estimado**: 3 minutos
**Dependências**: Tarefas 1, 2, 3, 4 completas

**Teste**:

1. **Do seu celular**, envie mensagem para o número conectado:
   ```
   Oi
   ```

2. **Aguarde 2-5 segundos**

3. **Você DEVE receber**:
   ```
   Olá! Bem-vindo à E2 Soluções! 👋

   Escolha um serviço:
   1️⃣ Energia Solar
   2️⃣ Subestação
   3️⃣ Projetos Elétricos
   4️⃣ Armazenamento de Energia
   5️⃣ Análise e Laudos
   ```

**Se NÃO receber resposta**:

**Debug Step 1: Verificar logs do n8n**
```bash
# Ver execuções em tempo real
docker logs -f e2bot-n8n-dev
```

Envie "Oi" novamente e observe:
- ✅ **BOM**: "Received webhook POST whatsapp-evolution"
- ✅ **BOM**: "Running node 'Webhook WhatsApp' started"
- ✅ **BOM**: "Trigger AI Agent started"
- ❌ **RUIM**: "Workflow does not exist"
- ❌ **RUIM**: "404 Not Found"

**Debug Step 2: Verificar logs da Evolution API**
```bash
docker logs e2bot-evolution-dev --tail 50 | grep -iE "webhook|send|http"
```

Deve mostrar tentativas de envio de webhook para n8n.

**Debug Step 3: Verificar banco de dados**
```bash
docker exec e2bot-postgres-dev psql -U postgres -d e2_bot -c "SELECT * FROM messages ORDER BY created_at DESC LIMIT 5;"
```

Se mensagens aparecem, o Workflow 01 está funcionando (salvou no banco).
Se não aparecem, o webhook não está chegando ao n8n.

---

## ⚠️ Problema Secundário (Não Bloqueia E2E)

### **Tarefa 6 (OPCIONAL): Corrigir Campo media_analysis**
**Prioridade**: 🟡 BAIXA
**Tempo estimado**: 10 minutos
**Dependências**: Tarefa 5 funcionando

**Problema**:
```
'media_analysis' expects a object but we got 'https://mmg.whatsapp.net/...'
```

O node "Save Inbound Message2" no Workflow 01 tem um campo `media_analysis` esperando um objeto JSON, mas está recebendo uma string (URL de mídia).

**Impacto**:
- ⚠️ **Mensagens com mídia não são salvas** (erro no node PostgreSQL)
- ✅ **Mensagens de texto continuam funcionando** (workflow prossegue)

**Solução**:

1. Abrir Workflow 01 no n8n
2. Localizar node "Save Inbound Message2"
3. Verificar mapeamento do campo `media_analysis`
4. **Opção A**: Remover campo se não for usado
5. **Opção B**: Corrigir expressão para retornar objeto vazio `{}` quando não há mídia
6. **Opção C**: Criar node intermediário para transformar URL em objeto estruturado

**Validação**:
Enviar mensagem com foto pelo WhatsApp → não deve gerar erro nos logs do n8n.

---

## 📝 Checklist de Validação Final

Após completar Tarefas 1-5:

- [ ] Webhook URL corrigido para `http://e2bot-n8n-dev:5678/webhook/whatsapp-evolution`
- [ ] Workflow 01 ID identificado: `__________`
- [ ] Workflow 02 ID identificado: `__________`
- [ ] Workflow 01 node "Trigger AI Agent" atualizado com ID correto do Workflow 02
- [ ] Workflow 01 está **ATIVO** (toggle verde)
- [ ] Workflow 02 está **ATIVO** (toggle verde)
- [ ] Teste E2E: Enviar "Oi" → Receber menu com 5 opções
- [ ] Logs do n8n mostram execução bem-sucedida (sem erros)
- [ ] Mensagens aparecem no banco de dados PostgreSQL

---

## 🚀 Próximos Passos (Após E2E Funcionar)

1. **Sprint 0.1 Validação Completa**: Executar `docs/validation/SPRINT_0.1_VALIDATION.md`
2. **Sprint 1.1 Setup**: Configurar RAG com Supabase e embeddings
3. **Sprint 1.2 Testing**: Validar sistema de agendamento

---

## 📊 Resumo Executivo

**Status Atual**: Evolution API + n8n + PostgreSQL rodando, mas comunicação quebrada

**Problemas Críticos**:
1. 🔴 Webhook URL com hostname errado (n8n-dev → e2bot-n8n-dev)
2. 🔴 Workflow ID "2" não existe (referência inválida)
3. 🔴 Workflows podem estar inativos (toggle vermelho/cinza)

**Tempo Total Estimado**: 15-20 minutos para correção completa

**Prioridade de Execução**:
```
Tarefa 1 (Webhook URL)
   ↓
Tarefa 4 (Ativar Workflows)
   ↓
Tarefa 2 (Identificar IDs)
   ↓
Tarefa 3 (Corrigir Referência)
   ↓
Tarefa 5 (Teste E2E)
```

---

**Criado por**: Claude Code - Análise Sistemática
**Comando usado**: `/sc:analyze`
**Próximo passo**: `/sc:task` para execução automatizada
