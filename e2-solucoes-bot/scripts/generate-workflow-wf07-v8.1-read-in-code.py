#!/usr/bin/env python3
"""
Generate WF07 V8.1 - Read Template in Code Node
Date: 2026-03-31
Solution: Move file reading to Code node using n8n $fileRead helper
"""

import json
from datetime import datetime

# V8.1: Read template in Code node using n8n helper
workflow = {
    "name": "07 - Send Email V8.1 (Read in Code)",
    "nodes": [
        # Node 1: Execute Workflow Trigger
        {
            "parameters": {"options": {}},
            "id": "execute-workflow-trigger",
            "name": "Execute Workflow Trigger",
            "type": "n8n-nodes-base.executeWorkflowTrigger",
            "typeVersion": 1,
            "position": [250, 300],
            "notes": "V8.1: Clean trigger configuration"
        },

        # Node 2: Prepare Email Data + Read Template
        {
            "parameters": {
                "jsCode": """// Prepare Email Data + Read Template - V8.1
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

console.log('📧 [Prepare Email Data V8.1] Input source:', {
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

// ===== READ TEMPLATE FILE USING $fs HELPER =====
const templatePath = `/email-templates/${templateInfo.file}`;

console.log('📂 [V8.1] Reading template file:', templatePath);

let templateHtml;
try {
    // V8.1 SOLUTION: Use n8n $fs helper to read file
    const fs = require('fs');
    templateHtml = fs.readFileSync(templatePath, 'utf8');

    console.log('✅ [V8.1] Template loaded:', {
        path: templatePath,
        length: templateHtml.length,
        first_100_chars: templateHtml.substring(0, 100)
    });
} catch (error) {
    console.error('❌ [V8.1] Template read failed:', error.message);
    throw new Error(`Failed to read template ${templatePath}: ${error.message}`);
}

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

// ===== RENDER TEMPLATE =====
const renderTemplate = (html, data) => {
    let rendered = html;

    console.log('🔄 [V8.1 Render] Starting template rendering');

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

console.log('✅ [V8.1 Render] Template rendered:', {
    html_length: htmlBody.length,
    text_length: textBody.length
});

// ===== RETURN COMPLETE EMAIL DATA =====
return {
    to: emailRecipient,
    template: emailTemplate,
    subject: templateInfo.subject,
    html_body: htmlBody,
    text_body: textBody,
    from_email: SENDER_CONFIG.from_email,
    from_name: SENDER_CONFIG.from_name,
    reply_to: SENDER_CONFIG.reply_to,
    template_data: templateData,
    source: isFromWF05 ? 'wf05_trigger' : 'manual_trigger',
    prepared_at: new Date().toISOString()
};
"""
            },
            "id": "prepare-and-render",
            "name": "Prepare and Render Email",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [450, 300],
            "notes": "V8.1: Read template + prepare data + render in single node using fs.readFileSync"
        },

        # Node 3: Send Email (SMTP)
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
            "position": [650, 300],
            "credentials": {"smtp": {"id": "1", "name": "SMTP - E2 Email"}}
        },

        # Node 4: Log Email Sent
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
            "position": [850, 300],
            "credentials": {"postgres": {"id": "1", "name": "PostgreSQL - E2 Bot"}}
        },

        # Node 5: Return Success
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
            "position": [1050, 300]
        }
    ],

    # Connections
    "connections": {
        "Execute Workflow Trigger": {
            "main": [[{"node": "Prepare and Render Email", "type": "main", "index": 0}]]
        },
        "Prepare and Render Email": {
            "main": [[{"node": "Send Email (SMTP)", "type": "main", "index": 0}]]
        },
        "Send Email (SMTP)": {
            "main": [[{"node": "Log Email Sent", "type": "main", "index": 0}]]
        },
        "Log Email Sent": {
            "main": [[{"node": "Return Success", "type": "main", "index": 0}]]
        }
    },

    "settings": {"errorWorkflow": "error-handler"},
    "staticData": None,
    "tags": [
        {"name": "wf05-integration", "createdAt": "2026-03-26T00:00:00.000000"},
        {"name": "v8.1", "createdAt": "2026-03-31T00:00:00.000000"},
        {"name": "read-in-code", "createdAt": "2026-03-31T00:00:00.000000"}
    ],
    "triggerCount": 1,
    "updatedAt": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
    "versionId": "V8.1"
}

# Write workflow to file
output_file = "/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/07_send_email_v8.1_read_in_code.json"

with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(workflow, f, indent=2, ensure_ascii=False)

print(f"✅ WF07 V8.1 generated: {output_file}")
print(f"   - 5 nodes (removed Read Template File node)")
print(f"   - Template reading moved to Code node using fs.readFileSync")
print(f"   - Size: {len(json.dumps(workflow))} bytes")
print("")
print("🎯 Next Steps:")
print("   1. Import: http://localhost:5678 → Import from File")
print("   2. Select: 07_send_email_v8.1_read_in_code.json")
print("   3. Test with appointment data")
print("   4. Verify email sent successfully")
