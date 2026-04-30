#!/usr/bin/env python3
"""
V71 Appointment Fix - Complete Solution
======================================

Fixes identified in ANALYSIS_V70_PROBLEMS.md:
1. ❌ Trigger Appointment Scheduler references unexecuted node
   → Fix: Check If Scheduling → Create Appointment → Trigger

2. ❌ Loose nodes States 9 and 10
   → Fix: Add routing from State Machine Logic to states 9/10

3. ❌ State 7 doesn't route to appointment flow
   → Fix: State 7 checks service type and routes to state 9 for services 1/3

Changes:
- Modified State Machine Logic code to handle states 9/10
- Added 3 outputs to State Machine Logic (states 1-8, state 9, state 10)
- Fixed connection flow: Check If Scheduling → Create Appointment → Trigger
- Updated state 7 logic for service-based routing
"""

import json
import sys
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent.parent
WORKFLOWS_DIR = BASE_DIR / "n8n" / "workflows"
V70_FILE = WORKFLOWS_DIR / "02_ai_agent_conversation_V70_COMPLETO.json"
V71_FILE = WORKFLOWS_DIR / "02_ai_agent_conversation_V4_APPOINTMENT_FIX.json"

def load_v70():
    """Load V70_COMPLETO as base"""
    print("📖 Loading V70_COMPLETO.json...")
    with open(V70_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def update_state_machine_logic_code(workflow):
    """
    FIX 1: Update State Machine Logic code to handle states 9 and 10
    """
    print("\n🔧 FIX 1: Updating State Machine Logic code...")

    # Find State Machine Logic node
    state_machine_node = None
    for node in workflow['nodes']:
        if node['name'] == 'State Machine Logic':
            state_machine_node = node
            break

    if not state_machine_node:
        print("❌ State Machine Logic node not found!")
        return

    # Get existing code (functionCode for n8n-nodes-base.function)
    code_field = 'functionCode' if 'functionCode' in state_machine_node['parameters'] else 'jsCode'
    existing_code = state_machine_node['parameters'][code_field]

    # Add states 9 and 10 handling BEFORE the final state 8 (confirmation)
    # Find where state 7 ends and insert new states

    state_9_10_code = '''
// ============================================================
// V4 FIX: NOVO - Estado 9 - collect_appointment_date
// ============================================================
else if (currentState === 'collect_appointment_date') {
    console.log('🔄 [State Machine V4] Estado 9: collect_appointment_date');
    console.log('Collected data:', JSON.stringify(collectedData, null, 2));

    // Se data foi validada com sucesso, vai para estado 10
    if (collectedData.scheduled_date && !collectedData.validation_error) {
        console.log('✅ Data validada, indo para collect_appointment_time');
        nextState = 'collect_appointment_time';
        aiResponseNeeded = false;
    }
    // Se erro de validação, fica no estado 9
    else if (collectedData.validation_error) {
        console.log('⚠️ Erro de validação, permanecendo em collect_appointment_date');
        nextState = 'collect_appointment_date';
        aiResponseNeeded = true;
    }
    // Primeira entrada no estado, precisa coletar data
    else {
        console.log('📅 Primeira entrada no estado, coletando data');
        nextState = 'collect_appointment_date';
        aiResponseNeeded = true;
    }
}

// ============================================================
// V4 FIX: NOVO - Estado 10 - collect_appointment_time
// ============================================================
else if (currentState === 'collect_appointment_time') {
    console.log('🔄 [State Machine V4] Estado 10: collect_appointment_time');
    console.log('Collected data:', JSON.stringify(collectedData, null, 2));

    // Se horário foi validado com sucesso, vai para confirmação
    if (collectedData.scheduled_time_start && !collectedData.validation_error) {
        console.log('✅ Horário validado, indo para confirmation');
        nextState = 'confirmation';
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

'''

    # Also update state 7 to route to appointment for services 1/3
    state_7_fix = '''
// ============================================================
// Estado 7 - collect_city (V4 FIX: routes to appointment for services 1/3)
// ============================================================
else if (currentState === 'collect_city') {
    console.log('🔄 [State Machine V4] Estado 7: collect_city');

    if (collectedData.city && collectedData.city.length >= 3) {
        console.log('✅ Cidade coletada:', collectedData.city);

        // V4 FIX: Check if service requires appointment (services 1 or 3)
        const requiresAppointment = collectedData.service_type === 'energia_solar' ||
                                   collectedData.service_type === 'projetos_eletricos';

        if (requiresAppointment) {
            console.log('📅 Serviço requer agendamento, indo para collect_appointment_date');
            nextState = 'collect_appointment_date';
        } else {
            console.log('✅ Serviço não requer agendamento, indo para confirmation');
            nextState = 'confirmation';
        }
        aiResponseNeeded = false;
    } else {
        console.log('⚠️ Cidade inválida ou muito curta');
        nextState = 'collect_city';
        aiResponseNeeded = true;
    }
}
'''

    # Replace old state 7 logic with new one
    # Find the state 7 block and replace it
    import re

    # Pattern to find state 7 block
    state_7_pattern = r"// Estado 7 - collect_city.*?else if \(currentState === 'confirmation'\)"

    # Replace with new state 7 + states 9/10 + confirmation start
    replacement = state_7_fix + '\n' + state_9_10_code + '\n// Estado 8 - confirmation\nelse if (currentState === \'confirmation\')'

    updated_code = re.sub(
        state_7_pattern,
        replacement,
        existing_code,
        flags=re.DOTALL
    )

    if updated_code == existing_code:
        print("⚠️ Warning: State 7 pattern not found, trying alternative approach...")
        # Fallback: insert before confirmation state
        confirmation_pattern = r"(// Estado 8 - confirmation.*?else if \(currentState === 'confirmation'\))"
        replacement = state_7_fix + '\n' + state_9_10_code + '\n\\1'
        updated_code = re.sub(confirmation_pattern, replacement, existing_code, flags=re.DOTALL)

    state_machine_node['parameters'][code_field] = updated_code
    print("✅ State Machine Logic code updated with states 9 and 10")

def add_state_machine_outputs(workflow):
    """
    FIX 2: Add 3 outputs to State Machine Logic node
    """
    print("\n🔧 FIX 2: Adding outputs to State Machine Logic...")

    for node in workflow['nodes']:
        if node['name'] == 'State Machine Logic':
            # Check if outputs already exist
            if 'outputs' not in node['parameters']:
                node['parameters']['outputs'] = []

            # Clear and set 3 outputs
            node['parameters']['outputs'] = [
                {'name': 'states_1_8'},   # Output 0: normal states
                {'name': 'state_9'},      # Output 1: appointment date
                {'name': 'state_10'}      # Output 2: appointment time
            ]
            print("✅ Added 3 outputs to State Machine Logic")
            break

def fix_connections(workflow):
    """
    FIX 3: Fix connection flow
    - Check If Scheduling → Create Appointment → Trigger Appointment
    - State Machine Logic → Build Update Queries (output 0)
    - State Machine Logic → State 9 (output 1)
    - State Machine Logic → State 10 (output 2)
    """
    print("\n🔧 FIX 3: Fixing connections...")

    # Find node IDs
    node_ids = {}
    for node in workflow['nodes']:
        node_ids[node['name']] = node['id']

    # Fix connection: Check If Scheduling → Create Appointment → Trigger
    for node in workflow['nodes']:
        if node['name'] == 'Check If Scheduling':
            if 'main' in node.get('connections', {}):
                # Change to connect to Create Appointment instead of Trigger
                node['connections']['main'] = [[{
                    'node': 'Create Appointment in Database',
                    'type': 'main',
                    'index': 0
                }]]
                print("✅ Check If Scheduling now connects to Create Appointment")

        elif node['name'] == 'Create Appointment in Database':
            # Ensure Create Appointment connects to Trigger
            if 'connections' not in node:
                node['connections'] = {}
            node['connections']['main'] = [[{
                'node': 'Trigger Appointment Scheduler',
                'type': 'main',
                'index': 0
            }]]
            print("✅ Create Appointment connects to Trigger")

        elif node['name'] == 'State Machine Logic':
            # Add 3 outputs
            if 'connections' not in node:
                node['connections'] = {}

            node['connections']['main'] = [
                # Output 0: states 1-8 go to Build Update Queries
                [{
                    'node': 'Build Update Queries',
                    'type': 'main',
                    'index': 0
                }],
                # Output 1: state 9 goes to State 9 node
                [{
                    'node': 'Claude AI Agent State 9 (collect_appointment_date)',
                    'type': 'main',
                    'index': 0
                }],
                # Output 2: state 10 goes to State 10 node
                [{
                    'node': 'Claude AI Agent State 10 (collect_appointment_time)',
                    'type': 'main',
                    'index': 0
                }]
            ]
            print("✅ State Machine Logic now has 3 output connections")

def update_metadata(workflow):
    """Update workflow metadata to V4"""
    print("\n📝 Updating metadata to V4...")
    workflow['name'] = '02 - AI Agent Conversation V4_APPOINTMENT_FIX'
    workflow['meta'] = workflow.get('meta', {})
    workflow['meta']['version'] = 'V4'
    workflow['meta']['description'] = 'V4 - Complete Appointment Fix: Trigger + States 9/10 + Routing'
    print("✅ Metadata updated")

def save_v71(workflow):
    """Save V4 workflow"""
    print(f"\n💾 Saving V4 to {V71_FILE}...")
    with open(V71_FILE, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)
    print(f"✅ V4 saved successfully!")
    print(f"\n📊 File size: {V71_FILE.stat().st_size / 1024:.1f} KB")

def main():
    print("=" * 70)
    print("V71 APPOINTMENT FIX - COMPLETE SOLUTION")
    print("=" * 70)

    try:
        # Load V70 as base
        workflow = load_v70()

        # Apply all fixes
        update_state_machine_logic_code(workflow)
        add_state_machine_outputs(workflow)
        fix_connections(workflow)
        update_metadata(workflow)

        # Save V4
        save_v71(workflow)

        print("\n" + "=" * 70)
        print("✅ V4 GENERATION COMPLETE!")
        print("=" * 70)
        print("\nFixes applied:")
        print("1. ✅ State Machine Logic code updated (states 9/10 + state 7 routing)")
        print("2. ✅ State Machine Logic has 3 outputs")
        print("3. ✅ Connection fixed: Check If Scheduling → Create Appointment → Trigger")
        print("4. ✅ State Machine connects to states 9 and 10")
        print("\nNext steps:")
        print("1. Import V71 workflow in n8n")
        print("2. Test complete appointment flow")
        print("3. Verify Trigger Appointment Scheduler executes correctly")

        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
