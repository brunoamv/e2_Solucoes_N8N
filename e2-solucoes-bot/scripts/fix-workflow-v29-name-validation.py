#!/usr/bin/env python3
"""
Fix V29: Name Validation Bug Fix
Problem: Bot rejects valid names and returns to menu
Solution: Fix validation logic to maintain current stage on error
"""

import json
import sys
from pathlib import Path

def fix_state_machine_validation(function_code):
    """Fix validation logic in State Machine to prevent unwanted stage changes"""

    # Find the collect_name case
    collect_name_start = function_code.find("case 'collect_name':")
    if collect_name_start == -1:
        print("Warning: Could not find collect_name case")
        return function_code

    # Find the end of collect_name case (next break)
    collect_name_end = function_code.find("break;", collect_name_start)
    next_case = function_code.find("case", collect_name_start + 20)
    if next_case != -1 and next_case < collect_name_end:
        collect_name_end = next_case

    # Build new collect_name case with V29 fixes
    new_collect_name = """  case 'collect_name':
    console.log('=== V29 NAME VALIDATION DEBUG ===');
    console.log('Stage: collect_name');
    console.log('Message received:', message);
    console.log('Calling validator: text_min_3_chars');

    if (validators.text_min_3_chars(message)) {
      console.log('V29: Name validation PASSED');
      updateData.lead_name = message.trim();
      responseText = templates.collect_phone.text;
      nextStage = 'collect_phone';
      errorCount = 0;
    } else {
      console.log('V29: Name validation FAILED - keeping in collect_name');
      responseText = '❌ Nome muito curto.\\n\\n👤 Digite seu nome completo:';
      // V29 FIX: Keep current stage on validation error
      nextStage = 'collect_name';  // EXPLICITLY SET TO CURRENT STAGE
      errorCount++;

      if (errorCount >= MAX_ERRORS) {
        nextStage = 'handoff_comercial';
        responseText = '⚠️ Vou transferir você para um especialista.\\n\\nAguarde...';
      }
    }
    break;"""

    # Replace the collect_name case
    before = function_code[:collect_name_start]
    after = function_code[collect_name_end:]
    function_code = before + new_collect_name + after

    # Add V29 debug at the beginning of switch statement
    switch_pos = function_code.find("switch (currentStage) {")
    if switch_pos != -1:
        debug_code = """
// V29 VALIDATION FIX DEBUG
console.log('=== V29 STATE VALIDATION ===');
console.log('Current Stage:', currentStage);
console.log('Message:', message);
console.log('Message type:', typeof message);
console.log('Message length:', message.length);

// Helper to track which validator should be used
const getExpectedValidator = (stage) => {
  const validatorMap = {
    'greeting': 'none',
    'service_selection': 'number_1_to_5',
    'collect_name': 'text_min_3_chars',
    'collect_phone': 'phone_brazil',
    'collect_email': 'email_or_skip',
    'collect_city': 'city_name',
    'confirmation': 'confirmation_1_or_2'
  };
  return validatorMap[stage] || 'unknown';
};

console.log('Expected validator for stage:', getExpectedValidator(currentStage));

switch (currentStage) {"""

        function_code = function_code.replace("switch (currentStage) {", debug_code)

    # Fix other stages to maintain currentStage on error
    # Fix collect_phone
    collect_phone = function_code.find("case 'collect_phone':")
    if collect_phone != -1:
        # Add explicit nextStage maintenance
        function_code = function_code.replace(
            "responseText = templates.invalid_phone.text;",
            """responseText = templates.invalid_phone.text;
      nextStage = 'collect_phone';  // V29: Keep current stage on error"""
        )

    # Fix collect_email
    collect_email = function_code.find("case 'collect_email':")
    if collect_email != -1:
        function_code = function_code.replace(
            "responseText = templates.invalid_email.text;",
            """responseText = templates.invalid_email.text;
      nextStage = 'collect_email';  // V29: Keep current stage on error"""
        )

    # Fix collect_city
    collect_city = function_code.find("case 'collect_city':")
    if collect_city != -1:
        function_code = function_code.replace(
            "responseText = '❌ Cidade inválida.\\n\\n📍 Digite o nome da cidade:';",
            """responseText = '❌ Cidade inválida.\\n\\n📍 Digite o nome da cidade:';
      nextStage = 'collect_city';  // V29: Keep current stage on error"""
        )

    # Fix service_selection to be explicit
    service_selection = function_code.find("case 'service_selection':")
    if service_selection != -1:
        function_code = function_code.replace(
            "responseText = templates.invalid_option.text + '\\n\\n' + templates.greeting.text;",
            """responseText = templates.invalid_option.text + '\\n\\n' + templates.greeting.text;
      nextStage = 'service_selection';  // V29: Keep current stage on error"""
        )

    return function_code

def add_v29_validator_debug(function_code):
    """Add debug to validators to track calls"""

    # Find validators object
    validators_start = function_code.find("const validators = {")
    if validators_start == -1:
        print("Warning: Could not find validators object")
        return function_code

    # Update number_1_to_5 validator with V29 debug
    old_validator = """  number_1_to_5: (input) => {
    // V26: More robust validation with debug
    const cleaned = String(input)
      .trim()
      .replace(/[^\\d]/g, '')  // Remove everything except digits
      .substring(0, 1);        // Take only first digit

    console.log('V26 Validator - Input:', JSON.stringify(input), '-> Cleaned:', cleaned);"""

    new_validator = """  number_1_to_5: (input) => {
    // V29: Enhanced validation with stage tracking
    console.log('=== V29 VALIDATOR: number_1_to_5 ===');
    const cleaned = String(input)
      .trim()
      .replace(/[^\\d]/g, '')  // Remove everything except digits
      .substring(0, 1);        // Take only first digit

    console.log('V29 number validator - Input:', JSON.stringify(input), '-> Cleaned:', cleaned);"""

    function_code = function_code.replace(old_validator, new_validator)

    # Update text_min_3_chars validator
    old_text_validator = """  text_min_3_chars: (input) => {
    return input.trim().length >= 3;
  },"""

    new_text_validator = """  text_min_3_chars: (input) => {
    console.log('=== V29 VALIDATOR: text_min_3_chars ===');
    const trimmed = input.trim();
    const isValid = trimmed.length >= 3;
    console.log('V29 text validator - Input:', JSON.stringify(input), 'Length:', trimmed.length, 'Valid:', isValid);
    return isValid;
  },"""

    function_code = function_code.replace(old_text_validator, new_text_validator)

    return function_code

def main():
    # Load V28 workflow
    v28_path = Path('n8n/workflows/02_ai_agent_conversation_V28_ARRAY_RETURN_FIX.json')
    if not v28_path.exists():
        print(f"Error: {v28_path} not found")
        sys.exit(1)

    with open(v28_path, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    # Update workflow name
    workflow['name'] = 'AI Agent Conversation - V29 (Name Validation Fix)'

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

            # Apply fixes
            fixed_code = fix_state_machine_validation(original_code)
            fixed_code = add_v29_validator_debug(fixed_code)

            # Update the node
            if node.get('type') == 'n8n-nodes-base.function':
                node['parameters']['functionCode'] = fixed_code
            else:
                node['parameters']['jsCode'] = fixed_code

            state_machine_fixed = True
            print("✅ Fixed State Machine Logic validation logic")
            break

    if not state_machine_fixed:
        print("Warning: Could not find State Machine Logic node")

    # Save as V29
    v29_path = Path('n8n/workflows/02_ai_agent_conversation_V29_NAME_VALIDATION_FIX.json')
    with open(v29_path, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Created V29 workflow: {v29_path}")
    print("\n📋 V29 Improvements:")
    print("1. Fixed name validation logic to not return to menu")
    print("2. Added explicit stage maintenance on validation errors")
    print("3. Enhanced V29 debug for validator tracking")
    print("4. Prevents unwanted stage changes on any validation error")

    print("\n🔍 Debug Features:")
    print("- V29 STATE VALIDATION - Shows current stage and expected validator")
    print("- V29 NAME VALIDATION DEBUG - Tracks name validation specifically")
    print("- V29 VALIDATOR logs - Shows which validator is being called")

    print("\n🚨 Testing Instructions:")
    print("1. Import V29 workflow into n8n")
    print("2. Deactivate V28 workflow")
    print("3. Activate V29 workflow")
    print("4. Test flow:")
    print("   a. Send '1' to select service")
    print("   b. Send 'Bruno Rosa' as name")
    print("   c. Verify it accepts the name and asks for phone")
    print("5. Check logs for V29 debug messages:")
    print("   docker logs -f e2bot-n8n-dev | grep V29")
    print("\n6. Expected behavior:")
    print("   - Names with 3+ characters should be accepted")
    print("   - Invalid names should keep user in collect_name stage")
    print("   - No unwanted returns to service_selection menu")

if __name__ == '__main__':
    main()