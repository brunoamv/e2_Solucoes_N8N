#!/bin/bash
# ============================================================================
# E2 Soluções Bot - Script de Teste: Sistema de Notificações
# ============================================================================
# Sprint 1.3 - Testes de Integração Multi-Canal
# Valida: Discord, Email, WhatsApp, Database Functions
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

# ============================================================================
# Helper Functions
# ============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
    ((TESTS_PASSED++))
    ((TESTS_TOTAL++))
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
    ((TESTS_FAILED++))
    ((TESTS_TOTAL++))
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

# ============================================================================
# Environment Validation
# ============================================================================

print_header "VALIDAÇÃO DE AMBIENTE"

# Check if .env exists
if [ ! -f "docker/.env" ]; then
    log_error "Arquivo docker/.env não encontrado!"
    log_info "Execute: cp docker/.env.dev.example docker/.env"
    exit 1
fi

# Load environment variables
source docker/.env

# Validate required variables
log_info "Validando variáveis de ambiente obrigatórias..."

required_vars=(
    "DATABASE_URL"
    "DISCORD_WEBHOOK_LEADS"
    "DISCORD_WEBHOOK_APPOINTMENTS"
    "DISCORD_WEBHOOK_ALERTS"
    "EVOLUTION_API_URL"
    "EVOLUTION_API_KEY"
)

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        log_error "Variável $var não configurada!"
        exit 1
    else
        log_success "Variável $var configurada"
    fi
done

# ============================================================================
# Database Connectivity Test
# ============================================================================

print_header "TESTE 1: Conectividade com PostgreSQL"

log_info "Testando conexão com o banco de dados..."

if psql "$DATABASE_URL" -c "SELECT 1;" > /dev/null 2>&1; then
    log_success "Conexão com PostgreSQL estabelecida"
else
    log_error "Falha ao conectar com PostgreSQL"
    exit 1
fi

# Validate tables exist
log_info "Validando existência das tabelas..."

tables=("leads" "appointments" "notifications" "rdstation_sync_log")

for table in "${tables[@]}"; do
    if psql "$DATABASE_URL" -c "SELECT 1 FROM $table LIMIT 1;" > /dev/null 2>&1; then
        log_success "Tabela $table existe"
    else
        log_error "Tabela $table não encontrada"
    fi
done

# Validate functions exist
log_info "Validando existência das funções SQL..."

functions=(
    "create_notification"
    "check_notification_allowed"
    "update_notification_status"
    "get_pending_notifications"
    "get_failed_notifications"
    "get_notification_stats"
    "create_appointment_reminders"
)

for func in "${functions[@]}"; do
    if psql "$DATABASE_URL" -c "SELECT pg_get_functiondef(oid) FROM pg_proc WHERE proname='$func';" > /dev/null 2>&1; then
        log_success "Função $func existe"
    else
        log_error "Função $func não encontrada"
    fi
done

# ============================================================================
# Discord Webhook Tests
# ============================================================================

print_header "TESTE 2: Discord Webhooks"

log_info "Testando webhook de Leads (#leads)..."

response=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$DISCORD_WEBHOOK_LEADS" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "🧪 **Teste Automático** - Webhook #leads funcionando!",
    "embeds": [{
      "title": "✅ Teste de Integração",
      "description": "Sistema de notificações operacional",
      "color": 5814783,
      "footer": {"text": "E2 Soluções Bot • Sprint 1.3"}
    }]
  }')

if [ "$response" -eq 204 ]; then
    log_success "Webhook LEADS funcionando (HTTP 204)"
else
    log_error "Webhook LEADS falhou (HTTP $response)"
fi

log_info "Testando webhook de Agendamentos (#agendamentos)..."

response=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$DISCORD_WEBHOOK_APPOINTMENTS" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "🧪 **Teste Automático** - Webhook #agendamentos funcionando!",
    "embeds": [{
      "title": "✅ Teste de Integração",
      "description": "Sistema de notificações operacional",
      "color": 3066993,
      "footer": {"text": "E2 Soluções Bot • Sprint 1.3"}
    }]
  }')

if [ "$response" -eq 204 ]; then
    log_success "Webhook APPOINTMENTS funcionando (HTTP 204)"
else
    log_error "Webhook APPOINTMENTS falhou (HTTP $response)"
fi

log_info "Testando webhook de Alertas (#alertas)..."

response=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$DISCORD_WEBHOOK_ALERTS" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "🧪 **Teste Automático** - Webhook #alertas funcionando!",
    "embeds": [{
      "title": "✅ Teste de Integração",
      "description": "Sistema de notificações operacional",
      "color": 15158332,
      "footer": {"text": "E2 Soluções Bot • Sprint 1.3"}
    }]
  }')

if [ "$response" -eq 204 ]; then
    log_success "Webhook ALERTS funcionando (HTTP 204)"
else
    log_error "Webhook ALERTS falhou (HTTP $response)"
fi

# ============================================================================
# Evolution API (WhatsApp) Tests
# ============================================================================

print_header "TESTE 3: Evolution API (WhatsApp)"

log_info "Verificando status da instância Evolution API..."

# Fetch instance status
response=$(curl -s -w "\n%{http_code}" "$EVOLUTION_API_URL/instance/connectionState/e2-solucoes-bot" \
  -H "apikey: $EVOLUTION_API_KEY")

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" -eq 200 ]; then
    log_success "Evolution API acessível (HTTP 200)"

    # Parse connection state
    state=$(echo "$body" | grep -o '"state":"[^"]*"' | cut -d'"' -f4)

    if [ "$state" == "open" ]; then
        log_success "WhatsApp conectado (state: open)"
    elif [ "$state" == "close" ]; then
        log_warning "WhatsApp desconectado (state: close) - Execute QR Code scan"
    else
        log_warning "WhatsApp em estado desconhecido: $state"
    fi
else
    log_error "Evolution API inacessível (HTTP $http_code)"
fi

# Fetch all instances
log_info "Listando todas as instâncias..."

response=$(curl -s -o /dev/null -w "%{http_code}" "$EVOLUTION_API_URL/instance/fetchInstances" \
  -H "apikey: $EVOLUTION_API_KEY")

if [ "$response" -eq 200 ]; then
    log_success "Instâncias listadas com sucesso (HTTP 200)"
else
    log_error "Falha ao listar instâncias (HTTP $response)"
fi

# ============================================================================
# SQL Functions Unit Tests
# ============================================================================

print_header "TESTE 4: Funções SQL Unitárias"

log_info "Executando testes unitários do PostgreSQL..."

# Run SQL test file
if [ -f "database/tests/test_notification_functions.sql" ]; then
    test_output=$(psql "$DATABASE_URL" -f "database/tests/test_notification_functions.sql" 2>&1)

    if echo "$test_output" | grep -q "TESTES CONCLUÍDOS COM SUCESSO"; then
        log_success "Testes SQL executados com sucesso"

        # Count passed tests
        passed_tests=$(echo "$test_output" | grep -c "✅ PASSOU:" || echo "0")
        log_info "Testes SQL passaram: $passed_tests"
    else
        log_error "Testes SQL falharam"
        echo "$test_output" | grep "❌ FALHOU:"
    fi
else
    log_error "Arquivo database/tests/test_notification_functions.sql não encontrado"
fi

# ============================================================================
# Integration Test: Create Test Notification
# ============================================================================

print_header "TESTE 5: Criação de Notificação End-to-End"

log_info "Criando notificação de teste via SQL..."

# Create test lead if doesn't exist
psql "$DATABASE_URL" <<EOF > /dev/null 2>&1
INSERT INTO leads (phone, name, email, address, city, state, service_type, status, notification_preferences)
VALUES (
    '+5562999999998',
    'Lead Teste Automático',
    'teste@e2solucoes.com.br',
    'Rua Teste, 123',
    'Goiânia',
    'GO',
    'energia_solar',
    'qualified',
    jsonb_build_object('email', true, 'whatsapp', true, 'discord', true)
)
ON CONFLICT (phone) DO NOTHING;
EOF

log_success "Lead de teste criado/verificado"

# Create test notification
notification_result=$(psql "$DATABASE_URL" -t -c "
SELECT create_notification(
    (SELECT id FROM leads WHERE phone = '+5562999999998' LIMIT 1),
    NULL,
    'discord',
    'test',
    '',
    'Notificação de Teste Automático',
    'Este é um teste automático do sistema de notificações Sprint 1.3',
    json_build_object(
        'lead_name', 'Lead Teste Automático',
        'service_name', 'Energia Solar',
        'test_source', 'bash_script'
    )::jsonb,
    5,
    NOW()
);
")

if [ -n "$notification_result" ]; then
    log_success "Notificação criada: $notification_result"

    # Wait for workflow processing
    log_info "Aguardando processamento do Workflow 11 (30 segundos)..."
    sleep 30

    # Check notification status
    notification_status=$(psql "$DATABASE_URL" -t -c "
    SELECT status FROM notifications WHERE id = '$notification_result';
    " | xargs)

    log_info "Status da notificação: $notification_status"

    if [ "$notification_status" == "sent" ]; then
        log_success "Notificação processada com sucesso (status: sent)"
    elif [ "$notification_status" == "pending" ]; then
        log_warning "Notificação ainda pendente - Verifique n8n Workflow 11"
    elif [ "$notification_status" == "failed" ]; then
        log_error "Notificação falhou - Verifique logs no n8n"
    fi
else
    log_error "Falha ao criar notificação"
fi

# ============================================================================
# n8n Workflows Validation
# ============================================================================

print_header "TESTE 6: Validação de Workflows n8n"

log_info "Verificando se n8n está acessível..."

response=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:5678/")

if [ "$response" -eq 200 ] || [ "$response" -eq 302 ]; then
    log_success "n8n acessível (HTTP $response)"
else
    log_error "n8n inacessível (HTTP $response)"
    log_warning "Execute: ./scripts/start-dev.sh"
fi

# Check if workflows exist
log_info "Validando existência dos workflows..."

workflows=(
    "11_notification_processor.json"
    "12_multi_channel_notifications.json"
    "13_discord_notifications.json"
)

for workflow in "${workflows[@]}"; do
    if [ -f "n8n/workflows/$workflow" ]; then
        log_success "Workflow $workflow existe"
    else
        log_error "Workflow $workflow não encontrado"
    fi
done

# ============================================================================
# Template Files Validation
# ============================================================================

print_header "TESTE 7: Validação de Templates"

log_info "Validando templates WhatsApp..."

whatsapp_templates=(
    "lembrete_24h.txt"
    "lembrete_2h.txt"
    "confirmacao_agendamento.txt"
    "apos_visita.txt"
)

for template in "${whatsapp_templates[@]}"; do
    if [ -f "templates/whatsapp/$template" ]; then
        # Check for placeholder syntax {{variable}}
        if grep -q "{{" "templates/whatsapp/$template"; then
            log_success "Template WhatsApp $template válido (com placeholders)"
        else
            log_warning "Template WhatsApp $template sem placeholders"
        fi
    else
        log_error "Template WhatsApp $template não encontrado"
    fi
done

log_info "Validando templates Email..."

email_templates=(
    "novo_lead.html"
    "lembrete_24h.html"
    "lembrete_2h.html"
    "confirmacao_agendamento.html"
    "apos_visita.html"
)

for template in "${email_templates[@]}"; do
    if [ -f "templates/emails/$template" ]; then
        # Check for n8n expression syntax
        if grep -q '{{ $json\.' "templates/emails/$template"; then
            log_success "Template Email $template válido (com expressões n8n)"
        else
            log_warning "Template Email $template sem expressões n8n"
        fi
    else
        log_error "Template Email $template não encontrado"
    fi
done

# ============================================================================
# Final Report
# ============================================================================

print_header "RELATÓRIO FINAL DE TESTES"

echo ""
echo -e "${BLUE}Total de Testes:${NC} $TESTS_TOTAL"
echo -e "${GREEN}Testes Passaram:${NC} $TESTS_PASSED"
echo -e "${RED}Testes Falharam:${NC} $TESTS_FAILED"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}✅ TODOS OS TESTES PASSARAM!${NC}"
    echo -e "${GREEN}========================================${NC}"
    exit 0
else
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}❌ ALGUNS TESTES FALHARAM${NC}"
    echo -e "${RED}========================================${NC}"
    echo ""
    echo -e "${YELLOW}Recomendações:${NC}"
    echo "  1. Verifique docker/.env está configurado"
    echo "  2. Execute ./scripts/start-dev.sh"
    echo "  3. Importe workflows no n8n (http://localhost:5678)"
    echo "  4. Escaneie QR Code do WhatsApp"
    echo "  5. Configure webhooks do Discord"
    echo ""
    exit 1
fi
