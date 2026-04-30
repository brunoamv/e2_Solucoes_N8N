#!/bin/bash
# Complete test for collected_data preservation after fix

set -e

PHONE="5562981755485"

echo "🧪 E2 Bot - Complete collected_data Preservation Test"
echo "====================================================="
echo ""

echo "1️⃣ Cleaning up test data..."
docker exec e2bot-postgres-dev psql -U postgres -d e2_bot -c "
DELETE FROM conversations WHERE phone_number IN ('$PHONE', 'undefined', '5511999999999');"

echo ""
echo "2️⃣ Creating initial conversation with data..."
docker exec e2bot-postgres-dev psql -U postgres -d e2_bot -c "
INSERT INTO conversations (phone_number, current_state, collected_data)
VALUES (
    '$PHONE',
    'coletando_dados',
    '{\"error_count\": 0, \"lead_name\": \"João Silva\", \"phone\": \"62981755485\"}'::jsonb
);"

echo ""
echo "3️⃣ Verifying initial data..."
docker exec e2bot-postgres-dev psql -U postgres -d e2_bot -c "
SELECT
    phone_number,
    current_state,
    jsonb_pretty(collected_data) as data,
    jsonb_typeof(collected_data->'error_count') as error_count_type
FROM conversations
WHERE phone_number = '$PHONE';"

echo ""
echo "4️⃣ Simulating State Machine update (adding email)..."
docker exec e2bot-postgres-dev psql -U postgres -d e2_bot -c "
UPDATE conversations
SET
    collected_data = collected_data || '{\"email\": \"joao@example.com\"}'::jsonb,
    current_state = 'coletando_dados'
WHERE phone_number = '$PHONE'
RETURNING jsonb_pretty(collected_data);"

echo ""
echo "5️⃣ Verifying data preservation after update..."
docker exec e2bot-postgres-dev psql -U postgres -d e2_bot -c "
SELECT
    phone_number,
    current_state,
    jsonb_pretty(collected_data) as data,
    jsonb_object_keys(collected_data) as all_keys
FROM conversations
WHERE phone_number = '$PHONE';"

echo ""
echo "6️⃣ Testing type preservation..."
docker exec e2bot-postgres-dev psql -U postgres -d e2_bot -c "
SELECT
    jsonb_typeof(collected_data->'error_count') as error_count_type,
    jsonb_typeof(collected_data->'lead_name') as lead_name_type,
    jsonb_typeof(collected_data->'phone') as phone_type,
    jsonb_typeof(collected_data->'email') as email_type,
    (collected_data->'error_count')::int as error_count_value
FROM conversations
WHERE phone_number = '$PHONE';"

echo ""
echo "7️⃣ Checking n8n logs for debug output..."
echo "(Last 20 lines containing COLLECTED DATA)"
docker logs e2bot-n8n-dev 2>&1 | grep "COLLECTED DATA" -A5 | tail -20 || echo "No debug logs found yet"

echo ""
echo "✅ Test complete!"
echo ""
echo "📋 Validation Checklist:"
echo "  ✓ All fields present in collected_data? (lead_name, phone, email)"
echo "  ✓ error_count type = 'number' (not 'string')?"
echo "  ✓ Data preserved after update?"
echo "  ✓ Debug logs show correct parsing?"
echo ""
echo "🔧 Next steps:"
echo "1. Apply Safe JSON Parsing fix to State Machine Logic"
echo "2. Send real WhatsApp message to test end-to-end"
echo "3. Re-run this script to verify"
