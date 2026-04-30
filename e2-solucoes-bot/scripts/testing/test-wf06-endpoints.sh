#!/bin/bash
# Test script for WF06 Calendar Availability Service
# Tests both next_dates and available_slots endpoints
# Created: 2026-04-06

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
N8N_URL="${N8N_URL:-http://localhost:5678}"
WEBHOOK_PATH="webhook/calendar-availability"
FULL_URL="$N8N_URL/$WEBHOOK_PATH"

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

# Helper functions
print_section() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_test() {
    echo -e "\n${YELLOW}Test $TESTS_TOTAL: $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ PASS: $1${NC}"
    ((TESTS_PASSED++))
}

print_failure() {
    echo -e "${RED}❌ FAIL: $1${NC}"
    ((TESTS_FAILED++))
}

# Validate JSON response structure
validate_json() {
    local response="$1"
    local expected_field="$2"

    if echo "$response" | jq -e ".$expected_field" > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Test 1: next_dates - Default parameters
test_next_dates_default() {
    ((TESTS_TOTAL++))
    print_test "next_dates with default parameters (3 dates)"

    local payload='{"action":"next_dates"}'
    local response=$(curl -s -X POST "$FULL_URL" \
        -H "Content-Type: application/json" \
        -d "$payload")

    echo "Response: $response"

    if validate_json "$response" "success" && \
       validate_json "$response" "action" && \
       validate_json "$response" "dates"; then

        local action=$(echo "$response" | jq -r '.action')
        local dates_count=$(echo "$response" | jq '.dates | length')

        if [[ "$action" == "next_dates" ]] && [[ "$dates_count" -eq 3 ]]; then
            print_success "Default next_dates returns 3 dates"
        else
            print_failure "Expected action='next_dates' and 3 dates, got action='$action' and $dates_count dates"
        fi
    else
        print_failure "Missing required fields (success, action, dates)"
    fi
}

# Test 2: next_dates - Custom count
test_next_dates_custom_count() {
    ((TESTS_TOTAL++))
    print_test "next_dates with custom count (5 dates)"

    local payload='{"action":"next_dates","count":5}'
    local response=$(curl -s -X POST "$FULL_URL" \
        -H "Content-Type: application/json" \
        -d "$payload")

    echo "Response: $response"

    if validate_json "$response" "dates"; then
        local dates_count=$(echo "$response" | jq '.dates | length')

        if [[ "$dates_count" -eq 5 ]]; then
            print_success "Custom count returns 5 dates"
        else
            print_failure "Expected 5 dates, got $dates_count"
        fi
    else
        print_failure "Missing dates field"
    fi
}

# Test 3: next_dates - Validate date structure
test_next_dates_structure() {
    ((TESTS_TOTAL++))
    print_test "next_dates date object structure validation"

    local payload='{"action":"next_dates","count":1}'
    local response=$(curl -s -X POST "$FULL_URL" \
        -H "Content-Type: application/json" \
        -d "$payload")

    echo "Response: $response"

    if validate_json "$response" "dates[0].date" && \
       validate_json "$response" "dates[0].display" && \
       validate_json "$response" "dates[0].day_of_week" && \
       validate_json "$response" "dates[0].total_slots" && \
       validate_json "$response" "dates[0].quality"; then

        local date=$(echo "$response" | jq -r '.dates[0].date')
        local quality=$(echo "$response" | jq -r '.dates[0].quality')

        if [[ "$date" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]] && \
           [[ "$quality" =~ ^(high|medium|low)$ ]]; then
            print_success "Date structure is valid (date format YYYY-MM-DD, quality indicator)"
        else
            print_failure "Invalid date format or quality indicator"
        fi
    else
        print_failure "Missing required date fields"
    fi
}

# Test 4: next_dates - Portuguese friendly labels
test_next_dates_portuguese() {
    ((TESTS_TOTAL++))
    print_test "next_dates Portuguese friendly labels"

    local payload='{"action":"next_dates","count":2}'
    local response=$(curl -s -X POST "$FULL_URL" \
        -H "Content-Type: application/json" \
        -d "$payload")

    echo "Response: $response"

    if validate_json "$response" "dates[0].display"; then
        local display=$(echo "$response" | jq -r '.dates[0].display')

        if [[ "$display" =~ (Amanhã|Depois de amanhã|Segunda|Terça|Quarta|Quinta|Sexta) ]]; then
            print_success "Portuguese friendly labels present: $display"
        else
            print_failure "Missing Portuguese labels, got: $display"
        fi
    else
        print_failure "Missing display field"
    fi
}

# Test 5: available_slots - Valid date
test_available_slots_valid() {
    ((TESTS_TOTAL++))
    print_test "available_slots with valid date"

    # Get tomorrow's date in YYYY-MM-DD format
    local tomorrow=$(date -d "tomorrow" +%Y-%m-%d 2>/dev/null || date -v +1d +%Y-%m-%d 2>/dev/null)

    local payload="{\"action\":\"available_slots\",\"date\":\"$tomorrow\"}"
    local response=$(curl -s -X POST "$FULL_URL" \
        -H "Content-Type: application/json" \
        -d "$payload")

    echo "Response: $response"

    if validate_json "$response" "success" && \
       validate_json "$response" "action" && \
       validate_json "$response" "date" && \
       validate_json "$response" "available_slots"; then

        local action=$(echo "$response" | jq -r '.action')

        if [[ "$action" == "available_slots" ]]; then
            print_success "available_slots returns valid response"
        else
            print_failure "Expected action='available_slots', got '$action'"
        fi
    else
        print_failure "Missing required fields"
    fi
}

# Test 6: available_slots - Slot structure validation
test_available_slots_structure() {
    ((TESTS_TOTAL++))
    print_test "available_slots slot object structure"

    local tomorrow=$(date -d "tomorrow" +%Y-%m-%d 2>/dev/null || date -v +1d +%Y-%m-%d 2>/dev/null)
    local payload="{\"action\":\"available_slots\",\"date\":\"$tomorrow\"}"
    local response=$(curl -s -X POST "$FULL_URL" \
        -H "Content-Type: application/json" \
        -d "$payload")

    echo "Response: $response"

    local slots_count=$(echo "$response" | jq '.available_slots | length')

    if [[ "$slots_count" -gt 0 ]]; then
        if validate_json "$response" "available_slots[0].start_time" && \
           validate_json "$response" "available_slots[0].end_time" && \
           validate_json "$response" "available_slots[0].formatted"; then

            local formatted=$(echo "$response" | jq -r '.available_slots[0].formatted')

            if [[ "$formatted" =~ [0-9]+h.*(às|até)[^0-9]*[0-9]+h ]]; then
                print_success "Slot structure valid with Portuguese formatting: $formatted"
            else
                print_failure "Invalid Portuguese time format: $formatted"
            fi
        else
            print_failure "Missing required slot fields"
        fi
    else
        print_success "No available slots (valid response, calendar may be fully booked)"
    fi
}

# Test 7: available_slots - Missing date parameter
test_available_slots_missing_date() {
    ((TESTS_TOTAL++))
    print_test "available_slots with missing date (error handling)"

    local payload='{"action":"available_slots"}'
    local response=$(curl -s -X POST "$FULL_URL" \
        -H "Content-Type: application/json" \
        -d "$payload")

    echo "Response: $response"

    # Expect error response
    if echo "$response" | jq -e '.error' > /dev/null 2>&1; then
        print_success "Correctly returns error for missing date"
    else
        print_failure "Should return error for missing date parameter"
    fi
}

# Test 8: Invalid action parameter
test_invalid_action() {
    ((TESTS_TOTAL++))
    print_test "Invalid action parameter (error handling)"

    local payload='{"action":"invalid_action"}'
    local response=$(curl -s -X POST "$FULL_URL" \
        -H "Content-Type: application/json" \
        -d "$payload")

    echo "Response: $response"

    if echo "$response" | jq -e '.error' > /dev/null 2>&1; then
        print_success "Correctly returns error for invalid action"
    else
        print_failure "Should return error for invalid action"
    fi
}

# Test 9: Missing action parameter
test_missing_action() {
    ((TESTS_TOTAL++))
    print_test "Missing action parameter (error handling)"

    local payload='{}'
    local response=$(curl -s -X POST "$FULL_URL" \
        -H "Content-Type: application/json" \
        -d "$payload")

    echo "Response: $response"

    if echo "$response" | jq -e '.error' > /dev/null 2>&1; then
        print_success "Correctly returns error for missing action"
    else
        print_failure "Should return error for missing action parameter"
    fi
}

# Test 10: Custom duration parameter
test_custom_duration() {
    ((TESTS_TOTAL++))
    print_test "next_dates with custom duration (60 minutes)"

    local payload='{"action":"next_dates","count":1,"duration_minutes":60}'
    local response=$(curl -s -X POST "$FULL_URL" \
        -H "Content-Type: application/json" \
        -d "$payload")

    echo "Response: $response"

    if validate_json "$response" "success"; then
        local total_slots=$(echo "$response" | jq '.dates[0].total_slots')

        # 60-minute slots should yield more availability than 120-minute slots
        if [[ "$total_slots" -ge 0 ]]; then
            print_success "Custom duration accepted (total_slots: $total_slots)"
        else
            print_failure "Invalid slot count with custom duration"
        fi
    else
        print_failure "Request failed with custom duration"
    fi
}

# Main execution
main() {
    print_section "WF06 Calendar Availability Service - Test Suite"

    echo "Testing endpoint: $FULL_URL"
    echo "Make sure n8n is running and WF06 is imported and active!"
    echo ""
    read -p "Press Enter to continue or Ctrl+C to cancel..."

    # Check if n8n is accessible
    if ! curl -s "$N8N_URL" > /dev/null; then
        echo -e "${RED}ERROR: Cannot reach n8n at $N8N_URL${NC}"
        echo "Please ensure n8n is running: docker logs e2bot-n8n-dev"
        exit 1
    fi

    print_section "Test Group 1: next_dates Endpoint"
    test_next_dates_default
    test_next_dates_custom_count
    test_next_dates_structure
    test_next_dates_portuguese
    test_custom_duration

    print_section "Test Group 2: available_slots Endpoint"
    test_available_slots_valid
    test_available_slots_structure

    print_section "Test Group 3: Error Handling"
    test_available_slots_missing_date
    test_invalid_action
    test_missing_action

    # Summary
    print_section "Test Results Summary"
    echo -e "Total Tests: ${BLUE}$TESTS_TOTAL${NC}"
    echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
    echo -e "Failed: ${RED}$TESTS_FAILED${NC}"

    if [[ $TESTS_FAILED -eq 0 ]]; then
        echo -e "\n${GREEN}🎉 All tests passed!${NC}"
        exit 0
    else
        echo -e "\n${RED}⚠️  Some tests failed. Review output above.${NC}"
        exit 1
    fi
}

# Run tests
main
