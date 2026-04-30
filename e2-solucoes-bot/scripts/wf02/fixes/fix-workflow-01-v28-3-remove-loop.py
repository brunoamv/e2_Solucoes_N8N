#!/usr/bin/env python3
"""
Workflow 01 V2.8.3: Remove Loop Infinito
Corrige loop causado por "Extract Conversation ID" conectando de volta para "Save Message"

CRITICAL FIX:
- Remove nó "Extract Conversation ID" (lógica do V2.7 incompatível com V2.8)
- Conecta "Trigger AI Agent" diretamente para "Webhook Response Success"
- Elimina segunda execução de "Save Message" (causava loop)

Date: 2026-03-10
Author: Claude Code V2.8.3 Fix
"""

import json
from pathlib import Path

# Input and output
INPUT_WORKFLOW = "n8n/workflows/01_main_whatsapp_handler_V2.8.2_FINAL.json"
OUTPUT_WORKFLOW = "n8n/workflows/01_main_whatsapp_handler_V2.8.3_NO_LOOP.json"


def fix_workflow_01_v28_3_remove_loop():
    """
    Fix Workflow 01 removendo loop infinito

    V2.8.3 = V2.8.2 - Extract Conversation ID node (causa loop)
    """

    print("=" * 80)
    print("Workflow 01 V2.8.3: Remove Loop Infinito")
    print("=" * 80)

    # Load V2.8.2 workflow
    print(f"\n📂 Loading Workflow 01 V2.8.2: {INPUT_WORKFLOW}")
    with open(INPUT_WORKFLOW, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    print(f"✅ Workflow loaded: {len(workflow['nodes'])} nodes")

    # Find "Extract Conversation ID" node
    extract_conv_idx = None
    trigger_ai_idx = None
    webhook_success_idx = None

    for idx, node in enumerate(workflow['nodes']):
        if node['name'] == 'Extract Conversation ID':
            extract_conv_idx = idx
        elif node['name'] == 'Trigger AI Agent':
            trigger_ai_idx = idx
        elif node['name'] == 'Webhook Response Success':
            webhook_success_idx = idx

    if extract_conv_idx is None:
        print("❌ ERROR: Could not find 'Extract Conversation ID' node!")
        return False

    if trigger_ai_idx is None or webhook_success_idx is None:
        print("❌ ERROR: Could not find required nodes!")
        return False

    print(f"\n🔍 Found nodes:")
    print(f"   Extract Conversation ID: index {extract_conv_idx} (SERÁ REMOVIDO)")
    print(f"   Trigger AI Agent: index {trigger_ai_idx}")
    print(f"   Webhook Response Success: index {webhook_success_idx}")

    # Step 1: Remove "Extract Conversation ID" node
    print(f"\n🔧 Step 1: Removing 'Extract Conversation ID' node...")
    removed_node = workflow['nodes'].pop(extract_conv_idx)
    print(f"   ✓ Removed node: {removed_node['name']}")
    print(f"   ✓ Reason: Node caused infinite loop (Save Message → ... → AI Agent → Extract → Save Message)")

    # Step 2: Update connections - Remove "Extract Conversation ID" connections
    print(f"\n🔧 Step 2: Cleaning connections...")

    # Remove connections FROM "Extract Conversation ID"
    if "Extract Conversation ID" in workflow['connections']:
        del workflow['connections']["Extract Conversation ID"]
        print("   ✓ Removed connections FROM 'Extract Conversation ID'")

    # Step 3: Connect "Trigger AI Agent" directly to "Webhook Response Success"
    print(f"\n🔧 Step 3: Fixing 'Trigger AI Agent' connection...")

    workflow['connections']['Trigger AI Agent'] = {
        "main": [[{
            "node": "Webhook Response Success",
            "type": "main",
            "index": 0
        }]]
    }
    print("   ✓ Trigger AI Agent → Webhook Response Success (DIRETO, SEM LOOP)")

    # Step 4: Verify no more references to "Extract Conversation ID"
    print(f"\n🔧 Step 4: Verifying no ghost references...")
    ghost_found = False

    for node_name, connections in workflow['connections'].items():
        for output_idx, output_connections in enumerate(connections.get('main', [])):
            for conn in output_connections:
                if conn.get('node') == 'Extract Conversation ID':
                    print(f"   ⚠️  Ghost reference found: {node_name} → Extract Conversation ID")
                    ghost_found = True

    if not ghost_found:
        print("   ✓ No ghost references found")
    else:
        print("   ❌ ERROR: Ghost references still present!")
        return False

    # Step 5: Update workflow metadata
    workflow['name'] = '01 - WhatsApp Handler V2.8.3 (No Loop Fix)'
    workflow['versionId'] = 'v2-8-3-no-loop-fix'
    workflow['id'] = 'workflow-01-v28-3-no-loop'
    print(f"\n✅ Workflow metadata updated")

    # Save corrected workflow
    print(f"\n💾 Saving V2.8.3 workflow...")
    with open(OUTPUT_WORKFLOW, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print(f"✅ Workflow saved: {OUTPUT_WORKFLOW}")

    # Summary
    print("\n" + "=" * 80)
    print("✅ WORKFLOW 01 V2.8.3 NO LOOP FIX COMPLETE")
    print("=" * 80)
    print(f"Input:  {INPUT_WORKFLOW}")
    print(f"Output: {OUTPUT_WORKFLOW}")
    print(f"\n🔧 Critical Fixes Applied:")
    print(f"  1. ✓ Removed 'Extract Conversation ID' node (caused infinite loop)")
    print(f"  2. ✓ Connected 'Trigger AI Agent' directly to 'Webhook Response Success'")
    print(f"  3. ✓ Eliminated second 'Save Message' execution")
    print(f"  4. ✓ Verified no ghost references to deleted node")
    print(f"\n🐛 Bugs Fixed:")
    print(f"  ✓ Bug #1: Race Condition - Save Message PRIMEIRO (V2.8)")
    print(f"  ✓ Bug #2: Ghost Connections - Limpas (V2.8.1)")
    print(f"  ✓ Bug #3: Node Parameter References - Atualizadas (V2.8.2)")
    print(f"  ✓ Bug #4: ExpressionError - Eliminado (V2.8.2)")
    print(f"  ✓ Bug #5: Infinite Loop - CORRIGIDO (V2.8.3) ⭐")
    print(f"\n📋 New Execution Flow (SEM LOOP):")
    print(f"  1. Extract Message Data")
    print(f"  2. Save Message (ON CONFLICT, RETURNING) ← ÚNICO SAVE!")
    print(f"  3. Check Operation (analisa operation)")
    print(f"  4. Is Duplicate?")
    print(f"     ├─ true → Webhook Response Duplicate")
    print(f"     └─ false → Is Image?")
    print(f"        ├─ true → Trigger Image Analysis → Prepare Data")
    print(f"        └─ false → Prepare Data")
    print(f"                    ↓")
    print(f"                 Trigger AI Agent")
    print(f"                    ↓")
    print(f"                 Webhook Response Success ← SEM LOOP! ✅")
    print(f"\n🎯 Expected Behavior:")
    print(f"  ✓ V2.8.3 logs will show 'V2.8.2 Check Operation' messages")
    print(f"  ✓ Save Message executes APENAS UMA VEZ")
    print(f"  ✓ operation='inserted' for new messages (ÚNICO)")
    print(f"  ✓ operation='updated' for duplicates (blocked)")
    print(f"  ✓ NO infinite loop")
    print(f"  ✓ NO second Save Message execution")
    print(f"  ✓ Workflow completes successfully")
    print(f"  ✓ Workflow 02 is called and COMPLETES ✅")
    print(f"\n⚠️  IMPORTANTE:")
    print(f"  - conversation_id será NULL na primeira mensagem (OK!)")
    print(f"  - Workflow 02 (AI Agent) criará/atualizará conversation_id")
    print(f"  - Mensagens seguintes do mesmo contato terão conversation_id preenchido")
    print(f"  - Isso é NORMAL e ESPERADO no fluxo V2.8.x")
    print(f"\n📋 Next Steps:")
    print(f"  1. Import workflow in n8n: {OUTPUT_WORKFLOW}")
    print(f"  2. Deactivate V2.8.2 (had infinite loop)")
    print(f"  3. Activate V2.8.3")
    print(f"  4. Test with WhatsApp message")
    print(f"  5. Verify 'Save Message' executes ONLY ONCE")
    print(f"  6. Verify Workflow 02 is called and completes")
    print(f"  7. Verify no loop in execution logs")
    print("=" * 80)

    return True


if __name__ == '__main__':
    success = fix_workflow_01_v28_3_remove_loop()
    exit(0 if success else 1)
