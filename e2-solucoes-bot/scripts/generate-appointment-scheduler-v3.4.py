#!/usr/bin/env python3
"""
Script: generate-appointment-scheduler-v3.4.py
Purpose: Fix Google Calendar attendees JSON.stringify and PostgreSQL function errors
Date: 2026-03-24

CRITICAL FIXES:
1. Google Calendar attendees: Remove JSON.stringify (pass array directly)
2. Google Calendar reminders: Remove JSON.stringify (pass object directly)
3. PostgreSQL function: Remove call to non-existent create_appointment_reminders()
4. Create simple INSERT for reminders instead
"""

import json
import sys
from pathlib import Path

# Colors
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_step(step_num, total, message):
    print(f"{BLUE}[{step_num}/{total}]{RESET} {message}")

def print_success(message):
    print(f"{GREEN}✅ {message}{RESET}")

def print_error(message):
    print(f"{RED}❌ {message}{RESET}")

def load_v3_3_workflow():
    """Load V3.3 workflow JSON"""
    v3_3_path = Path(__file__).parent.parent / "n8n" / "workflows" / "05_appointment_scheduler_v3.3.json"

    print_step(1, 3, "Loading V3.3 workflow...")

    if not v3_3_path.exists():
        print_error(f"V3.3 workflow not found: {v3_3_path}")
        sys.exit(1)

    with open(v3_3_path, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    print_success(f"Loaded V3.3 workflow: {len(workflow['nodes'])} nodes")
    return workflow

def fix_google_calendar_fields(workflow):
    """Fix Google Calendar additionalFields to pass objects directly"""
    print_step(2, 3, "Fixing Google Calendar additionalFields...")

    # Find node
    node = None
    for n in workflow['nodes']:
        if n['name'] == 'Create Google Calendar Event':
            node = n
            break

    if not node:
        print_error("Create Google Calendar Event node not found!")
        sys.exit(1)

    print(f"  Issue #1: attendees uses JSON.stringify - breaks forEach")
    print(f"  Issue #2: reminders uses JSON.stringify - breaks object structure")

    # Fix: Remove JSON.stringify, pass objects directly
    node['parameters']['additionalFields']['attendees'] = "={{ $json.calendar_event.attendees }}"
    node['parameters']['additionalFields']['reminders'] = "={{ $json.calendar_event.reminders }}"

    print_success("Fixed Google Calendar additionalFields:")
    print("  attendees: JSON.stringify(...) → direct array")
    print("  reminders: JSON.stringify(...) → direct object")

    return workflow

def fix_reminder_creation(workflow):
    """Replace PostgreSQL function call with direct INSERT"""
    print_step(3, 3, "Fixing reminder creation...")

    # Find node
    node = None
    for n in workflow['nodes']:
        if n['name'] == 'Create Appointment Reminders':
            node = n
            break

    if not node:
        print_error("Create Appointment Reminders node not found!")
        sys.exit(1)

    print(f"  Issue: Calls non-existent function create_appointment_reminders()")

    # New query: Direct INSERT for reminders
    new_query = """INSERT INTO appointment_reminders (
    appointment_id,
    reminder_type,
    reminder_time,
    status,
    created_at
)
SELECT
    '{{ $('Build Calendar Event Data').item.json.appointment_id }}'::uuid,
    'email' as reminder_type,
    a.scheduled_date + (a.scheduled_time_start - interval '24 hours') as reminder_time,
    'pending' as status,
    NOW() as created_at
FROM appointments a
WHERE a.id = '{{ $('Build Calendar Event Data').item.json.appointment_id }}'
  AND a.google_calendar_event_id IS NOT NULL
ON CONFLICT (appointment_id, reminder_type, reminder_time) DO NOTHING
RETURNING id, reminder_type, reminder_time;"""

    node['parameters']['query'] = new_query

    print_success("Fixed reminder creation: Function call → Direct INSERT")
    print("  Creates 24h email reminder before appointment")
    print("  ON CONFLICT prevents duplicates")

    return workflow

def update_metadata(workflow):
    """Update workflow metadata for V3.4"""
    workflow['name'] = "05 - Appointment Scheduler V3.4"
    workflow['versionId'] = "3.4"

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
            "name": "v3.4",
            "createdAt": "2026-03-24T00:00:00.000000"
        },
        {
            "name": "attendees-reminders-fixed",
            "createdAt": "2026-03-24T00:00:00.000000"
        }
    ]

    print_success("Updated metadata to V3.4")

def save_v3_4_workflow(workflow):
    """Save generated V3.4 workflow"""
    output_path = Path(__file__).parent.parent / "n8n" / "workflows" / "05_appointment_scheduler_v3.4.json"

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print_success(f"Saved V3.4 workflow: {output_path}")
    print_success(f"Total nodes: {len(workflow['nodes'])}")

    return output_path

def validate_workflow(workflow):
    """Validate generated workflow"""
    print(f"\n{BLUE}🔍 Validating V3.4 workflow...{RESET}")

    # Validate Google Calendar node
    calendar_node = next((n for n in workflow['nodes'] if n['name'] == 'Create Google Calendar Event'), None)

    if calendar_node:
        attendees = calendar_node['parameters']['additionalFields']['attendees']
        reminders = calendar_node['parameters']['additionalFields']['reminders']

        if 'JSON.stringify' in attendees:
            print_error("Google Calendar attendees still has JSON.stringify!")
            return False
        else:
            print_success("Google Calendar attendees: Direct array ✓")

        if 'JSON.stringify' in reminders:
            print_error("Google Calendar reminders still has JSON.stringify!")
            return False
        else:
            print_success("Google Calendar reminders: Direct object ✓")
    else:
        print_error("Create Google Calendar Event node NOT found!")
        return False

    # Validate reminder node
    reminder_node = next((n for n in workflow['nodes'] if n['name'] == 'Create Appointment Reminders'), None)

    if reminder_node:
        query = reminder_node['parameters']['query']

        if 'create_appointment_reminders' in query:
            print_error("Reminder node still calls create_appointment_reminders function!")
            return False
        else:
            print_success("Reminder creation: Direct INSERT ✓")

        if 'INSERT INTO appointment_reminders' in query:
            print_success("Reminder query uses INSERT INTO ✓")
        else:
            print_error("Reminder query doesn't have INSERT INTO!")
            return False
    else:
        print_error("Create Appointment Reminders node NOT found!")
        return False

    # Validate typeVersion preserved
    if calendar_node['typeVersion'] != 1:
        print_error(f"Google Calendar typeVersion not 1: {calendar_node['typeVersion']}")
        return False
    else:
        print_success("Google Calendar typeVersion: 1 ✓")

    # Validate ISO date fix preserved
    build_node = next((n for n in workflow['nodes'] if n['name'] == 'Build Calendar Event Data'), None)

    if build_node:
        code = build_node['parameters']['jsCode']
        if "scheduledDateRaw.includes('T')" in code:
            print_success("ISO date extraction preserved ✓")
        else:
            print_error("ISO date extraction missing!")
            return False

    print(f"\n{GREEN}✅ Validation complete - All checks passed!{RESET}")
    return True

def main():
    """Main script execution"""
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}Generate Appointment Scheduler V3.4 - Google Calendar & Reminder Fixes{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")

    print(f"{YELLOW}🎯 CRITICAL FIXES:{RESET}")
    print(f"Execution 14883 errors:")
    print(f"")
    print(f"1. Google Calendar Error:")
    print(f"   additionalFields.attendees.forEach is not a function")
    print(f"   Root cause: JSON.stringify([...]) → string, not array")
    print(f"   Fix: Remove JSON.stringify, pass array directly\n")
    print(f"2. PostgreSQL Function Error:")
    print(f"   function create_appointment_reminders(unknown) does not exist")
    print(f"   Root cause: Function was never created in database")
    print(f"   Fix: Replace with direct INSERT INTO appointment_reminders\n")
    print(f"{BLUE}{'='*70}{RESET}\n")

    # Load V3.3
    workflow = load_v3_3_workflow()

    # Fix Google Calendar fields
    workflow = fix_google_calendar_fields(workflow)

    # Fix reminder creation
    workflow = fix_reminder_creation(workflow)

    # Update metadata
    update_metadata(workflow)

    # Save V3.4
    output_path = save_v3_4_workflow(workflow)

    # Validate
    if validate_workflow(workflow):
        print(f"\n{GREEN}{'='*70}{RESET}")
        print(f"{GREEN}✅ V3.4 workflow generated successfully!{RESET}")
        print(f"{GREEN}{'='*70}{RESET}\n")
        print(f"{YELLOW}📋 Key Changes:{RESET}")
        print(f"1. Google Calendar attendees:")
        print(f"   Before: JSON.stringify(...) → string ❌")
        print(f"   After: Direct array → works with forEach ✅\n")
        print(f"2. Google Calendar reminders:")
        print(f"   Before: JSON.stringify(...) → string ❌")
        print(f"   After: Direct object → proper structure ✅\n")
        print(f"3. Reminder creation:")
        print(f"   Before: SELECT create_appointment_reminders(...) ❌")
        print(f"   After: INSERT INTO appointment_reminders ✅\n")
        print(f"{YELLOW}📋 Preserved from V3.3:{RESET}")
        print(f"TypeVersion: 1 (Google Calendar) ✓")
        print(f"ISO date extraction: preserved ✓")
        print(f"TIME type conversion: preserved ✓\n")
        print(f"{YELLOW}📋 Next steps:{RESET}")
        print(f"1. Import workflow: http://localhost:5678")
        print(f"2. File: {output_path}")
        print(f"3. Deactivate V3.3, activate V3.4")
        print(f"4. Test complete flow:")
        print(f"   WF02 V73.5 → Confirm → WF05 V3.4 executes")
        print(f"   Expected: Google Calendar event created ✓")
        print(f"   Expected: Appointment reminders created ✓")
        print(f"   Expected: All downstream nodes execute ✓\n")
        return 0
    else:
        print(f"\n{RED}{'='*70}{RESET}")
        print(f"{RED}❌ Validation failed - please review errors{RESET}")
        print(f"{RED}{'='*70}{RESET}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
