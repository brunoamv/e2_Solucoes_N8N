# BUGFIX WF02 V103 - Phone Number Preservation in WF06 Flow

**Date**: 2026-04-27
**Workflow ID**: 9tG2gR6KBt6nYyHT
**Execution**: 8427
**Problem**: After removing parallel connection, `phone_number` not reaching "Send WhatsApp Response" in WF06 flow
**Root Cause**: Data flow broken when parallel path was removed

---

## 🐛 PROBLEM ANALYSIS

### User Report
```
"Estamos quase lá, com a retirada das conexoes dos nodes (Merge WF06 Next Dates with User Data)
e (Get Conversation Details) para cortar o loop do state machine eu perdi o
{{ $input.first().json.phone_number }} no node Send WhatsApp Response"
```

### Error Message
```
Problem in node 'Send WhatsApp Response'
Bad request - please check your parameters
```

### Root Cause

**Before V103** (parallel connection existed):
```
Get Conversation Details
  ├─→ State Machine Logic
  │   └─→ Build Update Queries (has phone_number)
  │
  └─→ Merge WF06 Next Dates (parallel path - REMOVED)
      └─→ Build WF06 Response Message
          └─→ Send WhatsApp Response
              → $input.first().json.phone_number ✅ (from Merge)
```

**After V103** (parallel connection removed):
```
State Machine Logic
  └─→ Build Update Queries (has phone_number)
      └─→ WF06 HTTP Request
          └─→ Prepare WF06 Next Dates Data
              └─→ Merge WF06 Next Dates with User Data
                  └─→ Build WF06 Response Message
                      └─→ Send WhatsApp Response
                          → $input.first().json.phone_number ❌ (NOT in Build WF06 output!)
```

### Data Flow Analysis

**Build WF06 Response Message V102** currently outputs:
```javascript
return {
  json: {
    phone_number: input.phone_number,      // ✅ Has phone_number
    response_text: responseText,            // ✅ Has response_text
    date_suggestions: dates                 // ✅ Has dates
  }
};
```

**But `input.phone_number` comes from Merge WF06**, which gets it from:
- **Prepare WF06 Next Dates Data** → which gets it from `$node["Build Update Queries"].json`

**The chain is**:
1. Build Update Queries → has `phone_number` ✅
2. WF06 HTTP Request → LOSES phone_number ❌
3. Prepare WF06 → gets from `$node["Build Update Queries"].json` ✅
4. Merge WF06 → merges WF06 data + user data ✅
5. Build WF06 Response → should have phone_number ✅
6. Send WhatsApp → reads from $input ✅

**Issue**: Somewhere in this chain, phone_number is being lost!

---

## ✅ SOLUTION V103.1 - Preserve Phone Number Through Chain

### Option 1: Update Build WF06 Response Message (RECOMMENDED)

**Problem**: Build WF06 Response might not be receiving phone_number from Merge

**Fix**: Add explicit fallback chain in Build WF06 Response Message

```javascript
// WF02 V103.1 - Build WF06 Response Message with Phone Preservation
const input = $input.first().json;
const dates = input.wf06_next_dates || [];

console.log('=== BUILD WF06 RESPONSE MESSAGE V103.1 ===');
console.log('Input keys:', Object.keys(input));
console.log('Input phone_number:', input.phone_number);
console.log('WF06 dates count:', dates.length);

// CRITICAL: Extract phone_number with fallback chain
const phoneNumber = input.phone_number
                 || input.phone_with_code
                 || input.phone_without_code
                 || $node["Build Update Queries"].json.phone_number
                 || $node["Build Update Queries"].json.phone_with_code;

console.log('🔍 Phone number resolved:', phoneNumber);

if (!phoneNumber) {
  console.error('❌ CRITICAL: No phone_number found in input!');
  console.error('Available input:', JSON.stringify(input, null, 2));
}

// Handle empty calendar
if (!dates || dates.length === 0) {
  console.log('⚠️ No dates available from WF06');
  return {
    json: {
      phone_number: phoneNumber,
      response_text: '⚠️ Não encontramos horários disponíveis no momento.\\n\\n📞 Entre em contato: (62) 3092-2900'
    }
  };
}

// Build date options message
let dateOptions = '';
dates.forEach((dateObj, index) => {
  const number = index + 1;
  const qualityEmoji = dateObj.quality === 'high' ? '✨' :
                      dateObj.quality === 'medium' ? '📅' : '⚠️';
  dateOptions += `${number}️⃣ *${dateObj.display}*\\n   🕐 ${dateObj.total_slots} horários livres ${qualityEmoji}\\n\\n`;
});

const responseText = `📅 *Agendar Visita Técnica*\\n\\n` +
                    `📆 *Próximas datas disponíveis:*\\n\\n` +
                    dateOptions +
                    `💡 *Escolha uma opção (1-3)*\\n` +
                    `_Digite o número da data desejada_`;

console.log('✅ Response message built successfully');
console.log('✅ Phone number:', phoneNumber);
console.log('Message length:', responseText.length);

return {
  json: {
    phone_number: phoneNumber,           // ✅ With fallback chain
    response_text: responseText,
    date_suggestions: dates
  }
};
```

### Option 2: Update Merge WF06 Next Dates (ALTERNATIVE)

**Ensure Merge node** explicitly passes phone_number:

```javascript
// Merge WF06 Next Dates with User Data
const wf06Data = $input.first().json;
const userData = $node["Build Update Queries"].json;

console.log('=== MERGE WF06 V103.1 ===');
console.log('WF06 data keys:', Object.keys(wf06Data));
console.log('User data keys:', Object.keys(userData));

return {
  json: {
    // WF06 calendar data
    wf06_next_dates: wf06Data.dates_with_availability || [],

    // User data - EXPLICIT phone_number preservation
    phone_number: userData.phone_number || userData.phone_with_code,
    phone_with_code: userData.phone_with_code,
    phone_without_code: userData.phone_without_code,

    // Other user data
    lead_name: userData.lead_name,
    email: userData.email,
    city: userData.city,
    service_type: userData.service_type,
    conversation_id: userData.conversation_id
  }
};
```

### Option 3: Update Prepare WF06 Next Dates Data (COMPREHENSIVE)

**Ensure Prepare node** passes phone_number to Merge:

```javascript
// Prepare WF06 Next Dates Data V103.1
const wf06Response = $input.first().json;
const userData = $node["Build Update Queries"].json;

console.log('=== PREPARE WF06 NEXT DATES V103.1 ===');
console.log('WF06 response:', JSON.stringify(wf06Response, null, 2));
console.log('User data phone:', userData.phone_number);

// Extract dates from WF06 response
const dates = wf06Response.dates_with_availability || [];

return {
  json: {
    // WF06 data
    dates_with_availability: dates,

    // CRITICAL: Pass phone_number from userData
    phone_number: userData.phone_number,
    phone_with_code: userData.phone_with_code,
    phone_without_code: userData.phone_without_code,

    // Other user context
    lead_name: userData.lead_name,
    email: userData.email,
    service_type: userData.service_type
  }
};
```

---

## 🔧 IMPLEMENTATION STEPS

### Step 1: Diagnostic - Check What Data Exists

1. Open workflow: http://localhost:5678/workflow/9tG2gR6KBt6nYyHT/executions/8427
2. Click on **"Build WF06 Response Message"** node
3. Check **Input** tab → see what keys are available
4. Look for: `phone_number`, `phone_with_code`, `phone_without_code`

### Step 2: Apply Option 1 (Quick Fix - RECOMMENDED)

1. Click on node: **"Build WF06 Response Message"**
2. **DELETE** all existing code
3. **PASTE** the V103.1 code above (with fallback chain)
4. Click **Save**

### Step 3: Test WF06 Flow

```bash
# Send WhatsApp conversation
# Complete data collection
# At confirmation: "1" (agendar)

# Check logs for phone number resolution
docker logs -f e2bot-n8n-dev | grep -E "BUILD WF06 RESPONSE|Phone number resolved"

# Expected:
# 🔍 Phone number resolved: 556181755748 ✅
```

### Step 4: Verify Send WhatsApp Response

```bash
# After WF06 response sent
docker logs -f e2bot-evolution-dev | grep "sendText"

# Expected:
# ✅ 200 OK - Message sent successfully
# ❌ Should NOT see "Bad request - please check your parameters"
```

---

## 📊 VALIDATION

### Test Case 1: WF06 Next Dates Flow
```
User completes data → confirmation → "1" (agendar)
Expected:
  ✅ Build WF06 Response logs: "Phone number resolved: 556181755748"
  ✅ Send WhatsApp Response: 200 OK
  ✅ User receives calendar dates message
```

### Test Case 2: Empty Calendar
```
WF06 returns empty dates
Expected:
  ✅ Phone number still preserved
  ✅ User receives: "⚠️ Não encontramos horários disponíveis"
  ✅ No "Bad request" error
```

### Test Case 3: Available Slots Flow
```
User selects date → "1" (select date)
Expected:
  ✅ Build WF06 Slots Response also has phone_number
  ✅ Send WhatsApp Response: 200 OK
  ✅ User receives available slots message
```

---

## 🚨 ROOT CAUSE EXPLANATION

### Why Phone Number Was Lost

**Original V102 Design** relied on parallel connection:
- Merge WF06 executed in parallel with State Machine
- Merge had direct access to Get Conversation Details data
- Build WF06 Response inherited phone_number from Merge

**V103 Sequential Design** breaks that assumption:
- Merge WF06 now executes AFTER WF06 HTTP Request
- Data must flow through: Build Update Queries → WF06 HTTP → Prepare WF06 → Merge
- Each node must explicitly pass phone_number

**Solution**: Add explicit phone_number preservation at each step OR use fallback chain with `$node` reference

---

## 📁 RELATED FILES

**Code to update**:
- `scripts/wf02-v102-build-wf06-response.js` → V103.1 with fallback chain

**Alternative nodes to check**:
- Prepare WF06 Next Dates Data
- Merge WF06 Next Dates with User Data
- Build WF06 Slots Response Message (same issue)

---

**Status**: Solution identified - add phone_number fallback chain
**Priority**: HIGH - blocks WF06 calendar functionality
**Deployment**: Quick fix in Build WF06 Response Message node
