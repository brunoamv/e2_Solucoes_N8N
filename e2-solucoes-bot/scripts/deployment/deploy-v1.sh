#!/bin/bash
# ============================================================================
# E2 Soluções Bot - Deploy v1 Simple (Menu-Based)
# ============================================================================
# Script para deploy automatizado da versão v1 do bot (sem Claude AI)
# Autor: Claude Code
# Data: 2025-12-16
# Sprint: 0.1 - V1 Simple
# ============================================================================

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project paths
PROJECT_ROOT="/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot"
BACKUP_DIR="$PROJECT_ROOT/backups/v2_$(date +%Y%m%d_%H%M%S)"
WORKFLOWS_DIR="$PROJECT_ROOT/n8n/workflows"
SCRIPTS_DIR="$PROJECT_ROOT/scripts"

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

    # Check if workflow files exist
    if [ ! -f "$WORKFLOWS_DIR/02_ai_agent_conversation.json" ]; then
        log_error "Workflow 02 original não encontrado"
        exit 1
    fi

    if [ ! -f "$WORKFLOWS_DIR/02_ai_agent_conversation_V1_MENU.json" ]; then
        log_error "Workflow 02 v1 não encontrado"
        exit 1
    fi

    log_success "Pré-requisitos OK"
}

create_backup() {
    log_info "Criando backup do Workflow 02 original..."

    mkdir -p "$BACKUP_DIR"

    # Backup Workflow 02 (AI version)
    cp "$WORKFLOWS_DIR/02_ai_agent_conversation.json" "$BACKUP_DIR/"

    # Backup environment
    cp "$PROJECT_ROOT/docker/.env" "$BACKUP_DIR/.env.backup"

    # Create restore instructions
    cat > "$BACKUP_DIR/RESTORE_INSTRUCTIONS.md" << EOF
# Instruções de Restauração v2

Este backup foi criado em: $(date '+%Y-%m-%d %H:%M:%S')

## Para restaurar v2 (AI version):

1. Restaurar Workflow 02:
\`\`\`bash
cp $BACKUP_DIR/02_ai_agent_conversation.json $WORKFLOWS_DIR/
\`\`\`

2. Reimportar no n8n:
\`\`\`bash
# Acesse n8n: http://localhost:5678
# Workflows > Import from File > 02_ai_agent_conversation.json
\`\`\`

3. Reativar Workflows 03 e 04:
\`\`\`bash
# n8n > Workflows > 03_rag_knowledge_query > Active
# n8n > Workflows > 04_image_analysis > Active
\`\`\`

4. Restaurar .env (se necessário):
\`\`\`bash
cp $BACKUP_DIR/.env.backup $PROJECT_ROOT/docker/.env
\`\`\`

## Ou use o script automatizado:
\`\`\`bash
./scripts/rollback-to-v2.sh $BACKUP_DIR
\`\`\`
EOF

    log_success "Backup criado em: $BACKUP_DIR"
}

disable_ai_workflows() {
    log_info "Desabilitando Workflows 03 e 04 (RAG + Vision AI)..."

    # Note: This requires n8n CLI or API access
    # For now, we'll just log the manual steps

    log_warning "AÇÃO MANUAL NECESSÁRIA:"
    echo "  1. Acesse http://localhost:5678"
    echo "  2. Workflows > 03_rag_knowledge_query > Desativar (toggle off)"
    echo "  3. Workflows > 04_image_analysis > Desativar (toggle off)"
    echo ""

    read -p "Pressione ENTER após desativar Workflows 03 e 04..."
}

import_v1_workflow() {
    log_info "Importando Workflow 02 v1 (menu-based)..."

    # Copy v1 workflow to active directory
    cp "$WORKFLOWS_DIR/02_ai_agent_conversation_V1_MENU.json" "$WORKFLOWS_DIR/02_ai_agent_conversation.json.v1"

    log_warning "AÇÃO MANUAL NECESSÁRIA:"
    echo "  1. Acesse http://localhost:5678"
    echo "  2. Workflows > 02_ai_agent_conversation > Deletar (backup já feito)"
    echo "  3. Import from File > $WORKFLOWS_DIR/02_ai_agent_conversation.json.v1"
    echo "  4. Renomear para '02 - AI Agent Conversation V1'"
    echo "  5. Ativar workflow (toggle on)"
    echo ""

    read -p "Pressione ENTER após importar Workflow 02 v1..."
}

test_deployment() {
    log_info "Testando deployment v1..."

    # Run automated tests
    if [ -f "$SCRIPTS_DIR/test-v1-menu.sh" ]; then
        bash "$SCRIPTS_DIR/test-v1-menu.sh" --quick
    else
        log_warning "Script de teste não encontrado. Pule para teste manual."
    fi

    log_info "Teste manual recomendado:"
    echo "  1. Envie mensagem WhatsApp para bot: 'Oi'"
    echo "  2. Verifique se recebe menu com opções 1-5"
    echo "  3. Teste fluxo completo de coleta de dados"
    echo "  4. Confirme salvamento no PostgreSQL"
    echo ""
}

update_documentation() {
    log_info "Atualizando documentação..."

    # Update PROJECT_STATUS.md
    if [ -f "$PROJECT_ROOT/docs/PROJECT_STATUS.md" ]; then
        # Add deployment timestamp
        echo "" >> "$PROJECT_ROOT/docs/PROJECT_STATUS.md"
        echo "## Deploy v1 Simple" >> "$PROJECT_ROOT/docs/PROJECT_STATUS.md"
        echo "- **Data**: $(date '+%Y-%m-%d %H:%M:%S')" >> "$PROJECT_ROOT/docs/PROJECT_STATUS.md"
        echo "- **Versão**: v1.0 (Menu-based, sem Claude AI)" >> "$PROJECT_ROOT/docs/PROJECT_STATUS.md"
        echo "- **Backup**: $BACKUP_DIR" >> "$PROJECT_ROOT/docs/PROJECT_STATUS.md"
    fi

    log_success "Documentação atualizada"
}

display_summary() {
    echo ""
    echo "============================================================================"
    log_success "DEPLOY v1 CONCLUÍDO!"
    echo "============================================================================"
    echo ""
    echo "✅ Backup criado: $BACKUP_DIR"
    echo "✅ Workflow 02 v1 importado (menu-based)"
    echo "⚠️  Workflows 03 e 04 desabilitados (RAG + Vision AI)"
    echo ""
    echo "📊 Custos Mensais v1:"
    echo "  - Evolution API: R$ 50/mês"
    echo "  - Total: R$ 50/mês"
    echo ""
    echo "📈 Próximos Passos:"
    echo "  1. Testar bot com clientes reais"
    echo "  2. Coletar métricas de conversão"
    echo "  3. Planejar upgrade para v2 (com Claude AI)"
    echo "  4. Executar: ./scripts/upgrade-v1-to-v2.sh"
    echo ""
    echo "🔙 Para reverter:"
    echo "  ./scripts/rollback-to-v2.sh $BACKUP_DIR"
    echo ""
    echo "============================================================================"
}

# ============================================================================
# Main Execution
# ============================================================================

main() {
    echo ""
    echo "============================================================================"
    echo "  E2 Soluções Bot - Deploy v1 Simple (Menu-Based)"
    echo "============================================================================"
    echo ""

    log_warning "Este script irá:"
    echo "  1. Criar backup do Workflow 02 original (v2 com Claude AI)"
    echo "  2. Desabilitar Workflows 03 (RAG) e 04 (Vision AI)"
    echo "  3. Importar Workflow 02 v1 (menu-based)"
    echo "  4. Testar deployment"
    echo ""

    read -p "Deseja continuar? (s/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        log_warning "Deploy cancelado pelo usuário"
        exit 0
    fi

    check_prerequisites
    create_backup
    disable_ai_workflows
    import_v1_workflow
    test_deployment
    update_documentation
    display_summary
}

# Run main function
main "$@"
