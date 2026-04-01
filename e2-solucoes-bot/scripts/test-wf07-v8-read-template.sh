#!/bin/bash
# Test WF07 V8 - Read Template File Configuration
# Date: 2026-03-31

echo "🔍 Testing WF07 V8 Template Reading"
echo "===================================="
echo ""

# Test 1: Verify template files exist
echo "✅ Test 1: Template files in container"
docker exec e2bot-n8n-dev ls -lh /email-templates/

echo ""
echo "---"
echo ""

# Test 2: Verify file readability
echo "✅ Test 2: Read first template (confirmacao_agendamento.html)"
docker exec e2bot-n8n-dev head -10 /email-templates/confirmacao_agendamento.html

echo ""
echo "---"
echo ""

# Test 3: Check n8n Read/Write File node syntax
echo "📝 Test 3: Node 'Read Template File' Configuration"
echo ""
echo "   Expected filePath syntax: =/email-templates/{{ \$json.template_file }}"
echo "   ✅ '=' prefix: Indicates n8n expression"
echo "   ✅ '/email-templates/': Container path (NOT host path)"
echo "   ✅ '{{ \$json.template_file }}': Variable from previous node"
echo ""
echo "   Common ERRORS:"
echo "   ❌ WITHOUT '=': Treats as literal string '/email-templates/{{ \$json.template_file }}'"
echo "   ❌ Host path: '../email-templates/...' (WRONG - this is host, not container)"
echo "   ❌ Double braces in UI: Some versions require {{ }} not {{}}"
echo ""

# Test 4: Check if Prepare Email Data outputs template_file
echo "✅ Test 4: Verify 'Prepare Email Data' outputs template_file"
echo ""
echo "   The 'Prepare Email Data' node MUST output:"
echo "   {

    \"template_file\": \"confirmacao_agendamento.html\","
echo "     ..."
echo "   }"
echo ""

# Test 5: Manual trigger test
echo "🧪 Test 5: Manual WF07 V8 Trigger (for testing)"
echo ""
echo "curl -X POST http://localhost:5678/webhook/test-email \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{"
echo "    \"lead_email\": \"test@example.com\","
echo "    \"lead_name\": \"Test User\","
echo "    \"service_type\": \"energia_solar\","
echo "    \"scheduled_date\": \"2026-04-01\","
echo "    \"scheduled_time_start\": \"10:00:00\","
echo "    \"scheduled_time_end\": \"12:00:00\","
echo "    \"appointment_id\": 999,"
echo "    \"calendar_success\": true"
echo "  }'"
echo ""

# Test 6: Check recent WF07 executions
echo "📊 Test 6: Recent WF07 V8 executions"
docker logs e2bot-n8n-dev 2>&1 | grep -E "Prepare Email Data V3|Read Template|Render Template V8" | tail -20

echo ""
echo "===================================="
echo "✅ Tests Complete"
echo ""
echo "🔧 Next Steps:"
echo "   1. Open n8n UI: http://localhost:5678/workflow/obkmrHruB7oQmVLT"
echo "   2. Click 'Read Template File' node"
echo "   3. Verify 'File(s) Selector' field shows: =/email-templates/{{ \$json.template_file }}"
echo "   4. If different, UPDATE to this exact value"
echo "   5. Save workflow and test execution"
