#!/usr/bin/env bash
################################################################################
# Script Simplificado: Ingest Knowledge Base para Supabase
################################################################################

set -euo pipefail

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_error() { echo -e "${RED}[ERRO]${NC} $1" >&2; }

# Validar variáveis
: "${OPENAI_API_KEY:?Erro: OPENAI_API_KEY não definida}"
: "${SUPABASE_URL:?Erro: SUPABASE_URL não definida}"
: "${SUPABASE_SERVICE_KEY:?Erro: SUPABASE_SERVICE_KEY não definida}"

echo "========================================================================"
echo "E2 Soluções Bot - Ingest Knowledge Base"
echo "========================================================================"
echo ""

# Processar cada arquivo .md
TOTAL=0
SUCCESS=0

for file in knowledge/servicos/*.md; do
    [ -f "$file" ] || continue
    
    filename=$(basename "$file")
    category="servicos"
    
    log_info "Processando: $filename"
    
    # Ler conteúdo
    content=$(cat "$file")
    
    # Gerar embedding via OpenAI
    log_info "  → Gerando embedding..."
    embedding_response=$(curl -s -X POST "https://api.openai.com/v1/embeddings" \
        -H "Authorization: Bearer $OPENAI_API_KEY" \
        -H "Content-Type: application/json" \
        -d "{
            \"input\": $(echo "$content" | jq -Rs .),
            \"model\": \"text-embedding-3-small\"
        }")
    
    # Extrair embedding
    embedding=$(echo "$embedding_response" | jq -r '.data[0].embedding')
    
    if [ "$embedding" = "null" ] || [ -z "$embedding" ]; then
        log_error "  ✗ Falha ao gerar embedding"
        continue
    fi
    
    # Inserir no Supabase
    log_info "  → Inserindo no Supabase..."
    
    insert_response=$(curl -s -X POST "${SUPABASE_URL}/rest/v1/knowledge_documents" \
        -H "apikey: ${SUPABASE_SERVICE_KEY}" \
        -H "Authorization: Bearer ${SUPABASE_SERVICE_KEY}" \
        -H "Content-Type: application/json" \
        -H "Prefer: return=minimal" \
        -d "{
            \"id\": \"${category}/${filename}\",
            \"content\": $(echo "$content" | jq -Rs .),
            \"embedding\": [$(echo "$embedding" | tr -d '[]')],
            \"category\": \"$category\",
            \"source_file\": \"$filename\",
            \"metadata\": {}
        }")
    
    if [ -z "$insert_response" ]; then
        log_success "  ✓ Inserido com sucesso"
        ((SUCCESS++))
    else
        log_error "  ✗ Erro ao inserir: $insert_response"
    fi
    
    ((TOTAL++))
    echo ""
done

echo "========================================================================"
echo "RESUMO"
echo "========================================================================"
echo "Total processados: $TOTAL"
echo "Sucesso: $SUCCESS"
echo "Falhas: $((TOTAL - SUCCESS))"
echo ""

# Verificar quantidade no banco
count=$(curl -s "${SUPABASE_URL}/rest/v1/knowledge_documents?select=count" \
    -H "apikey: ${SUPABASE_SERVICE_KEY}" | jq -r '.[0].count')

log_success "Total de documentos no banco: $count"
