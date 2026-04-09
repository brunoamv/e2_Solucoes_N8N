# PLAN V74.1: Check If Scheduling Fix (Correção Crítica)

> **Date**: 2026-03-25
> **Base**: V74_APPOINTMENT_CONFIRMATION
> **Purpose**: Corrigir mismatch entre State Machine e Check If Scheduling
> **Type**: 🚨 CRITICAL BUG FIX

---

## 🚨 Problema Crítico Identificado

### **Root Cause Analysis**

**State Machine Logic** (STATE 11 - appointment_confirmation):
```javascript
case 'appointment_confirmation':
  if (message === '1') {
    nextStage = 'scheduling_redirect';  // ✅ State Machine seta ESTE VALOR
    updateData.status = 'scheduling';
    responseText = templates.scheduling_redirect;
  }
```

**Check If Scheduling** (V73.5 e V74 - AMBOS ERRADOS):
```json
{
  "value1": "={{ $node['Build Update Queries'].json.next_stage }}",
  "value2": "scheduling"  // ❌ COMPARA COM VALOR ERRADO!
}
```

**Resultado**: IF node **NUNCA** retorna TRUE porque:
- State Machine seta: `next_stage = 'scheduling_redirect'`
- IF node compara: `next_stage === 'scheduling'` ❌ **MISMATCH!**

**Consequência**: WF05 (Appointment Scheduler) **NUNCA** é trigado!

---

## 🔧 Solução V74.1

### **Mudança Única e Crítica**

**Nó**: `Check If Scheduling`
**ID**: `9151a253-13d4-4084-93ef-48397740ea7e` (manter este)
**Ação**: Corrigir `value2` de `"scheduling"` → `"scheduling_redirect"`

#### **ANTES (V74 - ERRADO)** ❌
```json
{
  "parameters": {
    "conditions": {
      "string": [{
        "value1": "={{ $node['Build Update Queries'].json.next_stage }}",
        "value2": "scheduling"  // ❌ ERRADO!
      }]
    }
  },
  "name": "Check If Scheduling",
  "type": "n8n-nodes-base.if"
}
```

#### **DEPOIS (V74.1 - CORRETO)** ✅
```json
{
  "parameters": {
    "conditions": {
      "string": [{
        "value1": "={{ $node['Build Update Queries'].json.next_stage }}",
        "operation": "equals",
        "value2": "scheduling_redirect"  // ✅ CORRIGIDO!
      }]
    }
  },
  "name": "Check If Scheduling",
  "type": "n8n-nodes-base.if"
}
```

---

## 📋 Implementação

### **Step 1: Remover Nó Duplicado**

V74 tem **DOIS** nós "Check If Scheduling" (bug no script de geração):

1. **ID**: `689d6869-74ad-486c-920d-75feff34c381` → ❌ **REMOVER** (valor errado)
2. **ID**: `9151a253-13d4-4084-93ef-48397740ea7e` → ✅ **MANTER** (será corrigido)

### **Step 2: Corrigir Nó Mantido**

**Nó ID**: `9151a253-13d4-4084-93ef-48397740ea7e`

**Alteração**:
```json
{
  "parameters": {
    "conditions": {
      "string": [{
        "value1": "={{ $node['Build Update Queries'].json.next_stage }}",
        "operation": "equals",
        "value2": "scheduling_redirect"  // ✅ CRITICAL FIX
      }]
    }
  },
  "id": "9151a253-13d4-4084-93ef-48397740ea7e",
  "name": "Check If Scheduling",
  "type": "n8n-nodes-base.if",
  "typeVersion": 1,
  "position": [1200, 512],
  "alwaysOutputData": false
}
```

### **Step 3: Verificar Conexão**

**OBRIGATÓRIO**: `Check If Scheduling` deve estar conectado a `Send WhatsApp Response`

**Send WhatsApp Response** → connections:
```json
{
  "connections": {
    "main": [[{
      "node": "Check If Scheduling",  // ✅ DEVE APONTAR AQUI
      "type": "main",
      "index": 0
    }]]
  }
}
```

**Check If Scheduling** → connections:
```json
{
  "connections": {
    "main": [
      [{
        "node": "Trigger Appointment Scheduler",  // TRUE branch
        "type": "main",
        "index": 0
      }],
      [{
        "node": "Check If Handoff",  // FALSE branch
        "type": "main",
        "index": 0
      }]
    ]
  }
}
```

---

## 🧪 Validação

### **Test Case 1: Services 1/3 + Confirm Appointment**

**Input**:
```
User: "oi"
Bot: Menu
User: "1" (Energia Solar)
... [coleta dados] ...
User: "1" (Sim, quero agendar)
... [coleta data/hora] ...
User: "1" (Confirmar agendamento)
```

**Expected Flow**:
```
STATE 11 (appointment_confirmation)
  ↓
nextStage = 'scheduling_redirect'  ✅
  ↓
Build Update Queries
  ↓
Send WhatsApp Response (template: scheduling_redirect)
  ↓
Check If Scheduling
  ↓
{{ next_stage === 'scheduling_redirect' }}  ✅ TRUE
  ↓
Trigger Appointment Scheduler (WF05 V3.6)
  ↓
Google Calendar Event Created ✅
```

**Verification**:
```sql
-- Check conversation state
SELECT phone_number, current_state, next_stage, status
FROM conversations
WHERE phone_number = '5562999999999';

-- Expected: next_stage = 'scheduling_redirect', status = 'scheduling'

-- Check appointment created
SELECT * FROM appointments
WHERE lead_name = 'Test User'
ORDER BY created_at DESC LIMIT 1;

-- Expected: Record exists with google_calendar_event_id
```

### **Test Case 2: Services 2/4/5 + Handoff**

**Input**:
```
User: "2" (Subestação)
... [coleta dados] ...
User: "2" (Falar com pessoa)
```

**Expected Flow**:
```
STATE 8 (confirmation)
  ↓
nextStage = 'handoff_comercial'  ✅
  ↓
Check If Scheduling
  ↓
{{ next_stage === 'scheduling_redirect' }}  ❌ FALSE
  ↓
Check If Handoff
  ↓
{{ next_stage === 'handoff_comercial' }}  ✅ TRUE
  ↓
Trigger Human Handoff ✅
```

---

## 📊 Comparação de Versões

| Aspecto | V73.5 | V74 (Original) | **V74.1 (Fixed)** |
|---------|-------|----------------|-------------------|
| State Machine Logic | ✅ Correto | ✅ Correto | ✅ Correto |
| Check If Scheduling value | ❌ `"scheduling"` | ❌ `"scheduling"` duplicado | ✅ `"scheduling_redirect"` |
| Nós duplicados | ❌ Não | ❌ Sim (2 nós) | ✅ Não (1 nó correto) |
| WF05 Trigger | ❌ Nunca | ❌ Nunca | ✅ Funciona |
| Conexão correta | ⚠️ Parcial | ⚠️ Parcial | ✅ Completa |
| **Status** | 🔴 Broken | 🔴 Broken | **🟢 Fixed** |

---

## 🚀 Deployment

### **Pre-Deployment Checklist**
- [ ] V74 workflow importado (base para correção)
- [ ] Backup de V73.5 disponível (rollback)
- [ ] WF05 V3.6 ativado e testado
- [ ] Database schema atualizado (appointment_reminders table)
- [ ] Evolution API conectada e funcionando

### **Deployment Steps**

```bash
# 1. Gerar V74.1 workflow corrigido
python3 scripts/generate-workflow-v74.1-check-if-scheduling-fix.py

# Output: n8n/workflows/02_ai_agent_conversation_V74.1_CHECK_IF_SCHEDULING_FIX.json

# 2. Import to n8n
# http://localhost:5678 → Import from File

# 3. Validate nodes
# - Check If Scheduling: value2 = "scheduling_redirect" ✅
# - Connections: Send WhatsApp Response → Check If Scheduling ✅
# - No duplicate nodes ✅

# 4. Deactivate V73.5
# 5. Activate V74.1
# 6. Test complete flow (Test Case 1 + 2)
# 7. Monitor executions (2h → 24h → 7d)
```

### **Rollback Plan**

```bash
# If V74.1 fails:
1. Deactivate V74.1
2. Activate V73.5 (with same bug, but known behavior)
3. Review logs:
   docker logs -f e2bot-n8n-dev | grep -E "V74.1|Check If Scheduling|ERROR"
4. Check workflow execution:
   http://localhost:5678/workflow/[workflow_id]/executions
5. Fix issues and re-deploy
```

---

## 🎯 Success Criteria

### **Functional Requirements**
- [ ] `Check If Scheduling` value2 = `"scheduling_redirect"`
- [ ] No duplicate nodes in workflow
- [ ] Connection: `Send WhatsApp Response` → `Check If Scheduling`
- [ ] TRUE branch: `Check If Scheduling` → `Trigger Appointment Scheduler`
- [ ] FALSE branch: `Check If Scheduling` → `Check If Handoff`
- [ ] WF05 triggers successfully for services 1/3 + confirm
- [ ] Google Calendar event created with correct data

### **Quality Requirements**
- [ ] No broken connections in workflow
- [ ] All data fields passed correctly between nodes
- [ ] Error handling for WF05 trigger failures
- [ ] Logging sufficient for debugging
- [ ] No execution errors in n8n logs

### **Performance Requirements**
- [ ] Total execution time < 10 seconds
- [ ] No duplicate executions
- [ ] No data loss between nodes
- [ ] WF05 trigger response < 5 seconds

---

## 📝 Notes

### **Why V73.5 Was "Working Perfectly"**

**User said**: "Aqui na v73.5 estava tudo funcionando perfeitamente"

**Reality**: V73.5 tinha o **MESMO BUG** (`value2 = "scheduling"`)!

**Possible Explanation**:
1. User may have manually tested appointment flow **without** going through STATE 11
2. Or WF05 was triggered **manually** (not via Check If Scheduling)
3. Or Check If Scheduling was **temporarily fixed** in running instance (not in saved JSON)

**Evidence**: V73.5 JSON file shows `value2 = "scheduling"` (incorrect)

### **V74 Introduction of Duplicate Node**

**How it happened**: Script generator created TWO "Check If Scheduling" nodes:
1. First with correct value (`scheduling_redirect`)
2. Second with incorrect value (`scheduling`) - copied from V73.5

**Fix**: Remove node with ID `689d6869-74ad-486c-920d-75feff34c381`

### **Critical Success Factor**

**Connection integrity**: Ensure all paths from "Send WhatsApp Response" lead to appropriate downstream logic.

```
Send WhatsApp Response
    ↓
Check If Scheduling (MUST be connected here!)
    ↓
    ├─ TRUE → Trigger Appointment Scheduler
    └─ FALSE → Check If Handoff
```

---

## 🔍 Future Enhancements (V75+)

### **V75: Enhanced Confirmation Message**
**Goal**: Show appointment details in final message (requires WF05 return data)

**Implementation**:
1. WF05 returns: `{ appointment_id, calendar_event_id, scheduled_date, scheduled_time }`
2. WF02 receives data and updates conversation
3. Send enhanced message with clickable calendar link

**Template**:
```
✅ *Agendamento Confirmado com Sucesso!*

📅 *Detalhes da Visita Técnica:*
🗓️ Data: 25/04/2026
⏰ Horário: 09:00 às 11:00
⏳ Duração: 2 horas
☀️ Serviço: Energia Solar

👤 Nome: João Silva
📍 Cidade: Goiânia - GO
📧 Confirmação enviada para: joao@email.com

🔗 *Adicionar ao Calendário:*
[Link do Google Calendar]

_Obrigado por escolher a E2 Soluções!_
```

### **V76: Appointment Title Fix**
**Goal**: Fix "Sem título" in Google Calendar events

**Implementation**: WF05 Build Calendar Event Data:
```javascript
summary: `${data.service_name} - ${data.lead_name}`
// Example: "Energia Solar - João Silva"
```

---

**Generated by**: Claude Code Analysis
**Review Status**: Ready for implementation
**Next Action**: Generate V74.1 script and test
