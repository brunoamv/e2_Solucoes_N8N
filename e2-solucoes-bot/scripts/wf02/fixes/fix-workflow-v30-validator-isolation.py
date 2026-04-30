#!/usr/bin/env python3
"""
Fix V30: Validator Isolation and Flow Correction
Problem: Wrong validator being called for stages (number_1_to_5 called in collect_name)
Solution: Proper case isolation and explicit validator mapping
"""

import json
import sys
from pathlib import Path

def fix_validator_isolation(function_code):
    """Fix validator isolation in State Machine Logic"""

    # First, remove any duplicate break statements
    function_code = function_code.replace("break;\nbreak;", "break;")
    function_code = function_code.replace("break;break;", "break;")

    # Fix the entire collect_name case
    collect_name_start = function_code.find("case 'collect_name':")
    if collect_name_start == -1:
        print("Warning: Could not find collect_name case")
        return function_code

    # Find the next case or default
    collect_phone_start = function_code.find("case 'collect_phone':", collect_name_start)
    if collect_phone_start == -1:
        collect_phone_start = function_code.find("default:", collect_name_start)

    if collect_phone_start == -1:
        print("Warning: Could not find next case after collect_name")
        return function_code

    # Build the new collect_name case with V30 fixes
    new_collect_name = """  case 'collect_name':
    // V30: Isolated name validation - NO OTHER VALIDATOR WILL BE CALLED
    console.log('=== V30 STAGE: collect_name ===');
    console.log('Input message:', message);
    console.log('Message type:', typeof message);
    console.log('Message length:', message.length);
    console.log('Calling ONLY text_min_3_chars validator');

    // V30: Direct validator call - isolated from other validators
    const nameValid = validators.text_min_3_chars(message);
    console.log('V30 Name validation result:', nameValid);

    if (nameValid) {
      console.log('V30: Name accepted, moving to collect_phone');
      updateData.lead_name = message.trim();
      responseText = templates.collect_phone.text;
      nextStage = 'collect_phone';
      errorCount = 0;
    } else {
      console.log('V30: Name rejected, STAYING in collect_name');
      responseText = '❌ Nome muito curto.\\n\\n👤 Digite seu nome completo:';
      nextStage = 'collect_name'; // V30: Explicit - stay in current stage
      errorCount++;

      if (errorCount >= MAX_ERRORS) {
        nextStage = 'handoff_comercial';
        responseText = '⚠️ Vou transferir você para um especialista.\\n\\nAguarde...';
      }
    }
    break; // V30: ONLY ONE BREAK STATEMENT

  """

    # Replace the entire collect_name case
    before = function_code[:collect_name_start]
    after = function_code[collect_phone_start:]
    function_code = before + new_collect_name + after

    return function_code

def fix_service_selection_isolation(function_code):
    """Fix service_selection to ensure it only validates numbers"""

    service_selection_start = function_code.find("case 'service_selection':")
    if service_selection_start == -1:
        print("Warning: Could not find service_selection case")
        return function_code

    # Find the next case
    next_case = function_code.find("case 'collect_name':", service_selection_start)
    if next_case == -1:
        next_case = function_code.find("case", service_selection_start + 30)

    # Build new service_selection with V30 isolation
    new_service_selection = """  case 'service_selection':
    // V30: Isolated service selection - ONLY number validation
    console.log('=== V30 STAGE: service_selection ===');
    console.log('Input message:', message);
    console.log('Calling ONLY number_1_to_5 validator');

    const serviceValid = validators.number_1_to_5(message);
    console.log('V30 Service validation result:', serviceValid);

    if (serviceValid) {
      console.log('V30: Service selected, moving to collect_name');
      const service = serviceMapping[message];
      updateData.service_type = service.id;
      updateData.service_name = service.name;
      updateData.service_emoji = service.emoji;

      responseText = fillTemplate(templates.service_selected.template, {
        emoji: service.emoji,
        service_name: service.name,
        description: service.description
      });

      nextStage = 'collect_name';
      errorCount = 0;
    } else {
      console.log('V30: Invalid service, STAYING in service_selection');
      responseText = templates.invalid_option.text + '\\n\\n' + templates.greeting.text;
      nextStage = 'service_selection'; // V30: Explicit - stay in current stage
      errorCount++;

      if (errorCount >= MAX_ERRORS) {
        nextStage = 'handoff_comercial';
        responseText = '⚠️ Percebi dificuldades. Vou transferir você para um especialista.\\n\\nAguarde um momento...';
      }
    }
    break; // V30: ONLY ONE BREAK STATEMENT

  """

    # Replace the service_selection case
    before = function_code[:service_selection_start]
    after = function_code[next_case:]
    function_code = before + new_service_selection + after

    return function_code

def add_stage_validator_mapping(function_code):
    """Add explicit stage-to-validator mapping at the beginning of the switch"""

    # Find the switch statement
    switch_pos = function_code.find("switch (currentStage) {")
    if switch_pos == -1:
        print("Warning: Could not find switch statement")
        return function_code

    # Add mapping before switch
    pre_switch_pos = function_code.rfind("\n", 0, switch_pos)

    mapping_code = """
// V30: EXPLICIT STAGE-TO-VALIDATOR MAPPING
const stageValidatorMap = {
  'greeting': 'none',
  'service_selection': 'number_1_to_5',
  'collect_name': 'text_min_3_chars',
  'collect_phone': 'phone_brazil',
  'collect_email': 'email_or_skip',
  'collect_city': 'city_name',
  'confirmation': 'confirmation_1_or_2',
  'handoff_comercial': 'none',
  'completed': 'none'
};

console.log('=== V30 VALIDATOR ISOLATION CHECK ===');
console.log('Current Stage:', currentStage);
console.log('Expected Validator:', stageValidatorMap[currentStage]);
console.log('Message to validate:', message);
console.log('================================');

"""

    # Insert the mapping code
    before = function_code[:pre_switch_pos]
    after = function_code[pre_switch_pos:]
    function_code = before + mapping_code + after

    return function_code

def update_validators_with_v30_debug(function_code):
    """Update validators to include V30 debug"""

    # Update text_min_3_chars validator
    old_text_validator = """  text_min_3_chars: (input) => {
    console.log('=== V29 VALIDATOR: text_min_3_chars ===');
    const trimmed = input.trim();
    const isValid = trimmed.length >= 3;
    console.log('V29 text validator - Input:', JSON.stringify(input), 'Length:', trimmed.length, 'Valid:', isValid);
    return isValid;
  },"""

    new_text_validator = """  text_min_3_chars: (input) => {
    console.log('=== V30 VALIDATOR CALLED: text_min_3_chars ===');
    console.log('V30: This should ONLY be called in collect_name stage');
    const trimmed = input.trim();
    const isValid = trimmed.length >= 3;
    console.log('V30 text validator - Input:', JSON.stringify(input), 'Length:', trimmed.length, 'Valid:', isValid);
    return isValid;
  },"""

    function_code = function_code.replace(old_text_validator, new_text_validator)

    # Update number_1_to_5 validator
    old_number_validator_pattern = "console.log('=== V29 VALIDATOR: number_1_to_5 ===');"
    new_number_validator_pattern = """console.log('=== V30 VALIDATOR CALLED: number_1_to_5 ===');
    console.log('V30: This should ONLY be called in service_selection stage');"""

    function_code = function_code.replace(old_number_validator_pattern, new_number_validator_pattern)

    return function_code

def main():
    # Load V29 workflow
    v29_path = Path('n8n/workflows/02_ai_agent_conversation_V29_NAME_VALIDATION_FIX.json')
    if not v29_path.exists():
        print(f"Error: {v29_path} not found")
        sys.exit(1)

    with open(v29_path, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    # Update workflow name
    workflow['name'] = 'AI Agent Conversation - V30 (Validator Isolation Fix)'

    # Fix State Machine Logic
    state_machine_fixed = False
    for node in workflow['nodes']:
        if node.get('name') == 'State Machine Logic':
            print(f"Found State Machine Logic node: {node['id']}")

            # Get the function code
            if node.get('type') == 'n8n-nodes-base.function':
                original_code = node['parameters']['functionCode']
            else:
                original_code = node['parameters']['jsCode']

            # Apply all fixes
            fixed_code = fix_service_selection_isolation(original_code)
            fixed_code = fix_validator_isolation(fixed_code)
            fixed_code = add_stage_validator_mapping(fixed_code)
            fixed_code = update_validators_with_v30_debug(fixed_code)

            # Update the node
            if node.get('type') == 'n8n-nodes-base.function':
                node['parameters']['functionCode'] = fixed_code
            else:
                node['parameters']['jsCode'] = fixed_code

            state_machine_fixed = True
            print("✅ Fixed State Machine Logic with V30 validator isolation")
            break

    if not state_machine_fixed:
        print("Warning: Could not find State Machine Logic node")

    # Save as V30
    v30_path = Path('n8n/workflows/02_ai_agent_conversation_V30_VALIDATOR_ISOLATION.json')
    with open(v30_path, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Created V30 workflow: {v30_path}")
    print("\n📋 V30 Critical Improvements:")
    print("1. Fixed validator isolation - each stage uses ONLY its validator")
    print("2. Removed duplicate break statements")
    print("3. Added explicit stage-to-validator mapping")
    print("4. Enhanced V30 debug to track validator calls")
    print("5. Ensures collect_name uses text_min_3_chars, not number_1_to_5")

    print("\n🔍 V30 Debug Features:")
    print("- V30 VALIDATOR ISOLATION CHECK - Shows expected validator per stage")
    print("- V30 STAGE logs - Shows which stage is processing")
    print("- V30 VALIDATOR CALLED logs - Confirms correct validator usage")

    print("\n🚨 Testing Instructions:")
    print("1. Import V30 workflow into n8n")
    print("2. Deactivate V29 workflow")
    print("3. Activate V30 workflow")
    print("4. Test critical flow:")
    print("   a. Send '1' to select service")
    print("   b. Send 'Bruno Rosa' as name")
    print("   c. VERIFY: Name is accepted (not rejected)")
    print("   d. Continue with phone number")
    print("\n5. Monitor V30 logs:")
    print("   docker logs -f e2bot-n8n-dev 2>&1 | grep V30")
    print("\n6. Expected log sequence:")
    print("   - V30 STAGE: service_selection → VALIDATOR CALLED: number_1_to_5")
    print("   - V30 STAGE: collect_name → VALIDATOR CALLED: text_min_3_chars")
    print("   - NO cross-validator calls!")

if __name__ == '__main__':
    main()