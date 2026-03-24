#!/usr/bin/env python3
"""
Script: generate-appointment-scheduler-v3.6.py
Purpose: DEFINITIVE FIX - Google Calendar attendees must be array of strings
Date: 2026-03-24

DEFINITIVE SOLUTION:
- Google Calendar node v1 expects attendees as ARRAY OF STRINGS: ["email@test.com"]
- NOT: string "email@test.com" (causes forEach error)
- NOT: array of objects [{email: "x"}] (causes split error)
- IF empty: don't send attendees field at all
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

def load_v3_5_workflow():
    """Load V3.5 workflow JSON"""
    v3_5_path = Path(__file__).parent.parent / "n8n" / "workflows" / "05_appointment_scheduler_v3.5.json"

    print_step(1, 3, "Loading V3.5 workflow...")

    if not v3_5_path.exists():
        print_error(f"V3.5 workflow not found: {v3_5_path}")
        sys.exit(1)

    with open(v3_5_path, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    print_success(f"Loaded V3.5 workflow: {len(workflow['nodes'])} nodes")
    return workflow

def fix_attendees_array_of_strings(workflow):
    """Fix attendees to be array of strings for Google Calendar node v1"""
    print_step(2, 3, "Fixing attendees to array of strings format...")

    # Find Build Calendar Event Data node
    build_node = None
    for n in workflow['nodes']:
        if n['name'] == 'Build Calendar Event Data':
            build_node = n
            break

    if not build_node:
        print_error("Build Calendar Event Data node not found!")
        sys.exit(1)

    print(f"  Issue: Build Calendar Event Data creates attendees as simple string")
    print(f"  Required: Array of strings for Google Calendar node v1")

    # Fix: Change attendees from string to array of strings
    old_code = build_node['parameters']['jsCode']

    # Replace the attendees line - NOW as array of strings
    new_code = old_code.replace(
        "attendees: data.lead_email || ''",
        "attendees: data.lead_email ? [data.lead_email] : []"
    )

    build_node['parameters']['jsCode'] = new_code

    print_success("Fixed Build Calendar Event Data:")
    print("  Before: attendees: 'email@test.com' (string)")
    print("  After:  attendees: ['email@test.com'] (array of strings)")

    return workflow

def fix_google_calendar_conditional_attendees(workflow):
    """Make attendees field conditional - only send if array has items"""
    print_step(3, 3, "Making attendees field conditional...")

    # Find Google Calendar node
    calendar_node = None
    for n in workflow['nodes']:
        if n['name'] == 'Create Google Calendar Event':
            calendar_node = n
            break

    if not calendar_node:
        print_error("Create Google Calendar Event node not found!")
        sys.exit(1)

    print(f"  Strategy: Use n8n conditional expression")
    print(f"  If attendees.length > 0: send field")
    print(f"  If attendees.length == 0: omit field")

    # Update attendees to be conditional
    # n8n expression: only include if array has items
    calendar_node['parameters']['additionalFields']['attendees'] = "={{ $json.calendar_event.attendees.length > 0 ? $json.calendar_event.attendees : undefined }}"

    print_success("Fixed Google Calendar node:")
    print("  Conditional: attendees sent only if array has items")
    print("  Empty array: field omitted (prevents Google API errors)")

    return workflow

def update_metadata(workflow):
    """Update workflow metadata for V3.6"""
    workflow['name'] = "05 - Appointment Scheduler V3.6"
    workflow['versionId'] = "3.6"

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
            "name": "v3.6",
            "createdAt": "2026-03-24T00:00:00.000000"
        },
        {
            "name": "attendees-array-strings-fixed",
            "createdAt": "2026-03-24T00:00:00.000000"
        }
    ]

    print_success("Updated metadata to V3.6")

def save_v3_6_workflow(workflow):
    """Save generated V3.6 workflow"""
    output_path = Path(__file__).parent.parent / "n8n" / "workflows" / "05_appointment_scheduler_v3.6.json"

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print_success(f"Saved V3.6 workflow: {output_path}")
    print_success(f"Total nodes: {len(workflow['nodes'])}")

    return output_path

def validate_workflow(workflow):
    """Validate generated workflow"""
    print(f"\n{BLUE}🔍 Validating V3.6 workflow...{RESET}")

    # Validate Build Calendar Event Data node
    build_node = next((n for n in workflow['nodes'] if n['name'] == 'Build Calendar Event Data'), None)

    if build_node:
        code = build_node['parameters']['jsCode']

        # Check attendees is array of strings
        if "attendees: data.lead_email ? [data.lead_email] : []" in code:
            print_success("Build Calendar Event Data: attendees is array of strings ✓")
        else:
            print_error("Build Calendar Event Data: attendees format incorrect!")
            return False

        # Check old string format is removed
        if "attendees: data.lead_email || ''" in code:
            print_error("Build Calendar Event Data: still has string format!")
            return False
        else:
            print_success("Build Calendar Event Data: string format removed ✓")

    else:
        print_error("Build Calendar Event Data node NOT found!")
        return False

    # Validate Google Calendar node conditional
    calendar_node = next((n for n in workflow['nodes'] if n['name'] == 'Create Google Calendar Event'), None)

    if calendar_node:
        attendees = calendar_node['parameters']['additionalFields']['attendees']

        if "attendees.length > 0" in attendees and "undefined" in attendees:
            print_success("Google Calendar node: conditional attendees ✓")
        else:
            print_error(f"Google Calendar node: conditional missing: {attendees}")
            return False

        # Verify reminders still correct (object, not stringified)
        reminders = calendar_node['parameters']['additionalFields']['reminders']
        if reminders == "={{ $json.calendar_event.reminders }}":
            print_success("Google Calendar node: reminders parameter correct ✓")
        else:
            print_error(f"Google Calendar node: reminders parameter incorrect")
            return False

    else:
        print_error("Create Google Calendar Event node NOT found!")
        return False

    print(f"\n{GREEN}✅ Validation complete - All checks passed!{RESET}")
    return True

def main():
    """Main script execution"""
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}Generate Appointment Scheduler V3.6 - DEFINITIVE Attendees Fix{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")

    print(f"{YELLOW}🎯 DEFINITIVE SOLUTION:{RESET}")
    print(f"V3.5 error: additionalFields.attendees.forEach is not a function")
    print(f"")
    print(f"Root Cause Analysis:")
    print(f"  V3.3: JSON.stringify([{{email}}]) → string '\"[...]\"' ❌")
    print(f"  V3.4: [{{email: 'x'}}] → array of objects ❌")
    print(f"  V3.5: 'email@test.com' → simple string ❌")
    print(f"  V3.6: ['email@test.com'] → array of strings ✅")
    print(f"")
    print(f"Google Calendar node v1 expectations:")
    print(f"  Type: Array of strings")
    print(f"  Example: ['user1@test.com', 'user2@test.com']")
    print(f"  Processing: Iterates with forEach(), sends to Google API")
    print(f"  Empty case: Omit field entirely (don't send empty array)")
    print(f"")
    print(f"{BLUE}{'='*70}{RESET}\n")

    # Load V3.5
    workflow = load_v3_5_workflow()

    # Fix attendees to array of strings
    workflow = fix_attendees_array_of_strings(workflow)

    # Make attendees conditional in Google Calendar node
    workflow = fix_google_calendar_conditional_attendees(workflow)

    # Update metadata
    update_metadata(workflow)

    # Save V3.6
    output_path = save_v3_6_workflow(workflow)

    # Validate
    if validate_workflow(workflow):
        print(f"\n{GREEN}{'='*70}{RESET}")
        print(f"{GREEN}✅ V3.6 workflow generated successfully!{RESET}")
        print(f"{GREEN}{'='*70}{RESET}\n")
        print(f"{YELLOW}📋 Complete Evolution:{RESET}")
        print(f"V3.3: JSON.stringify → string (forEach error)")
        print(f"V3.4: array of objects → (split error)")
        print(f"V3.5: simple string → (forEach error)")
        print(f"V3.6: array of strings → CORRECT FORMAT ✅\n")
        print(f"{YELLOW}📋 Technical Details:{RESET}")
        print(f"Build Calendar Event Data:")
        print(f"  Creates: ['email@test.com'] or []")
        print(f"  Type: Array<string>")
        print(f"")
        print(f"Google Calendar node:")
        print(f"  Receives: Array of strings")
        print(f"  Processes: forEach() iteration")
        print(f"  Sends: Google Calendar API format")
        print(f"  Empty handling: Field omitted (conditional expression)\n")
        print(f"{YELLOW}📋 Preserved from V3.5:{RESET}")
        print(f"TypeVersion: 1 (Google Calendar) ✓")
        print(f"ISO date extraction: preserved ✓")
        print(f"Direct INSERT reminders: preserved ✓")
        print(f"Reminders object format: preserved ✓\n")
        print(f"{YELLOW}📋 Next steps:{RESET}")
        print(f"1. Import workflow: http://localhost:5678")
        print(f"2. File: {output_path}")
        print(f"3. Deactivate V3.5, activate V3.6")
        print(f"4. Test complete flow:")
        print(f"   WF02 V73.5 → Confirm → WF05 V3.6 executes")
        print(f"   Expected: Google Calendar event created ✓")
        print(f"   Expected: Attendees field works (array of strings) ✓")
        print(f"   Expected: All downstream nodes execute ✓")
        print(f"   Expected: NO MORE attendees.forEach errors ✓\n")
        return 0
    else:
        print(f"\n{RED}{'='*70}{RESET}")
        print(f"{RED}❌ Validation failed - please review errors{RESET}")
        print(f"{RED}{'='*70}{RESET}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
