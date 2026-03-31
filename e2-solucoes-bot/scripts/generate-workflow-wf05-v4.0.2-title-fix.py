#!/usr/bin/env python3
"""
Generate WF05 V4.0.2 - Title Fix
=================================

CHANGES FROM V4.0.1:
1. FIX TITLE: Use user-requested simple title "E2 Soluções - Agenda"
2. Simplify title logic to avoid n8n expression evaluation issues

PROBLEMS SOLVED:
- Google Calendar showing "(Sem título)" despite code defining summary
- Complex title generation causing evaluation problems
- User explicitly requested: "E2 Soluções - Agenda"

Date: 2026-03-30
"""

import json
import sys
from pathlib import Path

# Configuration
BASE_V4_0_1 = Path(__file__).parent.parent / "n8n" / "workflows" / "05_appointment_scheduler_v4.0.1.json"
OUTPUT_V4_0_2 = Path(__file__).parent.parent / "n8n" / "workflows" / "05_appointment_scheduler_v4.0.2.json"

def generate_v4_0_2():
    """Generate V4.0.2 workflow with simplified title fix."""

    print("=" * 70)
    print("GENERATE WF05 V4.0.2 - TITLE FIX")
    print("=" * 70)

    # Load V4.0.1
    print(f"\n✅ Loading base V4.0.1 from: {BASE_V4_0_1}")
    with open(BASE_V4_0_1, "r", encoding="utf-8") as f:
        workflow = json.load(f)

    # Update workflow metadata
    workflow["name"] = "05_appointment_scheduler_v4.0.2"

    # Update version tag
    if "tags" in workflow:
        for tag in workflow["tags"]:
            if "name" in tag and tag["name"].startswith("v"):
                tag["name"] = "v4.0.2"

    # Find and update Build Calendar Event Data node
    build_calendar_updated = False
    for node in workflow["nodes"]:
        if node.get("name") == "Build Calendar Event Data":
            print(f"\n📝 Found Build Calendar Event Data node: {node['name']}")

            # Get current code
            js_code = node["parameters"]["jsCode"]

            # Replace the title generation logic
            # OLD: Complex title with formatServiceName and clientName
            # NEW: Simple static title as requested by user

            # Find the improvedTitle line
            title_start = js_code.find("const improvedTitle =")
            if title_start == -1:
                print("❌ ERROR: Could not find improvedTitle definition!")
                sys.exit(1)

            # Find the end of the line (semicolon)
            title_end = js_code.find(";", title_start)
            if title_end == -1:
                print("❌ ERROR: Could not find end of improvedTitle line!")
                sys.exit(1)

            # Replace with simple static title
            old_title_line = js_code[title_start:title_end + 1]
            new_title_line = "const improvedTitle = 'E2 Soluções - Agenda';  // ✅ V4.0.2: User-requested simple title"

            # Replace in code
            js_code_new = js_code.replace(old_title_line, new_title_line)

            # Also update the comment that describes the title logic
            js_code_new = js_code_new.replace(
                "// ===== V4.0 FIX: IMPROVED TITLE =====",
                "// ===== V4.0.2 FIX: SIMPLE STATIC TITLE ====="
            )

            # Update node
            node["parameters"]["jsCode"] = js_code_new
            build_calendar_updated = True

            print("✅ Updated Build Calendar Event Data node:")
            print(f"   - Simplified title to: 'E2 Soluções - Agenda'")
            print(f"   - Removed complex formatServiceName logic")
            break

    if not build_calendar_updated:
        print("❌ ERROR: Build Calendar Event Data node not found!")
        sys.exit(1)

    # Save V4.0.2
    print(f"\n💾 Saving V4.0.2 to: {OUTPUT_V4_0_2}")
    with open(OUTPUT_V4_0_2, "w", encoding="utf-8") as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 70)
    print("✅ V4.0.2 WORKFLOW GENERATED SUCCESSFULLY!")
    print("=" * 70)
    print(f"\n📁 Output: {OUTPUT_V4_0_2}")
    print("\n🎯 V4.0.2 Features:")
    print("   1. ✅ TIMEZONE FIX: Date created with -03:00 offset (Brazil time)")
    print("   2. ✅ TITLE FIX: Simple static title 'E2 Soluções - Agenda'")
    print("   3. ✅ ATTENDEES FIX: String array format (not object array)")
    print("   4. ✅ Maintains V4.0.1 timezone and attendees fixes")

    print("\n📊 Before vs After:")
    print("\n   BEFORE V4.0.1:")
    print("      Title: (Sem título) - Empty despite complex logic")
    print("      Complex: formatServiceName + clientName evaluation issues")
    print("\n   AFTER V4.0.2:")
    print("      Title: 'E2 Soluções - Agenda' (user-requested)")
    print("      Simple: Static string, no evaluation issues")

    print("\n📝 Next Steps:")
    print("   1. Import 05_appointment_scheduler_v4.0.2.json to n8n")
    print("   2. Test appointment creation")
    print("   3. Verify Google Calendar shows:")
    print("      - Correct title: 'E2 Soluções - Agenda'")
    print("      - Correct time: 08:00-10:00 (Brazil timezone)")
    print("      - Correct attendees: email address")
    print("   4. Deploy to production after validation")

    return 0

if __name__ == "__main__":
    sys.exit(generate_v4_0_2())
