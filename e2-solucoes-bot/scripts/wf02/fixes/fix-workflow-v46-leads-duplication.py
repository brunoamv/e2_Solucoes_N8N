#!/usr/bin/env python3
"""
V46 Fix Script - Remove state_machine_state from leads table queries
Purpose: Fix architectural duplication between conversations and leads tables
"""

import json
import re
from pathlib import Path

def fix_workflow_v46():
    """Remove state_machine_state references from leads queries in V41"""

    # Paths
    base_dir = Path(__file__).parent.parent
    workflow_v41 = base_dir / "n8n/workflows/02_ai_agent_conversation_V41_QUERY_BATCHING_FIX.json"
    workflow_v46 = base_dir / "n8n/workflows/02_ai_agent_conversation_V46_LEADS_FIX.json"

    print("=== V46 FIX: Remove state_machine_state from leads queries ===")
    print(f"Reading: {workflow_v41}")

    # Read workflow V41
    with open(workflow_v41, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    # Find "Build Update Queries" node
    build_update_node = None
    for node in workflow['nodes']:
        if node['name'] == 'Build Update Queries':
            build_update_node = node
            break

    if not build_update_node:
        print("❌ ERROR: 'Build Update Queries' node not found")
        return False

    print("✅ Found 'Build Update Queries' node")

    # Get JavaScript code
    js_code = build_update_node['parameters']['jsCode']

    # Count original occurrences for verification
    original_count = js_code.count('state_machine_state')
    print(f"\n📊 Original occurrences of 'state_machine_state': {original_count}")

    # Pattern 1: Remove state_machine_state from UPDATE SET clause in leads query
    print("\n1. Removing state_machine_state from UPDATE SET clause...")
    pattern_update = r"(\s+)(state_machine_state\s*=\s*'\${next_stage}',\s*\n)"
    matches_update = len(re.findall(pattern_update, js_code))
    print(f"   Found {matches_update} UPDATE SET occurrences")

    js_code_fixed = re.sub(
        pattern_update,
        r"\1-- V46: state_machine_state removed (belongs to conversations only)\n",
        js_code
    )

    # Pattern 2: Remove state_machine_state from INSERT column list
    print("2. Removing state_machine_state from INSERT columns...")
    pattern_insert_col = r"(\s+)(state_machine_state,\s*\n)"
    matches_insert_col = len(re.findall(pattern_insert_col, js_code_fixed))
    print(f"   Found {matches_insert_col} INSERT column occurrences")

    js_code_fixed = re.sub(
        pattern_insert_col,
        r"\1-- V46: state_machine_state removed\n",
        js_code_fixed
    )

    # Pattern 3: Remove next_stage value from INSERT VALUES (only in leads context)
    print("3. Removing next_stage value from INSERT VALUES...")
    # More precise pattern to only match in leads INSERT context
    pattern_insert_val = r"(INSERT INTO leads[\s\S]*?VALUES[\s\S]*?)('\${next_stage}',\s*\n)"
    matches_insert_val = len(re.findall(pattern_insert_val, js_code_fixed))
    print(f"   Found {matches_insert_val} INSERT value occurrences in leads query")

    js_code_fixed = re.sub(
        pattern_insert_val,
        r"\1-- V46: next_stage value removed\n",
        js_code_fixed
    )

    # Count remaining occurrences (should still have some for conversations table)
    remaining_count = js_code_fixed.count('state_machine_state')
    removed_count = original_count - remaining_count

    print(f"\n📊 Verification:")
    print(f"   Original occurrences: {original_count}")
    print(f"   Remaining occurrences: {remaining_count}")
    print(f"   Removed occurrences: {removed_count}")

    if removed_count == 0:
        print("\n⚠️  WARNING: No occurrences were removed!")
        print("This might indicate the pattern didn't match.")
        print("Please check the workflow manually.")

    # Update node with fixed code
    build_update_node['parameters']['jsCode'] = js_code_fixed

    # Update workflow metadata
    workflow['name'] = "02 - AI Agent Conversation V46 (Leads Duplication Fix)"
    workflow['versionId'] = "v46-leads-fix"

    # Save as V46
    print(f"\nSaving fixed workflow: {workflow_v46}")
    with open(workflow_v46, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print("\n✅ V46 Fix Complete!")
    print("\n" + "="*60)
    print("NEXT STEPS:")
    print("="*60)
    print("1. Import workflow V46 in n8n interface:")
    print("   http://localhost:5678")
    print("2. Deactivate workflow V41")
    print("3. Activate workflow V46")
    print("4. Test with WhatsApp message:")
    print("   - Send 'oi'")
    print("   - Complete conversation flow")
    print("   - Verify no 'column does not exist' errors")
    print("5. Verify database:")
    print("   - conversations table HAS state_machine_state ✅")
    print("   - leads table DOES NOT use state_machine_state ✅")
    print("="*60)

    return True

if __name__ == '__main__':
    success = fix_workflow_v46()
    exit(0 if success else 1)
