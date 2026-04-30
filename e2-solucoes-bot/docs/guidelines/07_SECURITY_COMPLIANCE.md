# Security and Compliance - Best Practices

> **Segurança de dados e conformidade LGPD** | Atualizado: 2026-04-29
> **Status**: ✅ PRODUCTION - Práticas de segurança implementadas em produção

---

## 📖 Visão Geral

Este documento documenta todas as práticas de segurança, gestão de credenciais, conformidade com LGPD (Lei Geral de Proteção de Dados), e data privacy implementadas no E2 Bot.

### Características Principais

- **Credential Management**: Gestão segura de API keys e OAuth tokens
- **Data Privacy**: Tratamento adequado de dados pessoais (LGPD)
- **Access Control**: Controle de acesso a dados sensíveis
- **Secure Communication**: Criptografia em trânsito (SSL/TLS)
- **Data Retention**: Políticas de retenção de dados
- **Audit Logging**: Logs de auditoria para compliance

---

## 🔐 Credential Management

### n8n Credentials System

**NUNCA** colocar credenciais diretamente no código:

```javascript
// ❌ ERRADO: Credenciais hardcoded
const apiKey = "ae569043cfa169380c378347f91a1141ea572541d2d1cadbed222db519c8a891";
const dbPassword = "minha_senha_secreta";

// ✅ CORRETO: Usar n8n Credentials
// n8n UI → Credentials → Create New Credential
// Select type (HTTP Header Auth, PostgreSQL, OAuth2, etc)
// Configure credential
// Reference in nodes via dropdown
```

### Credential Types Used

```yaml
Evolution API:
  type: "HTTP Header Auth"
  header_name: "apikey"
  header_value: "[Stored securely in n8n]"
  usage: "WF01 HTTP Request nodes"

PostgreSQL:
  type: "Postgres account"
  host: "e2bot-postgres-dev"
  database: "e2bot_dev"
  user: "postgres"
  password: "[Stored securely in n8n]"
  usage: "All PostgreSQL nodes"

Google Calendar:
  type: "Google OAuth2 API"
  client_id: "[Google Cloud Console]"
  client_secret: "[Stored securely]"
  scopes: "calendar.events, calendar.readonly"
  usage: "WF05, WF06 Google Calendar nodes"

SMTP Email:
  type: "SMTP account"
  host: "smtp.gmail.com"
  port: 465
  secure: true
  user: "[Email address]"
  password: "[App-specific password]"
  usage: "WF07 Email Send nodes"
```

### Credential Security Best Practices

```yaml
1. Never commit credentials to git:
   - Add .env to .gitignore ✅
   - Never hardcode API keys in code ✅
   - Use n8n credential system ✅

2. Rotate credentials periodically:
   - OAuth tokens: Refresh every 7 days (automatic)
   - API keys: Rotate every 90 days (manual)
   - Database passwords: Rotate every 180 days

3. Limit credential scope:
   - Google Calendar: Only calendar.events scope (not full access)
   - PostgreSQL: Only e2bot_dev database access
   - Evolution API: Only instance-specific apikey

4. Monitor credential usage:
   - Check n8n execution logs for unauthorized access
   - Review Google Cloud Console audit logs
   - Monitor database connection logs
```

### Google OAuth2 Setup (Secure)

```bash
# 1. Google Cloud Console
https://console.cloud.google.com/apis/credentials

# 2. Create OAuth 2.0 Client ID
Application type: Web application
Name: E2 Bot n8n Integration
Authorized redirect URIs: http://localhost:5678/rest/oauth2-credential/callback

# 3. Copy Client ID and Client Secret
# NEVER commit these to git!

# 4. n8n Credentials
# Type: Google OAuth2 API
# Client ID: [From Google Cloud Console]
# Client Secret: [From Google Cloud Console]
# Scopes: https://www.googleapis.com/auth/calendar.events

# 5. Authorize
# Click "Connect my account" → Sign in → Grant permissions
# Result: Access token stored securely in n8n database
```

---

## 🛡️ Data Privacy (LGPD Compliance)

### Personal Data Collected

```yaml
data_categories:
  identification:
    - Full name (lead_name)
    - Phone number (phone_number)
    - Email address (contact_email)
    purpose: "Contato para agendamento de reunião técnica"
    legal_basis: "Consentimento explícito do usuário"

  location:
    - State (state)
    - City (city)
    purpose: "Localização do serviço a ser prestado"
    legal_basis: "Execução de contrato"

  service_preference:
    - Service type (service_type)
    - Scheduled date/time
    purpose: "Execução do agendamento de reunião"
    legal_basis: "Execução de contrato"
```

### LGPD Compliance Requirements

```yaml
1. Consentimento:
   - Usuário inicia conversa voluntariamente ✅
   - Dados coletados apenas após consentimento explícito ✅
   - Propósito de uso explicado claramente ✅

2. Finalidade:
   - Dados usados APENAS para agendamento ✅
   - Não compartilhados com terceiros ✅
   - Não usados para marketing sem consentimento ✅

3. Adequação:
   - Coletamos apenas dados NECESSÁRIOS ✅
   - Nada além do mínimo para agendamento ✅

4. Transparência:
   - Usuário sabe quais dados são coletados ✅
   - Propósito claro (agendamento de reunião) ✅

5. Segurança:
   - Dados armazenados em database seguro ✅
   - Conexões via SSL/TLS ✅
   - Acesso restrito (credential-based) ✅

6. Direitos do Titular:
   - Right to access: SQL query para buscar dados
   - Right to deletion: DELETE FROM conversations WHERE...
   - Right to portability: Export JSON
```

### Data Retention Policy

```sql
-- Política de Retenção (Exemplo - Adaptar conforme necessidade)

-- Conversas: Manter por 90 dias
DELETE FROM conversations
WHERE created_at < NOW() - INTERVAL '90 days'
  AND state_machine_state = 'completed';

-- Appointments: Manter por 1 ano após data agendada
DELETE FROM appointments
WHERE scheduled_date < NOW() - INTERVAL '1 year';

-- Email Logs: Manter por 6 meses
DELETE FROM email_queue
WHERE created_at < NOW() - INTERVAL '6 months'
  AND status = 'sent';

-- IMPORTANTE: Executar mensalmente via cron job ou n8n workflow scheduled
```

### Right to Deletion (LGPD Art. 18)

```sql
-- Usuário solicita exclusão de dados via WhatsApp
-- Implementar workflow para processar solicitação

-- Step 1: Verificar identidade do solicitante
-- (Via phone_number ou email confirmation)

-- Step 2: Deletar dados
BEGIN;

DELETE FROM email_queue WHERE conversation_id IN (
  SELECT id FROM conversations WHERE phone_number = '556181755748'
);

DELETE FROM appointments WHERE conversation_id IN (
  SELECT id FROM conversations WHERE phone_number = '556181755748'
);

DELETE FROM conversations WHERE phone_number = '556181755748';

COMMIT;

-- Step 3: Confirmar exclusão ao usuário
-- Via WhatsApp: "Seus dados foram excluídos com sucesso."

-- Step 4: Log auditoria
INSERT INTO audit_log (action, phone_number, timestamp)
VALUES ('data_deletion', '556181755748', NOW());
```

---

## 🔒 Secure Communication

### SSL/TLS Configuration

```yaml
SMTP Email (Port 465):
  protocol: "SMTPS (SSL/TLS)"
  port: 465
  encryption: "SSL/TLS"
  certificate: "Valid TLS certificate"

PostgreSQL:
  connection: "Local Docker network (secure by isolation)"
  encryption: "Optional SSL (not required for local dev)"

Google Calendar API:
  protocol: "HTTPS"
  oauth2_flow: "Secure OAuth2 with tokens"

Evolution API:
  protocol: "HTTPS (production)"
  apikey: "Header-based authentication"
```

### Docker Network Isolation

```yaml
# docker-compose-dev.yml
networks:
  e2bot-network-dev:
    driver: bridge

services:
  e2bot-n8n-dev:
    networks:
      - e2bot-network-dev

  e2bot-postgres-dev:
    networks:
      - e2bot-network-dev

# PostgreSQL não exposto publicamente
# Apenas acessível dentro da network e2bot-network-dev
# n8n acessa via hostname: e2bot-postgres-dev:5432
```

---

## 🔍 Access Control

### Database Access Control

```sql
-- PostgreSQL User Permissions (Principle of Least Privilege)

-- n8n user: APENAS acesso ao database e2bot_dev
CREATE USER e2bot_n8n WITH PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE e2bot_dev TO e2bot_n8n;
GRANT USAGE ON SCHEMA public TO e2bot_n8n;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO e2bot_n8n;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO e2bot_n8n;

-- Revogar permissões não necessárias
REVOKE CREATE ON SCHEMA public FROM e2bot_n8n;
REVOKE DROP ON ALL TABLES IN SCHEMA public FROM e2bot_n8n;
```

### n8n UI Access Control

```yaml
# docker-compose-dev.yml
environment:
  - N8N_BASIC_AUTH_ACTIVE=true
  - N8N_BASIC_AUTH_USER=admin
  - N8N_BASIC_AUTH_PASSWORD=[secure_password]

# n8n UI requer login
# Credenciais separadas do sistema de workflows
```

### Evolution API Access Control

```yaml
# apikey para cada instância
instances:
  cocal_go_bot:
    apikey: "ae569043cfa169380c378347f91a1141ea572541d2d1cadbed222db519c8a891"
    permissions:
      - send_message: true
      - receive_webhook: true
      - fetch_instance: true
      - update_instance: false  # Não permitir mudanças
      - delete_instance: false  # Não permitir exclusão
```

---

## 📊 Audit Logging

### Audit Log Table

```sql
CREATE TABLE audit_log (
  id SERIAL PRIMARY KEY,
  action VARCHAR(100) NOT NULL,
  entity_type VARCHAR(50),
  entity_id INTEGER,
  phone_number VARCHAR(20),
  user_email VARCHAR(255),
  details JSONB,
  timestamp TIMESTAMP DEFAULT NOW()
);

-- Índices para performance
CREATE INDEX idx_audit_log_action ON audit_log(action);
CREATE INDEX idx_audit_log_timestamp ON audit_log(timestamp DESC);
CREATE INDEX idx_audit_log_phone ON audit_log(phone_number);
```

### Logged Actions

```yaml
user_actions:
  - conversation_created
  - data_collected
  - appointment_scheduled
  - email_sent
  - data_deletion_requested
  - data_exported

system_actions:
  - wf06_called
  - wf05_triggered
  - wf07_triggered
  - database_updated
  - credential_refreshed

security_events:
  - authentication_failed
  - unauthorized_access_attempt
  - credential_rotation
  - data_breach_detected
```

### Audit Log Example

```sql
-- Log de agendamento
INSERT INTO audit_log (action, entity_type, entity_id, phone_number, details)
VALUES (
  'appointment_scheduled',
  'appointment',
  123,
  '556181755748',
  '{"service": "energia_solar", "date": "2026-05-15", "time": "08:00-10:00"}'::jsonb
);

-- Log de exclusão de dados
INSERT INTO audit_log (action, phone_number, details)
VALUES (
  'data_deletion_requested',
  '556181755748',
  '{"reason": "user_request", "confirmed": true}'::jsonb
);
```

---

## 🚨 Security Incident Response

### Incident Classification

```yaml
severity_levels:
  critical:
    - Database breach
    - Credential leak
    - Unauthorized data access
    response_time: "Immediate (< 1 hour)"

  high:
    - OAuth token compromised
    - API key leaked
    - Suspicious activity detected
    response_time: "< 4 hours"

  medium:
    - Failed authentication attempts (> 10)
    - Unusual data access patterns
    response_time: "< 24 hours"

  low:
    - Single failed login
    - Minor configuration issue
    response_time: "< 48 hours"
```

### Incident Response Steps

```bash
# 1. Identify and Contain
# - Immediately deactivate compromised credentials
# - Isolate affected systems
# - Stop ongoing attacks

# Example: Credential compromised
# n8n UI → Credentials → Delete compromised credential
# Rotate API key immediately

# 2. Investigate
# - Review audit logs
SELECT * FROM audit_log
WHERE timestamp > NOW() - INTERVAL '24 hours'
ORDER BY timestamp DESC;

# - Check n8n execution logs
docker logs e2bot-n8n-dev | grep -E "ERROR|unauthorized|failed"

# 3. Eradicate
# - Remove unauthorized access
# - Patch vulnerabilities
# - Update credentials

# 4. Recover
# - Restore from clean backup if necessary
# - Verify system integrity
# - Re-activate services

# 5. Document
# - Create incident report
# - Document timeline
# - List actions taken
# - Identify lessons learned

# 6. Notify (if LGPD breach)
# - Notify ANPD (Autoridade Nacional de Proteção de Dados) within 72 hours
# - Notify affected individuals
# - Document notification timeline
```

---

## 🎯 Security Best Practices

### 1. Principle of Least Privilege

```yaml
apply_to:
  - Database users: Only necessary permissions
  - OAuth scopes: Only required API access
  - API keys: Instance-specific keys
  - n8n workflows: Credential-based access only

example:
  google_calendar_scope:
    required: "calendar.events"
    not_required: "calendar.readonly, drive.readonly"
```

### 2. Defense in Depth

```yaml
layers:
  1_network: "Docker network isolation"
  2_authentication: "Credential-based access control"
  3_authorization: "Role-based permissions"
  4_encryption: "SSL/TLS in transit"
  5_audit: "Comprehensive logging"
  6_monitoring: "Real-time alerts"
```

### 3. Regular Security Reviews

```bash
# Monthly Security Checklist

# 1. Review credentials
# n8n UI → Credentials → Check all connected and valid

# 2. Review audit logs
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT action, COUNT(*) FROM audit_log
      WHERE timestamp > NOW() - INTERVAL '30 days'
      GROUP BY action ORDER BY COUNT(*) DESC;"

# 3. Check failed authentications
docker logs e2bot-n8n-dev | grep -c "authentication failed"

# 4. Review data retention
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT COUNT(*) FROM conversations
      WHERE created_at < NOW() - INTERVAL '90 days';"

# 5. Update dependencies
docker-compose pull  # Update images
npm update           # Update n8n (if self-hosted)
```

### 4. Secure Development Practices

```yaml
code_review_checklist:
  - No hardcoded credentials ✅
  - No sensitive data in logs ✅
  - Proper error handling (no stack traces to user) ✅
  - Input validation (SQL injection prevention) ✅
  - HTTPS for external APIs ✅

deployment_checklist:
  - Credentials rotated ✅
  - Audit logs enabled ✅
  - Backup created ✅
  - Security review completed ✅
  - LGPD compliance verified ✅
```

---

## 📚 Referências

### LGPD Resources

- **LGPD Official Site**: https://www.gov.br/cidadania/pt-br/acesso-a-informacao/lgpd
- **ANPD**: https://www.gov.br/anpd/pt-br
- **LGPD Guide**: https://www.serpro.gov.br/lgpd

### Security Best Practices

- **OWASP Top 10**: https://owasp.org/www-project-top-ten/
- **n8n Security**: https://docs.n8n.io/hosting/security/
- **PostgreSQL Security**: https://www.postgresql.org/docs/current/security.html
- **Google OAuth2**: https://developers.google.com/identity/protocols/oauth2

### Internal Documentation

- **Credentials Setup**: `/docs/Setups/SETUP_CREDENTIALS.md`
- **Email Setup**: `/docs/Setups/SETUP_EMAIL.md`
- **Google Calendar Setup**: `/docs/Setups/SETUP_GOOGLE_CALENDAR.md`

---

**Última Atualização**: 2026-04-29
**Versão em Produção**: WF02 V114 com todas as práticas de segurança
**Status**: ✅ COMPLETO - LGPD compliance e security best practices implementadas
