#!/usr/bin/env python3
"""
Fix V26: Menu Validation Issue
Problem: Message "1" not being recognized as valid in service_selection state
Solution: Fix message extraction, add comprehensive debug logging, and robust validation
"""

import json
import sys
from pathlib import Path

def fix_prepare_phone_formats(js_code):
    """Fix the Prepare Phone Formats node to ensure all message fields are present"""

    # Find the return statement section
    return_start = js_code.find("return {")
    if return_start == -1:
        print("Warning: Could not find return statement in Prepare Phone Formats")
        return js_code

    # Build the new return with comprehensive message field handling
    new_return = """return {
    ...inputData, // Pass through all original data
    phone_with_code: phone_with_code,      // e.g., "556181755748"
    phone_without_code: phone_without_code, // e.g., "6181755748"
    // Keep original for compatibility
    phone_number: phone_with_code,

    // CRITICAL V26 FIX: Ensure ALL possible message field names are present
    // This handles different webhook formats from Evolution API
    message: inputData.message || inputData.body || inputData.text || inputData.content || '',
    content: inputData.content || inputData.message || inputData.body || inputData.text || '',
    body: inputData.body || inputData.message || inputData.text || inputData.content || '',
    text: inputData.text || inputData.message || inputData.body || inputData.content || '',

    // Also ensure whatsapp_name is present
    whatsapp_name: inputData.whatsapp_name || inputData.pushName || inputData.profileName || ''
};"""

    # Replace from return to end of function
    new_js_code = js_code[:return_start] + new_return

    return new_js_code

def fix_state_machine_logic(function_code):
    """Fix the State Machine Logic to add debug logging and robust message extraction"""

    # Find the message extraction line
    message_line = "const message = inputData.content || inputData.body || inputData.text || inputData.message || '';"

    if message_line not in function_code:
        print("Warning: Could not find message extraction line")
        return function_code

    # New message extraction with debug and sanitization
    new_message_extraction = """// V26 FIX: Comprehensive message extraction with debug
const rawMessage = inputData.content ||
                  inputData.body ||
                  inputData.text ||
                  inputData.message ||
                  inputData.input ||  // Additional fallback
                  '';

// Debug message extraction
console.log('=== V26 MESSAGE EXTRACTION DEBUG ===');
console.log('inputData keys:', Object.keys(inputData));
console.log('inputData.content:', inputData.content);
console.log('inputData.body:', inputData.body);
console.log('inputData.text:', inputData.text);
console.log('inputData.message:', inputData.message);
console.log('Raw message extracted:', rawMessage);

// Clean message from invisible characters
const message = rawMessage
  .toString()  // Ensure it's a string
  .replace(/[\\u200B-\\u200D\\uFEFF]/g, '')  // Remove zero-width chars
  .replace(/[\\u0000-\\u001F\\u007F-\\u009F]/g, '')  // Remove control chars
  .trim();

console.log('Cleaned message:', message);
console.log('Message type:', typeof message);
console.log('Message length:', message.length);
console.log('Message charCodes:', message.split('').map(c => c.charCodeAt(0)));"""

    # Replace the old message extraction
    function_code = function_code.replace(message_line, new_message_extraction)

    # Also fix the validators to be more robust
    old_validator = """number_1_to_5: (input) => {
    const num = parseInt(input.trim());
    return num >= 1 && num <= 5;
  }"""

    new_validator = """number_1_to_5: (input) => {
    // V26: More robust validation with debug
    const cleaned = String(input)
      .trim()
      .replace(/[^\\d]/g, '')  // Remove everything except digits
      .substring(0, 1);        // Take only first digit

    console.log('V26 Validator - Input:', JSON.stringify(input), '-> Cleaned:', cleaned);

    if (!cleaned) {
      console.log('V26 Validator - No digits found in input');
      return false;
    }

    const num = parseInt(cleaned);
    const isValid = num >= 1 && num <= 5;
    console.log('V26 Validator - Number:', num, 'Valid:', isValid);
    return isValid;
  }"""

    # Replace the validator
    function_code = function_code.replace(old_validator, new_validator)

    # Add additional debug in service_selection case
    service_case = "case 'service_selection':"
    if service_case in function_code:
        # Add debug log right after the case
        debug_log = """case 'service_selection':
    console.log('=== V26 SERVICE SELECTION DEBUG ===');
    console.log('Current message:', message);
    console.log('Validator result:', validators.number_1_to_5(message));
    """
        function_code = function_code.replace("case 'service_selection':", debug_log)

    return function_code

def main():
    # Load V25 workflow
    v25_path = Path('n8n/workflows/02_ai_agent_conversation_V25_SIMPLIFIED_UPSERT.json')
    if not v25_path.exists():
        print(f"Error: {v25_path} not found")
        print("Trying alternative path...")
        v25_path = Path('02_ai_agent_conversation_V25_SIMPLIFIED_UPSERT.json')
        if not v25_path.exists():
            print("Error: Could not find V25 workflow")
            sys.exit(1)

    with open(v25_path, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    # Update workflow name
    workflow['name'] = 'AI Agent Conversation - V26 (Menu Validation Fix)'

    # Fix Prepare Phone Formats node
    prepare_fixed = False
    for node in workflow['nodes']:
        if node.get('name') == 'Prepare Phone Formats':
            print(f"Found Prepare Phone Formats node: {node['id']}")

            original_code = node['parameters']['jsCode']
            fixed_code = fix_prepare_phone_formats(original_code)
            node['parameters']['jsCode'] = fixed_code

            prepare_fixed = True
            print("✅ Fixed Prepare Phone Formats node with comprehensive message fields")
            break

    if not prepare_fixed:
        print("Warning: Could not find Prepare Phone Formats node")

    # Fix State Machine Logic node
    state_fixed = False
    for node in workflow['nodes']:
        if node.get('name') == 'State Machine Logic':
            print(f"Found State Machine Logic node: {node['id']}")

            if node.get('type') == 'n8n-nodes-base.function':
                # Function node uses 'functionCode'
                original_code = node['parameters']['functionCode']
                fixed_code = fix_state_machine_logic(original_code)
                node['parameters']['functionCode'] = fixed_code
            else:
                # Code node uses 'jsCode'
                original_code = node['parameters']['jsCode']
                fixed_code = fix_state_machine_logic(original_code)
                node['parameters']['jsCode'] = fixed_code

            state_fixed = True
            print("✅ Fixed State Machine Logic with debug logging and robust validation")
            break

    if not state_fixed:
        print("Error: Could not find State Machine Logic node")
        sys.exit(1)

    # Save as V26
    v26_path = Path('n8n/workflows/02_ai_agent_conversation_V26_MENU_VALIDATION_FIX.json')
    with open(v26_path, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Created V26 workflow: {v26_path}")
    print("\n📋 Debug Features Added:")
    print("1. Comprehensive message field extraction (content, body, text, message)")
    print("2. Invisible character removal and sanitization")
    print("3. Detailed debug logging for message extraction")
    print("4. Robust validator with digit-only extraction")
    print("5. Debug output for validator processing")

    print("\n🔍 How to Debug:")
    print("1. Import V26 workflow into n8n")
    print("2. Send test message '1' via WhatsApp")
    print("3. Check execution logs for V26 DEBUG messages")
    print("4. Look for:")
    print("   - 'V26 MESSAGE EXTRACTION DEBUG' - shows all field values")
    print("   - 'V26 SERVICE SELECTION DEBUG' - shows validation process")
    print("   - 'V26 Validator' - shows input cleaning and validation")

    print("\n📌 Next Steps:")
    print("1. Import V26 workflow: http://localhost:5678")
    print("2. Deactivate old workflow (yI726yYDl8UOOyfo)")
    print("3. Activate V26 workflow")
    print("4. Test with WhatsApp sending '1'")
    print("5. Monitor logs: docker logs -f e2bot-n8n-dev | grep V26")

if __name__ == '__main__':
    main()