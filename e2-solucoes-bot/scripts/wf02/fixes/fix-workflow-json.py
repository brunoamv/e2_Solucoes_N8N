#!/usr/bin/env python3
"""
Fix n8n workflow JSON file with improperly escaped JavaScript code
"""
import json
import re

def fix_json_workflow(input_file, output_file):
    """
    Fix JSON workflow file by properly escaping JavaScript code
    """

    # Read the original file
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # The issue is in the jsCode fields - they contain actual newlines
    # We need to find these sections and escape them properly

    # Pattern to find jsCode fields with multiline content
    # This is tricky because we need to handle nested quotes and newlines

    # Strategy: Parse line by line and build proper JSON
    lines = content.split('\n')
    fixed_lines = []
    in_js_code = False
    js_code_buffer = []

    i = 0
    while i < len(lines):
        line = lines[i]

        # Check if we're starting a jsCode field
        if '"jsCode":' in line and not in_js_code:
            # This is the start of a jsCode field
            in_js_code = True
            js_code_buffer = [line]

            # Check if it's a single line jsCode
            if line.strip().endswith('",') or line.strip().endswith('"'):
                in_js_code = False
                fixed_lines.append(line)

            i += 1
            continue

        # If we're inside a jsCode field
        if in_js_code:
            js_code_buffer.append(line)

            # Check if this is the end of the jsCode field
            # It ends with a quote followed by nothing or a comma/bracket
            if (line.strip().endswith('",') or
                line.strip().endswith('"') or
                ('"' in line and '}' in line)):

                # Process the entire jsCode buffer
                js_content = '\n'.join(js_code_buffer)

                # Extract the JavaScript code
                match = re.search(r'"jsCode":\s*"(.*?)"(?:\s*[,}]|$)', js_content, re.DOTALL)
                if match:
                    js_code = match.group(1)
                    # Properly escape the JavaScript code
                    js_code_escaped = js_code.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')

                    # Rebuild the line with properly escaped code
                    indent = '        ' if 'jsCode' in js_code_buffer[0] else '      '
                    if js_content.strip().endswith(','):
                        fixed_line = f'{indent}"jsCode": "{js_code_escaped}",'
                    else:
                        fixed_line = f'{indent}"jsCode": "{js_code_escaped}"'

                    fixed_lines.append(fixed_line)
                else:
                    # Fallback: just escape newlines in the entire buffer
                    for buf_line in js_code_buffer:
                        fixed_lines.append(buf_line)

                in_js_code = False
                js_code_buffer = []

            i += 1
            continue

        # Normal line, not in jsCode
        fixed_lines.append(line)
        i += 1

    # Reconstruct the JSON
    fixed_content = '\n'.join(fixed_lines)

    # Try to parse and reformat
    try:
        data = json.loads(fixed_content)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"✅ Successfully fixed JSON and saved to {output_file}")
        return True
    except json.JSONDecodeError as e:
        print(f"❌ Still has JSON errors after fix attempt: {e}")

        # Save the attempted fix for debugging
        debug_file = output_file.replace('.json', '_debug.json')
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        print(f"💾 Saved attempted fix to {debug_file} for debugging")

        return False

# Fix the workflow file
if __name__ == "__main__":
    input_file = "/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/01_main_whatsapp_handler_V2.3_FIXED.json"
    output_file = "/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/01_main_whatsapp_handler_V2.3_FIXED_IMPORT.json"

    fix_json_workflow(input_file, output_file)