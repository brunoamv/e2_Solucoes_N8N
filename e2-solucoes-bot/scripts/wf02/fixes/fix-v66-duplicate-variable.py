#!/usr/bin/env python3
"""
V66 Critical Bug Fix - Duplicate trimmedName Variable Declaration

Problem: Two 'const trimmedName' declarations in State Machine Logic node
- Line 169: collect_name state
- Line ~387: correction_name state

Solution: Rename variable in correction_name state to trimmedCorrectedName

Author: Claude Code
Date: 2026-03-11
"""

import json
import re
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent.parent
V66_PATH = BASE_DIR / "n8n/workflows/02_ai_agent_conversation_V66_CORRECTION_STATES_COMPLETE.json"
V66_FIXED_PATH = BASE_DIR / "n8n/workflows/02_ai_agent_conversation_V66_CORRECTION_STATES_COMPLETE_FIXED.json"

print("=" * 70)
print("V66 Duplicate Variable Fix")
print("=" * 70)
print()

# Load V66
print(f"📂 Loading V66: {V66_PATH}")
with open(V66_PATH, 'r', encoding='utf-8') as f:
    workflow = json.load(f)

print(f"✅ Loaded: {len(workflow['nodes'])} nodes")
print()

# Find State Machine Logic node
print("🔍 Finding State Machine Logic node...")
state_machine_node = None
state_machine_index = None

for i, node in enumerate(workflow['nodes']):
    if node.get('name') == 'State Machine Logic':
        state_machine_node = node
        state_machine_index = i
        break

if not state_machine_node:
    print("❌ ERRO: State Machine Logic node not found!")
    exit(1)

print(f"✅ Found at index {state_machine_index}")
print()

# Get current code
code = state_machine_node['parameters']['functionCode']
print(f"📝 Current code size: {len(code)} chars")
print()

# Count trimmedName occurrences
trimmed_name_count = code.count('const trimmedName')
print(f"🔍 Found {trimmed_name_count} 'const trimmedName' declarations")
print()

if trimmed_name_count != 2:
    print(f"⚠️ Expected 2 declarations, found {trimmed_name_count}")
    print("This may not be the issue, or it's already been fixed.")
    exit(0)

# Fix: Replace SECOND occurrence of 'const trimmedName' with 'const trimmedCorrectedName'
# Strategy: Find correction_name state block and replace variable name within it

print("🔧 Applying fix...")
print()

# Find the correction_name case block
correction_name_pattern = r"(case 'correction_name':.*?)(const trimmedName = message\.trim\(\);)(.*?)(if \(trimmedName\.length >= 2 && !/\^\[0-9\]\+\$/\.test\(trimmedName\)\))(.*?)(updateData\.lead_name = trimmedName;)(.*?)(break;)"

# Replace within correction_name block only
def fix_correction_name_block(match):
    """Replace trimmedName with trimmedCorrectedName in correction_name block"""
    case_start = match.group(1)
    const_declaration = match.group(2)
    after_declaration = match.group(3)
    if_condition = match.group(4)
    after_condition = match.group(5)
    update_assignment = match.group(6)
    after_assignment = match.group(7)
    case_end = match.group(8)

    # Replace variable name
    fixed_const = const_declaration.replace('trimmedName', 'trimmedCorrectedName')
    fixed_if = if_condition.replace('trimmedName', 'trimmedCorrectedName')
    fixed_assignment = update_assignment.replace('trimmedName', 'trimmedCorrectedName')

    return (case_start + fixed_const + after_declaration +
            fixed_if + after_condition + fixed_assignment +
            after_assignment + case_end)

fixed_code = re.sub(correction_name_pattern, fix_correction_name_block, code, flags=re.DOTALL)

# Verify fix was applied
if 'trimmedCorrectedName' not in fixed_code:
    print("❌ Fix application failed - pattern not found")
    print()
    print("Attempting alternative fix strategy...")
    print()

    # Alternative strategy: Simple string replacement
    # Find the second occurrence of 'const trimmedName' and replace it

    parts = code.split('const trimmedName', 2)
    if len(parts) >= 3:
        # Reconstruct with second occurrence renamed
        fixed_code = parts[0] + 'const trimmedName' + parts[1] + 'const trimmedCorrectedName' + parts[2]

        # Also replace the usage of trimmedName within the correction_name block
        # Find the correction_name case and replace trimmedName references after the declaration
        correction_name_start = fixed_code.find("case 'correction_name':")
        if correction_name_start != -1:
            correction_name_end = fixed_code.find("break;", correction_name_start + len("case 'correction_name':")) + len("break;")
            correction_block = fixed_code[correction_name_start:correction_name_end]

            # Replace trimmedName with trimmedCorrectedName in this block (except the const declaration line)
            lines = correction_block.split('\n')
            fixed_lines = []
            for line in lines:
                if 'const trimmedCorrectedName' in line:
                    fixed_lines.append(line)
                else:
                    fixed_lines.append(line.replace('trimmedName', 'trimmedCorrectedName'))

            fixed_block = '\n'.join(fixed_lines)
            fixed_code = fixed_code[:correction_name_start] + fixed_block + fixed_code[correction_name_end:]

    if 'trimmedCorrectedName' not in fixed_code:
        print("❌ Alternative fix also failed")
        exit(1)

print("✅ Fix applied successfully!")
print()

# Verify no duplicate const declarations remain
const_trimmed_name_count = fixed_code.count('const trimmedName')
const_trimmed_corrected_name_count = fixed_code.count('const trimmedCorrectedName')

print(f"📊 After fix:")
print(f"   'const trimmedName' declarations: {const_trimmed_name_count}")
print(f"   'const trimmedCorrectedName' declarations: {const_trimmed_corrected_name_count}")
print()

if const_trimmed_name_count != 1:
    print(f"⚠️ Warning: Expected 1 'const trimmedName', found {const_trimmed_name_count}")
if const_trimmed_corrected_name_count != 1:
    print(f"⚠️ Warning: Expected 1 'const trimmedCorrectedName', found {const_trimmed_corrected_name_count}")

# Update workflow
workflow['nodes'][state_machine_index]['parameters']['functionCode'] = fixed_code

# Update metadata
workflow['name'] = "WF02: AI Agent V66 CORRECTION STATES COMPLETE (FIXED)"
workflow['meta']['bug_fix'] = 'duplicate_trimmedName_variable'
workflow['meta']['fix_applied_at'] = '2026-03-11'
workflow['meta']['fix_description'] = 'Renamed trimmedName to trimmedCorrectedName in correction_name state'

print("📝 Updating workflow metadata...")
print()

# Save fixed workflow
print(f"💾 Saving fixed V66: {V66_FIXED_PATH}")
with open(V66_FIXED_PATH, 'w', encoding='utf-8') as f:
    json.dump(workflow, f, indent=2, ensure_ascii=False)

fixed_size = V66_FIXED_PATH.stat().st_size
print(f"✅ Saved successfully!")
print(f"   Size: {fixed_size / 1024:.1f} KB")
print()

# Create success report
print("=" * 70)
print("✅ V66 BUG FIX COMPLETE")
print("=" * 70)
print()
print("🐛 Bug: Identifier 'trimmedName' has already been declared [Line 169]")
print()
print("🔧 Fix Applied:")
print("   ✅ Renamed variable in correction_name state to 'trimmedCorrectedName'")
print("   ✅ Updated all references within correction_name state")
print("   ✅ Original collect_name state unchanged")
print()
print("📊 Verification:")
print(f"   'const trimmedName': {const_trimmed_name_count} occurrence (collect_name state)")
print(f"   'const trimmedCorrectedName': {const_trimmed_corrected_name_count} occurrence (correction_name state)")
print()
print("🚀 Next Steps:")
print("   1. Import fixed workflow to n8n:")
print(f"      {V66_FIXED_PATH}")
print("   2. Deactivate old V66 (if imported)")
print("   3. Activate V66 FIXED")
print("   4. Test basic flow: 'oi' → complete → '3' → '1' → new name")
print()
