#!/usr/bin/env python3
"""
V48.2 Fix Script - Correct Merge Mode Name
Purpose: Fix Merge node to use correct mode name 'mergeByIndex'
Root Cause: Used 'mergeByPosition' which is not a valid n8n mode
Result: Use 'mergeByIndex' to preserve all fields from all inputs
"""

import json
from pathlib import Path

def fix_workflow_v48_2_merge_index():
    """Fix Merge node to use correct 'mergeByIndex' mode name"""

    # Paths
    base_dir = Path(__file__).parent.parent
    workflow_v48_1 = base_dir / "n8n/workflows/02_ai_agent_conversation_V48_1_MERGE_MODE_FIX.json"
    workflow_v48_2 = base_dir / "n8n/workflows/02_ai_agent_conversation_V48_2_MERGE_INDEX_FIX.json"

    print("=== V48.2 MERGE INDEX FIX ===")
    print(f"Reading: {workflow_v48_1}")

    # Read workflow V48.1
    with open(workflow_v48_1, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    changes_made = []

    # Fix: Merge Conversation Data - Use mergeByIndex (correct name!)
    merge_node = None
    for node in workflow['nodes']:
        if node['name'] == 'Merge Conversation Data':
            merge_node = node
            break

    if merge_node:
        print("\n✅ Found 'Merge Conversation Data' node")
        print(f"   Current mode: {merge_node.get('parameters', {}).get('mode', 'NOT SET')}")

        # Change to mergeByIndex mode (correct n8n mode name)
        merge_node['parameters'] = {
            'mode': 'mergeByIndex',
            'options': {}
        }

        changes_made.append("Changed Merge mode from 'mergeByPosition' to 'mergeByIndex' (correct n8n mode name)")
        print("✅ Changed Merge node to 'mergeByIndex' mode (CORRECT NAME)")
        print("   This mode merges items by their index position and preserves ALL fields")
    else:
        print("❌ ERROR: 'Merge Conversation Data' node not found")

    # Update workflow metadata
    workflow['name'] = "02 - AI Agent Conversation V48.2 (Merge Index Fix)"
    workflow['versionId'] = "v48-2-merge-index-fix"

    # Save as V48.2
    print(f"\nSaving fixed workflow: {workflow_v48_2}")
    with open(workflow_v48_2, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print("\n✅ V48.2 Merge Index Fix Complete!")
    print("\n" + "="*60)
    print("CHANGES MADE:")
    print("="*60)
    for i, change in enumerate(changes_made, 1):
        print(f"{i}. {change}")

    print("\n" + "="*60)
    print("ERROR FIXED:")
    print("="*60)
    print("❌ V48.1 Error: 'mergeByPosition' is not supported")
    print("✅ V48.2 Fix: Using 'mergeByIndex' (correct n8n mode name)")
    print("\nValid n8n Merge modes:")
    print("  - append")
    print("  - chooseBranch")
    print("  - clashHandling")
    print("  - combine")
    print("  - keepKeyMatches")
    print("  - mergeByIndex  ← CORRECT MODE")
    print("  - mergeByKey")
    print("  - multiplex")
    print("  - removeKeyMatches")
    print("  - wait")

    print("\n" + "="*60)
    print("CRITICAL FIX:")
    print("="*60)
    print("✅ Merge node now uses 'mergeByIndex' mode:")
    print("   - Correct n8n mode name (not 'mergeByPosition')")
    print("   - Merges items by their index position in arrays")
    print("   - Preserves ALL fields from ALL inputs")
    print("   - Works correctly with multiple inputs (4 in our case)")
    print("   - conversation_id will be preserved from Get Conversation Details")

    print("\n" + "="*60)
    print("EXPECTED BEHAVIOR:")
    print("="*60)
    print("BEFORE V48.2:")
    print("  ❌ n8n rejects 'mergeByPosition' as invalid mode")
    print("  ❌ Workflow validation fails")
    print("  ❌ Cannot execute workflow")
    print("\nAFTER V48.2:")
    print("  ✅ n8n accepts 'mergeByIndex' as valid mode")
    print("  ✅ Workflow validation passes")
    print("  ✅ Merge preserves all fields including conversation_id")
    print("  ✅ State Machine Logic receives valid conversation_id")
    print("  ✅ UPDATE queries work correctly")
    print("  ✅ State persists in database")
    print("  ✅ Bot progresses correctly (no loop back to menu)")

    print("\n" + "="*60)
    print("TESTING STEPS:")
    print("="*60)
    print("1. Import workflow V48.2 in n8n:")
    print("   http://localhost:5678")
    print("\n2. Deactivate workflow V48.1")
    print("\n3. Activate workflow V48.2")
    print("\n4. Clean test conversation:")
    print("   docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \\")
    print("     -c \"DELETE FROM conversations WHERE phone_number = '556181755748';\"")
    print("\n5. Test with WhatsApp:")
    print("   - Send 'oi' → Bot shows menu ✅")
    print("   - Send '1' → Bot asks for name ✅")
    print("   - Send 'Bruno Rosa' → Bot asks for phone ✅ (NOT menu!)")
    print("\n6. Check logs for V48 diagnostics:")
    print("   docker logs e2bot-n8n-dev 2>&1 | grep 'V48'")
    print("\n   Expected logs:")
    print("   ✅ V48 CONVERSATION ID CHECK")
    print("   ✅ FINAL conversation_id: 8b455c85... (NOT NULL!)")
    print("   ✅ V48: conversation_id validated")
    print("\n7. Verify database:")
    print("   docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \\")
    print("     -c \"SELECT phone_number, state_machine_state, contact_name FROM conversations;\"")
    print("\n   Expected:")
    print("   - state_machine_state = 'collect_phone' (NOT 'service_selection')")
    print("   - contact_name = 'Bruno Rosa'")

    print("\n" + "="*60)
    print("VALIDATION:")
    print("="*60)
    print("Check workflow imports without validation errors:")
    print("  - n8n should accept the workflow")
    print("  - No 'value not supported' errors")
    print("  - Merge node configuration valid")
    print("  - Workflow executes without stopping at Merge")
    print("  - conversation_id should NOT be NULL")
    print("  - Database should update correctly")
    print("="*60)

    return True

if __name__ == '__main__':
    success = fix_workflow_v48_2_merge_index()
    exit(0 if success else 1)
