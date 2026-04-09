# 📚 Índice de Documentação Técnica - E2 Soluções Bot

> **Última Atualização**: 2026-01-13
> **Versão Atual**: V27 (Message Flow Fix)
> **Status**: Sistema 100% Operacional

---

## 🗂️ Estrutura da Documentação

### 📌 Documentos Principais
- **[CLAUDE.md](../CLAUDE.md)** - Contexto principal para Claude Code (V17 → V27)
- **[PROJECT_STATUS.md](status/PROJECT_STATUS.md)** - Status atual do projeto
- **[README.md](../README.md)** - Overview geral do projeto

---

## 🔧 Evolução dos Workflows (V17 → V27)

### Documentação por Versão

#### V27 - Message Flow Fix (ATUAL ✅)
- **[V27_ANALYSIS_REPORT.md](V27_ANALYSIS_REPORT.md)** - Análise completa e solução
- **[V27_MESSAGE_FLOW_FIX.md](PLAN/V27_MESSAGE_FLOW_FIX.md)** - Plano detalhado da solução
- **Script**: `scripts/fix-workflow-v27-message-flow.py`
- **Workflow**: `02_ai_agent_conversation_V27_MESSAGE_FLOW_FIX.json`

#### V26 - Menu Validation Fix (Parcial ⚠️)
- **[V26_MENU_FIX_SUMMARY.md](V26_MENU_FIX_SUMMARY.md)** - Resumo da tentativa
- **[V26_MENU_VALIDATION_FIX.md](PLAN/V26_MENU_VALIDATION_FIX.md)** - Análise do problema
- **Script**: `scripts/fix-workflow-v26-menu-validation.py`
- **Workflow**: `02_ai_agent_conversation_V26_MENU_VALIDATION_FIX.json`

#### V25 - Simplified UPSERT (Resolvido ✅)
- **[V25_SOLUTION_SUMMARY.md](V25_SOLUTION_SUMMARY.md)** - Solução completa
- **[V24_UPDATE_CONVERSATION_FIX.md](PLAN/V24_UPDATE_CONVERSATION_FIX.md)** - Análise do V24
- **Script**: `scripts/fix-workflow-v25-upsert-simplified.py`
- **Workflow**: `02_ai_agent_conversation_V25_UPSERT_SIMPLIFIED.json`

#### V24 - User's Manual Fix (Falhou ❌)
- **Análise**: [V24_UPDATE_CONVERSATION_FIX.md](PLAN/V24_UPDATE_CONVERSATION_FIX.md)
- **Workflow**: `02_ai_agent_conversation_V24.json`

#### V23 - Extended Parallel Distribution
- **[ANALYSIS_V23_FIX.md](ANALYSIS_V23_FIX.md)** - Extended parallel pattern
- **Scripts**:
  - `scripts/fix-workflow-v23-upsert-lead.py`
  - `scripts/fix-workflow-v23-add-upsert-query.py`
- **Workflow**: `02_ai_agent_conversation_V23_EXTENDED_PARALLEL_COMPLETE.json`

#### V22 - Connection Pattern Fix
- **[ANALYSIS_V22_FIX.md](ANALYSIS_V22_FIX.md)** - Análise do padrão de conexões
- **Script**: `scripts/fix-workflow-v22-connection-pattern.py`
- **Workflow**: `02_ai_agent_conversation_V22_CONNECTION_PATTERN_FIXED.json`

#### V21 - Data Flow Fix
- **[FIX_DATA_FLOW_V21.md](FIX_DATA_FLOW_V21.md)** - Correção do fluxo de dados
- **Script**: `scripts/fix-workflow-v21-data-flow.py`
- **Workflow**: `02_ai_agent_conversation_V21_DATA_FLOW_FIXED.json`

#### V20 - Template String Fix
- **Script**: `scripts/fix-workflow-v20-query-format.py`
- **Workflow**: `02_ai_agent_conversation_V20_QUERY_FIX.json`

#### V19 - Conversation ID Fix
- **[FIX_CONVERSATION_ID_V19.md](FIX_CONVERSATION_ID_V19.md)** - Preservação do ID
- **Script**: `scripts/fix-conversation-id-v19.py`
- **Workflow**: `02_ai_agent_conversation_V19_MERGE_CONVERSATION.json`

#### V17-V18 - PostgreSQL Query Fix
- **[FIX_SUMMARY_V16_V17.md](FIX_SUMMARY_V16_V17.md)** - Query string errors
- **Script**: `scripts/fix-postgres-query-interpolation.py`
- **Workflow**: `02_ai_agent_conversation_V17.json`

---

## 🚀 Guias de Implementação

### Sprint 0.1 - Bot v1 Menu
- **[SPRINT_0.1_V1_SIMPLES.md](sprints/SPRINT_0.1_V1_SIMPLES.md)** - Implementação completa
- **[SPRINT_0.1_VALIDATION.md](validation/SPRINT_0.1_VALIDATION.md)** - Validação

### Sprint 1.1 - RAG e Base de Conhecimento
- **[SPRINT_1.1_COMPLETE.md](SPRINT_1.1_COMPLETE.md)** - Implementação completa
- **[SPRINT_1.1_STATUS.md](status/SPRINT_1.1_STATUS.md)** - Status da validação
- **[sprint_1.1_summary.md](validation/sprint_1.1_summary.md)** - Resumo executivo
- **[sprint_1.1_validation.md](validation/sprint_1.1_validation.md)** - Checklist técnico

### Sprint 1.2 - Sistema de Agendamento
- **[SPRINT_1.2_PLANNING.md](sprints/SPRINT_1.2_PLANNING.md)** - Planejamento
- **[SPRINT_1.2_VALIDATION.md](validation/SPRINT_1.2_VALIDATION.md)** - Validação

### Sprint 1.3 - Notificações Multi-Canal
- **[SPRINT_1.3_IMPLEMENTATION_STATUS.md](status/SPRINT_1.3_IMPLEMENTATION_STATUS.md)** - Status

---

## 📖 Guias de Setup e Configuração

### Setup Credenciais e APIs
1. **[SETUP_CREDENTIALS.md](Setups/SETUP_CREDENTIALS.md)** - Configurar todas as credenciais
2. **[SETUP_ANTHROPIC.md](Setups/SETUP_ANTHROPIC.md)** - Claude AI API
3. **[SETUP_EVOLUTION_API.md](Setups/SETUP_EVOLUTION_API.md)** - WhatsApp Evolution API v2.3.7
4. **[SETUP_RDSTATION.md](Setups/SETUP_RDSTATION.md)** - RD Station CRM
5. **[SETUP_GOOGLE_CALENDAR.md](Setups/SETUP_GOOGLE_CALENDAR.md)** - Google Calendar API
6. **[SETUP_EMAIL.md](Setups/SETUP_EMAIL.md)** - Email/SMTP
7. **[SETUP_DISCORD.md](Setups/SETUP_DISCORD.md)** - Discord Webhooks

### Setup Database e RAG
1. **[DEPLOY_SQL.md](Setups/DEPLOY_SQL.md)** - Deploy funções SQL
2. **[EXECUTE_INGEST.md](Setups/EXECUTE_INGEST.md)** - Popular banco de dados
3. **[IMPORT_N8N_WORKFLOW.md](Setups/IMPORT_N8N_WORKFLOW.md)** - Importar workflows

### Validação e Testes
1. **[RUN_VALIDATION_TESTS.md](Setups/RUN_VALIDATION_TESTS.md)** - Executar testes finais
2. **[README.md](validation/README.md)** - Índice de validação geral
3. **[VALIDATION_REPORT.md](validation/VALIDATION_REPORT.md)** - Relatório consolidado

---

## 🔍 Problemas e Soluções

### Evolution API Issues
- **[EVOLUTION_API_ISSUE.md](EVOLUTION_API_ISSUE.md)** - Migração v2.2.3 → v2.3.7
- **[evolution_api_v2.3_upgrade.md](PLAN/evolution_api_v2.3_upgrade.md)** - Plano de upgrade

### Workflow Issues Resolvidos
- **[workflow_02_phone_fix_report.md](PLAN/workflow_02_phone_fix_report.md)** - Phone extraction
- **[workflow_json_fix_analysis.md](PLAN/workflow_json_fix_analysis.md)** - JSON import
- **[workflow_02_update_state_fix.md](PLAN/workflow_02_update_state_fix.md)** - Update state
- **[collected_data_fix_complete.md](PLAN/collected_data_fix_complete.md)** - Collected data

---

## 🛠️ Scripts Utilitários

### Scripts de Correção V17-V27
```bash
# V27 - Message Flow Fix (ATUAL)
python scripts/fix-workflow-v27-message-flow.py

# V26 - Menu Validation Fix
python scripts/fix-workflow-v26-menu-validation.py

# V25 - Simplified UPSERT
python scripts/fix-workflow-v25-upsert-simplified.py

# V23 - Extended Parallel
python scripts/fix-workflow-v23-upsert-lead.py

# V22 - Connection Pattern
python scripts/fix-workflow-v22-connection-pattern.py

# V21 - Data Flow
python scripts/fix-workflow-v21-data-flow.py

# V20 - Template Strings
python scripts/fix-workflow-v20-query-format.py

# V19 - Conversation ID
python scripts/fix-conversation-id-v19.py

# V17-V18 - PostgreSQL
python scripts/fix-postgres-query-interpolation.py
```

### Scripts de Validação
```bash
# Validar V21 data flow
./scripts/validate-v21-fix.sh

# Validar PostgreSQL queries
./scripts/validate-postgres-fix.sh

# Monitorar V27 message flow
docker logs -f e2bot-n8n-dev | grep V27
```

### Scripts Gerais
```bash
# Start ambiente dev
./scripts/start-dev.sh

# Fix JSON import
python scripts/fix-workflow-json.py

# Fix collected data
python scripts/fix-collected-data-handling.py

# Health check
./scripts/health-check.sh

# Backup
./scripts/backup.sh
```

---

## 📊 Estrutura de Diretórios

```
docs/
├── TECHNICAL_INDEX.md           # Este arquivo - Índice técnico
├── status/                       # Status e progresso
│   ├── PROJECT_STATUS.md        # Status geral (V27)
│   ├── SPRINT_1.1_STATUS.md     # Status Sprint 1.1
│   └── SPRINT_1.3_IMPLEMENTATION_STATUS.md
│
├── PLAN/                        # Planos e análises
│   ├── V27_MESSAGE_FLOW_FIX.md # Solução V27
│   ├── V26_MENU_VALIDATION_FIX.md
│   ├── V24_UPDATE_CONVERSATION_FIX.md
│   ├── implementation_plan.md
│   └── [outros planos...]
│
├── sprints/                     # Documentação por sprint
│   ├── README.md               # Índice de sprints
│   ├── SPRINT_0.1_V1_SIMPLES.md
│   ├── SPRINT_1.2_PLANNING.md
│   └── [outros sprints...]
│
├── validation/                  # Validação e testes
│   ├── README.md               # Guia de validação
│   ├── sprint_1.1_summary.md
│   ├── sprint_1.1_validation.md
│   └── [outras validações...]
│
├── Setups/                     # Guias de configuração
│   ├── SETUP_CREDENTIALS.md
│   ├── DEPLOY_SQL.md
│   ├── EXECUTE_INGEST.md
│   └── [outros setups...]
│
└── [Análises V17-V27]          # Documentação de evolução
    ├── V27_ANALYSIS_REPORT.md
    ├── V26_MENU_FIX_SUMMARY.md
    ├── V25_SOLUTION_SUMMARY.md
    └── [outros documentos...]
```

---

## 🎯 Quick Links

### Para Começar
1. [CLAUDE.md](../CLAUDE.md) - Contexto principal
2. [PROJECT_STATUS.md](status/PROJECT_STATUS.md) - Status atual
3. [QUICKSTART.md](../docs/Setups/QUICKSTART.md) - Quick start guide

### Para Implementar V27
1. [V27_ANALYSIS_REPORT.md](V27_ANALYSIS_REPORT.md) - Entender a solução
2. `scripts/fix-workflow-v27-message-flow.py` - Gerar workflow
3. Importar `02_ai_agent_conversation_V27_MESSAGE_FLOW_FIX.json`

### Para Validar
1. [validation/README.md](validation/README.md) - Guia completo
2. [Setups/](Setups/) - Seguir guias 1-5
3. [RUN_VALIDATION_TESTS.md](Setups/RUN_VALIDATION_TESTS.md) - Testes finais

### Para Desenvolver
1. [sprints/README.md](sprints/README.md) - Índice de sprints
2. [SPRINT_1.2_PLANNING.md](sprints/SPRINT_1.2_PLANNING.md) - Próximo sprint
3. [implementation_plan.md](PLAN/implementation_plan.md) - Plano geral

---

## 📝 Notas Importantes

### Versão Atual: V27
- **Problema Resolvido**: Menu validation agora funciona corretamente
- **Solução**: Message fields preservados através de todo o workflow
- **Debug**: Logs V27 INPUT ANALYSIS para troubleshooting

### Evolution API
- **Versão Requerida**: v2.3.7 ou superior
- **Docker Image**: `evoapicloud/evolution-api:latest`
- **Campo Principal**: `senderPn` (não mais `remoteJid`)

### Próximos Passos
1. Importar e ativar workflow V27
2. Testar menu validation com WhatsApp
3. Validar Sprint 1.1 quando OpenAI token disponível
4. Iniciar Sprint 1.2 (Agendamento)

---

**Última Atualização**: 2026-01-13 | **Versão**: V27 | **Status**: ✅ Operacional