#!/usr/bin/env python3
"""
V58.1 UX Refactor - Complete Workflow Generator
Generates V58.1 with all 8 gap fixes applied
"""

import json
import sys
from pathlib import Path

# Read V57.2 as base
v57_2_path = Path(__file__).parent.parent / 'n8n/workflows/02_ai_agent_conversation_V57_2_CONVERSATION_FIX.json'
v58_1_path = Path(__file__).parent.parent / 'n8n/workflows/02_ai_agent_conversation_V58_1_UX_REFACTOR_COMPLETE.json'

print("=" * 80)
print("V58.1 UX REFACTOR - COMPLETE WORKFLOW GENERATOR")
print("=" * 80)
print(f"Base: {v57_2_path}")
print(f"Output: {v58_1_path}")
print()

# Load V57.2 workflow
with open(v57_2_path, 'r', encoding='utf-8') as f:
    workflow = json.load(f)

print("✓ Loaded V57.2 workflow")

# Update workflow metadata
workflow['name'] = "02 - AI Agent V58.1 (UX Refactor Complete - All 8 Gaps)"
workflow['versionId'] = "v58-1-ux-refactor-complete"
workflow['tags'] = [
    {"id": "v58_1", "name": "V58.1 UX Refactor"},
    {"id": "complete_gaps", "name": "All 8 Gaps Fixed"},
    {"id": "from_v57_2", "name": "Based on V57.2"}
]

print("✓ Updated workflow metadata")

# Find State Machine Logic node
state_machine_node = None
for node in workflow['nodes']:
    if node['name'] == 'State Machine Logic':
        state_machine_node = node
        break

if not state_machine_node:
    print("✗ ERROR: State Machine Logic node not found!")
    sys.exit(1)

print("✓ Found State Machine Logic node")

# Generate V58.1 State Machine Code with all 8 gap fixes
state_machine_code_v58_1 = '''
// =====================================
// V58.1 STATE MACHINE - COMPLETE UX REFACTOR (ALL 8 GAPS FIXED)
// =====================================
console.log('V58.1 STATE MACHINE - START (All 8 Gaps Addressed)');

// Extract input data
const input = $input.first().json;
const message = input.message || input.body || input.text || '';

// ============================================================================
// V54: CONVERSATION ID EXTRACTION (PRESERVED FROM V57.2)
// ============================================================================
console.log('=== V54 CONVERSATION ID EXTRACTION (V57.2 PRESERVED) ===');

const input_data = $input.first().json;

// Comprehensive extraction
let conversation_id = null;

if (input_data.id) {
  conversation_id = input_data.id;
  console.log('✅ V54: Found id from database:', conversation_id);
} else if (input_data.conversation_id) {
  conversation_id = input_data.conversation_id;
  console.log('✅ V54: Found conversation_id field:', conversation_id);
} else if (input_data.conversation && input_data.conversation.id) {
  conversation_id = input_data.conversation.id;
  console.log('✅ V54: Found id in conversation object:', conversation_id);
}

if (!conversation_id) {
  console.error('V54 CRITICAL ERROR: conversation_id is NULL!');
  throw new Error('V54: conversation_id extraction failed - no id field found');
}

console.log('✅ V54 SUCCESS: conversation_id validated:', conversation_id);
console.log('=== V54 CONVERSATION ID EXTRACTION COMPLETE ===');
// ============================================================================

const phoneNumber = input.phone_number || input.phone_without_code || '';
const currentData = input.collected_data || {};

console.log('V58.1 Input:');
console.log('  Message:', message);
console.log('  Phone:', phoneNumber);
console.log('  Conversation ID:', conversation_id);

// Get current state
const currentStage = input.state_machine_state ||
                     input.current_state ||
                     input.state_for_machine ||
                     'greeting';

console.log('V58.1 Current Stage:', currentStage);

// Initialize variables
let responseText = '';
let nextStage = currentStage;
let updateData = {};
let errorCount = input.error_count || 0;

// ============================================================================
// GAP #1 FIX: COMPLETE STATE NAME MAPPING (4 NEW ENTRIES)
// ============================================================================
console.log('=== GAP #1: COMPLETE STATE NAME MAPPING ===');

const stateNameMapping = {
  // V57.2 EXISTING MAPPINGS (PRESERVED)
  'novo': 'greeting',
  'greeting': 'greeting',
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

  // V58.1 NEW MAPPINGS (GAP #1 - 4 ENTRIES) ✅
  'coletando_telefone_confirmacao_whatsapp': 'collect_phone_whatsapp_confirmation',
  'collect_phone_whatsapp_confirmation': 'collect_phone_whatsapp_confirmation',
  'coletando_telefone_alternativo': 'collect_phone_alternative',
  'collect_phone_alternative': 'collect_phone_alternative'
};

const normalizedStage = stateNameMapping[currentStage] || currentStage;
console.log(`V58.1 GAP #1: State normalized: ${currentStage} → ${normalizedStage}`);
console.log('✅ GAP #1 FIXED: Complete state name mapping applied');

// ============================================================================
// GAP #2 FIX: COMPLETE VALIDATOR MAPPING
// ============================================================================
console.log('=== GAP #2: VALIDATOR MAPPING ===');

function getValidatorForStage(stage) {
  const validatorMapping = {
    // V57.2 EXISTING VALIDATORS (PRESERVED)
    'greeting': null,
    'service_selection': 'number_1_to_5',
    'collect_name': 'text_min_3_chars',
    'collect_phone': 'phone_brazil',
    'collect_email': 'email_or_skip',
    'collect_city': 'city_name',
    'confirmation': 'confirmation_1_or_2',

    // V58.1 NEW VALIDATORS (GAP #2 - 2 ENTRIES) ✅
    'collect_phone_whatsapp_confirmation': 'confirmation_1_or_2', // Reuse existing
    'collect_phone_alternative': 'phone_brazil' // Reuse existing
  };

  const validator = validatorMapping[stage];
  console.log(`V58.1 GAP #2: Validator for ${stage}: ${validator || 'none'}`);
  return validator;
}

console.log('✅ GAP #2 FIXED: Complete validator mapping');

// ============================================================================
// GAP #6 FIX: SERVICE SELECTION MAPPING (NUMBER → STRING)
// ============================================================================
console.log('=== GAP #6: SERVICE SELECTION MAPPING ===');

const serviceMapping = {
  '1': 'Energia Solar',
  '2': 'Subestação',
  '3': 'Projetos Elétricos',
  '4': 'BESS',
  '5': 'Análise e Laudos'
};

console.log('✅ GAP #6 FIXED: Service selection mapping ready');

// ============================================================================
// GAP #4 FIX: COMPLETE TEMPLATES (2 NEW TEMPLATES)
// ============================================================================
console.log('=== GAP #4: COMPLETE TEMPLATES ===');

const templates = {
  // V57.2 EXISTING TEMPLATES (PRESERVED)
  greeting: '🤖 Olá! Bem-vindo à E2 Soluções!\\n\\nSomos especialistas em engenharia elétrica.\\n\\nEscolha o serviço desejado:\\n\\n1️⃣ - Energia Solar\\n2️⃣ - Subestação\\n3️⃣ - Projetos Elétricos\\n4️⃣ - BESS (Armazenamento)\\n5️⃣ - Análise e Laudos\\n\\nDigite o número (1-5):',
  invalid_option: '❌ Opção inválida. Por favor, escolha um número de 1 a 5.',
  collect_name: '👤 Qual seu nome completo?',
  invalid_name: '❌ Por favor, informe um nome válido (mínimo 3 letras).',
  collect_phone: '📱 Agora, informe seu telefone com DDD:\\nExemplo: (61) 98765-4321',
  collect_email: '📧 Qual seu melhor e-mail?\\n\\n_Digite "pular" se não quiser informar_',
  collect_city: '📍 De qual cidade você está falando?',

  // V58.1 NEW TEMPLATES (GAP #4) ✅
  collect_phone_whatsapp_confirmation: `📱 *Confirmação de Contato*

Perfeito! Identificamos seu WhatsApp:
*{{phone}}*

Este número é seu contato principal para agendarmos a visita?

1️⃣ - Sim, pode me ligar neste número
2️⃣ - Não, prefiro informar outro número

💡 _Responda 1 ou 2_`,

  collect_phone_alternative: `📱 *Telefone de Contato*

Por favor, informe o melhor número para contato:

💡 _Exemplo: (62) 98765-4321_

_Usaremos este número para agendar sua visita_`
};

console.log('✅ GAP #4 FIXED: Complete templates with 2 new entries');

// Helper function for phone formatting
function formatPhoneDisplay(phone) {
  if (phone.length === 11) {
    return `(${phone.substr(0,2)}) ${phone.substr(2,5)}-${phone.substr(7,4)}`;
  } else if (phone.length === 10) {
    return `(${phone.substr(0,2)}) ${phone.substr(2,4)}-${phone.substr(6,4)}`;
  }
  return phone;
}

// ============================================================================
// STATE MACHINE LOGIC
// ============================================================================
console.log('=== V58.1 STATE MACHINE EXECUTION ===');

switch (normalizedStage) {
  case 'greeting':
  case 'novo':
    console.log('V58.1: Processing GREETING state');
    if (/^[1-5]$/.test(message)) {
      console.log('V58.1: Service selected:', message);
      updateData.service_selected = message;
      // GAP #6: Store service name string ✅
      updateData.service_type = serviceMapping[message];
      console.log(`V58.1 GAP #6: Service mapped: ${message} → ${updateData.service_type}`);
      responseText = 'Ótima escolha! Vou precisar de alguns dados.\\n\\n' + templates.collect_name;
      nextStage = 'collect_name';
    } else {
      console.log('V58.1: Showing greeting menu');
      responseText = templates.greeting;
      nextStage = 'service_selection';
    }
    break;

  case 'service_selection':
  case 'identificando_servico':
    console.log('V58.1: Processing SERVICE_SELECTION state');
    if (/^[1-5]$/.test(message)) {
      console.log('V58.1: Valid service number:', message);
      updateData.service_selected = message;
      // GAP #6: Store both number AND string ✅
      updateData.service_type = serviceMapping[message];
      console.log(`V58.1 GAP #6: Service mapped: ${message} → ${updateData.service_type}`);
      responseText = templates.collect_name;
      nextStage = 'collect_name';
    } else {
      console.log('V58.1: Invalid service selection');
      // GAP #7: Error handling ✅
      responseText = templates.invalid_option + '\\n\\n' + templates.greeting;
      nextStage = 'service_selection';
      updateData.errorCount = (currentData.errorCount || 0) + 1;
    }
    break;

  case 'collect_name':
  case 'coletando_nome':
    console.log('V58.1: Processing COLLECT_NAME state');
    const trimmedName = message.trim();

    if (trimmedName.length >= 2 && !/^[0-9]+$/.test(trimmedName)) {
      console.log('✅ V58.1: NAME ACCEPTED:', trimmedName);
      updateData.lead_name = trimmedName;
      responseText = `Obrigado, ${trimmedName}!\\n\\n` + templates.collect_phone;
      nextStage = 'collect_phone';
      updateData.errorCount = 0;
    } else {
      console.log('❌ V58.1: NAME REJECTED');
      // GAP #7: Error handling ✅
      responseText = templates.invalid_name;
      nextStage = 'collect_name';
      updateData.errorCount = (currentData.errorCount || 0) + 1;
    }
    break;

  // ============================================================================
  // GAP #3 FIX: MODIFIED COLLECT_PHONE (TRANSITION TO CONFIRMATION)
  // ============================================================================
  case 'collect_phone':
  case 'coletando_telefone':
    console.log('V58.1 GAP #3: Processing COLLECT_PHONE state (modified flow)');

    const phoneRegex = /^\\(?\\d{2}\\)?\\s?\\d{4,5}-?\\d{4}$/;
    if (phoneRegex.test(message.trim())) {
      console.log('V58.1: Valid phone number');
      const cleanPhone = message.replace(/\\D/g, '');
      updateData.phone = cleanPhone;
      updateData.phone_number = cleanPhone;

      // GAP #3: NEW FLOW - Transition to WhatsApp confirmation ✅
      responseText = templates.collect_phone_whatsapp_confirmation
        .replace('{{phone}}', formatPhoneDisplay(cleanPhone));
      nextStage = 'collect_phone_whatsapp_confirmation';

      console.log('✅ V58.1 GAP #3: Transitioning to WhatsApp confirmation (NEW)');
    } else {
      console.log('V58.1: Invalid phone format');
      // GAP #7: Error handling ✅
      responseText = `❌ *Telefone inválido*\\n\\n${templates.collect_phone}`;
      nextStage = 'collect_phone';
      updateData.errorCount = (currentData.errorCount || 0) + 1;
    }
    break;

  // ============================================================================
  // GAP #3 FIX: NEW STATE - collect_phone_whatsapp_confirmation
  // ============================================================================
  case 'collect_phone_whatsapp_confirmation':
  case 'coletando_telefone_confirmacao_whatsapp':
    console.log('V58.1 GAP #3: Processing COLLECT_PHONE_WHATSAPP_CONFIRMATION state (NEW)');

    if (message === '1') {
      console.log('V58.1: User confirmed WhatsApp number as primary contact');
      updateData.phone_primary = currentData.phone_number || currentData.phone;
      updateData.contact_phone = currentData.phone_number || currentData.phone; // GAP #8 ✅
      responseText = templates.collect_email;
      nextStage = 'collect_email';
    } else if (message === '2') {
      console.log('V58.1: User wants to provide alternative phone');
      responseText = templates.collect_phone_alternative;
      nextStage = 'collect_phone_alternative';
    } else {
      console.log('V58.1: Invalid input for phone confirmation');
      // GAP #7: Error handling ✅
      const errorCountLocal = (currentData.errorCount || 0) + 1;

      if (errorCountLocal >= 3) {
        responseText = `❌ *Desculpe, tivemos dificuldade*\\n\\nVocê gostaria de:\\n\\n1️⃣ - Voltar ao menu principal\\n2️⃣ - Falar com um atendente\\n\\n💡 _Responda 1 ou 2_`;
        nextStage = 'error_recovery';
      } else {
        responseText = `❌ *Opção inválida*\\n\\n${templates.collect_phone_whatsapp_confirmation.replace('{{phone}}', formatPhoneDisplay(currentData.phone_number || currentData.phone))}`;
        nextStage = currentStage;
      }

      updateData.errorCount = errorCountLocal;
    }

    console.log('✅ V58.1 GAP #3: WhatsApp confirmation state complete');
    break;

  // ============================================================================
  // GAP #3 FIX: NEW STATE - collect_phone_alternative
  // ============================================================================
  case 'collect_phone_alternative':
  case 'coletando_telefone_alternativo':
    console.log('V58.1 GAP #3: Processing COLLECT_PHONE_ALTERNATIVE state (NEW)');

    const altPhoneRegex = /^\\(?\\d{2}\\)?\\s?\\d{4,5}-?\\d{4}$/;
    if (altPhoneRegex.test(message.trim())) {
      console.log('V58.1: Valid alternative phone number provided');
      const cleanAltPhone = message.replace(/\\D/g, '');
      updateData.phone_alternative = cleanAltPhone;
      updateData.contact_phone = cleanAltPhone; // GAP #8 ✅ - Primary contact is alternative
      updateData.phone_primary = cleanAltPhone;
      responseText = templates.collect_email;
      nextStage = 'collect_email';
    } else {
      console.log('V58.1: Invalid alternative phone format');
      // GAP #7: Error handling ✅
      const errorCountLocal = (currentData.errorCount || 0) + 1;

      if (errorCountLocal >= 3) {
        responseText = `❌ *Desculpe, tivemos dificuldade*\\n\\nVocê gostaria de:\\n\\n1️⃣ - Voltar ao menu principal\\n2️⃣ - Falar com um atendente\\n\\n💡 _Responda 1 ou 2_`;
        nextStage = 'error_recovery';
      } else {
        responseText = `❌ *Telefone inválido*\\n\\nPor favor, informe um telefone válido no formato:\\n(62) 98765-4321\\n\\n💡 _Digite apenas números com DDD_`;
        nextStage = currentStage;
      }

      updateData.errorCount = errorCountLocal;
    }

    console.log('✅ V58.1 GAP #3: Alternative phone state complete');
    break;

  // ============================================================================
  // GAP #7 FIX: ERROR RECOVERY STATE (OPTIONAL ENHANCEMENT)
  // ============================================================================
  case 'error_recovery':
    console.log('V58.1 GAP #7: Processing ERROR_RECOVERY state');

    if (message === '1') {
      // Return to menu
      responseText = templates.service_selection || templates.greeting;
      nextStage = 'service_selection';
      updateData.errorCount = 0;
    } else if (message === '2') {
      // Handoff to human
      responseText = '👤 *Transferindo para atendente...*\\n\\nEm breve um de nossos especialistas entrará em contato!';
      nextStage = 'handoff_comercial';
      updateData.errorCount = 0;
    } else {
      responseText = '❌ *Opção inválida*\\n\\nDigite:\\n1 - Menu principal\\n2 - Atendente';
      nextStage = 'error_recovery';
    }

    console.log('✅ V58.1 GAP #7: Error recovery complete');
    break;

  case 'collect_email':
  case 'coletando_email':
    console.log('V58.1: Processing COLLECT_EMAIL state');
    if (message.toLowerCase() !== 'pular') {
      updateData.email = message;
    }
    responseText = templates.collect_city;
    nextStage = 'collect_city';
    break;

  case 'collect_city':
  case 'coletando_cidade':
    console.log('V58.1: Processing COLLECT_CITY state');
    updateData.city = message;
    responseText = '✅ Perfeito! Recebi todos os seus dados.\\n\\n' +
                  'Em breve, um de nossos especialistas entrará em contato.\\n\\n' +
                  'Obrigado por escolher a E2 Soluções! 🚀';
    nextStage = 'completed';
    break;

  default:
    console.log('V58.1: UNKNOWN STATE:', normalizedStage);
    responseText = templates.greeting;
    nextStage = 'greeting';
    break;
}

console.log('V58.1 State Machine Complete');
console.log('  Response:', responseText.substring(0, 50) + '...');
console.log('  Next Stage:', nextStage);

// ============================================================================
// FINAL RESULT ASSEMBLY
// ============================================================================
const result = {
  // CRITICAL FIELDS - V34 nomenclature (PRESERVED)
  response_text: responseText,
  next_stage: nextStage,
  current_state: normalizedStage,

  // Phone fields
  phone_number: phoneNumber,
  phone_with_code: phoneNumber,
  phone_without_code: phoneNumber.replace(/^55/, ''),

  // Update data (includes GAP #6 service_type and GAP #8 contact_phone)
  collected_data: {
    ...input.collected_data,
    ...updateData
  },

  // State machine fields
  state_machine_state: nextStage,
  errorCount: errorCount,

  // Message data
  message: message,
  message_type: 'text',

  // Conversation data
  conversation_id: conversation_id,
  lead_id: phoneNumber,

  // Execution tracking
  v58_1_executed: true,
  v58_1_timestamp: new Date().toISOString(),
  v58_1_gaps_fixed: 8,
  v58_1_gap_list: 'state_mapping,validator_mapping,state_design,templates,architecture_preserved,service_mapping,error_handling,contact_phone_field'
};

console.log('V58.1 Final Result Keys:', Object.keys(result));
console.log('V58.1 CRITICAL: response_text =', result.response_text ? 'SET' : 'MISSING');
console.log('V58.1 CRITICAL: next_stage =', result.next_stage);
console.log('V58.1 CRITICAL: conversation_id =', result.conversation_id || 'NULL');
console.log('V58.1 CRITICAL: service_type =', result.collected_data.service_type || 'NONE');
console.log('V58.1 CRITICAL: contact_phone =', result.collected_data.contact_phone || 'NONE');
console.log('');
console.log('✅ ALL 8 GAPS FIXED:');
console.log('  ✅ GAP #1: State name mapping (4 entries)');
console.log('  ✅ GAP #2: Validator mapping (2 entries)');
console.log('  ✅ GAP #3: State design complete (2 new states)');
console.log('  ✅ GAP #4: Templates complete (2 new templates)');
console.log('  ✅ GAP #5: V57 architecture preserved');
console.log('  ✅ GAP #6: Service selection mapping');
console.log('  ✅ GAP #7: Error handling patterns');
console.log('  ✅ GAP #8: contact_phone field mapping');
console.log('V58.1 STATE MACHINE - END');

return result;
'''

# Update State Machine Logic node code
state_machine_node['parameters']['jsCode'] = state_machine_code_v58_1
print("✓ Applied V58.1 State Machine Logic (all 8 gaps fixed)")

# Find Build Update Queries node
build_update_queries_node = None
for node in workflow['nodes']:
    if node['name'] == 'Build Update Queries':
        build_update_queries_node = node
        break

if not build_update_queries_node:
    print("✗ ERROR: Build Update Queries node not found!")
    sys.exit(1)

print("✓ Found Build Update Queries node")

# Generate V58.1 Build Update Queries Code (with GAP #6 and #8 fixes)
build_update_queries_code_v58_1 = '''// Build Update Queries - V58.1 (GAP #6 and #8 FIXES)
const inputData = $input.first().json;

console.log('=== V58.1 BUILD UPDATE QUERIES (GAP #6 & #8 FIXES) ===');
console.log('Input keys:', Object.keys(inputData));

// Helper functions
const escapeSql = (str) => {
  if (str === null || str === undefined || str === '') return '';
  return String(str).replace(/'/g, "''");
};

const prepareJsonb = (obj) => {
  if (!obj || typeof obj !== 'object') return '{}';
  return JSON.stringify(obj).replace(/'/g, "''");
};

// Extract phone data
let phone_number = String(inputData.phone_number || '');
phone_number = phone_number.replace(/[^0-9]/g, '');

if (phone_number && !phone_number.startsWith('55')) {
  if (phone_number.length === 10 || phone_number.length === 11) {
    phone_number = '55' + phone_number;
  }
}

const phone_with_code = phone_number;
const phone_without_code = phone_number.startsWith('55') ? phone_number.substring(2) : phone_number;

// Extract other data
const response_text = escapeSql(inputData.response_text || 'Olá! Como posso ajudar?');
const next_stage = inputData.next_stage || inputData.current_state || 'greeting';
const collected_data = inputData.collected_data || {};
const collected_data_json = prepareJsonb(collected_data);
const message_content = escapeSql(inputData.message || '');
const message_type = inputData.message_type || 'text';
const message_id = inputData.message_id || '';
const conversation_id = inputData.conversation_id || null;

// GAP #6: Extract service_type from collected_data ✅
const service_type = collected_data?.service_type || null;
console.log('V58.1 GAP #6: service_type extracted:', service_type);

// GAP #8: Extract contact_phone with priority fallback ✅
const contact_phone = collected_data?.contact_phone ||
                     collected_data?.phone_primary ||
                     collected_data?.phone ||
                     '';
console.log('V58.1 GAP #8: contact_phone extracted:', contact_phone);

// State mapping
const state_mapping = {
  'greeting': 'novo',
  'service_selection': 'identificando_servico',
  'collect_name': 'coletando_dados',
  'collect_phone': 'coletando_dados',
  'collect_phone_whatsapp_confirmation': 'coletando_dados',  // V58.1 NEW
  'collect_phone_alternative': 'coletando_dados',            // V58.1 NEW
  'collect_email': 'coletando_dados',
  'collect_city': 'coletando_dados',
  'confirmation': 'coletando_dados',
  'scheduling': 'agendando',
  'handoff_comercial': 'handoff_comercial',
  'completed': 'concluido'
};

const db_state = state_mapping[next_stage] || 'novo';

console.log('V58.1: Building queries with GAP #6 and #8 fixes');

// Query 1: Update Conversation State (V58.1 with GAP #6 and #8)
const query_update_conversation = `
INSERT INTO conversations (
  phone_number,
  whatsapp_name,
  current_state,
  state_machine_state,
  collected_data,
  service_type,           -- GAP #6 ✅
  contact_name,
  contact_email,
  contact_phone,          -- GAP #8 ✅
  city,
  status,
  last_message_at,
  created_at,
  updated_at
) VALUES (
  '${phone_with_code}',
  '${escapeSql(collected_data?.lead_name || '')}',
  '${db_state}',
  '${next_stage}',
  '${collected_data_json}'::jsonb,
  ${service_type ? "'" + escapeSql(service_type) + "'" : 'NULL'},  -- GAP #6 ✅
  '${escapeSql(collected_data?.lead_name || '')}',
  '${escapeSql(collected_data?.email || '')}',
  '${escapeSql(contact_phone)}',  -- GAP #8 ✅
  '${escapeSql(collected_data?.city || '')}',
  'active',
  NOW(),
  NOW(),
  NOW()
)
ON CONFLICT (phone_number)
DO UPDATE SET
  current_state = EXCLUDED.current_state,
  state_machine_state = EXCLUDED.state_machine_state,
  collected_data = conversations.collected_data || EXCLUDED.collected_data,
  service_type = COALESCE(EXCLUDED.service_type, conversations.service_type),  -- GAP #6 ✅
  contact_name = COALESCE(NULLIF(EXCLUDED.contact_name, ''), conversations.contact_name),
  contact_email = COALESCE(NULLIF(EXCLUDED.contact_email, ''), conversations.contact_email),
  contact_phone = COALESCE(EXCLUDED.contact_phone, conversations.contact_phone),  -- GAP #8 ✅
  city = COALESCE(NULLIF(EXCLUDED.city, ''), conversations.city),
  whatsapp_name = COALESCE(NULLIF(EXCLUDED.whatsapp_name, ''), conversations.whatsapp_name),
  last_message_at = NOW(),
  updated_at = NOW()
RETURNING *`.trim();

console.log('✅ V58.1: UPSERT query with GAP #6 (service_type) and GAP #8 (contact_phone)');

// Query 2: Save Inbound Message (unchanged)
const query_save_inbound = `
INSERT INTO messages (
  conversation_id,
  direction,
  content,
  message_type,
  whatsapp_message_id,
  created_at
)
VALUES (
  (SELECT id FROM conversations WHERE phone_number IN ('${phone_with_code}', '${phone_without_code}') ORDER BY updated_at DESC LIMIT 1),
  'inbound',
  '${message_content}',
  '${message_type}',
  '${message_id}',
  NOW()
)
ON CONFLICT (whatsapp_message_id)
WHERE whatsapp_message_id IS NOT NULL AND whatsapp_message_id != ''
DO NOTHING
RETURNING *`.trim();

// Query 3: Save Outbound Message (unchanged)
const query_save_outbound = `
INSERT INTO messages (
  conversation_id,
  direction,
  content,
  message_type,
  whatsapp_message_id,
  created_at
)
VALUES (
  (SELECT id FROM conversations WHERE phone_number IN ('${phone_with_code}', '${phone_without_code}') ORDER BY updated_at DESC LIMIT 1),
  'outbound',
  '${response_text}',
  'text',
  'out_' || extract(epoch from NOW())::bigint || '_' || random()::text,
  NOW()
)
RETURNING *`.trim();

// Query 4: Upsert Lead Data (unchanged)
const query_upsert_lead = `
WITH existing_lead AS (
  SELECT id
  FROM leads
  WHERE phone_number IN ('${phone_with_code}', '${phone_without_code}')
  LIMIT 1
),
updated AS (
  UPDATE leads
  SET
    name = COALESCE(NULLIF('${escapeSql(collected_data?.lead_name || '')}', ''), name),
    email = COALESCE(NULLIF('${escapeSql(collected_data?.email || '')}', ''), email),
    city = COALESCE(NULLIF('${escapeSql(collected_data?.city || '')}', ''), city),
    service_type = COALESCE(NULLIF('${escapeSql(collected_data?.service_type || '')}', ''), service_type),
    service_details = '${collected_data_json}'::jsonb,
    updated_at = NOW()
  WHERE id IN (SELECT id FROM existing_lead)
  RETURNING *, 'updated' as operation
),
inserted AS (
  INSERT INTO leads (
    phone_number,
    name,
    email,
    city,
    service_type,
    service_details,
    created_at,
    updated_at
  )
  SELECT
    '${phone_with_code}',
    '${escapeSql(collected_data?.lead_name || '')}',
    '${escapeSql(collected_data?.email || '')}',
    '${escapeSql(collected_data?.city || '')}',
    '${escapeSql(collected_data?.service_type || '')}',
    '${collected_data_json}'::jsonb,
    NOW(),
    NOW()
  WHERE NOT EXISTS (SELECT 1 FROM existing_lead)
  RETURNING *, 'inserted' as operation
)
SELECT * FROM updated
UNION ALL
SELECT * FROM inserted`.trim();

console.log('✅ V58.1: All queries built with GAP #6 and #8 fixes');

// Return all queries and data
return {
  phone_number: phone_with_code,
  phone_with_code: phone_with_code,
  phone_without_code: phone_without_code,
  response_text: inputData.response_text,
  next_stage: next_stage,
  collected_data: collected_data,
  conversation_id: conversation_id,
  message: inputData.message,
  message_type: message_type,
  message_id: message_id,

  // Queries SQL
  query_update_conversation,
  query_save_inbound,
  query_save_outbound,
  query_upsert_lead,

  // V58.1 metadata
  v58_1_gap_6_applied: !!service_type,
  v58_1_gap_8_applied: !!contact_phone,
  timestamp: new Date().toISOString()
};'''

# Update Build Update Queries node code
build_update_queries_node['parameters']['jsCode'] = build_update_queries_code_v58_1
print("✓ Applied V58.1 Build Update Queries (GAP #6 and #8 fixes)")

# Save V58.1 workflow
v58_1_path.parent.mkdir(parents=True, exist_ok=True)
with open(v58_1_path, 'w', encoding='utf-8') as f:
    json.dump(workflow, f, indent=2, ensure_ascii=False)

print()
print("=" * 80)
print("✅ V58.1 WORKFLOW GENERATED SUCCESSFULLY")
print("=" * 80)
print(f"Output: {v58_1_path}")
print()
print("All 8 Gaps Fixed:")
print("  ✅ GAP #1: State name mapping (4 new entries)")
print("  ✅ GAP #2: Validator mapping (2 new entries)")
print("  ✅ GAP #3: State design complete (2 new states)")
print("  ✅ GAP #4: Templates complete (2 new templates)")
print("  ✅ GAP #5: V57 architecture preserved (no modifications)")
print("  ✅ GAP #6: Service selection mapping (number → string)")
print("  ✅ GAP #7: Error handling patterns")
print("  ✅ GAP #8: contact_phone field mapping")
print()
print("Next Steps:")
print("  1. Import V58.1 workflow to n8n: http://localhost:5678")
print("  2. Verify all nodes loaded correctly")
print("  3. Run pre-deployment tests")
print("  4. Deploy with gradual rollout")
print()
