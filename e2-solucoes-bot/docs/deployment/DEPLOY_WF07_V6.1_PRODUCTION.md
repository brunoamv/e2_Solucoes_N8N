# Deploy WF07 V6.1 - Instruções Completas

**Versão**: V6.1 (Complete Fix)
**Data**: 2026-03-31
**Workflow**: `07_send_email_v6.1_complete_fix.json`
**Status**: ✅ PRONTO PARA DEPLOY

---

## 📋 Pré-Requisitos

### **1. Verificar Docker Volume Mount**
```bash
# Verificar que volume está montado corretamente
docker exec e2bot-n8n-dev ls -la /email-templates/

# Esperado:
# -rw-r--r-- 1 node node  xxx confirmacao_agendamento.html
# -rw-r--r-- 1 node node  xxx lembrete_2h.html
# -rw-r--r-- 1 node node  xxx novo_lead.html
# -rw-r--r-- 1 node node  xxx apos_visita.html
```

**Se volume NÃO estiver montado:**
```bash
# 1. Adicionar volume ao docker-compose-dev.yml (linha 73):
#    - ../email-templates:/email-templates:ro

# 2. Reiniciar container n8n:
docker-compose -f docker/docker-compose-dev.yml down
docker-compose -f docker/docker-compose-dev.yml up -d

# 3. Verificar novamente
docker exec e2bot-n8n-dev ls /email-templates/
```

---

### **2. Verificar Tabela `email_logs` no PostgreSQL**
```bash
# Verificar que tabela existe e tem colunas corretas
docker exec -it e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "\d email_logs"

# Esperado:
# Column          | Type      | Nullable
# ----------------+-----------+----------
# id              | serial    | not null
# recipient_email | text      | not null
# recipient_name  | text      |
# subject         | text      | not null
# template_used   | text      | not null
# status          | text      | not null
# sent_at         | timestamp | not null
# error_message   | text      |
# metadata        | jsonb     |
```

**Se tabela NÃO existir**, criar com:
```sql
CREATE TABLE IF NOT EXISTS email_logs (
    id SERIAL PRIMARY KEY,
    recipient_email TEXT NOT NULL,
    recipient_name TEXT,
    subject TEXT NOT NULL,
    template_used TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('sent', 'failed', 'pending')),
    sent_at TIMESTAMP NOT NULL DEFAULT NOW(),
    error_message TEXT,
    metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_email_logs_status ON email_logs(status);
CREATE INDEX idx_email_logs_sent_at ON email_logs(sent_at DESC);
CREATE INDEX idx_email_logs_recipient ON email_logs(recipient_email);
```

---

### **3. Verificar Credenciais SMTP**
```bash
# Verificar que credencial SMTP existe no n8n
# 1. Acessar: http://localhost:5678/credentials
# 2. Procurar por: "SMTP - E2 Email" (id: 1)
# 3. Verificar configurações:
#    - Host: smtp.gmail.com (ou outro)
#    - Port: 587 (TLS) ou 465 (SSL)
#    - User: contato@e2solucoes.com.br
#    - Password: [configurado]
```

---

## 🚀 Deploy Passo a Passo

### **Passo 1: Backup do Workflow Atual (se existir)**
```bash
# Se WF07 V6 estiver em produção, fazer backup
# 1. n8n UI → Workflows → "07 - Send Email V6"
# 2. Clicar em "..." → Download
# 3. Salvar como: backup_07_send_email_v6_20260331.json
```

---

### **Passo 2: Importar WF07 V6.1**
```bash
# 1. Acessar n8n
http://localhost:5678

# 2. Clicar em "Workflows" (menu lateral)
# 3. Clicar em "+ Add workflow" → "Import from file"
# 4. Selecionar arquivo:
n8n/workflows/07_send_email_v6.1_complete_fix.json

# 5. Workflow será importado com nome:
"07 - Send Email V6.1 (Complete Fix)"
```

**Resultado esperado:**
- ✅ 8 nós carregados
- ✅ 5 conexões estabelecidas
- ✅ Tags: v6.1, complete-fix, query-fix, template-simplification, wf05-integration

---

### **Passo 3: Desativar Workflow Anterior (V6)**
```bash
# Se WF07 V6 existir e estiver ativo:
# 1. n8n UI → Workflows → "07 - Send Email V6 (Docker Volume Fix)"
# 2. Clicar no toggle "Active" para DESATIVAR
# 3. Confirmar desativação
```

---

### **Passo 4: Ativar WF07 V6.1**
```bash
# 1. n8n UI → Workflows → "07 - Send Email V6.1 (Complete Fix)"
# 2. Clicar no toggle "Active" para ATIVAR
# 3. Aguardar confirmação: "Workflow is now active"
```

---

### **Passo 5: Teste Manual - Template Read**
```bash
# Testar que template é lido corretamente

# 1. n8n UI → WF07 V6.1
# 2. Clicar em "Execute Workflow Trigger" → "Listen for test event"
# 3. Em outra aba, executar:

curl -X POST http://localhost:5678/webhook-test/execute-workflow-07 \
  -H "Content-Type: application/json" \
  -d '{
    "to": "teste@example.com",
    "template": "confirmacao_agendamento",
    "name": "Teste Cliente",
    "service_type": "energia_solar",
    "scheduled_date": "2026-04-15",
    "formatted_date": "15/04/2026",
    "formatted_time": "09:00 às 10:00"
  }'

# 4. Verificar execução no n8n:
#    - Nó "Render Template": deve mostrar html_body e text_body preenchidos
#    - Nó "Send Email (SMTP)": deve ter enviado email
#    - Nó "Log Email Sent": deve ter inserido registro em email_logs
```

**Resultado esperado:**
- ✅ Execução completa sem erros
- ✅ Email recebido em teste@example.com
- ✅ Registro em `email_logs` com status='sent'

---

### **Passo 6: Teste com WF05 V4.0.4 Integration**
```bash
# Testar integração completa WF05 → WF07

# 1. Verificar que WF05 V4.0.4 está ativo
# 2. Verificar que WF07 V6.1 está ativo

# 3. Executar WF05 manualmente:
# n8n UI → WF05 V4.0.4 → Execute → Fornecer dados:

{
  "appointment_id": "550e8400-e29b-41d4-a716-446655440000"
}

# 4. Verificar execução:
#    WF05: Nó "Send Confirmation Email" deve triggerar WF07
#    WF07: Deve receber 16 campos de WF05
#    WF07: Deve enviar email com dados reais do appointment

# 5. Verificar logs PostgreSQL:
docker exec -it e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "
SELECT
  recipient_email,
  recipient_name,
  subject,
  template_used,
  status,
  sent_at
FROM email_logs
ORDER BY sent_at DESC
LIMIT 5;
"
```

**Resultado esperado:**
- ✅ WF05 executa sem erros
- ✅ WF07 triggera com 16 campos
- ✅ Email enviado com dados corretos do appointment
- ✅ Log em `email_logs` com status='sent'

---

### **Passo 7: Validação de Logs SQL**
```bash
# Verificar que queries SQL estão funcionando corretamente

# 1. Teste de sucesso (Log Email Sent):
docker exec -it e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "
SELECT
  id,
  recipient_email,
  recipient_name,
  subject,
  template_used,
  status,
  metadata->'source' as source,
  sent_at
FROM email_logs
WHERE status = 'sent'
ORDER BY sent_at DESC
LIMIT 3;
"

# Esperado:
# - Registros com status='sent'
# - metadata com campo 'source' (wf05_trigger ou manual_trigger)
# - Todos os campos preenchidos corretamente

# 2. Teste de erro (simular falha SMTP):
# - Desativar credencial SMTP temporariamente
# - Executar WF07 manualmente
# - Verificar que erro é logado:

docker exec -it e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "
SELECT
  id,
  recipient_email,
  status,
  error_message,
  metadata->'error' as error_details,
  sent_at
FROM email_logs
WHERE status = 'failed'
ORDER BY sent_at DESC
LIMIT 3;
"

# Esperado:
# - Registro com status='failed'
# - error_message preenchido
# - metadata com campo 'error'
```

---

## 🧪 Testes de Validação Completos

### **Teste 1: Template Read Direto (fs.readFileSync)**
```bash
# Verificar que template é lido sem nó "Read Template File"

docker exec e2bot-n8n-dev node -e "
const fs = require('fs');
const templatePath = '/email-templates/confirmacao_agendamento.html';
try {
  const content = fs.readFileSync(templatePath, 'utf8');
  console.log('✅ Template lido com sucesso');
  console.log('Length:', content.length, 'chars');
  console.log('Preview:', content.substring(0, 100));
} catch (error) {
  console.error('❌ Erro ao ler template:', error.message);
}
"
```

**Resultado esperado:**
```
✅ Template lido com sucesso
Length: 3456 chars (aproximado)
Preview: <!DOCTYPE html><html>...
```

---

### **Teste 2: Query SQL - 5 Parâmetros (Log Email Sent)**
```bash
# Testar query com 5 parâmetros ($1-$5)

docker exec -it e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "
-- Simular query do WF07 V6.1
PREPARE test_insert (text, text, text, text, jsonb) AS
INSERT INTO email_logs (
  recipient_email,
  recipient_name,
  subject,
  template_used,
  status,
  sent_at,
  metadata
) VALUES (\$1, \$2, \$3, \$4, 'sent', NOW(), \$5)
RETURNING id, status;

-- Executar teste
EXECUTE test_insert(
  'teste@example.com',
  'Teste Cliente',
  'Agendamento Confirmado - E2 Soluções',
  'confirmacao_agendamento',
  '{\"source\": \"manual_trigger\", \"test\": true}'::jsonb
);

-- Limpar
DEALLOCATE test_insert;
"
```

**Resultado esperado:**
```
 id  | status
-----+--------
 123 | sent
(1 row)
```

---

### **Teste 3: Query SQL - 6 Parâmetros (Log Email Error)**
```bash
# Testar query com 6 parâmetros ($1-$6)

docker exec -it e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "
-- Simular query do WF07 V6.1 (erro)
PREPARE test_error (text, text, text, text, text, jsonb) AS
INSERT INTO email_logs (
  recipient_email,
  recipient_name,
  subject,
  template_used,
  status,
  sent_at,
  error_message,
  metadata
) VALUES (\$1, \$2, \$3, \$4, 'failed', NOW(), \$5, \$6)
RETURNING id, status, error_message;

-- Executar teste
EXECUTE test_error(
  'teste@example.com',
  'Teste Cliente',
  'Agendamento Confirmado - E2 Soluções',
  'confirmacao_agendamento',
  'SMTP connection timeout',
  '{\"error\": \"SMTP connection timeout\", \"source\": \"manual_trigger\"}'::jsonb
);

-- Limpar
DEALLOCATE test_error;
"
```

**Resultado esperado:**
```
 id  | status | error_message
-----+--------+-------------------------
 124 | failed | SMTP connection timeout
(1 row)
```

---

## 📊 Monitoramento Pós-Deploy

### **Logs Docker (n8n)**
```bash
# Monitorar logs do n8n para erros
docker logs -f e2bot-n8n-dev | grep -E "ERROR|WF07|email"

# Esperado (sem erros):
# - [WF07 V6.1] Template lido com sucesso
# - [WF07 V6.1] Email enviado para: cliente@example.com
# - [WF07 V6.1] Log inserido em email_logs
```

---

### **Logs PostgreSQL (email_logs)**
```bash
# Monitorar logs de email em tempo real
docker exec -it e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "
SELECT
  to_char(sent_at, 'HH24:MI:SS') as time,
  recipient_email,
  template_used,
  status,
  CASE
    WHEN error_message IS NOT NULL THEN '❌ ' || error_message
    ELSE '✅'
  END as result
FROM email_logs
WHERE sent_at > NOW() - INTERVAL '1 hour'
ORDER BY sent_at DESC
LIMIT 10;
"
```

---

### **Métricas de Performance**
```bash
# Comparar performance V6 vs V6.1
# 1. n8n UI → Executions
# 2. Filtrar por workflow: "07 - Send Email V6.1"
# 3. Verificar tempo de execução:

# Esperado:
# - V6: ~150ms (9 nós)
# - V6.1: ~100ms (8 nós) ← 33% mais rápido
```

---

## 🔄 Rollback (Se Necessário)

### **Cenário 1: Erro na Importação**
```bash
# Se importação do V6.1 falhar:
# 1. Verificar erro no n8n
# 2. Corrigir arquivo JSON se necessário
# 3. Reimportar
```

---

### **Cenário 2: Erro em Produção**
```bash
# Se V6.1 apresentar erros em produção:

# 1. Desativar V6.1 imediatamente
# n8n UI → WF07 V6.1 → Toggle "Active" OFF

# 2. Reativar V6 (se disponível)
# n8n UI → WF07 V6 → Toggle "Active" ON

# 3. Investigar logs
docker logs e2bot-n8n-dev | tail -100

# 4. Reportar erro para análise
```

---

### **Cenário 3: Problemas com Templates**
```bash
# Se templates não forem encontrados:

# 1. Verificar volume mount
docker exec e2bot-n8n-dev ls /email-templates/

# 2. Se vazio, reiniciar container com volume configurado
docker-compose -f docker/docker-compose-dev.yml down
# Adicionar volume ao docker-compose-dev.yml
docker-compose -f docker/docker-compose-dev.yml up -d

# 3. Verificar novamente
docker exec e2bot-n8n-dev ls /email-templates/
```

---

## ✅ Checklist de Deploy

- [ ] **Pré-requisitos**
  - [ ] Docker volume mount verificado (`/email-templates/`)
  - [ ] Tabela `email_logs` existe e tem schema correto
  - [ ] Credencial SMTP configurada no n8n

- [ ] **Importação**
  - [ ] Backup do V6 criado (se aplicável)
  - [ ] WF07 V6.1 importado com sucesso
  - [ ] 8 nós e 5 conexões verificados

- [ ] **Ativação**
  - [ ] V6 desativado (se existir)
  - [ ] V6.1 ativado

- [ ] **Testes**
  - [ ] Teste manual - template read funcionando
  - [ ] Teste manual - email enviado com sucesso
  - [ ] Teste manual - log em `email_logs` com status='sent'
  - [ ] Teste WF05 → WF07 integration funcionando
  - [ ] Teste query SQL - 5 parâmetros (success)
  - [ ] Teste query SQL - 6 parâmetros (error)

- [ ] **Monitoramento**
  - [ ] Logs Docker sem erros
  - [ ] Logs PostgreSQL com registros corretos
  - [ ] Performance: ~100ms por execução

- [ ] **Documentação**
  - [ ] CLAUDE.md atualizado (V6.1 em produção)
  - [ ] Deploy registrado em histórico

---

## 🎯 Resultado Esperado

Após deploy completo do WF07 V6.1:

### **Performance**
- ✅ Execução 33% mais rápida (~100ms vs ~150ms)
- ✅ 11% menos overhead (8 nós vs 9 nós)
- ✅ Menor complexidade (leitura inline vs nó separado)

### **Confiabilidade**
- ✅ Queries SQL 100% funcionais
- ✅ Logs completos em `email_logs`
- ✅ Rastreabilidade total de emails enviados

### **Manutenibilidade**
- ✅ Código mais simples (fs.readFileSync inline)
- ✅ Menos pontos de falha (1 nó removido)
- ✅ Mais fácil de debugar

---

## 📞 Suporte

**Problemas durante deploy?**

1. **Verificar logs detalhados:**
   ```bash
   docker logs e2bot-n8n-dev --tail 200
   ```

2. **Verificar status dos containers:**
   ```bash
   docker ps -a | grep e2bot
   ```

3. **Consultar documentação:**
   - `docs/PLAN_WF07_V6.1_COMPLETE_FIX.md` (plano detalhado)
   - `docs/BUGFIX_WF05_V4.0.4_EMAIL_DATA_PASSING.md` (integração WF05)

---

**Status Final**: 🚀 **PRONTO PARA DEPLOY EM PRODUÇÃO**
