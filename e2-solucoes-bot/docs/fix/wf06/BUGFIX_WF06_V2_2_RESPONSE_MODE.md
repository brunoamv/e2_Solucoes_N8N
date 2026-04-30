# BUGFIX WF06 V2.2 - Response Mode Fix (n8n 2.15.0)

**Data**: 2026-04-20
**Versão**: WF06 V2.2
**Problema**: HTTP Request retornando `{"message":"Workflow was started"}` em vez de dados reais
**Causa Raiz**: n8n 2.15.0 mudou comportamento padrão de webhooks para modo assíncrono

---

## Problema Identificado

### Sintoma no WF02 V87
```
Error: Invalid WF06 response format - missing dates property in all locations [line 61]
```

### Comportamento Observado
- WF06 executava COMPLETAMENTE (todos os nodes incluindo "Respond to Webhook")
- HTTP Request recebia apenas: `{"message":"Workflow was started"}`
- WF02 buscava `dates` property que não existia na resposta

### Logs n8n 2.15.0
```
16:46:42.817   Running node "Respond to Webhook" finished successfully
16:46:42.817   Workflow execution finished successfully
```

✅ Workflow executado com sucesso
❌ Resposta não retornada ao caller (HTTP Request)

---

## Causa Raiz

### n8n 2.15.0 Breaking Change
O **Webhook Trigger** node mudou comportamento padrão:
- **Antes (< 2.15)**: `responseMode` não era obrigatório, assumia "responseNode"
- **Depois (≥ 2.15)**: Sem `responseMode`, webhook responde IMEDIATAMENTE com mensagem assíncrona

### Webhook Modes (n8n 2.15+)
| Mode | Comportamento | Response Timing |
|------|---------------|-----------------|
| **responseNode** | Usa "Respond to Webhook" node | Após workflow completo |
| **lastNode** | Retorna output do último node | Após workflow completo |
| **onReceived** | Responde imediatamente | Não espera workflow |

**WF06 V2.1**: Sem `responseMode` → Comportamento **onReceived** (assíncrono)
**WF06 V2.2**: `responseMode: "responseNode"` → Espera "Respond to Webhook" ✅

---

## Solução Implementada

### Alteração no Webhook Trigger
**Antes** (`06_calendar_availability_service_v2_1.json`):
```json
{
  "parameters": {
    "httpMethod": "POST",
    "path": "calendar-availability",
    "options": {}
  }
}
```

**Depois** (`06_calendar_availability_service_v2_2.json`):
```json
{
  "parameters": {
    "httpMethod": "POST",
    "path": "calendar-availability",
    "responseMode": "responseNode",
    "options": {}
  }
}
```

**Mudança**: Adiciona `"responseMode": "responseNode"`

---

## Deploy

### 1. Import WF06 V2.2
```bash
# Arquivo criado em:
n8n/workflows/06_calendar_availability_service_v2_2.json

# n8n UI:
# Menu → Import from file → 06_calendar_availability_service_v2_2.json
```

### 2. Ativar Workflow
1. Abrir WF06 V2.2 no n8n
2. Clicar em "Active" (toggle verde)
3. **IMPORTANTE**: Desativar V2.1 para evitar conflito de webhook path

### 3. Validar Fix
```bash
# Teste direto do endpoint
curl -X POST http://localhost:5678/webhook/calendar-availability \
  -H "Content-Type: application/json" \
  -d '{"action":"next_dates","count":3,"service_type":"energia_solar","duration_minutes":120}'
```

**✅ ESPERADO (V2.2)**:
```json
{
  "success": true,
  "action": "next_dates",
  "dates": [
    {
      "date": "2026-04-21",
      "display": "Amanhã (21/04)",
      "day_of_week": "Segunda",
      "total_slots": 8,
      "quality": "high"
    },
    ...
  ],
  "total_available": 3
}
```

**❌ PROBLEMA (V2.1)**:
```json
{
  "message": "Workflow was started"
}
```

### 4. Testar Integração WF02 + WF06
```bash
# Executar WF02 com service 1 (Solar) ou 3 (Projetos)
# Deve chegar ao state 8 (present_available_dates) com sucesso
```

---

## Validação Completa

### Checklist
- [x] WF06 V2.2 criado com `responseMode: "responseNode"`
- [ ] Import no n8n e ativação
- [ ] Teste direto retorna JSON com `dates` array
- [ ] WF02 state 8 processa resposta sem erro "missing dates property"
- [ ] Integração WF02 + WF06 funcional

### Logs de Sucesso
```
✅ [WF06 V2.2] Response formatted: {"success":true,"dates":[...]}
✅ [WF02 V87] Prepare WF06 Next Dates Data finished successfully
✅ [WF02 V87] State Machine Logic: state 8 completed
```

---

## Referências

**n8n Docs**:
- Webhook Node: https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.webhook/
- Respond to Webhook: https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.respondtowebhook/

**Related Issues**:
- n8n Community: "N8n only returning 'Workflow was started'"
- GitHub: n8n 2.15.0 webhook responseMode breaking change

**Project Context**:
- WF02 V87: `/n8n/workflows/02_ai_agent_conversation_V87_RESPONSE_FORMAT_FIX.json`
- WF06 V2.1: `/n8n/workflows/06_calendar_availability_service_v2_1.json` (broken)
- WF06 V2.2: `/n8n/workflows/06_calendar_availability_service_v2_2.json` (fixed)

---

**Status**: ✅ Fix implementado, aguardando deploy e validação
**Next**: Import V2.2 no n8n → Testar → Validar integração com WF02
