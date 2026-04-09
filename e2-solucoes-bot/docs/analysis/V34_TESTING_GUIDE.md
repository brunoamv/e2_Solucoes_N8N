# V34 NAME VALIDATION - COMPREHENSIVE TESTING GUIDE

## 🎯 Testing Objectives

1. **Verify name acceptance** - "Bruno Rosa" must be accepted
2. **Validate error handling** - Short names must be rejected properly
3. **Confirm state transitions** - Flow must continue after name acceptance
4. **Ensure no regression** - Other states must still work

---

## 🧪 Test Scenarios

### Scenario 1: Valid Name Acceptance ✅
**Input Sequence**:
```
You: 1
Bot: Qual seu nome completo?
You: Bruno Rosa
Bot: [Should ask for phone]
```

**Expected Logs**:
```
V34: Name validation PASSED
V34: Name accepted successfully: Bruno Rosa
V34: Moving to collect_phone state
```

**Success**: Bot accepts name and asks for phone

---

### Scenario 2: Single Name Acceptance ✅
**Input Sequence**:
```
You: João
Bot: [Should ask for phone]
```

**Expected**: Single names with 3+ chars are valid

---

### Scenario 3: Name with Accents ✅
**Input Sequence**:
```
You: José André
Bot: [Should ask for phone]
```

**Expected**: Portuguese accents are accepted

---

### Scenario 4: Short Name Rejection ❌
**Input Sequence**:
```
You: Jo
Bot: Por favor, informe um nome válido com pelo menos 3 letras
```

**Expected Logs**:
```
V34: Name too short (less than 3 chars)
V34: Name rejected, staying in collect_name state
```

---

### Scenario 5: Number-Only Rejection ❌
**Input Sequence**:
```
You: 12345
Bot: Por favor, informe um nome válido com pelo menos 3 letras
```

**Expected**: Pure numbers are rejected as names

---

### Scenario 6: Error Recovery 🔄
**Input Sequence**:
```
You: ab        (rejected - too short)
You: 123       (rejected - only numbers)
You: @#$       (rejected - invalid chars)
You: Bruno     (ACCEPTED)
Bot: [Should ask for phone]
```

**Expected**: After multiple errors, valid name is accepted

---

## 📊 Test Matrix

| Test Case | Input | Expected Result | Status |
|-----------|-------|-----------------|---------|
| Valid full name | "Bruno Rosa" | ✅ Accept | Test |
| Single name | "Maria" | ✅ Accept | Test |
| Name with accent | "José" | ✅ Accept | Test |
| Two chars | "Jo" | ❌ Reject | Test |
| Only numbers | "123" | ❌ Reject | Test |
| Special chars | "@#$" | ❌ Reject | Test |
| Mixed valid | "Ana123" | ✅ Accept | Test |
| Long name | "Francisco Silva Santos" | ✅ Accept | Test |

---

## 🔍 Monitoring Commands

### Real-time V34 Monitoring
```bash
docker logs -f e2bot-n8n-dev 2>&1 | grep -E "V34|collect_name"
```

### Check Specific Name Test
```bash
docker logs e2bot-n8n-dev 2>&1 | grep -A10 -B5 "Bruno Rosa"
```

### Database Verification
```bash
docker exec e2bot-postgres-dev psql -U e2bot_user -d e2bot_db \
  -c "SELECT lead_id, current_state, collected_data FROM conversations ORDER BY updated_at DESC LIMIT 1;"
```

---

## 📝 Test Execution Steps

### 1. Pre-Test Setup
```bash
# Ensure V34 is active
./scripts/validate-v34-fix.sh

# Clear old conversation (replace with your number)
docker exec e2bot-postgres-dev psql -U e2bot_user -d e2bot_db \
  -c "DELETE FROM conversations WHERE lead_id = '5562XXXXXXXXX';"
```

### 2. Execute Test Cases
- Open WhatsApp
- Send each test case
- Document results

### 3. Verify Logs
```bash
# After each test, check logs
docker logs e2bot-n8n-dev 2>&1 | tail -50 | grep V34
```

### 4. Record Results
Update the test matrix with Pass/Fail status

---

## ✅ Validation Checklist

### Pre-Import
- [ ] V34 workflow file exists
- [ ] V33 backup created
- [ ] n8n accessible

### Import Process
- [ ] V34 imported successfully
- [ ] V33 deactivated
- [ ] V34 activated (green)
- [ ] Cache cleared

### Functional Tests
- [ ] "Bruno Rosa" accepted
- [ ] "João" accepted (single name)
- [ ] "Jo" rejected (too short)
- [ ] "123" rejected (only numbers)
- [ ] Phone request after valid name
- [ ] Email request after phone
- [ ] Complete flow works

### Log Verification
- [ ] V34 initialization confirmed
- [ ] Name validation logs present
- [ ] No "Opção inválida" for valid names
- [ ] State transitions logged

---

## 🚨 Common Issues & Solutions

### Issue: "Opção inválida" still appears
**Solution**:
1. Verify V34 is the ONLY active workflow
2. Check logs for V34 initialization
3. Restart n8n if needed

### Issue: V34 logs not appearing
**Solution**:
1. V34 might not be imported
2. V34 might not be activated
3. Wrong workflow might be active

### Issue: Name accepted but flow breaks
**Solution**:
1. Check phone validation state
2. Verify database state transitions
3. Look for errors after name acceptance

---

## 📈 Performance Metrics

### Expected Response Times
- Name validation: < 100ms
- State transition: < 200ms
- Database update: < 50ms
- Total response: < 500ms

### Success Metrics
- Name acceptance rate: > 95% for valid names
- Error recovery: 100% after valid input
- State persistence: 100% reliability

---

## 🎉 Test Complete Confirmation

You know testing is successful when:
1. ✅ All valid names in test matrix pass
2. ✅ All invalid names properly rejected with clear message
3. ✅ Complete conversation flow works end-to-end
4. ✅ No regression in other states
5. ✅ Logs show V34 validation working

---

**Remember**: The key test is that "Bruno Rosa" must be ACCEPTED!