# Appointment Scheduler V3 - Análise Profunda e Plano Completo

> **Status**: 🚨 ANÁLISE CRÍTICA - Problema Identificado
> **Data**: 2026-03-18
> **Erro Reportado**: `appointment_id is required [line 6]` no nó `Validate Input Data`
> **Execução**: http://localhost:5678/workflow/yu0sW0TdzQpxqzb9/executions/13861

---

## 🔍 ROOT CAUSE ANALYSIS

### Problema Principal: **appointment_id NÃO está sendo enviado pelo WF02**

#### Evidência 1: Erro no Validate Input Data
```javascript
// Nó: Validate Input Data (linha 18-31 do WF05 V2.1)
const inputData = $input.first().json;

// Validate appointment_id exists
if (!inputData.appointment_id) {
    throw new Error('appointment_id is required');  // ❌ ERRO AQUI
}
```

**Análise**: O nó **recebe dados vazios ou sem o campo `appointment_id`**.

---

#### Evidência 2: Banco de Dados VAZIO
```bash
# Query executada:
SELECT id, lead_id, scheduled_date, service_type, status
FROM appointments
ORDER BY created_at DESC LIMIT 3;

# Resultado:
(0 rows)  # ❌ NENHUM APPOINTMENT CRIADO!
```

**Conclusão**: O WF02 **NUNCA está criando o appointment** antes de chamar o WF05!

---

#### Evidência 3: Trigger "Trigger Appointment Scheduler" existe no WF02
```bash
# Grep mostra que o nó existe em TODAS as versões do WF02:
/n8n/workflows/02_ai_agent_conversation_V69_2_NEXT_STAGE_FIX.json:306: "name": "Trigger Appointment Scheduler"
/n8n/workflows/02_ai_agent_conversation_V69_2_NEXT_STAGE_FIX.json:599: "node": "Trigger Appointment Scheduler"
/n8n/workflows/02_ai_agent_conversation_V69_2_NEXT_STAGE_FIX.json:617: "Trigger Appointment Scheduler": {
```

**Mas**: O nó de **CREATE APPOINTMENT NO BANCO** está FALTANDO antes do trigger!

---

## 🚨 CAUSA RAIZ IDENTIFICADA

### WF02 Estado "confirmation" NÃO cria appointment antes de chamar WF05

**Fluxo ATUAL (ERRADO)**:
```
WF02: Estado "confirmation"
  ↓
  [usuário responde "sim"]
  ↓
  ❌ NÃO CRIA APPOINTMENT NO BANCO
  ↓
  Trigger Appointment Scheduler (WF05)
  ↓
  WF05: Validate Input Data
  ↓
  ❌ ERRO: appointment_id is required
```

**Fluxo CORRETO (V3)**:
```
WF02: Estado "confirmation"
  ↓
  [usuário responde "sim"]
  ↓
  ✅ CREATE APPOINTMENT (INSERT INTO appointments)
  ↓
  ✅ Capture appointment_id retornado
  ↓
  ✅ Trigger Appointment Scheduler (enviar appointment_id)
  ↓
  WF05: Validate Input Data
  ↓
  ✅ SUCCESS
```

---

## 📋 PLANO V3 - SOLUÇÃO COMPLETA

### Fase 1: Adicionar Nó "Create Appointment" no WF02 ✅

#### 1.1. Novo Nó PostgreSQL: "Create Appointment in Database"

**Posição**: ANTES do nó "Trigger Appointment Scheduler"

**Query SQL**:
```sql
-- Criar appointment no banco
INSERT INTO appointments (
    id,
    lead_id,
    scheduled_date,
    scheduled_time_start,
    scheduled_time_end,
    service_type,
    notes,
    status,
    created_at,
    updated_at
)
VALUES (
    gen_random_uuid(),  -- Gera UUID automaticamente
    $1,                 -- lead_id
    $2,                 -- scheduled_date
    $3,                 -- scheduled_time_start
    $4,                 -- scheduled_time_end
    $5,                 -- service_type
    $6,                 -- notes
    'agendado',         -- status inicial
    NOW(),
    NOW()
)
RETURNING
    id as appointment_id,
    lead_id,
    scheduled_date,
    scheduled_time_start,
    scheduled_time_end,
    service_type,
    status;
```

**Parameters** (queryParameters):
```javascript
={{
    $json.lead_id
}},={{
    $json.scheduled_date
}},={{
    $json.scheduled_time_start
}},={{
    $json.scheduled_time_end
}},={{
    $json.service_type
}},={{
    'Agendamento via WhatsApp Bot - Cliente: ' + $json.lead_name
}}
```

**Configuração do Nó**:
```json
{
    "parameters": {
        "operation": "executeQuery",
        "query": "/* SQL acima */",
        "additionalFields": {
            "queryParameters": "/* Parameters acima */"
        }
    },
    "id": "create-appointment-database",
    "name": "Create Appointment in Database",
    "type": "n8n-nodes-base.postgres",
    "typeVersion": 2,
    "position": [2450, 300],  // ANTES do Trigger Appointment Scheduler
    "credentials": {
        "postgres": {
            "id": "1",
            "name": "PostgreSQL - E2 Bot"
        }
    },
    "alwaysOutputData": true,
    "continueOnFail": false,
    "notes": "V3: CREATE appointment BEFORE triggering scheduler workflow"
}
```

---

#### 1.2. Modificar Nó "Trigger Appointment Scheduler"

**ANTES (V69.2)**:
```json
{
    "parameters": {
        "workflowId": "yu0sW0TdzQpxqzb9",  // ID hardcoded
        "source": {
            "mode": "static"
        }
    },
    "id": "trigger-appointment-scheduler",
    "name": "Trigger Appointment Scheduler",
    "type": "n8n-nodes-base.executeWorkflow",
    "typeVersion": 1,
    "position": [2650, 300]
}
```

**DEPOIS (V3)**:
```json
{
    "parameters": {
        "workflowId": "yu0sW0TdzQpxqzb9",  // ID do WF05
        "source": {
            "mode": "static",
            "value": {
                "appointment_id": "={{ $('Create Appointment in Database').item.json.appointment_id }}",
                "source": "wf02_confirmation",
                "trigger_timestamp": "={{ new Date().toISOString() }}"
            }
        }
    },
    "id": "trigger-appointment-scheduler-v3",
    "name": "Trigger Appointment Scheduler",
    "type": "n8n-nodes-base.executeWorkflow",
    "typeVersion": 1,
    "position": [2650, 300],
    "notes": "V3: Send appointment_id from database INSERT"
}
```

---

#### 1.3. Nova Conexão no WF02

**ANTES (V69.2)**:
```json
"Send Confirmation Summary Message": {
    "main": [
        [
            {
                "node": "Trigger Appointment Scheduler",  // ❌ SEM CREATE ANTES
                "type": "main",
                "index": 0
            }
        ]
    ]
}
```

**DEPOIS (V3)**:
```json
"Send Confirmation Summary Message": {
    "main": [
        [
            {
                "node": "Create Appointment in Database",  // ✅ NOVO NÓ
                "type": "main",
                "index": 0
            }
        ]
    ]
},
"Create Appointment in Database": {
    "main": [
        [
            {
                "node": "Trigger Appointment Scheduler",  // ✅ AGORA COM appointment_id
                "type": "main",
                "index": 0
            }
        ]
    ]
}
```

---

### Fase 2: Capturar Dados do Agendamento no Estado "confirmation"

#### 2.1. Problema: Dados de agendamento (data/hora) NÃO estão sendo coletados

**Análise**: O WF02 atual coleta:
- ✅ lead_name
- ✅ phone_number
- ✅ email
- ✅ city
- ✅ service_type

**FALTANDO**:
- ❌ scheduled_date
- ❌ scheduled_time_start
- ❌ scheduled_time_end

#### 2.2. Solução: Adicionar Estados de Coleta de Agendamento

**Novo Fluxo de Estados (V3)**:
```
1. greeting → Menu (5 services)
2. service_selection → Capture (1-5)
3. collect_name → Get name + WhatsApp confirm
4. collect_phone_whatsapp_confirmation → Confirm/alternative
5. collect_phone_alternative → Alternative phone
6. collect_email → Email or skip
7. collect_city → City
8. collect_appointment_date → Data da visita        ✅ NOVO
9. collect_appointment_time → Horário da visita     ✅ NOVO
10. confirmation → Summary + CREATE APPOINTMENT + triggers
```

#### 2.3. Novo Estado: "collect_appointment_date"

**Prompt do Agente**:
```javascript
// Estado: collect_appointment_date
const systemPrompt = `
Você está coletando a DATA PREFERIDA para a visita técnica.

DADOS COLETADOS:
- Nome: ${collectedData.lead_name}
- Serviço: ${collectedData.service_type_display}
- Cidade: ${collectedData.city}

TAREFA:
1. Pergunte: "Qual a melhor data para a visita técnica?"
2. Aceite formatos: DD/MM/YYYY, DD/MM, ou "próxima segunda", "amanhã"
3. Valide:
   - Data não pode ser no passado
   - Data deve ser dia útil (segunda a sexta)
   - Data não pode ser feriado (verificar lista)

REGRAS:
- Se data inválida: explique e peça nova data
- Se data válida: extraia no formato YYYY-MM-DD
- Armazene em: collected_data.scheduled_date

NEXT STATE:
- Data válida → collect_appointment_time
- Data inválida → collect_appointment_date (repete)
`;
```

**Validação**:
```javascript
// Nó: Validate Appointment Date
const userResponse = $json.message;
const today = new Date();
today.setHours(0, 0, 0, 0);

// Parse date (vários formatos)
let parsedDate;
if (userResponse.match(/\d{2}\/\d{2}\/\d{4}/)) {
    // DD/MM/YYYY
    const [day, month, year] = userResponse.split('/');
    parsedDate = new Date(`${year}-${month}-${day}`);
} else if (userResponse.match(/\d{2}\/\d{2}/)) {
    // DD/MM (assume ano atual)
    const [day, month] = userResponse.split('/');
    const year = new Date().getFullYear();
    parsedDate = new Date(`${year}-${month}-${day}`);
} else if (userResponse.toLowerCase().includes('amanhã')) {
    parsedDate = new Date(today);
    parsedDate.setDate(parsedDate.getDate() + 1);
} else if (userResponse.toLowerCase().includes('próxima segunda')) {
    parsedDate = new Date(today);
    const daysUntilMonday = (1 + 7 - parsedDate.getDay()) % 7;
    parsedDate.setDate(parsedDate.getDate() + daysUntilMonday + 7);
}

// Validações
if (!parsedDate || isNaN(parsedDate)) {
    return {
        ...collected_data,
        validation_error: 'Data inválida. Use DD/MM/YYYY ou DD/MM.',
        next_stage: 'collect_appointment_date'
    };
}

if (parsedDate < today) {
    return {
        ...collected_data,
        validation_error: 'Data não pode ser no passado.',
        next_stage: 'collect_appointment_date'
    };
}

const dayOfWeek = parsedDate.getDay();
if (dayOfWeek === 0 || dayOfWeek === 6) {
    return {
        ...collected_data,
        validation_error: 'Visitas apenas de segunda a sexta-feira.',
        next_stage: 'collect_appointment_date'
    };
}

// Data válida
return {
    ...collected_data,
    scheduled_date: parsedDate.toISOString().split('T')[0],  // YYYY-MM-DD
    next_stage: 'collect_appointment_time'
};
```

---

#### 2.4. Novo Estado: "collect_appointment_time"

**Prompt do Agente**:
```javascript
// Estado: collect_appointment_time
const systemPrompt = `
Você está coletando o HORÁRIO PREFERIDO para a visita técnica.

DADOS COLETADOS:
- Data: ${collectedData.scheduled_date} (formatado: ${formatDateBR(collectedData.scheduled_date)})
- Serviço: ${collectedData.service_type_display}

TAREFA:
1. Pergunte: "Qual o melhor horário? (exemplo: 09:00 ou manhã)"
2. Aceite formatos: HH:MM, "manhã" (09:00-12:00), "tarde" (14:00-17:00)
3. Valide:
   - Horário comercial: 08:00 às 18:00
   - Horário mínimo de 1h30 para visita

REGRAS:
- Manhã → 09:00-11:00 (2h)
- Tarde → 14:00-16:00 (2h)
- Horário específico → calcular +2h automaticamente

NEXT STATE:
- Horário válido → confirmation
- Horário inválido → collect_appointment_time (repete)
`;
```

**Validação**:
```javascript
// Nó: Validate Appointment Time
const userResponse = $json.message.toLowerCase();
let timeStart, timeEnd;

// Parse time
if (userResponse.includes('manhã')) {
    timeStart = '09:00';
    timeEnd = '11:00';
} else if (userResponse.includes('tarde')) {
    timeStart = '14:00';
    timeEnd = '16:00';
} else if (userResponse.match(/\d{2}:\d{2}/)) {
    const match = userResponse.match(/(\d{2}):(\d{2})/);
    timeStart = `${match[1]}:${match[2]}`;

    // Calcular +2h
    const [hour, min] = timeStart.split(':').map(Number);
    const endHour = hour + 2;
    timeEnd = `${String(endHour).padStart(2, '0')}:${String(min).padStart(2, '0')}`;
}

// Validar horário comercial
const startHour = parseInt(timeStart.split(':')[0]);
const endHour = parseInt(timeEnd.split(':')[0]);

if (startHour < 8 || endHour > 18) {
    return {
        ...collected_data,
        validation_error: 'Horário deve ser entre 08:00 e 18:00.',
        next_stage: 'collect_appointment_time'
    };
}

// Horário válido
return {
    ...collected_data,
    scheduled_time_start: timeStart,
    scheduled_time_end: timeEnd,
    next_stage: 'confirmation'
};
```

---

### Fase 3: Modificar Estado "confirmation" para Incluir Dados de Agendamento

#### 3.1. Atualizar Mensagem de Resumo

**ANTES (V69.2)**:
```
📋 *RESUMO DOS SEUS DADOS*

✅ Nome: João Silva
✅ Telefone: (62) 99999-9999
✅ Email: joao@example.com
✅ Cidade: Goiânia
✅ Serviço: Energia Solar

Tudo certo? Responda *SIM* para confirmar.
```

**DEPOIS (V3)**:
```
📋 *RESUMO DA VISITA TÉCNICA*

👤 *SEUS DADOS:*
✅ Nome: João Silva
✅ Telefone: (62) 99999-9999
✅ Email: joao@example.com
✅ Cidade: Goiânia

🔧 *SERVIÇO:*
✅ Energia Solar

📅 *AGENDAMENTO:*
✅ Data: 20/03/2026 (Quinta-feira)
✅ Horário: 09:00 às 11:00

Confirma o agendamento? Responda *SIM* para confirmar.
```

---

### Fase 4: Atualizar Schema do Banco (se necessário)

#### 4.1. Verificar Constraints

**Query de Verificação**:
```sql
-- Verificar se appointments tem todos os campos
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'appointments'
ORDER BY ordinal_position;
```

**Campos Necessários**:
- ✅ id (UUID)
- ✅ lead_id (INTEGER)
- ✅ scheduled_date (DATE)
- ✅ scheduled_time_start (TIME)
- ✅ scheduled_time_end (TIME)
- ✅ service_type (VARCHAR)
- ✅ notes (TEXT)
- ✅ status (VARCHAR) - incluindo 'erro_calendario' (já adicionado no V2.1)
- ✅ google_calendar_event_id (VARCHAR)
- ✅ created_at (TIMESTAMP)
- ✅ updated_at (TIMESTAMP)

---

### Fase 5: Implementação do Script Python Gerador V3

#### 5.1. Arquivo: `scripts/generate-workflow-v70-complete-appointment-fix.py`

**Estrutura**:
```python
#!/usr/bin/env python3
"""
Generate WF02 V70 - Complete Appointment Scheduler Fix
Adiciona:
1. Estados collect_appointment_date e collect_appointment_time
2. Nó Create Appointment in Database
3. Trigger Appointment Scheduler com appointment_id
"""

import json
from datetime import datetime

def generate_wf02_v70():
    """
    Generate complete WF02 V70 with appointment collection
    """

    # Base: WF02 V69.2
    with open('n8n/workflows/02_ai_agent_conversation_V69_2_NEXT_STAGE_FIX.json') as f:
        workflow = json.load(f)

    # Update metadata
    workflow['name'] = '02 - AI Agent Conversation V70 (Complete Appointment Fix)'
    workflow['versionId'] = '70'

    # 1. Add estado collect_appointment_date (ID: state-8)
    state_8_node = create_state_node(
        state_id='collect_appointment_date',
        state_number=8,
        position=[1850, 300],
        system_prompt=APPOINTMENT_DATE_PROMPT,
        next_state_logic='collect_appointment_time',
        validation_function='validate_appointment_date'
    )

    # 2. Add estado collect_appointment_time (ID: state-9)
    state_9_node = create_state_node(
        state_id='collect_appointment_time',
        state_number=9,
        position=[2050, 300],
        system_prompt=APPOINTMENT_TIME_PROMPT,
        next_state_logic='confirmation',
        validation_function='validate_appointment_time'
    )

    # 3. Add nó Create Appointment in Database
    create_appointment_node = {
        "parameters": {
            "operation": "executeQuery",
            "query": CREATE_APPOINTMENT_SQL,
            "additionalFields": {
                "queryParameters": CREATE_APPOINTMENT_PARAMS
            }
        },
        "id": "create-appointment-database-v3",
        "name": "Create Appointment in Database",
        "type": "n8n-nodes-base.postgres",
        "typeVersion": 2,
        "position": [2450, 300],
        "credentials": {
            "postgres": {"id": "1", "name": "PostgreSQL - E2 Bot"}
        },
        "alwaysOutputData": True,
        "notes": "V3: CREATE appointment BEFORE triggering scheduler"
    }

    # 4. Modify Trigger Appointment Scheduler
    trigger_node = find_node_by_name(workflow, 'Trigger Appointment Scheduler')
    trigger_node['parameters']['source'] = {
        "mode": "static",
        "value": {
            "appointment_id": "={{ $('Create Appointment in Database').item.json.appointment_id }}",
            "source": "wf02_confirmation"
        }
    }

    # 5. Update connections
    update_connections(workflow, {
        'collect_city': 'collect_appointment_date',
        'collect_appointment_date': 'collect_appointment_time',
        'collect_appointment_time': 'confirmation',
        'Send Confirmation Summary Message': 'Create Appointment in Database',
        'Create Appointment in Database': 'Trigger Appointment Scheduler'
    })

    # 6. Update confirmation summary template
    update_confirmation_template(workflow)

    # Save
    output_path = 'n8n/workflows/02_ai_agent_conversation_V70_COMPLETE_APPOINTMENT_FIX.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print(f"✅ WF02 V70 gerado: {output_path}")
    return output_path

if __name__ == '__main__':
    generate_wf02_v70()
```

---

## 🎯 RESUMO EXECUTIVO - PLANO V3

### Mudanças Principais

| Componente | V69.2 | V3 |
|------------|-------|-----|
| **Estados** | 8 | 10 (+2) |
| **Coleta de Dados** | Nome, Tel, Email, Cidade | + Data e Horário |
| **CREATE Appointment** | ❌ NÃO | ✅ SIM (antes de chamar WF05) |
| **appointment_id** | ❌ Não enviado | ✅ Enviado do INSERT |
| **Validação de Horário** | ❌ NÃO | ✅ SIM (08:00-18:00) |
| **Resumo de Confirmação** | Básico | Completo (com agendamento) |

---

### Problemas Resolvidos

1. ✅ **appointment_id is required**: Resolvido criando appointment ANTES de chamar WF05
2. ✅ **Banco vazio**: Resolvido com INSERT INTO appointments
3. ✅ **Dados de agendamento ausentes**: Resolvido com novos estados de coleta
4. ✅ **Validação de horário**: Resolvido com validação 08:00-18:00
5. ✅ **Resumo incompleto**: Resolvido incluindo data/hora na confirmação

---

### Timeline de Implementação

| Fase | Duração | Dependências |
|------|---------|--------------|
| Criar script Python V70 | 30 min | - |
| Gerar workflow WF02 V70 | 5 min | Script pronto |
| Import no n8n | 5 min | Workflow gerado |
| Testes de coleta de dados | 20 min | Import completo |
| Testes de criação appointment | 15 min | Dados coletados |
| Testes de chamada WF05 | 10 min | Appointment criado |
| **TOTAL** | **~1h25min** | - |

---

### Próximos Passos

1. **Criar script Python** `generate-workflow-v70-complete-appointment-fix.py`
2. **Gerar WF02 V70** com novos estados e nó de criação
3. **Import no n8n** e desativar V69.2
4. **Teste completo** do fluxo: greeting → agendamento → confirmação → WF05
5. **Validar banco** que appointment foi criado com sucesso
6. **Validar WF05** que recebe appointment_id corretamente

---

## 📁 Arquivos a Serem Criados

| Arquivo | Descrição |
|---------|-----------|
| `scripts/generate-workflow-v70-complete-appointment-fix.py` | Gerador do WF02 V70 |
| `n8n/workflows/02_ai_agent_conversation_V70_COMPLETE_APPOINTMENT_FIX.json` | Workflow V70 gerado |
| `docs/PLAN_APPOINTMENT_SCHEDULER_V3_COMPLETE_FIX.md` | Este documento |

---

**Mantido por**: Claude Code
**Última Atualização**: 2026-03-18
**Status**: 📋 PLANO COMPLETO PRONTO PARA IMPLEMENTAÇÃO
