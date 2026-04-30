#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
V32 State Mapping Fix Script
============================
Fixes the critical state naming inconsistency between database and code.
Database sends "identificando_servico" but code expects "service_selection".

Key Features:
1. State name mapping (DB → Code)
2. State normalization before switch
3. Phone validation with WhatsApp confirmation
4. Enhanced V32 diagnostic logging
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any

# V31 Workflow as base
BASE_WORKFLOW = "02_ai_agent_conversation_V31_COMPREHENSIVE_FIX.json"
OUTPUT_WORKFLOW = "02_ai_agent_conversation_V32_STATE_MAPPING.json"

def create_state_mapping_code() -> str:
    """Create the state name mapping object."""
    return """
// =====================================
// V32: STATE NAME MAPPING
// =====================================
// Fixes the critical bug where database sends different state names
// than what the code expects (e.g., "identificando_servico" vs "service_selection")

const stateNameMapping = {
  // Database state name → Code state name
  'identificando_servico': 'service_selection',
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

console.log('V32 STATE MAPPING: Initialized with', Object.keys(stateNameMapping).length, 'mappings');
"""

def create_state_normalization_code() -> str:
    """Create the state normalization logic."""
    return """
// =====================================
// V32: STATE NORMALIZATION
// =====================================

// Get the raw state from database (try multiple fields for compatibility)
const rawCurrentStage = conversation.state_machine_state ||
                        conversation.state_for_machine ||
                        conversation.current_state ||
                        conversation.current_state_v2 ||
                        'greeting';

// V32: NORMALIZE STATE NAME using mapping
const currentStage = stateNameMapping[rawCurrentStage] || rawCurrentStage;

console.log('=====================================');
console.log('V32 STATE NORMALIZATION:');
console.log('  Raw state from DB:', rawCurrentStage);
console.log('  Normalized state:', currentStage);
console.log('  Mapping applied:', rawCurrentStage !== currentStage ? 'YES ✓' : 'NO');
console.log('=====================================');

// V32: Diagnostic - Log if state was not in mapping
if (!stateNameMapping[rawCurrentStage]) {
  console.log('⚠️ V32 WARNING: State not in mapping:', rawCurrentStage);
  console.log('  Using raw state as-is. Consider adding to mapping.');
}
"""

def create_phone_validation_code() -> str:
    """Create enhanced phone validation with WhatsApp confirmation."""
    return """
    case 'collect_phone':
      console.log('=== V32 PHONE VALIDATION ENHANCED ===');

      // Get WhatsApp number (the one they're messaging from)
      const whatsappNumber = leadId.replace(/\\D/g, '');
      const inputMessage = message.toLowerCase().trim();
      const inputNumber = message.replace(/\\D/g, '');

      console.log('V32 Phone Data:');
      console.log('  WhatsApp number:', whatsappNumber);
      console.log('  Input message:', inputMessage);
      console.log('  Input number:', inputNumber);
      console.log('  Stage data:', JSON.stringify(stageData));

      // Check if it's a confirmation response
      if (inputMessage === 'sim' || inputMessage === '1' || inputMessage === 's') {
        // User confirmed same number as WhatsApp
        const formatted = whatsappNumber.replace(/(\\d{2})(\\d{4,5})(\\d{4})/, '($1) $2-$3');

        console.log('V32: User confirmed WhatsApp as primary phone');

        updateData.phone = formatted;
        updateData.phone_whatsapp = formatted;
        updateData.phone_alternative = null;
        updateData.phone_validated = true;

        responseText = templates.collect_email.text;
        nextStage = 'collect_email';
        errorCount = 0;

      } else if (inputMessage === 'não' || inputMessage === 'nao' || inputMessage === '2' || inputMessage === 'n') {
        // User wants to provide different number
        console.log('V32: User wants different phone number');

        responseText = '📱 Por favor, digite seu telefone principal com DDD:\\n\\nExemplo: (62) 98175-5548';
        nextStage = 'collect_phone';
        updateData.phone_confirmation_asked = true;
        updateData.phone_different_requested = true;

      } else if (stageData.phone_different_requested && validators.phone_brazil(message)) {
        // User provided a different valid number
        const cleaned = inputNumber;
        const formatted = cleaned.replace(/(\\d{2})(\\d{4,5})(\\d{4})/, '($1) $2-$3');
        const whatsappFormatted = whatsappNumber.replace(/(\\d{2})(\\d{4,5})(\\d{4})/, '($1) $2-$3');

        console.log('V32: Different phone number provided and validated');

        updateData.phone = formatted;  // Main phone (different)
        updateData.phone_whatsapp = whatsappFormatted;  // WhatsApp phone
        updateData.phone_alternative = formatted;  // Alternative provided
        updateData.phone_validated = true;

        responseText = templates.collect_email.text;
        nextStage = 'collect_email';
        errorCount = 0;

      } else if (!stageData.phone_confirmation_asked) {
        // First time in this stage - ask for confirmation
        const formatted = whatsappNumber.replace(/(\\d{2})(\\d{4,5})(\\d{4})/, '($1) $2-$3');

        console.log('V32: First time - asking for phone confirmation');

        responseText = `📱 Percebi que você está usando o WhatsApp do número:\\n\\n*${formatted}*\\n\\nEste é seu telefone principal?\\n\\n✅ Digite *1* ou *SIM* para confirmar\\n❌ Digite *2* ou *NÃO* para informar outro número`;

        updateData.phone_confirmation_asked = true;
        nextStage = 'collect_phone';  // Stay in same stage

      } else if (validators.phone_brazil(message)) {
        // Direct phone number input (backward compatibility)
        const cleaned = inputNumber;
        const formatted = cleaned.replace(/(\\d{2})(\\d{4,5})(\\d{4})/, '($1) $2-$3');

        console.log('V32: Direct phone input validated (backward compatibility)');

        updateData.phone = formatted;
        updateData.phone_whatsapp = whatsappNumber.replace(/(\\d{2})(\\d{4,5})(\\d{4})/, '($1) $2-$3');
        updateData.phone_alternative = formatted !== updateData.phone_whatsapp ? formatted : null;
        updateData.phone_validated = true;

        responseText = templates.collect_email.text;
        nextStage = 'collect_email';
        errorCount = 0;

      } else {
        // Validation failed
        console.log('V32: Phone validation failed');

        responseText = templates.invalid_phone.text;
        nextStage = 'collect_phone';
        errorCount++;

        if (errorCount >= MAX_ERRORS) {
          nextStage = 'handoff_comercial';
          responseText = '⚠️ Vou transferir você para um especialista que pode ajudar melhor.\\n\\nAguarde um momento...';
        }
      }

      console.log('V32 Phone Stage Result:');
      console.log('  Next stage:', nextStage);
      console.log('  Phone validated:', updateData.phone_validated || false);
      console.log('  Error count:', errorCount);
      break;
"""

def create_confirmation_template_update() -> str:
    """Update confirmation template to show phone details."""
    return """
// V32: Enhanced confirmation template with phone details
confirmation: {
  template: '✅ *Dados confirmados!*\\n\\n' +
    '👤 *Nome:* {{lead_name}}\\n' +
    '📱 *Telefone Principal:* {{phone}}\\n' +
    '📲 *WhatsApp:* {{phone_whatsapp}}\\n' +
    '📧 *Email:* {{email}}\\n' +
    '📍 *Cidade:* {{city}}\\n' +
    '{{emoji}} *Serviço:* {{service_name}}\\n\\n' +
    '━━━━━━━━━━━━━━━\\n\\n' +
    '🗓️ Deseja agendar uma *visita técnica gratuita*?\\n\\n' +
    '1️⃣ Sim, quero agendar\\n' +
    '2️⃣ Não, prefiro falar com especialista\\n\\n' +
    '_Digite 1 ou 2:_'
}
"""

def fix_workflow():
    """Apply V32 state mapping fixes to workflow."""

    print("=" * 60)
    print("V32 STATE MAPPING FIX SCRIPT")
    print("=" * 60)

    # Load base workflow
    workflow_path = Path(f"../n8n/workflows/{BASE_WORKFLOW}")
    if not workflow_path.exists():
        print(f"❌ Base workflow not found: {workflow_path}")
        return False

    print(f"✅ Loading base workflow: {BASE_WORKFLOW}")

    with open(workflow_path, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    # Find the State Machine Logic node
    ai_agent_node = None
    for node in workflow.get('nodes', []):
        if node.get('name') == 'State Machine Logic':
            ai_agent_node = node
            break

    if not ai_agent_node:
        print("❌ State Machine Logic node not found")
        return False

    print("✅ Found State Machine Logic node")

    # Get the code
    code = ai_agent_node['parameters']['functionCode']

    print("\n📝 Applying V32 fixes:")

    # 1. Add state mapping after templates definition
    print("  1. Adding state name mapping...")
    templates_end = code.find("// =====================================\n// VALIDATOR FUNCTIONS")
    if templates_end > 0:
        code = (code[:templates_end] +
                create_state_mapping_code() + "\n" +
                code[templates_end:])

    # 2. Replace state initialization with normalization
    print("  2. Adding state normalization...")
    old_state_init = "const currentStage = conversation.current_state || 'greeting';"
    if old_state_init in code:
        code = code.replace(old_state_init, create_state_normalization_code())
    else:
        # Try V31 version
        v31_pattern = "const currentStage = conversation.state_machine_state"
        if v31_pattern in code:
            # Find the full statement
            start = code.find(v31_pattern)
            end = code.find(";", start) + 1
            old_statement = code[start:end]
            code = code.replace(old_statement, create_state_normalization_code())

    # 3. Update phone validation case
    print("  3. Updating phone validation with WhatsApp confirmation...")
    phone_case_start = code.find("case 'collect_phone':")
    if phone_case_start > 0:
        # Find the end of this case (next case or default)
        next_case = code.find("case '", phone_case_start + 20)
        if next_case == -1:
            next_case = code.find("default:", phone_case_start)

        if next_case > 0:
            # Find the break before the next case
            break_pos = code.rfind("break;", phone_case_start, next_case)
            if break_pos > 0:
                # Replace the entire case
                code = (code[:phone_case_start] +
                       create_phone_validation_code() + "\n" +
                       code[break_pos + 6:])

    # 4. Update confirmation template
    print("  4. Updating confirmation template with phone details...")
    conf_template_start = code.find("confirmation: {")
    if conf_template_start > 0:
        # Find the end of this template
        template_end = code.find("}", conf_template_start) + 1
        # Find the next template or section
        next_section = code.find(",\n", template_end)
        if next_section > 0:
            code = (code[:conf_template_start] +
                   create_confirmation_template_update() +
                   code[next_section:])

    # 5. Add V32 version logging
    print("  5. Adding V32 version identification...")
    version_marker = "console.log('=============== V31 EXECUTION START ===============');"
    if version_marker in code:
        code = code.replace(version_marker,
            "console.log('=============== V32 EXECUTION START ===============');\nconsole.log('Version: V32 - State Mapping + Phone Validation Fix');\nconsole.log('===============================================');")

    # Update the node with fixed code
    ai_agent_node['parameters']['functionCode'] = code

    # Save the new workflow
    output_path = Path(f"../n8n/workflows/{OUTPUT_WORKFLOW}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print(f"\n✅ V32 workflow saved: {OUTPUT_WORKFLOW}")

    # Create summary
    print("\n" + "=" * 60)
    print("V32 FIX SUMMARY")
    print("=" * 60)
    print("\n🎯 Key Changes Applied:")
    print("  1. State name mapping (DB → Code)")
    print("  2. State normalization before switch")
    print("  3. Phone validation with WhatsApp confirmation")
    print("  4. Enhanced confirmation template")
    print("  5. V32 diagnostic logging")

    print("\n📋 Next Steps:")
    print("  1. Import workflow in n8n:")
    print(f"     {OUTPUT_WORKFLOW}")
    print("  2. Deactivate V31 workflow")
    print("  3. Activate V32 workflow")
    print("  4. Run validation script:")
    print("     ./validate-v32-fix.sh")

    print("\n✅ V32 fix completed successfully!")

    return True

if __name__ == "__main__":
    success = fix_workflow()
    sys.exit(0 if success else 1)