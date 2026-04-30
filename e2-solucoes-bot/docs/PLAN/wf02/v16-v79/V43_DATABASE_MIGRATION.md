# V43 - DATABASE MIGRATION (Add Missing Columns)

**Data**: 2025-03-05
**Severidade**: 🔴 CRÍTICA
**Status**: Pronto para Execução
**Approach**: Database schema migration (opposite of V42)

---

## 🚨 PROBLEMA IDENTIFICADO

### Execuções Travadas Completamente
- **Sintoma**: Bot travou completamente após V42 ("travou de vez")
- **URL**: http://localhost:5678/workflow/uigCCwYAPK4ZuChP/executions/9419
- **Erro Original**: `column "contact_name" of relation "conversations" does not exist`
- **Erro V42**: Remoção de colunas piorou a situação

### Abordagem Errada V42
**O que V42 fez (ERRADO)**:
- Removeu referências a colunas do código n8n
- Modificou Build SQL Queries para não usar service_id, contact_name, contact_email, city
- Modificou Build Update Queries para não usar contact_name, contact_email, city

**Resultado**:
> "Vc deletou todas as - Remove todas as referências a colunas inexistentes mas agora travou de vez."

**User Request**:
> "Melhore o banco e deixe as colunas."

---

## ✅ SOLUÇÃO V43 (Abordagem Correta)

### Estratégia Oposta
**V42**: Modificar código para se adequar ao banco
**V43**: Modificar banco para se adequar ao código ✅

### Mudanças Necessárias
**NÃO mudar o código n8n** - manter V41 workflow como está

**SIM adicionar colunas ao banco**:
1. `service_id VARCHAR(100)`
2. `contact_name VARCHAR(255)`
3. `contact_email VARCHAR(255)`
4. `city VARCHAR(100)`

### Por Que Esta Abordagem é Melhor
1. **Código Permanece Intacto**: V41 workflow funciona sem mudanças
2. **Migração Segura**: `ADD COLUMN IF NOT EXISTS` não perde dados
3. **Compatibilidade**: Banco alinha com expectativas do código
4. **Rollback Simples**: Se necessário, apenas fazer DROP COLUMN

---

## 🏗️ ARQUITETURA DA SOLUÇÃO

### Arquivos Criados

```
database/migrations/
└── 001_add_conversation_columns.sql    ← Migration SQL

scripts/
└── run-migration-v43.sh                ← Execution script

database/
└── schema.sql                          ← Base schema updated
```

### Migration SQL
```sql
ALTER TABLE conversations
ADD COLUMN IF NOT EXISTS service_id VARCHAR(100),
ADD COLUMN IF NOT EXISTS contact_name VARCHAR(255),
ADD COLUMN IF NOT EXISTS contact_email VARCHAR(255),
ADD COLUMN IF NOT EXISTS city VARCHAR(100);
```

### Schema Atualizado
```sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY,
    phone_number VARCHAR(20) NOT NULL UNIQUE,
    whatsapp_name VARCHAR(255),
    current_state VARCHAR(50) DEFAULT 'novo',
    collected_data JSONB DEFAULT '{}',
    service_type VARCHAR(50),

    -- V43: Legacy columns for n8n workflow compatibility
    service_id VARCHAR(100),           -- ✅ NOVO
    contact_name VARCHAR(255),         -- ✅ NOVO
    contact_email VARCHAR(255),        -- ✅ NOVO
    city VARCHAR(100),                 -- ✅ NOVO

    rdstation_contact_id VARCHAR(100),
    rdstation_deal_id VARCHAR(100),
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    last_message_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active'
);
```

---

## 🎯 PLANO DE EXECUÇÃO

### Fase 1: Backup Automático
```bash
# Executado automaticamente pelo script
docker exec e2bot-postgres-dev pg_dump -U postgres -d e2bot_dev --schema-only > backup.sql
```

### Fase 2: Execução da Migration
```bash
# Executar migration script
./scripts/run-migration-v43.sh

# Output esperado:
# ✅ PostgreSQL container is running
# ✅ Backup created
# ✅ Migration executed successfully
# ✅ All 4 columns verified
```

### Fase 3: Verificação
```bash
# Verificar colunas existem
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "
  SELECT column_name, data_type
  FROM information_schema.columns
  WHERE table_name = 'conversations'
  AND column_name IN ('service_id', 'contact_name', 'contact_email', 'city');
"

# Resultado esperado:
#  column_name   | data_type
# ---------------+-----------
#  service_id    | VARCHAR
#  contact_name  | VARCHAR
#  contact_email | VARCHAR
#  city          | VARCHAR
```

### Fase 4: Ativar V41 (sem mudanças)
```bash
# In n8n interface (http://localhost:5678)
1. Desativar V42 (se estiver ativo)
2. Ativar V41 workflow
3. Limpar cache de execuções (opcional)
```

### Fase 5: Teste End-to-End
```
Test Case 1: Fluxo Completo
  1. Enviar "oi" → Deve receber menu
  2. Enviar "1" → Deve pedir nome
  3. Enviar "Bruno Rosa" → Deve pedir telefone (NÃO voltar ao menu)
  4. Enviar telefone → Deve pedir email
  5. Verificar banco:
     SELECT phone_number, contact_name, contact_email, city, collected_data
     FROM conversations
     WHERE phone_number = '5562999887766';

     Esperado:
     contact_name: "Bruno Rosa"
     contact_email: (email fornecido)
     city: (cidade fornecida)
     collected_data: { dados complementares }

Test Case 2: Execuções Não Travam
  - Verificar http://localhost:5678/projects/08qzhIsou3TK6J3Z/executions
  - Todas devem mostrar status "success" (não "running")
  - Tempo de execução < 10 segundos
```

---

## 📊 CRITÉRIOS DE SUCESSO

### ✅ Migration Completa Quando:
1. **Todas as 4 colunas existem**: service_id, contact_name, contact_email, city
2. **Schema verification passa**: Query information_schema retorna 4 rows
3. **Backup criado**: Arquivo de backup existe em /tmp

### ✅ Fix Completo Quando:
1. **Zero erros database**: Nenhuma query falhando
2. **Execuções completam**: Status "success" em < 10s
3. **Fluxo contínuo**: Bot não volta ao menu após nome
4. **Dados persistem**: Tanto em colunas novas quanto em collected_data JSONB
5. **Logs limpos**: Sem `column "..." does not exist`

### ⚠️ Validações Adicionais:
- V41 workflow funciona SEM mudanças
- CRM sync continua funcionando (RD Station)
- Mensagens inbound/outbound salvam OK
- Lead upsert funciona com as colunas novas

---

## 🔧 SCRIPTS DE EXECUÇÃO E VALIDAÇÃO

### Executar Migration
```bash
cd /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot
./scripts/run-migration-v43.sh
```

### Verificação Manual
```bash
# 1. Check columns exist
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "\d conversations"

# 2. Test insert (should work now)
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "
  INSERT INTO conversations (
    phone_number, contact_name, contact_email, city
  ) VALUES (
    '5562999999999', 'Test User', 'test@example.com', 'Goiânia'
  ) RETURNING *;
"

# 3. Clean up test
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "
  DELETE FROM conversations WHERE phone_number = '5562999999999';
"
```

---

## 📝 HISTÓRICO DE VERSÕES

### V41 (Base)
- **Status**: Workflow funcionando mas com erro de colunas
- **Problema**: Referencia colunas que não existem no banco
- **Queries**: Build SQL Queries + Build Update Queries usam contact_name, etc.

### V42 (Abordagem Errada) ❌
- **Data**: 2025-03-05
- **Abordagem**: Remover colunas do código n8n
- **Problema**: "Travou de vez" segundo usuário
- **Solução**: ABANDONAR esta abordagem
- **Status**: ❌ Não usar

### V43 (Abordagem Correta) ✅
- **Data**: 2025-03-05
- **Abordagem**: Adicionar colunas ao banco de dados
- **Impacto**: V41 workflow funciona SEM mudanças
- **Solução**: Migration SQL + updated schema
- **Status**: ✅ Pronto para execução

---

## 🚀 NEXT STEPS

1. **Immediate**: Executar `./scripts/run-migration-v43.sh`
2. **Verification**: Verificar que 4 colunas foram adicionadas
3. **Activation**: Desativar V42, ativar V41
4. **Testing**: Executar teste end-to-end completo
5. **Monitoring**: Observar logs por 1h após migration

---

## 📞 TROUBLESHOOTING

### Se V43 Migration Falhar
```bash
# Check error message
docker logs e2bot-postgres-dev 2>&1 | tail -50

# Restore from backup if needed
docker exec -i e2bot-postgres-dev psql -U postgres -d e2bot_dev < /tmp/e2bot_schema_backup_*.sql
```

### Se V41 Ainda Falhar Após Migration
```bash
# Check logs
docker logs -f e2bot-n8n-dev 2>&1 | grep -E "ERROR|column|does not exist"

# Verify columns again
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "\d conversations"

# Check actual query being executed
# (n8n logs should show the failing SQL)
```

### Rollback Plan
```bash
# Se V43 não funcionar, fazer rollback
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "
  ALTER TABLE conversations
  DROP COLUMN IF EXISTS service_id,
  DROP COLUMN IF EXISTS contact_name,
  DROP COLUMN IF EXISTS contact_email,
  DROP COLUMN IF EXISTS city;
"
```

---

## 💡 LIÇÕES APRENDIDAS

### V42 vs V43 Comparison

| Aspecto | V42 (Wrong) | V43 (Correct) |
|---------|-------------|---------------|
| **Approach** | Modify code | Modify database |
| **Impact** | Broke workflow | Fixes workflow |
| **Changes** | 2 n8n nodes | 1 database migration |
| **Risk** | High (code complexity) | Low (simple ALTER TABLE) |
| **Rollback** | Restore workflow JSON | DROP COLUMN |
| **User Feedback** | "Travou de vez" | Awaiting testing |

### Key Insight
> "When database and code disagree, sometimes it's better to fix the database than the code."

Especially when:
1. Code is complex (n8n workflow JSON)
2. Database change is simple (ALTER TABLE)
3. Database change is safer (ADD COLUMN IF NOT EXISTS)
4. User explicitly requests it ("Melhore o banco e deixe as colunas")

---

**Autor**: Claude Code Analysis
**Última Atualização**: 2025-03-05 19:30 BRT
**Próxima Ação**: Executar `./scripts/run-migration-v43.sh`
