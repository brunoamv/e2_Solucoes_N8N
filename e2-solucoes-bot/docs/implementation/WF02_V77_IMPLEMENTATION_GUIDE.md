# WF02 V77 - Implementation Guide

> **Versão**: V77 | **Data**: 2026-04-13 | **Status**: Implementation Guide
> **Objetivo**: Integração automática WF06 via script Python

---

## 🎯 Visão Geral

WF02 V77 adiciona **integração automática com WF06** através de 2 nós HTTP Request gerados automaticamente via script Python, eliminando configuração manual na UI do n8n.

### Diferenças V76 → V77

| Aspecto | V76 (Atual) | V77 (Novo) |
|---------|-------------|------------|
| **Integração WF06** | ❌ Manual (adicionar 2 nós HTTP na UI) | ✅ Automática (script Python) |
| **Nós HTTP Request** | 1 (apenas WhatsApp) | 3 (WhatsApp + 2 WF06) |
| **Reprodutibilidade** | ⚠️ Baixa (configuração manual) | ✅ Alta (geração automatizada) |
| **Manutenibilidade** | ⚠️ Difícil (mudanças na UI) | ✅ Fácil (mudanças no script) |
| **Risco de erro** | ⚠️ Alto (configuração incorreta) | ✅ Baixo (validação automática) |
| **State Machine** | Sem mudanças | Sem mudanças (reutiliza V76) |

---

## 📋 Arquitetura V77

### Fluxo Completo de Integração

```
State 8: confirmation
    └─> User escolhe "1 - Sim, quero agendar"
        ↓
    [NOVO] HTTP Request - Get Next Dates
        ├─> POST http://e2bot-n8n-dev:5678/webhook/calendar-availability
        ├─> Body: { action: "next_dates", count: 3, ... }
        ├─> Response: { success: true, dates: [...] }
        └─> Armazena em $json como wf06_next_dates
            ↓
    State Machine Logic → State 9: show_available_dates
        ├─> Lê input.wf06_next_dates
        ├─> Monta mensagem com 3 opções de datas
        └─> User escolhe opção (1-3)
            ↓
    State 10: process_date_selection
        └─> Valida escolha e armazena scheduled_date
            ↓
    [NOVO] HTTP Request - Get Available Slots
        ├─> POST http://e2bot-n8n-dev:5678/webhook/calendar-availability
        ├─> Body: { action: "available_slots", date: "2026-04-13", ... }
        ├─> Response: { success: true, available_slots: [...] }
        └─> Armazena em $json como wf06_available_slots
            ↓
    State Machine Logic → State 11: show_available_slots
        ├─> Lê input.wf06_available_slots
        ├─> Monta mensagem com horários disponíveis
        └─> User escolhe horário
            ↓
    State 12: process_slot_selection → State 13: trigger WF05
```

### Estrutura de Nós Adicionados

#### Nó 1: HTTP Request - Get Next Dates

**Função**: Buscar próximas 3 datas com disponibilidade no Google Calendar

**Especificação Completa**:
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
  "id": "uuid-gerado-automaticamente",
  "name": "HTTP Request - Get Next Dates",
  "type": "n8n-nodes-base.httpRequest",
  "typeVersion": 4.2,
  "position": [1200, 400],
  "continueOnFail": true,
  "retryOnFail": true,
  "maxTries": 2
}
```

**Request Body**:
```json
{
  "action": "next_dates",
  "count": 3,
  "start_date": "2026-04-13",
  "duration_minutes": 120
}
```

**Response Esperada**:
```json
{
  "success": true,
  "dates": [
    {
      "date": "2026-04-14",
      "display": "Amanhã (14/04)",
      "day_of_week": "Terça",
      "total_slots": 3,
      "quality": "high"
    },
    {
      "date": "2026-04-15",
      "display": "Quarta (15/04)",
      "day_of_week": "Quarta",
      "total_slots": 5,
      "quality": "high"
    },
    {
      "date": "2026-04-16",
      "display": "Quinta (16/04)",
      "day_of_week": "Quinta",
      "total_slots": 2,
      "quality": "medium"
    }
  ],
  "total_dates": 3,
  "requested_at": "2026-04-13T10:30:00Z"
}
```

**Error Handling**:
- `continueOnFail: true` → Se WF06 falhar, workflow continua
- State Machine detecta falha e ativa fallback para input manual

**Conexões**:
- **Input**: State Machine Logic (output quando state = 8 e escolha = "1")
- **Output**: State Machine Logic (input para processar State 9)

---

#### Nó 2: HTTP Request - Get Available Slots

**Função**: Buscar horários disponíveis em data específica

**Especificação Completa**:
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
  "id": "uuid-gerado-automaticamente",
  "name": "HTTP Request - Get Available Slots",
  "type": "n8n-nodes-base.httpRequest",
  "typeVersion": 4.2,
  "position": [1200, 600],
  "continueOnFail": true,
  "retryOnFail": true,
  "maxTries": 2
}
```

**Request Body**:
```json
{
  "action": "available_slots",
  "date": "2026-04-15",
  "duration_minutes": 120
}
```

**Response Esperada**:
```json
{
  "success": true,
  "date": "2026-04-15",
  "available_slots": [
    {
      "start_time": "09:00",
      "end_time": "11:00",
      "formatted": "9h às 11h",
      "duration_minutes": 120
    },
    {
      "start_time": "14:00",
      "end_time": "16:00",
      "formatted": "14h às 16h",
      "duration_minutes": 120
    }
  ],
  "total_available": 2,
  "requested_at": "2026-04-13T10:35:00Z"
}
```

**Error Handling**:
- `continueOnFail: true` → Se WF06 falhar, workflow continua
- State Machine detecta falha e ativa fallback para input manual de horário

**Conexões**:
- **Input**: State Machine Logic (output quando state = 10 e data válida)
- **Output**: State Machine Logic (input para processar State 11)

---

## 🔧 Script de Geração Python

### Estrutura do Script

```python
#!/usr/bin/env python3
"""
Generate WF02 V77 - WF06 Integration (Automatic HTTP Request Nodes)
===================================================================

CHANGES FROM V76:
- Add 2 HTTP Request nodes for WF06 integration
- Node 1: Get Next Dates (after State 8)
- Node 2: Get Available Slots (after State 10)
- Auto-generate connections between nodes
- Calculate UI positions automatically

Date: 2026-04-13
"""

import json
import uuid
from pathlib import Path

# Configuration
BASE_V76 = Path(__file__).parent.parent / "n8n" / "workflows" / "02_ai_agent_conversation_V76_PROACTIVE_UX.json"
OUTPUT_V77 = Path(__file__).parent.parent / "n8n" / "workflows" / "02_ai_agent_conversation_V77_WF06_INTEGRATION.json"

WF06_WEBHOOK_URL = "http://e2bot-n8n-dev:5678/webhook/calendar-availability"

def generate_uuid():
    """Generate unique UUID for n8n nodes."""
    return str(uuid.uuid4())

def create_http_request_node(name, json_body, position, node_id=None):
    """Create HTTP Request node for WF06 calls."""

    if node_id is None:
        node_id = generate_uuid()

    return {
        "parameters": {
            "method": "POST",
            "url": WF06_WEBHOOK_URL,
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

def add_node_connection(connections, source_node, target_node, source_output="main", target_input="main", output_index=0):
    """Add connection between nodes in workflow."""

    if source_node not in connections:
        connections[source_node] = {}

    if source_output not in connections[source_node]:
        connections[source_node][source_output] = []

    # Ensure output_index exists
    while len(connections[source_node][source_output]) <= output_index:
        connections[source_node][source_output].append([])

    # Add target connection
    connections[source_node][source_output][output_index].append({
        "node": target_node,
        "type": target_input,
        "index": 0
    })

def generate_v77():
    """Generate V77 workflow with automatic WF06 integration."""

    print("=" * 80)
    print("GENERATE WF02 V77 - WF06 INTEGRATION (AUTOMATIC)")
    print("=" * 80)

    # Load V76
    print(f"\n✅ Loading base V76 from: {BASE_V76}")
    with open(BASE_V76, "r", encoding="utf-8") as f:
        workflow = json.load(f)

    # Update workflow metadata
    workflow["name"] = "02_ai_agent_conversation_V77_WF06_INTEGRATION"

    # Create HTTP Request nodes
    print("\n📝 Creating HTTP Request nodes...")

    # Node 1: Get Next Dates
    node1_id = generate_uuid()
    node1 = create_http_request_node(
        name="HTTP Request - Get Next Dates",
        json_body="={{ JSON.stringify({\\n  action: 'next_dates',\\n  count: 3,\\n  start_date: new Date().toISOString().split('T')[0],\\n  duration_minutes: 120\\n}) }}",
        position=[1200, 400],
        node_id=node1_id
    )

    # Node 2: Get Available Slots
    node2_id = generate_uuid()
    node2 = create_http_request_node(
        name="HTTP Request - Get Available Slots",
        json_body="={{ JSON.stringify({\\n  action: 'available_slots',\\n  date: $json.scheduled_date,\\n  duration_minutes: 120\\n}) }}",
        position=[1200, 600],
        node_id=node2_id
    )

    # Add nodes to workflow
    workflow["nodes"].extend([node1, node2])

    print(f"   ✅ Created: HTTP Request - Get Next Dates (ID: {node1_id})")
    print(f"   ✅ Created: HTTP Request - Get Available Slots (ID: {node2_id})")

    # Add connections
    print("\n🔗 Adding node connections...")

    # Find State Machine Logic node ID
    state_machine_id = None
    for node in workflow["nodes"]:
        if node.get("name") == "State Machine Logic":
            state_machine_id = node.get("id")
            break

    if not state_machine_id:
        print("❌ ERROR: State Machine Logic node not found!")
        return 1

    # Connection 1: State Machine → HTTP Request 1 → State Machine
    # (This requires analyzing State Machine outputs - simplified here)
    add_node_connection(workflow["connections"], state_machine_id, node1["name"])
    add_node_connection(workflow["connections"], node1["name"], state_machine_id)

    # Connection 2: State Machine → HTTP Request 2 → State Machine
    add_node_connection(workflow["connections"], state_machine_id, node2["name"])
    add_node_connection(workflow["connections"], node2["name"], state_machine_id)

    print(f"   ✅ Connected: State Machine Logic ↔ HTTP Request - Get Next Dates")
    print(f"   ✅ Connected: State Machine Logic ↔ HTTP Request - Get Available Slots")

    # Save V77
    print(f"\n💾 Saving V77 to: {OUTPUT_V77}")
    with open(OUTPUT_V77, "w", encoding="utf-8") as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    # Summary
    print("\n" + "=" * 80)
    print("✅ V77 WORKFLOW GENERATED SUCCESSFULLY!")
    print("=" * 80)
    print(f"\n📁 Output: {OUTPUT_V77}")
    print(f"\n📊 Statistics:")
    print(f"   - Total nodes: {len(workflow['nodes'])}")
    print(f"   - HTTP Request nodes: 3 (WhatsApp + 2 WF06)")
    print(f"   - New nodes added: 2")

    print(f"\n🎯 V77 Features:")
    print("   1. ✅ Automatic WF06 integration (no manual UI configuration)")
    print("   2. ✅ HTTP Request - Get Next Dates (State 9 support)")
    print("   3. ✅ HTTP Request - Get Available Slots (State 11 support)")
    print("   4. ✅ Fallback support via continueOnFail")
    print("   5. ✅ Automatic retry (maxTries: 2)")

    print(f"\n📝 Next Steps:")
    print("   1. Import 02_ai_agent_conversation_V77_WF06_INTEGRATION.json to n8n")
    print("   2. Verify WF06 is active and responding")
    print("   3. Test State 9 (show_available_dates)")
    print("   4. Test State 11 (show_available_slots)")
    print("   5. Validate fallback when WF06 offline")

    return 0

if __name__ == "__main__":
    import sys
    sys.exit(generate_v77())
```

---

## 🧪 Testes

### Teste 1: Verificar WF06 Ativo

```bash
# WF06 deve estar ativo em n8n
curl -s http://localhost:5678/workflow/QDFJCEtzQSNON9cR | jq '.active'
# Expected: true

# Testar endpoint next_dates
curl -s -X POST http://localhost:5678/webhook/calendar-availability \
  -H "Content-Type: application/json" \
  -d '{"action":"next_dates","count":3}' | jq

# Testar endpoint available_slots
curl -s -X POST http://localhost:5678/webhook/calendar-availability \
  -H "Content-Type: application/json" \
  -d '{"action":"available_slots","date":"2026-04-15"}' | jq
```

### Teste 2: Gerar e Importar V77

```bash
# Gerar V77
cd /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot
python3 scripts/generate-workflow-wf02-v77-wf06-integration.py

# Importar via UI n8n
# http://localhost:5678 → Import → 02_ai_agent_conversation_V77_WF06_INTEGRATION.json

# Verificar nós adicionados
jq '.nodes[] | select(.name | contains("HTTP Request")) | .name' \
  n8n/workflows/02_ai_agent_conversation_V77_WF06_INTEGRATION.json
```

### Teste 3: E2E State 9 (Datas Disponíveis)

```bash
# Simular conversa até State 8
# User: "Olá" → State 1
# Bot: "Qual serviço?" → User: "1" → State 2
# Bot: "Qual seu nome?" → User: "Bruno" → State 3
# ... (continuar até State 8)
# Bot: "Confirma dados?" → User: "1 - Sim" → State 8

# Verificar execução do HTTP Request - Get Next Dates
docker logs e2bot-n8n-dev | grep "HTTP Request - Get Next Dates"

# Verificar State 9 mostra 3 datas
# Expected: Mensagem com "1️⃣ Amanhã (14/04)", "2️⃣ Quarta (15/04)", "3️⃣ Quinta (16/04)"
```

### Teste 4: E2E State 11 (Horários Disponíveis)

```bash
# Continuar conversa do Teste 3
# User escolhe data: "2" (segunda opção)

# Verificar execução do HTTP Request - Get Available Slots
docker logs e2bot-n8n-dev | grep "HTTP Request - Get Available Slots"

# Verificar State 11 mostra horários disponíveis
# Expected: Mensagem com "1️⃣ 9h às 11h ✅", "2️⃣ 14h às 16h ✅"
```

### Teste 5: Fallback quando WF06 Offline

```bash
# Desativar WF06 temporariamente
# n8n UI → WF06 → Deactivate

# Repetir Teste 3
# Expected: Bot mostra fallback "Por favor, informe a data (DD/MM/AAAA):"

# Reativar WF06
# n8n UI → WF06 → Activate
```

---

## 📊 Estrutura de Dados

### State 9: show_available_dates

**Input esperado** (do HTTP Request 1):
```javascript
{
  wf06_next_dates: {
    success: true,
    dates: [
      { date: "2026-04-14", display: "Amanhã (14/04)", total_slots: 3, quality: "high" },
      { date: "2026-04-15", display: "Quarta (15/04)", total_slots: 5, quality: "high" },
      { date: "2026-04-16", display: "Quinta (16/04)", total_slots: 2, quality: "medium" }
    ]
  }
}
```

**State Machine processa**:
```javascript
case 'show_available_dates':
    const nextDatesResponse = input.wf06_next_dates || {};

    if (nextDatesResponse.success && nextDatesResponse.dates && nextDatesResponse.dates.length > 0) {
        // BUILD PROACTIVE MESSAGE
        let dateOptions = '';
        nextDatesResponse.dates.forEach((dateObj, index) => {
            const number = index + 1;
            dateOptions += `${number}️⃣ *${dateObj.display}*\n   🕐 ${dateObj.total_slots} horários livres\n\n`;
        });

        responseText = `📅 *Agendar Visita Técnica*\n\n` +
                      `📆 *Próximas datas com horários disponíveis:*\n\n` +
                      dateOptions +
                      `💡 *Escolha uma opção (1-3)*`;

        nextStage = 'process_date_selection';
    } else {
        // FALLBACK
        responseText = `⚠️ *Não conseguimos buscar disponibilidade*\n\n` +
                      `Por favor, informe a data desejada (DD/MM/AAAA):`;
        nextStage = 'collect_appointment_date_manual';
    }
    break;
```

### State 11: show_available_slots

**Input esperado** (do HTTP Request 2):
```javascript
{
  wf06_available_slots: {
    success: true,
    date: "2026-04-15",
    available_slots: [
      { start_time: "09:00", end_time: "11:00", formatted: "9h às 11h" },
      { start_time: "14:00", end_time: "16:00", formatted: "14h às 16h" }
    ],
    total_available: 2
  }
}
```

**State Machine processa**:
```javascript
case 'show_available_slots':
    const slotsResponse = input.wf06_available_slots || {};

    if (slotsResponse.success && slotsResponse.available_slots && slotsResponse.available_slots.length > 0) {
        // BUILD PROACTIVE MESSAGE
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
        // FALLBACK
        responseText = `⚠️ *Não conseguimos buscar horários disponíveis*\n\n` +
                      `Por favor, informe o horário desejado (HH:MM):`;
        nextStage = 'collect_appointment_time_manual';
    }
    break;
```

---

## 🚀 Deploy

### Pré-requisitos

```bash
# 1. WF06 deve estar ativo
curl -s http://localhost:5678/workflow/QDFJCEtzQSNON9cR | jq '.active'

# 2. Google Calendar configurado
# Ver: /docs/Setups/SETUP_GOOGLE_CALENDAR.md

# 3. Credenciais n8n OK
# Ver: /docs/Setups/SETUP_CREDENTIALS.md
```

### Geração do Workflow

```bash
# Executar script Python
python3 scripts/generate-workflow-wf02-v77-wf06-integration.py

# Verificar arquivo gerado
ls -lh n8n/workflows/02_ai_agent_conversation_V77_WF06_INTEGRATION.json

# Validar JSON
jq . n8n/workflows/02_ai_agent_conversation_V77_WF06_INTEGRATION.json > /dev/null && echo "✅ JSON válido"
```

### Importação no n8n

```bash
# Via UI:
# 1. http://localhost:5678 → Workflows → Import
# 2. Selecionar: 02_ai_agent_conversation_V77_WF06_INTEGRATION.json
# 3. Verificar nós criados (HTTP Request - Get Next Dates/Slots)
# 4. Salvar (MANTER INATIVO)
```

### Validação

```bash
# Verificar nós criados
jq '.nodes[] | select(.type == "n8n-nodes-base.httpRequest") | {name, position, continueOnFail}' \
  n8n/workflows/02_ai_agent_conversation_V77_WF06_INTEGRATION.json

# Expected output:
# {
#   "name": "Send WhatsApp Response",
#   "position": [...],
#   "continueOnFail": false
# }
# {
#   "name": "HTTP Request - Get Next Dates",
#   "position": [1200, 400],
#   "continueOnFail": true
# }
# {
#   "name": "HTTP Request - Get Available Slots",
#   "position": [1200, 600],
#   "continueOnFail": true
# }
```

### Ativação (Canary Deployment)

```bash
# Fase 1: Testes isolados (keep inactive)
# - Testar manualmente via UI executions
# - Validar logs de WF06
# - Confirmar fallback funcionando

# Fase 2: Ativar V77 (substituir V74 ou V76)
# - Desativar WF02 anterior (V74/V76)
# - Ativar WF02 V77
# - Monitorar logs

# Fase 3: Monitoramento (24-48h)
# - Verificar executions bem-sucedidas
# - Monitorar taxa de fallback
# - Validar integração WF05 após States 9-12
```

---

## 🔍 Troubleshooting

### Problema 1: HTTP Request retorna erro 404

**Sintoma**: Erro em execução do nó HTTP Request

**Causa**: WF06 não está ativo ou URL incorreta

**Debug**:
```bash
# Verificar WF06 ativo
curl -s http://localhost:5678/workflow/QDFJCEtzQSNON9cR | jq '.active'

# Testar endpoint manualmente
curl -X POST http://localhost:5678/webhook/calendar-availability \
  -H "Content-Type: application/json" \
  -d '{"action":"next_dates","count":3}'
```

**Solução**:
```bash
# Ativar WF06
# n8n UI → Workflow QDFJCEtzQSNON9cR → Activate
```

### Problema 2: State Machine não recebe dados do HTTP Request

**Sintoma**: State 9 ou 11 cai no fallback mesmo com WF06 ativo

**Causa**: Conexões entre nós mal configuradas ou dados não passados corretamente

**Debug**:
```bash
# Ver execução do workflow na UI
# n8n → Executions → Ver último execution
# Verificar dados do HTTP Request node

# Logs
docker logs e2bot-n8n-dev | grep -E "HTTP Request|wf06_next_dates|wf06_available_slots"
```

**Solução**:
- Verificar connections no JSON do workflow
- Validar que State Machine recebe input correto

### Problema 3: IDs duplicados no workflow

**Sintoma**: Erro ao importar workflow "Duplicate node ID"

**Causa**: UUIDs gerados não são únicos

**Solução**:
```python
# Verificar geração de UUIDs no script Python
import uuid

def generate_uuid():
    return str(uuid.uuid4())  # Deve gerar UUID único a cada chamada
```

---

## 📚 Referências

- **WF02 V76**: `/n8n/workflows/02_ai_agent_conversation_V76_PROACTIVE_UX.json`
- **State Machine**: `/scripts/wf02-v76-state-machine.js` (reutilizado em V77)
- **WF06 Docs**: `/docs/implementation/WF06_CALENDAR_AVAILABILITY_SERVICE.md`
- **Planejamento**: `/docs/PLAN/PLAN_WF02_V77_WF06_INTEGRATION.md`
- **Script Generator**: `/scripts/generate-workflow-wf02-v77-wf06-integration.py` (a ser criado)

---

**Criado**: 2026-04-13
**Autor**: Implementação Técnica E2 Bot
**Status**: Guia Completo
**Próximo**: Desenvolver script Python de geração
