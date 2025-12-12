# 🤖 E2 Soluções AI Bot v3

Bot de WhatsApp inteligente com Claude AI, RAG e integração completa com RD Station CRM para automação de atendimento e qualificação de leads.

## ⚡ Quick Start (5 minutos)

### Pré-requisitos
- Docker e Docker Compose instalados
- Git
- Conta RD Station CRM (Basic, Pro ou Advanced)
- APIs: Anthropic Claude, Evolution API (WhatsApp)

### Instalação Rápida

```bash
# Clonar repositório
git clone <repo-url>
cd e2-solucoes-bot

# Copiar configuração de desenvolvimento
cp docker/.env.dev.example docker/.env.dev

# Editar variáveis (API keys obrigatórias)
nano docker/.env.dev

# Iniciar ambiente de desenvolvimento
./scripts/start-dev.sh
```

### Acessar Serviços

| Serviço | URL | Descrição |
|---------|-----|-----------|
| **n8n** | http://localhost:5678 | Workflows e configuração |
| **Supabase Studio** | http://localhost:3000 | Interface visual do banco |
| **Traefik Dashboard** | http://localhost:8080 | Status dos serviços |
| **Mailhog** | http://localhost:8025 | Emails de teste |
| **PostgreSQL** | localhost:5432 | Banco de dados principal |

## 🏗️ Arquitetura do Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                     WHATSAPP (Evolution API)                │
└───────────────────────────┬─────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   n8n WORKFLOW ORCHESTRATOR                 │
│  ┌─────────────────────────────────────────────────────┐    │
│  │           🤖 CLAUDE AI AGENT (3.5 Sonnet)           │    │
│  │  • Conversação natural em português                 │    │
│  │  • RAG: Consulta base de conhecimento E2           │    │
│  │  • Vision AI: Análise de fotos (conta luz, local)  │    │
│  │  • Memória persistente de conversa                 │    │
│  └─────────────────────────────────────────────────────┘    │
│         ↓              ↓              ↓             ↓        │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐  ┌──────────┐  │
│  │ Supabase │   │PostgreSQL│   │  Google  │  │RD Station│  │
│  │  Vector  │   │  Memory  │   │ Services │  │   CRM    │  │
│  │   RAG    │   │  + Leads │   │Cal/Drive │  │ Pipeline │  │
│  └──────────┘   └──────────┘   └──────────┘  └──────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 📋 Funcionalidades Principais

### 🧠 IA Conversacional
- **Entendimento Natural**: Detecta intenção sem menus rígidos
- **RAG Integrado**: Consulta automática base de conhecimento E2
- **Memória Persistente**: Contexto mantido entre conversas
- **Multimodal**: Processa texto, imagens, áudio, localização

### 🔍 Análise Inteligente
- **Vision AI**: Analisa contas de energia, fotos de instalações
- **Extração de Dados**: Consumo kWh, tensão, tipo de instalação
- **Dimensionamento**: Calcula potência solar necessária (kWp)
- **Estimativas**: Economia mensal, número de painéis

### 📅 Agendamento Automatizado
- **Google Calendar**: Sincronização de disponibilidade
- **Lembretes**: 24h e 2h antes da visita
- **Gestão de Técnicos**: Alocação por especialidade
- **Reagendamento**: Automático via chat

### 🔄 Integração RD Station CRM

#### Sincronização Automática
1. **Criar Contato** quando novo lead identificado
2. **Criar Negociação** no pipeline configurado
3. **Atualizar Dados** em tempo real durante coleta
4. **Mover Etapas** conforme progresso (Novo → Qualificando → Agendado)
5. **Criar Tarefas** para técnicos na data da visita
6. **Registrar Notas** com análise da IA e observações

#### Pipeline Sugerido
```
┌─────────────────────────────────────────────────────────────┐
│ Novo Lead → Qualificando → Agendado → Proposta → Ganho     │
│  (automático)  (bot coleta)  (visita)   (comercial) (venda) │
└─────────────────────────────────────────────────────────────┘
                                    ↓
                            [Perdido] (motivo registrado)
```

## 🎯 Serviços da E2 Soluções

| Serviço | Descrição | Dados Coletados |
|---------|-----------|-----------------|
| ☀️ **Energia Solar** | Projetos residenciais, comerciais, industriais | Consumo kWh, fotos conta/local, interesse em bateria |
| ⚡ **Subestação** | Reformas, manutenção, construção | Tensão, tipo de serviço, urgência, fotos |
| 📐 **Projetos Elétricos** | Projetos e regularizações | Tipo, carga estimada, planta |
| 🔋 **BESS (Armazenamento)** | Sistemas de baterias | Objetivo, potência necessária, possui solar |
| 📊 **Análise e Laudos** | Análise de consumo, qualidade, perícia | Tipo análise, histórico, descrição problema |

## 🛠️ Stack Tecnológica

| Camada | Tecnologia | Versão |
|--------|------------|--------|
| **Orquestração** | n8n | latest |
| **IA Principal** | Claude 3.5 Sonnet | 20241022 |
| **Vision AI** | Claude Vision | 3.5 |
| **Embeddings** | OpenAI | ada-002 |
| **Vector DB** | Supabase + pgvector | 15.1 |
| **Database** | PostgreSQL | 15 |
| **CRM** | RD Station CRM | API v1 |
| **WhatsApp** | Evolution API | - |
| **Cache** | Redis | 7 |
| **Gateway** | Traefik | 2.10 |
| **Storage** | Google Drive | API v3 |
| **Agenda** | Google Calendar | API v3 |

## 📂 Estrutura do Projeto

```
e2-solucoes-bot/
├── docker/                  # Infraestrutura containerizada
│   ├── docker-compose-dev.yml
│   ├── docker-compose.yml
│   └── configs/
├── database/                # Schema e migrations
│   ├── migrations/
│   ├── seeds/
│   └── schema.sql
├── n8n/                     # Workflows n8n
│   ├── workflows/           # 10 workflows JSON
│   └── credentials/
├── knowledge/               # Base de conhecimento RAG
│   ├── servicos/            # 5 serviços E2
│   ├── faq/
│   └── tecnicos/
├── docs/                    # Documentação completa
│   ├── PLAN/
│   ├── Setups/
│   ├── development/
│   └── deployment/
├── scripts/                 # Automação
└── templates/               # Email, Sheets, CRM
```

## 📖 Documentação Completa

| Seção | Conteúdo |
|-------|----------|
| [Planejamento](docs/PLAN/README.md) | Arquitetura, roadmap, decisões técnicas |
| [Setup Geral](docs/Setups/README.md) | Guias configuração de todos os serviços |
| [Setup RD Station](docs/Setups/SETUP_RDSTATION.md) | **Integração CRM detalhada** |
| [Desenvolvimento](docs/development/README.md) | Como desenvolver e debugar |
| [Deploy](docs/deployment/README.md) | Deploy em produção |
| [Workflows](docs/implementation/README.md) | Detalhes dos 10 workflows |
| [Monitoramento](docs/monitoring/README.md) | Logs, métricas, alertas |

## 🚀 Guias de Início Rápido

### Desenvolvedor
```bash
# Setup completo de desenvolvimento
./scripts/start-dev.sh

# Ver logs de todos os serviços
./scripts/logs.sh

# Rodar migrations
./scripts/migrate.sh

# Carregar base de conhecimento
./scripts/ingest-knowledge.sh
```

### Administrador
```bash
# Deploy produção
./scripts/start-prod.sh

# Backup completo
./scripts/backup.sh

# Health check
./scripts/health-check.sh
```

## 🔐 Variáveis de Ambiente Críticas

**Mínimo para rodar DEV:**
```bash
# APIs obrigatórias
ANTHROPIC_API_KEY=sk-ant-xxx
EVOLUTION_API_URL=https://evolution.seudominio.com.br
EVOLUTION_API_KEY=xxx

# RD Station CRM
RDSTATION_CLIENT_ID=xxx
RDSTATION_CLIENT_SECRET=xxx
RDSTATION_REFRESH_TOKEN=xxx
```

Ver `.env.dev.example` para lista completa.

## ⚙️ Configuração Inicial

### 1. Configurar RD Station CRM
```bash
# Seguir guia completo
docs/Setups/SETUP_RDSTATION.md

# Criar campos customizados no CRM
# Configurar pipeline "Bot WhatsApp E2 Soluções"
# Obter credenciais OAuth2
```

### 2. Importar Workflows n8n
```bash
# Acessar http://localhost:5678
# Importar workflows de n8n/workflows/
# Configurar credenciais:
#   - Anthropic API
#   - Evolution API
#   - RD Station CRM
#   - Google Services
```

### 3. Carregar Base de Conhecimento
```bash
./scripts/ingest-knowledge.sh
```

## 🧪 Testando o Bot

### Teste 1: Fluxo Energia Solar
```
Você: Oi, quero colocar energia solar
Bot: [Identifica serviço, cria contato RD Station]
     Olá! Que ótimo que você está interessado em energia solar! ☀️
     Para preparar um orçamento personalizado, qual é o seu nome?

Você: João Silva
Bot: [Atualiza contato no CRM, move para "Qualificando"]
     Prazer, João! Qual o seu melhor email?

[... fluxo continua até agendamento]

Bot: ✅ Visita confirmada!
     [CRM: Move para "Agendado", cria tarefa para técnico]
```

### Teste 2: Handoff para Comercial
```
Você: Quero falar com alguém
Bot: [CRM: Marca prioridade alta, notifica owner]
     Entendi! Vou te conectar com nosso time comercial.
```

## 📊 Métricas e Monitoramento

### Health Checks
```bash
./scripts/health-check.sh

# Saída:
✓ PostgreSQL: UP (5432)
✓ Supabase: UP (3000)
✓ n8n: UP (5678)
✓ Redis: UP (6379)
✓ RD Station API: UP (200ms latency)
```

### Logs
```bash
# Todos os serviços
docker-compose -f docker/docker-compose-dev.yml logs -f

# Apenas n8n
docker logs -f e2-n8n-dev

# Apenas conversações (PostgreSQL)
docker exec -it e2-postgres-dev psql -U e2solucoes -d e2_bot \
  -c "SELECT * FROM conversations ORDER BY created_at DESC LIMIT 10;"
```

## 🐛 Troubleshooting

| Problema | Solução |
|----------|---------|
| n8n não conecta no banco | Verificar credenciais em `.env.dev`, aguardar health check |
| Bot não responde | Verificar Evolution API conectada, webhook configurado |
| RAG não retorna resultados | Rodar `./scripts/ingest-knowledge.sh` |
| Erro sync RD Station | Verificar tokens OAuth2, `rdstation_sync_log` table |

Ver [docs/development/debugging.md](docs/development/debugging.md) para guia completo.

## 🤝 Contribuindo

Veja [docs/development/contributing.md](docs/development/contributing.md)

## 📄 Licença

Proprietário - E2 Soluções

---

## 🎯 Próximos Passos

1. ✅ Leia [docs/Setups/README.md](docs/Setups/README.md)
2. ✅ Configure [RD Station CRM](docs/Setups/SETUP_RDSTATION.md)
3. ✅ Suba ambiente dev: `./scripts/start-dev.sh`
4. ✅ Importe workflows n8n
5. ✅ Teste fluxo completo com WhatsApp

**Dúvidas?** Consulte a [documentação completa](docs/) ou abra uma issue.
