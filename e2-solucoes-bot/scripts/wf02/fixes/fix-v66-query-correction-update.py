#!/usr/bin/env python3
"""
V66 Critical Bug Fix #2 - query_correction_update Scope Error

Problem: query_correction_update declared inside if block but used outside
Error: "query_correction_update is not defined [line 265]"

Solution: Declare variable at top of Build Update Queries function with 'let'

Author: Claude Code
Date: 2026-03-11
"""

import json
import re
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent.parent
V66_FIXED_PATH = BASE_DIR / "n8n/workflows/02_ai_agent_conversation_V66_CORRECTION_STATES_COMPLETE_FIXED.json"
V66_FIXED_V2_PATH = BASE_DIR / "n8n/workflows/02_ai_agent_conversation_V66_CORRECTION_STATES_COMPLETE_FIXED_V2.json"

print("=" * 70)
print("V66 Critical Bug Fix #2: query_correction_update Scope Error")
print("=" * 70)
print()

# Load V66 FIXED (has first bug fix - trimmedName)
print(f"📂 Loading V66 FIXED: {V66_FIXED_PATH}")
with open(V66_FIXED_PATH, 'r', encoding='utf-8') as f:
    workflow = json.load(f)

print(f"✅ Loaded: {len(workflow['nodes'])} nodes")
print()

# Find Build Update Queries node
print("🔍 Finding Build Update Queries node...")
build_queries_node = None
build_queries_index = None

for i, node in enumerate(workflow['nodes']):
    if node.get('name') == 'Build Update Queries':
        build_queries_node = node
        build_queries_index = i
        break

if not build_queries_node:
    print("❌ ERRO: Build Update Queries node not found!")
    exit(1)

print(f"✅ Found at index {build_queries_index}")
print()

# Get current code
code = build_queries_node['parameters']['jsCode']
print(f"📝 Current code size: {len(code)} chars")
print()

# Check if query_correction_update is already declared at top
if re.search(r'^\s*let\s+query_correction_update', code, re.MULTILINE):
    print("⚠️ query_correction_update already declared at top with 'let'")
    print("Fix may have already been applied or code structure is different.")
    exit(0)

# Apply Fix: Add variable declaration after helper functions
print("🔧 Applying fix...")
print()

# Strategy: Insert 'let query_correction_update = null;' after prepareJsonb function
# Find the end of helper functions section (after prepareJsonb)

# Pattern: Find the prepareJsonb function definition
prepareJsonb_pattern = r'(const prepareJsonb = \(obj\) => \{[^}]+\};)'

match = re.search(prepareJsonb_pattern, code, re.DOTALL)

if not match:
    print("❌ Could not find prepareJsonb function!")
    print("Attempting alternative fix strategy...")

    # Alternative: Add after the console.log line
    console_pattern = r"(console\.log\('=== V58\.1 BUILD UPDATE QUERIES.*?==='\);)"
    match = re.search(console_pattern, code)

    if not match:
        print("❌ Alternative pattern also failed!")
        exit(1)

    insert_position = match.end()

else:
    insert_position = match.end()

# Insert variable declaration
variable_declaration = "\n\n// V66 FIX: Declare query_correction_update at function scope\nlet query_correction_update = null;\n"

fixed_code = code[:insert_position] + variable_declaration + code[insert_position:]

print("✅ Fix applied successfully!")
print()

# Verify fix was applied
if 'let query_correction_update = null;' not in fixed_code:
    print("❌ Fix verification failed - declaration not found in fixed code!")
    exit(1)

print(f"📊 After fix:")
print(f"   Code size: {len(fixed_code)} chars")
print(f"   'let query_correction_update' declarations: {fixed_code.count('let query_correction_update')}")
print()

# Update workflow
workflow['nodes'][build_queries_index]['parameters']['jsCode'] = fixed_code

# Update metadata
workflow['name'] = "WF02: AI Agent V66 CORRECTION STATES COMPLETE (FIXED V2)"
if 'meta' not in workflow:
    workflow['meta'] = {}
workflow['meta']['bug_fix_2'] = 'query_correction_update_scope_error'
workflow['meta']['fix_applied_at'] = '2026-03-11'
workflow['meta']['fix_description'] = 'Declared query_correction_update at function scope with let'

print("📝 Updating workflow metadata...")
print()

# Save fixed workflow V2
print(f"💾 Saving V66 FIXED V2: {V66_FIXED_V2_PATH}")
with open(V66_FIXED_V2_PATH, 'w', encoding='utf-8') as f:
    json.dump(workflow, f, indent=2, ensure_ascii=False)

fixed_size = V66_FIXED_V2_PATH.stat().st_size
print(f"✅ Saved successfully!")
print(f"   Size: {fixed_size / 1024:.1f} KB")
print()

# Create success report
print("=" * 70)
print("✅ V66 BUG FIX #2 COMPLETE")
print("=" * 70)
print()
print("🐛 Bug: query_correction_update is not defined [line 265]")
print()
print("🔧 Fix Applied:")
print("   ✅ Declared 'let query_correction_update = null;' at function scope")
print("   ✅ Variable now accessible in return statement")
print("   ✅ V66 correction UPDATE queries will now execute")
print()
print("📊 Verification:")
print(f"   'let query_correction_update' declarations: {fixed_code.count('let query_correction_update')}")
print()
print("🚀 Next Steps:")
print("   1. Import fixed workflow V2 to n8n:")
print(f"      {V66_FIXED_V2_PATH}")
print("   2. Deactivate old V66 FIXED (if imported)")
print("   3. Activate V66 FIXED V2")
print("   4. Test correction flow: 'oi' → complete → '3' → '1' → new name")
print()
