#!/usr/bin/env python3
"""
V69 COMPLETE FIX - Generator Script
Fixes all remaining bugs from V67/V68 versions:
- BUG #1: ✅ Already fixed in V68.3 (next_stage passing)
- BUG #2: ✅ Already fixed in V68.3 (trimmedCorrectedName)
- BUG #3: 🔧 FIX NOW - Add getServiceName() function definition

Based on V68.3 + adds missing getServiceName() function
"""

import json
import re

# Load V68.3 as base (has bugs #1 and #2 fixed, needs bug #3 fix)
print("📂 Loading V68.3 base workflow...")
with open('n8n/workflows/02_ai_agent_conversation_V68_3_COMPLETE_SYNTAX_FIX.json', 'r', encoding='utf-8') as f:
    workflow = json.load(f)

print("✅ V68.3 loaded")

# Update workflow metadata
print("\n📝 Updating workflow metadata...")
workflow['name'] = 'WF02: AI Agent V69 COMPLETE FIX'
workflow['nodes'][0]['name'] = 'WF02: AI Agent V69 COMPLETE FIX'

print("✅ Workflow name set to: 'WF02: AI Agent V69 COMPLETE FIX'")

# Find State Machine Logic node
print("\n🔍 Finding State Machine Logic node...")
state_machine_node = None
for node in workflow['nodes']:
    if node.get('name') == 'State Machine Logic':
        state_machine_node = node
        break

if not state_machine_node:
    raise ValueError("❌ State Machine Logic node not found!")

print("✅ Found State Machine Logic node")

# Get current function code
state_code = state_machine_node['parameters']['functionCode']

# V69 FIX: Add getServiceName() function after currentData declaration
print("\n🔧 V69 FIX: Adding getServiceName() function...")

# Pattern to find currentData declaration
pattern = r'(const currentData = input\.currentData \|\| \{\};)'

# Function to add
get_service_name_function = r'''\1

// V69 FIX: Helper function for service names (BUG #3 FIX)
function getServiceName(serviceCode) {
  const serviceNames = {
    '1': 'Energia Solar',
    '2': 'Subestações',
    '3': 'Projetos Elétricos',
    '4': 'BESS (Armazenamento de Energia)',
    '5': 'Análise e Laudos'
  };
  return serviceNames[serviceCode] || 'serviço selecionado';
}'''

# Apply fix
new_state_code = re.sub(pattern, get_service_name_function, state_code)

# Verify function was added
if 'function getServiceName' in new_state_code:
    print("✅ getServiceName() function added successfully!")
else:
    raise ValueError("❌ Failed to add getServiceName() function - pattern didn't match!")

# Count function calls to verify
call_count = new_state_code.count('getServiceName(')
if call_count >= 2:
    print(f"✅ Found {call_count} calls to getServiceName() (expected 2+)")
else:
    print(f"⚠️ Warning: Found only {call_count} calls to getServiceName() (expected 2)")

# Update node with new code
state_machine_node['parameters']['functionCode'] = new_state_code

# Save V69 workflow
output_path = 'n8n/workflows/02_ai_agent_conversation_V69_COMPLETE_FIX.json'
print(f"\n💾 Saving V69 workflow to {output_path}...")

with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(workflow, f, indent=2, ensure_ascii=False)

# Get file size
import os
file_size = os.path.getsize(output_path)
size_kb = file_size / 1024

print(f"✅ V69 workflow saved successfully!")
print(f"📊 File size: {size_kb:.1f} KB")

# Validation summary
print("\n" + "="*60)
print("🎯 V69 GENERATION SUMMARY")
print("="*60)
print(f"✅ Base: V68.3 COMPLETE SYNTAX FIX")
print(f"✅ Workflow Name: 'WF02: AI Agent V69 COMPLETE FIX'")
print(f"✅ BUG #1: next_stage passing (inherited from V68.3)")
print(f"✅ BUG #2: trimmedCorrectedName (inherited from V68.3)")
print(f"✅ BUG #3: getServiceName() function ADDED (NEW FIX)")
print(f"✅ Function calls detected: {call_count}")
print(f"✅ File: {output_path} ({size_kb:.1f} KB)")
print("="*60)

print("\n📋 Next Steps:")
print("1. Validate JavaScript syntax: node -c <extracted-code.js>")
print("2. Import to n8n: http://localhost:5678")
print("3. Test returning user flow (BUG #3 scenario)")
print("4. Test scheduling trigger (BUG #1 scenario)")
print("\n🚀 V69 COMPLETE FIX ready for deployment!")
