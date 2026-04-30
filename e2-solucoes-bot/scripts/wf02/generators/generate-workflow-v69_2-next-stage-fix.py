#!/usr/bin/env python3
"""
V69.2 NEXT_STAGE FIX - Generator Script

CRITICAL BUG: Check If Scheduling node receives data from "Send WhatsApp Response" (HTTP node)
which returns API response, NOT the workflow data with next_stage.

ROOT CAUSE:
- Build Update Queries returns: { next_stage: "scheduling", ... }
- Send WhatsApp Response (HTTP): Makes API call, returns: { messageId: "...", status: "sent" }
- Check If Scheduling: Tries {{ $json.next_stage }} but gets HTTP response (no next_stage!)

SOLUTION:
Change Check If Scheduling and Check If Handoff to reference Build Update Queries directly:
- OLD: {{ $json.next_stage }} (from Send WhatsApp Response - WRONG!)
- NEW: {{ $node["Build Update Queries"].json.next_stage }} (from correct source)

Based on: V69.1 + next_stage reference fix
"""

import json

# Load V69.1 as base
print("📂 Loading V69.1 base workflow...")
with open('n8n/workflows/02_ai_agent_conversation_V69_1_FIXED_CONNECTIONS.json', 'r', encoding='utf-8') as f:
    workflow = json.load(f)

print("✅ V69.1 loaded")

# Update workflow metadata
print("\n📝 Updating workflow metadata...")
workflow['name'] = 'WF02: AI Agent V69.2 NEXT_STAGE FIX'
print("✅ Workflow name set to: 'WF02: AI Agent V69.2 NEXT_STAGE FIX'")

# Find and fix Check If Scheduling node
print("\n🔍 Finding Check If Scheduling node...")
check_scheduling_node = None
for node in workflow['nodes']:
    if node.get('name') == 'Check If Scheduling':
        check_scheduling_node = node
        break

if not check_scheduling_node:
    raise ValueError("❌ Check If Scheduling node not found!")

print("✅ Found Check If Scheduling node")

# Fix value1 to reference Build Update Queries
print("\n🔧 V69.2 FIX: Fixing next_stage reference in Check If Scheduling...")
old_value = check_scheduling_node['parameters']['conditions']['string'][0]['value1']
new_value = '={{ $node["Build Update Queries"].json.next_stage }}'

print(f"   OLD: {old_value}")
print(f"   NEW: {new_value}")

check_scheduling_node['parameters']['conditions']['string'][0]['value1'] = new_value
print("✅ Check If Scheduling fixed!")

# Find and fix Check If Handoff node
print("\n🔍 Finding Check If Handoff node...")
check_handoff_node = None
for node in workflow['nodes']:
    if node.get('name') == 'Check If Handoff':
        check_handoff_node = node
        break

if not check_handoff_node:
    raise ValueError("❌ Check If Handoff node not found!")

print("✅ Found Check If Handoff node")

# Fix value1 to reference Build Update Queries
print("\n🔧 V69.2 FIX: Fixing next_stage reference in Check If Handoff...")
old_value_handoff = check_handoff_node['parameters']['conditions']['string'][0]['value1']
new_value_handoff = '={{ $node["Build Update Queries"].json.next_stage }}'

print(f"   OLD: {old_value_handoff}")
print(f"   NEW: {new_value_handoff}")

check_handoff_node['parameters']['conditions']['string'][0]['value1'] = new_value_handoff
print("✅ Check If Handoff fixed!")

# Save V69.2 workflow
output_path = 'n8n/workflows/02_ai_agent_conversation_V69_2_NEXT_STAGE_FIX.json'
print(f"\n💾 Saving V69.2 workflow to {output_path}...")

with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(workflow, f, indent=2, ensure_ascii=False)

# Get file size
import os
file_size = os.path.getsize(output_path)
size_kb = file_size / 1024

print(f"✅ V69.2 workflow saved successfully!")
print(f"📊 File size: {size_kb:.1f} KB")

# Validation summary
print("\n" + "="*60)
print("🎯 V69.2 GENERATION SUMMARY")
print("="*60)
print(f"✅ Base: V69.1 FIXED CONNECTIONS")
print(f"✅ Workflow Name: 'WF02: AI Agent V69.2 NEXT_STAGE FIX'")
print(f"✅ Check If Scheduling: Reference fixed to Build Update Queries")
print(f"✅ Check If Handoff: Reference fixed to Build Update Queries")
print(f"✅ BUG #1 ROOT CAUSE: RESOLVED (correct node reference)")
print(f"✅ All V69.1 fixes preserved (connections, getServiceName)")
print(f"✅ File: {output_path} ({size_kb:.1f} KB)")
print("="*60)

print("\n📋 Next Steps:")
print("1. Import to n8n: http://localhost:5678")
print("2. Test scheduling trigger (services 1 or 3)")
print("3. Verify Check If Scheduling = true (next_stage defined)")
print("4. Verify Trigger Appointment Scheduler executes")
print("\n🚀 V69.2 NEXT_STAGE FIX ready for deployment!")
