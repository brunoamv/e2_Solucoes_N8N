# Deploy de Funções SQL - Sprint 1.1 Validation

**Objetivo**: Fazer deploy das funções SQL do sistema RAG no Supabase

**Tempo Estimado**: 10-15 minutos

**Pré-requisitos**:
- ✅ Etapa 1 (SETUP_CREDENTIALS.md) completa
- ✅ Arquivo .env configurado com SUPABASE_URL e SUPABASE_SERVICE_KEY
- ✅ Projeto Supabase criado e ativo
- ✅ Extensão pgvector habilitada no Supabase

---

## 📋 O que Será Deployado

O arquivo `database/supabase_functions.sql` contém:

### 1. Tabela `knowledge_documents`
```sql
CREATE TABLE knowledge_documents (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    embedding vector(1536),
    category VARCHAR(50),
    source_file VARCHAR(255),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
```

**Propósito**: Armazenar chunks de conhecimento com seus embeddings vetoriais

### 2. Índices de Performance
```sql
-- Índice ivfflat para vector search (ANN - Approximate Nearest Neighbor)
CREATE INDEX knowledge_documents_embedding_idx
ON knowledge_documents
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Índices B-tree para filtros comuns
CREATE INDEX idx_knowledge_documents_category ON knowledge_documents(category);
CREATE INDEX idx_knowledge_documents_source ON knowledge_documents(source_file);

-- Índice GIN para metadata JSONB
CREATE INDEX idx_knowledge_documents_metadata ON knowledge_documents USING GIN (metadata);
```

**Propósito**: Otimizar queries de vector similarity e filtros

### 3. Função Principal `match_documents()`
```sql
CREATE OR REPLACE FUNCTION match_documents(
    query_embedding vector(1536),
    match_threshold FLOAT DEFAULT 0.75,
    match_count INT DEFAULT 5,
    filter_category VARCHAR DEFAULT NULL
)
RETURNS TABLE (
    id TEXT,
    content TEXT,
    category VARCHAR,
    source_file VARCHAR,
    metadata JSONB,
    similarity FLOAT
)
```

**Propósito**: Buscar documentos similares usando cosine distance

### 4. Funções de Utilidade
- `delete_documents_by_category(category VARCHAR)` - Re-ingest por categoria
- `delete_documents_by_source(source_file VARCHAR)` - Atualizar arquivo específico
- `get_documents_stats()` - Estatísticas gerais do banco
- `get_category_stats()` - Estatísticas por categoria

### 5. Trigger de Timestamp
```sql
CREATE TRIGGER update_knowledge_documents_timestamp
    BEFORE UPDATE ON knowledge_documents
    FOR EACH ROW
    EXECUTE FUNCTION update_documents_timestamp();
```

**Propósito**: Atualizar automaticamente `updated_at` em modificações

---

## 🚀 Opção A: Deploy via Supabase Dashboard (Recomendado)

**Vantagens**: Interface visual, validação automática, fácil debugging

### Passo a Passo

#### 1. Acessar SQL Editor

```bash
# Acesse seu projeto Supabase
# URL: https://supabase.com/dashboard/project/SEU_PROJECT_ID
```

1. No painel do Supabase, vá em: **SQL Editor** (ícone </> no menu lateral)
2. Clique em **+ New query**

#### 2. Copiar SQL do Projeto

```bash
# No seu terminal local
cd /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot

# Exibir conteúdo do arquivo SQL
cat database/supabase_functions.sql
```

Copie TODO o conteúdo do arquivo `database/supabase_functions.sql`

#### 3. Colar e Executar no SQL Editor

1. Cole o SQL completo no editor
2. Dê um nome à query: **"Sprint 1.1 - RAG Functions"**
3. Clique em **Run** (ou Ctrl+Enter)
4. **Aguarde confirmação**: Deve aparecer "Success. No rows returned"

#### 4. Verificar Deployment

Execute estas queries de validação no SQL Editor:

**Teste 1: Verificar Tabela Criada**
```sql
SELECT
    table_name,
    column_name,
    data_type
FROM information_schema.columns
WHERE table_name = 'knowledge_documents'
ORDER BY ordinal_position;
```

**Resultado Esperado**: 8 colunas (id, content, embedding, category, source_file, metadata, created_at, updated_at)

**Teste 2: Verificar Índices**
```sql
SELECT
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'knowledge_documents';
```

**Resultado Esperado**: 4 índices (primary key + embedding_idx + category + source + metadata)

**Teste 3: Verificar Funções**
```sql
SELECT
    routine_name,
    routine_type
FROM information_schema.routines
WHERE routine_schema = 'public'
AND routine_name IN (
    'match_documents',
    'delete_documents_by_category',
    'delete_documents_by_source',
    'get_documents_stats',
    'get_category_stats'
);
```

**Resultado Esperado**: 5 funções listadas

**Teste 4: Verificar Trigger**
```sql
SELECT
    trigger_name,
    event_manipulation,
    event_object_table
FROM information_schema.triggers
WHERE trigger_name = 'update_knowledge_documents_timestamp';
```

**Resultado Esperado**: 1 trigger (BEFORE UPDATE na tabela knowledge_documents)

**Teste 5: Testar Inserção**
```sql
-- Inserir documento de teste
INSERT INTO knowledge_documents (id, content, category, source_file)
VALUES ('test/sample/chunk-1', 'Documento de teste para validação do sistema RAG.', 'test', 'test.md');

-- Verificar inserção
SELECT * FROM knowledge_documents WHERE id = 'test/sample/chunk-1';

-- Limpar teste
DELETE FROM knowledge_documents WHERE id = 'test/sample/chunk-1';
```

**Resultado Esperado**: Insert OK, Select retorna 1 linha, Delete OK

---

## 🖥️ Opção B: Deploy via Supabase CLI

**Vantagens**: Automação, versionamento, integração CI/CD

### Pré-requisitos

```bash
# 1. Instalar Supabase CLI (se ainda não tiver)
# macOS
brew install supabase/tap/supabase

# Linux
brew install supabase/tap/supabase
# OU
curl -sL https://github.com/supabase/cli/releases/download/v1.142.2/supabase_1.142.2_linux_amd64.tar.gz | tar xz
sudo mv supabase /usr/local/bin/

# 2. Verificar instalação
supabase --version
```

### Deploy via CLI

#### 1. Fazer Login no Supabase

```bash
# Login interativo
supabase login

# Ou usar access token
supabase login --token YOUR_ACCESS_TOKEN
```

**Como obter access token**:
1. Acesse: https://supabase.com/dashboard/account/tokens
2. Clique em "Generate new token"
3. Dê um nome: "CLI Deploy"
4. Copie o token

#### 2. Vincular ao Projeto

```bash
cd /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot

# Vincular ao projeto Supabase
supabase link --project-ref SEU_PROJECT_REF

# Encontrar project-ref:
# URL do projeto: https://supabase.com/dashboard/project/abcdefghijklmnop
# project-ref = abcdefghijklmnop
```

#### 3. Executar SQL

```bash
# Executar arquivo SQL diretamente
supabase db push database/supabase_functions.sql

# OU usar psql
supabase db reset --db-url "$SUPABASE_URL" -f database/supabase_functions.sql
```

#### 4. Verificar via CLI

```bash
# Listar tabelas
supabase db dump --schema public

# Testar função match_documents
supabase db execute "SELECT routine_name FROM information_schema.routines WHERE routine_name = 'match_documents';"
```

---

## 🐳 Opção C: Deploy via Supabase Local (Desenvolvimento)

**Uso**: Desenvolvimento e testes locais antes de deploy em produção

### Setup Local

```bash
cd /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot

# Inicializar Supabase local (se ainda não fez)
supabase init

# Iniciar containers Docker
supabase start

# Aguardar ~30 segundos para inicialização
# Supabase exibirá credenciais locais:
# API URL: http://localhost:54321
# DB URL: postgresql://postgres:postgres@localhost:54322/postgres
# Studio URL: http://localhost:54323
```

### Executar SQL Localmente

```bash
# Opção 1: Via CLI
supabase db reset -f database/supabase_functions.sql

# Opção 2: Via psql
psql postgresql://postgres:postgres@localhost:54322/postgres -f database/supabase_functions.sql

# Opção 3: Via Supabase Studio (UI)
# Acessar http://localhost:54323
# SQL Editor → New query → Colar SQL → Run
```

### Validar Local

```bash
# Conectar ao banco local
psql postgresql://postgres:postgres@localhost:54322/postgres

# Executar testes (mesmos da Opção A)
SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'knowledge_documents';
# Deve retornar: 1

\q  # Sair do psql
```

---

## ✅ Validação Completa do Deploy

### Checklist de Validação

Execute este script de validação completo:

```bash
# Salvar como: scripts/validate-sql-deploy.sh
cd /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot

# Carregar variáveis de ambiente
set -a
source .env
set +a

# Função de teste
test_sql() {
    local test_name=$1
    local sql_query=$2

    echo "🧪 Teste: $test_name"

    result=$(curl -s "${SUPABASE_URL}/rest/v1/rpc/execute_sql" \
        -H "apikey: ${SUPABASE_SERVICE_KEY}" \
        -H "Authorization: Bearer ${SUPABASE_SERVICE_KEY}" \
        -H "Content-Type: application/json" \
        -d "{\"query\": \"$sql_query\"}")

    if [ $? -eq 0 ]; then
        echo "✅ $test_name: PASSOU"
        return 0
    else
        echo "❌ $test_name: FALHOU"
        echo "   Erro: $result"
        return 1
    fi
}

# Executar testes
echo "🔍 Validando Deploy SQL..."
echo ""

# Teste 1: Tabela existe
test_sql "Tabela knowledge_documents" \
    "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'knowledge_documents'"

# Teste 2: Função match_documents existe
test_sql "Função match_documents" \
    "SELECT COUNT(*) FROM information_schema.routines WHERE routine_name = 'match_documents'"

# Teste 3: Índice ivfflat existe
test_sql "Índice vector search" \
    "SELECT COUNT(*) FROM pg_indexes WHERE tablename = 'knowledge_documents' AND indexname LIKE '%embedding%'"

# Teste 4: Funções de utilidade
test_sql "Funções de utilidade" \
    "SELECT COUNT(*) FROM information_schema.routines WHERE routine_name IN ('get_documents_stats', 'get_category_stats')"

echo ""
echo "✅ Validação de Deploy SQL Completa!"
```

### Executar Validação

```bash
chmod +x scripts/validate-sql-deploy.sh
./scripts/validate-sql-deploy.sh
```

**Resultado Esperado**:
```
🔍 Validando Deploy SQL...

🧪 Teste: Tabela knowledge_documents
✅ Tabela knowledge_documents: PASSOU

🧪 Teste: Função match_documents
✅ Função match_documents: PASSOU

🧪 Teste: Índice vector search
✅ Índice vector search: PASSOU

🧪 Teste: Funções de utilidade
✅ Funções de utilidade: PASSOU

✅ Validação de Deploy SQL Completa!
```

---

## 🚨 Troubleshooting

### Problema: "extension vector does not exist"

**Causa**: Extensão pgvector não habilitada

**Solução**:
```sql
-- Via Supabase Dashboard SQL Editor
CREATE EXTENSION IF NOT EXISTS vector;

-- Verificar
SELECT * FROM pg_extension WHERE extname = 'vector';
```

### Problema: "permission denied for schema public"

**Causa**: Permissões insuficientes (usando anon key em vez de service_role)

**Solução**:
1. Verifique se está usando `SUPABASE_SERVICE_KEY` (não `SUPABASE_ANON_KEY`)
2. Confirme que service_role key está correta no .env
3. Re-execute com credenciais corretas

### Problema: "index method 'ivfflat' does not exist"

**Causa**: Extensão pgvector não instalada corretamente

**Solução**:
```bash
# Via Supabase Dashboard
# Database → Extensions → Procurar "vector" → Enable

# OU via SQL
CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public;
```

### Problema: "function match_documents already exists"

**Causa**: Tentando criar função que já existe

**Solução**:
```sql
-- Opção 1: Drop e recriar
DROP FUNCTION IF EXISTS match_documents CASCADE;

-- Depois re-execute o SQL completo

-- Opção 2: Usar CREATE OR REPLACE (já está no SQL)
-- Simplesmente re-execute o arquivo supabase_functions.sql
```

### Problema: Deploy via CLI falha com "connection refused"

**Causa**: Supabase local não está rodando ou credenciais cloud incorretas

**Solução Local**:
```bash
# Verificar status
supabase status

# Se não estiver rodando
supabase start

# Aguardar ~30 segundos
```

**Solução Cloud**:
```bash
# Verificar projeto vinculado
supabase projects list

# Re-vincular se necessário
supabase link --project-ref SEU_PROJECT_REF
```

### Problema: Índice ivfflat lento ou não usado

**Causa**: Tabela vazia ou sem VACUUM/ANALYZE após inserções

**Solução**:
```sql
-- Após popular a tabela com dados
VACUUM ANALYZE knowledge_documents;

-- Verificar uso do índice
EXPLAIN ANALYZE
SELECT * FROM match_documents(
    (SELECT embedding FROM knowledge_documents LIMIT 1),
    0.75, 5, NULL
);

-- Deve mostrar: "Index Scan using knowledge_documents_embedding_idx"
```

---

## 📊 Verificação de Performance

### Teste de Performance do Índice

```sql
-- Criar dados de teste (após ingest real)
EXPLAIN ANALYZE
SELECT
    id,
    content,
    1 - (embedding <=> (SELECT embedding FROM knowledge_documents LIMIT 1)) AS similarity
FROM knowledge_documents
WHERE 1 - (embedding <=> (SELECT embedding FROM knowledge_documents LIMIT 1)) > 0.75
ORDER BY similarity DESC
LIMIT 5;
```

**Métricas Esperadas**:
- **Planning Time**: < 5ms
- **Execution Time**: < 500ms (com ~100 chunks)
- **Index Scan**: Deve aparecer no query plan
- **Rows Scanned**: Deve ser << total de rows (prova de uso do índice)

### Monitorar Uso de Índices

```sql
-- Verificar estatísticas de uso de índices
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes
WHERE tablename = 'knowledge_documents';
```

---

## 📝 Checklist Final de Deploy

Antes de prosseguir para Etapa 3 (Ingest), confirme:

- [ ] ✅ SQL executado sem erros no Supabase
- [ ] ✅ Tabela `knowledge_documents` criada com 8 colunas
- [ ] ✅ 4 índices criados (primary key + embedding + category + source + metadata)
- [ ] ✅ Função `match_documents()` disponível
- [ ] ✅ 4 funções de utilidade criadas
- [ ] ✅ Trigger `update_knowledge_documents_timestamp` ativo
- [ ] ✅ Extensão `vector` habilitada
- [ ] ✅ Teste de inserção funcionou
- [ ] ✅ Script de validação passou todos os testes

**Status**: Se todos os checkboxes estão marcados, você está pronto para a **Etapa 3: Executar Script de Ingest**

---

## 🔐 Segurança

**IMPORTANTE**:

1. ✅ **Service Role Key**: Só usar em backend/scripts, NUNCA expor no frontend
2. ✅ **Row Level Security (RLS)**: Para produção, habilitar RLS:
   ```sql
   ALTER TABLE knowledge_documents ENABLE ROW LEVEL SECURITY;

   -- Política exemplo: Leitura pública, escrita apenas service_role
   CREATE POLICY "Leitura pública"
   ON knowledge_documents FOR SELECT
   TO anon, authenticated
   USING (true);
   ```
3. ✅ **Backup**: Supabase faz backup automático, mas considere exports periódicos
4. ✅ **Auditoria**: Habilitar pgAudit se necessário para compliance

---

**Próximo Documento**: `EXECUTE_INGEST.md` - Executar script de ingestão de conhecimento

**Tempo Total Etapa 2**: 10-15 minutos
**Próxima Etapa**: 15-20 minutos
