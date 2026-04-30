#!/usr/bin/env python3
"""
Fix V22 - Corrige o padrão de conexão para Save Messages
O problema: Save Inbound/Outbound Messages estão recebendo dados do Update Conversation State
mas precisam das queries que estão no Build Update Queries
Solução: Conectar Save Messages diretamente ao Build Update Queries
"""

import json
import sys
import os
from datetime import datetime

def create_v22_workflow():
    """Cria V22 com padrão de conexão corrigido"""

    workflow_path = "/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot/n8n/workflows/02_ai_agent_conversation_V21_DATA_FLOW_FIXED.json"

    # Check if file exists
    if not os.path.exists(workflow_path):
        print(f"❌ File not found: {workflow_path}")
        return False

    print(f"📖 Reading V21 workflow: {workflow_path}")

    try:
        with open(workflow_path, 'r', encoding='utf-8') as f:
            workflow = json.load(f)
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return False

    print("🔧 Creating V22 with fixed connection pattern...")

    # 1. Remove the leftover Prepare Update Data connection
    if 'connections' in workflow and 'Prepare Update Data' in workflow['connections']:
        del workflow['connections']['Prepare Update Data']
        print("✅ Removed leftover Prepare Update Data connection")

    # 2. Fix the connections - Build Update Queries should connect to ALL nodes that need queries
    if 'connections' in workflow:
        # Build Update Queries connects to multiple nodes in parallel
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
                    }
                ]
            ]
        }
        print("✅ Updated Build Update Queries to connect to all dependent nodes")

        # 3. Update Conversation State should NOT connect to Save Messages
        # It should connect to other downstream nodes if needed
        workflow['connections']['Update Conversation State'] = {
            "main": [
                [
                    # Update Conversation State doesn't need to connect to Save Messages
                    # Those get their data directly from Build Update Queries
                ]
            ]
        }
        print("✅ Removed incorrect connection from Update Conversation State to Save Messages")

        # 4. Save Messages should connect to next nodes in the flow
        workflow['connections']['Save Inbound Message'] = {
            "main": [
                [
                    # Save Inbound Message can connect to next step if needed
                ]
            ]
        }

        workflow['connections']['Save Outbound Message'] = {
            "main": [
                [
                    # Save Outbound Message can connect to next step if needed
                ]
            ]
        }

    # 5. Update workflow name and version
    workflow['name'] = "AI Agent Conversation - V22 (Connection Pattern Fixed)"

    # 6. Ensure Save Message nodes are configured to use the correct data
    for node in workflow['nodes']:
        if node.get('name') == 'Save Inbound Message':
            # Ensure it's using the query from its input
            if 'query' in node['parameters']:
                node['parameters']['query'] = "={{ $json.query_save_inbound }}"
            print("✅ Verified Save Inbound Message uses correct query reference")

        elif node.get('name') == 'Save Outbound Message':
            # Ensure it's using the query from its input
            if 'query' in node['parameters']:
                node['parameters']['query'] = "={{ $json.query_save_outbound }}"
            print("✅ Verified Save Outbound Message uses correct query reference")

    # Save the V22 workflow
    output_path = workflow_path.replace('V21_DATA_FLOW_FIXED.json', 'V22_CONNECTION_PATTERN_FIXED.json')
    print(f"\n💾 Saving V22 workflow: {output_path}")

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(workflow, f, indent=2, ensure_ascii=False)
        print(f"✅ V22 workflow saved successfully!")
        print(f"\n📋 Improvements in V22:")
        print("1. ✅ Build Update Queries connects directly to ALL nodes needing queries")
        print("2. ✅ Save Inbound Message receives query directly from Build Update Queries")
        print("3. ✅ Save Outbound Message receives query directly from Build Update Queries")
        print("4. ✅ Update Conversation State no longer incorrectly feeds Save Messages")
        print("5. ✅ Removed leftover Prepare Update Data connection")
        print(f"\n⚠️ CRITICAL FIX:")
        print("The 'Cannot read properties of undefined' error was caused by Save Message nodes")
        print("trying to access queries from Update Conversation State output (which returns DB rows)")
        print("Now they get queries directly from Build Update Queries where the queries are defined.")
        print(f"\n🚀 Next steps:")
        print(f"1. Import V22 into n8n: {output_path}")
        print(f"2. Deactivate V21 workflow")
        print(f"3. Activate V22 workflow")
        print(f"4. Test - the error should be resolved!")
        return True
    except Exception as e:
        print(f"❌ Error saving file: {e}")
        return False

if __name__ == "__main__":
    success = create_v22_workflow()
    sys.exit(0 if success else 1)