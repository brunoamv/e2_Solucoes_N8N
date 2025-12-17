#!/bin/bash
# ============================================================================
# E2 Soluções Bot - Rollback to v2 (AI Version)
# ============================================================================
# Script para reverter de v1 (menu) para v2 (Claude AI)
# Autor: Claude Code
# Data: 2025-12-16
# Sprint: 0.1 - V1 Simple
# ============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Project paths
PROJECT_ROOT="/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot"
WORKFLOWS_DIR="$PROJECT_ROOT/n8n/workflows"

# ============================================================================
# Helper Functions
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
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Verificando pré-requisitos..."

    # Check if n8n is running
    if ! docker ps | grep -q n8n; then
        log_error "n8n não está rodando. Execute ./scripts/start-dev.sh primeiro"
        exit 1
    fi

    # Check backup directory argument
    if [ -z "$1" ]; then
        log_error "Informe o diretório de backup"
        echo "Uso: ./scripts/rollback-to-v2.sh <backup_dir>"
        echo ""
        echo "Exemplo:"
        echo "  ./scripts/rollback-to-v2.sh /path/to/backups/v2_20241216_143000"
        echo ""

        # List available backups
        if [ -d "$PROJECT_ROOT/backups" ]; then
            log_info "Backups disponíveis:"
            ls -lt "$PROJECT_ROOT/backups" | grep "^d" | head -5
        fi

        exit 1
    fi

    BACKUP_DIR="$1"

    if [ ! -d "$BACKUP_DIR" ]; then
        log_error "Diretório de backup não encontrado: $BACKUP_DIR"
        exit 1
    fi

    if [ ! -f "$BACKUP_DIR/02_ai_agent_conversation.json" ]; then
        log_error "Backup do Workflow 02 não encontrado em $BACKUP_DIR"
        exit 1
    fi

    log_success "Pré-requisitos OK"
}

restore_workflow() {
    log_info "Restaurando Workflow 02 original (v2 com Claude AI)..."

    # Copy backup to workflows directory
    cp "$BACKUP_DIR/02_ai_agent_conversation.json" "$WORKFLOWS_DIR/"

    log_success "Arquivo Workflow 02 v2 restaurado"

    log_warning "AÇÃO MANUAL NECESSÁRIA:"
    echo "  1. Acesse http://localhost:5678"
    echo "  2. Workflows > 02 - AI Agent Conversation V1 > Desativar"
    echo "  3. Workflows > 02 - AI Agent Conversation V1 > Deletar"
    echo "  4. Import from File > $WORKFLOWS_DIR/02_ai_agent_conversation.json"
    echo "  5. Renomear para '02 - AI Agent Conversation'"
    echo "  6. Ativar workflow (toggle on)"
    echo ""

    read -p "Pressione ENTER após importar Workflow 02 v2..."
}

enable_ai_workflows() {
    log_info "Reativando Workflows 03 e 04 (RAG + Vision AI)..."

    log_warning "AÇÃO MANUAL NECESSÁRIA:"
    echo "  1. Acesse http://localhost:5678"
    echo "  2. Workflows > 03_rag_knowledge_query > Ativar (toggle on)"
    echo "  3. Workflows > 04_image_analysis > Ativar (toggle on)"
    echo ""

    read -p "Pressione ENTER após ativar Workflows 03 e 04..."
}

verify_environment() {
    log_info "Verificando variáveis de ambiente..."

    # Check if AI keys are configured
    if [ -f "$PROJECT_ROOT/docker/.env" ]; then
        source "$PROJECT_ROOT/docker/.env"

        # Check Anthropic API key
        if [ -z "$ANTHROPIC_API_KEY" ] || [ "$ANTHROPIC_API_KEY" == "sk-ant-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX" ]; then
            log_warning "ANTHROPIC_API_KEY não configurada"
            echo "  Configure em docker/.env para usar Claude AI"
        else
            log_success "ANTHROPIC_API_KEY configurada"
        fi

        # Check OpenAI API key
        if [ -z "$OPENAI_API_KEY" ] || [[ "$OPENAI_API_KEY" == sk-* ]]; then
            if [[ "$OPENAI_API_KEY" == sk-proj-* ]]; then
                log_success "OPENAI_API_KEY configurada"
            else
                log_warning "OPENAI_API_KEY pode estar inválida"
            fi
        else
            log_warning "OPENAI_API_KEY não configurada"
            echo "  Configure em docker/.env para usar RAG"
        fi
    else
        log_warning "Arquivo .env não encontrado"
    fi
}

test_rollback() {
    log_info "Testando rollback..."

    log_info "Teste manual recomendado:"
    echo "  1. Envie mensagem WhatsApp para bot: 'Oi'"
    echo "  2. Verifique se recebe resposta em linguagem natural (não menu)"
    echo "  3. Teste query RAG: 'Quanto custa energia solar?'"
    echo "  4. Teste Vision AI: envie foto de conta de luz"
    echo "  5. Teste fluxo completo de conversação"
    echo ""

    read -p "Deseja executar teste automatizado? (s/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        if [ -f "$PROJECT_ROOT/scripts/test-v2-ai.sh" ]; then
            bash "$PROJECT_ROOT/scripts/test-v2-ai.sh" --quick
        else
            log_warning "Script de teste v2 não encontrado"
        fi
    fi
}

update_documentation() {
    log_info "Atualizando documentação..."

    # Update PROJECT_STATUS.md
    if [ -f "$PROJECT_ROOT/docs/PROJECT_STATUS.md" ]; then
        echo "" >> "$PROJECT_ROOT/docs/PROJECT_STATUS.md"
        echo "## Rollback to v2 (AI Version)" >> "$PROJECT_ROOT/docs/PROJECT_STATUS.md"
        echo "- **Data**: $(date '+%Y-%m-%d %H:%M:%S')" >> "$PROJECT_ROOT/docs/PROJECT_STATUS.md"
        echo "- **Versão Restaurada**: v2.0 (Claude AI + RAG + Vision)" >> "$PROJECT_ROOT/docs/PROJECT_STATUS.md"
        echo "- **Backup Usado**: $BACKUP_DIR" >> "$PROJECT_ROOT/docs/PROJECT_STATUS.md"
    fi

    log_success "Documentação atualizada"
}

display_summary() {
    echo ""
    echo "============================================================================"
    log_success "ROLLBACK PARA v2 CONCLUÍDO!"
    echo "============================================================================"
    echo ""
    echo "✅ Workflow 02 v2 restaurado (Claude AI)"
    echo "✅ Workflows 03 (RAG) e 04 (Vision AI) reativados"
    echo "⚠️  Verifique se APIs estão configuradas (Anthropic + OpenAI)"
    echo ""
    echo "📊 Custos Mensais v2:"
    echo "  - Evolution API: R$ 50/mês"
    echo "  - Anthropic Claude: ~R$ 27/mês (100 conversas)"
    echo "  - OpenAI Embeddings: ~R$ 0,80/mês (100 consultas RAG)"
    echo "  - Total: ~R$ 78/mês"
    echo ""
    echo "📈 Próximos Passos:"
    echo "  1. Verificar saldo OpenAI (mínimo $5)"
    echo "  2. Validar Sprint 1.1 (RAG): docs/validation/README.md"
    echo "  3. Testar bot com clientes reais"
    echo "  4. Coletar métricas de conversão (espera-se 60%)"
    echo ""
    echo "🔙 Backup v1 preservado em: $PROJECT_ROOT/backups/"
    echo ""
    echo "============================================================================"
}

# ============================================================================
# Main Execution
# ============================================================================

main() {
    echo ""
    echo "============================================================================"
    echo "  E2 Soluções Bot - Rollback to v2 (AI Version)"
    echo "============================================================================"
    echo ""

    if [ -z "$1" ]; then
        check_prerequisites
        exit 1
    fi

    BACKUP_DIR="$1"

    log_warning "Este script irá:"
    echo "  1. Restaurar Workflow 02 v2 (Claude AI)"
    echo "  2. Reativar Workflows 03 (RAG) e 04 (Vision AI)"
    echo "  3. Verificar configuração de APIs"
    echo "  4. Testar rollback"
    echo ""
    echo "  Backup: $BACKUP_DIR"
    echo ""

    read -p "Deseja continuar? (s/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        log_warning "Rollback cancelado pelo usuário"
        exit 0
    fi

    check_prerequisites "$BACKUP_DIR"
    restore_workflow
    enable_ai_workflows
    verify_environment
    test_rollback
    update_documentation
    display_summary
}

# Run main function
main "$@"
