# 🔧 Guia de Reimportação do Workflow 01 - CORREÇÃO DEFINITIVA

**Problema Identificado**: O workflow antigo no n8n está com configuração em cache que não reflete as correções no arquivo JSON.

**Solução**: Importar workflow com novo nome forçando o n8n a tratá-lo como novo workflow.

---

## 📋 Passo 1: Desativar Workflow Antigo

1. Abra o n8n em seu navegador:
   ```
   http://localhost:5678/workflows
   ```

2. Localize o workflow **"01 - WhatsApp Handler"** (antigo)

3. Clique no workflow para abri-lo

4. No canto superior direito, encontre o toggle **"Active"**

5. **DESATIVE** o workflow (toggle deve ficar vermelho/cinza)

6. Confirme que o workflow está **INACTIVE**

---

## 📋 Passo 2: Importar Workflow Corrigido

1. No n8n, clique em **"+ Add workflow"** (botão superior direito)

2. Clique em **"Import from File"**

3. Selecione o arquivo:
   ```
   /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/01_main_whatsapp_handler.json
   ```

4. O workflow será importado com o nome **"01 - WhatsApp Handler (FIXED v3)"**

5. **NÃO ATIVE** o workflow ainda! Primeiro precisamos configurar as credenciais.

---

## 📋 Passo 3: Configurar Credencial do PostgreSQL

Após importar, o n8n vai mostrar **"1 issue"** (credencial faltando). Vamos configurar:

### 3.1. Abrir Node "Check Duplicate"

1. No canvas do workflow, clique no node **"Check Duplicate"** (retângulo cinza)

2. Vai aparecer um painel lateral à direita

3. No campo **"Credential to connect with"**, clique em **"Create New"**

### 3.2. Configurar Conexão PostgreSQL

Preencha os campos exatamente assim:

```
Name: PostgreSQL - E2 Bot
Host: postgres-dev
Port: 5432
Database: e2_bot
User: postgres
Password: CoraRosa
```

### 3.3. Testar Conexão

1. Clique no botão **"Test connection"** no painel de credenciais

2. Deve aparecer: ✅ **"Connection tested successfully!"**

3. Clique em **"Save"** para salvar a credencial

### 3.4. Aplicar Credencial a Outros Nodes

O n8n vai perguntar: **"Would you like to use this credential in the other nodes too?"**

- Clique em **"Yes, update 1 node"**

Isso vai aplicar a mesma credencial ao node "Save Inbound Message".

---

## 📋 Passo 4: Salvar Workflow

1. No canto superior direito, clique em **"Save"**

2. Confirme que o workflow foi salvo com sucesso (aparece mensagem verde)

---

## 📋 Passo 5: ATIVAR Workflow

**ESTE É O PASSO MAIS IMPORTANTE!**

1. No canto superior direito, localize o toggle **"Inactive"** (deve estar vermelho/cinza)

2. **CLIQUE** no toggle para mudar para **"Active"** (deve ficar verde)

3. Confirme que o toggle agora mostra **"Active"** em verde

4. Deve aparecer uma mensagem: **"Workflow activated successfully!"**

---

## 📋 Passo 6: Verificar Webhook Registrado

Abra o terminal e execute:

```bash
docker logs e2bot-n8n-dev 2>&1 | grep "whatsapp-evolution" | tail -5
```

Você deve ver algo como:
```
Received webhook "POST" for path "whatsapp-evolution"
```

Se aparecer, significa que o webhook está **REGISTRADO** e funcionando!

---

## 📋 Passo 7: Testar com Mensagem Real

1. **Envie uma mensagem de teste** do seu WhatsApp (5561981755748):
   ```
   Teste Final 123
   ```

2. **Monitore os logs** em tempo real:
   ```bash
   docker logs -f --tail 50 e2bot-n8n-dev 2>&1 | grep -E "(Webhook|Start executing|finished)"
   ```

3. **Você deve ver** esta sequência:
   ```
   Received webhook "POST" for path "whatsapp-evolution"
   Workflow execution started
   Start executing node "Webhook WhatsApp"
   Start executing node "Filter Messages"
   Start executing node "Extract Message Data"
   Start executing node "Check Duplicate"
   Start executing node "Is New Message?"
   Start executing node "Save Inbound Message"  ← DEVE PASSAR AQUI!
   Start executing node "Is Image?"
   Start executing node "Trigger AI Agent"
   Workflow execution finished successfully
   ```

4. **IMPORTANTE**: Verifique se passou pelo node **"Save Inbound Message"** (NÃO deve ir para "Response Duplicate")

---

## 📋 Passo 8: Verificar Mensagem Salva no Banco

Execute no terminal:

```bash
docker exec e2bot-postgres-dev psql -U postgres -d e2_bot -c "SELECT id, content, message_type, direction, whatsapp_message_id FROM messages ORDER BY created_at DESC LIMIT 5;"
```

Você deve ver:
```
 id |     content      | message_type | direction |  whatsapp_message_id
----+------------------+--------------+-----------+----------------------
  1 | Teste Final 123  | text         | inbound   | [ID único]
```

Se aparecer a mensagem, significa que o workflow está **FUNCIONANDO CORRETAMENTE**! 🎉

---

## 📋 Passo 9: (Opcional) Deletar Workflow Antigo

Após confirmar que o novo workflow está funcionando:

1. Volte para a lista de workflows: http://localhost:5678/workflows

2. Localize o workflow **"01 - WhatsApp Handler"** (antigo, sem "(FIXED)")

3. Clique nos **3 pontinhos** (...) ao lado do workflow

4. Selecione **"Delete"**

5. Confirme a exclusão

---

## ✅ Checklist de Validação Final

Marque cada item após completar:

- [ ] Workflow antigo desativado
- [ ] Workflow "(FIXED)" importado
- [ ] Credencial PostgreSQL configurada e testada
- [ ] Workflow salvo
- [ ] Workflow **ATIVADO** (toggle verde)
- [ ] Webhook "whatsapp-evolution" registrado nos logs
- [ ] Mensagem de teste enviada pelo WhatsApp
- [ ] Logs mostram execução completa até "Trigger AI Agent"
- [ ] Mensagem salva no banco de dados PostgreSQL
- [ ] Workflow antigo deletado (opcional)

---

## 🚨 Troubleshooting

### Problema: "Workflow não ativa" (toggle não muda)

**Solução**:
```bash
docker restart e2bot-n8n-dev
# Aguarde 30 segundos e tente ativar novamente
```

### Problema: "Credential test failed"

**Solução**: Verifique que o container PostgreSQL está rodando:
```bash
docker ps | grep postgres-dev
# Deve aparecer: e2bot-postgres-dev
```

### Problema: Ainda vai para "Response Duplicate"

**Solução**: Significa que o workflow antigo ainda está ativo! Desative-o:
1. Liste workflows ativos:
   ```bash
   docker logs e2bot-n8n-dev 2>&1 | grep "Workflow activated" | tail -5
   ```
2. Desative o workflow antigo pelo n8n UI

### Problema: "Workflow execution finished successfully" mas não passa pelo "Save Inbound Message"

**Solução**: Verifique os logs detalhados:
```bash
docker logs e2bot-n8n-dev 2>&1 | grep -A 50 "execution ID [ÚLTIMO_ID]"
```

Procure por erros específicos e reporte aqui.

---

## 📞 Suporte

Se encontrar qualquer problema durante a reimportação, envie:

1. **Screenshot do erro** no n8n UI
2. **Logs completos** da última execução:
   ```bash
   docker logs e2bot-n8n-dev 2>&1 | tail -100 > /tmp/n8n_logs.txt
   ```
3. **Status do workflow**:
   ```bash
   curl -s http://localhost:5678/api/v1/workflows 2>/dev/null
   ```

---

**Criado em**: 2025-12-17 19:15
**Problema Original**: n8n usando configuração em cache do workflow antigo
**Solução**: Importar workflow com novo nome "(FIXED)" forçando reimportação limpa
