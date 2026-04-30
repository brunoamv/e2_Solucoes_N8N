# E2 Bot - Desenvolvimento e Guidelines

> **Guia completo** de desenvolvimento para o E2 Bot WhatsApp AI Agent
> **Stack**: n8n 2.14.2 + Claude 3.5 Sonnet + PostgreSQL + Evolution API v2.3.7
> **Atualizado**: 2026-04-29

---

## 📚 Documentação de Desenvolvimento

Este diretório contém guidelines, boas práticas e padrões de desenvolvimento para o projeto E2 Bot:

### Documentação Principal

1. **[00_VISAO_GERAL.md](00_VISAO_GERAL.md)** ⭐ COMECE AQUI
   - Arquitetura do sistema
   - Stack tecnológico
   - Fluxo de workflows
   - Estrutura do projeto

2. **[01_N8N_BEST_PRACTICES.md](01_N8N_BEST_PRACTICES.md)** ⭐ ESSENCIAL
   - Limitações do n8n 2.14.2
   - Padrões de desenvolvimento
   - Soluções para problemas comuns
   - Estrutura de nodes

3. **[02_STATE_MACHINE_PATTERNS.md](02_STATE_MACHINE_PATTERNS.md)** ⭐ CRÍTICO
   - Padrão de State Machine
   - Estados e transições
   - Tratamento de dados
   - Integração WF06

4. **[03_DATABASE_PATTERNS.md](03_DATABASE_PATTERNS.md)**
   - Schema do PostgreSQL
   - Padrões de query
   - Race conditions e locks
   - Boas práticas SQL

5. **[04_WORKFLOW_INTEGRATION.md](04_WORKFLOW_INTEGRATION.md)**
   - Comunicação entre workflows
   - HTTP Request patterns
   - Tratamento de erros
   - Microservices approach

6. **[05_TESTING_VALIDATION.md](05_TESTING_VALIDATION.md)**
   - Estratégias de teste
   - Validação de workflows
   - Debugging técnicas
   - Logs e monitoramento

7. **[06_DEPLOYMENT_GUIDE.md](06_DEPLOYMENT_GUIDE.md)**
   - Processo de deployment
   - Versionamento
   - Rollback procedures
   - Production checklist

8. **[07_SECURITY_COMPLIANCE.md](07_SECURITY_COMPLIANCE.md)**
   - Segurança de dados
   - API keys management
   - LGPD compliance
   - Best practices

---

## 🎯 Quick Start para Desenvolvimento

### Novo Desenvolvedor

```bash
# 1. Ler documentação essencial
cat docs/guidelines/00_VISAO_GERAL.md          # Entender arquitetura
cat docs/guidelines/01_N8N_BEST_PRACTICES.md   # Aprender limitações n8n
cat docs/guidelines/02_STATE_MACHINE_PATTERNS.md  # Entender padrão central

# 2. Setup ambiente
cat docs/Setups/QUICKSTART.md                  # Setup completo (30-45 min)

# 3. Estudar workflow de produção
cat CLAUDE.md                                   # Contexto técnico
cat n8n/workflows/README.md                     # Organização de workflows
```

### Desenvolvendo Nova Feature

```bash
# 1. Analisar requisitos
cat docs/guidelines/00_VISAO_GERAL.md          # Identificar workflow afetado

# 2. Seguir padrões
cat docs/guidelines/02_STATE_MACHINE_PATTERNS.md  # Se alterar WF02
cat docs/guidelines/04_WORKFLOW_INTEGRATION.md    # Se integrar workflows

# 3. Validar e testar
cat docs/guidelines/05_TESTING_VALIDATION.md   # Estratégias de teste

# 4. Deployar
cat docs/guidelines/06_DEPLOYMENT_GUIDE.md     # Processo de deployment
```

### Debugando Problemas

```bash
# 1. Consultar problemas conhecidos
cat docs/guidelines/01_N8N_BEST_PRACTICES.md   # Limitações e workarounds

# 2. Analisar logs
docker logs -f e2bot-n8n-dev | grep -E "ERROR|V[0-9]+"

# 3. Ver bugfixes anteriores
ls docs/fix/wf02/v100-v114/                    # Problemas similares resolvidos
```

---

## 📖 Convenções do Projeto

### Versionamento de Workflows

```
WFXX_VYY_DESCRIPTION.json

Onde:
- XX: Número do workflow (01-07)
- YY: Versão sequencial
- DESCRIPTION: Descrição curta da versão

Exemplos:
- 02_ai_agent_conversation_V114_FUNCIONANDO.json
- 06_calendar_availability_service_v2_2.json
```

### Organização de Documentação

```
docs/
├── guidelines/         # Este diretório - padrões e boas práticas
├── Setups/            # Guias de configuração
├── deployment/        # Guias de deployment por workflow
├── fix/               # Relatórios de bugfix
├── PLAN/              # Planejamento e estratégia
└── analysis/          # Análises técnicas
```

### Nomenclatura de Branches Git

```
feature/wfXX-description       # Nova feature
bugfix/wfXX-vYY-issue          # Correção de bug
hotfix/critical-issue          # Correção urgente
refactor/wfXX-improvement      # Refatoração
```

### Commit Messages

```bash
# Formato
<type>: <description>

<body>

Signed-off-by: Nome <email>

# Tipos
feat:       # Nova feature
fix:        # Bugfix
refactor:   # Refatoração
docs:       # Documentação
chore:      # Manutenção
```

---

## 🚨 Avisos Críticos

### ❌ NUNCA Fazer

1. **NUNCA** modificar workflows de produção diretamente
   - Sempre criar versão de desenvolvimento
   - Testar completamente antes de promover

2. **NUNCA** usar `fs` module em n8n Code nodes
   - n8n 2.x bloqueia acesso a filesystem
   - Use HTTP Request + nginx para templates

3. **NUNCA** usar `$env` em Code nodes ou Set nodes
   - n8n 2.x bloqueia acesso a variáveis de ambiente
   - Use hardcoded values ou PostgreSQL para configuração

4. **NUNCA** usar `queryReplacement` com expressões `={{ }}`
   - n8n não resolve expressões em queryReplacement
   - Use INSERT...SELECT pattern

5. **NUNCA** assumir que database está atualizado
   - Sempre usar row locking (FOR UPDATE SKIP LOCKED)
   - Ver V111 para entender race conditions

### ✅ SEMPRE Fazer

1. **SEMPRE** seguir padrão de State Machine (WF02)
   - Todos os estados devem retornar `response_text` válido
   - Use estrutura de retorno compatível com n8n

2. **SEMPRE** testar race conditions
   - Simular mensagens rápidas (< 1 segundo)
   - Verificar concorrência

3. **SEMPRE** validar contra schema do banco
   - Verificar colunas antes de usar
   - Ver `docs/Setups/DATABASE_SCHEMA.md`

4. **SEMPRE** documentar mudanças
   - Criar bugfix report em `docs/fix/`
   - Atualizar CLAUDE.md se mudança de produção

5. **SEMPRE** usar proactive UX
   - Guiar usuário ao invés de validar
   - Ver WF02 V76+ para exemplo

---

## 🎓 Aprendizado Progressivo

### Nível 1: Básico (1-2 dias)

- [ ] Ler `00_VISAO_GERAL.md` - Entender arquitetura
- [ ] Ler `CLAUDE.md` - Contexto técnico completo
- [ ] Setup ambiente usando `docs/Setups/QUICKSTART.md`
- [ ] Executar workflow WF02 V114 de produção
- [ ] Entender fluxo completo: "oi" → agendamento

### Nível 2: Intermediário (1 semana)

- [ ] Ler `01_N8N_BEST_PRACTICES.md` - Limitações e soluções
- [ ] Ler `02_STATE_MACHINE_PATTERNS.md` - Padrão central
- [ ] Estudar histórico de bugfixes em `docs/fix/wf02/v100-v114/`
- [ ] Modificar workflow de desenvolvimento (criar V115 experimental)
- [ ] Implementar nova validação ou mensagem

### Nível 3: Avançado (2-4 semanas)

- [ ] Ler `03_DATABASE_PATTERNS.md` - Entender race conditions
- [ ] Ler `04_WORKFLOW_INTEGRATION.md` - Comunicação entre WFs
- [ ] Implementar nova feature completa (novo serviço, novo estado)
- [ ] Criar documentação completa (PLAN + implementação + teste)
- [ ] Fazer deployment para produção

### Nível 4: Expert (2+ meses)

- [ ] Entender todas as 114 versões do WF02 (histórico completo)
- [ ] Dominar todos os 7 workflows e integrações
- [ ] Contribuir com melhorias arquiteturais
- [ ] Mentorar novos desenvolvedores
- [ ] Criar novos padrões e guidelines

---

## 📞 Referências Rápidas

### Documentação Técnica

- **Contexto Completo**: `CLAUDE.md`
- **Setup Inicial**: `docs/Setups/QUICKSTART.md`
- **Workflows Organizados**: `n8n/workflows/README.md`
- **Scripts**: `scripts/README.md`
- **Índice Geral**: `docs/INDEX.md`

### Workflows de Produção

- **WF01 V2.8.3**: Deduplicação PostgreSQL
- **WF02 V114**: AI Agent + State Machine + WF06 integration ⭐
- **WF05 V7**: Appointment Scheduler (hardcoded)
- **WF06 V2.2**: Calendar Availability Service
- **WF07 V13**: Email Sender (INSERT...SELECT)

### Correções Críticas

- **V111**: Database row locking (race conditions)
- **V113.1**: WF06 suggestions persistence
- **V114**: PostgreSQL TIME fields
- **V104+V105**: State sync + routing fix
- **V76+**: Proactive UX approach

---

## 🔗 Links Úteis

### Documentação Externa

- **n8n Docs**: https://docs.n8n.io/
- **n8n Breaking Changes 2.0**: https://docs.n8n.io/2-0-breaking-changes/
- **PostgreSQL Row Locking**: https://www.postgresql.org/docs/current/explicit-locking.html
- **Evolution API**: https://doc.evolution-api.com/

### Community

- **n8n Forum**: https://community.n8n.io/
- **n8n GitHub**: https://github.com/n8n-io/n8n

---

**Mantido por**: Bruno Rosa & Claude Code
**Data de Organização**: 2026-04-29
**Status**: ✅ COMPLETO - Production V1 (WF02 V114)
