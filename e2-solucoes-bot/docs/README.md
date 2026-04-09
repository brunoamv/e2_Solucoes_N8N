# E2 Bot - Documentação

> **Versão**: 2.0 | **Última Refatoração**: 2026-04-08
> **Objetivo**: Documentação organizada e acessível do projeto E2 Bot

---

## 📋 Navegação Rápida

### 🎯 Documentos Essenciais

| Documento | Descrição | Localização |
|-----------|-----------|-------------|
| **INDEX.md** | Catálogo completo da documentação | `/docs/INDEX.md` |
| **QUICKSTART.md** | Guia de setup inicial (30-45 min) | `/docs/Setups/QUICKSTART.md` |
| **SETUP_EMAIL.md** | Configuração SMTP (Port 465) | `/docs/Setups/SETUP_EMAIL.md` |
| **SETUP_GOOGLE_CALENDAR.md** | OAuth2 Google Calendar | `/docs/Setups/SETUP_GOOGLE_CALENDAR.md` |
| **SETUP_CREDENTIALS.md** | Todas as credenciais n8n | `/docs/Setups/SETUP_CREDENTIALS.md` |

---

## 📁 Estrutura de Diretórios

### `/docs/` (Raiz)
- **INDEX.md** - Catálogo completo de documentação
- **README.md** - Este arquivo (visão geral e navegação)

### `/docs/Setups/` - Guias de Configuração
Documentação de setup e configuração de serviços:
- `SETUP_EMAIL.md` - Configuração SMTP (V3.0 DEFINITIVA - Port 465)
- `SETUP_GOOGLE_CALENDAR.md` - OAuth2 Google Calendar
- `SETUP_CREDENTIALS.md` - Credenciais n8n consolidadas
- `QUICKSTART_EVOLUTION_API.md` - Setup WhatsApp específico

### `/docs/Guides/` - Guias de Usuário
Documentação de uso e referência:
- `PROJECT_STATUS.md` - Status atual do projeto
- Guias de usuário e tutoriais

### `/docs/implementation/` - Implementação de Workflows
Documentação de implementação de features e workflows:
- **WF02**: Guias de implementação V76 (UX proativa, deployment, testes)
- **WF05/WF06**: Calendar e Appointment Scheduler
- Documentação técnica de features e integrações

### `/docs/analysis/` - Análises Técnicas
Análises técnicas e investigações:
- Análises de compatibilidade (Gmail SMTP, n8n versions)
- Análises de otimização (V76 UX, WF07 V9.2)
- Estudos de viabilidade e comparações técnicas

### `/docs/fix/` - Correções de Bugs
Histórico completo de bugfixes documentados:
- **WF05**: V4.0.1 a V4.0.4 (attendees, title, summary, email data)
- **WF07**: V3 a V13 (template access, encoding, STARTTLS, INSERT...SELECT)
- **WF02**: V72 a V76 (state machine, timing, appointment UX)

### `/docs/deployment/` - Deploys e Produção
Procedimentos de deployment e documentação de produção:
- Deploys históricos (V74, V75, WF05 V4-V7, WF07 V6.1-V8.1)
- Checklists de produção
- Estratégias de deployment

### `/docs/PLAN/` - Planejamentos
Planejamentos de features e estratégias de implementação:
- Planejamentos de refatorações
- Análises de arquitetura
- Estratégias de desenvolvimento

### `/docs/status/` - Status e Histórico
Documentação de status e versões históricas:
- Documentação de versões antigas (V3.x, V7x)
- Summaries e solutions de versões passadas
- Troubleshooting histórico

### `/docs/development/` - Desenvolvimento
Documentação de desenvolvimento e práticas:
- Guias de desenvolvimento
- Práticas e padrões

### `/docs/guidelines/` - Diretrizes
Diretrizes e padrões do projeto:
- Convenções de código
- Padrões de documentação

### `/docs/validation/` - Validação e Testes
Documentação de validação e testes:
- Estratégias de teste
- Validação de funcionalidades

### `/docs/sprints/` - Sprints e Iterações
Documentação de sprints e ciclos de desenvolvimento

### `/docs/monitoring/` - Monitoramento
Documentação de monitoramento e observabilidade

### `/docs/diagrams/` - Diagramas
Diagramas de arquitetura e fluxos

### `/docs/errors/` - Registro de Erros
Capturas de tela e logs de erros para debug

---

## 🗂️ Organização por Tipo de Documento

### 📚 Documentação de Referência
- **Setups**: `/docs/Setups/` - Configuração de serviços
- **Guides**: `/docs/Guides/` - Guias de usuário
- **Implementation**: `/docs/implementation/` - Implementações de workflows

### 🔍 Documentação de Desenvolvimento
- **Analysis**: `/docs/analysis/` - Análises técnicas
- **Planning**: `/docs/PLAN/` - Planejamentos
- **Bugfixes**: `/docs/fix/` - Correções documentadas
- **Development**: `/docs/development/` - Práticas de desenvolvimento
- **Guidelines**: `/docs/guidelines/` - Diretrizes e padrões

### 📦 Documentação de Operações
- **Deployment**: `/docs/deployment/` - Deploys e produção
- **Status**: `/docs/status/` - Status e versões históricas
- **Monitoring**: `/docs/monitoring/` - Monitoramento
- **Validation**: `/docs/validation/` - Validação e testes

### 📊 Recursos Adicionais
- **Sprints**: `/docs/sprints/` - Ciclos de desenvolvimento
- **Diagrams**: `/docs/diagrams/` - Diagramas
- **Errors**: `/docs/errors/` - Registro de erros

---

## 🎯 Como Encontrar Documentação

### Por Workflow

**WF01 (WhatsApp Handler)**:
- Configuração: `/docs/Setups/QUICKSTART_EVOLUTION_API.md`
- Status: Estável (V2.8.3)

**WF02 (AI Agent)**:
- Implementação V76: `/docs/implementation/WF02_V76_IMPLEMENTATION_GUIDE.md`
- Deployment: `/docs/implementation/WF02_V76_DEPLOYMENT_SUMMARY.md`
- Status: Ready for Production ✅

**WF05 (Appointment Scheduler)**:
- Deployment V7: `/docs/deployment/DEPLOY_WF05_V7_HARDCODED_FINAL.md`
- Status: Ready for Production (V7) ✅

**WF06 (Calendar Availability)**:
- Documentação: `/docs/implementation/WF06_CALENDAR_AVAILABILITY_SERVICE.md`
- Status: Ready for Production ✅

**WF07 (Email Sender)**:
- Setup SMTP: `/docs/Setups/SETUP_EMAIL.md` (V3.0 - Port 465)
- Bugfix V13: `/docs/fix/BUGFIX_WF07_V13_INSERT_SELECT_FIX.md`
- Status: Ready for Production (V13) ✅

### Por Problema/Erro

**Erro SMTP**: `docs/Setups/SETUP_EMAIL.md` seção Troubleshooting
**Erro Google Calendar**: `docs/Setups/SETUP_GOOGLE_CALENDAR.md` seção Troubleshooting
**Erro PostgreSQL**: `docs/Setups/SETUP_CREDENTIALS.md` seção Troubleshooting

### Por Tarefa

**Setup Inicial**: `/docs/Setups/QUICKSTART.md`
**Configurar Email**: `/docs/Setups/SETUP_EMAIL.md`
**Configurar Calendar**: `/docs/Setups/SETUP_GOOGLE_CALENDAR.md`
**Deploy WF02 V76**: `/docs/implementation/WF02_V76_QUICK_DEPLOY.md`

---

## 📊 Status de Workflows

### Produção Estável
- ✅ **WF01 V2.8.3** - WhatsApp Handler (deduplication)
- ✅ **WF02 V74.1.2** - AI Agent (reactive)

### Ready for Production
- 🚀 **WF02 V76** - AI Agent com UX proativa
- 🚀 **WF05 V7** - Appointment Scheduler (hardcoded business hours)
- 🚀 **WF06** - Calendar Availability Service
- 🚀 **WF07 V13** - Email Sender (INSERT...SELECT pattern)

### Documentação Detalhada
- **WF02 V76**: `/docs/implementation/` (5 documentos)
- **WF05/WF06**: `/docs/implementation/` (1 documento)
- **Setup**: `/docs/Setups/` (3 documentos principais)

---

## 🔧 Configurações Críticas

### SMTP (Port 465 + SSL/TLS)
```yaml
Host: smtp.gmail.com
Port: 465
Secure: true  # ✅ SSL/TLS (marcar checkbox)
User: seu-email@gmail.com
Password: [App Password sem espaços]
```

**Documentação**: `/docs/Setups/SETUP_EMAIL.md`

### Google Calendar OAuth2
```yaml
Client ID: xxxxxxxx.apps.googleusercontent.com
Client Secret: GOCSPX-xxxxxxxxxxxxx
Redirect URI: http://localhost:5678/rest/oauth2-credential/callback
```

**Documentação**: `/docs/Setups/SETUP_GOOGLE_CALENDAR.md`

### PostgreSQL
```yaml
Host: e2bot-postgres-dev
Database: e2bot_dev
User: postgres
Password: CoraRosa
Port: 5432
```

**Documentação**: `/docs/Setups/SETUP_CREDENTIALS.md`

---

## 📝 Convenções de Nomenclatura

### Arquivos de Documentação
```
CATEGORIA_ASSUNTO_VERSÃO_DESCRIÇÃO.md

Categorias:
- ANALYSIS: Análises técnicas
- BUGFIX: Correções de bugs
- DEPLOY: Procedimentos de deploy
- PLAN: Planejamentos
- SETUP: Guias de configuração
- WF0X: Workflows específicos

Exemplos:
- BUGFIX_WF07_V13_INSERT_SELECT_FIX.md
- DEPLOY_WF05_V7_HARDCODED_FINAL.md
- ANALYSIS_N8N_VERSION_UPGRADE_VS_WORKAROUNDS.md
```

---

## 🎓 Recursos de Aprendizado

### Para Iniciantes
1. **Começar aqui**: `/docs/Setups/QUICKSTART.md`
2. **Configurar credenciais**: `/docs/Setups/SETUP_CREDENTIALS.md`
3. **Entender limitações n8n**: `/docs/analysis/ANALYSIS_N8N_VERSION_UPGRADE_VS_WORKAROUNDS.md`

### Para Desenvolvedores
1. **Status do projeto**: `/docs/Guides/PROJECT_STATUS.md`
2. **Catálogo completo**: `/docs/INDEX.md`
3. **Histórico de bugfixes**: `/docs/fix/`
4. **Workflows organizados**: `/n8n/workflows/` (7 ativos) + `/n8n/workflows/old/` (57 arquivados)

### Para Deploy
1. **Deploy WF02 V76**: `/docs/implementation/WF02_V76_QUICK_DEPLOY.md`
2. **Deploy WF05 V7**: `/docs/deployment/DEPLOY_WF05_V7_HARDCODED_FINAL.md`
3. **Deploy WF07 V13**: `/docs/fix/BUGFIX_WF07_V13_INSERT_SELECT_FIX.md`
4. **Workflows README**: `/n8n/workflows/README.md` (procedimentos de deploy)

---

## 🔍 Índice Completo

Para visualizar todos os documentos disponíveis, consulte:

**📖 `/docs/INDEX.md`** - Catálogo completo com descrições e status

---

## 📦 Mudanças na Refatoração (2026-04-08)

### Estrutura Anterior
```
/docs/
  ├── 100+ arquivos .md na raiz
  ├── /Setups/
  ├── /analise/ (português)
  ├── /printErros/ (português)
  └── [outros diretórios em português/inglês misturados]
```

### Estrutura Nova
```
/docs/
  ├── INDEX.md (catálogo)
  ├── README.md (este arquivo)
  ├── /Setups/ (configuração)
  ├── /Guides/ (guias de usuário)
  ├── /implementation/ (workflows específicos)
  ├── /analysis/ (análises técnicas - renomeado)
  ├── /fix/ (bugfixes)
  ├── /deployment/ (deploys)
  ├── /PLAN/ (planejamentos)
  ├── /status/ (histórico)
  ├── /development/ (desenvolvimento)
  ├── /guidelines/ (diretrizes)
  ├── /validation/ (validação)
  ├── /sprints/ (sprints)
  ├── /monitoring/ (monitoramento)
  ├── /diagrams/ (diagramas)
  └── /errors/ (erros - renomeado)
```

### Benefícios
- ✅ **Navegação clara**: Documentos agrupados por categoria
- ✅ **Nomenclatura consistente**: Todas as pastas em inglês
- ✅ **Organização por tipo**: Análises, bugfixes, deploys separados
- ✅ **Setups centralizados**: Guias de configuração em um local
- ✅ **Redução de ruído**: Arquivos organizados por finalidade
- ✅ **QUICKSTART consolidado**: Um único arquivo em `/docs/Setups/QUICKSTART.md`
- ✅ **Workflows organizados**: 7 ativos, 57 em `/old/` para referência histórica

---

**Última Atualização**: 2026-04-08
**Mantido por**: E2 Soluções Dev Team
**Próximo Passo**: Consultar `/docs/INDEX.md` para catálogo completo
