#!/bin/bash
# Manual Test - WF07 V8 Complete Flow
# Date: 2026-03-31
# Purpose: Test WF07 V8 with manual trigger to identify exact failure point

echo "🧪 WF07 V8 - Manual Trigger Test"
echo "=================================="
echo ""

# Get WF05 latest appointment data for realistic test
echo "📋 Step 1: Get latest appointment data from WF05"
APPOINTMENT_DATA=$(docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -t -c "
SELECT json_build_object(
  'appointment_id', a.id,
  'lead_email', l.email,
  'lead_name', l.name,
  'phone_number', l.phone_number,
  'service_type', a.service_type,
  'scheduled_date', a.scheduled_date,
  'scheduled_time_start', a.scheduled_time_start,
  'scheduled_time_end', a.scheduled_time_end,
  'city', l.city,
  'google_calendar_event_id', a.google_calendar_event_id,
  'calendar_success', true
)
FROM appointments a
JOIN leads l ON a.lead_id = l.id
WHERE a.status = 'confirmado'
ORDER BY a.created_at DESC
LIMIT 1;
" | tr -d '[:space:]')

if [ -z "$APPOINTMENT_DATA" ] || [ "$APPOINTMENT_DATA" = "null" ]; then
    echo "❌ No appointment data found in database"
    echo "   Creating test data..."

    APPOINTMENT_DATA='{
        "appointment_id": 999,
        "lead_email": "test@example.com",
        "lead_name": "Test User",
        "phone_number": "556181755748",
        "service_type": "energia_solar",
        "scheduled_date": "2026-04-01",
        "scheduled_time_start": "10:00:00",
        "scheduled_time_end": "12:00:00",
        "city": "Brasilia",
        "google_calendar_event_id": "test123",
        "calendar_success": true
    }'
else
    echo "✅ Found appointment data:"
    echo "$APPOINTMENT_DATA" | jq '.'
fi

echo ""
echo "---"
echo ""

# Step 2: Trigger WF07 V8 manually via Execute Workflow
echo "🚀 Step 2: Trigger WF07 V8 manually"
echo ""
echo "   Using n8n CLI to execute workflow obkmrHruB7oQmVLT with data:"
echo "   $APPOINTMENT_DATA" | jq '.'
echo ""

# Note: n8n doesn't have CLI execution, we need to use HTTP or database
echo "⚠️  Manual Execution Steps:"
echo ""
echo "   1. Open n8n UI: http://localhost:5678/workflow/obkmrHruB7oQmVLT"
echo "   2. Click 'Execute Workflow' button"
echo "   3. In 'Execute Workflow Trigger' dialog, paste this data:"
echo ""
echo "$APPOINTMENT_DATA" | jq '.'
echo ""
echo "   4. Click 'Execute' and observe each node:"
echo ""
echo "      Node 1: Execute Workflow Trigger (should receive data)"
echo "      Node 2: Prepare Email Data (should output template_file, subject, etc)"
echo "      Node 3: Read Template File (should read /email-templates/confirmacao_agendamento.html)"
echo "      Node 4: Render Template (should process HTML with template_data)"
echo "      Node 5: Send Email (SMTP) - should send email"
echo "      Node 6: Log Email Sent - should insert into email_logs"
echo "      Node 7: Return Success - should return success message"
echo ""
echo "---"
echo ""

# Step 3: Check what went wrong
echo "📊 Step 3: After manual execution, check logs:"
echo ""
echo "   docker logs e2bot-n8n-dev -f | grep -E 'Prepare Email Data|Read Template|Render Template V8'"
echo ""
echo "   Expected logs if WORKING:"
echo "   📧 [Prepare Email Data V3] Input source: { isFromWF05: true, ... }"
echo "   📝 [Render Template V8] Template data received: { has_template_html: true, ... }"
echo "   ✅ [Render V8] Template rendered successfully: { html_length: 7494, ... }"
echo ""
echo "   If NO LOGS appear:"
echo "   → Workflow NOT executing nodes"
echo "   → Check if workflow is ACTIVE in n8n UI"
echo "   → Check if Execute Workflow Trigger is configured correctly"
echo ""

echo "=================================="
echo "✅ Manual Test Script Ready"
echo ""
echo "🔧 CRITICAL CHECKS:"
echo ""
echo "   1. Node 'Read Template File' configuration:"
echo "      ✅ File(s) Selector: =/email-templates/{{ \$json.template_file }}"
echo "      ✅ Options > Property Name: data"
echo "      ✅ Options > Encoding: utf8"
echo ""
echo "   2. Node 'Render Template' Code node line 6:"
echo "      ✅ const templateHtml = \$('Read Template File').first().json.data;"
echo ""
echo "   3. Workflow connections (verify in UI):"
echo "      Execute Workflow Trigger → Prepare Email Data"
echo "      Prepare Email Data → Read Template File"
echo "      Read Template File → Render Template"
echo "      Render Template → Send Email (SMTP)"
echo ""
