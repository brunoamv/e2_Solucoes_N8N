# Setup Google Calendar Integration V2.0

**Versão**: V2.0 (Refatorada)
**Data**: 2026-03-11
**Padrão**: V69.2 compliance

---

## 📋 Visão Geral

Guia completo para configurar a integração REFATORADA do bot E2 Soluções com Google Calendar, seguindo os padrões estabelecidos no WF02 V69.2.

**Principais Melhorias V2.0**:
- ✅ Validação de entrada robusta
- ✅ Error handling completo
- ✅ Retry logic para Google API
- ✅ Validação de disponibilidade
- ✅ Logging estruturado
- ✅ Database atomicity
- ✅ Configuração via env vars

---

## 🔧 Pré-requisitos

- Conta Google (Gmail ou Google Workspace)
- Acesso ao Google Cloud Console
- Permissões de administrador no calendário
- Projeto do bot configurado e rodando
- PostgreSQL com schema atualizado (appointments + leads)

---

## Etapa 1: Criar Projeto no Google Cloud

### 1.1. Acessar Google Cloud Console

1. Acesse: https://console.cloud.google.com/
2. Faça login com sua conta Google
3. Clique em **"Selecionar Projeto"** no topo
4. Clique em **"Novo Projeto"**

### 1.2. Configurar Projeto

```yaml
Nome do Projeto: E2 Soluções Bot
ID do Projeto: e2-solucoes-bot-XXXX (gerado automaticamente)
Organização: Sem organização (ou sua empresa)
Local: Sem organização
```

Clique em **"Criar"** e aguarde 1-2 minutos.

### 1.3. Selecionar Projeto

No topo da página, certifique-se que o projeto **"E2 Soluções Bot"** está selecionado.

---

## Etapa 2: Habilitar Google Calendar API

### 2.1. Acessar Biblioteca de APIs

1. No menu lateral, vá em: **APIs e Serviços → Biblioteca**
2. Na busca, digite: "Google Calendar API"
3. Clique em **"Google Calendar API"**
4. Clique em **"Ativar"**
5. Aguarde confirmação (30 segundos)

### 2.2. Verificar API Ativada

Vá em: **APIs e Serviços → Painel**

Deve aparecer "Google Calendar API" na lista de APIs ativadas.

---

## Etapa 3: Criar Credenciais OAuth2

> **V2.0 Change**: Agora usamos OAuth2 ao invés de Service Account para melhor integração com n8n.

### 3.1. Criar Credenciais OAuth2

1. Vá em: **APIs e Serviços → Credenciais**
2. Clique em **"Criar Credenciais"**
3. Selecione **"ID do cliente OAuth 2.0"**

### 3.2. Configurar Tela de Consentimento (se solicitado)

**Etapa 1: Tipo de aplicativo**
```yaml
Tipo de usuário: Interno (se Google Workspace) ou Externo
```

**Etapa 2: Informações do aplicativo**
```yaml
Nome do aplicativo: E2 Soluções Bot
Email de suporte: clima.cocal.2025@gmail.com
Logo: (opcional)
```

**Etapa 3: Escopos**
```yaml
Escopos necessários:
  - calendar.readonly
  - calendar.events
```

**Etapa 4: Usuários de teste** (apenas para Externo)
```yaml
Adicione seu email de técnico
```

### 3.3. Criar ID do Cliente OAuth

```yaml
Tipo de aplicativo: Aplicativo da Web
Nome: E2 Bot n8n Integration

URIs de redirecionamento autorizados:
  - http://localhost:5678/rest/oauth2-credential/callback
  - https://seu-dominio.com/rest/oauth2-credential/callback  # Se em produção
```

Clique em **"Criar"**

### 3.4. Salvar Client ID e Client Secret

Anote os valores:
```
Client ID: xxxxx.apps.googleusercontent.com
Client Secret: xxxxx
```

---

## Etapa 4: Criar e Compartilhar Calendário

### 4.1. Criar Calendário Dedicado

1. Acesse: https://calendar.google.com/
2. No lado esquerdo, próximo a "Outros calendários", clique no **"+"**
3. Selecione **"Criar novo calendário"**

```yaml
Nome: Visitas Técnicas E2 Soluções
Descrição: Agendamento automatizado de visitas técnicas pelo bot
Fuso horário: (GMT-03:00) Brasília
```

Clique em **"Criar calendário"**

### 4.2. Configurar Permissões do Calendário

1. Na lista de calendários, localize "Visitas Técnicas E2 Soluções"
2. Clique nos **3 pontos** → **"Configurações e compartilhamento"**
3. Em **"Permissões de acesso"**:
   - ✅ Tornar disponível ao público: **NÃO**
   - ✅ Compartilhar somente com pessoas específicas

4. Role até **"Compartilhar com pessoas específicas"**
5. Adicione o email do técnico responsável:

```yaml
Email: tecnico@e2solucoes.com.br
Permissões: Fazer alterações em eventos
```

### 4.3. Obter ID do Calendário

1. Ainda em "Configurações e compartilhamento"
2. Role até **"Integrar calendário"**
3. Localize **"ID do calendário"**
4. Copie o ID (formato: `xxxxx@group.calendar.google.com`)

**Anote o `CALENDAR_ID`** - você usará no .env.

---

## Etapa 5: Configurar n8n Credentials

### 5.1. Criar Credencial Google Calendar no n8n

1. Acesse: http://localhost:5678
2. Vá em: **Credentials → Add Credential**
3. Busque: "Google Calendar OAuth2"
4. Preencha:

```yaml
Credential Name: Google Calendar API - E2 Bot
Client ID: [Client ID do Step 3.4]
Client Secret: [Client Secret do Step 3.4]
Scope: https://www.googleapis.com/auth/calendar
```

5. Clique em **"Connect my account"**
6. Autorize o acesso na tela do Google
7. Aguarde redirecionamento para n8n

### 5.2. Anotar Credential ID

Após criar a credencial, clique nela e anote o ID da URL:

```
URL: http://localhost:5678/credentials/VXA1r8sd0TMIdPvS
                                         ^^^^^^^^^^^^^^^^
                                         CREDENTIAL_ID
```

**Anote o `CREDENTIAL_ID`** - você usará no .env.

---

## Etapa 6: Configurar Variáveis de Ambiente

### 6.1. Editar .env.dev

Edite `docker/.env.dev` e adicione/atualize:

```bash
# ============================================
# GOOGLE CALENDAR CONFIGURATION V2.0
# ============================================

# Calendar Configuration
GOOGLE_CALENDAR_ID=xxxxx@group.calendar.google.com
GOOGLE_CALENDAR_CREDENTIAL_ID=VXA1r8sd0TMIdPvS
GOOGLE_TECHNICIAN_EMAIL=tecnico@e2solucoes.com.br

# Timezone Configuration
CALENDAR_TIMEZONE=America/Sao_Paulo

# Business Hours (24h format)
CALENDAR_WORK_START=08:00
CALENDAR_WORK_END=18:00
CALENDAR_WORK_DAYS=1,2,3,4,5  # Segunda a Sexta (0=Dom, 6=Sáb)

# Reminders Configuration
CALENDAR_REMINDER_24H=true
CALENDAR_REMINDER_2H=true

# ============================================
# RD STATION CONFIGURATION
# ============================================

RDSTATION_URL=https://crm.rdstation.com
RDSTATION_API_URL=https://api.rd.services/platform
RDSTATION_ACCESS_TOKEN=xxxxx
RDSTATION_USER_TECNICO=xxxxx

# ============================================
# N8N WORKFLOW IDS
# ============================================

WORKFLOW_ID_EMAIL_CONFIRMATION=7
WORKFLOW_ID_APPOINTMENT_REMINDERS=6
```

### 6.2. Reiniciar Container n8n

```bash
cd /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot

# Recarregar env vars
docker-compose -f docker/docker-compose-dev.yml restart n8n

# Verificar logs
docker logs -f e2bot-n8n-dev | head -n 20
```

---

## Etapa 7: Database Schema Updates

### 7.1. Adicionar Novo Status

```bash
# Conectar ao PostgreSQL
docker exec -it e2bot-postgres-dev psql -U postgres -d e2bot_dev
```

```sql
-- Adicionar status 'erro_calendario'
ALTER TABLE appointments
DROP CONSTRAINT IF EXISTS valid_status;

ALTER TABLE appointments
ADD CONSTRAINT valid_status
CHECK (status IN (
    'agendado',
    'confirmado',
    'em_andamento',
    'realizado',
    'cancelado',
    'reagendado',
    'no_show',
    'erro_calendario'  -- NOVO V2.0
));

-- Adicionar índice para google_calendar_event_id
CREATE INDEX IF NOT EXISTS idx_appointments_google_event
ON appointments(google_calendar_event_id)
WHERE google_calendar_event_id IS NOT NULL;

-- Verificar
\d appointments
```

Saia com `\q`.

---

## Etapa 8: Import Workflow V2.0

### 8.1. Backup do Workflow V1.0

```bash
# Copiar workflow atual para backup
cp n8n/workflows/05_appointment_scheduler.json \
   n8n/workflows/05_appointment_scheduler_V1.0_BACKUP.json

echo "✅ Backup criado: 05_appointment_scheduler_V1.0_BACKUP.json"
```

### 8.2. Import Workflow V2.0

1. Acesse: http://localhost:5678
2. Vá em: **Workflows**
3. Clique em **Import from File**
4. Selecione: `n8n/workflows/05_appointment_scheduler_V2.0.json`
5. Clique em **Import**

### 8.3. Configurar Credenciais no Workflow

1. Abra o workflow importado
2. Clique no node **"Create Google Calendar Event"**
3. Em **Credentials**, selecione: "Google Calendar API - E2 Bot"
4. Clique em **Save**

### 8.4. Ativar Workflow

1. No topo da tela, clique em **Inactive**
2. Deve mudar para **Active**

---

## Etapa 9: Teste de Integração

### 9.1. Criar Appointment de Teste

```bash
# Inserir appointment de teste
docker exec -it e2bot-postgres-dev psql -U postgres -d e2bot_dev <<SQL
-- Criar lead de teste
INSERT INTO leads (
    phone_number,
    name,
    email,
    address,
    city,
    state,
    zip_code,
    service_type,
    status
) VALUES (
    '556299999999',
    'João Teste',
    'teste@example.com',
    'Rua Teste, 123',
    'Goiânia',
    'GO',
    '74000-000',
    'energia_solar',
    'novo'
)
RETURNING id;

-- Anote o lead_id retornado e use no próximo INSERT

-- Criar appointment de teste (ajuste o lead_id)
INSERT INTO appointments (
    lead_id,
    scheduled_date,
    scheduled_time_start,
    scheduled_time_end,
    service_type,
    status,
    notes
) VALUES (
    '...',  -- COLOQUE O lead_id aqui
    CURRENT_DATE + INTERVAL '2 days',
    '14:00',
    '16:00',
    'energia_solar',
    'agendado',
    'Teste de integração Google Calendar V2.0'
)
RETURNING id;
SQL
```

**Anote o `appointment_id` retornado**.

### 9.2. Trigger Workflow Manualmente

1. No n8n, abra o workflow **"05 - Appointment Scheduler V2.0"**
2. Clique no node **"Execute Workflow Trigger"**
3. Clique em **"Execute Node"**
4. No painel lateral, insira:

```json
{
  "appointment_id": "...",
  "source": "manual_test"
}
```

5. Clique em **"Execute Workflow"**

### 9.3. Verificar Resultados

**No n8n**:
- ✅ Todos os nodes devem estar verdes
- ✅ Node "Validate Input Data" deve ter validado o appointment_id
- ✅ Node "Get Appointment & Lead Data" deve ter retornado os dados
- ✅ Node "Create Google Calendar Event" deve ter criado o evento

**No Google Calendar**:
1. Acesse: https://calendar.google.com/
2. Selecione o calendário "Visitas Técnicas E2 Soluções"
3. Verifique se o evento aparece na data correta

**No Database**:
```bash
docker exec -it e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT id, status, google_calendar_event_id FROM appointments WHERE id = '...';"
```

Deve retornar:
- `status`: `confirmado`
- `google_calendar_event_id`: Preenchido

---

## Etapa 10: Fluxo Completo V2.0

```
┌─────────────────────────────────────────────────────┐
│   1. Trigger do WF02 (confirmação do lead)          │
│      Input: { appointment_id: uuid }                │
└──────────────────┬──────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────┐
│   2. Validate Input Data                            │
│      → Valida appointment_id (UUID format)          │
│      → Retorna dados validados + timestamp          │
└──────────────────┬──────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────┐
│   3. Get Appointment & Lead Data (Single Query)     │
│      → JOIN appointments + leads + conversations    │
│      → Status IN ('agendado', 'reagendado')         │
│      → Retorna todos os dados necessários           │
└──────────────────┬──────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────┐
│   4. Validate Availability                          │
│      → Verifica horário de expediente               │
│      → Verifica dia útil                            │
│      → Lança erro se inválido                       │
└──────────────────┬──────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────┐
│   5. Build Calendar Event Data                      │
│      → Configura duração por service_type           │
│      → Monta título, descrição, location            │
│      → Define attendees e reminders                 │
│      → Retorna calendar_event + metadata            │
└──────────────────┬──────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────┐
│   6. Create Google Calendar Event                   │
│      → POST /calendars/{id}/events                  │
│      → Retry: 3x com 1s entre tentativas            │
│      → continueOnFail: true (error handling)        │
│      → alwaysOutputData: true                       │
└──────────────────┬──────────────────────────────────┘
                   ↓
         ┌─────────┴─────────┐
         │                   │
    ✅ Success          ❌ Error
         │                   │
         ↓                   ↓
┌─────────────────┐   ┌────────────────────┐
│ Update Success  │   │ Update Error       │
│ Status:         │   │ Status:            │
│ 'confirmado'    │   │ 'erro_calendario'  │
│ + event_id      │   │ + error message    │
└────────┬────────┘   └────────┬───────────┘
         │                     │
         ↓                     ↓
┌─────────────────┐   ┌────────────────────┐
│ Create          │   │ Log Error &        │
│ Reminders       │   │ Notify Admin       │
└────────┬────────┘   └────────────────────┘
         │
         ↓
┌─────────────────┐
│ Create RD Task  │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ Send Email      │
└─────────────────┘
```

---

## Etapa 11: Configurar Horários Bloqueados

### 11.1. Bloqueios Manuais (Almoço, Reuniões)

```sql
-- Criar tabela de bloqueios (se não existir)
CREATE TABLE IF NOT EXISTS calendar_blocks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    block_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    reason VARCHAR(255),
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Adicionar bloqueio de almoço (recorrente)
INSERT INTO calendar_blocks (
    block_date,
    start_time,
    end_time,
    reason,
    created_by
) VALUES (
    CURRENT_DATE,
    '12:00',
    '13:30',
    'Almoço',
    'system'
);
```

### 11.2. Feriados de 2026

```sql
-- Criar tabela de feriados (se não existir)
CREATE TABLE IF NOT EXISTS holidays (
    id SERIAL PRIMARY KEY,
    holiday_date DATE NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) DEFAULT 'national',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Feriados nacionais 2026
INSERT INTO holidays (holiday_date, name, type) VALUES
('2026-01-01', 'Ano Novo', 'national'),
('2026-02-16', 'Carnaval', 'national'),
('2026-02-17', 'Carnaval', 'national'),
('2026-04-03', 'Sexta-feira Santa', 'national'),
('2026-04-21', 'Tiradentes', 'national'),
('2026-05-01', 'Dia do Trabalho', 'national'),
('2026-06-04', 'Corpus Christi', 'national'),
('2026-09-07', 'Independência', 'national'),
('2026-10-12', 'Nossa Senhora Aparecida', 'national'),
('2026-11-02', 'Finados', 'national'),
('2026-11-15', 'Proclamação da República', 'national'),
('2026-12-25', 'Natal', 'national')
ON CONFLICT (holiday_date) DO NOTHING;
```

---

## Etapa 12: Troubleshooting V2.0

### Problema: "Permission denied" ao criar evento

**Causa:** Credenciais OAuth2 não autorizadas

**Solução:**
1. Vá em n8n Credentials
2. Edite "Google Calendar API - E2 Bot"
3. Clique em **"Reconnect"**
4. Autorize o acesso novamente

### Problema: "Status erro_calendario" no banco

**Causa:** Falha na criação do evento Google Calendar

**Solução:**
```bash
# Verificar logs do erro
docker exec -it e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT id, notes FROM appointments WHERE status = 'erro_calendario' ORDER BY updated_at DESC LIMIT 5;"

# Verificar logs do n8n
docker logs e2bot-n8n-dev | grep -A 10 "Google Calendar Error"
```

Causas comuns:
- Quota exceeded (1M requests/dia)
- Credenciais expiradas
- Calendar ID incorreto
- Timezone inválido

### Problema: Horário criado errado no calendário

**Causa:** Timezone incorreto

**Solução:**
```bash
# Verificar timezone configurado
grep CALENDAR_TIMEZONE docker/.env.dev

# Deve ser: America/Sao_Paulo
# Lista completa: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
```

### Problema: Workflow não executa

**Causa:** Workflow desativado ou trigger incorreto

**Solução:**
1. Verificar se workflow está **Active**
2. Verificar se WF02 está chamando corretamente:

```bash
# Verificar logs do WF02
docker logs e2bot-n8n-dev | grep "Trigger Appointment Scheduler"
```

### Problema: Evento duplicado no calendário

**Causa:** Workflow executado múltiplas vezes

**Solução:**
```sql
-- Verificar duplicatas
SELECT
    google_calendar_event_id,
    COUNT(*) as count
FROM appointments
WHERE google_calendar_event_id IS NOT NULL
GROUP BY google_calendar_event_id
HAVING COUNT(*) > 1;

-- Remover duplicatas (manter a mais recente)
DELETE FROM appointments a
WHERE a.id NOT IN (
    SELECT DISTINCT ON (google_calendar_event_id) id
    FROM appointments
    WHERE google_calendar_event_id = a.google_calendar_event_id
    ORDER BY google_calendar_event_id, created_at DESC
);
```

---

## Etapa 13: Monitoramento

### 13.1. Queries de Monitoramento

```sql
-- Dashboard de agendamentos
SELECT
    DATE(scheduled_date) as dia,
    COUNT(*) as total,
    COUNT(CASE WHEN status = 'confirmado' THEN 1 END) as confirmados,
    COUNT(CASE WHEN status = 'erro_calendario' THEN 1 END) as erros,
    STRING_AGG(
        TO_CHAR(scheduled_time_start, 'HH24:MI') || ' - ' || l.name,
        ', '
    ) as visitas
FROM appointments a
JOIN leads l ON a.lead_id = l.id
WHERE scheduled_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '14 days'
GROUP BY DATE(scheduled_date)
ORDER BY dia;

-- Erros recentes
SELECT
    a.id,
    a.scheduled_date,
    a.status,
    l.name,
    a.notes,
    a.updated_at
FROM appointments a
JOIN leads l ON a.lead_id = l.id
WHERE a.status = 'erro_calendario'
ORDER BY a.updated_at DESC
LIMIT 10;

-- Taxa de sucesso (últimos 30 dias)
SELECT
    COUNT(CASE WHEN status = 'confirmado' THEN 1 END)::FLOAT /
    COUNT(*)::FLOAT * 100 as taxa_sucesso_pct
FROM appointments
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days';
```

### 13.2. Logs Estruturados

```bash
# Logs de validação
docker logs e2bot-n8n-dev | grep "✅ Input validated"

# Logs de criação de eventos
docker logs e2bot-n8n-dev | grep "✅ Calendar event built"

# Logs de erros
docker logs e2bot-n8n-dev | grep "❌ Google Calendar Error"

# Logs de disponibilidade
docker logs e2bot-n8n-dev | grep "✅ Availability validated"
```

---

## 📊 Checklist de Configuração V2.0

- [ ] Projeto criado no Google Cloud Console
- [ ] Google Calendar API habilitada
- [ ] Credenciais OAuth2 criadas
- [ ] Client ID e Client Secret anotados
- [ ] Calendário "Visitas Técnicas E2" criado
- [ ] Calendário compartilhado com técnico
- [ ] CALENDAR_ID obtido e anotado
- [ ] Credencial criada no n8n
- [ ] CREDENTIAL_ID anotado
- [ ] `.env.dev` atualizado com TODAS as variáveis
- [ ] Container n8n reiniciado
- [ ] Migration SQL executada (novo status)
- [ ] Workflow V1.0 backup criado
- [ ] Workflow V2.0 importado
- [ ] Credenciais configuradas no workflow
- [ ] Workflow V2.0 ativado
- [ ] Teste manual executado com sucesso
- [ ] Evento aparece no Google Calendar
- [ ] Status 'confirmado' no banco
- [ ] Feriados 2026 cadastrados
- [ ] Bloqueios de horário configurados
- [ ] Monitoramento configurado
- [ ] Documentação atualizada

---

## 🎯 Diferenças V1.0 → V2.0

| Aspecto | V1.0 | V2.0 |
|---------|------|------|
| **Auth** | Service Account | OAuth2 |
| **Validation** | ❌ None | ✅ Input + Availability |
| **Error Handling** | ❌ None | ✅ Complete |
| **Retry** | ❌ None | ✅ 3x with backoff |
| **Logging** | ❌ None | ✅ Structured |
| **Config** | Hardcoded | Env vars |
| **Database** | 2 queries | 1 atomic query |
| **Status** | 7 options | 8 options (+erro_calendario) |
| **Maintainability** | 🟡 Medium | ✅ High |

---

## 📚 Recursos Adicionais

- **Google Calendar API Docs**: https://developers.google.com/calendar/api
- **OAuth2 Setup**: https://developers.google.com/identity/protocols/oauth2
- **n8n Google Calendar Node**: https://docs.n8n.io/integrations/builtin/credentials/google/oauth-generic/
- **Limites de API**: 1.000.000 requests/dia
- **Quota Monitoring**: https://console.cloud.google.com/apis/api/calendar-json.googleapis.com/quotas

---

**Configuração V2.0 completa!** O bot agora tem integração robusta com Google Calendar, seguindo os padrões do WF02 V69.2.

**Maintido por**: Claude Code
**Próxima revisão**: Após deploy em produção
