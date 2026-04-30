# E2 Bot - Documentation Overview

> **Version**: 3.0 | **Last Updated**: 2026-04-29
> **Status**: ✅ ORGANIZED - Single source of truth structure implemented

---

## 📋 Quick Navigation

### 🎯 Essential Documents

| Document | Description | Location |
|-----------|-----------|-------------|
| **INDEX.md** | Complete documentation catalog | `/docs/INDEX.md` ⭐ |
| **QUICKSTART.md** | Initial setup guide (30-45 min) | `/docs/Setups/QUICKSTART.md` ⭐ |
| **SETUP_EMAIL.md** | SMTP configuration (Port 465) | `/docs/Setups/SETUP_EMAIL.md` ⭐ |
| **SETUP_GOOGLE_CALENDAR.md** | OAuth2 Google Calendar | `/docs/Setups/SETUP_GOOGLE_CALENDAR.md` ⭐ |
| **SETUP_CREDENTIALS.md** | All n8n credentials | `/docs/Setups/SETUP_CREDENTIALS.md` ⭐ |
| **DEPLOYMENT_STATUS.md** | Current deployment status | `/docs/status/DEPLOYMENT_STATUS.md` ⭐ |
| **PRODUCTION_V1_DEPLOYMENT.md** | Production V1 guide | `/docs/status/PRODUCTION_V1_DEPLOYMENT.md` ⭐ |

---

## 📁 Documentation Structure

### Organized by Category (2026-04-29)

```
docs/
├── INDEX.md                            Complete documentation catalog
├── README.md                           This file - Documentation overview
│
├── guidelines/ (8 comprehensive guides) ⭐ NEW (2026-04-29)
│   ├── README.md                       Guidelines organization guide
│   ├── 00_VISAO_GERAL.md               Arquitetura conceitual do sistema ⭐
│   ├── 01_N8N_BEST_PRACTICES.md        Limitações n8n 2.x e workarounds ⭐
│   ├── 02_STATE_MACHINE_PATTERNS.md    Padrão central de conversação ⭐
│   ├── 03_DATABASE_PATTERNS.md         Schema e queries PostgreSQL ⭐
│   ├── 04_WORKFLOW_INTEGRATION.md      Comunicação microserviços ⭐
│   ├── 05_TESTING_VALIDATION.md        Estratégias de teste
│   ├── 06_DEPLOYMENT_GUIDE.md          Processo de deployment
│   └── 07_SECURITY_COMPLIANCE.md       Segurança e LGPD
│
├── development/ (6 practical guides) ⭐ NEW (2026-04-29)
│   ├── README.md                       Development navigation guide ⭐
│   ├── 01_WORKFLOW_MODIFICATION.md     Modificar workflows ⭐
│   ├── 02_DEBUGGING_GUIDE.md           Debug e troubleshooting ⭐
│   ├── 03_COMMON_TASKS.md              Tarefas comuns ⭐
│   ├── 04_CODE_REVIEW_CHECKLIST.md     Checklist de revisão ⭐
│   └── 05_LOCAL_SETUP.md               Setup ambiente local (30-60 min) ⭐
│
├── diagrams/ (3 visual diagrams) ⭐ NEW (2026-04-29)
│   ├── README.md                       Diagrams navigation guide ⭐
│   ├── 01_SYSTEM_ARCHITECTURE.md       Arquitetura completa (850 lines) ⭐
│   └── 02_STATE_MACHINE_FLOW.md        15 estados detalhados (750 lines) ⭐
│
├── analysis/                           Technical analyses (7 subdirectories)
│   ├── DOCUMENTATION_REPORT.md         Current documentation report
│   ├── TECHNICAL_INDEX.md              Technical index and reference
│   ├── wf02-versions/                  WF02 version analyses
│   ├── wf07-versions/                  WF07 version analyses
│   ├── system/                         System-wide analyses
│   └── migrations/                     Migration analyses
│
├── deployment/                         Deployment guides (7 subdirectories)
│   ├── README.md                       Deployment organization guide ⭐
│   ├── wf02/                           WF02 deployments (v74-v79, v80-v99, v100-v114)
│   ├── wf05/                           WF05 deployments
│   ├── wf06/                           WF06 deployments
│   ├── wf07/                           WF07 deployments
│   └── production/                     Production deployment guides
│
├── fix/                                Bug fix reports (7 subdirectories)
│   ├── README.md                       Bug fix organization guide ⭐
│   ├── wf02/                           WF02 bug fixes (v63-v79, v80-v99, v100-v114)
│   ├── wf05/                           WF05 bug fixes
│   ├── wf06/                           WF06 bug fixes
│   ├── wf07/                           WF07 bug fixes
│   └── system/                         System-wide bug fixes
│
├── PLAN/                               Planning documents (10 subdirectories)
│   ├── README.md                       Planning organization guide ⭐
│   ├── wf01/                           WF01 planning (general, versions)
│   ├── wf02/                           WF02 planning (v16-v79, v80-v114, general)
│   ├── wf05/                           WF05 planning (versions)
│   ├── wf06/                           WF06 planning
│   ├── wf07/                           WF07 planning
│   ├── system/                         System-wide planning
│   └── infrastructure/                 Infrastructure planning
│
├── status/                             Status tracking (2 subdirectories)
│   ├── README.md                       Status organization guide ⭐
│   ├── DEPLOYMENT_STATUS.md            Current deployment status ⭐
│   ├── PRODUCTION_V1_DEPLOYMENT.md     Production V1 deployment guide ⭐
│   ├── DOCUMENTATION_UPDATE_SUMMARY.md Latest documentation updates
│   └── historical/                     Historical status documents
│
├── implementation/                     Implementation guides (16 files)
│   ├── WF02 implementation guides (V76, V77, V78, V93)
│   ├── WF05 implementation guides
│   └── WF06 implementation guides
│
├── Setups/                             Setup and configuration (13 files)
│   ├── QUICKSTART.md                   Complete setup guide (30-45 min) ⭐
│   ├── SETUP_EMAIL.md                  SMTP configuration (Port 465 SSL/TLS) ⭐
│   ├── SETUP_GOOGLE_CALENDAR.md        Google Calendar OAuth2 ⭐
│   ├── SETUP_CREDENTIALS.md            All n8n credentials ⭐
│   └── [other setup guides]
│
├── Guides/                             User guides
├── validation/                         Validation and testing
├── sprints/                            Sprint documentation
├── monitoring/                         Monitoring documentation
└── errors/                             Error logs and screenshots
```

---

## 🗂️ Documentation by Category

### 📖 Guidelines (Conceptual - "What and Why") ⭐ NEW
- **Location**: `/docs/guidelines/`
- **Purpose**: Conceptual architecture guides and system patterns
- **Total**: 8 comprehensive guides (~5,900 lines)
- **Key Files**:
  - `00_VISAO_GERAL.md` - Arquitetura conceitual do sistema ⭐
  - `01_N8N_BEST_PRACTICES.md` - Limitações n8n 2.x e workarounds ⭐
  - `02_STATE_MACHINE_PATTERNS.md` - Padrão central (15 estados) ⭐
  - `03_DATABASE_PATTERNS.md` - Schema e queries PostgreSQL ⭐
  - `04_WORKFLOW_INTEGRATION.md` - Comunicação microserviços ⭐
  - `05_TESTING_VALIDATION.md` - Estratégias de teste
  - `06_DEPLOYMENT_GUIDE.md` - Processo de deployment
  - `07_SECURITY_COMPLIANCE.md` - Segurança e LGPD
- **When to Use**: Understanding system architecture, design patterns, strategic decisions

### 💻 Development (Practical - "How to") ⭐ NEW
- **Location**: `/docs/development/`
- **Purpose**: Practical step-by-step development guides
- **Total**: 6 practical guides (~3,373 lines)
- **Key Files**:
  - `README.md` - Complete navigation guide ⭐
  - `01_WORKFLOW_MODIFICATION.md` - Modificar workflows na prática ⭐
  - `02_DEBUGGING_GUIDE.md` - Debug e troubleshooting ⭐
  - `03_COMMON_TASKS.md` - Tarefas comuns passo a passo ⭐
  - `04_CODE_REVIEW_CHECKLIST.md` - Checklist de revisão completo ⭐
  - `05_LOCAL_SETUP.md` - Setup ambiente local (30-60 min) ⭐
- **When to Use**: Implementing features, debugging, code review, local development

### 🎨 Diagrams (Visual - "See It") ⭐ NEW
- **Location**: `/docs/diagrams/`
- **Purpose**: Visual architecture diagrams (ASCII format for terminal compatibility)
- **Total**: 3 comprehensive diagrams (~1,880 lines)
- **Key Files**:
  - `README.md` - Diagrams navigation guide ⭐
  - `01_SYSTEM_ARCHITECTURE.md` - Arquitetura completa do sistema (850 lines) ⭐
  - `02_STATE_MACHINE_FLOW.md` - 15 estados detalhados (750 lines) ⭐
- **When to Use**: Onboarding new developers, understanding system flow, architecture review

### 📚 Setup & Configuration (Start Here!)
- **Location**: `/docs/Setups/`
- **Purpose**: Complete setup and configuration guides
- **Key Files**:
  - `QUICKSTART.md` - Complete setup (30-45 min) ⭐
  - `SETUP_EMAIL.md` - SMTP Port 465 SSL/TLS ⭐
  - `SETUP_GOOGLE_CALENDAR.md` - OAuth2 configuration ⭐
  - `SETUP_CREDENTIALS.md` - All n8n credentials ⭐

### 📊 Production Status
- **Location**: `/docs/status/`
- **Purpose**: Current deployment status and production guides
- **Key Files**:
  - `DEPLOYMENT_STATUS.md` - Current production status ⭐
  - `PRODUCTION_V1_DEPLOYMENT.md` - Production V1 guide ⭐
  - `DOCUMENTATION_UPDATE_SUMMARY.md` - Latest updates
- **Organization**: See `/docs/status/README.md` for complete guide

### 🚀 Deployment Guides
- **Location**: `/docs/deployment/`
- **Purpose**: Deployment procedures organized by workflow and version
- **Total**: 51 deployment documents
- **Organization**: See `/docs/deployment/README.md` for complete guide
- **Structure**:
  - `wf02/v74-v79/` - Early WF02 versions (6 files)
  - `wf02/v80-v99/` - Mid WF02 versions (21 files)
  - `wf02/v100-v114/` - Recent WF02 versions (13 files) ⭐
  - `wf05/` - WF05 deployments (5 files)
  - `wf06/` - WF06 deployments (2 files)
  - `wf07/` - WF07 deployments (3 files)
  - `production/` - Production deployment guides (1 file)

### 🐛 Bug Fixes
- **Location**: `/docs/fix/`
- **Purpose**: Complete bug fix documentation
- **Total**: 82 bug fix reports
- **Organization**: See `/docs/fix/README.md` for complete guide
- **Structure**:
  - `wf02/v63-v79/` - Early WF02 fixes (19 files)
  - `wf02/v80-v99/` - Mid WF02 fixes (8 files)
  - `wf02/v100-v114/` - Recent WF02 fixes (21 files) ⭐
  - `wf05/` - WF05 fixes (6 files)
  - `wf06/` - WF06 fixes (3 files)
  - `wf07/` - WF07 fixes (15 files)
  - `system/` - System-wide fixes (10 files)

### 📋 Planning Documents
- **Location**: `/docs/PLAN/`
- **Purpose**: Strategic planning and implementation plans
- **Total**: 137 planning documents
- **Organization**: See `/docs/PLAN/README.md` for complete guide
- **Structure**:
  - `wf01/` - WF01 planning (11 files)
  - `wf02/` - WF02 planning (85 files)
  - `wf05/` - WF05 planning (10 files)
  - `wf06/` - WF06 planning (1 file)
  - `wf07/` - WF07 planning (2 files)
  - `system/` - System-wide planning (10 files)
  - `infrastructure/` - Infrastructure planning (18 files)

### 🔍 Technical Analysis
- **Location**: `/docs/analysis/`
- **Purpose**: Technical analyses and investigations
- **Total**: 53 analysis documents
- **Key Areas**:
  - WF02 version analyses
  - WF07 version analyses
  - System-wide analyses
  - Migration analyses

### 💻 Implementation Guides
- **Location**: `/docs/implementation/`
- **Purpose**: Workflow implementation documentation
- **Total**: 16 implementation guides
- **Focus**: WF02, WF05, WF06 implementation details

---

## 🎯 How to Find Documentation

### By Workflow

**WF01 (Main WhatsApp Handler)**:
- **Status**: ✅ Production V2.8.3
- **Planning**: `/docs/PLAN/wf01/` (11 files)

**WF02 (AI Agent Conversation)**:
- **Status**: ✅ Production V114 COMPLETE
- **Current**: `/docs/deployment/wf02/v100-v114/WF02_V114_PRODUCTION_DEPLOYMENT.md` ⭐
- **Quick Deploy V111**: `/docs/WF02_V111_QUICK_DEPLOY.md` (database row locking)
- **Quick Deploy V114**: `/docs/WF02_V114_QUICK_DEPLOY.md` (TIME fields)
- **Bug Fixes**: `/docs/fix/wf02/` (48 files)
- **Planning**: `/docs/PLAN/wf02/` (85 files)
- **Deployment**: `/docs/deployment/wf02/` (40 files)

**WF05 (Appointment Scheduler)**:
- **Status**: ✅ Production V7 Hardcoded
- **Deployment**: `/docs/deployment/wf05/DEPLOY_WF05_V7_HARDCODED_FINAL.md` ⭐
- **Bug Fixes**: `/docs/fix/wf05/` (6 files)
- **Planning**: `/docs/PLAN/wf05/` (10 files)

**WF06 (Calendar Availability Service)**:
- **Status**: ✅ Production V2.2
- **Deployment**: `/docs/deployment/wf06/DEPLOY_WF06_V2_1_COMPLETE_FIX.md` ⭐
- **Planning**: `/docs/PLAN/wf06/PLAN_WF06_V2_OAUTH_FIX.md` ⭐
- **Bug Fixes**: `/docs/fix/wf06/` (3 files)

**WF07 (Send Email)**:
- **Status**: ✅ Production V13
- **Bug Fix V13**: `/docs/fix/wf07/BUGFIX_WF07_V13_INSERT_SELECT_FIX.md` ⭐
- **nginx Planning**: `/docs/PLAN/wf07/PLAN_NGINX_WF07_IMPLEMENTATION.md` ⭐
- **SMTP Setup**: `/docs/Setups/SETUP_EMAIL.md` (Port 465 SSL/TLS) ⭐
- **Bug Fixes**: `/docs/fix/wf07/` (15 files)

### By Error Type

| Error Message | Documentation |
|---------------|---------------|
| Template access denied | `/docs/PLAN/wf07/PLAN_NGINX_WF07_IMPLEMENTATION.md` |
| $env access denied | `/docs/deployment/wf05/DEPLOY_WF05_V7_HARDCODED_FINAL.md` |
| queryReplacement [undefined] | `/docs/fix/wf07/BUGFIX_WF07_V13_INSERT_SELECT_FIX.md` |
| Module 'fs' is disallowed | `/docs/analysis/system/ANALYSIS_N8N_VERSION_UPGRADE_VS_WORKAROUNDS.md` |
| Database row locking | `/docs/deployment/wf02/v100-v114/DEPLOY_WF02_V111_DATABASE_ROW_LOCKING.md` |
| PostgreSQL TIME fields | `/docs/WF02_V114_QUICK_DEPLOY.md` |

### By Task Type

| Task | Primary Documentation |
|------|----------------------|
| **Initial Setup** | `/docs/Setups/QUICKSTART.md` ⭐ |
| **Configure Email** | `/docs/Setups/SETUP_EMAIL.md` ⭐ |
| **Configure Calendar** | `/docs/Setups/SETUP_GOOGLE_CALENDAR.md` ⭐ |
| **Deploy WF02 V114** | `/docs/WF02_V114_QUICK_DEPLOY.md` ⭐ |
| **Deploy WF05 V7** | `/docs/deployment/wf05/DEPLOY_WF05_V7_HARDCODED_FINAL.md` ⭐ |
| **Deploy WF06 V2.1** | `/docs/deployment/wf06/DEPLOY_WF06_V2_1_COMPLETE_FIX.md` ⭐ |
| **Check Production Status** | `/docs/status/DEPLOYMENT_STATUS.md` ⭐ |

---

## 📊 Documentation Statistics

**Total Organized**: 320+ documents across 18 categories ⭐ UPDATED
- **guidelines/**: 8 files (~5,900 lines) ⭐ NEW - Conceptual architecture
- **development/**: 6 files (~3,373 lines) ⭐ NEW - Practical guides
- **diagrams/**: 3 files (~1,880 lines) ⭐ NEW - Visual architecture
- **analysis/**: 53 files (technical analyses)
- **deployment/**: 51 files (deployment guides)
- **fix/**: 82 files (bug fix reports)
- **PLAN/**: 137 files (planning documents)
- **status/**: 47 files (status tracking)
- **implementation/**: 16 files (implementation guides)
- **Setups/**: 13 files (setup guides)

**New Documentation (2026-04-29)**: 17 files (~11,153 lines)
**Organization Date**: 2026-04-29
**Current Production**: V1 (WF01 V2.8.3, WF02 V114, WF05 V7, WF06 V2.2, WF07 V13)

---

## 🔧 Critical Configurations

### SMTP (Port 465 + SSL/TLS)
```yaml
Host: smtp.gmail.com
Port: 465
Secure: true  # ✅ SSL/TLS (marcar checkbox)
User: seu-email@gmail.com
Password: [App Password sem espaços]
```

**Documentation**: `/docs/Setups/SETUP_EMAIL.md` ⭐

### Google Calendar OAuth2
```yaml
Client ID: xxxxxxxx.apps.googleusercontent.com
Client Secret: GOCSPX-xxxxxxxxxxxxx
Redirect URI: http://localhost:5678/rest/oauth2-credential/callback
```

**Documentation**: `/docs/Setups/SETUP_GOOGLE_CALENDAR.md` ⭐

### PostgreSQL
```yaml
Host: e2bot-postgres-dev
Database: e2bot_dev
User: postgres
Password: CoraRosa
Port: 5432
```

**Documentation**: `/docs/Setups/SETUP_CREDENTIALS.md` ⭐

---

## 📝 Documentation Standards

### File Organization Principles

1. **Single Source of Truth**: Each document exists in exactly one location
2. **Zero Duplication**: No duplicate files anywhere in repository
3. **Clear Categorization**: Documents organized by purpose (analysis, fix, deployment, planning, status)
4. **Workflow Grouping**: Workflow-specific documents grouped by version ranges
5. **Comprehensive READMEs**: Each major directory has organization guide

### Naming Conventions

```
CATEGORY_SUBJECT_VERSION_DESCRIPTION.md

Categories:
- ANALYSIS: Technical analysis documents
- BUGFIX: Bug fix reports and resolutions
- DEPLOY: Deployment procedures
- PLAN: Implementation planning
- SETUP: Configuration guides
- WF0X: Workflow-specific documents

Examples:
- BUGFIX_WF02_V111_DATABASE_STATE_RACE_CONDITION.md
- DEPLOY_WF05_V7_HARDCODED_FINAL.md
- ANALYSIS_N8N_VERSION_UPGRADE_VS_WORKAROUNDS.md
- PLAN_WF06_V2_OAUTH_FIX.md
```

---

## 🎓 Learning Resources

### For Beginners ⭐ UPDATED

**Quick Start (2 hours)**:
1. **Setup Local Environment**: `/docs/development/05_LOCAL_SETUP.md` ⭐ (30-60 min)
2. **Understand Architecture**: `/docs/guidelines/00_VISAO_GERAL.md` ⭐ (15 min)
3. **See System Diagrams**: `/docs/diagrams/01_SYSTEM_ARCHITECTURE.md` ⭐ (20 min)
4. **Check Production Status**: `/docs/status/DEPLOYMENT_STATUS.md` ⭐ (10 min)

**Alternative Path (Operations Focus)**:
1. **Start Here**: `/docs/Setups/QUICKSTART.md` ⭐ (30-45 min)
2. **Understand Credentials**: `/docs/Setups/SETUP_CREDENTIALS.md` ⭐
3. **Learn n8n Limitations**: `/docs/guidelines/01_N8N_BEST_PRACTICES.md` ⭐
4. **Check Production Status**: `/docs/status/DEPLOYMENT_STATUS.md` ⭐

### For Developers ⭐ UPDATED

**Essential Reading**:
1. **Project Context**: `CLAUDE.md` (root) ⭐
2. **Documentation Index**: `/docs/INDEX.md` ⭐
3. **Architecture Overview**: `/docs/guidelines/00_VISAO_GERAL.md` ⭐
4. **State Machine Pattern**: `/docs/guidelines/02_STATE_MACHINE_PATTERNS.md` ⭐
5. **Development Guide**: `/docs/development/README.md` ⭐

**Practical Guides**:
- **Modify Workflows**: `/docs/development/01_WORKFLOW_MODIFICATION.md` ⭐
- **Debug Issues**: `/docs/development/02_DEBUGGING_GUIDE.md` ⭐
- **Common Tasks**: `/docs/development/03_COMMON_TASKS.md` ⭐
- **Code Review**: `/docs/development/04_CODE_REVIEW_CHECKLIST.md` ⭐

**Historical Reference**:
- **Bug Fix History**: `/docs/fix/` (organized by workflow)
- **Planning History**: `/docs/PLAN/` (organized by workflow)
- **Analysis History**: `/docs/analysis/` (organized by category)

### For Operations

1. **Production Status**: `/docs/status/PRODUCTION_V1_DEPLOYMENT.md` ⭐
2. **Deployment Guides**: `/docs/deployment/` (organized by workflow)
3. **Current Status**: `/docs/status/DEPLOYMENT_STATUS.md` ⭐
4. **Setup Procedures**: `/docs/Setups/` (all configuration guides)

---

## 📦 Organization History

### Organization Timeline

- **2026-04-08**: Initial reorganization (moved files from root to categories)
- **2026-04-29 Morning**: Complete organization with subdirectories:
  - analysis/ organized into 7 subdirectories (53 files)
  - deployment/ organized into 7 subdirectories (51 files)
  - fix/ organized into 7 subdirectories (82 files)
  - PLAN/ organized into 10 subdirectories (137 files)
  - status/ organized into 2 subdirectories (47 files)
  - All documentation updated to reflect organized structure
- **2026-04-29 Evening**: New documentation tier creation ⭐
  - guidelines/ created (8 comprehensive guides, ~5,900 lines)
  - development/ created (6 practical guides, ~3,373 lines)
  - diagrams/ created (3 visual diagrams, ~1,880 lines)
  - CLAUDE.md, INDEX.md, README.md updated to reflect new tiers
  - Total: 17 new documentation files (~11,153 lines)

### Documentation Coverage

**Complete Coverage**:
- ✅ All workflows documented (WF01, WF02, WF05, WF06, WF07)
- ✅ All production versions documented (V2.8.3, V114, V7, V2.2, V13)
- ✅ Complete bug fix history (82 reports)
- ✅ Complete deployment history (51 guides)
- ✅ Complete planning history (137 documents)
- ✅ Complete analysis history (53 documents)
- ✅ Zero duplicate files
- ✅ Single source of truth structure

### Benefits of Organization

- ✅ **Clear Navigation**: Documents grouped by category and workflow
- ✅ **Consistent Naming**: All directories use English naming
- ✅ **Organized by Purpose**: Analysis, bugfixes, deploys clearly separated
- ✅ **Centralized Setups**: Configuration guides in one location
- ✅ **Noise Reduction**: Files organized by functionality
- ✅ **QUICKSTART Consolidated**: Single file in `/docs/Setups/QUICKSTART.md`
- ✅ **Workflows Organized**: 7 active, 57 in `/old/` for historical reference
- ✅ **Version Range Strategy**: Large version histories split into manageable ranges
- ✅ **Comprehensive READMEs**: Navigation guides in each major directory
- ✅ **Three-Tier Documentation** ⭐ NEW: Guidelines (conceptual) + Development (practical) + Diagrams (visual)
- ✅ **Comprehensive Onboarding**: 2-hour path for new developers with clear learning progression
- ✅ **Visual Architecture**: ASCII diagrams for terminal-compatible system visualization

---

## 🔍 Complete Index

For a comprehensive catalog of all available documents, consult:

**📖 `/docs/INDEX.md`** - Complete documentation catalog with descriptions and status ⭐

---

**Last Updated**: 2026-04-29
**Maintained**: E2 Soluções Dev Team | Claude Code
**Status**: ✅ ORGANIZED - Single source of truth structure implemented
**Next Step**: Consult `/docs/INDEX.md` for complete catalog
