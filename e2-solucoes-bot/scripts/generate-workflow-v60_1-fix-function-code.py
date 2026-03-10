#!/usr/bin/env python3
"""
V60.1 COMPLETE SOLUTION - Generator Script (FUNCTIONCODE FIX)

Purpose: Generate V60.1 workflow with V59 rich templates + V60 confirmation logic
Critical Fix: Replace functionCode instead of adding to jsCode

Changes from V60:
1. ✅ Replace functionCode field (n8n executes this)
2. ✅ Remove jsCode field (unused when functionCode present)
3. ✅ Keep all V60 features (rich templates, confirmation, correction_menu)

Date: 2026-03-10
Author: Claude Code (automated)
"""

import json
import re
from pathlib import Path

# ============================================================================
# V59 RICH TEMPLATES (16 TEMPLATES)
# ============================================================================
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

# ============================================================================
# V60 CONFIRMATION LOGIC (NEW STATE CASES)
# ============================================================================
V60_CONFIRMATION_LOGIC = r"""
  // ============================================================================
  // V60 NEW FEATURE: CONFIRMATION STATE WITH ON-THE-FLY SUMMARY
  // ============================================================================
  case 'confirmation':
  case 'confirmacao':
    console.log('V60: Processing CONFIRMATION state');

    const normalizedMessage = message.trim().toLowerCase();

    if (normalizedMessage === 'sim') {
      console.log('V60: User confirmed data');

      // Determine completion type based on service
      const serviceType = currentData.service_type || updateData.service_type || '';
      let completionTemplate = templates.generic_complete;

      if (serviceType.includes('Energia Solar') || serviceType.includes('Subestação')) {
        completionTemplate = templates.scheduling_complete;
      } else {
        completionTemplate = templates.handoff_complete;
      }

      responseText = completionTemplate;
      nextStage = 'completed';
      updateData.confirmed = true;
      updateData.confirmation_timestamp = new Date().toISOString();
    } else if (normalizedMessage === 'não' || normalizedMessage === 'nao') {
      console.log('V60: User wants to correct data');
      responseText = templates.correction_menu;
      nextStage = 'correction_menu';
    } else {
      console.log('V60: Invalid confirmation response');
      // GAP #7: Error handling ✅
      const errorCountLocal = (currentData.errorCount || 0) + 1;

      if (errorCountLocal >= 3) {
        responseText = `❌ *Desculpe, tivemos dificuldade*\n\nVocê gostaria de:\n\n1️⃣ - Voltar ao menu principal\n2️⃣ - Falar com um atendente\n\n💡 _Responda 1 ou 2_`;
        nextStage = 'error_recovery';
      } else {
        // Regenerate summary
        let summaryParts = [];

        if (currentData.lead_name) {
          summaryParts.push(`👤 *Nome:* ${currentData.lead_name}`);
        }
        if (currentData.phone_number || currentData.phone) {
          const displayPhone = formatPhoneDisplay(currentData.phone_number || currentData.phone);
          summaryParts.push(`📱 *Telefone:* ${displayPhone}`);
        }
        if (currentData.contact_phone && currentData.contact_phone !== (currentData.phone_number || currentData.phone)) {
          const displayContact = formatPhoneDisplay(currentData.contact_phone);
          summaryParts.push(`📞 *Contato:* ${displayContact} (Número alternativo)`);
        }
        if (currentData.email && currentData.email !== 'pular') {
          summaryParts.push(`📧 *E-mail:* ${currentData.email}`);
        } else {
          summaryParts.push(`📧 *E-mail:* _Não informado (documentos via WhatsApp)_`);
        }
        if (currentData.city) {
          summaryParts.push(`🏙️ *Cidade:* ${currentData.city}`);
        }
        if (currentData.service_type || updateData.service_type) {
          const serviceEmoji = {
            'Energia Solar': '☀️',
            'Subestação': '⚡',
            'Projetos Elétricos': '📐',
            'BESS': '🔋',
            'Análise e Laudos': '📊'
          }[currentData.service_type || updateData.service_type] || '🔧';
          summaryParts.push(`${serviceEmoji} *Serviço:* ${currentData.service_type || updateData.service_type}`);
        }

        const summary = summaryParts.join('\n');
        responseText = `❌ *Opção inválida*\n\nPor favor, responda *"sim"* ou *"não"*\n\n` +
                      templates.confirmation.replace('{{summary}}', summary);
        nextStage = currentStage;
      }

      updateData.errorCount = errorCountLocal;
    }

    console.log('✅ V60: Confirmation state complete');
    break;

  // ============================================================================
  // V60 NEW FEATURE: CORRECTION MENU STATE
  // ============================================================================
  case 'correction_menu':
  case 'menu_correcao':
    console.log('V60: Processing CORRECTION_MENU state');

    const correctionMap = {
      '1': { field: 'lead_name', nextState: 'collect_name', clearFields: ['lead_name'] },
      '2': { field: 'phone_number', nextState: 'collect_phone', clearFields: ['phone_number', 'contact_phone', 'phone'] },
      '3': { field: 'email', nextState: 'collect_email', clearFields: ['email'] },
      '4': { field: 'city', nextState: 'collect_city', clearFields: ['city'] },
      '5': { field: 'service_type', nextState: 'service_selection', clearFields: ['service_type', 'service_selected'] }
    };

    const correction = correctionMap[message];

    if (correction) {
      console.log(`V60: User wants to correct ${correction.field}`);

      // Clear the selected field(s)
      correction.clearFields.forEach(field => {
        if (currentData[field]) {
          currentData[field] = null;
          updateData[field] = null;
        }
      });

      // Get appropriate template
      const stateTemplates = {
        'collect_name': templates.collect_name,
        'collect_phone': templates.collect_phone,
        'collect_email': templates.collect_email,
        'collect_city': templates.collect_city,
        'service_selection': templates.greeting
      };

      responseText = stateTemplates[correction.nextState] || templates.greeting;
      nextStage = correction.nextState;
      updateData.correcting = correction.field;
      updateData.errorCount = 0;
    } else {
      console.log('V60: Invalid correction menu option');
      // GAP #7: Error handling ✅
      const errorCountLocal = (currentData.errorCount || 0) + 1;

      if (errorCountLocal >= 3) {
        responseText = `❌ *Desculpe, tivemos dificuldade*\n\nVocê gostaria de:\n\n1️⃣ - Voltar ao menu principal\n2️⃣ - Falar com um atendente\n\n💡 _Responda 1 ou 2_`;
        nextStage = 'error_recovery';
      } else {
        responseText = `❌ *Opção inválida*\n\nPor favor, escolha um número de 1 a 5:\n\n` + templates.correction_menu;
        nextStage = currentStage;
      }

      updateData.errorCount = errorCountLocal;
    }

    console.log('✅ V60: Correction menu state complete');
    break;
"""

# ============================================================================
# MAIN SCRIPT
# ============================================================================
def main():
    print("=" * 60)
    print("V60.1 Complete Solution - Workflow Generator (FUNCTIONCODE FIX)")
    print("=" * 60)
    print()

    # Paths
    base_dir = Path(__file__).parent.parent
    v58_1_file = base_dir / "n8n" / "workflows" / "02_ai_agent_conversation_V58_1_UX_REFACTOR_COMPLETE.json"
    v60_1_file = base_dir / "n8n" / "workflows" / "02_ai_agent_conversation_V60_1_FUNCTIONCODE_FIX.json"

    # Step 1: Read V58.1 workflow
    print("📖 Reading V58.1 workflow")
    with open(v58_1_file, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    print(f"✅ Loaded: {workflow['name']}")
    print(f"   Nodes: {len(workflow['nodes'])}")
    print()

    # Step 2: Find State Machine Logic node
    print("🔍 Locating State Machine Logic node")
    state_machine_node = None
    for node in workflow['nodes']:
        if node['name'] == 'State Machine Logic':
            state_machine_node = node
            break

    if not state_machine_node:
        print("❌ ERROR: State Machine Logic node not found")
        return

    print(f"✅ Found node: {state_machine_node['name']}")
    print()

    # Step 3: Get JavaScript code from FUNCTIONCODE (n8n actually executes this)
    print("📝 Extracting JavaScript code from functionCode")

    if 'functionCode' not in state_machine_node['parameters']:
        print("❌ ERROR: functionCode field not found")
        return

    js_code = state_machine_node['parameters']['functionCode']
    print(f"✅ Extracted: {len(js_code):,} characters")
    print()

    # Step 4: Replace templates
    print("🔄 Replacing templates with V59 rich templates")

    # Find and replace templates constant
    templates_pattern = r'const templates = \{.*?\n\};'
    match = re.search(templates_pattern, js_code, re.DOTALL)

    if not match:
        print("❌ ERROR: Templates constant not found")
        return

    old_templates = match.group(0)
    print(f"✅ Found templates constant: {len(old_templates):,} chars")

    js_code = js_code.replace(old_templates, V59_TEMPLATES)
    print(f"✅ Replaced with V59 templates: {len(V59_TEMPLATES):,} chars")
    print()

    # Step 5: Add V60 confirmation logic
    print("➕ Adding V60 confirmation and correction_menu states")

    # Find insertion point (before default case in switch)
    default_pattern = r'(\s+default:)'
    match = re.search(default_pattern, js_code)

    if not match:
        print("❌ ERROR: Default case not found in switch statement")
        return

    insertion_point = match.start()
    js_code = js_code[:insertion_point] + V60_CONFIRMATION_LOGIC + js_code[insertion_point:]

    print(f"✅ Inserted V60 confirmation logic: {len(V60_CONFIRMATION_LOGIC):,} chars")
    print()

    # Step 6: Update stateNameMapping
    print("🔄 Updating stateNameMapping")

    state_mapping_pattern = r'(const stateNameMapping = \{[^}]+)(\};)'
    match = re.search(state_mapping_pattern, js_code, re.DOTALL)

    if match:
        original_mapping = match.group(0)
        # Add V60 states before closing brace
        new_mapping = original_mapping.replace('};', ''',

  // V60 NEW MAPPINGS (2 ENTRIES)
  'correction_menu': 'correction_menu',
  'menu_correcao': 'correction_menu'
};''')

        js_code = js_code.replace(original_mapping, new_mapping)
        print("✅ Added V60 state mappings: 2 entries")
    else:
        print("⚠️ WARNING: Could not find stateNameMapping (proceeding anyway)")

    print()

    # Step 7: Update node with new code in FUNCTIONCODE
    print("🔄 Updating State Machine Logic node (functionCode)")
    state_machine_node['parameters']['functionCode'] = js_code

    # CRITICAL: Remove jsCode field if it exists (n8n ignores it anyway)
    if 'jsCode' in state_machine_node['parameters']:
        del state_machine_node['parameters']['jsCode']
        print("✅ Removed jsCode field (n8n doesn't use it)")

    print(f"✅ Updated State Machine Logic node: {len(js_code):,} characters")
    print()

    # Step 8: Update workflow metadata
    workflow['name'] = '02 - AI Agent V60.1 (Complete Solution - FUNCTIONCODE FIX)'
    workflow['settings']['executionOrder'] = 'v1'

    if 'meta' not in workflow:
        workflow['meta'] = {}

    workflow['meta']['instanceId'] = 'v60.1-functioncode-fix'

    # Step 9: Write V60.1 workflow
    print("💾 Writing V60.1 workflow")
    with open(v60_1_file, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    file_size = v60_1_file.stat().st_size
    print(f"✅ Wrote: {file_size:,} bytes")
    print()

    # Summary
    print("📊 Changes Applied:")
    print(f"   ✅ Templates: V58.1 → V59 (16 rich templates)")
    print(f"   ✅ States: Added confirmation + correction_menu")
    print(f"   ✅ Logic: {{{{summary}}}} generation ON-THE-FLY")
    print(f"   ✅ Mapping: 2 new state mappings")
    print(f"   ✅ CRITICAL FIX: Updated functionCode (n8n executes this)")
    print(f"   ✅ CRITICAL FIX: Removed jsCode (n8n ignores it)")
    print()
    print("=" * 60)
    print("✅ V60.1 WORKFLOW GENERATION COMPLETE")
    print("=" * 60)
    print()
    print("📁 Output file:", v60_1_file)
    print()
    print("🚀 Next Steps:")
    print("   1. Import V60.1 to n8n: http://localhost:5678")
    print("   2. Deactivate V58.1")
    print("   3. Activate V60.1")
    print("   4. Test WhatsApp conversation")
    print("   5. Verify rich templates appear correctly")
    print()

if __name__ == '__main__':
    main()
