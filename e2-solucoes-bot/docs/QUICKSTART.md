# 🚀 E2 Soluções Bot - Quick Start (Sprint 1.1)

Guia rápido para iniciar validação do sistema RAG em modo de desenvolvimento.

## ✅ Pré-requisitos

- Docker e Docker Compose instalados
- Credenciais configuradas:
  - ✅ OpenAI API Key
  - ✅ Supabase URL + Keys
  - ✅ n8n (será iniciado via Docker)

## 📁 Estrutura Organizada

```
e2-solucoes-bot/
├── docker/                        # ← Configurações Docker organizadas
│   ├── docker-compose.yml         # Produção (completo)
│   ├── docker-compose-dev.yml     # Desenvolvimento (Sprint 1.1)
│   ├── .env                       # Credenciais (NÃO commitar)
│   ├── .env.example               # Template produção
│   ├── .env.dev.example           # Template desenvolvimento
│   └── README.md                  # Documentação Docker completa
├── docs/validation/               # Guias de validação detalhados
├── n8n/workflows/                 # Workflows n8n
├── database/                      # Funções SQL
└── scripts/                       # Scripts de automação
```

## 🎯 Validação Sprint 1.1 (5 Passos)

### Passo 1: ✅ COMPLETO - Credenciais Configuradas

Você já completou esta etapa:
- ✅ OpenAI API Key configurada
- ✅ Supabase conectado
- ✅ docker/.env com credenciais válidas

### Passo 2: 🚀 Iniciar n8n (Development)

```bash
# Iniciar n8n em modo desenvolvimento
docker-compose -f docker/docker-compose-dev.yml up -d

# Verificar status
docker-compose -f docker/docker-compose-dev.yml ps

# Ver logs
docker-compose -f docker/docker-compose-dev.yml logs -f n8n-dev

# Acessar n8n
# URL: http://localhost:5678 (sem autenticação)
```

### Passo 3: Deploy Funções SQL

```bash
# Opção A: Dashboard Supabase (RECOMENDADO)
# 1. Acessar: https://supabase.com/dashboard/project/_/sql/new
# 2. Copiar conteúdo de: database/supabase_functions.sql
# 3. Executar (RUN)

# Opção B: Via Script (se tiver Supabase CLI)
supabase db reset
```

**Validação**:
```bash
# Verificar tabela criada
curl "${SUPABASE_URL}/rest/v1/knowledge_documents?select=count" \
  -H "apikey: ${SUPABASE_SERVICE_KEY}" \
  -H "Content-Type: application/json"
# Esperado: {"count": 0} ou similar
```

### Passo 4: Executar Ingest

```bash
# Popular base de conhecimento
./scripts/ingest-knowledge.sh

# Monitorar progresso
watch -n 10 "curl -s ${SUPABASE_URL}/rest/v1/knowledge_documents?select=count \
  -H 'apikey: ${SUPABASE_SERVICE_KEY}' | jq '.[0].count'"
```

**Esperado**: 50-100 chunks com embeddings inseridos

### Passo 5: Importar Workflow n8n

1. Acessar: http://localhost:5678
2. Menu → Import from File
3. Selecionar: `n8n/workflows/03_rag_knowledge_query.json`
4. Configurar credenciais:
   - **OpenAI API**: Adicionar OPENAI_API_KEY
   - **PostgreSQL**: Adicionar conexão Supabase
5. Ativar workflow (toggle ON)

### Passo 6: Validar Sistema

```bash
# Teste básico RAG
curl -X POST http://localhost:5678/webhook/rag-query \
  -H "Content-Type: application/json" \
  -d '{"query_text": "como funciona energia solar"}' | jq .

# Esperado: 3-5 resultados com similarity >= 0.75
```

## 📚 Documentação Completa

Para guias detalhados, consulte `docs/validation/`:

1. `SETUP_CREDENTIALS.md` - Como obter credenciais
2. `DEPLOY_SQL.md` - Deploy funções Supabase
3. `EXECUTE_INGEST.md` - Popular conhecimento
4. `IMPORT_N8N_WORKFLOW.md` - Importar workflow
5. `RUN_VALIDATION_TESTS.md` - Testes completos

## 🐛 Troubleshooting Rápido

### n8n não inicia
```bash
# Verificar se porta 5678 está livre
lsof -i :5678

# Reiniciar limpo
docker-compose -f docker/docker-compose-dev.yml down -v
docker-compose -f docker/docker-compose-dev.yml up -d
```

### Webhook não responde
```bash
# Verificar workflow ativo no n8n
# http://localhost:5678/workflows

# Ver logs detalhados
docker-compose -f docker/docker-compose-dev.yml logs -f n8n-dev
```

### Credenciais não funcionam
```bash
# Validar OpenAI
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $(grep OPENAI_API_KEY docker/.env | cut -d= -f2)" | jq .

# Validar Supabase
SUPABASE_URL=$(grep SUPABASE_URL docker/.env | cut -d= -f2)
SUPABASE_KEY=$(grep SUPABASE_SERVICE_KEY docker/.env | cut -d= -f2)
curl "${SUPABASE_URL}/rest/v1/" -H "apikey: ${SUPABASE_KEY}" | jq .
```

## ⚡ Comandos Úteis

```bash
# Parar n8n
docker-compose -f docker/docker-compose-dev.yml down

# Parar e remover dados
docker-compose -f docker/docker-compose-dev.yml down -v

# Ver logs em tempo real
docker-compose -f docker/docker-compose-dev.yml logs -f

# Restart completo
docker-compose -f docker/docker-compose-dev.yml restart
```

## ✅ Checklist de Validação

- [ ] n8n rodando em http://localhost:5678
- [ ] Funções SQL deployadas no Supabase
- [ ] 50-100 chunks com embeddings no banco
- [ ] Workflow RAG importado e ativo
- [ ] Webhook respondendo queries com resultados relevantes

## 🎉 Próximos Passos

### ✅ Ambiente Base Configurado!

Você completou o setup do ambiente de desenvolvimento:
- ✅ n8n rodando em `http://localhost:5678`
- ✅ PostgreSQL/Supabase configurados
- ✅ Credenciais no `docker/.env`

### 📱 Configurar WhatsApp (Evolution API)

Para adicionar integração WhatsApp ao projeto:

**👉 Siga agora**: **[QUICKSTART_EVOLUTION_API.md](QUICKSTART_EVOLUTION_API.md)**

Este guia específico ensina como:
- Iniciar Evolution API (containers separados)
- Aplicar workaround da Issue #1474
- Gerar QR Code e conectar WhatsApp
- Configurar credenciais no n8n
- Testar envio/recebimento de mensagens

**Tempo estimado**: 10-15 minutos

---

### 🚀 Roadmap Completo

Após validação Sprint 1.1:
- **Sprint 1.2**: Anthropic Claude API integration
- **Sprint 1.3**: ✅ Evolution API (WhatsApp) - **[Ver QUICKSTART_EVOLUTION_API.md](QUICKSTART_EVOLUTION_API.md)**
- **Sprint 1.4**: Google Calendar + Drive
- **Sprint 1.5**: RD Station CRM

---

## 📊 Status Atual (2025-12-12)

**Validação Estrutural**: ✅ **100% COMPLETA**

**Passos Concluídos**:
- ✅ Passo 1: Credenciais configuradas e validadas
- ✅ Passo 2: n8n rodando (localhost:5678, healthy)
- ✅ Passo 3: SQL functions deployadas no Supabase
- ✅ Passo 5: Documentação de importação workflow criada
- ✅ Passo 6: Infraestrutura 100% validada

**Pendente**:
- ⏸️ Passo 4: Ingest - **AGUARDANDO novo token OpenAI** (equipe comercial)
- ⏳ Passo 5: Importação manual do workflow no n8n UI (10-15 min)

**Próximos Passos** (quando token disponível):
1. Atualizar `docker/.env` com novo token OpenAI
2. Importar workflow via n8n UI (manual)
3. Configurar credenciais OpenAI e PostgreSQL
4. Executar `scripts/ingest-simple.sh`
5. Testar RAG query completo

**Tempo Estimado**: ~15 minutos após token disponível

**Relatório Detalhado**: `VALIDATION_REPORT.md`
**Documentação Completa**: `docker/README.md` e `docs/validation/`
