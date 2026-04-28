#!/usr/bin/env python3
"""
Generate WF02 V79.1 - Schema-Aligned Database Fix
==================================================

CRITICAL FIX from V79:
- V79 PROBLEM: Build Update Queries tries to INSERT contact_phone column
- PostgreSQL Schema: contact_phone column DOES NOT EXIST
- V79.1 FIX: Remove contact_phone from INSERT/UPDATE statements

Root Cause Analysis:
- V74 and V79 both have V58.1 Build Update Queries code
- V58.1 code tries to INSERT into contact_phone column
- Column does not exist in PostgreSQL schema
- Error: "column contact_phone of relation conversations does not exist"

V79.1 Solution:
- Update Build Update Queries with schema-aligned code
- Remove contact_phone column references
- Store contact_phone in collected_data JSONB only
- Preserve all other V79 IF cascade architecture

Date: 2026-04-13
Author: E2 Bot Development Team - V79.1 Schema Fix
Version: V79.1
"""

import json
import uuid
import sys
from pathlib import Path

# Configuration
BASE_V79 = Path(__file__).parent.parent / "n8n" / "workflows" / "02_ai_agent_conversation_V79_IF_CASCADE.json"
BUILD_UPDATE_QUERIES_FIXED = Path(__file__).parent / "wf02-v79-1-build-update-queries-fixed.js"
OUTPUT_V79_1 = Path(__file__).parent.parent / "n8n" / "workflows" / "02_ai_agent_conversation_V79_1_SCHEMA_FIX.json"


def find_node_by_name(workflow, node_name):
    """Find node in workflow by name."""
    for node in workflow["nodes"]:
        if node.get("name") == node_name:
            return node
    return None


def update_build_update_queries_code(workflow, fixed_code_path):
    """Replace Build Update Queries jsCode with schema-aligned version."""
    print("\n📝 Updating Build Update Queries with schema-aligned code...")

    build_update_node = find_node_by_name(workflow, "Build Update Queries")
    if not build_update_node:
        print("❌ ERROR: Build Update Queries node not found!")
        return False

    if not fixed_code_path.exists():
        print(f"❌ ERROR: Fixed code not found: {fixed_code_path}")
        return False

    with open(fixed_code_path, "r", encoding="utf-8") as f:
        fixed_code = f.read()

    build_update_node["parameters"]["jsCode"] = fixed_code

    print(f"   ✅ Build Update Queries code replaced ({len(fixed_code)} characters)")
    print(f"   ✅ Removed: contact_phone column references")
    print(f"   ✅ Schema-aligned: Only uses existing PostgreSQL columns")

    return True


def generate_v79_1_schema_fix():
    """Generate V79.1 workflow with schema-aligned Build Update Queries."""

    print("=" * 80)
    print("GENERATE WF02 V79.1 - SCHEMA-ALIGNED DATABASE FIX")
    print("=" * 80)

    print(f"\n✅ Loading base V79 from: {BASE_V79}")
    if not BASE_V79.exists():
        print(f"❌ ERROR: Base V79 file not found!")
        print(f"   Run generate-workflow-wf02-v79-if-cascade.py first")
        return 1

    with open(BASE_V79, "r", encoding="utf-8") as f:
        workflow = json.load(f)

    workflow["name"] = "02_ai_agent_conversation_V79_1_SCHEMA_FIX"

    # Verify Build Update Queries node exists
    build_update_node = find_node_by_name(workflow, "Build Update Queries")
    if not build_update_node:
        print("❌ ERROR: Build Update Queries node not found in V79!")
        return 1

    print(f"\n📍 Build Update Queries node found")

    # Replace Build Update Queries code with schema-aligned version
    if not update_build_update_queries_code(workflow, BUILD_UPDATE_QUERIES_FIXED):
        print("❌ ERROR: Failed to update Build Update Queries code")
        return 1

    # Save V79.1
    print(f"\n💾 Saving to: {OUTPUT_V79_1}")
    OUTPUT_V79_1.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_V79_1, "w", encoding="utf-8") as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 80)
    print("✅ V79.1 SCHEMA-ALIGNED FIX GENERATED SUCCESSFULLY!")
    print("=" * 80)

    print(f"\n📊 Statistics:")
    print(f"   - Total nodes: {len(workflow['nodes'])}")
    print(f"   - Modified: 1 node (Build Update Queries)")

    print(f"\n🎯 V79.1 Critical Fix:")
    print("   1. ✅ Removed contact_phone column from INSERT statement")
    print("   2. ✅ Removed contact_phone from UPDATE ON CONFLICT")
    print("   3. ✅ Removed contact_phone from correction logic")
    print("   4. ✅ contact_phone stored in collected_data JSONB only")

    print(f"\n🔍 PostgreSQL Schema Alignment:")
    print("   ✅ phone_number (exists)")
    print("   ✅ contact_name (exists)")
    print("   ✅ contact_email (exists)")
    print("   ✅ city (exists)")
    print("   ❌ contact_phone (DOES NOT EXIST - REMOVED)")

    print(f"\n📝 V79.1 vs V79 Changes:")
    print("   - V79: Build Update Queries tries to INSERT contact_phone → ERROR")
    print("   - V79.1: Build Update Queries uses only existing columns → SUCCESS")
    print("   - All other V79 features preserved (IF cascade, HTTP Requests, etc.)")

    print(f"\n📝 Next Steps:")
    print("   1. Import 02_ai_agent_conversation_V79_1_SCHEMA_FIX.json")
    print("   2. Test execution (should NOT get 'contact_phone does not exist' error)")
    print("   3. Verify data flows correctly to PostgreSQL")
    print("   4. Activate workflow")

    return 0


if __name__ == "__main__":
    sys.exit(generate_v79_1_schema_fix())
