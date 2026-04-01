#!/usr/bin/env python3
"""
WF07 V8 - No FS Module Solution Generator
Date: 2026-03-31
Fix: Remove fs module usage from Render Template node
Root Cause: n8n blocks Node.js modules (fs, path, etc) in Code nodes
Solution: Template HTML is already available from Read Template File node output
"""

import json
from datetime import datetime

def generate_wf07_v8():
    """Generate WF07 V8 without fs module usage"""

    # Read V6 as base
    with open('n8n/workflows/07_send_email_v6_docker_volume_fix.json', 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    # Update metadata
    workflow['name'] = '07 - Send Email V8 (No FS Module Fix)'
    workflow['versionId'] = 'V8'

    # Update tags
    workflow['tags'] = [
        {"name": "wf05-integration", "createdAt": "2026-03-26T00:00:00.000000"},
        {"name": "v8", "createdAt": "2026-03-31T00:00:00.000000"},
        {"name": "no-fs-module", "createdAt": "2026-03-31T00:00:00.000000"},
        {"name": "complete-fix", "createdAt": "2026-03-31T00:00:00.000000"}
    ]

    # Find "Render Template" node
    render_node = None
    for node in workflow['nodes']:
        if node.get('name') == 'Render Template':
            render_node = node
            break

    if not render_node:
        raise Exception("Render Template node not found!")

    # V8 FIX: Remove fs module usage, template HTML is already in $('Read Template File').first().json.data
    render_node['parameters']['jsCode'] = """// Render Template - V8 NO FS MODULE FIX
// REASON: n8n blocks Node.js modules (fs, path, etc) in Code nodes
// SOLUTION: Template HTML is already available from Read Template File node output

// ===== GET TEMPLATE HTML FROM PREVIOUS NODE =====
const templateHtml = $('Read Template File').first().json.data;
const data = $input.first().json;
const templateData = data.template_data;

console.log('📝 [Render Template V8] Template data received:', {
    has_template_html: !!templateHtml,
    template_length: templateHtml?.length || 0,
    template_data_keys: Object.keys(templateData || {})
});

if (!templateHtml) {
    throw new Error('Template HTML not found in Read Template File output');
}

// ===== SIMPLE TEMPLATE VARIABLE REPLACEMENT (NO FS MODULE) =====
const renderTemplate = (html, data) => {
    let rendered = html;

    console.log('🔄 [Render V8] Starting template rendering with data:', JSON.stringify(data, null, 2));

    // Replace {{variable}} style placeholders
    rendered = rendered.replace(/\\{\\{\\s*(\\w+)\\s*\\}\\}/g, (match, key) => {
        const value = data[key] !== undefined ? data[key] : match;
        console.log(`  Replace {{${key}}} → ${value}`);
        return value;
    });

    // Handle conditional blocks: {{#if variable}}...{{/if}}
    rendered = rendered.replace(/\\{\\{#if\\s+(\\w+)\\}\\}([\\s\\S]*?)\\{\\{\\/if\\}\\}/g, (match, key, content) => {
        const result = data[key] ? content : '';
        console.log(`  Conditional {{#if ${key}}} → ${data[key] ? 'included' : 'skipped'}`);
        return result;
    });

    // Handle inverted conditionals: {{#unless variable}}...{{/unless}}
    rendered = rendered.replace(/\\{\\{#unless\\s+(\\w+)\\}\\}([\\s\\S]*?)\\{\\{\\/unless\\}\\}/g, (match, key, content) => {
        const result = !data[key] ? content : '';
        console.log(`  Conditional {{#unless ${key}}} → ${!data[key] ? 'included' : 'skipped'}`);
        return result;
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

console.log('✅ [Render V8] Template rendered successfully:', {
    html_length: htmlBody.length,
    text_length: textBody.length
});

return {
    ...data,
    html_body: htmlBody,
    text_body: textBody
};
"""

    render_node['notes'] = """V8 FIX: No fs module usage (n8n blocks Node.js modules)
Template HTML is read from Read Template File node output (data property)
Pure JavaScript template replacement without external dependencies"""

    # Save V8 workflow
    output_path = 'n8n/workflows/07_send_email_v8_no_fs_module.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print(f"✅ WF07 V8 generated: {output_path}")
    print(f"📊 Nodes: {len(workflow['nodes'])}")
    print(f"🔗 Connections: {len(workflow['connections'])}")
    print(f"✨ Key Change: Removed fs module usage from Render Template node")
    print(f"✨ Solution: Template HTML from Read Template File node (data property)")

    # Validate JSON
    with open(output_path, 'r', encoding='utf-8') as f:
        json.load(f)
    print("✅ JSON validation: OK")

if __name__ == '__main__':
    generate_wf07_v8()
