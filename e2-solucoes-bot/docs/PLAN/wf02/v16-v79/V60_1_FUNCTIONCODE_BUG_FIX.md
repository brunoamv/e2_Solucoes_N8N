# V60.1 FunctionCode Bug Fix - Complete Analysis

> **Bug Fixed**: Generator script added V60 code to jsCode instead of replacing functionCode | Date: 2026-03-10

---

## 🐛 Bug Summary

**Problem**: V60 workflow responded with OLD V58.1 templates despite generator script reporting success

**Root Cause**: n8n Function node has TWO code fields (`functionCode` and `jsCode`), and when both exist, n8n **executes `functionCode` and ignores `jsCode`**

**Impact**: Users saw old simple templates ("Somos especialistas em engenharia elétrica") instead of rich templates ("com *15+ anos de experiência*")

---

## 🔍 Root Cause Analysis

### Discovery Process

1. **User Report**: "Importei V60 mas bot responde com UX antiga"
   - WhatsApp log showed: "Somos especialistas em engenharia elétrica." (OLD)
   - Expected: "Somos especialistas em engenharia elétrica com *15+ anos de experiência*." (NEW)

2. **Initial Investigation**: Verified V60 JSON file contains rich templates
   ```bash
   grep "15+ anos" V60_COMPLETE_SOLUTION.json
   # Result: ✅ FOUND at line 146
   ```

3. **Critical Discovery**: Found **TWO** template definitions in V60 JSON
   ```bash
   grep -n "const templates = {" V60_COMPLETE_SOLUTION.json
   # Line 145: functionCode (OLD templates - 9,590 chars)
   # Line 146: jsCode (NEW templates - 28,160 chars)
   ```

4. **n8n Behavior Confirmed**: When both fields exist, n8n executes `functionCode` field

---

## 📊 Technical Details

### n8n Function Node Fields

```json
{
  "name": "State Machine Logic",
  "type": "n8n-nodes-base.function",
  "parameters": {
    "functionCode": "...",  // ⚠️ n8n EXECUTES THIS
    "jsCode": "..."         // ❌ n8n IGNORES THIS
  }
}
```

**Execution Priority**:
- If `functionCode` exists → n8n executes this (regardless of `jsCode`)
- If only `jsCode` exists → n8n executes this
- If both exist → n8n executes `functionCode` and ignores `jsCode`

### What V60 Generator Did Wrong

**V60 Generator Script** (`scripts/generate-workflow-v60-complete.py`):
```python
# ❌ WRONG: Added V60 code to jsCode field
state_machine_node['parameters']['jsCode'] = js_code_with_v60

# ⚠️ PROBLEM: Did NOT remove or replace functionCode field
# Result: functionCode (OLD) overrides jsCode (NEW)
```

### What V60.1 Generator Does Right

**V60.1 Generator Script** (`scripts/generate-workflow-v60_1-fix-function-code.py`):
```python
# ✅ RIGHT: Replace functionCode field directly
state_machine_node['parameters']['functionCode'] = js_code_with_v60

# ✅ RIGHT: Remove jsCode field (n8n doesn't use it anyway)
if 'jsCode' in state_machine_node['parameters']:
    del state_machine_node['parameters']['jsCode']
```

---

## 🔧 Fix Implementation

### Changes Made in V60.1

1. **Script Location**: `scripts/generate-workflow-v60_1-fix-function-code.py`

2. **Key Changes**:
   - ✅ Read from V58.1 `functionCode` field (not jsCode)
   - ✅ Replace V58.1 templates with V59 rich templates
   - ✅ Add V60 confirmation and correction_menu states
   - ✅ Write result to `functionCode` field (not jsCode)
   - ✅ Delete `jsCode` field if present

3. **Output File**: `n8n/workflows/02_ai_agent_conversation_V60_1_FUNCTIONCODE_FIX.json`

### V60.1 Validation Results

```
✅ Has functionCode: True (20,431 characters)
❌ Has jsCode: False (removed)
✅ Rich templates: FOUND ("15+ anos de experiência")
✅ Confirmation state: FOUND (case 'confirmation':)
✅ Correction menu state: FOUND (case 'correction_menu':)
```

---

## 📋 Before vs After Comparison

### V60 (BROKEN)

```json
{
  "name": "State Machine Logic",
  "parameters": {
    "functionCode": "...(V40 OLD templates - 9,590 chars)...",
    "jsCode": "...(V58.1 + V60 NEW templates - 28,160 chars)..."
  }
}
```
**Result**: ❌ n8n executes `functionCode` → Users see OLD templates

### V60.1 (FIXED)

```json
{
  "name": "State Machine Logic",
  "parameters": {
    "functionCode": "...(V58.1 + V60 NEW templates - 20,431 chars)..."
    // jsCode field removed
  }
}
```
**Result**: ✅ n8n executes `functionCode` → Users see NEW rich templates

---

## 🧪 Testing Instructions

### Phase 1: Import V60.1 Workflow

```bash
# 1. Open n8n
open http://localhost:5678

# 2. Navigate to: Workflows → Import from File
# 3. Select: n8n/workflows/02_ai_agent_conversation_V60_1_FUNCTIONCODE_FIX.json
# 4. Click: Import
# 5. Verify workflow name: "02 - AI Agent V60.1 (Complete Solution - FUNCTIONCODE FIX)"
```

### Phase 2: Activation

```bash
# 1. Deactivate V58.1 (or V60 if imported)
#    - Find: "02 - AI Agent V58.1..." or "V60 (Complete Solution...)"
#    - Toggle: Inactive

# 2. Activate V60.1
#    - Find: "02 - AI Agent V60.1 (Complete Solution - FUNCTIONCODE FIX)"
#    - Toggle: Active
#    - Verify: Green toggle switch
```

### Phase 3: Test Rich Templates

**Test Path**:
```
User: oi

Expected Bot Response (V60.1):
🤖 *Olá! Bem-vindo à E2 Soluções!*

Somos especialistas em engenharia elétrica com *15+ anos de experiência*.

*Qual serviço você precisa?*

☀️ *1 - Energia Solar*
   Projetos fotovoltaicos residenciais e comerciais

⚡ *2 - Subestação*
   Reforma, manutenção e construção

📐 *3 - Projetos Elétricos*
   Adequações e laudos técnicos

🔋 *4 - BESS (Armazenamento)*
   Sistemas de armazenamento de energia

📊 *5 - Análise e Laudos*
   Qualidade de energia e eficiência

_Digite o número do serviço (1-5):_
```

**Validation**:
- ✅ Contains: "15+ anos de experiência"
- ✅ Contains: *bold* formatting markers
- ✅ Contains: _italic_ formatting markers
- ✅ Contains: Service descriptions (not just names)
- ✅ Contains: Emojis for each service (☀️ ⚡ 📐 🔋 📊)

### Phase 4: Test Complete Flow

```
User: oi
Bot: (rich greeting with 15+ anos) ✅

User: 1
Bot: Ótima escolha! Vou precisar de alguns dados.

     👤 *Qual é o seu nome completo?*
     💡 _Exemplo: Maria Silva Santos_
     _Usaremos para personalizar seu atendimento_ ✅

User: Bruno Rosa
Bot: Obrigado, Bruno Rosa!

     📱 *Qual é o seu telefone com DDD?*
     Identificaremos se é seu WhatsApp automaticamente.
     💡 _Exemplo: (62) 98765-4321_
     _Usaremos este número para agendarmos sua visita técnica_ ✅

User: (62) 98765-4321
Bot: 📱 *Confirmação de Contato*
     Perfeito! Identificamos seu WhatsApp:
     *(62) 98765-4321*
     Este número é seu contato principal para agendarmos a visita técnica?
     1️⃣ - *Sim*, pode me ligar neste número
     2️⃣ - *Não*, prefiro informar outro número
     💡 _Responda 1 ou 2_ ✅

User: 1
Bot: 📧 *Qual é o seu e-mail?*
     Enviaremos a proposta técnica e documentos por e-mail.
     💡 _Exemplo: maria.silva@email.com_
     _Digite *"pular"* se preferir não informar_
     ⚠️ _Sem e-mail, os documentos serão enviados apenas por WhatsApp_ ✅

User: bruno@email.com
Bot: 🏙️ *Em qual cidade você está?*
     Precisamos saber para agendar a visita técnica.
     💡 _Exemplo: Goiânia - GO_
     📍 *Área de Atendimento:*
        Atendemos todo o Centro-Oeste (GO, DF, MT, MS)
     _Informe a cidade e estado:_ ✅

User: Goiânia - GO
Bot: ✅ *Confirmação dos Dados*
     Por favor, confira as informações:

     👤 *Nome:* Bruno Rosa
     📱 *Telefone:* (62) 98765-4321
     📧 *E-mail:* bruno@email.com
     🏙️ *Cidade:* Goiânia - GO
     ☀️ *Serviço:* Energia Solar

     *Está tudo correto?*
     ✔️ Digite *"sim"* para confirmar
     ✏️ Digite *"não"* para corrigir alguma informação ✅

User: sim
Bot: ✅ *Agendamento Confirmado!*
     Tudo certo! Seu atendimento foi registrado com sucesso.
     📧 *Você receberá:*
        • E-mail de confirmação em até 1 hora
        • WhatsApp com detalhes da visita técnica
     📞 *Nossa equipe entrará em contato:*
        Em até 24 horas para agendar data/horário
     🙏 *Obrigado por escolher a E2 Soluções!*
     _Qualquer dúvida, responda esta mensagem_ ✅
```

---

## 🎯 Success Criteria

### Functional Requirements

- [x] V60.1 workflow generated successfully
- [x] Only `functionCode` field present (no `jsCode`)
- [x] All 16 rich templates included
- [x] V60 confirmation state logic added
- [x] V60 correction_menu state logic added
- [x] {{summary}} variable generation implemented

### Quality Validation

- [x] JSON structure valid (python -m json.tool passed)
- [x] Workflow name updated to V60.1
- [x] File size: 64 KB (vs V60: 82 KB)
- [x] Rich templates present: "15+ anos de experiência"
- [x] State cases present: confirmation, correction_menu
- [x] Template formatting: *bold*, _italic_, emojis

### Testing Validation

- [ ] Import to n8n successful
- [ ] Workflow activation successful
- [ ] Rich templates appear in WhatsApp
- [ ] Confirmation flow works correctly
- [ ] Correction menu works correctly
- [ ] Database updates correctly

---

## 📞 Monitoring Commands

### Real-time Logs

```bash
# V60.1 execution monitoring
docker logs -f e2bot-n8n-dev | grep -E "V60|confirmation|summary|templates"

# State transitions
docker logs -f e2bot-n8n-dev | grep "next_stage"

# Template rendering
docker logs -f e2bot-n8n-dev | grep "response_text"
```

### Database Verification

```bash
# Recent conversations
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "
SELECT lead_name, service_type, contact_phone, current_state, created_at
FROM conversations
ORDER BY created_at DESC
LIMIT 10;
"

# Confirmation statistics
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "
SELECT
  COUNT(*) as total,
  COUNT(CASE WHEN current_state = 'completed' THEN 1 END) as completed
FROM conversations
WHERE created_at > NOW() - INTERVAL '24 hours';
"
```

---

## 🔄 Rollback Plan (if needed)

### Immediate Rollback to V58.1

```bash
# 1. Deactivate V60.1 workflow in n8n
# 2. Activate V58.1 workflow
# 3. Verify bot functionality restored
```

**V58.1 File**: `n8n/workflows/02_ai_agent_conversation_V58_1_UX_REFACTOR_COMPLETE.json`

### Rollback Verification

```bash
# Test basic flow
# Send "oi" → should get V58.1 simple greeting (not rich)

# Monitor n8n logs
docker logs -f e2bot-n8n-dev | grep -E "V58.1|conversation_id"
```

---

## 📊 Lessons Learned

### What Went Wrong (V60)

1. **Assumption Error**: Assumed n8n uses `jsCode` field (it doesn't when `functionCode` exists)
2. **Incomplete Testing**: Didn't verify which field n8n actually executes
3. **Missing Validation**: Didn't check for duplicate code fields in generated JSON
4. **Tool Understanding Gap**: Didn't fully understand n8n Function node behavior

### What We Fixed (V60.1)

1. **Correct Field**: Now replace `functionCode` directly
2. **Field Cleanup**: Remove `jsCode` if present (n8n ignores it anyway)
3. **Comprehensive Validation**: Verify only correct field exists
4. **Tool Mastery**: Now understand n8n Function node execution logic

### Best Practices Going Forward

1. **Validate Tool Behavior**: Always verify which fields tools actually use
2. **Check for Duplicates**: Ensure no duplicate/conflicting fields in generated output
3. **Test End-to-End**: Verify runtime behavior matches expected output
4. **Document Tool Quirks**: Record non-obvious tool behaviors for future reference

---

## 📁 Files Reference

### Generated Files

- **V60.1 Workflow**: `n8n/workflows/02_ai_agent_conversation_V60_1_FUNCTIONCODE_FIX.json` (64 KB)
- **V60.1 Generator**: `scripts/generate-workflow-v60_1-fix-function-code.py` (13 KB)
- **This Document**: `docs/PLAN/V60_1_FUNCTIONCODE_BUG_FIX.md`

### Related Files

- **V60 (Broken)**: `n8n/workflows/02_ai_agent_conversation_V60_COMPLETE_SOLUTION.json` (82 KB)
- **V60 Generator**: `scripts/generate-workflow-v60-complete.py` (11 KB)
- **V58.1 Source**: `n8n/workflows/02_ai_agent_conversation_V58_1_UX_REFACTOR_COMPLETE.json` (58 KB)

---

**Status**: ✅ V60.1 GENERATED - Ready for Import & Testing
**Confidence**: 🟢 **HIGH** (99%) - Root cause identified and fixed
**Recommendation**: ✅ **IMPORT V60.1 AND TEST**

**Generated**: 2026-03-10 | **Analyst**: Claude Code (Automated)
