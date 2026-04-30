#!/usr/bin/env python3
"""
Fix V27: Message Flow Preservation
Problem: Message field is lost during data flow through merge nodes
Solution: Ensure message fields are preserved through entire workflow
"""

import json
import sys
from pathlib import Path

def fix_build_sql_queries(js_code):
    """Fix Build SQL Queries to preserve message fields"""

    # Find the return statement
    return_pos = js_code.rfind("return {")
    if return_pos == -1:
        print("Warning: Could not find return statement in Build SQL Queries")
        return js_code

    # Find the closing brace
    close_pos = js_code.rfind("};")
    if close_pos == -1:
        print("Warning: Could not find closing brace")
        return js_code

    # Build new return with message preservation
    new_return = """// Log para debug
console.log('=== BUILD SQL QUERIES (V27) ===');
console.log('Input message fields:');
console.log('  data.message:', data.message);
console.log('  data.content:', data.content);
console.log('  data.body:', data.body);
console.log('  data.text:', data.text);

// IMPORTANTE: Retornar cada query como campo string individual
// V27: PRESERVAR CAMPOS DE MENSAGEM
return {
  ...data,  // Pass through ALL original data

  // SQL Queries
  query_count: query_count,        // String SQL
  query_details: query_details,    // String SQL
  query_upsert: query_upsert,      // String SQL

  // V27 CRITICAL: Explicitly preserve message fields
  message: data.message || '',
  content: data.content || '',
  body: data.body || '',
  text: data.text || '',

  // Phone fields
  phone_with_code: phone_with_code,
  phone_without_code: phone_without_code,
  phone_number: data.phone_number || phone_with_code,

  // Other fields
  whatsapp_name: data.whatsapp_name || ''
};"""

    # Replace the return statement
    new_js_code = js_code[:return_pos] + new_return
    return new_js_code

def fix_merge_queries_data(js_code):
    """Fix Merge Queries Data nodes to preserve message fields"""

    # Find the return statement
    return_pos = js_code.find("return {")
    if return_pos == -1:
        print("Warning: Could not find return statement in Merge Queries Data")
        return js_code

    # Build new code with message preservation
    new_code = """// Merge Queries Node - Preserva todos os campos de query
// Este node garante que os campos query_* sejam preservados após o IF node
// V27: TAMBÉM PRESERVA CAMPOS DE MENSAGEM

const inputData = $input.first().json;
const queryData = $node["Build SQL Queries"].json;

// Log para debug
console.log('=== MERGE QUERIES V27 DEBUG ===');
console.log('Input has count:', inputData.count);
console.log('Query data available:', !!queryData);
console.log('Message fields from queryData:');
console.log('  queryData.message:', queryData.message);
console.log('  queryData.content:', queryData.content);
console.log('  queryData.body:', queryData.body);
console.log('  queryData.text:', queryData.text);

// Merge todos os dados preservando os campos de query E mensagem
return {
    ...inputData,
    ...queryData,  // V27: Include ALL fields from queryData

    // Preservar todos os campos de query do Build SQL Queries
    query_count: queryData.query_count,
    query_details: queryData.query_details,
    query_upsert: queryData.query_upsert,

    // V27 CRITICAL: Preservar campos de mensagem
    message: queryData.message || inputData.message || '',
    content: queryData.content || inputData.content || '',
    body: queryData.body || inputData.body || '',
    text: queryData.text || inputData.text || '',

    // Preservar dados do telefone
    phone_with_code: queryData.phone_with_code,
    phone_without_code: queryData.phone_without_code,
    phone_number: queryData.phone_number || queryData.phone_with_code,

    // Manter o count do resultado anterior
    count: inputData.count || 0,

    // Pass through outros dados
    whatsapp_name: queryData.whatsapp_name || inputData.whatsapp_name || ''
};"""

    return new_code

def add_state_machine_debug(function_code):
    """Add comprehensive debug to State Machine Logic"""

    # Find the items declaration
    items_pos = function_code.find("const items = $input.all();")
    if items_pos == -1:
        print("Warning: Could not find items declaration")
        return function_code

    # Add V27 debug right after items declaration
    debug_code = """const items = $input.all();

// V27 COMPREHENSIVE DEBUG
console.log('=== V27 INPUT ANALYSIS ===');
console.log('Total inputs received:', items.length);

// Debug first input (from Merge Conversation Data)
if (items[0]) {
  const keys0 = Object.keys(items[0].json);
  console.log('Input 0 keys:', keys0);
  console.log('Input 0 has message?:', 'message' in items[0].json);
  console.log('Input 0 has content?:', 'content' in items[0].json);
  console.log('Input 0 has body?:', 'body' in items[0].json);
  console.log('Input 0 has text?:', 'text' in items[0].json);
  console.log('Input 0 message value:', items[0].json.message);
  console.log('Input 0 content value:', items[0].json.content);
  console.log('Input 0 body value:', items[0].json.body);
  console.log('Input 0 text value:', items[0].json.text);
}

// Debug second input (from database)
if (items[1]) {
  console.log('Input 1 keys:', Object.keys(items[1].json));
}"""

    # Replace the line
    function_code = function_code.replace(
        "const items = $input.all();",
        debug_code
    )

    return function_code

def main():
    # Load V26 workflow
    v26_path = Path('n8n/workflows/02_ai_agent_conversation_V26_MENU_VALIDATION_FIX.json')
    if not v26_path.exists():
        print(f"Error: {v26_path} not found")
        sys.exit(1)

    with open(v26_path, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    # Update workflow name
    workflow['name'] = 'AI Agent Conversation - V27 (Message Flow Fix)'

    # Fix Build SQL Queries
    build_fixed = False
    for node in workflow['nodes']:
        if node.get('name') == 'Build SQL Queries':
            print(f"Found Build SQL Queries node: {node['id']}")

            original_code = node['parameters']['jsCode']
            fixed_code = fix_build_sql_queries(original_code)
            node['parameters']['jsCode'] = fixed_code

            build_fixed = True
            print("✅ Fixed Build SQL Queries to preserve message fields")
            break

    if not build_fixed:
        print("Warning: Could not find Build SQL Queries node")

    # Fix both Merge Queries Data nodes
    merge_count = 0
    for node in workflow['nodes']:
        if node.get('name') in ['Merge Queries Data', 'Merge Queries Data1']:
            print(f"Found {node['name']} node: {node['id']}")

            fixed_code = fix_merge_queries_data("")  # Generate new code
            node['parameters']['jsCode'] = fixed_code

            merge_count += 1
            print(f"✅ Fixed {node['name']} to preserve message fields")

    print(f"Fixed {merge_count} Merge Queries nodes")

    # Add comprehensive debug to State Machine Logic
    state_fixed = False
    for node in workflow['nodes']:
        if node.get('name') == 'State Machine Logic':
            print(f"Found State Machine Logic node: {node['id']}")

            if node.get('type') == 'n8n-nodes-base.function':
                # Function node uses 'functionCode'
                original_code = node['parameters']['functionCode']
                fixed_code = add_state_machine_debug(original_code)
                node['parameters']['functionCode'] = fixed_code
            else:
                # Code node uses 'jsCode'
                original_code = node['parameters']['jsCode']
                fixed_code = add_state_machine_debug(original_code)
                node['parameters']['jsCode'] = fixed_code

            state_fixed = True
            print("✅ Added V27 comprehensive debug to State Machine Logic")
            break

    if not state_fixed:
        print("Warning: Could not find State Machine Logic node")

    # Save as V27
    v27_path = Path('n8n/workflows/02_ai_agent_conversation_V27_MESSAGE_FLOW_FIX.json')
    with open(v27_path, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Created V27 workflow: {v27_path}")
    print("\n📋 V27 Improvements:")
    print("1. Build SQL Queries now preserves ALL message fields")
    print("2. Merge Queries Data nodes explicitly pass message fields")
    print("3. Comprehensive V27 debug shows exact data flow")
    print("4. All nodes now use spread operator to preserve fields")

    print("\n🔍 Debug Features:")
    print("- BUILD SQL QUERIES (V27) - Shows input message fields")
    print("- MERGE QUERIES V27 DEBUG - Shows field preservation")
    print("- V27 INPUT ANALYSIS - Shows exact State Machine inputs")

    print("\n🚨 Testing Instructions:")
    print("1. Import V27 workflow into n8n")
    print("2. Deactivate V26 workflow")
    print("3. Activate V27 workflow")
    print("4. Send test message '1' via WhatsApp")
    print("5. Check logs for V27 debug messages:")
    print("   docker logs -f e2bot-n8n-dev | grep V27")
    print("\n6. Look specifically for:")
    print("   - 'V27 INPUT ANALYSIS' - Check if message fields are present")
    print("   - 'Input 0 message value:' - Should show '1' not empty")
    print("\n7. If message is still empty, check workflow 01:")
    print("   - Is it passing the message field correctly?")
    print("   - Try testing webhook directly with curl")

if __name__ == '__main__':
    main()