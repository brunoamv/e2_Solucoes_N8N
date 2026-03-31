#!/usr/bin/env python3
"""
Generate WF02 V75 - Appointment Confirmation Message Fix
========================================================

CHANGES FROM V74.1:
- Replace `scheduling_redirect` template with personalized confirmation message
- Include appointment details (date, time, service, client data)
- Add Google Calendar link placeholder

Date: 2026-03-30
"""

import json
import sys
from pathlib import Path

# Configuration
BASE_V74_1 = Path(__file__).parent.parent / "n8n" / "workflows" / "02_ai_agent_conversation_V74.1_CHECK_IF_SCHEDULING_FIX.json"
OUTPUT_V75 = Path(__file__).parent.parent / "n8n" / "workflows" / "02_ai_agent_conversation_V75_APPOINTMENT_FINAL_MESSAGE.json"

# New template with real appointment data
NEW_SCHEDULING_REDIRECT_TEMPLATE = r"""✅ *Agendamento Confirmado com Sucesso!*

📅 *Detalhes da Visita Técnica:*
🗓️ Data: {{formatted_date}}
⏰ Horário: {{formatted_time_start}} às {{formatted_time_end}}
⏳ Duração: 2 horas
{{service_emoji}} Serviço: {{service_name}}

👤 Nome: {{name}}
📍 Cidade: {{city}}
📧 Confirmação enviada para: {{email}}

🔗 *Adicionar ao Calendário:*
{{google_calendar_link}}

_Obrigado por escolher a E2 Soluções!_"""

def generate_v75():
    """Generate V75 workflow with personalized appointment confirmation message."""

    print("=" * 70)
    print("GENERATE WF02 V75 - APPOINTMENT FINAL MESSAGE FIX")
    print("=" * 70)

    # Load V74.1
    print(f"\n✅ Loading base V74.1 from: {BASE_V74_1}")
    with open(BASE_V74_1, "r", encoding="utf-8") as f:
        workflow = json.load(f)

    # Update workflow metadata
    workflow["name"] = "02_ai_agent_conversation_V75_APPOINTMENT_FINAL_MESSAGE"

    # Find and update State Machine node
    state_machine_updated = False
    for node in workflow["nodes"]:
        if node.get("name") == "State Machine Logic":
            print(f"\n📝 Found State Machine node: {node['name']}")

            # Get current code
            js_code = node["parameters"]["functionCode"]

            # Replace the scheduling_redirect template
            # Find the template definition line
            old_template_start = js_code.find('"scheduling_redirect"')
            if old_template_start == -1:
                print("❌ ERROR: Could not find scheduling_redirect template!")
                sys.exit(1)

            # Find the end of this template (next template or closing brace)
            old_template_end = js_code.find('",\n\n  "handoff_comercial"', old_template_start)
            if old_template_end == -1:
                old_template_end = js_code.find('",\n\n  "handoff', old_template_start)

            if old_template_end == -1:
                print("❌ ERROR: Could not find end of scheduling_redirect template!")
                sys.exit(1)

            # Extract old template for logging
            old_template_full = js_code[old_template_start:old_template_end + 2]

            # Build new template definition
            new_template_def = f'  "scheduling_redirect": `{NEW_SCHEDULING_REDIRECT_TEMPLATE}`'

            # Replace in code
            js_code_new = js_code[:old_template_start] + new_template_def + js_code[old_template_end + 2:]

            # Now we need to UPDATE the case 'appointment_confirmation' to build the dynamic message
            # Find the line: responseText = templates.scheduling_redirect;
            appointment_case_start = js_code_new.find("case 'appointment_confirmation':")
            if appointment_case_start == -1:
                print("❌ ERROR: Could not find appointment_confirmation case!")
                sys.exit(1)

            # Find where responseText = templates.scheduling_redirect; is set
            response_line_start = js_code_new.find("responseText = templates.scheduling_redirect;", appointment_case_start)
            if response_line_start == -1:
                print("❌ ERROR: Could not find responseText assignment!")
                sys.exit(1)

            # Replace with dynamic template population
            dynamic_template_code = """// ===== V75: BUILD PERSONALIZED CONFIRMATION MESSAGE =====
      // Format date from DB (YYYY-MM-DD) to display (DD/MM/YYYY)
      const dbDate = currentData.scheduled_date || updateData.scheduled_date || '';
      let formattedDate = dbDate;
      if (dbDate && /^\\d{4}-\\d{2}-\\d{2}$/.test(dbDate)) {
        const [y, m, d] = dbDate.split('-');
        formattedDate = `${d}/${m}/${y}`;
      }

      // Format times (remove seconds)
      const startTime = currentData.scheduled_time_start || updateData.scheduled_time_start || '00:00:00';
      const endTime = currentData.scheduled_time_end || updateData.scheduled_time_end || '02:00:00';
      const formattedTimeStart = startTime.substring(0, 5); // HH:MM
      const formattedTimeEnd = endTime.substring(0, 5);     // HH:MM

      // Get service display info
      const serviceType = currentData.service_type || 'energia_solar';
      const serviceInfo = serviceDisplay[serviceType] || { emoji: '☀️', name: 'Energia Solar' };

      // Get client data
      const clientName = currentData.lead_name || 'Cliente';
      const clientEmail = currentData.email || 'não informado';
      const clientCity = currentData.city || 'não informado';

      // Build Google Calendar link (will be populated by WF05)
      const googleCalendarLink = '[Link será enviado por email]';

      // Populate template
      responseText = templates.scheduling_redirect
        .replace('{{formatted_date}}', formattedDate)
        .replace('{{formatted_time_start}}', formattedTimeStart)
        .replace('{{formatted_time_end}}', formattedTimeEnd)
        .replace('{{service_emoji}}', serviceInfo.emoji)
        .replace('{{service_name}}', serviceInfo.name)
        .replace('{{name}}', clientName)
        .replace('{{city}}', clientCity)
        .replace('{{email}}', clientEmail)
        .replace('{{google_calendar_link}}', googleCalendarLink);"""

            # Replace the single line with dynamic code
            response_line_end = js_code_new.find(";", response_line_start) + 1
            js_code_new = js_code_new[:response_line_start] + dynamic_template_code + js_code_new[response_line_end:]

            # Update node
            node["parameters"]["functionCode"] = js_code_new
            state_machine_updated = True

            print("✅ Updated State Machine node:")
            print(f"   - Replaced scheduling_redirect template")
            print(f"   - Added dynamic message builder in appointment_confirmation case")
            break

    if not state_machine_updated:
        print("❌ ERROR: State Machine node not found!")
        sys.exit(1)

    # Save V75
    print(f"\n💾 Saving V75 to: {OUTPUT_V75}")
    with open(OUTPUT_V75, "w", encoding="utf-8") as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 70)
    print("✅ V75 WORKFLOW GENERATED SUCCESSFULLY!")
    print("=" * 70)
    print(f"\n📁 Output: {OUTPUT_V75}")
    print("\n🎯 V75 Features:")
    print("   1. ✅ Personalized appointment confirmation message")
    print("   2. ✅ Real appointment details (date, time, service)")
    print("   3. ✅ Client information (name, city, email)")
    print("   4. ✅ Google Calendar link placeholder")
    print("   5. ✅ Professional message formatting")

    print("\n📝 Next Steps:")
    print("   1. Import 02_ai_agent_conversation_V75_APPOINTMENT_FINAL_MESSAGE.json to n8n")
    print("   2. Test with service 1 (Solar) or 3 (Projetos)")
    print("   3. Verify appointment confirmation message shows real data")
    print("   4. Deploy to production after validation")

    return 0

if __name__ == "__main__":
    sys.exit(generate_v75())
