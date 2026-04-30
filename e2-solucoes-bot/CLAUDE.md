# E2 Bot - Context

> **Production V1**: WF01 V2.8.3 | WF02 V114 ✅ COMPLETE | WF05 V7 | WF06 V2.2 | WF07 V13 ✅
> **Status**: ✅ ORGANIZED - Single source of truth structure implemented
> **Updated**: 2026-04-29 18:00 BRT

## Stack

n8n 2.14.2 + Claude 3.5 + PostgreSQL + Evolution API v2.3.7 | PT-BR
**Flow**: WhatsApp → WF01 (dedup) → WF02 (AI) → WF05 (calendar) → WF07 (email)

---

## Workflows

| WF | Production V1 | Location | Function |
|----|---------------|----------|----------|
| **01** | V2.8.3 ✅ | `production/wf01/` | Dedup via PostgreSQL ON CONFLICT |
| **02** | V114 ✅ COMPLETE | `production/wf02/` | AI conversation with proactive UX + WF06 integration + V111 row lock + V113 suggestions + V114 TIME fields |
| **05** | V7 Hardcoded ✅ | `production/wf05/` | Google Calendar + DB + WF07 trigger (hardcoded business hours) |
| **06** | V2.2 ✅ | `production/wf06/` | Calendar availability microservice (OAuth + empty calendar + response mode) |
| **07** | V13 ✅ | `production/wf07/` | nginx → HTTP → SMTP → DB (INSERT...SELECT pattern) |

**Services**: 1-Solar | 2-Subestação | 3-Projetos | 4-BESS | 5-Análise
**WF02 Flow**: Services 1/3 + confirm → WF06 → WF05 | Others → Handoff

---

## Files

**Workflows** (`n8n/workflows/`) - **ORGANIZED STRUCTURE**:
```
📁 production/          # Production V1 Package (SINGLE SOURCE OF TRUTH)
  ├── wf01/ → 01_main_whatsapp_handler_V2.8.3_NO_LOOP.json
  ├── wf02/ → 02_ai_agent_conversation_V114_FUNCIONANDO.json ⭐
  ├── wf05/ → 05_appointment_scheduler_v7_hardcoded_values.json
  ├── wf06/ → 06_calendar_availability_service_v2_2.json
  └── wf07/ → 07_send_email_v13_insert_select.json

📁 development/         # Development versions
  ├── wf02/ (development iterations)
  ├── wf05/ (v3.6, v8 experimental)
  └── wf06/ (v2, v2.1)

📁 historical/          # Complete version history
  └── wf02/ (V77-V113 iterations)

⚠️ IMPORTANT: NO workflow JSON files in root directory!
            All workflows organized in subfolders - zero duplication.

Production WF02 V114 ✅ COMPLETE:
  - Workflow ID: 9tG2gR6KBt6nYyHT
  - Node Count: 52 nodes
  - Location: production/wf02/02_ai_agent_conversation_V114_FUNCIONANDO.json
  - Includes ALL fixes:
    ✅ V111 Database Row Locking (FOR UPDATE SKIP LOCKED)
    ✅ V113.1 WF06 Suggestions Persistence (date_suggestions + slot_suggestions)
    ✅ V114 PostgreSQL TIME Fields (scheduled_time_start + scheduled_time_end)
    ✅ V79.1 Schema-Aligned Build Update Queries (no contact_phone)
    ✅ V105 Routing Fix (Update State BEFORE Check If WF06)
  - Documentation: docs/WF02_V114_PRODUCTION_DEPLOYMENT.md
  - README: n8n/workflows/README.md (complete organization guide)
  - Scripts (scripts/wf02/state-machines/):
    - wf02-v114-slot-time-fields-fix.js (State Machine)
    - wf02-v111-build-sql-queries-row-locking.js (SQL Queries)
    - wf02-v113-build-update-queries1-wf06-next-dates.js (Dates)
    - wf02-v113-build-update-queries2-wf06-available-slots.js (Slots)
```

**DB Schema**:
- `conversations`: phone, lead_name, service, state, next_stage, collected_data
- `appointments`: lead_name/email, service, scheduled_date, google_calendar_event_id
- `email_logs`: recipient_email/name, subject, template_used, status, sent_at

---

## Deploy

### WF02 V111 🔴 CRITICAL (Database Row Locking - Race Condition Fix)
```bash
# CRITICAL FIX: Prevents stale state processing via PostgreSQL row locking
# ROOT CAUSE: User sends messages faster than DB commits → workflow reads stale state
# SOLUTION: FOR UPDATE SKIP LOCKED prevents concurrent executions reading same conversation

# Quick Deploy (10 minutes)
# 1. Open n8n Workflow
# URL: http://localhost:5678/workflow/9tG2gR6KBt6nYyHT

# 2. Find "Build SQL Queries" Node (JavaScript Code node, early in workflow)

# 3. Locate query_details definition (around line 30)
# ADD THIS LINE before `.trim()`:
#   FOR UPDATE SKIP LOCKED

# Before:
#   LIMIT 1
# `.trim();

# After:
#   LIMIT 1
#   FOR UPDATE SKIP LOCKED
# `.trim();

# 4. Save Node → Save Workflow

# 5. Test Rapid Messages
# Send 3 messages very quickly (< 1 second apart):
# Message 1: "cocal-go" (city)
# Message 2: "1" (agendar)  ← Should NOT process with stale state
# Message 3: "test"
# Expected: Only first message fully processes, others queued or "Processando" message

# 6. Verify WF06 Execution
docker logs -f e2bot-n8n-dev 2>&1 | grep -E "V111:|V110: Current → Next:"
# Expected:
#   V111: DATABASE ROW LOCKING ENABLED  ✅
#   V110: Current → Next: confirmation → trigger_wf06_next_dates  ✅
# NOT Expected:
#   V110: Current → Next: collect_city → confirmation  ❌ (stale state)

# Why V111 Fixes Race Condition:
# - FOR UPDATE: Locks conversation row until transaction commits
# - SKIP LOCKED: Returns empty if row already locked (another execution in progress)
# - Result: Only ONE execution processes conversation at a time
# - Impact: No stale state scenarios → WF06 HTTP Request executes correctly

# Docs:
# - Quick Deploy: docs/WF02_V111_QUICK_DEPLOY.md ⭐ START HERE
# - Full Deployment: docs/deployment/wf02/v100-v114/DEPLOY_WF02_V111_DATABASE_ROW_LOCKING.md
# - Root Cause Analysis: docs/fix/wf02/v100-v114/BUGFIX_WF02_V111_DATABASE_STATE_RACE_CONDITION.md
# - V110 Investigation: docs/fix/wf02/v100-v114/BUGFIX_WF02_V110_EXECUTION_9045_COMPLETE_ROOT_CAUSE.md
# - V111 Code: scripts/wf02/state-machines/wf02-v111-build-sql-queries-row-locking.js
```

### WF02 V114 🔴 CRITICAL (PostgreSQL TIME Fields Fix)
```bash
# CRITICAL FIX: Extract start_time and end_time from WF06 slots for PostgreSQL TIME columns
# ROOT CAUSE: State Machine saves scheduled_time_display but NOT scheduled_time_start/end
# SOLUTION: V114 extracts TIME fields from WF06 slot structure for database compatibility

# Quick Deploy (5 minutes)
# 1. Open n8n Workflow
# URL: http://localhost:5678/workflow/9tG2gR6KBt6nYyHT

# 2. Find "State Machine Logic" Node (JavaScript Code node)

# 3. Replace ALL code with V114
cat /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/scripts/wf02-v114-slot-time-fields-fix.js
# Copy content → DELETE existing code in n8n → PASTE V114 code → Save

# 4. Save Workflow

# 5. Test Complete WF06 Flow
# Send WhatsApp: "oi" → complete → "1" (agendar) → "1" (select date) → "1" (select slot)
# Expected: Appointment confirmed AND saved (NOT PostgreSQL TIME error!)

# 6. Verify Database TIME Fields
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT phone_number,
             collected_data->'scheduled_time_start' as start_time,
             collected_data->'scheduled_time_end' as end_time
      FROM conversations
      WHERE phone_number = '556181755748';"
# Expected: start_time: "08:00", end_time: "10:00"  ✅

# 7. Monitor Logs
docker logs -f e2bot-n8n-dev 2>&1 | grep -E "V114|TIME"
# Expected:
#   V114: ✅ CRITICAL FIX - Extracted TIME fields:
#   V114:   start_time: 08:00
#   V114:   end_time: 10:00

# Why V114 Fixes PostgreSQL Error:
# - WF06 returns: { start_time: "08:00", end_time: "10:00", formatted: "8h às 10h" }
# - V113.1: Only saves scheduled_time_display: "8h às 10h" ❌
# - V114: Extracts and saves scheduled_time_start: "08:00" ✅
# - V114: Extracts and saves scheduled_time_end: "10:00" ✅
# - Impact: PostgreSQL TIME columns receive valid values → appointment creation succeeds

# Docs:
# - Quick Deploy: docs/WF02_V114_QUICK_DEPLOY.md ⭐ START HERE
# - Complete Summary: docs/WF02_V114_COMPLETE_SUMMARY.md
# - V114 Code: scripts/wf02/state-machines/wf02-v114-slot-time-fields-fix.js
# - Previous Version: V113.1 (date_suggestions and slot_suggestions persistence)
```

### WF02 V104+V104.2+V105+V106.1 COMPLETE 🔴 (State Sync + Schema + Routing + response_text)
```bash
# CRITICAL: FOUR components required for complete fix!
# - V104 State Machine (code)
# - V104.2 Build Update Queries (code)
# - V105 Routing Fix (workflow connections)
# - V106.1 response_text Fix (workflow Send node configuration)

# PART 1: V104 State Machine (puts state in collected_data)
# 1. Copy V104 State Machine Code
cat /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/scripts/wf02/state-machines/wf02-v104-database-state-update-fix.js

# 2. Update n8n Workflow - State Machine Node
# Open: http://localhost:5678/workflow/9tG2gR6KBt6nYyHT
# Node: "State Machine Logic"
# Action: DELETE all existing code → PASTE V104 code → Save

# PART 2: V104.2 Build Update Queries (reads state from collected_data + schema-compliant)
# 3. Copy V104.2 Build Update Queries Code
cat /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/scripts/wf02/state-machines/wf02-v104_2-build-update-queries-schema-fix.js

# 4. Update n8n Workflow - Build Update Queries Node
# Same workflow: http://localhost:5678/workflow/9tG2gR6KBt6nYyHT
# Node: "Build Update Queries"
# Action: DELETE all existing code → PASTE V104.2 code → Save

# 5. Test Critical Path (Infinite Loop Fix)
# Send WhatsApp: "oi" → complete flow → "1" (agendar) → Wait for dates → "1" (select date)
# Expected: Shows time slots (NOT dates again) ✅

# Verify database after date selection:
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT state_machine_state, current_state, collected_data->'current_stage' as stage_in_data
      FROM conversations
      WHERE phone_number = '556181755748';"

# Expected:
# state_machine_state: "process_date_selection" or "trigger_wf06_available_slots"  ✅
# current_state: "agendando"  ✅
# stage_in_data: "process_date_selection"  ✅ (MUST match state_machine_state!)

# PART 3: V105 Routing Fix (workflow connections - NO CODE)
# Open: http://localhost:5678/workflow/9tG2gR6KBt6nYyHT
# 1. Disconnect: Build Update Queries → Check If WF06 Next Dates
# 2. Disconnect: Check If WF06 Available Slots FALSE → Update Conversation State
# 3. Connect NEW: Build Update Queries → Update Conversation State
# 4. Connect NEW: Update Conversation State → Check If WF06 Next Dates
# 5. Save workflow
# Result: Update Conversation State executes BEFORE Check If WF06 routing (not after)

# Verify V105 routing fix:
# Send WhatsApp: "oi" → complete → "1" (agendar) → "1" (select date)
# Expected: Shows time slots (NOT dates again) ✅
# Database updates BEFORE WF06 route taken ✅

# PART 4: V106.1 response_text Fix (route-specific Send nodes - NO CODE)
# Open: http://localhost:5678/workflow/9tG2gR6KBt6nYyHT
# 1. Click "Send WhatsApp Response" node (normal flow Send node)
# 2. Find parameter: `text`
# 3. Change value from: {{ $input.first().json.response_text }}
#                   to: {{ $node["Build Update Queries"].json.response_text }}
# 4. Save node → Save workflow
# 5. Verify WF06 Send nodes (if separate nodes exist):
#    - "Send Message with Dates": Should use {{ $input.first().json.response_text }} (from Merge WF06 Next Dates) ✅
#    - "Send Message with Slots": Should use {{ $input.first().json.response_text }} (from Merge WF06 Slots) ✅

# Verify V106.1 response_text fix:
# Test 1 (Normal flow): Service 5 → "1" (confirmar) → Message has actual content (not undefined) ✅
# Test 2 (WF06 dates): Service 1 → "1" (agendar) → Message shows actual dates with slot counts ✅
# Test 3 (WF06 slots): Continue Test 2 → "1" (select date) → Message shows actual time slots ✅

# Why V104+V104.2+V105+V106.1 Completes Fix:
# - V104 State Machine: Puts state in collected_data.current_stage ✅
# - V104.2 Build Update Queries: Reads from collected_data.current_stage ✅
# - V104.2 Build Update Queries: Schema-compliant (no contact_phone references) ✅
# - V105 Routing Fix: Update executes BEFORE Check If WF06 routing ✅
# - V106.1 response_text Fix: Route-specific Send nodes with appropriate data sources ✅
# - Impact: Infinite loop + undefined messages completely eliminated on ALL routes ✅

# Docs:
# - Deployment V104.2: docs/deployment/wf02/v100-v114/DEPLOY_WF02_V104_2_BUILD_UPDATE_QUERIES_COMPLETE_FIX.md
# - Deployment V105: docs/deployment/wf02/v100-v114/DEPLOY_WF02_V105_WF06_ROUTING_FIX.md
# - Deployment V106.1: docs/deployment/wf02/v100-v114/DEPLOY_WF02_V106_1_COMPLETE_FIX.md
# - Quick Deploy V105: docs/WF02_V105_QUICK_DEPLOY.md
# - Bug Reports: docs/fix/wf02/v100-v114/BUGFIX_WF02_V104_1_BUILD_UPDATE_QUERIES_STATE_FIX.md (state)
#                docs/fix/wf02/v100-v114/BUGFIX_WF02_V104_2_SCHEMA_MISMATCH.md (schema)
#                docs/fix/wf02/v100-v114/BUGFIX_WF02_V105_WF06_ROUTING_STATE_UPDATE.md (routing)
#                docs/fix/wf02/v100-v114/BUGFIX_WF02_V106_RESPONSE_TEXT_ROUTING.md (response_text - incomplete)
#                docs/fix/wf02/v100-v114/BUGFIX_WF02_V106_1_CRITICAL_WF06_FLOW_BREAK.md (response_text - complete)
# - V104 State Machine: scripts/wf02/state-machines/wf02-v104-database-state-update-fix.js
# - V104.2 Build Update Queries: scripts/wf02/state-machines/wf02-v104_2-build-update-queries-schema-fix.js
# - V105: No code files (workflow connection change only)
# - V106.1: No code files (workflow Send node configuration only)
```

### WF02 V91 (State Initialization Fix - Previous Version)
```bash
# 1. Copy V91 State Machine Code
cat /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/scripts/wf02/state-machines/wf02-v91-state-initialization-fix.js

# 2. Update n8n Workflow
# Open: http://localhost:5678/workflow/fpMUFXvBulYXX4OX  # WF02 V90 workflow ID
# Node: "State Machine Logic" Function
# Action: DELETE all existing code → PASTE V91 code → Save

# 3. Test Critical Path (WF06 Return)
# Test 1: Service 1 (Solar) - Complete Flow
# - State 8: confirmation → "1" (agendar)
# - State 9: trigger_wf06_next_dates → WF06 HTTP Request
# - ✅ MUST return to State 10: show_available_dates (NOT service_selection)
# - State 10: Display 3 dates with slot counts
# - User selects date → State 11
# - State 12: trigger_wf06_available_slots → WF06 HTTP Request
# - ✅ MUST return to State 13: show_available_slots (NOT greeting)

# Test 2: Verify logs show proper state resolution
docker logs -f e2bot-n8n-dev | grep -E "V91: RESOLVED currentStage|V91: WF06 data source"
# Expected:
# V91: RESOLVED currentStage: show_available_dates  ✅
# V91: WF06 data source: input.wf06_next_dates  ✅

# Validation
# ✅ State 10 reached after WF06 next_dates (not service_selection)
# ✅ State 13 reached after WF06 available_slots (not greeting)
# ✅ All 15 states return valid response_text
# ✅ Enhanced logging shows state resolution chain
# ✅ No fallback to greeting during WF06 flow

# Why V91 Fixes V90 Bug:
# - V90: State Machine executes TWICE → second execution loses state context
# - V90: input.current_stage = undefined → defaults to 'greeting' ❌
# - V91: Enhanced state resolution with 4-level fallback chain ✅
# - V91: Returns explicit current_stage: nextStage ✅
# - V91: Comprehensive logging for debugging ✅

# Docs:
# - Deployment: docs/deployment/wf02/v80-v99/DEPLOY_WF02_V91_STATE_INITIALIZATION_FIX.md
# - V90 Refactored: scripts/wf02/state-machines/wf02-v90-state-machine-refactored.js
# - V91 Critical Fix: scripts/wf02/state-machines/wf02-v91-state-initialization-fix.js
```

### WF06 V2.1 COMPLETE (OAuth + Empty Calendar + Input Data Source)
```bash
# 1. Import WF06 V2.1 JSON
# n8n UI → Import from file → Select: 06_calendar_availability_service_v2_1.json

# 2. Activate Workflow
# Click "Active" toggle → Verify green

# 3. Test Empty Calendar (Primary Validation)
curl -X POST http://localhost:5678/webhook/calendar-availability \
  -H "Content-Type: application/json" \
  -d '{"action": "next_dates", "count": 3, "service_type": "energia_solar", "duration_minutes": 120}'

# Expected: 3 dates with 8 slots each (no crashes!)
# ✅ No "Cannot read properties of undefined" errors
# ✅ Response contains dates_with_availability array

# 4. Test WF02 V80 Integration
# Trigger WF02 with service 1 (Solar) or 3 (Projetos)
# Expected: WF02 state 8 shows 3 dates from WF06 V2.1

# Validation:
# ✅ V2.1 fixes all 3 bugs: OAuth + empty calendar + input data source
# ✅ Works with empty calendars AND calendars with events
# ✅ WF02 V80 integration successful

# Docs: docs/deployment/wf06/DEPLOY_WF06_V2_1_COMPLETE_FIX.md
```

### WF07 V13
```bash
# Import: 07_send_email_v13_insert_select.json
# Test: { lead_email, lead_name, service_type, city, calendar_success }
# Expected: Email sent + DB log RETURNING
# Docs: docs/fix/wf07/BUGFIX_WF07_V13_INSERT_SELECT_FIX.md
```

---

## Commands

```bash
# DB
docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT phone_number, lead_name, service_type, current_state FROM conversations ORDER BY updated_at DESC LIMIT 5;"

# Evolution API
curl -s http://localhost:8080/instance/fetchInstances \
  -H "apikey: ae569043cfa169380c378347f91a1141ea572541d2d1cadbed222db519c8a891" | jq

# Logs
docker logs -f e2bot-n8n-dev | grep -E "ERROR|V13|INSERT"
```

---

## Critical Learnings

### n8n Limitations
1. **queryReplacement**: Does NOT resolve `={{ }}` → Use INSERT...SELECT
2. **$env access**: Blocked (Code + Set) → Use hardcoded values
3. **Filesystem**: Read/Write blocked → Use HTTP Request + nginx

### Evolution Path
- **WF07**: V2-V5 (fs blocked) → V9 (HTTP) → V13 (INSERT...SELECT) ✅
- **WF05**: V3-V6 ($env blocked) → V7 (hardcoded) ✅
- **WF02**: V68-V75 (reactive) → V76 (proactive) → V77-V79 (various issues) → V80 (complete + WF06) → V90 (refactored) → V91 (state initialization fix) ✅

### Key Insights
1. **Proactive UX** > Reactive validation (100% error elimination)
2. **Complete States Required**: n8n Function nodes MUST return valid responseText (no placeholders or empty strings)
3. **Return Structure Compatibility**: n8n workflows expect specific key names (`response_text` not `response`, `update_data` not `updateData`)
4. **Working Code as Model**: Extract complete logic from production workflows (V74.1_2) instead of theoretical implementations
5. **Intermediate states** enable clean conditional workflow routing
6. **Microservices** (WF06) enable independent testing/scaling
7. **INSERT...SELECT** superior to VALUES for n8n PostgreSQL
8. **Merge Proven Patterns**: V74 states 1-7 (complete) + V78 states 8-15 (WF06) + V74 return structure = V80 success
9. **n8n Data Access Limitation**: `$input.first().json` only accesses previous node, use `$node["Node Name"].json` for explicit references
10. **n8n Empty Item Behavior**: Returns `[{ json: {} }]` not `[]` with `continueOnFail: true` → Filter by meaningful properties (id, start)
11. **State Initialization Critical**: State Machine may execute TWICE in same workflow → Use 4-level fallback chain + explicit `current_stage` return (V91 fix)

---

## Documentation

**Quick Access**:
- **Quick Start**: `docs/development/05_LOCAL_SETUP.md` (30-60 min setup completo) ⭐
- **Navigation**: `docs/development/README.md` (navegação completa) ⭐
- **Architecture**: `docs/diagrams/01_SYSTEM_ARCHITECTURE.md` (diagramas visuais) ⭐
- Setup: `docs/Setups/QUICKSTART.md` (30-45 min)
- Email: `docs/Setups/SETUP_EMAIL.md` (Port 465 SSL/TLS)
- Credentials: `docs/Setups/SETUP_CREDENTIALS.md`
- Index: `docs/INDEX.md` | README: `docs/README.md`

**Implementation**:
- **WF02 V104+V104.2+V105+V106.1**: 🔴 COMPLETE FIX (State sync + schema + routing + response_text)
  - Deployment V104.2: `docs/deployment/wf02/v100-v114/DEPLOY_WF02_V104_2_BUILD_UPDATE_QUERIES_COMPLETE_FIX.md`
  - Deployment V105: `docs/deployment/wf02/v100-v114/DEPLOY_WF02_V105_WF06_ROUTING_FIX.md`
  - Deployment V106.1: `docs/deployment/wf02/v100-v114/DEPLOY_WF02_V106_1_COMPLETE_FIX.md`
  - Quick Deploy V105: `docs/WF02_V105_QUICK_DEPLOY.md`
  - Bug Reports: `docs/fix/wf02/v100-v114/BUGFIX_WF02_V104_*.md` (state + schema + routing + response_text)
  - V104 Code: `scripts/wf02/state-machines/wf02-v104-database-state-update-fix.js`
  - V104.2 Code: `scripts/wf02/state-machines/wf02-v104_2-build-update-queries-schema-fix.js`
- **WF02 V91**: Deployment: `docs/deployment/wf02/v80-v99/DEPLOY_WF02_V91_STATE_INITIALIZATION_FIX.md`
- **WF02 V90**: Refactored: `scripts/wf02/state-machines/wf02-v90-state-machine-refactored.js`
- **WF02 V80**: Deployment: `docs/deployment/wf02/v80-v99/DEPLOY_WF02_V80_COMPLETE_STATE_MACHINE.md`
- **WF02 Analysis**: `docs/analysis/wf02-versions/WF02_STATE_MACHINE_WF06_INTEGRATION_PROBLEM.md`
- **WF06 V2.1**: Deployment: `docs/deployment/wf06/DEPLOY_WF06_V2_1_COMPLETE_FIX.md`
  - OAuth Fix Plan: `docs/PLAN/wf06/PLAN_WF06_V2_OAUTH_FIX.md`
  - Bug Reports: `docs/fix/wf06/BUGFIX_WF06_V2_*.md`
- **WF07 V13**: Bugfix: `docs/fix/wf07/BUGFIX_WF07_V13_INSERT_SELECT_FIX.md`
- **WF05 V7**: Deployment: `docs/deployment/wf05/DEPLOY_WF05_V7_HARDCODED_FINAL.md`

**Structure** (2026-04-29 complete organization):
```
docs/
├── INDEX.md, README.md (updated 2026-04-29)
├── guidelines/ (8 comprehensive guides) ⭐ NEW
│   ├── 00_VISAO_GERAL.md (arquitetura conceitual)
│   ├── 01_N8N_BEST_PRACTICES.md (limitações n8n 2.x)
│   ├── 02_STATE_MACHINE_PATTERNS.md (padrão central)
│   ├── 03_DATABASE_PATTERNS.md (schema e queries)
│   ├── 04_WORKFLOW_INTEGRATION.md (microserviços)
│   ├── 05_TESTING_VALIDATION.md (estratégias de teste)
│   ├── 06_DEPLOYMENT_GUIDE.md (processo de release)
│   └── 07_SECURITY_COMPLIANCE.md (segurança e LGPD)
├── development/ (6 practical guides) ⭐ NEW
│   ├── 01_WORKFLOW_MODIFICATION.md (modificar workflows)
│   ├── 02_DEBUGGING_GUIDE.md (debug e troubleshooting)
│   ├── 03_COMMON_TASKS.md (tarefas comuns)
│   ├── 04_CODE_REVIEW_CHECKLIST.md (checklist de revisão)
│   ├── 05_LOCAL_SETUP.md (setup ambiente local)
│   └── README.md (navegação completa)
├── diagrams/ (3 visual diagrams) ⭐ NEW
│   ├── 01_SYSTEM_ARCHITECTURE.md (850 lines - arquitetura completa)
│   ├── 02_STATE_MACHINE_FLOW.md (750 lines - 15 estados detalhados)
│   └── README.md (280 lines - navigation guide)
├── analysis/ (53 files in 7 subdirectories)
├── deployment/ (51 files in 7 subdirectories)
├── fix/ (82 files in 7 subdirectories)
├── PLAN/ (137 files in 10 subdirectories)
├── status/ (47 files in 2 subdirectories)
├── implementation/ (16 files)
├── Setups/ (13 config guides)
├── Guides/ (user docs)
├── validation/, sprints/, monitoring/, errors/

scripts/
├── README.md (304 scripts organized)
├── wf02/ (159 files: state-machines/, generators/, fixes/)
├── wf05/ (16 files: generators/, fixes/)
├── wf06/ (1 file)
├── wf07/ (17 files: generators/, fixes/)
├── deployment/, testing/, validation/
├── migration/, utilities/, evolution/
└── docker/, deprecated/

n8n/workflows/
├── production/ (WF01, WF02, WF05, WF06, WF07)
├── development/ (wf02/, wf05/, wf06/)
└── historical/ (wf02/ V77-V113)
```

---

**Project**: E2 Soluções WhatsApp Bot | n8n 2.14.2 | Maintained: Claude Code
