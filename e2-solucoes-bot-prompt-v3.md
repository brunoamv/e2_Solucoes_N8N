# PROJETO: E2 Soluções AI Bot v3 - WhatsApp com IA Conversacional + RD Station CRM

## VISÃO GERAL

Criar um bot de WhatsApp inteligente para a E2 Soluções, uma empresa brasileira especializada em soluções de energia e elétrica. O bot usa n8n como orquestrador e Claude AI como cérebro conversacional. Deve entender linguagem natural, consultar uma base de conhecimento (RAG), analisar imagens enviadas pelos clientes, e seguir um fluxo estruturado de coleta de dados para agendamento de visitas técnicas. Integração completa com RD Station CRM para gestão de leads e pipeline de vendas.

## ARQUITETURA TÉCNICA

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CANAIS DE ENTRADA                                  │
│                    [WhatsApp - Evolution API]                                │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                         n8n (ORQUESTRADOR)                                   │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    🤖 AI AGENT (Claude 3.5 Sonnet)                    │  │
│  │  • Entende linguagem natural                                          │  │
│  │  • Segue roteiro de coleta de dados                                   │  │
│  │  • Consulta base de conhecimento (RAG)                                │  │
│  │  • Analisa imagens com Vision AI                                      │  │
│  │  • Memória persistente por cliente                                    │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│         ↓                    ↓                    ↓                    ↓    │
│  ┌───────────┐      ┌───────────────┐     ┌─────────────┐    ┌───────────┐ │
│  │ Supabase  │      │  PostgreSQL   │     │   Google    │    │ RD Station│ │
│  │  Vector   │      │ Chat Memory   │     │  Services   │    │    CRM    │ │
│  │  Store    │      │  + Leads DB   │     │ Cal/Drive/  │    │  Deals +  │ │
│  │  (RAG)    │      │               │     │   Sheets    │    │  Contacts │ │
│  └───────────┘      └───────────────┘     └─────────────┘    └───────────┘ │
│                              ↓                                              │
│                    ┌─────────────────┐                                      │
│                    │  NOTIFICAÇÕES   │                                      │
│                    │ Email + Discord │                                      │
│                    └─────────────────┘                                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

## SERVIÇOS DA E2 SOLUÇÕES

### 1. Energia Solar Fotovoltaica
- Projetos residenciais, comerciais, industriais e agronegócios
- Instalação de painéis solares
- Sistemas on-grid, off-grid e híbridos
- Dimensionamento personalizado
- Homologação junto à concessionária

### 2. Subestação Elétrica
- Reformas de subestações
- Manutenções preventivas e corretivas
- Construção de novas subestações
- Adequação às normas técnicas
- Comissionamento e testes

### 3. Projetos Elétricos
- Projetos residenciais
- Projetos comerciais e industriais
- Adequações e regularizações
- Dimensionamento de cargas
- Laudos técnicos

### 4. Sistemas de Armazenamento de Energia (BESS)
- Instalação de sistemas de armazenamento
- Estudo de viabilidade técnica e econômica
- Integração com sistemas solares
- Soluções para backup e nobreak
- Gestão de demanda

### 5. Análise de Energia e Laudos
- Análise de consumo energético
- Análise de qualidade de energia
- Laudo para perícia judicial
- Diagnóstico de perdas
- Identificação de problemas elétricos

## INTEGRAÇÃO RD STATION CRM

### Visão Geral

O RD Station CRM será o sistema central de gestão de leads e pipeline de vendas. O bot irá:

1. **Criar Contatos** automaticamente quando um novo lead for identificado
2. **Criar Negociações (Deals)** no pipeline configurado
3. **Atualizar Negociações** conforme o lead avança no funil
4. **Registrar Atividades** (tarefas, notas) sobre cada interação
5. **Sincronizar Bidirecional** - alterações no CRM refletem no bot via webhooks

### Mapeamento de Dados Bot → RD Station CRM

| Dado do Bot | Campo RD Station CRM |
|-------------|---------------------|
| phone_number | contact.phone |
| name | contact.name |
| email | contact.email |
| service_type | deal.deal_source / custom_field |
| address | contact.address (campo customizado) |
| ai_analysis | deal.notes |
| status (agendado) | deal.deal_stage_id (mover no pipeline) |
| appointment_date | deal.deal_activities (tarefa agendada) |

### Pipeline Sugerido no RD Station CRM

```
PIPELINE: Bot WhatsApp E2 Soluções

ETAPAS:
┌──────────────────────────────────────────────────────────────────────────┐
│ 1. Novo Lead    │ 2. Qualificando │ 3. Agendado │ 4. Proposta │ 5. Ganho │
│    (automático) │   (bot coleta)  │  (visita)   │  (comercial)│  (venda) │
└──────────────────────────────────────────────────────────────────────────┘
                                         │
                                         ↓
                                 [6. Perdido] (motivo registrado)
```

### Pacote NPM para n8n

Instalar o pacote de nodes customizados:
```bash
npm install n8n-nodes-rd-station-crm
```

Este pacote fornece nodes nativos para:
- RD Station CRM Contatos
- RD Station CRM Negócios (Deals)
- RD Station CRM Tarefas
- RD Station CRM Notas
- RD Station CRM Empresas
- RD Station CRM Pipelines
- RD Station CRM Webhooks

## COMPORTAMENTO DO BOT

### Princípios de Conversação
1. **Linguagem natural primeiro**: O bot entende o que o cliente quer sem precisar de menus
2. **Menu como fallback**: Se não entender a intenção, oferece opções numeradas
3. **Coleta estruturada**: Mesmo conversando naturalmente, segue um fluxo para coletar todos os dados necessários
4. **RAG integrado**: Responde perguntas sobre serviços consultando a base de conhecimento
5. **Vision AI**: Analisa fotos enviadas (conta de luz, subestação, quadro elétrico)
6. **CRM Sync**: Cada interação é registrada no RD Station CRM em tempo real

### Exemplos de Interação Inteligente

```
Cliente: "Oi, quero colocar energia solar na minha empresa"
Bot: [ENTENDE: serviço = energia_solar, segmento = comercial/industrial]
     [CRM: Cria contato + negociação na etapa "Novo Lead"]
     
     "Olá! Que ótimo que você está interessado em energia solar! ☀️
      
      Para preparar um orçamento personalizado, vou precisar de algumas informações.
      
      Primeiro, qual é o seu nome e sobrenome?"

Cliente: "João Silva"
Bot: [SALVA: nome = "João Silva"]
     [CRM: Atualiza contato com nome, move deal para "Qualificando"]
     
     "Prazer, João! 
      
      Qual o seu melhor email para contato?"

Cliente: "joao@empresa.com.br"
Bot: [SALVA: email = "joao@empresa.com.br"]
     [CRM: Atualiza contato com email]
     
     "Perfeito! Agora me conta, qual o endereço do imóvel onde 
      você quer instalar o sistema solar?"

Cliente: "Rua das Indústrias, 500, Distrito Industrial, Goiânia"
Bot: [SALVA: endereco]
     [CRM: Atualiza campo customizado address]
     
     "Ótimo! Para dimensionar o sistema ideal, preciso analisar 
      sua conta de energia. Pode me enviar uma foto da última conta?"

Cliente: [ENVIA FOTO DA CONTA]
Bot: [CLAUDE VISION: analisa conta de luz]
     [GOOGLE DRIVE: salva imagem]
     [CRM: Adiciona nota com análise, atualiza valor estimado do deal]
     
     "Recebi sua conta! Analisando...
      
      📊 Consumo médio: 2.500 kWh/mês
      💡 Estimativa: Sistema de ~25 kWp
      💰 Economia estimada: R$ 2.800/mês
      
      Você tem interesse em sistema de armazenamento de energia (bateria) 
      para backup em caso de queda? Ou prefere apenas o sistema solar on-grid?"

Cliente: "Só o solar mesmo"
Bot: [SALVA: servico_adicional = nenhum]
     
     "Entendido! Vamos agendar uma visita técnica gratuita para 
      fazer o levantamento completo.
      
      Quais dias e horários funcionam melhor para você?"

Cliente: "Pode ser quinta às 14h"
Bot: [GOOGLE CALENDAR: verifica disponibilidade, agenda]
     [CRM: Move deal para "Agendado", cria tarefa para técnico]
     [NOTIFICAÇÕES: Email + Discord]
     
     "✅ Visita técnica confirmada!
      
      📅 Quinta-feira, 16/01/2025
      🕐 14:00 às 15:30
      👷 Técnico: Carlos Silva
      
      Você receberá um lembrete no dia anterior.
      Alguma observação sobre acesso ao local?"
```

### Exemplo: Cliente interessado em Subestação

```
Cliente: "Preciso fazer manutenção na subestação da fábrica"
Bot: [ENTENDE: serviço = subestacao, tipo = manutencao]
     [CRM: Cria contato + negociação]
     
     "Olá! Entendi que você precisa de serviço em subestação. 🔧
      
      Para entendermos melhor a necessidade, pode me informar:
      - É manutenção preventiva ou corretiva?
      - Qual a tensão da subestação (13.8kV, 34.5kV, etc.)?
      
      Mas primeiro, qual o seu nome?"
```

### Exemplo: Cliente interessado em Análise de Energia

```
Cliente: "Minha conta de luz está muito alta, quero entender o porquê"
Bot: [ENTENDE: serviço = analise_laudo, tipo = consumo]
     [CRM: Cria contato + negociação]
     
     "Entendo sua preocupação! 📊
      
      Podemos fazer uma análise completa do seu consumo para identificar 
      onde estão as perdas ou cobranças indevidas.
      
      Para começar, qual o seu nome?"
```

### Exemplo: Cliente interessado em BESS

```
Cliente: "Quero colocar bateria para não ficar sem energia quando cai a luz"
Bot: [ENTENDE: serviço = armazenamento_energia]
     [CRM: Cria contato + negociação]
     
     "Perfeito! Sistemas de armazenamento de energia são ideais para 
      garantir continuidade em quedas de energia. 🔋
      
      Você já possui sistema solar ou seria uma instalação independente?
      
      Mas antes, me diz seu nome?"
```

### Fluxo de Coleta de Dados (Estruturado mas Flexível)

O bot deve coletar estas informações, na ordem que fizer sentido na conversa:

**DADOS OBRIGATÓRIOS:**
1. Tipo de serviço (solar, subestação, projeto elétrico, BESS, análise/laudo, outro)
2. Nome e sobrenome
3. Telefone (confirmar se é o mesmo do WhatsApp)
4. Email
5. Endereço completo do local do serviço
6. Preferência de dias para visita
7. Preferência de turno (manhã/tarde)

**DADOS POR TIPO DE SERVIÇO:**

Energia Solar:
- Segmento (residencial, comercial, industrial, agronegócio)
- Foto da conta de energia (OBRIGATÓRIO)
- Fotos do local de instalação (telhado/solo)
- Interesse em sistema híbrido ou com bateria

Subestação:
- Tipo de serviço (reforma, manutenção preventiva, construção)
- Tensão da subestação
- Fotos da subestação atual (se existir)
- Urgência do serviço

Projetos Elétricos:
- Tipo de projeto (residencial, comercial, industrial)
- Descrição do que precisa
- Planta ou fotos do local (opcional)
- Carga estimada

Armazenamento de Energia (BESS):
- Já possui sistema solar?
- Objetivo (backup, gestão de demanda, autossuficiência)
- Potência necessária estimada
- Fotos do local e quadro elétrico

Análise e Laudos:
- Tipo de análise (consumo, qualidade, perícia)
- Descrição do problema ou objetivo
- Fotos relevantes
- Histórico de contas (se aplicável)

### Estados da Conversa

```
ESTADO: novo
→ Ainda não identificou intenção
→ CRM: Contato criado, Deal em "Novo Lead"

ESTADO: identificando_servico
→ Tentando entender o que o cliente quer
→ CRM: Deal em "Novo Lead"

ESTADO: coletando_dados
→ Sub-estados: nome, email, telefone, endereco, fotos, preferencia_horario
→ CRM: Deal em "Qualificando", atualizações em tempo real

ESTADO: aguardando_foto
→ Esperando cliente enviar imagem
→ CRM: Deal em "Qualificando"

ESTADO: agendando
→ Buscando horários e confirmando
→ CRM: Deal em "Qualificando"

ESTADO: agendado
→ Visita confirmada, aguardando
→ CRM: Deal em "Agendado", tarefa criada

ESTADO: handoff_comercial
→ Transferido para humano
→ CRM: Deal marcado como prioridade, notificação para owner

ESTADO: concluido
→ Atendimento finalizado
→ CRM: Deal em etapa final apropriada
```

### Comandos Especiais (Detectar em Qualquer Momento)

| Comando | Ação | CRM Action |
|---------|------|------------|
| "comercial", "falar com alguém", "atendente" | Handoff imediato | Criar tarefa urgente, notificar owner |
| "cancelar", "desistir" | Cancela agendamento se houver | Mover para "Perdido" com motivo |
| "reagendar", "mudar data" | Volta para seleção de horário | Atualizar tarefa, adicionar nota |
| "menu", "opções", "início" | Mostra menu principal | Adicionar nota de reinício |
| "meus dados", "o que você sabe" | Resume dados coletados | - |

## ENTREGÁVEIS TÉCNICOS

### 1. ESTRUTURA DE PASTAS

```
e2-solucoes-bot/
│
├── docker/
│   ├── docker-compose-dev.yml          # Stack desenvolvimento local (DEV)
│   ├── docker-compose.yml              # Stack produção (PROD)
│   ├── .env.example                    # Template variáveis PROD
│   ├── .env.dev.example                # Template variáveis DEV
│   └── configs/
│       ├── traefik/
│       │   ├── traefik.yml             # Config Traefik PROD
│       │   ├── traefik-dev.yml         # Config Traefik DEV (sem SSL)
│       │   └── dynamic/
│       │       ├── middlewares.yml
│       │       └── tls.yml
│       ├── n8n/
│       │   └── .n8n/                   # Persistência n8n
│       ├── supabase/
│       │   ├── kong.yml                # Config Kong API Gateway
│       │   └── volumes/                # Dados Supabase
│       └── postgres/
│           └── init/                   # Scripts inicialização DB
│
├── database/
│   ├── migrations/
│   │   ├── 001_create_conversations.sql
│   │   ├── 002_create_leads.sql
│   │   ├── 003_create_appointments.sql
│   │   ├── 004_create_messages.sql
│   │   ├── 005_create_vector_store.sql
│   │   └── 006_create_rdstation_sync.sql    # Tabela de sync CRM
│   ├── seeds/
│   │   ├── knowledge_base.sql          # Dados iniciais RAG
│   │   └── test_data.sql               # Dados para testes DEV
│   └── schema.sql                      # Schema completo consolidado
│
├── n8n/
│   ├── workflows/
│   │   ├── 01_main_whatsapp_handler.json
│   │   ├── 02_ai_agent_conversation.json
│   │   ├── 03_rag_knowledge_query.json
│   │   ├── 04_image_analysis.json
│   │   ├── 05_appointment_scheduler.json
│   │   ├── 06_notification_dispatcher.json
│   │   ├── 07_document_ingestion.json
│   │   ├── 08_rdstation_sync.json           # Sync com RD Station
│   │   ├── 09_rdstation_webhook_handler.json # Receber webhooks do CRM
│   │   └── 10_scheduled_reminders.json       # Lembretes agendados
│   ├── credentials/
│   │   └── README.md                   # Guia configuração credenciais
│   └── custom-nodes/
│       └── install-rdstation.sh        # Script para instalar nodes RD Station
│
├── knowledge/
│   ├── servicos/
│   │   ├── energia_solar.md
│   │   ├── subestacao.md
│   │   ├── projetos_eletricos.md
│   │   ├── armazenamento_energia.md
│   │   └── analise_laudos.md
│   ├── faq/
│   │   └── perguntas_frequentes.md
│   ├── tecnicos/
│   │   ├── especificacoes_solar.md
│   │   ├── especificacoes_subestacao.md
│   │   ├── especificacoes_bess.md
│   │   └── normas_tecnicas.md
│   └── portfolio/
│       └── projetos_realizados.md
│
├── docs/
│   │
│   ├── PLAN/
│   │   ├── README.md                   # Visão geral do planejamento
│   │   ├── architecture.md             # Decisões arquiteturais
│   │   ├── roadmap.md                  # Roadmap do projeto
│   │   ├── requirements.md             # Requisitos funcionais e técnicos
│   │   └── milestones.md               # Marcos e entregas
│   │
│   ├── Setups/
│   │   ├── README.md                   # Índice dos setups
│   │   ├── SETUP_DOCKER.md             # Configuração Docker/Containers
│   │   ├── SETUP_N8N.md                # Configuração n8n
│   │   ├── SETUP_SUPABASE.md           # Configuração Supabase
│   │   ├── SETUP_EVOLUTION_API.md      # Configuração Evolution/WhatsApp
│   │   ├── SETUP_CLAUDE.md             # Configuração Anthropic API
│   │   ├── SETUP_GOOGLE.md             # Configuração Google Services
│   │   ├── SETUP_DISCORD.md            # Configuração Discord Webhooks
│   │   ├── SETUP_EMAIL.md              # Configuração SMTP/Email
│   │   └── SETUP_RDSTATION.md          # Configuração RD Station CRM
│   │
│   ├── development/
│   │   ├── README.md                   # Guia do desenvolvedor
│   │   ├── local_setup.md              # Como rodar localmente
│   │   ├── workflow_guide.md           # Como funcionam os workflows
│   │   ├── database_guide.md           # Estrutura e queries úteis
│   │   ├── testing.md                  # Como testar o bot
│   │   ├── debugging.md                # Debug e logs
│   │   └── contributing.md             # Como contribuir
│   │
│   ├── deployment/
│   │   ├── README.md                   # Visão geral do deploy
│   │   ├── prerequisites.md            # Pré-requisitos servidor
│   │   ├── production_setup.md         # Setup ambiente produção
│   │   ├── ssl_certificates.md         # Configuração SSL/HTTPS
│   │   ├── domain_dns.md               # Configuração DNS
│   │   ├── security.md                 # Hardening e segurança
│   │   └── rollback.md                 # Procedimentos de rollback
│   │
│   ├── implementation/
│   │   ├── README.md                   # Status da implementação
│   │   ├── conversation_flow.md        # Fluxo detalhado de conversa
│   │   ├── ai_agent_config.md          # Configuração do AI Agent
│   │   ├── rag_setup.md                # Setup da base de conhecimento
│   │   ├── image_analysis.md           # Implementação Vision AI
│   │   ├── scheduling_logic.md         # Lógica de agendamento
│   │   ├── notifications.md            # Sistema de notificações
│   │   └── rdstation_integration.md    # Detalhes integração CRM
│   │
│   ├── guidelines/
│   │   ├── README.md                   # Índice das diretrizes
│   │   ├── code_style.md               # Padrões de código
│   │   ├── naming_conventions.md       # Convenções de nomenclatura
│   │   ├── git_workflow.md             # Workflow Git/branches
│   │   ├── secrets_management.md       # Gestão de segredos
│   │   ├── error_handling.md           # Tratamento de erros
│   │   └── bot_personality.md          # Tom e personalidade do bot
│   │
│   ├── monitoring/
│   │   ├── README.md                   # Visão geral monitoramento
│   │   ├── health_checks.md            # Health checks dos serviços
│   │   ├── logs.md                     # Estrutura e análise de logs
│   │   ├── metrics.md                  # Métricas a acompanhar
│   │   ├── alerts.md                   # Configuração de alertas
│   │   ├── backup_restore.md           # Backup e restauração
│   │   └── incident_response.md        # Resposta a incidentes
│   │
│   └── diagrams/
│       ├── architecture.mermaid        # Diagrama arquitetura
│       ├── conversation_flow.mermaid   # Fluxo de conversa
│       ├── data_flow.mermaid           # Fluxo de dados
│       ├── rdstation_sync.mermaid      # Fluxo de sync CRM
│       └── infrastructure.mermaid      # Infraestrutura
│
├── scripts/
│   ├── start.sh                        # Inicia ambiente (detecta dev/prod)
│   ├── start-dev.sh                    # Inicia ambiente DEV
│   ├── start-prod.sh                   # Inicia ambiente PROD
│   ├── stop.sh                         # Para containers
│   ├── restart.sh                      # Reinicia containers
│   ├── logs.sh                         # Visualiza logs
│   ├── backup.sh                       # Backup completo
│   ├── restore.sh                      # Restaurar backup
│   ├── migrate.sh                      # Roda migrations
│   ├── seed.sh                         # Carrega dados iniciais
│   ├── ingest-knowledge.sh             # Carrega base conhecimento RAG
│   ├── health-check.sh                 # Verifica saúde serviços
│   ├── install-n8n-nodes.sh            # Instala nodes customizados (RD Station)
│   └── cleanup.sh                      # Limpa volumes/dados antigos
│
├── templates/
│   ├── google_sheets/
│   │   └── leads_template.md           # Estrutura planilha leads
│   ├── email/
│   │   ├── novo_lead.html
│   │   ├── handoff_comercial.html
│   │   ├── confirmacao_agendamento.html
│   │   ├── lembrete_24h.html
│   │   └── lembrete_2h.html
│   └── rdstation/
│       ├── pipeline_config.md          # Configuração do pipeline
│       ├── custom_fields.md            # Campos customizados necessários
│       └── automation_rules.md         # Regras de automação sugeridas
│
├── .gitignore
├── .env.example
├── LICENSE
└── README.md                           # Documentação principal (quick start)
```

### 2. DOCKER COMPOSE - DESENVOLVIMENTO (docker-compose-dev.yml)

Criar stack para desenvolvimento local com:

**Serviços:**
- **n8n**: Porta 5678 exposta, sem autenticação básica, com nodes RD Station instalados
- **postgres**: Porta 5432 exposta para acesso direto
- **supabase-db**: PostgreSQL dedicado Supabase
- **supabase-studio**: Interface visual porta 3000
- **supabase-kong**: API Gateway
- **supabase-auth**: Autenticação
- **supabase-rest**: PostgREST
- **supabase-meta**: Metadata
- **redis**: Cache, porta 6379 exposta
- **traefik**: Sem SSL, dashboard habilitado porta 8080
- **mailhog**: SMTP fake para testes (porta 1025/8025)

**Configuração especial n8n para RD Station:**
```yaml
n8n:
  image: n8nio/n8n
  environment:
    - N8N_CUSTOM_EXTENSIONS=/home/node/.n8n/custom
  volumes:
    - n8n_data:/home/node/.n8n
    - ./n8n/custom-nodes:/home/node/.n8n/custom
  command: >
    sh -c "
      npm install -g n8n-nodes-rd-station-crm &&
      n8n start
    "
```

**Características DEV:**
- Todas as portas expostas para debug
- Volumes locais (não nomeados) para fácil reset
- Sem SSL (HTTP apenas)
- Hot reload onde possível
- Logs verbosos
- Mailhog para testar emails sem enviar

**Rede:**
- Rede bridge única: `e2-dev`

### 3. DOCKER COMPOSE - PRODUÇÃO (docker-compose.yml)

Criar stack para produção com:

**Serviços:** (mesmos do DEV, com diferenças)
- **n8n**: Autenticação básica obrigatória, nodes RD Station pré-instalados
- **postgres**: Porta NÃO exposta
- **supabase-***: Portas internas apenas
- **redis**: Porta NÃO exposta
- **traefik**: SSL automático Let's Encrypt

**Características PROD:**
- Apenas portas 80/443 expostas via Traefik
- Volumes nomeados para persistência
- SSL obrigatório
- Logs otimizados (warn/error)
- Healthchecks rigorosos
- Resource limits (memory/cpu)
- Restart: unless-stopped

**Redes:**
- `e2-public`: Traefik + serviços web
- `e2-internal`: Comunicação interna

### 4. SCHEMA DO BANCO DE DADOS

**Tabela: conversations**
```sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone_number VARCHAR(20) NOT NULL UNIQUE,
    whatsapp_name VARCHAR(255),
    current_state VARCHAR(50) DEFAULT 'novo',
    collected_data JSONB DEFAULT '{}',
    service_type VARCHAR(50),
    rdstation_contact_id VARCHAR(100),      -- ID do contato no RD Station
    rdstation_deal_id VARCHAR(100),         -- ID da negociação no RD Station
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_message_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'active',
    
    CONSTRAINT valid_state CHECK (current_state IN (
        'novo', 'identificando_servico', 'coletando_dados',
        'aguardando_foto', 'agendando', 'agendado',
        'handoff_comercial', 'concluido'
    )),
    CONSTRAINT valid_service CHECK (service_type IN (
        'energia_solar', 'subestacao', 'projeto_eletrico',
        'armazenamento_energia', 'analise_laudo', 'outro'
    ) OR service_type IS NULL)
);

CREATE INDEX idx_conversations_phone ON conversations(phone_number);
CREATE INDEX idx_conversations_status ON conversations(status);
CREATE INDEX idx_conversations_service ON conversations(service_type);
CREATE INDEX idx_conversations_rdstation_contact ON conversations(rdstation_contact_id);
CREATE INDEX idx_conversations_rdstation_deal ON conversations(rdstation_deal_id);
```

**Tabela: messages**
```sql
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    direction VARCHAR(10) NOT NULL,
    content TEXT,
    message_type VARCHAR(20) DEFAULT 'text',
    media_url TEXT,
    media_analysis JSONB,
    whatsapp_message_id VARCHAR(100) UNIQUE,
    synced_to_rdstation BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_direction CHECK (direction IN ('inbound', 'outbound')),
    CONSTRAINT valid_type CHECK (message_type IN (
        'text', 'image', 'document', 'audio', 'location', 'sticker'
    ))
);

CREATE INDEX idx_messages_conversation ON messages(conversation_id);
CREATE INDEX idx_messages_created ON messages(created_at DESC);
```

**Tabela: leads**
```sql
CREATE TABLE leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id),
    phone_number VARCHAR(20) NOT NULL,
    name VARCHAR(255),
    email VARCHAR(255),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(50),
    zip_code VARCHAR(20),
    
    -- Serviço
    service_type VARCHAR(50),
    service_subtype VARCHAR(50),             -- Ex: solar_residencial, subestacao_reforma
    service_details JSONB DEFAULT '{}',
    
    -- Específico por serviço
    segmento VARCHAR(50),                    -- residencial, comercial, industrial, agronegocio
    tensao_subestacao VARCHAR(20),           -- 13.8kV, 34.5kV, etc.
    possui_solar BOOLEAN,                    -- Para BESS
    tipo_analise VARCHAR(50),                -- consumo, qualidade, pericia
    
    preferred_days VARCHAR(100),
    preferred_shift VARCHAR(20),
    observations TEXT,
    media_files JSONB DEFAULT '[]',
    ai_analysis JSONB DEFAULT '{}',
    estimated_value DECIMAL(12,2),           -- Valor estimado do negócio
    estimated_kwp DECIMAL(6,2),              -- Para solar: potência estimada
    estimated_kwh DECIMAL(10,2),             -- Consumo médio
    
    status VARCHAR(20) DEFAULT 'novo',
    priority VARCHAR(20) DEFAULT 'normal',
    assigned_to VARCHAR(100),
    
    -- RD Station CRM IDs
    rdstation_contact_id VARCHAR(100),
    rdstation_deal_id VARCHAR(100),
    rdstation_company_id VARCHAR(100),
    rdstation_last_sync TIMESTAMP WITH TIME ZONE,
    
    -- Google Sheets (backup/visualização)
    google_sheets_row INTEGER,
    synced_to_sheets BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_status CHECK (status IN (
        'novo', 'em_atendimento', 'agendado', 'concluido', 'perdido', 'handoff'
    )),
    CONSTRAINT valid_priority CHECK (priority IN ('baixa', 'normal', 'alta', 'urgente'))
);

CREATE INDEX idx_leads_status ON leads(status);
CREATE INDEX idx_leads_service ON leads(service_type);
CREATE INDEX idx_leads_created ON leads(created_at DESC);
CREATE INDEX idx_leads_rdstation_deal ON leads(rdstation_deal_id);
```

**Tabela: appointments**
```sql
CREATE TABLE appointments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
    conversation_id UUID REFERENCES conversations(id),
    scheduled_date DATE NOT NULL,
    scheduled_time_start TIME NOT NULL,
    scheduled_time_end TIME NOT NULL,
    technician_name VARCHAR(100),
    technician_phone VARCHAR(20),
    service_type VARCHAR(50),                -- Tipo de serviço para alocar técnico certo
    google_calendar_event_id VARCHAR(100),
    rdstation_task_id VARCHAR(100),          -- ID da tarefa no RD Station
    status VARCHAR(20) DEFAULT 'agendado',
    reminder_24h_sent BOOLEAN DEFAULT FALSE,
    reminder_2h_sent BOOLEAN DEFAULT FALSE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_status CHECK (status IN (
        'agendado', 'confirmado', 'em_andamento', 'realizado', 'cancelado', 'reagendado', 'no_show'
    ))
);

CREATE INDEX idx_appointments_date ON appointments(scheduled_date);
CREATE INDEX idx_appointments_status ON appointments(status);
CREATE INDEX idx_appointments_service ON appointments(service_type);
CREATE INDEX idx_appointments_rdstation_task ON appointments(rdstation_task_id);
```

**Tabela: rdstation_sync_log (Auditoria de sincronização)**
```sql
CREATE TABLE rdstation_sync_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(50) NOT NULL,        -- contact, deal, task, note
    entity_id UUID NOT NULL,                  -- ID local
    rdstation_id VARCHAR(100),                -- ID no RD Station
    operation VARCHAR(20) NOT NULL,           -- create, update, delete
    request_payload JSONB,
    response_payload JSONB,
    status VARCHAR(20) DEFAULT 'pending',     -- pending, success, error
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_rdstation_sync_status ON rdstation_sync_log(status);
CREATE INDEX idx_rdstation_sync_entity ON rdstation_sync_log(entity_type, entity_id);
```

**Tabela: knowledge_documents (Vector Store - Supabase)**
```sql
-- Habilitar extensão pgvector
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE knowledge_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    embedding VECTOR(1536),
    category VARCHAR(50),                     -- solar, subestacao, projeto, bess, analise, faq
    subcategory VARCHAR(50),
    source_file VARCHAR(255),
    chunk_index INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índice para busca vetorial
CREATE INDEX idx_knowledge_embedding ON knowledge_documents 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

CREATE INDEX idx_knowledge_category ON knowledge_documents(category);

-- Função para busca por similaridade
CREATE OR REPLACE FUNCTION match_documents(
    query_embedding VECTOR(1536),
    match_threshold FLOAT DEFAULT 0.7,
    match_count INT DEFAULT 5,
    filter_category VARCHAR DEFAULT NULL
)
RETURNS TABLE (
    id UUID,
    content TEXT,
    metadata JSONB,
    category VARCHAR(50),
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        kd.id,
        kd.content,
        kd.metadata,
        kd.category,
        1 - (kd.embedding <=> query_embedding) AS similarity
    FROM knowledge_documents kd
    WHERE 1 - (kd.embedding <=> query_embedding) > match_threshold
      AND (filter_category IS NULL OR kd.category = filter_category)
    ORDER BY kd.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
```

**Tabela: chat_memory (n8n Postgres Chat Memory)**
```sql
CREATE TABLE chat_memory (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    message JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_chat_memory_session ON chat_memory(session_id);
CREATE INDEX idx_chat_memory_created ON chat_memory(created_at DESC);

-- Limpar mensagens antigas (manter últimos 30 dias)
CREATE OR REPLACE FUNCTION cleanup_old_chat_memory()
RETURNS void AS $$
BEGIN
    DELETE FROM chat_memory 
    WHERE created_at < NOW() - INTERVAL '30 days';
END;
$$ LANGUAGE plpgsql;
```

### 5. WORKFLOWS N8N

#### Workflow 1: Main WhatsApp Handler (01_main_whatsapp_handler.json)

```
[Webhook: POST /webhook/whatsapp-evolution]
    │
    ├─→ [IF: É verificação webhook?]
    │       └─→ [Respond: Challenge] → FIM
    │
    └─→ [IF: É mensagem real? (não status)]
            │
            ├─→ [Code: Extrair dados mensagem]
            │       - phone_number
            │       - whatsapp_name  
            │       - message_content
            │       - message_type (text/image/audio/document/location)
            │       - media_url (se aplicável)
            │       - whatsapp_message_id
            │
            ├─→ [Postgres: Verificar duplicata (message_id)]
            │       └─→ [IF: Duplicata?] → FIM
            │
            ├─→ [Postgres: Salvar mensagem inbound]
            │
            └─→ [Switch: Tipo de mensagem]
                    │
                    ├─→ text/location
                    │       └─→ [Execute Workflow: 02_ai_agent]
                    │
                    ├─→ image
                    │       ├─→ [Execute Workflow: 04_image_analysis]
                    │       └─→ [Execute Workflow: 02_ai_agent]
                    │
                    ├─→ document
                    │       ├─→ [Google Drive: Upload]
                    │       └─→ [Execute Workflow: 02_ai_agent]
                    │
                    └─→ audio
                            ├─→ [OpenAI Whisper: Transcrever]
                            └─→ [Execute Workflow: 02_ai_agent]
```

#### Workflow 2: AI Agent Conversation (02_ai_agent_conversation.json)

```
[Trigger: Dados da mensagem processada]
    │
    ├─→ [Postgres: Buscar/Criar conversa por phone_number]
    │       - Se não existe: criar com state='novo'
    │       - Se existe: carregar estado atual
    │
    ├─→ [Code: Preparar contexto]
    │       - Carregar collected_data
    │       - Montar histórico recente
    │       - Identificar dados faltantes
    │
    ├─→ [Postgres Chat Memory: Carregar histórico]
    │       - session_id = phone_number
    │       - context_window = 20 mensagens
    │
    └─→ [AI Agent Node]
            │
            ├── Model: Claude 3.5 Sonnet (claude-3-5-sonnet-20241022)
            ├── Temperature: 0.7
            ├── Max Tokens: 1024
            │
            ├── System Prompt: [VER SEÇÃO SYSTEM PROMPT]
            │
            ├── Tools:
            │   ├── conhecimento_e2 (Supabase Vector Store)
            │   │       - Mode: retrieve-as-tool
            │   │       - Description: "Base de conhecimento da E2 Soluções..."
            │   │       - Match threshold: 0.7
            │   │       - Match count: 5
            │   │
            │   ├── buscar_horarios_disponiveis (HTTP Request → Workflow 05)
            │   │       - Input: preferred_days, preferred_shift, service_type
            │   │       - Output: array de slots disponíveis
            │   │
            │   ├── confirmar_agendamento (HTTP Request → Workflow 05)
            │   │       - Input: slot_id, lead_data
            │   │       - Output: confirmação com detalhes
            │   │
            │   ├── salvar_dados_coletados (Code Node)
            │   │       - Input: campo, valor
            │   │       - Atualiza collected_data no Postgres
            │   │       - Trigger sync RD Station
            │   │
            │   ├── solicitar_handoff (HTTP Request → Workflow 06)
            │   │       - Notifica comercial
            │   │       - Atualiza estado para 'handoff_comercial'
            │   │       - Atualiza RD Station (prioridade alta)
            │   │
            │   └── finalizar_atendimento (Code Node)
            │           - Marca estado como 'concluido'
            │           - Trigger sincronização Sheets
            │           - Atualiza RD Station (etapa final)
            │
            └── Memory: Postgres Chat Memory
                    - session_id: phone_number
                    - auto_save: true
    │
    ├─→ [Code: Processar resposta do Agent]
    │       - Extrair texto da resposta
    │       - Extrair tool_calls executadas
    │       - Determinar novo estado
    │
    ├─→ [Postgres: Atualizar conversa]
    │       - current_state
    │       - collected_data  
    │       - last_message_at
    │
    ├─→ [Postgres: Salvar mensagem outbound]
    │
    ├─→ [Evolution API: Enviar resposta WhatsApp]
    │
    ├─→ [Execute Workflow: 08_rdstation_sync]
    │       - Dados atualizados
    │       - Tipo de atualização
    │
    └─→ [IF: Ações especiais necessárias?]
            ├─→ handoff → [Execute: 06_notification_dispatcher]
            ├─→ lead_completo → [Execute: 06_notification_dispatcher]
            └─→ agendamento → [Execute: 05_appointment_scheduler]
```

#### Workflow 4: Image Analysis (04_image_analysis.json)

```
[Trigger: Imagem recebida]
    │
    ├─→ [Code: Identificar contexto]
    │       - Qual serviço o cliente está solicitando?
    │       - O que esperamos nesta imagem?
    │
    ├─→ [HTTP Request: Baixar imagem]
    │       - URL da Evolution API
    │       - Converter para Base64
    │
    ├─→ [HTTP Request: Claude Vision API]
    │       POST https://api.anthropic.com/v1/messages
    │       Headers:
    │         - x-api-key: {{ANTHROPIC_API_KEY}}
    │         - anthropic-version: 2023-06-01
    │       Body:
    │       {
    │         "model": "claude-3-5-sonnet-20241022",
    │         "max_tokens": 1024,
    │         "messages": [{
    │           "role": "user",
    │           "content": [
    │             {
    │               "type": "image",
    │               "source": {
    │                 "type": "base64",
    │                 "media_type": "{{$json.media_type}}",
    │                 "data": "{{$json.base64_data}}"
    │               }
    │             },
    │             {
    │               "type": "text", 
    │               "text": "{{$json.analysis_prompt}}"
    │             }
    │           ]
    │         }]
    │       }
    │
    ├─→ [Code: Processar análise]
    │       - Extrair informações relevantes
    │       - Estruturar dados para o lead
    │
    ├─→ [Google Drive: Upload imagem]
    │       - Pasta: E2Solucoes/Leads/{{phone_number}}/
    │       - Nome: {{timestamp}}_{{tipo}}.jpg
    │
    ├─→ [Postgres: Salvar análise]
    │       - Atualizar messages.media_analysis
    │       - Atualizar leads.media_files
    │       - Atualizar leads.ai_analysis
    │
    └─→ [Return: Resultado para AI Agent]
            {
              "analysis_summary": "...",
              "extracted_data": {...},
              "drive_link": "...",
              "recommendations": "..."
            }
```

**Prompts de Análise por Tipo:**

```javascript
// Conta de Energia
const promptContaEnergia = `
Analise esta conta de energia elétrica brasileira.
Extraia e retorne em formato estruturado:

1. CONSUMO:
   - Consumo do mês atual (kWh)
   - Média dos últimos 12 meses (kWh)
   - Demanda contratada (kW) se aplicável
   - Histórico se visível

2. VALORES:
   - Valor total da fatura
   - Tarifa por kWh
   - Bandeira tarifária
   - Impostos identificáveis

3. DADOS DA UNIDADE:
   - Distribuidora
   - Número da instalação
   - Tipo (monofásico/bifásico/trifásico)
   - Classe (residencial/comercial/industrial)
   - Grupo tarifário (A/B)

4. ESTIMATIVA SOLAR:
   - Com base no consumo, estime o tamanho do sistema solar necessário (kWp)
   - Número aproximado de painéis (considerando 550W cada)
   - Economia mensal estimada

5. OBSERVAÇÕES:
   - Identifique possíveis anomalias ou cobranças indevidas
   - Sugira melhorias se identificar oportunidades

Seja objetivo e técnico. Se algum dado não estiver visível, indique "não identificado".
`;

// Telhado/Local para Solar
const promptLocalSolar = `
Analise esta foto de local para instalação de energia solar.
Avalie e descreva:

1. TIPO DE INSTALAÇÃO:
   - Telhado ou solo?
   - Se telhado: tipo de telha (cerâmica, fibrocimento, metálico, laje)
   - Se solo: características do terreno

2. CONDIÇÃO:
   - Estado aparente (bom, regular, necessita reparo)
   - Idade estimada da estrutura

3. ORIENTAÇÃO E INCLINAÇÃO:
   - Orientação aparente (norte, sul, leste, oeste)
   - Inclinação estimada (graus)
   - Adequação para solar (ideal: norte, 15-25°)

4. ÁREA ÚTIL:
   - Estimativa de área disponível para painéis (m²)
   - Capacidade estimada de instalação (kWp)
   - Obstáculos visíveis (caixa d'água, antenas, chaminés, árvores)

5. SOMBREAMENTO:
   - Fontes de sombra identificáveis
   - Períodos prováveis de sombreamento

6. OBSERVAÇÕES:
   - Acesso para instalação e manutenção
   - Recomendações ou alertas
   - Se precisa de mais fotos ou ângulos

Seja técnico mas acessível.
`;

// Subestação
const promptSubestacao = `
Analise esta foto de subestação elétrica.
Avalie:

1. TIPO E CLASSE:
   - Classe de tensão aparente (13.8kV, 34.5kV, 69kV, etc.)
   - Tipo de construção (abrigada, ao tempo, blindada)
   - Configuração aparente

2. EQUIPAMENTOS VISÍVEIS:
   - Transformador(es)
   - Disjuntores
   - Chaves seccionadoras
   - Para-raios
   - TCs e TPs
   - Painéis de comando

3. CONDIÇÃO GERAL:
   - Estado de conservação
   - Sinais de oxidação ou deterioração
   - Vazamentos de óleo
   - Vegetação invasora
   - Problemas de segurança visíveis

4. CONFORMIDADE:
   - Sinalização de segurança
   - Cercamento e proteção
   - Iluminação
   - Acessibilidade

5. RECOMENDAÇÕES:
   - Manutenções aparentemente necessárias
   - Adequações sugeridas
   - Alertas de segurança

Seja técnico e detalhado. Esta análise auxiliará no planejamento de serviço.
`;

// Quadro Elétrico (para BESS/Projeto)
const promptQuadroEletrico = `
Analise esta foto de quadro/painel elétrico.
Avalie:

1. TIPO E CAPACIDADE:
   - Tipo de quadro (distribuição, comando, medição)
   - Padrão (monofásico/bifásico/trifásico)
   - Disjuntor geral (amperagem)
   - Número de circuitos

2. CONDIÇÃO:
   - Estado geral (bom, regular, necessita adequação)
   - Organização dos circuitos
   - Identificação dos circuitos
   - Aquecimento aparente (descoloração)

3. PROTEÇÕES:
   - Presença de DPS (Dispositivo de Proteção contra Surtos)
   - Presença de DR (Diferencial Residual)
   - Aterramento visível
   - Barramentos

4. PARA INTEGRAÇÃO SOLAR/BESS:
   - Espaço disponível para novos disjuntores
   - Viabilidade de instalação de inversor
   - Necessidade de adequações

5. ALERTAS:
   - Problemas de segurança identificados
   - Não conformidades aparentes
   - Recomendações urgentes

Seja técnico e destaque questões de segurança.
`;
```

#### Workflow 8: RD Station Sync (08_rdstation_sync.json)

```
[Trigger: Dados para sincronizar]
    │
    ├─→ [Code: Preparar payload]
    │       - Mapear campos bot → RD Station
    │       - Identificar operação (create/update)
    │
    ├─→ [IF: Contato existe no RD Station?]
    │       │
    │       ├─→ NÃO: [RD Station CRM: Criar Contato]
    │       │       POST /contacts
    │       │       {
    │       │         "name": "{{lead.name}}",
    │       │         "phones": [{"phone": "{{lead.phone}}"}],
    │       │         "emails": [{"email": "{{lead.email}}"}],
    │       │         "custom_fields": {
    │       │           "cf_endereco": "{{lead.address}}",
    │       │           "cf_servico_interesse": "{{lead.service_type}}",
    │       │           "cf_segmento": "{{lead.segmento}}",
    │       │           "cf_origem": "Bot WhatsApp"
    │       │         }
    │       │       }
    │       │       └─→ [Postgres: Salvar rdstation_contact_id]
    │       │
    │       └─→ SIM: [RD Station CRM: Atualizar Contato]
    │               PUT /contacts/{{rdstation_contact_id}}
    │
    ├─→ [IF: Negociação existe?]
    │       │
    │       ├─→ NÃO: [RD Station CRM: Criar Negociação]
    │       │       POST /deals
    │       │       {
    │       │         "name": "{{lead.service_type}} - {{lead.name}}",
    │       │         "contact_id": "{{rdstation_contact_id}}",
    │       │         "deal_stage_id": "{{stage_novo_lead}}",
    │       │         "deal_source_id": "{{source_bot_whatsapp}}",
    │       │         "amount": {{lead.estimated_value}},
    │       │         "custom_fields": {
    │       │           "cf_servico": "{{lead.service_type}}",
    │       │           "cf_segmento": "{{lead.segmento}}",
    │       │           "cf_consumo_kwh": "{{lead.estimated_kwh}}",
    │       │           "cf_potencia_kwp": "{{lead.estimated_kwp}}",
    │       │           "cf_analise_ia": "{{lead.ai_analysis}}",
    │       │           "cf_fotos": "{{lead.media_files}}"
    │       │         }
    │       │       }
    │       │       └─→ [Postgres: Salvar rdstation_deal_id]
    │       │
    │       └─→ SIM: [RD Station CRM: Atualizar Negociação]
    │               PUT /deals/{{rdstation_deal_id}}
    │
    ├─→ [IF: Mudança de etapa?]
    │       └─→ [RD Station CRM: Mover Negociação]
    │
    ├─→ [IF: Tem nota para adicionar?]
    │       └─→ [RD Station CRM: Criar Nota]
    │
    ├─→ [Postgres: Log de sincronização]
    │
    └─→ [IF: Erro na sincronização?]
            └─→ [Discord: Notificar erro sync]
```

### 6. SYSTEM PROMPT DO AI AGENT

```
Você é o assistente virtual da E2 Soluções, uma empresa brasileira especializada em soluções de energia e elétrica.

## SERVIÇOS DA E2 SOLUÇÕES

1. **Energia Solar Fotovoltaica**
   - Projetos residenciais, comerciais, industriais e agronegócios
   - Instalação de painéis solares
   - Sistemas on-grid, off-grid e híbridos
   - Dimensionamento personalizado
   - Homologação junto à concessionária

2. **Subestação Elétrica**
   - Reformas de subestações
   - Manutenções preventivas e corretivas
   - Construção de novas subestações
   - Adequação às normas técnicas
   - Comissionamento e testes

3. **Projetos Elétricos**
   - Projetos residenciais
   - Projetos comerciais e industriais
   - Adequações e regularizações
   - Dimensionamento de cargas
   - Laudos técnicos

4. **Sistemas de Armazenamento de Energia (BESS)**
   - Instalação de sistemas de armazenamento
   - Estudo de viabilidade técnica e econômica
   - Integração com sistemas solares
   - Soluções para backup e nobreak
   - Gestão de demanda

5. **Análise de Energia e Laudos**
   - Análise de consumo energético
   - Análise de qualidade de energia
   - Laudo para perícia judicial
   - Diagnóstico de perdas
   - Identificação de problemas elétricos

## SUA PERSONALIDADE

- Simpático, profissional e prestativo
- Usa emojis com moderação (1 por mensagem no máximo)
- Respostas concisas, mas completas
- Tom consultivo, nunca agressivamente vendedor
- Paciente com clientes que não entendem termos técnicos
- Explica conceitos de forma simples quando necessário

## SEU OBJETIVO PRINCIPAL

Coletar informações do cliente para agendar uma visita técnica gratuita, seguindo este fluxo:

1. Identificar o serviço desejado (entender naturalmente, sem forçar menu)
2. Coletar nome e sobrenome
3. Coletar email
4. Confirmar telefone (é o mesmo do WhatsApp?)
5. Coletar endereço completo do local
6. Solicitar fotos relevantes (conta de luz para solar, fotos do local)
7. Definir preferência de dias e turno para visita
8. Apresentar horários disponíveis e confirmar agendamento

## REGRAS DE CONVERSAÇÃO

### Entendimento Natural
- SEMPRE tente entender a intenção do cliente naturalmente
- Palavras-chave para energia solar: "solar", "placa", "painel", "conta de luz alta", "economia de energia"
- Palavras-chave para subestação: "subestação", "média tensão", "transformador"
- Palavras-chave para sistema de armazenamento de energia: "bateria", "armazenamento", "BESS", "falta de energia", "queda de energia"
- Palavras-chave para análise e laudo: "consumo", "demanda", "queima de equipamentos", "qualidade de energia", "teste de energia", "perícia", "cobrança de energia"
- Palavras-chave para projetos: "projeto elétrico"

### Menu como Fallback
Se não entender após 2 tentativas, ofereça:
"Posso te ajudar com:
1️⃣ Energia Solar
2️⃣ Subestação
3️⃣ Projeto Elétrico
4️⃣ Armazenamento de Energia
5️⃣ Análise e Laudo
6️⃣ Falar com o Comercial"

### Coleta de Dados
- Colete UM dado por vez, não bombardeie
- Confirme dados importantes antes de prosseguir
- Se o cliente divagar, gentilmente retome o fluxo
- Seja flexível na ordem se fizer sentido no contexto

### Base de Conhecimento
- SEMPRE consulte a ferramenta 'conhecimento_e2' antes de responder perguntas sobre serviços
- Nunca invente informações técnicas ou preços
- Se não souber, diga que vai verificar ou que o técnico esclarecerá na visita

### Análise de Imagens
- Quando o cliente enviar uma imagem, você receberá a análise automática
- Comente os pontos relevantes da análise
- Use as informações para personalizar o atendimento

## COMANDOS ESPECIAIS

Detecte estas intenções em QUALQUER momento da conversa:

| Intenção | Palavras-chave | Ação |
|----------|---------------|------|
| Falar com humano | "comercial", "atendente", "pessoa real", "falar com alguém" | Use a ferramenta 'solicitar_handoff' |
| Cancelar | "cancelar", "desistir", "não quero mais" | Confirme e cancele se houver agendamento |
| Reagendar | "reagendar", "mudar data", "outro horário" | Volte para seleção de horários |
| Ver menu | "menu", "opções", "início", "começar de novo" | Mostre menu principal |
| Ver dados | "meus dados", "o que você sabe", "minhas informações" | Resuma dados coletados |

## PERGUNTAS ESPECÍFICAS POR SERVIÇO

### Energia Solar
- Qual o segmento? (residencial, comercial, industrial, agro)
- Pedir foto da conta de energia
- Perguntar se tem interesse em bateria/armazenamento

### Subestação
- Qual o tipo de serviço? (reforma, manutenção, construção)
- Qual a tensão? (13.8kV, 34.5kV, etc.)
- É urgente?

### BESS/Armazenamento
- Já possui sistema solar?
- Qual o objetivo? (backup, gestão de demanda, autossuficiência)

### Análise e Laudo
- Qual o tipo? (consumo, qualidade, perícia judicial)
- Qual o problema ou objetivo?

### Projeto Elétrico
- Qual o tipo? (residencial, comercial, industrial)
- É projeto novo ou adequação?

## FORMATO DE RESPOSTA

- Responda APENAS com a mensagem para o cliente
- Use as ferramentas disponíveis quando necessário
- Não explique suas ações internas
- Mantenha respostas entre 1-4 parágrafos curtos
- Use formatação WhatsApp: *negrito*, _itálico_, ~tachado~

## O QUE NUNCA FAZER

❌ Inventar preços, prazos ou especificações
❌ Prometer coisas que não pode cumprir
❌ Responder sobre assuntos não relacionados à E2 Soluções
❌ Usar linguagem muito formal ou robótica
❌ Ignorar pedidos de falar com humano
❌ Ser insistente se o cliente quiser desistir
❌ Compartilhar dados de outros clientes
❌ Fazer mais de 2 perguntas por mensagem

## CONTEXTO ATUAL

Dados já coletados deste cliente:
{{collected_data}}

Estado atual da conversa:
{{current_state}}

Última análise de imagem (se houver):
{{last_image_analysis}}
```

### 7. CONFIGURAÇÃO RD STATION CRM

#### Campos Customizados Necessários

Criar os seguintes campos customizados no RD Station CRM:

**Em Contatos:**
| Campo | Tipo | Descrição |
|-------|------|-----------|
| cf_endereco | Texto Longo | Endereço completo |
| cf_cidade | Texto | Cidade |
| cf_estado | Texto | Estado |
| cf_cep | Texto | CEP |
| cf_segmento | Lista | Residencial, Comercial, Industrial, Agronegócio |
| cf_origem | Texto | Origem do lead (Bot WhatsApp) |

**Em Negociações:**
| Campo | Tipo | Descrição |
|-------|------|-----------|
| cf_servico | Lista | Solar, Subestação, Projeto, BESS, Análise |
| cf_servico_subtipo | Texto | Subtipo específico |
| cf_segmento | Lista | Residencial, Comercial, Industrial, Agronegócio |
| cf_consumo_kwh | Número | Consumo médio kWh |
| cf_potencia_kwp | Número | Potência estimada kWp (solar) |
| cf_tensao | Texto | Tensão da subestação |
| cf_tipo_analise | Lista | Consumo, Qualidade, Perícia |
| cf_possui_solar | Checkbox | Já possui sistema solar (para BESS) |
| cf_analise_ia | Texto Longo | Análise da IA sobre documentos/fotos |
| cf_fotos_drive | URL | Link pasta Google Drive com fotos |
| cf_preferencia_dias | Texto | Dias preferidos para visita |
| cf_preferencia_turno | Lista | Manhã, Tarde |
| cf_observacoes_acesso | Texto | Portaria, interfone, etc. |

#### Configuração do Pipeline

```
Nome: Bot WhatsApp E2 Soluções

Etapas:
1. Novo Lead (ordem: 1)
   - Cor: Cinza
   - Descrição: Lead recém-captado pelo bot

2. Qualificando (ordem: 2)
   - Cor: Amarelo
   - Descrição: Bot está coletando informações

3. Agendado (ordem: 3)
   - Cor: Azul
   - Descrição: Visita técnica agendada

4. Proposta (ordem: 4)
   - Cor: Laranja
   - Descrição: Aguardando aprovação de proposta

5. Negociação (ordem: 5)
   - Cor: Roxo
   - Descrição: Em negociação com cliente

6. Ganho (ordem: 6)
   - Cor: Verde
   - Descrição: Venda fechada

7. Perdido (ordem: 7)
   - Cor: Vermelho
   - Descrição: Não fechou negócio
```

### 8. VARIÁVEIS DE AMBIENTE

**.env.example (PRODUÇÃO)**

```bash
# ===========================================
# E2 SOLUÇÕES BOT - CONFIGURAÇÃO DE PRODUÇÃO
# ===========================================

# --- DOMÍNIOS ---
DOMAIN=bot.e2solucoes.com.br
N8N_SUBDOMAIN=n8n
SUPABASE_SUBDOMAIN=supabase

# --- n8n ---
N8N_HOST=${N8N_SUBDOMAIN}.${DOMAIN}
N8N_PORT=5678
N8N_PROTOCOL=https
N8N_BASIC_AUTH_ACTIVE=true
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=GERAR_SENHA_FORTE_AQUI
N8N_ENCRYPTION_KEY=GERAR_CHAVE_32_CHARS
WEBHOOK_URL=https://${N8N_SUBDOMAIN}.${DOMAIN}/
EXECUTIONS_DATA_PRUNE=true
EXECUTIONS_DATA_MAX_AGE=168
GENERIC_TIMEZONE=America/Sao_Paulo

# --- PostgreSQL (n8n + chat memory) ---
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=e2solucoes
POSTGRES_PASSWORD=GERAR_SENHA_FORTE_AQUI
POSTGRES_DB=e2_bot
POSTGRES_NON_ROOT_USER=n8n_user
POSTGRES_NON_ROOT_PASSWORD=GERAR_SENHA_FORTE_AQUI

# --- Supabase ---
SUPABASE_HOST=${SUPABASE_SUBDOMAIN}.${DOMAIN}
SUPABASE_DB_HOST=supabase-db
SUPABASE_DB_PORT=5432
SUPABASE_DB_USER=supabase_admin
SUPABASE_DB_PASSWORD=GERAR_SENHA_FORTE_AQUI
SUPABASE_DB_NAME=supabase

SUPABASE_ANON_KEY=GERAR_JWT_ANON
SUPABASE_SERVICE_ROLE_KEY=GERAR_JWT_SERVICE
SUPABASE_JWT_SECRET=GERAR_JWT_SECRET_32_CHARS

SUPABASE_URL=https://${SUPABASE_SUBDOMAIN}.${DOMAIN}
SUPABASE_PUBLIC_URL=https://${SUPABASE_SUBDOMAIN}.${DOMAIN}

# --- Redis ---
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=GERAR_SENHA_FORTE_AQUI

# --- APIs Externas ---
ANTHROPIC_API_KEY=sk-ant-xxx
OPENAI_API_KEY=sk-xxx

# --- Evolution API (WhatsApp) ---
EVOLUTION_API_URL=https://evolution.seudominio.com.br
EVOLUTION_API_KEY=xxx
EVOLUTION_INSTANCE_NAME=e2solucoes

# --- Google Services ---
GOOGLE_SERVICE_ACCOUNT_EMAIL=bot@projeto.iam.gserviceaccount.com
GOOGLE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nxxx\n-----END PRIVATE KEY-----"
GOOGLE_CALENDAR_ID=tecnico@e2solucoes.com.br
GOOGLE_DRIVE_FOLDER_ID=xxx
GOOGLE_SHEETS_ID=xxx

# --- RD Station CRM ---
RDSTATION_CLIENT_ID=seu_client_id
RDSTATION_CLIENT_SECRET=seu_client_secret
RDSTATION_REFRESH_TOKEN=seu_refresh_token
RDSTATION_API_URL=https://crm.rdstation.com/api/v1
RDSTATION_PIPELINE_ID=id_do_pipeline_bot
RDSTATION_STAGE_NOVO_LEAD=id_etapa_novo
RDSTATION_STAGE_QUALIFICANDO=id_etapa_qualificando
RDSTATION_STAGE_AGENDADO=id_etapa_agendado
RDSTATION_STAGE_PROPOSTA=id_etapa_proposta
RDSTATION_STAGE_GANHO=id_etapa_ganho
RDSTATION_STAGE_PERDIDO=id_etapa_perdido
RDSTATION_SOURCE_BOT=id_fonte_bot_whatsapp
RDSTATION_USER_TECNICO=id_usuario_tecnico
RDSTATION_WEBHOOK_SECRET=secret_para_validar_webhooks

# --- Discord ---
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/xxx/xxx
DISCORD_WEBHOOK_ALERTS=https://discord.com/api/webhooks/xxx/xxx

# --- Email (SMTP) ---
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_SECURE=false
SMTP_USER=bot@e2solucoes.com.br
SMTP_PASSWORD=APP_PASSWORD_AQUI
EMAIL_FROM="E2 Soluções Bot <bot@e2solucoes.com.br>"
EMAIL_COMERCIAL=comercial@e2solucoes.com.br
EMAIL_TECNICO=tecnico@e2solucoes.com.br

# --- Traefik ---
TRAEFIK_ACME_EMAIL=ti@e2solucoes.com.br
TRAEFIK_LOG_LEVEL=WARN

# --- Configurações do Bot ---
BOT_NAME=E2 Soluções Assistente
BOT_DEFAULT_TECHNICIAN=Carlos Silva
BOT_APPOINTMENT_DURATION_MINUTES=90
BOT_APPOINTMENT_BUFFER_MINUTES=30
BOT_WORKING_HOURS_START=08:00
BOT_WORKING_HOURS_END=18:00
BOT_LUNCH_START=12:00
BOT_LUNCH_END=13:00
```

### 9. MENSAGENS DO BOT (REFERÊNCIA)

```
SAUDACAO_INICIAL:
"Olá! 👋 Sou o assistente virtual da E2 Soluções.

Como posso te ajudar hoje?

☀️ Energia Solar
⚡ Subestação Elétrica
📐 Projetos Elétricos
🔋 Armazenamento de Energia
📊 Análise e Laudos

Pode me contar o que você precisa, ou escolher uma opção acima!"

IDENTIFICOU_SOLAR:
"Perfeito! Energia solar é uma excelente escolha para economia e sustentabilidade. ☀️

Para preparar um orçamento personalizado, preciso de algumas informações.

Primeiro, qual é o seu nome e sobrenome?"

IDENTIFICOU_SUBESTACAO:
"Entendi! Trabalhamos com reformas, manutenções e construção de subestações. 🔧

Para entender melhor sua necessidade:
É manutenção preventiva, corretiva ou reforma completa?

Mas antes, qual o seu nome?"

IDENTIFICOU_BESS:
"Sistemas de armazenamento de energia são ideais para garantir continuidade e economia! 🔋

Você já possui sistema solar instalado ou seria uma instalação independente?

Mas primeiro, qual o seu nome?"

IDENTIFICOU_ANALISE:
"Entendo! Podemos fazer análise detalhada para identificar problemas ou oportunidades de economia. 📊

Seria análise de consumo, qualidade de energia ou laudo para perícia?

Antes, me diz seu nome?"

IDENTIFICOU_PROJETO:
"Perfeito! Fazemos projetos elétricos para todos os segmentos. 📐

É um projeto para construção nova ou adequação/regularização?

Qual o seu nome?"

PEDINDO_EMAIL:
"Prazer, {{nome}}!

Qual o seu melhor email para contato?"

PEDINDO_ENDERECO:
"Ótimo! Agora preciso do endereço onde será realizado o serviço.

Pode me passar o endereço completo (rua, número, bairro, cidade e CEP)?
Ou se preferir, envie sua localização pelo WhatsApp 📍"

PEDINDO_CONTA_ENERGIA:
"Para dimensionar o sistema ideal, preciso analisar seu consumo.

Pode me enviar uma foto da sua conta de energia mais recente? 📄"

ANALISOU_CONTA:
"Recebi e analisei sua conta! 📊

{{resultado_analise_vision}}

Agora preciso conhecer o local de instalação. Pode enviar algumas fotos?"

PEDINDO_FOTOS_LOCAL:
"Para {{servico}}, preciso ver o local.

Pode enviar 2-3 fotos mostrando:
{{instrucoes_especificas_servico}}"

PEDINDO_PREFERENCIA_HORARIO:
"Ótimo, já tenho as informações técnicas!

Vamos agendar uma visita gratuita. Quais dias e horários funcionam melhor pra você?

📅 Dias: Segunda a Sexta
🕐 Turnos: Manhã (8h-12h) ou Tarde (13h-18h)"

OFERECENDO_HORARIOS:
"Baseado na sua preferência, temos essas opções:

1️⃣ {{opcao_1}}
2️⃣ {{opcao_2}}
3️⃣ {{opcao_3}}

Qual funciona melhor? Ou quer ver outros horários?"

CONFIRMACAO_AGENDAMENTO:
"✅ Visita técnica confirmada!

📅 {{data}}
🕐 {{horario_inicio}} às {{horario_fim}}
📍 {{endereco}}
👷 Técnico: {{nome_tecnico}}

Você receberá um lembrete no dia anterior.

Alguma observação sobre acesso ao local? (portaria, interfone, etc.)"

HANDOFF_COMERCIAL:
"Entendi! Vou te conectar com nosso time comercial.

Em instantes um atendente vai continuar a conversa. ⏳

Enquanto isso, posso adiantar alguma informação sobre sua necessidade?"

DESPEDIDA:
"Foi um prazer atender você!

Se precisar de qualquer coisa, é só mandar mensagem aqui.

Até logo! 💚"

NAO_ENTENDI:
"Hmm, não tenho certeza se entendi. 🤔

Você gostaria de:
1️⃣ Energia Solar
2️⃣ Subestação
3️⃣ Projeto Elétrico
4️⃣ Armazenamento de Energia
5️⃣ Análise e Laudo
6️⃣ Falar com o Comercial

Responde com o número ou me conta mais sobre o que precisa!"

LEMBRETE_24H:
"⏰ Lembrete E2 Soluções

Sua visita técnica está agendada para amanhã, {{data}}, entre {{hora_ini}} e {{hora_fim}}.

Caso precise reagendar, responda com *reagendar*."

LEMBRETE_2H:
"🚗 O técnico está a caminho!

Sua visita da E2 Soluções está confirmada para hoje, entre {{hora_ini}} e {{hora_fim}}.

Qualquer problema, responda esta mensagem."
```

### 10. BASE DE CONHECIMENTO (knowledge/)

**knowledge/servicos/energia_solar.md**
```markdown
# Energia Solar Fotovoltaica - E2 Soluções

## O que é?
Sistema que converte luz solar em energia elétrica, reduzindo ou eliminando a conta de luz.

## Segmentos Atendidos
- **Residencial**: Casas e apartamentos
- **Comercial**: Lojas, escritórios, clínicas
- **Industrial**: Fábricas e galpões
- **Agronegócio**: Fazendas, irrigação, aviários

## Tipos de Sistema
- **On-grid**: Conectado à rede da concessionária. Excedente vira créditos.
- **Off-grid**: Independente da rede, com baterias. Ideal para locais remotos.
- **Híbrido**: Conectado à rede + baterias para backup.

## Benefícios
- Economia de até 95% na conta de luz
- Retorno do investimento em 3-5 anos
- Vida útil de 25+ anos
- Valorização do imóvel
- Energia limpa e sustentável

## Como funciona o processo
1. Análise da conta de energia
2. Visita técnica para levantamento
3. Projeto personalizado
4. Proposta comercial
5. Instalação (1-3 dias)
6. Homologação junto à concessionária
7. Ativação do sistema

## Perguntas Frequentes

### Quanto custa?
O valor varia conforme o consumo. Em média:
- Residencial (300-500 kWh): R$ 15.000 - R$ 25.000
- Comercial pequeno: R$ 30.000 - R$ 80.000
- Industrial: Sob consulta

### Quanto tempo dura a instalação?
Residencial: 1-2 dias
Comercial: 2-5 dias
Industrial: 1-4 semanas

### Precisa de manutenção?
Manutenção mínima. Limpeza periódica dos painéis (2-3x ao ano).
```

**knowledge/servicos/subestacao.md**
```markdown
# Subestação Elétrica - E2 Soluções

## O que é?
Conjunto de equipamentos que recebe energia em média/alta tensão e transforma para uso na instalação.

## Serviços Oferecidos

### Manutenção Preventiva
- Inspeção termográfica
- Análise de óleo do transformador
- Teste de equipamentos
- Limpeza e ajustes
- Relatório técnico

### Manutenção Corretiva
- Reparo de equipamentos
- Substituição de componentes
- Atendimento emergencial

### Reforma
- Adequação às normas vigentes
- Modernização de equipamentos
- Ampliação de capacidade
- Retrofit de disjuntores e chaves

### Construção
- Projeto completo
- Fornecimento de equipamentos
- Instalação e comissionamento
- Homologação junto à concessionária

## Classes de Tensão
- 13.8 kV
- 34.5 kV
- 69 kV
- 138 kV

## Normas Atendidas
- NR-10: Segurança em instalações elétricas
- NBR 14039: Instalações elétricas de média tensão
- Normas das concessionárias locais
```

**knowledge/servicos/armazenamento_energia.md**
```markdown
# Sistemas de Armazenamento de Energia (BESS) - E2 Soluções

## O que é?
Sistema de baterias que armazena energia para uso posterior, garantindo continuidade e economia.

## Aplicações

### Backup/Nobreak
- Proteção contra quedas de energia
- Continuidade para equipamentos críticos
- Ideal para: hospitais, data centers, indústrias

### Integração Solar
- Armazena excedente da geração solar
- Uso noturno da energia gerada de dia
- Maior independência da rede

### Gestão de Demanda
- Reduz picos de consumo
- Economia na tarifa de demanda
- Ideal para clientes do Grupo A

### Autossuficiência
- Independência total ou parcial da rede
- Combinação solar + baterias
- Ideal para locais remotos

## Tecnologias
- Lítio (LFP): Mais durável, segura
- Chumbo-ácido: Menor custo inicial
- Fluxo: Para grandes capacidades

## Benefícios
- Continuidade de energia
- Economia em tarifas horárias
- Proteção de equipamentos
- Independência energética
```

**knowledge/servicos/analise_laudos.md**
```markdown
# Análise de Energia e Laudos - E2 Soluções

## Serviços

### Análise de Consumo
- Identificação de desperdícios
- Análise de faturas
- Recomendações de economia
- Adequação tarifária

### Análise de Qualidade de Energia
- Medição de harmônicos
- Análise de fator de potência
- Identificação de distúrbios
- Soluções para problemas de qualidade

### Laudo para Perícia Judicial
- Análise técnica imparcial
- Documentação completa
- Suporte em processos judiciais
- Identificação de responsabilidades

## Quando Contratar?

### Análise de Consumo
- Conta de luz muito alta
- Suspeita de cobrança indevida
- Mudança de tarifa
- Planejamento de eficiência

### Qualidade de Energia
- Queima frequente de equipamentos
- Oscilações de tensão
- Problemas com motores
- Interferências em sistemas

### Laudo Pericial
- Processos contra concessionária
- Acidentes elétricos
- Disputas contratuais
- Sinistros em seguros
```

### 11. DOCUMENTAÇÃO PRINCIPAL (README.md)

```markdown
# 🤖 E2 Soluções AI Bot v3

Bot de WhatsApp inteligente para a E2 Soluções, usando IA conversacional para atendimento ao cliente, coleta de informações e agendamento de visitas técnicas. **Integração completa com RD Station CRM**.

## 🚀 Quick Start (5 minutos)

### Pré-requisitos
- Docker e Docker Compose instalados
- Git
- Conta RD Station CRM (Basic, Pro ou Advanced)

### Instalação

```bash
# Clonar repositório
git clone https://github.com/e2solucoes/bot-whatsapp.git
cd bot-whatsapp

# Copiar configuração de exemplo
cp docker/.env.dev.example docker/.env.dev

# Iniciar ambiente de desenvolvimento
./scripts/start-dev.sh
```

### Acessar
- **n8n**: http://localhost:5678
- **Supabase**: http://localhost:3000
- **Mailhog**: http://localhost:8025

## 📖 Documentação Completa

| Documento | Descrição |
|-----------|-----------|
| [Planejamento](docs/PLAN/README.md) | Arquitetura, roadmap, requisitos |
| [Setup](docs/Setups/README.md) | Guias de configuração de cada serviço |
| [Setup RD Station](docs/Setups/SETUP_RDSTATION.md) | Integração com CRM |
| [Desenvolvimento](docs/development/README.md) | Guia do desenvolvedor |
| [Deploy](docs/deployment/README.md) | Deploy em produção |
| [Implementação](docs/implementation/README.md) | Detalhes da implementação |
| [Diretrizes](docs/guidelines/README.md) | Padrões e convenções |
| [Monitoramento](docs/monitoring/README.md) | Logs, métricas, alertas |

## 🏗️ Arquitetura

```
[WhatsApp] ←→ [Evolution API] ←→ [n8n + Claude AI]
                                        ↓
                    ┌───────────────────┼───────────────────┐
                    ↓                   ↓                   ↓
            [Supabase RAG]      [PostgreSQL]        [RD Station CRM]
            Base Conhecimento   Chat Memory         Leads + Deals
                    ↓                   ↓                   ↓
            [Google Services]   [Notificações]      [Pipeline Vendas]
            Calendar/Drive      Email/Discord
```

## 🛠️ Stack Tecnológica

| Componente | Tecnologia |
|------------|------------|
| Orquestração | n8n (self-hosted) |
| IA Conversacional | Claude 3.5 Sonnet |
| IA Vision | Claude Vision |
| Embeddings | OpenAI ada-002 |
| Vector Store | Supabase + pgvector |
| Chat Memory | PostgreSQL |
| **CRM** | **RD Station CRM** |
| WhatsApp | Evolution API |
| Armazenamento | Google Drive |
| Agendamento | Google Calendar |
| Backup Leads | Google Sheets |
| Notificações | Email + Discord |

## ⚡ Serviços Atendidos

| Serviço | Ícone | Descrição |
|---------|-------|-----------|
| Energia Solar | ☀️ | Residencial, comercial, industrial, agro |
| Subestação | 🔧 | Reforma, manutenção, construção |
| Projetos Elétricos | 📐 | Residencial, comercial, industrial |
| BESS | 🔋 | Armazenamento e backup de energia |
| Análise e Laudos | 📊 | Consumo, qualidade, perícia |

## 📁 Estrutura do Projeto

```
e2-solucoes-bot/
├── docker/           # Docker Compose e configs
├── database/         # Migrations e seeds
├── n8n/              # Workflows exportados
├── knowledge/        # Base de conhecimento RAG
├── docs/             # Documentação completa
├── scripts/          # Scripts auxiliares
└── templates/        # Templates de email, sheets, CRM
```

## 🤝 Contribuindo

Veja [docs/development/contributing.md](docs/development/contributing.md)

## 📄 Licença

Proprietário - E2 Soluções
```

## CRITÉRIOS DE QUALIDADE

O código entregue deve:

1. **Funcional**: Estar pronto para rodar localmente sem modificações
2. **Completo**: Todos os arquivos especificados devem existir e ter conteúdo real
3. **Documentado**: Comentários onde necessário, READMEs explicativos
4. **Seguro**: Sem secrets hardcoded, validação de inputs
5. **Testável**: Ambiente dev isolado, dados de teste inclusos
6. **Organizado**: Estrutura de pastas clara, nomenclatura consistente
7. **Integrado**: RD Station CRM funcionando bidirecionalmente

## ORDEM DE EXECUÇÃO

1. **Infraestrutura Docker** (docker-compose-dev.yml, docker-compose.yml, configs)
2. **Banco de Dados** (migrations, seeds, schema - incluindo tabelas RD Station)
3. **Scripts auxiliares** (incluindo install-n8n-nodes.sh)
4. **Workflows n8n** (todos os 10 workflows em JSON)
5. **Base de Conhecimento** (arquivos .md em /knowledge - TODOS OS 5 SERVIÇOS)
6. **Templates** (email, sheets, rdstation)
7. **Documentação** (todos os .md em /docs)

## EXECUTE

Crie toda a estrutura de arquivos conforme especificado. Todo código deve ser funcional e completo - NÃO use placeholders como "// TODO" ou "...". Os workflows n8n devem estar prontos para importar. A documentação deve permitir que alguém sem conhecimento prévio consiga subir o projeto seguindo os passos.

Comece criando a estrutura de pastas, depois implemente cada componente na ordem especificada.
