# Setup Email - SMTP Configuration

> **Versão**: 3.0 (DEFINITIVA) | **Atualização**: 2026-04-08
> **Método**: Gmail App Password (desenvolvimento) + SMTP dedicado (produção)
> **Objetivo**: Configurar SMTP para WF07 (Send Email)

---

## 📋 Índice

1. [Pré-requisitos](#pré-requisitos)
2. [Opção A: Gmail App Password (Desenvolvimento)](#opção-a-gmail-app-password-desenvolvimento)
3. [Opção B: SMTP Dedicado (Produção)](#opção-b-smtp-dedicado-produção)
4. [Configurar Credencial n8n](#configurar-credencial-n8n)
5. [Testar Conexão](#testar-conexão)
6. [Troubleshooting](#troubleshooting)

---

## Pré-requisitos

**Obrigatório**:
- Conta Gmail (opção A) ou serviço SMTP (opção B)
- n8n rodando em `http://localhost:5678`
- WF07 (Send Email) importado

**Verificar n8n rodando**:
```bash
curl -I http://localhost:5678
# Deve retornar HTTP 200 ou redirecionamento
```

---

## Opção A: Gmail App Password (Desenvolvimento)

### ✅ RECOMENDADO: Port 465 + SSL/TLS

**Gmail SMTP Ports**:
- **Port 465**: SSL/TLS direto → Usar `Secure: true` ✅ **(RECOMENDADO)**
- **Port 587**: STARTTLS → Usar `Secure: false` (configuração alternativa)

**Configuração testada e aprovada**:
```yaml
Port: 465
SSL/TLS: habilitado (marcar checkbox)
Secure: true
```

**Configuração alternativa (Port 587)**:
- Usar apenas se Port 465 não funcionar no seu ambiente
- Requer `Secure: false` (STARTTLS)
- Erro comum se usar Port 587 + SSL/TLS habilitado:
  ```
  error:0A00010B:SSL routines:tls_validate_record_header:wrong version number
  ```

---

### Passo 1: Habilitar 2-Step Verification

1. **Acessar**: https://myaccount.google.com/security
2. **2-Step Verification** → **Enable**
3. Seguir processo de verificação (SMS, autenticador, etc.)

**Aguardar 10 minutos** para propagação da configuração

---

### Passo 2: Criar App Password

1. **Voltar**: https://myaccount.google.com/security
2. **Buscar**: "App passwords" na barra de pesquisa
3. **Clicar**: "App passwords"
4. **Selecionar**:
   - **App**: Mail
   - **Device**: Other (Custom name)
   - **Digite**: "E2 Bot n8n"
5. **Generate** → Copiar senha de 16 caracteres:

```
abcd efgh ijkl mnop
```

**⚠️ IMPORTANTE**: Remover espaços ao configurar no n8n:
- ✅ `abcdefghijklmnop`
- ❌ `abcd efgh ijkl mnop`

---

### Passo 3: Configurar docker/.env

```bash
# Editar arquivo
nano docker/.env

# Adicionar variáveis SMTP
SMTP_HOST=smtp.gmail.com
SMTP_PORT=465
SMTP_SECURE=true  # SSL/TLS direto ✅ RECOMENDADO
SMTP_USER=bruno.amv@gmail.com
SMTP_PASSWORD=abcdefghijklmnop  # App Password SEM ESPAÇOS
EMAIL_FROM=E2 Soluções <bruno.amv@gmail.com>
```

**Reiniciar n8n** para carregar variáveis:
```bash
docker-compose -f docker/docker-compose-dev.yml restart e2bot-n8n-dev
```

---

## Opção B: SMTP Dedicado (Produção)

### Provedores Recomendados

**1. SendGrid** (https://sendgrid.com)
- **Free tier**: 100 emails/dia
- **Vantagem**: Excelente deliverability, fácil configuração
- **Uso**: Emails transacionais

**Configuração SendGrid**:
```yaml
Host: smtp.sendgrid.net
Port: 587
Secure: false  # STARTTLS
User: apikey  # Literal "apikey"
Password: SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
From Email: bot@e2solucoes.com.br
```

---

**2. Mailgun** (https://mailgun.com)
- **Free tier**: 5.000 emails/mês (3 meses)
- **Vantagem**: API poderosa, boa documentação
- **Uso**: Emails transacionais e marketing

**Configuração Mailgun**:
```yaml
Host: smtp.mailgun.org
Port: 587
Secure: false  # STARTTLS
User: postmaster@seu-dominio.com
Password: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
From Email: bot@seu-dominio.com
```

---

**3. Amazon SES** (https://aws.amazon.com/ses/)
- **Custo**: $0.10 por 1.000 emails
- **Vantagem**: Escalável, integração AWS
- **Uso**: Alto volume de emails

**Configuração Amazon SES**:
```yaml
Host: email-smtp.us-east-1.amazonaws.com
Port: 587
Secure: false  # STARTTLS
User: AKIAXXXXXXXXXXXXXXXX  # SMTP credentials
Password: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
From Email: bot@seu-dominio.com
```

---

## Configurar Credencial n8n

### Passo 1: Criar Credencial SMTP

1. **Acessar n8n**: http://localhost:5678

2. **Menu lateral** → **Credentials**

3. **New credential** → Buscar **"SMTP"**

4. **Preencher** (Opção A - Gmail):

```yaml
Credential Name: SMTP - E2 Email
Host: smtp.gmail.com
Port: 465
Secure: true  # ✅ SSL/TLS (MARCAR checkbox SSL/TLS)
User: bruno.amv@gmail.com
Password: abcdefghijklmnop  # App Password SEM ESPAÇOS
From Email: E2 Soluções <bruno.amv@gmail.com>
```

**✅ CONFIGURAÇÃO RECOMENDADA**:
- **Port 465** → **Secure: true** (SSL/TLS) ✅
- Marcar checkbox "SSL/TLS" no n8n

**Configuração Alternativa**:
- **Port 587** → **Secure: false** (STARTTLS)
- Usar apenas se Port 465 não funcionar

5. **Save** (não há botão Test na credencial SMTP)

---

### Passo 2: Vincular Credencial ao WF07

1. **Workflows** → **07 Send Email**

2. **Abrir workflow**

3. **Localizar node "Send Email" (SMTP)**

4. **Credential to connect with** → Selecionar **"SMTP - E2 Email"**

5. **Save workflow** (Ctrl+S)

---

## Testar Conexão

### Teste 1: Envio Manual via WF07

**Dados de teste**:
```json
{
  "lead_email": "bruno.amv@gmail.com",
  "lead_name": "Teste SMTP",
  "service_type": "energia_solar",
  "city": "goiania-go",
  "calendar_success": true,
  "scheduled_date": "2026-04-15",
  "scheduled_time_start": "09:00:00",
  "scheduled_time_end": "11:00:00"
}
```

**Executar**:
1. WF07 → **Execute Workflow**
2. Colar JSON acima no input
3. **Execute**

**✅ Resultado esperado**:
- Node "Send Email" → **SUCCESS** (verde)
- Email recebido em `bruno.amv@gmail.com`
- Database log criado:
  ```sql
  SELECT * FROM email_logs ORDER BY sent_at DESC LIMIT 1;
  ```

**❌ Se falhar**: Ver [Troubleshooting](#troubleshooting)

---

### Teste 2: Verificar Email Recebido

**Verificar caixa de entrada**:
1. Inbox de `bruno.amv@gmail.com`
2. Procurar email de "E2 Soluções"
3. Subject: "Confirmação de Agendamento - E2 Soluções"
4. Verificar template renderizado corretamente:
   - Nome: "Teste SMTP"
   - Data: "15/04/2026"
   - Horário: "09:00 às 11:00"
   - Serviço: "energia_solar"

**Se email não chegou**:
- Verificar pasta **Spam**
- Verificar logs do WF07 (Executions)
- Verificar `email_logs` table:
  ```sql
  SELECT recipient_email, status, error_message, sent_at
  FROM email_logs
  ORDER BY sent_at DESC
  LIMIT 5;
  ```

---

### Teste 3: Verificar Log no Banco

```bash
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "
  SELECT
    id,
    recipient_email,
    recipient_name,
    template_used,
    status,
    sent_at
  FROM email_logs
  ORDER BY sent_at DESC
  LIMIT 1;
"
```

**✅ Resultado esperado**:
```
 id | recipient_email      | recipient_name | template_used            | status | sent_at
----+---------------------+----------------+--------------------------+--------+-------------------------
  1 | bruno.amv@gmail.com | Teste SMTP     | confirmacao_agendamento  | sent   | 2026-04-08 15:30:00
```

---

## Troubleshooting

### Erro: "Couldn't connect with these settings"

**Erro completo**:
```
50B223A123730000:error:0A00010B:SSL routines:tls_validate_record_header:wrong version number
```

**Causa**: Configuração incorreta de Port + SSL/TLS

**✅ SOLUÇÃO RECOMENDADA** (testada com sucesso):
1. Editar credencial SMTP no n8n
2. **Port**: 465
3. **SSL/TLS**: habilitado ✅ (marcar checkbox)
4. **Secure**: true
5. Save e testar novamente

**Solução Alternativa** (se Port 465 não funcionar):
1. **Port**: 587
2. **SSL/TLS**: desabilitado (desmarcar checkbox)
3. **Secure**: false (STARTTLS)

**Explicação técnica**:
- **Port 465**: SSL/TLS direto (criptografia desde o início) ✅ **RECOMENDADO**
- **Port 587**: STARTTLS (upgrade de conexão não criptografada para TLS)
- Misturar Port 587 + SSL/TLS habilitado causa erro de handshake
- Port 465 tem melhor compatibilidade e é a configuração oficial do Gmail

---

### Erro: "Authentication failed"

**Causa 1**: App Password incorreto ou com espaços

**Solução**:
```bash
# App Password deve ser SEM ESPAÇOS
✅ abcdefghijklmnop
❌ abcd efgh ijkl mnop

# Gerar novo App Password:
# https://myaccount.google.com/apppasswords
```

**Causa 2**: 2-Step Verification não habilitada

**Solução**:
1. https://myaccount.google.com/security
2. Enable 2-Step Verification
3. **Aguardar 10 minutos**
4. Criar App Password

---

### Erro: "SMTP timeout" ou "Connection refused"

**Causa**: Porta 587 bloqueada ou firewall

**Solução**:
```bash
# Testar conectividade
telnet smtp.gmail.com 587
# Deve conectar: "Trying 142.251.XXX.XXX..."

# Se não conectar, verificar firewall
sudo ufw status
sudo ufw allow 587/tcp

# Reiniciar Docker network
docker-compose -f docker/docker-compose-dev.yml restart
```

---

### Erro: "Recipient address rejected" ou Email inválido

**Causa**: Email de destino inválido ou não existe

**Solução**: Verificar formato do email
```javascript
// Regex validação
const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

// Exemplos válidos:
✅ bruno.amv@gmail.com
✅ contato@e2solucoes.com.br

// Exemplos inválidos:
❌ bruno.amv@gmail (sem domínio)
❌ @gmail.com (sem usuário)
❌ bruno amv@gmail.com (espaços)
```

---

### Email vai para Spam

**Causa**: SPF/DKIM não configurado (apenas se usar domínio próprio)

**Solução Gmail**: Usar App Password de conta Gmail verificada

**Solução SMTP dedicado**: Configurar SPF/DKIM no DNS

**SPF Record** (exemplo):
```
# DNS TXT Record
v=spf1 include:_spf.google.com ~all

# Para SendGrid:
v=spf1 include:sendgrid.net ~all
```

**Teste deliverability**:
1. https://www.mail-tester.com/
2. Enviar email de teste para endereço fornecido
3. Ver score (objetivo: 8/10 ou melhor)

---

## Variáveis de Ambiente (Referência)

**Arquivo**: `docker/.env`

```bash
# ============================================================================
# SMTP / Email Configuration
# ============================================================================

# Opção A: Gmail App Password
SMTP_HOST=smtp.gmail.com
SMTP_PORT=465
SMTP_SECURE=true  # SSL/TLS direto ✅ RECOMENDADO
SMTP_USER=bruno.amv@gmail.com
SMTP_PASSWORD=abcdefghijklmnop  # App Password SEM ESPAÇOS
EMAIL_FROM=E2 Soluções <bruno.amv@gmail.com>

# Opção B: SendGrid
# SMTP_HOST=smtp.sendgrid.net
# SMTP_PORT=587
# SMTP_SECURE=false
# SMTP_USER=apikey
# SMTP_PASSWORD=SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# EMAIL_FROM=E2 Soluções <bot@e2solucoes.com.br>

# Opção C: Mailgun
# SMTP_HOST=smtp.mailgun.org
# SMTP_PORT=587
# SMTP_SECURE=false
# SMTP_USER=postmaster@seu-dominio.com
# SMTP_PASSWORD=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# EMAIL_FROM=E2 Soluções <bot@seu-dominio.com>
```

**Carregar variáveis**:
```bash
docker-compose -f docker/docker-compose-dev.yml restart e2bot-n8n-dev
```

---

## Templates de Email

**Localização**: `templates/emails/` (servidos via nginx)

**Templates disponíveis**:
- `confirmacao_agendamento.html` - Confirmação de visita técnica
- `lembrete_24h.html` - Lembrete 24h antes
- `lembrete_2h.html` - Lembrete 2h antes
- `novo_lead.html` - Notificação equipe comercial
- `apos_visita.html` - Follow-up pós-visita

**Variáveis suportadas**: `{{lead_name}}`, `{{formatted_date}}`, `{{formatted_time}}`, `{{address}}`, `{{service_type}}`, etc.

**Acesso via HTTP**:
```bash
# Verificar template renderizado
curl http://localhost:8081/confirmacao_agendamento.html
```

---

## Checklist de Configuração

Antes de considerar setup completo:

- [ ] 2-Step Verification habilitada na conta Gmail
- [ ] App Password gerado (16 caracteres)
- [ ] `docker/.env` atualizado com SMTP_* variables
- [ ] n8n reiniciado para carregar variáveis
- [ ] Credencial SMTP criada no n8n:
  - [ ] Port 465 + Secure: true ✅
  - [ ] Password SEM ESPAÇOS
- [ ] WF07 importado e ativo
- [ ] Credencial SMTP vinculada ao node "Send Email"
- [ ] Teste manual executado com sucesso
- [ ] Email recebido (não na spam)
- [ ] Log criado em `email_logs` table com status "sent"
- [ ] Template renderizado corretamente (variáveis substituídas)

**Tudo OK?** 🎉 **SMTP configurado com sucesso!**

---

## Boas Práticas

### Rate Limiting

**Gmail Free Account**:
- Máximo: 500 emails/dia
- Recomendado: 100 emails/hora

**Implementação** (futuro):
```javascript
// Queue de emails com delay
const emailQueue = [];
const DELAY_MS = 1000; // 1 email/segundo

async function processEmailQueue() {
  while (emailQueue.length > 0) {
    const email = emailQueue.shift();
    await sendEmail(email);
    await sleep(DELAY_MS);
  }
}
```

### Monitoramento

**Dashboard SQL**:
```sql
-- Resumo diário de envios
SELECT
  DATE(sent_at) as dia,
  COUNT(*) as total,
  SUM(CASE WHEN status = 'sent' THEN 1 ELSE 0 END) as enviados,
  SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as falhas,
  ROUND(100.0 * SUM(CASE WHEN status = 'sent' THEN 1 ELSE 0 END) / COUNT(*), 2) as taxa_sucesso
FROM email_logs
WHERE sent_at >= NOW() - INTERVAL '7 days'
GROUP BY DATE(sent_at)
ORDER BY dia DESC;
```

**Alerta de falhas**:
```bash
#!/bin/bash
# scripts/check-email-failures.sh

FAILURES=$(docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -t -c "
  SELECT COUNT(*)
  FROM email_logs
  WHERE status = 'failed'
    AND sent_at >= NOW() - INTERVAL '1 hour'
")

if [ "$FAILURES" -gt 5 ]; then
  echo "⚠️ ALERTA: $FAILURES emails falharam na última hora!"
fi
```

---

## Documentação Relacionada

**Setup**:
- `QUICKSTART.md` - Guia completo de setup (seção 2.3)
- `SETUP_CREDENTIALS.md` - Todas as credenciais n8n (seção 3)

**Workflows**:
- `BUGFIX_WF07_V13_INSERT_SELECT_FIX.md` - WF07 V13 email workflow (INSERT...SELECT pattern)

**Arquitetura**:
- `ARCHITECTURE.md` - Visão geral do sistema
- `CLAUDE.md` - Contexto completo do projeto

---

**Última Atualização**: 2026-04-08
**Versão**: 3.0 (Consolidação DEFINITIVA)
**Mantido por**: E2 Soluções Dev Team
