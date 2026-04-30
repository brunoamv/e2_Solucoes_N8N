# 🚨 Evolution API v2.2.3 Critical Issue Documentation

> **Issue Period**: 2024-12-20 to 2025-01-06
> **Status**: ✅ RESOLVED
> **Resolution**: Migration to Evolution API v2.3.7
> **Impact Level**: CRITICAL - System completely non-functional

---

## Executive Summary

Evolution API v2.2.3 contained a critical bug in phone number extraction that made the WhatsApp bot system completely non-functional. The issue was resolved by migrating to Evolution API v2.3.7 and updating all workflow connections to use the new data structure.

## Problem Description

### Root Cause
Evolution API v2.2.3 had a malformed `remoteJid` field that duplicated country codes and appended WhatsApp domain suffixes, making it impossible to extract clean phone numbers for database operations.

### Symptoms
1. **Phone Number Extraction Failure**
   - `remoteJid` field contained: `55629817554855629817@s.whatsapp.net`
   - Notice the duplicated country code: `5562981755485` + `5629817`
   - Expected format: `5562981755485`

2. **Workflow Failures**
   - `phone_number` variable was undefined in all workflows
   - Database operations failed due to missing phone_number
   - State machine couldn't track conversations
   - Lead collection was impossible

3. **System Impact**
   - 100% failure rate for all incoming messages
   - No conversation could progress beyond initial reception
   - Complete system outage for WhatsApp interactions

## Technical Analysis

### Data Structure Comparison

#### Evolution API v2.2.3 (BROKEN)
```json
{
  "instance": {
    "instanceName": "e2-solucoes-bot",
    "status": "open"
  },
  "data": {
    "key": {
      "remoteJid": "55629817554855629817@s.whatsapp.net",  // ❌ Malformed
      "fromMe": false,
      "id": "msg_id_123"
    },
    "message": {
      "conversation": "Oi"
    }
  }
}
```

#### Evolution API v2.3.7 (WORKING)
```json
{
  "instance": {
    "instanceName": "e2-solucoes-bot",
    "status": "open"
  },
  "data": {
    "key": {
      "remoteJid": "5562981755485@s.whatsapp.net",  // ✅ Correct format
      "fromMe": false,
      "id": "msg_id_123"
    },
    "senderPn": "5562981755485",  // ✅ New clean field
    "message": {
      "conversation": "Oi"
    }
  }
}
```

### Field Extraction Issues

#### v2.2.3 Problems
```javascript
// Attempted extraction methods that ALL FAILED:
const phone1 = json.data.key.remoteJid.split('@')[0];
// Result: "55629817554855629817" (duplicated country code)

const phone2 = json.data.key.remoteJid.replace('@s.whatsapp.net', '');
// Result: "55629817554855629817" (still duplicated)

const phone3 = json.data.key.remoteJid.match(/^(\d+)@/)?.[1];
// Result: "55629817554855629817" (same issue)
```

#### v2.3.7 Solution
```javascript
// Clean extraction from new field:
const phone = json.data.senderPn;
// Result: "5562981755485" ✅ Perfect!

// Fallback for compatibility:
const phoneAlt = json.data.key.remoteJid.split('@')[0];
// Result: "5562981755485" ✅ Also works in v2.3.7
```

## Resolution Steps

### 1. Docker Container Update
```bash
# Stop old container
docker stop e2bot-evolution

# Remove old image (atendai repository deprecated)
docker rmi atendai/evolution-api:v2.2.3

# Pull new official image
docker pull evoapicloud/evolution-api:latest

# Update docker-compose-dev.yml
# FROM: image: atendai/evolution-api:v2.2.3
# TO:   image: evoapicloud/evolution-api:latest
```

### 2. Workflow Updates
All workflows were updated to use the new data structure:

#### Workflow 01 - Main WhatsApp Handler
```javascript
// Before (v2.2.3):
const phoneNumber = $json.data?.key?.remoteJid?.split('@')[0] || '';

// After (v2.3.7):
const phoneNumber = $json.data?.senderPn ||
                   $json.data?.key?.remoteJid?.split('@')[0] || '';
```

#### Workflow 02 - AI Agent Conversation
Updated to receive phone_number from proper data flow instead of trying to extract it again.

### 3. Data Flow Corrections
Fixed workflow connections to ensure phone_number propagates through the entire flow:
- Main Handler → Validate Phone Number → Check Conversation → AI Agent
- Each step now properly passes phone_number to the next

## Migration Guide

### For Developers
1. **Update Docker Image**
   ```bash
   cd /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot
   docker-compose -f docker/docker-compose-dev.yml pull evolution-api
   docker-compose -f docker/docker-compose-dev.yml up -d evolution-api
   ```

2. **Import Fixed Workflows**
   - Open n8n UI (http://localhost:5678)
   - Delete existing workflows (backup first!)
   - Import fixed versions from `n8n/workflows/`
   - Verify connections match documented flow

3. **Test Phone Extraction**
   ```bash
   # Send test message via WhatsApp
   # Check n8n execution logs for phone_number variable
   # Verify it's in format: 5562XXXXXXXXX
   ```

### For Operations
1. **Monitor After Migration**
   - Check Evolution API logs: `docker logs e2bot-evolution`
   - Verify webhook delivery to n8n
   - Confirm phone numbers are being extracted correctly

2. **Validation Checklist**
   - [ ] Evolution API v2.3.7 running
   - [ ] Webhook connected to n8n
   - [ ] Phone numbers extracting correctly
   - [ ] Database storing conversations
   - [ ] State machine progressing

## Lessons Learned

### 1. Version Dependency Management
- Always test third-party API updates in staging first
- Document exact version requirements in docker-compose
- Keep rollback procedures ready

### 2. Data Structure Validation
- Add defensive programming for field extraction
- Implement fallback mechanisms for data access
- Log data structures for debugging

### 3. Testing Requirements
- E2E tests should validate entire data flow
- Monitor critical fields like phone_number
- Set up alerts for undefined critical variables

## Prevention Measures

### Implemented Safeguards
1. **Multiple Extraction Methods**
   ```javascript
   // Primary method
   const phone = json.data?.senderPn;

   // Fallback method
   if (!phone) {
     phone = json.data?.key?.remoteJid?.split('@')[0];
   }

   // Validation
   if (!phone || !phone.match(/^55\d{10,11}$/)) {
     throw new Error('Invalid phone number format');
   }
   ```

2. **Version Pinning**
   ```yaml
   # docker-compose-dev.yml
   evolution-api:
     image: evoapicloud/evolution-api:v2.3.7  # Pin specific version
     # NOT: image: evoapicloud/evolution-api:latest
   ```

3. **Monitoring Setup**
   - Added health checks for Evolution API
   - Phone number validation in workflow
   - Alerts for undefined variables

## Related Documentation

- **Main Context**: `/CLAUDE.md`
- **Workflow Fixes**: `/docs/PLAN/workflow_02_phone_fix_report.md`
- **JSON Import Issues**: `/docs/PLAN/workflow_json_fix_analysis.md`
- **Fix Scripts**: `/scripts/fix-*.py`

## Support Resources

### Evolution API
- **GitHub**: https://github.com/EvolutionAPI/evolution-api
- **Docs**: https://docs.evolution-api.com
- **Discord**: Community support channel
- **Current Version**: v2.3.7 (as of 2025-01-06)

### Internal
- **Lead Developer**: Check git history for fix implementations
- **Testing Guide**: `/docs/validation/EVOLUTION_API_VALIDATION.md`

---

## Appendix: Error Logs

### Sample v2.2.3 Error
```
ERROR: Cannot read properties of undefined (reading 'phone_number')
  at workflow_02_ai_agent_conversation
  at node: Update Conversation State

SQL Query Failed:
  UPDATE conversations SET current_state = 'greeting'
  WHERE phone_number = 'undefined'
```

### Sample v2.3.7 Success
```
SUCCESS: Phone extracted: 5562981755485
SUCCESS: Conversation updated for phone: 5562981755485
SUCCESS: Lead created with phone: 5562981755485
```

---

**Document Version**: 1.0
**Last Updated**: 2025-01-06
**Status**: ✅ Issue Resolved