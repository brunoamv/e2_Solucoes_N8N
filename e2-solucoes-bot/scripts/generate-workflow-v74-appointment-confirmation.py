#!/usr/bin/env python3
"""
Script: generate-workflow-v74-appointment-confirmation.py
Purpose: Add appointment scheduling verification and trigger to WF02
Date: 2026-03-24

CHANGES FROM V73.5:
1. Add "Check If Scheduling" node (IF condition)
2. Add "Trigger Appointment Scheduler" node (executeWorkflow)
3. Update "Send WhatsApp Response" connections
4. Wire TRUE branch to trigger, FALSE branch to existing handoff check

CRITICAL VALIDATION:
- Service 1 (Energia Solar) → triggers WF05
- Service 3 (Projetos Elétricos) → triggers WF05
- Services 2,4,5 → handoff comercial (existing flow)
"""

import json
import sys
from pathlib import Path
import uuid

# Colors
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_step(step_num, total, message):
    print(f"{BLUE}[{step_num}/{total}]{RESET} {message}")

def print_success(message):
    print(f"{GREEN}✅ {message}{RESET}")

def print_error(message):
    print(f"{RED}❌ {message}{RESET}")

def print_warning(message):
    print(f"{YELLOW}⚠️  {message}{RESET}")

def load_v73_5_workflow():
    """Load V73.5 workflow JSON"""
    v73_5_path = Path(__file__).parent.parent / "n8n" / "workflows" / "02_ai_agent_conversation_V73.5_WORKFLOW_ID_FIX.json"

    print_step(1, 6, "Loading V73.5 workflow...")

    if not v73_5_path.exists():
        print_error(f"V73.5 workflow not found: {v73_5_path}")
        sys.exit(1)

    with open(v73_5_path, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    print_success(f"Loaded V73.5 workflow: {len(workflow['nodes'])} nodes")
    return workflow

def add_check_if_scheduling_node(workflow):
    """Add new IF node to check for scheduling_redirect state"""
    print_step(2, 6, "Adding 'Check If Scheduling' node...")

    # Generate unique ID
    node_id = str(uuid.uuid4())

    new_node = {
        "parameters": {
            "conditions": {
                "string": [
                    {
                        "value1": "={{ $node['Build Update Queries'].json.next_stage }}",
                        "operation": "equals",
                        "value2": "scheduling_redirect"
                    }
                ]
            }
        },
        "id": node_id,
        "name": "Check If Scheduling",
        "type": "n8n-nodes-base.if",
        "typeVersion": 1,
        "position": [1200, 512],
        "alwaysOutputData": False
    }

    workflow['nodes'].append(new_node)
    print_success(f"Added 'Check If Scheduling' node (ID: {node_id[:8]}...)")

    return workflow, node_id

def update_trigger_appointment_scheduler_node(workflow):
    """Update existing Trigger Appointment Scheduler node with correct workflow ID"""
    print_step(3, 6, "Updating 'Trigger Appointment Scheduler' node...")

    # Find existing node
    trigger_node = None
    for node in workflow['nodes']:
        if node['name'] == 'Trigger Appointment Scheduler':
            trigger_node = node
            break

    if trigger_node:
        # Update workflow ID to correct V3.6 workflow
        trigger_node['parameters']['workflowId'] = 'f6eIJIqfaSs6BSpJ'

        # Update/add fieldsUi with all required fields
        trigger_node['parameters']['fieldsUi'] = {
            "values": [
                {
                    "name": "phone_number",
                    "value": "={{ $node['Build Update Queries'].json.phone_number }}"
                },
                {
                    "name": "lead_name",
                    "value": "={{ $node['Build Update Queries'].json.collected_data.lead_name }}"
                },
                {
                    "name": "lead_email",
                    "value": "={{ $node['Build Update Queries'].json.collected_data.email }}"
                },
                {
                    "name": "service_type",
                    "value": "={{ $node['Build Update Queries'].json.collected_data.service_type }}"
                },
                {
                    "name": "city",
                    "value": "={{ $node['Build Update Queries'].json.collected_data.city }}"
                },
                {
                    "name": "service_selected",
                    "value": "={{ $node['Build Update Queries'].json.collected_data.service_selected }}"
                },
                {
                    "name": "triggered_from",
                    "value": "WF02_V74_confirmation_stage"
                }
            ]
        }

        print_success(f"Updated existing node with correct workflow ID and fields")
        node_id = trigger_node['id']
    else:
        # Create new node if doesn't exist
        print_warning("Node not found, creating new one...")
        node_id = str(uuid.uuid4())

        new_node = {
            "parameters": {
                "workflowId": "f6eIJIqfaSs6BSpJ",  # WF05 V3.6 ID (correct)
                "fieldsUi": {
                    "values": [
                        {
                            "name": "phone_number",
                            "value": "={{ $node['Build Update Queries'].json.phone_number }}"
                        },
                        {
                            "name": "lead_name",
                            "value": "={{ $node['Build Update Queries'].json.collected_data.lead_name }}"
                        },
                        {
                            "name": "lead_email",
                            "value": "={{ $node['Build Update Queries'].json.collected_data.email }}"
                        },
                        {
                            "name": "service_type",
                            "value": "={{ $node['Build Update Queries'].json.collected_data.service_type }}"
                        },
                        {
                            "name": "city",
                            "value": "={{ $node['Build Update Queries'].json.collected_data.city }}"
                        },
                        {
                            "name": "service_selected",
                            "value": "={{ $node['Build Update Queries'].json.collected_data.service_selected }}"
                        },
                        {
                            "name": "triggered_from",
                            "value": "WF02_V74_confirmation_stage"
                        }
                    ]
                }
            },
            "id": node_id,
            "name": "Trigger Appointment Scheduler",
            "type": "n8n-nodes-base.executeWorkflow",
            "typeVersion": 1,
            "position": [1440, 400],
            "alwaysOutputData": True
        }

        workflow['nodes'].append(new_node)
        print_success(f"Created new node (ID: {node_id[:8]}...)")

    return workflow, node_id

def update_send_whatsapp_response_connections(workflow, check_if_scheduling_id):
    """Update Send WhatsApp Response to connect to Check If Scheduling"""
    print_step(4, 6, "Updating 'Send WhatsApp Response' connections...")

    updated = False
    for node in workflow['nodes']:
        if node['name'] == 'Send WhatsApp Response':
            # Update connection from Check If Handoff to Check If Scheduling
            if 'connections' not in node:
                node['connections'] = {}

            node['connections']['main'] = [
                [
                    {
                        "node": "Check If Scheduling",
                        "type": "main",
                        "index": 0
                    }
                ]
            ]

            print_success("Updated 'Send WhatsApp Response' → 'Check If Scheduling'")
            updated = True
            break

    if not updated:
        print_warning("'Send WhatsApp Response' node not found or already updated")

    return workflow

def add_check_if_scheduling_connections(workflow, trigger_scheduler_id):
    """Add connections from Check If Scheduling node"""
    print_step(5, 6, "Wiring 'Check If Scheduling' connections...")

    for node in workflow['nodes']:
        if node['name'] == 'Check If Scheduling':
            if 'connections' not in node:
                node['connections'] = {}

            # TRUE branch → Trigger Appointment Scheduler
            # FALSE branch → Check If Handoff (existing flow)
            node['connections']['main'] = [
                [
                    {
                        "node": "Trigger Appointment Scheduler",
                        "type": "main",
                        "index": 0
                    }
                ],
                [
                    {
                        "node": "Check If Handoff",
                        "type": "main",
                        "index": 0
                    }
                ]
            ]

            print_success("TRUE branch → Trigger Appointment Scheduler")
            print_success("FALSE branch → Check If Handoff")
            break

    return workflow

def update_metadata(workflow):
    """Update workflow metadata for V74"""
    workflow['name'] = "02 - AI Agent Conversation V74"
    workflow['versionId'] = "V74"

    # Add tags
    workflow['tags'] = [
        {
            "name": "whatsapp-bot",
            "createdAt": "2026-03-24T00:00:00.000Z"
        },
        {
            "name": "v74",
            "createdAt": "2026-03-24T00:00:00.000Z"
        },
        {
            "name": "appointment-confirmation",
            "createdAt": "2026-03-24T00:00:00.000Z"
        }
    ]

    print_success("Updated metadata to V74")

def save_v74_workflow(workflow):
    """Save generated V74 workflow"""
    output_path = Path(__file__).parent.parent / "n8n" / "workflows" / "02_ai_agent_conversation_V74_APPOINTMENT_CONFIRMATION.json"

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print_success(f"Saved V74 workflow: {output_path}")
    print_success(f"Total nodes: {len(workflow['nodes'])}")

    return output_path

def validate_workflow(workflow):
    """Validate generated workflow structure"""
    print_step(6, 6, "Validating V74 workflow...")

    # Check critical nodes exist
    node_names = [n['name'] for n in workflow['nodes']]

    required_nodes = [
        "Send WhatsApp Response",
        "Check If Scheduling",
        "Trigger Appointment Scheduler",
        "Check If Handoff",
        "Build Update Queries"
    ]

    for required in required_nodes:
        if required in node_names:
            print_success(f"Node '{required}' exists ✓")
        else:
            print_error(f"Node '{required}' NOT found!")
            return False

    # Validate Send WhatsApp Response connections
    send_node = next((n for n in workflow['nodes'] if n['name'] == 'Send WhatsApp Response'), None)
    if send_node and 'connections' in send_node:
        main_conn = send_node['connections'].get('main', [[]])[0]
        if main_conn and main_conn[0]['node'] == 'Check If Scheduling':
            print_success("Send WhatsApp Response → Check If Scheduling ✓")
        else:
            print_error("Send WhatsApp Response connection incorrect!")
            return False
    else:
        print_error("Send WhatsApp Response has no connections!")
        return False

    # Validate Check If Scheduling connections
    check_node = next((n for n in workflow['nodes'] if n['name'] == 'Check If Scheduling'), None)
    if check_node and 'connections' in check_node:
        main_conn = check_node['connections'].get('main', [[], []])

        # TRUE branch
        if main_conn[0] and main_conn[0][0]['node'] == 'Trigger Appointment Scheduler':
            print_success("Check If Scheduling TRUE → Trigger Appointment Scheduler ✓")
        else:
            print_error("Check If Scheduling TRUE branch incorrect!")
            return False

        # FALSE branch
        if main_conn[1] and main_conn[1][0]['node'] == 'Check If Handoff':
            print_success("Check If Scheduling FALSE → Check If Handoff ✓")
        else:
            print_error("Check If Scheduling FALSE branch incorrect!")
            return False
    else:
        print_error("Check If Scheduling has no connections!")
        return False

    # Validate Trigger Appointment Scheduler parameters
    trigger_node = next((n for n in workflow['nodes'] if n['name'] == 'Trigger Appointment Scheduler'), None)
    if trigger_node:
        workflow_id = trigger_node['parameters'].get('workflowId')
        if workflow_id == 'f6eIJIqfaSs6BSpJ':
            print_success("Trigger Appointment Scheduler → WF05 V3.6 ✓")
        else:
            print_error(f"Trigger Appointment Scheduler workflow ID incorrect: {workflow_id}")
            return False

        # Check input fields
        fields = trigger_node['parameters'].get('fieldsUi', {}).get('values', [])
        field_names = [f['name'] for f in fields]
        required_fields = ['phone_number', 'lead_name', 'lead_email', 'service_type', 'city', 'service_selected']

        for req_field in required_fields:
            if req_field in field_names:
                print_success(f"Field '{req_field}' configured ✓")
            else:
                print_error(f"Field '{req_field}' missing!")
                return False
    else:
        print_error("Trigger Appointment Scheduler node not found!")
        return False

    print(f"\n{GREEN}✅ Validation complete - All checks passed!{RESET}")
    return True

def main():
    """Main script execution"""
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}Generate Workflow V74 - Appointment Confirmation Enhancement{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")

    print(f"{YELLOW}🎯 GOAL:{RESET}")
    print("Add verification logic to trigger WF05 V3.6 when user confirms scheduling")
    print("")
    print(f"{YELLOW}📋 CHANGES:{RESET}")
    print("1. Add 'Check If Scheduling' IF node")
    print("2. Add 'Trigger Appointment Scheduler' executeWorkflow node")
    print("3. Update 'Send WhatsApp Response' connections")
    print("4. Wire TRUE branch → trigger, FALSE branch → existing handoff")
    print("")
    print(f"{BLUE}{'='*70}{RESET}\n")

    # Load V73.5
    workflow = load_v73_5_workflow()

    # Add new nodes
    workflow, check_if_scheduling_id = add_check_if_scheduling_node(workflow)
    workflow, trigger_scheduler_id = update_trigger_appointment_scheduler_node(workflow)

    # Update connections
    workflow = update_send_whatsapp_response_connections(workflow, check_if_scheduling_id)
    workflow = add_check_if_scheduling_connections(workflow, trigger_scheduler_id)

    # Update metadata
    update_metadata(workflow)

    # Save V74
    output_path = save_v74_workflow(workflow)

    # Validate
    if validate_workflow(workflow):
        print(f"\n{GREEN}{'='*70}{RESET}")
        print(f"{GREEN}✅ V74 workflow generated successfully!{RESET}")
        print(f"{GREEN}{'='*70}{RESET}\n")

        print(f"{YELLOW}📋 Summary:{RESET}")
        print(f"Base: V73.5_WORKFLOW_ID_FIX")
        print(f"Output: {output_path}")
        print(f"Total nodes: {len(workflow['nodes'])}")
        print(f"New nodes: 2 (Check If Scheduling, Trigger Appointment Scheduler)")
        print("")

        print(f"{YELLOW}📋 Flow:{RESET}")
        print("State Machine → Build Update Queries → Send WhatsApp Response")
        print("                                              ↓")
        print("                                    Check If Scheduling")
        print("                                              ↓")
        print("                      TRUE (scheduling_redirect) → Trigger WF05 V3.6")
        print("                      FALSE (other states) → Check If Handoff")
        print("")

        print(f"{YELLOW}📋 Next steps:{RESET}")
        print("1. Import workflow: http://localhost:5678")
        print(f"2. File: {output_path}")
        print("3. Deactivate V73.5, activate V74")
        print("4. Test complete flow:")
        print("   a. User confirms scheduling (service 1 or 3)")
        print("   b. Verify WF05 V3.6 triggers")
        print("   c. Verify Google Calendar event created")
        print("   d. Verify client receives confirmation")
        print("5. Test handoff flow (service 2, 4, 5 or option 2)")
        print("6. Monitor executions and logs\n")

        return 0
    else:
        print(f"\n{RED}{'='*70}{RESET}")
        print(f"{RED}❌ Validation failed - please review errors{RESET}")
        print(f"{RED}{'='*70}{RESET}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
