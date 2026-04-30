# Plano de Implementação - E2 Soluções Bot v3

**Data Criação**: 2025-01-12
**Baseado em**: `e2-solucoes-bot-prompt-v3.md` + análise de gaps
**Status Atual**: 25% completo (15/60 arquivos)
**Para uso com**: `/sc:task` command

---

## 📋 Visão Geral do Plano

### Objetivo
Completar a implementação do bot WhatsApp E2 Soluções, transformando o sistema de 25% → 100% funcional com todas as features especificadas no prompt v3.

### Estratégia
**Abordagem Iterativa e Incremental** - 4 Fases com entregas incrementais:
- **FASE 1**: MVP Completo (funcionalidade end-to-end)
- **FASE 2**: Produção e Operações
- **FASE 3**: Documentação Completa
- **FASE 4**: Otimizações (opcional)

### Métricas de Sucesso
- ✅ Bot responde sobre TODOS os 5 serviços da E2
- ✅ Agendamento de visitas 100% automático
- ✅ Sincronização bidirecional com RD Station CRM
- ✅ Notificações automáticas (Email + Discord)
- ✅ Deploy em produção com SSL/HTTPS
- ✅ Documentação completa para operação

---

## 🎯 FASE 1: MVP Completo (Prioridade CRÍTICA)

**Duração Estimada**: 8-12 dias
**Objetivo**: Sistema funcionando end-to-end com todos os recursos essenciais
**Critério de Sucesso**: Cliente consegue conversar com bot, receber análise, agendar visita e ser sincronizado no CRM

### Sprint 1.1: RAG e Base de Conhecimento Completa
**Duração**: 3-5 dias
**Objetivo**: Bot pode responder perguntas sobre TODOS os serviços

#### Tarefas

##### 1. Completar Base de Conhecimento (3 arquivos faltantes)

**1.1 - Criar `knowledge/servicos/projetos_eletricos.md`**
```yaml
prioridade: CRÍTICA
estimativa: 2-3 horas
descrição: Conteúdo completo sobre projetos elétricos
estrutura:
  - O que é e para que serve
  - Tipos de projetos (residencial, comercial, industrial)
  - Processo de desenvolvimento
  - Adequações e regularizações
  - Dimensionamento de cargas
  - Laudos técnicos
  - Normas aplicáveis (NBR 5410, NR-10)
  - Perguntas frequentes
  - Quando contratar
template: Seguir padrão de energia_solar.md
validação: Mínimo 100 linhas, máximo 150 linhas
```

**1.2 - Criar `knowledge/servicos/armazenamento_energia.md`**
```yaml
prioridade: CRÍTICA
estimativa: 2-3 horas
descrição: Conteúdo completo sobre BESS
estrutura:
  - O que é sistema de armazenamento
  - Aplicações (backup, integração solar, gestão demanda)
  - Tecnologias de baterias (Lítio LFP, Chumbo-ácido, Fluxo)
  - Benefícios e ROI
  - Dimensionamento
  - Integração com solar
  - Casos de uso típicos
  - Perguntas frequentes
template: Seguir padrão de energia_solar.md
validação: Mínimo 100 linhas, máximo 150 linhas
```

**1.3 - Criar `knowledge/servicos/analise_laudos.md`**
```yaml
prioridade: CRÍTICA
estimativa: 2-3 horas
descrição: Conteúdo completo sobre análise de energia e laudos
estrutura:
  - Tipos de análise (consumo, qualidade, perícia)
  - Análise de consumo energético
  - Análise de qualidade de energia
  - Laudos periciais
  - Quando contratar cada tipo
  - Processo de análise
  - Equipamentos utilizados
  - Entregáveis
  - Perguntas frequentes
template: Seguir padrão de energia_solar.md
validação: Mínimo 100 linhas, máximo 150 linhas
```

##### 2. Implementar Sistema RAG Completo

**2.1 - Criar `scripts/ingest-knowledge.sh`**
```yaml
prioridade: CRÍTICA
estimativa: 4-6 horas
descrição: Script para gerar embeddings e popular Supabase
funcionalidades:
  - Ler todos os arquivos .md em knowledge/
  - Dividir em chunks (500-1000 chars)
  - Gerar embeddings via OpenAI API
  - Inserir em Supabase knowledge_documents
  - Logging de progresso
  - Tratamento de erros
tecnologias: bash + curl + jq
dependências: OPENAI_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_KEY
validação: Executar e verificar dados no Supabase
```

**2.2 - Atualizar `database/supabase_functions.sql`**
```yaml
prioridade: CRÍTICA
estimativa: 1-2 horas
descrição: Garantir função match_documents está completa
validações:
  - Função existe e está correta
  - Índice ivfflat criado
  - Testes de similaridade funcionando
  - Performance adequada (<500ms)
teste: Query de similaridade retorna resultados relevantes
```

**2.3 - Criar `n8n/workflows/03_rag_knowledge_query.json`**
```yaml
prioridade: CRÍTICA
estimativa: 4-6 horas
descrição: Workflow completo de query RAG
estrutura:
  - Trigger: HTTP POST /webhook/rag-query
  - Input: query_text, category (opcional)
  - Generate embedding (OpenAI API)
  - Query Supabase match_documents()
  - Format results para o AI Agent
  - Return structured response
nodes:
  - HTTP Request (OpenAI Embeddings)
  - Supabase (match_documents)
  - Code (formatting)
  - Respond to Webhook
validação:
  - Testar query "como funciona energia solar"
  - Verificar retorno de 3-5 resultados relevantes
```

**Entrega Sprint 1.1**: Bot responde perguntas sobre TODOS os 5 serviços com RAG funcional

---

### Sprint 1.2: Sistema de Agendamento Completo
**Duração**: 3-5 dias
**Objetivo**: Bot agenda visitas técnicas automaticamente no Google Calendar

#### Tarefas

##### 1. Workflow de Agendamento Principal

**1.1 - Criar `n8n/workflows/05_appointment_scheduler.json`**
```yaml
prioridade: CRÍTICA
estimativa: 6-8 horas
descrição: Workflow completo de agendamento
estrutura:
  endpoints:
    - POST /webhook/check-availability
      input: preferred_days, preferred_shift, service_type
      output: available_slots[]

    - POST /webhook/confirm-appointment
      input: slot_id, lead_data
      output: confirmation_details

  lógica:
    1. Buscar eventos Google Calendar
    2. Filtrar por horário comercial (8h-18h, exceto almoço)
    3. Gerar slots disponíveis (90min cada)
    4. Buffer de 30min entre visitas
    5. Criar evento no Calendar
    6. Salvar em appointments table
    7. Criar task no RD Station
    8. Retornar confirmação

nodes_principais:
  - Google Calendar: List Events
  - Code: Generate Available Slots
  - Google Calendar: Create Event
  - Postgres: Insert Appointment
  - RD Station: Create Task
  - Code: Format Response

configurações:
  working_hours: 08:00-18:00
  lunch_break: 12:00-13:00
  appointment_duration: 90 min
  buffer_time: 30 min
  days_ahead: 14

validação:
  - Listar slots disponíveis
  - Criar agendamento
  - Verificar evento no Calendar
  - Verificar registro no banco
  - Verificar task no RD Station
```

##### 2. Workflow de Lembretes

**2.1 - Criar `n8n/workflows/06_appointment_reminders.json`**
```yaml
prioridade: CRÍTICA
estimativa: 4-6 horas
descrição: Lembretes automáticos 24h e 2h antes

estrutura:
  trigger: Schedule (cron)
  schedule: "0 8,10,12,14,16 * * *" (5x/dia)

  fluxo:
    1. Query appointments próximos
    2. Para cada appointment:
       - Se 24h antes E reminder_24h_sent=false:
         → Enviar WhatsApp
         → Enviar Email
         → Marcar reminder_24h_sent=true

       - Se 2h antes E reminder_2h_sent=false:
         → Enviar WhatsApp
         → Marcar reminder_2h_sent=true

nodes:
  - Schedule Trigger (cron)
  - Postgres: Query Upcoming Appointments
  - Switch: Check Reminder Type
  - Evolution API: Send WhatsApp (2 nodes)
  - HTTP Request: Email Workflow (2 nodes)
  - Postgres: Update Reminder Flags (2 nodes)

mensagens:
  24h:
    whatsapp: "⏰ Lembrete E2 Soluções\n\nSua visita técnica está agendada para amanhã, {{data}}, entre {{hora_ini}} e {{hora_fim}}.\n\nCaso precise reagendar, responda com *reagendar*."

  2h:
    whatsapp: "🚗 O técnico está a caminho!\n\nSua visita da E2 Soluções está confirmada para hoje, entre {{hora_ini}} e {{hora_fim}}.\n\nQualquer problema, responda esta mensagem."

validação:
  - Simular appointment para amanhã
  - Verificar envio de lembrete 24h
  - Verificar flag atualizada
  - Simular appointment para daqui 2h
  - Verificar envio de lembrete 2h
```

**Entrega Sprint 1.2**: Agendamento completamente automático com lembretes

---

### Sprint 1.3: Sistema de Notificações por Email
**Duração**: 2-3 dias
**Objetivo**: Emails automáticos para equipe e clientes

#### Tarefas

##### 1. Templates de Email HTML

**1.1 - Criar `email-templates/novo_lead.html`**
```yaml
prioridade: IMPORTANTE
estimativa: 1-2 horas
descrição: Email para comercial quando novo lead completa dados
destinatário: EMAIL_COMERCIAL
conteúdo:
  - Cabeçalho E2 Soluções
  - Dados do lead (nome, email, telefone, serviço)
  - Resumo da necessidade
  - Análise da IA (se houver)
  - Link para RD Station deal
  - Botão CTA "Ver no CRM"
estilo: Responsivo, cores E2 (verde/branco)
```

**1.2 - Criar `email-templates/confirmacao_agendamento.html`**
```yaml
prioridade: IMPORTANTE
estimativa: 1-2 horas
descrição: Confirmação de agendamento para cliente
destinatário: lead.email
conteúdo:
  - Confirmação de agendamento
  - Data e horário
  - Dados do técnico
  - Endereço da visita
  - Instruções de preparação
  - Contato para reagendamento
  - Link para adicionar ao calendário (.ics)
estilo: Profissional, amigável
```

**1.3 - Criar `email-templates/lembrete_24h.html`**
```yaml
prioridade: IMPORTANTE
estimativa: 1 hora
descrição: Lembrete 24h antes
conteúdo:
  - Lembrete da visita amanhã
  - Confirmação de dados
  - Contato para reagendamento
estilo: Simples, direto
```

**1.4 - Criar `email-templates/lembrete_2h.html`**
```yaml
prioridade: IMPORTANTE
estimativa: 1 hora
descrição: Lembrete 2h antes
conteúdo:
  - Técnico a caminho
  - Chegada em breve
  - Contato emergencial
estilo: Urgente, conciso
```

**1.5 - Criar `email-templates/apos_visita.html`**
```yaml
prioridade: DESEJÁVEL
estimativa: 1-2 horas
descrição: Follow-up pós-visita
conteúdo:
  - Agradecimento pela visita
  - Próximos passos
  - Link para proposta (futuro)
  - Pesquisa de satisfação (futuro)
estilo: Agradecimento, profissional
```

##### 2. Workflow de Envio de Emails

**2.1 - Criar `n8n/workflows/07_send_email.json`**
```yaml
prioridade: IMPORTANTE
estimativa: 4-5 horas
descrição: Workflow centralizado de envio de emails

estrutura:
  trigger: HTTP POST /webhook/send-email
  input:
    template: nome_do_template
    to: email_destinatario
    data: objeto_com_variaveis

  fluxo:
    1. Validar input
    2. Carregar template HTML
    3. Substituir variáveis {{nome}}, {{data}}, etc
    4. Enviar via SMTP
    5. Log de envio
    6. Retornar status

nodes:
  - Webhook
  - Switch: Select Template
  - Read Binary File: Load Template (5 nodes)
  - Code: Replace Variables
  - Gmail/SMTP: Send Email
  - Postgres: Log Email Sent
  - Respond to Webhook

templates_suportados:
  - novo_lead
  - confirmacao_agendamento
  - lembrete_24h
  - lembrete_2h
  - apos_visita

configuração_smtp:
  host: SMTP_HOST
  port: SMTP_PORT
  secure: SMTP_SECURE
  user: SMTP_USER
  password: SMTP_PASSWORD
  from: EMAIL_FROM

validação:
  - Enviar cada tipo de email
  - Verificar recebimento
  - Validar formatação
  - Verificar links funcionam
```

**Entrega Sprint 1.3**: Sistema completo de notificações por email

---

### Sprint 1.4: Sincronização CRM Bidirecional
**Duração**: 2 dias
**Objetivo**: RD Station e bot sincronizados nos dois sentidos

#### Tarefas

**1.1 - Criar `n8n/workflows/09_rdstation_webhook_handler.json`**
```yaml
prioridade: IMPORTANTE
estimativa: 5-6 horas
descrição: Receber e processar webhooks do RD Station

estrutura:
  trigger: Webhook POST /webhook/rdstation-events

  eventos_suportados:
    - deal.created
    - deal.updated
    - deal.stage_changed
    - deal.lost
    - deal.won
    - contact.updated
    - task.created
    - note.created

  fluxo:
    1. Validar signature do webhook
    2. Identificar tipo de evento
    3. Buscar dados locais correspondentes
    4. Atualizar banco de dados local
    5. Trigger ações no bot (se necessário)
    6. Log de sincronização

nodes:
  - Webhook
  - Code: Validate Signature
  - Switch: Event Type
  - Postgres: Find Local Record
  - Postgres: Update Local Data
  - Switch: Trigger Bot Actions
  - Evolution API: Send Message (condicional)
  - Postgres: Log Sync

validação_signature:
  secret: RDSTATION_WEBHOOK_SECRET
  algorithm: HMAC-SHA256

ações_condicionais:
  deal.stage_changed:
    - Se mudou para "Proposta Enviada":
      → Notificar cliente no WhatsApp

  deal.lost:
    - Registrar motivo
    - Pausar automação bot

  task.created:
    - Se task.type = "Ligar para cliente":
      → Notificar no Discord

validação:
  - Simular webhook de cada tipo
  - Verificar atualização no banco
  - Verificar ações disparadas
  - Testar signature inválida (rejeitar)
```

**1.2 - Configurar Webhooks no RD Station**
```yaml
prioridade: IMPORTANTE
estimativa: 1 hora
descrição: Configuração via interface RD Station
passos:
  1. Acessar RD Station CRM > Configurações > Integrações > Webhooks
  2. Criar webhook para cada evento:
     - URL: https://n8n.dominio.com.br/webhook/rdstation-events
     - Secret: RDSTATION_WEBHOOK_SECRET
     - Eventos: deal.*, contact.updated, task.created, note.created
  3. Testar webhook com evento de teste
  4. Validar recebimento no n8n
documentação: Salvar em docs/Setups/SETUP_RDSTATION.md
```

**Entrega Sprint 1.4**: Sincronização bidirecional completa com RD Station

---

### Sprint 1.5: Handoff para Humanos
**Duração**: 1-2 dias
**Objetivo**: Transferência suave para equipe comercial

#### Tarefas

**1.1 - Criar `n8n/workflows/10_handoff_to_human.json`**
```yaml
prioridade: IMPORTANTE
estimativa: 3-4 horas
descrição: Workflow de transferência para atendente humano

estrutura:
  trigger: HTTP POST /webhook/handoff
  input:
    conversation_id: UUID
    reason: string (opcional)

  fluxo:
    1. Atualizar conversation state = 'handoff_comercial'
    2. Criar task urgente no RD Station
    3. Notificar Discord (canal #comercial)
    4. Enviar email para EMAIL_COMERCIAL
    5. Pausar automação do bot
    6. Enviar mensagem WhatsApp ao cliente
    7. Log de handoff

nodes:
  - Webhook
  - Postgres: Update Conversation State
  - RD Station: Create Urgent Task
  - Discord: Send Message
  - Execute Workflow: 07_send_email
  - Postgres: Pause Bot Automation
  - Evolution API: Send Message
  - Postgres: Log Handoff

mensagens:
  discord: |
    🚨 **HANDOFF URGENTE**

    Cliente: {{nome}} ({{phone}})
    Serviço: {{service_type}}
    Motivo: {{reason}}

    RD Station: [Ver Deal]({{rdstation_deal_url}})

    @comercial

  whatsapp_cliente: |
    Entendi! Vou te conectar com nosso time comercial agora mesmo.

    Em instantes um atendente vai continuar a conversa. ⏳

    Enquanto isso, posso adiantar alguma informação?

  email_comercial:
    template: handoff_urgente.html
    subject: "[URGENTE] Cliente solicitou atendimento humano"

validação:
  - Simular handoff
  - Verificar task no RD Station
  - Verificar mensagem no Discord
  - Verificar email recebido
  - Verificar bot pausado
```

**Entrega Sprint 1.5**: Sistema completo de handoff para equipe comercial

---

## 🏗️ FASE 2: Produção e Operações (Prioridade ALTA)

**Duração Estimada**: 2-3 dias
**Objetivo**: Sistema pronto para deploy em servidor de produção
**Critério de Sucesso**: Deploy com SSL, backups automáticos, monitoramento funcionando

### Sprint 2.1: Infraestrutura de Produção
**Duração**: 1-2 dias

#### Tarefas

**2.1.1 - Criar `docker-compose.yml` (Produção)**
```yaml
prioridade: ALTA
estimativa: 4-6 horas
descrição: Stack completa para produção com SSL

diferenças_vs_dev:
  segurança:
    - Todas as portas internas apenas
    - Apenas 80/443 expostos via Traefik
    - Autenticação obrigatória n8n
    - Secrets via Docker secrets (não .env)

  performance:
    - Resource limits (CPU/Memory)
    - Healthchecks rigorosos
    - Restart policies: unless-stopped

  persistência:
    - Volumes nomeados
    - Backup automático

  ssl:
    - Traefik com Let's Encrypt
    - Certificados automáticos
    - HTTP → HTTPS redirect

serviços:
  traefik:
    image: traefik:v2.10
    ports: ["80:80", "443:443"]
    volumes:
      - /var/run/docker.sock
      - ./configs/traefik/traefik.yml
      - ./configs/traefik/dynamic
      - traefik-certs:/letsencrypt

  n8n:
    depends_on: [postgres, redis]
    labels:
      - traefik.enable=true
      - traefik.http.routers.n8n.rule=Host(`${N8N_HOST}`)
      - traefik.http.routers.n8n.tls.certresolver=letsencrypt
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_PROTOCOL=https
    deploy:
      resources:
        limits: {cpus: '2', memory: 2G}

  [demais serviços com configurações prod...]

validação:
  - docker-compose config (sem erros)
  - Simular startup
  - Verificar SSL funciona
  - Testar healthchecks
```

**2.1.2 - Criar Configurações Traefik**
```yaml
configs_necessários:
  - docker/configs/traefik/traefik.yml (config principal)
  - docker/configs/traefik/dynamic/middlewares.yml (security headers)
  - docker/configs/traefik/dynamic/tls.yml (SSL config)

traefik.yml:
  entryPoints:
    web: {address: ":80"}
    websecure: {address: ":443"}

  certificatesResolvers:
    letsencrypt:
      acme:
        email: ${TRAEFIK_ACME_EMAIL}
        storage: /letsencrypt/acme.json
        httpChallenge: {entryPoint: web}

middlewares.yml:
  - security-headers (HSTS, CSP, etc)
  - rate-limit
  - compress
  - auth (básica)

tls.yml:
  - Minimum TLS 1.2
  - Strong ciphers apenas
```

**2.1.3 - Criar `.env.example` (Produção)**
```yaml
prioridade: ALTA
estimativa: 1 hora
descrição: Template de variáveis de ambiente para produção

seções:
  - DOMÍNIOS (com exemplos)
  - n8n (configurações prod)
  - PostgreSQL (senhas geradas)
  - Supabase (todos os JWTs)
  - Redis (senha forte)
  - APIs Externas
  - Evolution API
  - Google Services
  - RD Station CRM
  - Discord
  - Email/SMTP
  - Traefik
  - Configurações do Bot

instruções:
  - Como gerar senhas fortes
  - Como obter cada API key
  - Links para documentação
```

**2.1.4 - Criar `scripts/start-prod.sh`**
```yaml
prioridade: ALTA
estimativa: 2-3 horas
descrição: Script inteligente de startup produção

funcionalidades:
  - Validar .env completo
  - Validar domínios configurados
  - Verificar Docker/Compose instalado
  - Criar volumes se não existem
  - Iniciar stack prod
  - Aguardar healthchecks
  - Testar conectividade
  - Exibir status e próximos passos

validações_pre_start:
  - DNS apontando corretamente
  - Portas 80/443 liberadas
  - Certificados SSL válidos (ou criáveis)
  - Credenciais API válidas

output:
  - URLs de acesso
  - Status de cada serviço
  - Logs de inicialização
  - Warnings/erros encontrados
```

---

### Sprint 2.2: Scripts Operacionais
**Duração**: 1 dia

#### Tarefas

**2.2.1 - Criar `scripts/backup.sh`**
```yaml
prioridade: ALTA
estimativa: 3-4 horas
descrição: Backup completo do sistema

backups:
  postgres_main:
    comando: pg_dump
    formato: custom (.dump)
    destino: backups/postgres/e2_bot_{{timestamp}}.dump

  supabase_db:
    comando: pg_dump
    formato: custom (.dump)
    destino: backups/supabase/{{timestamp}}.dump

  volumes:
    - n8n_data
    - redis_data
    - traefik-certs
    método: tar.gz
    destino: backups/volumes/{{timestamp}}.tar.gz

  configurations:
    - docker/
    - knowledge/
    - n8n/workflows/
    método: zip
    destino: backups/configs/{{timestamp}}.zip

features:
  - Compressão automática
  - Retenção: 7 dias diários, 4 semanas semanais, 3 meses mensais
  - Upload para Google Drive (opcional)
  - Notificação Discord em caso de falha
  - Logs detalhados

agendamento_sugerido:
  diário: "0 3 * * *" (3h da manhã)
  semanal: "0 4 * * 0" (domingos 4h)

validação:
  - Executar backup
  - Verificar arquivos criados
  - Testar restauração
```

**2.2.2 - Criar `scripts/restore.sh`**
```yaml
prioridade: ALTA
estimativa: 2-3 horas
descrição: Restauração de backup

funcionalidades:
  - Listar backups disponíveis
  - Selecionar backup específico ou mais recente
  - Confirmar restauração (muito destrutivo)
  - Parar containers
  - Restaurar PostgreSQL
  - Restaurar Supabase
  - Restaurar volumes
  - Restaurar configs
  - Reiniciar stack
  - Validar integridade

segurança:
  - Confirmação dupla
  - Backup automático antes de restore
  - Rollback se falhar
  - Logs detalhados

validação:
  - Testar restauração de backup
  - Verificar sistema funcional pós-restore
```

**2.2.3 - Criar `scripts/migrate.sh`**
```yaml
prioridade: MÉDIA
estimativa: 2 horas
descrição: Executar migrations do banco

funcionalidades:
  - Listar migrations disponíveis
  - Verificar migrations aplicadas
  - Aplicar migrations pendentes
  - Rollback migrations (se suportado)
  - Validar schema pós-migration

migrations_path: database/migrations/

validação:
  - Aplicar migration
  - Verificar schema atualizado
  - Testar rollback
```

**2.2.4 - Criar `scripts/health-check.sh`**
```yaml
prioridade: ALTA
estimativa: 2-3 horas
descrição: Validação de saúde do sistema

verificações:
  docker:
    - Containers running
    - Healthchecks passing
    - Resource usage OK

  databases:
    - PostgreSQL acessível
    - Supabase acessível
    - Queries básicas funcionando

  apis:
    - n8n webhook respondendo
    - Evolution API acessível
    - RD Station API autenticada
    - Anthropic API válida

  integrações:
    - Google Calendar conectado
    - Google Drive acessível
    - SMTP funcionando
    - Discord webhook ativo

output:
  - Status geral (OK/WARNING/CRITICAL)
  - Detalhes de cada verificação
  - Recomendações de ação
  - Métricas coletadas

agendamento_sugerido: "*/5 * * * *" (a cada 5 min)
notificar_discord: apenas se CRITICAL
```

**2.2.5 - Criar `scripts/cleanup.sh`**
```yaml
prioridade: BAIXA
estimativa: 1-2 horas
descrição: Limpeza de dados antigos

limpezas:
  chat_memory:
    - Mensagens > 30 dias
    - Função: cleanup_old_chat_memory()

  logs:
    - Arquivos .log > 7 dias

  backups:
    - Aplicar política de retenção

  volumes:
    - Docker volumes órfãos
    - Imagens não utilizadas

segurança:
  - Dry-run mode (listar sem deletar)
  - Confirmação necessária
  - Logs detalhados

agendamento_sugerido: "0 2 * * 0" (domingos 2h)
```

---

## 📚 FASE 3: Documentação Completa (Prioridade MÉDIA)

**Duração Estimada**: 3-4 dias
**Objetivo**: Equipe consegue operar e manter o sistema sem ajuda externa
**Critério de Sucesso**: Novo desenvolvedor consegue subir ambiente e fazer deploy seguindo docs

### Sprint 3.1: Documentação de Setups
**Duração**: 1-2 dias

#### Tarefas

**3.1.1 - Criar Guias de Setup (8 documentos)**

Cada documento deve seguir estrutura padrão:
```markdown
# SETUP_{SERVIÇO}.md

## Pré-requisitos
## Criar Conta/Credenciais
## Configurar API/Serviço
## Integrar com n8n
## Variáveis de Ambiente
## Testar Integração
## Troubleshooting Comum
## Links Úteis
```

**Documentos necessários**:

1. `SETUP_DOCKER.md` (1-2h)
   - Instalação Docker/Compose
   - Comandos básicos
   - Troubleshooting Docker

2. `SETUP_N8N.md` (2-3h)
   - Instalação e configuração
   - Importar workflows
   - Credenciais
   - Custom nodes (RD Station)
   - Debugging workflows

3. `SETUP_SUPABASE.md` (2-3h)
   - Configuração local vs cloud
   - Vector extension
   - Migrations
   - Functions
   - Políticas de acesso

4. `SETUP_EVOLUTION_API.md` (1-2h)
   - Provisionamento de instância
   - Configurar webhook
   - Conectar WhatsApp
   - Testar envio/recebimento

5. `SETUP_CLAUDE.md` (1h)
   - Obter API key
   - Configurar billing
   - Rate limits
   - Best practices

6. `SETUP_GOOGLE.md` (3-4h)
   - Service Account
   - Google Calendar API
   - Google Drive API
   - Permissões e scopes
   - Testar integração

7. `SETUP_DISCORD.md` (1h)
   - Criar webhook
   - Configurar canal
   - Testar notificações

8. `SETUP_EMAIL.md` (1-2h)
   - SMTP Gmail
   - App passwords
   - Configurar templates
   - Testar envio

---

### Sprint 3.2: Documentação Operacional
**Duração**: 1-2 dias

#### Tarefas

**3.2.1 - Documentação PLAN** (5 documentos)

1. `docs/PLAN/architecture.md` (2-3h)
   - Decisões arquiteturais
   - Diagramas (Mermaid)
   - Trade-offs considerados
   - Dependências externas

2. `docs/PLAN/roadmap.md` (1-2h)
   - Histórico de implementação
   - Versões e releases
   - Roadmap futuro
   - Backlog de melhorias

3. `docs/PLAN/requirements.md` (1-2h)
   - Requisitos funcionais
   - Requisitos não-funcionais
   - Casos de uso
   - User stories

4. `docs/PLAN/milestones.md` (1h)
   - Marcos principais
   - Entregas realizadas
   - Próximos marcos

**3.2.2 - Documentação Development** (7 documentos)

1. `docs/development/local_setup.md` (2h)
   - Como rodar localmente
   - Pré-requisitos
   - Passo a passo
   - Troubleshooting

2. `docs/development/workflow_guide.md` (3h)
   - Como funcionam os workflows
   - Estrutura de cada workflow
   - Como criar novo workflow
   - Debugging

3. `docs/development/database_guide.md` (2h)
   - Schema completo
   - Relacionamentos
   - Queries úteis
   - Migrations

4. `docs/development/testing.md` (2h)
   - Como testar o bot
   - Testes manuais
   - Cenários de teste
   - Validação end-to-end

5. `docs/development/debugging.md` (2h)
   - Como debugar workflows
   - Logs úteis
   - Ferramentas de debug
   - Problemas comuns

6. `docs/development/contributing.md` (1h)
   - Workflow Git
   - Padrões de código
   - Como contribuir
   - Code review

**3.2.3 - Documentação Deployment** (7 documentos)

1. `docs/deployment/prerequisites.md` (1h)
   - Requisitos de servidor
   - Software necessário
   - Credenciais necessárias

2. `docs/deployment/production_setup.md` (3h)
   - Deploy passo a passo
   - Configurações de produção
   - Validação pós-deploy

3. `docs/deployment/ssl_certificates.md` (2h)
   - Configuração SSL
   - Let's Encrypt
   - Renovação automática

4. `docs/deployment/domain_dns.md` (1h)
   - Configuração DNS
   - Subdomínios necessários
   - Validação DNS

5. `docs/deployment/security.md` (2h)
   - Hardening do servidor
   - Firewall
   - Secrets management
   - Best practices

6. `docs/deployment/rollback.md` (2h)
   - Procedimentos de rollback
   - Quando fazer rollback
   - Como reverter deploy

**3.2.4 - Documentação Implementation** (8 documentos)

1. `docs/implementation/conversation_flow.md` (2h)
   - Fluxo detalhado de conversa
   - Estados e transições
   - Árvore de decisão

2. `docs/implementation/ai_agent_config.md` (2h)
   - Configuração do AI Agent
   - System prompt completo
   - Tools disponíveis
   - Tuning

3. `docs/implementation/rag_setup.md` (2h)
   - Como funciona RAG
   - Embeddings e chunks
   - Query e retrieval
   - Atualizar conhecimento

4. `docs/implementation/image_analysis.md` (1h)
   - Como funciona Vision
   - Prompts de análise
   - Casos de uso

5. `docs/implementation/scheduling_logic.md` (2h)
   - Lógica de agendamento
   - Disponibilidade
   - Conflitos
   - Reagendamento

6. `docs/implementation/notifications.md` (1h)
   - Sistema de notificações
   - Tipos de notificação
   - Templates
   - Triggers

7. `docs/implementation/rdstation_integration.md` (2h)
   - Integração completa CRM
   - Sync bidirecional
   - Webhooks
   - Troubleshooting

**3.2.5 - Documentação Monitoring** (6 documentos)

1. `docs/monitoring/health_checks.md` (1h)
2. `docs/monitoring/logs.md` (1h)
3. `docs/monitoring/metrics.md` (2h)
4. `docs/monitoring/alerts.md` (1h)
5. `docs/monitoring/backup_restore.md` (1h)
6. `docs/monitoring/incident_response.md` (2h)

---

### Sprint 3.3: Conteúdo Adicional da Base de Conhecimento
**Duração**: 1 dia (opcional mas recomendado)

#### Tarefas

**3.3.1 - Conteúdo FAQ**
```yaml
arquivo: knowledge/faq/perguntas_frequentes.md
estimativa: 2-3 horas
conteúdo:
  - 20-30 perguntas mais comuns
  - Categorizadas por serviço
  - Respostas concisas
  - Links para documentação
```

**3.3.2 - Especificações Técnicas**
```yaml
arquivos:
  - knowledge/tecnicos/especificacoes_solar.md (2h)
  - knowledge/tecnicos/especificacoes_subestacao.md (2h)
  - knowledge/tecnicos/especificacoes_bess.md (2h)
  - knowledge/tecnicos/normas_tecnicas.md (2h)

conteúdo:
  - Dados técnicos detalhados
  - Especificações de equipamentos
  - Normas aplicáveis
  - Cálculos e dimensionamentos
```

**3.3.3 - Portfolio**
```yaml
arquivo: knowledge/portfolio/projetos_realizados.md
estimativa: 1-2 horas
conteúdo:
  - Casos de sucesso
  - Fotos de projetos
  - Depoimentos
  - Números (kWp instalados, clientes, etc)
```

---

## 🎨 FASE 4: Otimizações e Melhorias (Opcional)

**Duração Estimada**: Variável
**Prioridade**: BAIXA (apenas após FASES 1-3 completas)

### Possíveis Melhorias Futuras

1. **Analytics e Dashboards**
   - Dashboard de métricas do bot
   - Funil de conversão
   - Taxa de agendamento
   - NPS automático

2. **Testes Automatizados**
   - Testes unitários workflows
   - Testes E2E completos
   - CI/CD pipeline

3. **Multi-idioma**
   - Suporte a inglês
   - Detecção automática de idioma

4. **Integrações Adicionais**
   - Slack
   - Telegram
   - Facebook Messenger

5. **IA Avançada**
   - Fine-tuning Claude
   - Análise de sentimento
   - Predição de conversão

---

## 📊 Resumo do Plano de Implementação

### Estatísticas Gerais

| Métrica | Valor |
|---------|-------|
| **Total de Tarefas** | ~68 itens |
| **Duração Total Estimada** | 24-35 dias úteis |
| **Arquivos a Criar** | ~45 arquivos |
| **Linhas de Código Estimadas** | ~15.000 linhas |
| **Documentação** | ~40 documentos |

### Por Fase

| Fase | Duração | Prioridade | Entregas |
|------|---------|------------|----------|
| **FASE 1: MVP** | 8-12 dias | CRÍTICA | Sistema funcional completo |
| **FASE 2: Produção** | 2-3 dias | ALTA | Deploy em produção |
| **FASE 3: Docs** | 3-4 dias | MÉDIA | Documentação completa |
| **FASE 4: Otimizações** | Variável | BAIXA | Melhorias adicionais |

### Por Categoria de Trabalho

| Categoria | Itens | Horas Est. | % do Total |
|-----------|-------|------------|------------|
| Workflows n8n | 6 workflows | 32-40h | 35% |
| Base Conhecimento | 3+6 arquivos | 16-20h | 18% |
| Scripts | 7 scripts | 16-20h | 18% |
| Infraestrutura | 5 configs | 10-14h | 12% |
| Documentação | 40+ docs | 60-80h | 45% |
| Templates | 5 HTML | 6-8h | 7% |

---

## 🎯 Critérios de Aceitação

### FASE 1 - MVP Completo ✅

- [ ] Bot responde perguntas sobre TODOS os 5 serviços via RAG
- [ ] Bot coleta dados estruturados de forma conversacional
- [ ] Bot analisa imagens (contas de energia, fotos de local)
- [ ] Bot agenda visitas no Google Calendar automaticamente
- [ ] Bot envia lembretes 24h e 2h antes da visita
- [ ] Bot sincroniza com RD Station CRM (ambas direções)
- [ ] Bot envia notificações por email (5 templates)
- [ ] Bot transfere para humano quando solicitado
- [ ] Todas as integrações testadas e funcionando

### FASE 2 - Produção ✅

- [ ] Docker Compose produção funciona com SSL
- [ ] Scripts de backup/restore testados
- [ ] Health checks validados
- [ ] Deploy em servidor de produção realizado
- [ ] Sistema acessível via HTTPS
- [ ] Monitoramento básico funcionando

### FASE 3 - Documentação ✅

- [ ] Todos os 8 guias de setup completos
- [ ] Documentação de desenvolvimento pronta
- [ ] Procedimentos de deployment documentados
- [ ] Novo desenvolvedor consegue subir ambiente
- [ ] Equipe operacional consegue manter sistema

---

## 🚀 Como Usar Este Plano com /sc:task

### Comandos Recomendados

**Para executar uma fase completa**:
```bash
/sc:task execute "FASE 1: MVP Completo" --strategy systematic --parallel
```

**Para executar um sprint específico**:
```bash
/sc:task execute "Sprint 1.1: RAG e Base de Conhecimento" --strategy agile
```

**Para executar uma tarefa individual**:
```bash
/sc:task create "Criar knowledge/servicos/projetos_eletricos.md"
```

**Para acompanhar progresso**:
```bash
/sc:task status
```

### Estratégias de Execução

**Systematic** (Recomendado para FASE 1):
- Execução metodológica e ordenada
- Validação em cada etapa
- Documentação simultânea

**Agile** (Para sprints curtos):
- Entregas incrementais
- Feedback rápido
- Ajustes conforme necessário

**Enterprise** (Para FASE 2 e 3):
- Validação rigorosa
- Compliance e segurança
- Documentação obrigatória

---

## 📝 Notas Finais

### Dependências Críticas

Antes de iniciar, garantir:
1. ✅ Anthropic API Key (Claude)
2. ❌ OpenAI API Key (embeddings)
3. ❌ Evolution API instance provisionada
4. ❌ RD Station OAuth2 completo
5. ❌ Google Service Account configurado
6. ❌ Servidor de produção (VPS/Cloud)
7. ❌ Domínio com DNS configurado

### Riscos e Mitigações

**Risco**: APIs podem ter rate limits
**Mitigação**: Implementar retry e backoff, monitorar usage

**Risco**: Integrações podem falhar
**Mitigação**: Logs detalhados, fallbacks, alertas

**Risco**: Complexidade pode atrasar
**Mitigação**: Entregas incrementais, validação constante

### Contatos e Suporte

Para dúvidas sobre implementação:
- Documentação: `/docs`
- Issues: GitHub Issues
- Suporte: time técnico E2 Soluções

---

**Plano criado automaticamente via /sc:analyze**
**Base**: Análise de gaps entre requisitos v3 e implementação atual
**Para execução com**: `/sc:task` command do SuperClaude Framework
