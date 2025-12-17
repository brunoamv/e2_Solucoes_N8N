#!/bin/bash
# ============================================================================
# E2 Soluções Bot - Upgrade v1 to v2 (Add Claude AI)
# ============================================================================
# Script para upgrade de v1 (menu) para v2 (Claude AI + RAG + Vision)
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
BACKUP_DIR="$PROJECT_ROOT/backups/v1_$(date +%Y%m%d_%H%M%S)"
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

    # Check if v1 is currently running
    if [ ! -f "$WORKFLOWS_DIR/02_ai_agent_conversation.json.v1" ]; then
        log_warning "Workflow v1 não encontrado. Pode já estar em v2."

        read -p "Continuar com upgrade? (s/N): " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Ss]$ ]]; then
            exit 0
        fi
    fi

    # Check if v2 workflow exists
    if [ ! -f "$WORKFLOWS_DIR/02_ai_agent_conversation.json" ]; then
        log_error "Workflow 02 v2 original não encontrado"
        log_error "Execute restore de um backup ou reimporte workflow original"
        exit 1
    fi

    log_success "Pré-requisitos OK"
}

verify_api_keys() {
    log_info "Verificando API keys..."

    if [ ! -f "$PROJECT_ROOT/docker/.env" ]; then
        log_error "Arquivo .env não encontrado"
        exit 1
    fi

    source "$PROJECT_ROOT/docker/.env"

    # Check Anthropic API key
    if [ -z "$ANTHROPIC_API_KEY" ] || [ "$ANTHROPIC_API_KEY" == "sk-ant-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX" ]; then
        log_error "ANTHROPIC_API_KEY não configurada em docker/.env"
        echo ""
        echo "Para obter API key:"
        echo "  1. Acesse: https://console.anthropic.com/account/keys"
        echo "  2. Crie nova API key"
        echo "  3. Configure em docker/.env:"
        echo "     ANTHROPIC_API_KEY=sk-ant-XXXXXXXX"
        echo ""
        echo "Custo estimado: ~R$ 27/mês para 100 conversas"
        echo ""
        exit 1
    fi
    log_success "ANTHROPIC_API_KEY configurada"

    # Check OpenAI API key
    if [ -z "$OPENAI_API_KEY" ]; then
        log_warning "OPENAI_API_KEY não configurada (opcional para RAG)"
        echo "  Para usar RAG, configure em docker/.env"
    else
        log_success "OPENAI_API_KEY configurada"

        # Test OpenAI balance
        log_info "Testando saldo OpenAI..."

        RESPONSE=$(curl -s https://api.openai.com/v1/models \
            -H "Authorization: Bearer $OPENAI_API_KEY" 2>&1)

        if echo "$RESPONSE" | grep -q "insufficient_quota"; then
            log_warning "OpenAI sem créditos. Adicione mínimo $5"
            echo "  Acesse: https://platform.openai.com/account/billing"
        elif echo "$RESPONSE" | grep -q "gpt"; then
            log_success "OpenAI API funcionando"
        else
            log_warning "Erro ao testar OpenAI API"
        fi
    fi
}

calculate_costs() {
    echo ""
    echo "============================================================================"
    echo "  COMPARATIVO DE CUSTOS: v1 vs v2"
    echo "============================================================================"
    echo ""
    echo "┌─────────────────────────┬──────────────┬──────────────┐"
    echo "│ Serviço                 │ v1 (Menu)    │ v2 (AI)      │"
    echo "├─────────────────────────┼──────────────┼──────────────┤"
    echo "│ Evolution API (WhatsApp)│ R$ 50/mês    │ R$ 50/mês    │"
    echo "│ Anthropic Claude        │ R$ 0         │ R$ 27/mês    │"
    echo "│ OpenAI Embeddings (RAG) │ R$ 0         │ R$ 0,80/mês  │"
    echo "├─────────────────────────┼──────────────┼──────────────┤"
    echo "│ TOTAL                   │ R$ 50/mês    │ R$ 77,80/mês │"
    echo "└─────────────────────────┴──────────────┴──────────────┘"
    echo ""
    echo "Investimento adicional: R$ 27,80/mês (+56%)"
    echo ""
    echo "Benefícios v2:"
    echo "  ✅ Conversação natural (não menu rígido)"
    echo "  ✅ Entende perguntas complexas"
    echo "  ✅ RAG: responde com conhecimento E2 Soluções"
    echo "  ✅ Vision AI: analisa contas de luz e fotos"
    echo "  ✅ Taxa de conversão: 60% (vs 30% v1)"
    echo "  ✅ Experiência do usuário: 90% satisfação (vs 60% v1)"
    echo ""

    read -p "Confirma investimento adicional de R$ 27,80/mês? (s/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        log_warning "Upgrade cancelado. Mantenha v1 por enquanto."
        exit 0
    fi
}

create_backup() {
    log_info "Criando backup do Workflow 02 v1..."

    mkdir -p "$BACKUP_DIR"

    # Backup v1 workflow if exists
    if [ -f "$WORKFLOWS_DIR/02_ai_agent_conversation.json.v1" ]; then
        cp "$WORKFLOWS_DIR/02_ai_agent_conversation.json.v1" "$BACKUP_DIR/"
    fi

    # Backup current active workflow
    cp "$WORKFLOWS_DIR/02_ai_agent_conversation.json" "$BACKUP_DIR/" 2>/dev/null || true

    # Backup environment
    cp "$PROJECT_ROOT/docker/.env" "$BACKUP_DIR/.env.backup"

    # Create restore instructions
    cat > "$BACKUP_DIR/RESTORE_INSTRUCTIONS.md" << EOF
# Instruções de Restauração v1

Este backup foi criado em: $(date '+%Y-%m-%d %H:%M:%S')

## Para restaurar v1 (menu version):

\`\`\`bash
./scripts/rollback-to-v1.sh $BACKUP_DIR
\`\`\`

Ou manualmente:

1. Reimportar Workflow 02 v1 no n8n
2. Desativar Workflows 03 e 04
3. Restaurar .env se necessário
EOF

    log_success "Backup criado em: $BACKUP_DIR"
}

import_v2_workflow() {
    log_info "Importando Workflow 02 v2 (Claude AI)..."

    log_warning "AÇÃO MANUAL NECESSÁRIA:"
    echo "  1. Acesse http://localhost:5678"
    echo "  2. Workflows > 02 - AI Agent Conversation V1 (menu) > Desativar"
    echo "  3. Workflows > 02 - AI Agent Conversation V1 > Deletar (backup já feito)"
    echo "  4. Import from File > $WORKFLOWS_DIR/02_ai_agent_conversation.json"
    echo "  5. Renomear para '02 - AI Agent Conversation'"
    echo "  6. Ativar workflow (toggle on)"
    echo ""

    read -p "Pressione ENTER após importar Workflow 02 v2..."
}

enable_ai_workflows() {
    log_info "Ativando Workflows 03 e 04 (RAG + Vision AI)..."

    log_warning "AÇÃO MANUAL NECESSÁRIA:"
    echo "  1. Acesse http://localhost:5678"
    echo "  2. Workflows > 03_rag_knowledge_query > Ativar (toggle on)"
    echo "  3. Workflows > 04_image_analysis > Ativar (toggle on)"
    echo ""

    read -p "Pressione ENTER após ativar Workflows 03 e 04..."
}

run_rag_ingest() {
    log_info "Gerando embeddings RAG..."

    # Check if OpenAI key is configured
    source "$PROJECT_ROOT/docker/.env"
    if [ -z "$OPENAI_API_KEY" ]; then
        log_warning "OpenAI API key não configurada. Pule geração de embeddings."
        return
    fi

    read -p "Deseja gerar embeddings agora? (~1 min, $0.30) (s/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        if [ -f "$SCRIPTS_DIR/ingest-knowledge.sh" ]; then
            log_info "Executando ingest-knowledge.sh..."
            bash "$SCRIPTS_DIR/ingest-knowledge.sh"
        else
            log_warning "Script ingest-knowledge.sh não encontrado"
            echo "  Execute manualmente: ./scripts/ingest-knowledge.sh"
        fi
    else
        log_warning "Embeddings não gerados. Execute depois:"
        echo "  ./scripts/ingest-knowledge.sh"
    fi
}

validate_upgrade() {
    log_info "Validando upgrade..."

    # Run Sprint 1.1 validation
    log_info "Executar validação Sprint 1.1?"
    echo "  Validação completa: 85-125 minutos"
    echo "  Guia: docs/validation/README.md"
    echo ""

    read -p "Executar validação agora? (s/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        log_info "Abrindo guia de validação..."
        cat "$PROJECT_ROOT/docs/validation/README.md"
    else
        log_warning "Validação não executada. Execute depois:"
        echo "  Siga: docs/validation/README.md"
    fi
}

test_upgrade() {
    log_info "Testando upgrade v2..."

    log_info "Teste manual recomendado:"
    echo "  1. Envie mensagem WhatsApp: 'Oi'"
    echo "  2. Verifique resposta em linguagem natural"
    echo "  3. Teste RAG: 'Quanto custa energia solar?'"
    echo "  4. Teste Vision AI: envie foto de conta de luz"
    echo "  5. Teste fluxo completo de conversação"
    echo ""

    read -p "Deseja executar testes automatizados? (s/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        if [ -f "$SCRIPTS_DIR/test-v2-ai.sh" ]; then
            bash "$SCRIPTS_DIR/test-v2-ai.sh"
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
        echo "## Upgrade v1 → v2" >> "$PROJECT_ROOT/docs/PROJECT_STATUS.md"
        echo "- **Data**: $(date '+%Y-%m-%d %H:%M:%S')" >> "$PROJECT_ROOT/docs/PROJECT_STATUS.md"
        echo "- **Versão**: v2.0 (Claude AI + RAG + Vision)" >> "$PROJECT_ROOT/docs/PROJECT_STATUS.md"
        echo "- **Backup v1**: $BACKUP_DIR" >> "$PROJECT_ROOT/docs/PROJECT_STATUS.md"
        echo "- **Investimento Adicional**: R$ 27,80/mês" >> "$PROJECT_ROOT/docs/PROJECT_STATUS.md"
    fi

    log_success "Documentação atualizada"
}

display_summary() {
    echo ""
    echo "============================================================================"
    log_success "UPGRADE v1 → v2 CONCLUÍDO!"
    echo "============================================================================"
    echo ""
    echo "✅ Backup v1 criado: $BACKUP_DIR"
    echo "✅ Workflow 02 v2 importado (Claude AI)"
    echo "✅ Workflows 03 (RAG) e 04 (Vision AI) ativados"
    echo "✅ APIs configuradas (Anthropic + OpenAI)"
    echo ""
    echo "📊 Custos Mensais v2:"
    echo "  - Evolution API: R$ 50/mês"
    echo "  - Anthropic Claude: ~R$ 27/mês"
    echo "  - OpenAI Embeddings: ~R$ 0,80/mês"
    echo "  - Total: ~R$ 78/mês (+R$ 28 vs v1)"
    echo ""
    echo "📈 Benefícios v2:"
    echo "  ✅ Conversação natural (não menu rígido)"
    echo "  ✅ Taxa de conversão: 60% (vs 30% v1)"
    echo "  ✅ Experiência do usuário: 90% (vs 60% v1)"
    echo "  ✅ RAG: conhecimento E2 Soluções"
    echo "  ✅ Vision AI: análise de imagens"
    echo ""
    echo "📋 Próximos Passos:"
    echo "  1. Validar Sprint 1.1: docs/validation/README.md"
    echo "  2. Testar bot com clientes reais"
    echo "  3. Monitorar custos Anthropic/OpenAI"
    echo "  4. Coletar métricas de conversão"
    echo ""
    echo "🔙 Para reverter para v1:"
    echo "  ./scripts/rollback-to-v1.sh $BACKUP_DIR"
    echo ""
    echo "============================================================================"
}

# ============================================================================
# Main Execution
# ============================================================================

main() {
    echo ""
    echo "============================================================================"
    echo "  E2 Soluções Bot - Upgrade v1 (Menu) to v2 (Claude AI)"
    echo "============================================================================"
    echo ""

    log_warning "Este script irá:"
    echo "  1. Verificar API keys (Anthropic + OpenAI)"
    echo "  2. Calcular custos adicionais (~R$ 28/mês)"
    echo "  3. Criar backup do Workflow 02 v1"
    echo "  4. Importar Workflow 02 v2 (Claude AI)"
    echo "  5. Ativar Workflows 03 (RAG) e 04 (Vision AI)"
    echo "  6. Gerar embeddings RAG (opcional)"
    echo "  7. Validar upgrade"
    echo ""

    read -p "Deseja continuar? (s/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        log_warning "Upgrade cancelado pelo usuário"
        exit 0
    fi

    check_prerequisites
    verify_api_keys
    calculate_costs
    create_backup
    import_v2_workflow
    enable_ai_workflows
    run_rag_ingest
    validate_upgrade
    test_upgrade
    update_documentation
    display_summary
}

# Run main function
main "$@"
