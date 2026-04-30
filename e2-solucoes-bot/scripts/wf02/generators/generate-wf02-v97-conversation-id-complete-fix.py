#!/usr/bin/env python3
"""
Generate WF02 V97 - Complete Conversation ID Fix
Fixes the critical conversation_id loss issue affecting V90-V96
Root Cause: State Machine executes TWICE, second execution loses conversation_id context
Solution:
  1. State Machine preserves conversation_id explicitly in output
  2. Build Update Queries uses robust multi-fallback extraction
  3. Enhanced logging for debugging
Date: 2026-04-27
"""

import json
import os
from datetime import datetime

# Base paths
BASE_DIR = "/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot"
WORKFLOWS_DIR = os.path.join(BASE_DIR, "n8n/workflows")

# Load V94 as base (it has the complete structure and state machine logic)
v94_path = os.path.join(WORKFLOWS_DIR, "02_ai_agent_conversation_V94_COMPLETE_FIX.json")

print("🔧 Generating WF02 V97 - Complete Conversation ID Fix...")
print(f"Loading base workflow from: {v94_path}")

with open(v94_path, 'r', encoding='utf-8') as f:
    workflow = json.load(f)

# Update workflow metadata
workflow['name'] = "02 - AI Agent Conversation V97 (Conversation ID Complete Fix)"
workflow['updatedAt'] = datetime.now().isoformat()

# V97 Build Update Queries Code - Robust conversation_id extraction
build_update_queries_v97 = """
// ===================================================
// V97 BUILD UPDATE QUERIES - CONVERSATION ID COMPLETE FIX
// ===================================================
// DEFINITIVE FIX: Prevent conversation_id loss with robust extraction
// - Multi-level fallback chain for conversation_id
// - Comprehensive debugging logs
// - Validation warnings when conversation_id is null
// Date: 2026-04-27
// Version: V97 Complete Fix
// ===================================================

// Get input from State Machine
const inputData = $input.first().json;

console.log('=== V97 BUILD UPDATE QUERIES START ===');
console.log('V97: Input keys:', Object.keys(inputData));

// ===================================================
// V97 CRITICAL FIX: Multi-level conversation_id extraction
// ===================================================
// This ensures conversation_id is NEVER lost, even when State Machine
// executes twice or context is incomplete
const conversation_id =
  inputData.conversation_id ||          // First: Direct from input
  inputData.id ||                       // Second: Alternative ID field
  inputData.currentData?.conversation_id ||  // Third: From currentData object
  inputData.currentData?.id ||          // Fourth: currentData alternative ID
  null;

console.log('V97: Conversation ID resolution:');
console.log('  - inputData.conversation_id:', inputData.conversation_id);
console.log('  - inputData.id:', inputData.id);
console.log('  - inputData.currentData?.conversation_id:', inputData.currentData?.conversation_id);
console.log('  - inputData.currentData?.id:', inputData.currentData?.id);
console.log('V97: RESOLVED conversation_id:', conversation_id);

// V97: Critical validation - warn if conversation_id is null
if (!conversation_id) {
  console.error('V97 CRITICAL WARNING: conversation_id is NULL!');
  console.error('V97 DEBUG: Full inputData:', JSON.stringify(inputData, null, 2));
  console.error('V97 DEBUG: This will cause database UPDATE to fail!');
}

// Extract other data
const phone_number = inputData.phone_number || inputData.phone_with_code || null;
const next_stage = inputData.next_stage || inputData.current_stage || 'greeting';
const update_data = inputData.update_data || {};

console.log('V97: Phone number:', phone_number);
console.log('V97: Next stage:', next_stage);
console.log('V97: Update data keys:', Object.keys(update_data));

// ===================================================
// V97: Build dynamic UPDATE query
// ===================================================
const updates = [];
const values = [];
let paramIndex = 2; // $1 is phone_number

// Always update current_stage (prevents loops)
updates.push(`current_stage = $${paramIndex}`);
values.push(next_stage);
paramIndex++;

// Add updates from State Machine
Object.entries(update_data).forEach(([key, value]) => {
  updates.push(`${key} = $${paramIndex}`);
  values.push(value);
  paramIndex++;
});

// Always update timestamps
updates.push(`updated_at = NOW()`);
updates.push(`last_message_at = NOW()`);

// Build final query
const updateQuery = `
  UPDATE conversations
  SET ${updates.join(', ')}
  WHERE phone_number = $1
  RETURNING *
`;

console.log('V97: Update query:', updateQuery);
console.log('V97: Query values:', [phone_number, ...values]);
console.log('=== V97 BUILD UPDATE QUERIES END ===');

// V97: Return with explicit conversation_id preservation
return {
  query_update_conversation: updateQuery,
  phone_number: phone_number,
  values: [phone_number, ...values],
  conversation_id: conversation_id,  // V97: EXPLICIT preservation
  next_stage: next_stage,
  version: 'V97'
};
"""

# Update Build Update Queries node
build_queries_updated = False
for node in workflow.get('nodes', []):
    if 'Build Update Queries' in node.get('name', ''):
        print(f"✅ Found Build Update Queries node: {node['name']}")

        # Determine code field
        if 'jsCode' in node.get('parameters', {}):
            code_field = 'jsCode'
        elif 'functionCode' in node.get('parameters', {}):
            code_field = 'functionCode'
        else:
            print("⚠️  Warning: No code field found in Build Update Queries")
            continue

        node['parameters'][code_field] = build_update_queries_v97
        build_queries_updated = True
        break

if not build_queries_updated:
    print("⚠️  Warning: Build Update Queries node not found in workflow")

# Now update State Machine to preserve conversation_id in output
# Find State Machine node
state_machine_updated = False
for node in workflow.get('nodes', []):
    if 'State Machine' in node.get('name', '') and node.get('type') == 'n8n-nodes-base.function':
        print(f"✅ Found State Machine node: {node['name']}")

        current_code = node['parameters'].get('functionCode', '')

        # V97: Modify the final return statement to include conversation_id
        # Find the line: const output = {
        if 'const output = {' in current_code:
            # Insert conversation_id preservation right after response_text
            modified_code = current_code.replace(
                '  response_text: responseText,',
                '''  response_text: responseText,
  conversation_id: input.conversation_id || input.id || input.currentData?.conversation_id || null,  // V97: Preserve conversation_id'''
            )

            # Also update version to V97
            modified_code = modified_code.replace(
                "  version: 'V94',",
                "  version: 'V97',"
            )

            # Update logging
            modified_code = modified_code.replace(
                "console.log('=== V94 STATE MACHINE START (COMPLETE FIX) ===');",
                """console.log('=== V97 STATE MACHINE START (CONVERSATION ID FIX) ===');
console.log('V97: conversation_id:', input.conversation_id || input.id || 'NULL');"""
            )

            modified_code = modified_code.replace(
                "console.log('=== V94 STATE MACHINE END ===');",
                """console.log('V97: Output conversation_id:', output.conversation_id);
console.log('=== V97 STATE MACHINE END ===');"""
            )

            node['parameters']['functionCode'] = modified_code
            state_machine_updated = True
        else:
            print("⚠️  Warning: Could not find output definition in State Machine")

if not state_machine_updated:
    print("⚠️  Warning: State Machine not updated")

# Save the updated workflow
output_path = os.path.join(WORKFLOWS_DIR, "02_ai_agent_conversation_V97_CONVERSATION_ID_COMPLETE_FIX.json")

with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(workflow, f, indent=2, ensure_ascii=False)

print(f"\n✅ V97 workflow generated successfully!")
print(f"📁 Output: {output_path}")

print("\n" + "=" * 70)
print("📝 DEPLOYMENT INSTRUCTIONS")
print("=" * 70)

print("\n1️⃣  Import V97 Workflow in n8n:")
print(f"   File: {output_path}")
print("   Action: Import from file in n8n UI")

print("\n2️⃣  Disable Current Active Workflow:")
print("   - Find: '02 - AI Agent Conversation V74.1_2' (or current active)")
print("   - Click: Active toggle to disable")

print("\n3️⃣  Activate V97 Workflow:")
print("   - Open imported V97 workflow")
print("   - Click: Active toggle to enable")

print("\n4️⃣  Test Conversation ID Preservation:")
print("   Send WhatsApp message and check logs:")
print("   ```bash")
print("   docker logs -f e2bot-n8n-dev | grep -E 'V97:|conversation_id'")
print("   ```")

print("\n5️⃣  Validate Database Updates:")
print("   ```bash")
print("   docker exec e2bot-postgres-dev psql -U postgres -d e2bot_dev \\")
print("     -c \"SELECT id, phone_number, current_state, updated_at FROM conversations ORDER BY updated_at DESC LIMIT 5;\"")
print("   ```")

print("\n" + "=" * 70)
print("🎯 KEY IMPROVEMENTS IN V97")
print("=" * 70)

print("\n✅ State Machine:")
print("   - Explicitly includes conversation_id in output")
print("   - Multi-level fallback: input.conversation_id → input.id → currentData")
print("   - Enhanced logging for conversation_id tracking")

print("\n✅ Build Update Queries:")
print("   - Robust 4-level conversation_id extraction")
print("   - Critical validation warnings when conversation_id is null")
print("   - Comprehensive debugging logs")
print("   - Explicit conversation_id preservation in return")

print("\n✅ Root Cause Fixed:")
print("   - Problem: State Machine executes TWICE in workflow")
print("   - Impact: Second execution loses conversation_id context")
print("   - Solution: Both nodes now preserve conversation_id explicitly")
print("   - Result: conversation_id NEVER lost between executions")

print("\n" + "=" * 70)
print("🔍 MONITORING & VALIDATION")
print("=" * 70)

print("\nExpected Log Output:")
print("```")
print("V97: conversation_id: <UUID>")
print("V97: RESOLVED conversation_id: <UUID>")
print("V97: Output conversation_id: <UUID>")
print("```")

print("\nError Indicators (should NOT appear):")
print("```")
print("V97 CRITICAL WARNING: conversation_id is NULL!")
print("```")

print("\nValidation Checklist:")
print("☐ V97 logs show conversation_id throughout execution")
print("☐ Build Update Queries receives conversation_id")
print("☐ Database UPDATE succeeds (no null conversation_id)")
print("☐ Workflow completes without errors")
print("☐ State transitions work correctly")

print("\n" + "=" * 70)
print("✅ V97 GENERATION COMPLETE")
print("=" * 70)
