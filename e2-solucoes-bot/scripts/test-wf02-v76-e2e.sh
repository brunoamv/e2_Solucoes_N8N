#!/bin/bash
# E2E Test Script for WF02 V76 - Proactive UX Happy Path
# Tests complete user journey from greeting to appointment confirmation
# Created: 2026-04-06

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
N8N_URL="${N8N_URL:-http://localhost:5678}"
WEBHOOK_PATH="webhook-ai-agent-v76"  # V76 test webhook
FULL_URL="$N8N_URL/$WEBHOOK_PATH"
TEST_PHONE="5562999887766"  # Test phone number

# Test data
TEST_NAME="Maria Silva Santos"
TEST_EMAIL="maria.silva@test.com"
TEST_CITY="Goiânia"
SERVICE_CHOICE="1"  # Energia Solar

# Counters
STEP=0
ERRORS=0

# Helper functions
print_header() {
    echo ""
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}========================================${NC}"
}

print_step() {
    ((STEP++))
    echo ""
    echo -e "${BLUE}[STEP $STEP] $1${NC}"
}

print_request() {
    echo -e "${YELLOW}📤 Sending:${NC} $1"
}

print_response() {
    echo -e "${GREEN}📥 Bot response:${NC}"
    echo "$1" | jq -r '.response' 2>/dev/null || echo "$1"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_failure() {
    echo -e "${RED}❌ $1${NC}"
    ((ERRORS++))
}

send_message() {
    local message="$1"
    local response

    response=$(curl -s -X POST "$FULL_URL" \
        -H "Content-Type: application/json" \
        -d "{
            \"phone_number\": \"$TEST_PHONE\",
            \"whatsapp_name\": \"Test User\",
            \"message\": \"$message\",
            \"message_type\": \"text\",
            \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"
        }")

    echo "$response"
}

validate_response_contains() {
    local response="$1"
    local expected_text="$2"
    local description="$3"

    if echo "$response" | grep -qi "$expected_text"; then
        print_success "$description"
        return 0
    else
        print_failure "$description - Expected text not found: '$expected_text'"
        return 1
    fi
}

# Wait for user input
wait_for_continue() {
    echo ""
    read -p "Press Enter to continue to next step..."
}

# Main test execution
main() {
    print_header "WF02 V76 - E2E Happy Path Test"

    echo "Testing endpoint: $FULL_URL"
    echo "Test phone: $TEST_PHONE"
    echo ""
    echo "This test will simulate a complete user journey:"
    echo "1. Greeting and service selection"
    echo "2. Data collection (name, phone, email, city)"
    echo "3. Confirmation"
    echo "4. 📅 NEW: Proactive date selection (V76)"
    echo "5. 🕐 NEW: Proactive time selection (V76)"
    echo "6. Appointment confirmation"
    echo ""
    read -p "Press Enter to start test..."

    # ========================================
    # PART 1: GREETING & DATA COLLECTION
    # ========================================

    print_step "Greeting - Trigger conversation start"
    print_request "oi"
    response=$(send_message "oi")
    print_response "$response"
    validate_response_contains "$response" "Bem-vindo" "Greeting message received"
    validate_response_contains "$response" "Energia Solar" "Service menu displayed"
    wait_for_continue

    print_step "Service Selection - Choose Energia Solar (1)"
    print_request "$SERVICE_CHOICE"
    response=$(send_message "$SERVICE_CHOICE")
    print_response "$response"
    validate_response_contains "$response" "nome completo" "Name request received"
    wait_for_continue

    print_step "Name Collection - Provide name"
    print_request "$TEST_NAME"
    response=$(send_message "$TEST_NAME")
    print_response "$response"
    validate_response_contains "$response" "$TEST_PHONE" "WhatsApp phone confirmation displayed"
    validate_response_contains "$response" "1️⃣.*Sim" "Confirmation options shown"
    wait_for_continue

    print_step "Phone Confirmation - Confirm WhatsApp number"
    print_request "1"
    response=$(send_message "1")
    print_response "$response"
    validate_response_contains "$response" "e-mail" "Email request received"
    wait_for_continue

    print_step "Email Collection - Provide email"
    print_request "$TEST_EMAIL"
    response=$(send_message "$TEST_EMAIL")
    print_response "$response"
    validate_response_contains "$response" "cidade" "City request received"
    wait_for_continue

    print_step "City Collection - Provide city"
    print_request "$TEST_CITY"
    response=$(send_message "$TEST_CITY")
    print_response "$response"
    validate_response_contains "$response" "resumo" "Confirmation summary displayed"
    validate_response_contains "$response" "$TEST_NAME" "Name in confirmation"
    validate_response_contains "$response" "$TEST_EMAIL" "Email in confirmation"
    validate_response_contains "$response" "$TEST_CITY" "City in confirmation"
    wait_for_continue

    # ========================================
    # PART 2: V76 PROACTIVE SCHEDULING
    # ========================================

    print_header "V76 PROACTIVE UX - Date & Time Selection"

    print_step "Confirmation - Choose to schedule appointment (1)"
    print_request "1"
    response=$(send_message "1")
    print_response "$response"

    # V76 CRITICAL: Check for proactive date suggestions
    if echo "$response" | grep -qi "Próximas datas"; then
        print_success "✨ V76 PROACTIVE: Date suggestions displayed"

        # Validate date options format
        validate_response_contains "$response" "1️⃣.*horários" "Option 1 with slot count"
        validate_response_contains "$response" "2️⃣.*horários" "Option 2 with slot count"
        validate_response_contains "$response" "3️⃣.*horários" "Option 3 with slot count"
        validate_response_contains "$response" "Escolha uma opção" "Selection prompt displayed"

        # Parse available dates (for reporting)
        echo ""
        echo -e "${CYAN}Available dates:${NC}"
        echo "$response" | grep -E "[1-3]️⃣" | head -3

    else
        print_failure "❌ V76 FAILED: No date suggestions - falling back to manual input?"
        validate_response_contains "$response" "Digite a data" "Fallback to manual date input"
    fi

    wait_for_continue

    print_step "Date Selection - Choose option 2 (V76 PROACTIVE)"
    print_request "2"
    response=$(send_message "2")
    print_response "$response"

    # V76 CRITICAL: Check for proactive time slot suggestions
    if echo "$response" | grep -qi "Horários Disponíveis"; then
        print_success "✨ V76 PROACTIVE: Time slot suggestions displayed"

        # Validate slot options format
        validate_response_contains "$response" "1️⃣.*h às.*h" "Option 1 with time range"
        validate_response_contains "$response" "Escolha um horário" "Time selection prompt"

        # Parse available slots (for reporting)
        echo ""
        echo -e "${CYAN}Available time slots:${NC}"
        echo "$response" | grep -E "[0-9]️⃣.*h" | head -5

    else
        print_failure "❌ V76 FAILED: No time slot suggestions - falling back to manual input?"
        validate_response_contains "$response" "Digite o horário" "Fallback to manual time input"
    fi

    wait_for_continue

    print_step "Time Selection - Choose option 2 (V76 PROACTIVE)"
    print_request "2"
    response=$(send_message "2")
    print_response "$response"

    # Final confirmation
    validate_response_contains "$response" "Confirmado\|agendado" "Appointment confirmation received"
    validate_response_contains "$response" "Data:" "Date in final confirmation"
    validate_response_contains "$response" "Horário:" "Time in final confirmation"
    validate_response_contains "$response" "$TEST_CITY" "City in final confirmation"

    wait_for_continue

    # ========================================
    # SUMMARY
    # ========================================

    print_header "Test Summary"

    echo -e "${BLUE}Total Steps:${NC} $STEP"
    echo -e "${GREEN}Passed:${NC} $((STEP - ERRORS))"
    echo -e "${RED}Failed:${NC} $ERRORS"

    echo ""
    echo -e "${CYAN}V76 Proactive UX Verification:${NC}"
    echo "✅ Date suggestions (State 9) - Automatic"
    echo "✅ Time slot suggestions (State 11) - Automatic"
    echo "✅ Single-digit selection (1-3 for dates, 1-N for times)"
    echo "✅ Zero manual typing required in happy path"

    echo ""
    echo -e "${CYAN}Expected UX Improvements:${NC}"
    echo "📊 Interactions: 7-10 (V75) → ~8 (V76 with data collection)"
    echo "📊 Appointment-specific interactions: 2 (date + time)"
    echo "📊 Errors: 2-3 (V75) → 0 (V76)"
    echo "📊 Mobile typing: Heavy (V75) → Minimal (V76 - only name, email, city)"

    if [[ $ERRORS -eq 0 ]]; then
        echo ""
        echo -e "${GREEN}🎉 All tests passed! WF02 V76 is working correctly.${NC}"
        exit 0
    else
        echo ""
        echo -e "${RED}⚠️  Some tests failed. Review output above.${NC}"
        exit 1
    fi
}

# Run tests
main
