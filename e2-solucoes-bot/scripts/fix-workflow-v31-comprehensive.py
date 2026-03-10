#!/usr/bin/env python3
"""
Fix V31: Comprehensive solution for stage transition and validator isolation bug
Problem: Wrong validator called + stage transition failure
Solution: Complete diagnostic + forced persistence + absolute isolation
"""

import json
import sys
from pathlib import Path

def add_comprehensive_diagnostics(function_code):
    """Add super verbose diagnostic logging at every critical point"""

    # Find the beginning of the function
    func_start = function_code.find("// Get phone number from different sources")
    if func_start == -1:
        func_start = function_code.find("const phone_number")

    if func_start != -1:
        diagnostic_code = """
// ========== V31 COMPREHENSIVE DIAGNOSTICS ==========
console.log('========== V31 EXECUTION START ==========');
console.log('Timestamp:', new Date().toISOString());
console.log('Execution ID:', $execution?.id || 'N/A');
console.log('Workflow Version: V31 COMPREHENSIVE FIX');
console.log('Node: State Machine Logic');

// V31: Log ALL incoming data
console.log('--- V31 INCOMING DATA ---');
console.log('phone_number:', phone_number);
console.log('message:', message);
console.log('currentStage from DB:', currentStage);
console.log('previousStage:', previousStage);
console.log('errorCount:', errorCount);
console.log('collected_data type:', typeof collectedData);
console.log('collected_data:', JSON.stringify(collectedData, null, 2));

// V31: Validate stage value
console.log('--- V31 STAGE VALIDATION ---');
console.log('Type of currentStage:', typeof currentStage);
console.log('currentStage length:', currentStage?.length);
console.log('currentStage exact value:', JSON.stringify(currentStage));
console.log('Is collect_name?:', currentStage === 'collect_name');
console.log('Is service_selection?:', currentStage === 'service_selection');

"""
        # Insert diagnostics after phone number extraction
        before = function_code[:func_start]
        after = function_code[func_start:]
        function_code = before + diagnostic_code + after

    return function_code

def add_validator_mapping_function(function_code):
    """Add explicit validator mapping function for absolute isolation"""

    # Find validators object
    validators_pos = function_code.find("const validators = {")
    if validators_pos == -1:
        print("Warning: Could not find validators object")
        return function_code

    # Find the end of validators object
    validators_end = function_code.find("};", validators_pos) + 2

    # Add mapping function after validators
    mapping_function = """

// V31: EXPLICIT VALIDATOR MAPPING FUNCTION
function getValidatorForStage(stage) {
  const validatorMap = {
    'greeting': null,
    'service_selection': 'number_1_to_5',
    'collect_name': 'text_min_3_chars',
    'collect_phone': 'phone_brazil',
    'collect_email': 'email_or_skip',
    'collect_city': 'city_name',
    'confirmation': 'confirmation_1_or_2',
    'scheduling': null,
    'handoff_comercial': null,
    'completed': null
  };

  console.log(`V31 VALIDATOR MAPPING: Stage "${stage}" → Validator "${validatorMap[stage]}"`);
  return validatorMap[stage];
}

// V31: Force update flag for persistence
let forceUpdateRequired = false;
let stageTransitionOccurred = false;

"""

    before = function_code[:validators_end]
    after = function_code[validators_end:]
    function_code = before + mapping_function + after

    return function_code

def fix_service_selection_stage(function_code):
    """Fix service_selection to ensure proper stage transition"""

    service_start = function_code.find("case 'service_selection':")
    if service_start == -1:
        print("Warning: Could not find service_selection case")
        return function_code

    # Find the end of service_selection case
    next_case = function_code.find("case 'collect_name':", service_start)
    if next_case == -1:
        next_case = function_code.find("case", service_start + 30)

    new_service_selection = """  case 'service_selection':
    console.log('=== V31 STAGE: service_selection ===');
    console.log('V31: Message received:', message);

    // V31: Use explicit validator
    const serviceValidatorName = getValidatorForStage('service_selection');
    console.log('V31: Using validator:', serviceValidatorName);

    if (serviceValidatorName === 'number_1_to_5' && validators.number_1_to_5(message)) {
      console.log('V31: Service number validated successfully');

      const service = serviceMapping[message];
      updateData.service_type = service.id;
      updateData.service_name = service.name;
      updateData.service_emoji = service.emoji;

      responseText = fillTemplate(templates.service_selected.template, {
        emoji: service.emoji,
        service_name: service.name,
        description: service.description
      });

      // V31: CRITICAL - Explicit stage transition
      nextStage = 'collect_name';
      console.log('V31 CRITICAL: Setting nextStage to:', nextStage);
      console.log('V31: Stage transition will occur: service_selection → collect_name');

      // V31: Force persistence
      forceUpdateRequired = true;
      stageTransitionOccurred = true;

      errorCount = 0;
    } else {
      console.log('V31: Invalid service selection');
      responseText = templates.invalid_option.text + '\\n\\n' + templates.greeting.text;
      nextStage = 'service_selection';
      errorCount++;

      if (errorCount >= MAX_ERRORS) {
        nextStage = 'handoff_comercial';
        responseText = '⚠️ Percebi dificuldades. Vou transferir você para um especialista.\\n\\nAguarde...';
        forceUpdateRequired = true;
      }
    }
    break;

  """

    # Replace the case
    before = function_code[:service_start]
    after = function_code[next_case:]
    function_code = before + new_service_selection + after

    return function_code

def fix_collect_name_stage(function_code):
    """Fix collect_name with absolute validator isolation and logging"""

    collect_name_start = function_code.find("case 'collect_name':")
    if collect_name_start == -1:
        print("Warning: Could not find collect_name case")
        return function_code

    # Find next case
    collect_phone_start = function_code.find("case 'collect_phone':", collect_name_start)
    if collect_phone_start == -1:
        collect_phone_start = function_code.find("default:", collect_name_start)

    new_collect_name = """  case 'collect_name':
    console.log('=== V31 STAGE EXECUTION: collect_name ===');
    console.log('V31 CRITICAL: This log MUST appear when processing names!');
    console.log('V31: Input message:', message);
    console.log('V31: Message type:', typeof message);
    console.log('V31: Message length:', message?.length);

    // V31: Get correct validator
    const nameValidatorName = getValidatorForStage('collect_name');
    console.log('V31: Validator for collect_name:', nameValidatorName);

    if (nameValidatorName !== 'text_min_3_chars') {
      console.error('V31 CRITICAL ERROR: Wrong validator mapped for collect_name!');
      console.error('Expected: text_min_3_chars, Got:', nameValidatorName);
    }

    // V31: ONLY use text validator for names
    const nameIsValid = validators.text_min_3_chars(message);
    console.log('V31: Name validation result:', nameIsValid);
    console.log('V31: Validator used: text_min_3_chars ONLY');

    if (nameIsValid) {
      console.log('V31 SUCCESS: Name accepted, transitioning to collect_phone');
      updateData.lead_name = message.trim();
      responseText = templates.collect_phone.text;

      // V31: Explicit transition
      nextStage = 'collect_phone';
      console.log('V31 CRITICAL: Setting nextStage to:', nextStage);
      console.log('V31: Stage transition will occur: collect_name → collect_phone');

      // V31: Force update
      forceUpdateRequired = true;
      stageTransitionOccurred = true;
      errorCount = 0;
    } else {
      console.log('V31: Name rejected - too short');
      responseText = '❌ Nome muito curto.\\n\\n👤 Digite seu nome completo:';

      // V31: Explicitly stay in current stage
      nextStage = 'collect_name';
      console.log('V31: Staying in collect_name stage');
      errorCount++;

      if (errorCount >= MAX_ERRORS) {
        nextStage = 'handoff_comercial';
        responseText = '⚠️ Vou transferir você para um especialista.\\n\\nAguarde...';
        forceUpdateRequired = true;
      }
    }
    break;

  """

    # Replace the case
    before = function_code[:collect_name_start]
    after = function_code[collect_phone_start:]
    function_code = before + new_collect_name + after

    return function_code

def add_switch_validation(function_code):
    """Add validation before and after switch statement"""

    # Find switch statement
    switch_pos = function_code.find("switch (currentStage) {")
    if switch_pos == -1:
        print("Warning: Could not find switch statement")
        return function_code

    # Add pre-switch validation
    pre_switch = """
// V31: PRE-SWITCH VALIDATION
console.log('--- V31 BEFORE SWITCH ---');
console.log('About to process stage:', currentStage);
console.log('Stage is exactly "collect_name"?:', currentStage === 'collect_name');
console.log('Stage is exactly "service_selection"?:', currentStage === 'service_selection');

// V31: Ensure stage is trimmed and clean
const cleanStage = String(currentStage).trim();
console.log('V31: Using clean stage:', cleanStage);

switch (cleanStage) {"""

    function_code = function_code.replace("switch (currentStage) {", pre_switch)

    # Find end of switch
    switch_end = function_code.find("}", switch_pos)
    # Find the actual end by counting braces
    brace_count = 1
    pos = function_code.find("{", switch_pos) + 1
    while brace_count > 0 and pos < len(function_code):
        if function_code[pos] == '{':
            brace_count += 1
        elif function_code[pos] == '}':
            brace_count -= 1
        pos += 1

    switch_end = pos

    # Add post-switch validation
    post_switch = """

// V31: POST-SWITCH VALIDATION
console.log('--- V31 AFTER SWITCH ---');
console.log('Final nextStage:', nextStage);
console.log('Force update required:', forceUpdateRequired);
console.log('Stage transition occurred:', stageTransitionOccurred);
console.log('Update data:', JSON.stringify(updateData, null, 2));

// V31: Ensure critical updates are persisted
if (stageTransitionOccurred || forceUpdateRequired) {
  console.log('V31 CRITICAL: Database update MUST occur now!');
  updateData.conversation_stage = nextStage;
  updateData.force_update = true;
}
"""

    before = function_code[:switch_end]
    after = function_code[switch_end:]
    function_code = before + post_switch + after

    return function_code

def update_validators_with_v31_logging(function_code):
    """Update validators with V31 specific logging"""

    # Update text_min_3_chars validator
    old_text = """  text_min_3_chars: (input) => {
    console.log('=== V30 VALIDATOR CALLED: text_min_3_chars ===');
    console.log('V30: This should ONLY be called in collect_name stage');
    const trimmed = input.trim();
    const isValid = trimmed.length >= 3;
    console.log('V30 text validator - Input:', JSON.stringify(input), 'Length:', trimmed.length, 'Valid:', isValid);
    return isValid;
  },"""

    new_text = """  text_min_3_chars: (input) => {
    console.log('=== V31 VALIDATOR EXECUTED: text_min_3_chars ===');
    console.log('V31 CHECK: This should ONLY run for collect_name stage!');
    console.log('V31: Input received:', JSON.stringify(input));
    const trimmed = String(input).trim();
    const isValid = trimmed.length >= 3;
    console.log('V31: Trimmed:', trimmed);
    console.log('V31: Length:', trimmed.length);
    console.log('V31: Valid:', isValid);
    console.log('V31: Returning:', isValid);
    return isValid;
  },"""

    function_code = function_code.replace(old_text, new_text)

    # Update number_1_to_5 validator
    old_number = 'console.log(\'=== V30 VALIDATOR CALLED: number_1_to_5 ===\');'
    new_number = """console.log('=== V31 VALIDATOR EXECUTED: number_1_to_5 ===');
    console.log('V31 CHECK: This should ONLY run for service_selection stage!');"""

    function_code = function_code.replace(old_number, new_number)

    return function_code

def add_final_return_validation(function_code):
    """Add validation to the final return statement"""

    # Find the return statement
    return_pos = function_code.rfind("return [{")
    if return_pos == -1:
        print("Warning: Could not find return statement")
        return function_code

    # Add validation before return
    validation = """
// V31: FINAL VALIDATION BEFORE RETURN
console.log('========== V31 FINAL VALIDATION ==========');
console.log('Will return nextStage:', nextStage);
console.log('Will return responseText:', responseText?.substring(0, 100) + '...');
console.log('Will return updateData:', JSON.stringify(updateData, null, 2));
console.log('Force update flag:', forceUpdateRequired);

// V31: Ensure we always return valid data
if (!nextStage) {
  console.error('V31 ERROR: nextStage is undefined! Setting to currentStage');
  nextStage = currentStage;
}

"""

    before = function_code[:return_pos]
    after = function_code[return_pos:]
    function_code = before + validation + after

    return function_code

def main():
    # Load V30 workflow
    v30_path = Path('n8n/workflows/02_ai_agent_conversation_V30_VALIDATOR_ISOLATION.json')
    if not v30_path.exists():
        # Try V29 as fallback
        v30_path = Path('n8n/workflows/02_ai_agent_conversation_V29_NAME_VALIDATION_FIX.json')
        if not v30_path.exists():
            print(f"Error: Could not find V30 or V29 workflow")
            sys.exit(1)

    print(f"Loading workflow from: {v30_path}")

    with open(v30_path, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    # Update workflow name
    workflow['name'] = 'AI Agent Conversation - V31 (Comprehensive Fix)'

    # Process State Machine Logic node
    state_machine_fixed = False
    for node in workflow['nodes']:
        if node.get('name') == 'State Machine Logic':
            print(f"Found State Machine Logic node: {node['id']}")

            # Get the function code
            if node.get('type') == 'n8n-nodes-base.function':
                original_code = node['parameters']['functionCode']
            else:
                original_code = node['parameters']['jsCode']

            # Apply ALL fixes in sequence
            print("Applying comprehensive diagnostics...")
            fixed_code = add_comprehensive_diagnostics(original_code)

            print("Adding validator mapping function...")
            fixed_code = add_validator_mapping_function(fixed_code)

            print("Fixing service_selection stage...")
            fixed_code = fix_service_selection_stage(fixed_code)

            print("Fixing collect_name stage...")
            fixed_code = fix_collect_name_stage(fixed_code)

            print("Adding switch validation...")
            fixed_code = add_switch_validation(fixed_code)

            print("Updating validators with V31 logging...")
            fixed_code = update_validators_with_v31_logging(fixed_code)

            print("Adding final return validation...")
            fixed_code = add_final_return_validation(fixed_code)

            # Update the node
            if node.get('type') == 'n8n-nodes-base.function':
                node['parameters']['functionCode'] = fixed_code
            else:
                node['parameters']['jsCode'] = fixed_code

            state_machine_fixed = True
            print("✅ Applied all V31 comprehensive fixes")
            break

    if not state_machine_fixed:
        print("Error: Could not find State Machine Logic node")
        sys.exit(1)

    # Save as V31
    v31_path = Path('n8n/workflows/02_ai_agent_conversation_V31_COMPREHENSIVE_FIX.json')
    with open(v31_path, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Created V31 workflow: {v31_path}")

    print("\n📋 V31 Comprehensive Improvements:")
    print("1. Super verbose diagnostics at EVERY critical point")
    print("2. Explicit validator mapping function for absolute isolation")
    print("3. Fixed service_selection with forced stage transition")
    print("4. Fixed collect_name with complete isolation and logging")
    print("5. Pre/post switch validation for debugging")
    print("6. Force update flags for database persistence")
    print("7. Final validation before return")

    print("\n🔍 V31 Debug Features:")
    print("- V31 EXECUTION START - Shows workflow initialization")
    print("- V31 STAGE VALIDATION - Validates current stage value")
    print("- V31 VALIDATOR MAPPING - Shows which validator should be used")
    print("- V31 STAGE EXECUTION - Confirms which case is running")
    print("- V31 CRITICAL - Highlights important state changes")
    print("- V31 FINAL VALIDATION - Verifies return data")

    print("\n🚨 Critical Testing Steps:")
    print("1. Import V31 workflow into n8n")
    print("2. IMPORTANT: Deactivate ALL other versions (V27-V30)")
    print("3. Activate ONLY V31 workflow")
    print("4. Clear any workflow cache/executions")
    print("5. Test the complete flow:")
    print("   a. Send '1' for service selection")
    print("   b. Send 'Bruno Rosa' for name")
    print("   c. VERIFY: Should accept name and ask for phone")

    print("\n📊 Monitor with:")
    print("docker logs -f e2bot-n8n-dev 2>&1 | grep -E 'V31|ERROR|CRITICAL'")

    print("\n✅ Expected log sequence:")
    print("1. V31 STAGE: service_selection")
    print("2. V31 CRITICAL: Setting nextStage to: collect_name")
    print("3. V31 STAGE EXECUTION: collect_name")
    print("4. V31 VALIDATOR EXECUTED: text_min_3_chars")
    print("5. V31 SUCCESS: Name accepted")
    print("6. V31 CRITICAL: Setting nextStage to: collect_phone")

if __name__ == '__main__':
    main()