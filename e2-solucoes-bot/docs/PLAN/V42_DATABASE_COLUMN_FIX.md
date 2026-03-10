# V42 - DATABASE COLUMN FIX

**Data**: 2025-03-05
**Severidade**: 🔴 CRÍTICA
**Status**: Em Desenvolvimento

---

## 🚨 PROBLEMA IDENTIFICADO

### Execuções Travadas em "Running"
- **URL**: http://localhost:5678/workflow/uigCCwYAPK4ZuChP/executions/9419
- **Sintoma**: Workflow fica em estado "running" indefinidamente e não completa
- **Erro Database**: `column "contact_name" of relation "conversations" does not exist`

### Comportamento Observado
```
[15:37] RogueBot: Menu (funcionou)
[15:38] User: 1
[15:38] RogueBot: Ótima escolha! Nome completo? (funcionou)
[15:38] User: Bruno Rosa
[15:38] RogueBot: 🤖 Menu novamente (BUG - voltou ao início)
```

**CRITICAL**: Bot volta ao menu ao invés de avançar para próxima etapa.

---

## 🔍 ROOT CAUSE ANALYSIS

### 1. Colunas Inexistentes no Banco
Schema atual (`database/schema.sql`):
```sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY,
    phone_number VARCHAR(20) NOT NULL UNIQUE,
    whatsapp_name VARCHAR(255),
    current_state VARCHAR(50) DEFAULT 'novo',
    collected_data JSONB DEFAULT '{}',  -- ← Dados vão aqui (JSONB)
    service_type VARCHAR(50),
    -- NÃO TEM: contact_name, contact_email, city, service_id
)
```

### 2. Queries Erradas no Workflow V41
**Build SQL Queries (linha 365)**:
```javascript
INSERT INTO conversations (
    service_id,        // ❌ NÃO EXISTE
    contact_name,      // ❌ NÃO EXISTE
    contact_email,     // ❌ NÃO EXISTE
    city,              // ❌ NÃO EXISTE
    ...
)
```

**Build Update Queries (linha 419)**:
```javascript
INSERT INTO conversations (
    contact_name,      // ❌ NÃO EXISTE
    contact_email,     // ❌ NÃO EXISTE
    city,              // ❌ NÃO EXISTE
    ...
)
ON CONFLICT (phone_number)
DO UPDATE SET
    contact_name = ...,  // ❌ NÃO EXISTE
    contact_email = ..., // ❌ NÃO EXISTE
    city = ...           // ❌ NÃO EXISTE
```

### 3. Cadeia de Falhas
```
1. User envia "Bruno Rosa"
2. State Machine valida OK
3. Build Update Queries cria SQL com contact_name
4. PostgreSQL node executa query
5. Database retorna ERRO: column "contact_name" does not exist
6. n8n trava execução (não completa)
7. Bot fica sem resposta do workflow
8. Evolution API reexibe menu ao usuário
```

---

## ✅ SOLUÇÃO V42

### Estratégia de Correção
**Princípio**: Dados pessoais vão para `collected_data` JSONB, não em colunas separadas.

### Mudanças Necessárias

#### 1. Build SQL Queries Node
**REMOVER colunas** (linha ~365):
```diff
  INSERT INTO conversations (
    phone_number,
    whatsapp_name,
-   service_id,
-   contact_name,
-   contact_email,
-   city,
    current_state,
    state_machine_state,
    collected_data,
    ...
  ) VALUES (
    '${phone_without_code}',
    '${whatsapp_name}',
-   NULL,
-   NULL,
-   NULL,
-   NULL,
    'novo',
    'greeting',
    '{}'::jsonb,
    ...
  )
```

#### 2. Build Update Queries Node
**REMOVER colunas do INSERT** (linha ~419):
```diff
  INSERT INTO conversations (
    phone_number,
    whatsapp_name,
    current_state,
    state_machine_state,
    collected_data,
    service_type,
-   contact_name,
-   contact_email,
-   city,
    status,
    last_message_at,
    created_at,
    updated_at
  ) VALUES (
    '${phone_with_code}',
    '${whatsapp_name}',
    '${db_state}',
    '${next_stage}',
    '${collected_data_json}'::jsonb,
    ${service_type},
-   '${lead_name}',
-   '${email}',
-   '${city}',
    'active',
    NOW(),
    NOW(),
    NOW()
  )
```

**REMOVER do UPDATE SET**:
```diff
  ON CONFLICT (phone_number)
  DO UPDATE SET
    current_state = EXCLUDED.current_state,
    state_machine_state = EXCLUDED.state_machine_state,
    collected_data = EXCLUDED.collected_data,
    service_type = COALESCE(EXCLUDED.service_type, conversations.service_type),
-   contact_name = COALESCE(NULLIF(EXCLUDED.contact_name, ''), conversations.contact_name),
-   contact_email = COALESCE(NULLIF(EXCLUDED.contact_email, ''), conversations.contact_email),
-   city = COALESCE(NULLIF(EXCLUDED.city, ''), conversations.city),
    whatsapp_name = COALESCE(NULLIF(EXCLUDED.whatsapp_name, ''), conversations.whatsapp_name),
    last_message_at = NOW(),
    updated_at = NOW()
  RETURNING *
```

### Dados Estruturados em JSONB
```json
{
  "collected_data": {
    "lead_name": "Bruno Rosa",
    "phone": "62999887766",
    "email": "bruno@example.com",
    "city": "Goiânia",
    "service_type": "energia_solar"
  }
}
```

---

## 🎯 PLANO DE EXECUÇÃO

### Fase 1: Criação do Fix
```bash
# 1. Criar script Python V42
python3 scripts/fix-workflow-v42-database-columns.py

# Output esperado:
# - 02_ai_agent_conversation_V42_DATABASE_COLUMNS_FIX.json
```

### Fase 2: Validação Estrutural
```bash
# 2. Validar remoção de colunas
grep -i "contact_name\|contact_email\|city\|service_id" \
  n8n/workflows/02_ai_agent_conversation_V42_DATABASE_COLUMNS_FIX.json

# Resultado esperado: NENHUMA ocorrência
```

### Fase 3: Deploy
```bash
# 3. Desativar V41
# Interface n8n: http://localhost:5678

# 4. Importar V42
# Arquivo: 02_ai_agent_conversation_V42_DATABASE_COLUMNS_FIX.json

# 5. Ativar V42

# 6. Limpar cache de execuções
docker exec e2bot-n8n-dev n8n cache clear
```

### Fase 4: Testes End-to-End
```
Test Case 1: Fluxo Completo
  1. Enviar "oi" → Deve receber menu
  2. Enviar "1" → Deve pedir nome
  3. Enviar "Bruno Rosa" → Deve pedir telefone (NÃO voltar ao menu)
  4. Enviar telefone → Deve pedir email
  5. Verificar banco:
     SELECT collected_data FROM conversations
     WHERE phone_number = '5562999887766';

     Esperado:
     {
       "lead_name": "Bruno Rosa",
       "phone": "62999887766",
       ...
     }

Test Case 2: Execuções Não Travam
  - Verificar http://localhost:5678/projects/08qzhIsou3TK6J3Z/executions
  - Todas devem mostrar status "success" (não "running")
  - Tempo de execução < 10 segundos
```

---

## 📊 CRITÉRIOS DE SUCESSO

### ✅ Fix Completo Quando:
1. **Zero erros database**: Nenhuma query falhando
2. **Execuções completam**: Status "success" em < 10s
3. **Fluxo contínuo**: Bot não volta ao menu após nome
4. **Dados persistem**: `collected_data` JSONB salva corretamente
5. **Logs limpos**: Sem `column "..." does not exist`

### ⚠️ Validações Adicionais:
- CRM sync continua funcionando (RD Station)
- Mensagens inbound/outbound salvam OK
- Lead upsert funciona sem as colunas removidas

---

## 🔧 SCRIPT DE VALIDAÇÃO

Criar `scripts/validate-v42-fix.sh`:
```bash
#!/bin/bash
echo "=== V42 DATABASE COLUMN FIX VALIDATION ==="

# 1. Check for removed columns
echo "1. Checking for non-existent columns..."
if grep -qi "contact_name\|service_id" n8n/workflows/02_ai_agent_conversation_V42_DATABASE_COLUMNS_FIX.json; then
    echo "❌ FAIL: Found non-existent columns in V42"
    exit 1
else
    echo "✅ PASS: No non-existent columns found"
fi

# 2. Verify collected_data usage
echo "2. Checking collected_data usage..."
if grep -q "collected_data" n8n/workflows/02_ai_agent_conversation_V42_DATABASE_COLUMNS_FIX.json; then
    echo "✅ PASS: collected_data JSONB is used"
else
    echo "❌ FAIL: collected_data not found"
    exit 1
fi

# 3. Check database schema
echo "3. Verifying database schema..."
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "\d conversations" | grep -q "contact_name"
if [ $? -eq 0 ]; then
    echo "❌ FAIL: contact_name still exists in database"
    exit 1
else
    echo "✅ PASS: Database schema matches (no contact_name)"
fi

# 4. Test execution
echo "4. Testing workflow execution..."
echo "Manual test required:"
echo "  1. Send 'oi' to WhatsApp bot"
echo "  2. Send '1'"
echo "  3. Send 'Bruno Rosa'"
echo "  4. Verify bot asks for phone (not back to menu)"
echo "  5. Check executions: http://localhost:5678/projects/08qzhIsou3TK6J3Z/executions"
echo "  6. All should show 'success' status"

echo ""
echo "=== V42 VALIDATION COMPLETE ==="
```

---

## 📝 HISTÓRICO DE VERSÕES

### V40 → V41
- **Problema**: `queryBatching: "independent"` engolia `RETURNING *`
- **Solução**: Remover `queryBatching` de 3 nodes PostgreSQL
- **Status**: ✅ Resolvido

### V41 → V42
- **Problema**: Colunas `contact_name`, `contact_email`, `city`, `service_id` não existem
- **Impacto**: Execuções travam, bot volta ao menu
- **Solução**: Remover referências a colunas inexistentes
- **Status**: 🔄 Em Desenvolvimento

---

## 🚀 NEXT STEPS

1. **Immediate**: Criar script `fix-workflow-v42-database-columns.py`
2. **Validation**: Executar `validate-v42-fix.sh`
3. **Deploy**: Importar V42 e desativar V41
4. **Testing**: Executar teste end-to-end completo
5. **Monitoring**: Observar logs por 24h após deploy

---

## 📞 TROUBLESHOOTING

### Se V42 Ainda Falhar:
```bash
# Check logs
docker logs -f e2bot-n8n-dev 2>&1 | grep -E "ERROR|column|does not exist"

# Check database
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "
  SELECT column_name, data_type
  FROM information_schema.columns
  WHERE table_name = 'conversations';
"

# Check executions
curl http://localhost:5678/healthz
```

### Rollback Plan:
```bash
# Se V42 não funcionar, voltar para V40
# V40 estava funcionando parcialmente (queryBatching issue menor)
1. Desativar V42
2. Ativar V40
3. Investigar mais profundamente
```

---

**Autor**: Claude Code Analysis
**Última Atualização**: 2025-03-05 18:50 BRT
