#!/usr/bin/env python3
"""
Fix Empty Options in V78.1.4 Workflow
======================================

Problem: n8n 2.15.0 rejects nodes with empty "options": {}
Solution: Remove ALL empty options parameters from workflow

This affects multiple V74 legacy nodes that had empty options.
"""

import json
from pathlib import Path

INPUT_FILE = Path(__file__).parent.parent / "n8n" / "workflows" / "02_ai_agent_conversation_V78_1_4_FINAL.json"
OUTPUT_FILE = Path(__file__).parent.parent / "n8n" / "workflows" / "02_ai_agent_conversation_V78_1_5_FINAL.json"

def fix_empty_options(workflow):
    """Remove empty options parameters from all nodes."""

    nodes_fixed = []

    for node in workflow.get("nodes", []):
        node_name = node.get("name", "Unknown")

        if "parameters" in node and "options" in node["parameters"]:
            options = node["parameters"]["options"]

            # Check if options is empty dict
            if options == {}:
                print(f"   🔧 Removing empty options from: {node_name}")
                del node["parameters"]["options"]
                nodes_fixed.append(node_name)
            else:
                print(f"   ✅ Keeping valid options in: {node_name}")

    return nodes_fixed

def main():
    print("=" * 80)
    print("FIX EMPTY OPTIONS IN V78.1.4 WORKFLOW")
    print("=" * 80)

    print(f"\n📖 Loading workflow: {INPUT_FILE}")
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        workflow = json.load(f)

    print(f"   - Workflow name: {workflow.get('name')}")
    print(f"   - Total nodes: {len(workflow.get('nodes', []))}")

    print("\n🔍 Analyzing nodes for empty options...")
    nodes_fixed = fix_empty_options(workflow)

    # Update workflow name
    workflow["name"] = "02_ai_agent_conversation_V78_1_5_FINAL"

    print(f"\n💾 Saving fixed workflow: {OUTPUT_FILE}")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 80)
    print("✅ WORKFLOW FIXED SUCCESSFULLY!")
    print("=" * 80)

    print(f"\n📊 Summary:")
    print(f"   - Total nodes fixed: {len(nodes_fixed)}")
    print(f"   - Nodes with empty options removed:")
    for node_name in nodes_fixed:
        print(f"     • {node_name}")

    print(f"\n📁 Output: {OUTPUT_FILE}")

    print(f"\n🎯 V78.1.5 Changes:")
    print("   - Removed ALL empty 'options': {} parameters")
    print("   - Kept valid options with actual configuration")
    print("   - n8n 2.15.0 should now accept the import")

    print(f"\n📝 Next Steps:")
    print("   1. Import 02_ai_agent_conversation_V78_1_5_FINAL.json to n8n")
    print("   2. Should import without 'Could not find property option' error")
    print("   3. Verify all nodes work correctly")
    print("   4. Test E2E flow")
    print("   5. Activate workflow")

if __name__ == "__main__":
    main()
