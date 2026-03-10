#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
V35 EXECUTION FIX - Force Code Execution with Correct DB Structure
===================================================================
CRITICAL FIX: Ensures code actually executes with heavy logging
and uses correct database structure (phone_number, state_machine_state)

This script creates TWO versions:
1. V35_MINIMAL - Ultra simple test to verify execution
2. V35_FULL - Complete fix with proper state handling
"""

import json
import sys
from pathlib import Path

# Try V34 first, fallback to V33
BASE_WORKFLOW = "02_ai_agent_conversation_V34_NAME_VALIDATION.json"
FALLBACK_WORKFLOW = "02_ai_agent_conversation_V33_DEFINITIVE.json"
OUTPUT_MINIMAL = "02_ai_agent_conversation_V35_MINIMAL_TEST.json"
OUTPUT_FULL = "02_ai_agent_conversation_V35_EXECUTION_FIX.json"

def create_minimal_test_code():
    """Create minimal test to verify execution."""
    return """
// =====================================
// V35 MINIMAL TEST - EXECUTION CHECK
// =====================================
console.log('################################');
console.log('# V35 MINIMAL TEST EXECUTING   #');
console.log('# Time:', new Date().toISOString());
console.log('################################');

// Log raw input
console.log('V35 Input:', JSON.stringify(items[0].json));

// Just return a simple response to verify flow
return [{
  json: {
    response: 'V35 MINIMAL TEST - If you see this, code is executing!',
    timestamp: new Date().toISOString(),
    received: items[0].json.message || 'no message',
    test: 'V35_MINIMAL_ACTIVE'
  }
}];
"""

def create_full_v35_code():
    """Create full V35 implementation with correct DB structure."""
    return """
// =====================================
// V35 FULL EXECUTION FIX
// =====================================
console.log('################################');
console.log('# V35 FULL VERSION EXECUTING   #');
console.log('# Time:', new Date().toISOString());
console.log('################################');

// CRITICAL: Log at the very start
const startTime = Date.now();
console.log('V35 START - Input items:', JSON.stringify(items).substring(0, 500));

// Extract input with extensive logging
const input = items[0].json;
console.log('V35 Input Object Keys:', Object.keys(input));

// Extract key fields (using CORRECT database structure)
const message = input.message || '';
const phoneNumber = input.phone_number || input.phoneNumber || input.remoteJid || '';
const conversation = input.conversation || {};

console.log('V35 Extracted Values:');
console.log('  Message:', message);
console.log('  Phone Number:', phoneNumber);
console.log('  Conversation Keys:', Object.keys(conversation));

// Get current state - check BOTH possible fields
const currentStage = conversation.state_machine_state ||
                     conversation.current_state ||
                     'greeting';

console.log('V35 Current Stage Found:', currentStage);

// Initialize response variables
let responseText = '';
let nextStage = currentStage;
let updateData = {};
let errorCount = conversation.error_count || 0;
const MAX_ERRORS = 3;

// State name mapping (DB uses different names)
const stateNameMapping = {
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
  'greeting': 'greeting'
};

// Normalize stage name
const normalizedStage = stateNameMapping[currentStage] || currentStage;
console.log('V35 Normalized Stage:', normalizedStage);

// Templates for responses
const templates = {
  greeting: {
    text: '🤖 Olá! Bem-vindo à E2 Soluções!\\n\\nSomos especialistas em engenharia elétrica.\\n\\nEscolha o serviço desejado:\\n\\n☀️ 1 - Energia Solar\\n⚡ 2 - Subestação\\n📐 3 - Projetos Elétricos\\n🔋 4 - BESS (Armazenamento)\\n📊 5 - Análise e Laudos\\n\\nDigite o número de 1 a 5:'
  },
  invalid_option: {
    text: '❌ Opção inválida. Por favor, escolha uma opção válida.'
  },
  collect_name: {
    text: '👤 Qual seu nome completo?'
  },
  invalid_name: {
    text: '❌ Por favor, informe um nome válido (mínimo 3 letras).'
  },
  collect_phone: {
    text: '📱 Agora, informe seu telefone com DDD:\\n\\nExemplo: (11) 98765-4321'
  },
  collect_email: {
    text: '📧 Qual seu melhor e-mail?\\n\\n_Digite "pular" se não quiser informar_'
  },
  collect_city: {
    text: '📍 De qual cidade você é?'
  }
};

console.log('V35 Entering State Machine - Stage:', normalizedStage);

// State machine with HEAVY logging
switch (normalizedStage) {
  case 'greeting':
    console.log('V35: Processing GREETING state');

    // Check if it's a service selection (1-5)
    if (/^[1-5]$/.test(message)) {
      console.log('V35: Service selected:', message);
      updateData.service_selected = message;
      responseText = 'Ótima escolha! Vou coletar alguns dados.\\n\\n' + templates.collect_name.text;
      nextStage = 'collect_name';
    } else {
      console.log('V35: Showing menu');
      responseText = templates.greeting.text;
      nextStage = 'greeting';
    }
    break;

  case 'service_selection':
    console.log('V35: Processing SERVICE_SELECTION state');
    console.log('V35: Message for service:', message);

    if (/^[1-5]$/.test(message)) {
      console.log('V35: Valid service number:', message);
      updateData.service_selected = message;
      responseText = templates.collect_name.text;
      nextStage = 'collect_name';
    } else {
      console.log('V35: Invalid service selection');
      responseText = templates.invalid_option.text + '\\n\\n' + templates.greeting.text;
      nextStage = 'greeting';
      errorCount++;
    }
    break;

  case 'collect_name':
    console.log('################################');
    console.log('# V35: COLLECT_NAME STATE      #');
    console.log('# Message:', message);
    console.log('################################');

    // ULTRA SIMPLE validation - just check length
    const trimmedName = message.trim();
    console.log('V35 Name Validation:');
    console.log('  Original:', message);
    console.log('  Trimmed:', trimmedName);
    console.log('  Length:', trimmedName.length);

    if (trimmedName.length >= 2 && !/^[0-9]+$/.test(trimmedName)) {
      console.log('🎉 V35: NAME ACCEPTED:', trimmedName);
      updateData.lead_name = trimmedName;
      responseText = templates.collect_phone.text;
      nextStage = 'collect_phone';
      errorCount = 0;
    } else {
      console.log('❌ V35: NAME REJECTED:', trimmedName);
      responseText = templates.invalid_name.text;
      nextStage = 'collect_name';
      errorCount++;

      if (errorCount >= MAX_ERRORS) {
        nextStage = 'handoff_comercial';
        responseText = 'Vou transferir você para um especialista.';
      }
    }
    break;

  case 'collect_phone':
    console.log('V35: Processing COLLECT_PHONE state');
    updateData.phone = message;
    responseText = templates.collect_email.text;
    nextStage = 'collect_email';
    break;

  case 'collect_email':
    console.log('V35: Processing COLLECT_EMAIL state');
    updateData.email = message;
    responseText = templates.collect_city.text;
    nextStage = 'collect_city';
    break;

  case 'collect_city':
    console.log('V35: Processing COLLECT_CITY state');
    updateData.city = message;
    responseText = 'Obrigado! Dados coletados com sucesso.';
    nextStage = 'confirmation';
    break;

  default:
    console.log('V35: UNKNOWN STATE:', normalizedStage);
    responseText = templates.greeting.text;
    nextStage = 'greeting';
    break;
}

console.log('V35 State Machine Complete:');
console.log('  Response Text:', responseText.substring(0, 100));
console.log('  Next Stage:', nextStage);
console.log('  Update Data:', JSON.stringify(updateData));

// Build response
const result = {
  responseText: responseText,
  nextStage: nextStage,
  updateData: updateData,
  phone_number: phoneNumber,  // Use correct field name
  state_machine_state: nextStage,  // Use correct field name
  errorCount: errorCount,
  v35_executed: true,
  execution_time: Date.now() - startTime
};

console.log('V35 Final Result:', JSON.stringify(result));
console.log('V35 EXECUTION COMPLETE - Time:', Date.now() - startTime, 'ms');

return [{ json: result }];
"""

def create_workflow(base_path, code, output_name, workflow_name):
    """Create a workflow with the given code."""

    # Load base workflow
    if not base_path.exists():
        return False

    with open(base_path, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    # Find State Machine Logic node
    state_machine_node = None
    for node in workflow.get('nodes', []):
        if 'State Machine' in node.get('name', '') or 'Code' in node.get('name', ''):
            state_machine_node = node
            break

    if not state_machine_node:
        print(f"❌ State Machine Logic node not found in {base_path}")
        return False

    # Update the code
    if 'parameters' in state_machine_node:
        if 'functionCode' in state_machine_node['parameters']:
            state_machine_node['parameters']['functionCode'] = code
        elif 'jsCode' in state_machine_node['parameters']:
            state_machine_node['parameters']['jsCode'] = code
        else:
            # Try to find the right field
            print("Warning: Trying to find code field...")
            state_machine_node['parameters']['code'] = code

    # Update workflow name
    workflow['name'] = workflow_name

    # Save
    output_path = Path(f"../n8n/workflows/{output_name}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print(f"✅ Created: {output_name}")
    return True

def main():
    """Create both V35 versions."""

    print("=" * 60)
    print("V35 EXECUTION FIX - WORKFLOW GENERATOR")
    print("=" * 60)
    print()

    # Find base workflow
    base_path = Path(f"../n8n/workflows/{BASE_WORKFLOW}")
    if not base_path.exists():
        base_path = Path(f"../n8n/workflows/{FALLBACK_WORKFLOW}")
        if not base_path.exists():
            print("❌ No base workflow found!")
            return False

    print(f"✅ Using base workflow: {base_path.name}")
    print()

    # Create MINIMAL version
    print("Creating V35 MINIMAL TEST...")
    success1 = create_workflow(
        base_path,
        create_minimal_test_code(),
        OUTPUT_MINIMAL,
        "02 - V35 MINIMAL TEST"
    )

    # Create FULL version
    print("Creating V35 FULL VERSION...")
    success2 = create_workflow(
        base_path,
        create_full_v35_code(),
        OUTPUT_FULL,
        "02 - V35 EXECUTION FIX"
    )

    if success1 and success2:
        print()
        print("=" * 60)
        print("SUCCESS! V35 WORKFLOWS CREATED")
        print("=" * 60)
        print()
        print("📋 NEXT STEPS:")
        print()
        print("1. TEST MINIMAL FIRST:")
        print(f"   - Import {OUTPUT_MINIMAL}")
        print("   - Send any message")
        print("   - Check logs: docker logs -f e2bot-n8n-dev | grep V35")
        print()
        print("2. IF MINIMAL WORKS, TEST FULL:")
        print(f"   - Import {OUTPUT_FULL}")
        print("   - Test complete flow")
        print()
        print("3. MONITOR EVERYTHING:")
        print("   docker logs -f e2bot-n8n-dev 2>&1")
        print()
        return True

    return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)