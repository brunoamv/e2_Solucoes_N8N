# Docker Configuration - E2 Soluções Bot

Configurações Docker organizadas para desenvolvimento e produção.

## 📁 Estrutura

```
docker/
├── docker-compose.yml          # Produção (Traefik, SSL, monitoramento)
├── docker-compose-dev.yml      # Desenvolvimento (minimalista, Sprint 1.1)
├── .env                        # Credenciais REAIS (não commitar)
├── .env.example                # Template produção (todos os sprints)
└── .env.dev.example            # Template desenvolvimento (Sprint 1.1)
```

## 🚀 Quick Start - Desenvolvimento (Sprint 1.1)

### 1. Configurar Credenciais

```bash
# Copiar template de desenvolvimento
cp docker/.env.dev.example docker/.env

# Editar e preencher credenciais obrigatórias
nano docker/.env

# Obrigatório para Sprint 1.1:
# - OPENAI_API_KEY
# - SUPABASE_URL
# - SUPABASE_SERVICE_KEY
# - SUPABASE_ANON_KEY
```

### 2. Iniciar n8n Development

```bash
# Iniciar stack de desenvolvimento
docker-compose -f docker/docker-compose-dev.yml up -d

# Verificar status
docker-compose -f docker/docker-compose-dev.yml ps

# Ver logs
docker-compose -f docker/docker-compose-dev.yml logs -f n8n-dev
```

### 3. Acessar n8n

```
URL: http://localhost:5678
Autenticação: DESABILITADA (dev only)
```

### 4. Parar Stack

```bash
# Parar serviços (preserva dados)
docker-compose -f docker/docker-compose-dev.yml down

# Parar e remover volumes (limpa tudo)
docker-compose -f docker/docker-compose-dev.yml down -v
```

## 🏭 Produção

### Configuração Completa

```bash
# Copiar template de produção
cp docker/.env.example docker/.env

# Preencher TODAS as credenciais
nano docker/.env

# Configurar domínios e SSL
# - DOMAIN=e2solucoes.com.br
# - TRAEFIK_ACME_EMAIL=admin@e2solucoes.com.br
# - N8N_SUBDOMAIN=n8n
# - EVOLUTION_SUBDOMAIN=whatsapp
```

### Iniciar Stack Produção

```bash
# Iniciar stack completa
docker-compose -f docker/docker-compose.yml up -d

# Verificar status
docker-compose -f docker/docker-compose.yml ps

# Ver logs Traefik (SSL)
docker-compose -f docker/docker-compose.yml logs -f traefik
```

## 🔍 Diferenças: Dev vs Prod

| Aspecto | Development | Production |
|---------|-------------|------------|
| **Serviços** | n8n apenas | Traefik, n8n, Evolution API, PostgreSQL, Redis, Prometheus, Grafana |
| **Autenticação** | Desabilitada | Basic Auth habilitado |
| **SSL/TLS** | HTTP simples | HTTPS com Let's Encrypt |
| **Domínio** | localhost:5678 | n8n.e2solucoes.com.br |
| **Banco de Dados** | Supabase Cloud | PostgreSQL local + Supabase |
| **Logs** | Console (debug) | Arquivo + Prometheus |
| **Monitoring** | Nenhum | Prometheus + Grafana |
| **Credenciais** | Sprint 1.1 apenas | Todos os sprints |

## 📋 Validação Sprint 1.1

### Checklist Desenvolvimento

- [ ] docker/.env criado com credenciais válidas
- [ ] OpenAI API Key funcionando
- [ ] Supabase conectando
- [ ] n8n acessível em http://localhost:5678
- [ ] Workflow RAG importado
- [ ] Webhook respondendo queries

### Comandos de Validação

```bash
# 1. Validar OpenAI API
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $(grep OPENAI_API_KEY docker/.env | cut -d= -f2)" | jq .

# 2. Validar Supabase
SUPABASE_URL=$(grep SUPABASE_URL docker/.env | cut -d= -f2)
SUPABASE_KEY=$(grep SUPABASE_SERVICE_KEY docker/.env | cut -d= -f2)
curl "${SUPABASE_URL}/rest/v1/" \
  -H "apikey: ${SUPABASE_KEY}" | jq .

# 3. Validar n8n
curl http://localhost:5678/healthz

# 4. Testar Webhook RAG (após import workflow)
curl -X POST http://localhost:5678/webhook/rag-query \
  -H "Content-Type: application/json" \
  -d '{"query_text": "como funciona energia solar"}' | jq .
```

## 🛠️ Troubleshooting

### n8n não inicia

```bash
# Verificar logs
docker-compose -f docker/docker-compose-dev.yml logs n8n-dev

# Verificar se porta 5678 está livre
lsof -i :5678

# Remover volume e reiniciar
docker-compose -f docker/docker-compose-dev.yml down -v
docker-compose -f docker/docker-compose-dev.yml up -d
```

### Credenciais não funcionam

```bash
# Verificar .env carregado
docker-compose -f docker/docker-compose-dev.yml config | grep -A 5 environment

# Recarregar credenciais
docker-compose -f docker/docker-compose-dev.yml down
docker-compose -f docker/docker-compose-dev.yml up -d
```

### Webhook não responde

```bash
# Verificar workflow ativo no n8n
# Acessar: http://localhost:5678/workflows

# Verificar execuções
# Acessar: http://localhost:5678/executions

# Testar manualmente
curl -v -X POST http://localhost:5678/webhook/rag-query \
  -H "Content-Type: application/json" \
  -d '{"query_text": "teste"}'
```

## 📚 Próximos Passos

Após validação Sprint 1.1 (desenvolvimento):

1. **Sprint 1.2**: Adicionar Anthropic Claude API
2. **Sprint 1.3**: Configurar Evolution API (WhatsApp)
3. **Sprint 1.4**: Integrar Google Calendar + Drive
4. **Sprint 1.5**: Conectar RD Station CRM
5. **Produção**: Migrar para docker-compose.yml completo

## 🔐 Segurança

⚠️ **NUNCA commite docker/.env no git!**

```bash
# Verificar se .env está no .gitignore
grep "^docker/.env$" .gitignore

# Se não estiver, adicionar
echo "docker/.env" >> .gitignore
```

## 📖 Documentação Completa

Guias detalhados em `docs/validation/`:

- `SETUP_CREDENTIALS.md` - Obter credenciais
- `DEPLOY_SQL.md` - Deploy funções Supabase
- `EXECUTE_INGEST.md` - Popular base de conhecimento
- `IMPORT_N8N_WORKFLOW.md` - Importar workflow RAG
- `RUN_VALIDATION_TESTS.md` - Testes end-to-end

---

**Status**: ✅ Estrutura organizada para dev e prod
**Sprint Atual**: 1.1 - RAG e Base de Conhecimento
**Última Atualização**: 2025-01-12
