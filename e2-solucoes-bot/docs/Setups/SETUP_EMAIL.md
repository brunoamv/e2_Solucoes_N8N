# Setup Email Notifications

## Visão Geral

Guia completo para configurar o sistema de envio de emails do bot E2 Soluções, incluindo notificações automáticas de agendamento, confirmações, lembretes e alertas para a equipe comercial.

## Pré-requisitos

- Conta de email para o bot (Gmail, Outlook, ou SMTP customizado)
- Acesso às configurações de segurança da conta
- Domínio próprio (opcional, para email profissional)

## Opção A: Gmail (Recomendado para Dev/Teste)

### A.1. Criar Conta Gmail Dedicada

1. Acesse: https://accounts.google.com/signup
2. Crie conta específica para o bot:
   - Email: `bot@e2solucoes.com.br` (se tiver domínio)
   - OU: `e2solucoes.bot@gmail.com`
   - Nome: "E2 Soluções Bot"

### A.2. Habilitar "App Passwords"

**IMPORTANTE:** Gmail bloqueou "less secure apps". Use App Password:

1. Acesse: https://myaccount.google.com/security
2. Ative **"2-Step Verification"** (obrigatório)
3. Volte em Security
4. Busque: **"App passwords"**
5. Clique em **"App passwords"**
6. Selecione:
   - App: **Mail**
   - Device: **Other (Custom name)** → "E2 Bot n8n"
7. Clique em **"Generate"**

Será gerado um password de 16 caracteres:

```
xxxx xxxx xxxx xxxx
```

**Guarde esta senha!** Ela substitui sua senha normal para SMTP.

### A.3. Configurar SMTP Gmail

```bash
# Editar .env.dev
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_SECURE=false  # STARTTLS
EMAIL_USER=e2solucoes.bot@gmail.com
EMAIL_PASSWORD=xxxx xxxx xxxx xxxx  # App Password (remover espaços)
EMAIL_FROM_NAME=E2 Soluções
EMAIL_FROM_ADDRESS=e2solucoes.bot@gmail.com
```

### A.4. Testar Conexão SMTP

```bash
#!/bin/bash
# scripts/test-email.sh

set -a
source docker/.env.dev
set +a

echo "🧪 Testando conexão SMTP..."

# Remover espaços do app password
EMAIL_PASSWORD=$(echo "$EMAIL_PASSWORD" | tr -d ' ')

# Testar conexão
swaks --to bruno@e2solucoes.com.br \
  --from "$EMAIL_FROM_ADDRESS" \
  --server "$EMAIL_HOST:$EMAIL_PORT" \
  --auth LOGIN \
  --auth-user "$EMAIL_USER" \
  --auth-password "$EMAIL_PASSWORD" \
  --tls \
  --header "Subject: Teste E2 Bot" \
  --body "Email de teste do bot E2 Soluções."

# Se swaks não instalado:
# sudo apt-get install swaks  # Ubuntu/Debian
# brew install swaks          # macOS
```

**Resultado esperado:**

```
*** CONNECTED to smtp.gmail.com:587
=== TLS started with cipher ...
<-  250 2.0.0 OK
=== Message sent successfully
```

---

## Opção B: Domínio Próprio (SMTP Customizado)

### B.1. Configurar DNS (MX Records)

Se usar email `bot@e2solucoes.com.br`, configure DNS:

```
MX Record:
  Priority: 10
  Value: mail.e2solucoes.com.br

A Record (mail):
  Name: mail
  Value: [IP do servidor SMTP]

SPF Record:
  Type: TXT
  Value: v=spf1 ip4:[IP do servidor] ~all

DKIM Record:
  Type: TXT
  Name: default._domainkey
  Value: [Chave DKIM do provedor]
```

### B.2. Escolher Provedor SMTP

**Opções profissionais:**

1. **SendGrid** (https://sendgrid.com)
   - Free tier: 100 emails/dia
   - Configuração simples
   - Excelente deliverability

2. **Mailgun** (https://mailgun.com)
   - Free tier: 5.000 emails/mês (3 meses)
   - API poderosa
   - Bom para transacional

3. **Amazon SES** (https://aws.amazon.com/ses/)
   - $0.10 por 1.000 emails
   - Escalável
   - Requer verificação de domínio

4. **Postmark** (https://postmarkapp.com)
   - Free trial: 100 emails
   - Especializado em transacional
   - Deliverability top

### B.3. Configurar SendGrid (Exemplo)

1. **Criar conta**: https://signup.sendgrid.com/
2. **Verificar email**
3. **Criar API Key**:
   - Settings → API Keys → Create API Key
   - Nome: "E2 Bot"
   - Permissions: Full Access (ou apenas Mail Send)
   - Copiar key: `SG.xxxxxxxxxxxxxxxxxxxx`

4. **Configurar .env**:

```bash
# SendGrid SMTP
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_SECURE=false
EMAIL_USER=apikey  # Literal "apikey"
EMAIL_PASSWORD=SG.xxxxxxxxxxxxxxxxxxxx  # API Key
EMAIL_FROM_NAME=E2 Soluções
EMAIL_FROM_ADDRESS=bot@e2solucoes.com.br
```

5. **Verificar domínio** (para email profissional):
   - Settings → Sender Authentication → Verify a Single Sender
   - Preencher dados da empresa
   - Verificar email de confirmação

---

## Etapa 3: Configurar n8n Email Node

### 3.1. Adicionar Credencial SMTP

1. Acesse: http://localhost:5678
2. Vá em: **Credentials → Add Credential**
3. Busque: "SMTP"
4. Selecione: **"SMTP"**
5. Preencha:

```yaml
Credential Name: E2 Bot Email
Host: smtp.gmail.com (ou outro)
Port: 587
User: e2solucoes.bot@gmail.com
Password: xxxx xxxx xxxx xxxx (App Password)
SSL/TLS: false (usar STARTTLS)
From Email: e2solucoes.bot@gmail.com
From Name: E2 Soluções
```

6. Clique em **"Test"** → Deve aparecer "Connection successful"
7. **"Create"**

### 3.2. Importar Workflow de Email

```bash
# Workflow já criado: n8n/workflows/07_send_email.json
```

No n8n:
1. **Workflows → Import from File**
2. Selecionar: `n8n/workflows/07_send_email.json`
3. Configurar credencial SMTP criada
4. Ativar workflow

---

## Etapa 4: Templates de Email

### 4.1. Templates Disponíveis

Localização: `templates/emails/`

```
templates/emails/
├── appointment_confirmation.html     # Confirmação de agendamento
├── appointment_reminder_24h.html     # Lembrete 24h antes
├── appointment_reminder_2h.html      # Lembrete 2h antes
├── lead_notification_comercial.html  # Notificar equipe comercial
└── appointment_cancelled.html        # Cancelamento de visita
```

### 4.2. Estrutura de Template

Exemplo: `appointment_confirmation.html`

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    body {
      font-family: Arial, sans-serif;
      line-height: 1.6;
      color: #333;
      max-width: 600px;
      margin: 0 auto;
      padding: 20px;
    }
    .header {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 30px;
      text-align: center;
      border-radius: 10px 10px 0 0;
    }
    .content {
      background: white;
      padding: 30px;
      border: 1px solid #e0e0e0;
      border-top: none;
    }
    .info-box {
      background: #f5f5f5;
      padding: 20px;
      border-radius: 8px;
      margin: 20px 0;
    }
    .info-row {
      display: flex;
      justify-content: space-between;
      margin: 10px 0;
    }
    .button {
      display: inline-block;
      background: #667eea;
      color: white;
      padding: 12px 30px;
      text-decoration: none;
      border-radius: 5px;
      margin: 20px 0;
    }
    .footer {
      text-align: center;
      color: #888;
      font-size: 12px;
      margin-top: 30px;
      padding-top: 20px;
      border-top: 1px solid #e0e0e0;
    }
  </style>
</head>
<body>
  <div class="header">
    <h1>✅ Visita Técnica Agendada</h1>
  </div>

  <div class="content">
    <p>Olá, <strong>{{lead_name}}</strong>!</p>

    <p>Sua visita técnica foi confirmada com sucesso!</p>

    <div class="info-box">
      <h3>📋 Detalhes do Agendamento:</h3>
      <div class="info-row">
        <span><strong>📅 Data:</strong></span>
        <span>{{visit_date}}</span>
      </div>
      <div class="info-row">
        <span><strong>🕐 Horário:</strong></span>
        <span>{{visit_time}}</span>
      </div>
      <div class="info-row">
        <span><strong>📍 Endereço:</strong></span>
        <span>{{address}}</span>
      </div>
      <div class="info-row">
        <span><strong>⚡ Serviço:</strong></span>
        <span>{{service_type}}</span>
      </div>
    </div>

    <h3>👨‍🔧 O que esperar?</h3>
    <ul>
      <li>Nosso técnico chegará no horário agendado</li>
      <li>Duração aproximada: 1h30</li>
      <li>Vistoria completa do local</li>
      <li>Proposta técnica e comercial em até 48h</li>
    </ul>

    <h3>📱 Precisa reagendar?</h3>
    <p>Entre em contato conosco:</p>
    <a href="https://wa.me/5562999999999" class="button">
      💬 WhatsApp: (62) 99999-9999
    </a>

    <p style="margin-top: 30px; color: #888; font-size: 14px;">
      Você receberá lembretes automáticos 24h e 2h antes da visita.
    </p>
  </div>

  <div class="footer">
    <p><strong>E2 Soluções - Engenharia Elétrica</strong></p>
    <p>Goiânia - GO | (62) 99999-9999</p>
    <p>www.e2solucoes.com.br</p>
  </div>
</body>
</html>
```

### 4.3. Variáveis Suportadas

Cada template suporta variáveis dinâmicas:

```yaml
appointment_confirmation.html:
  - {{lead_name}}
  - {{visit_date}}
  - {{visit_time}}
  - {{address}}
  - {{service_type}}
  - {{phone}}

appointment_reminder_24h.html:
  - {{lead_name}}
  - {{visit_date}}
  - {{visit_time}}
  - {{address}}
  - {{technician_name}}

appointment_reminder_2h.html:
  - {{lead_name}}
  - {{visit_time}}
  - {{technician_name}}

lead_notification_comercial.html:
  - {{lead_name}}
  - {{phone}}
  - {{service_type}}
  - {{collected_data}}
  - {{rdstation_link}}
```

---

## Etapa 5: Enviar Emails via n8n

### 5.1. Workflow de Envio

O workflow `07_send_email.json` funciona como serviço reutilizável:

```
[Webhook Trigger: /webhook/send-email]
    ↓
[Load Template]
    ↓
[Replace Variables]
    ↓
[Send Email (SMTP)]
    ↓
[Log in Database]
    ↓
[Return Success]
```

### 5.2. Chamar via HTTP Request

De outros workflows, chamar:

```javascript
// No nó HTTP Request
{
  "method": "POST",
  "url": "http://n8n:5678/webhook/send-email",
  "headers": {
    "Content-Type": "application/json"
  },
  "body": {
    "to": "cliente@email.com",
    "template": "appointment_confirmation",
    "variables": {
      "lead_name": "João Silva",
      "visit_date": "15/01/2024",
      "visit_time": "14:00",
      "address": "Rua Teste, 123",
      "service_type": "Energia Solar"
    }
  }
}
```

### 5.3. Resposta

```json
{
  "success": true,
  "message_id": "msg_xxxxx",
  "timestamp": "2024-01-10T14:30:00Z"
}
```

---

## Etapa 6: Notificações Automáticas

### 6.1. Confirmação de Agendamento

Trigger: Após criar evento no Google Calendar

```javascript
// No workflow 05_appointment_scheduler.json
// Após criar evento com sucesso:
[HTTP Request to /webhook/send-email]
  template: "appointment_confirmation"
  to: {{lead_email}}
```

### 6.2. Lembrete 24h Antes

Workflow `06_appointment_reminders.json`:

```yaml
Trigger: Cron (a cada 1 hora)
Query:
  SELECT * FROM appointments
  WHERE status = 'confirmed'
    AND reminder_24h_sent = false
    AND visit_datetime BETWEEN NOW() + INTERVAL '23 hours'
                           AND NOW() + INTERVAL '25 hours'

Action:
  - Enviar email (template: appointment_reminder_24h)
  - UPDATE reminder_24h_sent = true
```

### 6.3. Lembrete 2h Antes

```yaml
Trigger: Cron (a cada 30 minutos)
Query:
  SELECT * FROM appointments
  WHERE status = 'confirmed'
    AND reminder_2h_sent = false
    AND visit_datetime BETWEEN NOW() + INTERVAL '1 hour 45 minutes'
                           AND NOW() + INTERVAL '2 hours 15 minutes'

Action:
  - Enviar email (template: appointment_reminder_2h)
  - Enviar WhatsApp
  - UPDATE reminder_2h_sent = true
```

### 6.4. Notificação para Comercial

Trigger: Lead qualificado e pronto para contato humano

```javascript
// No workflow 02_ai_agent_conversation.json
// Quando conversation_state = 'completed':
[HTTP Request to /webhook/send-email]
  template: "lead_notification_comercial"
  to: comercial@e2solucoes.com.br
  cc: gerente@e2solucoes.com.br
```

---

## Etapa 7: Logs e Auditoria

### 7.1. Criar Tabela de Logs

```sql
CREATE TABLE email_logs (
  id SERIAL PRIMARY KEY,
  recipient VARCHAR(255) NOT NULL,
  subject VARCHAR(500),
  template_used VARCHAR(100),
  message_id VARCHAR(255),
  status VARCHAR(50),  -- sent, failed, bounced
  error_message TEXT,
  sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  -- Relacionamento
  lead_id INTEGER REFERENCES leads(id),
  appointment_id INTEGER REFERENCES appointments(id),

  -- Metadata
  smtp_server VARCHAR(255),
  retry_count INTEGER DEFAULT 0
);

-- Índices
CREATE INDEX idx_email_logs_recipient ON email_logs(recipient);
CREATE INDEX idx_email_logs_sent_at ON email_logs(sent_at);
CREATE INDEX idx_email_logs_status ON email_logs(status);
```

### 7.2. Registrar Envios

No workflow `07_send_email.json`, após enviar:

```sql
INSERT INTO email_logs (
  recipient,
  subject,
  template_used,
  message_id,
  status,
  lead_id,
  appointment_id
) VALUES (
  '{{to}}',
  '{{subject}}',
  '{{template}}',
  '{{response.messageId}}',
  'sent',
  {{lead_id}},
  {{appointment_id}}
);
```

### 7.3. Monitorar Falhas

```sql
-- Ver falhas de envio (últimas 24h)
SELECT
  recipient,
  subject,
  error_message,
  retry_count,
  sent_at
FROM email_logs
WHERE status = 'failed'
  AND sent_at >= NOW() - INTERVAL '24 hours'
ORDER BY sent_at DESC;

-- Estatísticas de envio
SELECT
  DATE(sent_at) as dia,
  COUNT(*) as total,
  SUM(CASE WHEN status = 'sent' THEN 1 ELSE 0 END) as enviados,
  SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as falhas,
  ROUND(100.0 * SUM(CASE WHEN status = 'sent' THEN 1 ELSE 0 END) / COUNT(*), 2) as taxa_sucesso
FROM email_logs
WHERE sent_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE(sent_at)
ORDER BY dia DESC;
```

---

## Etapa 8: Deliverability (Anti-Spam)

### 8.1. Configurar SPF

```
# DNS TXT Record
v=spf1 include:_spf.google.com ~all

# Para SendGrid:
v=spf1 include:sendgrid.net ~all
```

### 8.2. Configurar DKIM

Gmail: Configurado automaticamente

SendGrid: Settings → Sender Authentication → Domain Authentication

### 8.3. Configurar DMARC

```
# DNS TXT Record (_dmarc.e2solucoes.com.br)
v=DMARC1; p=none; rua=mailto:dmarc-reports@e2solucoes.com.br; pct=100; adkim=r; aspf=r
```

### 8.4. Boas Práticas Anti-Spam

1. **From Name consistente**
   - Sempre "E2 Soluções"
   - Nunca "noreply" ou genérico

2. **Subject claro**
   - "Confirmação de Visita - E2 Soluções"
   - Evitar: "RE:", "FWD:", caps lock, muitos !!!

3. **Conteúdo**
   - Mais texto que imagens
   - Links funcionais
   - Botão de unsubscribe (para marketing)

4. **Rate Limiting**
   - Máx 100 emails/hora (Gmail free)
   - Máx 500 emails/dia (Gmail free)
   - Usar fila se necessário

---

## Etapa 9: Troubleshooting

### Problema: "Authentication failed"

**Causa:** App Password incorreto ou expirado

**Solução:**
```bash
# Verificar variáveis
echo "User: $EMAIL_USER"
echo "Password: ${EMAIL_PASSWORD:0:4}****"  # Primeiros 4 chars

# Gerar novo App Password:
# https://myaccount.google.com/apppasswords

# Atualizar .env e reiniciar n8n
docker-compose restart n8n
```

### Problema: "SMTP timeout"

**Causa:** Porta bloqueada ou host incorreto

**Solução:**
```bash
# Testar conectividade
telnet smtp.gmail.com 587
# Deve conectar

# Verificar firewall
sudo ufw status
sudo ufw allow 587/tcp
```

### Problema: Emails vão para spam

**Causa:** SPF/DKIM não configurado

**Solução:**
1. Configurar SPF (Step 8.1)
2. Configurar DKIM (Step 8.2)
3. Testar: https://www.mail-tester.com/
4. Objetivo: Score 8/10 ou melhor

### Problema: "Recipient address rejected"

**Causa:** Email inválido ou não existe

**Solução:**
```javascript
// Validar email antes de enviar
function validateEmail(email) {
  const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return regex.test(email);
}

// No workflow, adicionar validação
if (!validateEmail(to_email)) {
  throw new Error('Email inválido: ' + to_email);
}
```

---

## Etapa 10: Monitoramento

### 10.1. Dashboard de Emails

```sql
-- Resumo diário
SELECT
  DATE(sent_at) as dia,
  template_used,
  COUNT(*) as total,
  SUM(CASE WHEN status = 'sent' THEN 1 ELSE 0 END) as ok,
  SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as falha
FROM email_logs
WHERE sent_at >= NOW() - INTERVAL '7 days'
GROUP BY DATE(sent_at), template_used
ORDER BY dia DESC, template_used;
```

### 10.2. Alertas de Falha

```bash
#!/bin/bash
# scripts/check-email-failures.sh

FAILURES=$(psql $DATABASE_URL -t -c "
  SELECT COUNT(*)
  FROM email_logs
  WHERE status = 'failed'
    AND sent_at >= NOW() - INTERVAL '1 hour'
")

if [ "$FAILURES" -gt 5 ]; then
  echo "⚠️ ALERTA: $FAILURES emails falharam na última hora!"
  # Enviar alerta (Discord, SMS, etc)
fi
```

### 10.3. Taxa de Abertura (Opcional)

Para tracking de abertura, adicionar pixel transparente:

```html
<!-- No final do template -->
<img src="https://seu-dominio.com/track/open/{{email_log_id}}.png"
     width="1" height="1" style="display:none" />
```

Criar endpoint que registra:

```javascript
// Endpoint: GET /track/open/:id.png
app.get('/track/open/:id.png', async (req, res) => {
  await db.query(
    'UPDATE email_logs SET opened_at = NOW() WHERE id = $1',
    [req.params.id]
  );

  // Retornar pixel transparente 1x1
  const pixel = Buffer.from(
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=',
    'base64'
  );

  res.set('Content-Type', 'image/png');
  res.send(pixel);
});
```

---

## Recursos Adicionais

- **Gmail SMTP Docs**: https://support.google.com/mail/answer/7126229
- **SendGrid Docs**: https://docs.sendgrid.com/
- **n8n Email Node**: https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.emailsend/
- **Email Testing**: https://www.mail-tester.com/
- **SPF Checker**: https://www.kitterman.com/spf/validate.html
- **Template Testing**: https://www.emailonacid.com/ (pago)

---

## Checklist de Configuração

- [ ] Conta de email criada (Gmail ou SMTP customizado)
- [ ] App Password gerado (se Gmail)
- [ ] SPF/DKIM configurados (se domínio próprio)
- [ ] .env.dev atualizado com credenciais SMTP
- [ ] Teste de conexão SMTP realizado (swaks)
- [ ] Credencial SMTP configurada no n8n
- [ ] Workflow 07_send_email.json importado e ativado
- [ ] Templates HTML validados
- [ ] Teste de envio realizado com sucesso
- [ ] Email recebido (não na spam)
- [ ] Tabela email_logs criada
- [ ] Logs de envio funcionando
- [ ] Notificações de confirmação ativas
- [ ] Lembretes 24h e 2h configurados
- [ ] Notificações para comercial funcionando
- [ ] Monitoramento de falhas ativo

---

**Configuração completa!** O sistema de emails está pronto para enviar notificações automáticas com templates profissionais.
