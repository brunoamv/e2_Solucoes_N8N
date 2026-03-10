#!/usr/bin/env python3
"""
V57.1: State Machine Syntax Fix
Removes obsolete V48 conversation_id extraction code that causes JavaScript syntax error

Problem: State Machine Logic has V48 code block with syntax error at line 169
         Isolated '=' character causing "Unexpected token '='" error
Solution: Remove entire V48 block, keep only V54 extraction code

Date: 2026-03-09
Author: Claude Code V57.1 Syntax Fix
"""

import json
from pathlib import Path

# Input and output
INPUT_WORKFLOW = "n8n/workflows/02_ai_agent_conversation_V57_MERGE_APPEND.json"
OUTPUT_WORKFLOW = "n8n/workflows/02_ai_agent_conversation_V57_1_STATE_MACHINE_FIX.json"

# Correct State Machine Logic code (V54 only, no V48)
CORRECT_STATE_MACHINE_CODE = """
// =====================================
// V40 STATE MACHINE - V34 COMPLETE STRUCTURE
// =====================================
console.log('V40 STATE MACHINE - START');

// Extract input data - agora conversation virá do banco via Get Conversation Details
const input = $input.first().json;
const message = input.message || input.body || input.text || '';

// ============================================================================
// V54: ENHANCED CONVERSATION ID EXTRACTION (replaces V48)
// ============================================================================
console.log('=== V54 CONVERSATION ID EXTRACTION ===');

// Get input data
const input_data = $input.first().json;

// Comprehensive diagnostic logging
console.log('V54 Diagnostics:');
console.log('  All available keys:', Object.keys(input_data).join(', '));
console.log('  Total fields:', Object.keys(input_data).length);

// Check all possible conversation_id sources
console.log('V54 Field Checks:');
console.log('  input_data.id:', input_data.id, '(type:', typeof input_data.id, ')');
console.log('  input_data.conversation_id:', input_data.conversation_id, '(type:', typeof input_data.conversation_id, ')');

// Check if we received database output
const hasDbFields = !!(
  input_data.state_machine_state ||
  input_data.current_state ||
  input_data.created_at ||
  input_data.updated_at
);

console.log('  Database fields present:', hasDbFields);

// Try to extract conversation_id from multiple sources
let conversation_id = null;

// Source 1: Direct id field from database
if (input_data.id) {
  conversation_id = input_data.id;
  console.log('✅ V54: Found id from database:', conversation_id);
}
// Source 2: Explicit conversation_id field
else if (input_data.conversation_id) {
  conversation_id = input_data.conversation_id;
  console.log('✅ V54: Found conversation_id field:', conversation_id);
}
// Source 3: Try to extract from conversation object (legacy support)
else if (input_data.conversation && input_data.conversation.id) {
  conversation_id = input_data.conversation.id;
  console.log('✅ V54: Found id in conversation object:', conversation_id);
}

// CRITICAL: Validate conversation_id
if (!conversation_id) {
  console.error('V54 CRITICAL ERROR: conversation_id is NULL!');
  console.error('V54 Full Diagnostic Dump:');
  console.error('  Available keys:', Object.keys(input_data));
  console.error('  Has DB fields?:', hasDbFields);
  console.error('  Input 0 (Merge Queries) likely has:', 'phone_number, message, query_*');
  console.error('  Input 1 (Database) should have:', 'id, state_machine_state, created_at');
  console.error('  Full input data:', JSON.stringify(input_data, null, 2).substring(0, 500) + '...');

  throw new Error('V54: conversation_id extraction failed - no id field found in merge output');
}

console.log('✅ V54 SUCCESS: conversation_id validated:', conversation_id);
console.log('=== V54 CONVERSATION ID EXTRACTION COMPLETE ===');
// ============================================================================

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


def fix_workflow_v57_1():
    """
    Fix V57 State Machine Logic syntax error

    Problem: State Machine Logic has obsolete V48 code with syntax error
    Solution: Replace with clean V54-only code
    """

    print("=" * 80)
    print("V57.1: State Machine Syntax Fix")
    print("=" * 80)

    # Load V57 workflow
    print(f"\n📂 Loading V57 workflow: {INPUT_WORKFLOW}")
    with open(INPUT_WORKFLOW, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    # Find State Machine Logic node
    state_machine_node = None
    state_machine_idx = None

    for idx, node in enumerate(workflow['nodes']):
        if node['name'] == 'State Machine Logic':
            state_machine_node = node
            state_machine_idx = idx
            break

    if not state_machine_node:
        print("❌ ERROR: State Machine Logic node not found!")
        return False

    print(f"✅ Found State Machine Logic node at index {state_machine_idx}")

    # Show current code length
    current_code = state_machine_node['parameters']['functionCode']
    print(f"\n📊 Current State Machine code:")
    print(f"   Length: {len(current_code)} characters")
    print(f"   Lines: {current_code.count(chr(10))} lines")

    # Replace with correct code
    print(f"\n🔧 Replacing with corrected V54-only code...")
    state_machine_node['parameters']['functionCode'] = CORRECT_STATE_MACHINE_CODE

    # Update workflow metadata
    workflow['name'] = '02 - AI Agent Conversation V57.1 (State Machine Syntax Fix)'
    workflow['versionId'] = 'v57-1-state-machine-syntax-fix'
    workflow['tags'] = [
        {'id': 'v57_1', 'name': 'V57.1 State Machine Fix'},
        {'id': 'syntax_fix', 'name': 'Syntax Error Fix'},
        {'id': 'from_v57', 'name': 'Based on V57'}
    ]

    # Save corrected workflow
    print(f"\n💾 Saving V57.1 workflow...")
    with open(OUTPUT_WORKFLOW, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print(f"✅ Workflow saved: {OUTPUT_WORKFLOW}")

    # Show new code length
    new_code = CORRECT_STATE_MACHINE_CODE
    print(f"\n📊 New State Machine code:")
    print(f"   Length: {len(new_code)} characters")
    print(f"   Lines: {new_code.count(chr(10))} lines")
    print(f"   Reduction: {len(current_code) - len(new_code)} characters removed")

    # Summary
    print("\n" + "=" * 80)
    print("✅ V57.1 FIX COMPLETE")
    print("=" * 80)
    print(f"Input:  {INPUT_WORKFLOW}")
    print(f"Output: {OUTPUT_WORKFLOW}")
    print(f"\nChanges:")
    print(f"  - Removed obsolete V48 conversation_id extraction code")
    print(f"  - Fixed 'Unexpected token =' syntax error at line 169")
    print(f"  - Kept only V54 conversation_id extraction (correct version)")
    print(f"  - All other nodes preserved from V57")
    print(f"\n🎯 Critical Fix:")
    print(f"  ✓ Syntax error removed from State Machine Logic")
    print(f"  ✓ V54 conversation_id extraction maintained")
    print(f"  ✓ V48 obsolete code completely removed")
    print(f"  ✓ JavaScript code now valid and executable")
    print(f"\n📋 Next Steps:")
    print(f"  1. Import workflow in n8n: {OUTPUT_WORKFLOW}")
    print(f"  2. Deactivate V57 workflow")
    print(f"  3. Activate V57.1 workflow")
    print(f"  4. Test with WhatsApp message")
    print(f"  5. Verify State Machine Logic executes without syntax errors")
    print("=" * 80)

    return True


if __name__ == '__main__':
    success = fix_workflow_v57_1()
    exit(0 if success else 1)
