# 🤖 E2 Soluções AI Bot v3

> **Status**: ✅ Sprints 1.1 e 1.2 Completos (75% Funcional) | 🧪 Aguardando Validação
> **Última Atualização**: 2025-12-15

Bot inteligente de WhatsApp com Claude AI, RAG e integração completa com RD Station CRM para automação de atendimento e qualificação de leads da E2 Soluções (empresa brasileira de engenharia elétrica).

---

## ⚡ Quick Start (5 minutos)

### Pré-requisitos
```bash
✓ Docker e Docker Compose instalados
✓ Git
✓ Credenciais configuradas (ver docs/QUICKSTART.md)
```

### Instalação Rápida
```bash
# Clonar repositório
git clone <repo-url>
cd e2-solucoes-bot

# Configurar ambiente de desenvolvimento
cp docker/.env.dev.example docker/.env.dev
nano docker/.env.dev  # Configurar API keys

# Iniciar ambiente
./scripts/start-dev.sh
```

### Acessar Serviços
| Serviço | URL | Descrição |
|---------|-----|-----------|
| **n8n** | http://localhost:5678 | Workflows e configuração |
| **Supabase Studio** | http://localhost:3000 | Interface do banco de dados |
| **PostgreSQL** | localhost:5432 | Banco principal (e2_bot) |
| **Traefik Dashboard** | http://localhost:8080 | Status dos serviços |

📘 **Documentação Completa**: `docs/QUICKSTART.md` (guia detalhado)

---

## 🎯 O Que o Bot Faz

### Funcionalidades Implementadas ✅

**Conversação Inteligente**:
- 🤖 Processamento de linguagem natural com Claude 3.5 Sonnet
- 💬 Conversas contextualizadas sem menus rígidos
- 🧠 Memória persistente de conversas
- 🔍 Consulta automática à base de conhecimento (RAG)

**Análise Inteligente**:
- 👁️ Vision AI: analisa fotos de contas de energia e locais de instalação
- 📊 Extração de dados: consumo kWh, tensão, tipo de instalação
- ⚡ Dimensionamento automático: calcula potência solar necessária (kWp)
- 💰 Estimativas: economia mensal, número de painéis

**Agendamento Automatizado**:
- 📅 Integração completa com Google Calendar
- 🔄 Verificação automática de disponibilidade
- ⏰ Lembretes 24h e 2h antes da visita (WhatsApp + Email)
- 📧 Confirmações por email com template profissional
- ♻️ Sistema de reagendamento automático

**CRM Integrado (RD Station)**:
- 👤 Criação automática de contatos
- 💼 Gestão de deals no pipeline
- 🔄 Sincronização bidirecional
- 📝 Registro automático de notas e tarefas
- 📊 Auditoria completa de sincronizações

**Notificações Multi-canal**:
- ✉️ Emails automatizados (5 templates HTML responsivos)
- 💬 Discord webhooks para equipe comercial
- 📱 WhatsApp para cliente (confirmações e lembretes)

### Serviços E2 Soluções (5 tipos)

| Serviço | Descrição | Dados Coletados |
|---------|-----------|-----------------|
| ☀️ **Energia Solar** | Projetos residenciais, comerciais, industriais | Consumo kWh, fotos conta/local, interesse em bateria |
| ⚡ **Subestação** | Reformas, manutenção, construção | Tensão, tipo de serviço, urgência, fotos |
| 📐 **Projetos Elétricos** | Projetos e regularizações | Tipo, carga estimada, documentação |
| 🔋 **BESS (Armazenamento)** | Sistemas de baterias | Objetivo, potência necessária, integração solar |
| 📊 **Análise e Laudos** | Análise de consumo, qualidade, perícia | Tipo análise, histórico, descrição problema |

---

## 🏗️ Arquitetura do Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                  WHATSAPP (Evolution API)                   │
└───────────────────────┬─────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│               n8n WORKFLOW ORCHESTRATOR                     │
│                    (10 workflows)                           │
│  ┌─────────────────────────────────────────────────────┐    │
│  │         🤖 CLAUDE AI AGENT (3.5 Sonnet)             │    │
│  │  • Conversação natural em português                 │    │
│  │  • RAG: Base de conhecimento E2 (5 serviços)      │    │
│  │  • Vision AI: Análise de imagens                   │    │
│  │  • Memória persistente                             │    │
│  └─────────────────────────────────────────────────────┘    │
│         ↓              ↓              ↓             ↓        │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐  ┌──────────┐  │
│  │PostgreSQL│   │ Supabase │   │  Google  │  │RD Station│  │
│  │  State   │   │  Vector  │   │ Services │  │   CRM    │  │
│  │ + Leads  │   │   RAG    │   │Cal+Drive │  │ Pipeline │  │
│  └──────────┘   └──────────┘   └──────────┘  └──────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Fluxo de Dados Crítico
1. **Recepção**: WhatsApp → Evolution API webhook → n8n workflow 01
2. **Processamento**: Máquina de estados → Claude AI → RAG query
3. **Coleta**: Dados estruturados por serviço → PostgreSQL
4. **Sincronização**: Auto-criação contato + deal no RD Station
5. **Agendamento**: Verificar disponibilidade → Criar evento → Lembretes
6. **Notificações**: Multi-canal (WhatsApp + Email + Discord)

---

## 📊 Status de Implementação

### ✅ Sprint 1.1 - RAG e Base de Conhecimento (100%)
**Status**: Implementado | **Validação**: Pendente (aguarda token OpenAI)

**Componentes**:
- ✅ Base de conhecimento (5 serviços, 1.380+ linhas)
- ✅ Script de ingestão (`scripts/ingest-knowledge.sh`, 515 linhas)
- ✅ Funções Supabase otimizadas (221 linhas SQL)
- ✅ Workflow n8n RAG (232 linhas JSON)
- ✅ Documentação de validação completa

📄 **Relatório**: `docs/SPRINT_1.1_COMPLETE.md`
🧪 **Validação**: `docs/validation/README.md` (guia 5 passos)

---

### ✅ Sprint 1.2 - Sistema de Agendamento (100%)
**Status**: Implementado | **Validação**: Pendente (testes end-to-end)

**Componentes**:
- ✅ Integração Google Calendar API
- ✅ Lógica de disponibilidade e conflitos (9 funções SQL)
- ✅ Sistema de lembretes (24h + 2h antes)
- ✅ Sincronização RD Station CRM (bidirecional)
- ✅ Notificações multi-canal (5 templates email)
- ✅ Workflow de reagendamento
- ✅ Follow-up pós-visita

📄 **Planejamento**: `docs/sprints/SPRINT_1.2_PLANNING.md`
🧪 **Validação**: `docs/validation/SPRINT_1.2_VALIDATION.md`

---

## 📂 Estrutura do Projeto

```
e2-solucoes-bot/
├── CLAUDE.md                    # ⭐ Contexto otimizado para Claude Code
├── README.md                    # Este arquivo - Overview geral
│
├── docker/                      # Infraestrutura containerizada
│   ├── docker-compose-dev.yml   # Ambiente de desenvolvimento
│   ├── .env.dev.example         # Template de configuração
│   ├── README.md                # Documentação Docker
│   └── configs/                 # Configurações dos serviços
│
├── database/                    # Schema e funções SQL
│   ├── schema.sql               # Schema principal (6 tabelas)
│   ├── appointment_functions.sql # 9 funções de agendamento
│   └── supabase_functions.sql   # Funções RAG e vector search
│
├── n8n/workflows/               # 10 workflows n8n
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
│
├── knowledge/                   # Base de conhecimento RAG
│   └── servicos/                # 5 arquivos de serviços E2
│       ├── energia_solar.md
│       ├── subestacao.md
│       ├── projetos_eletricos.md
│       ├── armazenamento_energia.md
│       └── analise_laudos.md
│
├── templates/emails/            # 5 templates HTML responsivos
│   ├── novo_lead.html
│   ├── confirmacao_agendamento.html
│   ├── lembrete_24h.html
│   ├── lembrete_2h.html
│   └── apos_visita.html
│
├── scripts/                     # Scripts de automação
│   ├── start-dev.sh             # Iniciar ambiente
│   ├── ingest-knowledge.sh      # Gerar embeddings
│   ├── logs.sh                  # Ver logs
│   ├── health-check.sh          # Validar sistema
│   └── [backup, restore, migrate]
│
└── docs/                        # 📚 Documentação organizada
    ├── QUICKSTART.md            # Guia rápido
    ├── PROJECT_STATUS.md        # Status consolidado
    ├── SPRINT_1.1_COMPLETE.md   # Relatório Sprint 1.1
    │
    ├── sprints/                 # Documentação por sprint
    │   ├── README.md            # Índice de sprints
    │   ├── SPRINT_1.2_PLANNING.md
    │   └── SPRINT_1.2_COMPLETE.md
    │
    ├── validation/              # Guias de validação
    │   ├── README.md            # Índice validação
    │   ├── SETUP_CREDENTIALS.md
    │   ├── DEPLOY_SQL.md
    │   ├── EXECUTE_INGEST.md
    │   ├── IMPORT_N8N_WORKFLOW.md
    │   ├── RUN_VALIDATION_TESTS.md
    │   ├── SPRINT_1.2_VALIDATION.md
    │   └── VALIDATION_REPORT.md
    │
    ├── status/                  # Relatórios de status
    │   └── IMPLEMENTATION_STATUS.md
    │
    ├── Setups/                  # Guias de configuração
    │   └── SETUP_RDSTATION.md   # RD Station CRM (462 linhas)
    │
    └── PLAN/                    # Planejamento e arquitetura
        └── implementation_plan.md
```

---

## 🛠️ Stack Tecnológica

| Camada | Tecnologia | Versão | Função |
|--------|------------|--------|--------|
| **Orquestração** | n8n | latest | Workflow automation |
| **IA Principal** | Claude 3.5 Sonnet | 20241022 | Conversação e análise |
| **Vision AI** | Claude Vision | 3.5 | Análise de imagens |
| **Embeddings** | OpenAI ada-002 | - | RAG embeddings |
| **Vector DB** | Supabase + pgvector | 15.1 | Busca semântica |
| **Database** | PostgreSQL | 15 | Estado e dados |
| **CRM** | RD Station CRM | API v1 | Gestão de leads |
| **WhatsApp** | Evolution API | - | Mensageria |
| **Gateway** | Traefik | 2.10 | Reverse proxy |
| **Storage** | Google Drive | API v3 | Armazenamento |
| **Agenda** | Google Calendar | API v3 | Agendamentos |

---

## 🔐 Variáveis de Ambiente Críticas

**Mínimo para DEV:**
```bash
# APIs Essenciais
ANTHROPIC_API_KEY=sk-ant-xxx      # Claude AI
OPENAI_API_KEY=sk-xxx             # Embeddings (ada-002)
EVOLUTION_API_URL=https://xxx
EVOLUTION_API_KEY=xxx

# RD Station CRM
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

📄 Ver lista completa: `docker/.env.dev.example`

---

## 📚 Documentação Completa

### Para Começar
| Documento | Descrição | Tempo |
|-----------|-----------|-------|
| [QUICKSTART.md](docs/QUICKSTART.md) | Guia rápido de início | 15 min |
| [CLAUDE.md](CLAUDE.md) | Contexto para Claude Code | 10 min leitura |
| [PROJECT_STATUS.md](docs/PROJECT_STATUS.md) | Status consolidado | 5 min |

### Validação e Testes
| Documento | Descrição | Tempo |
|-----------|-----------|-------|
| [Validação Sprint 1.1](docs/validation/README.md) | 5 passos detalhados | 2-3 horas |
| [Validação Sprint 1.2](docs/validation/SPRINT_1.2_VALIDATION.md) | Testes agendamento | 1-2 horas |

### Implementação
| Documento | Descrição |
|-----------|-----------|
| [Sprint 1.1 Completo](docs/SPRINT_1.1_COMPLETE.md) | Relatório RAG (100%) |
| [Sprint 1.2 Planning](docs/sprints/SPRINT_1.2_PLANNING.md) | Agendamento (100%) |
| [Setup RD Station](docs/Setups/SETUP_RDSTATION.md) | Integração CRM completa |
| [Implementation Plan](docs/PLAN/implementation_plan.md) | Plano geral do projeto |

---

## 🧪 Como Validar o Sistema

### Sprint 1.1 - RAG (Pendente)
```bash
# Seguir guia de 5 passos
cat docs/validation/README.md

# Etapas:
# 1. Configurar credenciais (30-45 min)
# 2. Deploy funções SQL (10-15 min)
# 3. Executar ingest (15-20 min) ⚠️ Aguarda token OpenAI
# 4. Importar workflow n8n (10-15 min)
# 5. Validar sistema (20-30 min)
```

### Sprint 1.2 - Agendamento (Pendente)
```bash
# Seguir guia detalhado
cat docs/validation/SPRINT_1.2_VALIDATION.md

# Testes end-to-end:
# - Verificar disponibilidade
# - Criar agendamento
# - Validar lembretes
# - Testar reagendamento
```

---

## 🚀 Próximos Passos

### Imediato (Prioridade ALTA)
1. ✅ **Validar Sprint 1.1**: Executar `docs/validation/README.md` (aguarda OpenAI token)
2. ✅ **Validar Sprint 1.2**: Testes end-to-end do sistema de agendamento
3. 📋 **Deploy Produção**: Criar `docker-compose.yml` com SSL/Traefik

### Backlog (Prioridade MÉDIA)
- Expandir base de conhecimento (FAQ, specs técnicas, portfolio)
- Scripts de backup/restore automatizados
- Dashboard de métricas e analytics
- Testes automatizados (unit + E2E)

---

## 🤝 Contribuindo

Para desenvolvimento local:
```bash
# 1. Configurar ambiente
./scripts/start-dev.sh

# 2. Acessar n8n
# http://localhost:5678

# 3. Editar workflows
# Modificar JSONs em n8n/workflows/
# Re-importar no n8n UI

# 4. Validar mudanças
./scripts/health-check.sh
```

---

## 📞 Suporte e Recursos

### Documentação Técnica
- **Claude Code Context**: `CLAUDE.md` (contexto otimizado)
- **Quick Start**: `docs/QUICKSTART.md`
- **Validação Completa**: `docs/validation/` (10 guias)
- **Status do Projeto**: `docs/PROJECT_STATUS.md`

### Troubleshooting
Cada guia de validação contém seção dedicada de troubleshooting com problemas comuns e soluções.

---

## 📄 Licença

Proprietário - E2 Soluções

---

**Última Atualização**: 2025-12-15
**Versão**: 3.0
**Status**: ✅ Sprints 1.1 e 1.2 Implementados | 🧪 Aguardando Validação
