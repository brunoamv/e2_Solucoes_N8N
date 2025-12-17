# E2 Soluções Bot - Sprints Documentation

Documentação organizada por sprint do projeto E2 Soluções Bot.

---

## 📊 Status Geral dos Sprints

| Sprint | Título | Status | Documentação |
|--------|--------|--------|--------------|
| **0.1** | **Bot v1 Menu-Based (Sem IA)** | 🆕 **NOVO** | `docs/sprints/SPRINT_0.1_V1_SIMPLES.md` |
| 1.1 | RAG e Base de Conhecimento | ✅ COMPLETO | `docs/SPRINT_1.1_COMPLETE.md` |
| 1.2 | Sistema de Agendamento | ✅ COMPLETO | `docs/sprints/SPRINT_1.2_PLANNING.md` |
| 1.3 | Sistema de Notificações | ✅ INTEGRADO (Sprint 1.2) | - |
| 1.4 | CRM Bidirecional | ✅ INTEGRADO (Sprint 1.2) | - |
| 1.5 | Handoff para Humanos | ✅ INTEGRADO (Sprint 1.2) | - |

---

## 🆕 Sprint 0.1 - Bot v1 Menu-Based (Sem Claude AI)

**Status**: 🆕 NOVO - PRONTO PARA IMPLEMENTAÇÃO

**Objetivo**: Lançar bot funcional em 2-3 dias com menu fixo, sem custos de IA (R$ 50/mês)

**Motivação**: Evitar custos iniciais de Anthropic Claude (~R$ 27/mês) e OpenAI (~R$ 0,80/mês) durante fase de testes

**Arquitetura**:
- ✅ Menu fixo com 5 opções de serviço (1-5)
- ✅ State machine com 8 estados (greeting → completed)
- ✅ Validadores JavaScript (telefone, email, cidade)
- ✅ Integração com Workflows 05 (agendamento) e 10 (handoff)
- ⚠️ **SEM** Claude AI (Workflow 02 substituído)
- ⚠️ **SEM** RAG (Workflow 03 desabilitado)
- ⚠️ **SEM** Vision AI (Workflow 04 desabilitado)

**Deliverables Implementados**:
- ✅ Workflow 02 v1 (menu-based) - 16 nodes n8n (`n8n/workflows/02_ai_agent_conversation_V1_MENU.json`)
- ✅ 4 Scripts de automação (`scripts/deploy-v1.sh`, `test-v1-menu.sh`, `rollback-to-v2.sh`, `upgrade-v1-to-v2.sh`)
- ✅ 9 Templates WhatsApp + README detalhado (`templates/whatsapp/v1/`)
- ✅ Documentação completa (1.400+ linhas em `docs/sprints/SPRINT_0.1_V1_SIMPLES.md`)

**Componentes Criados** (2025-12-16):
- ✅ **Workflow n8n**: 02_ai_agent_conversation_V1_MENU.json (16 nodes, 250+ linhas JavaScript)
- ✅ **Scripts Bash**:
  - `deploy-v1.sh` (350+ linhas) - Deploy automatizado v1
  - `test-v1-menu.sh` (450+ linhas) - Testes automatizados
  - `rollback-to-v2.sh` (300+ linhas) - Reverter para Claude AI
  - `upgrade-v1-to-v2.sh` (450+ linhas) - Upgrade v1 → v2
- ✅ **Templates WhatsApp**: 9 arquivos .txt + README (1.200+ linhas)
- ✅ **Documentação**: SPRINT_0.1_V1_SIMPLES.md (1.400+ linhas)

**Custos Mensais**:
- **v1 Simple (este sprint)**: R$ 50/mês (só Evolution API)
- **v2 AI (futuro)**: R$ 78/mês (+ Anthropic + OpenAI)
- **Economia inicial**: R$ 28/mês (56% menos)

**Métricas Esperadas**:
- Taxa de conversão: 30% (vs 60% v2 com AI)
- Tempo de implementação: 2-3 dias (vs 7 dias v2)
- Satisfação do usuário: 60% (vs 90% v2)

**Documentação**:
- **Implementação**: `docs/sprints/SPRINT_0.1_V1_SIMPLES.md` - Planejamento detalhado
- **Validação**: `docs/validation/SPRINT_0.1_VALIDATION.md` - Guia de validação completo (4 etapas)
- **Status**: `docs/status/SPRINT_0.1_STATUS.md` - Status de implementação e métricas
- **Scripts**: `scripts/deploy-v1.sh` (deploy), `scripts/test-v1-menu.sh` (testes)
- **Templates**: `templates/whatsapp/v1/README.md` - Documentação completa dos templates

**Próximos Passos**:
1. Dar permissão aos scripts: `chmod +x scripts/*.sh` ✅
2. Executar deploy: `./scripts/deploy-v1.sh`
3. Testar: `./scripts/test-v1-menu.sh`
4. Validar conforme: `docs/validation/SPRINT_0.1_VALIDATION.md`
5. Monitorar métricas (1-2 semanas) conforme `docs/status/SPRINT_0.1_STATUS.md`
6. Upgrade para v2 (opcional): `./scripts/upgrade-v1-to-v2.sh`

**Data Criação**: 16/12/2025

---

## ✅ Sprint 1.1 - RAG e Base de Conhecimento

**Status**: ✅ IMPLEMENTAÇÃO 100% COMPLETA

**Objetivo**: Bot responde perguntas sobre TODOS os 5 serviços com RAG funcional

**Deliverables Completos**:
- ✅ Base de conhecimento (5 serviços, 1.380+ linhas)
- ✅ Script de ingestão automatizado (515 linhas bash)
- ✅ Funções Supabase otimizadas (221 linhas SQL)
- ✅ Workflow n8n RAG (232 linhas JSON)
- ✅ Documentação de validação completa

**Documentação**:
- **Implementação**: `docs/SPRINT_1.1_COMPLETE.md` - Relatório completo
- **Setup**: `docs/Setups/` - Guias de configuração (SETUP_CREDENTIALS, DEPLOY_SQL, EXECUTE_INGEST, IMPORT_N8N_WORKFLOW)
- **Validação**: `docs/validation/README.md` - Procedimentos de teste
- **Status**: `docs/status/SPRINT_1.1_STATUS.md` - Status de validação
- **Resumo**: `docs/validation/sprint_1.1_summary.md`

**Próximo Passo**: Executar setup conforme `docs/Setups/` e validação conforme `docs/validation/README.md`

---

## ✅ Sprint 1.2 - Sistema de Agendamento Completo

**Status**: ✅ IMPLEMENTAÇÃO COMPLETA

**Objetivo**: Bot agenda visitas técnicas automaticamente no Google Calendar

**Pré-requisitos**:
- ✅ Sprint 1.1 (RAG) implementado
- ✅ Google Calendar API configurada
- ✅ RD Station OAuth2 funcionando

**Entregas Implementadas**:
1. ✅ Integração Google Calendar API (workflow 05)
2. ✅ Lógica de disponibilidade e conflitos (funções SQL)
3. ✅ Sistema de lembretes automatizados 24h + 2h (workflow 06)
4. ✅ Sincronização com RD Station CRM (workflow 08)
5. ✅ Notificações multi-canal WhatsApp + Email (5 templates)
6. ✅ Workflow de reagendamento (funções SQL)
7. ✅ Follow-up pós-visita (template + workflow)

**Componentes Criados**:
- ✅ 5 Templates de email HTML responsivos (`templates/emails/`)
- ✅ 9 Funções SQL para appointments (`database/appointment_functions.sql`)
- ✅ Workflows n8n 05 e 06 (já existentes, validados)
- ✅ Integração completa RD Station (workflow 08)

**Documentação**:
- **Implementação**: `docs/sprints/SPRINT_1.2_PLANNING.md` (detalhado)
- **Setup**: `docs/Setups/` - Guias Google Calendar e RD Station
- **Validação**: `docs/validation/SPRINT_1.2_VALIDATION.md` (guia completo)

**Data Implementação**: 15/12/2025

**Próximo Passo**: Executar setup conforme `docs/Setups/SETUP_GOOGLE_CALENDAR.md` e `docs/Setups/SETUP_RDSTATION.md`, depois validação conforme `docs/validation/SPRINT_1.2_VALIDATION.md`

---

## ✅ Sprint 1.3 - Sistema de Notificações

**Status**: ✅ INTEGRADO NO SPRINT 1.2

**Objetivo**: Notificações automatizadas multi-canal (completado)

**Entregas Implementadas**:
- ✅ Email templates profissionais (5 templates em `templates/emails/`)
- ✅ Discord webhooks para alertas (workflow 10)
- ✅ Notificações WhatsApp automatizadas (workflows 06)
- ✅ Sistema de tracking de notificações (flags no banco)

**Nota**: Estas funcionalidades foram integradas diretamente no Sprint 1.2 para otimizar o desenvolvimento.

---

## ✅ Sprint 1.4 - Sincronização CRM Bidirecional

**Status**: ✅ INTEGRADO NO SPRINT 1.2

**Objetivo**: Sincronização completa com RD Station CRM (completado)

**Entregas Implementadas**:
- ✅ Sincronização bidirecional de contatos (workflow 08)
- ✅ Gestão de deals e pipeline (workflow 08)
- ✅ Webhook handlers para eventos CRM (workflow 09)
- ✅ Auditoria de sincronizações (`rdstation_sync_log` table)

**Nota**: A integração RD Station foi implementada completamente no Sprint 1.2 com workflows 08 e 09.

---

## ✅ Sprint 1.5 - Handoff para Humanos

**Status**: ✅ INTEGRADO NO SPRINT 1.2

**Objetivo**: Transferência inteligente para time comercial (completado)

**Entregas Implementadas**:
- ✅ Regras de escalação (workflow 10)
- ✅ Protocolo de transferência (workflow 10)
- ✅ Preservação de contexto (tabelas conversations + messages)
- ✅ Notificações para equipe (Discord + Email)

**Nota**: O handoff comercial foi implementado no workflow 10 com notificações multi-canal.

---

## 📂 Estrutura de Documentação

```
docs/
├── SPRINT_1.1_COMPLETE.md          # Sprint 1.1 - Relatório final
├── sprints/
│   ├── README.md                    # Este arquivo - Índice geral
│   ├── SPRINT_0.1_V1_SIMPLES.md     # 🆕 Sprint 0.1 - Bot v1 menu-based
│   ├── SPRINT_1.2_PLANNING.md       # Sprint 1.2 - Planejamento
│   └── sprint_1.1_summary.md        # Sprint 1.1 - Resumo executivo
├── status/
│   ├── SPRINT_0.1_STATUS.md         # 🆕 Sprint 0.1 - Status implementação v1
│   ├── SPRINT_1.1_STATUS.md         # 🔄 Sprint 1.1 - Status de validação
│   └── SPRINT_1.3_IMPLEMENTATION_STATUS.md  # Sprint 1.3 - Status implementação
├── validation/
│   ├── README.md                    # Índice validação geral
│   ├── SPRINT_0.1_VALIDATION.md     # 🆕 Validação Sprint 0.1 (Bot v1)
│   ├── sprint_1.1_validation.md     # Validação Sprint 1.1
│   ├── SPRINT_1.2_VALIDATION.md     # Validação Sprint 1.2
│   ├── SPRINT_1.3_VALIDATION.md     # Validação Sprint 1.3
│   └── VALIDATION_REPORT.md         # Relatório consolidado validações
└── Setups/
    ├── SETUP_CREDENTIALS.md         # 🔄 Guia 1/5 - Configuração credenciais
    ├── DEPLOY_SQL.md                # 🔄 Guia 2/5 - Deploy SQL
    ├── EXECUTE_INGEST.md            # 🔄 Guia 3/5 - Execução ingest
    ├── IMPORT_N8N_WORKFLOW.md       # 🔄 Guia 4/5 - Import workflows n8n
    ├── RUN_VALIDATION_TESTS.md      # 🔄 Guia 5/5 - Testes validação (não existe ainda)
    ├── SETUP_ANTHROPIC.md           # Setup Anthropic Claude API
    ├── SETUP_DISCORD.md             # Setup Discord Webhooks
    ├── SETUP_EMAIL.md               # Setup Email/SMTP
    ├── SETUP_EVOLUTION_API.md       # Setup Evolution API (WhatsApp)
    ├── SETUP_GOOGLE_CALENDAR.md     # Setup Google Calendar API
    └── SETUP_RDSTATION.md           # Setup RD Station CRM
```

### Arquivos Gerados Sprint 0.1

```
scripts/
├── deploy-v1.sh                     # 🆕 Deploy automatizado v1
├── test-v1-menu.sh                  # 🆕 Testes automatizados
├── rollback-to-v2.sh                # 🆕 Reverter para Claude AI
└── upgrade-v1-to-v2.sh              # 🆕 Upgrade v1 → v2

n8n/workflows/
└── 02_ai_agent_conversation_V1_MENU.json  # 🆕 Workflow v1 menu-based

templates/whatsapp/v1/
├── greeting.txt                     # 🆕 Boas-vindas + menu
├── service_selected.txt             # 🆕 Confirmação de serviço
├── collect_name.txt                 # 🆕 Solicita nome
├── collect_phone.txt                # 🆕 Solicita telefone
├── collect_email.txt                # 🆕 Solicita email
├── collect_city.txt                 # 🆕 Solicita cidade
├── confirmation.txt                 # 🆕 Resumo + opções finais
├── invalid_option.txt               # 🆕 Erro genérico
├── error_generic.txt                # 🆕 Erro sistema
└── README.md                        # 🆕 Documentação templates (1.200+ linhas)
```

---

## 🎯 Workflow de Desenvolvimento

### Iniciando Novo Sprint

1. **Validar Sprint Anterior**
   ```bash
   # Executar testes de validação conforme docs/validation/
   ```

2. **Revisar Planejamento**
   ```bash
   # Ler docs/sprints/SPRINT_X.X_PLANNING.md
   ```

3. **Implementar Funcionalidades**
   ```bash
   # Seguir ordem de entregas do planejamento
   ```

4. **Documentar Progresso**
   ```bash
   # Atualizar status em SPRINT_X.X_PLANNING.md
   ```

5. **Validar Entregas**
   ```bash
   # Criar documentação de validação
   ```

6. **Finalizar Sprint**
   ```bash
   # Criar SPRINT_X.X_COMPLETE.md
   ```

---

## 🔗 Links Rápidos

### 🆕 Sprint 0.1 (Novo - Lançamento Rápido)
- [Planejamento Completo](./SPRINT_0.1_V1_SIMPLES.md) (1.400+ linhas)
- [Guia de Validação](../validation/SPRINT_0.1_VALIDATION.md) - 4 etapas (pré-requisitos → deploy → testes → manual)
- [Status de Implementação](../status/SPRINT_0.1_STATUS.md) - Métricas, riscos, próximos passos
- [Deploy Script](../../scripts/deploy-v1.sh)
- [Test Script](../../scripts/test-v1-menu.sh)
- [Templates README](../../templates/whatsapp/v1/README.md)
- [Workflow v1 JSON](../../n8n/workflows/02_ai_agent_conversation_V1_MENU.json)

### Sprint 1.1 (RAG)
- [Implementação Completa](../SPRINT_1.1_COMPLETE.md)
- [Setup Guides](../Setups/) - Configuração completa (5 guias)
- [Validação Index](../validation/README.md)
- [Status Validação](../status/SPRINT_1.1_STATUS.md)
- [Resumo Executivo](../validation/sprint_1.1_summary.md)

### Sprint 1.2 (Agendamento)
- [Planejamento](./SPRINT_1.2_PLANNING.md)
- [Setup Google Calendar](../Setups/SETUP_GOOGLE_CALENDAR.md)
- [Setup RD Station](../Setups/SETUP_RDSTATION.md)
- [Validação](../validation/SPRINT_1.2_VALIDATION.md)

### Documentação Geral
- [README Principal](../../README.md)
- [Implementation Plan](../PLAN/implementation_plan.md)

---

**Última Atualização**: 2025-12-16
**Status Geral**: Sprint 0.1 Implementado | Sprints 1.1 e 1.2 Completos | Sistema Pronto para Deploy
