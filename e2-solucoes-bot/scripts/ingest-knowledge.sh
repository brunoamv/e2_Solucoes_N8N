#!/usr/bin/env bash
################################################################################
# Script: ingest-knowledge.sh
# Descrição: Gera embeddings OpenAI e popula Supabase knowledge_documents
# Autor: E2 Soluções Bot Team
# Data: 2025-01-12
#
# Dependências:
#   - curl (HTTP requests)
#   - jq (JSON processing)
#   - Variáveis de ambiente:
#       OPENAI_API_KEY
#       SUPABASE_URL
#       SUPABASE_SERVICE_KEY
#
# Uso:
#   ./ingest-knowledge.sh [--dry-run] [--force]
#
# Opções:
#   --dry-run    Simula execução sem inserir dados
#   --force      Limpa dados existentes antes de inserir
################################################################################

set -euo pipefail

# ============================================================================
# CONFIGURAÇÃO
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
KNOWLEDGE_DIR="$PROJECT_ROOT/knowledge"

# Parâmetros de chunking
MIN_CHUNK_SIZE=500
MAX_CHUNK_SIZE=1000
CHUNK_OVERLAP=100

# OpenAI API
OPENAI_MODEL="text-embedding-3-small"
OPENAI_API_URL="https://api.openai.com/v1/embeddings"

# Retry configuration
MAX_RETRIES=3
RETRY_DELAY=2

# Modos de execução
DRY_RUN=false
FORCE_MODE=false

# Contadores
TOTAL_FILES=0
TOTAL_CHUNKS=0
SUCCESS_CHUNKS=0
FAILED_CHUNKS=0

# ============================================================================
# CORES PARA OUTPUT
# ============================================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================================
# FUNÇÕES DE LOGGING
# ============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

# ============================================================================
# VALIDAÇÕES
# ============================================================================

check_dependencies() {
    log_info "Verificando dependências..."
    
    local missing_deps=()
    
    if ! command -v curl &> /dev/null; then
        missing_deps+=("curl")
    fi
    
    if ! command -v jq &> /dev/null; then
        missing_deps+=("jq")
    fi
    
    if [ ${#missing_deps[@]} -gt 0 ]; then
        log_error "Dependências faltando: ${missing_deps[*]}"
        log_error "Instale com: sudo apt-get install ${missing_deps[*]}"
        exit 1
    fi
    
    log_success "Todas as dependências estão instaladas"
}

check_env_vars() {
    log_info "Verificando variáveis de ambiente..."
    
    local missing_vars=()
    
    if [ -z "${OPENAI_API_KEY:-}" ]; then
        missing_vars+=("OPENAI_API_KEY")
    fi
    
    if [ -z "${SUPABASE_URL:-}" ]; then
        missing_vars+=("SUPABASE_URL")
    fi
    
    if [ -z "${SUPABASE_SERVICE_KEY:-}" ]; then
        missing_vars+=("SUPABASE_SERVICE_KEY")
    fi
    
    if [ ${#missing_vars[@]} -gt 0 ]; then
        log_error "Variáveis de ambiente faltando: ${missing_vars[*]}"
        log_error "Configure no arquivo .env ou exporte manualmente"
        exit 1
    fi
    
    log_success "Todas as variáveis de ambiente configuradas"
}

check_knowledge_dir() {
    log_info "Verificando diretório knowledge..."
    
    if [ ! -d "$KNOWLEDGE_DIR" ]; then
        log_error "Diretório não encontrado: $KNOWLEDGE_DIR"
        exit 1
    fi
    
    local md_count=$(find "$KNOWLEDGE_DIR" -name "*.md" -type f | wc -l)
    
    if [ "$md_count" -eq 0 ]; then
        log_error "Nenhum arquivo .md encontrado em $KNOWLEDGE_DIR"
        exit 1
    fi
    
    log_success "Encontrados $md_count arquivos .md"
}

# ============================================================================
# PROCESSAMENTO DE CHUNKS
# ============================================================================

split_into_chunks() {
    local file_path="$1"
    local file_category="$2"
    local file_name=$(basename "$file_path")
    
    log_info "Dividindo arquivo: $file_name"
    
    # Ler conteúdo completo
    local content=$(cat "$file_path")
    
    # Dividir por seções (##) mantendo contexto
    local chunks=()
    local current_chunk=""
    local chunk_id=1
    
    # Processar linha por linha
    while IFS= read -r line; do
        # Se encontrar cabeçalho de seção e chunk atual é grande
        if [[ "$line" =~ ^##[[:space:]] ]] && [ ${#current_chunk} -ge $MIN_CHUNK_SIZE ]; then
            # Salvar chunk atual
            if [ -n "$current_chunk" ]; then
                local chunk_json=$(jq -n \
                    --arg id "${file_category}/${file_name}/chunk-${chunk_id}" \
                    --arg content "$current_chunk" \
                    --arg category "$file_category" \
                    --arg source "$file_name" \
                    '{id: $id, content: $content, category: $category, source: $source}')
                
                echo "$chunk_json"
                chunk_id=$((chunk_id + 1))
                
                # Manter overlap (últimas linhas)
                local overlap=$(echo "$current_chunk" | tail -c $CHUNK_OVERLAP)
                current_chunk="$overlap"
            fi
        fi
        
        # Adicionar linha ao chunk atual
        current_chunk="${current_chunk}${line}\n"
        
        # Se chunk ficou muito grande, forçar quebra
        if [ ${#current_chunk} -ge $MAX_CHUNK_SIZE ]; then
            local chunk_json=$(jq -n \
                --arg id "${file_category}/${file_name}/chunk-${chunk_id}" \
                --arg content "$current_chunk" \
                --arg category "$file_category" \
                --arg source "$file_name" \
                '{id: $id, content: $content, category: $category, source: $source}')
            
            echo "$chunk_json"
            chunk_id=$((chunk_id + 1))
            
            # Manter overlap
            local overlap=$(echo "$current_chunk" | tail -c $CHUNK_OVERLAP)
            current_chunk="$overlap"
        fi
    done <<< "$content"
    
    # Salvar último chunk se não vazio
    if [ -n "$current_chunk" ] && [ ${#current_chunk} -ge $MIN_CHUNK_SIZE ]; then
        local chunk_json=$(jq -n \
            --arg id "${file_category}/${file_name}/chunk-${chunk_id}" \
            --arg content "$current_chunk" \
            --arg category "$file_category" \
            --arg source "$file_name" \
            '{id: $id, content: $content, category: $category, source: $source}')
        
        echo "$chunk_json"
    fi
}

# ============================================================================
# INTEGRAÇÃO OPENAI
# ============================================================================

generate_embedding() {
    local text="$1"
    local attempt=1
    
    while [ $attempt -le $MAX_RETRIES ]; do
        log_info "Gerando embedding (tentativa $attempt/$MAX_RETRIES)..."
        
        local response=$(curl -s -w "\n%{http_code}" \
            -X POST "$OPENAI_API_URL" \
            -H "Authorization: Bearer $OPENAI_API_KEY" \
            -H "Content-Type: application/json" \
            -d @- << EOF
{
  "input": $(echo "$text" | jq -Rs .),
  "model": "$OPENAI_MODEL"
}
