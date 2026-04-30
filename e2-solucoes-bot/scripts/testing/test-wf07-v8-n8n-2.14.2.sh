#!/bin/bash
# Test WF07 V8 - n8n 2.14.2 Compatibility Fix
# Date: 2026-03-31

echo "🧪 WF07 V8 - n8n 2.14.2 Test"
echo "============================="
echo ""

echo "📋 Test Data (paste this in n8n UI Execute Workflow):"
echo ""

cat << 'EOF'
{
  "appointment_id": "86facc7a-e06d-4d4c-9fdb-2941d460fac3",
  "lead_email": "clima.cocal.2025@gmail.com",
  "lead_name": "bruno",
  "phone_number": "556181755748",
  "service_type": "energia_solar",
  "scheduled_date": "2026-04-01",
  "scheduled_time_start": "08:00:00",
  "scheduled_time_end": "10:00:00",
  "city": "cocal-go",
  "google_calendar_event_id": "1ucistntii2j145h4cn6f0ktak",
  "calendar_success": true
}
EOF

echo ""
echo "---"
echo ""

echo "🔧 CRITICAL CONFIG for n8n 2.14.2:"
echo ""
echo "Node: Read Template File"
echo ""
echo "✅ File(s) Selector: =/email-templates/{{ \$json.template_file }}"
echo "   (WITH '=' at the beginning)"
echo ""
echo "✅ Options: (LEAVE ALL EMPTY)"
echo "   ❌ DO NOT add 'Put Output File in Field'"
echo "   ❌ DO NOT add 'File Extension'"
echo "   ❌ DO NOT add 'File Name'"
echo "   ❌ DO NOT add 'Mime Type'"
echo ""
echo "---"
echo ""

echo "📊 Expected Execution Flow:"
echo ""
echo "1. Execute Workflow Trigger ✅"
echo "2. Prepare Email Data ✅"
echo "3. Read Template File ✅ (should output HTML in \$json.data)"
echo "4. Render Template ✅ (should process template variables)"
echo "5. Send Email (SMTP) ✅"
echo "6. Log Email Sent ✅"
echo "7. Return Success ✅"
echo ""

echo "🔍 Check Logs:"
echo ""
echo "docker logs e2bot-n8n-dev -f | grep -E 'Prepare Email Data|Read Template|Render Template V8'"
echo ""

echo "✅ Expected Logs:"
echo ""
echo "📧 [Prepare Email Data V3] Input source: { isFromWF05: true, ... }"
echo "📝 [Render Template V8] Template data received: { has_template_html: true, template_length: 7494, ... }"
echo "✅ [Render V8] Template rendered successfully: { html_length: 7494, text_length: 567 }"
echo ""

echo "============================="
echo "✅ Test Ready"
echo ""
echo "🎯 Next Steps:"
echo "1. Open http://localhost:5678/workflow/obkmrHruB7oQmVLT"
echo "2. Click 'Read Template File' node"
echo "3. Verify: File(s) Selector = =/email-templates/{{ \$json.template_file }}"
echo "4. Verify: Options = (all empty)"
echo "5. Save (Ctrl+S)"
echo "6. Execute with test data above"
echo "7. Check all 7 nodes execute successfully"
