#!/bin/bash
# Test collected_data type handling from PostgreSQL

set -e

echo "🔍 Testing collected_data type handling..."
echo "=========================================="
echo ""

# Create a test conversation with proper data
echo "1️⃣ Creating test conversation with full data..."
docker exec e2bot-postgres-dev psql -U postgres -d e2_bot -c "
INSERT INTO conversations (phone_number, current_state, collected_data)
VALUES (
    '5511999999999',
    'collecting_lead_name',
    '{\"error_count\": 0, \"lead_name\": \"João Silva\", \"phone\": \"11999999999\"}'::jsonb
)
ON CONFLICT (phone_number)
DO UPDATE SET
    collected_data = '{\"error_count\": 0, \"lead_name\": \"João Silva\", \"phone\": \"11999999999\"}'::jsonb,
    current_state = 'collecting_lead_name';
"

echo ""
echo "2️⃣ Querying collected_data as returned from PostgreSQL..."
docker exec e2bot-postgres-dev psql -U postgres -d e2_bot -c "
SELECT
    phone_number,
    current_state,
    collected_data,
    pg_typeof(collected_data) as pg_type,
    jsonb_typeof(collected_data) as jsonb_type,
    jsonb_typeof(collected_data->'error_count') as error_count_type
FROM conversations
WHERE phone_number = '5511999999999';
"

echo ""
echo "3️⃣ Testing JSON stringification (how n8n might receive it)..."
docker exec e2bot-postgres-dev psql -U postgres -d e2_bot -t -c "
SELECT collected_data::text
FROM conversations
WHERE phone_number = '5511999999999';
" | head -1

echo ""
echo "4️⃣ Testing if JSONB comes as object or string..."
docker exec e2bot-postgres-dev psql -U postgres -d e2_bot -c "
SELECT
    collected_data,
    jsonb_typeof(collected_data) as type,
    collected_data->'lead_name' as lead_name_value,
    collected_data->>'lead_name' as lead_name_text
FROM conversations
WHERE phone_number = '5511999999999';
"

echo ""
echo "✅ Test complete!"
echo ""
echo "📋 Analysis:"
echo "- If 'pg_type' = 'jsonb', PostgreSQL is storing correctly"
echo "- If 'jsonb_type' = 'object', the structure is correct"
echo "- If 'lead_name_value' shows \"João Silva\", data is preserved"
echo "- Problem may be in how n8n PostgreSQL node returns the data"
