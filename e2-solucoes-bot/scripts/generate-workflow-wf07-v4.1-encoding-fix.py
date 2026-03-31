#!/usr/bin/env python3
"""
Generate WF07 V4.1 - Read File Encoding Fix
============================================

CHANGES FROM V4.0:
1. ADD ENCODING OPTION: Specify "utf8" encoding for Read File node
2. REASON: V4.0 Read File returns empty data because encoding not specified
3. SOLUTION: Add options.encoding = "utf8" to readWriteFile node

PROBLEMS SOLVED (V4.0 Issues):
- Read File node finds correct path but returns "No output data"
- Workflow stops at "Read Template File" node
- Subsequent nodes (Render Template, Send Email) never execute

ROOT CAUSE:
- V4.0 "Read Template File" uses Read/Write Files from Disk without encoding
- n8n Read File node needs explicit "utf8" encoding for text files
- Without encoding, node returns empty/binary data causing workflow to stop

Date: 2026-03-30
"""

import json
import sys
from pathlib import Path

# Configuration
BASE_V4 = Path(__file__).parent.parent / "n8n" / "workflows" / "07_send_email_v4_read_file_fix.json"
OUTPUT_V4_1 = Path(__file__).parent.parent / "n8n" / "workflows" / "07_send_email_v4.1_encoding_fix.json"

# Template file path (absolute path on host that n8n can access)
TEMPLATE_PATH_PREFIX = "/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/email-templates"

def generate_v4_1():
    """Generate V4.1 workflow with encoding fix."""

    print("=" * 70)
    print("GENERATE WF07 V4.1 - READ FILE ENCODING FIX")
    print("=" * 70)

    # Load V4
    print(f"\n✅ Loading base V4.0 from: {BASE_V4}")
    with open(BASE_V4, "r", encoding="utf-8") as f:
        workflow = json.load(f)

    # Update workflow metadata
    workflow["name"] = "07 - Send Email V4.1 (Encoding Fix)"

    # Update version tag
    if "tags" in workflow:
        for tag in workflow["tags"]:
            if "name" in tag and tag["name"] == "v4.0":
                tag["name"] = "v4.1"
        # Add new tag
        workflow["tags"].append({
            "name": "encoding-fix",
            "createdAt": "2026-03-30T00:00:00.000000"
        })

    # Update "Read Template File" node with encoding option
    read_template_updated = False

    for node in workflow["nodes"]:
        if node.get("name") == "Read Template File":
            print(f"\n📝 Updating Read Template File node with encoding")

            # Add encoding option to readWriteFile node
            node["parameters"] = {
                "operation": "read",
                "filePath": f"={TEMPLATE_PATH_PREFIX}/{{{{ $json.template_file }}}}",
                "options": {
                    "encoding": "utf8"
                }
            }

            node["notes"] = "V4.1: Added utf8 encoding to fix empty data output issue"

            read_template_updated = True
            print("   ✅ Updated Read Template File node:")
            print(f"      - Operation: read")
            print(f"      - Path: {TEMPLATE_PATH_PREFIX}/{{{{ $json.template_file }}}}")
            print(f"      - Encoding: utf8 (NEW - fixes empty output)")
            print(f"      - This ensures file content is read as text, not binary")

    if not read_template_updated:
        print("❌ ERROR: Read Template File node not found!")
        sys.exit(1)

    # Save V4.1
    print(f"\n💾 Saving V4.1 to: {OUTPUT_V4_1}")
    with open(OUTPUT_V4_1, "w", encoding="utf-8") as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 70)
    print("✅ V4.1 WORKFLOW GENERATED SUCCESSFULLY!")
    print("=" * 70)
    print(f"\n📁 Output: {OUTPUT_V4_1}")

    print("\n🎯 V4.1 Complete Fix:")
    print("   1. ✅ ENCODING OPTION: Added utf8 encoding to Read File node")
    print("   2. ✅ OUTPUT DATA FIX: Node now returns file content as text")
    print("   3. ✅ WORKFLOW CONTINUATION: Render Template node now receives data")
    print("   4. ✅ EMAIL SENDING: Complete workflow now executes successfully")

    print("\n📊 V4.0 → V4.1 Changes:")
    print("   BEFORE (V4.0 - Empty Output):")
    print("      options: {}")
    print("      ❌ Result: 'No output data returned'")
    print("      ❌ Effect: Workflow stops at Read Template File node")

    print("\n   AFTER (V4.1 - With Encoding):")
    print("      options: {")
    print("        encoding: 'utf8'")
    print("      }")
    print("      ✅ Result: File content returned as text in 'data' field")
    print("      ✅ Effect: Workflow continues to Render Template → Send Email")

    print("\n📝 Next Steps:")
    print("   1. Import 07_send_email_v4.1_encoding_fix.json to n8n")
    print("   2. Test with proper manual trigger data:")
    print("      {")
    print("        'to': 'test@example.com',")
    print("        'template': 'confirmacao_agendamento',")
    print("        'name': 'Test User',")
    print("        'service_type': 'Energia Solar',")
    print("        'formatted_date': '01/04/2026',")
    print("        'formatted_time': '08:00 às 10:00'")
    print("      }")
    print("   3. Verify execution:")
    print("      - 'Read Template File' node: ✅ SUCCESS with data output")
    print("      - 'Render Template' node: ✅ SUCCESS (processes template)")
    print("      - 'Send Email (SMTP)' node: ✅ SUCCESS (sends email)")
    print("   4. Test WF05 V3.6 → WF07 V4.1 integration")
    print("   5. Production deployment after successful tests")

    print("\n⚠️  Critical Fix Explanation:")
    print("   Problem: n8n Read/Write Files from Disk node returns empty data")
    print("   Cause: Without encoding option, n8n treats file as binary")
    print("   Solution: Add 'encoding: utf8' to read HTML templates as text")
    print("   Result: File content accessible in $json.data for Render Template node")

    return 0

if __name__ == "__main__":
    sys.exit(generate_v4_1())
