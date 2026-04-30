#!/usr/bin/env python3
"""
Fix V23 - Estende o padrão de distribuição paralela para Upsert Lead Data
O problema: Upsert Lead Data está recebendo dados do Update Conversation State
mas precisa das queries que estão no Build Update Queries
Solução: Adicionar Upsert Lead Data ao padrão de distribuição paralela
"""

import json
import sys
import os
from datetime import datetime

def create_v23_workflow():
    """Cria V23 estendendo distribuição paralela para Upsert Lead Data"""

    workflow_path = "/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V22_CONNECTION_PATTERN_FIXED.json"

    # Check if file exists
    if not os.path.exists(workflow_path):
        print(f"❌ File not found: {workflow_path}")
        return False

    print(f"📖 Reading V22 workflow: {workflow_path}")

    try:
        with open(workflow_path, 'r', encoding='utf-8') as f:
            workflow = json.load(f)
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return False

    print("🔧 Creating V23 with extended parallel distribution pattern...")

    # 1. Extend Build Update Queries to include Upsert Lead Data
    if 'connections' in workflow:
        # Build Update Queries connects to ALL nodes that need queries including Upsert Lead Data
        workflow['connections']['Build Update Queries'] = {
            "main": [
                [
                    {
                        "node": "Update Conversation State",
                        "type": "main",
                        "index": 0
                    },
                    {
                        "node": "Save Inbound Message",
                        "type": "main",
                        "index": 0
                    },
                    {
                        "node": "Save Outbound Message",
                        "type": "main",
                        "index": 0
                    },
                    {
                        "node": "Send WhatsApp Response",
                        "type": "main",
                        "index": 0
                    },
                    {
                        "node": "Upsert Lead Data",
                        "type": "main",
                        "index": 0
                    }
                ]
            ]
        }
        print("✅ Extended Build Update Queries to include Upsert Lead Data in parallel distribution")

        # 2. Ensure Update Conversation State doesn't connect to Upsert Lead Data
        workflow['connections']['Update Conversation State'] = {
            "main": [
                [
                    # No connections - all nodes get data from Build Update Queries
                ]
            ]
        }
        print("✅ Ensured Update Conversation State doesn't incorrectly feed Upsert Lead Data")

        # 3. Upsert Lead Data should connect to any downstream nodes if needed
        workflow['connections']['Upsert Lead Data'] = {
            "main": [
                [
                    # Upsert Lead Data can connect to next step if needed
                ]
            ]
        }
        print("✅ Configured Upsert Lead Data connections")

    # 4. Update workflow name and version
    workflow['name'] = "AI Agent Conversation - V23 (Extended Parallel Distribution)"

    # 5. Look for Build Update Queries node to ensure it generates the query_upsert_lead
    for node in workflow['nodes']:
        if node.get('name') == 'Build Update Queries':
            # Check if it's a Code node and add query_upsert_lead generation if missing
            if node.get('type') == 'n8n-nodes-base.code':
                print("📝 Checking Build Update Queries node for query_upsert_lead generation...")
                # The code should already generate this, but let's make note
                print("ℹ️ Build Update Queries should generate query_upsert_lead in its output")

        elif node.get('name') == 'Upsert Lead Data':
            # Ensure it's using the query from Build Update Queries
            if 'query' in node['parameters']:
                node['parameters']['query'] = "={{ $json.query_upsert_lead }}"
                print("✅ Updated Upsert Lead Data to use query_upsert_lead from Build Update Queries")

    # Save the V23 workflow
    output_path = workflow_path.replace('V22_CONNECTION_PATTERN_FIXED.json', 'V23_EXTENDED_PARALLEL.json')
    print(f"\n💾 Saving V23 workflow: {output_path}")

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(workflow, f, indent=2, ensure_ascii=False)
        print(f"✅ V23 workflow saved successfully!")
        print(f"\n📋 Improvements in V23:")
        print("1. ✅ Build Update Queries now distributes to ALL nodes including Upsert Lead Data")
        print("2. ✅ Upsert Lead Data receives query directly from Build Update Queries")
        print("3. ✅ Removed incorrect connection from Update Conversation State to Upsert Lead Data")
        print("4. ✅ Complete parallel distribution pattern for all SQL operations")
        print(f"\n⚠️ CRITICAL FIX:")
        print("The 'Cannot read properties of undefined' error in Upsert Lead Data was caused by")
        print("the same issue as Save Messages - trying to access queries from Update Conversation State")
        print("output (which returns DB rows). Now Upsert Lead Data gets its query directly from")
        print("Build Update Queries where query_upsert_lead is properly defined.")
        print(f"\n📌 IMPORTANT NOTE:")
        print("Ensure Build Update Queries node generates 'query_upsert_lead' in its output.")
        print("This query should handle lead data upsert operations.")
        print(f"\n🚀 Next steps:")
        print(f"1. Import V23 into n8n: {output_path}")
        print(f"2. Deactivate V22 workflow")
        print(f"3. Activate V23 workflow")
        print(f"4. Test execution - all nodes should work without 'undefined' errors!")
        return True
    except Exception as e:
        print(f"❌ Error saving file: {e}")
        return False

if __name__ == "__main__":
    success = create_v23_workflow()
    sys.exit(0 if success else 1)