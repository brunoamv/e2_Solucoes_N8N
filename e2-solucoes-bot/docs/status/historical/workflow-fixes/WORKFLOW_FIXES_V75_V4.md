# Correções de Workflows: WF02 V75 e WF05 V4.0

> **Data**: 2026-03-30
> **Autor**: Claude Code
> **Status**: Pronto para implementação manual

---

## 📋 Resumo Executivo

Este documento detalha as correções necessárias para dois problemas críticos nos workflows:

1. **WF02 V75**: Mensagem final genérica → Mensagem personalizada com detalhes do agendamento
2. **WF05 V4.0**: Hora errada no Google Calendar (05:00-07:00 → 08:00-10:00) + Título sem formatação

---

## 🎯 Problema 1: WF02 - Mensagem Final Genérica

### Situação Atual (V74.1)
```
⏰ *Agendamento de Visita Técnica*

Perfeito! Agora vamos agendar sua visita técnica.

Nossa equipe entrará em contato em breve para:
✅ Confirmar melhor data e horário
✅ Esclarecer detalhes técnicos
✅ Preparar documentação necessária

🕐 *Horário de atendimento:*
Segunda a Sexta: 8h às 18h
Sábado: 8h às 12h

📱 *Contato direto:* (62) 3092-2900

_Obrigado por escolher a E2 Soluções!_
```

**Problemas**:
- ❌ Não mostra data/hora confirmados
- ❌ Não mostra dados do cliente
- ❌ Não mostra serviço escolhido
- ❌ Não inclui link do Google Calendar
- ❌ Parece que ainda não foi agendado

### Situação Desejada (V75)
```
✅ *Agendamento Confirmado com Sucesso!*

📅 *Detalhes da Visita Técnica:*
🗓️ Data: 01/04/2026
⏰ Horário: 08:00 às 10:00
⏳ Duração: 2 horas
☀️ Serviço: Energia Solar

👤 Nome: Bruno Rosa
📍 Cidade: Goiânia
📧 Confirmação enviada para: bruno@email.com

🔗 *Adicionar ao Calendário:*
[Link será enviado por email]

_Obrigado por escolher a E2 Soluções!_
```

**Melhorias**:
- ✅ Mostra data/hora real do agendamento
- ✅ Mostra dados do cliente (nome, cidade, email)
- ✅ Mostra serviço formatado (ex: "Energia Solar" ao invés de "energia_solar")
- ✅ Inclui placeholder para link do Google Calendar
- ✅ Confirma que agendamento foi realizado com sucesso

---

## 🔧 Solução WF02 V75: Implementação Manual

### Passo 1: Abrir Workflow no n8n

1. Acesse: `http://localhost:5678`
2. Abra o workflow: **02_ai_agent_conversation_V74.1_CHECK_IF_SCHEDULING_FIX**
3. Localize o nó: **"State Machine Logic"**
4. Clique duas vezes para editar

### Passo 2: Localizar Template `scheduling_redirect`

No código JavaScript, procure por:

```javascript
"scheduling_redirect": `⏰ *Agendamento de Visita Técnica*
```

Este template está dentro do objeto `templates` no início do código.

### Passo 3: Substituir Template

**REMOVER** (todo o conteúdo do template atual):

```javascript
  "scheduling_redirect": `⏰ *Agendamento de Visita Técnica*

Perfeito! Agora vamos agendar sua visita técnica.

Nossa equipe entrará em contato em breve para:
✅ Confirmar melhor data e horário
✅ Esclarecer detalhes técnicos
✅ Preparar documentação necessária

🕐 *Horário de atendimento:*
Segunda a Sexta: 8h às 18h
Sábado: 8h às 12h

📱 *Contato direto:* (62) 3092-2900

_Obrigado por escolher a E2 Soluções!_`,
```

**ADICIONAR** (novo template personalizado):

```javascript
  "scheduling_redirect": `✅ *Agendamento Confirmado com Sucesso!*

📅 *Detalhes da Visita Técnica:*
🗓️ Data: {{formatted_date}}
⏰ Horário: {{formatted_time_start}} às {{formatted_time_end}}
⏳ Duração: 2 horas
{{service_emoji}} Serviço: {{service_name}}

👤 Nome: {{name}}
📍 Cidade: {{city}}
📧 Confirmação enviada para: {{email}}

🔗 *Adicionar ao Calendário:*
{{google_calendar_link}}

_Obrigado por escolher a E2 Soluções!_`,
```

### Passo 4: Adicionar Lógica de Construção da Mensagem

Agora precisamos **construir as variáveis** `{{formatted_date}}`, `{{formatted_time_start}}`, etc.

**Localize** o case `'appointment_confirmation'` no código (procure por `case 'appointment_confirmation':`).

Dentro deste case, **LOCALIZE** a linha:

```javascript
      responseText = templates.scheduling_redirect;
```

**SUBSTITUIR** esta linha única por todo este bloco de código:

```javascript
      // ===== V75: BUILD PERSONALIZED CONFIRMATION MESSAGE =====
      // Format date from DB (YYYY-MM-DD) to display (DD/MM/YYYY)
      const dbDate = currentData.scheduled_date || updateData.scheduled_date || '';
      let formattedDate = dbDate;
      if (dbDate && /^\d{4}-\d{2}-\d{2}$/.test(dbDate)) {
        const [y, m, d] = dbDate.split('-');
        formattedDate = `${d}/${m}/${y}`;
      }

      // Format times (remove seconds)
      const startTime = currentData.scheduled_time_start || updateData.scheduled_time_start || '00:00:00';
      const endTime = currentData.scheduled_time_end || updateData.scheduled_time_end || '02:00:00';
      const formattedTimeStart = startTime.substring(0, 5); // HH:MM
      const formattedTimeEnd = endTime.substring(0, 5);     // HH:MM

      // Get service display info
      const serviceType = currentData.service_type || 'energia_solar';
      const serviceInfo = serviceDisplay[serviceType] || { emoji: '☀️', name: 'Energia Solar' };

      // Get client data
      const clientName = currentData.lead_name || 'Cliente';
      const clientEmail = currentData.email || 'não informado';
      const clientCity = currentData.city || 'não informado';

      // Build Google Calendar link (will be populated by WF05)
      const googleCalendarLink = '[Link será enviado por email]';

      // Populate template
      responseText = templates.scheduling_redirect
        .replace('{{formatted_date}}', formattedDate)
        .replace('{{formatted_time_start}}', formattedTimeStart)
        .replace('{{formatted_time_end}}', formattedTimeEnd)
        .replace('{{service_emoji}}', serviceInfo.emoji)
        .replace('{{service_name}}', serviceInfo.name)
        .replace('{{name}}', clientName)
        .replace('{{city}}', clientCity)
        .replace('{{email}}', clientEmail)
        .replace('{{google_calendar_link}}', googleCalendarLink);
```

### Passo 5: Salvar e Testar

1. Clique em **"Execute Node"** para validar o código JavaScript
2. Se não houver erros de sintaxe, clique em **"Save"**
3. Renomeie o workflow para: **02_ai_agent_conversation_V75_APPOINTMENT_FINAL_MESSAGE**
4. Clique em **"Save"** novamente

### Passo 6: Validação

Execute um teste completo:

```bash
# 1. Inicie conversa pelo WhatsApp
# 2. Escolha serviço 1 (Energia Solar) ou 3 (Projetos Elétricos)
# 3. Preencha dados: nome, telefone, email, cidade
# 4. Confirme agendamento (opção 1)
# 5. Verifique mensagem final
```

**Esperado**: Mensagem deve mostrar data/hora reais, nome do cliente, cidade, email, e serviço formatado.

---

## 🎯 Problema 2: WF05 - Hora Errada e Título Genérico

### Situação Atual (V3.6)

**Problema 1 - Timezone**:
```javascript
// ERRADO - Cria Date em UTC
const startDateTime = new Date(`${dateString}T${timeStart}`);
const endDateTime = new Date(`${dateString}T${timeEnd}`);
```

**Resultado**:
- Input: `2026-04-01T08:00:00` (sem timezone)
- JavaScript interpreta como UTC
- Google Calendar mostra 05:00-07:00 BRT (UTC - 3h)

**Problema 2 - Título**:
```javascript
summary: `Agendamento E2 Soluções - ${data.service_type || 'Serviço'}`
```

**Resultado**: "Agendamento E2 Soluções - energia_solar"

### Situação Desejada (V4.0)

**Timezone Correto**:
```javascript
// CORRETO - Cria Date em BRT (UTC-3)
const startDateTimeISO = `${dateString}T${timeStart}-03:00`;
const endDateTimeISO = `${dateString}T${timeEnd}-03:00`;
const startDateTime = new Date(startDateTimeISO);
const endDateTime = new Date(endDateTimeISO);
```

**Resultado**:
- Input: `2026-04-01T08:00:00-03:00` (BRT explícito)
- Google Calendar mostra 08:00-10:00 BRT ✅

**Título Formatado**:
```javascript
const improvedTitle = `Visita Técnica: ${serviceName} - ${clientName}`;
```

**Resultado**: "Visita Técnica: Energia Solar - Bruno Rosa"

---

## 🔧 Solução WF05 V4.0: Implementação Manual

### Passo 1: Abrir Workflow no n8n

1. Acesse: `http://localhost:5678`
2. Abra o workflow: **05_appointment_scheduler_v3.6**
3. Localize o nó: **"Build Calendar Event Data"**
4. Clique duas vezes para editar

### Passo 2: Adicionar Helper de Formatação de Serviço

No **INÍCIO** do código JavaScript (logo após `const data = $input.first().json;`), adicione:

```javascript
try {
    // ===== SERVICE NAME HELPER =====
    function formatServiceName(serviceType) {
        const serviceMap = {
            'energia_solar': 'Energia Solar',
            'subestacao': 'Subestação',
            'projeto_eletrico': 'Projetos Elétricos',
            'armazenamento_energia': 'BESS (Armazenamento)',
            'analise_laudo': 'Análise e Laudos'
        };
        return serviceMap[serviceType] || serviceType;
    }
```

### Passo 3: Localizar Seção de Criação de Datas

Procure por este bloco de código (aproximadamente linha 40-60):

```javascript
    const timeStart = typeof timeStartRaw === 'string'
        ? timeStartRaw
        : timeStartRaw?.toString() || '00:00:00';

    const timeEnd = typeof timeEndRaw === 'string'
        ? timeEndRaw
        : timeEndRaw?.toString() || '00:00:00';
```

**Logo APÓS** este bloco, **SUBSTITUA** as linhas de criação de `startDateTime` e `endDateTime`.

### Passo 4: Substituir Lógica de Timezone

**REMOVER** (linhas que criam Date sem timezone):

```javascript
    const startDateTime = new Date(`${dateString}T${timeStart}`);
    const endDateTime = new Date(`${dateString}T${timeEnd}`);
```

**ADICIONAR** (novo código com timezone explícito):

```javascript
    // ===== V4.0 FIX: CREATE DATE IN BRAZIL TIMEZONE =====
    // PROBLEM: new Date("2026-04-01T08:00:00") creates UTC Date
    // SOLUTION: Create date string with explicit timezone offset

    // Brazil timezone offset: UTC-3 (BRT - Brasília Time)
    const brazilOffset = '-03:00';

    // Build ISO strings with timezone
    const startDateTimeISO = `${dateString}T${timeStart}${brazilOffset}`;
    const endDateTimeISO = `${dateString}T${timeEnd}${brazilOffset}`;

    const startDateTime = new Date(startDateTimeISO);
    const endDateTime = new Date(endDateTimeISO);

    console.log('📅 [Build Calendar V4] DateTime with Brazil timezone:', {
        start_iso_input: startDateTimeISO,
        end_iso_input: endDateTimeISO,
        start_utc_output: startDateTime.toISOString(),
        end_utc_output: endDateTime.toISOString(),
        start_valid: !isNaN(startDateTime.getTime()),
        end_valid: !isNaN(endDateTime.getTime())
    });

    if (isNaN(startDateTime.getTime()) || isNaN(endDateTime.getTime())) {
        throw new Error('Invalid date/time format: ' + JSON.stringify({
            dateString,
            timeStart,
            timeEnd,
            startDateTimeISO,
            endDateTimeISO
        }));
    }
```

### Passo 5: Corrigir Título do Evento

Procure pela linha que define `summary:` (aproximadamente linha 80):

**REMOVER**:
```javascript
        summary: `Agendamento E2 Soluções - ${data.service_type || 'Serviço'}`,
```

**ADICIONAR** (logo ANTES da linha `summary:`):

```javascript
    // ===== V4.0 FIX: IMPROVED TITLE =====
    const serviceName = formatServiceName(data.service_type || 'energia_solar');
    const clientName = data.lead_name || 'Cliente';

    const improvedTitle = `Visita Técnica: ${serviceName} - ${clientName}`;

    console.log('📝 [Build Calendar V4] Improved title:', improvedTitle);

    // ===== BUILD CALENDAR EVENT =====
    const calendarEvent = {
        summary: improvedTitle,  // ✅ V4.0: Better title
```

### Passo 6: Salvar e Testar

1. Clique em **"Execute Node"** para validar o código JavaScript
2. Se não houver erros de sintaxe, clique em **"Save"**
3. Renomeie o workflow para: **05_appointment_scheduler_v4.0**
4. Clique em **"Save"** novamente

### Passo 7: Validação

Execute um teste completo:

```bash
# 1. Inicie conversa pelo WhatsApp
# 2. Escolha serviço 1 (Energia Solar) ou 3 (Projetos Elétricos)
# 3. Preencha dados: nome="Bruno Rosa", email, cidade
# 4. Confirme agendamento (opção 1)
# 5. Verifique Google Calendar
```

**Esperado**:
- ✅ Título: "Visita Técnica: Energia Solar - Bruno Rosa"
- ✅ Horário: 08:00-10:00 (não 05:00-07:00)
- ✅ Timezone: America/Sao_Paulo

---

## 📊 Comparação Antes/Depois

### WF02 - Mensagem Final

| Aspecto | V74.1 (Antes) | V75 (Depois) |
|---------|---------------|--------------|
| **Data** | ❌ Não mostra | ✅ "01/04/2026" |
| **Hora** | ❌ Não mostra | ✅ "08:00 às 10:00" |
| **Serviço** | ❌ Não mostra | ✅ "Energia Solar" (formatado) |
| **Cliente** | ❌ Não mostra | ✅ Nome, cidade, email |
| **Confirmação** | ❌ "vamos agendar" | ✅ "Confirmado com Sucesso!" |
| **Link Calendar** | ❌ Não menciona | ✅ Placeholder incluído |

### WF05 - Google Calendar

| Aspecto | V3.6 (Antes) | V4.0 (Depois) |
|---------|--------------|---------------|
| **Título** | ❌ "Agendamento E2 Soluções - energia_solar" | ✅ "Visita Técnica: Energia Solar - Bruno Rosa" |
| **Hora (BRT)** | ❌ 05:00-07:00 | ✅ 08:00-10:00 |
| **Timezone** | ❌ UTC (implícito) | ✅ BRT -03:00 (explícito) |
| **Formatação** | ❌ snake_case | ✅ Title Case com nome do cliente |

---

## 🧪 Plano de Testes

### Teste 1: Mensagem Final Personalizada (WF02 V75)

**Setup**:
- Workflow ativo: WF02 V75
- Serviço: 1 (Energia Solar)

**Passos**:
1. Envie mensagem: "Olá"
2. Responda: "1" (Energia Solar)
3. Nome: "Bruno Rosa"
4. Telefone: "62999999999" → Confirme "1"
5. Email: "bruno@email.com"
6. Cidade: "Goiânia"
7. Confirme agendamento: "1"

**Resultado Esperado**:
```
✅ *Agendamento Confirmado com Sucesso!*

📅 *Detalhes da Visita Técnica:*
🗓️ Data: [data real do agendamento]
⏰ Horário: 08:00 às 10:00
⏳ Duração: 2 horas
☀️ Serviço: Energia Solar

👤 Nome: Bruno Rosa
📍 Cidade: Goiânia
📧 Confirmação enviada para: bruno@email.com

🔗 *Adicionar ao Calendário:*
[Link será enviado por email]

_Obrigado por escolher a E2 Soluções!_
```

**Critérios de Sucesso**:
- ✅ Data formatada DD/MM/YYYY (não YYYY-MM-DD)
- ✅ Hora formatada HH:MM (não HH:MM:SS)
- ✅ Serviço formatado "Energia Solar" (não "energia_solar")
- ✅ Nome do cliente presente
- ✅ Cidade presente
- ✅ Email presente
- ✅ Mensagem confirma sucesso (não "vamos agendar")

### Teste 2: Timezone e Título Corretos (WF05 V4.0)

**Setup**:
- Workflow ativo: WF05 V4.0
- Mesmo teste acima (continua automaticamente)

**Passos**:
1. Continue do Teste 1
2. Aguarde 30 segundos (WF05 processa)
3. Abra Google Calendar
4. Localize evento criado

**Resultado Esperado**:
- **Título**: "Visita Técnica: Energia Solar - Bruno Rosa"
- **Data**: Dia correto (01/04/2026)
- **Hora**: 08:00-10:00 (horário de Brasília)
- **Timezone**: America/Sao_Paulo
- **Duração**: 2 horas

**Critérios de Sucesso**:
- ✅ Título contém "Visita Técnica:" prefix
- ✅ Serviço formatado com espaços (não snake_case)
- ✅ Nome do cliente no título
- ✅ Hora correta 08:00 (não 05:00)
- ✅ Timezone America/Sao_Paulo no evento

### Teste 3: Serviço 3 (Projetos Elétricos)

**Setup**:
- Mesmo procedimento, mas serviço 3

**Resultado Esperado WF02**:
```
⚡ Serviço: Projetos Elétricos
```

**Resultado Esperado WF05**:
```
Título: "Visita Técnica: Projetos Elétricos - [Nome Cliente]"
```

### Teste 4: Validação de Database

```sql
-- Verificar appointments criados
SELECT
    lead_name,
    service_type,
    scheduled_date,
    scheduled_time_start,
    scheduled_time_end,
    google_calendar_event_id,
    created_at
FROM appointments
ORDER BY created_at DESC
LIMIT 5;
```

**Esperado**:
- ✅ `scheduled_time_start` = '08:00:00'
- ✅ `scheduled_time_end` = '10:00:00'
- ✅ `google_calendar_event_id` presente (não NULL)

---

## 🚀 Deployment

### Checklist Pré-Deploy

- [ ] Backup dos workflows V74.1 e V3.6 (export JSON)
- [ ] Teste completo em ambiente dev (4 cenários)
- [ ] Validação do Google Calendar (timezone + título)
- [ ] Validação do database (appointments + reminders)
- [ ] Aprovação do usuário final

### Procedimento de Deploy

1. **Desativar workflows antigos**:
   - Desative WF02 V74.1
   - Desative WF05 V3.6

2. **Ativar novos workflows**:
   - Ative WF02 V75
   - Ative WF05 V4.0

3. **Monitoramento inicial** (2 horas):
   ```bash
   # Logs em tempo real
   docker logs -f e2bot-n8n-dev | grep -E "V75|V4.0|ERROR"

   # Database monitoring
   watch -n 30 'docker exec -it e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "SELECT COUNT(*) as appointments_hoje FROM appointments WHERE DATE(created_at) = CURRENT_DATE;"'
   ```

4. **Validação (primeiras 24h)**:
   - Mínimo 5 agendamentos com sucesso
   - 0 erros críticos nos logs
   - Google Calendar events com timezone/título corretos
   - Mensagens WhatsApp personalizadas

### Rollback (se necessário)

```bash
# 1. Desativar novos workflows
# 2. Reativar workflows antigos (V74.1 + V3.6)
# 3. Verificar funcionamento

# Database rollback: NÃO necessário (estrutura não mudou)
```

---

## 📝 Notas Técnicas

### Timezone no JavaScript

```javascript
// ❌ ERRADO - JavaScript interpreta como UTC
new Date("2026-04-01T08:00:00")
// Resultado: 2026-04-01T08:00:00.000Z (UTC)
// Google Calendar mostra: 05:00 BRT (UTC-3)

// ✅ CORRETO - Especificar timezone explicitamente
new Date("2026-04-01T08:00:00-03:00")
// Resultado: 2026-04-01T11:00:00.000Z (UTC)
// Google Calendar mostra: 08:00 BRT ✅
```

### Formatação de Serviços

```javascript
const serviceDisplay = {
  'energia_solar': { emoji: '☀️', name: 'Energia Solar' },
  'subestacao': { emoji: '⚡', name: 'Subestação' },
  'projeto_eletrico': { emoji: '📐', name: 'Projetos Elétricos' },
  'armazenamento_energia': { emoji: '🔋', name: 'BESS (Armazenamento)' },
  'analise_laudo': { emoji: '📋', name: 'Análise e Laudos' }
};
```

### Formatação de Datas

```javascript
// DB: "2026-04-01" (YYYY-MM-DD)
// Display: "01/04/2026" (DD/MM/YYYY)

const [y, m, d] = dbDate.split('-');
const formattedDate = `${d}/${m}/${y}`;
```

---

## ❓ FAQ

**Q: Por que a hora estava errada?**
A: JavaScript interpreta `new Date("2026-04-01T08:00:00")` como UTC. Google Calendar subtrai 3h para BRT, mostrando 05:00.

**Q: Como garantir que o timezone está correto?**
A: Adicionar `-03:00` explicitamente: `new Date("2026-04-01T08:00:00-03:00")`.

**Q: O título pode ser customizado?**
A: Sim, modifique a função `formatServiceName()` ou o template `improvedTitle`.

**Q: E se o cliente não informar email?**
A: Template mostra "não informado". WF05 não envia email (attendees vazio).

**Q: Precisa alterar WF01 ou WF07?**
A: Não. WF01 (handler) e WF07 (email) continuam funcionando normalmente.

---

## 📞 Suporte

**Problemas durante implementação?**

1. Verifique logs do n8n:
   ```bash
   docker logs e2bot-n8n-dev --tail 100
   ```

2. Teste código JavaScript isolado:
   - Copie o código do nó
   - Cole em um nó "Code" separado
   - Execute com dados de exemplo

3. Validação de sintaxe:
   - n8n mostra erros de sintaxe ao salvar
   - Use `console.log()` para debug

**Contato**: Claude Code | **Projeto**: E2 Soluções Bot

---

**Status**: ✅ Documentação completa e pronta para implementação
**Última atualização**: 2026-03-30
**Versão**: 1.0
