#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
V39 FIELD NAMING FIX - Correção de Nomenclatura
================================================
V38 usava "responseText" mas Build Update Queries espera "response_text"

PROBLEMA CRÍTICO:
- V34 Build Update Queries: inputData.response_text (com underscore)
- V38 State Machine: responseText (camelCase)
- Build Update Queries não encontra o campo!

SOLUÇÃO V39:
- Usar EXATAMENTE a mesma nomenclatura do V34
- response_text em vez de responseText
- next_stage em vez de nextStage
- current_state em vez de currentStage
"""

import json
import sys
from pathlib import Path

# Usar V34 como base (tem Build Update Queries funcionando)
BASE_WORKFLOW = "02_ai_agent_conversation_V34_NAME_VALIDATION.json"
OUTPUT_WORKFLOW = "02_ai_agent_conversation_V39_FIELD_NAMING_FIX.json"

def create_v39_state_machine_code():
    """
    V39 State Machine - EXATA nomenclatura do V34 Build Update Queries.

    CRITICAL: Os campos devem ser EXATAMENTE como V34 Build Update Queries espera:
    - response_text (não responseText)
    - next_stage (não nextStage)
    - current_state (não currentStage)
    """
    return """
// =====================================
// V39 STATE MACHINE - V34 FIELD NAMING
// =====================================
console.log('V39 STATE MACHINE - START');

// Extract input data
const input = $input.first().json;
const message = input.message || input.body || input.text || '';
const phoneNumber = input.phone_number || input.phone_without_code || '';
const conversation = input.conversation || {};

console.log('V39 Input:');
console.log('  Message:', message);
console.log('  Phone:', phoneNumber);

// Get current state
const currentStage = conversation.state_machine_state ||
                     conversation.current_state ||
                     conversation.state_for_machine ||
                     'greeting';

console.log('V39 Current Stage:', currentStage);

// Initialize variables
let responseText = '';
let nextStage = currentStage;
let updateData = {};
let errorCount = conversation.error_count || 0;

// State name mapping
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

const normalizedStage = stateNameMapping[currentStage] || currentStage;
console.log('V39 Normalized Stage:', normalizedStage);

// Templates
const templates = {
  greeting: '🤖 Olá! Bem-vindo à E2 Soluções!\\n\\nSomos especialistas em engenharia elétrica.\\n\\nEscolha o serviço desejado:\\n\\n1️⃣ - Energia Solar\\n2️⃣ - Subestação\\n3️⃣ - Projetos Elétricos\\n4️⃣ - BESS (Armazenamento)\\n5️⃣ - Análise e Laudos\\n\\nDigite o número (1-5):',
  invalid_option: '❌ Opção inválida. Por favor, escolha um número de 1 a 5.',
  collect_name: '👤 Qual seu nome completo?',
  invalid_name: '❌ Por favor, informe um nome válido (mínimo 3 letras).',
  collect_phone: '📱 Agora, informe seu telefone com DDD:\\nExemplo: (61) 98765-4321',
  collect_email: '📧 Qual seu melhor e-mail?\\n\\n_Digite "pular" se não quiser informar_',
  collect_city: '📍 De qual cidade você está falando?'
};

// State machine
switch (normalizedStage) {
  case 'greeting':
  case 'novo':
    console.log('V39: Processing GREETING state');
    if (/^[1-5]$/.test(message)) {
      console.log('V39: Service selected:', message);
      updateData.service_selected = message;
      responseText = 'Ótima escolha! Vou precisar de alguns dados.\\n\\n' + templates.collect_name;
      nextStage = 'collect_name';
    } else {
      console.log('V39: Showing greeting menu');
      responseText = templates.greeting;
      nextStage = 'service_selection';
    }
    break;

  case 'service_selection':
  case 'identificando_servico':
    console.log('V39: Processing SERVICE_SELECTION state');
    if (/^[1-5]$/.test(message)) {
      console.log('V39: Valid service number:', message);
      updateData.service_selected = message;
      responseText = templates.collect_name;
      nextStage = 'collect_name';
    } else {
      console.log('V39: Invalid service selection');
      responseText = templates.invalid_option + '\\n\\n' + templates.greeting;
      nextStage = 'service_selection';
      errorCount++;
    }
    break;

  case 'collect_name':
  case 'coletando_nome':
    console.log('================================');
    console.log('V39: COLLECT_NAME STATE');
    console.log('Message:', message);
    console.log('================================');

    const trimmedName = message.trim();
    console.log('V39 Name Validation:');
    console.log('  Trimmed:', trimmedName);
    console.log('  Length:', trimmedName.length);

    if (trimmedName.length >= 2 && !/^[0-9]+$/.test(trimmedName)) {
      console.log('✅ V39: NAME ACCEPTED:', trimmedName);
      updateData.lead_name = trimmedName;
      updateData.contact_name = trimmedName;
      responseText = `Obrigado, ${trimmedName}!\\n\\n` + templates.collect_phone;
      nextStage = 'collect_phone';
      errorCount = 0;
    } else {
      console.log('❌ V39: NAME REJECTED');
      responseText = templates.invalid_name;
      nextStage = 'collect_name';
      errorCount++;
    }
    break;

  case 'collect_phone':
  case 'coletando_telefone':
    console.log('V39: Processing COLLECT_PHONE state');
    updateData.phone = message;
    updateData.contact_phone = message;
    responseText = templates.collect_email;
    nextStage = 'collect_email';
    break;

  case 'collect_email':
  case 'coletando_email':
    console.log('V39: Processing COLLECT_EMAIL state');
    if (message.toLowerCase() !== 'pular') {
      updateData.email = message;
      updateData.contact_email = message;
    }
    responseText = templates.collect_city;
    nextStage = 'collect_city';
    break;

  case 'collect_city':
  case 'coletando_cidade':
    console.log('V39: Processing COLLECT_CITY state');
    updateData.city = message;
    responseText = '✅ Perfeito! Recebi todos os seus dados.\\n\\n' +
                  'Em breve, um de nossos especialistas entrará em contato.\\n\\n' +
                  'Obrigado por escolher a E2 Soluções! 🚀';
    nextStage = 'completed';
    break;

  default:
    console.log('V39: UNKNOWN STATE:', normalizedStage);
    responseText = templates.greeting;
    nextStage = 'greeting';
    break;
}

console.log('V39 State Machine Complete');
console.log('  Response:', responseText.substring(0, 50) + '...');
console.log('  Next Stage:', nextStage);

// CRITICAL: Usar EXATAMENTE a nomenclatura do V34 Build Update Queries
// V34 espera: response_text, next_stage, current_state (com underscore)
const result = {
  // CRITICAL FIELDS - EXATA nomenclatura V34 Build Update Queries
  response_text: responseText,        // V34 usa: inputData.response_text
  next_stage: nextStage,               // V34 usa: inputData.next_stage
  current_state: normalizedStage,      // V34 usa: inputData.current_state

  // Phone fields
  phone_number: phoneNumber,
  phone_with_code: phoneNumber,
  phone_without_code: phoneNumber.replace(/^55/, ''),

  // Update data
  collected_data: {
    ...conversation.collected_data,
    ...updateData
  },

  // State machine fields
  state_machine_state: nextStage,
  errorCount: errorCount,

  // Message data
  message: message,
  message_type: 'text',

  // Conversation data
  conversation_id: conversation.id || null,
  lead_id: phoneNumber,

  // Execution tracking
  v39_executed: true,
  v39_timestamp: new Date().toISOString()
};

console.log('V39 Final Result Keys:', Object.keys(result));
console.log('V39 CRITICAL: response_text =', result.response_text ? 'SET' : 'MISSING');
console.log('V39 CRITICAL: next_stage =', result.next_stage);
console.log('V39 STATE MACHINE - END');

return result;
"""

def update_workflow():
    """Update State Machine Logic node in V34 workflow."""

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

    # Update the code
    new_code = create_v39_state_machine_code()

    if 'parameters' in state_machine_node:
        if 'jsCode' in state_machine_node['parameters']:
            state_machine_node['parameters']['jsCode'] = new_code
            print("✅ Updated jsCode field")
        elif 'functionCode' in state_machine_node['parameters']:
            state_machine_node['parameters']['functionCode'] = new_code
            print("✅ Updated functionCode field")
        else:
            # Try to find any code field
            for key in state_machine_node['parameters']:
                if 'code' in key.lower():
                    state_machine_node['parameters'][key] = new_code
                    print(f"✅ Updated {key} field")
                    break

    # Update workflow name
    workflow['name'] = "02 - AI Agent Conversation V39 (Field Naming Fix)"

    # Save as V39
    output_path = Path(f"../n8n/workflows/{OUTPUT_WORKFLOW}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print(f"✅ Created: {OUTPUT_WORKFLOW}")
    return True

def main():
    """Main function to create V39."""

    print("=" * 60)
    print("V39 - FIELD NAMING FIX")
    print("=" * 60)
    print()
    print("PROBLEMA:")
    print("  V38 usava: responseText (camelCase)")
    print("  V34 Build Update Queries espera: response_text (underscore)")
    print()
    print("SOLUÇÃO V39:")
    print("  Usar EXATAMENTE a nomenclatura do V34:")
    print("  • response_text (não responseText)")
    print("  • next_stage (não nextStage)")
    print("  • current_state (não currentStage)")
    print()

    success = update_workflow()

    if success:
        print()
        print("=" * 60)
        print("SUCCESS! V39 WORKFLOW CREATED")
        print("=" * 60)
        print()
        print("🎯 DIFERENÇA CRÍTICA DO V39:")
        print("- V38: responseText → Build Update Queries NÃO encontrava")
        print("- V39: response_text → Build Update Queries ENCONTRA! ✅")
        print()
        print("📋 NEXT STEPS:")
        print()
        print("1. DEACTIVATE V38 workflow")
        print()
        print("2. IMPORT AND ACTIVATE V39:")
        print(f"   - Import: {OUTPUT_WORKFLOW}")
        print("   - Activate it (green toggle)")
        print()
        print("3. TEST THE FLOW:")
        print("   - Send '1' → Menu appears")
        print("   - Send 'Bruno Rosa' → ACCEPTED!")
        print("   - Check Build Update Queries logs:")
        print("     'Response text: <message>' should appear")
        print()
        print("4. MONITOR:")
        print("   docker logs -f e2bot-n8n-dev 2>&1 | grep -E 'V39|response_text'")
        print()
        print("✅ V39 usa a MESMA nomenclatura que V34 Build Update Queries!")
        print()
        return True

    return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
