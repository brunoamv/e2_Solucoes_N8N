# Importar Workflow n8n - Sprint 1.1 Validation

**Objetivo**: Importar e configurar o workflow RAG query no n8n

**Tempo Estimado**: 10-15 minutos

**Pré-requisitos**:
- ✅ Etapa 1 (SETUP_CREDENTIALS.md) completa
- ✅ Etapa 2 (DEPLOY_SQL.md) completa
- ✅ Etapa 3 (EXECUTE_INGEST.md) completa
- ✅ n8n instalado e rodando (localhost:5678 ou cloud)
- ✅ OpenAI e Supabase credenciais disponíveis

---

## 📋 O que Será Importado

O arquivo `n8n/workflows/03_rag_knowledge_query.json` (232 linhas) contém:

### Arquitetura do Workflow (7 Nós)

```
┌─────────────────────────────────────────────────────────────┐
│                    RAG Query Workflow                        │
└─────────────────────────────────────────────────────────────┘

1. Webhook RAG Query (Trigger)
   ↓
2. Validate Input
   ├─ Valid → Continue
   └─ Invalid → 3. Error Missing Query (HTTP 400)

4. Generate Embedding (OpenAI)
   ↓
5. Query Supabase (match_documents)
   ↓
6. Format Results for AI
   ↓
7. Respond Success (HTTP 200)
```

### Detalhes dos Nós

**Nó 1: Webhook RAG Query**
- **Tipo**: Webhook
- **Método**: POST
- **Endpoint**: `/webhook/rag-query`
- **Input**: `{ query_text, category?, match_threshold?, match_count? }`

**Nó 2: Validate Input**
- **Tipo**: IF
- **Condição**: `query_text` não vazio
- **Output**: true/false

**Nó 3: Error Missing Query**
- **Tipo**: Respond to Webhook
- **Status**: 400
- **Body**: `{ "error": "query_text is required", "status": "error" }`

**Nó 4: Generate Embedding (OpenAI)**
- **Tipo**: HTTP Request
- **Modelo**: text-embedding-3-small
- **Credencial**: openai-embeddings (API Key)
- **Output**: embedding vector(1536)

**Nó 5: Query Supabase**
- **Tipo**: PostgreSQL
- **Função**: match_documents()
- **Casting**: `'[...]'::vector`
- **Credencial**: supabase-postgres

**Nó 6: Format Results for AI**
- **Tipo**: Code (JavaScript)
- **Output**: Structured results + context string + metadata

**Nó 7: Respond Success**
- **Tipo**: Respond to Webhook
- **Status**: 200
- **Body**: JSON completo

---

## 🚀 Opção A: n8n via Docker (Recomendado para Desenvolvimento)

### Passo 1: Iniciar n8n via Docker

```bash
cd /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot

# Verificar se docker-compose.yml existe
ls docker-compose.yml

# Se existir, iniciar stack
docker-compose up -d

# Se NÃO existir, criar docker-compose.yml básico
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  n8n:
    image: n8nio/n8n:latest
    container_name: n8n
    restart: unless-stopped
    ports:
      - "5678:5678"
    environment:
      - N8N_BASIC_AUTH_ACTIVE=false
      - N8N_PORT=5678
      - N8N_PROTOCOL=http
      - N8N_HOST=localhost
      - WEBHOOK_URL=http://localhost:5678/
      - GENERIC_TIMEZONE=America/Sao_Paulo
    volumes:
      - n8n_data:/home/node/.n8n
      - ./n8n/workflows:/home/node/.n8n/workflows-import:ro

volumes:
  n8n_data:
    driver: local
EOF

# Iniciar n8n
docker-compose up -d

# Aguardar ~30-60 segundos
sleep 30

# Verificar status
docker-compose ps
# Deve mostrar: n8n (Up)

# Ver logs
docker-compose logs n8n
```

**Acessar n8n**: http://localhost:5678

### Passo 2: Configurar n8n (Primeira Vez)

1. Abrir navegador: http://localhost:5678
2. **Criar conta** (primeira execução):
   - Email: seu@email.com
   - Password: senha_forte_aqui
   - Clique em "Get Started"
3. **Pular tutoriais** (pode fazer depois)

### Passo 3: Importar Workflow via Interface

#### Método 1: Import via Arquivo

1. Na interface n8n, clique em **"Workflows"** (menu lateral esquerdo)
2. Clique em **"Add workflow"** (botão superior direito)
3. Clique no menu de 3 pontos **"⋮"** (canto superior direito)
4. Selecione **"Import from File..."**
5. Navegue até: `/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/03_rag_knowledge_query.json`
6. Clique em **"Open"**
7. Workflow será carregado na interface

#### Método 2: Import via Clipboard

```bash
# 1. Copiar conteúdo do workflow
cat /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/03_rag_knowledge_query.json | xclip -selection clipboard
# OU
cat n8n/workflows/03_rag_knowledge_query.json
# (copiar manualmente todo o JSON)
```

Na interface n8n:
1. Workflows → Add workflow
2. Menu ⋮ → **"Import from URL or Clipboard"**
3. Colar JSON completo
4. Clique em **"Import"**

---

## 🔧 Configurar Credenciais no n8n

### Credencial 1: OpenAI API (openai-embeddings)

1. No workflow importado, clique no nó **"Generate Embedding (OpenAI)"**
2. No painel direito, em **"Credentials"**, clique em **"Select Credential"**
3. Se não houver credencial OpenAI:
   - Clique em **"+ Create New Credential"**
   - Selecione tipo: **"OpenAI API"**
   - Nome: `openai-embeddings`
   - **API Key**: `sk-proj-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX`
     - (copiar do seu .env: `echo $OPENAI_API_KEY`)
   - Clique em **"Save"**
4. Selecione a credencial `openai-embeddings`

**Testar Credencial**:
- Clique em **"Test Credential"**
- Deve retornar: ✅ "Credential test successful"

### Credencial 2: PostgreSQL Supabase (supabase-postgres)

1. No workflow, clique no nó **"Query Supabase (match_documents)"**
2. No painel direito, em **"Credentials"**, clique em **"Select Credential"**
3. Se não houver credencial PostgreSQL:
   - Clique em **"+ Create New Credential"**
   - Selecione tipo: **"PostgreSQL"**
   - Nome: `supabase-postgres`
   - **Configuração**:
     ```
     Host: XXXXXXXX.supabase.co (extrair de SUPABASE_URL)
     Database: postgres
     User: postgres
     Password: [database_password] (do Supabase, NÃO é a SERVICE_KEY)
     Port: 5432
     SSL: Enabled (obrigatório para Supabase)
     ```
4. **Como obter Database Password**:
   - Supabase Dashboard → Settings → Database
   - **Database Password**: (você definiu ao criar o projeto)
   - **Ou resetar**: Settings → Database → Reset database password

**IMPORTANTE**: Use a **Database Password** do Supabase, NÃO a SERVICE_KEY!

**Testar Credencial**:
- Clique em **"Test Connection"**
- Deve retornar: ✅ "Connection successful"

---

## ✅ Ativar e Testar Workflow

### Passo 1: Ativar Workflow

1. No workflow importado, clique no botão **"Inactive"** (canto superior direito)
2. Deve mudar para: **"Active"** (verde)
3. Workflow agora está rodando e escutando webhooks

### Passo 2: Obter URL do Webhook

1. Clique no nó **"Webhook RAG Query"**
2. No painel direito, em **"Webhook URLs"**:
   - **Production URL**: `http://localhost:5678/webhook/rag-query`
   - **Test URL**: `http://localhost:5678/webhook-test/rag-query`

### Passo 3: Testar Webhook (Production)

```bash
# Teste 1: Query básica
curl -X POST http://localhost:5678/webhook/rag-query \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "como funciona energia solar"
  }' | jq .
```

**Resultado Esperado**:
```json
{
  "success": true,
  "results": [
    {
      "rank": 1,
      "content": "A energia solar fotovoltaica converte luz solar...",
      "source": {
        "file": "energia_solar.md",
        "category": "servicos"
      },
      "similarity": 0.87,
      "relevance": "high"
    },
    // ... mais resultados
  ],
  "context": "TOP 3 RESULTADOS MAIS RELEVANTES:\n\n1. [Similarity: 87%]...",
  "metadata": {
    "query": "como funciona energia solar",
    "total_results": 5,
    "average_similarity": 0.82,
    "categories_found": ["servicos"],
    "files_found": ["energia_solar.md", "projetos_eletricos.md"]
  }
}
```

### Passo 4: Testar com Filtro de Categoria

```bash
# Teste 2: Com filtro de categoria
curl -X POST http://localhost:5678/webhook/rag-query \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "quanto custa instalação",
    "category": "servicos",
    "match_count": 10,
    "match_threshold": 0.70
  }' | jq .
```

### Passo 5: Testar Error Handling

```bash
# Teste 3: Sem query_text (deve retornar erro 400)
curl -X POST http://localhost:5678/webhook/rag-query \
  -H "Content-Type: application/json" \
  -d '{}' \
  -w "\nHTTP Status: %{http_code}\n"
```

**Resultado Esperado**:
```json
{
  "error": "query_text is required",
  "status": "error"
}
HTTP Status: 400
```

---

## 🐛 Debugging no n8n

### Modo Execução de Teste

1. No workflow, clique em **"Execute Workflow"** (botão superior)
2. Digite dados de teste no painel "Input Data":
```json
{
  "query_text": "energia solar residencial"
}
```
3. Clique em **"Execute Workflow"**
4. Veja execução passo a passo de cada nó
5. Verifique outputs intermediários

### Ver Execuções Anteriores

1. Menu lateral esquerdo: **"Executions"**
2. Lista de todas as execuções do workflow
3. Clique em uma execução para ver detalhes:
   - Input de cada nó
   - Output de cada nó
   - Tempo de execução
   - Erros (se houver)

### Logs em Tempo Real

```bash
# Ver logs do container n8n
docker-compose logs -f n8n

# Ver apenas erros
docker-compose logs n8n | grep -i error
```

---

## 🚀 Opção B: n8n Cloud

### Passo 1: Criar Conta n8n Cloud

1. Acesse: https://n8n.io/cloud
2. Clique em **"Start for free"**
3. Crie conta (email + senha)
4. Confirme email
5. Acesse dashboard: `https://XXXXX.app.n8n.cloud`

### Passo 2: Importar Workflow

**Mesmo processo da Opção A** (Passos 3-5):
- Workflows → Add workflow
- Import from File ou Clipboard
- Configurar credenciais OpenAI e PostgreSQL

**Webhook URL será diferente**:
- Production: `https://XXXXX.app.n8n.cloud/webhook/rag-query`

### Passo 3: Configurar PostgreSQL Cloud

**IMPORTANTE**: n8n Cloud pode ter restrições de conexão com Supabase

**Solução**: Usar **Supabase Connection Pooler** (recomendado)

1. Supabase Dashboard → Settings → Database
2. **Connection Pooler** → Copiar:
   ```
   Host: aws-0-us-east-1.pooler.supabase.com
   Database: postgres
   Port: 6543
   User: postgres.XXXXX
   Password: [sua_senha]
   ```
3. Usar essas credenciais no n8n Cloud

---

## 🚨 Troubleshooting

### Problema: "n8n is not accessible"

**Solução**:
```bash
# Verificar Docker está rodando
docker ps

# Se n8n não estiver rodando
docker-compose up -d

# Aguardar 30 segundos
sleep 30

# Verificar novamente
curl -s -o /dev/null -w "%{http_code}" http://localhost:5678/
# Deve retornar: 200 ou 302
```

### Problema: "OpenAI credential test failed"

**Causas Comuns**:
1. API key incorreta
2. API key sem créditos
3. Billing não configurado

**Solução**:
```bash
# Testar API key diretamente
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -s | jq -r '.data[0].id'

# Se falhar:
# 1. Verificar API key: https://platform.openai.com/api-keys
# 2. Configurar billing: https://platform.openai.com/account/billing
# 3. Gerar nova key se necessário
```

### Problema: "PostgreSQL connection failed"

**Causas Comuns**:
1. Usando SERVICE_KEY em vez de Database Password
2. SSL não habilitado
3. Host incorreto

**Solução**:
```
# Credenciais corretas para Supabase:
Host: XXXXXXXX.supabase.co (SEM https://)
Database: postgres
User: postgres
Password: [database_password] (NÃO é a SERVICE_KEY!)
Port: 5432
SSL: Enabled (checkbox marcado)
```

**Testar conexão diretamente**:
```bash
# Instalar psql se não tiver
sudo apt-get install postgresql-client

# Testar conexão
psql "postgresql://postgres:[PASSWORD]@XXXXXXXX.supabase.co:5432/postgres?sslmode=require"

# Se conectar: \q para sair
```

### Problema: Workflow retorna "No results found"

**Causas**:
1. Banco vazio (ingest não executado)
2. Similarity threshold muito alto
3. Query muito específica

**Solução**:
```bash
# 1. Verificar banco tem dados
curl -s "${SUPABASE_URL}/rest/v1/knowledge_documents?select=count" \
  -H "apikey: ${SUPABASE_SERVICE_KEY}" \
  | jq '.[0].count'

# Se retornar 0 → executar Etapa 3 (EXECUTE_INGEST.md)

# 2. Testar com threshold mais baixo
curl -X POST http://localhost:5678/webhook/rag-query \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "energia",
    "match_threshold": 0.5
  }' | jq .
```

### Problema: "embedding has wrong dimensions"

**Causa**: Usando modelo OpenAI errado ou embedding corrompido

**Solução**:
1. Verificar nó "Generate Embedding" está usando: `text-embedding-3-small`
2. Verificar dimensões: 1536
3. Re-executar workflow teste

### Problema: Webhook retorna 404

**Causas**:
1. Workflow não ativado
2. URL incorreta

**Solução**:
```bash
# 1. Verificar workflow está ativo (botão verde "Active")

# 2. Verificar URL webhook
# Clicar no nó "Webhook RAG Query" → copiar Production URL exata

# 3. Testar com URL completa
curl -X POST http://localhost:5678/webhook/rag-query \
  -H "Content-Type: application/json" \
  -d '{"query_text": "test"}' \
  -v
```

---

## 📊 Monitoramento e Performance

### Métricas de Performance

```bash
# Testar tempo de resposta
time curl -X POST http://localhost:5678/webhook/rag-query \
  -H "Content-Type: application/json" \
  -d '{"query_text": "energia solar"}' \
  -s -o /dev/null

# Esperado: < 2 segundos
```

### Execuções do Workflow

No n8n Dashboard:
1. Sidebar → **"Executions"**
2. Filtrar por: Status (Success/Error), Data, Tempo de execução
3. Métricas úteis:
   - **Execution Time**: Quanto tempo levou cada execução
   - **Success Rate**: % de execuções bem-sucedidas
   - **Error Patterns**: Erros mais comuns

### Logs Avançados

```bash
# Ver logs detalhados do n8n
docker-compose logs -f n8n

# Filtrar por webhook específico
docker-compose logs n8n | grep "rag-query"

# Filtrar apenas erros
docker-compose logs n8n | grep -i "error\|fail"
```

---

## 📝 Checklist Final de Import

Antes de prosseguir para Etapa 5 (Testes de Validação), confirme:

- [ ] ✅ n8n instalado e acessível (http://localhost:5678)
- [ ] ✅ Workflow `03_rag_knowledge_query.json` importado
- [ ] ✅ Credencial OpenAI configurada e testada
- [ ] ✅ Credencial PostgreSQL Supabase configurada e testada
- [ ] ✅ Workflow ativado (botão verde "Active")
- [ ] ✅ Webhook URL acessível
- [ ] ✅ Teste básico retorna resultados
- [ ] ✅ Teste com filtro funciona
- [ ] ✅ Error handling funciona (400 para input inválido)

**Status**: Se todos os checkboxes estão marcados, você está pronto para a **Etapa 5: Executar Testes de Validação**

---

**Próximo Documento**: `RUN_VALIDATION_TESTS.md` - Executar testes completos de validação

**Tempo Total Etapa 4**: 10-15 minutos
**Próxima Etapa**: 20-30 minutos
