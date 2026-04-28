# WF02 V111 - Database Row Locking Quick Deploy

**Version**: V111 Database State Race Condition Fix
**Fix**: Prevents stale state processing via PostgreSQL row locking
**Time**: ~10 minutes
**Status**: 🔴 CRITICAL FIX

---

## 🎯 What V111 Fixes

**Problem**: WF06 HTTP Request never executes because workflow processes STALE database state

**Root Cause**: Race condition - user sends messages faster than database commits updates
- First execution reads old state before previous commit completes
- Check If WF06 evaluates with wrong next_stage → FALSE path → No HTTP Request

**Solution**: Add PostgreSQL row locking to prevent concurrent executions reading same conversation

---

## 🚀 Quick Deploy (10 minutes)

### 1. Open Workflow in n8n UI
```
URL: http://localhost:5678/workflow/9tG2gR6KBt6nYyHT
```

### 2. Find "Build SQL Queries" Node
- Type: Code (JavaScript)
- Location: Early in workflow (after Prepare Phone Formats)

### 3. Modify query_details SQL

**Find this code (around line 30)**:
```javascript
// Query para buscar detalhes da conversa
const query_details = `
  SELECT
    *,
    COALESCE(state_machine_state,
      CASE current_state
        WHEN 'novo' THEN 'greeting'
        WHEN 'identificando_servico' THEN 'service_selection'
        WHEN 'coletando_dados' THEN 'collect_name'
        WHEN 'agendando' THEN 'scheduling'
        WHEN 'handoff_comercial' THEN 'handoff_comercial'
        WHEN 'concluido' THEN 'completed'
        ELSE 'greeting'
      END
    ) as state_for_machine
  FROM conversations
  WHERE phone_number IN ('${escapeSql(phone_with_code)}', '${escapeSql(phone_without_code)}')
  ORDER BY updated_at DESC
  LIMIT 1
`.trim();
```

**Replace with this (ADD FOR UPDATE SKIP LOCKED)**:
```javascript
// Query para buscar detalhes da conversa
const query_details = `
  SELECT
    *,
    COALESCE(state_machine_state,
      CASE current_state
        WHEN 'novo' THEN 'greeting'
        WHEN 'identificando_servico' THEN 'service_selection'
        WHEN 'coletando_dados' THEN 'collect_name'
        WHEN 'agendando' THEN 'scheduling'
        WHEN 'handoff_comercial' THEN 'handoff_comercial'
        WHEN 'concluido' THEN 'completed'
        ELSE 'greeting'
      END
    ) as state_for_machine
  FROM conversations
  WHERE phone_number IN ('${escapeSql(phone_with_code)}', '${escapeSql(phone_without_code)}')
  ORDER BY updated_at DESC
  LIMIT 1
  FOR UPDATE SKIP LOCKED
`.trim();
```

**Critical Change**: Add `FOR UPDATE SKIP LOCKED` before `.trim()`

### 4. Save Changes
1. Click **"Save"** button (node)
2. Click **"Save"** button (workflow)

### 5. Add V111 Version Logging
**Optional but recommended**: Add version logging after query_details definition:

```javascript
// After query_details definition, add:
console.log('=== V111 DATABASE ROW LOCKING ENABLED ===');
console.log('V111: FOR UPDATE SKIP LOCKED added to query_details');
```

---

## 🧪 Test (5 minutes)

### Test 1: Rapid Message Scenario
```bash
# Send 3 messages very quickly (< 1 second apart):
# 1. "cocal-go" (city)
# 2. "1" (agendar)
# 3. "test"

# Expected V111 Behavior:
# - Only first message fully processes
# - Messages 2 and 3 might get "Processando mensagem anterior..." OR wait in queue
# - NO stale state processing
# - NO V110 error messages for intermediate states
```

### Test 2: Normal Flow (Baseline)
```bash
# Send messages with 2-3 second gaps:
# 1. "oi" → Wait 2s
# 2. Complete states 1-7 → Wait 2s each
# 3. "1" (agendar) → Wait 2s
# 4. Should show dates successfully

# Expected V111 Behavior:
# - All messages process normally
# - No "Processando" messages
# - Dates appear correctly
# - WF06 HTTP Request executes
```

### Test 3: WF06 Integration
```bash
# Complete flow to WF06 trigger:
# Service 1 (Solar) → "1" (confirmar) → Should trigger WF06

# Expected V111 Behavior:
# ✅ Check If WF06 Next Dates evaluates TRUE
# ✅ HTTP Request - Get Next Dates executes
# ✅ User receives dates within 2-3 seconds
# ✅ No stale state processing logged
```

### Database Check
```sql
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT phone_number, state_machine_state,
             collected_data->'current_stage' as stage
      FROM conversations
      WHERE phone_number = '556181755748'
      ORDER BY updated_at DESC LIMIT 1;"
```

**Expected**: `state_machine_state` and `stage` always match (no stale data)

### Log Check
```bash
docker logs -f e2bot-n8n-dev 2>&1 | grep -E "V111:|V110: Current → Next:"
```

**Expected**:
```
V111: DATABASE ROW LOCKING ENABLED  ✅
V110: Current → Next: confirmation → trigger_wf06_next_dates  ✅
```

**NOT Expected**:
```
V110: Current → Next: collect_city → confirmation  ❌ (stale state)
```

---

## ✅ Success Criteria

- ✅ No stale state processing in logs
- ✅ WF06 HTTP Request executes when user types "1" at confirmation
- ✅ Database state always reflects most recent completed execution
- ✅ Rapid messages handled gracefully (queued or informed to wait)
- ✅ Normal message timing (2-3 seconds) works perfectly

---

## 🔄 Rollback (if needed)

If V111 causes issues:

1. Open workflow: http://localhost:5678/workflow/9tG2gR6KBt6nYyHT
2. Find "Build SQL Queries" node
3. Remove `FOR UPDATE SKIP LOCKED` from query_details
4. Save workflow

**Note**: Rollback returns to V110 state - race condition persists but V110 error handling protects user experience.

---

## 📚 Detailed Documentation

- **Complete Analysis**: `docs/fix/BUGFIX_WF02_V111_DATABASE_STATE_RACE_CONDITION.md`
- **V110 Root Cause**: `docs/fix/BUGFIX_WF02_V110_EXECUTION_9045_COMPLETE_ROOT_CAUSE.md`
- **Active Workflow**: `/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/wk02_v102_1.json`

---

## 🔍 How Row Locking Works

**FOR UPDATE**:
- Locks the conversation row until transaction commits
- Prevents other executions from reading the same row simultaneously
- Ensures only ONE workflow execution processes a conversation at a time

**SKIP LOCKED**:
- If row is already locked (another execution in progress), query returns empty result
- Allows workflow to gracefully handle concurrent message attempts
- No waiting/blocking - immediate response to user

**Result**:
- Sequential message processing per conversation
- No race conditions
- No stale state scenarios
- Clean error handling for rapid messages

---

**Created**: 2026-04-28
**Status**: ✅ READY FOR DEPLOYMENT
**Risk Level**: LOW (PostgreSQL row locking is well-tested and reliable)
**Estimated Implementation Time**: 10 minutes
**Testing Time**: 5 minutes
