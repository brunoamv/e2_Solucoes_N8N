#!/usr/bin/env python3
"""
V72.1 - Critical Connection Fix

PROBLEM: Validate Appointment Date/Time nodes have NO output connections
RESULT: Validation runs but results never saved → infinite loop

FIX:
1. Validate Appointment Date → Build Update Queries
2. Validate Appointment Time → Build Update Queries

This allows validated data to flow to Postgres and State Machine Logic.

Base: V71_APPOINTMENT_FIX.json
Output: 02_ai_agent_conversation_V72.1_CONNECTION_FIX.json
"""

import json
import sys
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent.parent
V71_FILE = BASE_DIR / "n8n/workflows/02_ai_agent_conversation_V71_APPOINTMENT_FIX.json"
V72_1_FILE = BASE_DIR / "n8n/workflows/02_ai_agent_conversation_V72.1_CONNECTION_FIX.json"

def load_v71():
    """Load V71 workflow"""
    print(f"📂 Loading V71 from: {V71_FILE}")

    if not V71_FILE.exists():
        print(f"❌ V71 file not found: {V71_FILE}")
        sys.exit(1)

    with open(V71_FILE, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    print(f"✅ Loaded V71: {len(workflow['nodes'])} nodes")
    return workflow

def find_node(workflow, node_name):
    """Find node by name"""
    for node in workflow['nodes']:
        if node['name'] == node_name:
            return node
    return None

def fix_validate_date_connection(workflow):
    """Fix 1: Connect Validate Appointment Date → Build Update Queries"""
    print("\n🔧 Fix 1: Validate Appointment Date connection")

    validate_date = find_node(workflow, "Validate Appointment Date")

    if not validate_date:
        print("❌ 'Validate Appointment Date' node not found")
        return False

    # Check current connections
    current = validate_date.get('connections', {})
    print(f"   Current connections: {current}")

    # Add connection to Build Update Queries
    validate_date['connections'] = {
        'main': [[{
            'node': 'Build Update Queries',
            'type': 'main',
            'index': 0
        }]]
    }

    print("   ✅ Connected: Validate Appointment Date → Build Update Queries")
    return True

def fix_validate_time_connection(workflow):
    """Fix 2: Connect Validate Appointment Time → Build Update Queries"""
    print("\n🔧 Fix 2: Validate Appointment Time connection")

    validate_time = find_node(workflow, "Validate Appointment Time")

    if not validate_time:
        print("❌ 'Validate Appointment Time' node not found")
        return False

    # Check current connections
    current = validate_time.get('connections', {})
    print(f"   Current connections: {current}")

    # Add connection to Build Update Queries
    validate_time['connections'] = {
        'main': [[{
            'node': 'Build Update Queries',
            'type': 'main',
            'index': 0
        }]]
    }

    print("   ✅ Connected: Validate Appointment Time → Build Update Queries")
    return True

def update_metadata(workflow):
    """Update workflow metadata to V72.1"""
    print("\n📝 Updating metadata to V72.1")

    workflow['name'] = "02 - AI Agent Conversation V72.1_CONNECTION_FIX"

    if 'meta' not in workflow:
        workflow['meta'] = {}

    workflow['meta']['version'] = 'V72.1'
    workflow['meta']['description'] = 'V72.1 - Critical Connection Fix (Validate Date/Time → Build Update)'
    workflow['meta']['base'] = 'V71_APPOINTMENT_FIX'
    workflow['meta']['fixes'] = [
        'Validate Appointment Date → Build Update Queries',
        'Validate Appointment Time → Build Update Queries'
    ]

    print("   ✅ Metadata updated")

def validate_connections(workflow):
    """Validate that both connections exist"""
    print("\n✔️  Validating connections")

    issues = []

    # Check Validate Date
    validate_date = find_node(workflow, "Validate Appointment Date")
    if validate_date:
        conns = validate_date.get('connections', {}).get('main', [])
        if not conns or len(conns) == 0:
            issues.append("Validate Appointment Date has no connections")
        else:
            target = conns[0][0]['node'] if conns[0] else None
            if target != 'Build Update Queries':
                issues.append(f"Validate Date connects to '{target}', expected 'Build Update Queries'")
    else:
        issues.append("Validate Appointment Date node not found")

    # Check Validate Time
    validate_time = find_node(workflow, "Validate Appointment Time")
    if validate_time:
        conns = validate_time.get('connections', {}).get('main', [])
        if not conns or len(conns) == 0:
            issues.append("Validate Appointment Time has no connections")
        else:
            target = conns[0][0]['node'] if conns[0] else None
            if target != 'Build Update Queries':
                issues.append(f"Validate Time connects to '{target}', expected 'Build Update Queries'")
    else:
        issues.append("Validate Appointment Time node not found")

    # Check Build Update Queries exists
    if not find_node(workflow, "Build Update Queries"):
        issues.append("Build Update Queries node not found (connection target)")

    if issues:
        print("❌ Validation issues:")
        for issue in issues:
            print(f"   - {issue}")
        return False

    print("   ✅ All connections valid")
    return True

def save_v72_1(workflow):
    """Save V72.1 workflow"""
    print(f"\n💾 Saving V72.1 to: {V72_1_FILE}")

    with open(V72_1_FILE, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    size = V72_1_FILE.stat().st_size / 1024
    print(f"   ✅ Saved: {size:.1f} KB")

def main():
    """Generate V72.1 with critical connection fixes"""
    print("=" * 60)
    print("V72.1 - Critical Connection Fix Generator")
    print("=" * 60)

    # Load V71
    workflow = load_v71()

    # Apply fixes
    fix1_ok = fix_validate_date_connection(workflow)
    fix2_ok = fix_validate_time_connection(workflow)

    if not (fix1_ok and fix2_ok):
        print("\n❌ Failed to apply all fixes")
        sys.exit(1)

    # Update metadata
    update_metadata(workflow)

    # Validate
    if not validate_connections(workflow):
        print("\n❌ Validation failed")
        sys.exit(1)

    # Save
    save_v72_1(workflow)

    print("\n" + "=" * 60)
    print("✅ V72.1 GENERATION COMPLETE")
    print("=" * 60)
    print(f"\n📄 Output: {V72_1_FILE}")
    print("\n🔧 Fixes Applied:")
    print("   1. Validate Appointment Date → Build Update Queries")
    print("   2. Validate Appointment Time → Build Update Queries")
    print("\n🎯 Result: Loop resolved - validated data now flows to database")
    print("\n📥 Next Step: Import V72.1 to n8n and test appointment flow")

if __name__ == '__main__':
    main()
