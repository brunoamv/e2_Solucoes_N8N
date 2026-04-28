#!/usr/bin/env python3
"""
Fix V96 - Conversation ID Preservation Fix
Fixes the critical bug where conversation_id is lost between State Machine and Build Update Queries
"""

import json
import os

def fix_state_machine_conversation_id():
    """Add conversation_id preservation to State Machine output"""

    # Load V95 workflow
    v95_file = "/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V95_EMERGENCY_FIX.json"

    if not os.path.exists(v95_file):
        print(f"❌ Error: V95 file not found: {v95_file}")
        return False

    with open(v95_file, 'r') as f:
        workflow = json.load(f)

    # Find State Machine node
    state_machine_found = False
    for node in workflow['nodes']:
        if 'State Machine' in node.get('name', ''):
            print(f"✅ Found State Machine node: {node['name']}")

            # Get current code
            if 'parameters' in node:
                if 'functionCode' in node['parameters']:
                    code_field = 'functionCode'
                elif 'jsCode' in node['parameters']:
                    code_field = 'jsCode'
                else:
                    print("❌ No code field found in State Machine")
                    continue

                current_code = node['parameters'][code_field]

                # Find the return statement and add conversation_id
                # Look for the final return statement
                return_pattern = "return {"
                if return_pattern in current_code:
                    # Find the return statement and add conversation_id
                    lines = current_code.split('\n')
                    new_lines = []
                    for i, line in enumerate(lines):
                        new_lines.append(line)
                        # Add conversation_id after response_text in the return
                        if 'response_text: responseText,' in line:
                            new_lines.append('  conversation_id: input.conversation_id || input.id || null,  // V96 FIX: Preserve conversation_id')

                    node['parameters'][code_field] = '\n'.join(new_lines)
                    state_machine_found = True
                    print("✅ Added conversation_id to State Machine output")
                else:
                    print("⚠️ Could not find return statement pattern")

    if not state_machine_found:
        print("❌ State Machine not found or not fixed")
        return False

    # Update workflow name
    workflow['name'] = '02 - AI Agent Conversation V96 (Conversation ID Fix)'

    # Save as V96
    output_file = "/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V96_CONVERSATION_ID_FIX.json"

    with open(output_file, 'w') as f:
        json.dump(workflow, f, indent=2)

    print(f"✅ V96 workflow saved: {output_file}")
    return True

def create_comprehensive_fix():
    """Create a more comprehensive fix that ensures conversation_id is preserved everywhere"""

    print("🔧 Creating V96 with comprehensive conversation_id fix...")

    # Load V95 as base
    v95_file = "/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V95_EMERGENCY_FIX.json"

    with open(v95_file, 'r') as f:
        workflow = json.load(f)

    # Fix 1: Update State Machine to preserve conversation_id
    for node in workflow['nodes']:
        if 'State Machine' in node.get('name', ''):
            if 'parameters' in node:
                code_field = 'functionCode' if 'functionCode' in node['parameters'] else 'jsCode'
                if code_field in node['parameters']:
                    code = node['parameters'][code_field]

                    # Add conversation_id extraction at the beginning
                    extraction_code = """
// V96 FIX: Extract and preserve conversation_id
const conversation_id = input.conversation_id || input.id || input.currentData?.conversation_id || null;
console.log('V96: conversation_id extracted:', conversation_id);
"""

                    # Insert after the input extraction
                    if "const input = $input.all()[0].json;" in code:
                        code = code.replace(
                            "const input = $input.all()[0].json;",
                            "const input = $input.all()[0].json;\n" + extraction_code
                        )

                    # Fix the return statement to include conversation_id
                    if "return {" in code:
                        code = code.replace(
                            "return {",
                            "return {\n  conversation_id: conversation_id,  // V96 FIX: Always include conversation_id"
                        )

                    node['parameters'][code_field] = code
                    print("✅ Fixed State Machine with conversation_id preservation")

    # Fix 2: Update Build Update Queries to handle missing conversation_id better
    for node in workflow['nodes']:
        if node.get('name') == 'Build Update Queries':
            if 'parameters' in node and 'jsCode' in node['parameters']:
                code = node['parameters']['jsCode']

                # Add better conversation_id extraction
                fix_code = """
// V96 FIX: Better conversation_id extraction with multiple fallbacks
const conversation_id =
  inputData.conversation_id ||
  inputData.id ||
  inputData.currentData?.conversation_id ||
  inputData.currentData?.id ||
  null;

console.log('V96 Build Update Queries: conversation_id =', conversation_id);
if (!conversation_id) {
  console.warn('V96 WARNING: conversation_id is null in Build Update Queries!');
  console.log('V96 DEBUG: inputData keys:', Object.keys(inputData));
}
"""

                # Replace the existing conversation_id extraction
                if "const conversation_id = inputData.conversation_id || null;" in code:
                    code = code.replace(
                        "const conversation_id = inputData.conversation_id || null;",
                        fix_code
                    )
                elif "const conversation_id =" in code:
                    # Find and replace any conversation_id assignment
                    lines = code.split('\n')
                    for i, line in enumerate(lines):
                        if line.strip().startswith('const conversation_id ='):
                            lines[i] = fix_code
                            break
                    code = '\n'.join(lines)

                node['parameters']['jsCode'] = code
                print("✅ Fixed Build Update Queries with better conversation_id handling")

    # Update workflow name
    workflow['name'] = '02 - AI Agent Conversation V96 (Comprehensive Conversation ID Fix)'

    # Save V96
    output_file = "/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V96_CONVERSATION_ID_FIX.json"

    with open(output_file, 'w') as f:
        json.dump(workflow, f, indent=2)

    print(f"✅ V96 workflow generated successfully!")
    print(f"📁 Output: {output_file}")

    return output_file

def main():
    """Main execution"""

    print("=" * 60)
    print("🔧 V96 - CONVERSATION ID PRESERVATION FIX")
    print("=" * 60)
    print()
    print("Problem: conversation_id is lost between State Machine and Build Update Queries")
    print("Solution: Ensure conversation_id is passed through all nodes")
    print()

    # Create comprehensive fix
    output_file = create_comprehensive_fix()

    print()
    print("📝 DEPLOYMENT INSTRUCTIONS:")
    print("=" * 60)
    print("1. Import V96 in n8n:")
    print(f"   File: {output_file}")
    print()
    print("2. DISABLE the current workflow")
    print()
    print("3. ACTIVATE V96 workflow")
    print()
    print("4. Test the fix:")
    print("   - Send a message")
    print("   - Check logs: docker logs -f e2bot-n8n-dev | grep 'V96:'")
    print("   - Verify conversation_id is preserved")
    print()
    print("5. Monitor database:")
    print("   docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \\")
    print("     -c \"SELECT id, phone_number, current_state FROM conversations ORDER BY updated_at DESC LIMIT 5;\"")
    print()
    print("🎯 Key Improvements in V96:")
    print("- State Machine always includes conversation_id in output")
    print("- Build Update Queries has multiple fallbacks for conversation_id")
    print("- Enhanced logging for debugging")
    print("- Preserves conversation context throughout flow")
    print()
    print("✅ V96 fix complete!")

if __name__ == "__main__":
    main()