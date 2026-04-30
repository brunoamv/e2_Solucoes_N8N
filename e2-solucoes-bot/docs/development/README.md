# Guias de Desenvolvimento - E2 Bot

> **Objetivo**: Guias práticos para desenvolvimento do E2 Bot
> **Público-alvo**: Desenvolvedores trabalhando no projeto
> **Última atualização**: 2026-04-29

## 🎯 Quick Start

**Novo no projeto?** Siga esta sequência:

1. **[05_LOCAL_SETUP.md](05_LOCAL_SETUP.md)** (30-60 min) - Configure ambiente local completo
2. **[../guidelines/00_VISAO_GERAL.md](../guidelines/00_VISAO_GERAL.md)** (15 min) - Entenda a arquitetura do sistema
3. **[01_WORKFLOW_MODIFICATION.md](01_WORKFLOW_MODIFICATION.md)** (20 min) - Aprenda a modificar workflows
4. **[03_COMMON_TASKS.md](03_COMMON_TASKS.md)** (referência) - Consulte para tarefas específicas

**Total**: ~2 horas para setup + entendimento básico ✅

---

## 📚 Estrutura de Documentação

### Guias de Desenvolvimento (este diretório)

**Práticos e step-by-step** - Como fazer desenvolvimento:

| Guia | Conteúdo | Quando Usar |
|------|----------|-------------|
| **[01_WORKFLOW_MODIFICATION.md](01_WORKFLOW_MODIFICATION.md)** | Modificação prática de workflows com exemplos reais | Ao adicionar/modificar estados, integrar WF06, modificar database operations |
| **[02_DEBUGGING_GUIDE.md](02_DEBUGGING_GUIDE.md)** | Técnicas de debugging e troubleshooting | Ao investigar bugs, analisar logs, diagnosticar problemas |
| **[03_COMMON_TASKS.md](03_COMMON_TASKS.md)** | Procedimentos step-by-step para tarefas comuns | Ao versionar workflows, modificar schema, testar, deployar |
| **[04_CODE_REVIEW_CHECKLIST.md](04_CODE_REVIEW_CHECKLIST.md)** | Checklist completo de code review | Antes de deployar, ao revisar PRs, validar correções |
| **[05_LOCAL_SETUP.md](05_LOCAL_SETUP.md)** | Configuração completa de ambiente local | Ao iniciar no projeto, configurar nova máquina |

### Guidelines (../guidelines/)

**Conceituais e de arquitetura** - O que e por quê:

| Guideline | Conteúdo | Quando Consultar |
|-----------|----------|------------------|
| **[00_VISAO_GERAL.md](../guidelines/00_VISAO_GERAL.md)** | Arquitetura completa do sistema | Ao entender o sistema como um todo |
| **[01_N8N_BEST_PRACTICES.md](../guidelines/01_N8N_BEST_PRACTICES.md)** | Limitações n8n 2.x e workarounds | Ao encontrar bloqueios de $env, filesystem, queryReplacement |
| **[02_STATE_MACHINE_PATTERNS.md](../guidelines/02_STATE_MACHINE_PATTERNS.md)** | Padrão central de conversação | Ao entender ou modificar State Machine |
| **[03_DATABASE_PATTERNS.md](../guidelines/03_DATABASE_PATTERNS.md)** | Schema e queries PostgreSQL | Ao modificar schema, queries, entender estrutura de dados |
| **[04_WORKFLOW_INTEGRATION.md](../guidelines/04_WORKFLOW_INTEGRATION.md)** | Comunicação microserviços | Ao entender integração WF02→WF05→WF06→WF07 |
| **[05_TESTING_VALIDATION.md](../guidelines/05_TESTING_VALIDATION.md)** | Estratégias de teste | Ao planejar testes, entender test coverage |
| **[06_DEPLOYMENT_GUIDE.md](../guidelines/06_DEPLOYMENT_GUIDE.md)** | Processo de deployment | Ao entender workflow de release |
| **[07_SECURITY_COMPLIANCE.md](../guidelines/07_SECURITY_COMPLIANCE.md)** | Segurança e LGPD | Ao lidar com dados sensíveis, implementar features |

---

## 🚀 Workflows de Desenvolvimento

### Setup Inicial (Uma vez)

```bash
# 1. Configurar ambiente
Seguir: docs/development/05_LOCAL_SETUP.md

# 2. Entender arquitetura
Ler: docs/guidelines/00_VISAO_GERAL.md

# 3. Familiarizar com State Machine
Ler: docs/guidelines/02_STATE_MACHINE_PATTERNS.md

# Tempo total: ~2 horas
```

### Desenvolvimento de Feature

```bash
# 1. Criar branch
git checkout -b feature/nova-funcionalidade

# 2. Modificar workflow
Consultar: docs/development/01_WORKFLOW_MODIFICATION.md
Aplicar: Adicionar novo estado ou modificar existente

# 3. Testar localmente
Consultar: docs/development/03_COMMON_TASKS.md
Executar: Seção "Testing Workflow Changes Locally"

# 4. Code review self-check
Consultar: docs/development/04_CODE_REVIEW_CHECKLIST.md
Verificar: Todos os itens da checklist

# 5. Commit e PR
git add .
git commit -m "feat: descrição da feature"
git push origin feature/nova-funcionalidade
```

### Debugging de Problema

```bash
# 1. Reproduzir problema
Seguir: docs/development/02_DEBUGGING_GUIDE.md
Seção: "Reproducing Issues Locally"

# 2. Analisar logs
Consultar: docs/development/02_DEBUGGING_GUIDE.md
Seção: "Log Analysis" (n8n, PostgreSQL, Evolution API)

# 3. Investigar database
Consultar: docs/development/02_DEBUGGING_GUIDE.md
Seção: "Database State Inspection"

# 4. Aplicar fix
Consultar: docs/development/01_WORKFLOW_MODIFICATION.md
Aplicar: Correção baseada em root cause

# 5. Validar fix
Consultar: docs/development/03_COMMON_TASKS.md
Seção: "Testing Workflow Changes Locally"
```

### Deployment de Mudanças

```bash
# 1. Final review
Consultar: docs/development/04_CODE_REVIEW_CHECKLIST.md
Verificar: Checklist completo

# 2. Incrementar versão
Consultar: docs/development/03_COMMON_TASKS.md
Seção: "Managing Workflow Versions"

# 3. Deploy para produção
Consultar: docs/development/03_COMMON_TASKS.md
Seção: "Deploying Workflow to Production"

# 4. Validar em produção
Consultar: docs/development/03_COMMON_TASKS.md
Seção: "Post-Deployment Validation"

# 5. Rollback se necessário
Consultar: docs/development/03_COMMON_TASKS.md
Seção: "Rolling Back to Previous Version"
```

---

## 🔧 Tarefas Comuns - Quick Reference

### Adicionar Novo Estado

```bash
# Guia completo: docs/development/01_WORKFLOW_MODIFICATION.md
# Seção: "Adding a New State"

# Steps resumidos:
1. Definir estado em State Machine switch
2. Adicionar validação de input
3. Atualizar collected_data
4. Definir response_text
5. Especificar next_stage
6. Testar transição completa
```

### Modificar Schema de Banco

```bash
# Guia completo: docs/development/03_COMMON_TASKS.md
# Seção: "Modifying Database Schema"

# Steps resumidos:
1. Criar migration SQL
2. Aplicar em ambiente local
3. Testar com dados reais
4. Atualizar queries afetadas
5. Deploy migration para produção
```

### Integrar Novo Serviço Externo

```bash
# Guia completo: docs/development/03_COMMON_TASKS.md
# Seção: "Integrating New External Service"

# Steps resumidos:
1. Criar HTTP Request node
2. Configurar authentication
3. Adicionar error handling
4. Testar response structure
5. Integrar no workflow flow
```

### Debug Infinite Loop

```bash
# Guia completo: docs/development/02_DEBUGGING_GUIDE.md
# Seção: "Infinite Loop or Repeated State"

# Steps resumidos:
1. Reproduzir localmente
2. Analisar logs de transição
3. Verificar database state vs código
4. Identificar divergência
5. Aplicar V104+V105 fix pattern
```

### Investigar Mensagem Undefined

```bash
# Guia completo: docs/development/02_DEBUGGING_GUIDE.md
# Seção: "Empty or Undefined Messages"

# Steps resumidos:
1. Verificar response_text em logs
2. Identificar rota (normal/WF06)
3. Verificar Send node data source
4. Aplicar V106.1 fix pattern (explicit node reference)
5. Testar todas as rotas
```

---

## 📖 Casos de Uso Específicos

### "Preciso adicionar um novo tipo de serviço"

```bash
# 1. Modificar State Machine
Consultar: docs/development/01_WORKFLOW_MODIFICATION.md
Seção: "Modifying Existing States" → service_selection state

# 2. Atualizar database enum (se necessário)
Consultar: docs/development/03_COMMON_TASKS.md
Seção: "Modifying Database Schema"

# 3. Ajustar roteamento WF06 (se aplicável)
Consultar: docs/guidelines/04_WORKFLOW_INTEGRATION.md
Seção: "WF02 → WF06 Integration"

# 4. Testar fluxo completo
Consultar: docs/development/03_COMMON_TASKS.md
Seção: "Testing Workflow Changes Locally"
```

### "Workflow não está salvando dados no banco"

```bash
# 1. Debug database operations
Consultar: docs/development/02_DEBUGGING_GUIDE.md
Seção: "Database State Inspection"

# 2. Verificar Build Update Queries
Consultar: docs/development/04_CODE_REVIEW_CHECKLIST.md
Seção: "Build Update Queries Review"

# 3. Validar schema compliance
Consultar: docs/guidelines/03_DATABASE_PATTERNS.md
Seção: "Schema Design"

# 4. Aplicar V104.2 fix se necessário
Consultar: docs/development/01_WORKFLOW_MODIFICATION.md
Seção: "Common Mistakes" → V104.2 Schema Mismatch
```

### "WF06 retorna dados mas usuário volta para início"

```bash
# 1. Verificar routing
Consultar: docs/development/01_WORKFLOW_MODIFICATION.md
Seção: "Common Mistakes" → V105 Infinite Loop

# 2. Aplicar V105 fix
Consultar: docs/development/01_WORKFLOW_MODIFICATION.md
Seção: "Adding WF06 Integration States"

# 3. Validar state persistence
Consultar: docs/development/04_CODE_REVIEW_CHECKLIST.md
Seção: "Workflow Connections Review" → V105 Routing Fix

# 4. Testar fluxo completo com WF06
Consultar: docs/development/03_COMMON_TASKS.md
Seção: "Testing Workflow Changes Locally"
```

### "Mensagens simultâneas causam comportamento estranho"

```bash
# 1. Identificar race condition
Consultar: docs/development/02_DEBUGGING_GUIDE.md
Seção: "Race Conditions and Concurrent Messages"

# 2. Aplicar V111 row locking
Consultar: CLAUDE.md (raiz do projeto)
Seção: "Deploy → WF02 V111"

# 3. Testar mensagens rápidas
Consultar: docs/development/03_COMMON_TASKS.md
Seção: "Testing Workflow Changes Locally" → Rapid messages test

# 4. Validar logs de locking
Consultar: docs/development/02_DEBUGGING_GUIDE.md
Seção: "Log Analysis" → PostgreSQL logs
```

---

## 🎓 Aprendizado Progressivo

### Nível 1: Iniciante (Primeiros dias)

**Foco**: Configuração e entendimento básico

1. Completar setup: `05_LOCAL_SETUP.md`
2. Entender arquitetura: `../guidelines/00_VISAO_GERAL.md`
3. Explorar workflows existentes no n8n
4. Executar testes manuais simples

**Resultado esperado**: Ambiente funcionando, entendimento do fluxo geral

### Nível 2: Intermediário (Primeira semana)

**Foco**: Modificações simples e debugging básico

1. Modificar textos de mensagens: `01_WORKFLOW_MODIFICATION.md`
2. Adicionar validação simples a estado existente
3. Investigar logs: `02_DEBUGGING_GUIDE.md`
4. Realizar testes locais: `03_COMMON_TASKS.md`

**Resultado esperado**: Capaz de fazer modificações simples e debugar problemas básicos

### Nível 3: Avançado (Primeiro mês)

**Foco**: Features complexas e integrações

1. Adicionar novo estado completo: `01_WORKFLOW_MODIFICATION.md`
2. Integrar serviço externo: `03_COMMON_TASKS.md`
3. Modificar schema de banco: `03_COMMON_TASKS.md`
4. Aplicar code review completo: `04_CODE_REVIEW_CHECKLIST.md`

**Resultado esperado**: Capaz de implementar features completas e revisar código

### Nível 4: Expert (3+ meses)

**Foco**: Arquitetura e otimizações

1. Entender todas as guidelines: `../guidelines/`
2. Contribuir para padrões: `../guidelines/01_N8N_BEST_PRACTICES.md`
3. Otimizar performance: `../guidelines/03_DATABASE_PATTERNS.md`
4. Mentorar novos desenvolvedores

**Resultado esperado**: Profundo conhecimento do sistema, capaz de decisões arquiteturais

---

## 🔗 Referências Externas

### Documentação Oficial

- **n8n**: https://docs.n8n.io/
- **PostgreSQL**: https://www.postgresql.org/docs/
- **Evolution API**: https://doc.evolution-api.com/
- **Claude AI**: https://docs.anthropic.com/

### Recursos de Aprendizado

- **n8n Community**: https://community.n8n.io/
- **PostgreSQL Tutorial**: https://www.postgresqltutorial.com/
- **WhatsApp Business API**: https://developers.facebook.com/docs/whatsapp/

### Ferramentas Úteis

- **n8n Desktop App**: https://n8n.io/download
- **DBeaver** (PostgreSQL client): https://dbeaver.io/
- **Postman** (API testing): https://www.postman.com/
- **GitKraken** (Git visual): https://www.gitkraken.com/

---

## 📞 Suporte

### Quando encontrar problemas:

1. **Consultar este README** para quick reference
2. **Buscar nos guias específicos** usando índice acima
3. **Verificar CLAUDE.md** (raiz) para comandos de deploy específicos
4. **Consultar guidelines** para entendimento conceitual
5. **Explorar docs/fix/** para bugfixes históricos semelhantes

### Estrutura de Suporte:

```
Problema Prático → docs/development/
Dúvida Conceitual → docs/guidelines/
Comando Específico → CLAUDE.md (raiz)
Bug Histórico → docs/fix/
Deployment → docs/deployment/
```

---

## ✅ Checklist de Proficiência

Você está pronto para desenvolvimento quando conseguir:

- [ ] Configurar ambiente local completo (< 1 hora)
- [ ] Explicar arquitetura do sistema em alto nível
- [ ] Modificar texto de mensagem em workflow
- [ ] Adicionar validação simples a estado existente
- [ ] Reproduzir e debugar problema básico
- [ ] Executar testes locais de workflow
- [ ] Consultar logs de n8n, PostgreSQL, Evolution API
- [ ] Realizar code review usando checklist
- [ ] Adicionar novo estado completo ao State Machine
- [ ] Modificar schema de banco de dados
- [ ] Deployar mudança para produção
- [ ] Realizar rollback se necessário

**Objetivo**: 80% destes itens em 2 semanas ✅

---

## 📝 Notas Importantes

### Sempre Lembrar:

1. **n8n 2.14.2 Limitations**: $env blocked, filesystem blocked, queryReplacement limited
2. **Proactive UX First**: V76+ eliminou erros guiando usuário proativamente
3. **State Machine é Central**: 15 estados controlam toda conversação
4. **WF06 é Microserviço**: Testável e escalável independentemente
5. **V111 Row Locking é Crítico**: Previne race conditions em mensagens rápidas
6. **V114 TIME Fields**: PostgreSQL requer scheduled_time_start/end como TIME
7. **V104+V105 Routing**: Update State BEFORE Check If WF06 (previne loop)
8. **V106.1 Explicit Nodes**: Use `$node["Node Name"].json` para response_text correto

### Padrões de Sucesso:

- **V74.1_2**: Working code base - usar como modelo para estruturas de retorno
- **V80**: Complete + WF06 integration - padrão atual de arquitetura
- **V91**: State initialization - padrão para resolução de estado
- **V111**: Row locking - padrão para concurrency
- **V114**: TIME fields extraction - padrão atual de produção

---

**Última atualização**: 2026-04-29
**Versão**: 1.0
**Autores**: Time de Desenvolvimento E2 Bot
