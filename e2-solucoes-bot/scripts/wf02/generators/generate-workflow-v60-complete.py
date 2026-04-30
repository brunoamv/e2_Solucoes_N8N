#!/usr/bin/env python3
"""
V60 Complete Solution - Workflow Generator
===========================================
Purpose: Generate V60 workflow with ALL features:
  - V58.1 architecture (8 gaps fixed) - PRESERVED
  - V59 UX templates (16 rich templates) - NEW
  - V60 confirmation logic ({{summary}} generation) - NEW
  - V60 correction menu (field correction) - NEW

Input:  n8n/workflows/02_ai_agent_conversation_V58_1_UX_REFACTOR_COMPLETE.json
Output: n8n/workflows/02_ai_agent_conversation_V60_COMPLETE_SOLUTION.json

Date: 2026-03-10
Author: Claude Code (automated)
"""

import json
import re
from pathlib import Path

# File paths
BASE_DIR = Path(__file__).parent.parent
INPUT_FILE = BASE_DIR / "n8n/workflows/02_ai_agent_conversation_V58_1_UX_REFACTOR_COMPLETE.json"
OUTPUT_FILE = BASE_DIR / "n8n/workflows/02_ai_agent_conversation_V60_COMPLETE_SOLUTION.json"

# V59 Rich UX Templates
V59_TEMPLATES = r"""const templates = {
  // ===== 1. GREETING - Menu Principal =====
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

  // ===== 2. ERROR - Invalid Option =====
  invalid_option: `❌ *Opção inválida*

Por favor, escolha um número de *1 a 5* correspondente ao serviço desejado:

☀️ 1 - Energia Solar
⚡ 2 - Subestação
📐 3 - Projetos Elétricos
🔋 4 - BESS
📊 5 - Análise e Laudos

_Digite apenas o número (1-5):_`,

  // ===== 3. COLLECT NAME =====
  collect_name: `👤 *Qual é o seu nome completo?*

💡 _Exemplo: Maria Silva Santos_

_Usaremos para personalizar seu atendimento_`,

  // ===== 4. ERROR - Invalid Name =====
  invalid_name: `❌ *Nome incompleto*

Por favor, informe seu *nome completo* para prosseguirmos.

💡 _Exemplo: João da Silva_

_Precisamos do nome completo para o cadastro._`,

  // ===== 5. COLLECT PHONE =====
  collect_phone: `📱 *Qual é o seu telefone com DDD?*

Identificaremos se é seu WhatsApp automaticamente.

💡 _Exemplo: (62) 98765-4321_

_Usaremos este número para agendarmos sua visita técnica_`,

  // ===== 6. PHONE CONFIRMATION (V58.1 GAP #3) =====
  collect_phone_whatsapp_confirmation: `📱 *Confirmação de Contato*

Perfeito! Identificamos seu WhatsApp:
*{{phone}}*

Este número é seu contato principal para agendarmos a visita técnica?

1️⃣ - *Sim*, pode me ligar neste número
2️⃣ - *Não*, prefiro informar outro número

💡 _Responda 1 ou 2_`,

  // ===== 7. ALTERNATIVE PHONE (V58.1 GAP #4) =====
  collect_phone_alternative: `📱 *Telefone de Contato Alternativo*

Por favor, informe o melhor número para contato:

💡 _Exemplo: (62) 98765-4321_

_Usaremos este número para agendar sua visita técnica_`,

  // ===== 8. ERROR - Invalid Phone =====
  invalid_phone: `❌ *Formato de telefone inválido*

Por favor, informe um número válido com DDD:

💡 _Formato correto: (62) 98765-4321_

📍 _Exemplos válidos:_
   • (61) 99876-5432
   • (62) 3201-5000 (fixo)
   • 62987654321 (sem formatação)

_Certifique-se de incluir o DDD da sua região_`,

  // ===== 9. COLLECT EMAIL =====
  collect_email: `📧 *Qual é o seu e-mail?*

Enviaremos a proposta técnica e documentos por e-mail.

💡 _Exemplo: maria.silva@email.com_

_Digite *"pular"* se preferir não informar_

⚠️ _Sem e-mail, os documentos serão enviados apenas por WhatsApp_`,

  // ===== 10. ERROR - Invalid Email =====
  invalid_email: `❌ *Formato de e-mail inválido*

Por favor, informe um e-mail válido:

💡 _Exemplos corretos:_
   • maria@gmail.com
   • joao.silva@empresa.com.br
   • contato123@hotmail.com

_Ou digite *"pular"* para receber tudo via WhatsApp_`,

  // ===== 11. COLLECT CITY =====
  collect_city: `🏙️ *Em qual cidade você está?*

Precisamos saber para agendar a visita técnica.

💡 _Exemplo: Goiânia - GO_

📍 *Área de Atendimento:*
   Atendemos todo o Centro-Oeste (GO, DF, MT, MS)

_Informe a cidade e estado:_`,

  // ===== 12. ERROR - Invalid City =====
  invalid_city: `❌ *Cidade não reconhecida*

Por favor, informe a cidade e estado:

💡 _Exemplos corretos:_
   • Goiânia - GO
   • Brasília - DF
   • Anápolis - GO
   • Campo Grande - MS

📍 _Atendemos: GO, DF, MT, MS_`,

  // ===== 13. CONFIRMATION (V60 - WITH SUMMARY) =====
  confirmation: `✅ *Confirmação dos Dados*

Por favor, confira as informações:

{{summary}}

*Está tudo correto?*

✔️ Digite *"sim"* para confirmar
✏️ Digite *"não"* para corrigir alguma informação

⏭️ *Próximos Passos:*
   1. Você receberá a confirmação no e-mail
   2. Nossa equipe entrará em contato para agendar
   3. Realizaremos a visita técnica

_Aguardamos sua confirmação:_`,

  // ===== 14. COMPLETION MESSAGES =====
  scheduling_complete: `✅ *Agendamento Confirmado!*

Tudo certo! Seu atendimento foi registrado com sucesso.

📧 *Você receberá:*
   • E-mail de confirmação em até 1 hora
   • WhatsApp com detalhes da visita técnica

📞 *Nossa equipe entrará em contato:*
   Em até 24 horas para agendar data/horário

🙏 *Obrigado por escolher a E2 Soluções!*

_Qualquer dúvida, responda esta mensagem_`,

  handoff_complete: `✅ *Dados Encaminhados ao Comercial!*

Perfeito! Seu atendimento foi registrado.

👔 *Equipe Comercial:*
   Entrará em contato em até 24 horas

📧 *E-mail:*
   Você receberá a confirmação em breve

🎯 *Preparação para o Contato:*
   Nossa equipe já está analisando sua demanda para oferecer a melhor solução

🙏 *Obrigado pela confiança!*

_Qualquer dúvida, responda esta mensagem_`,

  generic_complete: `✅ *Atendimento Finalizado!*

Obrigado por entrar em contato com a E2 Soluções.

📧 Seus dados foram registrados com sucesso.

📞 *Precisa de algo mais?*
   • Responda esta mensagem
   • Ou envie "oi" para começar um novo atendimento

🙏 *Estamos sempre à disposição!*

_E2 Soluções - 15+ anos de experiência em engenharia elétrica_`,

  // ===== 15. CORRECTION MENU (V60 NEW) =====
  correction_menu: `✏️ *Correção de Dados*

Qual informação você gostaria de corrigir?

1️⃣ - Nome
2️⃣ - Telefone
3️⃣ - E-mail
4️⃣ - Cidade
5️⃣ - Serviço

💡 _Digite o número (1-5):_`
};"""

# V60 Confirmation State Logic
V60_CONFIRMATION_CASE = r"""
  // ============================================================================
  // V60 NEW: CONFIRMATION STATE (WITH SUMMARY GENERATION)
  // ============================================================================
  case 'confirmation':
  case 'confirmacao':
    console.log('V60: Processing CONFIRMATION state');

    // Helper function to format phone display
    const formatPhoneDisplay = (phone) => {
      if (!phone) return 'N/A';
      const cleaned = phone.replace(/\D/g, '');
      if (cleaned.length === 11) {
        return `(${cleaned.substr(0, 2)}) ${cleaned.substr(2, 5)}-${cleaned.substr(7)}`;
      }
      if (cleaned.length === 10) {
        return `(${cleaned.substr(0, 2)}) ${cleaned.substr(2, 4)}-${cleaned.substr(6)}`;
      }
      return phone;
    };

    // Build summary from collected data
    const summaryParts = [];

    // Name (always present)
    if (currentData.lead_name) {
      summaryParts.push(`👤 *Nome:* ${currentData.lead_name}`);
    }

    // Phone number (from WhatsApp or collected)
    if (currentData.phone_number || currentData.phone) {
      const phoneDisplay = formatPhoneDisplay(currentData.phone_number || currentData.phone);
      summaryParts.push(`📱 *Telefone:* ${phoneDisplay}`);
    }

    // Contact phone (if different from main phone - GAP #8)
    if (currentData.contact_phone && currentData.contact_phone !== (currentData.phone_number || currentData.phone)) {
      const contactDisplay = formatPhoneDisplay(currentData.contact_phone);
      const contactSource = currentData.contact_phone === currentData.phone_number
        ? '(WhatsApp confirmado)'
        : '(Número alternativo)';
      summaryParts.push(`📞 *Contato:* ${contactDisplay} ${contactSource}`);
    }

    // Email (if provided)
    if (currentData.email && currentData.email !== 'pular' && currentData.email.toLowerCase() !== 'pular') {
      summaryParts.push(`📧 *E-mail:* ${currentData.email}`);
    } else {
      summaryParts.push(`📧 *E-mail:* _Não informado (documentos via WhatsApp)_`);
    }

    // City (always present at confirmation stage)
    if (currentData.city) {
      summaryParts.push(`🏙️ *Cidade:* ${currentData.city}`);
    }

    // Service type (always present at confirmation stage)
    if (currentData.service_type) {
      const serviceEmojis = {
        'Energia Solar': '☀️',
        'Subestação': '⚡',
        'Projetos Elétricos': '📐',
        'BESS': '🔋',
        'Análise e Laudos': '📊'
      };
      const serviceEmoji = serviceEmojis[currentData.service_type] || '⚡';
      summaryParts.push(`${serviceEmoji} *Serviço:* ${currentData.service_type}`);
    }

    const summary = summaryParts.join('\n');

    // User input handling
    const normalizedMessage = message.toLowerCase().trim();

    if (normalizedMessage === 'sim') {
      console.log('V60: User confirmed data - proceeding to completion');
      updateData.current_state = 'completed';
      updateData.confirmation_status = 'confirmed';

      if (currentData.service_type === 'Energia Solar' || currentData.service_type === 'Projetos Elétricos') {
        responseText = templates.scheduling_complete;
        nextStage = 'completed';
      } else {
        responseText = templates.handoff_complete;
        nextStage = 'handoff_comercial';
      }

    } else if (normalizedMessage === 'não' || normalizedMessage === 'nao') {
      console.log('V60: User wants to correct data - showing correction menu');
      responseText = templates.correction_menu;
      nextStage = 'correction_menu';

    } else {
      console.log('V60: Invalid confirmation response - showing confirmation again');
      responseText = templates.confirmation.replace('{{summary}}', summary);
      nextStage = 'confirmation';
    }

    break;

  // ============================================================================
  // V60 NEW: CORRECTION MENU STATE
  // ============================================================================
  case 'correction_menu':
  case 'menu_correcao':
    console.log('V60: Processing CORRECTION_MENU state');

    const normalizedCorrectionChoice = message.trim();

    if (/^[1-5]$/.test(normalizedCorrectionChoice)) {
      console.log(`V60: User wants to correct field ${normalizedCorrectionChoice}`);

      const correctionMap = {
        '1': 'collect_name',
        '2': 'collect_phone',
        '3': 'collect_email',
        '4': 'collect_city',
        '5': 'service_selection'
      };

      nextStage = correctionMap[normalizedCorrectionChoice];

      switch (normalizedCorrectionChoice) {
        case '1':
          updateData.lead_name = null;
          responseText = templates.collect_name;
          break;
        case '2':
          updateData.phone_number = null;
          updateData.contact_phone = null;
          responseText = templates.collect_phone;
          break;
        case '3':
          updateData.email = null;
          responseText = templates.collect_email;
          break;
        case '4':
          updateData.city = null;
          responseText = templates.collect_city;
          break;
        case '5':
          updateData.service_type = null;
          responseText = templates.greeting;
          break;
      }

    } else {
      console.log('V60: Invalid correction menu choice');
      responseText = templates.correction_menu;
      nextStage = 'correction_menu';
    }

    break;"""


def main():
    print("=" * 60)
    print("V60 Complete Solution - Workflow Generator")
    print("=" * 60)
    print()

    # Read V58.1 workflow
    print(f"📖 Reading V58.1 workflow: {INPUT_FILE.name}")
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        workflow = json.load(f)
    print(f"✅ Loaded workflow: {workflow['name']}")
    print(f"   Nodes: {len(workflow['nodes'])}")
    print()

    # Locate State Machine Logic node
    print("🔍 Locating State Machine Logic node...")
    state_machine_node = None
    for node in workflow['nodes']:
        if node['name'] == 'State Machine Logic':
            state_machine_node = node
            break

    if not state_machine_node:
        print("❌ ERROR: State Machine Logic node not found!")
        return 1

    print(f"✅ Found node: {state_machine_node['name']} (ID: {state_machine_node['id']})")
    print()

    # Extract jsCode
    print("📝 Extracting JavaScript code...")
    js_code = state_machine_node['parameters']['jsCode']
    original_length = len(js_code)
    print(f"✅ Extracted {original_length} characters of JavaScript")
    print()

    # Replace templates
    print("🔄 Replacing templates with V59 rich templates...")

    # Find templates constant - match from "const templates = {" to the closing "};"
    templates_pattern = r'const templates = \{.*?\n\};'
    match = re.search(templates_pattern, js_code, re.DOTALL)

    if not match:
        print("❌ ERROR: Could not find templates constant!")
        return 1

    old_templates = match.group(0)
    print(f"✅ Found templates constant ({len(old_templates)} chars)")

    # Replace with V59 templates
    js_code = js_code.replace(old_templates, V59_TEMPLATES)
    print(f"✅ Replaced with V59 templates ({len(V59_TEMPLATES)} chars)")
    print()

    # Add confirmation and correction_menu cases
    print("➕ Adding V60 confirmation and correction_menu states...")

    # Find the location to insert - after collect_city case, before default case
    # Look for "case 'collect_city':" and find its break, then insert

    collect_city_pattern = r"(case 'collect_city':.*?break;)"
    match = re.search(collect_city_pattern, js_code, re.DOTALL)

    if not match:
        print("❌ ERROR: Could not find collect_city case!")
        return 1

    collect_city_end = match.end()
    print(f"✅ Found collect_city case end position")

    # Insert V60 confirmation and correction_menu cases
    js_code = js_code[:collect_city_end] + V60_CONFIRMATION_CASE + js_code[collect_city_end:]
    print(f"✅ Inserted V60 confirmation logic ({len(V60_CONFIRMATION_CASE)} chars)")
    print()

    # Update stateNameMapping to include new states
    print("🔄 Updating stateNameMapping with V60 states...")

    # Find stateNameMapping and add new entries before the closing brace
    state_mapping_pattern = r"(const stateNameMapping = \{.*?)(\n\};)"
    match = re.search(state_mapping_pattern, js_code, re.DOTALL)

    if match:
        existing_mapping = match.group(1)

        # Check if V60 states already exist
        if 'correction_menu' not in existing_mapping:
            v60_states = """,

  // V60 NEW MAPPINGS (2 ENTRIES) ✅
  'correction_menu': 'correction_menu',
  'menu_correcao': 'correction_menu'"""

            js_code = js_code.replace(match.group(0), existing_mapping + v60_states + match.group(2))
            print("✅ Added V60 state mappings (correction_menu, menu_correcao)")
        else:
            print("ℹ️  V60 state mappings already present")
    else:
        print("⚠️  WARNING: Could not update stateNameMapping")

    print()

    # Update node with modified jsCode
    state_machine_node['parameters']['jsCode'] = js_code
    print(f"✅ Updated State Machine Logic node ({len(js_code)} chars)")
    print()

    # Update workflow metadata
    print("🔄 Updating workflow metadata...")
    workflow['name'] = "02 - AI Agent V60 (Complete Solution - All 8 Gaps + UX + Confirmation)"
    workflow['versionId'] = "v60-complete-solution"

    # Update or add tags
    if 'tags' not in workflow:
        workflow['tags'] = []

    workflow['tags'] = [
        {"id": "v60-complete", "name": "V60 Complete"},
        {"id": "all-gaps-ux", "name": "All Gaps + UX"},
        {"id": "confirmation-logic", "name": "Confirmation Logic"}
    ]

    print(f"✅ Workflow name: {workflow['name']}")
    print(f"✅ Version ID: {workflow['versionId']}")
    print(f"✅ Tags: {len(workflow['tags'])}")
    print()

    # Write V60 workflow
    print(f"💾 Writing V60 workflow: {OUTPUT_FILE.name}")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    output_size = OUTPUT_FILE.stat().st_size
    print(f"✅ Wrote {output_size:,} bytes")
    print()

    # Summary
    print("=" * 60)
    print("✅ V60 WORKFLOW GENERATION COMPLETE")
    print("=" * 60)
    print()
    print("📊 Changes Applied:")
    print(f"   ✅ Templates: V58.1 → V59 (16 rich templates)")
    print(f"   ✅ States: Added confirmation + correction_menu")
    print(f"   ✅ Logic: {{{{summary}}}} generation ON-THE-FLY")
    print(f"   ✅ Mapping: 2 new state mappings")
    print(f"   ✅ Architecture: V58.1 (8 gaps) PRESERVED")
    print()
    print("📂 Output:")
    print(f"   {OUTPUT_FILE.relative_to(BASE_DIR)}")
    print()
    print("🚀 Next Steps:")
    print("   1. Import to n8n: http://localhost:5678")
    print("   2. Deactivate V58.1 workflow")
    print("   3. Activate V60 workflow")
    print("   4. Test complete flow (greeting → confirmation → completed)")
    print("   5. Test correction menu (não → 1-5 → verify field reset)")
    print()

    return 0


if __name__ == '__main__':
    exit(main())
