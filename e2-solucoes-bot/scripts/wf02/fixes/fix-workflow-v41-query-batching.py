#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
V41 QUERY BATCHING FIX - Remove query batching do Update Conversation State
============================================================================
V40 tinha queryBatching: "independent" que fazia n8n engolir o RETURNING *.

PROBLEMA:
- Update Conversation State node em V40 usa queryBatching: "independent"
- Isso faz o n8n não retornar o resultado do RETURNING *
- Query manual funciona, mas no workflow retorna empty output

SOLUÇÃO V41:
- Remover "queryBatching" option do Update Conversation State node
- Query executará normalmente e retornará o RETURNING *
- Estado será atualizado corretamente

FIX: Remove queryBatching option (lines 158-160 in V40)
"""

import json
import sys
from pathlib import Path

# Usar V40 como base
BASE_WORKFLOW = "02_ai_agent_conversation_V40_COMPLETE_STRUCTURE.json"
OUTPUT_WORKFLOW = "02_ai_agent_conversation_V41_QUERY_BATCHING_FIX.json"

def fix_update_conversation_node(workflow):
    """Remove queryBatching option from Update Conversation State node."""

    for node in workflow.get('nodes', []):
        if node.get('name') == 'Update Conversation State':
            print(f"✅ Found Update Conversation State node")

            # Current config
            if 'parameters' in node:
                params = node['parameters']
                print(f"   Current parameters: {json.dumps(params, indent=2)}")

                # Remove queryBatching option
                if 'options' in params:
                    if 'queryBatching' in params['options']:
                        del params['options']['queryBatching']
                        print("   ✅ Removed queryBatching option")

                    # If options is now empty, remove it entirely
                    if not params['options']:
                        del params['options']
                        print("   ✅ Removed empty options object")

                print(f"   New parameters: {json.dumps(params, indent=2)}")
                return True

    return False

def update_workflow():
    """Update V40 workflow to remove query batching."""

    # Load V40 workflow
    base_path = Path(f"../n8n/workflows/{BASE_WORKFLOW}")
    if not base_path.exists():
        print(f"❌ Base workflow not found: {BASE_WORKFLOW}")
        return False

    with open(base_path, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    print(f"✅ Loaded base workflow: {BASE_WORKFLOW}")
    print(f"   Nodes count: {len(workflow.get('nodes', []))}")

    # Fix Update Conversation State node
    if not fix_update_conversation_node(workflow):
        print("❌ Update Conversation State node not found!")
        return False

    # Update workflow name
    workflow['name'] = "02 - AI Agent Conversation V41 (Query Batching Fix)"

    # Save as V41
    output_path = Path(f"../n8n/workflows/{OUTPUT_WORKFLOW}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print(f"✅ Created: {OUTPUT_WORKFLOW}")
    print(f"   Preserves all {len(workflow.get('nodes', []))} nodes from V40")
    return True

def main():
    """Main function to create V41."""

    print("=" * 60)
    print("V41 - QUERY BATCHING FIX")
    print("=" * 60)
    print()
    print("PROBLEMA V40:")
    print("  • Update Conversation State usa queryBatching: independent")
    print("  • n8n engole o resultado do RETURNING *")
    print("  • Output vem empty mesmo com query correta")
    print()
    print("SOLUÇÃO V41:")
    print("  • Remover queryBatching option do node")
    print("  • Query executará normalmente")
    print("  • RETURNING * funcionará corretamente")
    print()

    success = update_workflow()

    if success:
        print()
        print("=" * 60)
        print("SUCCESS! V41 WORKFLOW CREATED")
        print("=" * 60)
        print()
        print("🎯 V41 FIX:")
        print("- ✅ Removed queryBatching: independent option")
        print("- ✅ RETURNING * will now return data")
        print("- ✅ Conversation state will persist")
        print()
        print("📋 NEXT STEPS:")
        print()
        print("1. DEACTIVATE V40 workflow")
        print()
        print("2. IMPORT AND ACTIVATE V41:")
        print(f"   - Import: {OUTPUT_WORKFLOW}")
        print("   - Activate it")
        print()
        print("3. TEST:")
        print("   - Send 'oi' → Menu")
        print("   - Send '1' → Ask for name")
        print("   - Send 'Bruno Rosa' → ACCEPTED + persist")
        print("   - Check database: state_machine_state should be 'collect_phone'")
        print()
        print("4. MONITOR:")
        print("   docker logs -f e2bot-n8n-dev 2>&1 | grep -E 'V40|Update Conversation'")
        print()
        print("✅ V41 = V40 + Query Batching Fix!")
        print()
        return True

    return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
