# Diagnóstico Webhook - Heartbeat vs Mensagens

**Data**: 2026-01-02 18:30
**Status**: ✅ Diagnóstico completo | ⏳ Aguardando teste com filtro desabilitado

---

## 🔍 Descoberta Crítica

### O que você relatou:
> "mensagem nao chegar no webhook"

### O que está realmente acontecendo:
✅ **Webhooks ESTÃO chegando** - Evolution envia requisições POST a cada ~10 segundos
✅ **Workflow 01 executa com sucesso** - Node "Webhook WhatsApp" completa sem erros
❌ **Workflow termina após "Filter Messages"** - Próximos nodes nunca executam

### Por que isso acontece:
Esses webhooks que chegam a cada 10 segundos são **heartbeats/keepalive do Evolution API**, NÃO são mensagens de WhatsApp.

---

## 📊 Análise dos Logs

### Padrão Observado (repetido a cada 10s):
```
18:09:27.423   debug   Received webhook "POST" for path "whatsapp-evolution"
18:09:27.447   debug   Running node "Webhook WhatsApp" started
18:09:27.447   debug   Running node "Webhook WhatsApp" finished successfully (20-25ms)
18:09:27.447   debug   Start executing node "Filter Messages"
18:09:27.447   debug   Running node "Filter Messages" finished successfully
18:09:27.447   debug   Workflow execution finished successfully
[WORKFLOW TERMINA - Nenhum node posterior executado]
```

### O que isso significa:
1. ✅ Evolution envia heartbeat → n8n recebe
2. ✅ "Webhook WhatsApp" node processa payload vazio/heartbeat
3. ✅ "Filter Messages" **CORRETAMENTE** bloqueia (não é evento `messages.upsert`)
4. ✅ Workflow termina com "sucesso" porque filtrou corretamente
5. ❌ Quando você envia "oi" do WhatsApp, a mensagem REAL **deveria** passar pelo filtro

---

## 🎯 Root Cause Analysis

### Hipótese #1: Filtro está funcionando corretamente
**Configuração atual do filtro** (`01_main_whatsapp_handler.json` linha 23):
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

**Comportamento esperado**:
- Heartbeats do Evolution: `$json.body.event` **≠** "messages.upsert" → Workflow termina ✅
- Mensagens do WhatsApp: `$json.body.event` **===** "messages.upsert" → Workflow continua ✅

**Problema**: Não sabemos se você testou enviar uma mensagem REAL do WhatsApp desde que o webhook foi corrigido.

### Hipótese #2: Payload do Evolution tem estrutura diferente
**Possibilidade**: Evolution API v2.2.3 pode enviar eventos com caminho diferente:
- ❌ `$json.body.event` (esperado pelo filtro)
- ✅ `$json.event` (caminho real?)
- ✅ `$json.data.event` (caminho real?)
- ✅ Outro formato completamente diferente

---

## ✅ Solução Aplicada: Desabilitar Filtro Temporariamente

### Modificação feita:
**Arquivo**: `/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/01_main_whatsapp_handler.json`

**ANTES** (linha 23):
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

**AGORA** (DEBUG):
```json
{
  "conditions": {
    "boolean": [{
      "value1": true,
      "value2": true
    }]
  }
}
```

**Resultado**: Filtro sempre passa (`true === true`) - **TODOS** os webhooks vão executar os próximos nodes.

---

## 📋 Plano de Teste

### Teste #1: Verificar se workflow continua com filtro desabilitado
**Objetivo**: Confirmar que o problema é APENAS o filtro, não a estrutura do workflow

**Passos**:
1. Reimportar `01_main_whatsapp_handler.json` no n8n (instruções no script)
2. Aguardar próximo heartbeat (10s)
3. Verificar logs: agora DEVE executar "Extract Message Data" e demais nodes
4. Observar erro no "Extract Message Data" (esperado - payload de heartbeat não tem estrutura de mensagem)

**Resultado esperado**:
```
✅ Workflow WhatsApp Started
✅ Filter Messages (PASSA - filtro desabilitado)
❌ Extract Message Data (ERRO - heartbeat não tem $json.body.data)
```

### Teste #2: Enviar mensagem real "oi" do WhatsApp
**Objetivo**: Ver payload completo de uma mensagem REAL

**Passos**:
1. Com filtro desabilitado, enviar "oi" do seu WhatsApp
2. Ver execução em http://localhost:5678/home/executions
3. Clicar na execução
4. Ver JSON completo em node "Webhook WhatsApp"
5. Identificar caminho correto de `event` no payload

**Resultado esperado**:
```json
{
  "body": {
    "event": "messages.upsert",  // OU
    "data": {
      "event": "messages.upsert",  // OU
      ...
    }
  },
  "event": "messages.upsert",  // OU outro caminho
  ...
}
```

### Teste #3: Corrigir filtro com caminho correto
**Objetivo**: Restaurar filtro com caminho real do payload Evolution

**Passos**:
1. Identificar caminho correto do `event` no payload (Teste #2)
2. Editar `01_main_whatsapp_handler.json` linha 23
3. Ajustar `value1` para caminho correto
4. Reimportar workflow
5. Testar novamente com "oi"

**Exemplo de correção**:
```json
// Se event está em $json.event (raiz):
"value1": "={{ $json.event }}"

// Se event está em $json.data.event:
"value1": "={{ $json.data.event }}"

// Se event está em outro lugar:
"value1": "={{ $json.body.data.event }}"
```

---

## 🔧 Scripts Criados

### `/scripts/reimport-workflow-01.sh`
**Função**: Instruções para reimportar workflow 01 modificado no n8n
**Uso**: `./scripts/reimport-workflow-01.sh`

**Saída**:
```
📋 Workflow 01 modificado está pronto para reimport
📂 Arquivo: .../01_main_whatsapp_handler.json
🔧 Modificação: Filtro DESABILITADO (sempre passa)
⚠️  IMPORTANTE: Use apenas para DEBUG
📝 PRÓXIMOS PASSOS: [instruções detalhadas]
```

---

## 🚨 IMPORTANTE: Filtro Desabilitado É Temporário

### ⚠️ Consequências do filtro desabilitado:
1. **Todos os heartbeats** (a cada 10s) vão executar workflow completo
2. **Tentará processar heartbeats** como mensagens → erros esperados
3. **Alta carga no banco de dados** → tentativas de salvar heartbeats
4. **Logs poluídos** → dezenas de execuções por minuto

### ✅ Uso correto:
- **Apenas para DEBUG** durante 5-10 minutos
- **Executar Teste #1 e Teste #2** rapidamente
- **Restaurar filtro correto** assim que identificar caminho do `event`

---

## 📊 Status Evolution API

### Conexão WhatsApp:
```bash
$ curl http://localhost:8080/instance/connectionState/e2-solucoes-bot \
  -H "apikey: ae569043cfa169380c378347f91a1141ea572541d2d1cadbed222db519c8a891"

{
  "instance": {
    "instanceName": "e2-solucoes-bot",
    "state": "open"  ✅ CONECTADO
  }
}
```

### Webhook Global:
```yaml
WEBHOOK_GLOBAL_URL: http://e2bot-n8n-dev:5678/webhook/whatsapp-evolution  ✅ CORRETO
WEBHOOK_GLOBAL_ENABLED: true  ✅ ATIVO
WEBHOOK_EVENTS_MESSAGES_UPSERT: true  ✅ EVENTO CONFIGURADO
```

---

## 🎯 Próximos Passos (URGENTE)

### 1️⃣ Reimportar workflow com filtro desabilitado
```bash
./scripts/reimport-workflow-01.sh
# Seguir instruções no output
```

### 2️⃣ Aguardar próximo heartbeat (10s)
```bash
# Monitorar logs
docker logs -f e2bot-n8n-dev 2>&1 | grep -E "Extract Message Data|Check Duplicate"
```

### 3️⃣ Enviar "oi" do WhatsApp
- Enviar mensagem do seu telefone para o número conectado
- Abrir http://localhost:5678/home/executions
- Clicar na execução
- Ver payload completo

### 4️⃣ Identificar caminho correto do event
- No payload JSON, encontrar onde está `"event": "messages.upsert"`
- Anotar o caminho completo (ex: `$json.body.event` ou `$json.event`)

### 5️⃣ Restaurar filtro com caminho correto
- Editar `01_main_whatsapp_handler.json` linha 23
- Ajustar `value1` para caminho correto
- Reimportar workflow

### 6️⃣ Testar mensagem novamente
- Enviar "oi" novamente
- Verificar se workflow 02 é chamado
- Confirmar resposta do bot no WhatsApp

---

## 📚 Documentação Relacionada

- **Diagnóstico Anterior**: `DIAGNOSTICO_WORKFLOW.md` (documentou problema original)
- **Pipeline Evolution**: `docs/EVOLUTION_QRCODE_PIPELINE.md` (como gerar QR Code)
- **Solução Webhook**: `SOLUCAO_WEBHOOK.md` (correção do webhook URL)
- **Resumo Completo**: `RESUMO_SOLUCAO_COMPLETA.md` (todas as soluções aplicadas)

---

**Conclusão**: Os webhooks ESTÃO chegando corretamente. O problema NÃO é delivery, é o filtro bloqueando corretamente heartbeats mas possivelmente também bloqueando mensagens reais (se caminho do `event` estiver incorreto no filtro).
