#!/usr/bin/env python3
"""
WF07 V5 Generator - Data Property Fix (Complete Read File Solution)

Root Cause: V4.1 "Read Template File" returns "No output data"
Issue: Missing dataPropertyName parameter in readWriteFile node options
Solution: Add dataPropertyName: "data" to define output property name

Changes from V4.1:
1. Read Template File node: Add "dataPropertyName": "data" to options
2. Update workflow name: V4.1 → V5
3. Update notes: Complete data property fix
4. Update tags: v4.1 → v5, add data-property-fix

Technical Impact:
- n8n now stores file content in accessible .data property
- Output format: { "data": "<html>...</html>", ... }
- Render Template node receives expected data structure
- Complete workflow execution: Read → Render → Send Email ✅
"""

import json
import sys
from datetime import datetime

def create_wf07_v5():
    """Generate WF07 V5 workflow with data property fix"""

    workflow = {
        "name": "07 - Send Email V5 (Data Property Fix)",
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

            # Node 2: Prepare Email Data (V3.0 - unchanged from V4.1)
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

            # Node 3: Read Template File (V5 - CRITICAL FIX)
            {
                "parameters": {
                    "operation": "read",
                    "filePath": "=/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/email-templates/{{ $json.template_file }}",
                    "options": {
                        "encoding": "utf8",          # V4.1: Text file reading
                        "dataPropertyName": "data"   # V5: ✅ CRITICAL FIX - Define output property name
                    }
                },
                "id": "read-template-file",
                "name": "Read Template File",
                "type": "n8n-nodes-base.readWriteFile",
                "typeVersion": 1,
                "position": [650, 300],
                "notes": "V5: Complete data property fix - encoding + dataPropertyName for accessible output"
            },

            # Node 4: Render Template (unchanged from V4.1)
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

            # Node 5: Send Email (SMTP) (unchanged)
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

            # Node 6: Log Email Sent (unchanged)
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

            # Node 7: Return Success (unchanged)
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

            # Node 8: Error Handler (unchanged)
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

            # Node 9: Log Email Error (unchanged)
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
            {"name": "v5", "createdAt": "2026-03-30T00:00:00.000000"},
            {"name": "data-property-fix", "createdAt": "2026-03-30T00:00:00.000000"},
            {"name": "complete-fix", "createdAt": "2026-03-30T00:00:00.000000"}
        ],

        "triggerCount": 1,
        "updatedAt": "2024-01-10T00:00:00.000Z",
        "versionId": "2.0"
    }

    return workflow


def validate_workflow(workflow):
    """Validate V5 workflow structure"""

    print("\n🔍 Validating WF07 V5 workflow...")

    errors = []
    warnings = []

    # Check workflow name
    if "V5" not in workflow["name"]:
        errors.append("❌ Workflow name must contain 'V5'")
    else:
        print("✅ Workflow name correct: V5 (Data Property Fix)")

    # Check nodes count
    if len(workflow["nodes"]) != 9:
        errors.append(f"❌ Expected 9 nodes, found {len(workflow['nodes'])}")
    else:
        print(f"✅ Node count correct: 9 nodes")

    # Find Read Template File node
    read_file_node = None
    for node in workflow["nodes"]:
        if node["id"] == "read-template-file":
            read_file_node = node
            break

    if not read_file_node:
        errors.append("❌ Read Template File node not found")
    else:
        print("✅ Read Template File node found")

        # Check CRITICAL V5 fix: dataPropertyName parameter
        options = read_file_node["parameters"].get("options", {})

        if "encoding" not in options:
            errors.append("❌ CRITICAL: encoding parameter missing in Read Template File")
        elif options["encoding"] != "utf8":
            errors.append(f"❌ CRITICAL: encoding should be 'utf8', found '{options['encoding']}'")
        else:
            print("✅ encoding: utf8 (V4.1 fix present)")

        if "dataPropertyName" not in options:
            errors.append("❌ CRITICAL: dataPropertyName parameter MISSING in Read Template File (V5 fix)")
        elif options["dataPropertyName"] != "data":
            errors.append(f"❌ CRITICAL: dataPropertyName should be 'data', found '{options['dataPropertyName']}'")
        else:
            print("✅ dataPropertyName: data (V5 CRITICAL FIX present) 🎉")

        # Check node notes
        if "V5" not in read_file_node.get("notes", ""):
            warnings.append("⚠️ Read Template File notes should mention V5 fix")
        else:
            print("✅ Read Template File notes mention V5")

    # Check connections
    if len(workflow["connections"]) != 6:
        errors.append(f"❌ Expected 6 connections, found {len(workflow['connections'])}")
    else:
        print(f"✅ Connections correct: 6")

    # Check tags
    v5_tag_found = False
    data_property_tag_found = False
    for tag in workflow["tags"]:
        if tag["name"] == "v5":
            v5_tag_found = True
        if tag["name"] == "data-property-fix":
            data_property_tag_found = True

    if not v5_tag_found:
        warnings.append("⚠️ 'v5' tag missing")
    else:
        print("✅ v5 tag present")

    if not data_property_tag_found:
        warnings.append("⚠️ 'data-property-fix' tag missing")
    else:
        print("✅ data-property-fix tag present")

    # Print results
    print("\n" + "="*60)
    if errors:
        print("\n❌ VALIDATION FAILED\n")
        for error in errors:
            print(error)
        return False

    if warnings:
        print("\n⚠️ VALIDATION PASSED WITH WARNINGS\n")
        for warning in warnings:
            print(warning)
    else:
        print("\n✅ VALIDATION PASSED - ALL CHECKS OK\n")

    print("="*60)
    return True


def save_workflow(workflow, output_path):
    """Save workflow to JSON file"""

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(workflow, f, indent=2, ensure_ascii=False)

        # Get file size
        import os
        size_bytes = os.path.getsize(output_path)
        size_kb = size_bytes / 1024

        print(f"\n✅ Workflow saved successfully!")
        print(f"📁 File: {output_path}")
        print(f"📊 Size: {size_kb:.1f} KB ({size_bytes:,} bytes)")
        print(f"🔢 Nodes: {len(workflow['nodes'])}")
        print(f"🔗 Connections: {len(workflow['connections'])}")

        return True

    except Exception as e:
        print(f"\n❌ Error saving workflow: {e}")
        return False


def main():
    """Main execution"""

    print("="*60)
    print("WF07 V5 Generator - Data Property Fix")
    print("="*60)
    print("\nRoot Cause: Missing dataPropertyName in Read File node")
    print("Solution: Add dataPropertyName: 'data' to options")
    print("\n" + "="*60)

    # Generate workflow
    print("\n🔨 Generating WF07 V5 workflow...")
    workflow = create_wf07_v5()
    print("✅ Workflow structure created")

    # Validate
    if not validate_workflow(workflow):
        print("\n❌ Validation failed. Aborting.")
        sys.exit(1)

    # Save
    output_path = "n8n/workflows/07_send_email_v5_data_property_fix.json"
    if not save_workflow(workflow, output_path):
        print("\n❌ Save failed. Aborting.")
        sys.exit(1)

    # Success summary
    print("\n" + "="*60)
    print("✅ WF07 V5 GENERATION COMPLETE")
    print("="*60)
    print("\n🎯 Key Changes from V4.1:")
    print("  1. ✅ Read Template File options: added dataPropertyName: 'data'")
    print("  2. ✅ Workflow name updated: V4.1 → V5")
    print("  3. ✅ Tags updated: v4.1 → v5, added data-property-fix")
    print("  4. ✅ Node notes updated: V5 complete fix documentation")

    print("\n📋 Next Steps:")
    print("  1. Import to n8n: http://localhost:5678")
    print("  2. Test Read File node output (check .data property)")
    print("  3. Test complete flow: WF02 → WF05 → WF07 V5")
    print("  4. Verify email sent with correct content")
    print("  5. Monitor for 'No output data returned' errors (should be 0)")

    print("\n🔍 Testing Command:")
    print(f"  jq '.nodes[] | select(.id == \"read-template-file\") | .parameters.options' {output_path}")
    print("\n  Expected output:")
    print("  {")
    print('    "encoding": "utf8",')
    print('    "dataPropertyName": "data"')
    print("  }")

    print("\n" + "="*60)
    print("🚀 V5 ready for testing and deployment!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
