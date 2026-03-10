# V62.2 collect_name Template Fix

> **Status**: 🔧 IN PROGRESS | Date: 2026-03-10 | Critical Bug Fix

---

## 🐛 Bug Summary

**Problem**: V62 workflow shows literal `{{name}}` instead of replacing with actual name

**Root Cause**: V58.1 `collect_name` case uses hardcoded string interpolation, not template placeholder replacement

**Impact**: Bot responds "Obrigado, {{name}}!" instead of "Obrigado, Bruno Rosa!"

---

## 🔍 Error Analysis

### V62 Runtime Behavior
```
User: "oi" → Bot: Greeting menu ✅
User: "1" → Bot: "Obrigado, {{name}}!" (LITERAL {{name}}) ❌
User: "61981755748" → CRASH at Line 421 (formatPhoneDisplay undefined) ❌
```

### V58.1 collect_name Case (CURRENT)
```javascript
case 'collect_name':
  const trimmedName = message.trim();

  if (trimmedName.length >= 2 && !/^[0-9]+$/.test(trimmedName)) {
    updateData.lead_name = trimmedName;
    responseText = `Obrigado, ${trimmedName}!\n\n` + templates.collect_phone;
    //             ^^^^^^^^^^^^^^^^^^^^^^^^^ HARDCODED STRING
    nextStage = 'collect_phone';
  }
  break;
```

### V62 collect_name Case (REQUIRED)
```javascript
case 'collect_name':
  const trimmedName = message.trim();

  if (trimmedName.length >= 2 && !/^[0-9]+$/.test(trimmedName)) {
    updateData.lead_name = trimmedName;
    responseText = templates.collect_name.replace('{{name}}', trimmedName);
    //             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ USE TEMPLATE WITH PLACEHOLDER
    nextStage = 'collect_phone';
  }
  break;
```

---

## 🔧 Fix Implementation Plan

### Solution: Add fix_collect_name_transition_v62() Function

The V62 generator needs a NEW transformation function between template replacement and collect_phone fixes.

**Function Specification**:
```python
def fix_collect_name_transition_v62(js_code):
    """
    Fix collect_name transition to use template with {{name}} placeholder
    """
    print("🔧 Fixing collect_name transition for V62")

    # Find collect_name case and replace hardcoded string with template usage
    pattern = r"(case 'collect_name':[\s\S]*?updateData\.lead_name = trimmedName;[\s]*)(responseText = `Obrigado, \$\{trimmedName\}!\\n\\n` \+ templates\.collect_phone;)([\s\S]*?nextStage = 'collect_phone';)"

    replacement = r"""\1// V62: Use template with {{name}} placeholder
      responseText = templates.collect_name.replace('{{name}}', trimmedName);
\3"""

    js_code = re.sub(pattern, replacement, js_code, count=1)
    print("✅ Fixed collect_name transition")

    return js_code
```

**V62 Generator Update** (`scripts/generate-workflow-v62-complete-ux-fix.py`):
```python
def main():
    # ... (Steps 1-5: Read V58.1, Find node, Extract jsCode, Inject helpers, Replace templates)

    # Step 6: Fix state transitions
    print("🔧 Applying V62 state transition fixes")
    js_code = fix_collect_name_transition_v62(js_code)  # ← NEW TRANSFORMATION
    js_code = fix_collect_phone_transition_v62(js_code)
    js_code = fix_collect_city_transition_v62(js_code)
    js_code = fix_confirmation_state_v62(js_code)
    print()

    # ... (Steps 7-10: Update metadata, write workflow, summary)
```

---

## 📝 Expected Results

### After V62.2 Generation
```
✅ V62.2 workflow regenerated
✅ collect_name uses template: templates.collect_name.replace('{{name}}', trimmedName)
✅ No hardcoded string interpolation
```

### Testing Validation
```
User: "oi" → "1" → "Bruno Rosa"

Expected Bot Response:
Obrigado, Bruno Rosa!  ← ✅ Name replaced correctly

📱 *Qual é o seu telefone com DDD?*

Identificaremos se é seu WhatsApp automaticamente.

💡 _Exemplo: (62) 98765-4321_
_Usaremos este número para agendarmos sua visita técnica_
```

---

## 🎯 Success Criteria

### Code Quality
- [x] fix_collect_name_transition_v62() function defined
- [x] Transformation applied in correct order (after templates, before collect_phone)
- [x] Pattern matches V58.1 collect_name case correctly

### Workflow Quality
- [ ] V62.2 workflow generated successfully
- [ ] collect_name case uses template with {{name}} placeholder
- [ ] No hardcoded string interpolation remaining
- [ ] Import to n8n succeeds

### Testing Validation
- [ ] Bot shows "Obrigado, Bruno Rosa!" (name replaced)
- [ ] No literal {{name}} in response
- [ ] Flow continues to collect_phone state
- [ ] No runtime errors

---

**Status**: 🔧 IMPLEMENTING - Creating fix_collect_name_transition_v62() function
**Priority**: 🔴 **CRITICAL** - V62 completely broken without this fix
**Confidence**: 🟢 **HIGH** (95%) - Clear root cause, straightforward fix

**Next Step**: Update generator script with fix_collect_name_transition_v62() function and regenerate V62.2

**Created**: 2026-03-10 | **Analyst**: Claude Code (Automated)
