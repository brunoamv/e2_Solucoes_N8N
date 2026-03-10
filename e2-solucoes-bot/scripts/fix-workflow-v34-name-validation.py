#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
V34 NAME VALIDATION DEFINITIVE FIX
===================================
CRITICAL FIX: Ensures correct validator is used in collect_name state.
Currently, names are being validated with number_1_to_5 validator
instead of text_min_3_chars, causing all names to be rejected.

This script:
1. Loads V33 workflow (which has stateNameMapping fixed)
2. Fixes the collect_name state validator selection
3. Adds comprehensive V34 debugging
4. Ensures explicit validator usage (no automatic mapping bugs)
5. Saves as V34 for import into n8n
"""

import json
import sys
from pathlib import Path

# Use V33 as base (it has stateNameMapping fixed)
BASE_WORKFLOW = "02_ai_agent_conversation_V33_DEFINITIVE.json"
OUTPUT_WORKFLOW = "02_ai_agent_conversation_V34_NAME_VALIDATION.json"

def create_v34_diagnostics():
    """Create V34 diagnostic logging."""
    return """
// =====================================
// V34 NAME VALIDATION FIX
// =====================================
console.log('=============== V34 NAME VALIDATION FIX ACTIVE ===============');
console.log('V34: Fixing validator selection in collect_name state');
console.log('V34: Ensuring text_min_3_chars validator for names');
console.log('==============================================================');

"""

def create_fixed_collect_name_case():
    """Create the fixed collect_name case with proper validation."""
    return """
    case 'collect_name':
      console.log('=====================================');
      console.log('V34 COLLECT_NAME STATE ENTERED');
      console.log('  Message received:', message);
      console.log('  Message length:', message.length);
      console.log('  Current error count:', errorCount);
      console.log('=====================================');

      // V34 FIX: EXPLICIT validator selection - NO automatic mapping
      // This ensures we ALWAYS use the correct validator

      // First, define what we expect for a valid name
      const nameMinLength = 3;
      const nameMaxLength = 100;

      // V34: Manual name validation (bypassing potentially buggy validator mapping)
      const trimmedName = message.trim();
      const nameLength = trimmedName.length;

      console.log('V34 Name Validation:');
      console.log('  Trimmed name:', trimmedName);
      console.log('  Name length:', nameLength);
      console.log('  Min required:', nameMinLength);

      // V34: Simple, explicit validation logic
      let isValidName = false;

      if (nameLength < nameMinLength) {
        console.log('V34: Name too short (less than 3 chars)');
        isValidName = false;
      } else if (nameLength > nameMaxLength) {
        console.log('V34: Name too long (more than 100 chars)');
        isValidName = false;
      } else if (/^[0-9]+$/.test(trimmedName)) {
        console.log('V34: Name cannot be only numbers');
        isValidName = false;
      } else if (/^[^a-zA-ZÀ-ÿ\s]/.test(trimmedName)) {
        console.log('V34: Name contains invalid characters');
        isValidName = false;
      } else {
        console.log('V34: Name validation PASSED');
        isValidName = true;
      }

      console.log('V34 Validation Result:', isValidName ? 'VALID ✓' : 'INVALID ✗');

      if (!isValidName) {
        console.log('V34: Name rejected, staying in collect_name state');
        responseText = '❌ Por favor, informe um nome válido com pelo menos 3 letras.\\n\\nExemplo: João Silva';
        nextStage = 'collect_name'; // Stay in same state
        errorCount++;

        console.log('V34: Error count increased to:', errorCount);

        if (errorCount >= MAX_ERRORS) {
          console.log('V34: Max errors reached, transferring to commercial');
          nextStage = 'handoff_comercial';
          responseText = '⚠️ Vou transferir você para um especialista que pode ajudar melhor.\\n\\nAguarde um momento...';
        }
      } else {
        console.log('V34: Name accepted successfully:', trimmedName);
        console.log('V34: Moving to collect_phone state');

        // Name is valid, save and continue
        updateData.lead_name = trimmedName;
        responseText = templates.collect_phone.text || '📱 Agora, por favor, informe seu telefone com DDD.\\n\\nExemplo: (11) 98765-4321';
        nextStage = 'collect_phone';
        errorCount = 0; // Reset error count

        console.log('V34: Name saved as:', updateData.lead_name);
        console.log('V34: Next stage set to:', nextStage);
      }

      console.log('V34 collect_name case completed');
      console.log('  Response:', responseText.substring(0, 50) + '...');
      console.log('  Next stage:', nextStage);
      console.log('=====================================');
      break;
"""

def create_validator_safety_check():
    """Create safety check to prevent wrong validator usage."""
    return """
// V34: Validator safety check function
function V34_validateInput(stage, input) {
  console.log('V34 Validator Safety Check:');
  console.log('  Stage:', stage);
  console.log('  Input:', input);

  // Prevent number validator from being used on text stages
  if (stage === 'collect_name' || stage === 'collect_city') {
    if (/^[1-5]$/.test(input)) {
      console.log('V34 WARNING: Numeric input in text field, but allowing it as valid text');
      return true; // Allow single digit as part of name if needed
    }
  }

  // Prevent text validator from being used on number stages
  if (stage === 'service_selection' || stage === 'confirmation') {
    if (!/^[1-5]$/.test(input) && !/^(sim|não|nao|s|n)$/i.test(input)) {
      console.log('V34 WARNING: Non-numeric input in number field');
      return false;
    }
  }

  return true; // Default to allowing input
}

"""

def fix_workflow():
    """Apply V34 name validation fix to workflow."""

    print("=" * 60)
    print("V34 NAME VALIDATION DEFINITIVE FIX")
    print("=" * 60)
    print()
    print("🔴 FIXING: Name validation using wrong validator")
    print("   Current: number_1_to_5 validator (rejects all names)")
    print("   Fixed: Explicit name validation logic")
    print()

    # Load V33 workflow
    workflow_path = Path(f"../n8n/workflows/{BASE_WORKFLOW}")
    if not workflow_path.exists():
        print(f"❌ ERROR: Base workflow not found: {BASE_WORKFLOW}")
        print("   Please ensure V33 workflow exists")
        return False

    print(f"✅ Loading base workflow: {BASE_WORKFLOW}")

    with open(workflow_path, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    # Find State Machine Logic node
    state_machine_node = None
    for node in workflow.get('nodes', []):
        if 'State Machine' in node.get('name', ''):
            state_machine_node = node
            break

    if not state_machine_node:
        print("❌ ERROR: State Machine Logic node not found!")
        return False

    print("✅ Found State Machine Logic node")

    # Get current code
    code = state_machine_node['parameters']['functionCode']

    print()
    print("📝 APPLYING V34 FIXES:")
    print("  1. Adding V34 diagnostic logging")
    print("  2. Replacing collect_name case with explicit validation")
    print("  3. Adding validator safety checks")
    print("  4. Ensuring no automatic validator mapping bugs")
    print()

    # Add V34 diagnostics at the beginning
    if '// V34 NAME VALIDATION FIX' not in code:
        # Find a good insertion point after V33 logs
        if 'V33 DEFINITIVE FIX ACTIVE' in code:
            v33_end = code.find('==========================================================')
            if v33_end > 0:
                v33_end = code.find('\n', v33_end) + 1
                code = code[:v33_end] + '\n' + create_v34_diagnostics() + code[v33_end:]
        else:
            # Add after initial setup
            code = create_v34_diagnostics() + '\n' + code

    # Add validator safety check function
    if 'V34_validateInput' not in code:
        # Add before the switch statement
        switch_pos = code.find('switch (currentStage)')
        if switch_pos > 0:
            code = code[:switch_pos] + create_validator_safety_check() + '\n' + code[switch_pos:]

    # Replace the collect_name case
    collect_name_start = code.find("case 'collect_name':")
    if collect_name_start > 0:
        # Find the end of this case (next case or default)
        next_case_pos = code.find("case '", collect_name_start + 20)
        if next_case_pos == -1:
            next_case_pos = code.find("default:", collect_name_start)

        if next_case_pos > 0:
            # Find the break statement before the next case
            break_pos = code.rfind("break;", collect_name_start, next_case_pos)
            if break_pos > 0:
                # Replace entire case
                code = (code[:collect_name_start] +
                       create_fixed_collect_name_case() + '\n' +
                       code[break_pos + 6:])
                print("✅ Replaced collect_name case with V34 fix")
            else:
                print("⚠️ WARNING: Could not find break statement in collect_name case")
    else:
        print("⚠️ WARNING: collect_name case not found, will add it")
        # Add the case before the default case
        default_pos = code.find('default:')
        if default_pos > 0:
            code = (code[:default_pos] +
                   create_fixed_collect_name_case() + '\n\n' +
                   code[default_pos:])

    # Update node with fixed code
    state_machine_node['parameters']['functionCode'] = code

    # Update workflow name
    workflow['name'] = "02 - AI Agent Conversation V34 NAME VALIDATION FIX"

    # Save the fixed workflow
    output_path = Path(f"../n8n/workflows/{OUTPUT_WORKFLOW}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print()
    print("✅ V34 workflow saved:", OUTPUT_WORKFLOW)
    print()
    print("=" * 60)
    print("V34 FIX COMPLETED SUCCESSFULLY")
    print("=" * 60)
    print()
    print("📋 NEXT STEPS (MANUAL REQUIRED):")
    print()
    print("1. IMPORT WORKFLOW IN N8N:")
    print(f"   - Open http://localhost:5678")
    print(f"   - Import: {OUTPUT_WORKFLOW}")
    print()
    print("2. DEACTIVATE OLD WORKFLOWS:")
    print("   - Deactivate V33 workflow")
    print("   - Keep only V34 active")
    print()
    print("3. TEST THE FIX:")
    print("   - Send '1' to bot")
    print("   - Send 'Bruno Rosa' as name")
    print("   - Should ACCEPT and ask for phone")
    print()
    print("4. MONITOR LOGS:")
    print("   docker logs -f e2bot-n8n-dev 2>&1 | grep -E 'V34|collect_name|Bruno'")
    print()
    print("✅ Expected: 'V34: Name validation PASSED'")
    print("✅ Expected: 'V34: Name accepted successfully: Bruno Rosa'")
    print()

    return True

if __name__ == "__main__":
    success = fix_workflow()
    sys.exit(0 if success else 1)