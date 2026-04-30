#!/usr/bin/env python3
"""
Script: generate-appointment-scheduler-v3.2.py
Purpose: Fix ISO date string handling in Build Calendar Event Data
Date: 2026-03-24

CRITICAL FIX:
Problem: PostgreSQL returns DATE as "2026-04-25T00:00:00.000Z" (ISO with time)
Current code: Assumes string is "YYYY-MM-DD" format
Result: Invalid DateTime "2026-04-25T00:00:00.000ZT08:00:00" ❌

Solution: Always extract date part from ISO strings before concatenation
"""

import json
import sys
from pathlib import Path

# Colors for terminal output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_step(step_num, total, message):
    """Print formatted step progress"""
    print(f"{BLUE}[{step_num}/{total}]{RESET} {message}")

def print_success(message):
    """Print success message"""
    print(f"{GREEN}✅ {message}{RESET}")

def print_warning(message):
    """Print warning message"""
    print(f"{YELLOW}⚠️  {message}{RESET}")

def print_error(message):
    """Print error message"""
    print(f"{RED}❌ {message}{RESET}")

def load_v3_1_workflow():
    """Load V3.1 workflow JSON"""
    v3_1_path = Path(__file__).parent.parent / "n8n" / "workflows" / "05_appointment_scheduler_v3.1.json"

    print_step(1, 3, "Loading V3.1 workflow...")

    if not v3_1_path.exists():
        print_error(f"V3.1 workflow not found: {v3_1_path}")
        sys.exit(1)

    with open(v3_1_path, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    print_success(f"Loaded V3.1 workflow: {len(workflow['nodes'])} nodes")
    return workflow

def fix_build_calendar_event_date_handling(workflow):
    """Fix Build Calendar Event Data ISO date handling"""
    print_step(2, 3, "Fixing Build Calendar Event Data ISO date handling...")

    # Find node
    node = None
    for n in workflow['nodes']:
        if n['name'] == 'Build Calendar Event Data':
            node = n
            break

    if not node:
        print_error("Build Calendar Event Data node not found!")
        sys.exit(1)

    print(f"  Current issue: ISO date string creates invalid DateTime")
    print(f"  Example: '2026-04-25T00:00:00.000Z' + 'T08:00:00' = Invalid ❌")

    # NEW CODE: Handle ISO date strings correctly
    new_code = """// Build Calendar Event Data - V3.2 FIX (ISO Date Handling)
const data = $input.first().json;

try {
    // ===== NORMALIZE DATE AND TIME =====
    const scheduledDateRaw = data.scheduled_date;
    const timeStartRaw = data.scheduled_time_start;
    const timeEndRaw = data.scheduled_time_end;

    // ===== FIX: Extract date part from ISO strings =====
    // PostgreSQL may return DATE as "2026-04-25T00:00:00.000Z" (ISO string with time)
    let dateString;

    if (scheduledDateRaw instanceof Date) {
        // If Date object, convert to YYYY-MM-DD
        dateString = scheduledDateRaw.toISOString().split('T')[0];
    } else if (typeof scheduledDateRaw === 'string' && scheduledDateRaw.includes('T')) {
        // If ISO string (contains 'T'), extract date part
        dateString = scheduledDateRaw.split('T')[0];
    } else {
        // Already in YYYY-MM-DD format (or other string format)
        dateString = scheduledDateRaw;
    }

    const timeStart = typeof timeStartRaw === 'string'
        ? timeStartRaw
        : timeStartRaw?.toString() || '00:00:00';

    const timeEnd = typeof timeEndRaw === 'string'
        ? timeEndRaw
        : timeEndRaw?.toString() || '00:00:00';

    console.log('📅 [Build Calendar] Normalized:', {
        original_date: scheduledDateRaw,
        extracted_date: dateString,
        timeStart,
        timeEnd
    });

    // ===== BUILD DATETIME =====
    const startDateTime = new Date(`${dateString}T${timeStart}`);
    const endDateTime = new Date(`${dateString}T${timeEnd}`);

    console.log('📅 [Build Calendar] DateTime constructed:', {
        start_string: `${dateString}T${timeStart}`,
        end_string: `${dateString}T${timeEnd}`,
        start_valid: !isNaN(startDateTime.getTime()),
        end_valid: !isNaN(endDateTime.getTime())
    });

    if (isNaN(startDateTime.getTime()) || isNaN(endDateTime.getTime())) {
        throw new Error('Invalid date/time format: ' + JSON.stringify({
            dateString,
            timeStart,
            timeEnd,
            start_result: startDateTime.toString(),
            end_result: endDateTime.toString()
        }));
    }

    // ===== BUILD CALENDAR EVENT =====
    const calendarEvent = {
        summary: `Agendamento E2 Soluções - ${data.service_type || 'Serviço'}`,
        description: `
Cliente: ${data.lead_name || 'N/A'}
Telefone: ${data.phone_number || 'N/A'}
Email: ${data.lead_email || 'N/A'}
Serviço: ${data.service_type || 'N/A'}
Cidade: ${data.city || 'N/A'}
Detalhes: ${data.service_details || 'N/A'}
Observações: ${data.notes || 'N/A'}
        `.trim(),
        location: `${data.address || ''}, ${data.city || ''}, ${data.state || ''}`.trim(),
        start: {
            dateTime: startDateTime.toISOString(),
            timeZone: $env.CALENDAR_TIMEZONE || 'America/Sao_Paulo'
        },
        end: {
            dateTime: endDateTime.toISOString(),
            timeZone: $env.CALENDAR_TIMEZONE || 'America/Sao_Paulo'
        },
        attendees: data.lead_email ? [{ email: data.lead_email }] : [],
        reminders: {
            useDefault: false,
            overrides: [
                { method: 'email', minutes: 24 * 60 },
                { method: 'popup', minutes: 30 }
            ]
        },
        colorId: '9'
    };

    console.log('✅ [Build Calendar] Event created:', {
        summary: calendarEvent.summary,
        start: calendarEvent.start.dateTime,
        end: calendarEvent.end.dateTime
    });

    return {
        ...data,
        calendar_event: calendarEvent
    };

} catch (error) {
    console.error('❌ [Build Calendar] Error:', error.message);
    console.error('Data received:', JSON.stringify(data, null, 2));
    throw error;
}"""

    # Update code
    node['parameters']['jsCode'] = new_code

    print_success("Fixed ISO date handling: Extract date part before concatenation")

    return workflow

def update_metadata(workflow):
    """Update workflow metadata for V3.2"""
    print_step(3, 3, "Updating workflow metadata...")

    workflow['name'] = "05 - Appointment Scheduler V3.2"
    workflow['versionId'] = "3.2"

    # Update tags
    workflow['tags'] = [
        {
            "name": "appointment",
            "createdAt": "2026-03-24T00:00:00.000000"
        },
        {
            "name": "google-calendar",
            "createdAt": "2026-03-24T00:00:00.000000"
        },
        {
            "name": "v3.2",
            "createdAt": "2026-03-24T00:00:00.000000"
        },
        {
            "name": "iso-date-fixed",
            "createdAt": "2026-03-24T00:00:00.000000"
        }
    ]

    print_success("Updated metadata to V3.2")

def save_v3_2_workflow(workflow):
    """Save generated V3.2 workflow"""
    output_path = Path(__file__).parent.parent / "n8n" / "workflows" / "05_appointment_scheduler_v3.2.json"

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print_success(f"Saved V3.2 workflow: {output_path}")
    print_success(f"Total nodes: {len(workflow['nodes'])}")

    return output_path

def validate_workflow(workflow):
    """Validate generated workflow structure"""
    print(f"\n{BLUE}🔍 Validating V3.2 workflow...{RESET}")

    # Validate node count (same as V3.1)
    expected_nodes = 11
    actual_nodes = len(workflow['nodes'])

    if actual_nodes != expected_nodes:
        print_warning(f"Expected {expected_nodes} nodes, got {actual_nodes}")
    else:
        print_success(f"Node count correct: {actual_nodes} nodes")

    # Validate Build Calendar Event Data has ISO date handling
    build_node = next((n for n in workflow['nodes'] if n['name'] == 'Build Calendar Event Data'), None)

    if build_node:
        code = build_node['parameters']['jsCode']

        # Check for ISO date extraction logic
        if "scheduledDateRaw.includes('T')" in code and "split('T')[0]" in code:
            print_success("Build Calendar Event Data: ISO date extraction implemented ✓")
        else:
            print_error("Build Calendar Event Data: Missing ISO date extraction!")
            return False

        # Check for enhanced logging
        if 'original_date' in code and 'extracted_date' in code:
            print_success("Build Calendar Event Data: Enhanced logging implemented ✓")
        else:
            print_warning("Build Calendar Event Data: Missing enhanced logging")

        # Check for DateTime validation logging
        if 'start_valid' in code and 'end_valid' in code:
            print_success("Build Calendar Event Data: DateTime validation logging ✓")
        else:
            print_warning("Build Calendar Event Data: Missing validation logging")

    else:
        print_error("Build Calendar Event Data node NOT found!")
        return False

    # Validate connections still intact
    connections = workflow.get('connections', {})
    build_connections = connections.get('Build Calendar Event Data', {})

    if build_connections and build_connections.get('main'):
        main_conn = build_connections['main'][0]
        if main_conn and main_conn[0]['node'] == 'Create Google Calendar Event':
            print_success("Connections: Build → Google Calendar ✓")
        else:
            print_error("Connections: Build → Google Calendar BROKEN!")
            return False
    else:
        print_error("Build Calendar Event Data has no connections!")
        return False

    print(f"\n{GREEN}✅ Validation complete - All checks passed!{RESET}")
    return True

def main():
    """Main script execution"""
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}Generate Appointment Scheduler V3.2 - ISO Date Fix{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")

    print(f"{YELLOW}🎯 CRITICAL FIX:{RESET}")
    print(f"Problem: PostgreSQL DATE returns '2026-04-25T00:00:00.000Z' (ISO with time)")
    print(f"Current: Assumes 'YYYY-MM-DD' format")
    print(f"Result: Invalid DateTime '2026-04-25T00:00:00.000ZT08:00:00' ❌\n")
    print(f"Solution: Extract date part from ISO strings before concatenation")
    print(f"  '2026-04-25T00:00:00.000Z'.split('T')[0] = '2026-04-25' ✓")
    print(f"  '2026-04-25' + 'T' + '08:00:00' = '2026-04-25T08:00:00' ✓\n")
    print(f"{BLUE}{'='*70}{RESET}\n")

    # Load V3.1
    workflow = load_v3_1_workflow()

    # Fix ISO date handling
    workflow = fix_build_calendar_event_date_handling(workflow)

    # Update metadata
    update_metadata(workflow)

    # Save V3.2
    output_path = save_v3_2_workflow(workflow)

    # Validate
    if validate_workflow(workflow):
        print(f"\n{GREEN}{'='*70}{RESET}")
        print(f"{GREEN}✅ V3.2 workflow generated successfully!{RESET}")
        print(f"{GREEN}{'='*70}{RESET}\n")
        print(f"{YELLOW}📋 Key Change:{RESET}")
        print(f"Build Calendar Event Data: ISO date string extraction")
        print(f"  Before: '2026-04-25T00:00:00.000Z' used directly ❌")
        print(f"  After: Extract '2026-04-25' first ✅")
        print(f"  Result: Valid DateTime construction ✓\n")
        print(f"{YELLOW}📋 Next steps:{RESET}")
        print(f"1. Import workflow: http://localhost:5678")
        print(f"2. File: {output_path}")
        print(f"3. Deactivate V3.1, activate V3.2")
        print(f"4. Test complete flow:")
        print(f"   WF02 (V73.5) → Confirm appointment → WF05 (V3.2) executes")
        print(f"   Expected: DateTime construction succeeds ✓")
        print(f"   Expected: Google Calendar event created ✓\n")
        return 0
    else:
        print(f"\n{RED}{'='*70}{RESET}")
        print(f"{RED}❌ Validation failed - please review errors{RESET}")
        print(f"{RED}{'='*70}{RESET}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
