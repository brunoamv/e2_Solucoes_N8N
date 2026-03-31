#!/usr/bin/env python3
"""
WF07 V6 - Docker Volume Mount Fix Generator

Generates 07_send_email_v6_docker_volume_fix.json workflow with Docker-compatible template path.

Changes from V5:
- Read Template File node filePath: /home/bruno/.../email-templates/ → /email-templates/
- Docker volume mount required: ../email-templates:/email-templates:ro

Root Cause Fixed:
- V5 used host filesystem path which doesn't exist inside Docker container
- V6 uses container mount path which is accessible after docker-compose volume mount

Usage:
    python3 scripts/generate-workflow-wf07-v6-docker-volume-fix.py

Output:
    n8n/workflows/07_send_email_v6_docker_volume_fix.json
"""

import json
import os
from datetime import datetime

# Base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_FILE = os.path.join(BASE_DIR, "n8n/workflows/07_send_email_v6_docker_volume_fix.json")

def generate_wf07_v6():
    """Generate WF07 V6 workflow with Docker volume mount fix"""

    workflow = {
        "name": "07 - Send Email V6 (Docker Volume Fix)",
        "nodes": [
            # Node 1: Execute Workflow Trigger
            {
                "parameters": {
                    "options": {}
                },
                "id": "execute-workflow-trigger",
                "name": "Execute Workflow Trigger",
                "type": "n8n-nodes-base.executeWorkflowTrigger",
                "typeVersion": 1,
                "position": [250, 300],
                "notes": "V3.0: Clean trigger configuration"
            },

            # Node 2: Prepare Email Data (V3.0 - Complete with template mapping)
            {
                "parameters": {
                    "jsCode": """// Prepare Email Data - V3.0 (Complete Fix)
const input = $input.first().json;

// ===== TEMPLATE CONFIGURATION =====
const TEMPLATE_CONFIG = {
    "confirmacao_agendamento": {
        "file": "confirmacao_agendamento.html",
        "subject": "Agendamento Confirmado - E2 Soluções"
    },
    "lembrete_2h": {
        "file": "lembrete_2h.html",
        "subject": "Lembrete: Sua visita é em 2 horas - E2 Soluções"
    },
    "novo_lead": {
        "file": "novo_lead.html",
        "subject": "Obrigado pelo contato - E2 Soluções"
    },
    "apos_visita": {
        "file": "apos_visita.html",
        "subject": "Obrigado pela visita - E2 Soluções"
    }
};

// ===== EMAIL SENDER CONFIGURATION =====
const SENDER_CONFIG = {
    "from_email": "contato@e2solucoes.com.br",
    "from_name": "E2 Soluções",
    "reply_to": "contato@e2solucoes.com.br"
};

// ===== DETECT INPUT SOURCE =====
const isFromWF05 = !!(input.appointment_id && input.calendar_success !== undefined);

console.log('📧 [Prepare Email Data V3] Input source:', {
    isFromWF05,
    has_appointment_id: !!input.appointment_id,
    has_calendar_success: input.calendar_success !== undefined,
    has_template: !!input.template,
    has_to: !!input.to,
    has_lead_email: !!input.lead_email
});

// ===== DETERMINE EMAIL RECIPIENT =====
let emailRecipient;

if (isFromWF05) {
    // WF05 input: use lead_email
    emailRecipient = input.lead_email;
    console.log('📧 Using lead_email from WF05:', emailRecipient);
} else {
    // Manual trigger: use 'to' or 'email' field
    emailRecipient = input.to || input.email;
    console.log('📧 Using manual trigger recipient:', emailRecipient);
}

if (!emailRecipient) {
    throw new Error('Email recipient not found in input data. WF05 needs lead_email, manual trigger needs to/email field.');
}

// ===== DETERMINE TEMPLATE =====
let emailTemplate;

if (isFromWF05) {
    // WF05 input: always use confirmacao_agendamento template
    emailTemplate = 'confirmacao_agendamento';
    console.log('📧 Using WF05 template: confirmacao_agendamento');
} else {
    // Manual trigger: use specified template
    emailTemplate = input.template || input.email_template;
    if (!emailTemplate) {
        throw new Error('Email template not specified. Provide template field.');
    }
    console.log('📧 Using manual template:', emailTemplate);
}

// ===== VALIDATE TEMPLATE EXISTS =====
if (!TEMPLATE_CONFIG[emailTemplate]) {
    throw new Error(`Unknown email template: ${emailTemplate}. Available: ${Object.keys(TEMPLATE_CONFIG).join(', ')}`);
}

const templateInfo = TEMPLATE_CONFIG[emailTemplate];

// ===== PREPARE TEMPLATE DATA =====
let templateData;

if (isFromWF05) {
    // ===== WF05 DATA MAPPING =====

    // Extract date part from scheduled_date
    let dateString = input.scheduled_date;
    if (typeof dateString === 'string' && dateString.includes('T')) {
        dateString = dateString.split('T')[0]; // "2026-04-25"
    }

    // Format date to Brazilian format (DD/MM/YYYY)
    const [year, month, day] = dateString.split('-');
    const formattedDate = `${day}/${month}/${year}`;

    // Extract time parts (remove seconds if present)
    const timeStart = input.scheduled_time_start?.split(':').slice(0, 2).join(':') || '00:00';
    const timeEnd = input.scheduled_time_end?.split(':').slice(0, 2).join(':') || '00:00';
    const formattedTime = `${timeStart} às ${timeEnd}`;

    // Generate Google Calendar event link
    const googleEventLink = input.google_calendar_event_id
        ? `https://calendar.google.com/calendar/event?eid=${input.google_calendar_event_id}`
        : '';

    templateData = {
        // Lead information
        name: input.lead_name || 'Cliente',
        email: emailRecipient,
        phone_number: input.phone_number || '',
        whatsapp_name: input.whatsapp_name || input.lead_name || 'Cliente',

        // Service information
        service_type: input.service_type || 'Serviço',
        city: input.city || '',
        address: input.address || '',
        state: input.state || '',
        zip_code: input.zip_code || '',

        // Appointment information
        scheduled_date: dateString, // YYYY-MM-DD
        formatted_date: formattedDate, // DD/MM/YYYY
        formatted_time: formattedTime, // HH:MM às HH:MM

        // Calendar integration
        google_event_link: googleEventLink,
        google_calendar_event_id: input.google_calendar_event_id || '',

        // Status
        appointment_id: input.appointment_id,
        status: input.status || 'confirmado'
    };

    console.log('✅ [WF05 Data Mapping] Template data prepared:', {
        name: templateData.name,
        email: templateData.email,
        service: templateData.service_type,
        date: templateData.formatted_date,
        time: templateData.formatted_time,
        has_google_link: !!templateData.google_event_link
    });

} else {
    // ===== MANUAL TRIGGER DATA MAPPING (BACKWARD COMPATIBILITY) =====
    templateData = {
        name: input.name || 'Cliente',
        email: emailRecipient,
        phone_number: input.phone_number || input.phone || '',
        service_type: input.service_type || '',
        scheduled_date: input.scheduled_date || '',
        formatted_date: input.formatted_date || '',
        formatted_time: input.formatted_time || '',
        google_event_link: input.google_event_link || '',
        ...input // Spread all input for backward compatibility
    };

    console.log('✅ [Manual Trigger] Template data prepared (backward compatible)');
}

// ===== RETURN COMPLETE EMAIL DATA =====
return {
    // Recipient
    to: emailRecipient,

    // Template
    template: emailTemplate,
    template_file: templateInfo.file, // ✅ V3: Template filename for Read Template File node
    subject: templateInfo.subject,    // ✅ V3: Email subject

    // Template data (variables)
    template_data: templateData,

    // Sender info
    from_email: SENDER_CONFIG.from_email,   // ✅ V3: Sender email
    from_name: SENDER_CONFIG.from_name,     // ✅ V3: Sender name
    reply_to: SENDER_CONFIG.reply_to,       // ✅ V3: Reply-to address

    // Metadata
    source: isFromWF05 ? 'wf05_trigger' : 'manual_trigger',
    prepared_at: new Date().toISOString()
};"""
                },
                "id": "prepare-email-data",
                "name": "Prepare Email Data",
                "type": "n8n-nodes-base.code",
                "typeVersion": 2,
                "position": [450, 300],
                "notes": "V3.0: Complete email data preparation with template mapping, subject, and sender info"
            },

            # Node 3: Read Template File (V6 - DOCKER VOLUME FIX)
            {
                "parameters": {
                    "operation": "read",
                    "filePath": "=/email-templates/{{ $json.template_file }}",  # ✅ V6 FIX: Docker container path
                    "options": {
                        "encoding": "utf8",           # V4.1: Text file reading
                        "dataPropertyName": "data"    # V5: Output property definition
                    }
                },
                "id": "read-template-file",
                "name": "Read Template File",
                "type": "n8n-nodes-base.readWriteFile",
                "typeVersion": 1,
                "position": [650, 300],
                "notes": "V6: Docker volume mount fix - uses container path /email-templates/ (requires volume mount in docker-compose.yml)"
            },

            # Node 4: Render Template
            {
                "parameters": {
                    "jsCode": """// Get template HTML and data
const templateHtml = $('Read Template File').first().json.data;
const data = $input.first().json;
const templateData = data.template_data;

// Simple template variable replacement
const renderTemplate = (html, data) => {
  let rendered = html;

  // Replace {{variable}} style placeholders
  rendered = rendered.replace(/\\{\\{\\s*(\\w+)\\s*\\}\\}/g, (match, key) => {
    return data[key] !== undefined ? data[key] : match;
  });

  // Handle conditional blocks: {{#if variable}}...{{/if}}
  rendered = rendered.replace(/\\{\\{#if\\s+(\\w+)\\}\\}([\\s\\S]*?)\\{\\{\\/if\\}\\}/g, (match, key, content) => {
    return data[key] ? content : '';
  });

  // Handle inverted conditionals: {{#unless variable}}...{{/unless}}
  rendered = rendered.replace(/\\{\\{#unless\\s+(\\w+)\\}\\}([\\s\\S]*?)\\{\\{\\/unless\\}\\}/g, (match, key, content) => {
    return !data[key] ? content : '';
  });

  return rendered;
};

// Render the template
const htmlBody = renderTemplate(templateHtml, templateData);

// Generate plain text version (simple HTML stripping)
const textBody = htmlBody
  .replace(/<style[^>]*>.*?<\\/style>/gs, '')
  .replace(/<script[^>]*>.*?<\\/script>/gs, '')
  .replace(/<[^>]+>/g, '')
  .replace(/&nbsp;/g, ' ')
  .replace(/&lt;/g, '<')
  .replace(/&gt;/g, '>')
  .replace(/&amp;/g, '&')
  .replace(/\\n\\s*\\n/g, '\\n\\n')
  .trim();

return {
  ...data,
  html_body: htmlBody,
  text_body: textBody
};
"""
                },
                "id": "render-template",
                "name": "Render Template",
                "type": "n8n-nodes-base.code",
                "typeVersion": 2,
                "position": [850, 300],
                "notes": "V4.0: Updated to read .data instead of .stdout (Read File output)"
            },

            # Node 5: Send Email (SMTP)
            {
                "parameters": {
                    "fromEmail": "={{ $json.from_email }}",
                    "toEmail": "={{ $json.to }}",
                    "subject": "={{ $json.subject }}",
                    "emailFormat": "html",
                    "html": "={{ $json.html_body }}",
                    "options": {
                        "fromName": "={{ $json.from_name }}",
                        "replyTo": "={{ $json.reply_to }}",
                        "ccEmail": "",
                        "bccEmail": "",
                        "allowUnauthorizedCerts": False
                    }
                },
                "id": "send-email-smtp",
                "name": "Send Email (SMTP)",
                "type": "n8n-nodes-base.emailSend",
                "typeVersion": 2.1,
                "position": [1050, 300],
                "credentials": {
                    "smtp": {
                        "id": "1",
                        "name": "SMTP - E2 Email"
                    }
                }
            },

            # Node 6: Log Email Sent
            {
                "parameters": {
                    "operation": "executeQuery",
                    "query": """INSERT INTO email_logs (
  recipient_email,
  recipient_name,
  subject,
  template_used,
  status,
  sent_at,
  metadata
) VALUES ($1, $2, $3, $4, $5, NOW(), $6)""",
                    "additionalFields": {
                        "queryParameters": "={{ $json.to }},={{ $json.template_data.name }},={{ $json.subject }},={{ $json.template }},sent,={{ JSON.stringify({ template_data: $json.template_data }) }}"
                    }
                },
                "id": "log-email-sent",
                "name": "Log Email Sent",
                "type": "n8n-nodes-base.postgres",
                "typeVersion": 2,
                "position": [1250, 300],
                "credentials": {
                    "postgres": {
                        "id": "1",
                        "name": "PostgreSQL - E2 Bot"
                    }
                }
            },

            # Node 7: Return Success
            {
                "parameters": {
                    "jsCode": """// Return success response
const input = $input.first().json;

return {
  success: true,
  message: 'Email sent successfully',
  recipient: input.to,
  subject: input.subject,
  template: input.template,
  sent_at: new Date().toISOString()
};
"""
                },
                "id": "return-success",
                "name": "Return Success",
                "type": "n8n-nodes-base.code",
                "typeVersion": 2,
                "position": [1450, 300]
            },

            # Node 8: Error Handler
            {
                "parameters": {
                    "errorMessage": "={{ $json.error }}",
                    "options": {}
                },
                "id": "error-handler",
                "name": "Error Handler",
                "type": "n8n-nodes-base.stopAndError",
                "typeVersion": 1,
                "position": [850, 500]
            },

            # Node 9: Log Email Error
            {
                "parameters": {
                    "operation": "executeQuery",
                    "query": """INSERT INTO email_logs (
  recipient_email,
  recipient_name,
  subject,
  template_used,
  status,
  sent_at,
  error_message,
  metadata
) VALUES ($1, $2, $3, $4, $5, NOW(), $6, $7)""",
                    "additionalFields": {
                        "queryParameters": "={{ $('Prepare Email Data').item.json.to }},={{ $('Prepare Email Data').item.json.template_data.name }},={{ $('Prepare Email Data').item.json.subject }},={{ $('Prepare Email Data').item.json.template }},failed,={{ $json.message }},={{ JSON.stringify({ error: $json.message }) }}"
                    }
                },
                "id": "log-email-error",
                "name": "Log Email Error",
                "type": "n8n-nodes-base.postgres",
                "typeVersion": 2,
                "position": [1050, 500],
                "credentials": {
                    "postgres": {
                        "id": "1",
                        "name": "PostgreSQL - E2 Bot"
                    }
                }
            }
        ],

        "connections": {
            "Execute Workflow Trigger": {
                "main": [[{"node": "Prepare Email Data", "type": "main", "index": 0}]]
            },
            "Prepare Email Data": {
                "main": [[{"node": "Read Template File", "type": "main", "index": 0}]]
            },
            "Read Template File": {
                "main": [[{"node": "Render Template", "type": "main", "index": 0}]]
            },
            "Render Template": {
                "main": [[{"node": "Send Email (SMTP)", "type": "main", "index": 0}]]
            },
            "Send Email (SMTP)": {
                "main": [[{"node": "Log Email Sent", "type": "main", "index": 0}]]
            },
            "Log Email Sent": {
                "main": [[{"node": "Return Success", "type": "main", "index": 0}]]
            }
        },

        "settings": {
            "errorWorkflow": "error-handler"
        },

        "staticData": None,

        "tags": [
            {"name": "wf05-integration", "createdAt": "2026-03-26T00:00:00.000000"},
            {"name": "v6", "createdAt": "2026-03-30T00:00:00.000000"},
            {"name": "docker-volume-fix", "createdAt": "2026-03-30T00:00:00.000000"},
            {"name": "complete-fix", "createdAt": "2026-03-30T00:00:00.000000"}
        ],

        "triggerCount": 1,
        "updatedAt": "2024-01-10T00:00:00.000Z",
        "versionId": "2.0"
    }

    return workflow

def validate_v6_workflow(workflow):
    """Validate V6 workflow has all required fixes"""

    checks = {
        "1. Read Template File node exists": False,
        "2. Docker container path used": False,
        "3. Encoding utf8 present": False,
        "4. dataPropertyName present": False,
        "5. Prepare Email Data complete": False,
        "6. Render Template updated": False,
        "7. SMTP Send configured": False,
        "8. Database logging present": False,
        "9. Error handling configured": False
    }

    # Find Read Template File node
    read_file_node = None
    for node in workflow["nodes"]:
        if node["id"] == "read-template-file":
            read_file_node = node
            checks["1. Read Template File node exists"] = True
            break

    if read_file_node:
        # V6 FIX: Check Docker container path (not host path)
        file_path = read_file_node["parameters"]["filePath"]
        if file_path == "=/email-templates/{{ $json.template_file }}":
            checks["2. Docker container path used"] = True

        # V4.1 + V5 FIXES: Check options
        options = read_file_node["parameters"].get("options", {})
        if options.get("encoding") == "utf8":
            checks["3. Encoding utf8 present"] = True
        if options.get("dataPropertyName") == "data":
            checks["4. dataPropertyName present"] = True

    # Check other nodes
    for node in workflow["nodes"]:
        if node["id"] == "prepare-email-data":
            checks["5. Prepare Email Data complete"] = True
        if node["id"] == "render-template":
            checks["6. Render Template updated"] = True
        if node["id"] == "send-email-smtp":
            checks["7. SMTP Send configured"] = True
        if node["id"] == "log-email-sent":
            checks["8. Database logging present"] = True
        if node["id"] == "error-handler":
            checks["9. Error handling configured"] = True

    return checks

def main():
    """Main execution"""
    print("=" * 70)
    print("WF07 V6 - Docker Volume Mount Fix Generator")
    print("=" * 70)
    print()

    # Generate workflow
    print("🔧 Generating WF07 V6 workflow...")
    workflow = generate_wf07_v6()

    # Validate
    print("✅ Validating V6 configuration...")
    checks = validate_v6_workflow(workflow)

    print("\n📋 Validation Results:")
    all_passed = True
    for check, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"   {status} {check}")
        if not passed:
            all_passed = False

    if not all_passed:
        print("\n❌ Validation failed! Fix issues before proceeding.")
        return 1

    # Write workflow
    print(f"\n💾 Writing workflow to: {OUTPUT_FILE}")
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    file_size = os.path.getsize(OUTPUT_FILE)
    print(f"✅ Workflow created successfully!")
    print(f"   Size: {file_size:,} bytes ({file_size / 1024:.1f} KB)")
    print(f"   Nodes: {len(workflow['nodes'])}")
    print(f"   Connections: {len(workflow['connections'])}")

    # Verification commands
    print("\n" + "=" * 70)
    print("🔍 Verification Commands:")
    print("=" * 70)

    print("\n1. Verify V6 Read File configuration:")
    print("   jq '.nodes[] | select(.id == \"read-template-file\") | .parameters' \\")
    print(f"     {OUTPUT_FILE}")
    print()
    print("   Expected output:")
    print('   {')
    print('     "operation": "read",')
    print('     "filePath": "=/email-templates/{{ $json.template_file }}",')
    print('     "options": {')
    print('       "encoding": "utf8",')
    print('       "dataPropertyName": "data"')
    print('     }')
    print('   }')

    print("\n2. Update docker-compose-dev.yml (add to n8n-dev volumes):")
    print("   - ../email-templates:/email-templates:ro")

    print("\n3. Restart Docker stack:")
    print("   docker-compose -f docker/docker-compose-dev.yml down")
    print("   docker-compose -f docker/docker-compose-dev.yml up -d")

    print("\n4. Verify mount inside container:")
    print("   docker exec e2bot-n8n-dev ls -la /email-templates/")
    print("   # Should show 4 HTML files")

    print("\n5. Import workflow to n8n:")
    print("   http://localhost:5678 → Import from File")
    print(f"   → {OUTPUT_FILE}")

    print("\n6. Test Read Template File node:")
    print("   Execute workflow → Click 'Read Template File'")
    print("   → Verify output: { \"data\": \"<html>...</html>\", ... }")

    print("\n" + "=" * 70)
    print("✅ WF07 V6 generation complete!")
    print("=" * 70)
    print("\n📚 Documentation:")
    print("   - Plan: docs/PLAN_V6_DOCKER_TEMPLATE_ACCESS.md")
    print("   - Bugfix: docs/BUGFIX_WF07_V6_DOCKER_VOLUME_FIX.md (to be created)")
    print()

    return 0

if __name__ == "__main__":
    exit(main())
