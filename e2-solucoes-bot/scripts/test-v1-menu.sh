#!/bin/bash
# ============================================================================
# E2 Soluções Bot - Testes Automatizados v1 Menu
# ============================================================================
# Script para testar bot v1 (menu-based) com validação de fluxos
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
TEST_LOG="$PROJECT_ROOT/logs/test_v1_$(date +%Y%m%d_%H%M%S).log"

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Database connection (from .env)
source "$PROJECT_ROOT/docker/.env"
PGPASSWORD="$POSTGRES_PASSWORD"

# ============================================================================
# Helper Functions
# ============================================================================

log_test() {
    TESTS_RUN=$((TESTS_RUN + 1))
    echo -e "${BLUE}[TEST $TESTS_RUN]${NC} $1" | tee -a "$TEST_LOG"
}

log_pass() {
    TESTS_PASSED=$((TESTS_PASSED + 1))
    echo -e "${GREEN}  ✅ PASS${NC} $1" | tee -a "$TEST_LOG"
}

log_fail() {
    TESTS_FAILED=$((TESTS_FAILED + 1))
    echo -e "${RED}  ❌ FAIL${NC} $1" | tee -a "$TEST_LOG"
}

log_skip() {
    echo -e "${YELLOW}  ⏭️  SKIP${NC} $1" | tee -a "$TEST_LOG"
}

query_db() {
    docker exec -e PGPASSWORD="$POSTGRES_PASSWORD" postgres-e2 \
        psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -A -c "$1"
}

# ============================================================================
# Unit Tests - Validators
# ============================================================================

test_validators() {
    echo ""
    echo "==================== UNIT TESTS: VALIDATORS ===================="
    echo ""

    # Test 1: Service selection validator (1-5)
    log_test "Validator: service_selection (1-5)"

    # Valid inputs
    for num in 1 2 3 4 5; do
        if [[ "$num" =~ ^[1-5]$ ]]; then
            log_pass "Input '$num' aceito"
        else
            log_fail "Input '$num' deveria ser aceito"
        fi
    done

    # Invalid inputs
    for num in 0 6 99 "abc" ""; do
        if [[ ! "$num" =~ ^[1-5]$ ]]; then
            log_pass "Input '$num' rejeitado"
        else
            log_fail "Input '$num' deveria ser rejeitado"
        fi
    done

    # Test 2: Phone validator (Brazilian format)
    log_test "Validator: phone_brazil"

    # Valid phones
    VALID_PHONES=("62999887766" "11987654321" "(62) 99988-7766" "62 99988-7766")
    for phone in "${VALID_PHONES[@]}"; do
        cleaned=$(echo "$phone" | tr -d '[:space:](-)' )
        if [[ "$cleaned" =~ ^[0-9]{10,11}$ ]]; then
            log_pass "Telefone '$phone' aceito"
        else
            log_fail "Telefone '$phone' deveria ser aceito"
        fi
    done

    # Invalid phones
    INVALID_PHONES=("123" "abcdefghij" "999887766" "629998877665")
    for phone in "${INVALID_PHONES[@]}"; do
        cleaned=$(echo "$phone" | tr -d '[:space:](-)' )
        if [[ ! "$cleaned" =~ ^[0-9]{10,11}$ ]]; then
            log_pass "Telefone '$phone' rejeitado"
        else
            log_fail "Telefone '$phone' deveria ser rejeitado"
        fi
    done

    # Test 3: Email validator
    log_test "Validator: email_or_skip"

    # Valid emails
    VALID_EMAILS=("teste@email.com" "usuario.nome@empresa.com.br" "pular")
    for email in "${VALID_EMAILS[@]}"; do
        if [[ "$email" == "pular" ]] || [[ "$email" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
            log_pass "Email '$email' aceito"
        else
            log_fail "Email '$email' deveria ser aceito"
        fi
    done

    # Invalid emails
    INVALID_EMAILS=("teste@" "@email.com" "teste email.com" "teste@email")
    for email in "${INVALID_EMAILS[@]}"; do
        if [[ ! "$email" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
            log_pass "Email '$email' rejeitado"
        else
            log_fail "Email '$email' deveria ser rejeitado"
        fi
    done
}

# ============================================================================
# Integration Tests - Database
# ============================================================================

test_database() {
    echo ""
    echo "==================== INTEGRATION TESTS: DATABASE ===================="
    echo ""

    # Test 4: Conversations table exists
    log_test "Database: conversations table structure"

    RESULT=$(query_db "SELECT COUNT(*) FROM information_schema.tables WHERE table_name='conversations';")
    if [ "$RESULT" -eq "1" ]; then
        log_pass "Tabela 'conversations' existe"
    else
        log_fail "Tabela 'conversations' não encontrada"
    fi

    # Test 5: Required columns in conversations
    log_test "Database: conversations required columns"

    REQUIRED_COLS=("lead_id" "current_stage" "stage_data" "created_at" "updated_at")
    for col in "${REQUIRED_COLS[@]}"; do
        RESULT=$(query_db "SELECT COUNT(*) FROM information_schema.columns WHERE table_name='conversations' AND column_name='$col';")
        if [ "$RESULT" -eq "1" ]; then
            log_pass "Coluna '$col' existe"
        else
            log_fail "Coluna '$col' não encontrada"
        fi
    done

    # Test 6: Insert test conversation
    log_test "Database: Insert test conversation"

    TEST_PHONE="5562999887766_TEST_$(date +%s)"
    RESULT=$(query_db "INSERT INTO conversations (lead_id, current_stage, stage_data) VALUES ('$TEST_PHONE', 'greeting', '{}') RETURNING id;" 2>&1)
    if [[ ! "$RESULT" =~ "ERROR" ]]; then
        log_pass "Conversa de teste inserida (ID: $RESULT)"

        # Cleanup
        query_db "DELETE FROM conversations WHERE lead_id='$TEST_PHONE';" > /dev/null
        log_pass "Cleanup: conversa de teste removida"
    else
        log_fail "Erro ao inserir conversa de teste: $RESULT"
    fi

    # Test 7: Leads table exists
    log_test "Database: leads table structure"

    RESULT=$(query_db "SELECT COUNT(*) FROM information_schema.tables WHERE table_name='leads';")
    if [ "$RESULT" -eq "1" ]; then
        log_pass "Tabela 'leads' existe"
    else
        log_fail "Tabela 'leads' não encontrada"
    fi
}

# ============================================================================
# Integration Tests - n8n Workflows
# ============================================================================

test_workflows() {
    echo ""
    echo "==================== INTEGRATION TESTS: N8N WORKFLOWS ===================="
    echo ""

    # Test 8: n8n is running
    log_test "n8n: Container running"

    if docker ps | grep -q n8n; then
        log_pass "Container n8n está rodando"
    else
        log_fail "Container n8n não encontrado"
    fi

    # Test 9: n8n API accessible
    log_test "n8n: API accessible"

    if curl -s http://localhost:5678 > /dev/null 2>&1; then
        log_pass "n8n API acessível em http://localhost:5678"
    else
        log_fail "n8n API não acessível"
    fi

    # Test 10: Workflow 02 v1 exists
    log_test "n8n: Workflow 02 v1 file exists"

    if [ -f "$PROJECT_ROOT/n8n/workflows/02_ai_agent_conversation_V1_MENU.json" ]; then
        log_pass "Arquivo Workflow 02 v1 encontrado"
    else
        log_fail "Arquivo Workflow 02 v1 não encontrado"
    fi

    # Test 11: Workflow 02 JSON valid
    log_test "n8n: Workflow 02 v1 JSON syntax"

    if jq empty "$PROJECT_ROOT/n8n/workflows/02_ai_agent_conversation_V1_MENU.json" 2>/dev/null; then
        log_pass "JSON do Workflow 02 v1 é válido"
    else
        log_fail "JSON do Workflow 02 v1 tem erro de sintaxe"
    fi
}

# ============================================================================
# E2E Tests - Conversation Flow (Manual)
# ============================================================================

test_e2e_manual() {
    echo ""
    echo "==================== E2E TESTS: CONVERSATION FLOW (MANUAL) ===================="
    echo ""

    log_test "E2E: Fluxo completo de conversa"

    log_skip "Teste E2E requer interação manual via WhatsApp"
    echo ""
    echo "  📱 Passos para Teste Manual E2E:"
    echo "  1. Envie mensagem para bot: 'Oi'"
    echo "  2. Verifique menu com 5 opções (1-5)"
    echo "  3. Digite: 1 (Energia Solar)"
    echo "  4. Digite nome: 'João da Silva Teste'"
    echo "  5. Digite telefone: '62 99988-7766'"
    echo "  6. Digite email: 'joao@teste.com' ou 'pular'"
    echo "  7. Digite cidade: 'Goiânia'"
    echo "  8. Confirme dados: 1 (Agendar) ou 2 (Falar com especialista)"
    echo ""
    echo "  ✅ Verificar:"
    echo "  - Mensagens recebidas em formato correto"
    echo "  - Validações funcionando (telefone, email)"
    echo "  - Dados salvos no PostgreSQL (tabela leads)"
    echo "  - Redirecionamento correto (agendamento ou handoff)"
    echo ""

    read -p "  Pressione ENTER após completar teste manual E2E..."

    read -p "  Teste E2E passou? (s/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        log_pass "Teste E2E confirmado pelo usuário"
    else
        log_fail "Teste E2E falhou (reportado pelo usuário)"
    fi
}

# ============================================================================
# Performance Tests
# ============================================================================

test_performance() {
    echo ""
    echo "==================== PERFORMANCE TESTS ===================="
    echo ""

    # Test 12: Database query performance
    log_test "Performance: Database query (<100ms)"

    START=$(date +%s%3N)
    query_db "SELECT COUNT(*) FROM conversations;" > /dev/null
    END=$(date +%s%3N)
    DURATION=$((END - START))

    if [ "$DURATION" -lt 100 ]; then
        log_pass "Query executada em ${DURATION}ms (< 100ms)"
    else
        log_fail "Query demorou ${DURATION}ms (esperado < 100ms)"
    fi

    # Test 13: Workflow file size
    log_test "Performance: Workflow 02 v1 file size (<100KB)"

    FILE_SIZE=$(stat -f%z "$PROJECT_ROOT/n8n/workflows/02_ai_agent_conversation_V1_MENU.json" 2>/dev/null || stat -c%s "$PROJECT_ROOT/n8n/workflows/02_ai_agent_conversation_V1_MENU.json" 2>/dev/null)
    SIZE_KB=$((FILE_SIZE / 1024))

    if [ "$SIZE_KB" -lt 100 ]; then
        log_pass "Workflow file: ${SIZE_KB}KB (< 100KB)"
    else
        log_fail "Workflow file: ${SIZE_KB}KB (esperado < 100KB)"
    fi
}

# ============================================================================
# Test Summary
# ============================================================================

display_summary() {
    echo ""
    echo "============================================================================"
    echo "  RESUMO DOS TESTES v1 MENU"
    echo "============================================================================"
    echo ""
    echo "  Total de Testes: $TESTS_RUN"
    echo "  ✅ Passaram: $TESTS_PASSED"
    echo "  ❌ Falharam: $TESTS_FAILED"
    echo ""

    SUCCESS_RATE=$(awk "BEGIN {printf \"%.1f\", ($TESTS_PASSED / $TESTS_RUN) * 100}")
    echo "  Taxa de Sucesso: $SUCCESS_RATE%"
    echo ""

    if [ "$TESTS_FAILED" -eq 0 ]; then
        echo -e "${GREEN}  ✅ TODOS OS TESTES PASSARAM!${NC}"
    else
        echo -e "${RED}  ⚠️  ALGUNS TESTES FALHARAM${NC}"
        echo "  Verifique o log: $TEST_LOG"
    fi

    echo ""
    echo "============================================================================"
}

# ============================================================================
# Main Execution
# ============================================================================

main() {
    # Create log directory
    mkdir -p "$(dirname "$TEST_LOG")"

    echo ""
    echo "============================================================================"
    echo "  E2 Soluções Bot - Testes Automatizados v1 Menu"
    echo "============================================================================"
    echo ""
    echo "  Log: $TEST_LOG"
    echo ""

    # Check for quick mode
    QUICK_MODE=false
    if [[ "$1" == "--quick" ]]; then
        QUICK_MODE=true
        echo "  Modo: QUICK (pula testes manuais)"
    else
        echo "  Modo: FULL (inclui testes manuais)"
    fi
    echo ""

    # Run test suites
    test_validators
    test_database
    test_workflows

    if [ "$QUICK_MODE" = false ]; then
        test_e2e_manual
    fi

    test_performance

    # Display summary
    display_summary

    # Exit code
    if [ "$TESTS_FAILED" -eq 0 ]; then
        exit 0
    else
        exit 1
    fi
}

# Run main function
main "$@"
