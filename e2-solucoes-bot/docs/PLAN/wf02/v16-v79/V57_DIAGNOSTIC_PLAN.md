# V57 Diagnostic Plan - Runtime Error Investigation

**Data**: 2026-03-09
**Autor**: Claude Code V57 Diagnostic Analysis
**Erro**: http://localhost:5678/workflow/v5aN1f3jQ1Fu50qk/executions/10080

---

## ✅ Confirmação Estrutural

### V57 Workflow ESTÁ COMPLETO

Análise do arquivo `02_ai_agent_conversation_V57_MERGE_APPEND.json`:

**Total de Nós**: 27 nós (23 de V54 + 4 novos V57)

**Todos os Nós de Banco Presentes** ✅:
1. Get Conversation Count (PostgreSQL v1) - linha 59
2. Get Conversation Details (PostgreSQL v1) - linha 80
3. Create New Conversation (PostgreSQL v2) - linha 122
4. Update Conversation State (PostgreSQL v2.5) - linha 157
5. Save Inbound Message (PostgreSQL v2.5) - linha 178
6. Save Outbound Message (PostgreSQL v2.5) - linha 199
7. Upsert Lead Data (PostgreSQL v2.5) - linha 329

**Credenciais PostgreSQL em TODOS** ✅:
```json
"credentials": {
  "postgres": {
    "id": "VXA1r8sd0TMIdPvS",
    "name": "PostgreSQL - E2 Bot"
  }
}
```

**Nós de Preparação de Dados** ✅:
- Validate Input Data (linha 15)
- Prepare Phone Formats (linha 28)
- Build SQL Queries (linha 366)
- Build Update Queries (linha 408)

**Nós V57 Merge Append** ✅:
- Merge Append New User V57 (linha 422) - mode: "append"
- Process New User Data V57 (linha 436) - Code processor
- Merge Append Existing User V57 (linha 451) - mode: "append"
- Process Existing User Data V57 (linha 467) - Code processor

**Conexões Completas** ✅:
- Path 1 (New User): Merge Queries Data → Create New Conversation → Merge Append → Process → State Machine
- Path 2 (Existing User): Merge Queries Data1 → Get Conversation Details → Merge Append → Process → State Machine
- Após State Machine: Build Update Queries → 5 operações paralelas de banco

---

## 🚨 Problema Real: Erro de Runtime

**Conclusão**: V57 NÃO está faltando configurações de banco. O problema é de **execução em runtime**.

### Possíveis Causas

#### 1. Credenciais PostgreSQL Não Existem
**Problema**: O ID de credencial pode não existir na instância n8n do usuário
```
Credential ID: VXA1r8sd0TMIdPvS
Nome: PostgreSQL - E2 Bot
```

**Como Verificar**:
```bash
# No n8n, ir para Settings → Credentials
# Verificar se existe "PostgreSQL - E2 Bot"
# Se não existir, criar credenciais com:
#   Host: e2bot-postgres-dev
#   Database: e2bot_dev
#   User: postgres
#   Password: (da .env.dev)
#   Port: 5432
```

#### 2. Problema com Merge Append Mode
**Problema**: O modo `append` pode ter comportamento inesperado em runtime

**Sintoma Esperado**:
- V57 Code Processor recebe array de items
- Verifica se tem exatamente 2 items
- Se não tiver 2 items → erro "Expected 2 items from append, received X"

**Como Verificar**:
1. Acessar execução 10080: http://localhost:5678/workflow/v5aN1f3jQ1Fu50qk/executions/10080
2. Verificar logs do nó "Process New User Data V57" ou "Process Existing User Data V57"
3. Procurar por mensagens:
   - "V57: Received X items from Merge append"
   - "V57 ERROR: Expected 2 items from append, received X"
   - "V57 CRITICAL ERROR: conversation_id is NULL!"

#### 3. Estrutura de Dados de Entrada
**Problema**: Dados podem não estar chegando no formato esperado

**Verificar**:
1. No nó "Merge Queries Data" ou "Merge Queries Data1"
2. Ver output real dos dados
3. Comparar com o que V57 Code Processor espera receber

**Formato Esperado pelo Code Processor**:
```javascript
items[0].json = {
  phone_number: "556299887766",
  message: "Olá",
  query_count: "SELECT...",
  query_details: "SELECT...",
  // ... outros campos de queries
}

items[1].json = {
  id: 123,  // ← CRITICAL: conversation_id
  phone_number: "556299887766",
  state_machine_state: "greeting",
  created_at: "2026-03-09...",
  // ... outros campos do banco
}
```

#### 4. Problema de Importação no n8n
**Problema**: Workflow pode não ter importado todos os nós corretamente

**Como Verificar**:
1. Abrir workflow V57 no n8n
2. Contar nós manualmente: deve ter 27 nós
3. Verificar se todos os nós PostgreSQL têm credenciais configuradas
4. Verificar se há erros de validação nos nós (ícone vermelho)

---

## 📊 Checklist de Diagnóstico

Execute estes passos em ordem:

### Passo 1: Verificar Credenciais PostgreSQL
```bash
# No n8n:
1. Settings → Credentials
2. Procurar "PostgreSQL - E2 Bot"
3. Se não existir → CRIAR credencial nova
4. Se existir → verificar se connection test passa
```

**Resultado**: [ ] Credenciais OK / [ ] Credenciais faltando

---

### Passo 2: Verificar Importação do Workflow
```bash
# No n8n:
1. Abrir workflow V57
2. Contar nós: deve ter 27 nós
3. Verificar nós com erro (ícone vermelho)
4. Verificar se "Merge Append New User V57" existe
5. Verificar se "Process New User Data V57" existe
```

**Resultado**: [ ] 27 nós presentes / [ ] Nós faltando: ___________

---

### Passo 3: Analisar Logs da Execução 10080
```bash
# No n8n:
1. Abrir: http://localhost:5678/workflow/v5aN1f3jQ1Fu50qk/executions/10080
2. Clicar em cada nó para ver output
3. Identificar qual nó falhou
4. Copiar mensagem de erro completa
```

**Nó que falhou**: ___________
**Mensagem de erro**: ___________

---

### Passo 4: Verificar Logs do Container n8n
```bash
docker logs e2bot-n8n-dev 2>&1 | grep -A 20 "V57"
```

**Procurar por**:
- "V57 CODE PROCESSOR START"
- "V57: Received X items from Merge append"
- "V57 ERROR:"
- "V57 CRITICAL ERROR:"

---

### Passo 5: Teste Simples
```bash
# Desativar V54, V55, V56
# Ativar apenas V57
# Enviar mensagem simples no WhatsApp: "oi"
# Verificar execução em tempo real
```

---

## 🔧 Soluções Possíveis

### Se Credenciais Faltam
```bash
# Criar nova credencial no n8n:
Nome: PostgreSQL - E2 Bot
Host: e2bot-postgres-dev
Database: e2bot_dev
User: postgres
Password: (verificar em .env.dev)
Port: 5432
SSL: Disable

# Após criar, RE-IMPORTAR workflow V57
# (Para que n8n reconheça as credenciais)
```

### Se Merge Append Recebe Apenas 1 Item
**Problema**: Mesmo erro que V55 - Merge não está recebendo 2 inputs

**Solução**: Verificar conexões no n8n visual:
```
Path 1 (New User):
Merge Queries Data ──→ Merge Append New User V57 (input 0)
Create New Conversation ──→ Merge Append New User V57 (input 1)

Path 2 (Existing User):
Merge Queries Data1 ──→ Merge Append Existing User V57 (input 0)
Get Conversation Details ──→ Merge Append Existing User V57 (input 1)
```

Se alguma conexão não existir → RECONECTAR manualmente no n8n

### Se conversation_id é NULL
**Problema**: Database não está retornando ID

**Solução**: Verificar se queries PostgreSQL têm `RETURNING *`:
```sql
-- Em Create New Conversation e Get Conversation Details
-- Deve terminar com:
RETURNING *
```

---

## 📋 Próximas Ações

**Baseado no diagnóstico, criar plano específico**:

1. **Se Credenciais**: Criar V57.1 com credenciais atualizadas
2. **Se Conexões**: Criar guia de reconexão manual
3. **Se Merge Append**: Considerar V58 com abordagem diferente
4. **Se Outra Causa**: Investigar mais profundamente

---

## 🎯 Informações Necessárias do Usuário

Para continuar diagnóstico, precisamos:

1. ✅ **Logs da Execução 10080**:
   - Screenshot ou texto completo do erro
   - Output de cada nó (especialmente os V57)
   - Mensagem de erro específica

2. ✅ **Status das Credenciais**:
   - Existe "PostgreSQL - E2 Bot" nas credenciais?
   - Connection test passa?

3. ✅ **Contagem de Nós no n8n**:
   - Quantos nós aparecem no workflow V57 importado?
   - Todos têm ícone verde (sem erros)?

4. ✅ **Logs do Container**:
   ```bash
   docker logs e2bot-n8n-dev 2>&1 | tail -100
   ```

---

**Conclusão**: V57 está estruturalmente perfeito. O erro é de runtime, não de configuração ausente. Precisamos dos logs de execução para identificar a causa exata.
