#!/usr/bin/env python3
"""
V52 Fix Script - Replace Code Merge with Native n8n Merge Nodes
Purpose: Use native n8n Merge nodes that automatically wait for all inputs
Root Cause: Code nodes execute immediately, don't wait for multiple inputs
Solution: Replace with n8n-nodes-base.merge nodes with 'combine' mode
"""

import json
from pathlib import Path

def fix_workflow_v52_native_merge():
    """Replace Code-based merge nodes with native n8n Merge nodes"""

    base_dir = Path(__file__).parent.parent
    workflow_v51 = base_dir / "n8n/workflows/02_ai_agent_conversation_V51_GHOST_CONNECTION_FIX.json"
    workflow_v52 = base_dir / "n8n/workflows/02_ai_agent_conversation_V52_NATIVE_MERGE.json"

    print("=== V52 NATIVE MERGE NODE FIX ===")
    print(f"Reading: {workflow_v51}")

    with open(workflow_v51, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    changes_made = []

    # 1. Find and replace "Merge New User Data" Code node with native Merge node
    for i, node in enumerate(workflow['nodes']):
        if node['name'] == 'Merge New User Data' and node['type'] == 'n8n-nodes-base.code':
            print(f"\n✅ Found 'Merge New User Data' Code node")

            # Create native Merge node
            workflow['nodes'][i] = {
                "parameters": {
                    "mode": "combine",
                    "options": {
                        "includeUnpopulated": True,
                        "multipleMatches": "first"
                    }
                },
                "id": "merge-new-user-v52",
                "name": "Merge New User Data",
                "type": "n8n-nodes-base.merge",
                "typeVersion": 2.1,
                "position": node['position'],  # Keep same position
                "alwaysOutputData": True
            }
            changes_made.append("Replaced 'Merge New User Data' Code node with native Merge node")
            print(f"   ✅ Replaced with native Merge node (type: n8n-nodes-base.merge)")

    # 2. Find and replace "Merge Existing User Data" Code node with native Merge node
    for i, node in enumerate(workflow['nodes']):
        if node['name'] == 'Merge Existing User Data' and node['type'] == 'n8n-nodes-base.code':
            print(f"\n✅ Found 'Merge Existing User Data' Code node")

            # Create native Merge node
            workflow['nodes'][i] = {
                "parameters": {
                    "mode": "combine",
                    "options": {
                        "includeUnpopulated": True,
                        "multipleMatches": "first"
                    }
                },
                "id": "merge-existing-user-v52",
                "name": "Merge Existing User Data",
                "type": "n8n-nodes-base.merge",
                "typeVersion": 2.1,
                "position": node['position'],  # Keep same position
                "alwaysOutputData": True
            }
            changes_made.append("Replaced 'Merge Existing User Data' Code node with native Merge node")
            print(f"   ✅ Replaced with native Merge node (type: n8n-nodes-base.merge)")

    # 3. Update workflow metadata
    workflow['name'] = "02 - AI Agent Conversation V52 (Native Merge)"
    workflow['versionId'] = "v52-native-merge"

    # 4. Save V52
    print(f"\nSaving fixed workflow: {workflow_v52}")
    with open(workflow_v52, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print("\n✅ V52 Native Merge Fix Complete!")

    if changes_made:
        print("\n" + "="*60)
        print("CHANGES MADE:")
        print("="*60)
        for i, change in enumerate(changes_made, 1):
            print(f"{i}. {change}")
    else:
        print("\n" + "="*60)
        print("WARNING: No Code nodes found to replace!")
        print("="*60)

    print("\n" + "="*60)
    print("WHY V52 WORKS (vs V51):")
    print("="*60)
    print("❌ V51 Problem:")
    print("   - Code nodes execute immediately on first input")
    print("   - Custom $input.all() validation too late")
    print("   - Merge receives 1 input, fails before both arrive")
    print("")
    print("✅ V52 Solution:")
    print("   - Native n8n Merge nodes WAIT for all inputs")
    print("   - Execution engine tracks input requirements")
    print("   - Node only executes when BOTH inputs have data")
    print("   - Result: Automatic synchronization ✅")

    print("\n" + "="*60)
    print("MERGE NODE CONFIGURATION:")
    print("="*60)
    print("Type: n8n-nodes-base.merge")
    print("Mode: combine (merges all fields from all inputs)")
    print("Options:")
    print("  - includeUnpopulated: true (preserve all fields)")
    print("  - multipleMatches: first (handle multiple items)")
    print("")
    print("Behavior:")
    print("  - Input 0: Data from Merge Queries Data (queries, message)")
    print("  - Input 1: Data from Create/Get Details (id, state)")
    print("  - Waits until BOTH inputs arrive")
    print("  - Combines all fields from both inputs")
    print("  - Sends merged result to State Machine Logic")

    print("\n" + "="*60)
    print("TESTING:")
    print("="*60)
    print("1. Import V52 in n8n: http://localhost:5678")
    print("2. Deactivate V51, activate V52")
    print("3. Clean test data:")
    print("   docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \\")
    print("     -c \"DELETE FROM conversations WHERE phone_number = '556181755748';\"")
    print("")
    print("4. Test NEW user flow:")
    print("   - Send 'oi' → Bot shows menu")
    print("   - Send '1' → Bot asks for name")
    print("   - Send 'Bruno Rosa' → Bot asks for phone (NOT menu!)")
    print("")
    print("5. Check V52 execution logs:")
    print("   docker logs e2bot-n8n-dev 2>&1 | grep -A 10 'Merge New User Data'")
    print("")
    print("   Expected:")
    print("   ✅ Node waits until both inputs arrive")
    print("   ✅ Execution shows successful merge")
    print("   ✅ No 'received 1 input' error")
    print("   ✅ Data flows to State Machine Logic")
    print("="*60)

    return True

if __name__ == '__main__':
    success = fix_workflow_v52_native_merge()
    exit(0 if success else 1)
