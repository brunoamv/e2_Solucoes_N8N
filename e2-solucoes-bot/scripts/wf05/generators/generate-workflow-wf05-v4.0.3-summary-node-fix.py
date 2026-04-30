#!/usr/bin/env python3
"""
Generate WF05 V4.0.3 - Google Calendar Node Summary Fix
========================================================

CHANGES FROM V4.0.2:
1. FIX SUMMARY: Move summary from expression to additionalFields OR fix expression evaluation
2. Ensure Google Calendar API receives the summary parameter correctly

PROBLEMS SOLVED:
- V4.0.2: summary appears in node INPUT but NOT in API OUTPUT (missing from response)
- Google Calendar shows "(Sem título)" despite summary being set in JavaScript
- Expression "={{ $json.calendar_event.summary }}" not sending value to API

ROOT CAUSE ANALYSIS:
- User evidence: "Campo calendar_event summary E2 Soluções - Agenda esta aparecendo no nó"
- BUT: Google Calendar API response has NO summary field
- Issue: n8n Google Calendar node v1 may not handle summary parameter correctly with expressions
- Solution: Try moving summary to additionalFields OR use direct value instead of expression

Date: 2026-03-30
"""

import json
import sys
from pathlib import Path

# Configuration
BASE_V4_0_2 = Path(__file__).parent.parent / "n8n" / "workflows" / "05_appointment_scheduler_v4.0.2.json"
OUTPUT_V4_0_3 = Path(__file__).parent.parent / "n8n" / "workflows" / "05_appointment_scheduler_v4.0.3.json"

def generate_v4_0_3():
    """Generate V4.0.3 workflow with Google Calendar node summary fix."""

    print("=" * 70)
    print("GENERATE WF05 V4.0.3 - GOOGLE CALENDAR NODE SUMMARY FIX")
    print("=" * 70)

    # Load V4.0.2
    print(f"\n✅ Loading base V4.0.2 from: {BASE_V4_0_2}")
    with open(BASE_V4_0_2, "r", encoding="utf-8") as f:
        workflow = json.load(f)

    # Update workflow metadata
    workflow["name"] = "05_appointment_scheduler_v4.0.3"

    # Update version tag
    if "tags" in workflow:
        for tag in workflow["tags"]:
            if "name" in tag and tag["name"].startswith("v"):
                tag["name"] = "v4.0.3"

    # Find and update Create Google Calendar Event node
    google_calendar_updated = False
    for node in workflow["nodes"]:
        if node.get("name") == "Create Google Calendar Event":
            print(f"\n📝 Found Create Google Calendar Event node")

            # Get current parameters
            params = node["parameters"]

            # SOLUTION ATTEMPT 1: Move summary from main parameter to additionalFields
            # This ensures it's explicitly included in the API request

            # Remove summary from main parameters if it exists
            if "summary" in params:
                print(f"   📌 Current summary parameter: {params['summary']}")
                del params["summary"]

            # Ensure additionalFields exists
            if "additionalFields" not in params:
                params["additionalFields"] = {}

            # Add summary to additionalFields with the SAME expression
            params["additionalFields"]["summary"] = "={{ $json.calendar_event.summary }}"

            # Update the node parameters
            node["parameters"] = params
            google_calendar_updated = True

            print("✅ Updated Google Calendar node:")
            print("   - Moved summary to additionalFields")
            print("   - Expression: {{ $json.calendar_event.summary }}")
            print("   - This ensures summary is explicitly included in API request")
            break

    if not google_calendar_updated:
        print("❌ ERROR: Create Google Calendar Event node not found!")
        sys.exit(1)

    # Save V4.0.3
    print(f"\n💾 Saving V4.0.3 to: {OUTPUT_V4_0_3}")
    with open(OUTPUT_V4_0_3, "w", encoding="utf-8") as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 70)
    print("✅ V4.0.3 WORKFLOW GENERATED SUCCESSFULLY!")
    print("=" * 70)
    print(f"\n📁 Output: {OUTPUT_V4_0_3}")
    print("\n🎯 V4.0.3 Fix:")
    print("   1. ✅ SUMMARY PARAMETER: Moved to additionalFields for explicit API inclusion")
    print("   2. ✅ EXPRESSION PRESERVED: {{ $json.calendar_event.summary }}")
    print("   3. ✅ TIMEZONE FIX: Maintained from V4.0 (Brazil -03:00)")
    print("   4. ✅ ATTENDEES FIX: Maintained from V4.0.1 (string array)")
    print("   5. ✅ STATIC TITLE: Maintained from V4.0.2 ('E2 Soluções - Agenda')")

    print("\n📊 Technical Change:")
    print("   BEFORE (V4.0.2):")
    print('      "summary": "={{ $json.calendar_event.summary }}"  # Main parameter')
    print("   AFTER (V4.0.3):")
    print('      "additionalFields": {')
    print('         "summary": "={{ $json.calendar_event.summary }}"  # Explicit in additionalFields')
    print('      }')

    print("\n📝 Next Steps:")
    print("   1. Import 05_appointment_scheduler_v4.0.3.json to n8n")
    print("   2. Test appointment creation")
    print("   3. Verify Google Calendar shows:")
    print("      - Correct title: 'E2 Soluções - Agenda' (not '(Sem título)')")
    print("      - Correct time: 08:00-10:00 (Brazil timezone)")
    print("      - Correct attendees: email address")
    print("   4. Check API response includes summary field")
    print("   5. Deploy to production after validation")

    print("\n⚠️  Alternative Solution (if V4.0.3 fails):")
    print("   - Try using static title directly in additionalFields")
    print("   - Investigate n8n Google Calendar node version compatibility")
    print("   - Check if typeVersion: 1 → 2 update needed")

    return 0

if __name__ == "__main__":
    sys.exit(generate_v4_0_3())
