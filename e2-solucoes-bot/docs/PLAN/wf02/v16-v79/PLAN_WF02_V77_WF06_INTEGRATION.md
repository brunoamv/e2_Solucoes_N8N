# PLAN WF02 V77 - Integração Automática WF06

> **Data**: 2026-04-13 | **Status**: Planejamento | **Objetivo**: Eliminar configuração manual

---

## 🎯 Objetivo

Criar WF02 V77 com integração WF06 **100% automática** via script Python, eliminando necessidade de adicionar nós HTTP Request manualmente na UI do n8n.

---

## 📊 Análise Atual

### WF02 V76 - Estado Atual
```yaml
Arquivo: 02_ai_agent_conversation_V76_PROACTIVE_UX.json
Linhas: 1028
Nós totais: 34
HTTP Request nodes: 1 (apenas "Send WhatsApp Response")

Problema:
  - Faltam 2 nós HTTP Request para chamar WF06
  - Usuário precisa adicionar manualmente na UI
  - Risco de configuração incorreta
  - Difícil manutenção e reprodutibilidade
```

### WF06 - Endpoints Disponíveis
```yaml
Webhook: http://e2bot-n8n-dev:5678/webhook/calendar-availability

Endpoint 1: next_dates
  - Action: next_dates
  - Retorna: 3 próximas datas com disponibilidade
  - Usado em: State 9 (show_available_dates)

Endpoint 2: available_slots
  - Action: available_slots
  - Retorna: Horários disponíveis em data específica
  - Usado em: State 11 (show_available_slots)
```

---

## 🔀 Abordagem 1: HTTP Request Nodes (Recomendada)

### Conceito
Adicionar 2 nós HTTP Request no workflow JSON via script Python, seguindo padrão de geração de workflows existentes.

### Vantagens
✅ **Mínima mudança arquitetural** - Mantém estrutura atual do WF02 V76
✅ **Padrão estabelecido** - Segue padrão de 47 geradores Python existentes
✅ **Flexibilidade** - HTTP Request permite retry, timeout, error handling
✅ **Observabilidade** - Visualização clara de chamadas WF06 na UI n8n
✅ **Fallback robusto** - Continue On Fail permite degradação graciosa
✅ **Testabilidade** - Nós HTTP Request podem ser testados isoladamente

### Desvantagens
⚠️ **Complexidade JSON** - Necessário gerar estrutura completa de nó n8n
⚠️ **Posicionamento UI** - Coordenadas X/Y precisam ser calculadas
⚠️ **Conexões** - Precisa criar connections corretamente entre nós

### Estrutura dos Nós

#### Nó 1: HTTP Request - Get Next Dates
```json
{
  "parameters": {
    "method": "POST",
    "url": "http://e2bot-n8n-dev:5678/webhook/calendar-availability",
    "authentication": "none",
    "sendBody": true,
    "specifyBody": "json",
    "jsonBody": "={{ JSON.stringify({\n  action: 'next_dates',\n  count: 3,\n  start_date: new Date().toISOString().split('T')[0],\n  duration_minutes: 120\n}) }}",
    "options": {
      "response": {
        "response": {
          "responseFormat": "json"
        }
      },
      "timeout": 5000
    }
  },
  "name": "HTTP Request - Get Next Dates",
  "type": "n8n-nodes-base.httpRequest",
  "typeVersion": 4.2,
  "position": [1200, 400],
  "continueOnFail": true,
  "retryOnFail": true,
  "maxTries": 2
}
```

**Conexões**:
- Input: State Machine Logic (quando state = 8 e escolha = "1")
- Output: State Machine Logic (passa para state 9)

#### Nó 2: HTTP Request - Get Available Slots
```json
{
  "parameters": {
    "method": "POST",
    "url": "http://e2bot-n8n-dev:5678/webhook/calendar-availability",
    "authentication": "none",
    "sendBody": true,
    "specifyBody": "json",
    "jsonBody": "={{ JSON.stringify({\n  action: 'available_slots',\n  date: $json.scheduled_date,\n  duration_minutes: 120\n}) }}",
    "options": {
      "response": {
        "response": {
          "responseFormat": "json"
        }
      },
      "timeout": 5000
    }
  },
  "name": "HTTP Request - Get Available Slots",
  "type": "n8n-nodes-base.httpRequest",
  "typeVersion": 4.2,
  "position": [1200, 600],
  "continueOnFail": true,
  "retryOnFail": true,
  "maxTries": 2
}
```

**Conexões**:
- Input: State Machine Logic (quando state = 10 e data válida)
- Output: State Machine Logic (passa para state 11)

### Implementação Python

```python
def add_http_request_node(workflow, name, url, json_body, position, node_id):
    """Adiciona nó HTTP Request ao workflow."""
    node = {
        "parameters": {
            "method": "POST",
            "url": url,
            "authentication": "none",
            "sendBody": True,
            "specifyBody": "json",
            "jsonBody": json_body,
            "options": {
                "response": {
                    "response": {
                        "responseFormat": "json"
                    }
                },
                "timeout": 5000
            }
        },
        "id": node_id,
        "name": name,
        "type": "n8n-nodes-base.httpRequest",
        "typeVersion": 4.2,
        "position": position,
        "continueOnFail": True,
        "retryOnFail": True,
        "maxTries": 2
    }

    workflow["nodes"].append(node)
    return node_id

def add_node_connections(workflow, source_node, target_node, condition=None):
    """Adiciona conexões entre nós."""
    # Lógica para adicionar connections no workflow["connections"]
    pass
```

### Fluxo de Dados

```
State 8: confirmation (user escolhe "1")
    ↓
HTTP Request - Get Next Dates
    ↓ (armazena em $json)
State Machine Logic → State 9: show_available_dates
    ↓ (lê input.wf06_next_dates do $json anterior)
    ↓ (user escolhe data)
    ↓
State 10: process_date_selection (valida escolha)
    ↓
HTTP Request - Get Available Slots
    ↓ (armazena em $json)
State Machine Logic → State 11: show_available_slots
    ↓ (lê input.wf06_available_slots do $json anterior)
```

### Posicionamento UI

```
Análise do V76 atual:
- State Machine Logic está em [900, 300]
- Trigger Appointment Scheduler está em [1100, 500]

Nós novos:
- HTTP Request - Get Next Dates: [1200, 400]
- HTTP Request - Get Available Slots: [1200, 600]
```

### Estimativa de Esforço
- **Desenvolvimento**: 3-4 horas
- **Testes**: 2 horas
- **Documentação**: 1 hora
- **Total**: 6-7 horas

---

## 🔀 Abordagem 2: Function Node com fetch() [Não Recomendada]

### Conceito
Manter nós Code existentes e adicionar chamadas `fetch()` dentro do State Machine Logic.

### Exemplo de Código
```javascript
case 'show_available_dates':
    console.log('V77: Calling WF06 next_dates...');

    try {
        const response = await fetch('http://e2bot-n8n-dev:5678/webhook/calendar-availability', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                action: 'next_dates',
                count: 3,
                start_date: new Date().toISOString().split('T')[0],
                duration_minutes: 120
            })
        });

        const nextDatesResponse = await response.json();

        if (nextDatesResponse.success && nextDatesResponse.dates) {
            // Build proactive date selection message
        }
    } catch (error) {
        console.error('V77: WF06 call failed:', error);
        // FALLBACK to manual input
    }
    break;
```

### Vantagens
✅ **Menos código Python** - Mudanças apenas no state machine JS
✅ **Menos nós** - Não adiciona nós novos ao workflow
✅ **Lógica concentrada** - Tudo no State Machine Logic

### Desvantagens ❌ CRÍTICAS
❌ **fetch() bloqueado** - n8n 2.14.2 não permite fetch() em Code nodes
❌ **Sem retry automático** - Precisa implementar retry manualmente
❌ **Sem timeout visual** - Dificulta debug
❌ **Sem observabilidade** - Chamadas HTTP invisíveis na UI
❌ **Error handling complexo** - Try/catch manual em cada caso
❌ **Performance** - Bloqueia execução do state machine durante HTTP call

### Estimativa de Esforço
- **Desenvolvimento**: 2-3 horas
- **Testes**: 3-4 horas (alta probabilidade de bugs)
- **Documentação**: 1 hora
- **Total**: 6-8 horas

---

## ✅ Decisão: Abordagem 1 (HTTP Request Nodes)

### Justificativa

1. **Padrão Estabelecido**
   - 47 scripts Python de geração de workflow já existem
   - Padrão funcional e testado no projeto

2. **Manutenibilidade**
   - HTTP Request nodes são visíveis na UI
   - Fácil debug e troubleshooting
   - Configuração explícita (não mágica)

3. **Robustez**
   - Continue On Fail nativo
   - Retry automático
   - Timeout configurável
   - Error handling visual

4. **Compatibilidade n8n**
   - Não depende de APIs bloqueadas (fetch)
   - Usa recursos nativos do n8n
   - Funciona em n8n 2.14.2

5. **Observabilidade**
   - Chamadas WF06 visíveis em executions
   - Tempo de resposta rastreável
   - Dados de request/response inspecionáveis

---

## 📋 Plano de Implementação (Abordagem 1)

### Fase 1: Preparação (30 min)
- [x] Analisar estrutura JSON do WF02 V76
- [ ] Identificar posições e IDs de nós existentes
- [ ] Planejar estrutura de connections
- [ ] Definir IDs únicos para novos nós

### Fase 2: Desenvolvimento Script Python (3h)
- [ ] Criar `generate-workflow-wf02-v77-wf06-integration.py`
- [ ] Implementar função `add_http_request_node()`
- [ ] Implementar função `add_node_connections()`
- [ ] Calcular posições UI automaticamente
- [ ] Gerar IDs únicos para nós
- [ ] Adicionar validação de workflow resultante

### Fase 3: Testes (2h)
- [ ] Gerar WF02 V77
- [ ] Importar em n8n de desenvolvimento
- [ ] Testar State 9 (show_available_dates)
- [ ] Testar State 11 (show_available_slots)
- [ ] Testar fallback quando WF06 offline
- [ ] Validar estrutura JSON com n8n

### Fase 4: Documentação (1h)
- [ ] Criar guia de implementação completo
- [ ] Documentar estrutura dos nós HTTP Request
- [ ] Adicionar troubleshooting guide
- [ ] Atualizar CLAUDE.md e README.md

### Fase 5: Validação (1h)
- [ ] Teste E2E completo (State 1-13)
- [ ] Verificar logs de WF06
- [ ] Validar dados passados entre nós
- [ ] Confirmar fallback funcionando

---

## 🎯 Estrutura de Arquivos Resultante

```
/scripts/
  ├── generate-workflow-wf02-v77-wf06-integration.py  ← NOVO
  └── deploy-wf02-v77.sh                              ← NOVO

/n8n/workflows/
  └── 02_ai_agent_conversation_V77_WF06_INTEGRATION.json  ← GERADO

/docs/PLAN/
  └── PLAN_WF02_V77_WF06_INTEGRATION.md  ← ESTE DOCUMENTO

/docs/implementation/
  └── WF02_V77_IMPLEMENTATION_GUIDE.md  ← PRÓXIMO
```

---

## 🔍 Riscos e Mitigações

### Risco 1: Incompatibilidade de typeVersion
**Probabilidade**: Média
**Impacto**: Alto
**Mitigação**: Usar typeVersion 4.2 do HTTP Request (compatível com n8n 2.14.2)

### Risco 2: IDs de nós duplicados
**Probabilidade**: Baixa
**Impacto**: Crítico
**Mitigação**: Gerar UUIDs únicos para novos nós

### Risco 3: Connections mal configuradas
**Probabilidade**: Média
**Impacto**: Alto
**Mitigação**: Validação de connections antes de salvar JSON

### Risco 4: Posicionamento UI sobreposto
**Probabilidade**: Baixa
**Impacto**: Baixo (estético)
**Mitigação**: Calcular posições baseadas em nós existentes

---

## 📝 Próximos Passos

1. ✅ **Criar este documento de planejamento**
2. [ ] **Criar guia de implementação** (`/docs/implementation/WF02_V77_IMPLEMENTATION_GUIDE.md`)
3. [ ] **Desenvolver script Python** (`generate-workflow-wf02-v77-wf06-integration.py`)
4. [ ] **Testar geração do workflow V77**
5. [ ] **Validar em ambiente de desenvolvimento**
6. [ ] **Documentar processo de deploy**

---

## 📚 Referências

- **WF02 V76 Base**: `/n8n/workflows/02_ai_agent_conversation_V76_PROACTIVE_UX.json`
- **State Machine Code**: `/scripts/wf02-v76-state-machine.js`
- **WF06 Docs**: `/docs/implementation/WF06_CALENDAR_AVAILABILITY_SERVICE.md`
- **Gerador WF05 V7**: `/scripts/generate-workflow-wf05-v7-hardcoded-values.py` (referência)
- **Gerador WF07 V13**: `/scripts/generate-workflow-wf07-v13-insert-select.py` (referência)

---

**Criado**: 2026-04-13
**Autor**: Planejamento Técnico E2 Bot
**Status**: Pronto para Implementação
**Próximo**: Criar guia de implementação detalhado
