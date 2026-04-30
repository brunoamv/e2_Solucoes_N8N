#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
V33 DEFINITIVE FIX - stateNameMapping Not Defined Error
========================================================
CRITICAL FIX: Adds stateNameMapping definition BEFORE line 130
where it's used, fixing the "stateNameMapping is not defined" error.

This script:
1. Loads the most recent workflow (V32 or V31)
2. Adds stateNameMapping at the BEGINNING of the code
3. Ensures the mapping is available throughout execution
4. Saves as V33_DEFINITIVE for import into n8n
"""

import json
import sys
from pathlib import Path

# Try V32 first, fallback to V31
POSSIBLE_WORKFLOWS = [
    "02_ai_agent_conversation_V32_STATE_MAPPING.json",
    "02_ai_agent_conversation_V31_COMPREHENSIVE_FIX.json",
    "02_ai_agent_conversation_V30_VALIDATOR_ISOLATION.json"
]

OUTPUT_WORKFLOW = "02_ai_agent_conversation_V33_DEFINITIVE.json"

def create_state_mapping_definition():
    """Create the complete stateNameMapping object."""
    return """
// =====================================
// V33 DEFINITIVE FIX: STATE NAME MAPPING
// =====================================
// CRITICAL: This MUST be defined BEFORE line 130 where it's used
// This maps database state names to code state names

const stateNameMapping = {
  // Database state name → Code state name
  'identificando_servico': 'service_selection',  // CRITICAL MAPPING
  'service_selection': 'service_selection',
  'coletando_nome': 'collect_name',
  'collect_name': 'collect_name',
  'coletando_telefone': 'collect_phone',
  'collect_phone': 'collect_phone',
  'coletando_email': 'collect_email',
  'collect_email': 'collect_email',
  'coletando_cidade': 'collect_city',
  'collect_city': 'collect_city',
  'confirmacao': 'confirmation',
  'confirmation': 'confirmation',
  'agendamento': 'scheduling',
  'scheduling': 'scheduling',
  'transferencia_comercial': 'handoff_comercial',
  'handoff_comercial': 'handoff_comercial',
  'finalizado': 'completed',
  'completed': 'completed',
  'greeting': 'greeting',
  'saudacao': 'greeting'
};

console.log('=============== V33 DEFINITIVE FIX ACTIVE ===============');
console.log('V33 STATE MAPPING: Initialized with', Object.keys(stateNameMapping).length, 'mappings');
console.log('V33 FIX: stateNameMapping is now defined BEFORE line 130');
console.log('=========================================================');

"""

def fix_workflow():
    """Apply V33 definitive fix to workflow."""

    print("=" * 60)
    print("V33 DEFINITIVE FIX - CRITICAL ERROR RESOLUTION")
    print("=" * 60)
    print()
    print("🔴 FIXING: stateNameMapping is not defined [Line 130]")
    print()

    # Find a base workflow to fix
    base_workflow = None
    workflow_path = None

    for workflow_name in POSSIBLE_WORKFLOWS:
        test_path = Path(f"../n8n/workflows/{workflow_name}")
        if test_path.exists():
            base_workflow = workflow_name
            workflow_path = test_path
            break

    if not workflow_path:
        print("❌ ERROR: No base workflow found to fix!")
        print("   Tried:", POSSIBLE_WORKFLOWS)
        return False

    print(f"✅ Found base workflow: {base_workflow}")

    # Load the workflow
    with open(workflow_path, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    # Find the State Machine Logic node
    state_machine_node = None
    for node in workflow.get('nodes', []):
        if 'State Machine' in node.get('name', ''):
            state_machine_node = node
            break

    if not state_machine_node:
        print("❌ ERROR: State Machine Logic node not found!")
        return False

    print("✅ Found State Machine Logic node")

    # Get the current code
    current_code = state_machine_node['parameters']['functionCode']

    # Check if stateNameMapping is already defined (it shouldn't be)
    if 'const stateNameMapping' in current_code:
        print("⚠️ WARNING: stateNameMapping already exists in code")
        print("   Removing old definition and adding at the beginning")
        # Remove any existing stateNameMapping definition
        lines = current_code.split('\n')
        new_lines = []
        skip_until_closing = False
        for line in lines:
            if 'const stateNameMapping' in line:
                skip_until_closing = True
                continue
            if skip_until_closing and '};' in line:
                skip_until_closing = False
                continue
            if not skip_until_closing:
                new_lines.append(line)
        current_code = '\n'.join(new_lines)

    print()
    print("📝 APPLYING FIX:")
    print("  1. Adding stateNameMapping definition at code START")
    print("  2. This ensures it's defined BEFORE line 130")
    print("  3. Making it available throughout entire execution")
    print()

    # Find where to insert the mapping
    # We need to add it at the very beginning, after the initial variable declarations

    # Look for the first major section or just add at the beginning
    insert_position = 0

    # Try to find a good insertion point after initial setup
    if '// Get conversation data' in current_code:
        insert_position = current_code.find('// Get conversation data')
    elif 'const conversation' in current_code:
        # Add after the first const conversation line
        first_const = current_code.find('const conversation')
        if first_const > 0:
            # Find the end of that line
            newline_after = current_code.find('\n', first_const)
            if newline_after > 0:
                insert_position = newline_after + 1

    # Insert the state mapping definition
    if insert_position > 0:
        fixed_code = (
            current_code[:insert_position] +
            "\n" + create_state_mapping_definition() + "\n" +
            current_code[insert_position:]
        )
    else:
        # Just add at the very beginning
        fixed_code = create_state_mapping_definition() + "\n" + current_code

    # Update the node with fixed code
    state_machine_node['parameters']['functionCode'] = fixed_code

    # Add V33 marker to workflow name
    workflow['name'] = "02 - AI Agent Conversation V33 DEFINITIVE FIX"

    # Save the fixed workflow
    output_path = Path(f"../n8n/workflows/{OUTPUT_WORKFLOW}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print("✅ V33 workflow saved:", OUTPUT_WORKFLOW)
    print()
    print("=" * 60)
    print("V33 FIX COMPLETED SUCCESSFULLY")
    print("=" * 60)
    print()
    print("📋 NEXT STEPS (MANUAL REQUIRED):")
    print()
    print("1. IMPORT WORKFLOW IN N8N:")
    print(f"   - Open http://localhost:5678")
    print(f"   - Import: {OUTPUT_WORKFLOW}")
    print()
    print("2. DEACTIVATE OLD WORKFLOWS:")
    print("   - Deactivate ALL V31, V32 versions")
    print("   - Keep only V33 active")
    print()
    print("3. TEST THE FIX:")
    print("   - Send '1' to bot")
    print("   - Should NOT see 'stateNameMapping is not defined'")
    print("   - Should see 'V33 STATE MAPPING: Initialized'")
    print()
    print("4. MONITOR LOGS:")
    print("   docker logs -f e2bot-n8n-dev 2>&1 | grep -E 'V33|ERROR'")
    print()

    return True

if __name__ == "__main__":
    success = fix_workflow()
    sys.exit(0 if success else 1)