# WF05 V8 - Deployment Confirmation

**Date**: 2026-04-28
**Status**: ✅ PART 1 COMPLETE - Database Schema Created
**Remaining**: 🔴 PART 2 PENDING - Google OAuth Re-authentication

---

## ✅ COMPLETED - Part 1: PostgreSQL Database Schema

### Tabela appointment_reminders Criada

**Timestamp**: 2026-04-28 22:12 BRT
**Database**: e2bot_dev
**Container**: e2bot-postgres-dev

### Schema Completo

```sql
Table "public.appointment_reminders"
     Column     |            Type             | Nullable |           Default
----------------+-----------------------------+----------+------------------------------
 id             | uuid                        | not null | gen_random_uuid()
 appointment_id | uuid                        | not null |
 reminder_type  | character varying(50)       | not null |
 reminder_time  | timestamp without time zone | not null |
 status         | character varying(20)       | not null | 'pending'::character varying
 sent_at        | timestamp without time zone |          |
 error_message  | text                        |          |
 created_at     | timestamp without time zone | not null | now()
 updated_at     | timestamp without time zone |          | now()

Indexes:
    "appointment_reminders_pkey" PRIMARY KEY, btree (id)
    "idx_appointment_reminders_status" btree (status) WHERE status::text = 'pending'::text
    "idx_appointment_reminders_time" btree (reminder_time) WHERE status::text = 'pending'::text
    "unique_appointment_reminder" UNIQUE CONSTRAINT, btree (appointment_id, reminder_type, reminder_time)

Foreign-key constraints:
    "appointment_reminders_appointment_id_fkey" FOREIGN KEY (appointment_id) REFERENCES appointments(id) ON DELETE CASCADE
```

### Validação de Funcionalidade

**Teste de Inserção Executado**:
```sql
INSERT INTO appointment_reminders (
    appointment_id,
    reminder_type,
    reminder_time,
    status,
    created_at
)
SELECT
    'e5e6b9f4-1c35-43db-a775-75331eb3ddb9'::uuid,
    'email' as reminder_type,
    a.scheduled_date + (a.scheduled_time_start - interval '24 hours') as reminder_time,
    'pending' as status,
    NOW() as created_at
FROM appointments a
WHERE a.id = 'e5e6b9f4-1c35-43db-a775-75331eb3ddb9'
ON CONFLICT (appointment_id, reminder_type, reminder_time) DO NOTHING
RETURNING id, reminder_type, reminder_time, status;
```

**Resultado**:
```
                  id                  | reminder_type |    reminder_time    | status
--------------------------------------+---------------+---------------------+---------
 01980e2d-286a-4bf2-a3cb-e01ec9f83221 | email         | 2026-04-29 08:00:00 | pending

INSERT 0 1
```

✅ **Inserção bem-sucedida!**

### Comandos Executados

1. **Criação da Tabela**:
```bash
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "CREATE TABLE IF NOT EXISTS appointment_reminders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    appointment_id UUID NOT NULL REFERENCES appointments(id) ON DELETE CASCADE,
    reminder_type VARCHAR(50) NOT NULL,
    reminder_time TIMESTAMP NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    sent_at TIMESTAMP,
    error_message TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT unique_appointment_reminder UNIQUE (appointment_id, reminder_type, reminder_time)
);"
```

2. **Criação de Índices**:
```bash
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "CREATE INDEX idx_appointment_reminders_status ON appointment_reminders(status) WHERE status = 'pending';"

docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "CREATE INDEX idx_appointment_reminders_time ON appointment_reminders(reminder_time) WHERE status = 'pending';"
```

3. **Comentário na Tabela**:
```bash
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "COMMENT ON TABLE appointment_reminders IS 'Stores appointment reminder notifications (email, SMS, etc.)';"
```

---

## 🔴 PENDING - Part 2: Google Calendar OAuth Re-authentication

### Próximos Passos (10 minutos)

1. **Acessar n8n Credentials**:
   - URL: http://localhost:5678/credentials
   - Procurar credential: "Google Calendar API" (ID: 1)

2. **Deletar Credential Expirado** (se existir):
   - Clicar no credential "Google Calendar API"
   - Clicar em "Delete"
   - Confirmar exclusão

3. **Criar Novo Google Calendar OAuth2 Credential**:
   - Clicar em "Add Credential"
   - Selecionar "Google Calendar OAuth2 API"
   - Nome: "Google Calendar API"

4. **Configurar OAuth Settings**:
   ```
   Client ID: [From Google Cloud Console]
   Client Secret: [From Google Cloud Console]
   Scope: https://www.googleapis.com/auth/calendar
   ```

5. **Autenticar**:
   - Clicar "Connect my account"
   - Login com conta Google
   - Conceder permissões de acesso ao calendário
   - Verificar status "Connected" verde

### Verificação Google Cloud Console

Antes de criar o credential, verificar:

1. **Google Calendar API Habilitado**:
   - URL: https://console.cloud.google.com/apis/library
   - Pesquisar "Google Calendar API"
   - Verificar se está "Enabled"

2. **OAuth Consent Screen**:
   - URL: https://console.cloud.google.com/apis/credentials/consent
   - Verificar configurações
   - Garantir que app não está em modo "Testing" ou adicionar usuários de teste

3. **OAuth 2.0 Client ID**:
   - URL: https://console.cloud.google.com/apis/credentials
   - Verificar Client ID e Secret
   - **CRITICAL**: Confirmar Redirect URI: `http://localhost:5678/rest/oauth2-credential/callback`

---

## ✅ Critérios de Sucesso Após OAuth

Após completar Part 2 (OAuth re-authentication):

### 1. Credential Status
```
n8n UI → Credentials → "Google Calendar API"
Status: Connected ✅ (verde)
```

### 2. Teste Manual WF05
```bash
# Via n8n UI: http://localhost:5678/workflow/42eG7UpfmZ2PoBlY
# Clicar "Execute Workflow"
# Input de teste: {"appointment_id": "e5e6b9f4-1c35-43db-a775-75331eb3ddb9"}

# Resultado Esperado:
# ✅ Execução completa sem erros
# ✅ Nó "Create Google Calendar Event" SUCCESS
# ✅ Nó "Create Appointment Reminders" SUCCESS
# ✅ Google Calendar mostra evento criado
# ✅ appointment_reminders tem novo registro
```

### 3. Verificar Reminder Criado
```bash
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT * FROM appointment_reminders ORDER BY created_at DESC LIMIT 1;"

# Esperado:
# id | appointment_id | reminder_type | reminder_time | status
# ---+----------------+---------------+---------------+--------
# ... | valid-uuid     | email         | 2026-04-29... | pending
```

### 4. Verificar Evento no Google Calendar
- Abrir Google Calendar da conta autenticada
- Verificar evento "E2 Soluções - Agenda" criado
- Data/hora: conforme appointment

### 5. Fluxo Completo WF02 → WF05 → WF07
```
1. WF02: Usuário completa agendamento → triggers WF05 ✅
2. WF05: Cria evento no Google Calendar ✅ (NOT OAuth error!)
3. WF05: Cria reminder em appointment_reminders ✅ (NOT table error!)
4. WF05: Atualiza appointment status = 'confirmado' ✅
5. WF05: Trigger WF07 para envio de email ✅
6. WF07: Envia email de confirmação ✅
```

---

## 📊 Estado Atual do Deployment

| Componente | Status | Descrição |
|------------|--------|-----------|
| **Database Schema** | ✅ COMPLETO | Tabela appointment_reminders criada com sucesso |
| **Índices** | ✅ COMPLETO | idx_appointment_reminders_status + time criados |
| **Foreign Keys** | ✅ COMPLETO | appointment_id → appointments(id) CASCADE |
| **Unique Constraints** | ✅ COMPLETO | (appointment_id, reminder_type, reminder_time) |
| **Teste de Inserção** | ✅ VALIDADO | INSERT com padrão WF05 funcionando |
| **Google OAuth** | 🔴 PENDENTE | Credential expirado - requer re-autenticação |

---

## 🔄 Próximo Passo Crítico

**AÇÃO IMEDIATA**: Re-autenticar Google Calendar OAuth2 credential

**Tempo Estimado**: 10 minutos
**Prioridade**: 🔴 ALTA
**Bloqueio**: WF05 não funciona sem OAuth válido
**Impacto**: Integração WF02 → WF05 → WF07 completa após OAuth fix

---

## 📁 Documentação Relacionada

- **Bugfix Complete**: `docs/fix/BUGFIX_WF05_V8_APPOINTMENT_REMINDERS_GOOGLE_OAUTH.md`
- **Deployment Status**: `docs/DEPLOYMENT_STATUS.md`
- **WF05 V7 Workflow**: `n8n/workflows/05_appointment_scheduler_v7_hardcoded_values.json`

---

**Analyst**: Claude Code Analysis System
**Deployment Date**: 2026-04-28
**Part 1 Status**: ✅ COMPLETE
**Part 2 Status**: 🔴 PENDING - Requires manual OAuth re-authentication via n8n UI
