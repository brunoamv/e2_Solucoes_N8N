#!/usr/bin/env python3
"""
WF05 V7 - Hardcoded Values Solution Generator
Date: 2026-03-31
Fix: Use hardcoded business hours values directly in Code node
Root Cause: n8n blocks $env access EVERYWHERE (Code nodes AND Set node Expressions)
Solution: Hardcode values from docker/.env directly in workflow JSON
"""

import json
from datetime import datetime

def generate_wf05_v7():
    """Generate WF05 V7 with hardcoded business hours values"""

    # Read V4.0.4 as base (before any env var attempts)
    with open('n8n/workflows/05_appointment_scheduler_v4.0.4.json', 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    # Update metadata
    workflow['name'] = '05_appointment_scheduler_v7_hardcoded_values'
    workflow['versionId'] = 'V7'

    # Update tags
    workflow['tags'] = [
        {"name": "appointment", "createdAt": "2026-03-24T00:00:00.000000"},
        {"name": "google-calendar", "createdAt": "2026-03-24T00:00:00.000000"},
        {"name": "v7", "createdAt": "2026-03-31T00:00:00.000000"},
        {"name": "hardcoded-values", "createdAt": "2026-03-31T00:00:00.000000"},
        {"name": "definitive-fix", "createdAt": "2026-03-31T00:00:00.000000"}
    ]

    # Find "Validate Availability" node
    validate_node = None
    for node in workflow['nodes']:
        if node.get('name') == 'Validate Availability':
            validate_node = node
            break

    if not validate_node:
        raise Exception("Validate Availability node not found!")

    # V7 CODE: Hardcoded business hours from docker/.env
    validate_node['parameters']['jsCode'] = """// Validate Availability - V7 HARDCODED VALUES FIX
const data = $input.first().json;

try {
    // ===== VALIDATE INPUT DATA =====
    const scheduledDate = data.scheduled_date;
    const timeStartRaw = data.scheduled_time_start;
    const timeEndRaw = data.scheduled_time_end;

    if (!scheduledDate || !timeStartRaw || !timeEndRaw) {
        throw new Error('Dados de agendamento incompletos: ' + JSON.stringify({
            scheduledDate: !!scheduledDate,
            timeStart: !!timeStartRaw,
            timeEnd: !!timeEndRaw
        }));
    }

    // ===== NORMALIZE TIME VALUES =====
    // PostgreSQL TIME type may be object or string
    const timeStart = typeof timeStartRaw === 'string'
        ? timeStartRaw
        : timeStartRaw?.toString() || '';

    const timeEnd = typeof timeEndRaw === 'string'
        ? timeEndRaw
        : timeEndRaw?.toString() || '';

    console.log('⏰ [Validate Availability V7] Times:', { timeStart, timeEnd });

    // ===== V7 FIX: HARDCODED BUSINESS HOURS =====
    // REASON: n8n blocks $env access EVERYWHERE (Code nodes AND Set Expressions)
    // SOLUTION: Hardcode values from docker/.env directly here
    // SOURCE: docker/.env lines with CALENDAR_WORK_*

    const WORK_START = '08:00';  // From CALENDAR_WORK_START
    const WORK_END = '18:00';    // From CALENDAR_WORK_END
    const WORK_DAYS = [1, 2, 3, 4, 5];  // From CALENDAR_WORK_DAYS (Segunda-Sexta)

    console.log('✅ [Validate Availability V7] Business hours (hardcoded):', {
        workStart: WORK_START,
        workEnd: WORK_END,
        workDays: WORK_DAYS
    });

    // ===== CHECK BUSINESS HOURS =====
    const startHour = parseInt(timeStart.split(':')[0]);
    const endHour = parseInt(timeEnd.split(':')[0]);

    const workStartHour = parseInt(WORK_START.split(':')[0]);
    const workEndHour = parseInt(WORK_END.split(':')[0]);

    if (startHour < workStartHour || endHour > workEndHour) {
        throw new Error(`Horário fora do expediente: ${timeStart}-${timeEnd} (expediente: ${WORK_START}-${WORK_END})`);
    }

    // ===== CHECK WEEKEND =====
    const dateObj = scheduledDate instanceof Date
        ? scheduledDate
        : new Date(scheduledDate);

    const dayOfWeek = dateObj.getDay();

    if (!WORK_DAYS.includes(dayOfWeek)) {
        throw new Error(`Dia não útil: ${scheduledDate} (dia da semana: ${dayOfWeek})`);
    }

    console.log('✅ [Validate Availability V7] Approved:', scheduledDate, timeStart);

    return {
        ...data,
        validation_status: 'approved',
        validated_at: new Date().toISOString()
    };

} catch (error) {
    console.error('❌ [Validate Availability V7] Error:', error.message);
    console.error('Data received:', JSON.stringify(data, null, 2));
    throw error;
}"""

    validate_node['notes'] = '''V7 FIX: Hardcoded business hours (08:00-18:00, Mon-Fri)
Source: docker/.env CALENDAR_WORK_* variables
Reason: n8n blocks $env access everywhere (Code + Set Expressions)
To change hours: Edit this Code node directly or regenerate workflow'''

    # Save V7 workflow
    output_path = 'n8n/workflows/05_appointment_scheduler_v7_hardcoded_values.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print(f"✅ WF05 V7 generated: {output_path}")
    print(f"📊 Nodes: {len(workflow['nodes'])}")
    print(f"🔗 Connections: {len(workflow['connections'])}")
    print(f"✨ Key Change: Hardcoded business hours directly in Code node")
    print(f"✨ Values: 08:00-18:00, Monday-Friday (1,2,3,4,5)")
    print(f"⚠️  NOTE: To change hours, edit Code node or regenerate workflow")

    # Validate JSON
    with open(output_path, 'r', encoding='utf-8') as f:
        json.load(f)
    print("✅ JSON validation: OK")

if __name__ == '__main__':
    generate_wf05_v7()
