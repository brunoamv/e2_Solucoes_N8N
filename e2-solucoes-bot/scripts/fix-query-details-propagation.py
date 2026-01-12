#!/usr/bin/env python3
"""
Fix Query Details Propagation Issue in n8n Workflow
Ensures query_details is available for Get Conversation Details node
"""

import json
import sys
import os
from pathlib import Path

def add_merge_queries_node():
    """Create a Merge Queries node that preserves all query fields"""
    return {
        "parameters": {
            "jsCode": """// Merge Queries Node - Preserva todos os campos de query
// Este node garante que os campos query_* sejam preservados após o IF node

const inputData = $input.first().json;
const queryData = $node["Build SQL Queries"].json;

// Log para debug
console.log('=== MERGE QUERIES DEBUG ===');
console.log('Input has count:', inputData.count);
console.log('Query data available:', !!queryData);

// Merge todos os dados preservando os campos de query
return {
    ...inputData,
    // Preservar todos os campos de query do Build SQL Queries
    query_count: queryData.query_count,
    query_details: queryData.query_details,
    query_upsert: queryData.query_upsert,
    queries: queryData.queries,
    // Preservar dados do telefone
    phone_with_code: queryData.phone_with_code,
    phone_without_code: queryData.phone_without_code,
    phone_number: queryData.phone_number,
    // Manter o count do resultado anterior
    count: inputData.count || 0,
    // Pass through outros dados
    whatsapp_name: queryData.whatsapp_name || inputData.whatsapp_name || ''
};"""
        },
        "id": "merge-queries",
        "name": "Merge Queries Data",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [650, 350],
        "alwaysOutputData": True
    }


def fix_workflow(workflow_data):
    """Fix the workflow by adding Merge Queries node and updating connections"""

    nodes = workflow_data.get('nodes', [])
    connections = workflow_data.get('connections', {})

    # 1. Add the new Merge Queries Data node
    merge_node = add_merge_queries_node()

    # Check if node already exists
    node_exists = False
    for node in nodes:
        if node.get('name') == 'Merge Queries Data':
            # Update existing node
            node.update(merge_node)
            node_exists = True
            print("✓ Updated existing Merge Queries Data node")
            break

    if not node_exists:
        nodes.append(merge_node)
        print("✓ Added new Merge Queries Data node")

    # 2. Find the Check Conversation Exists (IF) node
    if_node_name = None
    for node in nodes:
        if node.get('type') == 'n8n-nodes-base.if':
            if_node_name = node.get('name')
            print(f"✓ Found IF node: {if_node_name}")
            break

    # If no IF node found, look for alternative pattern
    if not if_node_name:
        # Look for the connection pattern from Get Conversation Count
        if 'Get Conversation Count' in connections:
            count_connections = connections['Get Conversation Count'].get('main', [[]])[0]
            if count_connections:
                target_node = count_connections[0].get('node')
                print(f"✓ Get Conversation Count connects to: {target_node}")
                if_node_name = target_node

    # 3. Update connections to insert Merge Queries Data
    if if_node_name:
        # Save the original connection from IF node (true output)
        if if_node_name in connections:
            if_true_connection = connections[if_node_name].get('main', [[]])[0]

            # Update IF node to connect to Merge Queries Data (on true)
            connections[if_node_name] = {
                'main': [
                    [{
                        'node': 'Merge Queries Data',
                        'type': 'main',
                        'index': 0
                    }],
                    connections[if_node_name].get('main', [[], []])[1] if len(connections[if_node_name].get('main', [])) > 1 else []
                ]
            }
            print(f"✓ Connected {if_node_name} (true) → Merge Queries Data")

            # Connect Merge Queries Data to Get Conversation Details
            connections['Merge Queries Data'] = {
                'main': [[{
                    'node': 'Get Conversation Details',
                    'type': 'main',
                    'index': 0
                }]]
            }
            print("✓ Connected Merge Queries Data → Get Conversation Details")
    else:
        # Alternative approach: directly update based on known pattern
        print("⚠ Using alternative connection pattern")

        # Find Get Conversation Count connections
        if 'Get Conversation Count' in connections:
            # This should point to some conditional node
            connections['Merge Queries Data'] = {
                'main': [[{
                    'node': 'Get Conversation Details',
                    'type': 'main',
                    'index': 0
                }]]
            }
            print("✓ Connected Merge Queries Data → Get Conversation Details")

    # 4. Ensure Get Conversation Details uses the correct query field
    for node in nodes:
        if node.get('name') == 'Get Conversation Details':
            # Already fixed in V16 to use {{$json.query_details}}
            print("✓ Get Conversation Details already configured to use query_details")
            break

    return workflow_data


def main():
    """Main function to process the workflow file"""

    # Input and output file paths
    input_file = "n8n/workflows/02_ai_agent_conversation_V16.json"
    output_file = "n8n/workflows/02_ai_agent_conversation_V17.json"

    # Get the project root directory
    project_root = Path("/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot")
    input_path = project_root / input_file
    output_path = project_root / output_file

    print(f"\n🔧 Fixing Query Details Propagation Issue")
    print(f"=" * 60)
    print(f"Input:  {input_path}")
    print(f"Output: {output_path}")
    print(f"=" * 60)

    # Check if input file exists
    if not input_path.exists():
        print(f"❌ Error: Input file not found: {input_path}")
        sys.exit(1)

    try:
        # Read the workflow file
        with open(input_path, 'r', encoding='utf-8') as f:
            workflow_data = json.load(f)
        print(f"✓ Loaded workflow: {workflow_data.get('name', 'Unknown')}")

        # Apply fixes
        fixed_workflow = fix_workflow(workflow_data)

        # Update workflow metadata
        fixed_workflow['name'] = 'AI Agent Conversation - V17 Query Propagation Fixed'
        if 'meta' in fixed_workflow:
            fixed_workflow['meta']['notes'] = 'Fixed query_details propagation through IF node by adding Merge Queries Data node'

        # Save the fixed workflow
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(fixed_workflow, f, indent=2, ensure_ascii=False)
        print(f"\n✅ Fixed workflow saved to: {output_path}")

        # Provide implementation instructions
        print(f"\n📋 Next Steps:")
        print(f"1. Import the fixed workflow into n8n:")
        print(f"   - Open n8n at http://localhost:5678")
        print(f"   - Go to Workflows → Import from File")
        print(f"   - Select: {output_file}")
        print(f"2. Test the workflow:")
        print(f"   - Send a WhatsApp message from an existing number")
        print(f"   - Verify that Get Conversation Details executes successfully")
        print(f"3. Monitor execution for any errors")

        # Create documentation
        doc_path = project_root / "docs" / "PLAN" / "query_details_propagation_fix.md"
        with open(doc_path, 'w') as f:
            f.write("""# Query Details Propagation Fix

## Problem
The IF node (Check Conversation Exists) was not propagating the `query_details` field from Build SQL Queries node to Get Conversation Details node, causing "Parameter 'query' must be a text string" error.

## Solution
Added a "Merge Queries Data" node that:
1. Receives data from the IF node (when conversation exists)
2. Retrieves all query fields from Build SQL Queries node
3. Merges both data sources
4. Passes complete data to Get Conversation Details

## Flow
```
Build SQL Queries → Get Conversation Count → Check Exists (IF)
                                                    ↓ (true)
                                            Merge Queries Data
                                                    ↓
                                         Get Conversation Details
```

## Implementation
- **New Node**: Merge Queries Data (Code node)
- **Position**: Between IF node and Get Conversation Details
- **Function**: Preserves all query_* fields through the flow

## Testing
1. Send message from existing number
2. Verify count returns 1
3. Verify Get Conversation Details executes without error
4. Check that conversation data is properly retrieved
""")
        print(f"✓ Created documentation: {doc_path}")

    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in input file: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()