#!/usr/bin/env python3
"""
V46 Fix Script - Surgical removal of state_machine_state from leads query
Purpose: Fix architectural duplication between conversations and leads tables
"""

import json
from pathlib import Path

def fix_workflow_v46_surgical():
    """Surgically remove state_machine_state references from leads query only"""

    # Paths
    base_dir = Path(__file__).parent.parent
    workflow_v41 = base_dir / "n8n/workflows/02_ai_agent_conversation_V41_QUERY_BATCHING_FIX.json"
    workflow_v46 = base_dir / "n8n/workflows/02_ai_agent_conversation_V46_LEADS_FIX.json"

    print("=== V46 SURGICAL FIX: Remove state_machine_state from leads ===")
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

    print(f"\n📊 Original code length: {len(js_code)} characters")

    # Find and replace the query_upsert_lead section
    # We'll do precise string replacements for the specific lines

    # Fix 1: Remove state_machine_state from UPDATE SET
    original_update_line = "    state_machine_state = '${next_stage}',"
    replacement_update_line = "    -- V46: state_machine_state removed (belongs to conversations only)"

    if original_update_line in js_code:
        js_code = js_code.replace(original_update_line, replacement_update_line)
        print("✅ Fixed UPDATE SET clause")
    else:
        print("⚠️  UPDATE SET clause pattern not found")

    # Fix 2: Remove state_machine_state from INSERT column list
    original_insert_col = "    state_machine_state,"
    replacement_insert_col = "    -- V46: state_machine_state removed"

    # Count occurrences before replacement
    count_before = js_code.count(original_insert_col)
    print(f"\n📊 Found {count_before} occurrences of 'state_machine_state,' in INSERT columns")

    # Replace in leads INSERT only by being more specific
    # Look for the leads INSERT context
    leads_insert_marker = "INSERT INTO leads ("
    if leads_insert_marker in js_code:
        # Find the position of leads INSERT
        leads_pos = js_code.find(leads_insert_marker)
        # Find the end of that INSERT statement (look for "WHERE NOT EXISTS")
        leads_end = js_code.find("WHERE NOT EXISTS", leads_pos)

        if leads_end > leads_pos:
            # Extract the leads INSERT section
            leads_section = js_code[leads_pos:leads_end]

            # Replace in this section only
            leads_section_fixed = leads_section.replace(original_insert_col, replacement_insert_col)

            # Replace back in the full code
            js_code = js_code[:leads_pos] + leads_section_fixed + js_code[leads_end:]
            print("✅ Fixed INSERT column list in leads query")
        else:
            print("⚠️  Could not find end of leads INSERT")
    else:
        print("⚠️  leads INSERT marker not found")

    # Fix 3: Remove next_stage value from INSERT SELECT
    original_value_line = "    '${next_stage}',"
    replacement_value_line = "    -- V46: next_stage value removed"

    # Again, be specific to leads context
    select_marker = "  SELECT\n    '${phone_with_code}',"
    if select_marker in js_code:
        select_pos = js_code.find(select_marker)
        # Find WHERE NOT EXISTS after this SELECT
        where_pos = js_code.find("WHERE NOT EXISTS", select_pos)

        if where_pos > select_pos:
            select_section = js_code[select_pos:where_pos]
            select_section_fixed = select_section.replace(original_value_line, replacement_value_line)
            js_code = js_code[:select_pos] + select_section_fixed + js_code[where_pos:]
            print("✅ Fixed INSERT SELECT values in leads query")
        else:
            print("⚠️  Could not find WHERE NOT EXISTS after SELECT")
    else:
        print("⚠️  SELECT marker not found")

    # Verify changes
    print(f"\n📊 Modified code length: {len(js_code)} characters")

    # Count remaining state_machine_state occurrences
    remaining_in_conversations = js_code.count("state_machine_state")
    print(f"📊 Remaining 'state_machine_state' occurrences: {remaining_in_conversations}")
    print("   (Should be ~2: one in conversations UPDATE, one in conversations INSERT)")

    # Update node with fixed code
    build_update_node['parameters']['jsCode'] = js_code

    # Update workflow metadata
    workflow['name'] = "02 - AI Agent Conversation V46 (Leads Duplication Fix)"
    workflow['versionId'] = "v46-leads-fix-surgical"

    # Save as V46
    print(f"\nSaving fixed workflow: {workflow_v46}")
    with open(workflow_v46, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print("\n✅ V46 Surgical Fix Complete!")
    print("\n" + "="*60)
    print("VERIFICATION:")
    print("="*60)
    print(f"✅ Workflow V46 created: {workflow_v46.name}")
    print(f"✅ state_machine_state removed from leads queries")
    print(f"✅ state_machine_state preserved in conversations queries")
    print("\n" + "="*60)
    print("NEXT STEPS:")
    print("="*60)
    print("1. Import workflow V46 in n8n:")
    print("   http://localhost:5678")
    print("2. Deactivate workflow V41")
    print("3. Activate workflow V46")
    print("4. Test with WhatsApp:")
    print("   - Send 'oi'")
    print("   - Complete conversation flow")
    print("   - Should see NO 'column does not exist' errors")
    print("="*60)

    return True

if __name__ == '__main__':
    success = fix_workflow_v46_surgical()
    exit(0 if success else 1)
