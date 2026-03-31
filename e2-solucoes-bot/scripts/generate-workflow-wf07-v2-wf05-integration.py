#!/usr/bin/env python3
"""
Script: generate-workflow-wf07-v2-wf05-integration.py
Purpose: Refactor WF07 (Send Email) to integrate with WF05 V3.6 output
Base: 07_send_email.json
Date: 2026-03-26
Enhancement: WF05 data structure compatibility + proper field mapping
"""

import json
import sys
from pathlib import Path

# Define paths
BASE_DIR = Path(__file__).parent.parent
WORKFLOWS_DIR = BASE_DIR / "n8n" / "workflows"
INPUT_FILE = WORKFLOWS_DIR / "07_send_email.json"
OUTPUT_FILE = WORKFLOWS_DIR / "07_send_email_v2_wf05_integration.json"

# Validate input file exists
if not INPUT_FILE.exists():
    print(f"❌ ERROR: Input file not found: {INPUT_FILE}")
    sys.exit(1)

print(f"📂 Reading: {INPUT_FILE}")

# Load WF07 workflow
with open(INPUT_FILE, 'r', encoding='utf-8') as f:
    workflow = json.load(f)

print(f"✅ Loaded workflow: {workflow['name']}")
print(f"📊 Total nodes: {len(workflow['nodes'])}")

# ============================================
# STEP 1: Update workflow metadata
# ============================================
print("\n🔧 STEP 1: Updating workflow metadata...")

workflow['name'] = '07 - Send Email V2 (WF05 Integration)'
workflow['versionId'] = '2.0'
print(f"   ✅ Updated name: {workflow['name']}")

# Update tags
if 'tags' not in workflow:
    workflow['tags'] = []
workflow['tags'].append({
    'name': 'wf05-integration',
    'createdAt': '2026-03-26T00:00:00.000000'
})
workflow['tags'].append({
    'name': 'v2.0',
    'createdAt': '2026-03-26T00:00:00.000000'
})
print(f"   ✅ Added tags: wf05-integration, v2.0")

# ============================================
# STEP 2: Update "Prepare Email Data" node
# ============================================
print("\n🔧 STEP 2: Updating 'Prepare Email Data' node...")

# Find the node
prepare_email_data_node = None
for node in workflow['nodes']:
    if node.get('name') == 'Prepare Email Data':
        prepare_email_data_node = node
        break

if not prepare_email_data_node:
    print(f"   ❌ ERROR: 'Prepare Email Data' node not found")
    sys.exit(1)

# New JavaScript code with WF05 compatibility
new_js_code = """// Prepare Email Data - V2.0 (WF05 Integration)
const input = $input.first().json;

// ===== DETECT INPUT SOURCE =====
const isFromWF05 = !!(input.appointment_id && input.calendar_success !== undefined);

console.log('📧 [Prepare Email Data V2] Input source:', {
    isFromWF05,
    has_appointment_id: !!input.appointment_id,
    has_calendar_success: input.calendar_success !== undefined,
    has_template: !!input.template,
    has_to: !!input.to
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
    throw new Error('Email recipient not found in input data');
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
        throw new Error('Email template not specified');
    }
    console.log('📧 Using manual template:', emailTemplate);
}

// ===== PREPARE TEMPLATE DATA =====
let templateData;

if (isFromWF05) {
    // ===== WF05 DATA MAPPING =====
    // WF05 output from "Build Calendar Event Data" node:
    // - appointment_id (UUID)
    // - lead_name, lead_email, phone_number
    // - scheduled_date (ISO or YYYY-MM-DD), scheduled_time_start, scheduled_time_end
    // - service_type, city, address, state, zip_code
    // - google_calendar_event_id (from Update Appointment node)
    // - calendar_success (boolean from Update Appointment node)

    // Extract date part from scheduled_date (may be ISO string like "2026-04-25T00:00:00.000Z")
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

// ===== RETURN PREPARED DATA =====
return {
    to: emailRecipient,
    template: emailTemplate,
    template_data: templateData,
    source: isFromWF05 ? 'wf05_trigger' : 'manual_trigger',
    prepared_at: new Date().toISOString()
};"""

# Update node's JavaScript code
prepare_email_data_node['parameters']['jsCode'] = new_js_code
print(f"   ✅ Updated 'Prepare Email Data' node with WF05 compatibility logic")

# Update node notes
prepare_email_data_node['notes'] = "V2.0: WF05 integration with automatic source detection and data mapping"
print(f"   ✅ Updated node notes")

# ============================================
# STEP 3: Validation summary
# ============================================
print("\n📊 VALIDATION SUMMARY:")
print(f"   ✅ Workflow name: {workflow['name']}")
print(f"   ✅ Version: {workflow.get('versionId', 'N/A')}")
print(f"   ✅ Total nodes: {len(workflow['nodes'])}")
print(f"   ✅ Prepare Email Data updated: WF05 compatibility added")
print(f"   ✅ Backward compatibility: Manual triggers still supported")

# ============================================
# STEP 4: Key improvements documentation
# ============================================
print("\n🎯 KEY IMPROVEMENTS:")
print("   1. ✅ Automatic WF05 input detection (appointment_id + calendar_success)")
print("   2. ✅ Smart email recipient selection (lead_email from WF05 or 'to' from manual)")
print("   3. ✅ Template auto-selection (confirmacao_agendamento for WF05)")
print("   4. ✅ Date/time formatting (ISO → DD/MM/YYYY, HH:MM)")
print("   5. ✅ Google Calendar event link generation")
print("   6. ✅ Backward compatibility (manual triggers still work)")

# ============================================
# STEP 5: WF05 integration details
# ============================================
print("\n📋 WF05 INTEGRATION DETAILS:")
print("   Input from WF05 'Build Calendar Event Data' node:")
print("   - appointment_id (UUID)")
print("   - lead_name, lead_email, phone_number")
print("   - scheduled_date, scheduled_time_start, scheduled_time_end")
print("   - service_type, city, address, state")
print("   - google_calendar_event_id (from Update Appointment)")
print("   - calendar_success (boolean from Update Appointment)")
print("\n   Output to 'Read Template' node:")
print("   - to: lead_email")
print("   - template: 'confirmacao_agendamento'")
print("   - template_data: { name, email, formatted_date, formatted_time, google_event_link, ... }")

# ============================================
# STEP 6: Save workflow
# ============================================
print(f"\n💾 Saving workflow to: {OUTPUT_FILE}")

with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(workflow, f, indent=2, ensure_ascii=False)

print(f"✅ SUCCESS: WF07 V2.0 generated!")
print(f"\n📋 NEXT STEPS:")
print(f"   1. Import workflow: http://localhost:5678")
print(f"   2. File: {OUTPUT_FILE}")
print(f"   3. Test WF05 → WF07 integration:")
print(f"      - Services 1/3 + confirm appointment → WF05 triggers → WF07 sends email")
print(f"   4. Verify email template rendering with WF05 data")
print(f"   5. Check backward compatibility (manual triggers still work)")
print(f"\n🎯 CRITICAL SUCCESS FACTORS:")
print(f"   • Email recipient: lead_email from WF05")
print(f"   • Template: confirmacao_agendamento (auto-selected)")
print(f"   • Date format: DD/MM/YYYY (Brazilian format)")
print(f"   • Time format: HH:MM às HH:MM")
print(f"   • Google Calendar link: Generated from event_id")
