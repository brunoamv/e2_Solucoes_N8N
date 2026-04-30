# V58.1 Database Migration Plan

> **Critical Database Schema Update** | Date: 2026-03-10 | Version: V58.1

---

## 🎯 Migration Overview

**Problem**: V58.1 workflow implements fields that don't exist in PostgreSQL database

**Solution**: Complete database schema migration with all V58.1 gap fixes

**Status**: ⏳ READY TO EXECUTE

---

## 🔍 Gap Analysis Summary

### Current Database Schema (V43)
```sql
conversations table:
  - phone_number (VARCHAR(20), NOT NULL)
  - service_type (VARCHAR(50), NULL)          -- ⚠️ Constraint outdated
  - current_state (VARCHAR(50))                -- ⚠️ Constraint incomplete
  - contact_phone (column)                     -- ❌ DOES NOT EXIST (GAP #8)
```

### V58.1 Workflow Requirements
```javascript
// GAP #8: contact_phone field mapping
updateData.contact_phone = currentData.phone_number || currentData.phone;  // Line 240

// GAP #6: service_type STRING mapping
updateData.service_type = serviceMapping[message];  // "Energia Solar", not "energia_solar"

// GAP #1: New states for phone confirmation
'collect_phone_whatsapp_confirmation'
'collect_phone_alternative'
```

---

## 📋 Migration Changes

### 1. **GAP #8 - Add contact_phone Column** ✅

**Purpose**: Store primary contact phone (WhatsApp confirmed or alternative)

**SQL**:
```sql
ALTER TABLE conversations
ADD COLUMN contact_phone VARCHAR(20);

CREATE INDEX idx_conversations_contact_phone
ON conversations(contact_phone);

-- Populate from existing data
UPDATE conversations
SET contact_phone = phone_number
WHERE contact_phone IS NULL AND phone_number IS NOT NULL;
```

**Field Details**:
- **Type**: `VARCHAR(20)`
- **Nullable**: `YES` (optional field)
- **Purpose**: Primary contact phone (may differ from WhatsApp phone_number)
- **Index**: Added for query performance

---

### 2. **GAP #6 - Update service_type Constraint** ✅

**Problem**: Current constraint only accepts snake_case values (`energia_solar`)
**Solution**: Accept both STRING ("Energia Solar") AND legacy snake_case

**SQL**:
```sql
-- Drop old constraint
ALTER TABLE conversations DROP CONSTRAINT valid_service;

-- Add new V58.1 constraint
ALTER TABLE conversations ADD CONSTRAINT valid_service_v58 CHECK (
    service_type IS NULL OR
    service_type IN (
        -- V58.1: STRING values (Gap #6)
        'Energia Solar',
        'Subestação',
        'Projetos Elétricos',
        'BESS',
        'Análise e Laudos',
        -- Legacy: Backward compatibility
        'energia_solar',
        'subestacao',
        'projeto_eletrico',
        'armazenamento_energia',
        'analise_laudo',
        'outro'
    )
);
```

**Impact**:
- ✅ Accepts new STRING format from V58.1 service mapping
- ✅ Maintains backward compatibility with V43-V57 data
- ✅ Prevents invalid service types

---

### 3. **GAP #1 - Update current_state Constraint** ✅

**Problem**: Current constraint doesn't include V58.1 phone confirmation states
**Solution**: Add 2 new states to valid_state constraint

**SQL**:
```sql
-- Drop old constraint
ALTER TABLE conversations DROP CONSTRAINT valid_state;

-- Add new V58.1 constraint
ALTER TABLE conversations ADD CONSTRAINT valid_state_v58 CHECK (
    current_state IN (
        -- Original states
        'novo',
        'identificando_servico',
        'coletando_dados',
        'aguardando_foto',
        'agendando',
        'agendado',
        'handoff_comercial',
        'concluido',
        -- V58.1 NEW: Phone confirmation states
        'coletando_telefone_confirmacao_whatsapp',
        'coletando_telefone_alternativo'
    )
);
```

**New States**:
1. `coletando_telefone_confirmacao_whatsapp` - WhatsApp number confirmation
2. `coletando_telefone_alternativo` - Alternative phone collection

---

## 🚀 Execution Plan

### Pre-Migration Checklist
- [ ] All services running (`docker-compose up -d`)
- [ ] No active workflows processing messages
- [ ] Database backup created automatically by script
- [ ] Migration script has execution permissions

### Execution Steps

**Step 1: Run Migration Script**
```bash
cd /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot
./scripts/run-migration-v58_1-complete.sh
```

**Step 2: Verify Migration**
```bash
# Check contact_phone column
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "\d conversations"

# Test contact_phone query (should work now)
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -c \
  "SELECT phone_number, service_type, contact_phone, current_state
   FROM conversations ORDER BY updated_at DESC LIMIT 5;"
```

**Step 3: Import V58.1 Workflow**
1. Access n8n: http://localhost:5678
2. Import: `n8n/workflows/02_ai_agent_conversation_V58_1_UX_REFACTOR_COMPLETE.json`
3. Deactivate V57.2 workflow
4. Activate V58.1 workflow

**Step 4: Test V58.1 Paths**
Execute 3 test paths from `docs/Setups/QUICKSTART.md` section "Test V58.1"

---

## 🔄 Rollback Plan

### Automatic Backup
Migration script creates automatic backup:
```
/tmp/e2bot_backup_v58_1_YYYYMMDD_HHMMSS.sql
```

### Rollback Command
```bash
# Restore from backup
cat /tmp/e2bot_backup_v58_1_YYYYMMDD_HHMMSS.sql | \
  docker exec -i e2bot-postgres-dev psql -U postgres -d e2bot_dev
```

### Manual Rollback (if needed)
```sql
-- Remove contact_phone column
ALTER TABLE conversations DROP COLUMN IF EXISTS contact_phone;

-- Restore original service_type constraint
ALTER TABLE conversations DROP CONSTRAINT IF EXISTS valid_service_v58;
ALTER TABLE conversations ADD CONSTRAINT valid_service CHECK (
    service_type IN (
        'energia_solar',
        'subestacao',
        'projeto_eletrico',
        'armazenamento_energia',
        'analise_laudo',
        'outro'
    ) OR service_type IS NULL
);

-- Restore original state constraint
ALTER TABLE conversations DROP CONSTRAINT IF EXISTS valid_state_v58;
ALTER TABLE conversations ADD CONSTRAINT valid_state CHECK (
    current_state IN (
        'novo',
        'identificando_servico',
        'coletando_dados',
        'aguardando_foto',
        'agendando',
        'agendado',
        'handoff_comercial',
        'concluido'
    )
);

-- Remove migration record
DELETE FROM schema_migrations WHERE version = 'V58.1';
```

---

## 📊 Schema Comparison

### Before Migration (V43)
| Column | Type | Constraint |
|--------|------|------------|
| phone_number | VARCHAR(20) | NOT NULL |
| service_type | VARCHAR(50) | valid_service (6 snake_case values) |
| current_state | VARCHAR(50) | valid_state (8 states) |
| contact_phone | - | ❌ DOES NOT EXIST |

### After Migration (V58.1)
| Column | Type | Constraint |
|--------|------|------------|
| phone_number | VARCHAR(20) | NOT NULL |
| service_type | VARCHAR(50) | valid_service_v58 (11 values: 5 STRING + 6 snake_case) |
| current_state | VARCHAR(50) | valid_state_v58 (10 states: 8 original + 2 new) |
| contact_phone | VARCHAR(20) | ✅ NEW COLUMN (indexed) |

---

## 🔬 Validation Tests

### Test 1: contact_phone Population
```sql
-- After migration, check data migration
SELECT
    phone_number,
    contact_phone,
    CASE
        WHEN contact_phone = phone_number THEN 'Migrated from phone_number'
        WHEN contact_phone IS NULL THEN 'NULL (expected for empty)'
        ELSE 'User-provided alternative'
    END as contact_phone_source
FROM conversations
WHERE phone_number IS NOT NULL
ORDER BY updated_at DESC
LIMIT 10;
```

**Expected**: All existing rows with `phone_number` should have `contact_phone = phone_number`

### Test 2: service_type STRING Values
```sql
-- Test new STRING service type insertion
INSERT INTO conversations (
    phone_number,
    service_type,
    current_state
) VALUES (
    '5562999999999',
    'Energia Solar',  -- V58.1 STRING format
    'novo'
) ON CONFLICT (phone_number) DO UPDATE SET service_type = EXCLUDED.service_type;

-- Verify
SELECT phone_number, service_type
FROM conversations
WHERE phone_number = '5562999999999';
```

**Expected**: No constraint violation, service_type = "Energia Solar"

### Test 3: New State Validation
```sql
-- Test new V58.1 states
UPDATE conversations
SET current_state = 'coletando_telefone_confirmacao_whatsapp'
WHERE phone_number = '5562999999999';

-- Verify
SELECT phone_number, current_state
FROM conversations
WHERE phone_number = '5562999999999';
```

**Expected**: No constraint violation, state updated successfully

---

## 🐛 Known Issues & Solutions

### Issue 1: Existing Data Without contact_phone
**Problem**: Old conversations have NULL contact_phone
**Solution**: Migration automatically populates from phone_number
**Impact**: Minimal - V58.1 uses fallback logic

### Issue 2: Mixed service_type Formats
**Problem**: Database may have both "Energia Solar" and "energia_solar"
**Solution**: Constraint accepts both formats
**Impact**: None - both formats valid

### Issue 3: State Machine Compatibility
**Problem**: V57.2 data has states not in V58.1
**Solution**: V58.1 preserves all V57.2 states + adds 2 new
**Impact**: None - full backward compatibility

---

## 📈 Migration Metrics

### Estimated Duration
- **Backup**: ~2-5 seconds (depends on data size)
- **Migration SQL**: ~1-2 seconds
- **Verification**: ~1 second
- **Total**: ~5-10 seconds

### Database Downtime
- **Planned**: ~10 seconds (during ALTER TABLE operations)
- **Impact**: Minimal - n8n workflows can be paused

### Data Impact
- **Rows Modified**: All existing conversations (contact_phone population)
- **Constraints Modified**: 2 (service_type, current_state)
- **Columns Added**: 1 (contact_phone)
- **Data Loss Risk**: NONE (backup created first)

---

## ✅ Post-Migration Checklist

- [ ] Migration script executed successfully
- [ ] Backup file created and verified
- [ ] contact_phone column exists in schema
- [ ] service_type constraint accepts "Energia Solar"
- [ ] current_state constraint accepts new phone states
- [ ] Schema_migrations table has V58.1 record
- [ ] Test query with contact_phone works
- [ ] V58.1 workflow imported to n8n
- [ ] 3 test paths executed and verified
- [ ] Database monitoring active (check logs)

---

## 📞 Critical Queries Reference

### Check Migration Status
```sql
SELECT version, applied_at, description
FROM schema_migrations
WHERE version = 'V58.1';
```

### Check contact_phone Data
```sql
SELECT
    COUNT(*) as total_conversations,
    COUNT(contact_phone) as with_contact_phone,
    COUNT(*) - COUNT(contact_phone) as without_contact_phone
FROM conversations;
```

### Check service_type Distribution
```sql
SELECT
    service_type,
    COUNT(*) as count
FROM conversations
WHERE service_type IS NOT NULL
GROUP BY service_type
ORDER BY count DESC;
```

### Check State Distribution
```sql
SELECT
    current_state,
    COUNT(*) as count
FROM conversations
GROUP BY current_state
ORDER BY count DESC;
```

---

## 🎯 Success Criteria

✅ **Migration Successful When**:
1. All 3 gaps fixed (contact_phone column, service_type constraint, state constraint)
2. Backup created and validated
3. No constraint violations in existing data
4. Test queries execute without errors
5. V58.1 workflow processes messages correctly
6. Database fields populate as expected (verified in 3 test paths)

---

## 📚 Related Documentation

- **Migration Script**: `scripts/run-migration-v58_1-complete.sh`
- **V58.1 Workflow**: `n8n/workflows/02_ai_agent_conversation_V58_1_UX_REFACTOR_COMPLETE.json`
- **Implementation Report**: `docs/PLAN/V58_1_IMPLEMENTATION_REPORT.md`
- **Quick Start Guide**: `docs/Setups/QUICKSTART.md`
- **Database Schema**: Check with `\d conversations` in psql

---

**Status**: ⏳ READY TO EXECUTE
**Next Step**: Run `./scripts/run-migration-v58_1-complete.sh`
