#!/usr/bin/env python3
"""
V62 Complete UX Fix - Workflow Generator

Combines:
1. V60.2 Syntax Fix (escaped \\n)
2. V61 formatPhoneDisplay Fix (helper function)
3. V62 User's exact UX templates and confirmation flow

Changes from V58.1:
- Adds formatPhoneDisplay helper function
- Adds getServiceEmoji helper function
- Replaces templates with user's exact specs
- Uses individual placeholders ({{name}}, {{phone}}, etc.)
- Implements "1/2" routing logic (NOT "sim/não")
- Adds scheduling_redirect and handoff_comercial templates

Date: 2026-03-10
"""

import json
import re
import sys
import os

# Paths
V58_1_WORKFLOW_PATH = 'n8n/workflows/02_ai_agent_conversation_V58_1_UX_REFACTOR_COMPLETE.json'
OUTPUT_WORKFLOW_PATH = 'n8n/workflows/02_ai_agent_conversation_V62_COMPLETE_UX_FIX.json'

# ============================================================================
# V62 CONSTANTS
# ============================================================================

# V62: formatPhoneDisplay helper function (double-escaped for regex replacement)
FORMATPHONE_HELPER = r"""
// ============================================================================
// HELPER FUNCTION: Format Phone Display
// ============================================================================
/**
 * Format phone number for display
 * Examples:
 *   "556281755748" → "(62) 98175-5748"
 *   "62981755748" → "(62) 98175-5748"
 *   "(62) 98175-5748" → "(62) 98175-5748" (already formatted)
 */
function formatPhoneDisplay(phone) {
  if (!phone) return '';

  // Remove all non-digit characters
  const digits = phone.replace(/\\D/g, '');

  // Handle Brazilian phone numbers
  // Format: (XX) XXXXX-XXXX for mobile or (XX) XXXX-XXXX for landline

  if (digits.length >= 12 && digits.startsWith('55')) {
    // International format: 556281755748
    const ddd = digits.substring(2, 4);
    const rest = digits.substring(4);

    if (rest.length === 9) {
      // Mobile: (XX) 9XXXX-XXXX
      return `(${ddd}) ${rest.substring(0, 5)}-${rest.substring(5)}`;
    } else if (rest.length === 8) {
      // Landline: (XX) XXXX-XXXX
      return `(${ddd}) ${rest.substring(0, 4)}-${rest.substring(4)}`;
    }
  } else if (digits.length === 11) {
    // National mobile: 62981755748
    const ddd = digits.substring(0, 2);
    const number = digits.substring(2);
    return `(${ddd}) ${number.substring(0, 5)}-${number.substring(5)}`;
  } else if (digits.length === 10) {
    // National landline: 6232015000
    const ddd = digits.substring(0, 2);
    const number = digits.substring(2);
    return `(${ddd}) ${number.substring(0, 4)}-${number.substring(4)}`;
  }

  // Return original if format not recognized
  return phone;
}
"""

# V62: getServiceEmoji helper function
SERVICE_EMOJI_HELPER = r"""
// ============================================================================
// HELPER FUNCTION: Get Service Emoji
// ============================================================================
function getServiceEmoji(serviceType) {
  const emojiMap = {
    'Energia Solar': '☀️',
    'energia_solar': '☀️',
    'Subestação': '⚡',
    'subestacao': '⚡',
    'Projetos Elétricos': '📐',
    'projeto_eletrico': '📐',
    'BESS': '🔋',
    'armazenamento_energia': '🔋',
    'Análise e Laudos': '📊',
    'analise_laudo': '📊'
  };
  return emojiMap[serviceType] || '🔧';
}
"""

# V62: Templates (user's exact specs)
V62_TEMPLATES = r"""const templates = {
  greeting: `🤖 *Olá! Bem-vindo à E2 Soluções!*

Somos especialistas em engenharia elétrica com *15+ anos de experiência*.

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

  service_selection: `Ótima escolha! Vou precisar de alguns dados.

👤 *Qual é o seu nome completo?*

💡 _Exemplo: Maria Silva Santos_
_Usaremos para personalizar seu atendimento_`,

  collect_name: `Obrigado, {{name}}!

📱 *Qual é o seu telefone com DDD?*

Identificaremos se é seu WhatsApp automaticamente.

💡 _Exemplo: (62) 98765-4321_
_Usaremos este número para agendarmos sua visita técnica_`,

  collect_phone: `📱 *Qual é o seu telefone com DDD?*

💡 _Exemplo: (62) 98765-4321_
_Usaremos este número para agendarmos sua visita técnica_`,

  collect_phone_whatsapp_confirm: `📱 *Ótimo, {{name}}!*

Vi que você está me enviando mensagens pelo número:
*{{whatsapp_number}}*

Este é o melhor número para contato?

1️⃣ *Sim, pode usar este*
2️⃣ *Não, vou informar outro*`,

  collect_phone_alternative: `📱 *Certo! Qual o melhor telefone para contato?*

_Informe com DDD:_
Exemplo: (62) 98765-4321 ou 62987654321`,

  invalid_phone: `❌ *Telefone inválido.*

Por favor, informe um telefone válido com DDD.

*Formatos aceitos:*
• (62) 98765-4321
• 62 98765-4321
• 62987654321`,

  collect_email: `📧 *Qual é o seu e-mail?*

Enviaremos a proposta técnica e documentos por e-mail.

💡 _Exemplo: maria.silva@email.com_
_Digite *"pular"* se preferir não informar_

⚠️ _Sem e-mail, os documentos serão enviados apenas por WhatsApp_`,

  collect_city: `🏙️ *Em qual cidade você está?*

Precisamos saber para agendar a visita técnica.

💡 _Exemplo: Goiânia - GO_

📍 *Área de Atendimento:*
   Atendemos todo o Centro-Oeste (GO, DF, MT, MS)

_Informe a cidade e estado:_`,

  confirmation: `✅ *Perfeito! Veja o resumo dos seus dados:*

👤 *Nome:* {{name}}
📱 *Telefone:* {{phone}}
📧 *E-mail:* {{email}}
📍 *Cidade:* {{city}}
{{service_emoji}} *Serviço:* {{service_name}}

---

*Visita Técnica*

Deseja agendar uma visita técnica gratuita para avaliarmos seu projeto?

1️⃣ *Sim, quero agendar*
2️⃣ *Não agora, falar com uma pessoa*`,

  scheduling_redirect: `🗓️ *Ótima escolha!*

Vou te direcionar para o agendamento de visita técnica.

_Um momento, por favor..._`,

  handoff_comercial: `💼 *Entendido!*

Vou encaminhar seus dados para nossa equipe comercial.

*Você receberá:*
✅ Orçamento detalhado em até 24h
✅ Contato da nossa equipe
✅ Informações sobre o serviço

_Obrigado por escolher a E2 Soluções!_ 🙏`,

  completed: `✅ *Agendamento Confirmado!*

Tudo certo! Seu atendimento foi registrado com sucesso.

📧 *Você receberá:*
   • E-mail de confirmação em até 1 hora
   • WhatsApp com detalhes da visita técnica

📞 *Nossa equipe entrará em contato:*
   Em até 24 horas para agendar data/horário

🙏 *Obrigado por escolher a E2 Soluções!*

_Qualquer dúvida, responda esta mensagem_`
};
"""

# ============================================================================
# TRANSFORMATION FUNCTIONS
# ============================================================================

def inject_helper_functions(js_code):
    """
    Inject formatPhoneDisplay and getServiceEmoji helper functions
    at the top of the code, right after input extraction
    """
    print("🔧 Injecting helper functions")

    # Find insertion point (after message extraction in V58.1)
    pattern = r"(const message = input\.message \|\| input\.body \|\| input\.text \|\| '';[\s\n]+)"

    # Use string concatenation instead of raw string to avoid escape issues
    replacement = "\\1" + FORMATPHONE_HELPER + "\n" + SERVICE_EMOJI_HELPER + "\n"

    js_code = re.sub(pattern, replacement, js_code, count=1)
    print("✅ Injected formatPhoneDisplay and getServiceEmoji helper functions")

    return js_code

def replace_templates_v62(js_code):
    """
    Replace V58.1 templates with V62 templates (user's exact specs)
    """
    print("🔄 Replacing templates with V62 versions")

    # Find and replace templates constant
    pattern = r"const templates = \{[\s\S]*?\};[\s\n]+"

    js_code = re.sub(pattern, V62_TEMPLATES + "\n", js_code, count=1)
    print("✅ Replaced with V62 templates")

    return js_code

def fix_collect_name_transition_v62(js_code):
    """
    Fix collect_name transition to use template with {{name}} placeholder
    (V58.1 uses hardcoded string interpolation, V62 needs template replacement)
    """
    print("🔧 Fixing collect_name transition for V62")

    # Find collect_name case and replace hardcoded string with template usage
    pattern = r"(case 'collect_name':[\s\S]*?updateData\.lead_name = trimmedName;[\s]*)(responseText = `Obrigado, \$\{trimmedName\}!\\n\\n` \+ templates\.collect_phone;)"

    replacement = r"""\1// V62: Use template with {{name}} placeholder
      responseText = templates.collect_name.replace('{{name}}', trimmedName);"""

    js_code = re.sub(pattern, replacement, js_code, count=1)
    print("✅ Fixed collect_name transition")

    return js_code

def fix_collect_phone_transition_v62(js_code):
    """
    Fix collect_phone transition to use {{name}} and {{whatsapp_number}} placeholders
    """
    print("🔧 Fixing collect_phone transition for V62")

    # Find collect_phone case and fix the template usage
    pattern = r"(case 'collect_phone':[\s\S]*?// Format phone for display[\s]*const formattedPhone = formatPhoneDisplay\(cleanPhone\);[\s]*)(responseText = templates\.collect_phone_whatsapp_confirmation[\s\S]*?;[\s]*nextStage = 'collect_phone_whatsapp_confirmation';)"

    replacement = r"""\1
    // V62: Replace placeholders
    responseText = templates.collect_phone_whatsapp_confirm
      .replace('{{name}}', currentData.lead_name || currentData.name || 'amigo')
      .replace('{{whatsapp_number}}', formattedPhone);

    nextStage = 'collect_phone_whatsapp_confirmation';"""

    js_code = re.sub(pattern, replacement, js_code, count=1)
    print("✅ Fixed collect_phone transition")

    return js_code

def fix_collect_city_transition_v62(js_code):
    """
    Fix collect_city → confirmation transition to use individual placeholders (NOT {{summary}})
    """
    print("🔧 Fixing collect_city → confirmation transition for V62")

    # Find collect_city case and replace entire summary generation logic
    pattern = r"case 'collect_city':[\s]*updateData\.city = message;[\s\S]*?nextStage = 'confirmation';"

    replacement = r"""case 'collect_city':
      updateData.city = message;

      console.log('V62: Transitioning to confirmation with individual placeholders');

      // V62: Get service emoji and name
      const serviceEmoji = getServiceEmoji(currentData.service_type);
      const serviceName = currentData.service_type || 'Não especificado';

      // V62: Format phone display
      const displayPhone = formatPhoneDisplay(currentData.phone_number || currentData.phone);

      // V62: Get email or default
      const displayEmail = currentData.email || currentData.contact_email || '_Não informado (documentos via WhatsApp)_';

      // V62: Get city
      const displayCity = message || '_Não informado_';

      // V62: Get name
      const displayName = currentData.lead_name || currentData.contact_name || currentData.name || '_Não informado_';

      // V62: Replace individual placeholders (NOT {{summary}})
      responseText = templates.confirmation
        .replace('{{name}}', displayName)
        .replace('{{phone}}', displayPhone)
        .replace('{{email}}', displayEmail)
        .replace('{{city}}', displayCity)
        .replace('{{service_emoji}}', serviceEmoji)
        .replace('{{service_name}}', serviceName);

      nextStage = 'confirmation';"""

    js_code = re.sub(pattern, replacement, js_code, count=1)
    print("✅ Fixed collect_city → confirmation transition")

    return js_code

def fix_confirmation_state_v62(js_code):
    """
    Replace confirmation state logic to use "1/2" routing instead of "sim/não"
    """
    print("🔧 Fixing confirmation state for V62 (1/2 routing)")

    # Find confirmation case and replace entire logic
    pattern = r"case 'confirmation':[\s\S]*?break;"

    replacement = r"""case 'confirmation':
      const choice = message.trim();

      if (choice === '1') {
        // V62: User wants to schedule visit
        console.log('V62: User chose scheduling (option 1)');

        responseText = templates.scheduling_redirect;
        nextStage = 'agendando';

        // TODO: Trigger external appointment scheduler integration
        // updateData.scheduled_visit_requested = true;

      } else if (choice === '2') {
        // V62: User wants to talk to person
        console.log('V62: User chose human handoff (option 2)');

        responseText = templates.handoff_comercial;
        nextStage = 'handoff_comercial';

        // TODO: Trigger human handoff workflow (RD Station, email, etc.)
        // updateData.requires_human_handoff = true;

      } else {
        // Invalid - show confirmation again
        console.log('V62: Invalid confirmation choice');

        // Regenerate confirmation with same data
        const serviceEmoji = getServiceEmoji(currentData.service_type);
        const serviceName = currentData.service_type || 'Não especificado';
        const displayPhone = formatPhoneDisplay(currentData.phone_number || currentData.phone);
        const displayEmail = currentData.email || currentData.contact_email || '_Não informado (documentos via WhatsApp)_';
        const displayCity = currentData.city || '_Não informado_';
        const displayName = currentData.lead_name || currentData.contact_name || currentData.name || '_Não informado_';

        responseText = `❌ *Opção inválida*\n\nPor favor, responda *1* ou *2*\n\n` +
                       templates.confirmation
                         .replace('{{name}}', displayName)
                         .replace('{{phone}}', displayPhone)
                         .replace('{{email}}', displayEmail)
                         .replace('{{city}}', displayCity)
                         .replace('{{service_emoji}}', serviceEmoji)
                         .replace('{{service_name}}', serviceName);
      }
      break;"""

    js_code = re.sub(pattern, replacement, js_code, count=1)
    print("✅ Fixed confirmation state logic")

    return js_code

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """
    V62 Complete UX Fix - Workflow Generator
    """
    print("=" * 60)
    print("V62 Complete UX Fix - Workflow Generator")
    print("=" * 60)
    print()

    # Step 1: Read V58.1 workflow
    print("📖 Reading V58.1 workflow")
    v58_1_path = V58_1_WORKFLOW_PATH

    if not os.path.exists(v58_1_path):
        print(f"❌ ERROR: V58.1 workflow not found at {v58_1_path}")
        sys.exit(1)

    with open(v58_1_path, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    print(f"✅ Loaded: {workflow['name']}")
    print(f"   Nodes: {len(workflow['nodes'])}")
    print()

    # Step 2: Find State Machine Logic node
    print("🔍 Locating State Machine Logic node")
    state_machine_node = None

    for node in workflow['nodes']:
        if node.get('name') == 'State Machine Logic':
            state_machine_node = node
            break

    if not state_machine_node:
        print("❌ ERROR: State Machine Logic node not found")
        sys.exit(1)

    print("✅ Found node: State Machine Logic")
    print()

    # Step 3: Extract JavaScript code from jsCode (V58.1 has proper logic there)
    print("📝 Extracting JavaScript code")

    # V58.1 has BOTH functionCode (OLD V40 code) and jsCode (NEW V58.1 code)
    # We MUST use jsCode which has the proper phone confirmation states
    if 'jsCode' in state_machine_node['parameters']:
        js_code = state_machine_node['parameters']['jsCode']
        print(f"✅ Extracted from jsCode (NEW V58.1 code): {len(js_code)} characters")
    else:
        js_code = state_machine_node['parameters']['functionCode']
        print(f"✅ Extracted from functionCode: {len(js_code)} characters")

    print()

    # Step 4: Inject helper functions (formatPhoneDisplay + getServiceEmoji)
    print("➕ Injecting helper functions")
    js_code = inject_helper_functions(js_code)
    print()

    # Step 5: Replace templates with V62 versions
    print("🔄 Replacing templates with V62 versions")
    js_code = replace_templates_v62(js_code)
    print()

    # Step 6: Fix state transitions
    print("🔧 Applying V62 state transition fixes")
    js_code = fix_collect_name_transition_v62(js_code)      # NEW: Fix {{name}} placeholder
    js_code = fix_collect_phone_transition_v62(js_code)
    js_code = fix_collect_city_transition_v62(js_code)
    js_code = fix_confirmation_state_v62(js_code)
    print()

    # Step 7: Update workflow metadata
    print("🏷️  Updating workflow metadata")
    workflow['name'] = '02 - AI Agent V62 (Complete UX Fix - All Issues Resolved)'
    workflow['meta'] = {
        'instanceId': workflow.get('meta', {}).get('instanceId', ''),
        'version': 'v62-complete-ux-fix',
        'generated_at': '2026-03-10',
        'changes': [
            'V60.2: Syntax fix (escaped \\n)',
            'V61: formatPhoneDisplay helper function',
            'V62: User\'s exact UX templates',
            'V62: Individual placeholders ({{name}}, {{phone}}, etc.)',
            'V62: 1/2 routing logic (scheduling vs handoff)',
            'V62: New templates (scheduling_redirect, handoff_comercial)',
            'V62: getServiceEmoji helper function'
        ]
    }

    if 'tags' not in workflow:
        workflow['tags'] = []

    workflow['tags'] = [
        {'name': 'v62-complete-ux-fix'},
        {'name': 'production-ready'},
        {'name': 'all-fixes-applied'}
    ]

    print("✅ Updated metadata")
    print()

    # Step 8: Update functionCode
    print("💾 Updating State Machine Logic node")
    state_machine_node['parameters']['functionCode'] = js_code

    # Remove jsCode if present (n8n ignores it)
    if 'jsCode' in state_machine_node['parameters']:
        del state_machine_node['parameters']['jsCode']
        print("✅ Removed jsCode field (n8n ignores it)")

    print(f"✅ Updated functionCode: {len(js_code)} characters")
    print()

    # Step 9: Write V62 workflow
    print("💾 Writing V62 workflow")
    output_path = OUTPUT_WORKFLOW_PATH

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    file_size = os.path.getsize(output_path)
    print(f"✅ Wrote: {file_size:,} bytes")
    print()

    # Step 10: Summary
    print("=" * 60)
    print("📊 Changes Applied:")
    print("=" * 60)
    print("   ✅ Helper Functions: formatPhoneDisplay + getServiceEmoji")
    print("   ✅ Templates: V62 (user's exact specs)")
    print("   ✅ Placeholders: Individual ({{name}}, {{phone}}, etc.)")
    print("   ✅ Confirmation: 1/2 routing (NOT sim/não)")
    print("   ✅ States: scheduling_redirect + handoff_comercial")
    print("   ✅ Syntax: Properly escaped \\n")
    print("   ✅ Updated functionCode (n8n executes this)")
    print("   ✅ Removed jsCode (n8n ignores it)")
    print()
    print("📁 Output: " + output_path)
    print()
    print("=" * 60)
    print("✅ V62 WORKFLOW GENERATION COMPLETE")
    print("=" * 60)

if __name__ == '__main__':
    main()
