#!/usr/bin/env python3
"""
WF07 V10 - STARTTLS SMTP Fix
Fixes execution 18445: SSL routines wrong version number
Changes from V9.3: Added connectionSecurity: STARTTLS in SMTP options
"""

import json
from datetime import datetime

def generate_wf07_v10():
    """Generate WF07 V10 with STARTTLS SMTP configuration"""

    workflow = {
        "name": "07 - Send Email V10 (STARTTLS)",
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
                "notes": "V10: Trigger for WF05 integration"
            },

            # Node 2: Prepare Email Data
            {
                "parameters": {
                    "jsCode": """// Prepare Email Data - V10
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
    "lembrete_24h": {
        "file": "lembrete_24h.html",
        "subject": "Lembrete: Sua visita é amanhã - E2 Soluções"
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

console.log('📧 [Prepare Email Data V10] Input source:', {
    isFromWF05,
    has_appointment_id: !!input.appointment_id,
    has_calendar_success: input.calendar_success !== undefined
});

// ===== DETERMINE EMAIL RECIPIENT =====
let emailRecipient;

if (isFromWF05) {
    emailRecipient = input.lead_email;
    console.log('📧 Using lead_email from WF05:', emailRecipient);
} else {
    emailRecipient = input.to || input.email;
    console.log('📧 Using manual trigger recipient:', emailRecipient);
}

if (!emailRecipient) {
    throw new Error('Email recipient not found');
}

// ===== DETERMINE TEMPLATE =====
let emailTemplate;

if (isFromWF05) {
    emailTemplate = 'confirmacao_agendamento';
    console.log('📧 Using WF05 template: confirmacao_agendamento');
} else {
    emailTemplate = input.template || input.email_template;
    if (!emailTemplate) {
        throw new Error('Email template not specified');
    }
    console.log('📧 Using manual template:', emailTemplate);
}

// ===== VALIDATE TEMPLATE EXISTS =====
if (!TEMPLATE_CONFIG[emailTemplate]) {
    throw new Error(`Unknown email template: ${emailTemplate}`);
}

const templateInfo = TEMPLATE_CONFIG[emailTemplate];

// ===== PREPARE TEMPLATE DATA =====
let templateData;

if (isFromWF05) {
    // WF05 DATA MAPPING
    let dateString = input.scheduled_date;
    if (typeof dateString === 'string' && dateString.includes('T')) {
        dateString = dateString.split('T')[0];
    }

    const [year, month, day] = dateString.split('-');
    const formattedDate = `${day}/${month}/${year}`;

    const timeStart = input.scheduled_time_start?.split(':').slice(0, 2).join(':') || '00:00';
    const timeEnd = input.scheduled_time_end?.split(':').slice(0, 2).join(':') || '00:00';
    const formattedTime = `${timeStart} às ${timeEnd}`;

    const googleEventLink = input.google_calendar_event_id
        ? `https://calendar.google.com/calendar/event?eid=${input.google_calendar_event_id}`
        : '';

    templateData = {
        name: input.lead_name || 'Cliente',
        email: emailRecipient,
        phone_number: input.phone_number || '',
        whatsapp_name: input.whatsapp_name || input.lead_name || 'Cliente',
        service_type: input.service_type || 'Serviço',
        city: input.city || '',
        address: input.address || '',
        state: input.state || '',
        zip_code: input.zip_code || '',
        scheduled_date: dateString,
        formatted_date: formattedDate,
        formatted_time: formattedTime,
        google_event_link: googleEventLink,
        google_calendar_event_id: input.google_calendar_event_id || '',
        appointment_id: input.appointment_id,
        status: input.status || 'confirmado'
    };
} else {
    // MANUAL TRIGGER DATA MAPPING
    templateData = {
        name: input.name || 'Cliente',
        email: emailRecipient,
        phone_number: input.phone_number || input.phone || '',
        service_type: input.service_type || '',
        scheduled_date: input.scheduled_date || '',
        formatted_date: input.formatted_date || '',
        formatted_time: input.formatted_time || '',
        google_event_link: input.google_event_link || '',
        ...input
    };
}

console.log('✅ [Prepare Email Data V10] Data prepared:', {
    recipient: emailRecipient,
    template: emailTemplate,
    template_file: templateInfo.file
});

// ===== RETURN DATA FOR HTTP REQUEST NODE =====
return {
    to: emailRecipient,
    template: emailTemplate,
    template_file: templateInfo.file,
    subject: templateInfo.subject,
    template_data: templateData,
    from_email: SENDER_CONFIG.from_email,
    from_name: SENDER_CONFIG.from_name,
    reply_to: SENDER_CONFIG.reply_to,
    source: isFromWF05 ? 'wf05_trigger' : 'manual_trigger',
    prepared_at: new Date().toISOString()
};
"""
                },
                "id": "prepare-email-data",
                "name": "Prepare Email Data",
                "type": "n8n-nodes-base.code",
                "typeVersion": 2,
                "position": [450, 300],
                "notes": "V10: Prepare data and determine template"
            },

            # Node 3: Fetch Template (HTTP)
            {
                "parameters": {
                    "method": "GET",
                    "url": "=http://e2bot-templates-dev/{{ $json.template_file }}",
                    "options": {
                        "response": {
                            "response": {
                                "responseFormat": "string"
                            }
                        }
                    }
                },
                "id": "fetch-template-http",
                "name": "Fetch Template (HTTP)",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.2,
                "position": [650, 300],
                "notes": "V10: Fetch HTML template from nginx"
            },

            # Node 4: Render Template
            {
                "parameters": {
                    "jsCode": """// Render Template - V10 (Safe Property Check)
// GET TEMPLATE HTML FROM HTTP REQUEST NODE
let rawData = $('Fetch Template (HTTP)').first().json;

// ===== SAFE LOGGING (FIX for execution 18273) =====
// Use typeof check BEFORE 'in' operator to avoid array error
const safeHasDataProperty = (typeof rawData === 'object' && rawData !== null && !Array.isArray(rawData))
    ? ('data' in rawData)
    : false;

console.log('🔍 [Render Template V10] Raw data inspection:', {
    type: typeof rawData,
    is_array: Array.isArray(rawData),
    has_data_property: safeHasDataProperty,
    data_type: rawData?.data ? typeof rawData.data : 'N/A',
    data_is_array: rawData?.data ? Array.isArray(rawData.data) : false,
    first_5_keys: Array.isArray(rawData) ? 'array' : (rawData && typeof rawData === 'object' ? Object.keys(rawData).slice(0, 5) : 'N/A'),
    sample_structure: JSON.stringify(rawData).substring(0, 200)
});

// ===== ROBUST FORMAT DETECTION AND CONVERSION =====
let templateHtml = '';

// Helper function to check if object has only numeric string keys
const hasOnlyNumericKeys = (obj) => {
    if (!obj || typeof obj !== 'object' || Array.isArray(obj)) return false;
    const keys = Object.keys(obj);
    return keys.length > 0 && keys.every(k => /^\\d+$/.test(k));
};

// Helper function to convert object with numeric keys to string
const numericKeysToString = (obj) => {
    const keys = Object.keys(obj).sort((a, b) => parseInt(a) - parseInt(b));
    return keys.map(k => obj[k]).join('');
};

// FORMAT DETECTION LOGIC (Comprehensive + Safe)
if (typeof rawData === 'string') {
    // Case 1: Direct string response
    templateHtml = rawData;
    console.log('✅ [V10] Case 1: Direct string (length:', templateHtml.length, ')');

} else if (Array.isArray(rawData)) {
    // Case 2: Direct array response (FIXED - detected BEFORE property check)
    templateHtml = rawData.join('');
    console.log('✅ [V10] Case 2: Direct array converted (length:', templateHtml.length, ')');

} else if (typeof rawData === 'object' && rawData !== null) {

    // Case 3: Object with 'data' property (string)
    if (rawData.data && typeof rawData.data === 'string') {
        templateHtml = rawData.data;
        console.log('✅ [V10] Case 3: Object.data as string (length:', templateHtml.length, ')');

    // Case 4: Object with 'data' property (array)
    } else if (rawData.data && Array.isArray(rawData.data)) {
        templateHtml = rawData.data.join('');
        console.log('✅ [V10] Case 4: Object.data as array converted (length:', templateHtml.length, ')');

    // Case 5: Object with 'data' property (object with numeric keys)
    } else if (rawData.data && typeof rawData.data === 'object' && hasOnlyNumericKeys(rawData.data)) {
        templateHtml = numericKeysToString(rawData.data);
        console.log('✅ [V10] Case 5: Object.data with numeric keys converted (length:', templateHtml.length, ')');

    // Case 6: Object with numeric keys directly (no 'data' wrapper)
    } else if (hasOnlyNumericKeys(rawData)) {
        templateHtml = numericKeysToString(rawData);
        console.log('✅ [V10] Case 6: Root object with numeric keys converted (length:', templateHtml.length, ')');

    // Case 7: Unknown object structure
    } else {
        console.error('❌ [V10] Unknown object structure:', {
            has_data: !!rawData.data,
            data_type: typeof rawData.data,
            keys_sample: Object.keys(rawData).slice(0, 10),
            data_keys_sample: rawData.data ? Object.keys(rawData.data).slice(0, 10) : null
        });
        throw new Error('Template HTML format not recognized - see logs for details');
    }

} else {
    // Case 8: Completely unknown format
    console.error('❌ [V10] Completely unknown format:', typeof rawData);
    throw new Error('Template HTML is null, undefined, or unsupported type');
}

// VALIDATION
if (!templateHtml || templateHtml.length === 0) {
    throw new Error('Template HTML is empty after format conversion');
}

console.log('📝 [V10] Template conversion successful:', {
    final_length: templateHtml.length,
    starts_with: templateHtml.substring(0, 30),
    is_html: templateHtml.trim().toLowerCase().startsWith('<!doctype') || templateHtml.trim().toLowerCase().startsWith('<html')
});

// GET EMAIL DATA FROM PREPARE EMAIL DATA NODE
const emailData = $('Prepare Email Data').first().json;
const templateData = emailData.template_data;

// ===== RENDER TEMPLATE =====
const renderTemplate = (html, data) => {
    let rendered = html;

    console.log('🔄 [Render V10] Starting template rendering');

    // Replace {{variable}}
    rendered = rendered.replace(/\\{\\{\\s*(\\w+)\\s*\\}\\}/g, (match, key) => {
        const value = data[key] !== undefined ? data[key] : match;
        return value;
    });

    // Handle {{#if variable}}...{{/if}}
    rendered = rendered.replace(/\\{\\{#if\\s+(\\w+)\\}\\}([\\s\\S]*?)\\{\\{\\/if\\}\\}/g, (match, key, content) => {
        return data[key] ? content : '';
    });

    // Handle {{#unless variable}}...{{/unless}}
    rendered = rendered.replace(/\\{\\{#unless\\s+(\\w+)\\}\\}([\\s\\S]*?)\\{\\{\\/unless\\}\\}/g, (match, key, content) => {
        return !data[key] ? content : '';
    });

    return rendered;
};

const htmlBody = renderTemplate(templateHtml, templateData);

// Generate plain text version
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

console.log('✅ [Render V10] Template rendered successfully:', {
    html_length: htmlBody.length,
    text_length: textBody.length
});

// ===== RETURN COMPLETE EMAIL DATA =====
return {
    to: emailData.to,
    template: emailData.template,
    subject: emailData.subject,
    html_body: htmlBody,
    text_body: textBody,
    from_email: emailData.from_email,
    from_name: emailData.from_name,
    reply_to: emailData.reply_to,
    template_data: templateData,
    source: emailData.source,
    rendered_at: new Date().toISOString()
};
"""
                },
                "id": "render-template",
                "name": "Render Template",
                "type": "n8n-nodes-base.code",
                "typeVersion": 2,
                "position": [850, 300],
                "notes": "V10: Safe property check + template rendering"
            },

            # Node 5: Send Email (SMTP) - V10 FIX
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
                        "allowUnauthorizedCerts": False,
                        "connectionSecurity": "STARTTLS"  # V10 FIX: Added STARTTLS for Gmail
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
                },
                "notes": "V10 FIX: Added connectionSecurity STARTTLS (fixes exec 18445)"
            },

            # Node 6: Log Email Sent
            {
                "parameters": {
                    "operation": "executeQuery",
                    "query": "INSERT INTO email_logs (recipient_email, recipient_name, subject, template_used, status, sent_at, metadata) VALUES ($1, $2, $3, $4, $5, NOW(), $6)",
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
                },
                "notes": "V10: Log email to database"
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
                "position": [1450, 300],
                "notes": "V10: Return success response"
            }
        ],

        "connections": {
            "Execute Workflow Trigger": {
                "main": [[{"node": "Prepare Email Data", "type": "main", "index": 0}]]
            },
            "Prepare Email Data": {
                "main": [[{"node": "Fetch Template (HTTP)", "type": "main", "index": 0}]]
            },
            "Fetch Template (HTTP)": {
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
            {
                "name": "wf05-integration",
                "createdAt": "2026-03-26T00:00:00.000000"
            },
            {
                "name": "v10",
                "createdAt": "2026-04-01T00:00:00.000000"
            },
            {
                "name": "starttls-fix",
                "createdAt": "2026-04-01T00:00:00.000000"
            }
        ],

        "triggerCount": 1,
        "updatedAt": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "versionId": "V10"
    }

    return workflow

def main():
    print("🔧 Generating WF07 V10 - STARTTLS SMTP Fix...")

    workflow = generate_wf07_v10()

    output_path = "n8n/workflows/07_send_email_v10_starttls.json"

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print(f"✅ WF07 V10 generated successfully: {output_path}")
    print("\nV10 Changes:")
    print("  - Added connectionSecurity: STARTTLS in SMTP node options")
    print("  - Fixes execution 18445: SSL routines wrong version number")
    print("  - Gmail SMTP compatibility (port 587 + STARTTLS)")
    print("\nNext Steps:")
    print("  1. Import workflow: http://localhost:5678")
    print("  2. Verify SMTP credentials configuration")
    print("  3. Test with same data from execution 18445")
    print("  4. Monitor logs for successful email send")

if __name__ == "__main__":
    main()
