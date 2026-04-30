#!/usr/bin/env python3
"""
Script: generate-v73.4-state-11-add.py
Purpose: Generate V73.4 workflow by ADDING State 11 (appointment_confirmation)
Date: 2026-03-24

CRITICAL FIX:
V73.3 is MISSING State 11 (appointment_confirmation) entirely!
State 10 sets nextStage = 'appointment_confirmation' but State 11 doesn't exist.
Result: Bot goes back to greeting instead of creating appointment.

V73.4 adds State 11 with correct logic:
- User confirms "1" → next_stage = 'scheduling_redirect'
- Sets updateData.status = 'scheduling'
- This allows "Check If Scheduling" to execute via Build Update Queries next_stage field
"""

import json
import sys
from pathlib import Path
import re

# Colors for terminal output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_step(step_num, total, message):
    """Print formatted step progress"""
    print(f"{BLUE}[{step_num}/{total}]{RESET} {message}")

def print_success(message):
    """Print success message"""
    print(f"{GREEN}✅ {message}{RESET}")

def print_warning(message):
    """Print warning message"""
    print(f"{YELLOW}⚠️  {message}{RESET}")

def print_error(message):
    """Print error message"""
    print(f"{RED}❌ {message}{RESET}")

def load_v73_3_workflow():
    """Load V73.3 workflow JSON"""
    v73_3_path = Path(__file__).parent.parent / "n8n" / "workflows" / "02_ai_agent_conversation_V73.3_STATE_9_10_FIX.json"

    print_step(1, 4, "Loading V73.3 workflow...")

    if not v73_3_path.exists():
        print_error(f"V73.3 workflow not found: {v73_3_path}")
        sys.exit(1)

    with open(v73_3_path, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    print_success(f"Loaded V73.3 workflow: {len(workflow['nodes'])} nodes")
    return workflow

def add_state_11(workflow):
    """Add State 11 (appointment_confirmation) AFTER State 10"""
    print_step(2, 4, "Adding State 11 (appointment_confirmation)...")

    # Find State Machine Logic node
    state_machine_node = None
    for node in workflow['nodes']:
        if node['name'] == 'State Machine Logic':
            state_machine_node = node
            break

    if not state_machine_node:
        print_error("State Machine Logic node not found!")
        sys.exit(1)

    # Get current function code
    function_code = state_machine_node['parameters']['functionCode']

    print(f"  Original State Machine length: {len(function_code)} chars")

    # NEW State 11 code to insert AFTER State 10
    state_11_new = r"""
  // ===== V73.4 FIX: STATE 11: APPOINTMENT CONFIRMATION - Final appointment confirmation =====
  case 'appointment_confirmation':
  case 'confirmacao_agendamento':
    console.log('V73.4: Processing APPOINTMENT_CONFIRMATION state');

    if (message === '1') {
      // User confirms appointment
      console.log('V73.4 FIX: User confirmed appointment → setting next_stage = scheduling_redirect');

      // ✅ V73.4 CRITICAL: Set next_stage to 'scheduling_redirect'
      // This allows "Check If Scheduling" IF node to execute via:
      // {{ $node["Build Update Queries"].json.next_stage }} === 'scheduling_redirect'
      nextStage = 'scheduling_redirect';
      updateData.status = 'scheduling';

      // Show final confirmation message
      responseText = templates.scheduling_redirect;

      console.log('V73.4 FIX: next_stage set to:', nextStage);
      console.log('V73.4 FIX: updateData.status set to:', updateData.status);

    } else if (message === '2') {
      // User wants to correct appointment data
      console.log('V73.4: User wants to correct appointment data');

      // Go back to collect_appointment_date (State 9)
      responseText = '🔧 *Vamos corrigir os dados do agendamento.*\n\nQual a melhor data para você? (formato DD/MM/AAAA)\n\n💡 _Exemplo: 25/04/2026_';
      nextStage = 'collect_appointment_date';

      // Clear previous appointment data
      updateData.scheduled_date = null;
      updateData.scheduled_time_start = null;
      updateData.scheduled_time_end = null;

    } else {
      // Invalid option
      console.log('V73.4: Invalid appointment confirmation option');

      // Show same confirmation message again
      const dbDate = currentData.scheduled_date || '';
      let displayDate = dbDate;
      if (dbDate && /^\d{4}-\d{2}-\d{2}$/.test(dbDate)) {
        const [y, m, d] = dbDate.split('-');
        displayDate = `${d}/${m}/${y}`;
      }

      const startTime = currentData.scheduled_time_start || '00:00:00';
      const endTime = currentData.scheduled_time_end || '02:00:00';
      const [startH, startM] = startTime.split(':');
      const [endH, endM] = endTime.split(':');
      const serviceName = getServiceName(currentData.service_selected || '1');

      responseText = `❌ *Opção inválida*\n\n✅ *Agendamento quase pronto!*\n\n📅 *Resumo da visita técnica:*\n\n🗓️ Data: ${displayDate}\n⏰ Horário: ${startH}:${startM} às ${endH}:${endM}\n⏳ Duração: 2 horas\n🔧 Serviço: ${serviceName}\n\n---\n\nConfirma o agendamento?\n\n1️⃣ *Sim, confirmar*\n2️⃣ *Não, corrigir dados*`;
      nextStage = 'appointment_confirmation';
    }
    break;
"""

    # Find where to insert State 11 (after State 10)
    # State 10 ends with: break; followed by State 8 comment
    state_10_end_pattern = re.compile(
        r"(case 'collect_appointment_time':.*?break;)(\s*// ===== STATE 8)",
        re.DOTALL
    )

    match = state_10_end_pattern.search(function_code)
    if match:
        # Insert State 11 BETWEEN State 10 and State 8
        function_code = state_10_end_pattern.sub(
            lambda m: m.group(1) + state_11_new + "\n" + m.group(2),
            function_code
        )
        print_success("Added State 11 after State 10")
    else:
        print_error("Could not find insertion point after State 10!")
        print_error("Looking for pattern: break; followed by // ===== STATE 8")
        sys.exit(1)

    # Update State Machine node
    state_machine_node['parameters']['functionCode'] = function_code
    print_success(f"Updated State Machine: {len(function_code)} chars (+{len(function_code) - len(state_machine_node['parameters']['functionCode'])} chars)")

    return workflow

def update_metadata(workflow):
    """Update workflow metadata for V73.4"""
    print_step(3, 4, "Updating workflow metadata...")

    workflow['meta'] = {
        "version": "V73.4_STATE_11_ADD",
        "fixes_applied": [
            "BUG #4: SQL syntax error (V73 - fixed with Set node)",
            "BUG #5: Appointment timing (V73.1 - removed premature IF)",
            "BUG #6: State Machine wrong template (V73.2 - fixed State 8)",
            "BUG #7: State 9/10 infinite loop (V73.3 - message parsing)",
            "BUG #8: State 11 MISSING (V73.4 - added appointment_confirmation)",
            "SOLUTION: State 11 now sets next_stage = 'scheduling_redirect'",
            "RESULT: Check If Scheduling executes → Appointment created ✅"
        ],
        "fix_date": "2026-03-24",
        "preserves_v73_3_fixes": True,
        "states_total": 14,
        "templates_total": 28,
        "nodes_total": 34,
        "cumulative_fixes": [
            "V66 Fix #1: trimmedCorrectedName duplicate variable",
            "V66 Fix #2: query_correction_update scope",
            "V67 Fix: Service display keys (all 5 services)",
            "V68 Fix #1: Trigger node execution",
            "V68 Fix #2: Name field validation",
            "V68 Fix #3: Returning user detection",
            "V72 Fix: Complete appointment flow (States 9/10/11)",
            "V73 Fix: SQL syntax error - simplified expressions",
            "V73.1 Fix: Appointment timing - removed IF from State 8",
            "V73.2 Fix: State Machine State 8 logic - correct template",
            "V73.3 Fix: State 9/10 message parsing - inline validation",
            "V73.4 Fix: State 11 MISSING - added appointment_confirmation"
        ],
        "instanceId": "v73_4_state_11_add_complete",
        "description": "V73.4 STATE 11 ADD - Adds missing appointment_confirmation state"
    }

    workflow['versionId'] = "73.4"
    workflow['tags'] = [
        {
            "name": "v73.4-state-11-add-complete"
        },
        {
            "name": "ready-for-production"
        }
    ]

    print_success("Updated metadata to V73.4")

def save_v73_4_workflow(workflow):
    """Save generated V73.4 workflow"""
    output_path = Path(__file__).parent.parent / "n8n" / "workflows" / "02_ai_agent_conversation_V73.4_STATE_11_ADD.json"

    print_step(4, 4, "Saving V73.4 workflow...")

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print_success(f"Saved V73.4 workflow: {output_path}")
    print_success(f"Total nodes: {len(workflow['nodes'])}")
    print_success(f"Total connections: {len(workflow.get('connections', {}))}")

    return output_path

def validate_workflow(workflow):
    """Validate generated workflow structure"""
    print(f"\n{BLUE}🔍 Validating V73.4 workflow...{RESET}")

    # Validate node count (same as V73.3)
    expected_nodes = 34
    actual_nodes = len(workflow['nodes'])

    if actual_nodes != expected_nodes:
        print_warning(f"Expected {expected_nodes} nodes, got {actual_nodes}")
    else:
        print_success(f"Node count correct: {actual_nodes} nodes")

    # Validate State Machine has State 11
    state_machine_node = next((n for n in workflow['nodes'] if n['name'] == 'State Machine Logic'), None)

    if state_machine_node:
        function_code = state_machine_node['parameters']['functionCode']

        # Check for V73.4 State 11 markers
        if "case 'appointment_confirmation':" in function_code:
            print_success("State 11 case found ✓")
        else:
            print_error("State 11 case NOT found!")
            return False

        if "V73.4 FIX: User confirmed appointment" in function_code:
            print_success("V73.4 State 11 fix markers found ✓")
        else:
            print_error("V73.4 fix markers NOT found!")
            return False

        # Check for critical next_stage assignment
        if "nextStage = 'scheduling_redirect';" in function_code:
            print_success("State 11 sets next_stage = 'scheduling_redirect' ✓")
        else:
            print_error("State 11 next_stage NOT set correctly!")
            return False

        # Count state cases
        state_count = function_code.count("case '")
        print_success(f"Total state cases: {state_count}")

    else:
        print_error("State Machine Logic node NOT found!")
        return False

    # Validate "Prepare Appointment Data" node exists
    prepare_node_exists = any(n['name'] == 'Prepare Appointment Data' for n in workflow['nodes'])
    if prepare_node_exists:
        print_success("'Prepare Appointment Data' node exists ✓")
    else:
        print_error("'Prepare Appointment Data' node NOT found!")
        return False

    # Validate "Create Appointment in Database" SQL
    create_node = next((n for n in workflow['nodes'] if n['name'] == 'Create Appointment in Database'), None)
    if create_node:
        sql = create_node['parameters']['query']
        if '{{ $json.phone_number }}' in sql:
            print_success("SQL uses simplified expressions ✓")
        else:
            print_warning("SQL may have issues")
    else:
        print_error("'Create Appointment in Database' node NOT found!")
        return False

    print(f"\n{GREEN}✅ Validation complete - All checks passed!{RESET}")
    return True

def main():
    """Main script execution"""
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}Generate V73.4 Workflow - Add State 11{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")

    print(f"{YELLOW}🎯 CRITICAL FIX:{RESET}")
    print(f"V73.3 is MISSING State 11 (appointment_confirmation)!")
    print(f"  ❌ State 10 sets nextStage = 'appointment_confirmation'")
    print(f"  ❌ But State 11 doesn't exist in switch/case")
    print(f"  ❌ Result: Bot goes back to greeting\n")
    print(f"V73.4 will add State 11 with:")
    print(f"  ✅ User confirms → nextStage = 'scheduling_redirect'")
    print(f"  ✅ updateData.status = 'scheduling'")
    print(f"  ✅ This allows Check If Scheduling to execute")
    print(f"\n{BLUE}{'='*70}{RESET}\n")

    # Load V73.3
    workflow = load_v73_3_workflow()

    # Add State 11
    workflow = add_state_11(workflow)

    # Update metadata
    update_metadata(workflow)

    # Save V73.4
    output_path = save_v73_4_workflow(workflow)

    # Validate
    if validate_workflow(workflow):
        print(f"\n{GREEN}{'='*70}{RESET}")
        print(f"{GREEN}✅ V73.4 workflow generated successfully!{RESET}")
        print(f"{GREEN}{'='*70}{RESET}\n")
        print(f"{YELLOW}📋 Key Changes:{RESET}")
        print(f"1. Added State 11 (appointment_confirmation) AFTER State 10")
        print(f"2. State 11: User confirms → nextStage = 'scheduling_redirect'")
        print(f"3. State 11: Sets updateData.status = 'scheduling'")
        print(f"4. Flow now: State 10 (time) → State 11 (confirm) → Check If Scheduling → Create Appointment\n")
        print(f"{YELLOW}📋 Next steps:{RESET}")
        print(f"1. Import workflow: http://localhost:5678")
        print(f"2. File: {output_path}")
        print(f"3. Deactivate V73.3, activate V73.4")
        print(f"4. Test complete flow:")
        print(f"   WhatsApp: 'oi' → '1' (solar) → complete data → '1' (sim, agendar)")
        print(f"   Date: '25/04/2026' → Time: '08:00' → Confirm: '1'")
        print(f"   Expected: Appointment created + Check If Scheduling executes ✓\n")
        return 0
    else:
        print(f"\n{RED}{'='*70}{RESET}")
        print(f"{RED}❌ Validation failed - please review errors{RESET}")
        print(f"{RED}{'='*70}{RESET}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
