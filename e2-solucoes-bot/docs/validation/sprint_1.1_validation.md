# Sprint 1.1 Validation Report

**Sprint**: RAG e Base de Conhecimento
**Data**: 2025-01-12
**Status**: EM VALIDAÇÃO
**Objetivo**: Bot responde perguntas sobre TODOS os 5 serviços com RAG funcional

---

## 📋 Checklist de Validação

### 1. Base de Conhecimento (5 arquivos) ✅

- [x] `knowledge/servicos/energia_solar.md` - 264 linhas
- [x] `knowledge/servicos/subestacao.md` - Verificado
- [x] `knowledge/servicos/projetos_eletricos.md` - 351 linhas
- [x] `knowledge/servicos/armazenamento_energia.md` - 351 linhas
- [x] `knowledge/servicos/analise_laudos.md` - 418 linhas

**Total**: 1380+ linhas de conhecimento estruturado

### 2. Script de Ingestão ✅

- [x] `scripts/ingest-knowledge.sh` criado (515 linhas)
- [x] Script executável (`chmod +x`)
- [x] Validações implementadas:
  - [x] Dependências (curl, jq)
  - [x] Variáveis de ambiente (OPENAI_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_KEY)
  - [x] Diretório knowledge/ existe
- [x] Chunking inteligente (500-1000 chars, overlap 100 chars)
- [x] Respeita estrutura markdown (quebra em ##)
- [x] Retry logic (3 tentativas, delay 2s)
- [x] Logging colorido (INFO/SUCCESS/WARNING/ERROR)

### 3. Funções Supabase ✅

- [x] `database/supabase_functions.sql` atualizado
- [x] Tabela `knowledge_documents` com schema correto:
  - [x] id TEXT (formato: category/filename/chunk-N)
  - [x] content TEXT
  - [x] embedding vector(1536)
  - [x] category VARCHAR(50)
  - [x] source_file VARCHAR(255)
  - [x] metadata JSONB
  - [x] timestamps (created_at, updated_at)
- [x] Índices otimizados:
  - [x] ivfflat para vector search (lists=100)
  - [x] category index
  - [x] source_file index
  - [x] metadata GIN index
- [x] Função `match_documents()` implementada:
  - [x] Parâmetros: query_embedding, match_threshold (0.75), match_count (5), filter_category
  - [x] Retorna: id, content, category, source_file, metadata, similarity
  - [x] Usa cosine distance (<=>)
- [x] Funções de utilidade:
  - [x] delete_documents_by_category()
  - [x] delete_documents_by_source()
  - [x] get_documents_stats()
  - [x] get_category_stats()
- [x] Trigger de updated_at
- [x] Comentários e queries de teste

### 4. Workflow n8n RAG ✅

- [x] `n8n/workflows/03_rag_knowledge_query.json` criado (232 linhas)
- [x] Estrutura com 7 nós:
  1. [x] Webhook RAG Query (POST /webhook/rag-query)
  2. [x] Validate Input (verifica query_text)
  3. [x] Error Missing Query (resposta 400)
  4. [x] Generate Embedding (OpenAI text-embedding-3-small)
  5. [x] Query Supabase (match_documents com casting vector)
  6. [x] Format Results for AI (JavaScript formata contexto)
  7. [x] Respond Success (200 com JSON estruturado)
- [x] Conexões corretas entre nós
- [x] Parâmetros opcionais: category, match_threshold, match_count
- [x] Response estruturado:
  - [x] success boolean
  - [x] results array (rank, content, source, similarity, relevance)
  - [x] context string (top 3 resultados formatados para AI)
  - [x] metadata (query, total_results, avg_similarity, categories_found, files_found)

---

## 🧪 Testes de Validação

### Teste 1: Executar Ingest Script

**Comando**:
```bash
cd /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot
./scripts/ingest-knowledge.sh
```

**Validações**:
- [ ] Script executa sem erros
- [ ] Processa 5 arquivos .md
- [ ] Gera chunks (estimativa: 50-100 chunks total)
- [ ] Conecta com OpenAI API
- [ ] Gera embeddings (1536 dimensões cada)
- [ ] Insere em Supabase knowledge_documents
- [ ] Logs mostram progresso
- [ ] Tempo de execução: < 5 minutos

**Resultado**: PENDENTE

---

### Teste 2: Verificar Dados no Supabase

**Query SQL**:
```sql
-- Total de documentos
SELECT COUNT(*) as total FROM knowledge_documents;

-- Por categoria
SELECT * FROM get_category_stats();

-- Por arquivo fonte
SELECT source_file, COUNT(*) as chunks
FROM knowledge_documents
GROUP BY source_file
ORDER BY chunks DESC;

-- Estatísticas gerais
SELECT * FROM get_documents_stats();
```

**Validações**:
- [ ] Total de chunks >= 50
- [ ] 5 categorias "servicos" presentes
- [ ] 5 arquivos fonte presentes
- [ ] Todos os embeddings não são NULL
- [ ] avg_content_length razoável (500-1000 chars)

**Resultado**: PENDENTE

---

### Teste 3: Importar Workflow n8n

**Passos**:
1. Acessar n8n (http://localhost:5678)
2. Workflows → Import from File
3. Selecionar `n8n/workflows/03_rag_knowledge_query.json`
4. Configurar credenciais:
   - OpenAI API (id: openai-embeddings)
   - PostgreSQL Supabase (id: supabase-postgres)
5. Ativar workflow

**Validações**:
- [ ] Workflow importado sem erros
- [ ] Todos os nós visíveis e conectados
- [ ] Credenciais configuradas
- [ ] Webhook URL disponível

**Resultado**: PENDENTE

---

### Teste 4: Query RAG - "como funciona energia solar"

**Request**:
```bash
curl -X POST http://localhost:5678/webhook/rag-query \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "como funciona energia solar"
  }'
```

**Validações**:
- [ ] Response HTTP 200
- [ ] success: true
- [ ] results array com 3-5 itens
- [ ] Cada result tem: rank, content, source, similarity, relevance
- [ ] source.file contém "energia_solar.md"
- [ ] source.category = "servicos"
- [ ] similarity >= 0.75 (75%)
- [ ] relevance = "high" ou "medium"
- [ ] context string formatado para AI
- [ ] metadata.total_results >= 3
- [ ] metadata.average_similarity >= 0.75

**Resultado**: PENDENTE

---

### Teste 5: Query RAG - Com Filtro de Categoria

**Request**:
```bash
curl -X POST http://localhost:5678/webhook/rag-query \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "quanto custa",
    "category": "servicos",
    "match_count": 10
  }'
```

**Validações**:
- [ ] Retorna até 10 resultados
- [ ] Todos de category "servicos"
- [ ] Busca em múltiplos arquivos
- [ ] metadata.category_filter = "servicos"

**Resultado**: PENDENTE

---

### Teste 6: Query RAG - Cada Serviço

**Queries de Teste**:
1. "energia solar residencial" → deve retornar chunks de energia_solar.md
2. "subestação transformador" → deve retornar chunks de subestacao.md
3. "projeto elétrico residencial" → deve retornar chunks de projetos_eletricos.md
4. "bateria lítio armazenamento" → deve retornar chunks de armazenamento_energia.md
5. "análise de consumo energético" → deve retornar chunks de analise_laudos.md

**Validações**:
- [ ] Todos os 5 serviços retornam resultados relevantes
- [ ] Similarity score adequado (>= 0.75)
- [ ] Context string útil para AI

**Resultado**: PENDENTE

---

### Teste 7: Performance - Tempo de Resposta

**Comando**:
```bash
time curl -X POST http://localhost:5678/webhook/rag-query \
  -H "Content-Type: application/json" \
  -d '{"query_text": "teste performance"}'
```

**Validações**:
- [ ] Tempo total < 2 segundos
- [ ] Query Supabase < 500ms (verificar com EXPLAIN ANALYZE)
- [ ] OpenAI embedding generation < 1 segundo

**Resultado**: PENDENTE

---

### Teste 8: Performance - Query Database

**Query SQL**:
```sql
EXPLAIN ANALYZE
SELECT * FROM match_documents(
    (SELECT embedding FROM knowledge_documents LIMIT 1),
    0.75,
    5,
    NULL
);
```

**Validações**:
- [ ] Execution Time < 500ms
- [ ] Usa ivfflat index (verificar no plan)
- [ ] Não faz seq scan completo

**Resultado**: PENDENTE

---

### Teste 9: Error Handling - Sem query_text

**Request**:
```bash
curl -X POST http://localhost:5678/webhook/rag-query \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Validações**:
- [ ] Response HTTP 400
- [ ] Body contém: { "error": "query_text is required", "status": "error" }

**Resultado**: PENDENTE

---

### Teste 10: Error Handling - Nenhum Resultado

**Request**:
```bash
curl -X POST http://localhost:5678/webhook/rag-query \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "xyzabcqwerty123",
    "match_threshold": 0.95
  }'
```

**Validações**:
- [ ] Response HTTP 200
- [ ] success: false
- [ ] results: []
- [ ] context: ""
- [ ] message: "Nenhum conhecimento relevante encontrado"

**Resultado**: PENDENTE

---

## ✅ Critérios de Aceitação Final

**Sprint 1.1 será APROVADO se**:

1. ✅ Todos os 5 arquivos de conhecimento completos e estruturados
2. ⏳ Script de ingest executa sem erros e popula Supabase
3. ⏳ Workflow n8n funciona e retorna resultados relevantes
4. ⏳ Query "como funciona energia solar" retorna 3-5 resultados com >75% similarity
5. ⏳ Todos os 5 serviços podem ser consultados via RAG
6. ⏳ Performance adequada (<500ms query DB, <2s total)
7. ⏳ Error handling funciona corretamente

**Próximos Passos Após Aprovação**:
- Sprint 1.2: Sistema de Agendamento Completo
- Sprint 1.3: Sistema de Notificações por Email
- Sprint 1.4: Sincronização CRM Bidirecional
- Sprint 1.5: Handoff para Humanos

---

## 📝 Notas de Implementação

### Decisões Técnicas

1. **Modelo de Embeddings**: text-embedding-3-small (1536 dims)
   - Razão: Balance custo/qualidade, compatível com Supabase vector
   - Alternativa considerada: ada-002 (deprecated)

2. **Similarity Threshold**: 0.75 (75%)
   - Razão: Balance qualidade vs. recall
   - Pode ser ajustado via parâmetro na query

3. **Chunk Size**: 500-1000 caracteres com overlap 100
   - Razão: Contexto suficiente sem perder granularidade
   - Respeita quebras naturais em markdown (##)

4. **Índice ivfflat**: lists=100
   - Razão: Otimizado para dataset pequeno (<10K vetores)
   - Ajustar para lists=sqrt(total_rows) se crescer

5. **Tabela knowledge_documents**:
   - Renomeado de knowledge_base para maior clareza
   - Adicionado source_file para rastreabilidade
   - Category simplificado (VARCHAR vs JSONB) para performance

### Pontos de Atenção

- **Custo OpenAI**: ~$0.0001 por 1K tokens → estimativa $0.10 total ingest
- **Supabase Storage**: ~50-100 chunks × 1536 dims × 4 bytes = ~300KB embeddings
- **Re-ingest**: Usar delete_documents_by_category() antes de re-processar
- **Updates**: Usar delete_documents_by_source() para atualizar arquivo específico

### Troubleshooting Comum

**Problema**: "pgvector extension not found"
**Solução**: Executar `CREATE EXTENSION IF NOT EXISTS vector;` no Supabase

**Problema**: Ingest script falha com erro OpenAI
**Solução**: Verificar OPENAI_API_KEY está configurada e tem créditos

**Problema**: Queries muito lentas
**Solução**:
1. Verificar índice ivfflat foi criado
2. Aumentar shared_buffers no PostgreSQL
3. Verificar lists parameter do índice

**Problema**: Resultados irrelevantes
**Solução**:
1. Reduzir match_threshold (ex: 0.70)
2. Aumentar match_count (ex: 10)
3. Melhorar conteúdo dos documentos

---

**Documento criado**: 2025-01-12
**Última atualização**: 2025-01-12
**Status**: Aguardando execução dos testes
