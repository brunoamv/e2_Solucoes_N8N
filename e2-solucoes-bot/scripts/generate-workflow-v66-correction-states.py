#!/usr/bin/env python3
"""
V66 Correction States Complete Implementation Generator

Objetivo: Adicionar 5 estados de correção + 11 templates + UPDATE queries
Base: V65 UX Complete Fix (templates-only approach)
Approach: Extend state machine with correction logic preserving V65 stability

Autor: Claude Code
Data: 2026-03-11
"""

import json
import re
from datetime import datetime
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent.parent
V65_PATH = BASE_DIR / "n8n/workflows/02_ai_agent_conversation_V65_UX_COMPLETE_FIX.json"
V66_PATH = BASE_DIR / "n8n/workflows/02_ai_agent_conversation_V66_CORRECTION_STATES_COMPLETE.json"

print("=" * 80)
print("V66 Correction States Generator - COMPLETE IMPLEMENTATION")
print("=" * 80)
print()

# Load V65
print(f"📂 Loading V65: {V65_PATH}")
with open(V65_PATH, 'r', encoding='utf-8') as f:
    workflow = json.load(f)

print(f"✅ Loaded: {len(workflow['nodes'])} nodes")
print()

# Find State Machine Logic node
print("🔍 Finding State Machine Logic node...")
state_machine_node = None
state_machine_index = None

for i, node in enumerate(workflow['nodes']):
    if node.get('name') == 'State Machine Logic':
        state_machine_node = node
        state_machine_index = i
        break

if not state_machine_node:
    print("❌ ERRO: State Machine Logic node not found!")
    exit(1)

print(f"✅ Found at index {state_machine_index}")
print()

# Get current code
code = state_machine_node['parameters']['functionCode']
print(f"📝 Current code size: {len(code)} chars")
print()

# Build V66 templates object (25 templates - 14 from V65 + 11 new)
print("🔨 Building V66 templates object (25 templates)...")

new_templates_js = '''const templates = {
  // 1. GREETING E MENU PRINCIPAL (2)
  "greeting": `🤖 *Olá! Bem-vindo à E2 Soluções!*

Somos especialistas em engenharia elétrica com 15+ anos de experiência.

*Qual serviço você precisa?*

☀️ *1 - Energia Solar*
   Projetos fotovoltaicos residenciais e comerciais

⚡ *2 - Subestação*
   Reforma, manutenção e construção

📐 *3 - Projetos Elétricos*
   Adequações e laudos técnicos

🔋 *4 - BESS (Armazenamento)*
   Sistemas de armazenamento de energia

📊 *5 - Análise e Laudos*
   Qualidade de energia e eficiência

_Digite o número do serviço (1-5):_`,

  "invalid_service": `❌ *Opção inválida*

Por favor, escolha uma das opções disponíveis:

1️⃣ - Energia Solar
2️⃣ - Subestações
3️⃣ - Projetos Elétricos
4️⃣ - BESS
5️⃣ - Análise de Consumo

_Digite apenas o número (1 a 5)_`,

  // 2. COLETA DE NOME (2)
  "service_acknowledged": `✅ *Perfeito!*

👤 *Qual é o seu nome completo?*

💡 _Exemplo: Maria Silva Santos_
_Usaremos para personalizar seu atendimento_`,

  "invalid_name": `❌ *Nome inválido*

Por favor, informe seu nome completo (mínimo 2 letras).

_Não use apenas números ou caracteres especiais._`,

  // 3. COLETA DE TELEFONE (3)
  "phone_whatsapp_confirm": `📱 *Ótimo, {{name}}!*

Vi que você está me enviando mensagens pelo número:
*{{whatsapp_number}}*

Este é o melhor número para contato?

1️⃣ *Sim, pode usar este*
2️⃣ *Não, vou informar outro*

💡 _Digite 1 ou 2_`,

  "phone_alternative": `📱 *Qual número prefere para contato, {{name}}?*

Por favor, informe com DDD:

💡 _Exemplo: (62) 98765-4321_
_Usaremos este número para agendarmos sua visita técnica_`,

  "invalid_phone": `❌ *Telefone inválido*

Por favor, informe um telefone válido com DDD.

💡 _Exemplos aceitos:_
• (62) 98765-4321
• 62987654321
• 6298765-4321

_Use apenas números, espaços, parênteses e hífen_`,

  // 4. COLETA DE EMAIL (2)
  "email_request": `📧 *Qual é o seu e-mail, {{name}}?*

💡 _Exemplo: maria.silva@email.com_

Se preferir não informar, digite *pular*
_O e-mail nos ajuda a enviar documentação técnica e propostas_`,

  "invalid_email": `❌ *E-mail inválido*

Por favor, informe um e-mail válido.

*Exemplos:*
• maria@gmail.com
• joao.silva@empresa.com.br

Ou digite *pular* se não quiser informar.`,

  // 5. COLETA DE CIDADE (2)
  "city_request": `📍 *Em qual cidade você está, {{name}}?*

💡 _Exemplo: Goiânia - GO_
_Precisamos saber para agendar a visita técnica com nossa equipe local_`,

  "invalid_city": `❌ *Cidade inválida*

Por favor, informe uma cidade válida (mínimo 2 letras).

_Exemplo: Goiânia, Brasília, Anápolis..._`,

  // 6. CONFIRMAÇÃO - 3 OPÇÕES (2)
  "confirmation": `✅ *Perfeito! Veja o resumo dos seus dados:*

👤 *Nome:* {{name}}
📱 *Telefone:* {{phone}}
📧 *E-mail:* {{email}}
📍 *Cidade:* {{city}}
{{service_emoji}} *Serviço:* {{service_name}}

---

Deseja agendar uma visita técnica gratuita para avaliarmos seu projeto?

1️⃣ *Sim, quero agendar*
2️⃣ *Não agora, falar com uma pessoa*
3️⃣ *Meus dados estão errados, quero corrigir*`,

  "invalid_confirmation": `❌ *Opção inválida*

Por favor, escolha uma das opções:

1️⃣ *Sim, quero agendar*
2️⃣ *Não agora, falar com uma pessoa*
3️⃣ *Meus dados estão errados, quero corrigir*`,

  // 7. REDIRECIONAMENTOS (2)
  "scheduling_redirect": `⏰ *Agendamento de Visita Técnica*

Perfeito! Agora vamos agendar sua visita técnica.

Nossa equipe entrará em contato em breve para:
✅ Confirmar melhor data e horário
✅ Esclarecer detalhes técnicos
✅ Preparar documentação necessária

🕐 *Horário de atendimento:*
Segunda a Sexta: 8h às 18h
Sábado: 8h às 12h

📱 *Contato direto:* (62) 3092-2900

_Obrigado por escolher a E2 Soluções!_`,

  "handoff_comercial": `👔 *Transferência para Atendimento Comercial*

Obrigado pelas informações!

Nossa equipe comercial especializada entrará em contato para:
✅ Apresentar soluções personalizadas
✅ Elaborar proposta técnica-comercial
✅ Esclarecer dúvidas sobre investimento

🕐 *Retorno em:* até 24 horas úteis

📱 *Contato direto:* (62) 3092-2900

_Aguarde nosso retorno!_`,

  // 8. V66 CORRECTION FLOW TEMPLATES (11 NEW)
  "ask_correction_field": `🔧 *Sem problemas! Vamos corrigir.*

Qual dado você quer alterar?

1️⃣ *Nome* (atual: {{name}})
2️⃣ *Telefone* (atual: {{phone}})
3️⃣ *E-mail* (atual: {{email}})
4️⃣ *Cidade* (atual: {{city}})

_Digite o número do campo que deseja corrigir:_`,

  "invalid_correction_field": `❌ *Opção inválida*

Por favor, escolha um número de 1 a 4 para o campo que deseja corrigir.

1️⃣ - Nome
2️⃣ - Telefone
3️⃣ - E-mail
4️⃣ - Cidade`,

  "correction_prompt_name": `👤 *Corrigindo Nome*

Nome atual: *{{name}}*

Digite o nome correto:
_Exemplo: Maria Silva Santos_`,

  "correction_prompt_phone": `📱 *Corrigindo Telefone*

Telefone atual: *{{phone}}*

Digite o telefone correto com DDD:
_Exemplo: (62) 98765-4321_`,

  "correction_prompt_email": `📧 *Corrigindo E-mail*

E-mail atual: *{{email}}*

Digite o e-mail correto:
_Exemplo: maria.silva@email.com_`,

  "correction_prompt_city": `📍 *Corrigindo Cidade*

Cidade atual: *{{city}}*

Digite a cidade correta:
_Exemplo: Goiânia - GO_`,

  "correction_success_name": `✅ *Nome corrigido com sucesso!*

Nome anterior: {{old_value}}
Nome novo: *{{new_value}}*

Voltando para a confirmação...`,

  "correction_success_phone": `✅ *Telefone corrigido com sucesso!*

Telefone anterior: {{old_value}}
Telefone novo: *{{new_value}}*

Voltando para a confirmação...`,

  "correction_success_email": `✅ *E-mail corrigido com sucesso!*

E-mail anterior: {{old_value}}
E-mail novo: *{{new_value}}*

Voltando para a confirmação...`,

  "correction_success_city": `✅ *Cidade corrigida com sucesso!*

Cidade anterior: {{old_value}}
Cidade nova: *{{new_value}}*

Voltando para a confirmação...`
};'''

print("✅ V66 templates object built (25 templates: 14 base + 11 correction)")
print()

# Replace templates in code
print("🔄 Replacing templates object in State Machine Logic...")

pattern = r'const templates = \{.*?\n\};'
match = re.search(pattern, code, re.DOTALL)

if not match:
    print("❌ ERRO: Could not find templates object!")
    exit(1)

start, end = match.span()
print(f"   Found templates at position {start}:{end} ({end - start} chars)")

# Replace templates
code_with_new_templates = code[:start] + new_templates_js + code[end:]

print(f"✅ Templates replaced!")
print(f"   Old size: {end - start} chars")
print(f"   New size: {len(new_templates_js)} chars")
print()

# Add V66 correction states to switch statement
print("🔨 Adding V66 correction states to switch statement...")

# Find confirmation case
confirmation_pattern = r"(case 'confirmation':.*?break;)"
confirmation_match = re.search(confirmation_pattern, code_with_new_templates, re.DOTALL)

if not confirmation_match:
    print("❌ ERRO: Could not find confirmation case!")
    exit(1)

# Extract confirmation case
confirmation_case = confirmation_match.group(1)

# Build enhanced confirmation case with V66 option 3 implementation
enhanced_confirmation = """case 'confirmation':
    console.log('V66: Processing CONFIRMATION state');

    // Option 1: Agendar visita
    if (message === '1') {
      const serviceSelected = currentData.service_selected || '1';
      if (serviceSelected === '1' || serviceSelected === '3') {
        responseText = templates.scheduling_redirect;
        nextStage = 'scheduling';
        updateData.status = 'scheduling';
      } else {
        responseText = templates.handoff_comercial;
        nextStage = 'handoff_comercial';
        updateData.status = 'handoff';
      }
    }
    // Option 2: Falar com pessoa
    else if (message === '2') {
      responseText = templates.handoff_comercial;
      nextStage = 'handoff_comercial';
      updateData.status = 'handoff';
    }
    // Option 3: Corrigir dados ← V66 NEW FUNCTIONALITY
    else if (message === '3') {
      console.log('V66: User chose correction option');
      const leadName = currentData.lead_name || 'não informado';
      const phoneNumber = currentData.contact_phone || currentData.phone_number || 'não informado';
      const email = currentData.email || 'não informado';
      const city = currentData.city || 'não informado';

      responseText = templates.ask_correction_field
        .replace('{{name}}', leadName)
        .replace('{{phone}}', formatPhoneDisplay(phoneNumber))
        .replace('{{email}}', email)
        .replace('{{city}}', city);

      nextStage = 'correction_field_selection';
      updateData.correction_in_progress = true;
      updateData.correction_attempts = (currentData.correction_attempts || 0) + 1;

      // Loop protection - max 5 corrections
      if (updateData.correction_attempts > 5) {
        console.warn('V66: Maximum correction attempts reached');
        responseText = `⚠️ *Você já corrigiu dados 5 vezes.*\\n\\n` +
                      `Para sua segurança, vou encaminhar para nossa equipe.\\n\\n` +
                      templates.handoff_comercial;
        nextStage = 'handoff_comercial';
        updateData.status = 'handoff';
        updateData.correction_in_progress = false;
      }
    }
    else {
      responseText = templates.invalid_confirmation;
      nextStage = 'confirmation';
    }
    break;"""

# Replace confirmation case
code_with_corrections = code_with_new_templates.replace(confirmation_case, enhanced_confirmation)

print("✅ Enhanced confirmation case with V66 option 3 logic")
print()

# Add 5 new correction states after confirmation
print("🔨 Adding 5 new correction states...")

# Find where to insert (after confirmation case)
insertion_point = code_with_corrections.find(enhanced_confirmation) + len(enhanced_confirmation)

correction_states = """

    // V66 CORRECTION STATES (5 NEW)

    case 'correction_field_selection':
      console.log('V66: Processing CORRECTION_FIELD_SELECTION state');

      if (/^[1-4]$/.test(message)) {
        const selectedField = message;
        console.log('V66: User wants to correct field:', selectedField);

        const fieldMapping = {
          '1': { db_field: 'lead_name', jsonb_key: 'lead_name', display: 'Nome' },
          '2': { db_field: 'contact_phone', jsonb_key: 'contact_phone', display: 'Telefone' },
          '3': { db_field: 'email', jsonb_key: 'email', display: 'E-mail' },
          '4': { db_field: 'city', jsonb_key: 'city', display: 'Cidade' }
        };

        const currentName = currentData.lead_name || 'não informado';
        const currentPhone = formatPhoneDisplay(currentData.contact_phone || currentData.phone_number || '');
        const currentEmail = currentData.email || 'não informado';
        const currentCity = currentData.city || 'não informado';

        updateData.correcting_field = selectedField;
        updateData.correction_field_name = fieldMapping[selectedField].display;

        switch (selectedField) {
          case '1': // Name
            responseText = templates.correction_prompt_name.replace('{{name}}', currentName);
            nextStage = 'correction_name';
            break;
          case '2': // Phone
            responseText = templates.correction_prompt_phone.replace('{{phone}}', currentPhone);
            nextStage = 'correction_phone';
            break;
          case '3': // Email
            responseText = templates.correction_prompt_email.replace('{{email}}', currentEmail);
            nextStage = 'correction_email';
            break;
          case '4': // City
            responseText = templates.correction_prompt_city.replace('{{city}}', currentCity);
            nextStage = 'correction_city';
            break;
        }
      } else {
        console.log('V66: Invalid correction field selection');
        responseText = templates.invalid_correction_field;
        nextStage = 'correction_field_selection';
      }
      break;

    case 'correction_name':
      console.log('V66: Processing CORRECTION_NAME state');

      const trimmedName = message.trim();

      if (trimmedName.length >= 2 && !/^[0-9]+$/.test(trimmedName)) {
        console.log('V66: Valid corrected name:', trimmedName);
        const oldName = currentData.lead_name || 'não informado';

        updateData.lead_name = trimmedName;
        updateData.contact_name = trimmedName;
        updateData.correction_old_value = oldName;
        updateData.correction_new_value = trimmedName;
        updateData.needs_db_update = true;
        updateData.update_field = 'lead_name';

        responseText = templates.correction_success_name
          .replace('{{old_value}}', oldName)
          .replace('{{new_value}}', trimmedName);

        nextStage = 'confirmation';
        updateData.correction_in_progress = false;
      } else {
        console.log('V66: Invalid corrected name format');
        responseText = `${templates.invalid_name}\\n\\n${templates.correction_prompt_name.replace('{{name}}', currentData.lead_name || '')}`;
        nextStage = 'correction_name';
      }
      break;

    case 'correction_phone':
      console.log('V66: Processing CORRECTION_PHONE state');

      const cleanPhone = message.replace(/[^0-9]/g, '');

      if (cleanPhone.length >= 10 && cleanPhone.length <= 13) {
        console.log('V66: Valid corrected phone:', cleanPhone);
        const oldPhone = formatPhoneDisplay(currentData.contact_phone || currentData.phone_number || '');
        const formattedPhone = formatPhoneDisplay(cleanPhone);

        updateData.contact_phone = cleanPhone;
        updateData.phone_number = cleanPhone;
        updateData.correction_old_value = oldPhone;
        updateData.correction_new_value = formattedPhone;
        updateData.needs_db_update = true;
        updateData.update_field = 'contact_phone';

        responseText = templates.correction_success_phone
          .replace('{{old_value}}', oldPhone)
          .replace('{{new_value}}', formattedPhone);

        nextStage = 'confirmation';
        updateData.correction_in_progress = false;
      } else {
        console.log('V66: Invalid corrected phone format');
        responseText = `${templates.invalid_phone}\\n\\n${templates.correction_prompt_phone.replace('{{phone}}', formatPhoneDisplay(currentData.contact_phone || ''))}`;
        nextStage = 'correction_phone';
      }
      break;

    case 'correction_email':
      console.log('V66: Processing CORRECTION_EMAIL state');

      const trimmedEmail = message.trim().toLowerCase();
      const emailRegex = /^[a-z0-9._%+-]+@[a-z0-9.-]+\\.[a-z]{2,}$/;

      if (emailRegex.test(trimmedEmail)) {
        console.log('V66: Valid corrected email:', trimmedEmail);
        const oldEmail = currentData.email || 'não informado';

        updateData.email = trimmedEmail;
        updateData.contact_email = trimmedEmail;
        updateData.correction_old_value = oldEmail;
        updateData.correction_new_value = trimmedEmail;
        updateData.needs_db_update = true;
        updateData.update_field = 'email';

        responseText = templates.correction_success_email
          .replace('{{old_value}}', oldEmail)
          .replace('{{new_value}}', trimmedEmail);

        nextStage = 'confirmation';
        updateData.correction_in_progress = false;
      } else {
        console.log('V66: Invalid corrected email format');
        responseText = `${templates.invalid_email}\\n\\n${templates.correction_prompt_email.replace('{{email}}', currentData.email || '')}`;
        nextStage = 'correction_email';
      }
      break;

    case 'correction_city':
      console.log('V66: Processing CORRECTION_CITY state');

      const trimmedCity = message.trim();

      if (trimmedCity.length >= 2) {
        console.log('V66: Valid corrected city:', trimmedCity);
        const oldCity = currentData.city || 'não informado';

        updateData.city = trimmedCity;
        updateData.correction_old_value = oldCity;
        updateData.correction_new_value = trimmedCity;
        updateData.needs_db_update = true;
        updateData.update_field = 'city';

        responseText = templates.correction_success_city
          .replace('{{old_value}}', oldCity)
          .replace('{{new_value}}', trimmedCity);

        nextStage = 'confirmation';
        updateData.correction_in_progress = false;
      } else {
        console.log('V66: Invalid corrected city format');
        responseText = `${templates.invalid_city}\\n\\n${templates.correction_prompt_city.replace('{{city}}', currentData.city || '')}`;
        nextStage = 'correction_city';
      }
      break;
"""

# Insert correction states
final_code = code_with_corrections[:insertion_point] + correction_states + code_with_corrections[insertion_point:]

print("✅ Added 5 correction states after confirmation")
print()

# Update node with final code
workflow['nodes'][state_machine_index]['parameters']['functionCode'] = final_code

print(f"✅ State Machine Logic updated!")
print(f"   Final code size: {len(final_code)} chars")
print()

# Now update Build Update Queries node
print("🔍 Finding Build Update Queries node...")
build_queries_node = None
build_queries_index = None

for i, node in enumerate(workflow['nodes']):
    if node.get('name') == 'Build Update Queries':
        build_queries_node = node
        build_queries_index = i
        break

if not build_queries_node:
    print("⚠️ Warning: Build Update Queries node not found, skipping UPDATE query logic")
else:
    print(f"✅ Found at index {build_queries_index}")
    print()

    print("🔨 Adding V66 correction UPDATE query builder...")

    # V66 FIX: Code nodes use 'jsCode' not 'functionCode'
    queries_code = build_queries_node['parameters'].get('jsCode') or build_queries_node['parameters'].get('functionCode')

    # Add correction UPDATE query builder before return statement
    correction_query_builder = """
  // V66: Correction UPDATE Query Builder
  if (inputData.needs_db_update && inputData.update_field) {
    console.log('V66: Building correction UPDATE query for field:', inputData.update_field);

    const fieldConfig = {
      'lead_name': { db_column: 'contact_name', jsonb_key: 'lead_name' },
      'contact_phone': {
        db_column: 'contact_phone',
        jsonb_key: 'contact_phone',
        also_update: 'phone_number'
      },
      'email': { db_column: 'contact_email', jsonb_key: 'email' },
      'city': { db_column: 'city', jsonb_key: 'city' }
    };

    const config = fieldConfig[inputData.update_field];
    const newValue = escapeSql(inputData[inputData.update_field] || '');

    let additionalUpdates = '';
    if (config.also_update) {
      const additionalValue = escapeSql(inputData[config.also_update] || newValue);
      additionalUpdates = `${config.also_update} = '${additionalValue}',`;
    }

    query_correction_update = `
UPDATE conversations
SET
  ${config.db_column} = '${newValue}',
  ${additionalUpdates}
  collected_data = jsonb_set(
    collected_data,
    '{${config.jsonb_key}}',
    to_jsonb('${newValue}')
  ),
  current_state = 'coletando_dados',
  state_machine_state = 'confirmation',
  updated_at = NOW()
WHERE conversation_id = '${conversation_id}'
  AND phone_number IN ('${phone_with_code}', '${phone_without_code}')
RETURNING conversation_id, phone_number, collected_data,
          ${config.db_column} as corrected_field, current_state,
          state_machine_state, updated_at
    `.trim();

    console.log('V66: Correction UPDATE query built for field:', inputData.update_field);
  }
"""

    # Find return statement and insert before it
    return_pattern = r'(return \{.*?\};)'
    return_match = re.search(return_pattern, queries_code, re.DOTALL)

    if return_match:
        return_pos = return_match.start()
        queries_code_updated = queries_code[:return_pos] + correction_query_builder + "\n\n  " + queries_code[return_pos:]

        # Add query_correction_update to return object
        queries_code_updated = queries_code_updated.replace(
            'return {',
            'return {\n    query_correction_update: query_correction_update || null,\n    correction_field_updated: inputData.update_field || null,'
        )

        # V66 FIX: Update correct parameter name
        if 'jsCode' in build_queries_node['parameters']:
            workflow['nodes'][build_queries_index]['parameters']['jsCode'] = queries_code_updated
        else:
            workflow['nodes'][build_queries_index]['parameters']['functionCode'] = queries_code_updated
        print("✅ Correction UPDATE query builder added to Build Update Queries")
    else:
        print("⚠️ Warning: Could not find return statement in Build Update Queries")
    print()

# Validate V66 markers
print("🔍 Validating V66 markers in generated code...")
v66_markers = [
    "V66: Processing CORRECTION state",
    "V66: User chose correction option",
    "V66: Processing CORRECTION_FIELD_SELECTION",
    "V66: Processing CORRECTION_NAME",
    "V66: Processing CORRECTION_PHONE",
    "V66: Processing CORRECTION_EMAIL",
    "V66: Processing CORRECTION_CITY",
    "V66: Building correction UPDATE query"
]

# V66 FIX: Check correct parameter for Build Update Queries node
build_queries_code = ''
if build_queries_node:
    build_queries_code = workflow['nodes'][build_queries_index]['parameters'].get('jsCode') or workflow['nodes'][build_queries_index]['parameters'].get('functionCode') or ''

markers_found = sum(1 for marker in v66_markers if marker in final_code or marker in build_queries_code)
print(f"   V66 markers found: {markers_found}/{len(v66_markers)}")

if markers_found < len(v66_markers):
    print("   ⚠️ Some markers missing (check console logs)")
else:
    print("   ✅ All V66 markers present!")
print()

# Update workflow metadata
print("📝 Updating workflow metadata...")
workflow['name'] = "WF02: AI Agent V66 CORRECTION STATES COMPLETE"
workflow['versionId'] = "66.0.0"
workflow['meta'] = {
    'version': 'v66-correction-states-complete',
    'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    'base_version': 'V65 UX Complete Fix',
    'generator_script': 'generate-workflow-v66-correction-states.py',
    'templates_updated': 25,  # 14 base + 11 correction
    'states': 13,  # 8 base + 5 correction
    'features': [
        'Complete data correction flow (5 new states)',
        'Selective field correction (name, phone, email, city)',
        'SQL UPDATE queries with JSONB operations',
        'Loop protection (max 5 corrections)',
        'Reuse existing validators',
        'Return to confirmation after correction'
    ],
    'notes': 'V66 completes V65 vision: users can correct data without restarting conversation'
}

workflow['tags'] = [
    {"name": "v66-correction-states-complete"},
    {"name": "ready-for-testing"}
]

print("✅ Metadata updated")
print()

# Save V66
print(f"💾 Saving V66: {V66_PATH}")
with open(V66_PATH, 'w', encoding='utf-8') as f:
    json.dump(workflow, f, indent=2, ensure_ascii=False)

v66_size = V66_PATH.stat().st_size
print(f"✅ Saved successfully!")
print(f"   Size: {v66_size / 1024:.1f} KB")
print()

# Final summary
print("=" * 80)
print("✅ V66 GENERATION COMPLETE")
print("=" * 80)
print()
print("📊 What Changed (V65 → V66):")
print("   ✅ Templates: 14 → 25 (+11 correction templates)")
print("   ✅ States: 8 → 13 (+5 correction states)")
print("   ✅ Confirmation option 3: Message → Full correction flow")
print("   ✅ UPDATE queries: Added correction query builder")
print("   ✅ Loop protection: Max 5 corrections with handoff")
print()
print("🧪 Testing Required:")
print("   1. Basic flow: 'oi' → complete → verify confirmation with 3 options")
print("   2. Correction - Name: '3' → '1' → new name → verify UPDATE")
print("   3. Correction - Phone: '3' → '2' → new phone → verify UPDATE")
print("   4. Correction - Email: '3' → '3' → new email → verify UPDATE")
print("   5. Correction - City: '3' → '4' → new city → verify UPDATE")
print("   6. Multiple corrections: Correct → confirm → '3' again → verify")
print("   7. Loop protection: Try 6 corrections → verify handoff")
print("   8. Validation errors: Invalid formats → verify error messages")
print()
print("🚀 Next Steps:")
print("   1. Import to n8n: http://localhost:5678")
print("   2. Deactivate V65")
print("   3. Activate V66")
print("   4. Test all 15 scenarios from V66 plan")
print("   5. Monitor database UPDATEs with:")
print("      docker exec -it e2bot-postgres-dev psql -U postgres -d e2bot_dev \\")
print("      -c \"SELECT conversation_id, lead_name, contact_phone, contact_email, city FROM conversations ORDER BY updated_at DESC LIMIT 5;\"")
print("   6. Check logs: docker logs -f e2bot-n8n-dev | grep -E 'V66|correction'")
print()
print("📋 Rollback Plan:")
print("   If issues: Deactivate V66 → Activate V65 (stable)")
print()
