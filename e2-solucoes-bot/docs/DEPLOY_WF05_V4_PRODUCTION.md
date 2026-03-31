# Deploy WF05 V4.0 - Timezone and Title Fix

> **Data**: 2026-03-30
> **Status**: ✅ Pronto para Deploy
> **Arquivo**: `05_appointment_scheduler_v4.0.json`

---

## 📋 Resumo Executivo

**Workflow criado com sucesso!** WF05 V4.0 implementa correção de timezone (Brasil UTC-3) e título melhorado com nome do cliente.

### ✅ Alterações Implementadas

1. **TIMEZONE FIX - Brazil Timezone (-03:00)**:
   - **Problema**: Google Calendar mostrava 05:00-07:00 ao invés de 08:00-10:00
   - **Causa**: Date objects criados sem timezone explícito (assumia UTC)
   - **Solução**: Criar ISO strings com offset `-03:00` (Brasília Time)
   - **Exemplo**: `2026-04-01T08:00:00-03:00` → Calendar mostra 08:00 (correto)

2. **TITLE FIX - Improved Event Title**:
   - **Antes**: "Agendamento E2 Soluções - energia_solar" (genérico)
   - **Depois**: "Visita Técnica: Energia Solar - Bruno Rosa" (personalizado)
   - **Formato**: `Visita Técnica: {ServiceName} - {ClientName}`
   - **Benefício**: Títulos profissionais e informativos no Google Calendar

3. **Service Name Formatting Helper**:
   - Função `formatServiceName()` converte snake_case → Title Case
   - Mapeamento completo: energia_solar → Energia Solar, etc.
   - Consistência com WF02 (mesmo service display)

---

## 🔍 Validação Técnica

### ✅ Verificações Realizadas

```bash
✅ JSON válido
✅ Workflow: 05_appointment_scheduler_v4.0
✅ Nodes: 11 (igual ao V3.6)
✅ Build Calendar Event Data node atualizado
✅ formatServiceName helper presente
✅ Brazil timezone offset (-03:00) implementado
✅ Improved title format presente
✅ V4.0 comment markers encontrados
✅ Tamanho: 20.3 KB
```

### 📊 Comparação com V3.6

| Aspecto | V3.6 (Antes) | V4.0 (Depois) |
|---------|--------------|---------------|
| **Título** | "Agendamento E2 Soluções - energia_solar" | "Visita Técnica: Energia Solar - Bruno Rosa" |
| **Timezone** | UTC (implícito) → 05:00-07:00 | BRT (-03:00) → 08:00-10:00 |
| **Service Format** | snake_case (energia_solar) | Title Case (Energia Solar) |
| **Client Name** | ❌ Não inclui no título | ✅ Inclui no título |
| **Personalização** | ❌ Genérico | ✅ Personalizado |

---

## 🚀 Procedimento de Deploy

### Passo 1: Backup

```bash
# Criar backup do V3.6 atual
cd /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows
cp 05_appointment_scheduler_v3.6.json backups/05_V3.6_backup_$(date +%Y%m%d_%H%M%S).json

echo "✅ Backup criado"
```

### Passo 2: Import no n8n

1. **Acesse n8n**: `http://localhost:5678`

2. **Import Workflow**:
   - Clique em **"Import from File"** (menu superior direito)
   - Selecione: `05_appointment_scheduler_v4.0.json`
   - Clique em **"Import"**

3. **Verificar Importação**:
   - ✅ Nome: `05 - Appointment Scheduler V4.0`
   - ✅ Nodes: 11
   - ✅ Nó "Build Calendar Event Data" presente
   - ✅ Sem erros de validação

### Passo 3: Testes Preliminares

**Teste 1: Validação de Sintaxe JavaScript**

1. Abra nó "Build Calendar Event Data"
2. Clique em "Execute Node"
3. Verificar: ✅ Sem erros de sintaxe

**Teste 2: Verificação Visual do Código**

1. No código do nó, procure por:
   - `formatServiceName` (helper function)
   - `brazilOffset = '-03:00'` (timezone fix)
   - `Visita Técnica:` (improved title)
   - `startDateTimeISO` e `endDateTimeISO` (ISO strings with timezone)

### Passo 4: Testes End-to-End

**Cenário 1: Service 1 (Energia Solar) - 08:00**

```
1. WhatsApp: "Olá"
2. Bot: Menu de serviços
3. Você: "1" (Energia Solar)
4. Bot: Coleta de dados (nome, email, cidade)
5. Bot: Confirmação do resumo
6. Você: "1" (agendar)
7. Bot: "Qual a melhor data?"
8. Você: "01/04/2026"
9. Bot: "Qual horário você prefere?"
10. Você: "08:00"
11. Bot: Confirmação do agendamento
12. Você: "1" (confirmar)

✅ ESPERADO: Google Calendar Event
   - Título: "Visita Técnica: Energia Solar - {Seu Nome}"
   - Data: 01/04/2026
   - Horário: 08:00-10:00 (não 05:00-07:00!)
   - Timezone: America/Sao_Paulo
```

**Cenário 2: Service 3 (Projetos Elétricos) - 14:00**

```
(Mesmo fluxo, mas serviço "3" e horário "14:00")

✅ ESPERADO: Google Calendar Event
   - Título: "Visita Técnica: Projetos Elétricos - {Seu Nome}"
   - Data: {Data escolhida}
   - Horário: 14:00-16:00 (não 11:00-13:00!)
   - Timezone: America/Sao_Paulo
```

**Cenário 3: Service 2 (Subestação) - Deve fazer Handoff**

```
(Mesmo fluxo, mas serviço "2")

✅ ESPERADO:
   - Não deve criar evento no Google Calendar
   - Deve fazer handoff para humano
   - WF05 não é acionado
```

### Passo 5: Deploy para Produção

**Ativação**:

1. **Desativar V3.6**:
   - Abra workflow V3.6
   - Toggle "Active" → OFF

2. **Ativar V4.0**:
   - Abra workflow V4.0
   - Toggle "Active" → ON

3. **Verificar Status**:
   ```bash
   # Verificar workflows ativos
   docker logs e2bot-n8n-dev --tail 50 | grep "Workflow.*active"
   ```

**Monitoramento Inicial (2 horas)**:

```bash
# Logs em tempo real
docker logs -f e2bot-n8n-dev | grep -E "V4|Build Calendar|ERROR"

# Database: verificar novos appointments e títulos
docker exec -it e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT a.lead_name, a.service_type, a.scheduled_date, a.scheduled_time_start, ce.summary as calendar_title FROM appointments a LEFT JOIN google_calendar_events ce ON a.google_calendar_event_id = ce.id WHERE DATE(a.created_at) = CURRENT_DATE ORDER BY a.created_at DESC LIMIT 10;"
```

### Passo 6: Validação de Produção (24h)

**Critérios de Sucesso**:

- [ ] Mínimo 3 agendamentos processados com V4.0
- [ ] 0 erros críticos nos logs
- [ ] Google Calendar mostra horários corretos (08:00 ao invés de 05:00)
- [ ] Títulos personalizados com nome do cliente visíveis
- [ ] Database: appointments criados corretamente

**Métricas a Monitorar**:

```sql
-- Agendamentos hoje com títulos
SELECT
    a.lead_name,
    a.service_type,
    a.scheduled_date,
    a.scheduled_time_start,
    a.google_calendar_event_id,
    CASE
        WHEN a.google_calendar_event_id IS NOT NULL THEN 'Calendar criado'
        ELSE 'Sem calendar'
    END as calendar_status
FROM appointments a
WHERE DATE(a.created_at) = CURRENT_DATE
ORDER BY a.created_at DESC;

-- Verificar horários no Google Calendar (comparação UTC vs Local)
-- Nota: Se Google Calendar API retornar eventos, verificar campo dateTime
```

---

## 🔄 Rollback (se necessário)

### Quando fazer Rollback?

- ❌ Erros críticos de sintaxe JavaScript
- ❌ Google Calendar ainda mostra horários errados (05:00 ao invés de 08:00)
- ❌ Títulos não personalizados (ainda genéricos)
- ❌ Taxa de erro >5% nos agendamentos

### Procedimento de Rollback

```bash
# Passo 1: Desativar V4.0
# (via n8n interface: Toggle Active → OFF)

# Passo 2: Reativar V3.6
# (via n8n interface: Toggle Active → ON)

# Passo 3: Verificar funcionamento
docker logs -f e2bot-n8n-dev | grep "V3.6"

# Passo 4: Notificar problema
echo "Rollback executado: [descrever problema]" >> logs/rollback_v4.0.log
```

**Importante**: Rollback NÃO afeta database. Agendamentos criados durante V4.0 continuam válidos.

---

## 📊 Comparação Final: Antes vs Depois

### Problema Anterior (V3.6)

**Google Calendar Event**:
```
Título: "Agendamento E2 Soluções - energia_solar"
Data: 01/04/2026
Horário: 05:00-07:00  ❌ ERRADO (UTC ao invés de BRT)
Timezone: America/Sao_Paulo (mas Date criado como UTC)
```

**Problemas**:
- ❌ Horário 3 horas adiantado (UTC offset)
- ❌ Título genérico sem nome do cliente
- ❌ Service em snake_case (não amigável)
- ❌ Cliente confuso com horário diferente do combinado

### Solução Nova (V4.0)

**Google Calendar Event**:
```
Título: "Visita Técnica: Energia Solar - Bruno Rosa"
Data: 01/04/2026
Horário: 08:00-10:00  ✅ CORRETO (BRT)
Timezone: America/Sao_Paulo (Date criado com -03:00)
```

**Benefícios**:
- ✅ Horário correto (08:00 conforme combinado)
- ✅ Título personalizado com nome do cliente
- ✅ Service formatado (Title Case)
- ✅ Profissional e informativo
- ✅ Cliente recebe horário correto no email

---

## 📝 Notas Técnicas

### Código Modificado

**Localização**: Nó "Build Calendar Event Data" → JavaScript Code

**Antes (V3.6)**:
```javascript
// Build datetime without timezone
const startDateTime = new Date(`${dateString}T${timeStart}`);
const endDateTime = new Date(`${dateString}T${timeEnd}`);

// Generic title
summary: `Agendamento E2 Soluções - ${data.service_type || 'Serviço'}`
```

**Depois (V4.0)**:
```javascript
// ===== V4.0 FIX: CREATE DATE IN BRAZIL TIMEZONE =====
const brazilOffset = '-03:00';
const startDateTimeISO = `${dateString}T${timeStart}${brazilOffset}`;
const endDateTimeISO = `${dateString}T${timeEnd}${brazilOffset}`;

const startDateTime = new Date(startDateTimeISO);
const endDateTime = new Date(endDateTimeISO);

// ===== V4.0 FIX: IMPROVED TITLE =====
const serviceName = formatServiceName(data.service_type || 'energia_solar');
const clientName = data.lead_name || 'Cliente';
const improvedTitle = `Visita Técnica: ${serviceName} - ${clientName}`;

summary: improvedTitle  // ✅ V4.0: Better title
```

### Service Name Mapping

```javascript
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

### Timezone Calculation Example

**Input** (Database):
- `scheduled_date`: 2026-04-01
- `scheduled_time_start`: 08:00:00
- `scheduled_time_end`: 10:00:00

**V3.6 Processing** (WRONG):
```javascript
const startDateTime = new Date('2026-04-01T08:00:00');
// JavaScript interprets this as UTC → 2026-04-01T08:00:00.000Z
// Google Calendar converts to local: 08:00 UTC → 05:00 BRT ❌
```

**V4.0 Processing** (CORRECT):
```javascript
const startDateTimeISO = '2026-04-01T08:00:00-03:00';
const startDateTime = new Date(startDateTimeISO);
// JavaScript: 2026-04-01T08:00:00-03:00 → 2026-04-01T11:00:00.000Z (UTC)
// Google Calendar converts back: 11:00 UTC → 08:00 BRT ✅
```

---

## ❓ FAQ

**Q: Por que o horário estava errado no V3.6?**
A: JavaScript's `new Date('2026-04-01T08:00:00')` sem timezone assume UTC. Google Calendar converte UTC → Local, resultando em 05:00 (08:00 - 3 horas).

**Q: Como V4.0 resolve o problema?**
A: Adiciona offset explícito `-03:00` ao criar Date: `'2026-04-01T08:00:00-03:00'`. JavaScript converte para UTC internamente, Google Calendar converte de volta para BRT, resultando no horário correto.

**Q: O título antigo ainda funciona?**
A: Sim, mas é genérico. V4.0 melhora significativamente a experiência do usuário.

**Q: Precisa alterar WF02 ou WF07?**
A: Não para esta versão. V4.0 é independente (apenas WF05).

**Q: E se der erro no deploy?**
A: Execute rollback imediatamente (Passo 6).

**Q: Posso testar antes de produção?**
A: Sim! Siga Passo 3 e 4 antes de ativar em produção.

---

## 📞 Suporte

**Problemas durante deploy?**

1. Verificar logs: `docker logs e2bot-n8n-dev --tail 100`
2. Testar código isolado no nó "Code"
3. Comparar com V3.6 (backup)
4. Consultar documentação: `docs/WORKFLOW_FIXES_V75_V4.md`

**Contato**: Claude Code | **Projeto**: E2 Soluções Bot

---

**Status**: ✅ Pronto para Deploy
**Última atualização**: 2026-03-30
**Versão**: 1.0
