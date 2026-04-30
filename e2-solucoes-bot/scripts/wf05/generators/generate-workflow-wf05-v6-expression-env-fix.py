#!/usr/bin/env python3
"""
WF05 V6 - Expression Environment Variable Fix Generator
Date: 2026-03-31
Fix: Use n8n Set node with Expressions to load env vars into workflow data BEFORE Code node
Root Cause: Code nodes cannot access $env or process.env directly
Solution: Set node with {{ $env.VARIABLE }} expressions loads vars into workflow data
"""

import json
from datetime import datetime

def generate_wf05_v6():
    """Generate WF05 V6 with Set node loading env vars via Expressions"""

    # Read V4.0.4 as base
    with open('n8n/workflows/05_appointment_scheduler_v4.0.4.json', 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    # Update metadata
    workflow['name'] = '05_appointment_scheduler_v6_expression_env_fix'
    workflow['versionId'] = 'V6'

    # Update tags
    workflow['tags'] = [
        {"name": "appointment", "createdAt": "2026-03-24T00:00:00.000000"},
        {"name": "google-calendar", "createdAt": "2026-03-24T00:00:00.000000"},
        {"name": "v6", "createdAt": "2026-03-31T00:00:00.000000"},
        {"name": "expression-env-fix", "createdAt": "2026-03-31T00:00:00.000000"},
        {"name": "set-node-solution", "createdAt": "2026-03-31T00:00:00.000000"}
    ]

    # Find nodes we need to modify
    validate_node = None
    validate_node_index = None

    for i, node in enumerate(workflow['nodes']):
        if node.get('name') == 'Validate Availability':
            validate_node = node
            validate_node_index = i
            break

    if not validate_node:
        raise Exception("Validate Availability node not found!")

    # Create new "Load Env Vars" Set node BEFORE Validate Availability
    load_env_node = {
        "parameters": {
            "mode": "manual",
            "duplicateItem": False,
            "assignments": {
                "assignments": [
                    {
                        "id": "env_work_start",
                        "name": "env_work_start",
                        "value": "={{ $env.CALENDAR_WORK_START }}",
                        "type": "string"
                    },
                    {
                        "id": "env_work_end",
                        "name": "env_work_end",
                        "value": "={{ $env.CALENDAR_WORK_END }}",
                        "type": "string"
                    },
                    {
                        "id": "env_work_days",
                        "name": "env_work_days",
                        "value": "={{ $env.CALENDAR_WORK_DAYS }}",
                        "type": "string"
                    }
                ]
            },
            "options": {}
        },
        "name": "Load Env Vars",
        "type": "n8n-nodes-base.set",
        "typeVersion": 3.4,
        "position": [
            validate_node['position'][0] - 200,
            validate_node['position'][1]
        ],
        "notes": "V6 FIX: Load env vars using Expressions (={{ $env.VAR }}) into workflow data"
    }

    # Update Validate Availability Code node to use workflow data instead of $env
    validate_node['parameters']['jsCode'] = """// Validate Availability - V6 EXPRESSION FIX
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

    console.log('⏰ [Validate Availability V6] Times:', { timeStart, timeEnd });

    // ===== V6 FIX: READ ENV VARS FROM WORKFLOW DATA =====
    // REASON: Code nodes cannot access $env or process.env directly
    // SOLUTION: "Load Env Vars" Set node loaded them via Expressions (={{ $env.VAR }})

    const workStart = data.env_work_start;
    const workEnd = data.env_work_end;
    const workDays = data.env_work_days;

    if (!workStart || !workEnd || !workDays) {
        console.warn('⚠️  V6: Calendar env vars not configured - skipping validation');
        return {
            ...data,
            validation_status: 'skipped',
            validation_reason: 'env_vars_missing_v6',
            validated_at: new Date().toISOString()
        };
    }

    console.log('✅ [Validate Availability V6] Env vars loaded:', {
        workStart,
        workEnd,
        workDays
    });

    // ===== CHECK BUSINESS HOURS =====
    const startHour = parseInt(timeStart.split(':')[0]);
    const endHour = parseInt(timeEnd.split(':')[0]);

    const workStartHour = parseInt(workStart.split(':')[0]);
    const workEndHour = parseInt(workEnd.split(':')[0]);

    if (startHour < workStartHour || endHour > workEndHour) {
        throw new Error(`Horário fora do expediente: ${timeStart}-${timeEnd} (expediente: ${workStart}-${workEnd})`);
    }

    // ===== CHECK WEEKEND =====
    const dateObj = scheduledDate instanceof Date
        ? scheduledDate
        : new Date(scheduledDate);

    const dayOfWeek = dateObj.getDay();
    const workDaysArray = workDays.split(',').map(d => parseInt(d.trim()));

    if (!workDaysArray.includes(dayOfWeek)) {
        throw new Error(`Dia não útil: ${scheduledDate} (dia da semana: ${dayOfWeek})`);
    }

    console.log('✅ [Validate Availability V6] Approved:', scheduledDate, timeStart);

    return {
        ...data,
        validation_status: 'approved',
        validated_at: new Date().toISOString()
    };

} catch (error) {
    console.error('❌ [Validate Availability V6] Error:', error.message);
    console.error('Data received:', JSON.stringify(data, null, 2));
    throw error;
}"""

    validate_node['notes'] = 'V6 FIX: Reads env vars from workflow data (loaded by "Load Env Vars" Set node)'

    # Insert "Load Env Vars" node before "Validate Availability"
    workflow['nodes'].insert(validate_node_index, load_env_node)

    # Update connections - find what connects to Validate Availability
    # and insert Load Env Vars in between
    for node_name, connections in workflow['connections'].items():
        for output_type, output_connections in connections.items():
            for i, conn_list in enumerate(output_connections):
                for j, conn in enumerate(conn_list):
                    if conn['node'] == 'Validate Availability':
                        # Redirect this connection to Load Env Vars instead
                        workflow['connections'][node_name][output_type][i][j]['node'] = 'Load Env Vars'

    # Add connection from Load Env Vars to Validate Availability
    workflow['connections']['Load Env Vars'] = {
        'main': [[{'node': 'Validate Availability', 'type': 'main', 'index': 0}]]
    }

    # Save V6 workflow
    output_path = 'n8n/workflows/05_appointment_scheduler_v6_expression_env_fix.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print(f"✅ WF05 V6 generated: {output_path}")
    print(f"📊 Nodes: {len(workflow['nodes'])}")
    print(f"🔗 Connections: {len(workflow['connections'])}")
    print(f"✨ Key Change: Added 'Load Env Vars' Set node using Expression syntax")
    print(f"✨ Solution: {{ $env.VAR }} in Set node → data.env_var in Code node")

    # Validate JSON
    with open(output_path, 'r', encoding='utf-8') as f:
        json.load(f)
    print("✅ JSON validation: OK")

if __name__ == '__main__':
    generate_wf05_v6()
