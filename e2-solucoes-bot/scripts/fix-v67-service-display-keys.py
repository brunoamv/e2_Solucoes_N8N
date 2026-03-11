#!/usr/bin/env python3
"""
V67 Service Display Keys Fix

Problem: serviceDisplay keys don't match serviceMapping values
Error: Service field shows "Não informado" despite user selecting service

Solution: Fix serviceDisplay object keys to match serviceMapping values

Author: Claude Code
Date: 2026-03-11
"""

import json
import re
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent.parent
V66_FIXED_V2_PATH = BASE_DIR / "n8n/workflows/02_ai_agent_conversation_V66_CORRECTION_STATES_COMPLETE_FIXED_V2.json"
V67_PATH = BASE_DIR / "n8n/workflows/02_ai_agent_conversation_V67_SERVICE_DISPLAY_FIX.json"

print("=" * 70)
print("V67 Service Display Keys Fix")
print("=" * 70)
print()

# Load V66 FIXED V2
print(f"📂 Loading V66 FIXED V2: {V66_FIXED_V2_PATH}")
with open(V66_FIXED_V2_PATH, 'r', encoding='utf-8') as f:
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

# Apply Fix: Replace serviceDisplay keys
print("🔧 Applying fix: Update serviceDisplay keys...")
print()

# Define the fix replacement
# BEFORE (V66 - WRONG KEYS):
# const serviceDisplay = {
#   'solar': { emoji: '☀️', name: 'Energia Solar' },
#   'subestacao': { emoji: '⚡', name: 'Subestações' },
#   'projetos': { emoji: '📐', name: 'Projetos Elétricos' },
#   'bess': { emoji: '🔋', name: 'BESS (Armazenamento de Energia)' },
#   'analise': { emoji: '📊', name: 'Análise de Consumo' }
# };

# AFTER (V67 - CORRECT KEYS):
# const serviceDisplay = {
#   'energia_solar': { emoji: '☀️', name: 'Energia Solar' },
#   'subestacao': { emoji: '⚡', name: 'Subestações' },
#   'projeto_eletrico': { emoji: '📐', name: 'Projetos Elétricos' },
#   'armazenamento_energia': { emoji: '🔋', name: 'BESS (Armazenamento de Energia)' },
#   'analise_laudo': { emoji: '📊', name: 'Análise e Laudos' }
# };

# Strategy: Find and replace the entire serviceDisplay object
old_service_display = """// Service emoji and name mapping
const serviceDisplay = {
  'solar': { emoji: '☀️', name: 'Energia Solar' },
  'subestacao': { emoji: '⚡', name: 'Subestações' },
  'projetos': { emoji: '📐', name: 'Projetos Elétricos' },
  'bess': { emoji: '🔋', name: 'BESS (Armazenamento de Energia)' },
  'analise': { emoji: '📊', name: 'Análise de Consumo' }
};"""

new_service_display = """// Service emoji and name mapping (V67 FIX: Keys match serviceMapping values)
const serviceDisplay = {
  'energia_solar': { emoji: '☀️', name: 'Energia Solar' },
  'subestacao': { emoji: '⚡', name: 'Subestações' },
  'projeto_eletrico': { emoji: '📐', name: 'Projetos Elétricos' },
  'armazenamento_energia': { emoji: '🔋', name: 'BESS (Armazenamento de Energia)' },
  'analise_laudo': { emoji: '📊', name: 'Análise e Laudos' }
};"""

# Check if old pattern exists
if old_service_display not in code:
    print("⚠️ Warning: Could not find exact serviceDisplay pattern")
    print("Attempting alternative strategy...")

    # Alternative: Use regex to find and replace
    # Find the serviceDisplay object with flexible whitespace
    pattern = r"(// Service emoji and name mapping\s*\nconst serviceDisplay = \{[^}]+\};)"

    match = re.search(pattern, code, re.DOTALL)

    if not match:
        print("❌ Alternative pattern also failed!")
        print("Showing relevant code section:")
        # Find approximate location
        service_display_loc = code.find("const serviceDisplay")
        if service_display_loc != -1:
            print(code[service_display_loc:service_display_loc+500])
        exit(1)

    # Replace using regex match
    fixed_code = code[:match.start()] + new_service_display + code[match.end():]
else:
    # Direct replacement
    fixed_code = code.replace(old_service_display, new_service_display)

print("✅ Fix applied successfully!")
print()

# Verify fix was applied
verification_checks = [
    ("'energia_solar'", "Service 1 key (was 'solar')"),
    ("'subestacao'", "Service 2 key (unchanged)"),
    ("'projeto_eletrico'", "Service 3 key (was 'projetos')"),
    ("'armazenamento_energia'", "Service 4 key (was 'bess')"),
    ("'analise_laudo'", "Service 5 key (was 'analise')")
]

print("🔍 Verification:")
all_checks_passed = True
for check_str, description in verification_checks:
    if check_str in fixed_code:
        print(f"   ✅ {description}")
    else:
        print(f"   ❌ {description} NOT FOUND")
        all_checks_passed = False

print()

if not all_checks_passed:
    print("❌ Verification failed - not all keys were updated correctly!")
    exit(1)

# Verify old keys are gone (except in comments/debug)
old_keys = ["'solar':", "'projetos':", "'bess':", "'analise':"]
print("🔍 Checking old keys removed:")
for old_key in old_keys:
    # Count occurrences in serviceDisplay context
    if f"{old_key} {{ emoji:" in fixed_code:
        print(f"   ❌ Old key still present: {old_key}")
        all_checks_passed = False
    else:
        print(f"   ✅ Old key removed: {old_key}")

print()

if not all_checks_passed:
    print("❌ Old keys still present in code!")
    exit(1)

print(f"📊 After fix:")
print(f"   Code size: {len(fixed_code)} chars")
print(f"   Size change: {len(fixed_code) - len(code):+d} chars")
print()

# Update workflow
workflow['nodes'][state_machine_index]['parameters']['functionCode'] = fixed_code

# Update metadata
workflow['name'] = "WF02: AI Agent V67 SERVICE DISPLAY FIX"
if 'meta' not in workflow:
    workflow['meta'] = {}
workflow['meta']['version'] = 'V67'
workflow['meta']['fix_applied'] = 'service_display_keys'
workflow['meta']['fix_date'] = '2026-03-11'
workflow['meta']['fix_description'] = 'Fixed serviceDisplay keys to match serviceMapping values (energia_solar, projeto_eletrico, armazenamento_energia, analise_laudo)'
workflow['meta']['preserves_v66_fixes'] = True
workflow['meta']['v66_fix_1'] = 'trimmedCorrectedName (duplicate variable)'
workflow['meta']['v66_fix_2'] = 'query_correction_update (scope error)'

print("📝 Updating workflow metadata...")
print()

# Save V67 workflow
print(f"💾 Saving V67: {V67_PATH}")
with open(V67_PATH, 'w', encoding='utf-8') as f:
    json.dump(workflow, f, indent=2, ensure_ascii=False)

fixed_size = V67_PATH.stat().st_size
print(f"✅ Saved successfully!")
print(f"   Size: {fixed_size / 1024:.1f} KB")
print()

# Create success report
print("=" * 70)
print("✅ V67 SERVICE DISPLAY FIX COMPLETE")
print("=" * 70)
print()
print("🐛 Bug: Service field shows 'Não informado' despite user selection")
print()
print("🔧 Fix Applied:")
print("   ✅ serviceDisplay keys now match serviceMapping values")
print("   ✅ 'solar' → 'energia_solar'")
print("   ✅ 'projetos' → 'projeto_eletrico'")
print("   ✅ 'bess' → 'armazenamento_energia'")
print("   ✅ 'analise' → 'analise_laudo'")
print("   ✅ 'subestacao' unchanged (already correct)")
print()
print("📊 Preserved V66 Fixes:")
print("   ✅ Bug #1: trimmedCorrectedName (duplicate variable)")
print("   ✅ Bug #2: query_correction_update (scope error)")
print()
print("🧪 Test Requirements:")
print("   Service 1: Should show '☀️ Serviço: Energia Solar'")
print("   Service 2: Should show '⚡ Serviço: Subestações'")
print("   Service 3: Should show '📐 Serviço: Projetos Elétricos'")
print("   Service 4: Should show '🔋 Serviço: BESS (Armazenamento de Energia)'")
print("   Service 5: Should show '📊 Serviço: Análise e Laudos'")
print()
print("🚀 Next Steps:")
print("   1. Import V67 to n8n:")
print(f"      {V67_PATH}")
print("   2. Test all 5 services (especially 1, 3, 4, 5)")
print("   3. Verify service display in confirmation messages")
print("   4. Deploy V67 to production")
print()
