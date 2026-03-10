#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
V40 COMPLETE STRUCTURE - Estrutura Completa do V34
===================================================
V39 não tinha os nodes de busca de conversation do banco.
V40 mantém TODA estrutura do V34 + nomenclatura correta.

PROBLEMA:
- V39 não buscava conversation do banco antes do State Machine
- Por isso currentStage voltava sempre para 'greeting'
- Build Update Queries executava mas conversation estava vazia

SOLUÇÃO V40:
- Usar V34 COMPLETO (tem Get Conversation Details + Merge)
- Apenas corrigir nomenclatura no State Machine Logic
- response_text (não responseText)
"""

import json
import sys
from pathlib import Path

# Usar V34 COMPLETO como base
BASE_WORKFLOW = "02_ai_agent_conversation_V34_NAME_VALIDATION.json"
OUTPUT_WORKFLOW = "02_ai_agent_conversation_V40_COMPLETE_STRUCTURE.json"

def create_v40_state_machine_code():
    """
    V40 State Machine - MESMA lógica do V39 mas será usada com estrutura completa V34.
    """
    return """
// =====================================
// V40 STATE MACHINE - V34 COMPLETE STRUCTURE
// =====================================
console.log('V40 STATE MACHINE - START');

// Extract input data - agora conversation virá do banco via Get Conversation Details
const input = $input.first().json;
const message = input.message || input.body || input.text || '';
const phoneNumber = input.phone_number || input.phone_without_code || '';
const conversation = input.conversation || {};  // Agora será populado!

console.log('V40 Input:');
console.log('  Message:', message);
console.log('  Phone:', phoneNumber);
console.log('  Conversation ID:', conversation.id || 'NEW');

// Get current state - agora virá do banco!
const currentStage = conversation.state_machine_state ||
                     conversation.current_state ||
                     conversation.state_for_machine ||
                     'greeting';

console.log('V40 Current Stage:', currentStage);
console.log('V40 Conversation State Machine State:', conversation.state_machine_state);

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
console.log('V40 Normalized Stage:', normalizedStage);

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
    console.log('V40: Processing GREETING state');
    if (/^[1-5]$/.test(message)) {
      console.log('V40: Service selected:', message);
      updateData.service_selected = message;
      responseText = 'Ótima escolha! Vou precisar de alguns dados.\\n\\n' + templates.collect_name;
      nextStage = 'collect_name';
    } else {
      console.log('V40: Showing greeting menu');
      responseText = templates.greeting;
      nextStage = 'service_selection';
    }
    break;

  case 'service_selection':
  case 'identificando_servico':
    console.log('V40: Processing SERVICE_SELECTION state');
    if (/^[1-5]$/.test(message)) {
      console.log('V40: Valid service number:', message);
      updateData.service_selected = message;
      responseText = templates.collect_name;
      nextStage = 'collect_name';
    } else {
      console.log('V40: Invalid service selection');
      responseText = templates.invalid_option + '\\n\\n' + templates.greeting;
      nextStage = 'service_selection';
      errorCount++;
    }
    break;

  case 'collect_name':
  case 'coletando_nome':
    console.log('================================');
    console.log('V40: COLLECT_NAME STATE');
    console.log('Message:', message);
    console.log('================================');

    const trimmedName = message.trim();
    console.log('V40 Name Validation:');
    console.log('  Trimmed:', trimmedName);
    console.log('  Length:', trimmedName.length);

    if (trimmedName.length >= 2 && !/^[0-9]+$/.test(trimmedName)) {
      console.log('✅ V40: NAME ACCEPTED:', trimmedName);
      updateData.lead_name = trimmedName;
      responseText = `Obrigado, ${trimmedName}!\\n\\n` + templates.collect_phone;
      nextStage = 'collect_phone';
      errorCount = 0;
    } else {
      console.log('❌ V40: NAME REJECTED');
      responseText = templates.invalid_name;
      nextStage = 'collect_name';
      errorCount++;
    }
    break;

  case 'collect_phone':
  case 'coletando_telefone':
    console.log('V40: Processing COLLECT_PHONE state');
    updateData.phone = message;
    responseText = templates.collect_email;
    nextStage = 'collect_email';
    break;

  case 'collect_email':
  case 'coletando_email':
    console.log('V40: Processing COLLECT_EMAIL state');
    if (message.toLowerCase() !== 'pular') {
      updateData.email = message;
    }
    responseText = templates.collect_city;
    nextStage = 'collect_city';
    break;

  case 'collect_city':
  case 'coletando_cidade':
    console.log('V40: Processing COLLECT_CITY state');
    updateData.city = message;
    responseText = '✅ Perfeito! Recebi todos os seus dados.\\n\\n' +
                  'Em breve, um de nossos especialistas entrará em contato.\\n\\n' +
                  'Obrigado por escolher a E2 Soluções! 🚀';
    nextStage = 'completed';
    break;

  default:
    console.log('V40: UNKNOWN STATE:', normalizedStage);
    responseText = templates.greeting;
    nextStage = 'greeting';
    break;
}

console.log('V40 State Machine Complete');
console.log('  Response:', responseText.substring(0, 50) + '...');
console.log('  Next Stage:', nextStage);

// CRITICAL: Usar nomenclatura V34 Build Update Queries (snake_case)
const result = {
  // CRITICAL FIELDS - EXATA nomenclatura V34
  response_text: responseText,        // V34 Build Update Queries usa isso!
  next_stage: nextStage,
  current_state: normalizedStage,

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

  // Conversation data - IMPORTANTE: agora temos ID do banco!
  conversation_id: conversation.id || null,
  lead_id: phoneNumber,

  // Execution tracking
  v40_executed: true,
  v40_timestamp: new Date().toISOString()
};

console.log('V40 Final Result Keys:', Object.keys(result));
console.log('V40 CRITICAL: response_text =', result.response_text ? 'SET' : 'MISSING');
console.log('V40 CRITICAL: next_stage =', result.next_stage);
console.log('V40 CRITICAL: conversation_id =', result.conversation_id || 'NULL');
console.log('V40 STATE MACHINE - END');

return result;
"""

def update_workflow():
    """Update State Machine Logic in V34 workflow."""

    # Load V34 workflow
    base_path = Path(f"../n8n/workflows/{BASE_WORKFLOW}")
    if not base_path.exists():
        print(f"❌ Base workflow not found: {BASE_WORKFLOW}")
        return False

    with open(base_path, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    print(f"✅ Loaded base workflow: {BASE_WORKFLOW}")
    print(f"   Nodes count: {len(workflow.get('nodes', []))}")

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
    new_code = create_v40_state_machine_code()

    if 'parameters' in state_machine_node:
        if 'functionCode' in state_machine_node['parameters']:
            state_machine_node['parameters']['functionCode'] = new_code
            print("✅ Updated functionCode field")
        elif 'jsCode' in state_machine_node['parameters']:
            state_machine_node['parameters']['jsCode'] = new_code
            print("✅ Updated jsCode field")

    # Update workflow name
    workflow['name'] = "02 - AI Agent Conversation V40 (Complete Structure)"

    # Save as V40
    output_path = Path(f"../n8n/workflows/{OUTPUT_WORKFLOW}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print(f"✅ Created: {OUTPUT_WORKFLOW}")
    print(f"   Preserves ALL {len(workflow.get('nodes', []))} nodes from V34")
    return True

def main():
    """Main function to create V40."""

    print("=" * 60)
    print("V40 - COMPLETE STRUCTURE FIX")
    print("=" * 60)
    print()
    print("PROBLEMA V39:")
    print("  • State Machine Logic não recebia conversation do banco")
    print("  • currentStage voltava sempre para 'greeting'")
    print("  • Faltavam nodes: Get Conversation Details + Merge")
    print()
    print("SOLUÇÃO V40:")
    print("  • Usar V34 COMPLETO (tem todos os nodes necessários)")
    print("  • Apenas atualizar State Machine Logic")
    print("  • Manter nomenclatura response_text (snake_case)")
    print()

    success = update_workflow()

    if success:
        print()
        print("=" * 60)
        print("SUCCESS! V40 WORKFLOW CREATED")
        print("=" * 60)
        print()
        print("🎯 V40 TEM TUDO:")
        print("- ✅ Get Conversation Details (busca estado do banco)")
        print("- ✅ Merge Conversation Data (merge com input)")
        print("- ✅ State Machine Logic (response_text correto)")
        print("- ✅ Build Update Queries (V34 funcional)")
        print()
        print("📋 NEXT STEPS:")
        print()
        print("1. DEACTIVATE V39 workflow")
        print()
        print("2. IMPORT AND ACTIVATE V40:")
        print(f"   - Import: {OUTPUT_WORKFLOW}")
        print("   - Activate it")
        print()
        print("3. TEST:")
        print("   - Send 'oi' → Menu")
        print("   - Send '1' → Ask for name")
        print("   - Send 'Bruno Rosa' → ACCEPTED! (e persist no banco)")
        print("   - Send 'oi' novamente → Deve continuar de collect_phone")
        print()
        print("4. MONITOR:")
        print("   docker logs -f e2bot-n8n-dev 2>&1 | grep V40")
        print()
        print("✅ V40 = Estrutura Completa V34 + Nomenclatura Correta!")
        print()
        return True

    return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
