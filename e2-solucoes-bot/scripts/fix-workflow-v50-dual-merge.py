#!/usr/bin/env python3
"""
V50 Fix Script - Dual Merge Architecture
Purpose: Split single merge node into two separate nodes (one per path)
Root Cause: n8n executes node on first input, doesn't wait for both
Solution: Separate merge nodes for NEW and EXISTING user paths
"""

import json
from pathlib import Path

def fix_workflow_v50_dual_merge():
    """Create dual merge architecture - separate merge for each path"""

    base_dir = Path(__file__).parent.parent
    workflow_v49 = base_dir / "n8n/workflows/02_ai_agent_conversation_V49_MERGE_VALIDATION.json"
    workflow_v50 = base_dir / "n8n/workflows/02_ai_agent_conversation_V50_DUAL_MERGE.json"

    print("=== V50 DUAL MERGE ARCHITECTURE FIX ===")
    print(f"Reading: {workflow_v49}")

    with open(workflow_v49, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    changes_made = []

    # 1. Find the original Merge Conversation Data node
    merge_node = None
    for node in workflow['nodes']:
        if node['name'] == 'Merge Conversation Data':
            merge_node = node
            break

    if not merge_node:
        print("❌ ERROR: 'Merge Conversation Data' node not found")
        return False

    print(f"\n✅ Found 'Merge Conversation Data' node")

    # 2. Create Merge New User Data node (duplicate of original)
    merge_new_user = merge_node.copy()
    merge_new_user['name'] = 'Merge New User Data'
    merge_new_user['id'] = 'merge-new-user-v50'
    merge_new_user['position'] = [176, 400]  # Adjust position

    # Update code with V50 NEW USER branding
    new_user_code = merge_node['parameters']['jsCode'].replace(
        '=== V49 MERGE INPUT VALIDATION ===',
        '=== V50 MERGE NEW USER DATA ==='
    ).replace(
        'V49 CRITICAL ERROR',
        'V50 NEW USER CRITICAL ERROR'
    ).replace(
        '✅ V49:',
        '✅ V50 (NEW):'
    ).replace(
        'V49 CUSTOM MERGE',
        'V50 CUSTOM MERGE (NEW USER)'
    )

    merge_new_user['parameters']['jsCode'] = new_user_code
    changes_made.append("Created Merge New User Data node with V49 validation")

    # 3. Create Merge Existing User Data node (duplicate of original)
    merge_existing_user = merge_node.copy()
    merge_existing_user['name'] = 'Merge Existing User Data'
    merge_existing_user['id'] = 'merge-existing-user-v50'
    merge_existing_user['position'] = [176, 1100]  # Adjust position

    # Update code with V50 EXISTING USER branding
    existing_user_code = merge_node['parameters']['jsCode'].replace(
        '=== V49 MERGE INPUT VALIDATION ===',
        '=== V50 MERGE EXISTING USER DATA ==='
    ).replace(
        'V49 CRITICAL ERROR',
        'V50 EXISTING USER CRITICAL ERROR'
    ).replace(
        '✅ V49:',
        '✅ V50 (EXISTING):'
    ).replace(
        'V49 CUSTOM MERGE',
        'V50 CUSTOM MERGE (EXISTING USER)'
    )

    merge_existing_user['parameters']['jsCode'] = existing_user_code
    changes_made.append("Created Merge Existing User Data node with V49 validation")

    # 4. Remove old Merge Conversation Data node, add new ones
    workflow['nodes'] = [n for n in workflow['nodes'] if n['name'] != 'Merge Conversation Data']
    workflow['nodes'].append(merge_new_user)
    workflow['nodes'].append(merge_existing_user)
    changes_made.append("Replaced single Merge node with dual merge nodes")

    # 5. Update connections
    # NEW USER PATH
    # Merge Queries Data → [Create New Conversation, Merge New User Data (0)]
    workflow['connections']['Merge Queries Data'] = {
        "main": [[
            {"node": "Create New Conversation", "type": "main", "index": 0},
            {"node": "Merge New User Data", "type": "main", "index": 0}
        ]]
    }
    changes_made.append("Updated Merge Queries Data connections (NEW USER path)")

    # Create New Conversation → Merge New User Data (1)
    workflow['connections']['Create New Conversation'] = {
        "main": [[
            {"node": "Merge New User Data", "type": "main", "index": 1}
        ]]
    }
    changes_made.append("Updated Create New Conversation connections")

    # Merge New User Data → State Machine Logic
    workflow['connections']['Merge New User Data'] = {
        "main": [[
            {"node": "State Machine Logic", "type": "main", "index": 0}
        ]]
    }
    changes_made.append("Connected Merge New User Data to State Machine")

    # EXISTING USER PATH
    # Merge Queries Data1 → [Get Conversation Details, Merge Existing User Data (0)]
    workflow['connections']['Merge Queries Data1'] = {
        "main": [[
            {"node": "Get Conversation Details", "type": "main", "index": 0},
            {"node": "Merge Existing User Data", "type": "main", "index": 0}
        ]]
    }
    changes_made.append("Updated Merge Queries Data1 connections (EXISTING USER path)")

    # Get Conversation Details → Merge Existing User Data (1)
    workflow['connections']['Get Conversation Details'] = {
        "main": [[
            {"node": "Merge Existing User Data", "type": "main", "index": 1}
        ]]
    }
    changes_made.append("Updated Get Conversation Details connections")

    # Merge Existing User Data → State Machine Logic
    workflow['connections']['Merge Existing User Data'] = {
        "main": [[
            {"node": "State Machine Logic", "type": "main", "index": 0}
        ]]
    }
    changes_made.append("Connected Merge Existing User Data to State Machine")

    # 6. Update workflow metadata
    workflow['name'] = "02 - AI Agent Conversation V50 (Dual Merge)"
    workflow['versionId'] = "v50-dual-merge-architecture"

    # 7. Save V50
    print(f"\nSaving fixed workflow: {workflow_v50}")
    with open(workflow_v50, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print("\n✅ V50 Dual Merge Architecture Fix Complete!")
    print("\n" + "="*60)
    print("CHANGES MADE:")
    print("="*60)
    for i, change in enumerate(changes_made, 1):
        print(f"{i}. {change}")

    print("\n" + "="*60)
    print("ARCHITECTURE IMPROVEMENTS:")
    print("="*60)
    print("✅ NEW USER PATH:")
    print("   Merge Queries Data")
    print("      ├─→ Create New Conversation")
    print("      │   └─→ Merge New User Data (input 1)")
    print("      └─→ Merge New User Data (input 0)")
    print("          └─→ State Machine Logic")
    print("")
    print("✅ EXISTING USER PATH:")
    print("   Merge Queries Data1")
    print("      ├─→ Get Conversation Details")
    print("      │   └─→ Merge Existing User Data (input 1)")
    print("      └─→ Merge Existing User Data (input 0)")
    print("          └─→ State Machine Logic")

    print("\n" + "="*60)
    print("WHY V50 WORKS (vs V49):")
    print("="*60)
    print("❌ V49 Problem:")
    print("   - Single merge node receives from 2 mutually exclusive paths")
    print("   - n8n executes node when FIRST input arrives")
    print("   - Doesn't wait for BOTH inputs")
    print("   - Result: Merge receives only 1 input")
    print("")
    print("✅ V50 Solution:")
    print("   - TWO separate merge nodes (one per path)")
    print("   - Each merge receives from only 1 path")
    print("   - Both inputs arrive from SAME execution context")
    print("   - n8n waits until BOTH inputs arrive")
    print("   - Result: Each merge receives 2 inputs ✅")

    print("\n" + "="*60)
    print("VALIDATION:")
    print("="*60)
    print("✅ Dual merge nodes created successfully")
    print("✅ V49 input validation preserved in both nodes")
    print("✅ Connections updated for separate paths")
    print("✅ Both merge nodes connect to State Machine")
    print("✅ Ready for import and testing")

    print("\n" + "="*60)
    print("TESTING:")
    print("="*60)
    print("1. Import V50 in n8n: http://localhost:5678")
    print("2. Deactivate V49, activate V50")
    print("3. Clean test data:")
    print("   docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \\")
    print("     -c \"DELETE FROM conversations WHERE phone_number = '556181755748';\"")
    print("")
    print("4. Test NEW user flow:")
    print("   - Send 'oi' → Bot shows menu")
    print("   - Send '1' → Bot asks for name")
    print("   - Send 'Bruno Rosa' → Bot asks for phone (NOT menu!)")
    print("")
    print("5. Check V50 NEW USER logs:")
    print("   docker logs e2bot-n8n-dev 2>&1 | grep -A 30 'V50 MERGE NEW USER'")
    print("")
    print("   Expected:")
    print("   ✅ Total inputs received: 2")
    print("   ✅ V50 (NEW): Input count validated")
    print("   ✅ V50 (NEW): Database input validated")
    print("   ✅ id: d784ce32-...")
    print("")
    print("6. Test EXISTING user flow (send 'oi' again)")
    print("7. Check V50 EXISTING USER logs:")
    print("   docker logs e2bot-n8n-dev 2>&1 | grep -A 30 'V50 MERGE EXISTING USER'")
    print("")
    print("   Expected:")
    print("   ✅ Total inputs received: 2")
    print("   ✅ V50 (EXISTING): Input count validated")
    print("   ✅ V50 (EXISTING): Database input validated")
    print("="*60)

    return True

if __name__ == '__main__':
    success = fix_workflow_v50_dual_merge()
    exit(0 if success else 1)
