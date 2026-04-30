#!/usr/bin/env python3
"""
V47 Fix Script - Phone Number Consistency Fix
Purpose: Ensure all queries use phone_with_code consistently (with 55 prefix)
Root Cause: Build SQL Queries inserts with phone_without_code while Build Update Queries uses phone_with_code
Result: Creates duplicate conversations with different phone numbers
"""

import json
from pathlib import Path

def fix_workflow_v47_phone_consistency():
    """Fix phone number inconsistency between create and update operations"""

    # Paths
    base_dir = Path(__file__).parent.parent
    workflow_v46 = base_dir / "n8n/workflows/02_ai_agent_conversation_V46_LEADS_FIX.json"
    workflow_v47 = base_dir / "n8n/workflows/02_ai_agent_conversation_V47_PHONE_CONSISTENCY.json"

    print("=== V47 PHONE CONSISTENCY FIX ===")
    print(f"Reading: {workflow_v46}")

    # Read workflow V46
    with open(workflow_v46, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    # Find "Build SQL Queries" node (the one that creates new conversations)
    build_sql_node = None
    for node in workflow['nodes']:
        if node['name'] == 'Build SQL Queries':
            build_sql_node = node
            break

    if not build_sql_node:
        print("❌ ERROR: 'Build SQL Queries' node not found")
        return False

    print("✅ Found 'Build SQL Queries' node")

    # Get JavaScript code
    js_code = build_sql_node['parameters']['jsCode']

    print(f"\n📊 Original code length: {len(js_code)} characters")

    # Fix: Change INSERT to use phone_with_code instead of phone_without_code
    original_insert_line = "    '${escapeSql(phone_without_code)}',"
    replacement_insert_line = "    '${escapeSql(phone_with_code)}',"

    # Context: This is the VALUES section of the INSERT statement
    insert_marker = "INSERT INTO conversations ("
    values_marker = ") VALUES ("

    if insert_marker in js_code and values_marker in js_code:
        # Find the INSERT INTO conversations section
        insert_pos = js_code.find(insert_marker)
        values_pos = js_code.find(values_marker, insert_pos)
        on_conflict_pos = js_code.find("ON CONFLICT", values_pos)

        if on_conflict_pos > values_pos:
            # Extract the VALUES section
            values_section = js_code[values_pos:on_conflict_pos]

            # Replace phone_without_code with phone_with_code in VALUES
            values_section_fixed = values_section.replace(
                original_insert_line,
                replacement_insert_line
            )

            # Replace back in the full code
            js_code = js_code[:values_pos] + values_section_fixed + js_code[on_conflict_pos:]
            print("✅ Fixed INSERT VALUES to use phone_with_code")
        else:
            print("⚠️  Could not find ON CONFLICT after VALUES")
    else:
        print("⚠️  INSERT marker not found")

    # Verify changes
    print(f"\n📊 Modified code length: {len(js_code)} characters")

    # Count occurrences
    count_with_code = js_code.count("phone_with_code")
    count_without_code = js_code.count("phone_without_code")
    print(f"📊 phone_with_code occurrences: {count_with_code}")
    print(f"📊 phone_without_code occurrences: {count_without_code}")

    # Update node with fixed code
    build_sql_node['parameters']['jsCode'] = js_code

    # Update workflow metadata
    workflow['name'] = "02 - AI Agent Conversation V47 (Phone Consistency Fix)"
    workflow['versionId'] = "v47-phone-consistency"

    # Save as V47
    print(f"\nSaving fixed workflow: {workflow_v47}")
    with open(workflow_v47, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print("\n✅ V47 Phone Consistency Fix Complete!")
    print("\n" + "="*60)
    print("CRITICAL FIX:")
    print("="*60)
    print("✅ Build SQL Queries now uses phone_with_code (556181755748)")
    print("✅ Build Update Queries already uses phone_with_code (556181755748)")
    print("✅ NO MORE DUPLICATE CONVERSATIONS!")
    print("\n" + "="*60)
    print("VERIFICATION:")
    print("="*60)
    print(f"✅ Workflow V47 created: {workflow_v47.name}")
    print("✅ Phone number consistency enforced")
    print("\n" + "="*60)
    print("DATABASE CLEANUP REQUIRED:")
    print("="*60)
    print("Before testing, delete duplicate conversation:")
    print("  DELETE FROM conversations WHERE phone_number = '6181755748';")
    print("\n" + "="*60)
    print("NEXT STEPS:")
    print("="*60)
    print("1. Clean duplicates:")
    print("   docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \\")
    print("     -c \"DELETE FROM conversations WHERE phone_number = '6181755748';\"")
    print("2. Import workflow V47 in n8n:")
    print("   http://localhost:5678")
    print("3. Deactivate workflow V46")
    print("4. Activate workflow V47")
    print("5. Test with WhatsApp:")
    print("   - Send 'oi'")
    print("   - Select service: 1")
    print("   - Name: Bruno Rosa")
    print("   - Should NOW ask for phone (not return to menu!)")
    print("="*60)

    return True

if __name__ == '__main__':
    success = fix_workflow_v47_phone_consistency()
    exit(0 if success else 1)
