#!/usr/bin/env python3
"""
Script: generate-appointment-scheduler-v3.1.py
Purpose: Fix PostgreSQL type handling and Google Calendar credentials
Date: 2026-03-24

CRITICAL FIXES:
1. Validate Availability: PostgreSQL TIME type conversion
2. Build Calendar Event Data: Type-safe DATE/TIME handling
3. Create Google Calendar Event: Static credential ID
4. Comprehensive error handling and logging

Strategy: Complete refactoring of all problematic nodes
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

def load_v3_workflow():
    """Load V3 workflow JSON"""
    v3_path = Path(__file__).parent.parent / "n8n" / "workflows" / "05_appointment_scheduler_v3.json"

    print_step(1, 5, "Loading V3 workflow...")

    if not v3_path.exists():
        print_error(f"V3 workflow not found: {v3_path}")
        sys.exit(1)

    with open(v3_path, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    print_success(f"Loaded V3 workflow: {len(workflow['nodes'])} nodes")
    return workflow

def fix_validate_availability_node(workflow):
    """Fix Validate Availability with PostgreSQL type conversion"""
    print_step(2, 5, "Fixing Validate Availability node...")

    # Find node
    node = None
    for n in workflow['nodes']:
        if n['name'] == 'Validate Availability':
            node = n
            break

    if not node:
        print_error("Validate Availability node not found!")
        sys.exit(1)

    print(f"  Current code has TypeError on line 12: timeStart.split()")

    # NEW CODE: Complete rewrite with type safety
    new_code = """// Validate Availability - V3.1 FIX
const data = $input.first().json;

try {
    // ===== VALIDATE INPUT DATA =====
    const scheduledDate = data.scheduled_date;
    const timeStartRaw = data.scheduled_time_start;
    const timeEndRaw = data.scheduled_time_end;

    if (!scheduledDate || !timeStartRaw || !timeEndRaw) {
        throw new Error('Dados de agendamento incompletos: ' + JSON.stringify({
            scheduledDate: !!scheduledDate,
            timeStart: !!timeStartRaw,
            timeEnd: !!timeEndRaw
        }));
    }

    // ===== NORMALIZE TIME VALUES =====
    // PostgreSQL TIME type may be object or string
    const timeStart = typeof timeStartRaw === 'string'
        ? timeStartRaw
        : timeStartRaw?.toString() || '';

    const timeEnd = typeof timeEndRaw === 'string'
        ? timeEndRaw
        : timeEndRaw?.toString() || '';

    console.log('⏰ [Validate Availability] Times:', { timeStart, timeEnd });

    // ===== CHECK ENV VARS EXIST =====
    if (!$env.CALENDAR_WORK_START || !$env.CALENDAR_WORK_END || !$env.CALENDAR_WORK_DAYS) {
        console.warn('⚠️  Calendar env vars not configured - skipping validation');
        return {
            ...data,
            validation_status: 'skipped',
            validation_reason: 'env_vars_missing',
            validated_at: new Date().toISOString()
        };
    }

    // ===== CHECK BUSINESS HOURS =====
    const startHour = parseInt(timeStart.split(':')[0]);
    const endHour = parseInt(timeEnd.split(':')[0]);

    const workStart = parseInt($env.CALENDAR_WORK_START.split(':')[0]);
    const workEnd = parseInt($env.CALENDAR_WORK_END.split(':')[0]);

    if (startHour < workStart || endHour > workEnd) {
        throw new Error(`Horário fora do expediente: ${timeStart}-${timeEnd} (expediente: ${$env.CALENDAR_WORK_START}-${$env.CALENDAR_WORK_END})`);
    }

    // ===== CHECK WEEKEND =====
    const dateObj = scheduledDate instanceof Date
        ? scheduledDate
        : new Date(scheduledDate);

    const dayOfWeek = dateObj.getDay();
    const workDays = $env.CALENDAR_WORK_DAYS.split(',').map(d => parseInt(d.trim()));

    if (!workDays.includes(dayOfWeek)) {
        throw new Error(`Dia não útil: ${scheduledDate} (dia da semana: ${dayOfWeek})`);
    }

    console.log('✅ [Validate Availability] Approved:', scheduledDate, timeStart);

    return {
        ...data,
        validation_status: 'approved',
        validated_at: new Date().toISOString()
    };

} catch (error) {
    console.error('❌ [Validate Availability] Error:', error.message);
    console.error('Data received:', JSON.stringify(data, null, 2));
    throw error;
}"""

    # Update code
    node['parameters']['jsCode'] = new_code

    print_success("Fixed Validate Availability with type-safe TIME conversion")

    return workflow

def fix_build_calendar_event_node(workflow):
    """Fix Build Calendar Event Data with type-safe DATE/TIME handling"""
    print_step(3, 5, "Fixing Build Calendar Event Data node...")

    # Find node
    node = None
    for n in workflow['nodes']:
        if n['name'] == 'Build Calendar Event Data':
            node = n
            break

    if not node:
        print_error("Build Calendar Event Data node not found!")
        sys.exit(1)

    print(f"  Adding type safety for PostgreSQL DATE/TIME types")

    # NEW CODE: Complete rewrite with type safety
    new_code = """// Build Calendar Event Data - V3.1 FIX
const data = $input.first().json;

try {
    // ===== NORMALIZE DATE AND TIME =====
    const scheduledDateRaw = data.scheduled_date;
    const timeStartRaw = data.scheduled_time_start;
    const timeEndRaw = data.scheduled_time_end;

    // Convert to strings if needed
    const dateString = scheduledDateRaw instanceof Date
        ? scheduledDateRaw.toISOString().split('T')[0]
        : scheduledDateRaw;

    const timeStart = typeof timeStartRaw === 'string'
        ? timeStartRaw
        : timeStartRaw?.toString() || '00:00:00';

    const timeEnd = typeof timeEndRaw === 'string'
        ? timeEndRaw
        : timeEndRaw?.toString() || '00:00:00';

    console.log('📅 [Build Calendar] Date/Time:', { dateString, timeStart, timeEnd });

    // ===== BUILD DATETIME =====
    const startDateTime = new Date(`${dateString}T${timeStart}`);
    const endDateTime = new Date(`${dateString}T${timeEnd}`);

    if (isNaN(startDateTime.getTime()) || isNaN(endDateTime.getTime())) {
        throw new Error('Invalid date/time format: ' + JSON.stringify({ dateString, timeStart, timeEnd }));
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

    print_success("Fixed Build Calendar Event Data with type-safe handling")

    return workflow

def fix_google_calendar_credentials(workflow):
    """Fix Create Google Calendar Event credentials"""
    print_step(4, 5, "Fixing Google Calendar Event credentials...")

    # Find node
    node = None
    for n in workflow['nodes']:
        if n['name'] == 'Create Google Calendar Event':
            node = n
            break

    if not node:
        print_error("Create Google Calendar Event node not found!")
        sys.exit(1)

    print(f"  Current credentials use invalid expression")

    # CRITICAL FIX: Replace expression with static ID
    node['credentials'] = {
        "googleCalendarOAuth2Api": {
            "id": "1",
            "name": "Google Calendar API"
        }
    }

    print_success("Fixed credentials to use static ID: '1'")

    return workflow

def update_metadata(workflow):
    """Update workflow metadata for V3.1"""
    print_step(5, 5, "Updating workflow metadata...")

    workflow['name'] = "05 - Appointment Scheduler V3.1"
    workflow['versionId'] = "3.1"

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
            "name": "v3.1",
            "createdAt": "2026-03-24T00:00:00.000000"
        },
        {
            "name": "type-safe-fixed",
            "createdAt": "2026-03-24T00:00:00.000000"
        }
    ]

    print_success("Updated metadata to V3.1")

def save_v3_1_workflow(workflow):
    """Save generated V3.1 workflow"""
    output_path = Path(__file__).parent.parent / "n8n" / "workflows" / "05_appointment_scheduler_v3.1.json"

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print_success(f"Saved V3.1 workflow: {output_path}")
    print_success(f"Total nodes: {len(workflow['nodes'])}")

    return output_path

def validate_workflow(workflow):
    """Validate generated workflow structure"""
    print(f"\n{BLUE}🔍 Validating V3.1 workflow...{RESET}")

    # Validate node count (same as V3)
    expected_nodes = 11
    actual_nodes = len(workflow['nodes'])

    if actual_nodes != expected_nodes:
        print_warning(f"Expected {expected_nodes} nodes, got {actual_nodes}")
    else:
        print_success(f"Node count correct: {actual_nodes} nodes")

    # Validate Validate Availability has type conversion
    validate_node = next((n for n in workflow['nodes'] if n['name'] == 'Validate Availability'), None)

    if validate_node:
        code = validate_node['parameters']['jsCode']

        if 'typeof timeStartRaw === \'string\'' in code and 'toString()' in code:
            print_success("Validate Availability: Type conversion implemented ✓")
        else:
            print_error("Validate Availability: Missing type conversion!")
            return False

        if 'try {' in code and 'catch (error)' in code:
            print_success("Validate Availability: Error handling implemented ✓")
        else:
            print_warning("Validate Availability: Missing error handling")

    else:
        print_error("Validate Availability node NOT found!")
        return False

    # Validate Build Calendar Event Data has type safety
    build_node = next((n for n in workflow['nodes'] if n['name'] == 'Build Calendar Event Data'), None)

    if build_node:
        code = build_node['parameters']['jsCode']

        if 'typeof timeStartRaw === \'string\'' in code:
            print_success("Build Calendar Event Data: Type safety implemented ✓")
        else:
            print_error("Build Calendar Event Data: Missing type safety!")
            return False

        if 'isNaN(startDateTime.getTime())' in code:
            print_success("Build Calendar Event Data: DateTime validation implemented ✓")
        else:
            print_warning("Build Calendar Event Data: Missing DateTime validation")

    else:
        print_error("Build Calendar Event Data node NOT found!")
        return False

    # Validate Google Calendar credentials use static ID
    calendar_node = next((n for n in workflow['nodes'] if n['name'] == 'Create Google Calendar Event'), None)

    if calendar_node:
        creds = calendar_node.get('credentials', {})
        google_creds = creds.get('googleCalendarOAuth2Api', {})
        cred_id = google_creds.get('id', '')

        if cred_id == '1':
            print_success("Create Google Calendar Event: Static credential ID ✓")
        else:
            print_error(f"Create Google Calendar Event: Credential ID is '{cred_id}', not '1'!")
            return False

        # Check that expression is gone
        if '{{' in str(cred_id) or '$env' in str(cred_id):
            print_error("Create Google Calendar Event: Still using expression in credential ID!")
            return False
        else:
            print_success("Create Google Calendar Event: Expression removed ✓")

    else:
        print_error("Create Google Calendar Event node NOT found!")
        return False

    print(f"\n{GREEN}✅ Validation complete - All checks passed!{RESET}")
    return True

def main():
    """Main script execution"""
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}Generate Appointment Scheduler V3.1 - Type Safety Fix{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")

    print(f"{YELLOW}🎯 CRITICAL FIXES:{RESET}")
    print(f"1. Validate Availability: PostgreSQL TIME type conversion")
    print(f"2. Build Calendar Event Data: Type-safe DATE/TIME handling")
    print(f"3. Create Google Calendar Event: Static credential ID")
    print(f"\nStrategy: Complete refactoring with comprehensive error handling")
    print(f"\n{BLUE}{'='*70}{RESET}\n")

    # Load V3
    workflow = load_v3_workflow()

    # Fix all 3 nodes
    workflow = fix_validate_availability_node(workflow)
    workflow = fix_build_calendar_event_node(workflow)
    workflow = fix_google_calendar_credentials(workflow)

    # Update metadata
    update_metadata(workflow)

    # Save V3.1
    output_path = save_v3_1_workflow(workflow)

    # Validate
    if validate_workflow(workflow):
        print(f"\n{GREEN}{'='*70}{RESET}")
        print(f"{GREEN}✅ V3.1 workflow generated successfully!{RESET}")
        print(f"{GREEN}{'='*70}{RESET}\n")
        print(f"{YELLOW}📋 Key Changes:{RESET}")
        print(f"1. Validate Availability: Type-safe TIME conversion with toString()")
        print(f"2. Build Calendar Event Data: Type-safe DATE/TIME handling")
        print(f"3. Create Google Calendar Event: Static credential ID '1'")
        print(f"4. Comprehensive error handling and logging in all nodes\n")
        print(f"{YELLOW}📋 Next steps:{RESET}")
        print(f"1. Import workflow: http://localhost:5678")
        print(f"2. File: {output_path}")
        print(f"3. Deactivate V3, activate V3.1")
        print(f"4. Test complete flow:")
        print(f"   WF02 (V73.5) → Confirm appointment → WF05 (V3.1) executes")
        print(f"   Expected: All nodes execute without TypeError ✓")
        print(f"   Expected: Google Calendar event created ✓\n")
        return 0
    else:
        print(f"\n{RED}{'='*70}{RESET}")
        print(f"{RED}❌ Validation failed - please review errors{RESET}")
        print(f"{RED}{'='*70}{RESET}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
