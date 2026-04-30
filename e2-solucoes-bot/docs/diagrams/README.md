# Diagramas de Arquitetura - E2 Bot

> **Objetivo**: Visualização da arquitetura do sistema
> **Formato**: Diagramas ASCII (compatível com terminal e documentação)
> **Última atualização**: 2026-04-29

## 📊 Diagramas Disponíveis

### 01. System Architecture
**Arquivo**: [`01_SYSTEM_ARCHITECTURE.md`](01_SYSTEM_ARCHITECTURE.md)

**Conteúdo**:
- Visão geral do sistema (WhatsApp → Evolution API → n8n → Claude AI → PostgreSQL)
- Fluxo completo de mensagens (WF01 → WF02 → WF05/WF06 → WF07)
- Arquitetura de workflows (n8n)
- State Machine detalhado (15 estados)
- Database schema (conversations, appointments, email_logs)
- Correções críticas (V111-V114)
- Deployment flow
- Technology stack

**Quando consultar**:
- Entender arquitetura completa do sistema
- Ver fluxo end-to-end de mensagens
- Compreender integração entre workflows
- Revisar correções críticas implementadas
- Entender deployment workflow

---

### 02. State Machine Flow
**Arquivo**: [`02_STATE_MACHINE_FLOW.md`](02_STATE_MACHINE_FLOW.md)

**Conteúdo**:
- Fluxograma completo (15 estados)
- Detalhamento de cada estado (input, validation, action, response, next)
- Rotas alternativas (handoff_to_human, error handling)
- Integração de correções críticas no fluxo (V104-V114)
- Exemplos de mensagens e respostas

**Quando consultar**:
- Entender fluxo detalhado de conversação
- Ver validações de cada estado
- Compreender rotas alternativas
- Verificar integração de correções críticas
- Debugging de problemas de fluxo

---

## 🎯 Como Usar Esta Documentação

### Para Novos Desenvolvedores

1. **Primeiro**: Ler [`01_SYSTEM_ARCHITECTURE.md`](01_SYSTEM_ARCHITECTURE.md)
   - Tempo: ~20 minutos
   - Foco: Entendimento geral do sistema

2. **Segundo**: Ler [`02_STATE_MACHINE_FLOW.md`](02_STATE_MACHINE_FLOW.md)
   - Tempo: ~30 minutos
   - Foco: Fluxo detalhado de conversação

3. **Terceiro**: Consultar guidelines complementares
   - [`../guidelines/00_VISAO_GERAL.md`](../guidelines/00_VISAO_GERAL.md) - Arquitetura conceitual
   - [`../guidelines/02_STATE_MACHINE_PATTERNS.md`](../guidelines/02_STATE_MACHINE_PATTERNS.md) - Padrões técnicos

**Resultado esperado**: Entendimento completo da arquitetura em ~1 hora

---

### Para Debugging

**Problema**: Mensagens não chegam ao usuário
- Consultar: [`01_SYSTEM_ARCHITECTURE.md`](01_SYSTEM_ARCHITECTURE.md) → "Fluxo de Mensagens"
- Ver: Cada ponto de falha possível (Evolution API → WF01 → WF02 → Send)

**Problema**: Estado incorreto após transição
- Consultar: [`02_STATE_MACHINE_FLOW.md`](02_STATE_MACHINE_FLOW.md) → Estado específico
- Ver: Validações e condições de transição

**Problema**: WF06 retorna dados mas usuário volta para início
- Consultar: [`02_STATE_MACHINE_FLOW.md`](02_STATE_MACHINE_FLOW.md) → "V105: Routing Fix"
- Ver: Ordem correta de execução (Update State BEFORE Check If WF06)

**Problema**: Mensagens simultâneas causam comportamento estranho
- Consultar: [`01_SYSTEM_ARCHITECTURE.md`](01_SYSTEM_ARCHITECTURE.md) → "V111: Database Row Locking"
- Ver: FOR UPDATE SKIP LOCKED implementação

---

### Para Modificações

**Adicionar novo estado**:
1. Ver estrutura em [`02_STATE_MACHINE_FLOW.md`](02_STATE_MACHINE_FLOW.md)
2. Seguir padrão de validação e resposta
3. Consultar [`../development/01_WORKFLOW_MODIFICATION.md`](../development/01_WORKFLOW_MODIFICATION.md)

**Modificar integração WF06**:
1. Ver fluxo em [`01_SYSTEM_ARCHITECTURE.md`](01_SYSTEM_ARCHITECTURE.md) → "Arquitetura de Workflows"
2. Ver estados 9-13 em [`02_STATE_MACHINE_FLOW.md`](02_STATE_MACHINE_FLOW.md)
3. Verificar V105 routing fix

**Adicionar novo serviço**:
1. Ver State 4 em [`02_STATE_MACHINE_FLOW.md`](02_STATE_MACHINE_FLOW.md)
2. Ver State 8 decision tree
3. Consultar [`../development/01_WORKFLOW_MODIFICATION.md`](../development/01_WORKFLOW_MODIFICATION.md)

---

## 📋 Quick Reference

### Estados do State Machine

| Estado | Nome | Tipo | Próximo |
|--------|------|------|---------|
| 1 | greeting | INPUT | collect_name |
| 2 | collect_name | INPUT | collect_email |
| 3 | collect_email | INPUT | service_selection |
| 4 | service_selection | INPUT | collect_city |
| 5 | collect_city | INPUT | claude_analysis |
| 6 | claude_analysis | AUTO | ai_response_display |
| 7 | ai_response_display | AUTO | confirmation |
| 8 | confirmation | DECISION | trigger_wf06_next_dates OR handoff_to_human |
| 9 | trigger_wf06_next_dates | AUTO | show_available_dates |
| 10 | show_available_dates | INPUT | process_date_selection |
| 11 | process_date_selection | INPUT | trigger_wf06_available_slots |
| 12 | trigger_wf06_available_slots | AUTO | show_available_slots |
| 13 | show_available_slots | INPUT | process_appointment_booking |
| 14 | process_appointment_booking | AUTO | booking_confirmation |
| 15 | booking_confirmation | FINAL | END |

### Workflows

| WF | Versão | Função | Documentação |
|----|--------|--------|--------------|
| WF01 | V2.8.3 | Dedup | [`01_SYSTEM_ARCHITECTURE.md`](01_SYSTEM_ARCHITECTURE.md) |
| WF02 | V114 | AI Conversation | [`01_SYSTEM_ARCHITECTURE.md`](01_SYSTEM_ARCHITECTURE.md), [`02_STATE_MACHINE_FLOW.md`](02_STATE_MACHINE_FLOW.md) |
| WF05 | V7 | Scheduler | [`01_SYSTEM_ARCHITECTURE.md`](01_SYSTEM_ARCHITECTURE.md) |
| WF06 | V2.2 | Calendar Service | [`01_SYSTEM_ARCHITECTURE.md`](01_SYSTEM_ARCHITECTURE.md) |
| WF07 | V13 | Email Service | [`01_SYSTEM_ARCHITECTURE.md`](01_SYSTEM_ARCHITECTURE.md) |

### Correções Críticas

| Versão | Nome | Diagrama | Linha |
|--------|------|----------|-------|
| V104 | State Sync | [`02_STATE_MACHINE_FLOW.md`](02_STATE_MACHINE_FLOW.md) | ~500 |
| V104.2 | Schema Fix | [`02_STATE_MACHINE_FLOW.md`](02_STATE_MACHINE_FLOW.md) | ~520 |
| V105 | Routing Fix | [`02_STATE_MACHINE_FLOW.md`](02_STATE_MACHINE_FLOW.md) | ~540 |
| V106.1 | response_text | [`02_STATE_MACHINE_FLOW.md`](02_STATE_MACHINE_FLOW.md) | ~570 |
| V111 | Row Locking | [`01_SYSTEM_ARCHITECTURE.md`](01_SYSTEM_ARCHITECTURE.md) | ~200, [`02_STATE_MACHINE_FLOW.md`](02_STATE_MACHINE_FLOW.md) | ~480 |
| V113 | WF06 Persistence | [`02_STATE_MACHINE_FLOW.md`](02_STATE_MACHINE_FLOW.md) | ~590 |
| V114 | TIME Fields | [`02_STATE_MACHINE_FLOW.md`](02_STATE_MACHINE_FLOW.md) | ~630 |

---

## 🔗 Documentação Relacionada

### Guidelines (Conceituais)

- [`../guidelines/00_VISAO_GERAL.md`](../guidelines/00_VISAO_GERAL.md) - Arquitetura do sistema (conceitual)
- [`../guidelines/01_N8N_BEST_PRACTICES.md`](../guidelines/01_N8N_BEST_PRACTICES.md) - Limitações n8n 2.x
- [`../guidelines/02_STATE_MACHINE_PATTERNS.md`](../guidelines/02_STATE_MACHINE_PATTERNS.md) - Padrões State Machine
- [`../guidelines/03_DATABASE_PATTERNS.md`](../guidelines/03_DATABASE_PATTERNS.md) - Schema e queries
- [`../guidelines/04_WORKFLOW_INTEGRATION.md`](../guidelines/04_WORKFLOW_INTEGRATION.md) - Comunicação microserviços

### Development (Práticos)

- [`../development/01_WORKFLOW_MODIFICATION.md`](../development/01_WORKFLOW_MODIFICATION.md) - Modificar workflows
- [`../development/02_DEBUGGING_GUIDE.md`](../development/02_DEBUGGING_GUIDE.md) - Debug e troubleshooting
- [`../development/03_COMMON_TASKS.md`](../development/03_COMMON_TASKS.md) - Tarefas comuns
- [`../development/04_CODE_REVIEW_CHECKLIST.md`](../development/04_CODE_REVIEW_CHECKLIST.md) - Checklist de revisão
- [`../development/05_LOCAL_SETUP.md`](../development/05_LOCAL_SETUP.md) - Setup ambiente local

### Código

- **State Machine V114**: `scripts/wf02/state-machines/wf02-v114-slot-time-fields-fix.js`
- **Production WF02**: `n8n/workflows/production/wf02/02_ai_agent_conversation_V114_FUNCIONANDO.json`
- **Production WF06**: `n8n/workflows/production/wf06/06_calendar_availability_service_v2_2.json`

---

## 💡 Dicas de Uso

### Imprimindo Diagramas

```bash
# Visualizar no terminal
cat docs/diagrams/01_SYSTEM_ARCHITECTURE.md | less

# Gerar PDF (requer pandoc)
pandoc docs/diagrams/01_SYSTEM_ARCHITECTURE.md -o system_architecture.pdf

# Converter para HTML
pandoc docs/diagrams/01_SYSTEM_ARCHITECTURE.md -o system_architecture.html
```

### Buscando Informação Específica

```bash
# Encontrar estado específico
grep -n "STATE 10" docs/diagrams/02_STATE_MACHINE_FLOW.md

# Encontrar correção crítica
grep -n "V111" docs/diagrams/*.md

# Encontrar workflow específico
grep -n "WF06" docs/diagrams/01_SYSTEM_ARCHITECTURE.md
```

### Navegando por Tópico

**Arquitetura Geral**:
- [`01_SYSTEM_ARCHITECTURE.md`](01_SYSTEM_ARCHITECTURE.md) → "Visão Geral do Sistema"

**Fluxo de Mensagens**:
- [`01_SYSTEM_ARCHITECTURE.md`](01_SYSTEM_ARCHITECTURE.md) → "Fluxo de Mensagens (Message Flow)"

**Estado Específico**:
- [`02_STATE_MACHINE_FLOW.md`](02_STATE_MACHINE_FLOW.md) → "STATE N: nome_do_estado"

**Correção Crítica**:
- [`01_SYSTEM_ARCHITECTURE.md`](01_SYSTEM_ARCHITECTURE.md) → "Correções Críticas (V111-V114)"
- [`02_STATE_MACHINE_FLOW.md`](02_STATE_MACHINE_FLOW.md) → "VXX: Nome da Correção"

**Database Schema**:
- [`01_SYSTEM_ARCHITECTURE.md`](01_SYSTEM_ARCHITECTURE.md) → "Database Schema"

**Deployment**:
- [`01_SYSTEM_ARCHITECTURE.md`](01_SYSTEM_ARCHITECTURE.md) → "Deployment Flow"

---

## ✅ Checklist de Compreensão

Você compreendeu a arquitetura quando conseguir:

- [ ] Explicar fluxo completo de mensagem (WhatsApp → Resposta)
- [ ] Desenhar diagrama de 15 estados do State Machine
- [ ] Identificar cada workflow e sua função
- [ ] Explicar V111 row locking e por que é crítico
- [ ] Explicar V114 TIME fields extraction
- [ ] Explicar V105 routing fix (Update BEFORE Check)
- [ ] Descrever database schema (4 tabelas)
- [ ] Identificar pontos de integração WF02→WF06
- [ ] Explicar diferença entre service 1/3 vs 2/4/5
- [ ] Descrever deployment workflow completo

**Objetivo**: 80% destes itens em 2 horas de estudo ✅

---

**Última atualização**: 2026-04-29
**Versão**: Production V1
**Autores**: Time de Desenvolvimento E2 Bot
