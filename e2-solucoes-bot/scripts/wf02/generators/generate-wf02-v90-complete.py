#!/usr/bin/env python3
"""
Generate WF02 V90 COMPLETE workflow JSON
Combines V89 workflow structure with V90 refactored State Machine
"""

import json
import sys
from pathlib import Path

def main():
    # Paths
    v89_json_path = Path("/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V89_COMPLETE.json")
    v90_state_machine_path = Path("/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/scripts/wf02-v90-state-machine-refactored.js")
    output_path = Path("/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V90_COMPLETE.json")

    # Read V89 workflow
    print("📖 Reading V89 workflow JSON...")
    with open(v89_json_path, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    # Read V90 State Machine code
    print("📖 Reading V90 State Machine code...")
    with open(v90_state_machine_path, 'r', encoding='utf-8') as f:
        v90_code = f.read()

    # Find State Machine Logic node
    state_machine_node = None
    for node in workflow.get('nodes', []):
        if node.get('name') == 'State Machine Logic':
            state_machine_node = node
            break

    if not state_machine_node:
        print("❌ ERROR: State Machine Logic node not found!")
        return 1

    print("✅ Found State Machine Logic node")

    # Update with V90 code
    if 'parameters' not in state_machine_node:
        state_machine_node['parameters'] = {}

    state_machine_node['parameters']['jsCode'] = v90_code

    # Update workflow metadata
    workflow['name'] = '02_ai_agent_conversation_V90_COMPLETE'

    # Add V90 metadata to workflow meta if exists
    if 'meta' not in workflow:
        workflow['meta'] = {}

    workflow['meta']['version'] = 'V90'
    workflow['meta']['description'] = 'State Machine V90 - Clean refactored code + multi-source state initialization + V89 WF06 data access'
    workflow['meta']['changes'] = [
        'V90: Multi-source state initialization (input.current_stage || input.next_stage || currentData.current_stage)',
        'V90: Clean refactored code structure with constants',
        'V90: Enhanced logging throughout all states',
        'V90: Maintained V89 multi-location WF06 data access',
        'V90: Removed legacy code and redundant comments'
    ]

    # Write V90 workflow
    print(f"💾 Writing V90 workflow to {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    # Summary
    print("\n" + "="*60)
    print("✅ WF02 V90 COMPLETE GENERATED")
    print("="*60)
    print(f"📄 Output: {output_path}")
    print(f"📊 Nodes: {len(workflow.get('nodes', []))}")
    print(f"🔗 Connections: {len(workflow.get('connections', {}))}")
    print("\n🎯 Key Changes:")
    print("  • Multi-source state initialization fixed")
    print("  • Clean refactored code structure")
    print("  • Enhanced V90 logging")
    print("  • V89 WF06 data access maintained")
    print("  • Legacy code removed")
    print("\n📋 Next Steps:")
    print("  1. Import to n8n: http://localhost:5678")
    print("  2. Activate workflow")
    print("  3. Test with services 1 and 3 (WF06 integration)")
    print("="*60)

    return 0

if __name__ == '__main__':
    sys.exit(main())
