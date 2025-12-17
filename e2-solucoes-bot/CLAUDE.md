# E2 Soluções WhatsApp Bot - Context for Claude Code

> **Critical Development Context** | Last Updated: 2025-12-15
> This document provides essential project context optimized for Claude Code comprehension and minimal auto-compaction.

---

## 🎯 Project Identity

**System**: Intelligent WhatsApp bot with Claude AI + RAG for E2 Soluções (Brazilian electrical engineering company)

**Core Function**: Automated lead qualification, technical analysis, appointment scheduling, and CRM integration

**Tech Stack**: n8n (orchestration) + Claude 3.5 Sonnet (AI) + Supabase (vector DB) + PostgreSQL (state) + Evolution API (WhatsApp) + RD Station CRM

**Language**: Portuguese (PT-BR) - All content, conversations, and documentation

---

## 📊 Current Implementation Status

### ✅ Completed (85% functional)
- **Infrastructure**: Docker dev environment with 11 services
- **Database**: Complete schema with 7 tables + 14 functions (Sprint 1.3: notifications table + 7 funções)
- **AI Agent**: Claude conversation flow with state machine
- **Vision AI**: Image analysis (energy bills, installation sites)
- **CRM Sync**: RD Station integration (contacts + deals)
- **Knowledge Base**: 5 service files (energia_solar, subestacao, projetos_eletricos, armazenamento_energia, analise_laudos)
- **Workflows**: 13 n8n workflows (Sprint 1.3: +3 novos workflows de notificação)
- **Email System**: 5 HTML templates + sending workflow
- **Appointments**: Google Calendar integration + reminders (24h + 2h)
- **Multi-Channel Notifications** (Sprint 1.3): Email + WhatsApp + Discord com retry automático e conformidade LGPD

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
WhatsApp (Evolution API)
    ↓
n8n Workflow Orchestrator (10 workflows)
    ├─→ Claude AI Agent (conversation + RAG + Vision)
    ├─→ PostgreSQL (state + leads + appointments)
    ├─→ Supabase (vector search for knowledge)
    ├─→ Google Calendar (appointment scheduling)
    ├─→ RD Station CRM (bidirectional sync)
    ├─→ Email/Discord (notifications)
    └─→ Google Drive (file storage)
```

### Critical Data Flow
1. **Message Reception**: Evolution API webhook → n8n workflow 01
2. **Conversation Processing**: State machine → Claude AI → RAG query
3. **Data Collection**: Service-specific structured data → PostgreSQL
4. **CRM Sync**: Auto-create contact + deal in RD Station
5. **Appointment**: Check availability → Create event → Send reminders
6. **Notifications**: Multi-channel (WhatsApp + Email + Discord)

---

## 📂 Project Structure (Essential Paths)

```
e2-solucoes-bot/
├── docker/
│   ├── docker-compose-dev.yml       # Dev environment (11 services)
│   ├── .env.dev.example             # Config template
│   └── configs/                     # Service configurations
├── database/
│   ├── schema.sql                   # Main PostgreSQL schema
│   ├── appointment_functions.sql    # Scheduling logic (9 functions)
│   └── supabase_functions.sql       # RAG functions
├── n8n/workflows/                   # 10 JSON workflows
│   ├── 01_main_whatsapp_handler.json
│   ├── 02_ai_agent_conversation.json
│   ├── 03_rag_knowledge_query.json
│   ├── 04_image_analysis.json
│   ├── 05_appointment_scheduler.json
│   ├── 06_appointment_reminders.json
│   ├── 07_send_email.json
│   ├── 08_rdstation_sync.json
│   ├── 09_rdstation_webhook_handler.json
│   └── 10_handoff_to_human.json
├── knowledge/servicos/              # 5 service descriptions (MD)
├── templates/emails/                # 5 HTML email templates
├── scripts/                         # Automation scripts
│   ├── start-dev.sh                 # Start dev environment
│   ├── ingest-knowledge.sh          # Generate embeddings
│   └── [backup, health-check, etc]
└── docs/                            # Organized documentation
    ├── PROJECT_STATUS.md            # High-level status
    ├── SPRINT_1.1_COMPLETE.md       # RAG implementation report
    ├── sprints/
    │   ├── README.md                # Sprint index
    │   └── SPRINT_1.2_PLANNING.md   # Scheduling implementation
    ├── validation/                  # Testing guides (10 files)
    ├── Setups/                      # Integration guides
    └── PLAN/                        # Architecture decisions
```

---

## 🔑 Critical Development Information

### Database Schema (6 tables)
1. **conversations**: State machine, tracks user journey stages
2. **messages**: Complete chat history
3. **leads**: Collected contact/service data
4. **appointments**: Scheduled visits with reminders
5. **knowledge_documents**: RAG vector embeddings
6. **rdstation_sync_log**: CRM sync audit trail

### Conversation States (State Machine)
```
greeting → identifying_service → collecting_data → scheduling →
completed | handoff_comercial | awaiting_documents
```

### E2 Services (5 types)
1. **Energia Solar**: Residential/commercial/industrial solar projects
2. **Subestação**: Substation reform, maintenance, construction
3. **Projetos Elétricos**: Electrical projects and compliance
4. **BESS (Armazenamento)**: Battery energy storage systems
5. **Análise e Laudos**: Energy analysis, quality audits, expert reports

### Environment Variables (Critical)
```bash
# AI & Embeddings
ANTHROPIC_API_KEY=sk-ant-xxx           # Claude API
OPENAI_API_KEY=sk-xxx                  # Embeddings (ada-002)

# WhatsApp
EVOLUTION_API_URL=https://evolution.xxx
EVOLUTION_API_KEY=xxx

# CRM
RDSTATION_CLIENT_ID=xxx
RDSTATION_CLIENT_SECRET=xxx
RDSTATION_REFRESH_TOKEN=xxx

# Databases
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=xxx
DATABASE_URL=postgresql://xxx

# Google Services
GOOGLE_SERVICE_ACCOUNT_EMAIL=xxx
GOOGLE_CALENDAR_ID=xxx
```

---

## 🚀 Quick Start Commands

### Development Environment
```bash
# Start all services
cd /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot
./scripts/start-dev.sh

# Access services
# n8n:              http://localhost:5678
# Supabase Studio:  http://localhost:3000
# PostgreSQL:       localhost:5432

# View logs
./scripts/logs.sh

# Stop environment
./scripts/stop.sh
```

### Testing & Validation
```bash
# Validate Sprint 1.1 (RAG)
# See: docs/validation/README.md (5-step guide)

# Validate Sprint 1.2 (Scheduling)
# See: docs/validation/SPRINT_1.2_VALIDATION.md

# Health check
./scripts/health-check.sh
```

---

## 🧠 AI Agent Configuration

### System Prompt Structure
- **Identity**: E2 Soluções virtual assistant (friendly, professional)
- **Capabilities**: Service information, data collection, image analysis, scheduling
- **Behavior**: Conversational (no menus), ask one question at a time, validate data
- **Tools**: RAG query, vision analysis, calendar check, CRM sync

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

### For Developers
- **Setup Guide**: `docs/validation/README.md` (5 detailed steps)
- **Architecture**: `docs/PLAN/implementation_plan.md`
- **Sprint Reports**: `docs/SPRINT_1.1_COMPLETE.md`, `docs/sprints/SPRINT_1.2_PLANNING.md`
- **RD Station Integration**: `docs/Setups/SETUP_RDSTATION.md` (462 lines)

### For Operations
- **Quick Start**: `QUICKSTART.md`
- **Project Status**: `docs/PROJECT_STATUS.md`
- **Deployment**: `docker/README.md`
- **Troubleshooting**: Each validation guide has dedicated section

### For Business Context
- **Main README**: `README.md` (comprehensive overview)
- **Service Descriptions**: `knowledge/servicos/*.md` (5 files)

---

## 🎯 Development Priorities

### Current Sprint Focus
1. **Validate Sprint 1.1**: Execute `docs/validation/README.md` (pending OpenAI token)
2. **Validate Sprint 1.2**: Test appointment system end-to-end
3. **Production Setup**: Create `docker-compose.yml` with SSL/Traefik

### Known Issues
- ⚠️ **OpenAI Token**: Expired, awaiting renewal for embedding generation
- ⚠️ **End-to-End Testing**: Needs manual validation of full conversation flow
- ℹ️ **Production Deploy**: Infrastructure defined but not deployed

### Next Features (Backlog)
- FAQ content expansion
- Technical specifications knowledge
- Portfolio case studies
- Analytics dashboard
- Automated testing suite

---

## 🔒 Security & Compliance

### Data Handling
- **LGPD Compliant**: Personal data stored in Brazil (Supabase BR region)
- **Encryption**: TLS for all external APIs, encrypted at rest
- **Secrets Management**: Docker secrets in production (not .env)
- **Access Control**: RLS policies on Supabase, auth on n8n

### API Rate Limits
- **Anthropic**: 50K requests/day (Claude)
- **OpenAI**: 3M tokens/min (embeddings)
- **RD Station**: 120 calls/min (CRM)
- **Evolution**: No documented limit (WhatsApp)

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
