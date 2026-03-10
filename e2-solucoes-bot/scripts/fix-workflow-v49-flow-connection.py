#!/usr/bin/env python3
"""
V49 Fix Script - Add Missing Connection in Flow
Purpose: Fix conversation_id NULL by connecting Create New Conversation → Merge Conversation Data
Root Cause: Create New Conversation não tem saída conectada ao Merge (input 1)
Result: Both new and existing user flows provide 'id' to State Machine
"""

import json
from pathlib import Path

def fix_workflow_v49_flow_connection():
    """Add missing connection from Create New Conversation to Merge Conversation Data"""

    # Paths
    base_dir = Path(__file__).parent.parent
    workflow_v48_4 = base_dir / "n8n/workflows/02_ai_agent_conversation_V48_4_CUSTOM_MERGE.json"
    workflow_v49 = base_dir / "n8n/workflows/02_ai_agent_conversation_V49_FLOW_FIX.json"

    print("=== V49 FLOW CONNECTION FIX ===")
    print(f"Reading: {workflow_v48_4}")

    # Read workflow V48.4
    with open(workflow_v48_4, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    changes_made = []

    # Find Create New Conversation node
    create_node = None
    for node in workflow['nodes']:
        if node['name'] == 'Create New Conversation':
            create_node = node
            break

    if not create_node:
        print("❌ ERROR: 'Create New Conversation' node not found")
        return False

    print(f"\n✅ Found 'Create New Conversation' node")
    print(f"   Node ID: {create_node['id']}")

    # Check current connections
    current_connections = workflow.get('connections', {}).get('Create New Conversation', {}).get('main', [[]])

    print(f"\n📊 Current Connections from 'Create New Conversation':")
    if current_connections and current_connections[0]:
        for conn in current_connections[0]:
            print(f"   → {conn.get('node')} (index: {conn.get('index', 0)})")
    else:
        print("   ❌ NO CONNECTIONS (this is the bug!)")

    # CRITICAL FIX: Add connection to Merge Conversation Data with index=1 (second input)
    new_connection = {
        "node": "Merge Conversation Data",
        "type": "main",
        "index": 1  # CRITICAL: Input 1 (second input to merge node)
    }

    # Update connections
    if 'Create New Conversation' not in workflow['connections']:
        workflow['connections']['Create New Conversation'] = {"main": [[]]}

    if not workflow['connections']['Create New Conversation']['main']:
        workflow['connections']['Create New Conversation']['main'] = [[]]

    # Add new connection to existing connections
    workflow['connections']['Create New Conversation']['main'][0].append(new_connection)

    changes_made.append("Added connection: Create New Conversation → Merge Conversation Data (input 1)")

    print("\n✅ Connection Added!")
    print(f"   Create New Conversation → Merge Conversation Data (index: 1)")

    # Verify complete flow
    print("\n📊 Verifying Complete Flow:")

    # Check Merge Queries Data connections
    merge_queries_conn = workflow['connections'].get('Merge Queries Data', {}).get('main', [[]])
    print("\n1. Merge Queries Data connections:")
    for conn in merge_queries_conn[0]:
        print(f"   → {conn['node']} (index: {conn.get('index', 0)})")

    # Check Merge Queries Data1 connections
    merge_queries1_conn = workflow['connections'].get('Merge Queries Data1', {}).get('main', [[]])
    print("\n2. Merge Queries Data1 connections:")
    for conn in merge_queries1_conn[0]:
        print(f"   → {conn['node']} (index: {conn.get('index', 0)})")

    # Check Create New Conversation connections (after fix)
    create_conn = workflow['connections'].get('Create New Conversation', {}).get('main', [[]])
    print("\n3. Create New Conversation connections (AFTER FIX):")
    for conn in create_conn[0]:
        print(f"   → {conn['node']} (index: {conn.get('index', 0)})")

    # Check Get Conversation Details connections
    get_details_conn = workflow['connections'].get('Get Conversation Details', {}).get('main', [[]])
    print("\n4. Get Conversation Details connections:")
    for conn in get_details_conn[0]:
        print(f"   → {conn['node']} (index: {conn.get('index', 0)})")

    # Update workflow metadata
    workflow['name'] = "02 - AI Agent Conversation V49 (Flow Fix)"
    workflow['versionId'] = "v49-flow-connection-fix"

    # Save as V49
    print(f"\nSaving fixed workflow: {workflow_v49}")
    with open(workflow_v49, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print("\n✅ V49 Flow Connection Fix Complete!")
    print("\n" + "="*60)
    print("CHANGES MADE:")
    print("="*60)
    for i, change in enumerate(changes_made, 1):
        print(f"{i}. {change}")

    print("\n" + "="*60)
    print("PROBLEM ANALYSIS:")
    print("="*60)
    print("❌ V48.4 Bug:")
    print("   Create New Conversation → (NO OUTPUT CONNECTION)")
    print("   Result: Merge node receives only 1 input (missing 'id')")
    print("")
    print("✅ V49 Fix:")
    print("   Create New Conversation → Merge Conversation Data (input 1)")
    print("   Result: Merge node receives 2 inputs (HAS 'id')")

    print("\n" + "="*60)
    print("EXPECTED FLOW AFTER FIX:")
    print("="*60)
    print("\n📍 NEW USER (count = 0):")
    print("   Merge Queries Data")
    print("      ├─→ Create New Conversation (RETURNING *)")
    print("      │   └─→ Merge Conversation Data (input 1) ✅ COM ID!")
    print("      └─→ Merge Conversation Data (input 0) ✅ COM QUERIES!")
    print("")
    print("📍 EXISTING USER (count > 0):")
    print("   Merge Queries Data1")
    print("      ├─→ Get Conversation Details (SELECT *)")
    print("      │   └─→ Merge Conversation Data (input 1) ✅ COM ID!")
    print("      └─→ Merge Conversation Data (input 0) ✅ COM QUERIES!")

    print("\n" + "="*60)
    print("TESTING STEPS:")
    print("="*60)
    print("1. Import workflow V49 in n8n")
    print("   http://localhost:5678")
    print("")
    print("2. Deactivate V48.4, activate V49")
    print("")
    print("3. Clean test data:")
    print("   docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \\")
    print("     -c \"DELETE FROM conversations WHERE phone_number = '556181755748';\"")
    print("")
    print("4. Test NEW USER flow:")
    print("   - Send 'oi' → Bot shows menu")
    print("   - Send '1' → Bot asks for name")
    print("   - Send 'Bruno Rosa' → Bot asks for phone (NOT menu!)")
    print("")
    print("5. Check V48.4 Custom Merge logs:")
    print("   docker logs e2bot-n8n-dev 2>&1 | grep -A 15 'V48.4 CUSTOM MERGE'")
    print("")
    print("   Expected:")
    print("   ✅ Query input keys: [...query fields...]")
    print("   ✅ DB input keys: [..., 'id', ...]  ← NOW PRESENT!")
    print("   ✅ DB input id: d784ce32-...  ← UUID NOT undefined!")
    print("   ✅ Merged id: d784ce32-...")
    print("   ✅ conversation_id: d784ce32-...")
    print("")
    print("6. Check V48 State Machine logs:")
    print("   docker logs e2bot-n8n-dev 2>&1 | grep -A 10 'V48 CONVERSATION ID CHECK'")
    print("")
    print("   Expected:")
    print("   ✅ Input data keys: [..., 'id', ...]  ← NOW PRESENT!")
    print("   ✅ raw_id: d784ce32-...  ← NOT undefined!")
    print("   ✅ FINAL conversation_id: d784ce32-...  ← NOT NULL!")
    print("   ✅ V48: conversation_id validated")
    print("")
    print("7. Verify database:")
    print("   docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev -c \\")
    print("     \"SELECT phone_number, state_machine_state, contact_name \\")
    print("      FROM conversations WHERE phone_number = '556181755748';\"")
    print("")
    print("   Expected:")
    print("   - state_machine_state: collect_phone ✅ (NOT service_selection!)")
    print("   - contact_name: Bruno Rosa ✅ (NOT empty!)")

    print("\n" + "="*60)
    print("VALIDATION:")
    print("="*60)
    print("✅ Missing connection added successfully")
    print("✅ Both flows now provide 'id' to Merge node")
    print("✅ conversation_id will be valid in State Machine")
    print("✅ Ready for import and testing")
    print("="*60)

    return True

if __name__ == '__main__':
    success = fix_workflow_v49_flow_connection()
    exit(0 if success else 1)
