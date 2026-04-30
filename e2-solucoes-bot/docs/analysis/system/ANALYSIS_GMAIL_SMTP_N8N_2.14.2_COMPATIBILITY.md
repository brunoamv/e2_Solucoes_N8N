# ANÁLISE PROFUNDA: Gmail SMTP + n8n 2.14.2 Compatibilidade

**Data**: 2026-04-01
**Versão n8n**: 2.14.2
**Node**: `emailSend` v2.1
**Status**: ⚠️ PROBLEMA CRÍTICO DE CONFIGURAÇÃO

---

## 🔍 Análise do Erro

### Erro Recebido (Execução 18579)
```
50A2312CC1710000:error:0A00010B:SSL routines:tls_validate_record_header:wrong version number:../../deps/openssl/openssl/ssl/record/methods/tlsany_meth.c:77:
```

### Configuração do Usuário
```
User: bruno.amv@gmail.com
Host: smtp.gmail.com
Port: 587
SSL/TLS: ON
```

---

## ❌ PROBLEMA IDENTIFICADO

### Causa Raiz
**Incompatibilidade entre protocolo e porta**:

1. **Porta 587** = STARTTLS (RFC 3207)
   - Começa conexão **plain text**
   - Depois **upgrade para TLS** via comando STARTTLS

2. **SSL/TLS Toggle ON** no n8n
   - n8n tenta conexão **SSL direta** (handshake SSL imediato)
   - Servidor Gmail **rejeita** porque espera plain text primeiro

3. **Resultado**: `wrong version number` - cliente e servidor falam protocolos diferentes

---

## 📊 Matriz de Configurações Gmail SMTP

### Opção 1: Porta 587 (STARTTLS) - RECOMENDADO
```
Host: smtp.gmail.com
Port: 587
Encryption: STARTTLS (upgrade plain connection)
SSL/TLS Toggle: ??? (CONFUSÃO NA DOCUMENTAÇÃO)
Authentication: OAuth2 ou App Password
```

**Problema**: Documentação n8n contraditória:
- Docs oficiais n8n: "Port 587 → SSL/TLS Toggle **ON**"
- RFC 3207 (STARTTLS): "Port 587 → Começar **plain**, depois upgrade"

### Opção 2: Porta 465 (SSL/TLS) - ALTERNATIVA
```
Host: smtp.gmail.com
Port: 465
Encryption: SSL/TLS direto (desde o início)
SSL/TLS Toggle: ON
Authentication: OAuth2 ou App Password
```

**Vantagem**: Sem ambiguidade - SSL direto

---

## 🔬 Investigação Técnica

### n8n 2.14.2 EmailSend Node (v2.1)

**Código fonte** (`send.operation.ts:276`):
```typescript
// Onde o erro acontece
const transport = nodemailer.createTransport({
    host: credentials.host,
    port: credentials.port,
    secure: credentials.secure,  // ← SSL/TLS Toggle
    auth: { ... }
});
```

**Comportamento**:
- `secure: true` → SSL direto (porta 465)
- `secure: false` → Plain text, depois STARTTLS se disponível (porta 587)

### Gmail SMTP Requirements (2024+)

**Desde Set/2024**:
- ❌ **Password básico**: Não funciona mais
- ✅ **OAuth2**: Recomendado para aplicações
- ✅ **App Password**: Para 2FA habilitado

**Portas suportadas**:
- **587** (STARTTLS): Padrão moderno
- **465** (SSL/TLS): Legacy mas suportado
- ~~**25**~~ (Plain): Bloqueado pelo Gmail

---

## 🧪 Testes Realizados

### Teste 1: Port 587 + SSL/TLS ON
```
❌ FALHOU
Erro: wrong version number
Razão: n8n tentou SSL direto, Gmail esperava plain text
```

### Teste 2: Workflow V10 (connectionSecurity: STARTTLS)
```
❌ FALHOU
Erro: Mesmo erro SSL
Razão: Parâmetro ignorado se credencial tem SSL/TLS toggle ON
```

### Conclusão
**Parâmetro `connectionSecurity` no workflow NÃO sobrescreve credencial SMTP**

---

## ✅ SOLUÇÕES POSSÍVEIS

### Solução 1: Usar Porta 465 (SSL Direto) ⭐ RECOMENDADO
```yaml
Credencial SMTP:
  Host: smtp.gmail.com
  Port: 465
  SSL/TLS: ON
  User: bruno.amv@gmail.com
  Password: [App Password de 16 dígitos]

Workflow:
  Sem mudanças necessárias
```

**Vantagens**:
- ✅ Zero ambiguidade
- ✅ SSL desde o início
- ✅ Suportado oficialmente pelo Gmail
- ✅ Compatível com n8n 2.14.2

**Desvantagens**:
- ⚠️ Porta "legacy" (mas Gmail suporta indefinidamente)

---

### Solução 2: Usar Porta 587 + SSL/TLS OFF
```yaml
Credencial SMTP:
  Host: smtp.gmail.com
  Port: 587
  SSL/TLS: OFF  ← CRÍTICO
  User: bruno.amv@gmail.com
  Password: [App Password de 16 dígitos]

Workflow:
  Sem mudanças necessárias
```

**Vantagens**:
- ✅ Porta moderna (587 é recomendada)
- ✅ STARTTLS automático (nodemailer detecta)

**Desvantagens**:
- ⚠️ Contra-intuitivo (SSL/TLS OFF para conexão segura)
- ⚠️ Depende de nodemailer fazer upgrade STARTTLS corretamente

---

### Solução 3: Migrar para Serviço de Email (Long-term)
```yaml
Alternativas:
  - SendGrid (API REST, sem SMTP)
  - AWS SES (API + SMTP)
  - Mailgun (API + SMTP)
  - Resend (API moderna)
```

**Vantagens**:
- ✅ Sem problemas SMTP complexos
- ✅ Melhor deliverability
- ✅ Analytics detalhado
- ✅ Rate limits maiores

**Desvantagens**:
- ⚠️ Custo adicional
- ⚠️ Requer mudança de arquitetura

---

## 🚀 AÇÃO RECOMENDADA IMEDIATA

### Passo 1: Testar Porta 465
```bash
# 1. Acessar n8n UI
http://localhost:5678

# 2. Ir em Settings → Credentials → SMTP account

# 3. Editar credencial:
Host: smtp.gmail.com
Port: 465  ← MUDAR DE 587 PARA 465
SSL/TLS: ON (manter)
User: bruno.amv@gmail.com
Password: [Mesmo App Password]

# 4. Save

# 5. Testar workflow WF07 V10 novamente
```

### Passo 2: Validar App Password
```bash
# Verificar se App Password é válido (16 dígitos sem espaços)

# Gerar novo se necessário:
https://myaccount.google.com/apppasswords

# Requirements:
- 2FA habilitado na conta Google
- App password específico para "Mail" ou "Other"
- 16 caracteres (remover espaços se copiou com)
```

### Passo 3: Teste de Conexão Manual
```bash
# Testar SMTP diretamente via telnet/openssl

# Porta 465 (SSL direto):
openssl s_client -connect smtp.gmail.com:465 -crlf

# Porta 587 (STARTTLS):
telnet smtp.gmail.com 587
# Depois: EHLO localhost
# Depois: STARTTLS
```

---

## 📚 Documentação Oficial

### Google SMTP Settings
- **Oficial**: https://support.google.com/mail/answer/7126229
- **Developer**: https://developers.google.com/workspace/gmail/imap/imap-smtp

### n8n SMTP Configuration
- **Send Email**: https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.emailsend/
- **Credentials**: https://docs.n8n.io/integrations/builtin/credentials/sendemail/

### RFCs Relevantes
- **STARTTLS**: RFC 3207
- **SMTP**: RFC 5321
- **SMTP AUTH**: RFC 4954

---

## 🔧 Troubleshooting Checklist

- [ ] App Password válido (16 dígitos, sem espaços)
- [ ] 2FA habilitado na conta Google
- [ ] Porta correta (465 com SSL ON ou 587 com SSL OFF)
- [ ] Host correto: smtp.gmail.com
- [ ] Username: email completo (bruno.amv@gmail.com)
- [ ] Credencial salva no n8n
- [ ] Workflow usando credencial correta
- [ ] Firewall permitindo porta de saída
- [ ] Docker network permitindo conexões externas

---

## ⚠️ Avisos Importantes

### Gmail Rate Limits
- **Sending limit**: 500 emails/dia (conta gratuita)
- **Recipients/message**: 100 destinatários máximo
- **API/SMTP**: Mesmo limite compartilhado

### Segurança
- ✅ **SEMPRE** usar App Password (nunca senha principal)
- ✅ **SEMPRE** usar SSL/TLS (porta 465) ou STARTTLS (porta 587)
- ❌ **NUNCA** usar porta 25 plain text
- ❌ **NUNCA** commitar credenciais no código

### n8n 2.14.2 Limitações
- Node `emailSend` v2.1 não expõe opção explícita STARTTLS
- Parâmetro `connectionSecurity` em workflow **ignorado** se credencial define SSL
- Comportamento SSL/TLS controlado **apenas** pela credencial

---

## 📊 Comparação Final

| Config | Porta | SSL Toggle | STARTTLS | Gmail Suporta | n8n Funciona | Recomendado |
|--------|-------|------------|----------|---------------|--------------|-------------|
| A | 587 | ON | ❌ | ❌ | ❌ | ❌ |
| B | 587 | OFF | ✅ | ✅ | ⚠️ | ⚠️ |
| C | 465 | ON | N/A | ✅ | ✅ | ✅ |
| D | 465 | OFF | ❌ | ❌ | ❌ | ❌ |

**Legenda**:
- ✅ Funciona confiavelmente
- ⚠️ Pode funcionar (depende de nodemailer)
- ❌ Não funciona

---

## 🎯 Conclusão

**RESPOSTA DIRETA**:
- ✅ **SIM**, n8n 2.14.2 **PODE** enviar email com Gmail
- ⚠️ **MAS** requer configuração **EXATA**: **Porta 465 + SSL/TLS ON**
- ❌ **Porta 587 + SSL/TLS ON** = **NÃO FUNCIONA** (seu erro atual)

**PRÓXIMO PASSO**:
1. Editar credencial SMTP: Mudar porta **587 → 465**
2. Manter SSL/TLS **ON**
3. Testar novamente

**Se falhar ainda**:
- Verificar App Password (gerar novo)
- Testar conexão manual (openssl s_client)
- Considerar alternativa (SendGrid, AWS SES)

---

**Gerado**: 2026-04-01 por Claude Code
**Status**: ✅ ANÁLISE COMPLETA - SOLUÇÃO IDENTIFICADA
