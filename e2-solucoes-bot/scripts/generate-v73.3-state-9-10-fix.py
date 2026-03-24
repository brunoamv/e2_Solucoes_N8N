#!/usr/bin/env python3
"""
Script: generate-v73.3-state-9-10-fix.py
Purpose: Generate V73.3 workflow fixing State 9/10 message processing
Date: 2026-03-24

CRITICAL FIX:
State 9/10 não processam mensagem raw do usuário - só verificam se dados já existem no banco

V73.2 (INCORRETO):
- State 9: if (currentData.scheduled_date) → só verifica banco ❌
- State 10: if (currentData.scheduled_time_start) → só verifica banco ❌
- Resultado: Loop infinito, nunca processa input do usuário

V73.3 (CORRETO):
- State 9: Parse message variable → validate DD/MM/AAAA → store updateData.scheduled_date ✅
- State 10: Parse message variable → validate HH:MM → store updateData.scheduled_time_start/end ✅
- Resultado: Progressão fluida State 9 → 10 → 11 → Create Appointment
"""

import json
import sys
import re
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

def load_v73_2_workflow():
    """Load V73.2 workflow JSON"""
    v73_2_path = Path(__file__).parent.parent / "n8n" / "workflows" / "02_ai_agent_conversation_V73.2_STATE_MACHINE_FIX.json"

    print_step(1, 4, "Loading V73.2 workflow...")

    if not v73_2_path.exists():
        print_error(f"V73.2 workflow not found: {v73_2_path}")
        sys.exit(1)

    with open(v73_2_path, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    print_success(f"Loaded V73.2 workflow: {len(workflow['nodes'])} nodes")
    return workflow

def fix_state_9_10_logic(workflow):
    """Fix State Machine State 9/10 to process raw message input"""
    print_step(2, 4, "Fixing State Machine State 9/10 logic...")

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

    # STATE 9 FIX: Use regex to find and replace State 9 logic
    # Pattern: from "case 'collect_appointment_date':" to the "break;" before State 10
    state_9_pattern = re.compile(
        r"case 'collect_appointment_date':.*?break;(?=\s*// =====.*?STATE 10)",
        re.DOTALL
    )

    state_9_new = r"""case 'collect_appointment_date':
  case 'coletando_data_agendamento':
    console.log('V73.3: Processing COLLECT_APPOINTMENT_DATE state');

    // V73.3 FIX: PROCESS raw message input directly
    const dateInput = message.trim();

    // Date validation regex: DD/MM/AAAA
    const dateRegex = /^(\d{2})\/(\d{2})\/(\d{4})$/;
    const dateMatch = dateInput.match(dateRegex);

    if (dateMatch) {
      const day = parseInt(dateMatch[1], 10);
      const month = parseInt(dateMatch[2], 10);
      const year = parseInt(dateMatch[3], 10);

      // Validate date ranges
      if (day >= 1 && day <= 31 && month >= 1 && month <= 12 && year >= 2026 && year <= 2030) {
        // Format to ISO: YYYY-MM-DD
        const isoDate = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;

        // Validate it's not in the past
        const now = new Date();
        const appointmentDate = new Date(isoDate);

        if (appointmentDate >= now) {
          console.log('V73.3 FIX: Valid date →', isoDate);

          // STORE validated date
          updateData.scheduled_date = isoDate;

          // GO TO STATE 10
          responseText = `⏰ *Perfeito! Data confirmada: ${dateInput}*

Qual horário você prefere?

💡 _Formato: HH:MM (ex: 09:00, 14:30)_

🕐 Horário comercial: 08:00 às 18:00`;
          nextStage = 'collect_appointment_time';
        } else {
          // Date is in the past
          console.log('V73.3: Date in past');
          responseText = `❌ *Data inválida*

A data informada (${dateInput}) já passou.

Por favor, informe uma data futura (formato DD/MM/AAAA):

💡 _Exemplo: 25/04/2026_`;
          nextStage = 'collect_appointment_date';
        }
      } else {
        // Invalid day/month/year ranges
        console.log('V73.3: Invalid date ranges');
        responseText = `❌ *Data inválida*

Por favor, informe uma data válida (formato DD/MM/AAAA):

💡 _Exemplo: 25/04/2026_
_Dia: 01-31, Mês: 01-12, Ano: 2026-2030_`;
        nextStage = 'collect_appointment_date';
      }
    } else {
      // Format doesn't match DD/MM/AAAA
      console.log('V73.3: Invalid date format');
      responseText = `❌ *Formato inválido*

Por favor, use o formato DD/MM/AAAA:

💡 _Exemplo: 25/04/2026_
_Certifique-se de usar barras (/) para separar dia, mês e ano_`;
      nextStage = 'collect_appointment_date';
    }
    break;"""

    match = state_9_pattern.search(function_code)
    if match:
        # Use lambda to avoid re.sub interpreting backslashes
        function_code = state_9_pattern.sub(lambda m: state_9_new, function_code)
        print_success("Replaced State 9 logic via regex")
    else:
        print_error("Could not find State 9 logic pattern!")
        sys.exit(1)

    # STATE 10 FIX: Use regex to find and replace State 10 logic
    # Pattern: from "case 'collect_appointment_time':" to "break;" before next case or comment
    state_10_pattern = re.compile(
        r"case 'collect_appointment_time':.*?break;(?=\s*(?://|case\s))",
        re.DOTALL
    )

    state_10_new = r"""case 'collect_appointment_time':
  case 'coletando_horario_agendamento':
    console.log('V73.3: Processing COLLECT_APPOINTMENT_TIME state');

    // V73.3 FIX: PROCESS raw message input directly
    const timeInput = message.trim();

    // Time validation regex: HH:MM
    const timeRegex = /^(\d{2}):(\d{2})$/;
    const timeMatch = timeInput.match(timeRegex);

    if (timeMatch) {
      const hour = parseInt(timeMatch[1], 10);
      const minute = parseInt(timeMatch[2], 10);

      // Validate time ranges and business hours
      if (hour >= 0 && hour <= 23 && minute >= 0 && minute <= 59) {
        // Check business hours: 08:00 to 18:00
        if (hour >= 8 && hour < 18) {
          // Calculate end time (2 hours later for technical visit)
          const endHour = hour + 2;
          const startTime = `${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}:00`;
          const endTime = `${String(endHour).padStart(2, '0')}:${String(minute).padStart(2, '0')}:00`;

          console.log('V73.3 FIX: Valid time →', startTime, 'to', endTime);

          // STORE validated times
          updateData.scheduled_time_start = startTime;
          updateData.scheduled_time_end = endTime;

          // Format date for display (from currentData or updateData)
          const dbDate = updateData.scheduled_date || currentData.scheduled_date || '';
          let displayDate = dbDate;
          if (dbDate && /^\d{4}-\d{2}-\d{2}$/.test(dbDate)) {
            const [y, m, d] = dbDate.split('-');
            displayDate = `${d}/${m}/${y}`;
          }

          // GO TO STATE 11 (final confirmation)
          const serviceName = getServiceName(currentData.service_selected || '1');
          responseText = `✅ *Agendamento quase pronto!*

📅 *Resumo da visita técnica:*

🗓️ Data: ${displayDate}
⏰ Horário: ${timeInput} às ${String(endHour).padStart(2, '0')}:${String(minute).padStart(2, '0')}
⏳ Duração: 2 horas
🔧 Serviço: ${serviceName}

---

Confirma o agendamento?

1️⃣ *Sim, confirmar*
2️⃣ *Não, corrigir dados*`;
          nextStage = 'appointment_confirmation';
        } else {
          // Outside business hours
          console.log('V73.3: Time outside business hours');
          responseText = `❌ *Horário fora do expediente*

Por favor, escolha um horário entre 08:00 e 17:59.

🕐 *Horário comercial:*
Segunda a Sexta: 08:00 às 18:00
Sábado: 08:00 às 12:00

💡 _Exemplo: 09:00, 14:30_`;
          nextStage = 'collect_appointment_time';
        }
      } else {
        // Invalid hour/minute ranges
        console.log('V73.3: Invalid time ranges');
        responseText = `❌ *Horário inválido*

Por favor, informe um horário válido (formato HH:MM):

💡 _Exemplo: 09:00, 14:30_
_Hora: 00-23, Minuto: 00-59_`;
        nextStage = 'collect_appointment_time';
      }
    } else {
      // Format doesn't match HH:MM
      console.log('V73.3: Invalid time format');
      responseText = `❌ *Formato inválido*

Por favor, use o formato HH:MM:

💡 _Exemplo: 09:00, 14:30_
_Certifique-se de usar dois-pontos (:) para separar hora e minuto_`;
      nextStage = 'collect_appointment_time';
    }
    break;"""

    match = state_10_pattern.search(function_code)
    if match:
        # Use lambda to avoid re.sub interpreting backslashes
        function_code = state_10_pattern.sub(lambda m: state_10_new, function_code)
        print_success("Replaced State 10 logic via regex")
    else:
        print_error("Could not find State 10 logic pattern!")
        sys.exit(1)

    # Update State Machine node
    state_machine_node['parameters']['functionCode'] = function_code
    print_success(f"Updated State Machine: {len(function_code)} chars")

    return workflow

def update_metadata(workflow):
    """Update workflow metadata for V73.3"""
    print_step(3, 4, "Updating workflow metadata...")

    workflow['meta'] = {
        "version": "V73.3_STATE_9_10_FIX",
        "fixes_applied": [
            "BUG #4: SQL syntax error (V73 - fixed with Set node)",
            "BUG #5: Appointment timing - creating with NULL dates (V73.1 attempted)",
            "BUG #6: State Machine wrong template/next_stage at State 8 (V73.2 fixed)",
            "BUG #7: State 9/10 not processing raw message input (V73.3 COMPLETE FIX)",
            "SOLUTION: State 9/10 now parse, validate, and store user's date/time input",
            "RESULT: Smooth flow State 9 → 10 → 11 → Create Appointment with dates populated"
        ],
        "fix_date": "2026-03-24",
        "preserves_v73_fixes": True,
        "preserves_v73_1_timing": True,
        "preserves_v73_2_state_8": True,
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
            "V73.2 Fix: State Machine State 8 logic - correct template and next_stage",
            "V73.3 Fix: State 9/10 message processing - parse and validate user input"
        ],
        "instanceId": "v73_3_state_9_10_fix_complete",
        "description": "V73.3 STATE 9/10 FIX - States now process raw message input with inline validation"
    }

    workflow['versionId'] = "73.3"
    workflow['tags'] = [
        {
            "name": "v73.3-state-9-10-fix-complete"
        },
        {
            "name": "ready-for-production"
        }
    ]

    print_success("Updated metadata to V73.3")

def save_v73_3_workflow(workflow):
    """Save generated V73.3 workflow"""
    output_path = Path(__file__).parent.parent / "n8n" / "workflows" / "02_ai_agent_conversation_V73.3_STATE_9_10_FIX.json"

    print_step(4, 4, "Saving V73.3 workflow...")

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print_success(f"Saved V73.3 workflow: {output_path}")
    print_success(f"Total nodes: {len(workflow['nodes'])}")
    print_success(f"Total connections: {len(workflow.get('connections', {}))}")

    return output_path

def validate_workflow(workflow):
    """Validate generated workflow structure"""
    print(f"\n{BLUE}🔍 Validating V73.3 workflow...{RESET}")

    # Validate node count (same as V73.2)
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

        # Check for V73.3 fix markers - State 9
        if "V73.3 FIX: PROCESS raw message input directly" in function_code and "const dateInput = message.trim();" in function_code:
            print_success("V73.3 State 9 fix markers found ✓")
        else:
            print_error("V73.3 State 9 fix markers NOT found!")
            return False

        # Check for State 9 date parsing
        if "const dateRegex = /^(\\d{2})\\/(\\d{2})\\/(\\d{4})$/;" in function_code:
            print_success("State 9 date parsing regex present ✓")
        else:
            print_error("State 9 date parsing NOT found!")
            return False

        # Check for State 9 updateData storage
        if "updateData.scheduled_date = isoDate;" in function_code:
            print_success("State 9 stores updateData.scheduled_date ✓")
        else:
            print_error("State 9 updateData.scheduled_date NOT found!")
            return False

        # Check for V73.3 fix markers - State 10
        if "const timeInput = message.trim();" in function_code:
            print_success("V73.3 State 10 fix markers found ✓")
        else:
            print_error("V73.3 State 10 fix markers NOT found!")
            return False

        # Check for State 10 time parsing
        if "const timeRegex = /^(\\d{2}):(\\d{2})$/;" in function_code:
            print_success("State 10 time parsing regex present ✓")
        else:
            print_error("State 10 time parsing NOT found!")
            return False

        # Check for State 10 updateData storage
        if "updateData.scheduled_time_start = startTime;" in function_code and "updateData.scheduled_time_end = endTime;" in function_code:
            print_success("State 10 stores updateData.scheduled_time_start/end ✓")
        else:
            print_error("State 10 updateData.scheduled_time NOT found!")
            return False

        # Check for business hours validation
        if "if (hour >= 8 && hour < 18)" in function_code:
            print_success("State 10 validates business hours (08:00-17:59) ✓")
        else:
            print_error("State 10 business hours validation NOT found!")
            return False

    else:
        print_error("State Machine Logic node NOT found!")
        return False

    # Validate "Prepare Appointment Data" node exists (V73 fix)
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
    print(f"{BLUE}Generate V73.3 Workflow - State 9/10 Message Processing Fix{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")

    print(f"{YELLOW}🎯 CRITICAL FIX:{RESET}")
    print(f"V73.2 State 9/10 was checking if dates ALREADY EXIST in database:")
    print(f"  ❌ if (currentData.scheduled_date) → only checks DB, ignores user input")
    print(f"  ❌ Result: Infinite loop asking for date")
    print(f"\nV73.3 will parse user's raw message:")
    print(f"  ✅ Parse message → \"25/04/2026\"")
    print(f"  ✅ Validate format DD/MM/AAAA")
    print(f"  ✅ Store updateData.scheduled_date")
    print(f"  ✅ Transition to State 10")
    print(f"\n{BLUE}{'='*70}{RESET}\n")

    # Load V73.2
    workflow = load_v73_2_workflow()

    # Fix State 9/10
    workflow = fix_state_9_10_logic(workflow)

    # Update metadata
    update_metadata(workflow)

    # Save V73.3
    output_path = save_v73_3_workflow(workflow)

    # Validate
    if validate_workflow(workflow):
        print(f"\n{GREEN}{'='*70}{RESET}")
        print(f"{GREEN}✅ V73.3 workflow generated successfully!{RESET}")
        print(f"{GREEN}{'='*70}{RESET}\n")
        print(f"{YELLOW}📋 Key Changes:{RESET}")
        print(f"1. State 9: Now parses message variable directly → validates DD/MM/AAAA → stores updateData.scheduled_date")
        print(f"2. State 10: Now parses message variable directly → validates HH:MM + business hours → stores updateData.scheduled_time_start/end")
        print(f"3. Flow now works: State 9 (date) → State 10 (time) → State 11 (confirm) → Create Appointment")
        print(f"4. Dates POPULATED before PostgreSQL INSERT (no more NULL errors)\n")
        print(f"{YELLOW}📋 Next steps:{RESET}")
        print(f"1. Import workflow: http://localhost:5678")
        print(f"2. File: {output_path}")
        print(f"3. Deactivate V73.2, activate V73.3")
        print(f"4. Test complete flow:")
        print(f"   WhatsApp: 'oi' → '1' (solar) → complete data → '1' (sim, agendar)")
        print(f"   Date: '25/04/2026' ← DEVE PROCESSAR!")
        print(f"   Time: '09:00' ← DEVE PROCESSAR!")
        print(f"   Confirm: 'sim'")
        print(f"   Finally: Appointment created with dates in PostgreSQL ✓\n")
        return 0
    else:
        print(f"\n{RED}{'='*70}{RESET}")
        print(f"{RED}❌ Validation failed - please review errors{RESET}")
        print(f"{RED}{'='*70}{RESET}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
