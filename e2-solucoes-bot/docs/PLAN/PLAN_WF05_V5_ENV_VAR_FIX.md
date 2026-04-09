# WF05 V5 - Environment Variable Access Fix Plan

**Date**: 2026-03-31
**Status**: 🚀 **READY FOR IMPLEMENTATION**

---

## 🎯 Executive Summary

WF05 V4.0.4 fails with `Error: access to env vars denied` after Docker configuration changes. This plan provides **two solutions** to resolve the environment variable access issue in the "Validate Availability" node.

---

## 📊 Problem Analysis

### **Error Context**

| Aspect | Details |
|--------|---------|
| **Error** | `Cannot assign to read only property 'name' of object 'Error: access to env vars denied'` |
| **Node** | "Validate Availability" (lines 55-69) |
| **Workflow** | WF05 V4.0.4 (ID: `HZTlBcXKId6bD1En`) |
| **Last Working** | Execution 16329 |
| **First Failure** | Execution 16946 |
| **Trigger** | After adding `/email-templates` volume to docker-compose-dev.yml |

### **Root Cause**

```javascript
// Line 57-63: WF05 V4.0.4 "Validate Availability"
if (!$env.CALENDAR_WORK_START || !$env.CALENDAR_WORK_END || !$env.CALENDAR_WORK_DAYS) {
    console.warn('⚠️  Calendar env vars not configured - skipping validation');
    return {
        ...data,
        validation_status: 'skipped',
        validation_reason: 'env_vars_missing',
        validated_at: new Date().toISOString()
    };
}
```

**The Problem**:
1. ❌ CALENDAR_WORK_START/END/DAYS **DO NOT EXIST** in n8n container environment
2. ❌ n8n security policy **BLOCKS access to `$env` object** when variables are missing
3. ❌ Error occurs **BEFORE the `if` check completes** - can't even test if variables exist

**Evidence**:
```bash
docker exec e2bot-n8n-dev env | grep CALENDAR
# (empty - variables don't exist)
```

---

## 🛠️ Solution Options

### **Option A: Add Environment Variables (RECOMMENDED)**

**Approach**: Add CALENDAR_WORK_* variables to docker-compose-dev.yml

**Pros**:
- ✅ No workflow changes needed
- ✅ Enables actual availability validation (business value)
- ✅ Future-proof for production deployment
- ✅ Follows n8n best practices

**Cons**:
- ⚠️ Requires Docker restart
- ⚠️ Need to define business hours configuration

**Implementation**:

1. **Add to `docker-compose-dev.yml`** (n8n-dev service, line ~60):
```yaml
environment:
  # ... existing variables ...

  # === Calendar Availability Configuration ===
  - CALENDAR_WORK_START=09:00
  - CALENDAR_WORK_END=18:00
  - CALENDAR_WORK_DAYS=1,2,3,4,5  # Monday-Friday (1=Monday, 7=Sunday)
```

2. **Restart Docker**:
```bash
docker-compose -f docker/docker-compose-dev.yml down
docker-compose -f docker/docker-compose-dev.yml up -d
```

3. **Verify**:
```bash
docker exec e2bot-n8n-dev env | grep CALENDAR_WORK
# Expected output:
# CALENDAR_WORK_START=09:00
# CALENDAR_WORK_END=18:00
# CALENDAR_WORK_DAYS=1,2,3,4,5
```

4. **Test WF05**: Execute flow and verify "Validate Availability" passes

---

### **Option B: Graceful Fallback (FALLBACK)**

**Approach**: Modify "Validate Availability" node to handle missing env vars without accessing `$env`

**Pros**:
- ✅ No Docker changes needed
- ✅ Workflow works immediately
- ✅ Graceful degradation (skips validation if not configured)

**Cons**:
- ❌ No actual availability validation (business risk)
- ❌ Loses feature functionality
- ❌ Not production-ready

**Implementation** (WF05 V5):

```javascript
// V5: Validate Availability with Try-Catch Protection
try {
    // ===== TRY TO ACCESS ENV VARS SAFELY =====
    const workStart = process.env.CALENDAR_WORK_START;
    const workEnd = process.env.CALENDAR_WORK_END;
    const workDays = process.env.CALENDAR_WORK_DAYS;

    // If any variable is missing, skip validation
    if (!workStart || !workEnd || !workDays) {
        console.warn('⚠️  V5: Calendar env vars not configured - skipping validation');
        return {
            ...data,
            validation_status: 'skipped',
            validation_reason: 'env_vars_missing_v5',
            validated_at: new Date().toISOString()
        };
    }

    // ===== VALIDATION LOGIC (unchanged) =====
    // ... rest of validation code ...

} catch (error) {
    // ===== HANDLE ENV ACCESS DENIAL =====
    console.error('⚠️  V5: Cannot access environment variables:', error.message);
    return {
        ...data,
        validation_status: 'skipped',
        validation_reason: 'env_access_denied',
        error_details: error.message,
        validated_at: new Date().toISOString()
    };
}
```

**Key Changes**:
1. ✅ Use `process.env.CALENDAR_WORK_*` instead of `$env.CALENDAR_WORK_*`
2. ✅ Wrap entire node logic in try-catch
3. ✅ Graceful fallback if env vars missing or inaccessible
4. ✅ Log reason for skipping validation

---

## 🎯 Recommendation

**Use Option A (Add Environment Variables)** because:

1. **Business Value**: Enables actual availability validation (prevents appointments outside business hours)
2. **Production Ready**: Required for production deployment anyway
3. **Best Practices**: Follows n8n environment variable patterns
4. **No Workflow Changes**: WF05 V4.0.4 works as-is once env vars are added

**Option B is only for**:
- Emergency hotfix if can't restart Docker
- Development environments where availability validation is not needed

---

## 📦 Deliverables

### **Option A Deliverables**:
1. ✅ Updated `docker-compose-dev.yml` with CALENDAR_WORK_* variables
2. ✅ Verification script to test env vars
3. ✅ Documentation update in CLAUDE.md

### **Option B Deliverables** (if needed):
1. ✅ `scripts/generate-workflow-wf05-v5-env-fallback.py` - Python generator
2. ✅ `n8n/workflows/05_appointment_scheduler_v5_env_fallback.json` - Generated workflow
3. ✅ `docs/DEPLOY_WF05_V5_ENV_FALLBACK.md` - Deployment instructions

---

## 🚀 Implementation Steps

### **For Option A (Recommended)**:

```bash
# 1. Update docker-compose-dev.yml (add CALENDAR_WORK_* to n8n-dev environment)

# 2. Restart Docker
docker-compose -f docker/docker-compose-dev.yml down
docker-compose -f docker/docker-compose-dev.yml up -d

# 3. Verify environment variables
docker exec e2bot-n8n-dev env | grep CALENDAR_WORK

# 4. Test WF05 V4.0.4
# - Trigger flow with service 1 or 3
# - Verify "Validate Availability" node executes successfully
# - Check execution logs for validation results

# 5. Monitor execution 16947+ for success
```

### **For Option B (Fallback)**:

```bash
# 1. Generate WF05 V5
python3 scripts/generate-workflow-wf05-v5-env-fallback.py

# 2. Import to n8n
# http://localhost:5678 → Import → 05_appointment_scheduler_v5_env_fallback.json

# 3. Test
# - Trigger flow
# - Verify "Validate Availability" skips gracefully
# - Check logs for "validation_status: 'skipped'"

# 4. Deploy (if Option A fails)
# - Deactivate V4.0.4
# - Activate V5
# - Monitor executions
```

---

## 🧪 Testing Validation

### **Success Criteria**:

| Test | Expected Result |
|------|-----------------|
| **Env Vars Present** | `docker exec e2bot-n8n-dev env \| grep CALENDAR_WORK` shows 3 variables |
| **WF05 Execution** | No "access to env vars denied" error |
| **Validation Node** | Executes successfully with `validation_status: 'valid'` or `'skipped'` |
| **Business Hours** | Appointments only allowed 09:00-18:00 Monday-Friday |
| **Outside Hours** | Returns `validation_status: 'invalid'` with reason |

### **Test Cases**:

```javascript
// Test 1: Valid appointment (Tuesday 10:00)
// Expected: validation_status: 'valid'

// Test 2: Outside hours (Tuesday 20:00)
// Expected: validation_status: 'invalid', reason: 'outside_work_hours'

// Test 3: Weekend (Saturday 10:00)
// Expected: validation_status: 'invalid', reason: 'outside_work_days'

// Test 4: Missing env vars (Option B only)
// Expected: validation_status: 'skipped', reason: 'env_vars_missing_v5'
```

---

## 📚 Documentation Updates

### **CLAUDE.md**:
```markdown
## 🔧 Environment Variables

**Calendar Availability** (WF05):
- CALENDAR_WORK_START=09:00 (business hours start)
- CALENDAR_WORK_END=18:00 (business hours end)
- CALENDAR_WORK_DAYS=1,2,3,4,5 (Monday-Friday, 1=Monday, 7=Sunday)
```

### **docker-compose-dev.yml**:
```yaml
# === Calendar Availability Configuration (WF05) ===
- CALENDAR_WORK_START=09:00
- CALENDAR_WORK_END=18:00
- CALENDAR_WORK_DAYS=1,2,3,4,5  # Monday-Friday
```

---

## ⚠️ Risks and Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Docker restart downtime** | Medium | 100% | Schedule during off-hours, <2min downtime |
| **Env var misconfiguration** | High | Low | Verification script, test cases |
| **Business hours too restrictive** | Low | Medium | Document configuration, easy to adjust |
| **Option B loses validation** | High | N/A | Only use as emergency fallback |

---

## 🎯 Success Metrics

- ✅ WF05 executes without "access to env vars denied" error
- ✅ Availability validation works for business hours (Option A)
- ✅ All test cases pass
- ✅ No regression in WF05 → WF07 integration

---

## 🔄 Rollback Plan

### **If Option A Fails**:
1. Remove CALENDAR_WORK_* variables from docker-compose-dev.yml
2. Restart Docker
3. Deploy Option B (WF05 V5 with graceful fallback)

### **If Option B Fails**:
1. Restore WF05 V3.6 (last known stable)
2. Investigate n8n security policy changes
3. Contact n8n support for `$env` access guidance

---

## 📋 Next Steps

1. **Immediate**: Implement Option A (add env vars to Docker)
2. **Verify**: Test WF05 V4.0.4 with new env vars
3. **Document**: Update CLAUDE.md with env var configuration
4. **Generate Option B** (only if Option A fails): Create WF05 V5 with fallback logic

---

**Status**: ✅ **PLAN COMPLETE - READY FOR IMPLEMENTATION**
**Recommended**: **Option A (Add Environment Variables)**
**Estimated Time**: 15 minutes (5min config + 2min restart + 8min test)
