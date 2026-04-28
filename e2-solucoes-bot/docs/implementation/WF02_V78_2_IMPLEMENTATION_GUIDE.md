# WF02 V78.2 - Guia de Implementação Completo

> **Versão**: V78.2 FINAL
> **Data**: 2026-04-13
> **Correção Crítica**: Switch Node v3 'conditions' structure
> **Tempo Estimado**: 30-45 minutos (import + config + testes)

---

## 📋 Índice

1. [Pré-Requisitos](#pré-requisitos)
2. [Análise da Correção](#análise-da-correção)
3. [Importação do Workflow](#importação-do-workflow)
4. [Validação da Configuração](#validação-da-configuração)
5. [Testes End-to-End](#testes-end-to-end)
6. [Troubleshooting](#troubleshooting)
7. [Rollback](#rollback)

---

## 🎯 Pré-Requisitos

### Serviços Ativos

```bash
# 1. Verificar containers
docker ps | grep -E "e2bot-n8n-dev|e2bot-postgres-dev|e2bot-evolution-dev"

# Esperado: 3 containers RUNNING
# e2bot-n8n-dev         Up X minutes   0.0.0.0:5678->5678/tcp
# e2bot-postgres-dev    Up X minutes   5432/tcp
# e2bot-evolution-dev   Up X minutes   0.0.0.0:8080->8080/tcp

# 2. Verificar WF06 ativo
curl -s http://localhost:5678/webhook/calendar-availability \
  -H "Content-Type: application/json" \
  -d '{"action":"next_dates","count":3}' | jq

# Esperado: {"success":true,"dates":[...]}
```

### Arquivos Necessários

```bash
# Validar presença dos arquivos
ls -lh n8n/workflows/02_ai_agent_conversation_V78_2_FINAL.json
ls -lh scripts/generate-workflow-wf02-v78_2-final.py
ls -lh scripts/wf02-v78-state-machine.js

# Verificar tamanho do workflow
cat n8n/workflows/02_ai_agent_conversation_V78_2_FINAL.json | jq '.nodes | length'
# Esperado: 37
```

---

## 🔍 Análise da Correção

### O Que Mudou de V78.1.6 → V78.2

#### Switch Node Structure (CRÍTICO)

**❌ V78.1.6 (ERRADO):**
```json
{
  "parameters": {
    "mode": "rules",
    "output": "multipleOutputs",
    "rules": {
      "rules": [
        {
          "expression": "={{ $json.next_stage === 'trigger_wf06_next_dates' }}",
          "outputIndex": 0
        }
      ]
    },
    "fallbackOutput": 2
  },
  "typeVersion": 3
}
```
**Problema**: Estrutura `mode/rules` é do Switch v3.4+, incompatível com n8n 2.15.0

**✅ V78.2 (CORRETO):**
```json
{
  "parameters": {
    "conditions": {
      "options": {
        "combineOperation": "any"
      },
      "conditions": [
        {
          "id": "uuid-generated",
          "leftValue": "={{ $json.next_stage }}",
          "rightValue": "trigger_wf06_next_dates",
          "operator": {
            "type": "string",
            "operation": "equals"
          }
        },
        {
          "id": "uuid-generated",
          "leftValue": "={{ $json.next_stage }}",
          "rightValue": "trigger_wf06_available_slots",
          "operator": {
            "type": "string",
            "operation": "equals"
          }
        }
      ]
    }
  },
  "typeVersion": 3
}
```
**Solução**: Estrutura `conditions` do Switch v3.0 (provada funcional em workflows existentes)

#### Por Que Funciona Agora?

1. **Estrutura Correta**: Baseada em workflows FUNCIONAIS (`09_rdstation_webhook_handler.json`)
2. **Compatibilidade**: n8n 2.15.0 reconhece `conditions` como estrutura v3.0 válida
3. **Outputs Implícitos**: Switch v3 com `conditions` cria automaticamente:
   - Output 0: Primeira condição (`next_stage === 'trigger_wf06_next_dates'`)
   - Output 1: Segunda condição (`next_stage === 'trigger_wf06_available_slots'`)
   - Output 2: Fallback (nenhuma condição satisfeita)

---

## 📥 Importação do Workflow

### Passo 1: Backup V74 (Se Necessário)

```bash
# V74.1_2 JÁ EXISTE como fallback
# Não precisa fazer backup adicional
# Arquivo: n8n/workflows/02_ai_agent_conversation_V74.1_2_FUNCIONANDO.json
```

### Passo 2: Abrir n8n

```bash
# 1. Acessar n8n
http://localhost:5678

# 2. Login (se necessário)
# Usuário: (configurado anteriormente)
```

### Passo 3: Import Workflow

1. **Menu**: Workflows → Import from File
2. **Selecionar**: `n8n/workflows/02_ai_agent_conversation_V78_2_FINAL.json`
3. **Aguardar**: Upload e parsing

**✅ SUCESSO ESPERADO:**
```
Workflow imported successfully
Name: 02_ai_agent_conversation_V78_2_FINAL
Nodes: 37
```

**❌ SE ERRO "Could not find property option":**
- **ATENÇÃO**: Significa que a correção NÃO funcionou
- **Ação**: Consultar seção [Troubleshooting](#troubleshooting)
- **Rollback**: Reativar V74 imediatamente

### Passo 4: Primeira Validação

```bash
# No n8n UI, verificar:
1. Workflow aparece na lista
2. Abrir workflow
3. Visualizar canvas com 37 nós
4. Nós não devem ter ícones de erro vermelho
```

---

## ✅ Validação da Configuração

### Validação 1: Switch Node

1. **Abrir nó**: "Route Based on Stage"

2. **Verificar Parameters**:
   - **Conditions**: Deve mostrar 2 condições
   - **Condition 1**:
     - Left Value: `{{ $json.next_stage }}`
     - Operation: `equals`
     - Right Value: `trigger_wf06_next_dates`
   - **Condition 2**:
     - Left Value: `{{ $json.next_stage }}`
     - Operation: `equals`
     - Right Value: `trigger_wf06_available_slots`

3. **Verificar Outputs**:
   - **Node Canvas**: Deve mostrar **3 saídas** (outputs 0, 1, 2)
   - **Conexões**:
     - Output 0 → "HTTP Request - Get Next Dates"
     - Output 1 → "HTTP Request - Get Available Slots"
     - Output 2 → 5 nós paralelos

**✅ SUCESSO**: Switch mostra 3 outputs com conexões corretas
**❌ PROBLEMA**: Se mostra 4+ outputs ou conexões erradas, consultar [Troubleshooting](#troubleshooting)

### Validação 2: HTTP Request - Get Next Dates

1. **Abrir nó**: "HTTP Request - Get Next Dates"

2. **Verificar Configuração**:
   - **Method**: POST
   - **URL**: `http://e2bot-n8n-dev:5678/webhook/calendar-availability`
   - **Send Headers**: ✅ Enabled
     - Content-Type: `application/json`
   - **Send Body**: ✅ Enabled
   - **Body Parameters**:
     - `action` = `next_dates`
     - `count` = `3`
     - `start_date` = `{{ new Date().toISOString().split('T')[0] }}`
     - `duration_minutes` = `120`

3. **Verificar Conexões**:
   - **Input**: De "Route Based on Stage" (Output 0)
   - **Output**: Para "State Machine Logic"

**✅ SUCESSO**: Configuração completa e conexões corretas

### Validação 3: HTTP Request - Get Available Slots

1. **Abrir nó**: "HTTP Request - Get Available Slots"

2. **Verificar Configuração**:
   - **Method**: POST
   - **URL**: `http://e2bot-n8n-dev:5678/webhook/calendar-availability`
   - **Body Parameters**:
     - `action` = `available_slots`
     - `date` = `{{ $json.scheduled_date }}`
     - `duration_minutes` = `120`

3. **Verificar Conexões**:
   - **Input**: De "Route Based on Stage" (Output 1)
   - **Output**: Para "State Machine Logic"

**✅ SUCESSO**: Configuração completa e loop back correto

### Validação 4: State Machine Logic

1. **Abrir nó**: "State Machine Logic"

2. **Verificar Code**:
   - **Campo jsCode**: Deve conter 18,293 caracteres
   - **Buscar**: `trigger_wf06_next_dates` (deve aparecer no código)
   - **Buscar**: `trigger_wf06_available_slots` (deve aparecer no código)

3. **Verificar Conexões**:
   - **Input**: De "When Chat Message Received"
   - **Output**: Para "Build Update Queries"

**✅ SUCESSO**: Code embedded corretamente, lógica WF06 presente

### Validação 5: Parallel Connections (Output 2 Fallback)

1. **Verificar nó**: "Route Based on Stage"

2. **Output 2 (fallback)** deve conectar a **TODOS os 5 nós**:
   - ✅ Update Conversation State
   - ✅ Save Inbound Message
   - ✅ Save Outbound Message
   - ✅ Upsert Lead Data
   - ✅ Send WhatsApp Response

**✅ SUCESSO**: Todos os 5 nós conectados em paralelo

---

## 🧪 Testes End-to-End

### Preparação

```bash
# 1. Ativar V78.2 no n8n UI
# Workflows → 02_ai_agent_conversation_V78_2_FINAL → Activate

# 2. Desativar V74 (se ativo)
# Workflows → V74_1_2 → Deactivate

# 3. Limpar DB (opcional, para testes limpos)
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "DELETE FROM conversations WHERE phone_number = '556299999999';"
```

### Test 1: Service 1 (Solar) - WF06 Next Dates

**Objetivo**: Validar que service 1 aciona WF06 para buscar próximas datas

```bash
# Enviar mensagem simulando escolha do service 1
curl -X POST http://localhost:8080/message/sendText/e2-solucoes-bot \
  -H "apikey: ae569043cfa169380c378347f91a1141ea572541d2d1cadbed222db519c8a891" \
  -H "Content-Type: application/json" \
  -d '{
    "number": "556299999999",
    "text": "1"
  }'
```

**Fluxo Esperado**:
1. State Machine detecta service `1` (Solar)
2. Define `next_stage = 'trigger_wf06_next_dates'`
3. Switch Node:
   - Avalia condição 1: `$json.next_stage === 'trigger_wf06_next_dates'` → **TRUE**
   - Roteia para **Output 0**
4. HTTP Request - Get Next Dates:
   - Chama WF06: `POST /webhook/calendar-availability`
   - Body: `{"action":"next_dates","count":3,"duration_minutes":120}`
5. WF06 responde com 3 datas
6. HTTP Request retorna dados para **State Machine Logic**
7. State Machine processa datas e envia opções ao usuário

**Validação**:

```bash
# 1. Verificar DB - Estado deve ser 'awaiting_date_selection'
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT phone_number, current_state, state_machine_state, collected_data FROM conversations WHERE phone_number = '556299999999';"

# Esperado:
# current_state = 'awaiting_date_selection'
# state_machine_state contém próximas datas do WF06

# 2. Verificar mensagem WhatsApp recebida (Evolution API)
# Deve conter 3 opções de datas formatadas
```

**✅ SUCESSO**: Usuário recebe mensagem com 3 opções de data
**❌ FALHA**: Se não receber datas, consultar logs:
```bash
docker logs e2bot-n8n-dev | grep -A5 "Route Based on Stage"
docker logs e2bot-n8n-dev | grep -A5 "HTTP Request - Get Next Dates"
```

### Test 2: Service 3 (Projetos) - WF06 Available Slots

**Objetivo**: Validar que após escolher data, WF06 retorna slots disponíveis

```bash
# Pré-requisito: Completar Test 1 primeiro

# Escolher uma das datas apresentadas (ex: opção 1)
curl -X POST http://localhost:8080/message/sendText/e2-solucoes-bot \
  -H "apikey: ae569043cfa169380c378347f91a1141ea572541d2d1cadbed222db519c8a891" \
  -H "Content-Type: application/json" \
  -d '{
    "number": "556299999999",
    "text": "1"
  }'
```

**Fluxo Esperado**:
1. State Machine processa escolha de data
2. Define `next_stage = 'trigger_wf06_available_slots'`
3. Switch Node:
   - Avalia condição 2: `$json.next_stage === 'trigger_wf06_available_slots'` → **TRUE**
   - Roteia para **Output 1**
4. HTTP Request - Get Available Slots:
   - Chama WF06: `POST /webhook/calendar-availability`
   - Body: `{"action":"available_slots","date":"2026-04-15","duration_minutes":120}`
5. WF06 responde com slots disponíveis
6. State Machine apresenta horários

**Validação**:

```bash
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT current_state, state_machine_state FROM conversations WHERE phone_number = '556299999999';"

# Esperado: current_state = 'awaiting_time_selection'
```

**✅ SUCESSO**: Usuário recebe opções de horário
**❌ FALHA**: Consultar logs WF06 e HTTP Request

### Test 3: Service 2 (Subestação) - Handoff Direto (Fallback)

**Objetivo**: Validar que services 2/4/5 NÃO acionam WF06

```bash
# Reiniciar conversa
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "DELETE FROM conversations WHERE phone_number = '556299999998';"

# Enviar mensagem escolhendo service 2
curl -X POST http://localhost:8080/message/sendText/e2-solucoes-bot \
  -H "apikey: ae569043cfa169380c378347f91a1141ea572541d2d1cadbed222db519c8a891" \
  -H "Content-Type: application/json" \
  -d '{
    "number": "556299999998",
    "text": "2"
  }'
```

**Fluxo Esperado**:
1. State Machine detecta service `2` (Subestação)
2. Define `next_stage = 'handoff_comercial'` (NÃO aciona WF06)
3. Switch Node:
   - Avalia condição 1: `$json.next_stage === 'trigger_wf06_next_dates'` → **FALSE**
   - Avalia condição 2: `$json.next_stage === 'trigger_wf06_available_slots'` → **FALSE**
   - Roteia para **Output 2 (fallback)**
4. Executa **5 nós em paralelo**:
   - Update Conversation State
   - Save Inbound Message
   - Save Outbound Message
   - Upsert Lead Data
   - Send WhatsApp Response
5. Usuário recebe mensagem de handoff

**Validação**:

```bash
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT current_state, service_type FROM conversations WHERE phone_number = '556299999998';"

# Esperado:
# current_state = 'handoff_comercial'
# service_type = 'Subestação'
```

**✅ SUCESSO**: Handoff sem acionar WF06
**❌ FALHA**: Se tentar chamar WF06, há erro na lógica do State Machine

---

## 🔧 Troubleshooting

### Erro 1: "Could not find property option" ao Importar

**Sintoma**: Mesmo após V78.2, erro persiste ao importar

**Diagnóstico**:
```bash
# Verificar estrutura do Switch Node no JSON
cat n8n/workflows/02_ai_agent_conversation_V78_2_FINAL.json | \
  jq '.nodes[] | select(.name == "Route Based on Stage") | .parameters'

# Esperado: Deve mostrar "conditions", NÃO "mode" ou "rules"
```

**Possíveis Causas**:
1. **Arquivo Errado**: Importou V78.1.6 ao invés de V78.2
2. **Cache n8n**: n8n cached versão antiga
3. **Versão n8n**: n8n não é 2.15.0 (verificar `docker exec e2bot-n8n-dev n8n --version`)

**Soluções**:
```bash
# 1. Verificar arquivo correto
ls -lh n8n/workflows/02_ai_agent_conversation_V78_2_FINAL.json
# Data deve ser 2026-04-13 (hoje)

# 2. Limpar cache n8n
docker restart e2bot-n8n-dev

# 3. Regerar workflow
python3 scripts/generate-workflow-wf02-v78_2-final.py

# 4. Reimportar
```

### Erro 2: Switch Mostra 4+ Outputs ao Invés de 3

**Sintoma**: UI do Switch mostra mais outputs que o esperado

**Diagnóstico**: Estrutura do Switch pode estar errada

**Solução**:
1. Deletar workflow V78.2 importado
2. Regerar:
   ```bash
   python3 scripts/generate-workflow-wf02-v78_2-final.py
   ```
3. Reimportar JSON gerado

### Erro 3: HTTP Request Não Chama WF06

**Sintoma**: Switch roteia corretamente, mas WF06 não é acionado

**Diagnóstico**:
```bash
# 1. Verificar WF06 ativo
curl http://localhost:5678/webhook/calendar-availability \
  -H "Content-Type: application/json" \
  -d '{"action":"next_dates","count":3}' | jq

# 2. Verificar logs HTTP Request
docker logs e2bot-n8n-dev | grep "HTTP Request - Get Next Dates"
```

**Possíveis Causas**:
- WF06 inativo
- URL incorreta no HTTP Request
- Body parameters malformados

**Soluções**:
```bash
# Ativar WF06
# n8n UI → Workflows → 06_calendar_availability_service_v1 → Activate

# Verificar URL no HTTP Request node
# Deve ser: http://e2bot-n8n-dev:5678/webhook/calendar-availability
```

### Erro 4: Loop Infinito (HTTP Request Não Retorna)

**Sintoma**: HTTP Request executa indefinidamente

**Causa**: WF06 não responde ou timeout

**Solução**:
```bash
# Verificar WF06 logs
docker logs e2bot-n8n-dev | grep "calendar-availability"

# Se timeout, aumentar no HTTP Request:
# options.timeout = 10000 (10 segundos)
```

---

## 🔄 Rollback

### Quando Fazer Rollback?

- ❌ Import falha com erro "property option"
- ❌ Switch não funciona corretamente
- ❌ WF06 integration quebra flow existente
- ❌ Erro rate > 5% nos primeiros testes

### Rollback Imediato (< 1 minuto)

```bash
# 1. n8n UI
# Workflows → 02_ai_agent_conversation_V78_2_FINAL → Deactivate

# 2. Reativar V74
# Workflows → V74_1_2 → Activate

# 3. Validar V74 funcionando
curl -X POST http://localhost:8080/message/sendText/e2-solucoes-bot \
  -H "apikey: ae569043cfa169380c378347f91a1141ea572541d2d1cadbed222db519c8a891" \
  -H "Content-Type: application/json" \
  -d '{
    "number": "556299999999",
    "text": "oi"
  }'

# Esperado: V74 responde normalmente (SEM WF06, mas estável)
```

**Estado Após Rollback**:
- ✅ Sistema estável com V74
- ❌ Sem integração WF06 (calendário manual)
- ✅ Todos os outros flows funcionando

---

## 📊 Checklist Final

### Pré-Deploy
- [x] V78.2 workflow gerado
- [x] State Machine embedded
- [x] WF06 ativo e testado
- [x] Plano estratégico documentado

### Deploy
- [ ] V78.2 importado sem erros
- [ ] Switch mostra 3 outputs
- [ ] HTTP Requests configurados
- [ ] Conexões validadas

### Testes
- [ ] Test 1: Service 1 aciona WF06 next_dates
- [ ] Test 2: Service 3 aciona WF06 available_slots
- [ ] Test 3: Service 2 handoff direto (fallback)
- [ ] Error rate < 1%

### Produção
- [ ] V74 desativado
- [ ] V78.2 ativo
- [ ] Monitoramento configurado
- [ ] Rollback testado

---

## 📚 Referências

### Arquivos do Projeto
- **Workflow**: `n8n/workflows/02_ai_agent_conversation_V78_2_FINAL.json`
- **Generator**: `scripts/generate-workflow-wf02-v78_2-final.py`
- **State Machine**: `scripts/wf02-v78-state-machine.js`
- **Plano Estratégico**: `docs/PLAN/PLAN_WF02_V78_2_STRATEGIC_FIX.md`

### Workflows Referência
- **Switch v3**: `n8n/workflows/old/09_rdstation_webhook_handler.json`
- **HTTP Request v3**: `n8n/workflows/02_ai_agent_conversation_V74.1_2_FUNCIONANDO.json`

### Comandos Úteis

```bash
# Logs n8n
docker logs -f e2bot-n8n-dev

# Logs Evolution
docker logs -f e2bot-evolution-dev

# DB Check
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT * FROM conversations ORDER BY updated_at DESC LIMIT 5;"

# WF06 Test
curl http://localhost:5678/webhook/calendar-availability \
  -H "Content-Type: application/json" \
  -d '{"action":"next_dates","count":3}' | jq
```

---

**Última Atualização**: 2026-04-13
**Versão**: V78.2 FINAL
**Status**: ✅ PRONTO PARA DEPLOY
