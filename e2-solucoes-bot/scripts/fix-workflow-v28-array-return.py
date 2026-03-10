#!/usr/bin/env python3
"""
Fix V28: Array Return Fix for Merge Queries Data nodes
Problem: Merge nodes returning object instead of array
Solution: Ensure all Code nodes return array of objects
"""

import json
import sys
from pathlib import Path

def fix_merge_queries_data_array(js_code):
    """Fix Merge Queries Data nodes to return array of objects"""

    # Build new code that returns array
    new_code = """// Merge Queries Node - V28 Array Return Fix
// Este node garante que os campos query_* sejam preservados após o IF node
// V28: RETORNA ARRAY DE OBJETOS como n8n espera

const inputData = $input.first().json;
const queryData = $node["Build SQL Queries"].json;

// Log para debug
console.log('=== MERGE QUERIES V28 ARRAY FIX ===');
console.log('Input has count:', inputData.count);
console.log('Query data available:', !!queryData);
console.log('Message fields from queryData:');
console.log('  queryData.message:', queryData.message);
console.log('  queryData.content:', queryData.content);
console.log('  queryData.body:', queryData.body);
console.log('  queryData.text:', queryData.text);

// Merge todos os dados preservando os campos de query E mensagem
const mergedData = {
    ...inputData,
    ...queryData,  // V28: Include ALL fields from queryData

    // Preservar todos os campos de query do Build SQL Queries
    query_count: queryData.query_count,
    query_details: queryData.query_details,
    query_upsert: queryData.query_upsert,

    // V28 CRITICAL: Preservar campos de mensagem
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
};

// V28 CRITICAL: Return ARRAY of objects, not single object
console.log('V28: Returning array with 1 object');
return [mergedData];  // ← ARRAY RETURN FIX"""

    return new_code

def fix_build_sql_queries_array(js_code):
    """Fix Build SQL Queries to return array if needed"""

    # Find the return statement
    return_pos = js_code.rfind("return {")
    if return_pos == -1:
        print("Warning: Could not find return statement in Build SQL Queries")
        return js_code

    # Build new return with array fix
    new_return = """// Log para debug
console.log('=== BUILD SQL QUERIES (V28) ===');
console.log('Input message fields:');
console.log('  data.message:', data.message);
console.log('  data.content:', data.content);
console.log('  data.body:', data.body);
console.log('  data.text:', data.text);

// IMPORTANTE: Retornar cada query como campo string individual
// V28: PRESERVAR CAMPOS DE MENSAGEM E RETORNAR ARRAY
const result = {
  ...data,  // Pass through ALL original data

  // SQL Queries
  query_count: query_count,        // String SQL
  query_details: query_details,    // String SQL
  query_upsert: query_upsert,      // String SQL

  // V28 CRITICAL: Explicitly preserve message fields
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
};

// V28: Return as array for n8n compatibility
console.log('V28: Build SQL Queries returning array');
return [result];"""

    # Replace the return statement
    new_js_code = js_code[:return_pos] + new_return
    return new_js_code

def add_state_machine_debug_v28(function_code):
    """Add comprehensive debug to State Machine Logic with V28 markers"""

    # Find the items declaration
    items_pos = function_code.find("const items = $input.all();")
    if items_pos == -1:
        print("Warning: Could not find items declaration")
        return function_code

    # Add V28 debug right after items declaration
    debug_code = """const items = $input.all();

// V28 ARRAY FIX DEBUG
console.log('=== V28 INPUT ANALYSIS (ARRAY FIX) ===');
console.log('Total inputs received:', items.length);
console.log('Input types:', items.map(i => typeof i.json));

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
  console.log('Input 1 conversation_id:', items[1].json.id);
}"""

    # Replace the line
    function_code = function_code.replace(
        "const items = $input.all();",
        debug_code
    )

    return function_code

def main():
    # Load V27 workflow
    v27_path = Path('n8n/workflows/02_ai_agent_conversation_V27_MESSAGE_FLOW_FIX.json')
    if not v27_path.exists():
        print(f"Error: {v27_path} not found")
        print("Creating from V26 instead...")
        v27_path = Path('n8n/workflows/02_ai_agent_conversation_V26_MENU_VALIDATION_FIX.json')
        if not v27_path.exists():
            print(f"Error: {v27_path} not found either")
            sys.exit(1)

    with open(v27_path, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    # Update workflow name
    workflow['name'] = 'AI Agent Conversation - V28 (Array Return Fix)'

    # Fix Build SQL Queries
    build_fixed = False
    for node in workflow['nodes']:
        if node.get('name') == 'Build SQL Queries':
            print(f"Found Build SQL Queries node: {node['id']}")

            original_code = node['parameters']['jsCode']
            fixed_code = fix_build_sql_queries_array(original_code)
            node['parameters']['jsCode'] = fixed_code

            build_fixed = True
            print("✅ Fixed Build SQL Queries to return array")
            break

    if not build_fixed:
        print("Warning: Could not find Build SQL Queries node")

    # Fix both Merge Queries Data nodes
    merge_count = 0
    for node in workflow['nodes']:
        if node.get('name') in ['Merge Queries Data', 'Merge Queries Data1']:
            print(f"Found {node['name']} node: {node['id']}")

            fixed_code = fix_merge_queries_data_array("")  # Generate new code
            node['parameters']['jsCode'] = fixed_code

            merge_count += 1
            print(f"✅ Fixed {node['name']} to return array")

    print(f"Fixed {merge_count} Merge Queries nodes to return arrays")

    # Add comprehensive debug to State Machine Logic
    state_fixed = False
    for node in workflow['nodes']:
        if node.get('name') == 'State Machine Logic':
            print(f"Found State Machine Logic node: {node['id']}")

            if node.get('type') == 'n8n-nodes-base.function':
                # Function node uses 'functionCode'
                original_code = node['parameters']['functionCode']
                fixed_code = add_state_machine_debug_v28(original_code)
                node['parameters']['functionCode'] = fixed_code
            else:
                # Code node uses 'jsCode'
                original_code = node['parameters']['jsCode']
                fixed_code = add_state_machine_debug_v28(original_code)
                node['parameters']['jsCode'] = fixed_code

            state_fixed = True
            print("✅ Added V28 array debug to State Machine Logic")
            break

    if not state_fixed:
        print("Warning: Could not find State Machine Logic node")

    # Save as V28
    v28_path = Path('n8n/workflows/02_ai_agent_conversation_V28_ARRAY_RETURN_FIX.json')
    with open(v28_path, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Created V28 workflow: {v28_path}")
    print("\n📋 V28 Improvements:")
    print("1. Merge Queries Data nodes now return ARRAY of objects")
    print("2. Build SQL Queries also returns array for consistency")
    print("3. All Code nodes properly formatted for n8n")
    print("4. Message fields still preserved through workflow")

    print("\n🔍 Debug Features:")
    print("- BUILD SQL QUERIES (V28) - Array return format")
    print("- MERGE QUERIES V28 ARRAY FIX - Shows array return")
    print("- V28 INPUT ANALYSIS - Validates array format")

    print("\n🚨 Testing Instructions:")
    print("1. Import V28 workflow into n8n")
    print("2. Deactivate V27 workflow")
    print("3. Activate V28 workflow")
    print("4. Send test message '1' via WhatsApp")
    print("5. Check logs for V28 debug messages:")
    print("   docker logs -f e2bot-n8n-dev | grep V28")
    print("\n6. Verify no more 'Code doesn't return items properly' error")
    print("7. Confirm message flow works correctly")

if __name__ == '__main__':
    main()