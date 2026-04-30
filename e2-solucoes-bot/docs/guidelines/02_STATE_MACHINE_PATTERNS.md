# State Machine Patterns - WF02 AI Agent

> **Padrão central do E2 Bot** | Atualizado: 2026-04-29
> **Status**: ✅ PRODUCTION - WF02 V114 com todas as correções implementadas

---

## 📖 Visão Geral

O **State Machine** é o coração do WF02 AI Agent, implementado no node "State Machine Logic". Ele gerencia toda a jornada conversacional do usuário através de 15 estados bem definidos, desde a saudação inicial até a conclusão do agendamento.

### Características Principais

- **15 Estados Sequenciais**: Fluxo lógico que guia o usuário passo a passo
- **Proactive UX (V76+)**: Guia o usuário ao invés de validar reatividade
- **Integração WF06**: Estados especiais para chamadas ao serviço de calendário
- **Persistência de Estado**: Todos os estados salvos no PostgreSQL
- **Recuperação de Contexto**: Retomada de conversas interrompidas
- **Validação Inline**: Validação durante coleta, não após

---

## 🎯 Os 15 Estados

### 1. Fluxo Principal (9 Estados)

```yaml
greeting:
  descrição: "Saudação inicial e apresentação do sistema"
  próximo: service_selection
  validação: nenhuma

service_selection:
  descrição: "Usuário escolhe entre 1 (agendar) ou 2 (comercial)"
  próximo: collect_name | handoff_comercial
  validação: "1" ou "2" apenas

collect_name:
  descrição: "Coleta nome completo do usuário"
  próximo: collect_phone
  validação: mínimo 2 palavras

collect_phone:
  descrição: "Coleta telefone com código de área"
  próximo: collect_email
  validação: formato brasileiro (DDD + número)

collect_email:
  descrição: "Coleta endereço de email"
  próximo: collect_state
  validação: formato email válido

collect_state:
  descrição: "Coleta estado (UF)"
  próximo: collect_city
  validação: UF válida (GO, DF, etc)

collect_city:
  descrição: "Coleta cidade"
  próximo: confirmation
  validação: string não vazia

confirmation:
  descrição: "Apresenta dados coletados para confirmação"
  próximo: trigger_wf06_next_dates | collect_name (se recusar)
  validação: confirmação ou recusa

handoff_comercial:
  descrição: "Transferência para equipe comercial"
  próximo: completed
  validação: nenhuma
```

### 2. Estados de Integração WF06 (4 Estados)

```yaml
trigger_wf06_next_dates:
  descrição: "Marca flag para chamar WF06 (próximas 3 datas)"
  próximo: awaiting_wf06_next_dates
  ação: "Define trigger_wf06_next_dates = true"

awaiting_wf06_next_dates:
  descrição: "Aguarda retorno do WF06 com datas disponíveis"
  próximo: trigger_wf06_available_slots
  dados_esperados: "date_suggestions (array de datas)"

trigger_wf06_available_slots:
  descrição: "Marca flag para chamar WF06 (horários da data escolhida)"
  próximo: awaiting_wf06_available_slots
  ação: "Define trigger_wf06_available_slots = true"

awaiting_wf06_available_slots:
  descrição: "Aguarda retorno do WF06 com horários disponíveis"
  próximo: scheduling
  dados_esperados: "slot_suggestions (array de horários)"
```

### 3. Estados Finais (2 Estados)

```yaml
scheduling:
  descrição: "Processa agendamento final e dispara WF05 + WF07"
  próximo: completed
  ação: |
    - Salva agendamento no PostgreSQL
    - Dispara WF05 (cria appointment)
    - Dispara WF07 (envia email de confirmação)

completed:
  descrição: "Conversa finalizada com sucesso"
  próximo: null
  ação: "Estado terminal, nenhuma próxima ação"
```

---

## 🔧 Estrutura do State Machine Logic

### Template Base (JavaScript n8n Code Node)

```javascript
// ============================================================
// STATE MACHINE LOGIC - WF02 V114
// ============================================================

const items = $input.all();
const results = [];

for (const item of items) {
  const phone = item.json.phone_number;
  const message = item.json.message_text?.trim().toLowerCase() || '';
  const currentState = item.json.state_machine_state || 'greeting';
  const collectedData = item.json.collected_data || {};

  let response_text = '';
  let next_stage = currentState;
  let trigger_wf06_next_dates = false;
  let trigger_wf06_available_slots = false;

  // ============================================================
  // IMPORTANTE: Toda lógica de estado DEVE retornar:
  // {
  //   response_text: string,
  //   next_stage: string,
  //   collected_data: object,
  //   trigger_wf06_next_dates?: boolean,
  //   trigger_wf06_available_slots?: boolean
  // }
  // ============================================================

  switch(currentState) {
    case 'greeting':
      response_text = `Olá! 👋 Sou a assistente virtual da Cocal-GO.\n\n` +
                     `Como posso ajudar você hoje?\n\n` +
                     `1️⃣ - Agendar uma reunião técnica\n` +
                     `2️⃣ - Falar com a equipe comercial`;
      next_stage = 'service_selection';
      break;

    case 'service_selection':
      if (message === '1') {
        response_text = `Ótimo! Vamos agendar sua reunião técnica. 📅\n\n` +
                       `Para começar, preciso de algumas informações.\n\n` +
                       `Por favor, me informe seu *nome completo*:`;
        next_stage = 'collect_name';
      } else if (message === '2') {
        response_text = `Perfeito! Vou transferir você para nossa equipe comercial.\n\n` +
                       `Em breve um de nossos consultores entrará em contato. 👨‍💼`;
        next_stage = 'handoff_comercial';
      } else {
        // Proactive UX: Guia ao invés de validar
        response_text = `Por favor, escolha uma das opções:\n\n` +
                       `1️⃣ - Agendar uma reunião técnica\n` +
                       `2️⃣ - Falar com a equipe comercial`;
        next_stage = 'service_selection'; // Permanece no mesmo estado
      }
      break;

    case 'collect_name':
      // Validação inline: aceita qualquer texto com 2+ palavras
      const words = message.split(/\s+/).filter(w => w.length > 0);
      if (words.length >= 2) {
        collectedData.name = message;
        response_text = `Prazer em conhecê-lo, ${message.split(' ')[0]}! 😊\n\n` +
                       `Agora, por favor informe seu *telefone* com DDD:`;
        next_stage = 'collect_phone';
      } else {
        response_text = `Por favor, informe seu *nome completo* (nome e sobrenome):`;
        next_stage = 'collect_name'; // Permanece no estado
      }
      break;

    case 'collect_phone':
      // Validação de telefone brasileiro
      const cleanPhone = message.replace(/\D/g, '');
      if (cleanPhone.length >= 10 && cleanPhone.length <= 11) {
        collectedData.phone = cleanPhone;
        response_text = `Perfeito! 📱\n\n` +
                       `Agora preciso do seu *e-mail*:`;
        next_stage = 'collect_email';
      } else {
        response_text = `Por favor, informe um telefone válido com DDD.\n\n` +
                       `Exemplo: (62) 99999-9999`;
        next_stage = 'collect_phone';
      }
      break;

    case 'collect_email':
      // Validação simples de email
      if (message.includes('@') && message.includes('.')) {
        collectedData.email = message;
        response_text = `Ótimo! 📧\n\n` +
                       `Qual é o seu *estado* (UF)?\n\n` +
                       `Exemplo: GO, DF, SP`;
        next_stage = 'collect_state';
      } else {
        response_text = `Por favor, informe um e-mail válido.\n\n` +
                       `Exemplo: seunome@email.com`;
        next_stage = 'collect_email';
      }
      break;

    case 'collect_state':
      collectedData.state = message.toUpperCase();
      response_text = `Perfeito! 🗺️\n\n` +
                     `Agora informe sua *cidade*:`;
      next_stage = 'collect_city';
      break;

    case 'collect_city':
      collectedData.city = message;
      response_text = `Excelente! Vamos confirmar seus dados:\n\n` +
                     `📋 *DADOS CADASTRADOS*\n` +
                     `━━━━━━━━━━━━━━━━━━\n` +
                     `👤 Nome: ${collectedData.name}\n` +
                     `📱 Telefone: ${collectedData.phone}\n` +
                     `📧 E-mail: ${collectedData.email}\n` +
                     `🗺️ Estado: ${collectedData.state}\n` +
                     `🏙️ Cidade: ${collectedData.city}\n\n` +
                     `Os dados estão corretos?\n\n` +
                     `✅ - Sim, confirmar\n` +
                     `❌ - Não, recomeçar`;
      next_stage = 'confirmation';
      break;

    case 'confirmation':
      if (message.includes('sim') || message.includes('✅')) {
        response_text = `Dados confirmados! ✅\n\n` +
                       `Agora vou buscar as próximas datas disponíveis para sua reunião...\n\n` +
                       `⏳ Aguarde um momento...`;
        next_stage = 'trigger_wf06_next_dates';
        trigger_wf06_next_dates = true; // CRÍTICO: Marca flag para Check If WF06
      } else {
        response_text = `Sem problemas! Vamos recomeçar.\n\n` +
                       `Por favor, me informe seu *nome completo*:`;
        next_stage = 'collect_name';
        collectedData = {}; // Reset dados coletados
      }
      break;

    case 'trigger_wf06_next_dates':
      // Estado intermediário: aguarda Check If WF06 processar
      response_text = `Buscando próximas datas disponíveis...\n\n` +
                     `⏳ Por favor, aguarde...`;
      next_stage = 'awaiting_wf06_next_dates';
      break;

    case 'awaiting_wf06_next_dates':
      // WF06 já retornou com date_suggestions
      const dates = item.json.date_suggestions || [];
      if (dates.length > 0) {
        response_text = `📅 *DATAS DISPONÍVEIS*\n` +
                       `━━━━━━━━━━━━━━━━━━\n\n`;
        dates.forEach((date, index) => {
          response_text += `${index + 1}️⃣ - ${date}\n`;
        });
        response_text += `\nPor favor, escolha uma opção (1, 2 ou 3):`;
        next_stage = 'trigger_wf06_available_slots';
      } else {
        response_text = `Desculpe, não há datas disponíveis no momento.\n\n` +
                       `Nossa equipe entrará em contato em breve. 📞`;
        next_stage = 'completed';
      }
      break;

    case 'trigger_wf06_available_slots':
      // Usuário escolheu uma data
      const dateChoice = parseInt(message);
      const dates2 = item.json.date_suggestions || [];
      if (dateChoice >= 1 && dateChoice <= dates2.length) {
        collectedData.selected_date = dates2[dateChoice - 1];
        response_text = `Data selecionada: ${dates2[dateChoice - 1]}\n\n` +
                       `Buscando horários disponíveis...\n\n` +
                       `⏳ Aguarde um momento...`;
        next_stage = 'awaiting_wf06_available_slots';
        trigger_wf06_available_slots = true; // CRÍTICO: Marca flag
      } else {
        response_text = `Por favor, escolha uma opção válida (1, 2 ou 3):`;
        next_stage = 'trigger_wf06_available_slots';
      }
      break;

    case 'awaiting_wf06_available_slots':
      // WF06 já retornou com slot_suggestions
      const slots = item.json.slot_suggestions || [];
      if (slots.length > 0) {
        response_text = `🕐 *HORÁRIOS DISPONÍVEIS*\n` +
                       `━━━━━━━━━━━━━━━━━━\n\n`;
        slots.forEach((slot, index) => {
          response_text += `${index + 1}️⃣ - ${slot}\n`;
        });
        response_text += `\nPor favor, escolha um horário:`;
        next_stage = 'scheduling';
      } else {
        response_text = `Desculpe, não há horários disponíveis para esta data.\n\n` +
                       `Por favor, escolha outra data.`;
        next_stage = 'trigger_wf06_next_dates';
        trigger_wf06_next_dates = true;
      }
      break;

    case 'scheduling':
      // Usuário escolheu horário final
      const slotChoice = parseInt(message);
      const slots2 = item.json.slot_suggestions || [];
      if (slotChoice >= 1 && slotChoice <= slots2.length) {
        collectedData.selected_slot = slots2[slotChoice - 1];
        response_text = `✅ *AGENDAMENTO CONFIRMADO!*\n` +
                       `━━━━━━━━━━━━━━━━━━\n\n` +
                       `📅 Data: ${collectedData.selected_date}\n` +
                       `🕐 Horário: ${collectedData.selected_slot}\n\n` +
                       `Você receberá um e-mail de confirmação em breve. 📧\n\n` +
                       `Obrigado por agendar com a Cocal-GO! 🎉`;
        next_stage = 'completed';
        // WF05 e WF07 serão disparados pelo Update Conversation State
      } else {
        response_text = `Por favor, escolha um horário válido:`;
        next_stage = 'scheduling';
      }
      break;

    case 'handoff_comercial':
    case 'completed':
      // Estados terminais
      response_text = `Obrigado! Até logo! 👋`;
      next_stage = 'completed';
      break;

    default:
      // Fallback: estado desconhecido
      response_text = `Desculpe, ocorreu um erro. Vamos recomeçar.\n\n` +
                     `Olá! 👋 Como posso ajudar você?`;
      next_stage = 'greeting';
      collectedData = {};
  }

  // ============================================================
  // RETORNO OBRIGATÓRIO (V106.1 FIX)
  // Todos os estados DEVEM retornar este formato exato
  // ============================================================
  results.push({
    json: {
      phone_number: phone,
      response_text: response_text,
      next_stage: next_stage,
      collected_data: collectedData,
      trigger_wf06_next_dates: trigger_wf06_next_dates,
      trigger_wf06_available_slots: trigger_wf06_available_slots,
      // Preserva outros campos do input
      conversation_id: item.json.conversation_id,
      message_text: item.json.message_text
    }
  });
}

return results;
```

---

## 🎨 Proactive UX Approach (V76+)

### Antes (Reactive Validation)

```javascript
// ❌ Abordagem antiga: Validação reativa
case 'collect_phone':
  const phone = validatePhone(message);
  if (!phone) {
    response_text = "❌ Telefone inválido!";
    next_stage = 'collect_phone';
  } else {
    // Continua
  }
```

**Problemas**:
- Mensagem de erro negativa
- Usuário não sabe o que fazer
- Experiência frustrante

### Depois (Proactive Guidance)

```javascript
// ✅ Abordagem V76+: Guia proativo
case 'collect_phone':
  const cleanPhone = message.replace(/\D/g, '');
  if (cleanPhone.length >= 10 && cleanPhone.length <= 11) {
    collectedData.phone = cleanPhone;
    response_text = `Perfeito! 📱\n\nAgora preciso do seu *e-mail*:`;
    next_stage = 'collect_email';
  } else {
    // Guia ao invés de validar
    response_text = `Por favor, informe um telefone válido com DDD.\n\n` +
                   `Exemplo: (62) 99999-9999`;
    next_stage = 'collect_phone'; // Permanece no estado
  }
```

**Benefícios**:
- Mensagem positiva e educativa
- Exemplo claro do formato esperado
- Usuário sabe exatamente o que fazer
- Experiência amigável

---

## 🔄 Integração WF06

### Fluxo de Chamada do WF06

```
State Machine          Check If WF06          WF06 Service
     |                      |                      |
     |  trigger_wf06_       |                      |
     |  next_dates=true     |                      |
     |--------------------->|                      |
     |                      |  HTTP Request        |
     |                      |--------------------->|
     |                      |                      |
     |                      |  Response            |
     |                      |  (date_suggestions)  |
     |                      |<---------------------|
     |  date_suggestions    |                      |
     |  + next_stage        |                      |
     |<---------------------|                      |
     |                      |                      |
```

### Estados de Trigger vs Awaiting

**CRÍTICO**: Entender a diferença entre estados `trigger_*` e `awaiting_*`:

```javascript
// Estado TRIGGER: Marca flag para Check If WF06 processar
case 'trigger_wf06_next_dates':
  response_text = `Buscando datas...`;
  next_stage = 'awaiting_wf06_next_dates';
  trigger_wf06_next_dates = true; // ✅ CRUCIAL: Define flag
  break;

// Estado AWAITING: WF06 já retornou com dados
case 'awaiting_wf06_next_dates':
  const dates = item.json.date_suggestions || []; // Dados do WF06
  if (dates.length > 0) {
    // Mostra datas para usuário
  }
  break;
```

### Ordem de Execução (V105 FIX)

```
1. State Machine Logic → Define trigger_wf06_next_dates = true
2. Update Conversation State → Salva no banco
3. Check If WF06 Next Dates → Verifica flag e chama WF06
4. Merge WF06 Response → Adiciona date_suggestions aos dados
5. Loop volta para State Machine Logic (estado = awaiting_wf06_next_dates)
```

**IMPORTANTE**: V105 corrigiu ordem de execução. NUNCA coloque Check If WF06 ANTES de Update Conversation State, senão ele lê estado desatualizado do banco.

---

## 📊 Persistência de Estado

### Update Conversation State Node

```sql
-- Build Update Queries V79.1 (Schema-Aligned)
UPDATE conversations
SET
  state_machine_state = '{{ $json.next_stage }}',
  collected_data = '{{ JSON.stringify($json.collected_data) }}'::jsonb,
  updated_at = NOW()
WHERE phone_number = '{{ $json.phone_number }}'
RETURNING *;
```

**CRÍTICO**: Schema-aligned query (V79.1) - NÃO usa `contact_phone` (coluna inexistente).

### Recuperação de Contexto

```sql
-- Build SQL Queries V111 (Row Locking)
SELECT
  *,
  COALESCE(
    state_machine_state,
    'greeting'
  ) as state_for_machine
FROM conversations
WHERE phone_number IN (
  '{{ $json.phone_with_code }}',
  '{{ $json.phone_without_code }}'
)
ORDER BY updated_at DESC
LIMIT 1
FOR UPDATE SKIP LOCKED;
```

**CRÍTICO**: `FOR UPDATE SKIP LOCKED` (V111) previne race conditions quando usuário envia mensagens rápidas.

---

## 🚨 Correções Críticas

### V91: State Initialization

**Problema**: Estados undefined causavam fluxo incorreto.

**Solução**:
```javascript
const currentState = item.json.state_machine_state || 'greeting';
```

Sempre inicializa com `'greeting'` se estado não existir.

### V104: State Synchronization

**Problema**: Estado no banco diferente do estado no fluxo.

**Solução**: Update Conversation State SEMPRE antes de Check If WF06.

### V105: Routing Fix

**Problema**: Check If WF06 lia estado desatualizado.

**Solução**: Ordem de execução corrigida:
```
State Machine → Update State → Check If WF06 → Loop
```

### V106.1: Response Text Fix

**Problema**: Estados sem `response_text` causavam mensagens vazias.

**Solução**: TODOS os estados devem retornar:
```javascript
{
  response_text: string,      // ✅ OBRIGATÓRIO
  next_stage: string,          // ✅ OBRIGATÓRIO
  collected_data: object,      // ✅ OBRIGATÓRIO
  trigger_wf06_next_dates: boolean,
  trigger_wf06_available_slots: boolean
}
```

### V111: Database Row Locking

**Problema**: Race conditions quando usuário envia mensagens rápidas.

**Solução**:
```sql
FOR UPDATE SKIP LOCKED;
```

Garante que apenas UMA execução processa conversa por vez.

### V113: WF06 Suggestions Persistence

**Problema**: `date_suggestions` e `slot_suggestions` não eram salvos no banco.

**Solução**: Build Update Queries1 e Build Update Queries2 salvam sugestões:
```sql
UPDATE conversations
SET
  date_suggestions = '{{ JSON.stringify($json.date_suggestions) }}'::jsonb
WHERE phone_number = '{{ $json.phone_number }}';
```

### V114: PostgreSQL TIME Fields

**Problema**: `scheduled_time_start` e `scheduled_time_end` tinham formato errado.

**Solução**: Extrair apenas TIME dos slots:
```javascript
// Slot format: "08:00 - 09:00"
const [startTime, endTime] = slot.split(' - ');
```

---

## 🎯 Best Practices

### 1. Sempre Retornar Estrutura Completa

```javascript
// ✅ CORRETO
return [{
  json: {
    response_text: "Mensagem",
    next_stage: "próximo_estado",
    collected_data: {...},
    trigger_wf06_next_dates: false,
    trigger_wf06_available_slots: false
  }
}];

// ❌ ERRADO: Campos faltando
return [{
  json: {
    response_text: "Mensagem"
    // Falta next_stage, collected_data, etc
  }
}];
```

### 2. Validação Inline (Proactive UX)

```javascript
// ✅ CORRETO: Guia o usuário
if (cleanPhone.length >= 10 && cleanPhone.length <= 11) {
  // Continua
} else {
  response_text = `Por favor, informe um telefone válido com DDD.\n\n` +
                 `Exemplo: (62) 99999-9999`;
  next_stage = 'collect_phone'; // Permanece no estado
}

// ❌ ERRADO: Apenas valida
if (!isValidPhone(message)) {
  response_text = "❌ Telefone inválido!";
  // Usuário não sabe o que fazer
}
```

### 3. Inicializar Defaults

```javascript
// ✅ CORRETO
const currentState = item.json.state_machine_state || 'greeting';
const collectedData = item.json.collected_data || {};

// ❌ ERRADO: Pode gerar undefined
const currentState = item.json.state_machine_state;
const collectedData = item.json.collected_data;
```

### 4. Preservar Dados do Input

```javascript
// ✅ CORRETO: Preserva campos necessários
results.push({
  json: {
    // Novos campos
    response_text: response_text,
    next_stage: next_stage,
    // Preserva do input
    conversation_id: item.json.conversation_id,
    phone_number: item.json.phone_number,
    message_text: item.json.message_text
  }
});
```

### 5. Estados Terminais Explícitos

```javascript
case 'completed':
  response_text = `Obrigado! Até logo! 👋`;
  next_stage = 'completed'; // Permanece em completed
  break;
```

### 6. Fallback para Estados Desconhecidos

```javascript
default:
  // Fallback: recomeça conversa
  response_text = `Desculpe, ocorreu um erro. Vamos recomeçar.`;
  next_stage = 'greeting';
  collectedData = {}; // Reset
```

---

## 🔍 Debugging State Machine

### 1. Verificar Estado Atual

```sql
SELECT
  phone_number,
  state_machine_state,
  collected_data,
  updated_at
FROM conversations
WHERE phone_number = '62999999999'
ORDER BY updated_at DESC
LIMIT 1;
```

### 2. Logs do n8n

```bash
docker logs -f e2bot-n8n-dev | grep -E "State Machine|WF02"
```

### 3. Validar Estrutura de Retorno

```javascript
// Adicione console.log no State Machine Logic
console.log('State:', currentState);
console.log('Response:', response_text);
console.log('Next:', next_stage);
console.log('Collected:', collectedData);
```

### 4. Testar Race Conditions

```
1. Envie mensagem "1" (service_selection)
2. IMEDIATAMENTE envie "João Silva" (collect_name)
3. Verifique se ambas foram processadas corretamente
```

Se houver problemas, verificar se V111 row locking está implementado.

### 5. Verificar Ordem de Execução

```
State Machine → Update State → Check If WF06 → Loop
```

Se ordem estiver errada (Check If WF06 antes de Update), você terá V105 bug (estado desatualizado).

---

## 📚 Referências Importantes

### Documentação de Bugfixes

- **V76**: `/docs/fix/wf02/v63-v79/BUGFIX_WF02_V76_LOOP_FIX_IMPLEMENTATION.md`
- **V91**: `/docs/deployment/wf02/v80-v99/DEPLOY_WF02_V91_STATE_INITIALIZATION.md`
- **V104**: `/docs/fix/wf02/v100-v114/BUGFIX_WF02_V104_DATABASE_STATE_UPDATE.md`
- **V105**: `/docs/fix/wf02/v100-v114/BUGFIX_WF02_V105_ROUTING_FIX.md`
- **V106.1**: `/docs/fix/wf02/v100-v114/BUGFIX_WF02_V106_1_RESPONSE_TEXT_FIX.md`
- **V111**: `/docs/fix/wf02/v100-v114/BUGFIX_WF02_V111_DATABASE_STATE_RACE_CONDITION.md`
- **V113**: `/docs/fix/wf02/v100-v114/BUGFIX_WF02_V113_1_WF06_SUGGESTIONS_PERSISTENCE.md`
- **V114**: `/docs/WF02_V114_QUICK_DEPLOY.md`

### Scripts de Geração

- **State Machine V114**: `/scripts/wf02/state-machines/wf02-v114-slot-time-fields-fix.js`
- **Build SQL Queries V111**: `/scripts/wf02/state-machines/wf02-v111-build-sql-queries-row-locking.js`
- **Build Update Queries V79.1**: `/scripts/wf02/fixes/wf02-v79_1-build-update-queries-schema-fix.js`

### Workflow de Produção

- **WF02 V114**: `/n8n/workflows/production/wf02/02_ai_agent_conversation_V114_FUNCIONANDO.json`

---

**Última Atualização**: 2026-04-29
**Versão em Produção**: WF02 V114
**Status**: ✅ COMPLETO - Todas as correções críticas implementadas
