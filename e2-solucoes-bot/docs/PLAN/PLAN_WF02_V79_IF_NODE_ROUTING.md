# WF02 V79 - Plano Estratégico: IF Node Routing (NO Switch!)

> **Versão**: V79
> **Data**: 2026-04-13
> **Status**: 🎯 PLANEJADO
> **Mudança Crítica**: Usar IF nodes em cascata ao invés de Switch

---

## 🎯 Objetivo

Implementar routing para WF06 usando **IF nodes em cascata** (padrão V74) ao invés de Switch Node que não funciona com múltiplas conditions em n8n 2.15.0.

---

## 🚨 Por Que NÃO Usar Switch?

### Problema Fundamental

**Switch Node n8n 2.15.0** com múltiplas conditions:
- ❌ Import: SUCESSO, mas UI quebrada
- ❌ UI mostra: "value1 is equal to value2" (placeholders genéricos)
- ❌ Conexões não renderizadas corretamente
- ❌ Apenas 1 output visível (deveria ser 3)
- ❌ 5 nodes paralelos aparecem desconectados

**Tentativas Falhadas**:
- V77: Switch v3 completo → Import error
- V78.1.6: Switch mode/rules → Import error "property option"
- V78.2: Switch conditions com "id" → UI quebrada
- V78.3: Switch conditions SEM "id" → **MESMA UI quebrada**

**Conclusão**: Switch Node NÃO suporta múltiplas conditions em n8n 2.15.0

### Lição do Usuário

> "EU nao usei Swith ate aqui por esse problemas. Nao podemos usar as conditionantes como Check If Scheduling"

**Solução Comprovada**: Usar **IF nodes** como em V74!

---

## ✅ Solução V79: IF Node Cascade Pattern

### Arquitetura

```
Build Update Queries
  ↓
Check If WF06 Next Dates (IF node)
  ├─ TRUE → HTTP Request - Get Next Dates → State Machine Logic
  └─ FALSE ↓

Check If WF06 Available Slots (IF node)
  ├─ TRUE → HTTP Request - Get Available Slots → State Machine Logic
  └─ FALSE ↓

5 PARALLEL NODES (fallback):
  ├─ Update Conversation State
  ├─ Save Inbound Message
  ├─ Save Outbound Message
  ├─ Upsert Lead Data
  └─ Send WhatsApp Response
```

### Vantagens

1. ✅ **Comprovado**: V74 usa IF nodes com sucesso
2. ✅ **Simples**: Estrutura clara e linear
3. ✅ **Confiável**: Não depende de Switch problemático
4. ✅ **Mantível**: Fácil adicionar novas conditions
5. ✅ **Testado**: Pattern já funciona em produção

---

## 🔧 Implementação V79

### IF Node 1: Check If WF06 Next Dates

**Tipo**: `n8n-nodes-base.if`
**TypeVersion**: 1 (padrão V74)

**Parameters**:
```json
{
  "conditions": {
    "string": [
      {
        "value1": "={{ $node['Build Update Queries'].json.next_stage }}",
        "value2": "trigger_wf06_next_dates"
      }
    ]
  }
}
```

**Connections**:
- **TRUE**: → HTTP Request - Get Next Dates
- **FALSE**: → Check If WF06 Available Slots (próximo IF)

### IF Node 2: Check If WF06 Available Slots

**Tipo**: `n8n-nodes-base.if`
**TypeVersion**: 1

**Parameters**:
```json
{
  "conditions": {
    "string": [
      {
        "value1": "={{ $node['Build Update Queries'].json.next_stage }}",
        "value2": "trigger_wf06_available_slots"
      }
    ]
  }
}
```

**Connections**:
- **TRUE**: → HTTP Request - Get Available Slots
- **FALSE**: → 5 PARALLEL NODES (fallback)

### HTTP Request Nodes

**IDÊNTICOS a V78.2/V78.3**:
- HTTP Request - Get Next Dates (typeVersion 3)
- HTTP Request - Get Available Slots (typeVersion 3)
- Ambos fazem loop back para State Machine Logic

### Fallback: 5 Parallel Nodes

**Conexões do FALSE path do IF 2**:
- Update Conversation State
- Save Inbound Message
- Save Outbound Message
- Upsert Lead Data
- Send WhatsApp Response

**IDÊNTICO a V74 pattern!**

---

## 📊 Comparação: Switch vs IF Cascade

| Aspecto | Switch (V78.2/V78.3) | IF Cascade (V79) |
|---------|----------------------|------------------|
| **Import** | ✅ Sucesso | ✅ Sucesso |
| **UI Rendering** | ❌ Quebrada | ✅ Correta |
| **Connections Visible** | ❌ 1 output | ✅ Todas |
| **Pattern Proven** | ❌ NO | ✅ V74 production |
| **Complexity** | Switch v3 obscuro | IF simples |
| **Maintainability** | ❌ Difícil debug | ✅ Fácil |
| **Production Ready** | ❌ NO | ✅ **YES** |

---

## 🎯 V79 Especificação Completa

### Total Nodes: 39

**Base V74**: 34 nodes
**Novos V79**:
1. Check If WF06 Next Dates (IF node)
2. Check If WF06 Available Slots (IF node)
3. HTTP Request - Get Next Dates
4. HTTP Request - Get Available Slots
5. State Machine Logic (atualizado com V78 code)

### Connections Architecture

```
Webhook (Evolution) → Extract Phone Number
  ↓
Count Phone in DB
  ↓
Check If New User (IF) → [new user flow]
  FALSE ↓
Fetch Existing Conversation
  ↓
State Machine Logic (V78 code embedded)
  ↓
Build Update Queries
  ↓
Check If WF06 Next Dates (IF) ✨ NEW
  TRUE → HTTP Request - Get Next Dates → State Machine Logic (loop)
  FALSE ↓
Check If WF06 Available Slots (IF) ✨ NEW
  TRUE → HTTP Request - Get Available Slots → State Machine Logic (loop)
  FALSE ↓
5 PARALLEL NODES (fallback):
  ├─ Update Conversation State
  ├─ Save Inbound Message
  ├─ Save Outbound Message
  ├─ Upsert Lead Data
  └─ Send WhatsApp Response
```

---

## ✅ Validação V79

### Pre-Import Checks

1. **JSON válido**: `jq . workflow.json`
2. **IF nodes structure**: Verificar `parameters.conditions.string`
3. **Total nodes**: 39
4. **Connections**: TRUE/FALSE paths corretos

### Post-Import UI Checks

1. **IF Node 1 UI**:
   - Condition: `Build Update Queries.next_stage === "trigger_wf06_next_dates"`
   - TRUE path: → HTTP Request - Get Next Dates
   - FALSE path: → Check If WF06 Available Slots

2. **IF Node 2 UI**:
   - Condition: `Build Update Queries.next_stage === "trigger_wf06_available_slots"`
   - TRUE path: → HTTP Request - Get Available Slots
   - FALSE path: → 5 parallel nodes

3. **Canvas Visual**:
   - ✅ Todas conexões visíveis
   - ✅ TRUE/FALSE paths claros
   - ✅ HTTP Requests conectados
   - ✅ 5 parallel nodes visíveis

### Functional Tests

1. **Service 1 (Solar)**: next_stage = trigger_wf06_next_dates
   - IF 1: TRUE → HTTP Request 1 → WF06 /next_dates
   - IF 2: NÃO executa

2. **Service 3 (Projetos)**: next_stage = trigger_wf06_available_slots
   - IF 1: FALSE
   - IF 2: TRUE → HTTP Request 2 → WF06 /available_slots

3. **Service 2 (Subestação)**: next_stage = handoff_comercial
   - IF 1: FALSE
   - IF 2: FALSE → 5 parallel nodes

---

## 🔄 Migration Path

### V74 → V79

**O Que Muda**:
1. ✅ State Machine code: V74 (10 states) → V79 (14 states)
2. ✅ Adiciona: 2 IF nodes + 2 HTTP Request nodes
3. ✅ Routing: Linear com IF cascade

**O Que NÃO Muda**:
- ✅ Todos os 34 nodes V74 preservados
- ✅ IF node pattern (já usado em V74)
- ✅ Parallel connections pattern
- ✅ PostgreSQL queries
- ✅ Evolution API integration

### V78.2/V78.3 → V79

**Abandona**:
- ❌ Switch Node (não funciona)
- ❌ V78.2/V78.3 (UI quebrada)

**Adota**:
- ✅ IF cascade pattern (V74 proven)
- ✅ 2 IF nodes ao invés de 1 Switch

---

## 📋 Checklist de Sucesso V79

### Technical Validation

- [ ] JSON válido
- [ ] 39 nodes total
- [ ] 2 IF nodes criados
- [ ] 2 HTTP Request nodes criados
- [ ] State Machine V78 embedded
- [ ] Connections corretas no JSON

### UI Validation

- [ ] IF 1 mostra condition correta
- [ ] IF 2 mostra condition correta
- [ ] TRUE paths visíveis
- [ ] FALSE paths visíveis
- [ ] HTTP Requests conectados
- [ ] 5 parallel nodes visíveis

### Execution Validation

- [ ] Service 1: Roteia para HTTP Request 1
- [ ] Service 3: Roteia para HTTP Request 2
- [ ] Service 2: Roteia para fallback (5 parallel)
- [ ] HTTP Requests fazem loop back
- [ ] 5 parallel nodes executam simultaneamente
- [ ] Error rate < 1%

---

## 🎓 Lições Aprendidas

### 1. **User Experience > Technical Elegance**

**Problema**: Tentei usar Switch porque "é mais elegante"
**Realidade**: IF cascade funciona, Switch não
**Learning**: Sempre usar patterns comprovados do usuário

### 2. **Trust User's Historical Decisions**

**Problema**: Ignorei que usuário nunca usou Switch
**Realidade**: Usuário evitou Switch exatamente por esse problema!
**Learning**: Se usuário evita um pattern, há razão histórica

### 3. **Working Code > Theoretical Best Practice**

**Problema**: Switch "deveria" funcionar segundo docs
**Realidade**: n8n 2.15.0 Switch não suporta múltiplas conditions
**Learning**: Código funcionando > documentação teórica

### 4. **Simplicity Wins**

**Problema**: 10 versões (V77-V78.3) tentando fazer Switch funcionar
**Realidade**: IF cascade é simples, claro, e funciona
**Learning**: Simplicidade > sofisticação quebrada

---

## 🚀 Timeline V79

**Total**: 15-20 minutos

```
T+0min:  Create V79 generator script
T+5min:  Generate V79 workflow
T+8min:  Validate JSON structure
T+10min: Import to n8n
T+12min: Verify UI rendering
T+15min: Execute tests
T+20min: Production ready
```

---

## 📚 Referências

### Working Patterns

- `n8n/workflows/02_ai_agent_conversation_V74.1_2_FUNCIONANDO.json` ← ✅ IF cascade pattern
- IF nodes: Check If New User, Check If Handoff, Check If Scheduling

### Failed Attempts (Learn What NOT to Do)

- V77-V78.3: Switch Node attempts (all failed UI rendering)
- Root cause: n8n 2.15.0 Switch v3 não suporta múltiplas conditions

### V79 Files

- Generator: `scripts/generate-workflow-wf02-v79-if-cascade.py`
- Workflow: `n8n/workflows/02_ai_agent_conversation_V79_IF_CASCADE.json`
- State Machine: `scripts/wf02-v78-state-machine.js` (reused)

---

**Status**: 🎯 V79 PLANO ESTRATÉGICO COMPLETO
**Próximo**: Criar generator script V79
**Confiança**: 95% (baseado em V74 proven pattern)
**Risk**: LOW (pattern já em produção)
