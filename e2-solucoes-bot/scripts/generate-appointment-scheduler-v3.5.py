#!/usr/bin/env python3
"""
Script: generate-appointment-scheduler-v3.5.py
Purpose: Fix Google Calendar attendees format - node v1 expects CSV string, not array
Date: 2026-03-24

CRITICAL FIX:
- Google Calendar node v1 expects attendees as CSV string: "email1@test.com,email2@test.com"
- V3.4 was passing array of objects: [{email: "x"}]
- Caused error: "attendee.split is not a function"
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

def load_v3_4_workflow():
    """Load V3.4 workflow JSON"""
    v3_4_path = Path(__file__).parent.parent / "n8n" / "workflows" / "05_appointment_scheduler_v3.4.json"

    print_step(1, 2, "Loading V3.4 workflow...")

    if not v3_4_path.exists():
        print_error(f"V3.4 workflow not found: {v3_4_path}")
        sys.exit(1)

    with open(v3_4_path, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    print_success(f"Loaded V3.4 workflow: {len(workflow['nodes'])} nodes")
    return workflow

def fix_attendees_format(workflow):
    """Fix attendees to be CSV string instead of array of objects"""
    print_step(2, 2, "Fixing attendees format for Google Calendar node v1...")

    # Find Build Calendar Event Data node
    build_node = None
    for n in workflow['nodes']:
        if n['name'] == 'Build Calendar Event Data':
            build_node = n
            break

    if not build_node:
        print_error("Build Calendar Event Data node not found!")
        sys.exit(1)

    print(f"  Issue: Build Calendar Event Data creates attendees as array of objects")
    print(f"  Expected: CSV string for Google Calendar node v1")

    # Fix: Change attendees from array [{email: x}] to simple string "email"
    old_code = build_node['parameters']['jsCode']

    # Replace the attendees line
    new_code = old_code.replace(
        "attendees: data.lead_email ? [{ email: data.lead_email }] : []",
        "attendees: data.lead_email || ''"
    )

    build_node['parameters']['jsCode'] = new_code

    print_success("Fixed Build Calendar Event Data:")
    print("  Before: attendees: [{email: 'x'}] (array of objects)")
    print("  After:  attendees: 'email@test.com' (CSV string)")

    return workflow

def update_metadata(workflow):
    """Update workflow metadata for V3.5"""
    workflow['name'] = "05 - Appointment Scheduler V3.5"
    workflow['versionId'] = "3.5"

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
            "name": "v3.5",
            "createdAt": "2026-03-24T00:00:00.000000"
        },
        {
            "name": "attendees-csv-fixed",
            "createdAt": "2026-03-24T00:00:00.000000"
        }
    ]

    print_success("Updated metadata to V3.5")

def save_v3_5_workflow(workflow):
    """Save generated V3.5 workflow"""
    output_path = Path(__file__).parent.parent / "n8n" / "workflows" / "05_appointment_scheduler_v3.5.json"

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print_success(f"Saved V3.5 workflow: {output_path}")
    print_success(f"Total nodes: {len(workflow['nodes'])}")

    return output_path

def validate_workflow(workflow):
    """Validate generated workflow"""
    print(f"\n{BLUE}🔍 Validating V3.5 workflow...{RESET}")

    # Validate Build Calendar Event Data node
    build_node = next((n for n in workflow['nodes'] if n['name'] == 'Build Calendar Event Data'), None)

    if build_node:
        code = build_node['parameters']['jsCode']

        # Check attendees is now simple string
        if "attendees: data.lead_email || ''" in code:
            print_success("Build Calendar Event Data: attendees is CSV string ✓")
        else:
            print_error("Build Calendar Event Data: attendees format incorrect!")
            return False

        # Check old array format is removed
        if "[{ email:" in code:
            print_error("Build Calendar Event Data: still has array format!")
            return False
        else:
            print_success("Build Calendar Event Data: array format removed ✓")

    else:
        print_error("Build Calendar Event Data node NOT found!")
        return False

    # Validate Google Calendar node still exists
    calendar_node = next((n for n in workflow['nodes'] if n['name'] == 'Create Google Calendar Event'), None)

    if calendar_node:
        attendees = calendar_node['parameters']['additionalFields']['attendees']

        if attendees == "={{ $json.calendar_event.attendees }}":
            print_success("Google Calendar node: attendees parameter correct ✓")
        else:
            print_error(f"Google Calendar node: attendees parameter incorrect: {attendees}")
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
    print(f"{BLUE}Generate Appointment Scheduler V3.5 - Attendees CSV String Fix{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")

    print(f"{YELLOW}🎯 CRITICAL FIX:{RESET}")
    print(f"Execution 14940 error:")
    print(f"")
    print(f"Error: attendee.split is not a function")
    print(f"")
    print(f"Root Cause:")
    print(f"  Google Calendar node v1 expects attendees as CSV string")
    print(f"  V3.4 was passing array of objects: [{{email: 'x'}}]")
    print(f"  Node internally calls attendees.split(',') → fails on array")
    print(f"")
    print(f"Fix:")
    print(f"  Build Calendar Event Data now creates:")
    print(f"  attendees: data.lead_email || '' (simple string)")
    print(f"  Instead of: [{{email: data.lead_email}}] (array)")
    print(f"")
    print(f"{BLUE}{'='*70}{RESET}\n")

    # Load V3.4
    workflow = load_v3_4_workflow()

    # Fix attendees format
    workflow = fix_attendees_format(workflow)

    # Update metadata
    update_metadata(workflow)

    # Save V3.5
    output_path = save_v3_5_workflow(workflow)

    # Validate
    if validate_workflow(workflow):
        print(f"\n{GREEN}{'='*70}{RESET}")
        print(f"{GREEN}✅ V3.5 workflow generated successfully!{RESET}")
        print(f"{GREEN}{'='*70}{RESET}\n")
        print(f"{YELLOW}📋 Key Change:{RESET}")
        print(f"Attendees format:")
        print(f"  V3.3: JSON.stringify([{{email}}]) → '\"[{{\\\"email\\\"...}}]\"' ❌")
        print(f"  V3.4: [{{email: 'x'}}] → array of objects ❌")
        print(f"  V3.5: 'email@test.com' → CSV string ✅\n")
        print(f"{YELLOW}📋 Google Calendar node v1 behavior:{RESET}")
        print(f"  Expects: String 'email1@test.com,email2@test.com'")
        print(f"  Processes: attendees.split(',') internally")
        print(f"  Formats: Converts to Google Calendar API format\n")
        print(f"{YELLOW}📋 Preserved from V3.4:{RESET}")
        print(f"TypeVersion: 1 (Google Calendar) ✓")
        print(f"ISO date extraction: preserved ✓")
        print(f"Direct INSERT reminders: preserved ✓")
        print(f"Reminders object format: preserved ✓\n")
        print(f"{YELLOW}📋 Next steps:{RESET}")
        print(f"1. Import workflow: http://localhost:5678")
        print(f"2. File: {output_path}")
        print(f"3. Deactivate V3.4, activate V3.5")
        print(f"4. Test complete flow:")
        print(f"   WF02 V73.5 → Confirm → WF05 V3.5 executes")
        print(f"   Expected: Google Calendar event created ✓")
        print(f"   Expected: Attendees field works (CSV string) ✓")
        print(f"   Expected: All downstream nodes execute ✓\n")
        return 0
    else:
        print(f"\n{RED}{'='*70}{RESET}")
        print(f"{RED}❌ Validation failed - please review errors{RESET}")
        print(f"{RED}{'='*70}{RESET}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
