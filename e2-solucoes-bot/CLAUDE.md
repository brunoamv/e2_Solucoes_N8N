# E2 Soluções WhatsApp Bot - Context for Claude Code

> **Critical Context** | Updated: 2026-03-10 | V2.8.3 (WF01) + V57.2 (WF02) DEPLOYED

---

## 🎯 Project Identity

**System**: WhatsApp bot with Claude AI + RAG (E2 Soluções - Brazilian electrical engineering)

**Stack**: n8n + Claude 3.5 Sonnet + Supabase + PostgreSQL + Evolution API v2.3.7 + RD Station CRM

**Language**: Portuguese (PT-BR)

---

## ✅ Current Production Status

### Workflow 01 - WhatsApp Handler V2.8.3 ✅ DEPLOYED

**Critical Fix**: Atomic duplicate detection via PostgreSQL ON CONFLICT
**Status**: ✅ WORKING IN PRODUCTION

**5 Bugs Resolved**:
1. ✅ Race Condition - Save Message first (atomic duplicate detection)
2. ✅ Ghost Connections - Removed obsolete nodes
3. ✅ Node References - Updated to valid nodes only
4. ✅ ExpressionError - All expressions validated
5. ✅ Infinite Loop - Removed "Extract Conversation ID" node

**Flow**:
```
Extract → Save Message (ON CONFLICT) → Check Operation →
Is Duplicate? → [true: Duplicate Response | false: AI Agent]
```

**Files**:
- Workflow: `n8n/workflows/01_main_whatsapp_handler_V2.8.3_NO_LOOP.json`
- Docs: `docs/PLAN/V2.8_3_FINAL_VALIDATION.md`

---

### Workflow 02 - AI Agent V57.2 ✅ READY FOR TESTING

**Critical Fix**: Remove empty `conversation` object that caused conversation_id NULL
**Status**: ✅ GENERATED - Ready for import and testing

**Problem Solved**:
- V57.1 created empty `conversation = {}` object
- Used `conversation.id` instead of extracted `conversation_id` variable
- Result: conversation_id always NULL → executions stuck in "running"

**Solution V57.2**:
- ✅ Removed `const conversation = input.conversation || {}`
- ✅ Changed all `conversation.field` → `input.field` (8 surgical fixes)
- ✅ Uses V54-extracted `conversation_id` variable correctly
- ✅ Preserves V54 extraction, V32 state mapping, V57 merge append

**Flow**:
```
V57 Code Processor → State Machine Logic (uses input.* directly) →
Build Update Queries (receives valid conversation_id) → Database Updates
```

**Files**:
- Workflow: `n8n/workflows/02_ai_agent_conversation_V57_2_CONVERSATION_FIX.json`
- Docs: `docs/PLAN/V57_2_CONVERSATION_OBJECT_BUG.md`
- Script: `scripts/fix-workflow-v57_2-conversation-object-bug.py`

**Testing Steps**:
```bash
# 1. Import V57.2 workflow: http://localhost:5678
# 2. Deactivate V57.1 workflow
# 3. Activate V57.2 workflow
# 4. Send WhatsApp "oi" → menu
# 5. Send "1" → asks name
# 6. Send "Bruno Rosa" → asks phone (NOT menu loop)
# 7. Monitor: docker logs -f e2bot-n8n-dev | grep "conversation_id"
# 8. Verify: conversation_id NOT NULL in logs
# 9. Verify: Executions complete with "success" status
```

---

## 📊 Architecture

```
WhatsApp (Evolution API v2.3.7 - senderPn field)
  ↓
Workflow 01 V2.8.3 - WhatsApp Handler
  ├─→ ON CONFLICT duplicate detection (atomic)
  └─→ Route to AI Agent or Duplicate Response
      ↓
Workflow 02 V57.2 - AI Agent
  ├─→ V57 Merge Append (combines data sources)
  ├─→ V54 Extraction (extracts conversation_id correctly)
  ├─→ State Machine (uses input.* directly - V57.2 fix)
  ├─→ V32 State Mapping (DB → code names)
  ├─→ V43 Database (all columns present)
  ├─→ Claude AI + Supabase RAG
  └─→ RD Station CRM + Calendar + Email
```

---

## 📂 Essential Files

```
n8n/workflows/
  ├── 01_main_whatsapp_handler_V2.8.3_NO_LOOP.json        # WF01 ✅ DEPLOYED
  └── 02_ai_agent_conversation_V57_2_CONVERSATION_FIX.json # WF02 ⏳ TESTING

scripts/
  ├── fix-workflow-01-v28-3-remove-loop.py                 # V2.8.3 generator
  ├── fix-workflow-v57_2-conversation-object-bug.py        # V57.2 generator
  └── run-migration-v43.sh                                 # V43 database

docs/PLAN/
  ├── V2.8_3_FINAL_VALIDATION.md                           # WF01 validation
  └── V57_2_CONVERSATION_OBJECT_BUG.md                     # WF02 bug analysis
```

---

## 🎯 Conversation States

```
greeting → service_selection → collect_name → collect_phone →
collect_email → collect_city → confirmation →
scheduling | handoff_comercial | completed
```

**E2 Services**:
1. Energia Solar | 2. Subestação | 3. Projetos Elétricos | 4. BESS | 5. Análise e Laudos

---

## 🔧 Quick Testing

### V2.8.3 (WF01)
```bash
# Monitor duplicate detection
docker logs -f e2bot-n8n-dev | grep -E "V2.8|operation"

# Test: Send "oi" → operation='inserted', AI Agent called
# Test: Send duplicate → operation='updated', returns "duplicate"
```

### V57.2 (WF02)
```bash
# Monitor conversation_id
docker logs -f e2bot-n8n-dev | grep "conversation_id"

# Test: Send "oi" → "1" → "Bruno Rosa"
# Verify: conversation_id NOT NULL
# Verify: Bot progresses (NOT menu loop)
# Check: http://localhost:5678/projects/08qzhIsou3TK6J3Z/executions
```

### Database
```bash
# V43 columns check
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -c "\d conversations"
```

---

## 🐛 Version History (Ultra-Compact)

**Workflow 01 Evolution**:
- V2.8.0: Race condition fix (Save Message first)
- V2.8.1: Ghost connections cleanup
- V2.8.2: Node references update
- V2.8.3: Infinite loop fix ✅ **DEPLOYED**

**Workflow 02 Evolution**:
- V27-V30: Early validation issues → Fixed
- V31: Validator isolation → Fixed
- V32: State mapping → Fixed
- V43: Database migration → Executed
- V48-V56: Merge attempts → Evolved to V57
- V57: Merge append pattern → Implemented
- V57.1: State machine syntax → Fixed
- V57.2: Conversation object bug → **READY FOR TESTING**

---

## 📞 Critical Docs

**V2.8.3 (WF01)**:
- Validation: `docs/PLAN/V2.8_3_FINAL_VALIDATION.md`
- Analysis: `docs/PLAN/V2.8_3_ANALYSIS_REPORT.md`

**V57.2 (WF02)**:
- Bug Analysis: `docs/PLAN/V57_2_CONVERSATION_OBJECT_BUG.md`
- V57 Base: `docs/PLAN/V57_MERGE_APPEND_SOLUTION.md`

**External**:
- n8n: https://docs.n8n.io
- Claude: https://docs.anthropic.com
- Evolution: https://github.com/EvolutionAPI

---

**Status**: V2.8.3 DEPLOYED ✅ | V57.2 READY FOR TESTING ⏳
