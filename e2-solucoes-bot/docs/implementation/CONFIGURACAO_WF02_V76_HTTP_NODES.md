# Configuração WF02 V76 - Nós HTTP Request para WF06

> **Data**: 2026-04-08 | **Status**: Guia de Configuração Manual

## ❌ Problema

WF02 V76 importado não possui os nós HTTP Request necessários para chamar WF06. O workflow depende de 2 chamadas HTTP que precisam ser adicionadas manualmente.

**Evidência**:
- ✅ WF06 está ativo em http://localhost:5678/workflow/QDFJCEtzQSNON9cR
- ✅ WF05 tem trigger em WF02 (nó "Trigger Appointment Scheduler")
- ❌ **NÃO HÁ** triggers para WF06 no workflow V76

---

## ✅ Solução: Adicionar 2 Nós HTTP Request

### 📍 Localização dos Nós

```
WF02 V76 Flow:
State 8 (confirmation) → escolhe "1 - Sim, quero agendar"
    ↓
[❌ FALTA] HTTP Request: Get Next Dates → chama WF06 next_dates
    ↓
State 9: show_available_dates → mostra 3 opções de datas
    ↓
State 10: process_date_selection → usuário escolhe data
    ↓
[❌ FALTA] HTTP Request: Get Available Slots → chama WF06 available_slots
    ↓
State 11: show_available_slots → mostra horários disponíveis
    ↓
State 12: process_slot_selection → usuário escolhe horário
    ↓
State 13: appointment_final_confirmation → chama WF05 ✅ (já existe)
```

---

## 🔧 Configuração Manual no n8n

### Passo 1: Adicionar Node "HTTP Request - Get Next Dates"

**Localização**: Entre State 8 e State 9

**Passos no n8n UI**:

1. Abra WF02 V76: http://localhost:5678/workflow/arP2YRn5ZdZfH9Xi
2. Clique no **+** (Add Node) APÓS o nó "State Machine Logic" (quando state = 8 e escolha = "1")
3. Selecione: **HTTP Request**

**Configurações do Nó**:

```json
Nome do Nó: HTTP Request - Get Next Dates

Parameters:
- Method: POST
- URL: http://e2bot-n8n-dev:5678/webhook/calendar-availability
- Authentication: None
- Send Body: Yes
- Specify Body: Using JSON

Body JSON:
{
  "action": "next_dates",
  "count": 3,
  "start_date": "{{ new Date().toISOString().split('T')[0] }}",
  "duration_minutes": 120
}

Options:
- Response Format: JSON
- Timeout: 5000 (5 segundos)

Error Handling:
- Continue On Fail: Yes (IMPORTANTE - permite fallback)
- Retry On Fail: Yes
- Max Tries: 2
```

**Expressão n8n para Body**:
```javascript
={{ JSON.stringify({
  action: 'next_dates',
  count: 3,
  start_date: new Date().toISOString().split('T')[0],
  duration_minutes: 120
}) }}
```

**Conexões**:
- **Input**: Conectar do nó que valida State 8 (confirmation) com escolha "1"
- **Output**: Conectar para o nó "State Machine Logic" que processa State 9

---

### Passo 2: Adicionar Node "HTTP Request - Get Available Slots"

**Localização**: Entre State 10 e State 11

**Passos no n8n UI**:

1. Ainda em WF02 V76
2. Clique no **+** (Add Node) APÓS State 10 (process_date_selection)
3. Selecione: **HTTP Request**

**Configurações do Nó**:

```json
Nome do Nó: HTTP Request - Get Available Slots

Parameters:
- Method: POST
- URL: http://e2bot-n8n-dev:5678/webhook/calendar-availability
- Authentication: None
- Send Body: Yes
- Specify Body: Using JSON

Body JSON:
{
  "action": "available_slots",
  "date": "{{ $json.scheduled_date }}",
  "duration_minutes": 120
}

Options:
- Response Format: JSON
- Timeout: 5000

Error Handling:
- Continue On Fail: Yes (IMPORTANTE - permite fallback)
- Retry On Fail: Yes
- Max Tries: 2
```

**Expressão n8n para Body**:
```javascript
={{ JSON.stringify({
  action: 'available_slots',
  date: $json.scheduled_date,  // Data selecionada no State 10
  duration_minutes: 120
}) }}
```

**Conexões**:
- **Input**: Conectar do nó que valida State 10 (process_date_selection) quando data válida
- **Output**: Conectar para o nó "State Machine Logic" que processa State 11

---

## 📊 Como o State Machine Acessa as Respostas

### State 9: show_available_dates

**Código no State Machine**:
```javascript
case 'show_available_dates':
    console.log('V76: Showing available dates (PROACTIVE UX)');

    // Acessa resposta do HTTP Request - Get Next Dates
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

**Onde vem `input.wf06_next_dates`?**
- Vem do **resultado do nó HTTP Request - Get Next Dates**
- n8n armazena automaticamente o response no `$json`
- State Machine acessa via `input` parameter

### State 11: show_available_slots

**Código no State Machine**:
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

## ⚙️ Mapeamento de Dados Entre Nós

### Fluxo de Dados Completo

```
1. State 8 confirmation (user escolhe "1")
   ↓ passa para HTTP Request 1

2. HTTP Request - Get Next Dates
   Input: {
     action: "next_dates",
     count: 3,
     start_date: "2026-04-08"
   }

   Output: {
     success: true,
     dates: [
       { date: "2026-04-09", display: "Amanhã (09/04)", total_slots: 3 },
       { date: "2026-04-10", display: "Quinta (10/04)", total_slots: 5 },
       { date: "2026-04-11", display: "Sexta (11/04)", total_slots: 2 }
     ]
   }
   ↓ armazena em $json

3. State Machine State 9
   Acessa: input.wf06_next_dates (= $json do HTTP Request 1)
   Mostra: "1️⃣ Amanhã (09/04) - 3 horários 📅"
   User: digita "2"
   ↓

4. State Machine State 10
   Valida: escolha "2" = dates[1]
   Armazena: scheduled_date = "2026-04-10"
   ↓ passa para HTTP Request 2

5. HTTP Request - Get Available Slots
   Input: {
     action: "available_slots",
     date: "2026-04-10",  ← vem de $json.scheduled_date
     duration_minutes: 120
   }

   Output: {
     success: true,
     available_slots: [
       { start_time: "09:00", end_time: "11:00", formatted: "9h às 11h" },
       { start_time: "14:00", end_time: "16:00", formatted: "14h às 16h" }
     ],
     total_available: 2
   }
   ↓ armazena em $json

6. State Machine State 11
   Acessa: input.wf06_available_slots (= $json do HTTP Request 2)
   Mostra: "1️⃣ 9h às 11h ✅"
   User: digita "1"
   ↓

7. State Machine State 12
   Valida: escolha "1" = available_slots[0]
   Armazena: scheduled_time_start = "09:00"
   ↓

8. State 13: Trigger WF05 ✅ (já configurado)
```

---

## 🧪 Teste Após Configuração

### Passo 1: Verificar se WF06 está respondendo

```bash
curl -X POST http://localhost:5678/webhook/calendar-availability \
  -H "Content-Type: application/json" \
  -d '{"action":"next_dates","count":3}' | jq
```

**Esperado**:
```json
{
  "success": true,
  "dates": [
    { "date": "2026-04-09", "display": "Amanhã (09/04)", "total_slots": 3 }
  ]
}
```

### Passo 2: Testar WF02 V76 completo

**Via WhatsApp (ou Postman simulando Evolution API)**:

1. Inicie conversa → Complete States 1-7 (serviço, nome, phone, email, city)
2. State 8 confirmation → Escolha "1 - Sim, quero agendar"
3. **DEVE APARECER**: Mensagem com 3 datas numeradas (📅 📅 ⚠️)
4. Escolha "2" (segunda data)
5. **DEVE APARECER**: Mensagem com horários disponíveis naquela data
6. Escolha "1" (primeiro horário)
7. **DEVE APARECER**: Confirmação do agendamento + email enviado

### Passo 3: Verificar Logs

```bash
# Ver execuções do WF06
docker logs e2bot-n8n-dev | grep "calendar-availability"

# Ver execuções do WF02 State 9-11
docker logs e2bot-n8n-dev | grep -E "show_available_dates|show_available_slots"
```

---

## 🚨 Troubleshooting

### Problema 1: State 9 mostra fallback manual

**Sintoma**: Bot pede para digitar data em DD/MM/AAAA em vez de mostrar 3 opções

**Causa**: HTTP Request 1 não foi configurado ou falhou

**Debug**:
```bash
# Ver se WF06 foi chamado
docker logs e2bot-n8n-dev | grep "next_dates"

# Ver execuções do WF02
n8n UI → Executions → Filtrar por "02_ai_agent_conversation_V76"
→ Procurar pelo nó "HTTP Request - Get Next Dates"
→ Verificar se há erro
```

**Solução**:
1. Verificar se nó HTTP Request 1 existe no workflow
2. Verificar URL: `http://e2bot-n8n-dev:5678/webhook/calendar-availability`
3. Verificar se "Continue On Fail" está marcado
4. Testar WF06 isoladamente com curl

### Problema 2: State 11 mostra fallback manual

**Sintoma**: Bot pede para digitar horário HH:MM em vez de mostrar opções

**Causa**: HTTP Request 2 não foi configurado ou falhou

**Debug**:
```bash
# Ver se date foi passada corretamente
docker logs e2bot-n8n-dev | grep "available_slots"

# Verificar se scheduled_date existe no $json
n8n UI → Executions → Ver dados do State 10
```

**Solução**:
1. Verificar se nó HTTP Request 2 existe no workflow
2. Verificar expressão: `$json.scheduled_date` está correto?
3. Verificar se State 10 armazenou `scheduled_date` corretamente

### Problema 3: Erro "Cannot read property 'dates' of undefined"

**Sintoma**: Crash no State 9

**Causa**: Resposta do WF06 não está sendo armazenada corretamente

**Solução**:
1. Verificar conexões no workflow:
   - HTTP Request 1 → State Machine Logic deve estar conectado
2. Verificar estrutura do `input` parameter no State Machine
3. Adicionar defensive coding:
   ```javascript
   const nextDatesResponse = input.wf06_next_dates || {};
   ```

---

## ✅ Checklist de Configuração

- [ ] **WF06 ativo**: http://localhost:5678/workflow/QDFJCEtzQSNON9cR
- [ ] **WF06 responde**: `curl` test retorna success
- [ ] **Nó HTTP Request 1 criado**: "Get Next Dates"
  - [ ] URL: `http://e2bot-n8n-dev:5678/webhook/calendar-availability`
  - [ ] Body: `{"action":"next_dates","count":3,...}`
  - [ ] Continue On Fail: ✅ Marcado
  - [ ] Conexão: State 8 → HTTP Request 1 → State Machine
- [ ] **Nó HTTP Request 2 criado**: "Get Available Slots"
  - [ ] URL: `http://e2bot-n8n-dev:5678/webhook/calendar-availability`
  - [ ] Body: `{"action":"available_slots","date":"{{ $json.scheduled_date }}",...}`
  - [ ] Continue On Fail: ✅ Marcado
  - [ ] Conexão: State 10 → HTTP Request 2 → State Machine
- [ ] **State Machine atualizado**: Scripts/wf02-v76-state-machine.js copiado
- [ ] **Teste E2E**: Conversa completa até agendamento funciona

---

## 📚 Referências

- **WF06 Documentation**: `/docs/implementation/WF06_CALENDAR_AVAILABILITY_SERVICE.md`
- **WF02 V76 Implementation**: `/docs/implementation/WF02_V76_IMPLEMENTATION_GUIDE.md`
- **State Machine Code**: `/scripts/wf02-v76-state-machine.js`
- **Test Script WF06**: `/scripts/test-wf06-endpoints.sh`
- **Test Script WF02**: `/scripts/test-wf02-v76-e2e.sh`

---

**Criado**: 2026-04-08
**Autor**: Documentação Técnica E2 Bot
**Próximo passo**: Adicionar os 2 nós HTTP Request no n8n UI
