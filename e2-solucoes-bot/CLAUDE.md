# E2 Soluções WhatsApp Bot - Context for Claude Code

> **Critical Development Context** | Last Updated: 2025-01-12 (V22 Complete)
> This document provides essential project context optimized for Claude Code comprehension and minimal auto-compaction.

---

## 🎯 Project Identity

**System**: Intelligent WhatsApp bot with Claude AI + RAG for E2 Soluções (Brazilian electrical engineering company)

**Core Function**: Automated lead qualification, technical analysis, appointment scheduling, and CRM integration

**Tech Stack**: n8n (orchestration) + Claude 3.5 Sonnet (AI) + Supabase (vector DB) + PostgreSQL (state) + Evolution API (WhatsApp) + RD Station CRM

**Language**: Portuguese (PT-BR) - All content, conversations, and documentation

---

## 🚨 Critical Issues Resolved (2025-01-12)

### Complete Workflow Evolution (V17 → V22)
**V17-V18**: Query String Errors
- **Problem**: "Parameter 'query' must be a text string" errors
- **Solution**: Build SQL Queries node returning pure strings
- **Scripts**: `scripts/fix-postgres-query-interpolation.py`

**V19**: Conversation ID Null
- **Problem**: `conversation_id` sempre null causando menu loop
- **Solution**: Merge Conversation Data node preservando ID
- **Scripts**: `scripts/fix-conversation-id-v19.py`

**V20**: Template String Processing
- **Problem**: Template strings `{{ }}` não processadas pelo PostgreSQL
- **Solution**: Build Update Queries node com SQL puro
- **Scripts**: `scripts/fix-workflow-v20-query-format.py`

**V21**: Data Flow Issues
- **Problem**: Build Update Queries não recebia dados completos
- **Solution**: Conexão direta State Machine → Build Update Queries
- **Scripts**: `scripts/fix-workflow-v21-data-flow.py`

**V22 (CURRENT)**: Connection Pattern Fix ✅
- **Problem**: Save Message nodes recebiam database rows ao invés de queries
- **Error**: "Cannot read properties of undefined (reading 'match')"
- **Solution**: Build Update Queries conecta em paralelo para TODOS os nodes
- **Scripts**: `scripts/fix-workflow-v22-connection-pattern.py`
- **Workflow atual**: `02_ai_agent_conversation_V22_CONNECTION_PATTERN_FIXED.json`

### Evolution API v2.2.3 → v2.3.7 Migration
**Problem**: Evolution API v2.2.3 had critical phone number extraction issues
- `remoteJid` field contained malformed data: `55629817554855629817@s.whatsapp.net`
- Duplicate country codes breaking phone number validation
- Complex regex parsing required and prone to errors

**Solution**: Upgraded to Evolution API v2.3.7
- New `senderPn` field provides clean phone numbers
- Docker image: `evoapicloud/evolution-api:latest` (NOT atendai repository)
- Workflow updated with fallback: check `senderPn` first, then `remoteJid`

### Workflow JSON Import Issues
**Problem**: n8n couldn't import workflow files due to invalid JSON formatting
- Unescaped newlines in JavaScript code blocks
- Control characters in multi-line strings

**Solution**: Created Python script to properly escape JSON
- Fixed files: `01_main_whatsapp_handler_V2.3_FIXED_IMPORT.json`
- Script: `scripts/fix-workflow-json.py`

### Database collected_data Handling
**Problem**: Update Conversation State node failing with "No output data returned"
- Direct `JSON.stringify()` in SQL templates causing issues
- Undefined values and special characters breaking queries

**Solution**: Added data preparation layer
- New "Prepare Update Data" node for safe data handling
- PostgreSQL JSONB casting with `::jsonb`
- Fixed workflow: `02_ai_agent_conversation_V1_MENU_FIXED_v3.json`

---

## 📊 Current Implementation Status

### ✅ Completed (90% functional)
- **Infrastructure**: Docker dev environment with 11 services
- **Database**: Complete schema with 7 tables + 14 functions (Sprint 1.3: notifications table + 7 funções)
- **AI Agent**: Claude conversation flow with state machine (v1 Menu-based)
- **Vision AI**: Image analysis (energy bills, installation sites)
- **CRM Sync**: RD Station integration (contacts + deals)
- **Knowledge Base**: 5 service files (energia_solar, subestacao, projetos_eletricos, armazenamento_energia, analise_laudos)
- **Workflows**: 13 n8n workflows (Sprint 1.3: +3 novos workflows de notificação)
- **Email System**: 5 HTML templates + sending workflow
- **Appointments**: Google Calendar integration + reminders (24h + 2h)
- **Multi-Channel Notifications** (Sprint 1.3): Email + WhatsApp + Discord com retry automático e conformidade LGPD
- **Evolution API v2.3.7**: Phone extraction fixed with senderPn field
- **Data Flow**: Complete pipeline from WhatsApp → State Machine → Database → CRM

### ⚠️ Validation Pending
- **Sprint 1.1 (RAG)**: Implemented but awaiting OpenAI token for embedding generation
- **Sprint 1.2 (Scheduling)**: Implemented, needs end-to-end testing
- **Sprint 1.3 (Notifications)**: Implementado e testado, aguardando validação E2E completa

### 🚧 Future Work
- Production deployment (SSL, Traefik, backups)
- Extended knowledge base (FAQ, technical specs, portfolio)
- Automated testing suite (Sprint 1.3: testes SQL e bash criados)

---

## 🏗️ Architecture Overview

```
WhatsApp User (Evolution API v2.3.7)
    ↓ [webhook with senderPn field]
n8n Workflow 01 - WhatsApp Handler
    ↓ [phone extraction priority: senderPn → remoteJid]
n8n Workflow 02 - AI Agent V22 (Menu State Machine)
    ├─→ State Machine Logic (conversation flow)
    ├─→ Build Update Queries (parallel distribution) ⚡
    │   ├─→ Update Conversation State (query_update_conversation)
    │   ├─→ Save Inbound Message (query_save_inbound)
    │   ├─→ Save Outbound Message (query_save_outbound)
    │   └─→ Send WhatsApp Response (phone_number + response_text)
    ├─→ Claude AI Agent (Portuguese conversations)
    ├─→ Supabase (vector search for knowledge)
    ├─→ Google Calendar (appointment scheduling)
    ├─→ RD Station CRM (bidirectional sync)
    └─→ Email/Discord (multi-channel notifications)
```

### Critical Data Flow V22 (FIXED) ✅
1. **Message Reception**: Evolution API v2.3.7 webhook → n8n workflow 01
   - Phone extraction: `data.senderPn || extractFromRemoteJid(data.key.remoteJid)`
2. **State Machine Processing**: Logic determina próximo estado e resposta
3. **Query Building**: Build Update Queries constrói todas as SQL queries
4. **Parallel Distribution**: Queries distribuídas em PARALELO para todos os nodes
   - Update Conversation State recebe `query_update_conversation`
   - Save Inbound Message recebe `query_save_inbound`
   - Save Outbound Message recebe `query_save_outbound`
   - Send WhatsApp Response recebe `phone_number` e `response_text`
5. **Data Persistence**: PostgreSQL JSONB para collected_data
6. **CRM Sync**: Auto-create contact + deal in RD Station
7. **Notifications**: Multi-channel (WhatsApp + Email + Discord)

---

## 📂 Project Structure (Essential Paths)

```
e2-solucoes-bot/
├── docker/
│   ├── docker-compose-dev.yml       # Dev environment (Evolution v2.3.7)
│   ├── .env.dev.example             # Config template
│   └── configs/                     # Service configurations
├── database/
│   ├── schema.sql                   # PostgreSQL schema (JSONB collected_data)
│   ├── appointment_functions.sql    # Scheduling logic (9 functions)
│   └── supabase_functions.sql       # RAG functions
├── n8n/workflows/                   # Workflows principais + versões
│   ├── 01_main_whatsapp_handler_V2.3_FIXED_IMPORT.json  # Handler principal
│   ├── 02_ai_agent_conversation_V22_CONNECTION_PATTERN_FIXED.json  # ⭐ VERSÃO ATUAL V22
│   ├── 02_ai_agent_conversation_V21_DATA_FLOW_FIXED.json  # V21 - Data flow direto
│   ├── 02_ai_agent_conversation_V20_QUERY_FIX.json  # V20 - Template strings
│   ├── 02_ai_agent_conversation_V19_MERGE_CONVERSATION.json  # V19 - Conversation ID
│   ├── 02_ai_agent_conversation_V17.json  # V17 - Build SQL Queries
│   ├── 03_rag_knowledge_query.json
│   ├── 04_image_analysis.json
│   ├── 05_appointment_scheduler.json
│   ├── 06_appointment_reminders.json
│   ├── 07_send_email.json
│   ├── 08_rdstation_sync.json
│   ├── 09_rdstation_webhook_handler.json
│   ├── 10_handoff_to_human.json
│   ├── 11_notification_email.json
│   ├── 12_notification_whatsapp.json
│   ├── 13_notification_discord.json
│   └── [Versões anteriores V1-V16 preservadas para histórico]
├── knowledge/servicos/              # 5 service descriptions (MD)
├── templates/emails/                # 5 HTML email templates
├── scripts/                         # Automation & fix scripts
│   ├── start-dev.sh                 # Start dev environment
│   ├── fix-workflow-json.py         # Fix JSON import issues
│   ├── fix-workflow-02-connections.py  # Fix phone_number flow
│   ├── fix-update-conversation-node.py # Fix no output issue
│   ├── fix-collected-data-handling.py  # Fix collected_data
│   ├── fix-postgres-query-interpolation.py  # ✨ V16-V18: Build SQL Queries
│   ├── fix-conversation-id-v19.py           # ✨ V19: Merge Conversation ID
│   ├── fix-workflow-v20-query-format.py     # ✨ V20: Template strings fix
│   ├── fix-workflow-v21-data-flow.py        # ✨ V21: Direct data flow
│   ├── fix-workflow-v22-connection-pattern.py # ✨ V22: Parallel connections
│   ├── validate-v21-fix.sh                  # ✨ Validação V21
│   ├── validate-postgres-fix.sh             # ✨ Validação PostgreSQL
│   └── [backup, health-check, etc]
└── docs/                            # Complete documentation
    ├── status/PROJECT_STATUS.md     # High-level status
    ├── EVOLUTION_API_ISSUE.md       # v2.2.3 → v2.3.7 migration
    ├── FIX_SUMMARY_V16_V17.md       # V16-V17: PostgreSQL queries
    ├── FIX_CONVERSATION_ID_V19.md   # V19: Conversation ID fix
    ├── FIX_DATA_FLOW_V21.md         # V21: Data flow documentation
    ├── ANALYSIS_V22_FIX.md          # V22: Connection pattern analysis
    ├── PLAN/                        # Technical solutions
    │   ├── evolution_api_v2.3_upgrade.md
    │   ├── workflow_02_phone_fix_report.md
    │   ├── workflow_json_fix_analysis.md
    │   ├── workflow_02_update_state_fix.md
    │   └── collected_data_fix_complete.md
    ├── sprints/                     # Sprint documentation
    ├── validation/                  # Testing guides
    └── Setups/                      # Integration guides
```

---

## 🔑 Critical Development Information

### Database Schema (7 tables)
1. **conversations**: State machine with JSONB collected_data field
2. **messages**: Complete chat history with conflict handling
3. **leads**: Contact/service data with JSONB storage
4. **appointments**: Scheduled visits with reminders
5. **knowledge_documents**: RAG vector embeddings
6. **rdstation_sync_log**: CRM sync audit trail
7. **notifications**: Multi-channel notification tracking

### Conversation States (Menu-Based State Machine v1)
```
greeting → service_selection → collect_name → collect_phone →
collect_email → collect_city → confirmation →
scheduling | handoff_comercial | completed
```

### E2 Services (5 types)
1. **Energia Solar** (ID: 1): Projetos fotovoltaicos
2. **Subestação** (ID: 2): Reforma, manutenção, construção
3. **Projetos Elétricos** (ID: 3): Adequações e laudos
4. **BESS** (ID: 4): Armazenamento de energia
5. **Análise e Laudos** (ID: 5): Qualidade de energia

### Critical Workflows

#### Workflow 01 - WhatsApp Handler (v2.3 Fixed)
- Receives Evolution API v2.3.7 webhooks
- Extracts phone using priority: `senderPn` → `remoteJid`
- Formats Brazilian phone numbers correctly
- Passes clean data to Workflow 02

#### Workflow 02 - AI Agent V22 (Connection Pattern Fixed) ✅
- **Current Version**: V22 - Parallel query distribution
- **Key Architecture**: Build Update Queries → Parallel connections to all nodes
- **State Machine**: Menu-based conversation flow (8 states)
- **Query Distribution**:
  - Update Conversation State: Receives `query_update_conversation`
  - Save Inbound Message: Receives `query_save_inbound`
  - Save Outbound Message: Receives `query_save_outbound`
  - Send WhatsApp Response: Receives `phone_number` + `response_text`
- **Data Safety**: PostgreSQL JSONB for collected_data
- **Error Prevention**: `alwaysOutputData: true` on all database nodes

### Environment Variables (Critical)
```bash
# AI & Embeddings
ANTHROPIC_API_KEY=sk-ant-xxx           # Claude API
OPENAI_API_KEY=sk-xxx                  # Embeddings (ada-002)

# WhatsApp (Evolution v2.3.7)
EVOLUTION_API_URL=http://evolution:8080
EVOLUTION_API_KEY=xxx
EVOLUTION_INSTANCE_NAME=e2-solucoes-bot

# CRM
RDSTATION_CLIENT_ID=xxx
RDSTATION_CLIENT_SECRET=xxx
RDSTATION_REFRESH_TOKEN=xxx

# Databases
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=xxx
DATABASE_URL=postgresql://postgres:xxx@postgres:5432/e2_bot

# Google Services
GOOGLE_SERVICE_ACCOUNT_EMAIL=xxx
GOOGLE_CALENDAR_ID=xxx
```

---

## 🚀 Quick Start Commands

### Development Environment
```bash
# Start all services (Evolution API v2.3.7)
cd /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot
./scripts/start-dev.sh

# Access services
# n8n:              http://localhost:5678
# Supabase Studio:  http://localhost:3000
# PostgreSQL:       localhost:5432
# Evolution API:    http://localhost:8080

# View logs
docker logs -f e2bot-evolution-dev  # Check v2.3.7
docker logs -f e2bot-n8n-dev

# Stop environment
./scripts/stop.sh
```

### Import Fixed Workflows
```bash
# In n8n interface (http://localhost:5678)
# 1. Import Workflow 01:
#    01_main_whatsapp_handler_V2.3_FIXED_IMPORT.json
# 2. Import Workflow 02 V22 (CURRENT):
#    02_ai_agent_conversation_V22_CONNECTION_PATTERN_FIXED.json
# 3. Deactivate old versions (V17-V21)
# 4. Activate V22 workflow
```

### Testing & Validation
```bash
# Check Evolution API version
curl http://localhost:8080/manager/status | jq .version
# Should show: "2.3.7"

# Test phone extraction
# Send WhatsApp message and check logs
docker logs -f e2bot-n8n-dev | grep "phone_number"

# Validate database
docker exec e2bot-postgres-dev psql -U postgres -d e2_bot \
  -c "SELECT phone_number, collected_data FROM conversations ORDER BY created_at DESC LIMIT 1;"
```

---

## 🧠 AI Agent Configuration

### System Prompt Structure (Menu-Based v1)
- **Identity**: E2 Soluções assistant (friendly, professional)
- **Behavior**: Menu-driven conversation, one question at a time
- **Validation**: Brazilian phone format, email validation
- **Error Handling**: Max 3 errors before handoff to human

### State Machine Features
- **Service Selection**: 1-5 numeric options
- **Data Collection**: Progressive form filling
- **Validation**: Real-time input validation
- **Error Recovery**: Graceful error handling with retry limits
- **Collected Data**: Safely stored as PostgreSQL JSONB

### RAG Configuration
- **Chunk Size**: 500-1000 chars
- **Embedding Model**: OpenAI text-embedding-ada-002 (1536 dims)
- **Similarity Threshold**: 0.75 (cosine)
- **Max Results**: 5 per query
- **Vector Search**: Supabase pgvector with ivfflat index

### Vision AI (Claude)
- **Model**: Claude 3.5 Sonnet
- **Use Cases**: Energy bill analysis, installation site photos
- **Extraction**: kWh consumption, voltage, installation type, area estimate

---

## 📋 Documentation Map

### Critical Technical Documents - V22 Evolution
- **V22 Analysis**: `docs/ANALYSIS_V22_FIX.md` (Current connection pattern fix)
- **V21 Data Flow**: `docs/FIX_DATA_FLOW_V21.md` (Direct data flow implementation)
- **V19 Conversation ID**: `docs/FIX_CONVERSATION_ID_V19.md` (ID preservation fix)
- **V16-V17 PostgreSQL**: `docs/FIX_SUMMARY_V16_V17.md` (Query string fixes)
- **Evolution API Issue**: `docs/EVOLUTION_API_ISSUE.md` (v2.2.3 → v2.3.7)
- **Phone Fix Report**: `docs/PLAN/workflow_02_phone_fix_report.md`
- **JSON Import Fix**: `docs/PLAN/workflow_json_fix_analysis.md`
- **collected_data Fix**: `docs/PLAN/collected_data_fix_complete.md`

### For Developers
- **Setup Guide**: `docs/validation/README.md` (5 detailed steps)
- **Architecture**: `docs/PLAN/implementation_plan.md`
- **Sprint Reports**: `docs/sprints/` directory
- **RD Station Integration**: `docs/Setups/SETUP_RDSTATION.md`

### For Operations
- **Quick Start**: `QUICKSTART.md`
- **Project Status**: `docs/PROJECT_STATUS.md`
- **Deployment**: `docker/README.md`
- **Troubleshooting**: `docs/EVOLUTION_API_ISSUE.md`

### For Business Context
- **Main README**: `README.md` (comprehensive overview)
- **Service Descriptions**: `knowledge/servicos/*.md` (5 files)

---

## 🎯 Development Priorities

### Immediate Actions
1. ✅ **Evolution API v2.3.7**: Successfully migrated
2. ✅ **Workflow Fixes**: All critical issues resolved
3. ⏳ **Validate RAG**: Awaiting OpenAI token renewal
4. ⏳ **E2E Testing**: Full conversation flow validation needed

### Known Issues (Resolved)
- ✅ **Evolution API v2.2.3**: Fixed by upgrading to v2.3.7
- ✅ **JSON Import**: Fixed with escaping script
- ✅ **Phone Undefined**: Fixed with proper data flow
- ✅ **collected_data**: Fixed with data preparation node

### Next Features (Backlog)
- FAQ content expansion
- Technical specifications knowledge
- Portfolio case studies
- Analytics dashboard
- Automated testing suite
- Production deployment

---

## 🔒 Security & Compliance

### Data Handling
- **LGPD Compliant**: Personal data stored in Brazil
- **Encryption**: TLS for all external APIs
- **Secrets Management**: Docker secrets for production
- **Access Control**: RLS on Supabase, auth on n8n

### API Rate Limits
- **Anthropic**: 50K requests/day
- **OpenAI**: 3M tokens/min
- **RD Station**: 120 calls/min
- **Evolution**: No documented limit

---

## 💡 Critical Fix Scripts

### V22 - Connection Pattern Fix (CURRENT) ✅
```bash
python3 scripts/fix-workflow-v22-connection-pattern.py
# Fixes parallel query distribution to all nodes
# Resolves "Cannot read properties of undefined" error
```

### V21 - Data Flow Fix
```bash
python3 scripts/fix-workflow-v21-data-flow.py
# Direct connection State Machine → Build Update Queries
```

### V20 - Template String Fix
```bash
python3 scripts/fix-workflow-v20-query-format.py
# Fixes template string processing in PostgreSQL
```

### V19 - Conversation ID Fix
```bash
python3 scripts/fix-conversation-id-v19.py
# Preserves conversation_id through state transitions
```

### V17-V18 - PostgreSQL Query Fix
```bash
python3 scripts/fix-postgres-query-interpolation.py
# Build SQL Queries returning pure strings
```

### Validation Scripts
```bash
./scripts/validate-v21-fix.sh  # Validates V21 data flow
./scripts/validate-postgres-fix.sh  # Validates PostgreSQL queries
```

---

## 💡 Claude Code Usage Tips

### When Analyzing Code
```bash
# Read workflow structure
Read n8n/workflows/02_ai_agent_conversation.json

# Check database schema
Read database/schema.sql

# Review service knowledge
Read knowledge/servicos/energia_solar.md
```

### When Making Changes
```bash
# Always check current documentation first
Read docs/PROJECT_STATUS.md

# For workflow changes: validate JSON structure
# For database changes: test in dev first
# For documentation: maintain consistency with existing structure
```

### Common Tasks
- **Add new service**: Create `knowledge/servicos/new_service.md` (follow template)
- **Modify workflow**: Edit JSON in `n8n/workflows/`, re-import to n8n
- **Update schema**: Add to `database/migrations/`, run `./scripts/migrate.sh`
- **Change AI prompt**: Edit `n8n/workflows/02_ai_agent_conversation.json`

---

## 📞 Support & Resources

### External Documentation
- **n8n**: https://docs.n8n.io
- **Claude API**: https://docs.anthropic.com
- **Supabase**: https://supabase.com/docs
- **RD Station CRM**: https://developers.rdstation.com/pt-BR/reference/crm

### Internal Knowledge
- **Validation Procedures**: `docs/validation/` (10 detailed guides)
- **Sprint Planning**: `docs/sprints/` (implementation roadmaps)
- **Setup Guides**: `docs/Setups/` (integration walkthroughs)

---

## ⚙️ Technical Decisions & Rationale

### Why n8n?
- Visual workflow editor for non-developers
- Self-hosted (no vendor lock-in)
- Native integrations with all required services
- Easy debugging and monitoring

### Why Supabase?
- PostgreSQL + pgvector for RAG
- Built-in auth and RLS
- Realtime subscriptions
- Dashboard for debugging

### Why Claude AI?
- Best-in-class Portuguese comprehension
- Vision capabilities for image analysis
- Long context window (200K tokens)
- Reliable structured output

### Why RD Station?
- Dominant CRM in Brazilian market
- E2 Soluções already uses it
- Robust API with webhooks
- Pipeline management features

---

**End of Critical Context Document**

For detailed implementation details, refer to:
- **Full Implementation Report**: `docs/SPRINT_1.1_COMPLETE.md`
- **Architecture Deep Dive**: `docs/PLAN/implementation_plan.md`
- **Validation Checklist**: `docs/validation/README.md`
