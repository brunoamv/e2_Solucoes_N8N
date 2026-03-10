# V45 - Add state_machine_state Column Fix

**Data**: 2026-03-06
**Severidade**: 🔴 CRÍTICA
**Status**: Plano pronto para execução
**Approach**: Add missing state_machine_state column to conversations table

---

## 🚨 PROBLEMA IDENTIFICADO

### Erro Atual
```
column "state_machine_state" of relation "conversations" does not exist
Failed query: INSERT INTO conversations (..., state_machine_state, ...)
```

### Root Cause Analysis
**Workflow V41 espera coluna que não existe**:
```
Database Schema (ATUAL):
  ✅ current_state VARCHAR(50)
  ❌ state_machine_state VARCHAR(50)  ← FALTA ESTA COLUNA

Workflow V41 (EXPECTED):
  state_machine_state: nextStage,  ← Workflow usa esta coluna
  current_state: normalizedStage
```

### Timeline do Problema
1. **V43**: Criou database e2bot_dev com schema base
2. **V44**: Atualizou credenciais n8n (e2_bot → e2bot_dev)
3. **V41 Workflow**: Tenta usar state_machine_state
4. **Error**: Coluna não existe no schema

### Impact
- ✅ Credenciais corretas (e2bot_dev)
- ✅ Database existe
- ✅ Todas outras colunas existem
- ❌ state_machine_state faltando causa INSERT failure
- ❌ Conversas não são criadas/atualizadas
- ❌ Bot não funciona

---

## ✅ SOLUÇÃO V45

### Estratégia
**Adicionar coluna state_machine_state à tabela conversations**

### Mudança Necessária
```sql
ALTER TABLE conversations
ADD COLUMN state_machine_state VARCHAR(50);
```

### Análise da Coluna
- **Nome**: state_machine_state
- **Tipo**: VARCHAR(50)
- **Propósito**: Armazenar estado da máquina de estados (greeting, service_selection, collect_name, etc.)
- **Diferença de current_state**:
  - `current_state`: Estados do banco (novo, identificando_servico, coletando_dados)
  - `state_machine_state`: Estados da máquina (greeting, service_selection, collect_name)
- **Nullable**: SIM (permitir NULL para conversas antigas)
- **Default**: NULL (será populado pelo workflow)

---

## 🎯 PLANO DE EXECUÇÃO

### Fase 1: Criar Script de Migração

**Arquivo**: `database/migrations/002_add_state_machine_state.sql`

```sql
-- V45 Migration: Add state_machine_state column
-- Purpose: Support V41 workflow state machine tracking

BEGIN;

-- Add state_machine_state column
ALTER TABLE conversations
ADD COLUMN IF NOT EXISTS state_machine_state VARCHAR(50);

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_conversations_state_machine
ON conversations(state_machine_state);

-- Populate existing records with mapped values
UPDATE conversations
SET state_machine_state = CASE current_state
  WHEN 'novo' THEN 'greeting'
  WHEN 'identificando_servico' THEN 'service_selection'
  WHEN 'coletando_dados' THEN 'collect_name'
  WHEN 'agendando' THEN 'scheduling'
  WHEN 'handoff_comercial' THEN 'handoff_comercial'
  WHEN 'concluido' THEN 'completed'
  ELSE 'greeting'
END
WHERE state_machine_state IS NULL;

-- Verify migration
DO $$
DECLARE
    v_column_exists BOOLEAN;
BEGIN
    SELECT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'conversations'
        AND column_name = 'state_machine_state'
    ) INTO v_column_exists;

    IF v_column_exists THEN
        RAISE NOTICE '✅ V45: state_machine_state column added successfully';
    ELSE
        RAISE EXCEPTION '❌ V45: Failed to add state_machine_state column';
    END IF;
END $$;

COMMIT;
```

### Fase 2: Executar Migração

**Comandos**:
```bash
cd /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot

# Executar migration diretamente
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -f /migrations/002_add_state_machine_state.sql

# OU executar via volume mount
docker exec -i e2bot-postgres-dev psql -U postgres -d e2bot_dev < database/migrations/002_add_state_machine_state.sql
```

### Fase 3: Verificar Migration

**Comandos de Verificação**:
```bash
# 1. Verificar que coluna existe
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "
  SELECT column_name, data_type, character_maximum_length
  FROM information_schema.columns
  WHERE table_name = 'conversations'
  AND column_name = 'state_machine_state';
"

# Esperado:
#     column_name      | data_type        | character_maximum_length
# ---------------------+------------------+--------------------------
#  state_machine_state | character varying|                       50

# 2. Verificar índice criado
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "
  SELECT indexname
  FROM pg_indexes
  WHERE tablename = 'conversations'
  AND indexname = 'idx_conversations_state_machine';
"

# Esperado:
#          indexname
# -------------------------------
#  idx_conversations_state_machine

# 3. Verificar estrutura completa da tabela
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "\d conversations"
```

### Fase 4: Atualizar Schema Base

**Arquivo**: `database/schema.sql`

Adicionar coluna ao CREATE TABLE:
```sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phone_number VARCHAR(20) NOT NULL UNIQUE,
    whatsapp_name VARCHAR(255),
    current_state VARCHAR(50) DEFAULT 'novo',
    state_machine_state VARCHAR(50),  -- ← ADICIONAR ESTA LINHA
    collected_data JSONB DEFAULT '{}',
    -- ... resto das colunas
);

-- Adicionar índice
CREATE INDEX idx_conversations_state_machine ON conversations(state_machine_state);
```

### Fase 5: Testar Workflow V41

**Teste Manual**:
```
1. Enviar mensagem WhatsApp: "oi"
2. Verificar resposta do bot (menu)
3. Verificar que não há erro de coluna
4. Verificar execução em n8n (success)
5. Verificar banco de dados
```

**Verificação Database**:
```bash
# Verificar registro criado com state_machine_state
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "
  SELECT
    phone_number,
    current_state,
    state_machine_state,  -- ← NOVA COLUNA
    collected_data,
    created_at
  FROM conversations
  ORDER BY created_at DESC
  LIMIT 3;
"

# Esperado: state_machine_state populado (greeting, service_selection, etc.)
```

---

## 📊 CRITÉRIOS DE SUCESSO

### ✅ Migration Completa Quando:
1. **Coluna Adicionada**: state_machine_state existe na tabela conversations
2. **Índice Criado**: idx_conversations_state_machine existe
3. **Dados Migrados**: Conversas existentes têm state_machine_state populado
4. **Schema Atualizado**: schema.sql contém a nova coluna

### ✅ Workflow V41 Funciona Quando:
1. **INSERT Success**: Nenhum erro "column does not exist"
2. **Conversa Criada**: Registro criado em conversations
3. **Estado Salvo**: state_machine_state populado corretamente
4. **Execução Success**: Workflow completa com status "success"

---

## 🔧 SCRIPT DE EXECUÇÃO AUTOMATIZADO

**Arquivo**: `scripts/run-migration-v45.sh`

```bash
#!/bin/bash

# V45 Migration Script
# Purpose: Add state_machine_state column to conversations table

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "V45 Migration: Add state_machine_state"
echo "=========================================="

# Check if container is running
if ! docker ps | grep -q e2bot-postgres-dev; then
    echo -e "${RED}❌${NC} PostgreSQL container not running"
    echo "Start with: docker-compose -f docker/docker-compose-dev.yml up -d postgres-dev"
    exit 1
fi

# Check if database exists
DB_EXISTS=$(docker exec e2bot-postgres-dev psql -U postgres -lqt | cut -d \| -f 1 | grep -w e2bot_dev | wc -l)
if [ "$DB_EXISTS" -eq "0" ]; then
    echo -e "${RED}❌${NC} Database e2bot_dev does not exist"
    exit 1
fi

echo -e "${GREEN}✅${NC} Database e2bot_dev found"

# Execute migration
echo ""
echo "Executing migration..."
docker exec -i e2bot-postgres-dev psql -U postgres -d e2bot_dev << 'EOF'
-- V45 Migration: Add state_machine_state column
BEGIN;

-- Add column
ALTER TABLE conversations
ADD COLUMN IF NOT EXISTS state_machine_state VARCHAR(50);

-- Create index
CREATE INDEX IF NOT EXISTS idx_conversations_state_machine
ON conversations(state_machine_state);

-- Populate existing records
UPDATE conversations
SET state_machine_state = CASE current_state
  WHEN 'novo' THEN 'greeting'
  WHEN 'identificando_servico' THEN 'service_selection'
  WHEN 'coletando_dados' THEN 'collect_name'
  WHEN 'agendando' THEN 'scheduling'
  WHEN 'handoff_comercial' THEN 'handoff_comercial'
  WHEN 'concluido' THEN 'completed'
  ELSE 'greeting'
END
WHERE state_machine_state IS NULL;

COMMIT;
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅${NC} Migration executed successfully"
else
    echo -e "${RED}❌${NC} Migration failed"
    exit 1
fi

# Verify migration
echo ""
echo "Verifying migration..."

# Check column exists
COLUMN_EXISTS=$(docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -t -c "
    SELECT COUNT(*)
    FROM information_schema.columns
    WHERE table_name = 'conversations'
    AND column_name = 'state_machine_state';
" | tr -d ' ')

if [ "$COLUMN_EXISTS" = "1" ]; then
    echo -e "${GREEN}✅${NC} Column state_machine_state exists"
else
    echo -e "${RED}❌${NC} Column state_machine_state NOT found"
    exit 1
fi

# Check index exists
INDEX_EXISTS=$(docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -t -c "
    SELECT COUNT(*)
    FROM pg_indexes
    WHERE tablename = 'conversations'
    AND indexname = 'idx_conversations_state_machine';
" | tr -d ' ')

if [ "$INDEX_EXISTS" = "1" ]; then
    echo -e "${GREEN}✅${NC} Index idx_conversations_state_machine exists"
else
    echo -e "${YELLOW}⚠️${NC} Index idx_conversations_state_machine NOT found"
fi

# Show column details
echo ""
echo "Column details:"
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "
    SELECT column_name, data_type, character_maximum_length
    FROM information_schema.columns
    WHERE table_name = 'conversations'
    AND column_name = 'state_machine_state';
"

# Show sample data
echo ""
echo "Sample data (last 3 records):"
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "
    SELECT
        phone_number,
        current_state,
        state_machine_state,
        LEFT(COALESCE(whatsapp_name, ''), 20) as name
    FROM conversations
    ORDER BY updated_at DESC
    LIMIT 3;
"

echo ""
echo "=========================================="
echo -e "${GREEN}✅ V45 Migration Complete${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Test workflow V41: Send WhatsApp message 'oi'"
echo "2. Verify n8n execution: http://localhost:5678/projects/08qzhIsou3TK6J3Z/executions"
echo "3. Check database: state_machine_state should be populated"
echo ""
```

---

## 📝 RESUMO EXECUTIVO

### Problema
Workflow V41 tenta usar coluna `state_machine_state` que não existe

### Causa
Schema V43 não incluiu esta coluna necessária para tracking da state machine

### Solução
Adicionar coluna `state_machine_state VARCHAR(50)` à tabela conversations

### Impacto
- **Baixo**: Apenas adição de coluna (non-breaking)
- **Rápido**: 2 minutos para executar
- **Seguro**: ALTER TABLE ADD COLUMN não afeta dados existentes
- **Reversível**: Pode remover coluna se necessário (mas não deve precisar)

### Benefício
- ✅ Workflow V41 funcionará completamente
- ✅ State machine tracking funcionará
- ✅ Conversas serão criadas e atualizadas corretamente
- ✅ Sistema funcionará end-to-end

---

## 🚨 PRECAUÇÕES

### Antes de Executar
- ✅ Database e2bot_dev existe
- ✅ PostgreSQL container rodando
- ✅ Backup não necessário (adição de coluna é segura)

### Durante Execução
- ⚠️ **NÃO** remover colunas existentes
- ⚠️ **NÃO** modificar dados existentes além da população inicial
- ⚠️ Migration deve ser rápida (<5 segundos)

### Após Execução
- ✅ Verificar coluna existe
- ✅ Verificar índice criado
- ✅ Verificar dados populados
- ✅ Testar workflow V41

---

## 🔄 ROLLBACK PLAN

**Se V45 causar problemas**:

```bash
# Option 1: Remover coluna (NÃO RECOMENDADO - V41 precisa dela)
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "
  ALTER TABLE conversations DROP COLUMN IF EXISTS state_machine_state;
  DROP INDEX IF EXISTS idx_conversations_state_machine;
"

# Option 2: Manter coluna mas limpar dados
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "
  UPDATE conversations SET state_machine_state = NULL;
"
```

**Recomendação**: V45 é seguro. Apenas adiciona coluna necessária para V41.

---

**Autor**: Claude Code Analysis
**Data**: 2026-03-06
**Versão**: V45 Plan
**Status**: Ready for Execution
**Estimated Time**: 2-5 minutes
**Risk Level**: LOW (column addition only)
**Rollback**: Easy (just drop column)

---

**EXECUTE QUANDO PRONTO**
**Instrução**:
1. Criar script: `scripts/run-migration-v45.sh`
2. Dar permissão: `chmod +x scripts/run-migration-v45.sh`
3. Executar: `./scripts/run-migration-v45.sh`
4. Testar workflow V41
