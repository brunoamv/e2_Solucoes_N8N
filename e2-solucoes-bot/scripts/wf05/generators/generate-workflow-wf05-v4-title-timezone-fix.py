#!/usr/bin/env python3
"""
Generate WF05 V4.0 - Title and Timezone Fix
============================================

CHANGES FROM V3.6:
1. FIX TIMEZONE: Create Date objects in America/Sao_Paulo timezone
2. FIX TITLE: Improved event title with client name and formatted service
3. ADD: Service name formatting helper function

PROBLEMS SOLVED:
- Calendar showing 05:00-07:00 instead of 08:00-10:00 (UTC vs BRT issue)
- Generic title "Agendamento E2 Soluções - energia_solar"
- Title now: "Visita Técnica: Energia Solar - Bruno Rosa"

Date: 2026-03-30
"""

import json
import sys
from pathlib import Path

# Configuration
BASE_V3_6 = Path(__file__).parent.parent / "n8n" / "workflows" / "05_appointment_scheduler_v3.6.json"
OUTPUT_V4_0 = Path(__file__).parent.parent / "n8n" / "workflows" / "05_appointment_scheduler_v4.0.json"

# Service name mapping (matches WF02)
SERVICE_NAME_MAP = {
    "energia_solar": "Energia Solar",
    "subestacao": "Subestação",
    "projeto_eletrico": "Projetos Elétricos",
    "armazenamento_energia": "BESS (Armazenamento)",
    "analise_laudo": "Análise e Laudos"
}

def generate_v4_0():
    """Generate V4.0 workflow with timezone and title fixes."""

    print("=" * 70)
    print("GENERATE WF05 V4.0 - TITLE AND TIMEZONE FIX")
    print("=" * 70)

    # Load V3.6
    print(f"\n✅ Loading base V3.6 from: {BASE_V3_6}")
    with open(BASE_V3_6, "r", encoding="utf-8") as f:
        workflow = json.load(f)

    # Update workflow metadata
    workflow["name"] = "05_appointment_scheduler_v4.0"

    # Find and update Build Calendar Event Data node
    build_calendar_updated = False
    for node in workflow["nodes"]:
        if node.get("name") == "Build Calendar Event Data":
            print(f"\n📝 Found Build Calendar Event Data node: {node['name']}")

            # Get current code
            js_code = node["parameters"]["jsCode"]

            # Build new code with timezone fix
            new_js_code = """// Build Calendar Event Data - V4.0 FIX (Timezone + Title)
const data = $input.first().json;

try {
    // ===== SERVICE NAME HELPER =====
    function formatServiceName(serviceType) {
        const serviceMap = {
            'energia_solar': 'Energia Solar',
            'subestacao': 'Subestação',
            'projeto_eletrico': 'Projetos Elétricos',
            'armazenamento_energia': 'BESS (Armazenamento)',
            'analise_laudo': 'Análise e Laudos'
        };
        return serviceMap[serviceType] || serviceType;
    }

    // ===== NORMALIZE DATE AND TIME =====
    const scheduledDateRaw = data.scheduled_date;
    const timeStartRaw = data.scheduled_time_start;
    const timeEndRaw = data.scheduled_time_end;

    // ===== FIX: Extract date part from ISO strings =====
    let dateString;
    if (scheduledDateRaw instanceof Date) {
        dateString = scheduledDateRaw.toISOString().split('T')[0];
    } else if (typeof scheduledDateRaw === 'string' && scheduledDateRaw.includes('T')) {
        dateString = scheduledDateRaw.split('T')[0];
    } else {
        dateString = scheduledDateRaw;
    }

    const timeStart = typeof timeStartRaw === 'string'
        ? timeStartRaw
        : timeStartRaw?.toString() || '00:00:00';

    const timeEnd = typeof timeEndRaw === 'string'
        ? timeEndRaw
        : timeEndRaw?.toString() || '00:00:00';

    console.log('📅 [Build Calendar V4] Normalized:', {
        original_date: scheduledDateRaw,
        extracted_date: dateString,
        timeStart,
        timeEnd
    });

    // ===== V4.0 FIX: CREATE DATE IN BRAZIL TIMEZONE =====
    // PROBLEM: new Date("2026-04-01T08:00:00") creates UTC Date
    // SOLUTION: Create date string with explicit timezone offset

    // Brazil timezone offset: UTC-3 (BRT - Brasília Time)
    const brazilOffset = '-03:00';

    // Build ISO strings with timezone
    const startDateTimeISO = `${dateString}T${timeStart}${brazilOffset}`;
    const endDateTimeISO = `${dateString}T${timeEnd}${brazilOffset}`;

    const startDateTime = new Date(startDateTimeISO);
    const endDateTime = new Date(endDateTimeISO);

    console.log('📅 [Build Calendar V4] DateTime with Brazil timezone:', {
        start_iso_input: startDateTimeISO,
        end_iso_input: endDateTimeISO,
        start_utc_output: startDateTime.toISOString(),
        end_utc_output: endDateTime.toISOString(),
        start_valid: !isNaN(startDateTime.getTime()),
        end_valid: !isNaN(endDateTime.getTime())
    });

    if (isNaN(startDateTime.getTime()) || isNaN(endDateTime.getTime())) {
        throw new Error('Invalid date/time format: ' + JSON.stringify({
            dateString,
            timeStart,
            timeEnd,
            startDateTimeISO,
            endDateTimeISO
        }));
    }

    // ===== V4.0 FIX: IMPROVED TITLE =====
    const serviceName = formatServiceName(data.service_type || 'energia_solar');
    const clientName = data.lead_name || 'Cliente';

    const improvedTitle = `Visita Técnica: ${serviceName} - ${clientName}`;

    console.log('📝 [Build Calendar V4] Improved title:', improvedTitle);

    // ===== BUILD CALENDAR EVENT =====
    const calendarEvent = {
        summary: improvedTitle,  // ✅ V4.0: Better title
        description: `
Cliente: ${data.lead_name || 'N/A'}
Telefone: ${data.phone_number || 'N/A'}
Email: ${data.lead_email || 'N/A'}
Serviço: ${serviceName}
Cidade: ${data.city || 'N/A'}
Detalhes: ${data.service_details || 'N/A'}
Observações: ${data.notes || 'Agendamento via WhatsApp Bot - Cliente: ' + (data.lead_name || 'N/A') + ' | Cidade: ' + (data.city || 'N/A')}
        `.trim(),
        location: `${data.address || ''}, ${data.city || ''}, ${data.state || ''}`.trim(),
        start: {
            dateTime: startDateTime.toISOString(),  // ✅ V4.0: Correct Brazil time
            timeZone: 'America/Sao_Paulo'
        },
        end: {
            dateTime: endDateTime.toISOString(),  // ✅ V4.0: Correct Brazil time
            timeZone: 'America/Sao_Paulo'
        },
        attendees: data.lead_email ? [{ email: data.lead_email }] : [],  // ✅ V3.6: Fixed attendees format
        reminders: {
            useDefault: false,
            overrides: [
                { method: 'email', minutes: 24 * 60 },
                { method: 'popup', minutes: 30 }
            ]
        },
        colorId: '9'
    };

    console.log('✅ [Build Calendar V4] Event created:', {
        summary: calendarEvent.summary,
        start_brazil_time: startDateTimeISO,
        start_utc: calendarEvent.start.dateTime,
        end_brazil_time: endDateTimeISO,
        end_utc: calendarEvent.end.dateTime
    });

    return {
        ...data,
        calendar_event: calendarEvent
    };

} catch (error) {
    console.error('❌ [Build Calendar V4] Error:', error.message);
    console.error('Data received:', JSON.stringify(data, null, 2));
    throw error;
}"""

            # Update node
            node["parameters"]["jsCode"] = new_js_code
            build_calendar_updated = True

            print("✅ Updated Build Calendar Event Data node:")
            print(f"   - Added timezone offset (-03:00) to Date creation")
            print(f"   - Improved event title format")
            print(f"   - Added service name formatting helper")
            break

    if not build_calendar_updated:
        print("❌ ERROR: Build Calendar Event Data node not found!")
        sys.exit(1)

    # Save V4.0
    print(f"\n💾 Saving V4.0 to: {OUTPUT_V4_0}")
    with open(OUTPUT_V4_0, "w", encoding="utf-8") as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 70)
    print("✅ V4.0 WORKFLOW GENERATED SUCCESSFULLY!")
    print("=" * 70)
    print(f"\n📁 Output: {OUTPUT_V4_0}")
    print("\n🎯 V4.0 Features:")
    print("   1. ✅ TIMEZONE FIX: Date created with -03:00 offset (Brazil time)")
    print("   2. ✅ TITLE FIX: 'Visita Técnica: Energia Solar - Bruno Rosa'")
    print("   3. ✅ Service name formatting helper function")
    print("   4. ✅ Maintains V3.6 attendees array fix")

    print("\n📊 Before vs After:")
    print("\n   BEFORE V3.6:")
    print("      Title: 'Agendamento E2 Soluções - energia_solar'")
    print("      Time: 05:00-07:00 (UTC conversion issue)")
    print("\n   AFTER V4.0:")
    print("      Title: 'Visita Técnica: Energia Solar - Bruno Rosa'")
    print("      Time: 08:00-10:00 (Correct Brazil time)")

    print("\n📝 Next Steps:")
    print("   1. Import 05_appointment_scheduler_v4.0.json to n8n")
    print("   2. Test appointment creation")
    print("   3. Verify Google Calendar shows:")
    print("      - Correct title with client name")
    print("      - Correct time (08:00-10:00)")
    print("   4. Deploy to production after validation")

    return 0

if __name__ == "__main__":
    sys.exit(generate_v4_0())
