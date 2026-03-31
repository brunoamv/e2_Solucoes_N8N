#!/usr/bin/env python3
"""
Generate WF07 V3 - Complete Email Workflow Fix
==============================================

CHANGES FROM V2.0:
1. FIX TEMPLATE FILE MAPPING: Add template → filename mapping
2. FIX EMAIL METADATA: Add subject, from_email, from_name, reply_to
3. FIX MISSING FIELDS: Ensure all required fields for downstream nodes
4. SIMPLIFY TRIGGER: Clean Execute Workflow Trigger configuration

PROBLEMS SOLVED (V2.0 Issues):
- "Prepare Email Data" error: Email recipient not found [line 29]
- Missing template_file field for "Read Template File" node
- Missing subject, from_email, from_name, reply_to fields
- Execute Workflow Trigger configuration error

ROOT CAUSE:
- V2.0 "Prepare Email Data" incomplete output (missing 6 critical fields)
- Template name → filename mapping not implemented
- Email sender metadata not configured

Date: 2026-03-30
"""

import json
import sys
from pathlib import Path

# Configuration
BASE_V2_0 = Path(__file__).parent.parent / "n8n" / "workflows" / "07_send_email_v2_wf05_integration.json"
OUTPUT_V3 = Path(__file__).parent.parent / "n8n" / "workflows" / "07_send_email_v3_complete_fix.json"

# Template configuration (template name → filename + subject)
TEMPLATE_CONFIG = {
    'confirmacao_agendamento': {
        'file': 'confirmacao_agendamento.html',
        'subject': 'Agendamento Confirmado - E2 Soluções'
    },
    'lembrete_2h': {
        'file': 'lembrete_2h.html',
        'subject': 'Lembrete: Sua visita é em 2 horas - E2 Soluções'
    },
    'novo_lead': {
        'file': 'novo_lead.html',
        'subject': 'Obrigado pelo contato - E2 Soluções'
    },
    'apos_visita': {
        'file': 'apos_visita.html',
        'subject': 'Obrigado pela visita - E2 Soluções'
    }
}

# Email sender configuration
EMAIL_SENDER_CONFIG = {
    'from_email': 'contato@e2solucoes.com.br',
    'from_name': 'E2 Soluções',
    'reply_to': 'contato@e2solucoes.com.br'
}

def generate_prepare_email_data_code():
    """Generate complete JavaScript code for Prepare Email Data node."""

    template_map_js = json.dumps(TEMPLATE_CONFIG, indent=4)
    sender_config_js = json.dumps(EMAIL_SENDER_CONFIG, indent=4)

    return f'''// Prepare Email Data - V3.0 (Complete Fix)
const input = $input.first().json;

// ===== TEMPLATE CONFIGURATION =====
const TEMPLATE_CONFIG = {template_map_js};

// ===== EMAIL SENDER CONFIGURATION =====
const SENDER_CONFIG = {sender_config_js};

// ===== DETECT INPUT SOURCE =====
const isFromWF05 = !!(input.appointment_id && input.calendar_success !== undefined);

console.log('📧 [Prepare Email Data V3] Input source:', {{
    isFromWF05,
    has_appointment_id: !!input.appointment_id,
    has_calendar_success: input.calendar_success !== undefined,
    has_template: !!input.template,
    has_to: !!input.to,
    has_lead_email: !!input.lead_email
}});

// ===== DETERMINE EMAIL RECIPIENT =====
let emailRecipient;

if (isFromWF05) {{
    // WF05 input: use lead_email
    emailRecipient = input.lead_email;
    console.log('📧 Using lead_email from WF05:', emailRecipient);
}} else {{
    // Manual trigger: use 'to' or 'email' field
    emailRecipient = input.to || input.email;
    console.log('📧 Using manual trigger recipient:', emailRecipient);
}}

if (!emailRecipient) {{
    throw new Error('Email recipient not found in input data. WF05 needs lead_email, manual trigger needs to/email field.');
}}

// ===== DETERMINE TEMPLATE =====
let emailTemplate;

if (isFromWF05) {{
    // WF05 input: always use confirmacao_agendamento template
    emailTemplate = 'confirmacao_agendamento';
    console.log('📧 Using WF05 template: confirmacao_agendamento');
}} else {{
    // Manual trigger: use specified template
    emailTemplate = input.template || input.email_template;
    if (!emailTemplate) {{
        throw new Error('Email template not specified. Provide template field.');
    }}
    console.log('📧 Using manual template:', emailTemplate);
}}

// ===== VALIDATE TEMPLATE EXISTS =====
if (!TEMPLATE_CONFIG[emailTemplate]) {{
    throw new Error(`Unknown email template: ${{emailTemplate}}. Available: ${{Object.keys(TEMPLATE_CONFIG).join(', ')}}`);
}}

const templateInfo = TEMPLATE_CONFIG[emailTemplate];

// ===== PREPARE TEMPLATE DATA =====
let templateData;

if (isFromWF05) {{
    // ===== WF05 DATA MAPPING =====

    // Extract date part from scheduled_date
    let dateString = input.scheduled_date;
    if (typeof dateString === 'string' && dateString.includes('T')) {{
        dateString = dateString.split('T')[0]; // \"2026-04-25\"
    }}

    // Format date to Brazilian format (DD/MM/YYYY)
    const [year, month, day] = dateString.split('-');
    const formattedDate = `${{day}}/${{month}}/${{year}}`;

    // Extract time parts (remove seconds if present)
    const timeStart = input.scheduled_time_start?.split(':').slice(0, 2).join(':') || '00:00';
    const timeEnd = input.scheduled_time_end?.split(':').slice(0, 2).join(':') || '00:00';
    const formattedTime = `${{timeStart}} às ${{timeEnd}}`;

    // Generate Google Calendar event link
    const googleEventLink = input.google_calendar_event_id
        ? `https://calendar.google.com/calendar/event?eid=${{input.google_calendar_event_id}}`
        : '';

    templateData = {{
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
    }};

    console.log('✅ [WF05 Data Mapping] Template data prepared:', {{
        name: templateData.name,
        email: templateData.email,
        service: templateData.service_type,
        date: templateData.formatted_date,
        time: templateData.formatted_time,
        has_google_link: !!templateData.google_event_link
    }});

}} else {{
    // ===== MANUAL TRIGGER DATA MAPPING (BACKWARD COMPATIBILITY) =====
    templateData = {{
        name: input.name || 'Cliente',
        email: emailRecipient,
        phone_number: input.phone_number || input.phone || '',
        service_type: input.service_type || '',
        scheduled_date: input.scheduled_date || '',
        formatted_date: input.formatted_date || '',
        formatted_time: input.formatted_time || '',
        google_event_link: input.google_event_link || '',
        ...input // Spread all input for backward compatibility
    }};

    console.log('✅ [Manual Trigger] Template data prepared (backward compatible)');
}}

// ===== RETURN COMPLETE EMAIL DATA =====
return {{
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
}};'''

def generate_v3():
    """Generate V3 workflow with complete fixes."""

    print("=" * 70)
    print("GENERATE WF07 V3 - COMPLETE EMAIL WORKFLOW FIX")
    print("=" * 70)

    # Load V2.0
    print(f"\n✅ Loading base V2.0 from: {BASE_V2_0}")
    with open(BASE_V2_0, "r", encoding="utf-8") as f:
        workflow = json.load(f)

    # Update workflow metadata
    workflow["name"] = "07 - Send Email V3 (Complete Fix)"

    # Update version tag
    if "tags" in workflow:
        for tag in workflow["tags"]:
            if "name" in tag and tag["name"] == "v2.0":
                tag["name"] = "v3.0"

    # Update nodes
    prepare_email_updated = False
    trigger_updated = False

    for node in workflow["nodes"]:
        # Fix 1: Update Prepare Email Data node with complete logic
        if node.get("name") == "Prepare Email Data":
            print(f"\n📝 Updating Prepare Email Data node")

            # Replace JavaScript code with complete version
            node["parameters"]["jsCode"] = generate_prepare_email_data_code()
            node["notes"] = "V3.0: Complete email data preparation with template mapping, subject, and sender info"

            prepare_email_updated = True
            print("   ✅ Updated Prepare Email Data:")
            print("      - Added template → filename mapping (template_file)")
            print("      - Added email subject from template config")
            print("      - Added sender info (from_email, from_name, reply_to)")
            print("      - Improved error messages with hints")

        # Fix 2: Simplify Execute Workflow Trigger (clean configuration)
        if node.get("name") == "Execute Workflow Trigger":
            print(f"\n📝 Updating Execute Workflow Trigger node")

            # Ensure clean configuration
            node["parameters"] = {"options": {}}
            node["notes"] = "V3.0: Clean trigger configuration"

            trigger_updated = True
            print("   ✅ Updated Execute Workflow Trigger:")
            print("      - Cleaned configuration (no leftover settings)")

    if not prepare_email_updated:
        print("❌ ERROR: Prepare Email Data node not found!")
        sys.exit(1)

    if not trigger_updated:
        print("❌ ERROR: Execute Workflow Trigger node not found!")
        sys.exit(1)

    # Save V3
    print(f"\n💾 Saving V3 to: {OUTPUT_V3}")
    with open(OUTPUT_V3, "w", encoding="utf-8") as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 70)
    print("✅ V3 WORKFLOW GENERATED SUCCESSFULLY!")
    print("=" * 70)
    print(f"\n📁 Output: {{OUTPUT_V3}}")

    print("\n🎯 V3 Complete Fixes:")
    print("   1. ✅ TEMPLATE FILE MAPPING: template_file field created")
    print("   2. ✅ EMAIL SUBJECT: Subject from template configuration")
    print("   3. ✅ SENDER INFO: from_email, from_name, reply_to added")
    print("   4. ✅ ERROR MESSAGES: Improved with helpful hints")
    print("   5. ✅ TRIGGER CONFIG: Cleaned Execute Workflow Trigger")

    print("\n📊 V2.0 → V3 Changes:")
    print("   BEFORE (V2.0 - Incomplete):")
    print("      return {{")
    print("         to: emailRecipient,")
    print("         template: emailTemplate,")
    print("         template_data: templateData")
    print("      }};")
    print("      // ❌ Missing: template_file, subject, from_email, from_name, reply_to")

    print("\n   AFTER (V3 - Complete):")
    print("      return {{")
    print("         to: emailRecipient,")
    print("         template: emailTemplate,")
    print("         template_file: templateInfo.file,      // ✅ NEW")
    print("         subject: templateInfo.subject,          // ✅ NEW")
    print("         template_data: templateData,")
    print("         from_email: SENDER_CONFIG.from_email,   // ✅ NEW")
    print("         from_name: SENDER_CONFIG.from_name,     // ✅ NEW")
    print("         reply_to: SENDER_CONFIG.reply_to        // ✅ NEW")
    print("      }};")

    print("\n📝 Next Steps:")
    print("   1. Import 07_send_email_v3_complete_fix.json to n8n")
    print("   2. Test WF05 V4.0.3 → WF07 V3 integration:")
    print("      - Create appointment (Service 1/3 + confirm)")
    print("      - Verify email sent to lead_email")
    print("      - Check email content (date, time, Google Calendar link)")
    print("   3. Test manual trigger (backward compatibility):")
    print("      - Execute WF07 manually with test data")
    print("      - Verify template rendering and sending")
    print("   4. Monitor email_logs table:")
    print("      SELECT * FROM email_logs ORDER BY sent_at DESC LIMIT 5;")
    print("   5. Deploy to production after validation")

    print("\n⚠️  Template Files Required:")
    print("   Ensure these files exist in email-templates/:")
    for template_name, config in TEMPLATE_CONFIG.items():
        print(f"      - {config['file']} (for template: {template_name})")

    print("\n📧 Email Sender Configuration:")
    for key, value in EMAIL_SENDER_CONFIG.items():
        print(f"      - {key}: {value}")

    return 0

if __name__ == "__main__":
    sys.exit(generate_v3())
