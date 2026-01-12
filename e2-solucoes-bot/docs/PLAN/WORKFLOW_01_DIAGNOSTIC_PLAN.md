# Plano de Diagnóstico e Correção: Workflow 01 - WhatsApp Handler (FIXED v5)

**Data**: 2025-01-05
**Status**: ANÁLISE COMPLETA - PRONTO PARA EXECUÇÃO
**Workflow**: `/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/01 - WhatsApp Handler (FIXED v5).json`
**Problema**: Workflow para no nó "Check Duplicate" após executar "Extract Message Data"

---

## 🔍 DIAGNÓSTICO COMPLETO

### Análise dos Logs

```
19:15:03.589   Workflow execution started
19:15:03.590   Start executing node "Filter Messages"
19:15:03.590   Running node "Filter Messages" started
19:15:03.591   Running node "Filter Messages" finished successfully
19:15:03.591   Start executing node "Extract Message Data"
19:15:03.591   Running node "Extract Message Data" started
19:15:03.604   Running node "Extract Message Data" finished successfully
19:15:03.646   Workflow execution finished successfully ❌ PARA AQUI
```

**Observação Crítica**: O nó "Check Duplicate" NUNCA é executado. O workflow termina imediatamente após "Extract Message Data".

---

## 🎯 PROBLEMAS IDENTIFICADOS (Ordem de Gravidade)

### 1️⃣ PROBLEMA CRÍTICO: Condição Inválida no Nó "Is New Message?"

**Localização**: Linhas 118-126 do workflow JSON

```json
{
  "id": "c0f87358-6ef9-460b-9257-ae5c426f8b5a",
  "leftValue": "",          ❌ VAZIO
  "rightValue": "",         ❌ VAZIO
  "operator": {
    "type": "string",
    "operation": "equals",
    "name": "filter.operator.equals"
  }
}
```

**Impacto**: Esta condição vazia no array de condições quebra a lógica do nó "Is New Message?", impedindo que o workflow processe mensagens corretamente após o Check Duplicate.

**Evidência**: Comparando com o workflow funcional `01_main_whatsapp_handler.json`, este nó deveria ter APENAS UMA condição (verificar se id está vazio), não duas.

---

### 2️⃣ PROBLEMA DE CONFIGURAÇÃO: Credencial PostgreSQL

**Localização**: Linha 93-94 do workflow JSON

```json
"credentials": {
  "postgres": {
    "id": "VXA1r8sd0TMIdPvS",
    "name": "PostgreSQL - E2 Bot"
  }
}
```

**Possíveis Causas**:
- Credencial não configurada no n8n
- Credencial configurada mas inativa/inválida
- Problemas de conexão com o banco PostgreSQL

**Como Verificar**: Acessar n8n UI → Credentials → Verificar se "PostgreSQL - E2 Bot" está ativa

---

### 3️⃣ PROBLEMA DE SINTAXE: Query SQL com Template Incorreto

**Localização**: Linha 80 do workflow JSON

```sql
SELECT id FROM messages WHERE whatsapp_message_id = '{{ $json.message_id }}'
```

**Análise**:
- Sintaxe n8n correta: `{{ $json.message_id }}`
- Query está usando aspas simples dentro do template
- Pode causar problemas se message_id contiver caracteres especiais

**Sintaxe Recomendada**:
```sql
SELECT id FROM messages WHERE whatsapp_message_id = {{ $json.message_id }}
```

Ou usar parâmetros seguros do n8n (se disponível na versão).

---

### 4️⃣ PROBLEMA DE FLUXO: Código JavaScript no Extract Message Data

**Localização**: Linha 66-67 do workflow JSON

```javascript
const body = $input.item.json.body || {};
const data = body.data || {};
```

**Análise**:
- Código usa fallback `|| {}` para evitar erros
- Retorna objeto válido mesmo quando dados não existem
- **NÃO é a causa raiz** do problema atual
- **MAS**: Pode causar processamento de mensagens vazias

**Melhoria Recomendada**:
```javascript
// Validar dados ANTES de processar
const body = $input.item.json.body;
if (!body || !body.data || !body.data.message) {
  throw new Error('Dados inválidos recebidos do webhook');
}

const data = body.data;
const message = data.message;
const key = data.key;
// ... resto do código
```

---

## 🔧 PLANO DE CORREÇÃO (Ordem de Execução)

### Fase 1: Validação de Infraestrutura (5 min)

**Objetivo**: Garantir que serviços e credenciais estão funcionais

```bash
# 1.1 Verificar status dos containers
cd /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot
docker ps | grep -E 'postgres|n8n'

# 1.2 Testar conexão PostgreSQL
docker exec -it e2bot-postgres-dev psql -U e2bot_user -d e2bot_db -c "SELECT COUNT(*) FROM messages;"

# 1.3 Verificar tabela messages existe
docker exec -it e2bot-postgres-dev psql -U e2bot_user -d e2bot_db -c "\d messages"
```

**Resultado Esperado**:
- ✅ Containers rodando
- ✅ Conexão PostgreSQL OK
- ✅ Tabela messages existe com coluna whatsapp_message_id

**Se Falhar**:
- Executar `./scripts/start-dev.sh`
- Executar schema: `docker exec -i e2bot-postgres-dev psql -U e2bot_user -d e2bot_db < database/schema.sql`

---

### Fase 2: Correção do Workflow JSON (15 min)

**Objetivo**: Corrigir problemas no arquivo JSON do workflow

#### 2.1 Backup do Workflow Atual

```bash
cp "n8n/workflows/01 - WhatsApp Handler (FIXED v5).json" \
   "n8n/workflows/01 - WhatsApp Handler (FIXED v5).json.backup-$(date +%Y%m%d-%H%M%S)"
```

#### 2.2 Corrigir Nó "Is New Message?"

**Localização**: Linhas 99-140

**Substituir**:
```json
{
  "parameters": {
    "conditions": {
      "options": {
        "caseSensitive": true,
        "leftValue": "",
        "typeValidation": "strict",
        "version": 1
      },
      "conditions": [
        {
          "id": "14ffcedc-76c1-4cfe-bb85-c5632b86ec18",
          "leftValue": "={{ $input.all()[0].json.id }}",
          "rightValue": "",
          "operator": {
            "type": "any",
            "operation": "isEmpty"
          }
        }
      ],
      "combinator": "and"
    },
    "options": {}
  },
  "id": "7907ea4f-cbed-4d09-ac1e-750ec0bcc482",
  "name": "Is New Message?",
  "type": "n8n-nodes-base.if",
  "typeVersion": 2,
  "position": [-608, 208]
}
```

**REMOVER**: A segunda condição vazia (id: c0f87358-6ef9-460b-9257-ae5c426f8b5a)

#### 2.3 Corrigir Query SQL no Check Duplicate

**Localização**: Linha 80

**Opção 1 - Manter Template Simples**:
```json
"query": "=SELECT id FROM messages WHERE whatsapp_message_id = {{ $json.message_id ? \"'\" + $json.message_id + \"'\" : \"NULL\" }}"
```

**Opção 2 - Usar Expressão Segura (RECOMENDADO)**:
```json
"query": "=SELECT id FROM messages WHERE whatsapp_message_id = '{{ $json.message_id.replace(/'/g, \"''\") }}'"
```

#### 2.4 Melhorar Código Extract Message Data (OPCIONAL)

**Localização**: Linhas 66-67

**Adicionar Validação**:
```javascript
// Extract message data from Evolution API webhook
const inputData = $input.item.json;

// Validate required structure
if (!inputData.body || !inputData.body.data) {
  throw new Error('Invalid webhook payload: missing body.data');
}

const body = inputData.body;
const data = body.data;

if (!data.message || !data.key) {
  throw new Error('Invalid webhook payload: missing message or key');
}

const message = data.message;
const key = data.key;

// Extract relevant fields (resto do código permanece igual)
const output = {
  phone_number: key.remoteJid ? key.remoteJid.replace('@s.whatsapp.net', '') : '',
  // ... resto dos campos
};

return output;
```

---

### Fase 3: Validação das Credenciais n8n (10 min)

**Objetivo**: Garantir que credencial PostgreSQL está configurada corretamente

#### 3.1 Acessar n8n UI

```bash
# URL: http://localhost:5678
# Login com credenciais do .env.dev
```

#### 3.2 Verificar Credencial PostgreSQL

1. Menu → Credentials
2. Buscar por "PostgreSQL - E2 Bot"
3. Verificar configuração:
   - **Host**: `e2bot-postgres-dev` (nome do container)
   - **Database**: `e2bot_db`
   - **User**: `e2bot_user`
   - **Password**: (conforme .env.dev)
   - **Port**: `5432`
   - **SSL**: Disabled (dev environment)

#### 3.3 Testar Conexão

1. Abrir credencial
2. Clicar em "Test connection"
3. Verificar sucesso

**Se Falhar**:
- Verificar variáveis de ambiente no .env.dev
- Recriar credencial com dados corretos
- **Anotar novo ID da credencial** para atualizar no workflow JSON

---

### Fase 4: Reimportação do Workflow Corrigido (5 min)

**Objetivo**: Aplicar correções no n8n

#### 4.1 Método Automático (via API)

```bash
# Script de reimportação
./scripts/reimport-workflow-01.sh
```

**Conteúdo do script**:
```bash
#!/bin/bash
WORKFLOW_FILE="n8n/workflows/01 - WhatsApp Handler (FIXED v5).json"
N8N_URL="http://localhost:5678"
WORKFLOW_ID="Xd7D60MVRs8M9nQS"

# Atualizar workflow via API n8n
curl -X PATCH "${N8N_URL}/api/v1/workflows/${WORKFLOW_ID}" \
  -H "Content-Type: application/json" \
  --data @"${WORKFLOW_FILE}"
```

#### 4.2 Método Manual (via UI)

1. Acessar n8n: http://localhost:5678
2. Abrir workflow "01 - WhatsApp Handler (FIXED v5)"
3. Menu → Settings → Import from File
4. Selecionar arquivo JSON corrigido
5. Confirmar substituição
6. **Salvar** e **Ativar** workflow

---

### Fase 5: Teste End-to-End (15 min)

**Objetivo**: Validar que workflow processa mensagens corretamente

#### 5.1 Teste Manual via Webhook

```bash
# Simular webhook do Evolution API
curl -X POST http://localhost:5678/webhook/whatsapp-evolution \
  -H "Content-Type: application/json" \
  -d '{
    "event": "messages.upsert",
    "data": {
      "key": {
        "remoteJid": "5562999999999@s.whatsapp.net",
        "fromMe": false,
        "id": "TEST_MESSAGE_001"
      },
      "pushName": "Teste Usuario",
      "message": {
        "conversation": "Olá, gostaria de informações sobre energia solar"
      }
    }
  }'
```

#### 5.2 Verificar Execução no n8n

1. Acessar n8n UI → Executions
2. Verificar última execução
3. Confirmar que TODOS os nós executaram:
   - ✅ Webhook WhatsApp
   - ✅ Filter Messages
   - ✅ Extract Message Data
   - ✅ Check Duplicate ← **DEVE EXECUTAR AGORA**
   - ✅ Is New Message?
   - ✅ Save Inbound Message
   - ✅ Trigger AI Agent

#### 5.3 Verificar Dados no Banco

```bash
# Verificar mensagem foi salva
docker exec -it e2bot-postgres-dev psql -U e2bot_user -d e2bot_db -c "
  SELECT id, direction, content, message_type, whatsapp_message_id, created_at
  FROM messages
  WHERE whatsapp_message_id = 'TEST_MESSAGE_001';
"
```

**Resultado Esperado**:
```
                  id                  | direction |                content                | message_type | whatsapp_message_id |         created_at
--------------------------------------+-----------+--------------------------------------+--------------+---------------------+----------------------------
 a1b2c3d4-e5f6-... | inbound   | Olá, gostaria de informações... | text         | TEST_MESSAGE_001    | 2025-01-05 19:30:15.123456
```

#### 5.4 Teste de Duplicação

```bash
# Enviar MESMA mensagem novamente
curl -X POST http://localhost:5678/webhook/whatsapp-evolution \
  -H "Content-Type: application/json" \
  -d '{
    "event": "messages.upsert",
    "data": {
      "key": {
        "remoteJid": "5562999999999@s.whatsapp.net",
        "fromMe": false,
        "id": "TEST_MESSAGE_001"
      },
      "pushName": "Teste Usuario",
      "message": {
        "conversation": "Olá, gostaria de informações sobre energia solar"
      }
    }
  }'
```

**Resultado Esperado**:
- Workflow executa até "Is New Message?"
- Detecta duplicata (id NÃO está vazio)
- Retorna resposta via "Response Duplicate"
- **NÃO salva mensagem novamente** no banco

```bash
# Verificar que há apenas UMA mensagem no banco
docker exec -it e2bot-postgres-dev psql -U e2bot_user -d e2bot_db -c "
  SELECT COUNT(*) FROM messages WHERE whatsapp_message_id = 'TEST_MESSAGE_001';
"
# Deve retornar: count = 1
```

---

## 📋 CHECKLIST DE VALIDAÇÃO

### Pré-Requisitos
- [ ] Containers Docker rodando (postgres, n8n)
- [ ] Banco de dados PostgreSQL acessível
- [ ] Tabela `messages` criada com schema correto
- [ ] Credencial PostgreSQL configurada no n8n

### Correções Aplicadas
- [ ] Backup do workflow original criado
- [ ] Condição vazia removida do nó "Is New Message?"
- [ ] Query SQL corrigida no nó "Check Duplicate"
- [ ] (Opcional) Validação adicionada ao Extract Message Data
- [ ] Workflow reimportado no n8n
- [ ] Workflow ativado no n8n

### Testes Executados
- [ ] Teste 1: Mensagem nova é processada e salva no banco
- [ ] Teste 2: Nó "Check Duplicate" executa sem erros
- [ ] Teste 3: Mensagem duplicada é detectada e NÃO é salva
- [ ] Teste 4: Workflow completo executa até "Trigger AI Agent"
- [ ] Teste 5: Verificação manual dos dados no PostgreSQL

---

## 🐛 TROUBLESHOOTING

### Problema: Check Duplicate ainda não executa

**Diagnóstico**:
```bash
# Ver logs do n8n
docker logs e2bot-n8n-dev --tail 100 -f
```

**Possíveis Causas**:
1. Credencial PostgreSQL inválida → Reconfigurar credencial
2. Query SQL com erro de sintaxe → Revisar linha 80 do JSON
3. Conexão entre nós quebrada → Verificar seção "connections" do JSON

**Solução**: Recriar nó "Check Duplicate" manualmente no n8n UI

---

### Problema: Credencial PostgreSQL não conecta

**Diagnóstico**:
```bash
# Testar conexão direta
docker exec -it e2bot-n8n-dev ping e2bot-postgres-dev
docker exec -it e2bot-postgres-dev psql -U e2bot_user -d e2bot_db -c "SELECT 1;"
```

**Possíveis Causas**:
1. Containers em redes diferentes
2. Senha incorreta no .env.dev
3. PostgreSQL não aceitando conexões externas

**Solução**:
```bash
# Recriar network se necessário
docker network create e2bot-network
docker network connect e2bot-network e2bot-postgres-dev
docker network connect e2bot-network e2bot-n8n-dev
```

---

### Problema: Mensagem não tem message_id

**Diagnóstico**: Verificar payload do webhook no n8n Executions

**Causa**: Evolution API pode enviar estrutura diferente em alguns tipos de mensagem

**Solução**: Adicionar validação no Extract Message Data:
```javascript
const message_id = key.id || `generated_${Date.now()}_${Math.random()}`;
```

---

## 📊 MÉTRICAS DE SUCESSO

### Critérios de Aceitação

1. **Fluxo Completo**: Workflow executa TODOS os nós sem parar no Check Duplicate
2. **Detecção de Duplicatas**: Mensagens com mesmo whatsapp_message_id NÃO são salvas 2x
3. **Performance**: Query no Check Duplicate executa em <50ms
4. **Logs Limpos**: Sem erros no docker logs do n8n
5. **Dados Corretos**: Mensagens aparecem na tabela `messages` com todos os campos

### Métricas Observáveis

```sql
-- Verificar mensagens processadas
SELECT
  DATE(created_at) as data,
  COUNT(*) as total_mensagens,
  COUNT(DISTINCT whatsapp_message_id) as mensagens_unicas
FROM messages
GROUP BY DATE(created_at)
ORDER BY data DESC;

-- Verificar duplicatas (não deveria haver)
SELECT
  whatsapp_message_id,
  COUNT(*) as qtd
FROM messages
GROUP BY whatsapp_message_id
HAVING COUNT(*) > 1;
```

---

## 🚀 PRÓXIMOS PASSOS APÓS CORREÇÃO

1. **Validar Workflow 02**: Testar integração com AI Agent
2. **Monitorar Logs**: Observar comportamento em produção por 24h
3. **Otimizar Query**: Adicionar índice em whatsapp_message_id se não existir
4. **Documentar**: Atualizar docs/PROJECT_STATUS.md com status da correção
5. **Criar Testes**: Script automatizado para validação do workflow

---

## 📝 NOTAS FINAIS

- **Tempo Estimado Total**: 50 minutos
- **Prioridade**: CRÍTICA (workflow está quebrado em produção)
- **Risco**: BAIXO (correções são estruturais, não afetam lógica de negócio)
- **Rollback**: Backup automático criado, fácil reverter se necessário

**Autor**: Claude Code SuperClaude Analysis
**Data Análise**: 2025-01-05 19:20:00
**Versão**: 1.0
