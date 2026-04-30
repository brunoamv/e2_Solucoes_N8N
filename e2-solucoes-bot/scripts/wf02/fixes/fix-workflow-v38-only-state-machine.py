#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
V38 - ONLY STATE MACHINE LOGIC UPDATE
======================================
Keep everything else from V34, only update State Machine Logic node.
This preserves the working Build Update Queries structure.

CRITICAL: Only modify the State Machine Logic node code.
Keep all other nodes unchanged from V34.
"""

import json
import sys
from pathlib import Path

# Use V34 as base - it has working Build Update Queries
BASE_WORKFLOW = "02_ai_agent_conversation_V34_NAME_VALIDATION.json"
OUTPUT_WORKFLOW = "02_ai_agent_conversation_V38_STATE_MACHINE_ONLY.json"

def create_v38_state_machine_code():
    """
    V38 State Machine - Based on V34 structure with improved logic.
    CRITICAL: Return structure must match what Build Update Queries expects.
    """
    return """
// =====================================
// V38 STATE MACHINE LOGIC (V34 Structure)
// =====================================
console.log('V38 STATE MACHINE LOGIC - START');

// Extract input data with same structure as V34
const input = $input.first().json;
const message = input.message || input.body || input.text || '';
const phoneNumber = input.phone_number || input.phone_without_code || '';
const conversation = input.conversation || {};

console.log('V38 Input:');
console.log('  Message:', message);
console.log('  Phone:', phoneNumber);
console.log('  Conversation Keys:', Object.keys(conversation));

// Get current state - EXACT same logic as V34
const currentStage = conversation.state_machine_state ||
                     conversation.current_state ||
                     conversation.state_for_machine ||
                     'greeting';

console.log('V38 Current Stage:', currentStage);

// Initialize variables - SAME AS V34
let responseText = '';
let nextStage = currentStage;
let updateData = {};
let errorCount = conversation.error_count || 0;

// State name mapping - CRITICAL for database consistency
const stateNameMapping = {
  'novo': 'greeting',
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
  'greeting': 'greeting'
};

// Normalize stage name
const normalizedStage = stateNameMapping[currentStage] || currentStage;
console.log('V38 Normalized Stage:', normalizedStage);

// Templates - Portuguese messages
const templates = {
  greeting: '🤖 Olá! Bem-vindo à E2 Soluções!\\n\\nSomos especialistas em engenharia elétrica.\\n\\nEscolha o serviço desejado:\\n\\n1️⃣ - Energia Solar\\n2️⃣ - Subestação\\n3️⃣ - Projetos Elétricos\\n4️⃣ - BESS (Armazenamento)\\n5️⃣ - Análise e Laudos\\n\\nDigite o número (1-5):',
  invalid_option: '❌ Opção inválida. Por favor, escolha um número de 1 a 5.',
  collect_name: '👤 Qual seu nome completo?',
  invalid_name: '❌ Por favor, informe um nome válido (mínimo 3 letras).',
  collect_phone: '📱 Agora, informe seu telefone com DDD:\\nExemplo: (61) 98765-4321',
  collect_email: '📧 Qual seu melhor e-mail?\\n\\n_Digite "pular" se não quiser informar_',
  collect_city: '📍 De qual cidade você está falando?'
};

// State machine - EXACT V34 logic with V38 improvements
switch (normalizedStage) {
  case 'greeting':
  case 'novo':
    console.log('V38: Processing GREETING state');

    // Check if it's a service selection
    if (/^[1-5]$/.test(message)) {
      console.log('V38: Service selected:', message);
      updateData.service_selected = message;
      responseText = 'Ótima escolha! Vou precisar de alguns dados.\\n\\n' + templates.collect_name;
      nextStage = 'collect_name';
    } else {
      console.log('V38: Showing greeting menu');
      responseText = templates.greeting;
      nextStage = 'service_selection';
    }
    break;

  case 'service_selection':
  case 'identificando_servico':
    console.log('V38: Processing SERVICE_SELECTION state');

    if (/^[1-5]$/.test(message)) {
      console.log('V38: Valid service number:', message);
      updateData.service_selected = message;
      responseText = templates.collect_name;
      nextStage = 'collect_name';
    } else {
      console.log('V38: Invalid service selection');
      responseText = templates.invalid_option + '\\n\\n' + templates.greeting;
      nextStage = 'service_selection';
      errorCount++;
    }
    break;

  case 'collect_name':
  case 'coletando_nome':
    console.log('================================');
    console.log('V38: COLLECT_NAME STATE');
    console.log('Message:', message);
    console.log('================================');

    // Simple name validation - at least 2 chars, not just numbers
    const trimmedName = message.trim();
    console.log('V38 Name Validation:');
    console.log('  Original:', message);
    console.log('  Trimmed:', trimmedName);
    console.log('  Length:', trimmedName.length);

    if (trimmedName.length >= 2 && !/^[0-9]+$/.test(trimmedName)) {
      console.log('✅ V38: NAME ACCEPTED:', trimmedName);
      updateData.lead_name = trimmedName;
      updateData.contact_name = trimmedName; // Also update contact_name
      responseText = `Obrigado, ${trimmedName}!\\n\\n` + templates.collect_phone;
      nextStage = 'collect_phone';
      errorCount = 0;
    } else {
      console.log('❌ V38: NAME REJECTED');
      responseText = templates.invalid_name;
      nextStage = 'collect_name';
      errorCount++;
    }
    break;

  case 'collect_phone':
  case 'coletando_telefone':
    console.log('V38: Processing COLLECT_PHONE state');
    updateData.phone = message;
    updateData.contact_phone = message; // Also update contact_phone
    responseText = templates.collect_email;
    nextStage = 'collect_email';
    break;

  case 'collect_email':
  case 'coletando_email':
    console.log('V38: Processing COLLECT_EMAIL state');
    if (message.toLowerCase() !== 'pular') {
      updateData.email = message;
      updateData.contact_email = message; // Also update contact_email
    }
    responseText = templates.collect_city;
    nextStage = 'collect_city';
    break;

  case 'collect_city':
  case 'coletando_cidade':
    console.log('V38: Processing COLLECT_CITY state');
    updateData.city = message;
    responseText = '✅ Perfeito! Recebi todos os seus dados.\\n\\n' +
                  'Em breve, um de nossos especialistas entrará em contato.\\n\\n' +
                  'Obrigado por escolher a E2 Soluções! 🚀';
    nextStage = 'completed';
    break;

  default:
    console.log('V38: UNKNOWN STATE:', normalizedStage);
    responseText = templates.greeting;
    nextStage = 'greeting';
    break;
}

console.log('V38 State Machine Complete:');
console.log('  Response Text:', responseText.substring(0, 50) + '...');
console.log('  Next Stage:', nextStage);
console.log('  Update Data:', JSON.stringify(updateData));

// CRITICAL: Return structure MUST match what Build Update Queries expects
// This is the EXACT structure from V34 that works
const result = {
  responseText: responseText,
  nextStage: nextStage,
  currentStage: normalizedStage,
  updateData: updateData,
  phone_number: phoneNumber,
  state_machine_state: nextStage,
  errorCount: errorCount,
  // Add these fields that Build Update Queries needs
  lead_id: phoneNumber, // Build Update Queries uses this
  conversation_id: conversation.id || null,
  collected_data: {
    ...conversation.collected_data,
    ...updateData
  }
};

console.log('V38 Final Result Keys:', Object.keys(result));
console.log('V38 STATE MACHINE LOGIC - END');

// Return in the format Build Update Queries expects
return result;
"""

def update_workflow():
    """Update only the State Machine Logic node in V34 workflow."""

    # Load V34 workflow
    base_path = Path(f"../n8n/workflows/{BASE_WORKFLOW}")
    if not base_path.exists():
        print(f"❌ Base workflow not found: {BASE_WORKFLOW}")
        return False

    with open(base_path, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    print(f"✅ Loaded base workflow: {BASE_WORKFLOW}")

    # Find State Machine Logic node
    state_machine_node = None
    for node in workflow.get('nodes', []):
        if 'State Machine Logic' in node.get('name', ''):
            state_machine_node = node
            print(f"✅ Found State Machine Logic node: {node.get('name')}")
            break

    if not state_machine_node:
        print("❌ State Machine Logic node not found!")
        return False

    # Update ONLY the code in State Machine Logic node
    new_code = create_v38_state_machine_code()

    if 'parameters' in state_machine_node:
        if 'jsCode' in state_machine_node['parameters']:
            state_machine_node['parameters']['jsCode'] = new_code
            print("✅ Updated jsCode field")
        elif 'functionCode' in state_machine_node['parameters']:
            state_machine_node['parameters']['functionCode'] = new_code
            print("✅ Updated functionCode field")
        else:
            print("⚠️ Warning: Code field not found in expected location")
            # Try to find any code field
            for key in state_machine_node['parameters']:
                if 'code' in key.lower():
                    state_machine_node['parameters'][key] = new_code
                    print(f"✅ Updated {key} field")
                    break

    # Update workflow name to V38
    workflow['name'] = "02 - AI Agent Conversation V38 (State Machine Only)"

    # Save as V38
    output_path = Path(f"../n8n/workflows/{OUTPUT_WORKFLOW}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print(f"✅ Created: {OUTPUT_WORKFLOW}")
    return True

def main():
    """Main function to create V38."""

    print("=" * 60)
    print("V38 - ONLY STATE MACHINE LOGIC UPDATE")
    print("=" * 60)
    print()
    print("This version keeps the V34 structure that works with")
    print("Build Update Queries, only updating State Machine Logic.")
    print()

    success = update_workflow()

    if success:
        print()
        print("=" * 60)
        print("SUCCESS! V38 WORKFLOW CREATED")
        print("=" * 60)
        print()
        print("🎯 WHAT'S DIFFERENT IN V38:")
        print("- ONLY State Machine Logic node was updated")
        print("- All other nodes remain EXACTLY as V34")
        print("- Return structure matches Build Update Queries expectations")
        print()
        print("📋 NEXT STEPS:")
        print()
        print("1. DEACTIVATE all other conversation workflows")
        print()
        print("2. IMPORT AND ACTIVATE V38:")
        print(f"   - Import: {OUTPUT_WORKFLOW}")
        print("   - Activate it (green toggle)")
        print("   - This preserves the working Build Update Queries structure")
        print()
        print("3. TEST THE FLOW:")
        print("   - Send '1' → Should show menu")
        print("   - Send 'Bruno Rosa' → Should be ACCEPTED!")
        print("   - Check that database updates work")
        print()
        print("4. MONITOR:")
        print("   docker logs -f e2bot-n8n-dev 2>&1 | grep V38")
        print()
        print("✅ This approach preserves what works and only fixes the State Machine!")
        print()
        return True

    return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)