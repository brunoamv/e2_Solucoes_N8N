# V44 - n8n Credentials Database Name Fix

**Data**: 2025-03-06
**Severidade**: 🔴 CRÍTICA
**Status**: Plano pronto para execução
**Approach**: Update n8n PostgreSQL credentials

---

## 🚨 PROBLEMA IDENTIFICADO

### Erro Atual
```
database "e2_bot" does not exist
Failed query: INSERT INTO messages (conversation_id, ...)
```

### Root Cause Analysis
**Credenciais n8n DESATUALIZADAS**:
```
Current (WRONG):
  Host: postgres-dev
  Database: e2_bot        ← PROBLEMA: Este banco não existe mais
  User: postgres
  Password: CoraRosa

Expected (CORRECT):
  Host: postgres-dev
  Database: e2bot_dev     ← CORRETO: Banco criado pelo V43
  User: postgres
  Password: CoraRosa
```

### Timeline do Problema
1. **V43**: Recriamos database como `e2bot_dev` (correto)
2. **n8n**: Credenciais antigas apontam para `e2_bot` (errado)
3. **Result**: Workflow V41 tenta inserir em banco inexistente
4. **Error**: `database "e2_bot" does not exist`

### Impact
- ✅ WhatsApp funciona (Evolution API OK)
- ✅ n8n workflow 01 funciona (recebe mensagens)
- ❌ n8n workflow 02 (V41) FALHA ao acessar database
- ❌ Mensagens não são salvas
- ❌ Conversas não são criadas

---

## ✅ SOLUÇÃO V44

### Estratégia
**NÃO** modificar banco de dados
**SIM** atualizar credenciais do n8n para apontar ao banco correto

### Mudança Necessária
```yaml
Credential ID: VXA1r8sd0TMIdPvS
URL: http://localhost:5678/projects/08qzhIsou3TK6J3Z/credentials/VXA1r8sd0TMIdPvS

Change:
  Database: e2_bot → e2bot_dev

Keep unchanged:
  Host: postgres-dev
  User: postgres
  Password: CoraRosa
```

---

## 🎯 PLANO DE EXECUÇÃO

### Fase 1: Identificar Uso da Credencial

**Objetivo**: Descobrir quais workflows usam esta credencial

**Comandos**:
```bash
cd /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot

# Buscar referência à credencial em todos workflows
grep -r "VXA1r8sd0TMIdPvS" n8n/workflows/

# Buscar referência ao banco "e2_bot" em workflows
grep -r '"e2_bot"' n8n/workflows/
```

**Esperado**: Workflows V41, V01, e possivelmente outros

### Fase 2: Atualizar Credencial no n8n (Interface Web)

**Passo a Passo**:

1. **Abrir n8n**:
   ```
   URL: http://localhost:5678
   ```

2. **Navegar para Credenciais**:
   ```
   Menu lateral → Credentials
   OU
   Acessar diretamente: http://localhost:5678/projects/08qzhIsou3TK6J3Z/credentials
   ```

3. **Localizar Credencial PostgreSQL**:
   ```
   Buscar por: VXA1r8sd0TMIdPvS
   OU
   Nome: "PostgreSQL E2 Bot" (ou similar)
   ```

4. **Editar Credencial**:
   ```
   Click em "Edit" ou no nome da credencial
   ```

5. **Alterar Database Name**:
   ```
   ANTES:
   Host: postgres-dev
   Database: e2_bot         ← Mudar isto
   User: postgres
   Password: CoraRosa

   DEPOIS:
   Host: postgres-dev
   Database: e2bot_dev      ← Para isto
   User: postgres
   Password: CoraRosa
   ```

6. **Testar Conexão**:
   ```
   Click em "Test Connection" ou "Test"
   Esperado: ✅ Connection successful
   ```

7. **Salvar**:
   ```
   Click em "Save" ou "Update"
   ```

### Fase 3: Reiniciar Workflows Afetados

**Comandos**:
```bash
# Reiniciar n8n para garantir que pegue credenciais atualizadas
docker-compose -f docker/docker-compose-dev.yml restart n8n-dev

# Aguardar n8n estar pronto (30-60 segundos)
sleep 60
```

**Na Interface n8n**:
1. Desativar workflows que usam a credencial
2. Ativar novamente
3. Testar execução

### Fase 4: Verificação de Funcionamento

**Teste Manual**:
```
1. Enviar mensagem WhatsApp: "oi"
2. Verificar resposta do bot
3. Verificar se não há erro de database
4. Verificar execução em n8n
```

**Verificação Database**:
```bash
# Verificar se mensagem foi salva
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "
  SELECT id, direction, content, created_at
  FROM messages
  ORDER BY created_at DESC
  LIMIT 5;
"

# Esperado: Mensagens recentes aparecendo
```

**Verificação Logs**:
```bash
# Verificar logs n8n (não deve ter erro "e2_bot")
docker logs e2bot-n8n-dev 2>&1 | tail -50 | grep -E "e2_bot|ERROR"

# Esperado: Nenhuma referência a "e2_bot", nenhum erro de database
```

---

## 📊 CRITÉRIOS DE SUCESSO

### ✅ Fix Completo Quando:
1. **Credencial Atualizada**: Database name = `e2bot_dev`
2. **Teste de Conexão**: n8n consegue conectar ao PostgreSQL
3. **Mensagens Salvas**: INSERT em messages funciona sem erro
4. **Conversas Criadas**: Registro em conversations criado
5. **Execuções Success**: Workflow V41 completa com status "success"
6. **Logs Limpos**: Nenhum erro "database e2_bot does not exist"

### ✅ Validações Adicionais:
- Workflow 01 (WhatsApp Handler) continua funcionando
- Workflow 02 (V41 AI Agent) executa sem erros de database
- Dados persistem corretamente em e2bot_dev
- Nenhuma referência ao banco antigo "e2_bot" nos logs

---

## 🔧 ALTERNATIVA: Atualização via SQL (Se Interface não funcionar)

**Se a interface web do n8n não permitir edição**:

### Option A: Atualizar Diretamente no Banco do n8n

```bash
# Conectar ao banco de dados do n8n
docker exec -it e2bot-n8n-dev sh

# Dentro do container n8n, acessar SQLite (ou PostgreSQL se configurado)
# Localizar e atualizar credencial
# CUIDADO: Isto requer conhecer estrutura interna do n8n
```

### Option B: Deletar e Recriar Credencial

**Na interface n8n**:
1. Anotar todos os workflows que usam a credencial
2. Deletar credencial antiga
3. Criar nova credencial com database correto
4. Atualizar workflows para usar nova credencial

**Preferência**: Usar Fase 2 (edição via interface) - mais seguro

---

## 📝 WORKFLOWS AFETADOS (Estimativa)

Baseado na estrutura do projeto, estes workflows provavelmente usam a credencial:

1. **01 - Main WhatsApp Handler**: Salva mensagens inbound
2. **02 - AI Agent Conversation V41**: Queries e updates em conversations
3. **Outros workflows de database**: Qualquer workflow que acesse PostgreSQL

**Ação Requerida**: Após atualizar credencial, todos esses workflows funcionarão automaticamente

---

## 🚨 PRECAUÇÕES

### Antes de Executar
- ✅ Confirmar que database `e2bot_dev` existe
- ✅ Confirmar que database `e2bot_dev` tem todas as tabelas
- ✅ Confirmar que credenciais postgres estão corretas

### Durante Execução
- ⚠️ **NÃO** deletar credencial antes de criar nova (se usar Option B)
- ⚠️ **NÃO** modificar Host, User ou Password (apenas Database)
- ⚠️ **SEMPRE** testar conexão antes de salvar

### Após Execução
- ✅ Verificar que workflows funcionam
- ✅ Verificar que mensagens são salvas
- ✅ Verificar que execuções completam com success

---

## 🔄 ROLLBACK PLAN

**Se V44 causar problemas**:

```bash
# Option 1: Reverter credencial
# Na interface n8n, voltar Database para "e2_bot"
# (mas isto não funcionará pois banco não existe)

# Option 2: Recriar banco antigo
docker exec e2bot-postgres-dev psql -U postgres -c "
  CREATE DATABASE e2_bot;
"
# Aplicar schema antigo
# (NÃO RECOMENDADO - V43 é a solução correta)

# Option 3: Restaurar estado anterior completo
# Usar backup de antes do V43
# (NÃO RECOMENDADO - V43 resolveu problemas)
```

**Recomendação**: V44 é seguro. Apenas atualiza nome do banco nas credenciais.

---

## 📊 RESUMO EXECUTIVO

### Problema
n8n está tentando acessar database `e2_bot` que não existe mais

### Causa
V43 criou database `e2bot_dev`, mas credenciais n8n não foram atualizadas

### Solução
Atualizar credencial do n8n para usar `e2bot_dev`

### Impacto
- **Baixo**: Apenas mudança de configuração
- **Rápido**: 5 minutos para executar
- **Seguro**: Não afeta dados ou código
- **Reversível**: Pode voltar se necessário (mas não deve precisar)

### Benefício
- ✅ Workflows V41 funcionarão
- ✅ Mensagens serão salvas
- ✅ Conversas serão criadas
- ✅ Sistema funcionará end-to-end

---

## 🎯 PRÓXIMOS PASSOS APÓS V44

### Immediate (Após fix)
1. Testar conversa completa no WhatsApp
2. Verificar database persistence
3. Confirmar execuções com "success"

### Seguinte
1. Testar todos os 5 tipos de serviço
2. Testar fluxo completo até agendamento
3. Verificar integração RD Station CRM

---

## 📞 TROUBLESHOOTING

### Se "Test Connection" Falhar

**Erro possível**: `Connection refused`
```bash
# Verificar PostgreSQL está rodando
docker ps | grep postgres

# Verificar network
docker exec e2bot-n8n-dev ping -c 1 postgres-dev
```

**Erro possível**: `database "e2bot_dev" does not exist`
```bash
# Verificar database existe
docker exec e2bot-postgres-dev psql -U postgres -l | grep e2bot_dev

# Se não existir, reexecutar V43
./scripts/recreate-postgres-v43.sh
```

### Se Workflow Ainda Falhar Após Fix

```bash
# Verificar logs n8n
docker logs e2bot-n8n-dev 2>&1 | tail -100

# Verificar que credencial foi atualizada
# Na interface n8n, abrir credencial e confirmar Database = e2bot_dev

# Reiniciar n8n
docker-compose -f docker/docker-compose-dev.yml restart n8n-dev
```

---

**Autor**: Claude Code Analysis
**Data**: 2025-03-06
**Versão**: V44 Plan
**Status**: Ready for Execution
**Estimated Time**: 5-10 minutes
**Risk Level**: LOW (configuration change only)
**Rollback**: Easy (just change back)

---

**EXECUTE QUANDO PRONTO**
**Instrução**: Seguir Fase 1 → Fase 2 → Fase 3 → Fase 4 em sequência
