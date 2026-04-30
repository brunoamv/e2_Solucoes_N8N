#!/usr/bin/env python3
"""
Generate WF07 V11 - Service Name Fix
====================================

Date: 2026-04-01
Previous: V10 (STARTTLS fix)
Issue: {{service_name}} not replaced in template (shows literal {{service_name}})
Root Cause: template_data has service_type but template expects service_name

Changes from V10:
-----------------
1. Add formatServiceName() function
2. Map service_type → service_name
   Examples:
   - energia_solar → Energia Solar
   - subestacao → Subestação
   - projetos_eletricos → Projetos Eletricos
   - bess → Bess
   - analise_rede → Analise Rede

3. Include service_name in templateData

Status:
-------
✅ email_logs table created (id, recipient_email, subject, template_used, status, sent_at, metadata)
✅ SMTP credential configured (port 465, SSL/TLS ON, password without spaces)
⏳ service_name mapping (THIS FIX)

Testing:
--------
Input: service_type: "energia_solar"
Expected: email shows "Energia Solar" instead of "{{service_name}}"
"""

import json
from datetime import datetime

# ===== WORKFLOW METADATA =====
workflow_name = "07 - Send Email V11 (Service Name Fix)"
workflow_id = "07_send_email_v11_service_name_fix"
version = "V11"
created_at = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

# ===== PREPARE EMAIL DATA NODE (FIXED) =====
prepare_email_data_code = """// Prepare Email Data - V11 (Service Name Fix)
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

// ===== SERVICE NAME FORMATTER (V11 FIX) =====
const formatServiceName = (serviceType) => {
    if (!serviceType) return 'Serviço';

    // Special cases
    const specialCases = {
        'bess': 'BESS',
        'energia_solar': 'Energia Solar',
        'subestacao': 'Subestação',
        'projetos_eletricos': 'Projetos Elétricos',
        'analise_rede': 'Análise de Rede'
    };

    if (specialCases[serviceType]) {
        return specialCases[serviceType];
    }

    // Default: capitalize each word
    return serviceType
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
};

// ===== DETECT INPUT SOURCE =====
const isFromWF05 = !!(input.appointment_id && input.calendar_success !== undefined);

console.log('📧 [Prepare Email Data V11] Input source:', {
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

    // V11 FIX: Format service name
    const serviceType = input.service_type || 'servico';
    const serviceName = formatServiceName(serviceType);

    console.log('🔧 [V11 Service Name Fix]:', {
        service_type: serviceType,
        service_name: serviceName
    });

    templateData = {
        name: input.lead_name || 'Cliente',
        email: emailRecipient,
        phone_number: input.phone_number || '',
        whatsapp_name: input.whatsapp_name || input.lead_name || 'Cliente',
        service_type: serviceType,
        service_name: serviceName,  // V11 FIX: Added formatted service name
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
    const serviceType = input.service_type || '';
    const serviceName = formatServiceName(serviceType);

    templateData = {
        name: input.name || 'Cliente',
        email: emailRecipient,
        phone_number: input.phone_number || input.phone || '',
        service_type: serviceType,
        service_name: serviceName,  // V11 FIX: Added formatted service name
        scheduled_date: input.scheduled_date || '',
        formatted_date: input.formatted_date || '',
        formatted_time: input.formatted_time || '',
        google_event_link: input.google_event_link || '',
        ...input
    };
}

console.log('✅ [Prepare Email Data V11] Data prepared:', {
    recipient: emailRecipient,
    template: emailTemplate,
    template_file: templateInfo.file,
    service_name: templateData.service_name  // V11: Log service name
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

# ===== RENDER TEMPLATE NODE (V10 - NO CHANGES) =====
render_template_code = """// Render Template - V11 (Same as V10 - Safe Property Check)
// GET TEMPLATE HTML FROM HTTP REQUEST NODE
let rawData = $('Fetch Template (HTTP)').first().json;

// ===== SAFE LOGGING (FIX for execution 18273) =====
const safeHasDataProperty = (typeof rawData === 'object' && rawData !== null && !Array.isArray(rawData))
    ? ('data' in rawData)
    : false;

console.log('🔍 [Render Template V11] Raw data inspection:', {
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

// Helper functions
const hasOnlyNumericKeys = (obj) => {
    if (!obj || typeof obj !== 'object' || Array.isArray(obj)) return false;
    const keys = Object.keys(obj);
    return keys.length > 0 && keys.every(k => /^\\d+$/.test(k));
};

const numericKeysToString = (obj) => {
    const keys = Object.keys(obj).sort((a, b) => parseInt(a) - parseInt(b));
    return keys.map(k => obj[k]).join('');
};

// FORMAT DETECTION
if (typeof rawData === 'string') {
    templateHtml = rawData;
    console.log('✅ [V11] Case 1: Direct string (length:', templateHtml.length, ')');

} else if (Array.isArray(rawData)) {
    templateHtml = rawData.join('');
    console.log('✅ [V11] Case 2: Direct array converted (length:', templateHtml.length, ')');

} else if (typeof rawData === 'object' && rawData !== null) {

    if (rawData.data && typeof rawData.data === 'string') {
        templateHtml = rawData.data;
        console.log('✅ [V11] Case 3: Object.data as string (length:', templateHtml.length, ')');

    } else if (rawData.data && Array.isArray(rawData.data)) {
        templateHtml = rawData.data.join('');
        console.log('✅ [V11] Case 4: Object.data as array converted (length:', templateHtml.length, ')');

    } else if (rawData.data && typeof rawData.data === 'object' && hasOnlyNumericKeys(rawData.data)) {
        templateHtml = numericKeysToString(rawData.data);
        console.log('✅ [V11] Case 5: Object.data with numeric keys converted (length:', templateHtml.length, ')');

    } else if (hasOnlyNumericKeys(rawData)) {
        templateHtml = numericKeysToString(rawData);
        console.log('✅ [V11] Case 6: Root object with numeric keys converted (length:', templateHtml.length, ')');

    } else {
        console.error('❌ [V11] Unknown object structure');
        throw new Error('Template HTML format not recognized');
    }

} else {
    console.error('❌ [V11] Completely unknown format');
    throw new Error('Template HTML is null, undefined, or unsupported type');
}

if (!templateHtml || templateHtml.length === 0) {
    throw new Error('Template HTML is empty after format conversion');
}

// GET EMAIL DATA
const emailData = $('Prepare Email Data').first().json;
const templateData = emailData.template_data;

console.log('🔧 [V11] Template data contains:', {
    service_name: templateData.service_name,
    service_type: templateData.service_type
});

// ===== RENDER TEMPLATE =====
const renderTemplate = (html, data) => {
    let rendered = html;

    // Replace {{variable}}
    rendered = rendered.replace(/\\{\\{\\s*(\\w+)\\s*\\}\\}/g, (match, key) => {
        const value = data[key] !== undefined ? data[key] : match;
        console.log(`📝 [V11] Replacing {{${key}}} with:`, value);
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

console.log('✅ [Render V11] Template rendered successfully');

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

# ===== BUILD WORKFLOW JSON =====
workflow = {
    "name": workflow_name,
    "nodes": [
        # 1. Execute Workflow Trigger
        {
            "parameters": {"options": {}},
            "id": "execute-workflow-trigger",
            "name": "Execute Workflow Trigger",
            "type": "n8n-nodes-base.executeWorkflowTrigger",
            "typeVersion": 1,
            "position": [250, 300],
            "notes": "V11: Trigger for WF05 integration"
        },

        # 2. Prepare Email Data (V11 FIX)
        {
            "parameters": {"jsCode": prepare_email_data_code},
            "id": "prepare-email-data",
            "name": "Prepare Email Data",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [450, 300],
            "notes": "V11 FIX: Added service_name formatting"
        },

        # 3. Fetch Template (HTTP) - NO CHANGES
        {
            "parameters": {
                "method": "GET",
                "url": "=http://e2bot-templates-dev/{{ $json.template_file }}",
                "options": {
                    "response": {
                        "response": {"responseFormat": "string"}
                    }
                }
            },
            "id": "fetch-template-http",
            "name": "Fetch Template (HTTP)",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4.2,
            "position": [650, 300],
            "notes": "V11: Fetch HTML template from nginx"
        },

        # 4. Render Template (V11 - Same as V10)
        {
            "parameters": {"jsCode": render_template_code},
            "id": "render-template",
            "name": "Render Template",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [850, 300],
            "notes": "V11: Safe property check + service_name rendering"
        },

        # 5. Send Email (SMTP) - NO CHANGES
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
            },
            "notes": "V11: SMTP with port 465 + SSL/TLS ON (password without spaces)"
        },

        # 6. Log Email Sent (V11 - email_logs table created)
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
            "notes": "V11: Log email to database (table created)"
        },

        # 7. Return Success - NO CHANGES
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
            "notes": "V11: Return success response"
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
        {"name": "wf05-integration", "createdAt": "2026-03-26T00:00:00.000000"},
        {"name": "v11", "createdAt": created_at},
        {"name": "service-name-fix", "createdAt": created_at}
    ],
    "triggerCount": 1,
    "updatedAt": created_at,
    "versionId": version
}

# ===== SAVE WORKFLOW =====
output_file = f"../n8n/workflows/{workflow_id}.json"

with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(workflow, f, indent=2, ensure_ascii=False)

print(f"✅ Workflow V11 generated: {output_file}")
print(f"📦 File size: {len(json.dumps(workflow))/ 1024:.1f} KB")
print(f"🔧 Nodes: {len(workflow['nodes'])}")
print(f"📝 Changes from V10:")
print(f"   - Added formatServiceName() function")
print(f"   - Added service_name field to templateData")
print(f"   - service_type: 'energia_solar' → service_name: 'Energia Solar'")
print(f"   - email_logs table support (created in this session)")
