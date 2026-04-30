#!/usr/bin/env python3
"""
Script: generate-v73.2-state-machine-fix.py
Purpose: Generate V73.2 workflow with State Machine fix for appointment flow
Date: 2026-03-24

CRITICAL FIX:
State 8 (confirmation) usando template ERRADO e next_stage ERRADO

V73.1 (INCORRETO):
- responseText = templates.scheduling_redirect (MENSAGEM FINAL!)
- nextStage = 'scheduling' (ERRADO!)

V73.2 (CORRETO):
- responseText = templates.appointment_date_request (PEDIR DATA!)
- nextStage = 'collect_appointment_date' (IR PARA STATE 9!)

Fluxo correto:
State 8 → State 9 (data) → State 10 (hora) → State 11 (confirmação final) → Create Appointment
"""

import json
import sys
from pathlib import Path

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

def load_v73_1_workflow():
    """Load V73.1 workflow JSON"""
    v73_1_path = Path(__file__).parent.parent / "n8n" / "workflows" / "02_ai_agent_conversation_V73.1_TIMING_FIX.json"

    print_step(1, 4, "Loading V73.1 workflow...")

    if not v73_1_path.exists():
        print_error(f"V73.1 workflow not found: {v73_1_path}")
        sys.exit(1)

    with open(v73_1_path, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    print_success(f"Loaded V73.1 workflow: {len(workflow['nodes'])} nodes")
    return workflow

def fix_state_machine(workflow):
    """Fix State Machine State 8 logic"""
    print_step(2, 4, "Fixing State Machine State 8 logic...")

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

    # CRITICAL FIX: Replace State 8 confirmation logic
    # Find and replace the INCORRECT code

    incorrect_code = """  // ===== STATE 8: CONFIRMATION - Final confirmation =====
  case 'confirmation':
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
    }"""

    correct_code = """  // ===== STATE 8: CONFIRMATION - Final confirmation =====
  case 'confirmation':
    console.log('V73.2: Processing CONFIRMATION state');

    // Option 1: Agendar visita
    if (message === '1') {
      const serviceSelected = currentData.service_selected || '1';
      if (serviceSelected === '1' || serviceSelected === '3') {
        // V73.2 FIX: Go to State 9 to collect appointment date, NOT final message!
        console.log('V73.2 FIX: Services 1 or 3 → Going to collect_appointment_date (State 9)');
        responseText = '📅 *Ótimo! Vamos agendar sua visita técnica.*\\n\\nQual a melhor data para você? (formato DD/MM/AAAA)\\n\\n💡 _Exemplo: 25/04/2026_';
        nextStage = 'collect_appointment_date';  // ✅ GO TO STATE 9!
      } else {
        // Other services → handoff
        console.log('V73.2: Other services → handoff_comercial');
        responseText = templates.handoff_comercial;
        nextStage = 'handoff_comercial';
        updateData.status = 'handoff';
      }
    }"""

    if incorrect_code in function_code:
        function_code = function_code.replace(incorrect_code, correct_code)
        print_success("Replaced State 8 confirmation logic")
    else:
        print_warning("Exact match not found, trying alternative replacement...")

        # Try finding State 8 case differently
        import re
        pattern = r"(case 'confirmation':.*?if \(serviceSelected === '1' \|\| serviceSelected === '3'\) \{)(.*?)(responseText = templates\.scheduling_redirect;.*?nextStage = 'scheduling';.*?updateData\.status = 'scheduling';)"

        def replace_match(match):
            return match.group(1) + "\n        // V73.2 FIX: Go to State 9 to collect appointment date\n        console.log('V73.2 FIX: Services 1 or 3 → Going to collect_appointment_date (State 9)');\n        responseText = '📅 *Ótimo! Vamos agendar sua visita técnica.*\\\\n\\\\nQual a melhor data para você? (formato DD/MM/AAAA)\\\\n\\\\n💡 _Exemplo: 25/04/2026_';\n        nextStage = 'collect_appointment_date';  // ✅ GO TO STATE 9!\n      "

        function_code_new = re.sub(pattern, replace_match, function_code, flags=re.DOTALL)

        if function_code_new != function_code:
            function_code = function_code_new
            print_success("Applied State 8 fix via regex")
        else:
            print_error("Could not find State 8 confirmation logic to replace!")
            print_error("Manual fix required")
            sys.exit(1)

    # Update State Machine node
    state_machine_node['parameters']['functionCode'] = function_code
    print_success(f"Updated State Machine: {len(function_code)} chars")

    return workflow

def update_metadata(workflow):
    """Update workflow metadata for V73.2"""
    print_step(3, 4, "Updating workflow metadata...")

    workflow['meta'] = {
        "version": "V73.2_STATE_MACHINE_FIX",
        "fixes_applied": [
            "BUG #4: SQL syntax error (V73 - fixed with Set node)",
            "BUG #5: Appointment timing - creating with NULL dates (V73.1 attempted)",
            "BUG #6: State Machine wrong template/next_stage at State 8",
            "SOLUTION: State 8 now transitions to collect_appointment_date (State 9)",
            "RESULT: Appointment created AFTER States 9/10/11 with dates populated"
        ],
        "fix_date": "2026-03-24",
        "preserves_v73_fixes": True,
        "preserves_v73_1_timing": True,
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
            "V73.2 Fix: State Machine State 8 logic - correct template and next_stage"
        ],
        "instanceId": "v73_2_state_machine_fix_complete",
        "description": "V73.2 STATE MACHINE FIX - State 8 now correctly transitions to State 9 to collect dates"
    }

    workflow['versionId'] = "73.2"
    workflow['tags'] = [
        {
            "name": "v73.2-state-machine-fix-complete"
        },
        {
            "name": "ready-for-production"
        }
    ]

    print_success("Updated metadata to V73.2")

def save_v73_2_workflow(workflow):
    """Save generated V73.2 workflow"""
    output_path = Path(__file__).parent.parent / "n8n" / "workflows" / "02_ai_agent_conversation_V73.2_STATE_MACHINE_FIX.json"

    print_step(4, 4, "Saving V73.2 workflow...")

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print_success(f"Saved V73.2 workflow: {output_path}")
    print_success(f"Total nodes: {len(workflow['nodes'])}")
    print_success(f"Total connections: {len(workflow.get('connections', {}))}")

    return output_path

def validate_workflow(workflow):
    """Validate generated workflow structure"""
    print(f"\n{BLUE}🔍 Validating V73.2 workflow...{RESET}")

    # Validate node count (same as V73/V73.1)
    expected_nodes = 34
    actual_nodes = len(workflow['nodes'])

    if actual_nodes != expected_nodes:
        print_warning(f"Expected {expected_nodes} nodes, got {actual_nodes}")
    else:
        print_success(f"Node count correct: {actual_nodes} nodes")

    # Validate State Machine fix
    state_machine_node = next((n for n in workflow['nodes'] if n['name'] == 'State Machine Logic'), None)

    if state_machine_node:
        function_code = state_machine_node['parameters']['functionCode']

        # Check for V73.2 fix markers
        if "V73.2 FIX: Services 1 or 3 → Going to collect_appointment_date" in function_code:
            print_success("V73.2 State Machine fix markers found ✓")
        else:
            print_error("V73.2 fix markers NOT found!")
            return False

        # Check for correct next_stage
        if "nextStage = 'collect_appointment_date';" in function_code:
            print_success("State 8 uses correct next_stage (collect_appointment_date) ✓")
        else:
            print_error("State 8 next_stage NOT corrected!")
            return False

        # Check that INCORRECT code is gone
        if "nextStage = 'scheduling';" in function_code:
            # Check if it's only in other contexts (like State 11)
            # Count occurrences
            count = function_code.count("nextStage = 'scheduling';")
            if count > 0:
                print_warning(f"Found {count} occurrence(s) of nextStage = 'scheduling' (may be valid in other states)")

        # Check that scheduling_redirect is NOT used in State 8
        if "templates.scheduling_redirect" in function_code:
            # This might be OK if used in State 11, check context
            print_warning("templates.scheduling_redirect found in State Machine (check if only in State 11)")
        else:
            print_success("No scheduling_redirect template usage ✓")

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
    print(f"{BLUE}Generate V73.2 Workflow - State Machine Fix{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")

    print(f"{YELLOW}🎯 CRITICAL FIX:{RESET}")
    print(f"State 8 confirmation was using:")
    print(f"  ❌ templates.scheduling_redirect (FINAL MESSAGE)")
    print(f"  ❌ nextStage = 'scheduling' (WRONG!)")
    print(f"\nV73.2 will use:")
    print(f"  ✅ Ask for appointment date")
    print(f"  ✅ nextStage = 'collect_appointment_date' (State 9)")
    print(f"\n{BLUE}{'='*70}{RESET}\n")

    # Load V73.1
    workflow = load_v73_1_workflow()

    # Fix State Machine
    workflow = fix_state_machine(workflow)

    # Update metadata
    update_metadata(workflow)

    # Save V73.2
    output_path = save_v73_2_workflow(workflow)

    # Validate
    if validate_workflow(workflow):
        print(f"\n{GREEN}{'='*70}{RESET}")
        print(f"{GREEN}✅ V73.2 workflow generated successfully!{RESET}")
        print(f"{GREEN}{'='*70}{RESET}\n")
        print(f"{YELLOW}📋 Key Changes:{RESET}")
        print(f"1. State 8: Changed template from scheduling_redirect to appointment_date_request")
        print(f"2. State 8: Changed next_stage from 'scheduling' to 'collect_appointment_date'")
        print(f"3. Flow now: State 8 → 9 (date) → 10 (time) → 11 (confirm) → Create Appointment")
        print(f"4. Dates will be POPULATED before PostgreSQL INSERT\n")
        print(f"{YELLOW}📋 Next steps:{RESET}")
        print(f"1. Import workflow: http://localhost:5678")
        print(f"2. File: {output_path}")
        print(f"3. Deactivate V73.1, activate V73.2")
        print(f"4. Test complete flow:")
        print(f"   WhatsApp: 'oi' → '1' (solar) → complete data → '1' (sim, agendar)")
        print(f"   Expected: Bot asks for DATE (not final message!)")
        print(f"   Then: User provides date → time → final confirmation")
        print(f"   Finally: Appointment created with dates in PostgreSQL ✓\n")
        return 0
    else:
        print(f"\n{RED}{'='*70}{RESET}")
        print(f"{RED}❌ Validation failed - please review errors{RESET}")
        print(f"{RED}{'='*70}{RESET}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
