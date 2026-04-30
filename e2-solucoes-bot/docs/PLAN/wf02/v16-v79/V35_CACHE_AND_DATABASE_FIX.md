# V35 DEFINITIVE FIX - Cache, Database and Execution Issues

**Date**: 2026-01-16
**Version**: V35 - Complete System Fix
**Status**: 🚨 CRITICAL - Multiple System Failures
**Priority**: CRITICAL

---

## 🔴 CRITICAL ISSUES IDENTIFIED

### Issue 1: V34 Code Not Executing
- **Evidence**: V34 shows as active but validation code never runs
- **Missing Logs**: No "V34 COLLECT_NAME STATE" in logs
- **Missing Logs**: No "Bruno" being processed
- **Conclusion**: Code exists but isn't being executed

### Issue 2: Database Connection Error
```bash
psql: error: FATAL: role "e2bot_user" does not exist
```
- **Impact**: Cannot verify conversation state
- **Possible Cause**: Wrong database configuration or container

### Issue 3: Possible Cache Issues
- **Symptom**: Same error persists across versions
- **Hypothesis**: n8n may be caching old workflow code
- **Solution**: Need to force cache clear

---

## ✅ V35 SOLUTION STRATEGY

### Phase 1: Database Fix
1. **Identify correct database credentials**
2. **Fix PostgreSQL connection**
3. **Verify conversation storage**

### Phase 2: Cache Clear
1. **Clear n8n execution cache**
2. **Restart all containers**
3. **Force workflow reload**

### Phase 3: Code Injection at Entry Point
1. **Add logging at the VERY START of code**
2. **Log BEFORE any state logic**
3. **Ensure code execution visibility**

---

## 📋 V35 IMPLEMENTATION PLAN

### Step 1: Fix Database Access
```bash
# Find correct database user
docker exec e2bot-postgres-dev psql -U postgres -l

# Try different user
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_db -c "\du"

# Alternative containers
docker ps | grep postgres
```

### Step 2: Force Cache Clear
```bash
# Stop all containers
docker-compose -f docker/docker-compose-dev.yml down

# Clear n8n data (BE CAREFUL - backs up first)
docker volume ls | grep n8n
# If safe: docker volume rm [n8n_volume]

# Restart clean
docker-compose -f docker/docker-compose-dev.yml up -d
```

### Step 3: V35 Code with Entry Point Logging
```javascript
// V35: IMMEDIATE LOGGING - FIRST LINE OF CODE
console.log('================================');
console.log('V35 CODE EXECUTION CONFIRMED');
console.log('Time:', new Date().toISOString());
console.log('================================');

// Log input immediately
const input = items[0].json;
console.log('V35 INPUT RECEIVED:', JSON.stringify(input).substring(0, 200));

// Log message immediately
const message = input.message || '';
console.log('V35 MESSAGE:', message);

// THEN continue with rest of code...
```

### Step 4: Simplified Name Validation
```javascript
// V35: ULTRA-SIMPLE validation to eliminate complexity
if (currentStage === 'collect_name') {
  console.log('V35: IN COLLECT_NAME - MESSAGE:', message);

  // Just check if it's not a number
  if (message && message.length >= 3 && isNaN(message)) {
    console.log('V35: NAME ACCEPTED:', message);
    // Accept the name
    updateData.lead_name = message;
    responseText = 'Nome aceito! Qual seu telefone?';
    nextStage = 'collect_phone';
  } else {
    console.log('V35: NAME REJECTED:', message);
    responseText = 'Por favor, digite um nome válido.';
    nextStage = 'collect_name';
  }
}
```

---

## 🔧 PYTHON SCRIPT REQUIREMENTS

The V35 script must:
1. **Add logging at the VERY BEGINNING** of the function code
2. **Log before ANY other logic**
3. **Use ultra-simple validation**
4. **Ensure visibility of execution**

### Critical Changes
```python
def add_v35_logging_at_start(code):
    # This MUST be the first thing in the code
    v35_header = '''
console.log('==== V35 EXECUTION START ====');
console.log('V35 Timestamp:', new Date().toISOString());
console.log('V35 Active: YES');

// Log raw input
const rawInput = JSON.stringify(items[0].json);
console.log('V35 Raw Input:', rawInput.substring(0, 500));
'''

    # Insert at the absolute beginning
    return v35_header + '\n' + code
```

---

## 🧪 TESTING PROCEDURE

### Pre-Test: Fix Database
```bash
# Try these users
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_db -c "SELECT 1;"
docker exec e2bot-postgres-dev psql -U e2bot -d e2bot_db -c "SELECT 1;"
docker exec e2bot-postgres-dev psql -U admin -d e2bot_db -c "SELECT 1;"
```

### Pre-Test: Clear Everything
```bash
# 1. Export V34 as backup
# 2. Stop n8n
docker stop e2bot-n8n-dev

# 3. Clear cache (if safe)
docker exec e2bot-n8n-dev rm -rf /home/node/.n8n/cache/*

# 4. Restart
docker start e2bot-n8n-dev
```

### Test Execution
1. Import V35
2. Activate ONLY V35
3. Send "1" to bot
4. **CHECK LOGS IMMEDIATELY**:
```bash
docker logs -f e2bot-n8n-dev 2>&1 | grep V35
```

### Expected First Log
```
==== V35 EXECUTION START ====
V35 Timestamp: 2026-01-16T...
V35 Active: YES
V35 Raw Input: {"message":"1"...
```

If this doesn't appear, the code is NOT executing.

---

## 🚨 TROUBLESHOOTING MATRIX

| Symptom | Likely Cause | Solution |
|---------|--------------|----------|
| No V35 logs at all | Code not in workflow | Re-import V35 |
| V35 init but no execution | Wrong node configuration | Check node type |
| Database error | Wrong credentials | Find correct user |
| Same error across versions | Cache issue | Full restart |
| Works then stops | Memory/resource issue | Check container resources |

---

## 📊 DIAGNOSTIC COMMANDS

### Check All Containers
```bash
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

### Find Database Config
```bash
grep -r "DATABASE\|POSTGRES\|DB_" docker/.env*
cat docker/.env.dev
```

### Monitor All Logs
```bash
# n8n logs
docker logs -f e2bot-n8n-dev 2>&1

# Database logs
docker logs e2bot-postgres-dev 2>&1 | tail -50

# Evolution logs
docker logs e2bot-evolution-dev 2>&1 | tail -50
```

### Check Workflow Execution
```bash
# See last execution details
curl -X GET http://localhost:5678/api/v1/executions/latest \
  -H "Accept: application/json"
```

---

## 🎯 SUCCESS CRITERIA

V35 is working when:
1. ✅ Logs show "V35 EXECUTION START" immediately
2. ✅ Message "Bruno Rosa" appears in V35 logs
3. ✅ Database connection works
4. ✅ Name is accepted and stored
5. ✅ Bot asks for phone number

---

## 🚀 EMERGENCY PLAN

If V35 still doesn't work:

### Option 1: Complete Reset
```bash
docker-compose -f docker/docker-compose-dev.yml down -v
docker-compose -f docker/docker-compose-dev.yml up -d
# Re-import everything from scratch
```

### Option 2: Direct Database Fix
```bash
# Create user if missing
docker exec e2bot-postgres-dev psql -U postgres -c "CREATE USER e2bot_user WITH PASSWORD 'e2bot_pass';"
docker exec e2bot-postgres-dev psql -U postgres -c "GRANT ALL ON DATABASE e2bot_db TO e2bot_user;"
```

### Option 3: Bypass State Machine
Create a simple webhook that just collects data without complex logic.

---

## 📝 NOTES

- The problem seems to be EXECUTION, not logic
- V34 code looks correct but never runs
- Database issues may be preventing state persistence
- Cache may be serving old code

---

**End of V35 Plan - Focus on Execution Visibility**