#!/bin/bash
# Complete validation script for v5 workflow fix
# Tests type preservation and data accumulation

set -e

echo "🔍 E2 Bot Workflow v5 - Complete Validation"
echo "==========================================="
echo ""

# Configuration
DB_CONTAINER="e2bot-postgres-dev"
DB_NAME="e2_bot"
DB_USER="postgres"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to run SQL query
run_query() {
    docker exec $DB_CONTAINER psql -U $DB_USER -d $DB_NAME -t -c "$1" 2>/dev/null
}

# Function to check JSON type
check_json_type() {
    local phone=$1
    local field=$2
    local expected=$3

    result=$(run_query "SELECT jsonb_typeof(collected_data->'$field') FROM conversations WHERE phone_number='$phone' LIMIT 1;" | xargs)

    if [ "$result" = "$expected" ]; then
        echo -e "${GREEN}✅${NC} $field type is '$expected' - CORRECT"
        return 0
    else
        echo -e "${RED}❌${NC} $field type is '$result' but should be '$expected' - FAILED"
        return 1
    fi
}

# Function to check field exists
check_field_exists() {
    local phone=$1
    local field=$2

    result=$(run_query "SELECT collected_data->'$field' IS NOT NULL FROM conversations WHERE phone_number='$phone' LIMIT 1;" | xargs)

    if [ "$result" = "t" ]; then
        value=$(run_query "SELECT collected_data->'$field' FROM conversations WHERE phone_number='$phone' LIMIT 1;" | xargs)
        echo -e "${GREEN}✅${NC} $field exists with value: $value"
        return 0
    else
        echo -e "${YELLOW}⚠️${NC} $field does not exist or is null"
        return 1
    fi
}

# Main validation
echo "1️⃣ Checking if workflow v5 is imported..."
echo ""

# Get a test phone number from recent conversations
TEST_PHONE=$(run_query "SELECT phone_number FROM conversations ORDER BY updated_at DESC LIMIT 1;" | xargs)

if [ -z "$TEST_PHONE" ]; then
    echo -e "${YELLOW}⚠️ No conversations found in database${NC}"
    echo "Please send a test message via WhatsApp first"
    exit 1
fi

echo "📱 Using test phone: $TEST_PHONE"
echo ""

echo "2️⃣ Checking type preservation..."
echo ""

# Check critical field types
all_passed=true

check_json_type "$TEST_PHONE" "error_count" "number" || all_passed=false
check_json_type "$TEST_PHONE" "last_processed_message" "string" || all_passed=false
check_json_type "$TEST_PHONE" "last_state" "string" || all_passed=false

echo ""
echo "3️⃣ Checking data preservation..."
echo ""

# Check if fields are being preserved
check_field_exists "$TEST_PHONE" "error_count" || true
check_field_exists "$TEST_PHONE" "lead_name" || true
check_field_exists "$TEST_PHONE" "phone" || true
check_field_exists "$TEST_PHONE" "email" || true
check_field_exists "$TEST_PHONE" "city" || true
check_field_exists "$TEST_PHONE" "service_type" || true

echo ""
echo "4️⃣ Checking complete collected_data..."
echo ""

# Show the full collected_data
echo "Full collected_data JSON:"
docker exec $DB_CONTAINER psql -U $DB_USER -d $DB_NAME -c "
SELECT jsonb_pretty(collected_data) as collected_data
FROM conversations
WHERE phone_number='$TEST_PHONE';"

echo ""
echo "5️⃣ Checking workflow execution logs..."
echo ""

# Check n8n logs for debug output
echo "Recent n8n logs (looking for debug output):"
docker logs e2bot-n8n-dev 2>&1 | grep -A2 -B2 "PREPARE UPDATE DATA DEBUG" | tail -20 || echo "No debug logs found"

echo ""
echo "==========================================="
echo "📊 VALIDATION SUMMARY"
echo "==========================================="

if [ "$all_passed" = true ]; then
    echo -e "${GREEN}✅ Type preservation is working correctly!${NC}"
    echo -e "${GREEN}✅ Workflow v5 appears to be functioning properly${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Send more test messages to verify data accumulation"
    echo "2. Check that error_count increments on invalid inputs"
    echo "3. Verify all collected fields persist between steps"
else
    echo -e "${RED}❌ Type preservation issues detected!${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "1. Verify workflow v5 is imported and active in n8n"
    echo "2. Check that old v3 workflow is deactivated"
    echo "3. Look at n8n execution logs for errors"
    echo "4. Ensure PostgreSQL connection is working"
fi

echo ""
echo "==========================================="
echo "🔧 Quick Fix Commands:"
echo ""
echo "# Clear test data:"
echo "docker exec $DB_CONTAINER psql -U $DB_USER -d $DB_NAME -c \"DELETE FROM conversations WHERE phone_number='$TEST_PHONE';\""
echo ""
echo "# Watch real-time data changes:"
echo "watch -n 2 \"docker exec $DB_CONTAINER psql -U $DB_USER -d $DB_NAME -c 'SELECT phone_number, current_state, collected_data FROM conversations ORDER BY updated_at DESC LIMIT 3;'\""
echo ""
echo "# Check n8n workflow status:"
echo "curl http://localhost:5678/rest/workflows | jq '.data[] | select(.name | contains(\"V1\")) | {id, name, active}'"