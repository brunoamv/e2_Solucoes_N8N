# V43 - Next Steps for Testing

**Status**: ✅ V43 Database Migration COMPLETED
**Date**: 2025-03-05
**Database**: e2bot_dev created with all required columns

---

## ✅ What Was Done

### 1. Database Created Successfully
```
Database: e2bot_dev
Tables: 6 (conversations, messages, leads, appointments, rdstation_sync_log, chat_memory)
V43 Columns: All 4 present in conversations table
  ✓ service_id VARCHAR(100)
  ✓ contact_name VARCHAR(255)
  ✓ contact_email VARCHAR(255)
  ✓ city VARCHAR(100)
```

### 2. Docker Configuration Updated
- Created `database/init-e2bot-dev.sh` for automatic database initialization
- Updated `docker-compose-dev.yml` to mount init script
- PostgreSQL container recreated with V43 schema

### 3. Verification Completed
```bash
✅ Database e2bot_dev exists
✅ All 6 tables created
✅ All 4 V43 columns present in conversations
✅ Correct data types and constraints
✅ Indexes and triggers operational
```

---

## 🚀 Next Steps

### Step 1: Start n8n Container

```bash
cd /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot
docker-compose -f docker/docker-compose-dev.yml up -d n8n-dev
```

**Expected Output**:
```
Starting e2bot-n8n-dev ... done
```

### Step 2: Access n8n Interface

Open browser: http://localhost:5678

**What to do**:
1. Check if n8n is running
2. Log in (or continue without auth in dev mode)
3. Navigate to workflows

### Step 3: Activate V41 Workflow

**In n8n Interface**:
1. Find workflow: `02 - AI Agent Conversation V41 (Query Batching Fix)`
2. **Deactivate** any other V2X workflows (V42, V32, V31, etc.)
3. **Activate** V41 workflow
4. Verify it's the only active conversation workflow

**Why V41?**
- V41 is designed to work with V43 database schema
- V41 queries reference: service_id, contact_name, contact_email, city
- V43 database has all these columns ✅

### Step 4: Test Conversation Flow

**Send WhatsApp Messages** (use your test number):

1. **Send**: `oi`
   - **Expected**: Menu with 5 service options

2. **Send**: `1` (Energia Solar)
   - **Expected**: Bot asks for name

3. **Send**: `Bruno Rosa`
   - **Expected**: Bot asks for phone (NOT menu again!)
   - **Critical**: If bot returns to menu, V43 didn't fix the issue

4. **Send**: Your phone number
   - **Expected**: Bot asks for email

5. **Send**: Your email
   - **Expected**: Bot asks for city

6. **Send**: City name
   - **Expected**: Bot asks for confirmation

7. **Continue** conversation flow to completion

### Step 5: Verify Executions

**Check n8n Executions**:
- URL: http://localhost:5678/projects/08qzhIsou3TK6J3Z/executions
- **All executions should show**: `success` status
- **None should be**: `running` (stuck)
- **Execution time**: < 10 seconds

**Success Indicators**:
- ✅ No executions stuck in "running"
- ✅ All show "success" status
- ✅ Conversation flows without looping back to menu
- ✅ Data persists between messages

### Step 6: Verify Database Data

```bash
# Check conversation data
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "
  SELECT
    phone_number,
    contact_name,
    contact_email,
    city,
    collected_data,
    current_state
  FROM conversations
  WHERE phone_number = '5562999887766';  -- Replace with your test number
"
```

**Expected Results**:
```
phone_number   | 5562999887766
contact_name   | Bruno Rosa
contact_email  | bruno@example.com
city           | Goiânia
collected_data | {"additional": "data in JSONB"}
current_state  | (current conversation stage)
```

**Data Verification**:
- ✅ `contact_name` column populated
- ✅ `contact_email` column populated
- ✅ `city` column populated
- ✅ `collected_data` JSONB has additional info
- ✅ No NULL values in expected columns

### Step 7: Check Logs for Errors

```bash
# Watch n8n logs
docker logs -f e2bot-n8n-dev 2>&1 | grep -E 'ERROR|column.*does not exist|CRITICAL'
```

**Expected**: No output (no errors)

**If you see errors**:
- `column "..." does not exist` → V43 columns missing (verify database)
- Other errors → Check n8n workflow configuration

---

## ✅ Success Criteria

### Must Have (Critical)
- [ ] n8n container starts successfully
- [ ] V41 workflow activates without errors
- [ ] Conversation flows without returning to menu after name
- [ ] Executions complete with "success" status (not stuck in "running")
- [ ] Database shows data in V43 columns (contact_name, contact_email, city)
- [ ] No "column does not exist" errors in logs

### Should Have (Important)
- [ ] Execution time < 10 seconds
- [ ] Data persists correctly in both columns and collected_data JSONB
- [ ] CRM sync works (RD Station integration)
- [ ] WhatsApp messages send/receive correctly

### Nice to Have (Optional)
- [ ] Test multiple conversations simultaneously
- [ ] Test all 5 service types
- [ ] Verify appointment scheduling flow

---

## 🔧 Troubleshooting

### Problem: n8n Won't Start

```bash
# Check logs
docker logs e2bot-n8n-dev

# Restart container
docker-compose -f docker/docker-compose-dev.yml restart n8n-dev
```

### Problem: V41 Workflow Not Found

```bash
# Import workflow manually
1. Open n8n: http://localhost:5678
2. Click "Import from File"
3. Select: n8n/workflows/02_ai_agent_conversation_V41_QUERY_BATCHING_FIX.json
4. Activate the imported workflow
```

### Problem: Bot Still Returns to Menu After Name

**Check**:
1. Is V41 workflow active? (not V42 or others)
2. Are V43 columns present in database?
3. Are there errors in n8n logs?

**Verify V43 columns**:
```bash
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "
  SELECT column_name, data_type
  FROM information_schema.columns
  WHERE table_name = 'conversations'
  AND column_name IN ('service_id', 'contact_name', 'contact_email', 'city');
"

# Expected: 4 rows returned
```

### Problem: Executions Stuck in "Running"

**Check PostgreSQL connection**:
```bash
docker exec e2bot-n8n-dev ping -c 1 e2bot-postgres-dev
# Should succeed
```

**Check database exists**:
```bash
docker exec e2bot-postgres-dev psql -U postgres -l | grep e2bot_dev
# Should show e2bot_dev database
```

### Problem: Column Errors Still Appear

**This means V43 migration didn't work**. Recreate:
```bash
./scripts/recreate-postgres-v43.sh
# Type "yes" when prompted
# Wait for completion
# Restart n8n
```

---

## 📊 Testing Checklist

### Pre-Test Verification
- [ ] PostgreSQL container running: `docker ps | grep postgres`
- [ ] Database e2bot_dev exists
- [ ] All 4 V43 columns present in conversations table
- [ ] n8n container running: `docker ps | grep n8n`

### V41 Workflow Test
- [ ] V41 workflow active
- [ ] All other V2X workflows deactivated
- [ ] No errors when activating V41

### Conversation Flow Test
- [ ] Send "oi" → Menu appears
- [ ] Send "1" → Bot asks for name
- [ ] Send "Bruno Rosa" → Bot asks for phone (NOT menu)
- [ ] Send phone → Bot asks for email
- [ ] Send email → Bot asks for city
- [ ] Complete flow → Confirmation received

### Database Verification Test
- [ ] Conversation record created
- [ ] contact_name field populated
- [ ] contact_email field populated
- [ ] city field populated
- [ ] collected_data JSONB has additional info

### Execution Verification Test
- [ ] All executions show "success" status
- [ ] No executions stuck in "running"
- [ ] Execution time < 10 seconds
- [ ] No database errors in logs

---

## 📁 Reference Files

### V43 Documentation
- Plan: `docs/PLAN/V43_DATABASE_MIGRATION.md`
- Summary: `docs/V43_SOLUTION_SUMMARY.md`
- This File: `NEXT_STEPS_V43.md`

### V43 Implementation
- Init Script: `database/init-e2bot-dev.sh`
- Schema: `database/schema.sql` (includes V43 columns)
- Docker Config: `docker/docker-compose-dev.yml`
- Recreation Script: `scripts/recreate-postgres-v43.sh`

### V41 Workflow
- File: `n8n/workflows/02_ai_agent_conversation_V41_QUERY_BATCHING_FIX.json`
- Compatible with V43 database schema ✅

---

## 🎯 Expected Final State

### Infrastructure
```
✅ PostgreSQL: e2bot-postgres-dev running
✅ Database: e2bot_dev with 6 tables
✅ Columns: All 4 V43 columns present
✅ n8n: e2bot-n8n-dev running
✅ Workflow: V41 active
```

### Conversation Flow
```
User: oi
Bot: Menu (5 options)

User: 1
Bot: Asks for name

User: Bruno Rosa
Bot: Asks for phone ← KEY: NOT returning to menu

User: Phone
Bot: Asks for email

User: Email
Bot: Asks for city

User: City
Bot: Asks for confirmation
```

### Database State
```sql
-- Conversation created with all V43 columns populated
SELECT * FROM conversations WHERE phone_number = 'test_number';

Result:
  contact_name: "Bruno Rosa"
  contact_email: "test@example.com"
  city: "Test City"
  collected_data: {additional JSONB data}
  current_state: (conversation stage)
```

### Execution Status
```
All executions: SUCCESS ✅
None stuck in: RUNNING ❌
Time per execution: < 10 seconds
Database errors: NONE
```

---

## ✅ When Everything Works

You'll know V43 is successful when:

1. **Database**: All 4 columns exist and are being populated
2. **Workflow**: V41 runs without "column does not exist" errors
3. **Executions**: Complete with "success" status, not stuck
4. **Conversation**: Flows naturally without looping back to menu
5. **Data**: Persists correctly in both columns and JSONB

**Congratulations! V43 migration complete and working! 🎉**

---

## 📞 Need Help?

### Check These First
1. V43 columns exist: `\d conversations` in PostgreSQL
2. V41 workflow active: Check n8n interface
3. n8n logs: `docker logs e2bot-n8n-dev`
4. PostgreSQL logs: `docker logs e2bot-postgres-dev`

### Common Issues and Solutions
See `docs/PLAN/V43_DATABASE_MIGRATION.md` section "Troubleshooting"

---

**Ready to Test!** 🚀

Start with Step 1 (Start n8n) and follow the checklist.
Good luck! 🍀
