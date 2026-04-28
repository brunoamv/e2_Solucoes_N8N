# WF02 V77 - Guia de Implementação: Fix Loop Infinito

> **Data**: 2026-04-13 | **Versão**: V77 Fixed | **Status**: Pronto para Implementação

---

## 🎯 Objetivo

Corrigir loop infinito em WF02 V77 adicionando:
1. **Switch Node** para controle de fluxo condicional
2. **2 novos estados** no State Machine V77
3. **Conexões corretas** entre State Machine → Switch → HTTP Requests

---

## 📋 Sumário Executivo

### Problema
- WF02 V77 executa HTTP Request sempre, criando loop infinito
- State Machine V63 não gerencia chamadas WF06
- Conexões circulares State Machine → HTTP Request → State Machine

### Solução
- **Switch Node**: Roteia baseado em `next_stage`
- **State Machine V77**: Adiciona estados `trigger_wf06_next_dates` e `trigger_wf06_available_slots`
- **Conexões Condicionais**: HTTP Requests só executam quando `next_stage` correto

---

## 📐 Arquitetura da Solução

### Fluxo de Dados Correto

```
┌─────────────────────────────────────────────────────────────────┐
│ State 8: confirmation (user escolhe "1 - Sim, quero agendar")  │
│   ↓ next_stage = 'trigger_wf06_next_dates'                     │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ Build Update Queries (SQL + next_stage passthrough)            │
│   ↓ $json.next_stage = 'trigger_wf06_next_dates'               │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ Route Based on Stage (Switch Node)                             │
│   ├─ Output 0: next_stage === 'trigger_wf06_next_dates'        │
│   ├─ Output 1: next_stage === 'trigger_wf06_available_slots'   │
│   └─ Output 2 (default): Send WhatsApp Response                │
└─────────────────────────────────────────────────────────────────┘
         ↓ Output 0                 ↓ Output 1
┌───────────────────────┐  ┌────────────────────────────────┐
│ HTTP Request 1        │  │ HTTP Request 2                 │
│ Get Next Dates        │  │ Get Available Slots            │
│   ↓ WF06 response     │  │   ↓ WF06 response              │
└───────────────────────┘  └────────────────────────────────┘
         ↓                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ State Machine Logic (recebe input.wf06_next_dates ou           │
│                      input.wf06_available_slots)                │
│   ↓ Processa resposta WF06 e avança para próximo estado        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔨 Implementação Passo a Passo

### Passo 1: Criar State Machine V77

**Arquivo**: `/scripts/wf02-v77-state-machine.js`

**Base**: Copiar `wf02-v76-state-machine.js` (V63)

**Mudanças**:

#### 1.1 Header do Arquivo

```javascript
// ===================================================
// V77 STATE MACHINE - WF06 INTEGRATION
// ===================================================
// Changes from V63:
// - ADDED: trigger_wf06_next_dates state (intermediary)
// - ADDED: trigger_wf06_available_slots state (intermediary)
// - MODIFIED: confirmation state (sets trigger states)
// - MODIFIED: process_date_selection state (sets trigger states)
// - STATES: 14 (was 12 in V63)
// Date: 2026-04-13
// ===================================================
```

#### 1.2 State 8 - confirmation (MODIFICAR)

**Localização**: Linha ~450

**ANTES (V63)**:
```javascript
case 'confirmation':
  if (message === '1') {
    const serviceSelected = currentData.service_selected || '1';
    if (serviceSelected === '1' || serviceSelected === '3') {
      console.log('V73.2 FIX: Services 1 or 3 → Going to collect_appointment_date (State 9)');
      responseText = '📅 *Ótimo! Vamos agendar sua visita técnica.*\n\nQual a melhor data para você? (formato DD/MM/AAAA)\n\n💡 _Exemplo: 25/04/2026_';
      nextStage = 'collect_appointment_date';
    }
  }
  break;
```

**DEPOIS (V77)**:
```javascript
case 'confirmation':
  console.log('V77: Processing CONFIRMATION state');

  if (message === '1') {
    const serviceSelected = currentData.service_selected || '1';
    if (serviceSelected === '1' || serviceSelected === '3') {
      // V77 FIX: Set intermediate stage to trigger WF06 call via Switch Node
      console.log('V77 FIX: Services 1 or 3 → trigger WF06 next_dates call');
      nextStage = 'trigger_wf06_next_dates';  // ← MUDANÇA CRÍTICA
      responseText = '⏳ *Buscando próximas datas disponíveis...*\n\n_Aguarde um momento..._';
      updateData.awaiting_wf06_next_dates = true;  // ← FLAG para debugging
    } else {
      // Other services → handoff
      console.log('V77: Other services → handoff_comercial');
      responseText = templates.handoff_comercial;
      nextStage = 'handoff_comercial';
      updateData.status = 'handoff';
    }
  }
  // Option 2: Falar com pessoa
  else if (message === '2') {
    responseText = templates.handoff_comercial;
    nextStage = 'handoff_comercial';
    updateData.status = 'handoff';
  }
  // Option 3: Corrigir dados
  else if (message === '3') {
    console.log('V66: User chose correction option');
    // ... (resto do código V66 sem mudanças)
  }
  else {
    responseText = templates.invalid_confirmation;
    nextStage = 'confirmation';
  }
  break;
```

#### 1.3 NOVO State: trigger_wf06_next_dates (ADICIONAR APÓS State 8)

**Localização**: Inserir ANTES de `case 'collect_appointment_date':`

```javascript
  // ===== V77 NEW: INTERMEDIATE STATE - Trigger WF06 Next Dates =====
  case 'trigger_wf06_next_dates':
    console.log('V77: INTERMEDIATE STATE - Triggering WF06 next_dates call');

    // This state exists ONLY to trigger the Switch Node in workflow
    // Workflow detects next_stage === 'trigger_wf06_next_dates' and routes to HTTP Request 1
    // After HTTP Request returns, workflow passes data back to State Machine
    // Then State Machine advances to 'show_available_dates' to process WF06 response

    console.log('V77: Waiting for WF06 response...');
    console.log('V77: After HTTP Request, workflow will re-call State Machine');
    console.log('V77: Then State Machine will process input.wf06_next_dates and show dates');

    // Set next stage to process WF06 response
    nextStage = 'show_available_dates';  // ← State Machine will be called again
    responseText = '';  // ← No message here, HTTP Request sends "Aguarde..."

    break;
```

#### 1.4 State 9 - show_available_dates (SEM MUDANÇA)

**Código permanece EXATAMENTE como V63**:
```javascript
case 'show_available_dates':
    console.log('V76: Showing available dates (PROACTIVE UX)');

    // HTTP Request node should have already called WF06 and stored response
    const nextDatesResponse = input.wf06_next_dates || {};

    if (nextDatesResponse.success && nextDatesResponse.dates && nextDatesResponse.dates.length > 0) {
        // Monta mensagem com 3 opções de datas
        let dateOptions = '';
        nextDatesResponse.dates.forEach((dateObj, index) => {
            const number = index + 1;
            const qualityEmoji = dateObj.quality === 'high' ? '✨' :
                                dateObj.quality === 'medium' ? '📅' : '⚠️';
            dateOptions += `${number}️⃣ *${dateObj.display}*\n   🕐 ${dateObj.total_slots} horários livres ${qualityEmoji}\n\n`;
        });

        responseText = `📅 *Agendar Visita Técnica*\n\n` +
                      `📆 *Próximas datas com horários disponíveis:*\n\n` +
                      dateOptions +
                      `💡 *Escolha uma opção (1-3)*`;

        nextStage = 'process_date_selection';
    } else {
        // FALLBACK se WF06 falhar
        console.warn('V76: WF06 failed, falling back to manual date input');
        responseText = `⚠️ *Não conseguimos buscar disponibilidade*\n\n` +
                      `Por favor, informe a data desejada (DD/MM/AAAA):`;
        nextStage = 'collect_appointment_date_manual';
    }
    break;
```

#### 1.5 State 10 - process_date_selection (MODIFICAR)

**ANTES (V63)**: Não existe este estado

**DEPOIS (V77)**: ADICIONAR NOVO ESTADO

**Localização**: Inserir ANTES de `case 'collect_appointment_time':`

```javascript
  // ===== V77 NEW: STATE 10 - Process Date Selection =====
  case 'process_date_selection':
    console.log('V77: Processing DATE SELECTION state');

    // User chose a date from the 3 options (1, 2, or 3)
    const dateChoice = message.trim();

    if (/^[1-3]$/.test(dateChoice)) {
      const choiceIndex = parseInt(dateChoice, 10) - 1;

      // Get selected date from previous WF06 response
      const previousDatesResponse = input.wf06_next_dates || {};
      const selectedDateObj = previousDatesResponse.dates ? previousDatesResponse.dates[choiceIndex] : null;

      if (selectedDateObj && selectedDateObj.date) {
        console.log('V77: Valid date selection:', selectedDateObj.date);

        // Store selected date
        updateData.scheduled_date = selectedDateObj.date;  // YYYY-MM-DD format
        updateData.scheduled_date_display = selectedDateObj.display;  // "Amanhã (09/04)"

        // V77 FIX: Set intermediate stage to trigger WF06 available_slots call
        console.log('V77 FIX: Triggering WF06 available_slots call for date:', selectedDateObj.date);
        nextStage = 'trigger_wf06_available_slots';  // ← MUDANÇA CRÍTICA
        responseText = `⏳ *Buscando horários disponíveis para ${selectedDateObj.display}...*\n\n_Aguarde um momento..._`;
        updateData.awaiting_wf06_available_slots = true;  // ← FLAG para debugging

      } else {
        // Invalid choice index
        console.log('V77: Date choice out of range');
        responseText = `❌ *Opção inválida*\n\nPor favor, escolha uma opção de 1 a 3.`;
        nextStage = 'show_available_dates';  // ← Mostra datas novamente
      }

    } else {
      // Invalid format
      console.log('V77: Invalid date choice format');
      responseText = `❌ *Opção inválida*\n\nPor favor, digite apenas o número da data escolhida (1, 2 ou 3).`;
      nextStage = 'show_available_dates';
    }
    break;
```

#### 1.6 NOVO State: trigger_wf06_available_slots (ADICIONAR)

**Localização**: Inserir ANTES de `case 'show_available_slots':`

```javascript
  // ===== V77 NEW: INTERMEDIATE STATE - Trigger WF06 Available Slots =====
  case 'trigger_wf06_available_slots':
    console.log('V77: INTERMEDIATE STATE - Triggering WF06 available_slots call');

    // This state exists ONLY to trigger the Switch Node in workflow
    // Workflow detects next_stage === 'trigger_wf06_available_slots' and routes to HTTP Request 2
    // After HTTP Request returns, workflow passes data back to State Machine
    // Then State Machine advances to 'show_available_slots' to process WF06 response

    console.log('V77: Waiting for WF06 available_slots response...');
    console.log('V77: After HTTP Request, workflow will re-call State Machine');
    console.log('V77: Then State Machine will process input.wf06_available_slots and show slots');

    // Set next stage to process WF06 response
    nextStage = 'show_available_slots';  // ← State Machine will be called again
    responseText = '';  // ← No message here, HTTP Request sends "Aguarde..."

    break;
```

#### 1.7 State 11 - show_available_slots (SEM MUDANÇA)

**Código permanece EXATAMENTE como V63**:
```javascript
case 'show_available_slots':
    console.log('V76: Showing available slots (PROACTIVE UX)');

    // Acessa resposta do HTTP Request - Get Available Slots
    const slotsResponse = input.wf06_available_slots || {};

    if (slotsResponse.success && slotsResponse.available_slots && slotsResponse.available_slots.length > 0) {
        // Monta mensagem com horários disponíveis
        let slotOptions = '';
        slotsResponse.available_slots.forEach((slot, index) => {
            const number = index + 1;
            slotOptions += `${number}️⃣ *${slot.formatted}* ✅\n`;
        });

        responseText = `🕐 *Horários Disponíveis - ${currentData.scheduled_date_display}*\n\n` +
                      slotOptions + `\n` +
                      `💡 *Escolha um horário (1-${slotsResponse.total_available})*`;

        nextStage = 'process_slot_selection';
    } else {
        // FALLBACK se WF06 falhar
        console.error('V76: WF06 available_slots failed, falling back to manual');
        responseText = `⚠️ *Não conseguimos buscar horários disponíveis*\n\n` +
                      `Por favor, informe o horário desejado (HH:MM):`;
        nextStage = 'collect_appointment_time_manual';
    }
    break;
```

---

### Passo 2: Atualizar Gerador Python V77

**Arquivo**: `/scripts/generate-workflow-wf02-v77-fixed.py`

**Base**: Copiar `generate-workflow-wf02-v77-wf06-integration.py`

**Mudanças**:

#### 2.1 Header do Script

```python
#!/usr/bin/env python3
"""
Generate WF02 V77 FIXED - WF06 Integration with Loop Fix
========================================================

CHANGES FROM V77 ORIGINAL:
- Add Switch Node for conditional routing
- Fix connections: State Machine → Switch → HTTP Requests
- No direct connection State Machine → HTTP Requests
- HTTP Requests only execute when next_stage matches

INTEGRATION FLOW:
State 8 → trigger_wf06_next_dates → Switch → HTTP Request 1 → State Machine → State 9
State 10 → trigger_wf06_available_slots → Switch → HTTP Request 2 → State Machine → State 11

Date: 2026-04-13
Author: E2 Bot Development Team
"""
```

#### 2.2 Adicionar Função create_switch_node

```python
def create_switch_node(node_id, position):
    """
    Create Switch node for conditional routing based on next_stage.

    Args:
        node_id: UUID for the node
        position: [x, y] coordinates in n8n UI

    Returns:
        dict: Complete n8n Switch node object
    """

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
            "fallbackOutput": 2  # Default: Send WhatsApp Response
        },
        "id": node_id,
        "name": "Route Based on Stage",
        "type": "n8n-nodes-base.switch",
        "typeVersion": 3,
        "position": position
    }
```

#### 2.3 Modificar generate_v77_fixed()

**Localização**: Função principal

```python
def generate_v77_fixed():
    """Generate V77 FIXED workflow with Switch Node."""

    print("=" * 80)
    print("GENERATE WF02 V77 FIXED - LOOP FIX WITH SWITCH NODE")
    print("=" * 80)

    # Load V76 base
    print(f"\n✅ Loading base V76 from: {BASE_V76}")
    with open(BASE_V76, "r", encoding="utf-8") as f:
        workflow = json.load(f)

    # Update workflow metadata
    workflow["name"] = "02_ai_agent_conversation_V77_FIXED"

    # Find State Machine Logic node for position reference
    state_machine = find_node_by_name(workflow, "State Machine Logic")
    if not state_machine:
        print("❌ ERROR: State Machine Logic node not found!")
        return 1

    # Find Build Update Queries node (will connect to Switch)
    build_update = find_node_by_name(workflow, "Build Update Queries")
    if not build_update:
        print("❌ ERROR: Build Update Queries node not found!")
        return 1

    print(f"\n📍 Found State Machine Logic at position: {state_machine.get('position')}")
    print(f"📍 Found Build Update Queries at position: {build_update.get('position')}")

    # Calculate positions for new nodes
    # Switch Node: Between Build Update Queries and HTTP Requests
    switch_position = calculate_position(build_update, offset_x=200, offset_y=0)

    # HTTP Request nodes: To the right of Switch
    node1_position = calculate_position(build_update, offset_x=400, offset_y=-100)
    node2_position = calculate_position(build_update, offset_x=400, offset_y=100)

    # Create Switch Node
    print("\n📝 Creating Switch Node...")
    switch_id = generate_uuid()
    switch_node = create_switch_node(switch_id, switch_position)

    # Create HTTP Request nodes (SAME as V77 original)
    print("\n📝 Creating HTTP Request nodes...")

    node1_id = generate_uuid()
    node1 = create_http_request_node(
        name="HTTP Request - Get Next Dates",
        json_body=NEXT_DATES_BODY,
        position=node1_position,
        node_id=node1_id
    )

    node2_id = generate_uuid()
    node2 = create_http_request_node(
        name="HTTP Request - Get Available Slots",
        json_body=AVAILABLE_SLOTS_BODY,
        position=node2_position,
        node_id=node2_id
    )

    # Add nodes to workflow
    workflow["nodes"].extend([switch_node, node1, node2])

    print(f"   ✅ Created: {switch_node['name']} (ID: {switch_id})")
    print(f"   ✅ Created: {node1['name']} (ID: {node1_id})")
    print(f"   ✅ Created: {node2['name']} (ID: {node2_id})")

    # ===== CRITICAL: FIX CONNECTIONS =====
    print("\n🔗 Fixing node connections...")

    # REMOVE broken connection: State Machine → HTTP Request 1
    # This was causing the loop!
    if "State Machine Logic" in workflow["connections"]:
        state_machine_conns = workflow["connections"]["State Machine Logic"]["main"]
        # Filter out HTTP Request connections
        workflow["connections"]["State Machine Logic"]["main"] = [
            [conn for conn in output if conn["node"] != "HTTP Request - Get Next Dates"]
            for output in state_machine_conns
        ]
        print("   ✅ Removed broken connection: State Machine → HTTP Request 1")

    # ADD correct connection: Build Update Queries → Switch
    if "Build Update Queries" not in workflow["connections"]:
        workflow["connections"]["Build Update Queries"] = {"main": [[]]}

    workflow["connections"]["Build Update Queries"]["main"][0] = [{
        "node": "Route Based on Stage",
        "type": "main",
        "index": 0
    }]
    print("   ✅ Added connection: Build Update Queries → Route Based on Stage")

    # ADD connections: Switch → HTTP Requests + Send WhatsApp
    workflow["connections"]["Route Based on Stage"] = {
        "main": [
            # Output 0: trigger_wf06_next_dates
            [{
                "node": "HTTP Request - Get Next Dates",
                "type": "main",
                "index": 0
            }],
            # Output 1: trigger_wf06_available_slots
            [{
                "node": "HTTP Request - Get Available Slots",
                "type": "main",
                "index": 0
            }],
            # Output 2 (fallback): default
            [{
                "node": "Send WhatsApp Response",
                "type": "main",
                "index": 0
            }]
        ]
    }
    print("   ✅ Added connection: Switch Output 0 → HTTP Request 1")
    print("   ✅ Added connection: Switch Output 1 → HTTP Request 2")
    print("   ✅ Added connection: Switch Output 2 → Send WhatsApp Response")

    # KEEP existing connections: HTTP Requests → State Machine
    workflow["connections"]["HTTP Request - Get Next Dates"] = {
        "main": [[{
            "node": "State Machine Logic",
            "type": "main",
            "index": 0
        }]]
    }

    workflow["connections"]["HTTP Request - Get Available Slots"] = {
        "main": [[{
            "node": "State Machine Logic",
            "type": "main",
            "index": 0
        }]]
    }
    print("   ✅ Kept connection: HTTP Request 1 → State Machine Logic")
    print("   ✅ Kept connection: HTTP Request 2 → State Machine Logic")

    # Save V77 FIXED
    print(f"\n💾 Saving V77 FIXED to: {OUTPUT_V77_FIXED}")
    OUTPUT_V77_FIXED.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_V77_FIXED, "w", encoding="utf-8") as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    # Summary
    print("\n" + "=" * 80)
    print("✅ V77 FIXED WORKFLOW GENERATED SUCCESSFULLY!")
    print("=" * 80)

    print(f"\n📁 Output: {OUTPUT_V77_FIXED}")
    print(f"\n📊 Statistics:")
    print(f"   - Total nodes: {len(workflow['nodes'])}")
    print(f"   - HTTP Request nodes: 3 (1 WhatsApp + 2 WF06)")
    print(f"   - Switch nodes: 1 (Route Based on Stage)")
    print(f"   - New nodes added: 3 (2 HTTP + 1 Switch)")

    print(f"\n🎯 V77 FIXED Features:")
    print("   1. ✅ Switch Node for conditional routing (LOOP FIX)")
    print("   2. ✅ HTTP Request - Get Next Dates (State 9 support)")
    print("   3. ✅ HTTP Request - Get Available Slots (State 11 support)")
    print("   4. ✅ Fallback support via continueOnFail")
    print("   5. ✅ Automatic retry (maxTries: 2)")
    print("   6. ✅ 5-second timeout per request")
    print("   7. ✅ NO DIRECT CONNECTION State Machine → HTTP Requests")

    return 0
```

#### 2.4 Atualizar Configuração de Saída

```python
# Configuration
BASE_V76 = Path(__file__).parent.parent / "n8n" / "workflows" / "02_ai_agent_conversation_V76_PROACTIVE_UX.json"
OUTPUT_V77_FIXED = Path(__file__).parent.parent / "n8n" / "workflows" / "02_ai_agent_conversation_V77_FIXED.json"  # ← MUDANÇA
```

---

### Passo 3: Testar Workflow V77 Fixed

**Arquivo**: `/scripts/test-wf02-v77-fixed-e2e.sh`

```bash
#!/bin/bash
# Test WF02 V77 FIXED - E2E with WF06 Integration

set -e

echo "========================================"
echo "WF02 V77 FIXED - E2E TEST"
echo "========================================"

# 1. Verificar WF06 está ativo
echo ""
echo "1. Verificando WF06..."
WF06_STATUS=$(curl -s http://localhost:5678/workflow/QDFJCEtzQSNON9cR | jq -r '.active')
if [ "$WF06_STATUS" != "true" ]; then
    echo "❌ WF06 não está ativo!"
    exit 1
fi
echo "✅ WF06 ativo"

# 2. Testar endpoints WF06
echo ""
echo "2. Testando WF06 next_dates..."
NEXT_DATES_RESULT=$(curl -s -X POST http://localhost:5678/webhook/calendar-availability \
  -H "Content-Type: application/json" \
  -d '{"action":"next_dates","count":3}' | jq -r '.success')

if [ "$NEXT_DATES_RESULT" != "true" ]; then
    echo "❌ WF06 next_dates falhou!"
    exit 1
fi
echo "✅ WF06 next_dates funcionando"

echo ""
echo "3. Testando WF06 available_slots..."
SLOTS_RESULT=$(curl -s -X POST http://localhost:5678/webhook/calendar-availability \
  -H "Content-Type: application/json" \
  -d '{"action":"available_slots","date":"2026-04-15"}' | jq -r '.success')

if [ "$SLOTS_RESULT" != "true" ]; then
    echo "❌ WF06 available_slots falhou!"
    exit 1
fi
echo "✅ WF06 available_slots funcionando"

# 4. Simular conversa completa (via Postman ou Evolution API)
echo ""
echo "4. Teste E2E - Simular conversa..."
echo "   MANUAL: Use WhatsApp ou Postman para testar fluxo completo"
echo "   Checkpoint 1: Escolher serviço 1 (Energia Solar)"
echo "   Checkpoint 2: Preencher dados até confirmação"
echo "   Checkpoint 3: Escolher '1 - Sim, quero agendar'"
echo "   Checkpoint 4: Verificar mensagem '⏳ Buscando próximas datas...'"
echo "   Checkpoint 5: Verificar 3 opções de datas aparecem"
echo "   Checkpoint 6: Escolher data (ex: '2')"
echo "   Checkpoint 7: Verificar mensagem '⏳ Buscando horários...'"
echo "   Checkpoint 8: Verificar horários disponíveis aparecem"
echo "   Checkpoint 9: Escolher horário e confirmar agendamento"

echo ""
echo "========================================"
echo "✅ PRÉ-REQUISITOS OK!"
echo "   Prossiga com teste manual no WhatsApp"
echo "========================================"
```

---

## 🧪 Validação da Solução

### Checklist de Implementação

- [ ] **State Machine V77 criado** (`wf02-v77-state-machine.js`)
  - [ ] Header atualizado com V77
  - [ ] State 8 modificado (trigger_wf06_next_dates)
  - [ ] State trigger_wf06_next_dates adicionado
  - [ ] State 10 process_date_selection adicionado
  - [ ] State trigger_wf06_available_slots adicionado
  - [ ] States 9 e 11 sem mudanças

- [ ] **Gerador Python V77 Fixed criado** (`generate-workflow-wf02-v77-fixed.py`)
  - [ ] Função create_switch_node implementada
  - [ ] Conexões corretas: Build Update → Switch → HTTP Requests
  - [ ] Conexão removida: State Machine → HTTP Requests
  - [ ] Workflow name = "02_ai_agent_conversation_V77_FIXED"

- [ ] **Workflow V77 Fixed gerado** (`02_ai_agent_conversation_V77_FIXED.json`)
  - [ ] Total de 37 nós (36 original + 1 Switch)
  - [ ] Switch Node presente com 3 outputs
  - [ ] Conexões verificadas no JSON

- [ ] **Testes E2E executados**
  - [ ] WF06 respondendo corretamente
  - [ ] State Machine define next_stage corretamente
  - [ ] Switch Node roteia para HTTP Request correto
  - [ ] HTTP Requests executam apenas quando necessário
  - [ ] Sem loop infinito detectado
  - [ ] Fluxo completo funciona até agendamento

---

## 📚 Referências

- **Plano Estratégico**: `/docs/PLAN/PLAN_WF02_V77_LOOP_FIX.md`
- **WF02 V76 Base**: `/n8n/workflows/02_ai_agent_conversation_V76_PROACTIVE_UX.json`
- **State Machine V63**: `/scripts/wf02-v76-state-machine.js`
- **WF06 Docs**: `/docs/implementation/WF06_CALENDAR_AVAILABILITY_SERVICE.md`
- **Gerador V77 Original**: `/scripts/generate-workflow-wf02-v77-wf06-integration.py`

---

**Criado**: 2026-04-13
**Autor**: Implementação Técnica E2 Bot
**Status**: Pronto para Execução
**Próximo**: Executar Passo 1 (State Machine V77)
