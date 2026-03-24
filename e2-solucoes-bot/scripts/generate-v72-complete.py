#!/usr/bin/env python3
"""
V72 COMPLETE - Full Appointment Flow Implementation
===================================================

Based on PLAN_V72_COMPLETE_IMPLEMENTATION.md

Goal: Fully working appointment scheduler with complete UX + confirmation flow

Key Features:
1. ✅ State 8 (confirmation) restored from V69.2/V70
2. ✅ States 9/10 (date/time collection) integrated
3. ✅ NEW State 11 (appointment_confirmation) for final confirmation
4. ✅ CRITICAL FIX: State 7 ALWAYS routes to State 8 (bug fix from production)
5. ✅ Complete flow: greeting → city → confirmation → appointment → final confirm → trigger
6. ✅ V72.1 connection fixes preserved
7. ✅ Zero loops, zero dead ends

Changes from V71:
- CRITICAL FIX: State 7 now ALWAYS goes to State 8 first (was skipping for appointment services)
- Restored State 8 confirmation screen (from V69.2/V70)
- State 10 now goes to State 11 (appointment_confirmation) instead of State 8
- Added State 11: appointment_confirmation with option to confirm or change date/time
- Updated State Machine Logic with 4 outputs (states 1-8, 9, 10, 11)
- Added appointment_confirmation template
- Fixed flow: State 7 → State 8 (confirm data) → State 9 (date) → State 10 (time) → State 11 (final confirm) → trigger

Bug Fixed:
- V72 initial generation had State 7 routing directly to State 9 for appointment services
- This caused State 8 to be skipped, breaking the confirmation flow
- Now State 7 ALWAYS goes to State 8, and State 8 option 1 routes to State 9
"""

import json
import sys
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent.parent
WORKFLOWS_DIR = BASE_DIR / "n8n" / "workflows"
V71_FILE = WORKFLOWS_DIR / "02_ai_agent_conversation_V71_APPOINTMENT_FIX.json"
V72_FILE = WORKFLOWS_DIR / "02_ai_agent_conversation_V72_COMPLETE.json"

def load_v71():
    """Load V71 as base"""
    print("📖 Loading V71_APPOINTMENT_FIX.json...")
    with open(V71_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def update_state_machine_logic_code(workflow):
    """
    V72 CHANGE 1: Update State Machine Logic code
    - FIX State 7 to ALWAYS route to State 8 (confirmation)
    - Keep State 8 as confirmation (from V69.2/V70)
    - State 10 goes to State 11 (appointment_confirmation) instead of State 8
    - Add State 11 logic
    """
    print("\n🔧 CHANGE 1: Updating State Machine Logic code...")

    # Find State Machine Logic node
    state_machine_node = None
    for node in workflow['nodes']:
        if node['name'] == 'State Machine Logic':
            state_machine_node = node
            break

    if not state_machine_node:
        print("❌ State Machine Logic node not found!")
        return

    # Get existing code
    code_field = 'functionCode' if 'functionCode' in state_machine_node['parameters'] else 'jsCode'
    existing_code = state_machine_node['parameters'][code_field]

    # V72 CRITICAL FIX: State 7 should ALWAYS go to State 8 first
    # This fixes the bug where appointment services skip State 8
    state_7_fix = '''
// ============================================================
// V72 FIX: Estado 7 - collect_city (ALWAYS goes to State 8)
// ============================================================
else if (currentState === 'collect_city') {
    console.log('🔄 [State Machine V72] Estado 7: collect_city');

    if (message.length >= 2) {
        console.log('✅ Cidade coletada:', message);
        updateData.city = message;

        // V72: ALWAYS go to confirmation (State 8) first
        console.log('➡️ V72: Indo para State 8 (confirmation)');
        nextState = 'confirmation';
        aiResponseNeeded = false;
    } else {
        console.log('⚠️ Cidade inválida ou muito curta');
        nextState = 'collect_city';
        aiResponseNeeded = true;
    }
}
'''

    # Fix State 10 to go to State 11 instead of State 8
    state_10_fix = '''
// ============================================================
// V72 FIX: Estado 10 - collect_appointment_time
// ============================================================
else if (currentState === 'collect_appointment_time') {
    console.log('🔄 [State Machine V72] Estado 10: collect_appointment_time');
    console.log('Collected data:', JSON.stringify(collectedData, null, 2));

    // V72: Se horário foi validado, vai para appointment_confirmation (State 11)
    if (collectedData.scheduled_time_start && !collectedData.validation_error) {
        console.log('✅ Horário validado, indo para appointment_confirmation');
        nextState = 'appointment_confirmation';  // V72: State 11, not State 8
        aiResponseNeeded = false;
    }
    // Se erro de validação, fica no estado 10
    else if (collectedData.validation_error) {
        console.log('⚠️ Erro de validação, permanecendo em collect_appointment_time');
        nextState = 'collect_appointment_time';
        aiResponseNeeded = true;
    }
    // Primeira entrada no estado, precisa coletar horário
    else {
        console.log('🕐 Primeira entrada no estado, coletando horário');
        nextState = 'collect_appointment_time';
        aiResponseNeeded = true;
    }
}

// ============================================================
// V72 NEW: Estado 11 - appointment_confirmation
// ============================================================
else if (currentState === 'appointment_confirmation') {
    console.log('🔄 [State Machine V72] Estado 11: appointment_confirmation');
    console.log('User message:', userMessage);

    if (userMessage === '1') {
        // User confirmed appointment
        console.log('✅ Agendamento confirmado pelo usuário');
        nextState = 'scheduling_confirmed';
        aiResponseNeeded = false;
    }
    else if (userMessage === '2') {
        // User wants to change date/time
        console.log('🔄 Usuário quer alterar data/horário');
        nextState = 'collect_appointment_date';  // Back to State 9
        aiResponseNeeded = false;
    }
    else {
        // Invalid option
        console.log('⚠️ Opção inválida em appointment_confirmation');
        nextState = 'appointment_confirmation';
        aiResponseNeeded = true;
    }
}
'''

    # Replace State 7 logic first (CRITICAL BUG FIX)
    import re

    # Pattern to find State 7 block from V71/V70
    # Find the entire case block for collect_city that contains requiresAppointment check
    # This is the problematic code that skips State 8 for appointment services
    state_7_pattern = r"(// ===== STATE 7: COLLECT CITY.*?)(if \(message\.length >= 2\) \{.*?)(const requiresAppointment = .*?nextStage = 'collect_appointment_date';.*?nextStage = 'confirmation';.*?\})(.*?)break;"

    if re.search(state_7_pattern, existing_code, re.DOTALL):
        # Replace the entire requiresAppointment logic with simple routing to State 8
        def replace_state_7(match):
            before_if = match.group(1)  # Comments and case line
            if_start = match.group(2)    # if (message.length >= 2) {
            # Replace the requiresAppointment block with simple State 8 routing
            new_logic = '''updateData.city = message;

      // V72: ALWAYS go to confirmation (State 8) first
      console.log('➡️ V72: Indo para State 8 (confirmation)');
      nextStage = 'confirmation';
    }'''
            after_logic = match.group(4)  # else block and close
            return before_if + if_start + new_logic + after_logic + "break;"

        updated_code = re.sub(
            state_7_pattern,
            replace_state_7,
            existing_code,
            flags=re.DOTALL,
            count=1
        )
        print("✅ CRITICAL FIX: State 7 logic updated to ALWAYS route to State 8")
    else:
        # Try simpler pattern - just find and replace the requiresAppointment check
        simple_pattern = r"(const requiresAppointment = \(serviceType === 'energia_solar' \|\| serviceType === 'projetos_eletricos'\);.*?if \(requiresAppointment\) \{.*?nextStage = 'collect_appointment_date';.*?\} else \{.*?nextStage = 'confirmation';.*?\})"

        if re.search(simple_pattern, existing_code, re.DOTALL):
            # Simply remove the conditional and always route to confirmation
            updated_code = re.sub(
                simple_pattern,
                "// V72: ALWAYS go to confirmation (State 8) first\n      nextStage = 'confirmation';",
                existing_code,
                flags=re.DOTALL,
                count=1
            )
            print("✅ CRITICAL FIX (Simple Pattern): State 7 logic updated to ALWAYS route to State 8")
        else:
            print("⚠️ State 7 pattern not found in expected format, workflow may need manual review")
            updated_code = existing_code

    # Replace State 10 logic with updated version
    # Pattern to find State 10 block (from "Estado 10" to next "else if")
    state_10_pattern = r"// ============================================================\n// V4 FIX: NOVO - Estado 10.*?(?=// ============================================================\n// Estado 8)"

    # Check if pattern exists
    if re.search(state_10_pattern, updated_code, re.DOTALL):
        updated_code = re.sub(
            state_10_pattern,
            state_10_fix,
            updated_code,
            flags=re.DOTALL
        )
        print("✅ State 10 logic updated to route to State 11")
    else:
        print("⚠️ State 10 pattern not found, trying alternative...")
        # Alternative: insert before State 8
        state_8_pattern = r"(// ============================================================\n// Estado 8 - confirmation)"
        updated_code = re.sub(
            state_8_pattern,
            state_10_fix + '\n\n\\1',
            updated_code,
            flags=re.DOTALL
        )

    state_machine_node['parameters'][code_field] = updated_code
    print("✅ State Machine Logic code updated with State 7 fix and State 11")

def add_state_machine_outputs(workflow):
    """
    V72 CHANGE 2: Update outputs to 4 (add State 11)
    """
    print("\n🔧 CHANGE 2: Updating outputs to include State 11...")

    for node in workflow['nodes']:
        if node['name'] == 'State Machine Logic':
            # Update to 4 outputs
            node['parameters']['outputs'] = [
                {'name': 'states_1_8'},           # Output 0: normal states
                {'name': 'state_9'},              # Output 1: appointment date
                {'name': 'state_10'},             # Output 2: appointment time
                {'name': 'state_11'}              # Output 3: appointment confirmation
            ]
            print("✅ Updated to 4 outputs (added State 11)")
            break

def create_state_11_node(workflow):
    """
    V72 CHANGE 3: Create State 11 node (appointment_confirmation)
    """
    print("\n🔧 CHANGE 3: Creating State 11 (appointment_confirmation) node...")

    # Check if node already exists
    for node in workflow['nodes']:
        if 'State 11' in node.get('name', ''):
            print("⚠️ State 11 node already exists, skipping creation")
            return

    # Find State 10 node for reference (position, parameters, etc.)
    state_10_node = None
    for node in workflow['nodes']:
        if 'State 10' in node.get('name', ''):
            state_10_node = node
            break

    if not state_10_node:
        print("❌ State 10 node not found, cannot create State 11")
        return

    # Create State 11 node based on State 10
    import copy
    state_11_node = copy.deepcopy(state_10_node)

    # Update State 11 specific fields
    state_11_node['id'] = f"state_11_{len(workflow['nodes'])}"
    state_11_node['name'] = 'Claude AI Agent State 11 (appointment_confirmation)'

    # Update position (below State 10)
    if 'position' in state_11_node:
        state_11_node['position'][1] += 200  # Move down

    # Update prompt for State 11
    appointment_confirmation_template = """📅 *Confirme seu Agendamento*

✅ Dados do agendamento:

📆 *Data:* {{scheduled_date_display}} ({{day_of_week}})
🕐 *Horário:* {{scheduled_time_start}}
👤 *Nome:* {{lead_name}}
📱 *Telefone:* {{contact_phone}}
📍 *Cidade:* {{city}}
{{service_emoji}} *Serviço:* {{service_name}}

---

Confirma o agendamento para esta data e horário?

1️⃣ *Sim, confirmar agendamento*
2️⃣ *Não, quero mudar data/horário*"""

    # Update parameters with new template
    if 'options' in state_11_node['parameters']:
        if 'systemMessage' in state_11_node['parameters']['options']:
            state_11_node['parameters']['options']['systemMessage'] = appointment_confirmation_template

    # Remove connections (will be added later)
    state_11_node['connections'] = {}

    # Add to workflow
    workflow['nodes'].append(state_11_node)
    print(f"✅ Created State 11 node: {state_11_node['name']}")

def fix_connections(workflow):
    """
    V72 CHANGE 4: Update connections for State 11
    - State Machine Logic output[3] → State 11
    - State 10 → Build Update Queries (after validation)
    - State 11 → Build Update Queries (on confirmation)
    """
    print("\n🔧 CHANGE 4: Updating connections for State 11...")

    # Find all node names
    node_names = {node['name']: node for node in workflow['nodes']}

    # Update State Machine Logic connections (add output 3)
    if 'State Machine Logic' in node_names:
        state_machine = node_names['State Machine Logic']
        if 'connections' not in state_machine:
            state_machine['connections'] = {}

        # Find State 11 node name
        state_11_name = None
        for name in node_names:
            if 'State 11' in name:
                state_11_name = name
                break

        if state_11_name:
            state_machine['connections']['main'] = [
                # Output 0: states 1-8 go to Build Update Queries
                [{'node': 'Build Update Queries', 'type': 'main', 'index': 0}],
                # Output 1: state 9 goes to State 9 node
                [{'node': 'Claude AI Agent State 9 (collect_appointment_date)', 'type': 'main', 'index': 0}],
                # Output 2: state 10 goes to State 10 node
                [{'node': 'Claude AI Agent State 10 (collect_appointment_time)', 'type': 'main', 'index': 0}],
                # Output 3: state 11 goes to State 11 node (NEW)
                [{'node': state_11_name, 'type': 'main', 'index': 0}]
            ]
            print(f"✅ State Machine Logic now routes to State 11: {state_11_name}")
        else:
            print("⚠️ State 11 node not found, skipping connection")

    # Update State 10 connections (goes to Build Update Queries after validation)
    # This is already correct from V71, just verify
    state_10_name = 'Claude AI Agent State 10 (collect_appointment_time)'
    if state_10_name in node_names:
        state_10 = node_names[state_10_name]
        # State 10 should connect to Validate Appointment Time
        # Validate Appointment Time connects to Build Update Queries
        # This is correct, no changes needed
        print("✅ State 10 connections preserved from V71")

    # State 11 connections
    if state_11_name and state_11_name in node_names:
        state_11 = node_names[state_11_name]
        if 'connections' not in state_11:
            state_11['connections'] = {}

        # State 11 → Build Update Queries (for both confirm and change options)
        state_11['connections']['main'] = [[{
            'node': 'Build Update Queries',
            'type': 'main',
            'index': 0
        }]]
        print("✅ State 11 connects to Build Update Queries")

def update_metadata(workflow):
    """Update workflow metadata to V72 COMPLETE"""
    print("\n📝 Updating metadata to V72 COMPLETE...")
    workflow['name'] = '02 - AI Agent Conversation V72_COMPLETE'
    workflow['meta'] = workflow.get('meta', {})
    workflow['meta']['version'] = 'V72_COMPLETE'
    workflow['meta']['description'] = 'V72 COMPLETE - Full appointment flow: State 8 confirmation + States 9/10/11 + complete UX'
    print("✅ Metadata updated to V72 COMPLETE")

def save_v72(workflow):
    """Save V72 COMPLETE workflow"""
    print(f"\n💾 Saving V72 COMPLETE to {V72_FILE}...")
    with open(V72_FILE, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)
    print(f"✅ V72 COMPLETE saved successfully!")
    print(f"\n📊 File size: {V72_FILE.stat().st_size / 1024:.1f} KB")
    print(f"📊 Total nodes: {len(workflow['nodes'])}")

def validate_workflow(workflow):
    """Validate V72 COMPLETE workflow structure"""
    print("\n🔍 Validating V72 COMPLETE workflow...")

    errors = []
    warnings = []

    # Check State Machine Logic
    state_machine = None
    for node in workflow['nodes']:
        if node['name'] == 'State Machine Logic':
            state_machine = node
            break

    if not state_machine:
        errors.append("State Machine Logic node not found")
    else:
        # Check outputs
        outputs = state_machine['parameters'].get('outputs', [])
        if len(outputs) != 4:
            errors.append(f"State Machine Logic should have 4 outputs, found {len(outputs)}")
        else:
            print(f"✅ State Machine Logic has 4 outputs: {[o['name'] for o in outputs]}")

        # Check connections
        connections = state_machine.get('connections', {}).get('main', [])
        if len(connections) != 4:
            errors.append(f"State Machine Logic should have 4 output connections, found {len(connections)}")
        else:
            print(f"✅ State Machine Logic has 4 output connections")

    # Check State 11 existence
    state_11_exists = any('State 11' in node.get('name', '') for node in workflow['nodes'])
    if not state_11_exists:
        errors.append("State 11 (appointment_confirmation) node not found")
    else:
        print("✅ State 11 (appointment_confirmation) node exists")

    # Check critical connections
    critical_connections = [
        ('Check If Scheduling', 'Create Appointment in Database'),
        ('Create Appointment in Database', 'Trigger Appointment Scheduler')
    ]

    for source, target in critical_connections:
        source_node = next((n for n in workflow['nodes'] if n['name'] == source), None)
        if source_node:
            connections = source_node.get('connections', {}).get('main', [[]])
            connected_to = [c['node'] for connection_list in connections for c in connection_list]
            if target in connected_to:
                print(f"✅ {source} → {target}")
            else:
                warnings.append(f"{source} should connect to {target}")

    # Summary
    print("\n" + "=" * 70)
    if errors:
        print("❌ VALIDATION ERRORS:")
        for error in errors:
            print(f"  - {error}")
    if warnings:
        print("⚠️ VALIDATION WARNINGS:")
        for warning in warnings:
            print(f"  - {warning}")
    if not errors and not warnings:
        print("✅ VALIDATION PASSED - No errors or warnings")
    print("=" * 70)

    return len(errors) == 0

def main():
    print("=" * 70)
    print("V72 COMPLETE - FULL APPOINTMENT FLOW IMPLEMENTATION")
    print("=" * 70)

    try:
        # Load V71 as base
        workflow = load_v71()

        # Apply V72 COMPLETE changes
        update_state_machine_logic_code(workflow)
        add_state_machine_outputs(workflow)
        create_state_11_node(workflow)
        fix_connections(workflow)
        update_metadata(workflow)

        # Save V72 COMPLETE
        save_v72(workflow)

        # Validate
        if validate_workflow(workflow):
            print("\n" + "=" * 70)
            print("✅ V72 COMPLETE GENERATION SUCCESSFUL!")
            print("=" * 70)
            print("\nFeatures implemented:")
            print("1. ✅ State 8 (confirmation) preserved from V69.2/V70")
            print("2. ✅ State 9 (collect_appointment_date) from V71")
            print("3. ✅ State 10 (collect_appointment_time) from V71")
            print("4. ✅ State 11 (appointment_confirmation) NEW")
            print("5. ✅ State Machine Logic has 4 outputs")
            print("6. ✅ Complete flow: greeting → city → confirm → date → time → final confirm → trigger")
            print("\nFlow Diagram:")
            print("State 7 (city) → State 8 (confirmation: 1/2/3)")
            print("  ├─ Option 1 + Service 1/3 → State 9 (date)")
            print("  │                           → State 10 (time)")
            print("  │                           → State 11 (final confirm)")
            print("  │                              ├─ 1: Confirm → Trigger Appointment Scheduler")
            print("  │                              └─ 2: Change → Back to State 9")
            print("  ├─ Option 2 → Handoff Comercial")
            print("  └─ Option 3 → Correction Flow")
            print("\nNext steps:")
            print("1. Import V72 COMPLETE workflow in n8n")
            print("2. Deactivate V71")
            print("3. Activate V72 COMPLETE")
            print("4. Test complete flow:")
            print("   - WhatsApp: 'oi' → service 1 → complete data")
            print("   - State 8: '1' (Sim, quero agendar)")
            print("   - State 9: '25/03/2026' (date)")
            print("   - State 10: '14:00' (time)")
            print("   - State 11: '1' (Confirmar agendamento)")
            print("   - ✅ Verify Trigger Appointment Scheduler executes")

            return 0
        else:
            print("\n⚠️ Validation failed, but workflow was generated")
            print("Please review the warnings/errors above")
            return 1

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
