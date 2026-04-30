# PLAN WF02 V77 - Fix Loop Infinito HTTP Request

> **Data**: 2026-04-13 | **Status**: Análise Crítica | **Severidade**: 🚨 BLOQUEADOR

---

## 🚨 Problema Identificado

### Sintoma
WF02 V77 entra em **loop infinito** no nó "HTTP Request - Get Next Dates" sem disparar conversa com usuário.

### Evidência
```
Error: invalid syntax
URL: http://localhost:5678/workflow/uVyvQUgNfxoOIxJ0/executions/5
Node: HTTP Request - Get Next Dates
Executions: 103 of 103 (1 item)
Status: This node will automatically retry if it fails
```

---

## 🔍 Root Cause Analysis

### Causa Raiz 1: Conexões Circulares Incorretas

**Arquivo**: `02_ai_agent_conversation_V77_WF06_INTEGRATION.json`

**Problema Detectado** (linhas 830-842):
```json
"State Machine Logic": {
  "main": [
    [
      {
        "node": "Build Update Queries",
        "type": "main",
        "index": 0
      },
      {
        "node": "HTTP Request - Get Next Dates",  // ❌ SEMPRE executa!
        "type": "main",
        "index": 0
      }
    ],
```

**Problema**:
- State Machine Logic tem saída PARALELA para 2 nós no mesmo index 0
- "HTTP Request - Get Next Dates" é executado **SEMPRE**, independente do estado
- Cria loop: State Machine → HTTP Request → State Machine → HTTP Request...

**Comportamento Esperado**:
- HTTP Request só deve executar quando `next_stage === 'show_available_dates'`
- Deve haver nó IF condicional entre State Machine e HTTP Request

### Causa Raiz 2: State Machine Não Gerencia Chamadas WF06

**Arquivo**: State Machine Code (V63)

**Problema**: State Machine V63 **NÃO TEM LÓGICA** para disparar HTTP Requests WF06.

**Código Atual** (State 8 - confirmation):
```javascript
case 'confirmation':
  if (message === '1') {
    const serviceSelected = currentData.service_selected || '1';
    if (serviceSelected === '1' || serviceSelected === '3') {
      console.log('V73.2 FIX: Services 1 or 3 → Going to collect_appointment_date (State 9)');
      responseText = '📅 *Ótimo! Vamos agendar sua visita técnica.*\n\nQual a melhor data para você?';
      nextStage = 'collect_appointment_date';  // ✅ VAI para State 9
    }
  }
```

**Problema**:
- State Machine define `nextStage = 'collect_appointment_date'` (State 9)
- **MAS** WF02 V77 chama HTTP Request ANTES de State 9!
- State Machine V63 espera dados de WF06 em `input.wf06_next_dates` no State 9:

```javascript
case 'show_available_dates':  // State 9
  const nextDatesResponse = input.wf06_next_dates || {};  // ❌ Espera dados WF06
```

**Conflito Arquitetural**:
1. V76 (manual): Usuário adiciona HTTP Request nodes manualmente na UI
2. V77 (automático): Script Python adiciona nodes, mas sem lógica de orquestração
3. State Machine V63: Não sabe que HTTP Requests existem

---

## 🎯 Estratégia de Correção

### Abordagem 1: Conexões Condicionais (Recomendada)

**Conceito**: Adicionar nós IF entre State Machine e HTTP Requests para controle de fluxo.

**Arquitetura**:
```
State Machine Logic
    ↓ (next_stage)
Build Update Queries
    ↓
IF: Should Call WF06? (next_stage === 'collect_appointment_date')
    ├─ TRUE → HTTP Request - Get Next Dates → State Machine Logic
    └─ FALSE → Send WhatsApp Response
```

**Vantagens**:
✅ Conexões condicionais nativas do n8n
✅ State Machine V63 não precisa mudar
✅ HTTP Requests só executam quando necessário
✅ Fácil debugar no n8n UI

**Desvantagens**:
⚠️ Adiciona 2 nós IF (complexidade moderada)
⚠️ Script Python mais complexo

### Abordagem 2: State Machine Inteligente

**Conceito**: State Machine decide quando chamar WF06 via `next_stage`.

**Mudanças no State Machine**:
```javascript
case 'confirmation':
  if (message === '1') {
    if (serviceSelected === '1' || serviceSelected === '3') {
      // V77 FIX: Set stage to trigger WF06 call
      nextStage = 'trigger_wf06_next_dates';  // ← NOVO ESTADO
      responseText = '⏳ Buscando datas disponíveis...';
    }
  }
  break;

// NOVO STATE
case 'trigger_wf06_next_dates':
  // State Machine não faz nada aqui
  // Workflow IF node detecta este stage e chama HTTP Request
  // Após HTTP Request retornar, vai para 'show_available_dates'
  nextStage = 'show_available_dates';
  break;
```

**Vantagens**:
✅ Controle centralizado no State Machine
✅ Menos nós IF no workflow

**Desvantagens**:
❌ Adiciona estados "virtuais" no State Machine
❌ State Machine fica acoplado ao workflow

### Abordagem 3: Switch Node (Mais Elegante)

**Conceito**: Usar Switch node para rotear baseado em `next_stage`.

**Arquitetura**:
```
State Machine Logic
    ↓
Build Update Queries
    ↓
Switch (next_stage)
    ├─ 'trigger_wf06_next_dates' → HTTP Request 1 → State Machine
    ├─ 'trigger_wf06_available_slots' → HTTP Request 2 → State Machine
    └─ default → Send WhatsApp Response
```

**Vantagens**:
✅ Mais elegante e escalável
✅ Fácil adicionar novos casos
✅ State Machine mantém controle

**Desvantagens**:
⚠️ Adiciona 1 nó Switch (complexidade baixa)

---

## ✅ Decisão: Abordagem 3 (Switch Node)

### Justificativa

1. **Escalabilidade**: Fácil adicionar novos estados WF06 no futuro
2. **Manutenibilidade**: Lógica de roteamento clara e visual
3. **Performance**: Switch é nativo n8n, sem overhead
4. **Compatibilidade**: State Machine V63 precisa apenas adicionar 2 estados novos

---

## 📋 Plano de Implementação

### Fase 1: Atualizar State Machine V63 → V77

**Arquivo**: `scripts/wf02-v77-state-machine.js` (NOVO)

**Mudanças**:

1. **State 8 - confirmation**:
```javascript
case 'confirmation':
  if (message === '1') {
    if (serviceSelected === '1' || serviceSelected === '3') {
      // V77: Trigger WF06 next_dates call
      nextStage = 'trigger_wf06_next_dates';  // ← MUDANÇA
      responseText = '⏳ *Buscando próximas datas disponíveis...*';
      updateData.awaiting_wf06_response = true;
    }
  }
  break;
```

2. **NOVO State: trigger_wf06_next_dates**:
```javascript
case 'trigger_wf06_next_dates':
  console.log('V77: WF06 next_dates triggered, waiting for response...');
  // Workflow detecta este stage e chama HTTP Request
  // Após retornar, avança para show_available_dates
  nextStage = 'show_available_dates';
  responseText = '';  // Sem mensagem aqui
  break;
```

3. **State 9 - show_available_dates** (SEM MUDANÇA):
```javascript
case 'show_available_dates':
  const nextDatesResponse = input.wf06_next_dates || {};

  if (nextDatesResponse.success && nextDatesResponse.dates) {
    // Monta mensagem com datas
  } else {
    // FALLBACK manual
  }
  break;
```

4. **State 10 - process_date_selection**:
```javascript
case 'process_date_selection':
  // Valida escolha da data
  if (validDateChoice) {
    // V77: Trigger WF06 available_slots call
    nextStage = 'trigger_wf06_available_slots';  // ← MUDANÇA
    responseText = '⏳ *Buscando horários disponíveis...*';
  }
  break;
```

5. **NOVO State: trigger_wf06_available_slots**:
```javascript
case 'trigger_wf06_available_slots':
  console.log('V77: WF06 available_slots triggered, waiting for response...');
  nextStage = 'show_available_slots';
  responseText = '';
  break;
```

### Fase 2: Adicionar Switch Node no Workflow

**Script**: `scripts/generate-workflow-wf02-v77-fixed.py`

**Mudanças**:

1. **Criar Switch Node**:
```python
def create_switch_node(node_id, position):
    return {
        "parameters": {
            "mode": "expression",
            "output": "multipleOutputs",
            "rules": {
                "rules": [
                    {
                        "expression": "={{ $json.next_stage === 'trigger_wf06_next_dates' }}",
                        "outputIndex": 0
                    },
                    {
                        "expression": "={{ $json.next_stage === 'trigger_wf06_available_slots' }}",
                        "outputIndex": 1
                    }
                ]
            },
            "fallbackOutput": 2
        },
        "id": node_id,
        "name": "Route Based on Stage",
        "type": "n8n-nodes-base.switch",
        "typeVersion": 3,
        "position": position
    }
```

2. **Reconfigurar Conexões**:
```python
# ANTES (ERRADO - V77 original):
connections["State Machine Logic"]["main"][0].append({
    "node": "HTTP Request - Get Next Dates",
    "type": "main",
    "index": 0
})

# DEPOIS (CORRETO - V77 fixed):
connections["Build Update Queries"]["main"][0] = [{
    "node": "Route Based on Stage",
    "type": "main",
    "index": 0
}]

connections["Route Based on Stage"]["main"] = [
    [{"node": "HTTP Request - Get Next Dates", "type": "main", "index": 0}],  # Output 0
    [{"node": "HTTP Request - Get Available Slots", "type": "main", "index": 0}],  # Output 1
    [{"node": "Send WhatsApp Response", "type": "main", "index": 0}]  # Output 2 (default)
]
```

### Fase 3: Validar Fluxo Completo

**Teste E2E**:
1. Usuário escolhe serviço 1 (Energia Solar)
2. Preenche dados até confirmação
3. Escolhe "1 - Sim, quero agendar"
4. **Checkpoint 1**: State Machine retorna `next_stage = 'trigger_wf06_next_dates'`
5. **Checkpoint 2**: Switch detecta e roteia para HTTP Request 1
6. **Checkpoint 3**: HTTP Request chama WF06 `/next_dates`
7. **Checkpoint 4**: State Machine recebe resposta em `input.wf06_next_dates`
8. **Checkpoint 5**: State Machine mostra 3 datas disponíveis
9. Usuário escolhe data
10. **Checkpoint 6**: State Machine retorna `next_stage = 'trigger_wf06_available_slots'`
11. **Checkpoint 7**: Switch detecta e roteia para HTTP Request 2
12. **Checkpoint 8**: HTTP Request chama WF06 `/available_slots`
13. **Checkpoint 9**: State Machine recebe resposta em `input.wf06_available_slots`
14. **Checkpoint 10**: State Machine mostra horários disponíveis

---

## 🔧 Estrutura de Arquivos

```
/scripts/
  ├── wf02-v77-state-machine.js              ← State Machine V77 (V63 + 2 estados)
  ├── generate-workflow-wf02-v77-fixed.py    ← Gerador V77 Fixed (com Switch)
  └── test-wf02-v77-fixed-e2e.sh             ← Teste E2E completo

/n8n/workflows/
  └── 02_ai_agent_conversation_V77_FIXED.json  ← Workflow gerado (36 nós + Switch)

/docs/PLAN/
  └── PLAN_WF02_V77_LOOP_FIX.md  ← ESTE DOCUMENTO

/docs/implementation/
  └── WF02_V77_LOOP_FIX_IMPLEMENTATION_GUIDE.md  ← PRÓXIMO
```

---

## 🚨 Riscos e Mitigações

### Risco 1: Switch Node Não Detecta Estado Correto

**Probabilidade**: Baixa
**Impacto**: Alto
**Mitigação**: Validar expressão `={{ $json.next_stage === 'trigger_wf06_next_dates' }}` em todos os nós

### Risco 2: HTTP Request Falha e Loop Continua

**Probabilidade**: Média
**Impacto**: Médio
**Mitigação**: `continueOnFail: true` já implementado + fallback no State Machine

### Risco 3: State Machine V77 Incompatível com V76

**Probabilidade**: Baixa
**Impacto**: Alto
**Mitigação**: Adicionar apenas 2 estados novos, manter V63 intacto

---

## 📊 Comparação V76 vs V77 Original vs V77 Fixed

| Aspecto | V76 (Manual) | V77 Original (Broken) | V77 Fixed (Proposta) |
|---------|--------------|----------------------|---------------------|
| **HTTP Requests** | Manual UI | Auto Python | Auto Python |
| **Conexões** | Manual UI | Auto (ERRADO) | Auto (CORRETO) |
| **State Machine** | V63 | V63 (incompatível) | V77 (V63 + 2 estados) |
| **Controle Fluxo** | Manual (usuário) | NENHUM (loop) | Switch Node |
| **Manutenção** | Difícil | Impossível | Fácil |

---

## 📝 Próximos Passos

1. ✅ **Criar este documento de planejamento**
2. [ ] **Criar guia de implementação** (`/docs/implementation/WF02_V77_LOOP_FIX_IMPLEMENTATION_GUIDE.md`)
3. [ ] **Desenvolver State Machine V77** (`scripts/wf02-v77-state-machine.js`)
4. [ ] **Atualizar gerador Python** (`scripts/generate-workflow-wf02-v77-fixed.py`)
5. [ ] **Testar geração do workflow V77 Fixed**
6. [ ] **Validar em ambiente de desenvolvimento**
7. [ ] **Documentar processo de deploy**

---

**Criado**: 2026-04-13
**Autor**: Planejamento Técnico E2 Bot
**Status**: Pronto para Implementação
**Próximo**: Criar guia de implementação detalhado
