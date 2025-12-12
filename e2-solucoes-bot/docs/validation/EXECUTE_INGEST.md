# Executar Script de Ingest - Sprint 1.1 Validation

**Objetivo**: Popular o banco de dados Supabase com embeddings da base de conhecimento

**Tempo Estimado**: 15-20 minutos (depende da API OpenAI)

**Pré-requisitos**:
- ✅ Etapa 1 (SETUP_CREDENTIALS.md) completa
- ✅ Etapa 2 (DEPLOY_SQL.md) completa
- ✅ Arquivo .env configurado com OPENAI_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_KEY
- ✅ Funções SQL deployadas no Supabase
- ✅ Extensão pgvector habilitada

---

## 📋 O que o Script Faz

O arquivo `scripts/ingest-knowledge.sh` (515 linhas) executa:

### 1. Validações Iniciais
- Verifica dependências: `curl`, `jq`
- Valida variáveis de ambiente obrigatórias
- Confirma existência do diretório `knowledge/`
- Testa conectividade com OpenAI e Supabase

### 2. Processamento de Arquivos
```bash
knowledge/
├── servicos/
│   ├── energia_solar.md          (264 linhas)
│   ├── subestacao.md
│   ├── projetos_eletricos.md     (351 linhas)
│   ├── armazenamento_energia.md  (351 linhas)
│   └── analise_laudos.md         (418 linhas)
```

**Total**: 5 arquivos | ~1.380 linhas

### 3. Text Chunking
- **Tamanho dos Chunks**: 500-1000 caracteres
- **Overlap**: 100 caracteres entre chunks
- **Estratégia**: Quebra em seções markdown (##) quando possível
- **Resultado Esperado**: ~50-100 chunks total

### 4. Embedding Generation
- **Modelo**: `text-embedding-3-small` (OpenAI)
- **Dimensões**: 1536
- **Custo Estimado**: ~$0.10 para ingest inicial
- **Retry Logic**: 3 tentativas com delay de 2s

### 5. Inserção no Supabase
- **Formato do ID**: `{category}/{filename}/chunk-{N}`
  - Exemplo: `servicos/energia_solar.md/chunk-1`
- **Tabela**: `knowledge_documents`
- **Campos**: id, content, embedding, category, source_file, metadata

---

## 🚀 Executar Script de Ingest

### Passo 1: Verificar Pré-requisitos

```bash
cd /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot

# 1. Verificar dependências
which curl && echo "✅ curl instalado"
which jq && echo "✅ jq instalado"

# Se jq não estiver instalado:
# Ubuntu/Debian
sudo apt-get install jq
# macOS
brew install jq

# 2. Verificar .env existe e está carregado
[ -f .env ] && echo "✅ .env existe" || echo "❌ .env não encontrado"

# 3. Carregar variáveis de ambiente
set -a
source .env
set +a

# 4. Verificar variáveis críticas
echo "OpenAI Key: ${OPENAI_API_KEY:0:20}..."
echo "Supabase URL: $SUPABASE_URL"
echo "Supabase Key: ${SUPABASE_SERVICE_KEY:0:20}..."

# 5. Verificar arquivos de conhecimento
ls -lh knowledge/servicos/*.md
```

**Resultado Esperado**:
```
✅ curl instalado
✅ jq instalado
✅ .env existe
OpenAI Key: sk-proj-XXXXXXXXXX...
Supabase URL: https://XXXXX.supabase.co
Supabase Key: eyJhbGciOiJIUzI1NiI...
-rw-r--r-- 1 user user  12K energia_solar.md
-rw-r--r-- 1 user user  11K subestacao.md
-rw-r--r-- 1 user user  16K projetos_eletricos.md
-rw-r--r-- 1 user user  15K armazenamento_energia.md
-rw-r--r-- 1 user user  18K analise_laudos.md
```

### Passo 2: Tornar Script Executável

```bash
# Verificar permissões atuais
ls -l scripts/ingest-knowledge.sh

# Adicionar permissão de execução
chmod +x scripts/ingest-knowledge.sh

# Verificar permissões atualizadas
ls -l scripts/ingest-knowledge.sh
# Deve mostrar: -rwxr-xr-x (com 'x' de executável)
```

### Passo 3: Executar Script (Dry Run - Recomendado)

```bash
# Dry run para validar sem inserir dados
./scripts/ingest-knowledge.sh --dry-run

# O script mostrará:
# - Arquivos a serem processados
# - Chunks que seriam gerados
# - Embeddings que seriam criados
# - NÃO inserirá no Supabase
```

**Saída Esperada (Dry Run)**:
```
[INFO] Iniciando ingest de conhecimento (DRY RUN)
[INFO] Validando dependências...
[SUCCESS] curl encontrado
[SUCCESS] jq encontrado
[INFO] Validando variáveis de ambiente...
[SUCCESS] OPENAI_API_KEY configurada
[SUCCESS] SUPABASE_URL configurada
[SUCCESS] SUPABASE_SERVICE_KEY configurada
[INFO] Testando conectividade OpenAI...
[SUCCESS] OpenAI API acessível
[INFO] Testando conectividade Supabase...
[SUCCESS] Supabase acessível
[INFO] Processando knowledge/servicos/energia_solar.md...
[INFO] Arquivo tem 264 linhas
[INFO] Gerando chunks (tamanho: 500-1000 chars, overlap: 100)...
[INFO] Gerados 12 chunks
[DRY RUN] Geraria embedding para chunk 1/12
[DRY RUN] Geraria embedding para chunk 2/12
...
[DRY RUN] Inseriria chunk servicos/energia_solar.md/chunk-1 no Supabase
...
[INFO] Processamento completo (DRY RUN)
[INFO] Total: 5 arquivos, ~50 chunks processados
```

### Passo 4: Executar Script (Produção)

```bash
# Execução real com inserção no Supabase
./scripts/ingest-knowledge.sh

# OU com logging detalhado
./scripts/ingest-knowledge.sh --verbose

# Aguardar processamento (15-20 minutos)
# O script exibirá progresso em tempo real
```

**Saída Esperada (Produção)**:
```
[INFO] Iniciando ingest de conhecimento
[INFO] Validando dependências...
[SUCCESS] curl encontrado
[SUCCESS] jq encontrado
[INFO] Validando variáveis de ambiente...
[SUCCESS] Todas as variáveis configuradas
[INFO] Testando conectividade...
[SUCCESS] OpenAI e Supabase acessíveis
[INFO] Processando knowledge/servicos/energia_solar.md...
[INFO] Gerando chunks...
[SUCCESS] 12 chunks gerados
[INFO] Gerando embedding para chunk 1/12...
[SUCCESS] Embedding gerado (1536 dimensões)
[INFO] Inserindo chunk servicos/energia_solar.md/chunk-1 no Supabase...
[SUCCESS] Chunk inserido
[INFO] Gerando embedding para chunk 2/12...
[SUCCESS] Embedding gerado
[INFO] Inserindo chunk servicos/energia_solar.md/chunk-2 no Supabase...
[SUCCESS] Chunk inserido
...
[INFO] Arquivo energia_solar.md completo (12/12 chunks)
[INFO] Processando knowledge/servicos/subestacao.md...
...
[SUCCESS] Ingest completo!
[INFO] Resumo:
[INFO] - Arquivos processados: 5
[INFO] - Total de chunks: 53
[INFO] - Embeddings gerados: 53
[INFO] - Inserções no Supabase: 53
[INFO] - Falhas: 0
[INFO] - Tempo total: 18m 32s
```

### Passo 5: Monitorar Progresso

**Em outro terminal**, você pode monitorar o progresso em tempo real:

```bash
# Terminal 2: Monitorar quantidade de documentos no Supabase
cd /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot

# Carregar .env
set -a; source .env; set +a

# Loop de monitoramento
watch -n 10 "curl -s ${SUPABASE_URL}/rest/v1/knowledge_documents?select=count \
  -H 'apikey: ${SUPABASE_SERVICE_KEY}' \
  -H 'Authorization: Bearer ${SUPABASE_SERVICE_KEY}' \
  | jq '.[0].count'"

# Atualiza a cada 10 segundos mostrando quantidade de chunks inseridos
```

---

## ✅ Validação do Ingest

### Teste 1: Verificar Quantidade de Documentos

```bash
# Via curl
curl -s "${SUPABASE_URL}/rest/v1/knowledge_documents?select=count" \
  -H "apikey: ${SUPABASE_SERVICE_KEY}" \
  -H "Authorization: Bearer ${SUPABASE_SERVICE_KEY}" \
  | jq '.[0].count'

# Via Supabase Dashboard SQL Editor
SELECT COUNT(*) as total FROM knowledge_documents;
```

**Resultado Esperado**: Entre 50-100 documentos (depende do chunking exato)

### Teste 2: Verificar Distribuição por Categoria

```bash
# Via SQL
SELECT * FROM get_category_stats();

# OU via curl
curl -s "${SUPABASE_URL}/rest/v1/rpc/get_category_stats" \
  -H "apikey: ${SUPABASE_SERVICE_KEY}" \
  -H "Authorization: Bearer ${SUPABASE_SERVICE_KEY}" \
  -H "Content-Type: application/json" \
  | jq .
```

**Resultado Esperado**:
```json
[
  {
    "category": "servicos",
    "document_count": 53,
    "avg_content_length": 750
  }
]
```

### Teste 3: Verificar Distribuição por Arquivo

```sql
SELECT
    source_file,
    COUNT(*) as chunks,
    AVG(LENGTH(content)) as avg_length
FROM knowledge_documents
GROUP BY source_file
ORDER BY chunks DESC;
```

**Resultado Esperado**:
```
source_file                      | chunks | avg_length
---------------------------------+--------+-----------
analise_laudos.md                | 14     | 820
armazenamento_energia.md         | 12     | 780
projetos_eletricos.md            | 11     | 760
energia_solar.md                 | 10     | 740
subestacao.md                    | 6      | 690
```

### Teste 4: Verificar Embeddings Válidos

```sql
-- Verificar que todos os embeddings foram gerados
SELECT COUNT(*) as total_docs FROM knowledge_documents;
SELECT COUNT(*) as docs_with_embedding FROM knowledge_documents WHERE embedding IS NOT NULL;

-- Devem ser iguais
```

**Resultado Esperado**: Ambos devem retornar o mesmo número (ex: 53)

### Teste 5: Verificar Dimensões dos Embeddings

```sql
SELECT
    id,
    vector_dims(embedding) as dimensions
FROM knowledge_documents
LIMIT 5;
```

**Resultado Esperado**: Todas as linhas devem ter `dimensions = 1536`

### Teste 6: Testar Função match_documents()

```sql
-- Testar busca semântica com embedding de um chunk existente
SELECT
    id,
    content,
    similarity
FROM match_documents(
    (SELECT embedding FROM knowledge_documents LIMIT 1),
    0.75,
    5,
    NULL
);
```

**Resultado Esperado**:
- 5 resultados (ou menos se similarity < 0.75)
- Cada resultado com id, content, similarity
- Similarity entre 0.75 e 1.0

### Teste 7: Verificar Metadata

```sql
SELECT
    id,
    category,
    source_file,
    metadata,
    created_at
FROM knowledge_documents
LIMIT 5;
```

**Resultado Esperado**:
- `category`: "servicos"
- `source_file`: nome do arquivo .md
- `metadata`: JSONB (pode estar vazio `{}`)
- `created_at`: timestamp recente

### Teste 8: Estatísticas Gerais

```sql
SELECT * FROM get_documents_stats();
```

**Resultado Esperado**:
```json
{
  "total_documents": 53,
  "total_categories": 1,
  "avg_content_length": 760,
  "total_storage_mb": 0.45
}
```

---

## 🔄 Re-Ingest (Atualizar Conhecimento)

### Cenário 1: Re-ingest de Arquivo Específico

```bash
# Se você editou um arquivo específico (ex: energia_solar.md)

# 1. Deletar chunks antigos
curl -X POST "${SUPABASE_URL}/rest/v1/rpc/delete_documents_by_source" \
  -H "apikey: ${SUPABASE_SERVICE_KEY}" \
  -H "Authorization: Bearer ${SUPABASE_SERVICE_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"source_file": "energia_solar.md"}'

# 2. Re-executar ingest apenas desse arquivo
./scripts/ingest-knowledge.sh --file knowledge/servicos/energia_solar.md
```

### Cenário 2: Re-ingest Completo (Todos os Arquivos)

```bash
# 1. Deletar todos os documentos
curl -X POST "${SUPABASE_URL}/rest/v1/rpc/delete_documents_by_category" \
  -H "apikey: ${SUPABASE_SERVICE_KEY}" \
  -H "Authorization: Bearer ${SUPABASE_SERVICE_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"category": "servicos"}'

# 2. Re-executar ingest completo
./scripts/ingest-knowledge.sh --force
```

### Cenário 3: Ingest Incremental (Novos Arquivos)

```bash
# Adicione novos arquivos em knowledge/servicos/

# Execute ingest normalmente (script detecta chunks novos)
./scripts/ingest-knowledge.sh

# Script pula chunks que já existem no banco
```

---

## 🚨 Troubleshooting

### Problema: "curl: command not found"

**Solução**:
```bash
# Ubuntu/Debian
sudo apt-get install curl

# macOS (curl já vem instalado, mas se necessário)
brew install curl
```

### Problema: "jq: command not found"

**Solução**:
```bash
# Ubuntu/Debian
sudo apt-get install jq

# macOS
brew install jq

# Verificar instalação
jq --version
```

### Problema: "OPENAI_API_KEY não configurada"

**Solução**:
```bash
# 1. Verificar .env
cat .env | grep OPENAI_API_KEY

# 2. Se estiver vazia ou incorreta, editar
nano .env
# Adicionar: OPENAI_API_KEY=sk-proj-XXXXXXXXXX

# 3. Recarregar .env
set -a; source .env; set +a

# 4. Verificar variável
echo $OPENAI_API_KEY
```

### Problema: OpenAI API retorna erro 401 (Unauthorized)

**Causa**: API key inválida ou sem créditos

**Solução**:
```bash
# Testar API key diretamente
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -s | jq -r '.data[0].id'

# Se retornar erro:
# 1. Verificar API key está correta
# 2. Verificar billing: https://platform.openai.com/account/billing
# 3. Adicionar crédito se necessário ($5 mínimo)
```

### Problema: OpenAI API retorna erro 429 (Rate Limit)

**Causa**: Muitas requisições simultâneas

**Solução**: O script tem retry logic automático (3 tentativas com delay 2s). Aguarde finalização.

**Se persistir**:
```bash
# Executar com delay maior entre requisições
./scripts/ingest-knowledge.sh --delay 5  # 5 segundos entre embeddings
```

### Problema: Supabase connection failed

**Solução**:
```bash
# 1. Verificar URL e Key
echo "URL: $SUPABASE_URL"
echo "Key: ${SUPABASE_SERVICE_KEY:0:20}..."

# 2. Testar conectividade
curl -s "${SUPABASE_URL}/rest/v1/" \
  -H "apikey: ${SUPABASE_SERVICE_KEY}" \
  | jq '.'

# 3. Se falhar:
# - Verificar SUPABASE_URL não tem / no final
# - Confirmar está usando SERVICE_KEY (não ANON_KEY)
# - Verificar projeto Supabase está ativo (não pausado)
```

### Problema: Script trava em "Gerando embedding..."

**Causa**: Timeout na API OpenAI

**Solução**:
```bash
# 1. Cancelar script: Ctrl+C

# 2. Verificar logs OpenAI
# Dashboard: https://platform.openai.com/account/usage

# 3. Re-executar (script pula chunks já inseridos)
./scripts/ingest-knowledge.sh
```

### Problema: Embeddings NULL no banco

**Causa**: Falha na geração de embeddings ou erro na inserção

**Solução**:
```sql
-- 1. Identificar chunks sem embedding
SELECT id, content
FROM knowledge_documents
WHERE embedding IS NULL;

-- 2. Deletar chunks problemáticos
DELETE FROM knowledge_documents WHERE embedding IS NULL;

-- 3. Re-executar ingest
```

### Problema: "duplicate key value violates unique constraint"

**Causa**: Tentando inserir chunk que já existe

**Solução**:
```bash
# Opção 1: Usar --force para re-ingest completo
./scripts/ingest-knowledge.sh --force

# Opção 2: Deletar duplicatas manualmente
# SQL Editor do Supabase:
DELETE FROM knowledge_documents
WHERE id IN (
    SELECT id FROM knowledge_documents
    GROUP BY id
    HAVING COUNT(*) > 1
);
```

---

## 📊 Métricas de Sucesso

### Custo OpenAI

```bash
# Calcular custo aproximado
# text-embedding-3-small: $0.00002 / 1K tokens

# Estimativa para 1.380 linhas (~50K tokens):
# 50K tokens × $0.00002 = $0.10

# Verificar uso real:
# https://platform.openai.com/account/usage
```

### Tempo de Execução

**Esperado**: 15-20 minutos para 5 arquivos (53 chunks)

**Cálculo**:
- Chunking: ~1 minuto
- Embedding generation: ~10-15 minutos (depende da API OpenAI)
- Inserção Supabase: ~2-3 minutos
- **Total**: 13-19 minutos + overhead

### Taxa de Sucesso

**Alvo**: 100% de chunks inseridos com embeddings válidos

```sql
-- Verificar taxa de sucesso
SELECT
    COUNT(*) as total_chunks,
    SUM(CASE WHEN embedding IS NOT NULL THEN 1 ELSE 0 END) as successful,
    ROUND(100.0 * SUM(CASE WHEN embedding IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 2) as success_rate
FROM knowledge_documents;
```

**Resultado Esperado**: `success_rate = 100.00`

---

## 📝 Checklist Final de Ingest

Antes de prosseguir para Etapa 4 (Importar Workflow n8n), confirme:

- [ ] ✅ Script executou sem erros
- [ ] ✅ Total de documentos no banco: 50-100 chunks
- [ ] ✅ 5 arquivos fonte processados
- [ ] ✅ Todos os embeddings são NOT NULL
- [ ] ✅ Dimensões dos embeddings: 1536
- [ ] ✅ Função match_documents() retorna resultados
- [ ] ✅ Estatísticas por categoria corretas
- [ ] ✅ Estatísticas por arquivo corretas
- [ ] ✅ Taxa de sucesso: 100%

**Status**: Se todos os checkboxes estão marcados, você está pronto para a **Etapa 4: Importar Workflow n8n**

---

**Próximo Documento**: `IMPORT_N8N_WORKFLOW.md` - Importar workflow RAG no n8n

**Tempo Total Etapa 3**: 15-20 minutos
**Próxima Etapa**: 10-15 minutos
