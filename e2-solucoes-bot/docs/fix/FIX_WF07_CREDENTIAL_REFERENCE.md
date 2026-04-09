# FIX: WF07 Credential Reference Update

**Data**: 2026-04-01
**Problema**: Credential with ID "9ORZxG81Lf8aDbVa" does not exist
**Status**: ✅ CREDENCIAL SMTP FUNCIONANDO - Apenas atualizar workflow

---

## ✅ SITUAÇÃO ATUAL

### Credencial SMTP - FUNCIONANDO
```
✅ Connection tested successfully

Configuração:
User: bruno.amv@gmail.com
Password: [App Password sem espaços - 16 chars]
Host: smtp.gmail.com
Port: 465
SSL/TLS: ON
Client Host Name: Bruno
```

**Status**: ✅ **CREDENCIAL VÁLIDA E TESTADA**

### Workflow WF07 V10 - Referência Antiga
```
❌ Erro: Credential with ID "9ORZxG81Lf8aDbVa" does not exist

Causa: Workflow aponta para credencial antiga/deletada
Solução: Atualizar referência para nova credencial
```

---

## 🔧 SOLUÇÃO - Atualizar Credencial no Workflow

### Método 1: Via UI n8n (Recomendado - 30 segundos) ⭐

**Passo a Passo Visual**:

```
1. Abrir n8n UI:
   http://localhost:5678

2. Ir para workflow WF07 V10:
   Workflows → "07 - Send Email V10 (STARTTLS)"
   OU
   http://localhost:5678/workflow/WGJI8hHcF4Huz7Ya

3. Clicar no node "Send Email (SMTP)"
   (Node laranja com ícone de email)

4. No painel direito, seção "Credentials":
   ┌─────────────────────────────┐
   │ Credentials                 │
   │ ┌─────────────────────────┐ │
   │ │ [Dropdown ▼]            │ │ ← Clicar aqui
   │ └─────────────────────────┘ │
   └─────────────────────────────┘

5. Selecionar nova credencial:
   Options:
   ○ Create New Credential
   ● SMTP - Bruno  ← Selecionar esta (ou nome similar)

   (A que mostra "Connection tested successfully")

6. Salvar workflow:
   Botão "Save" (canto superior direito)

7. Testar:
   Botão "Execute Workflow" → Manual Execute
```

**Indicadores de Sucesso**:
- ✅ Dropdown mostra nome da nova credencial
- ✅ Sem ícone de erro vermelho no node
- ✅ "Save" fica disponível (workflow modificado)

---

### Método 2: Identificar Credencial Correta

**Se houver múltiplas credenciais SMTP**:

1. **Via UI n8n**:
   ```
   Settings → Credentials

   Buscar por tipo: "SMTP"

   Identificar qual tem:
   - Host: smtp.gmail.com
   - Port: 465
   - User: bruno.amv@gmail.com
   - Status: ✅ Connection tested successfully
   ```

2. **Anotar nome da credencial**:
   - Exemplo: "SMTP - Bruno"
   - Exemplo: "Gmail SMTP"
   - Ou qualquer nome que você deu

3. **Usar no workflow** (Método 1 acima)

---

### Método 3: Workflow JSON Manual (Avançado)

**Apenas se Método 1 não funcionar**:

1. **Exportar workflow atual**:
   ```
   n8n UI → Workflow WF07 V10 → Menu (⋮) → Download
   ```

2. **Editar JSON**:
   ```json
   Localizar seção "Send Email (SMTP)":

   {
     "name": "Send Email (SMTP)",
     "type": "n8n-nodes-base.emailSend",
     "credentials": {
       "smtp": {
         "id": "9ORZxG81Lf8aDbVa",  ← ID ANTIGO
         "name": "SMTP account"
       }
     }
   }

   Substituir por (obter ID correto via UI):

   {
     "credentials": {
       "smtp": {
         "id": "[NOVO_ID_AQUI]",
         "name": "SMTP - Bruno"
       }
     }
   }
   ```

3. **Importar workflow atualizado**:
   ```
   n8n UI → Import from File → Selecionar JSON editado
   ```

**⚠️ NÃO RECOMENDADO**: Use Método 1 (muito mais simples)

---

## 🧪 TESTE APÓS ATUALIZAÇÃO

### Dados de Teste
```json
{
  "appointment_id": "test-smtp-fix",
  "lead_email": "bruno.amv@gmail.com",
  "lead_name": "Bruno Teste",
  "phone_number": "556181755748",
  "service_type": "energia_solar",
  "scheduled_date": "2026-04-02",
  "scheduled_time_start": "09:00:00",
  "scheduled_time_end": "11:00:00",
  "city": "Brasília",
  "google_calendar_event_id": "test-event-id",
  "calendar_success": true
}
```

### Executar Teste
```
1. Workflow WF07 V10 aberto
2. Botão "Execute Workflow"
3. Colar dados acima
4. "Execute"
```

### Resultado Esperado
```
✅ Prepare Email Data - Success
✅ Fetch Template (HTTP) - Success
✅ Render Template - Success
✅ Send Email (SMTP) - Success  ← CRÍTICO
✅ Log Email Sent - Success
✅ Return Success - Success

Email recebido em: bruno.amv@gmail.com
Subject: Agendamento Confirmado - E2 Soluções
```

### Logs de Sucesso
```bash
docker logs -f e2bot-n8n-dev | grep -E "Email|SMTP"

Esperado:
✅ SMTP connection established
✅ Email sent to bruno.amv@gmail.com
✅ Message-ID: <...@smtp.gmail.com>
```

---

## 🚨 Se Ainda Falhar

### Erro 1: "Credential does not exist"
```
Causa: Credencial não selecionada corretamente
Solução:
1. Verificar dropdown mostra nome correto
2. Salvar workflow novamente
3. Recarregar página n8n
4. Verificar novamente
```

### Erro 2: "Connection failed" (após atualizar credencial)
```
Causa: App Password ainda com espaços
Solução:
1. Editar credencial SMTP
2. Verificar password tem 16 caracteres exatos
3. Remover espaços se houver
4. Test Connection
5. Save
```

### Erro 3: "Invalid credentials"
```
Causa: App Password incorreto
Solução:
1. Gerar novo App Password no Google
2. Copiar SEM espaços
3. Atualizar credencial n8n
4. Test Connection
5. Salvar
```

---

## 📊 Checklist de Validação

### Antes de Executar Workflow
```
[ ] Credencial SMTP testada com sucesso
[ ] Workflow aberto em n8n UI
[ ] Node "Send Email (SMTP)" selecionado
[ ] Dropdown de credenciais mostra credencial correta
[ ] Workflow salvo após mudança
[ ] Sem ícones de erro vermelho nos nodes
```

### Durante Execução
```
[ ] Todos os nodes executam sem erro
[ ] Node "Send Email (SMTP)" mostra sucesso
[ ] Logs n8n mostram "Email sent"
[ ] Email recebido no Gmail
```

### Validação Final
```
[ ] Email recebido em bruno.amv@gmail.com
[ ] Template HTML renderizado corretamente
[ ] Variáveis substituídas (nome, data, horário)
[ ] Log criado no banco de dados
```

---

## 🎯 SOLUÇÃO PASSO A PASSO COMPLETO

### Passo 1: Abrir Workflow
```
http://localhost:5678/workflow/WGJI8hHcF4Huz7Ya
```

### Passo 2: Atualizar Credencial
```
1. Clicar em "Send Email (SMTP)" node
2. Dropdown "Credentials" → Selecionar "SMTP - Bruno"
3. Save workflow
```

### Passo 3: Testar
```
Execute Workflow → Manual Execute → Usar dados de teste acima
```

### Passo 4: Verificar Email
```
Checar inbox: bruno.amv@gmail.com
Esperado: Email "Agendamento Confirmado - E2 Soluções"
```

### Passo 5: Validar Logs
```bash
docker logs e2bot-n8n-dev | grep -i "email sent" | tail -5
```

---

## 📚 Contexto Técnico

### Por que o ID mudou?
```
Quando você criou nova credencial SMTP com senha correta,
n8n gerou novo ID único para ela.

Workflow antigo ainda referenciava ID da credencial anterior.

Solução: Simplesmente atualizar referência via dropdown.
```

### Estrutura de Credenciais n8n
```json
{
  "id": "9ORZxG81Lf8aDbVa",  ← ID único (antigo)
  "name": "SMTP account",
  "type": "smtp",
  "data": {
    "host": "smtp.gmail.com",
    "port": 465,
    "user": "bruno.amv@gmail.com",
    "password": "[encrypted]"
  }
}

Nova credencial:
{
  "id": "[NOVO_ID_GERADO]",  ← Novo ID
  "name": "SMTP - Bruno",
  "type": "smtp",
  "data": { ... }  ← Mesmos dados, senha correta
}
```

### Workflow Credentials Reference
```json
Workflow JSON referencia credencial por ID:

"credentials": {
  "smtp": {
    "id": "9ORZxG81Lf8aDbVa",  ← Deve ser ID da nova credencial
    "name": "SMTP - Bruno"
  }
}
```

---

## ✅ RESUMO EXECUTIVO

**Situação**:
- ✅ Credencial SMTP configurada corretamente (porta 465, senha sem espaços)
- ✅ Connection test passed
- ❌ Workflow referencia credencial antiga (ID não existe)

**Solução**:
1. Abrir workflow WF07 V10
2. Node "Send Email (SMTP)" → Dropdown credenciais
3. Selecionar nova credencial ("SMTP - Bruno")
4. Save
5. Execute

**Tempo estimado**: 30 segundos

**Resultado esperado**: ✅ Email enviado com sucesso

---

**Gerado**: 2026-04-01 por Claude Code
**Status**: ✅ SOLUÇÃO SIMPLES - APENAS ATUALIZAR DROPDOWN
