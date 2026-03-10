#!/usr/bin/env python3
"""
V53 Fix Script - Change Merge Mode to mergeByPosition
Purpose: Fix n8n Merge node configuration error
Root Cause: Mode "combine" requires field matching configuration
Solution: Use "mergeByPosition" mode which merges items by position (no field matching needed)
"""

import json
from pathlib import Path

def fix_workflow_v53_merge_by_position():
    """Change Merge node mode from 'combine' to 'mergeByPosition'"""

    base_dir = Path(__file__).parent.parent
    workflow_v52 = base_dir / "n8n/workflows/02_ai_agent_conversation_V52_NATIVE_MERGE.json"
    workflow_v53 = base_dir / "n8n/workflows/02_ai_agent_conversation_V53_MERGE_BY_POSITION.json"

    print("=== V53 MERGE BY POSITION FIX ===")
    print(f"Reading: {workflow_v52}")

    with open(workflow_v52, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    changes_made = []

    # 1. Find and update "Merge New User Data" node
    for i, node in enumerate(workflow['nodes']):
        if node['name'] == 'Merge New User Data' and node['type'] == 'n8n-nodes-base.merge':
            print(f"\n✅ Found 'Merge New User Data' Merge node")

            # Update mode to mergeByPosition
            workflow['nodes'][i]['parameters'] = {
                "mode": "mergeByPosition",
                "options": {}
            }
            changes_made.append("Changed 'Merge New User Data' mode: 'combine' → 'mergeByPosition'")
            print(f"   ✅ Changed mode to 'mergeByPosition'")

    # 2. Find and update "Merge Existing User Data" node
    for i, node in enumerate(workflow['nodes']):
        if node['name'] == 'Merge Existing User Data' and node['type'] == 'n8n-nodes-base.merge':
            print(f"\n✅ Found 'Merge Existing User Data' Merge node")

            # Update mode to mergeByPosition
            workflow['nodes'][i]['parameters'] = {
                "mode": "mergeByPosition",
                "options": {}
            }
            changes_made.append("Changed 'Merge Existing User Data' mode: 'combine' → 'mergeByPosition'")
            print(f"   ✅ Changed mode to 'mergeByPosition'")

    # 3. Update workflow metadata
    workflow['name'] = "02 - AI Agent Conversation V53 (Merge By Position)"
    workflow['versionId'] = "v53-merge-by-position"

    # 4. Save V53
    print(f"\nSaving fixed workflow: {workflow_v53}")
    with open(workflow_v53, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print("\n✅ V53 Merge By Position Fix Complete!")

    if changes_made:
        print("\n" + "="*60)
        print("CHANGES MADE:")
        print("="*60)
        for i, change in enumerate(changes_made, 1):
            print(f"{i}. {change}")
    else:
        print("\n" + "="*60)
        print("WARNING: No Merge nodes found to update!")
        print("="*60)

    print("\n" + "="*60)
    print("WHY V53 WORKS (vs V52):")
    print("="*60)
    print("❌ V52 Problem:")
    print("   - Mode 'combine' requires field matching configuration")
    print("   - Error: 'You need to define at least one pair of fields'")
    print("   - n8n doesn't know how to JOIN the inputs")
    print("")
    print("✅ V53 Solution:")
    print("   - Mode 'mergeByPosition' merges by item position")
    print("   - Item 0 from input 0 + Item 0 from input 1")
    print("   - No field matching needed")
    print("   - All fields from both items combined")

    print("\n" + "="*60)
    print("MERGE BY POSITION BEHAVIOR:")
    print("="*60)
    print("Input 0 (Merge Queries Data):")
    print("  - phone_number, message")
    print("  - query_count, query_details, query_upsert")
    print("")
    print("Input 1 (Create New Conversation):")
    print("  - id, phone_number, state_machine_state")
    print("  - collected_data, created_at, updated_at")
    print("")
    print("Merged Output:")
    print("  - ALL fields from both inputs")
    print("  - Input 1 fields override Input 0 for duplicates")
    print("  - conversation_id = input 1's id")
    print("  - message = input 0's message")

    print("\n" + "="*60)
    print("TESTING:")
    print("="*60)
    print("1. Import V53 in n8n: http://localhost:5678")
    print("2. Deactivate V52, activate V53")
    print("3. Clean test data:")
    print("   docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \\")
    print("     -c \"DELETE FROM conversations WHERE phone_number = '556181755748';\"")
    print("")
    print("4. Test NEW user flow:")
    print("   - Send 'oi' → Bot shows menu")
    print("   - Send '1' → Bot asks for name")
    print("   - Send 'Bruno Rosa' → Bot asks for phone (NOT menu!)")
    print("")
    print("5. Check V53 execution:")
    print("   docker logs e2bot-n8n-dev 2>&1 | grep -A 10 'Merge New User Data'")
    print("")
    print("   Expected:")
    print("   ✅ No 'Fields to Match' configuration error")
    print("   ✅ Merge executes successfully")
    print("   ✅ Data flows to State Machine Logic")
    print("="*60)

    return True

if __name__ == '__main__':
    success = fix_workflow_v53_merge_by_position()
    exit(0 if success else 1)
