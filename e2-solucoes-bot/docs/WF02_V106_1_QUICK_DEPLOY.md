# WF02 V106.1 - Quick Deploy Checklist

**Workflow ID**: 9tG2gR6KBt6nYyHT
**Fix**: Multi-route response_text data source correction
**Time**: 5-10 minutes
**Risk**: Very Low (configuration only)

---

## ✅ PRE-REQUISITES

- [ ] V105 routing fix deployed (Update Conversation State before Check If WF06)
- [ ] Workflow URL: http://localhost:5678/workflow/9tG2gR6KBt6nYyHT

---

## 🔧 DEPLOYMENT STEPS

### Step 1: Verify Workflow Structure
- [ ] Open workflow in n8n UI
- [ ] Search for "Send Message with Dates" (Ctrl+F)
- [ ] Search for "Send Message with Slots" (Ctrl+F)
- [ ] Search for "Send WhatsApp Response" or "Send Message"

**Determine scenario**:
- [ ] **Scenario A**: Separate Send nodes exist for WF06 routes (most likely)
- [ ] **Scenario B**: Only ONE Send node exists for all routes

---

## 📋 SCENARIO A: Separate Send Nodes Exist

### A1: Verify WF06 Send Nodes (No Changes Needed)

**Send Message with Dates**:
- [ ] Click node
- [ ] Verify `text` parameter: `{{ $input.first().json.response_text }}` ✅
- [ ] NO CHANGES NEEDED if already correct ✅

**Send Message with Slots**:
- [ ] Click node
- [ ] Verify `text` parameter: `{{ $input.first().json.response_text }}` ✅
- [ ] NO CHANGES NEEDED if already correct ✅

### A2: Fix Normal Flow Send Node

**Send WhatsApp Response**:
- [ ] Click node
- [ ] Find `text` parameter
- [ ] Current value: `{{ $input.first().json.response_text }}` ❌
- [ ] **Change to**: `{{ $node["Build Update Queries"].json.response_text }}` ✅
- [ ] Save node
- [ ] Save workflow

---

## 📋 SCENARIO B: Only ONE Send Node Exists

**See full deployment guide**: `docs/deployment/DEPLOY_WF02_V106_1_COMPLETE_FIX.md` Section B

---

## ✅ VALIDATION TESTS

### Test 1: Normal Flow
```bash
# Send WhatsApp: "oi" → service "5" → complete → "1" (confirmar)
# Expected: Bot sends confirmation message ✅
# Verify: Message has actual content (not undefined) ✅
```
- [ ] Normal flow works ✅
- [ ] No undefined messages ✅

### Test 2: WF06 Next Dates
```bash
# Send WhatsApp: "oi" → service "1" → complete → "1" (agendar)
# Expected: Bot sends message with 3 dates ✅
# Verify: "28/04 (8 horários)" format ✅
# Verify: NOT generic "Escolha um horário disponível:" ❌
```
- [ ] WF06 dates show actual dates ✅
- [ ] Message is NOT generic ✅

### Test 3: WF06 Available Slots
```bash
# Continue from Test 2: send "1" (select first date)
# Expected: Bot sends message with time slots ✅
# Verify: "09:00 - 11:00" format ✅
# Verify: NOT generic "Escolha um horário:" ❌
```
- [ ] WF06 slots show actual times ✅
- [ ] Message is NOT generic ✅

---

## 🚨 ROLLBACK (If Tests Fail)

**Scenario A**:
- [ ] Open workflow
- [ ] Click "Send WhatsApp Response"
- [ ] Change `text` back to: `{{ $input.first().json.response_text }}`
- [ ] Save workflow
- [ ] Investigate issue before retrying

---

## ✅ SUCCESS CRITERIA

- [ ] Normal flow: Messages have actual content (not undefined) ✅
- [ ] WF06 dates: Messages show actual dates with slot counts ✅
- [ ] WF06 slots: Messages show actual time slots ✅
- [ ] No infinite loops ✅
- [ ] All flows complete successfully ✅

---

## 📚 DOCUMENTATION

**Quick Reference**:
- This checklist - Quick deployment steps

**Complete Guide**:
- `docs/deployment/DEPLOY_WF02_V106_1_COMPLETE_FIX.md` - Full deployment with both scenarios

**Root Cause Analysis**:
- `docs/fix/BUGFIX_WF02_V106_1_CRITICAL_WF06_FLOW_BREAK.md` - Why V106 breaks WF06 flows
- `docs/fix/BUGFIX_WF02_V106_RESPONSE_TEXT_ROUTING.md` - V106 incomplete analysis

**Prerequisites**:
- `docs/deployment/DEPLOY_WF02_V105_WF06_ROUTING_FIX.md` - V105 routing fix

---

**Status**: V106.1 quick deployment checklist
**Impact**: Fixes response_text undefined on ALL routes (normal + WF06)
**Critical**: V106.1 correct solution, V106 original breaks WF06 flows
