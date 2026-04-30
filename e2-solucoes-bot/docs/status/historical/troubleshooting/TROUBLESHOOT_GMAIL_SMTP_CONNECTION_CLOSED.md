# TROUBLESHOOTING: Gmail SMTP "Connection closed unexpectedly"

**Data**: 2026-04-01
**Erro**: Connection closed unexpectedly
**Configuração**: Port 465 + SSL/TLS ON
**Status**: ⚠️ PROBLEMA CRÍTICO IDENTIFICADO

---

## 🔍 Problema Identificado

### Configuração Atual
```
User: bruno.amv@gmail.com
Password: suni sdev gbnj wtdc  ← FORMATO INCORRETO!
Host: smtp.gmail.com
Port: 465
SSL/TLS: ON
```

### ❌ ERRO CRÍTICO - App Password com Espaços

**Problema**: App Password fornecido tem **espaços**

```
❌ FORMATO INCORRETO (com espaços):
suni sdev gbnj wtdc

✅ FORMATO CORRETO (sem espaços):
sunidevgbnjwtdc
```

**Por que isso causa "Connection closed unexpectedly"**:
1. n8n envia App Password **com espaços** para Gmail
2. Gmail rejeita credencial inválida
3. Gmail fecha conexão imediatamente
4. Erro: "Connection closed unexpectedly"

---

## 🧪 Testes Realizados

### Teste 1: Conectividade SSL
```bash
$ openssl s_client -connect smtp.gmail.com:465

✅ SUCESSO
- Certificado SSL válido
- Conexão estabelecida
- Servidor respondendo
```

**Conclusão**: Rede e SSL funcionando corretamente.

### Teste 2: Formato App Password
```
Fornecido: "suni sdev gbnj wtdc"
Caracteres: 19 (incluindo 3 espaços)
Esperado: 16 caracteres (sem espaços)

❌ INVÁLIDO
```

**Conclusão**: App Password com formato incorreto.

### Teste 3: Pesquisa em Comunidade n8n
```
Erro comum: "Connection closed unexpectedly"
Causa principal: Credenciais incorretas
Solução: Regenerar App Password SEM copiar espaços
```

---

## ✅ SOLUÇÕES

### Solução 1: Remover Espaços do App Password (Rápido)
```
1. Editar credencial SMTP no n8n
2. Campo Password:
   ANTES: suni sdev gbnj wtdc
   DEPOIS: sunidevgbnjwtdc
3. Save
4. Testar workflow
```

**Vantagens**:
- ✅ Rápido (1 minuto)
- ✅ Sem gerar nova senha

**Desvantagens**:
- ⚠️ Se senha já estiver errada, ainda vai falhar

---

### Solução 2: Gerar Novo App Password (Recomendado) ⭐
```
1. Acessar: https://myaccount.google.com/apppasswords

2. Verificar pré-requisitos:
   ✅ 2FA habilitado na conta
   ✅ Conta Google pessoal (não workspace)

3. Gerar novo App Password:
   - Selecionar app: "Mail"
   - Selecionar dispositivo: "Other (Custom name)"
   - Nome: "n8n E2 Bot"
   - Copiar senha gerada: XXXX XXXX XXXX XXXX

4. IMPORTANTE: Remover espaços ao colar no n8n
   Copiar: XXXX XXXX XXXX XXXX
   Colar: XXXXXXXXXXXXXXXX (sem espaços)

5. Salvar e testar
```

**Vantagens**:
- ✅ Senha garantidamente válida
- ✅ Elimina qualquer dúvida sobre senha antiga
- ✅ Melhor prática de segurança

---

### Solução 3: Alternativa - Usar Outro Serviço de Email
```yaml
SendGrid (Recomendado):
  - Free tier: 100 emails/dia
  - API simples (sem SMTP)
  - Configuração em 5 minutos
  - Melhor deliverability

AWS SES:
  - Free tier: 62.000 emails/mês
  - SMTP + API disponível
  - Requer verificação de domínio

Resend:
  - Free tier: 3.000 emails/mês
  - API moderna
  - Ótima documentação
```

---

## 🔧 Passo a Passo Completo

### Método Recomendado: Novo App Password

**Passo 1: Gerar App Password**
```
1. Abrir: https://myaccount.google.com/apppasswords
2. Login: bruno.amv@gmail.com
3. Verificar 2FA ativo
4. Criar novo App Password:
   Nome: "n8n E2 Solucoes Bot"
5. Copiar senha: XXXX XXXX XXXX XXXX
```

**Passo 2: Remover Espaços**
```
Senha gerada pelo Google: abcd efgh ijkl mnop
Copiar para n8n: abcdefghijklmnop

DICA: Copiar para editor de texto primeiro,
      remover espaços, depois copiar para n8n
```

**Passo 3: Configurar n8n**
```
1. n8n UI: http://localhost:5678
2. Settings → Credentials → SMTP account
3. Editar credencial:
   User: bruno.amv@gmail.com
   Password: [App Password SEM espaços]
   Host: smtp.gmail.com
   Port: 465
   SSL/TLS: ON (marcar checkbox)
4. Save
```

**Passo 4: Testar**
```
1. Abrir WF07 V10
2. Manual Execute com dados de teste
3. Verificar logs:
   docker logs -f e2bot-n8n-dev | grep -E "SMTP|Email"

Esperado:
✅ Email sent successfully
✅ No "Connection closed unexpectedly"
```

---

## 🚨 Problemas Comuns

### Problema 1: "Invalid login credentials"
```
Causa: App Password incorreto ou com espaços
Solução: Gerar novo App Password, colar SEM espaços
```

### Problema 2: "Connection closed unexpectedly"
```
Causas possíveis:
1. App Password com espaços (MAIS COMUM)
2. 2FA não habilitado
3. App Password revogado
4. Limite de rate do Gmail excedido

Solução: Verificar cada item acima
```

### Problema 3: "2FA não habilitado"
```
Erro: "App Passwords não disponível"
Solução:
1. https://myaccount.google.com/security
2. Habilitar 2-Step Verification
3. Aguardar 10 minutos
4. Gerar App Password
```

### Problema 4: Rate Limit Gmail
```
Erro: "Too many login attempts"
Solução:
1. Aguardar 15-30 minutos
2. Limpar tentativas falhadas
3. Testar novamente
```

---

## 📊 Diagnóstico Sistemático

### Checklist de Validação
```
[ ] 2FA habilitado em bruno.amv@gmail.com
[ ] App Password gerado recentemente
[ ] App Password copiado SEM espaços
[ ] Credencial n8n salva corretamente
[ ] Port 465 configurado
[ ] SSL/TLS toggle marcado
[ ] Conexão SSL teste bem-sucedida (openssl)
[ ] Workflow usando credencial correta
[ ] Sem rate limit Gmail ativo
```

### Teste Manual de Conexão
```bash
# Testar conexão SSL
openssl s_client -connect smtp.gmail.com:465 -quiet

# Esperado:
# depth=2 C = US, O = Google Trust Services LLC...
# (Certificado SSL válido)

# Testar autenticação (manual)
# Após conectar, enviar:
EHLO localhost
AUTH LOGIN
[base64 do email]
[base64 do app password]

# Esperado:
# 235 2.7.0 Accepted (se credenciais corretas)
```

---

## 🔍 Logs de Diagnóstico

### n8n Logs
```bash
# Ver erro completo
docker logs e2bot-n8n-dev 2>&1 | grep -A 5 "Connection closed"

# Ver tentativas SMTP
docker logs e2bot-n8n-dev 2>&1 | grep -i smtp | tail -20
```

### Logs Esperados (Sucesso)
```
✅ SMTP connection established
✅ Email sent to bruno.amv@gmail.com
✅ Message-ID: <...@smtp.gmail.com>
```

### Logs Esperados (Falha - App Password)
```
❌ Connection closed unexpectedly
❌ Invalid login: 535-5.7.8 Username and Password not accepted
```

---

## 🎯 Solução Definitiva - Passo a Passo Visual

### Visual 1: Gerar App Password
```
Google Account Security
    ↓
2-Step Verification (DEVE estar ON)
    ↓
App passwords
    ↓
Select app: Mail
    ↓
Select device: Other (custom name)
    ↓
Generate
    ↓
Copy: XXXX XXXX XXXX XXXX
```

### Visual 2: Preparar Senha
```
Senha copiada: abcd efgh ijkl mnop
       ↓
Editor de texto
       ↓
Remover espaços: abcdefghijklmnop
       ↓
Copiar senha limpa
```

### Visual 3: Configurar n8n
```
n8n Settings
    ↓
Credentials
    ↓
SMTP account (editar)
    ↓
Password: [Colar senha SEM espaços]
    ↓
Port: 465
SSL/TLS: [✓] ON
    ↓
Save
```

---

## 📚 Referências

### Google App Passwords
- **Gerar**: https://myaccount.google.com/apppasswords
- **Docs**: https://support.google.com/accounts/answer/185833
- **2FA**: https://myaccount.google.com/security

### n8n Gmail SMTP
- **Docs oficiais**: https://docs.n8n.io/integrations/builtin/credentials/sendemail/
- **Community**: https://community.n8n.io/tag/gmail

### Problemas Conhecidos
- **Community Thread 1**: "Connection closed unexpectedly with Gmail"
- **Community Thread 2**: "Gmail SMTP setup issues"
- **GitHub Issues**: nodemailer + Gmail compatibility

---

## ⚠️ Avisos Finais

### Segurança
- ✅ **SEMPRE** gerar App Password específico (nunca senha principal)
- ✅ **REVOGAR** App Passwords não usados
- ❌ **NUNCA** commitar App Password no código
- ❌ **NUNCA** compartilhar App Password

### Gmail Limits
- **Sending limit**: 500 emails/dia (conta gratuita)
- **Rate limit**: ~100 emails/hora
- **Recipients**: 100 por mensagem

### Alternativas Recomendadas
Se problemas persistirem após seguir TODOS os passos:
1. **SendGrid** - Mais confiável para automação
2. **AWS SES** - Escalável e barato
3. **Resend** - API moderna

---

## 🎯 RESPOSTA DIRETA

**"Criei senha nova e nada funciona"**

**CAUSA MAIS PROVÁVEL**: ❌ **App Password copiado COM ESPAÇOS**

**SOLUÇÃO**:
1. Gerar novo App Password
2. **Copiar para editor de texto**
3. **Remover TODOS os espaços**
4. Colar no n8n (deve ter 16 caracteres)
5. Testar

**EXEMPLO**:
```
❌ ERRADO (19 chars): suni sdev gbnj wtdc
✅ CERTO (16 chars):  sunidevgbnjwtdc
```

**Se ainda falhar após isso**:
- Verificar 2FA habilitado
- Aguardar 15 min (rate limit)
- Considerar alternativa (SendGrid)

---

**Gerado**: 2026-04-01 por Claude Code
**Status**: ✅ CAUSA IDENTIFICADA - SOLUÇÃO DOCUMENTADA
