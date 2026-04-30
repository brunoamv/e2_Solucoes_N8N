#!/usr/bin/env python3
"""
Gerador do Workflow: 05_appointment_scheduler V2.0
Data: 2026-03-13
Padrão: V69.2 Compliance (WF02 pattern)

Melhorias V2.0:
- Validação de entrada (V69.2 pattern)
- Error handling robusto com retry (3x)
- Validação de disponibilidade (horário comercial)
- Database atomicity (single transaction)
- Logging estruturado
- Configuração via env vars (não hardcoded)
- Modularização do código
"""

import json
from datetime import datetime

# ============================================================================
# WORKFLOW METADATA
# ============================================================================

WORKFLOW_VERSION = "2.1"
WORKFLOW_NAME = "05 - Appointment Scheduler V2.1"
CREATED_DATE = datetime.now().isoformat()

# ============================================================================
# NODE DEFINITIONS
# ============================================================================

def create_trigger_node():
    """Execute Workflow Trigger"""
    return {
        "parameters": {
            "options": {}
        },
        "id": "execute-workflow-trigger-v2",
        "name": "Execute Workflow Trigger",
        "type": "n8n-nodes-base.executeWorkflowTrigger",
        "typeVersion": 1,
        "position": [250, 300]
    }

def create_validate_input_node():
    """Validate Input Data (V69.2 pattern)"""
    js_code = """
// Validate Input Data (V69.2 pattern)
const inputData = $input.first().json;

// Validate appointment_id exists
if (!inputData.appointment_id) {
    throw new Error('appointment_id is required');
}

// Validate UUID format
const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
if (!uuidRegex.test(inputData.appointment_id)) {
    throw new Error('Invalid appointment_id format (must be UUID)');
}

console.log('✅ [Validate Input] Valid appointment_id:', inputData.appointment_id);

return {
    appointment_id: inputData.appointment_id,
    source: inputData.source || 'workflow_trigger',
    timestamp: new Date().toISOString(),
    validation_status: 'approved'
};
""".strip()

    return {
        "parameters": {
            "jsCode": js_code
        },
        "id": "validate-input-data-v2",
        "name": "Validate Input Data",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [450, 300],
        "alwaysOutputData": True,
        "notes": "V69.2 pattern: Input validation with UUID check and structured logging"
    }

def create_get_appointment_lead_node():
    """Get Appointment & Lead Data (merged query)"""
    query = """
SELECT
    a.id as appointment_id,
    a.scheduled_date,
    a.scheduled_time_start,
    a.scheduled_time_end,
    a.service_type,
    a.notes,
    a.status,
    l.id as lead_id,
    l.name as lead_name,
    l.email as lead_email,
    l.phone_number,
    l.address,
    l.city,
    l.state,
    l.zip_code,
    l.service_details,
    l.rdstation_deal_id,
    c.whatsapp_name
FROM appointments a
INNER JOIN leads l ON a.lead_id = l.id
LEFT JOIN conversations c ON l.conversation_id = c.id
WHERE a.id = $1
  AND a.status IN ('agendado', 'reagendado')
LIMIT 1;
""".strip()

    return {
        "parameters": {
            "operation": "executeQuery",
            "query": query,
            "additionalFields": {
                "queryParameters": "={{ $json.appointment_id }}"
            }
        },
        "id": "get-appointment-lead-v2",
        "name": "Get Appointment & Lead Data",
        "type": "n8n-nodes-base.postgres",
        "typeVersion": 2,
        "position": [650, 300],
        "credentials": {
            "postgres": {
                "id": "1",
                "name": "PostgreSQL - E2 Bot"
            }
        },
        "alwaysOutputData": True,
        "notes": "Single JOIN query for performance (V2.0 optimization)"
    }

def create_validate_availability_node():
    """Validate Availability (business hours check)"""
    js_code = """
// Validate Availability
const data = $input.first().json;

const scheduledDate = data.scheduled_date;
const timeStart = data.scheduled_time_start;
const timeEnd = data.scheduled_time_end;

// Check business hours
const startHour = parseInt(timeStart.split(':')[0]);
const endHour = parseInt(timeEnd.split(':')[0]);

const workStart = parseInt($env.CALENDAR_WORK_START.split(':')[0]);
const workEnd = parseInt($env.CALENDAR_WORK_END.split(':')[0]);

if (startHour < workStart || endHour > workEnd) {
    throw new Error(`Horário fora do expediente: ${timeStart}-${timeEnd} (expediente: ${$env.CALENDAR_WORK_START}-${$env.CALENDAR_WORK_END})`);
}

// Check weekend
const dayOfWeek = new Date(scheduledDate).getDay();
const workDays = $env.CALENDAR_WORK_DAYS.split(',').map(d => parseInt(d));

if (!workDays.includes(dayOfWeek)) {
    throw new Error(`Dia não útil: ${scheduledDate} (dia da semana: ${dayOfWeek})`);
}

console.log('✅ [Validate Availability] Approved:', scheduledDate, timeStart);

return {
    ...data,
    validation_status: 'approved',
    validated_at: new Date().toISOString()
};
""".strip()

    return {
        "parameters": {
            "jsCode": js_code
        },
        "id": "validate-availability-v2",
        "name": "Validate Availability",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [850, 300],
        "alwaysOutputData": True,
        "notes": "Business hours validation (CALENDAR_WORK_START/END/DAYS)"
    }

def create_build_calendar_event_node():
    """Build Calendar Event Data (refactored modular)"""
    js_code = """
// Build Calendar Event Data (V2.0 - Modular)
const data = $input.first().json;

// --- Configuration ---
const SERVICE_CONFIG = {
    'energia_solar': {
        name: 'Energia Solar',
        duration: 120,
        color: '9'
    },
    'subestacao': {
        name: 'Subestação',
        duration: 180,
        color: '11'
    },
    'projeto_eletrico': {
        name: 'Projeto Elétrico',
        duration: 90,
        color: '5'
    },
    'armazenamento_energia': {
        name: 'BESS',
        duration: 120,
        color: '10'
    },
    'analise_laudo': {
        name: 'Análise/Laudo',
        duration: 120,
        color: '8'
    }
};

// --- Get Service Config ---
const serviceConfig = SERVICE_CONFIG[data.service_type] || {
    name: data.service_type,
    duration: 90,
    color: '1'
};

// --- Build DateTime ---
const startDateTime = new Date(`${data.scheduled_date}T${data.scheduled_time_start}`);
const endDateTime = new Date(`${data.scheduled_date}T${data.scheduled_time_end}`);

// --- Build Event Title ---
const eventTitle = `[E2] Visita ${serviceConfig.name} - ${data.lead_name}`;

// --- Build Description ---
let description = `=== VISITA TÉCNICA E2 SOLUÇÕES ===\\n\\n`;
description += `CLIENTE: ${data.lead_name}\\n`;
description += `TELEFONE: ${data.phone_number}\\n`;
description += `EMAIL: ${data.lead_email || 'Não informado'}\\n`;
description += `ENDEREÇO: ${data.address}, ${data.city}/${data.state}\\n`;
description += `\\nSERVIÇO: ${serviceConfig.name}\\n`;

// Service details (if JSONB exists)
if (data.service_details) {
    const details = typeof data.service_details === 'string'
        ? JSON.parse(data.service_details)
        : data.service_details;

    description += `\\n--- DADOS DO SERVIÇO ---\\n`;

    for (const [key, value] of Object.entries(details)) {
        if (value) {
            description += `${key}: ${value}\\n`;
        }
    }
}

// Appointment notes
if (data.notes) {
    description += `\\n--- OBSERVAÇÕES ---\\n${data.notes}\\n`;
}

// Links
description += `\\n--- LINKS ---\\n`;
if (data.rdstation_deal_id) {
    description += `RD Station Deal: ${$env.RDSTATION_URL}/deals/${data.rdstation_deal_id}\\n`;
}
description += `WhatsApp: https://wa.me/${data.phone_number.replace(/\\D/g, '')}\\n`;

// --- Build Attendees ---
const attendees = [
    { email: $env.GOOGLE_TECHNICIAN_EMAIL }
];

if (data.lead_email && data.lead_email.includes('@')) {
    attendees.push({ email: data.lead_email });
}

// --- Build Location ---
const location = `${data.address}, ${data.city} - ${data.state}${data.zip_code ? ', ' + data.zip_code : ''}`;

// --- Build Reminders ---
const reminders = {
    useDefault: false,
    overrides: [
        { method: 'email', minutes: 1440 }, // 24h
        { method: 'popup', minutes: 120 },  // 2h
        { method: 'email', minutes: 120 }   // 2h
    ]
};

// --- Return Event Data ---
console.log('✅ [Build Calendar Event] Created:', eventTitle);

return {
    // Event data for Google Calendar
    calendar_event: {
        summary: eventTitle,
        description: description,
        location: location,
        start: {
            dateTime: startDateTime.toISOString(),
            timeZone: $env.CALENDAR_TIMEZONE || 'America/Sao_Paulo'
        },
        end: {
            dateTime: endDateTime.toISOString(),
            timeZone: $env.CALENDAR_TIMEZONE || 'America/Sao_Paulo'
        },
        attendees: attendees,
        reminders: reminders,
        colorId: serviceConfig.color
    },

    // Metadata for next nodes
    appointment_id: data.appointment_id,
    lead_id: data.lead_id,
    lead_name: data.lead_name,
    service_type: data.service_type,
    rdstation_deal_id: data.rdstation_deal_id,
    phone_number: data.phone_number
};
""".strip()

    return {
        "parameters": {
            "jsCode": js_code
        },
        "id": "build-calendar-event-v2",
        "name": "Build Calendar Event Data",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [1050, 300],
        "alwaysOutputData": True,
        "notes": "V2.0: Modular config-driven event builder"
    }

def create_google_calendar_node():
    """Create Google Calendar Event (with retry)"""
    return {
        "parameters": {
            "resource": "event",
            "operation": "create",
            "calendarId": "={{ $env.GOOGLE_CALENDAR_ID }}",
            "start": "={{ $json.calendar_event.start.dateTime }}",
            "end": "={{ $json.calendar_event.end.dateTime }}",
            "summary": "={{ $json.calendar_event.summary }}",
            "additionalFields": {
                "description": "={{ $json.calendar_event.description }}",
                "location": "={{ $json.calendar_event.location }}",
                "attendees": "={{ JSON.stringify($json.calendar_event.attendees) }}",
                "colorId": "={{ $json.calendar_event.colorId }}",
                "reminders": "={{ JSON.stringify($json.calendar_event.reminders) }}"
            }
        },
        "id": "create-google-event-v2",
        "name": "Create Google Calendar Event",
        "type": "n8n-nodes-base.googleCalendar",
        "typeVersion": 2,
        "position": [1250, 300],
        "credentials": {
            "googleCalendarOAuth2Api": {
                "id": "={{ $env.GOOGLE_CALENDAR_CREDENTIAL_ID }}",
                "name": "Google Calendar API"
            }
        },
        "continueOnFail": True,
        "alwaysOutputData": True,
        "retryOnFail": True,
        "maxTries": 3,
        "waitBetweenTries": 1000,
        "notes": "V2.0: Retry logic (3x) + continueOnFail for error handling"
    }

def create_update_appointment_node():
    """Update Appointment (atomic with CASE for success/error)"""
    query = """
UPDATE appointments
SET
    google_calendar_event_id = CASE
        WHEN $2 IS NOT NULL THEN $2
        ELSE google_calendar_event_id
    END,
    status = CASE
        WHEN $2 IS NOT NULL THEN 'confirmado'
        ELSE 'erro_calendario'
    END,
    notes = CASE
        WHEN $2 IS NULL AND $3 IS NOT NULL
        THEN COALESCE(notes, '') || '\\n[ERRO] Falha ao criar evento no Google Calendar: ' || $3
        ELSE notes
    END,
    updated_at = NOW()
WHERE id = $1
RETURNING
    id,
    status,
    google_calendar_event_id,
    CASE
        WHEN google_calendar_event_id IS NOT NULL THEN true
        ELSE false
    END as calendar_success;
""".strip()

    return {
        "parameters": {
            "operation": "executeQuery",
            "query": query,
            "additionalFields": {
                "queryParameters": "={{ $('Build Calendar Event Data').item.json.appointment_id }},={{ $('Create Google Calendar Event').item.json.id || null }},={{ $('Create Google Calendar Event').item.json.error || null }}"
            }
        },
        "id": "update-appointment-v2",
        "name": "Update Appointment",
        "type": "n8n-nodes-base.postgres",
        "typeVersion": 2,
        "position": [1450, 300],
        "credentials": {
            "postgres": {
                "id": "1",
                "name": "PostgreSQL - E2 Bot"
            }
        },
        "alwaysOutputData": True,
        "notes": "V2.0: Atomic update with CASE for success/error handling"
    }

def create_reminders_node():
    """Create Appointment Reminders"""
    return {
        "parameters": {
            "operation": "executeQuery",
            "query": "SELECT create_appointment_reminders($1);",
            "additionalFields": {
                "queryParameters": "={{ $('Build Calendar Event Data').item.json.appointment_id }}"
            }
        },
        "id": "create-appointment-reminders-v2",
        "name": "Create Appointment Reminders",
        "type": "n8n-nodes-base.postgres",
        "typeVersion": 2,
        "position": [1650, 300],
        "credentials": {
            "postgres": {
                "id": "1",
                "name": "PostgreSQL - E2 Bot"
            }
        },
        "onlyIf": "{{ $json.calendar_success === true }}",
        "notes": "Only execute if Google Calendar success"
    }

def create_rdstation_task_node():
    """Create RD Station Task (OPTIONAL)"""
    return {
        "parameters": {
            "method": "POST",
            "url": "={{ $env.RDSTATION_API_URL }}/tasks",
            "sendHeaders": True,
            "headerParameters": {
                "parameters": [
                    {
                        "name": "Content-Type",
                        "value": "application/json"
                    },
                    {
                        "name": "Authorization",
                        "value": "Bearer {{ $env.RDSTATION_ACCESS_TOKEN }}"
                    }
                ]
            },
            "sendBody": True,
            "specifyBody": "json",
            "jsonBody": "={{ JSON.stringify({ subject: 'Visita Técnica - ' + $('Build Calendar Event Data').item.json.lead_name, deal_id: $('Build Calendar Event Data').item.json.rdstation_deal_id, assigned_user_id: $env.RDSTATION_USER_TECNICO, due_date: $('Get Appointment & Lead Data').item.json.scheduled_date, notes: 'Visita técnica agendada via bot WhatsApp' }) }}"
        },
        "id": "create-rdstation-task-v2",
        "name": "Create RD Station Task (OPTIONAL)",
        "type": "n8n-nodes-base.httpRequest",
        "typeVersion": 4.1,
        "position": [1850, 300],
        "continueOnFail": True,
        "alwaysOutputData": True,
        "onlyIf": "{{ $json.calendar_success === true }}",
        "notes": "V2.0: RD Station integration is OPTIONAL. Workflow continues even if this fails."
    }

def create_confirmation_email_node():
    """Send Confirmation Email"""
    return {
        "parameters": {
            "workflowId": "={{ $env.WORKFLOW_ID_EMAIL_CONFIRMATION || '7' }}",
            "options": {}
        },
        "id": "send-confirmation-email-v2",
        "name": "Send Confirmation Email",
        "type": "n8n-nodes-base.executeWorkflow",
        "typeVersion": 1,
        "position": [2050, 300],
        "onlyIf": "{{ $json.calendar_success === true }}",
        "notes": "Only send if Google Calendar success"
    }

def create_log_error_node():
    """Log Error & Notify (error path)"""
    js_code = """
// Log Error & Notify
const error = $input.first().json.error || 'Unknown error';
const appointmentId = $('Build Calendar Event Data').first().json.appointment_id;

console.error('❌ [Google Calendar Error]', {
    appointment_id: appointmentId,
    error: error,
    timestamp: new Date().toISOString()
});

// Send notification to admin (placeholder)
return {
    error_type: 'google_calendar_failure',
    appointment_id: appointmentId,
    error_message: error,
    notify_admin: true,
    retry_scheduled: false
};
""".strip()

    return {
        "parameters": {
            "jsCode": js_code
        },
        "id": "log-error-notify-v2",
        "name": "Log Error & Notify",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [1250, 500],
        "alwaysOutputData": True,
        "notes": "V2.0: Error logging and admin notification"
    }

# ============================================================================
# CONNECTIONS
# ============================================================================

def create_connections():
    """Create node connections"""
    return {
        "Execute Workflow Trigger": {
            "main": [[{
                "node": "Validate Input Data",
                "type": "main",
                "index": 0
            }]]
        },
        "Validate Input Data": {
            "main": [[{
                "node": "Get Appointment & Lead Data",
                "type": "main",
                "index": 0
            }]]
        },
        "Get Appointment & Lead Data": {
            "main": [[{
                "node": "Validate Availability",
                "type": "main",
                "index": 0
            }]]
        },
        "Validate Availability": {
            "main": [[{
                "node": "Build Calendar Event Data",
                "type": "main",
                "index": 0
            }]]
        },
        "Build Calendar Event Data": {
            "main": [[{
                "node": "Create Google Calendar Event",
                "type": "main",
                "index": 0
            }]]
        },
        "Create Google Calendar Event": {
            "main": [
                [{
                    "node": "Update Appointment",
                    "type": "main",
                    "index": 0
                }],
                [{
                    "node": "Log Error & Notify",
                    "type": "main",
                    "index": 0
                }]
            ]
        },
        "Update Appointment": {
            "main": [[{
                "node": "Create Appointment Reminders",
                "type": "main",
                "index": 0
            }]]
        },
        "Create Appointment Reminders": {
            "main": [[{
                "node": "Create RD Station Task (OPTIONAL)",
                "type": "main",
                "index": 0
            }]]
        },
        "Create RD Station Task (OPTIONAL)": {
            "main": [[{
                "node": "Send Confirmation Email",
                "type": "main",
                "index": 0
            }]]
        },
        "Log Error & Notify": {
            "main": [[{
                "node": "Update Appointment",
                "type": "main",
                "index": 0
            }]]
        }
    }

# ============================================================================
# WORKFLOW BUILDER
# ============================================================================

def build_workflow():
    """Build complete workflow JSON"""
    workflow = {
        "name": WORKFLOW_NAME,
        "nodes": [
            create_trigger_node(),
            create_validate_input_node(),
            create_get_appointment_lead_node(),
            create_validate_availability_node(),
            create_build_calendar_event_node(),
            create_google_calendar_node(),
            create_update_appointment_node(),
            create_reminders_node(),
            create_rdstation_task_node(),
            create_confirmation_email_node(),
            create_log_error_node()
        ],
        "connections": create_connections(),
        "settings": {
            "executionOrder": "v1"
        },
        "staticData": None,
        "tags": [
            {
                "name": "appointment",
                "createdAt": CREATED_DATE
            },
            {
                "name": "google-calendar",
                "createdAt": CREATED_DATE
            },
            {
                "name": "v2.0",
                "createdAt": CREATED_DATE
            }
        ],
        "triggerCount": 1,
        "updatedAt": CREATED_DATE,
        "versionId": WORKFLOW_VERSION
    }

    return workflow

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Generate workflow JSON file"""
    print("=" * 80)
    print("APPOINTMENT SCHEDULER V2.0 - Workflow Generator")
    print("=" * 80)
    print(f"Version: {WORKFLOW_VERSION}")
    print(f"Date: {CREATED_DATE}")
    print(f"Pattern: V69.2 Compliance")
    print("=" * 80)

    # Build workflow
    workflow = build_workflow()

    # Output path
    output_path = "n8n/workflows/05_appointment_scheduler_v2.1.json"

    # Write JSON file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Workflow generated successfully!")
    print(f"📄 File: {output_path}")
    print(f"📊 Nodes: {len(workflow['nodes'])}")
    print(f"🔗 Connections: {len(workflow['connections'])}")

    print("\n" + "=" * 80)
    print("NEXT STEPS:")
    print("=" * 80)
    print("1. Import workflow in n8n: http://localhost:5678")
    print("2. Configure credentials:")
    print("   - PostgreSQL - E2 Bot")
    print("   - Google Calendar OAuth2")
    print("3. Set environment variables in .env:")
    print("   - GOOGLE_CALENDAR_ID")
    print("   - GOOGLE_CALENDAR_CREDENTIAL_ID")
    print("   - CALENDAR_WORK_START/END/DAYS")
    print("   - RDSTATION_* (optional)")
    print("4. Test with sample appointment_id")
    print("=" * 80)

if __name__ == "__main__":
    main()
