#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
V37 WHATSAPP STRUCTURE FIX - Based on Working V34 Pattern
===========================================================
Uses the exact return structure that worked in previous versions.

PROBLEM: V36 still getting "Bad request" in Send WhatsApp Response
SOLUTION: Use exact structure from working versions (single items pass-through)
"""

import json
import sys
from pathlib import Path

# Use V36 as base
BASE_WORKFLOW = "02_ai_agent_conversation_V36_MINIMAL_FIXED.json"
FALLBACK_WORKFLOW = "02_ai_agent_conversation_V34_NAME_VALIDATION.json"
OUTPUT_MINIMAL = "02_ai_agent_conversation_V37_MINIMAL_PASSTHROUGH.json"
OUTPUT_FULL = "02_ai_agent_conversation_V37_FULL_WORKING.json"

def create_v37_minimal_code():
    """
    V37 Minimal - Ultra simple passthrough to test WhatsApp sending.
    This passes the original items through with minimal modification.
    """
    return """
// =====================================
// V37 MINIMAL - PASSTHROUGH TEST
// =====================================
console.log('################################');
console.log('# V37 MINIMAL PASSTHROUGH      #');
console.log('################################');

// Log input structure
const input = items[0].json;
console.log('V37 Input Keys:', Object.keys(input));
console.log('V37 Phone Number:', input.phone_number || 'NOT FOUND');
console.log('V37 Message:', input.message || 'NOT FOUND');

// CRITICAL: Pass through the original structure with minimal changes
// The Send WhatsApp Response expects the data in items[0].json format
// We just add the response text

const result = {
  ...input,  // Keep ALL original fields
  responseText: 'V37 TEST: Mensagem recebida com sucesso!',  // Add response
  // Keep original phone fields
  phone_number: input.phone_number || input.phone_without_code || '',
  phone_with_code: input.phone_with_code || input.phone_number || ''
};

console.log('V37 Output Keys:', Object.keys(result));
console.log('V37 PASSTHROUGH COMPLETE');

// Return as items array - exactly as n8n expects
return items.map(item => ({
  json: result
}));
"""

def create_v37_full_code():
    """
    V37 Full - Complete implementation using passthrough pattern.
    """
    return """
// =====================================
// V37 FULL - WORKING IMPLEMENTATION
// =====================================
console.log('################################');
console.log('# V37 FULL VERSION EXECUTING   #');
console.log('################################');

// Get input - preserve original structure
const input = items[0].json;
console.log('V37 Input received with', Object.keys(input).length, 'fields');

// Extract key fields with multiple fallbacks
const message = input.message || input.content || input.text || '';
const phoneNumber = input.phone_number || input.phone_without_code || '';
const conversation = input.conversation || {};

console.log('V37 Processing:');
console.log('  Message:', message);
console.log('  Phone:', phoneNumber);

// Get current state
const currentStage = conversation.state_machine_state ||
                     conversation.current_state ||
                     conversation.state_for_machine ||
                     'greeting';

console.log('  Current Stage:', currentStage);

// Initialize response variables
let responseText = '';
let nextStage = currentStage;
let updateData = {};

// Normalize stage names (handle DB inconsistencies)
const stageMapping = {
  'novo': 'greeting',
  'identificando_servico': 'service_selection',
  'coletando_nome': 'collect_name',
  'coletando_telefone': 'collect_phone',
  'coletando_email': 'collect_email',
  'coletando_cidade': 'collect_city',
  'confirmacao': 'confirmation'
};

const normalizedStage = stageMapping[currentStage] || currentStage;
console.log('  Normalized Stage:', normalizedStage);

// State machine implementation
switch(normalizedStage) {
  case 'greeting':
  case 'novo':
    console.log('V37: Processing GREETING');
    responseText = '🤖 Olá! Bem-vindo à E2 Soluções!\\n\\n' +
                  'Somos especialistas em engenharia elétrica.\\n\\n' +
                  'Escolha o serviço desejado:\\n\\n' +
                  '1️⃣ - Energia Solar\\n' +
                  '2️⃣ - Subestação\\n' +
                  '3️⃣ - Projetos Elétricos\\n' +
                  '4️⃣ - BESS (Armazenamento)\\n' +
                  '5️⃣ - Análise e Laudos\\n\\n' +
                  'Digite o número (1-5):';
    nextStage = 'service_selection';
    break;

  case 'service_selection':
    console.log('V37: Processing SERVICE_SELECTION');
    if (/^[1-5]$/.test(message)) {
      console.log('  Valid service:', message);
      updateData.service_selected = message;
      responseText = '✅ Ótima escolha!\\n\\n' +
                    'Para prosseguir, vou precisar de alguns dados.\\n\\n' +
                    '👤 Por favor, informe seu nome completo:';
      nextStage = 'collect_name';
    } else {
      responseText = '⚠️ Por favor, digite apenas o número da opção (1 a 5).';
      nextStage = 'service_selection';
    }
    break;

  case 'collect_name':
    console.log('################################');
    console.log('# V37 COLLECT_NAME STATE       #');
    console.log('# Message:', message);
    console.log('################################');

    const trimmedName = message.trim();
    // Simple validation: at least 2 chars, not just numbers
    if (trimmedName.length >= 2 && !/^[0-9]+$/.test(trimmedName)) {
      console.log('✅ V37: NAME ACCEPTED:', trimmedName);
      updateData.lead_name = trimmedName;
      responseText = 'Obrigado, ' + trimmedName + '!\\n\\n' +
                    '📱 Agora, por favor, informe seu telefone com DDD:\\n' +
                    'Exemplo: (61) 98765-4321';
      nextStage = 'collect_phone';
    } else {
      console.log('❌ V37: NAME REJECTED');
      responseText = '❌ Por favor, informe um nome válido.\\n' +
                    'Digite seu nome completo:';
      nextStage = 'collect_name';
    }
    break;

  case 'collect_phone':
    console.log('V37: Processing COLLECT_PHONE');
    updateData.phone = message;
    responseText = '📧 Qual seu melhor e-mail?\\n\\n' +
                  '_Digite "pular" se preferir não informar_';
    nextStage = 'collect_email';
    break;

  case 'collect_email':
    console.log('V37: Processing COLLECT_EMAIL');
    if (message.toLowerCase() !== 'pular') {
      updateData.email = message;
    }
    responseText = '📍 De qual cidade você está falando?';
    nextStage = 'collect_city';
    break;

  case 'collect_city':
    console.log('V37: Processing COLLECT_CITY');
    updateData.city = message;
    responseText = '✅ Perfeito! Recebi todos os seus dados.\\n\\n' +
                  'Em breve, um de nossos especialistas entrará em contato.\\n\\n' +
                  'Obrigado por escolher a E2 Soluções! 🚀';
    nextStage = 'completed';
    break;

  default:
    console.log('V37: UNKNOWN STATE:', normalizedStage);
    responseText = '🔄 Vamos recomeçar...\\n\\n' +
                  'Digite "oi" para iniciar.';
    nextStage = 'greeting';
    break;
}

console.log('V37 State Machine Result:');
console.log('  Response (preview):', responseText.substring(0, 50));
console.log('  Next Stage:', nextStage);

// CRITICAL: Build response preserving original structure
// Pass through all original fields and add our response
const result = {
  ...input,  // Keep ALL original fields from input

  // Override/add specific fields for response
  responseText: responseText,  // The actual WhatsApp message

  // Ensure phone fields are present
  phone_number: phoneNumber,
  phone_with_code: input.phone_with_code || phoneNumber,
  phone_without_code: input.phone_without_code || phoneNumber,

  // State machine updates
  nextStage: nextStage,
  currentStage: normalizedStage,
  state_machine_state: nextStage,
  updateData: updateData,

  // Execution tracking
  v37_executed: true,
  v37_timestamp: new Date().toISOString()
};

console.log('V37 Final Output has', Object.keys(result).length, 'fields');
console.log('V37 FULL EXECUTION COMPLETE');

// Return preserving items structure
return items.map(item => ({
  json: result
}));
"""

def create_workflow(base_path, code, output_name, workflow_name):
    """Create a workflow with the given code."""

    if not base_path.exists():
        print(f"❌ Base workflow not found: {base_path}")
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
        print(f"❌ State Machine Logic node not found")
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
    """Create both V37 versions."""

    print("=" * 60)
    print("V37 WHATSAPP STRUCTURE FIX")
    print("=" * 60)
    print()
    print("Using passthrough pattern from working versions...")
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

    # Create V37 MINIMAL
    print("Creating V37 MINIMAL (Passthrough)...")
    success1 = create_workflow(
        base_path,
        create_v37_minimal_code(),
        OUTPUT_MINIMAL,
        "02 - V37 MINIMAL PASSTHROUGH"
    )

    # Create V37 FULL
    print("Creating V37 FULL VERSION...")
    success2 = create_workflow(
        base_path,
        create_v37_full_code(),
        OUTPUT_FULL,
        "02 - V37 FULL WORKING"
    )

    if success1 and success2:
        print()
        print("=" * 60)
        print("SUCCESS! V37 WORKFLOWS CREATED")
        print("=" * 60)
        print()
        print("🎯 KEY DIFFERENCE IN V37:")
        print("- Uses passthrough pattern (...input)")
        print("- Preserves ALL original fields")
        print("- Returns items.map() structure")
        print()
        print("📋 NEXT STEPS:")
        print()
        print("1. DEACTIVATE V36 workflows")
        print()
        print("2. TEST V37 MINIMAL:")
        print(f"   - Import {OUTPUT_MINIMAL}")
        print("   - Activate it")
        print("   - Send any message")
        print("   - Should see WhatsApp response WITHOUT error!")
        print()
        print("3. IF MINIMAL WORKS, TEST FULL:")
        print(f"   - Import {OUTPUT_FULL}")
        print("   - Test: Send '1' → Menu appears")
        print("   - Test: Send 'Bruno Rosa' → ACCEPTED!")
        print()
        print("4. MONITOR:")
        print("   docker logs -f e2bot-n8n-dev 2>&1 | grep V37")
        print("   docker logs -f e2bot-evolution-dev 2>&1 | grep sendMessage")
        print()
        return True

    return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)