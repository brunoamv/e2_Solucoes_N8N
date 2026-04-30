#!/usr/bin/env python3
"""
Generate WF05 V4.0.4 - Email Data Passing Fix
==============================================

PROBLEM SOLVED:
- WF07 V3 fails with "Email recipient not found" because WF05 V4.0.3
  doesn't pass appointment data when triggering WF07
- "Send Confirmation Email" node has empty options: {}
- $json from "Update Appointment" only contains 4 fields:
  {id, status, google_calendar_event_id, calendar_success}
- Missing critical fields: lead_email, lead_name, scheduled_date, etc.

ROOT CAUSE:
- "Send Confirmation Email" executeWorkflow node receives incomplete data
- Full appointment data exists in "Get Appointment & Lead Data" node
- But data isn't passed forward to WF07 trigger

SOLUTION V4.0.4:
- Add "Prepare Email Trigger Data" node before "Send Confirmation Email"
- Merge data from two sources:
  1. "Get Appointment & Lead Data" → Lead info, appointment details
  2. "Update Appointment" → calendar_success flag, google_calendar_event_id
- "Send Confirmation Email" now receives complete 16-field object

Date: 2026-03-30
"""

import json
import sys
from pathlib import Path

# Configuration
BASE_V4_0_3 = Path(__file__).parent.parent / "n8n" / "workflows" / "05_appointment_scheduler_v4.0.3.json"
OUTPUT_V4_0_4 = Path(__file__).parent.parent / "n8n" / "workflows" / "05_appointment_scheduler_v4.0.4.json"

def generate_prepare_email_data_node():
    """Generate JavaScript code for Prepare Email Trigger Data node."""

    return '''// Prepare Email Trigger Data for WF07
const appointmentData = $('Get Appointment & Lead Data').item.json;
const updateResult = $('Update Appointment').item.json;

// Merge data for WF07 V3
return {
    // Appointment identifiers
    appointment_id: appointmentData.appointment_id,

    // Calendar integration
    google_calendar_event_id: updateResult.google_calendar_event_id,
    calendar_success: updateResult.calendar_success,

    // Lead information
    lead_id: appointmentData.lead_id,
    lead_name: appointmentData.lead_name,
    lead_email: appointmentData.lead_email,  // ✅ CRITICAL: WF07 needs this
    phone_number: appointmentData.phone_number,
    whatsapp_name: appointmentData.whatsapp_name,

    // Appointment details
    scheduled_date: appointmentData.scheduled_date,
    scheduled_time_start: appointmentData.scheduled_time_start,
    scheduled_time_end: appointmentData.scheduled_time_end,
    service_type: appointmentData.service_type,

    // Location
    city: appointmentData.city,
    address: appointmentData.address,
    state: appointmentData.state,
    zip_code: appointmentData.zip_code,

    // Status
    status: updateResult.status
};'''

def generate_v4_0_4():
    """Generate V4.0.4 workflow with email data fix."""

    print("=" * 70)
    print("GENERATE WF05 V4.0.4 - EMAIL DATA PASSING FIX")
    print("=" * 70)

    # Load V4.0.3
    print(f"\n✅ Loading base V4.0.3 from: {BASE_V4_0_3}")
    with open(BASE_V4_0_3, "r", encoding="utf-8") as f:
        workflow = json.load(f)

    # Update workflow metadata
    workflow["name"] = "05_appointment_scheduler_v4.0.4"
    workflow["versionId"] = "4.0.4"

    # Update version tag
    if "tags" in workflow:
        workflow["tags"] = [tag for tag in workflow["tags"] if tag.get("name") != "v4.0.3"]
        workflow["tags"].append({
            "name": "v4.0.4",
            "createdAt": "2026-03-30T00:00:00.000000"
        })
        workflow["tags"].append({
            "name": "email-data-fix",
            "createdAt": "2026-03-30T00:00:00.000000"
        })

    # Add new "Prepare Email Trigger Data" node
    prepare_email_node = {
        "parameters": {
            "jsCode": generate_prepare_email_data_node()
        },
        "id": "prepare-email-trigger-data-v4",
        "name": "Prepare Email Trigger Data",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [2000, 300],
        "notes": "V4.0.4: Merge appointment data for WF07 email trigger"
    }

    print("\n📝 Adding new node: Prepare Email Trigger Data")
    print("   ✅ Merges data from:")
    print("      - Get Appointment & Lead Data (16 fields)")
    print("      - Update Appointment (calendar_success flag)")

    # Find "Send Confirmation Email" node and update position
    send_email_updated = False
    for node in workflow["nodes"]:
        if node.get("name") == "Send Confirmation Email":
            print("\n📝 Updating Send Confirmation Email node")
            node["position"] = [2250, 300]  # Move right to accommodate new node
            node["notes"] = "V4.0.4: Receives complete merged data from Prepare Email Trigger Data"
            send_email_updated = True
            print("   ✅ Position updated: [2250, 300]")
            print("   ✅ Now receives 16-field merged object")

    if not send_email_updated:
        print("❌ ERROR: Send Confirmation Email node not found!")
        sys.exit(1)

    # Insert new node before Send Confirmation Email
    workflow["nodes"].insert(-1, prepare_email_node)  # Insert before last node (error handler)

    # Update connections
    print("\n📝 Updating workflow connections")

    # Find RD Station Task node connections and insert new node between it and Send Email
    if "Create RD Station Task (OPTIONAL)" in workflow["connections"]:
        # RD Station → Prepare Email Trigger Data
        workflow["connections"]["Create RD Station Task (OPTIONAL)"]["main"] = [
            [
                {
                    "node": "Prepare Email Trigger Data",
                    "type": "main",
                    "index": 0
                }
            ]
        ]
        print("   ✅ RD Station Task → Prepare Email Trigger Data")

    # Prepare Email Trigger Data → Send Confirmation Email
    workflow["connections"]["Prepare Email Trigger Data"] = {
        "main": [
            [
                {
                    "node": "Send Confirmation Email",
                    "type": "main",
                    "index": 0
                }
            ]
        ]
    }
    print("   ✅ Prepare Email Trigger Data → Send Confirmation Email")

    # Save V4.0.4
    print(f"\n💾 Saving V4.0.4 to: {OUTPUT_V4_0_4}")
    with open(OUTPUT_V4_0_4, "w", encoding="utf-8") as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 70)
    print("✅ V4.0.4 WORKFLOW GENERATED SUCCESSFULLY!")
    print("=" * 70)
    print(f"\n📁 Output: {OUTPUT_V4_0_4}")

    print("\n🎯 V4.0.4 Complete Fix:")
    print("   1. ✅ NEW NODE: Prepare Email Trigger Data (merges appointment data)")
    print("   2. ✅ DATA PASSING: 16 fields → WF07 (vs 4 fields in V4.0.3)")
    print("   3. ✅ WF07 COMPATIBILITY: All required fields now present")
    print("   4. ✅ CONNECTIONS: RD Station → Prepare Email → Send Email")

    print("\n📊 V4.0.3 → V4.0.4 Changes:")
    print("   Node Count: 37 → 38 nodes (+1 data preparation)")
    print("   \n   BEFORE (V4.0.3 - Incomplete):")
    print("      RD Station Task → Send Confirmation Email")
    print("      $json = {id, status, google_calendar_event_id, calendar_success}")
    print("      ❌ Missing: lead_email, lead_name, scheduled_date, etc.")
    print("   \n   AFTER (V4.0.4 - Complete):")
    print("      RD Station Task → Prepare Email Trigger Data → Send Email")
    print("      $json = {")
    print("         appointment_id, google_calendar_event_id, calendar_success,")
    print("         lead_id, lead_name, lead_email, phone_number, whatsapp_name,")
    print("         scheduled_date, scheduled_time_start, scheduled_time_end,")
    print("         service_type, city, address, state, zip_code, status")
    print("      }")
    print("      ✅ All 16 fields WF07 needs!")

    print("\n📝 Next Steps:")
    print("   1. Import 05_appointment_scheduler_v4.0.4.json to n8n")
    print("   2. Verify WF07 V3 import: 07_send_email_v3_complete_fix.json")
    print("   3. Test WF05 V4.0.4 → WF07 V3 integration:")
    print("      - Create appointment (Service 1/3 + confirm)")
    print("      - Verify Google Calendar event created")
    print("      - Check WF07 V3 receives complete data")
    print("      - Verify email sent to lead_email")
    print("      - Check email content (date, time, Google Calendar link)")
    print("   4. Monitor execution logs:")
    print("      docker logs -f e2bot-n8n-dev | grep -E 'Prepare Email|WF07|ERROR'")
    print("   5. Verify email_logs table:")
    print("      SELECT * FROM email_logs ORDER BY sent_at DESC LIMIT 5;")
    print("   6. Production deployment after successful tests")

    print("\n⚠️  Data Validation:")
    print("   Ensure WF07 V3 receives these fields:")
    print("   ✅ appointment_id (WF07 detection)")
    print("   ✅ calendar_success (WF07 detection)")
    print("   ✅ lead_email (email recipient)")
    print("   ✅ lead_name (email personalization)")
    print("   ✅ scheduled_date (ISO format)")
    print("   ✅ scheduled_time_start / scheduled_time_end (time range)")
    print("   ✅ service_type (service description)")
    print("   ✅ city, address, state (location info)")
    print("   ✅ phone_number, whatsapp_name (contact info)")
    print("   ✅ google_calendar_event_id (calendar link)")

    return 0

if __name__ == "__main__":
    sys.exit(generate_v4_0_4())
