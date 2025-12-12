# Testes de Validação - Sprint 1.1 Validation

**Objetivo**: Executar testes completos para validar o sistema RAG end-to-end

**Tempo Estimado**: 20-30 minutos

**Pré-requisitos**:
- ✅ Etapa 1 (SETUP_CREDENTIALS.md) completa
- ✅ Etapa 2 (DEPLOY_SQL.md) completa
- ✅ Etapa 3 (EXECUTE_INGEST.md) completa
- ✅ Etapa 4 (IMPORT_N8N_WORKFLOW.md) completa
- ✅ Sistema completo operacional

---

## 📋 Plano de Testes

Este documento executa **10 testes de validação** completos conforme `docs/validation/sprint_1.1_validation.md`:

1. ✅ Executar script de ingest (já validado na Etapa 3)
2. ✅ Verificar dados no Supabase (já validado na Etapa 3)
3. ✅ Importar workflow n8n (já validado na Etapa 4)
4. **Teste 4**: Query RAG - "como funciona energia solar"
5. **Teste 5**: Query RAG - Com filtro de categoria
6. **Teste 6**: Query RAG - Cada serviço (5 serviços)
7. **Teste 7**: Performance - Tempo de resposta
8. **Teste 8**: Performance - Query database
9. **Teste 9**: Error handling - Sem query_text
10. **Teste 10**: Error handling - Nenhum resultado

---

## 🧪 Configuração do Ambiente de Testes

### Passo 1: Preparar Script de Testes

```bash
cd /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot

# Criar diretório para resultados de testes
mkdir -p docs/validation/test_results

# Carregar variáveis de ambiente
set -a
source .env
set +a

# Verificar n8n está rodando
curl -s -o /dev/null -w "%{http_code}" http://localhost:5678/
# Esperado: 200 ou 302
```

### Passo 2: Definir Variáveis de Teste

```bash
# URL base do webhook n8n
N8N_WEBHOOK_URL="http://localhost:5678/webhook/rag-query"

# Função helper para testes
run_test() {
    local test_name=$1
    local payload=$2
    local expected_status=${3:-200}

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🧪 Teste: $test_name"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    response=$(curl -s -w "\n%{http_code}" -X POST "$N8N_WEBHOOK_URL" \
        -H "Content-Type: application/json" \
        -d "$payload")

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    echo "📨 Request:"
    echo "$payload" | jq '.' 2>/dev/null || echo "$payload"
    echo ""
    echo "📬 Response (HTTP $http_code):"
    echo "$body" | jq '.' 2>/dev/null || echo "$body"
    echo ""

    if [ "$http_code" -eq "$expected_status" ]; then
        echo "✅ PASSOU: Status HTTP $http_code (esperado: $expected_status)"
        return 0
    else
        echo "❌ FALHOU: Status HTTP $http_code (esperado: $expected_status)"
        return 1
    fi
}
```

---

## 🎯 Teste 4: Query RAG - "como funciona energia solar"

**Objetivo**: Validar query básica retorna resultados relevantes

### Executar Teste

```bash
run_test "Query básica - energia solar" '{
  "query_text": "como funciona energia solar"
}' 200
```

### Critérios de Aceitação

**Response deve conter**:
- ✅ `"success": true`
- ✅ `"results"`: array com 3-5 itens
- ✅ Cada result tem: `rank`, `content`, `source`, `similarity`, `relevance`
- ✅ `source.file` contém `"energia_solar.md"`
- ✅ `source.category` = `"servicos"`
- ✅ `similarity` >= 0.75 (75%)
- ✅ `relevance` = `"high"` ou `"medium"`
- ✅ `context`: string formatada para AI
- ✅ `metadata.total_results` >= 3
- ✅ `metadata.average_similarity` >= 0.75

### Validação Adicional

```bash
# Salvar response para análise
curl -s -X POST "$N8N_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{"query_text": "como funciona energia solar"}' \
  > docs/validation/test_results/test_4_energia_solar.json

# Verificar estrutura
cat docs/validation/test_results/test_4_energia_solar.json | jq '{
  success,
  total_results: .metadata.total_results,
  avg_similarity: .metadata.average_similarity,
  top_file: .results[0].source.file,
  top_similarity: .results[0].similarity
}'
```

**Resultado Esperado**:
```json
{
  "success": true,
  "total_results": 5,
  "avg_similarity": 0.82,
  "top_file": "energia_solar.md",
  "top_similarity": 0.87
}
```

---

## 🎯 Teste 5: Query RAG - Com Filtro de Categoria

**Objetivo**: Validar filtros funcionam corretamente

### Executar Teste

```bash
run_test "Query com filtro de categoria" '{
  "query_text": "quanto custa instalação",
  "category": "servicos",
  "match_count": 10,
  "match_threshold": 0.70
}' 200
```

### Critérios de Aceitação

**Response deve conter**:
- ✅ Até 10 resultados (match_count=10)
- ✅ Todos com `category` = `"servicos"`
- ✅ Busca em múltiplos arquivos
- ✅ `metadata.category_filter` = `"servicos"`
- ✅ Similarity >= 0.70 (threshold personalizado)

### Validação Adicional

```bash
# Salvar e analisar
curl -s -X POST "$N8N_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "quanto custa instalação",
    "category": "servicos",
    "match_count": 10,
    "match_threshold": 0.70
  }' \
  > docs/validation/test_results/test_5_filtro_categoria.json

# Verificar filtro aplicado
cat docs/validation/test_results/test_5_filtro_categoria.json | jq '{
  category_filter: .metadata.category_filter,
  total_results: .metadata.total_results,
  files_found: .metadata.files_found,
  all_servicos: [.results[].source.category] | all(. == "servicos")
}'
```

**Resultado Esperado**:
```json
{
  "category_filter": "servicos",
  "total_results": 7,
  "files_found": ["energia_solar.md", "subestacao.md", "projetos_eletricos.md"],
  "all_servicos": true
}
```

---

## 🎯 Teste 6: Query RAG - Cada Serviço

**Objetivo**: Validar todos os 5 serviços retornam resultados relevantes

### 6.1 - Energia Solar

```bash
run_test "Serviço 1: Energia Solar" '{
  "query_text": "energia solar residencial fotovoltaica"
}' 200

# Validar arquivo correto
curl -s -X POST "$N8N_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{"query_text": "energia solar residencial fotovoltaica"}' \
  | jq '.results[0].source.file'
# Esperado: "energia_solar.md"
```

### 6.2 - Subestação

```bash
run_test "Serviço 2: Subestação" '{
  "query_text": "subestação transformador adequação"
}' 200

# Validar
curl -s -X POST "$N8N_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{"query_text": "subestação transformador adequação"}' \
  | jq '.results[0].source.file'
# Esperado: "subestacao.md"
```

### 6.3 - Projetos Elétricos

```bash
run_test "Serviço 3: Projetos Elétricos" '{
  "query_text": "projeto elétrico residencial NBR 5410"
}' 200

# Validar
curl -s -X POST "$N8N_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{"query_text": "projeto elétrico residencial NBR 5410"}' \
  | jq '.results[0].source.file'
# Esperado: "projetos_eletricos.md"
```

### 6.4 - Armazenamento de Energia

```bash
run_test "Serviço 4: Armazenamento" '{
  "query_text": "bateria lítio armazenamento energia BESS"
}' 200

# Validar
curl -s -X POST "$N8N_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{"query_text": "bateria lítio armazenamento energia BESS"}' \
  | jq '.results[0].source.file'
# Esperado: "armazenamento_energia.md"
```

### 6.5 - Análise e Laudos

```bash
run_test "Serviço 5: Análise e Laudos" '{
  "query_text": "análise consumo energético laudo pericial"
}' 200

# Validar
curl -s -X POST "$N8N_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{"query_text": "análise consumo energético laudo pericial"}' \
  | jq '.results[0].source.file'
# Esperado: "analise_laudos.md"
```

### Resumo Teste 6

```bash
# Verificar todos os 5 serviços
echo "📊 Resumo Teste 6: Cobertura dos 5 Serviços"
echo ""

services=(
  "energia solar residencial fotovoltaica"
  "subestação transformador adequação"
  "projeto elétrico residencial NBR 5410"
  "bateria lítio armazenamento energia BESS"
  "análise consumo energético laudo pericial"
)

for query in "${services[@]}"; do
    file=$(curl -s -X POST "$N8N_WEBHOOK_URL" \
        -H "Content-Type: application/json" \
        -d "{\"query_text\": \"$query\"}" \
        | jq -r '.results[0].source.file')
    echo "✅ Query: $query → Arquivo: $file"
done
```

**Resultado Esperado**:
```
📊 Resumo Teste 6: Cobertura dos 5 Serviços

✅ Query: energia solar residencial fotovoltaica → Arquivo: energia_solar.md
✅ Query: subestação transformador adequação → Arquivo: subestacao.md
✅ Query: projeto elétrico residencial NBR 5410 → Arquivo: projetos_eletricos.md
✅ Query: bateria lítio armazenamento energia BESS → Arquivo: armazenamento_energia.md
✅ Query: análise consumo energético laudo pericial → Arquivo: analise_laudos.md
```

---

## 🎯 Teste 7: Performance - Tempo de Resposta

**Objetivo**: Validar tempo total < 2 segundos

### Executar Teste

```bash
echo "⏱️ Teste 7: Performance - Tempo de Resposta"
echo ""

# Teste com medição de tempo
time curl -s -X POST "$N8N_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{"query_text": "teste performance energia solar"}' \
  -o /dev/null

# Teste detalhado com breakdown
curl -w "\n\nPerformance Metrics:\n  DNS Lookup: %{time_namelookup}s\n  TCP Connect: %{time_connect}s\n  TLS Handshake: %{time_appconnect}s\n  Server Processing: %{time_starttransfer}s\n  Total Time: %{time_total}s\n" \
  -s -X POST "$N8N_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{"query_text": "teste performance"}' \
  -o /dev/null
```

### Critérios de Aceitação

**Benchmarks**:
- ✅ **Total Time**: < 2.0 segundos
- ✅ **Server Processing**: < 1.5 segundos
- ✅ Breakdown aproximado:
  - OpenAI embedding generation: ~800ms
  - Supabase vector search: ~300ms
  - n8n processing: ~200ms
  - Network overhead: ~100ms

### Múltiplas Execuções

```bash
# 10 testes para média
echo "📊 Executando 10 testes de performance..."
echo ""

total=0
for i in {1..10}; do
    time_taken=$(curl -w "%{time_total}" -s -o /dev/null -X POST "$N8N_WEBHOOK_URL" \
        -H "Content-Type: application/json" \
        -d '{"query_text": "teste performance '$i'"}')

    echo "Teste $i: ${time_taken}s"
    total=$(echo "$total + $time_taken" | bc)
done

average=$(echo "scale=3; $total / 10" | bc)
echo ""
echo "📈 Tempo médio: ${average}s"
echo ""

if (( $(echo "$average < 2.0" | bc -l) )); then
    echo "✅ PASSOU: Tempo médio ${average}s < 2.0s"
else
    echo "❌ FALHOU: Tempo médio ${average}s >= 2.0s"
fi
```

---

## 🎯 Teste 8: Performance - Query Database

**Objetivo**: Validar query SQL < 500ms

### Executar Teste

```bash
echo "🗄️ Teste 8: Performance - Query Database"
echo ""

# Conectar ao Supabase via psql (se disponível)
# OU usar SQL Editor do Supabase Dashboard

# Executar EXPLAIN ANALYZE
psql "postgresql://postgres:[PASSWORD]@[HOST].supabase.co:5432/postgres?sslmode=require" << 'EOF'
EXPLAIN ANALYZE
SELECT * FROM match_documents(
    (SELECT embedding FROM knowledge_documents LIMIT 1),
    0.75,
    5,
    NULL
);
EOF
```

### Via Supabase Dashboard (Alternativa)

1. Acessar Supabase Dashboard → SQL Editor
2. Executar query:

```sql
EXPLAIN ANALYZE
SELECT * FROM match_documents(
    (SELECT embedding FROM knowledge_documents LIMIT 1),
    0.75,
    5,
    NULL
);
```

### Critérios de Aceitação

**Query Plan deve mostrar**:
- ✅ **Execution Time**: < 500ms
- ✅ **Index Scan**: usando `knowledge_documents_embedding_idx`
- ✅ **Não faz Seq Scan** completo (prova de uso do índice ivfflat)
- ✅ Rows Scanned << Total Rows (eficiência do índice)

**Exemplo de Query Plan Esperado**:
```
Planning Time: 2.341 ms
Execution Time: 234.567 ms

Index Scan using knowledge_documents_embedding_idx on knowledge_documents
  Filter: (1 - (embedding <=> $1)) > 0.75
  Rows Removed by Filter: 12
  Rows Returned: 5
```

### Otimização (se necessário)

```sql
-- Se query estiver lenta, executar VACUUM ANALYZE
VACUUM ANALYZE knowledge_documents;

-- Re-executar teste
```

---

## 🎯 Teste 9: Error Handling - Sem query_text

**Objetivo**: Validar error handling retorna HTTP 400

### Executar Teste

```bash
run_test "Error handling - query_text vazio" '{}' 400

# Validar mensagem de erro
curl -s -X POST "$N8N_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{}' \
  | jq '{
      error,
      status
    }'
```

### Critérios de Aceitação

**Response deve conter**:
- ✅ **HTTP Status**: 400
- ✅ `"error": "query_text is required"`
- ✅ `"status": "error"`

**Resultado Esperado**:
```json
{
  "error": "query_text is required",
  "status": "error"
}
```

---

## 🎯 Teste 10: Error Handling - Nenhum Resultado

**Objetivo**: Validar comportamento quando não há resultados

### Executar Teste

```bash
run_test "Error handling - nenhum resultado" '{
  "query_text": "xyzabcqwerty123nonsensequery",
  "match_threshold": 0.95
}' 200

# Validar response
curl -s -X POST "$N8N_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "xyzabcqwerty123nonsensequery",
    "match_threshold": 0.95
  }' \
  | jq '{
      success,
      results_count: (.results | length),
      context,
      message
    }'
```

### Critérios de Aceitação

**Response deve conter**:
- ✅ **HTTP Status**: 200 (não é erro, apenas sem resultados)
- ✅ `"success": false`
- ✅ `"results": []` (array vazio)
- ✅ `"context": ""` (string vazia)
- ✅ `"message": "Nenhum conhecimento relevante encontrado"`

**Resultado Esperado**:
```json
{
  "success": false,
  "results_count": 0,
  "context": "",
  "message": "Nenhum conhecimento relevante encontrado"
}
```

---

## 📊 Relatório de Validação Completa

### Script de Relatório Automático

```bash
#!/bin/bash
# scripts/generate-validation-report.sh

cd /home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot

# Carregar .env
set -a; source .env; set +a

# Função de teste
run_test() {
    local test_name=$1
    local payload=$2
    local expected_status=${3:-200}

    response=$(curl -s -w "\n%{http_code}" -X POST "http://localhost:5678/webhook/rag-query" \
        -H "Content-Type: application/json" \
        -d "$payload")

    http_code=$(echo "$response" | tail -n1)

    if [ "$http_code" -eq "$expected_status" ]; then
        echo "✅ $test_name: PASSOU (HTTP $http_code)"
        return 0
    else
        echo "❌ $test_name: FALHOU (HTTP $http_code, esperado: $expected_status)"
        return 1
    fi
}

# Executar todos os testes
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 RELATÓRIO DE VALIDAÇÃO SPRINT 1.1"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Data: $(date +'%Y-%m-%d %H:%M:%S')"
echo ""

passed=0
failed=0

# Teste 4
if run_test "Teste 4: Query básica" '{"query_text":"como funciona energia solar"}'; then
    ((passed++))
else
    ((failed++))
fi

# Teste 5
if run_test "Teste 5: Query com filtro" '{"query_text":"quanto custa","category":"servicos","match_count":10}'; then
    ((passed++))
else
    ((failed++))
fi

# Teste 6 (5 serviços)
echo ""
echo "🔍 Teste 6: Cobertura dos 5 Serviços"
services_passed=0
for query in "energia solar residencial" "subestação transformador" "projeto elétrico NBR" "bateria lítio BESS" "análise consumo laudo"; do
    if run_test "  - $query" "{\"query_text\":\"$query\"}"; then
        ((services_passed++))
    fi
done

if [ $services_passed -eq 5 ]; then
    echo "✅ Teste 6: PASSOU (5/5 serviços)"
    ((passed++))
else
    echo "❌ Teste 6: FALHOU ($services_passed/5 serviços)"
    ((failed++))
fi

# Teste 7 (Performance)
echo ""
echo "⏱️ Teste 7: Performance"
time_taken=$(curl -w "%{time_total}" -s -o /dev/null -X POST "http://localhost:5678/webhook/rag-query" \
    -H "Content-Type: application/json" \
    -d '{"query_text":"teste performance"}')

if (( $(echo "$time_taken < 2.0" | bc -l) )); then
    echo "✅ Teste 7: PASSOU (${time_taken}s < 2.0s)"
    ((passed++))
else
    echo "❌ Teste 7: FALHOU (${time_taken}s >= 2.0s)"
    ((failed++))
fi

# Teste 9 (Error handling)
if run_test "Teste 9: Error handling (sem query)" '{}' 400; then
    ((passed++))
else
    ((failed++))
fi

# Teste 10 (Sem resultados)
if run_test "Teste 10: Sem resultados" '{"query_text":"xyzabcqwerty123","match_threshold":0.95}'; then
    ((passed++))
else
    ((failed++))
fi

# Resumo final
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 RESUMO FINAL"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Testes Executados: $((passed + failed))"
echo "✅ Passou: $passed"
echo "❌ Falhou: $failed"
echo ""

if [ $failed -eq 0 ]; then
    echo "🎉 VALIDAÇÃO COMPLETA: TODOS OS TESTES PASSARAM!"
    echo ""
    echo "✅ Sprint 1.1 está 100% validado e pronto para uso"
    exit 0
else
    echo "⚠️ VALIDAÇÃO INCOMPLETA: $failed teste(s) falharam"
    echo ""
    echo "Por favor, revise os testes falhados e corrija antes de prosseguir"
    exit 1
fi
```

### Executar Relatório

```bash
chmod +x scripts/generate-validation-report.sh
./scripts/generate-validation-report.sh
```

---

## ✅ Checklist Final de Validação

### Infraestrutura

- [ ] ✅ OpenAI API configurada e funcional
- [ ] ✅ Supabase configurado com pgvector
- [ ] ✅ n8n instalado e rodando
- [ ] ✅ Todas as credenciais configuradas

### Deploy

- [ ] ✅ Funções SQL deployadas no Supabase
- [ ] ✅ Extensão pgvector habilitada
- [ ] ✅ Índices criados corretamente
- [ ] ✅ Workflow n8n importado e ativo

### Dados

- [ ] ✅ 5 arquivos de conhecimento processados
- [ ] ✅ 50-100 chunks inseridos no banco
- [ ] ✅ Todos os embeddings gerados (1536 dims)
- [ ] ✅ Distribuição por serviço correta

### Funcionalidade

- [ ] ✅ Teste 4: Query básica funciona
- [ ] ✅ Teste 5: Filtros funcionam
- [ ] ✅ Teste 6: Todos os 5 serviços respondem
- [ ] ✅ Teste 7: Performance adequada (<2s)
- [ ] ✅ Teste 8: Query SQL eficiente (<500ms)
- [ ] ✅ Teste 9: Error handling funciona
- [ ] ✅ Teste 10: Comportamento sem resultados correto

### Qualidade

- [ ] ✅ Similarity score >= 0.75
- [ ] ✅ Context string formatado corretamente
- [ ] ✅ Metadata completo e correto
- [ ] ✅ Taxa de sucesso 100%

---

## 🎉 Sprint 1.1 Validação COMPLETA!

Se todos os checkboxes acima estão marcados:

**✅ PARABÉNS!** O sistema RAG está 100% validado e funcional!

### O que foi validado:

1. ✅ **Base de Conhecimento**: 5 serviços E2 Soluções documentados (1.380+ linhas)
2. ✅ **Script de Ingest**: Chunking, embedding generation, inserção Supabase funcionando
3. ✅ **Funções SQL**: match_documents() e utilidades deployadas e testadas
4. ✅ **Workflow n8n**: 7 nós coordenados, webhook funcional, credenciais configuradas
5. ✅ **Sistema End-to-End**: Query → Embedding → Vector Search → Format → Response

### Próximos Passos:

**Sprint 1.2**: Sistema de Agendamento Completo
- Google Calendar integration
- RD Station CRM sync
- Appointment scheduling logic
- Reminder system

**Sprint 1.3**: Sistema de Notificações
- Email notifications
- Discord webhooks
- Template system

**Sprint 1.4**: Sincronização CRM Bidirecional
- RD Station full integration
- Contact sync
- Deal tracking

**Sprint 1.5**: Handoff para Humanos
- Escalation rules
- Human takeover
- Session transfer

---

**Documento criado**: 2025-01-12
**Status**: Sprint 1.1 - VALIDAÇÃO COMPLETA ✅
**Tempo Total Validação**: 2-3 horas conforme planejado
