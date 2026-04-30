#!/usr/bin/env python3
"""
Fix V72 COMPLETE Syntax Error
==============================

BUG: Line 552 has extra closing brace before 'else'
FIX: Remove the '} ' before 'else {' in State 7

Author: Claude Code
Date: 2026-03-18
"""

import json
import sys
from pathlib import Path

def fix_state_7_syntax(workflow_path: str) -> bool:
    """
    Fix syntax error in State 7 (collect_city) where regex replacement
    left an extra closing brace before the else statement.

    Error: Line 552 has '} else {' when it should be 'else {'
    """

    print(f"🔧 V72 COMPLETE Syntax Error Fix")
    print(f"=" * 60)
    print(f"Input: {workflow_path}\n")

    # Read workflow
    try:
        with open(workflow_path, 'r', encoding='utf-8') as f:
            workflow = json.load(f)
    except Exception as e:
        print(f"❌ ERROR: Could not read workflow file: {e}")
        return False

    # Find State Machine Logic node
    state_machine_node = None
    for node in workflow['nodes']:
        if node['name'] == 'State Machine Logic':
            state_machine_node = node
            break

    if not state_machine_node:
        print("❌ ERROR: State Machine Logic node not found")
        return False

    print("✅ Found State Machine Logic node")

    # Get function code
    code = state_machine_node['parameters']['functionCode']
    lines = code.split('\n')

    print(f"   Total lines: {len(lines)}\n")

    # Find the problematic line in State 7
    print("🔍 Analyzing State 7 (collect_city)...\n")

    fixed = False
    for i, line in enumerate(lines):
        # Look for the pattern: "    } else {" with extra closing brace
        # This appears after the if block ends with "    }"
        if i > 0 and '} else {' in line and lines[i-1].strip() == '}':
            print(f"🐛 FOUND ERROR at line {i+1}:")
            print(f"   Line {i}: {lines[i-1]}")
            print(f"   Line {i+1}: {lines[i]} ❌ (extra '}}' before else)")
            print()

            # Fix: Remove the '} ' before 'else {'
            # Original: "    } else {"
            # Fixed:    "    else {"
            lines[i] = line.replace('} else {', 'else {', 1)

            print(f"✅ FIXED:")
            print(f"   Line {i}: {lines[i-1]}")
            print(f"   Line {i+1}: {lines[i]} ✅ (removed extra '}}\')")
            print()

            fixed = True
            break

    if not fixed:
        print("⚠️  WARNING: Could not find expected error pattern")
        print("   Searching for State 7 section...")

        # Find collect_city case
        for i, line in enumerate(lines):
            if 'case \'collect_city\':' in line:
                print(f"\n📍 State 7 starts at line {i+1}")
                print(f"   Showing lines {i+1} to {i+40}:\n")
                for j in range(i, min(i+40, len(lines))):
                    marker = " ❌" if '} else {' in lines[j] else ""
                    print(f"   {j+1:4d} | {lines[j]}{marker}")
                break

        return False

    # Update code
    state_machine_node['parameters']['functionCode'] = '\n'.join(lines)

    # Save fixed workflow
    output_path = workflow_path  # Overwrite original

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(workflow, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Saved fixed workflow to: {output_path}")

        # Validate JSON
        with open(output_path, 'r', encoding='utf-8') as f:
            json.load(f)  # Will raise if invalid

        print(f"✅ JSON syntax validated")

    except Exception as e:
        print(f"❌ ERROR: Could not save fixed workflow: {e}")
        return False

    print(f"\n{'='*60}")
    print(f"✅ V72 COMPLETE SYNTAX ERROR FIXED")
    print(f"{'='*60}\n")

    print("📋 Next Steps:")
    print("   1. Import workflow to n8n: http://localhost:5678")
    print("   2. Navigate to: Workflows → Import from File")
    print("   3. Select: n8n/workflows/02_ai_agent_conversation_V72_COMPLETE.json")
    print("   4. Verify State Machine Logic node has no syntax errors")
    print("   5. Test workflow execution with WhatsApp message")
    print()

    return True


if __name__ == '__main__':
    workflow_path = 'n8n/workflows/02_ai_agent_conversation_V72_COMPLETE.json'

    if not Path(workflow_path).exists():
        print(f"❌ ERROR: Workflow file not found: {workflow_path}")
        sys.exit(1)

    success = fix_state_7_syntax(workflow_path)
    sys.exit(0 if success else 1)
