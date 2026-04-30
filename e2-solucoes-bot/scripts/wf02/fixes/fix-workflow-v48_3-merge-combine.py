#!/usr/bin/env python3
"""
V48.3 Fix Script - Merge Node to Combine Mode
Purpose: Change Merge node from mergeByIndex to combine for proper field preservation
Root Cause: mergeByIndex only takes first input, doesn't merge fields from both
Result: Use 'combine' mode with proper merge configuration to include all fields
"""

import json
from pathlib import Path

def fix_workflow_v48_3_merge_combine():
    """Fix Merge node to use 'combine' mode for proper field merging"""

    # Paths
    base_dir = Path(__file__).parent.parent
    workflow_v48_2 = base_dir / "n8n/workflows/02_ai_agent_conversation_V48_2_MERGE_INDEX_FIX.json"
    workflow_v48_3 = base_dir / "n8n/workflows/02_ai_agent_conversation_V48_3_MERGE_COMBINE_FIX.json"

    print("=== V48.3 MERGE COMBINE FIX ===")
    print(f"Reading: {workflow_v48_2}")

    # Read workflow V48.2
    with open(workflow_v48_2, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    changes_made = []

    # Fix: Merge Conversation Data - Use combine mode to merge all fields
    merge_node = None
    for node in workflow['nodes']:
        if node['name'] == 'Merge Conversation Data':
            merge_node = node
            break

    if merge_node:
        print("\n✅ Found 'Merge Conversation Data' node")
        print(f"   Current mode: {merge_node.get('parameters', {}).get('mode', 'NOT SET')}")

        # Change to combine mode which merges all fields from both inputs
        merge_node['parameters'] = {
            'mode': 'combine',
            'mergeByFields': {
                'values': []
            },
            'options': {
                'includeUnpopulated': True,
                'multipleMatches': 'first'
            }
        }

        changes_made.append("Changed Merge mode from 'mergeByIndex' to 'combine' with includeUnpopulated")
        print("✅ Changed Merge node to 'combine' mode with includeUnpopulated=true")
        print("   This mode combines ALL fields from BOTH inputs")
    else:
        print("❌ ERROR: 'Merge Conversation Data' node not found")

    # Update workflow metadata
    workflow['name'] = "02 - AI Agent Conversation V48.3 (Merge Combine Fix)"
    workflow['versionId'] = "v48-3-merge-combine-fix"

    # Save as V48.3
    print(f"\nSaving fixed workflow: {workflow_v48_3}")
    with open(workflow_v48_3, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print("\n✅ V48.3 Merge Combine Fix Complete!")
    print("\n" + "="*60)
    print("CHANGES MADE:")
    print("="*60)
    for i, change in enumerate(changes_made, 1):
        print(f"{i}. {change}")

    print("\n" + "="*60)
    print("ERROR FIXED:")
    print("="*60)
    print("❌ V48.2 Error: 'mergeByIndex' only takes fields from first input")
    print("✅ V48.3 Fix: Using 'combine' mode with includeUnpopulated=true")
    print("\nMerge modes comparison:")
    print("  - mergeByIndex: Merges by position, but doesn't combine fields")
    print("  - combine: Merges ALL fields from ALL inputs into single item")

    print("\n" + "="*60)
    print("CRITICAL FIX:")
    print("="*60)
    print("✅ Merge node now uses 'combine' mode:")
    print("   - Combines ALL fields from both inputs")
    print("   - includeUnpopulated: true ensures no field is lost")
    print("   - multipleMatches: 'first' handles multiple items")
    print("   - conversation_id from Get Conversation Details will be preserved")
    print("   - All query fields from Merge Queries Data will be preserved")

    print("\n" + "="*60)
    print("EXPECTED BEHAVIOR:")
    print("="*60)
    print("BEFORE V48.3:")
    print("  ❌ Merge receives two inputs:")
    print("     Input 1: {phone_number, query_count, query_details, ...}")
    print("     Input 2: {id, phone_number, state_machine_state, ...}")
    print("  ❌ mergeByIndex mode takes only Input 1 fields")
    print("  ❌ Result: NO 'id' field → conversation_id = NULL")
    print("\nAFTER V48.3:")
    print("  ✅ Merge receives two inputs:")
    print("     Input 1: {phone_number, query_count, query_details, ...}")
    print("     Input 2: {id, phone_number, state_machine_state, ...}")
    print("  ✅ combine mode merges ALL fields from BOTH inputs")
    print("  ✅ Result: {id, phone_number, query_count, state_machine_state, ...}")
    print("  ✅ State Machine Logic receives valid 'id' field")
    print("  ✅ conversation_id = id value (d784ce32-06f6-4423-9ff8-99e49ed81a15)")
    print("  ✅ UPDATE queries work correctly")
    print("  ✅ State persists in database")
    print("  ✅ Bot progresses correctly (no loop back to menu)")

    print("\n" + "="*60)
    print("TESTING STEPS:")
    print("="*60)
    print("1. Import workflow V48.3 in n8n:")
    print("   http://localhost:5678")
    print("\n2. Deactivate workflow V48.2")
    print("\n3. Activate workflow V48.3")
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
    print("   ✅ Input data keys: [..., 'id', ...]")
    print("   ✅ raw_id: d784ce32-06f6-4423-9ff8-99e49ed81a15")
    print("   ✅ FINAL conversation_id: d784ce32... (NOT NULL!)")
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
    print("Check workflow imports without errors:")
    print("  - n8n should accept the workflow")
    print("  - Merge node uses 'combine' mode")
    print("  - includeUnpopulated option is true")
    print("  - Execution should show 'id' field in State Machine Logic input")
    print("  - conversation_id should NOT be NULL")
    print("  - Database should update correctly")
    print("="*60)

    return True

if __name__ == '__main__':
    success = fix_workflow_v48_3_merge_combine()
    exit(0 if success else 1)
