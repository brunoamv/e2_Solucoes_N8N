#!/usr/bin/env python3
"""
Fix PostgreSQL Query Interpolation in n8n Workflow
Resolves the issue where n8n doesn't properly process JavaScript interpolation in SQL queries
"""

import json
import sys
import os
from pathlib import Path

def create_build_sql_queries_node():
    """Create the Build SQL Queries node that prepares all SQL queries"""
    return {
        "parameters": {
            "jsCode": """// Build SQL Queries Node - Prepara todas as queries SQL
// Recebe dados do node anterior
const data = $input.first().json;
const phone_with_code = data.phone_with_code || '';
const phone_without_code = data.phone_without_code || '';

// Validação de segurança
if (!phone_with_code || !phone_without_code) {
  throw new Error('Phone numbers not properly formatted');
}

// Escape simples para SQL injection
const escapeSql = (str) => {
  return String(str).replace(/'/g, "''");
};

// Construir queries SQL
const queries = {
  // Query para contar conversas existentes
  count: `
    SELECT COUNT(*) as count
    FROM conversations
    WHERE phone_number IN ('${escapeSql(phone_with_code)}', '${escapeSql(phone_without_code)}')
  `,

  // Query para buscar detalhes da conversa
  details: `
    SELECT
      *,
      COALESCE(state_machine_state,
        CASE current_state
          WHEN 'novo' THEN 'greeting'
          WHEN 'identificando_servico' THEN 'service_selection'
          WHEN 'coletando_dados' THEN 'collect_name'
          WHEN 'agendando' THEN 'scheduling'
          WHEN 'handoff_comercial' THEN 'handoff_comercial'
          WHEN 'concluido' THEN 'completed'
          ELSE 'greeting'
        END
      ) as state_for_machine
    FROM conversations
    WHERE phone_number IN ('${escapeSql(phone_with_code)}', '${escapeSql(phone_without_code)}')
    ORDER BY updated_at DESC
    LIMIT 1
  `,

  // Query para criar/atualizar conversa
  upsert: `
    -- Limpar duplicatas antigas
    DELETE FROM conversations
    WHERE phone_number = '${escapeSql(phone_without_code)}'
      AND phone_number != '${escapeSql(phone_with_code)}';

    -- Inserir ou atualizar
    INSERT INTO conversations (
      phone_number,
      whatsapp_name,
      current_state,
      state_machine_state,
      created_at,
      updated_at
    )
    VALUES (
      '${escapeSql(phone_with_code)}',
      '${escapeSql(data.whatsapp_name || '')}',
      'novo',
      'greeting',
      NOW(),
      NOW()
    )
    ON CONFLICT (phone_number)
    DO UPDATE SET
      whatsapp_name = EXCLUDED.whatsapp_name,
      updated_at = NOW(),
      current_state = CASE
        WHEN conversations.current_state = 'concluido' THEN 'novo'
        ELSE conversations.current_state
      END,
      state_machine_state = CASE
        WHEN conversations.state_machine_state = 'completed' THEN 'greeting'
        ELSE conversations.state_machine_state
      END
    RETURNING *
  `
};

// Log para debug
console.log('=== BUILD SQL QUERIES ===');
console.log('Phone with code:', phone_with_code);
console.log('Phone without code:', phone_without_code);
console.log('Queries built successfully');

// Retornar dados + queries
return {
  ...data,
  queries: queries,
  query_count: queries.count,
  query_details: queries.details,
  query_upsert: queries.upsert
};"""
        },
        "id": "build-sql-queries",
        "name": "Build SQL Queries",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [-750, 250],
        "alwaysOutputData": True
    }


def fix_workflow(workflow_data):
    """Fix the workflow by adding Build SQL Queries node and updating connections"""

    nodes = workflow_data.get('nodes', [])
    connections = workflow_data.get('connections', {})

    # 1. Add the new Build SQL Queries node
    build_sql_node = create_build_sql_queries_node()

    # Check if node already exists
    node_exists = False
    for node in nodes:
        if node.get('name') == 'Build SQL Queries':
            # Update existing node
            node.update(build_sql_node)
            node_exists = True
            print("✓ Updated existing Build SQL Queries node")
            break

    if not node_exists:
        nodes.append(build_sql_node)
        print("✓ Added new Build SQL Queries node")

    # 2. Update PostgreSQL nodes to use the prepared queries
    for node in nodes:
        if node.get('type') == 'n8n-nodes-base.postgres':
            node_name = node.get('name', '')

            # Update Get Conversation Count
            if 'Get Conversation Count' in node_name or node.get('id') == 'node_get_conversation':
                node['parameters']['query'] = "={{$json.query_count}}"
                print(f"✓ Updated query in {node_name}")

            # Update Get Conversation Details
            elif 'Get Conversation Details' in node_name or node.get('id') == 'node_get_conversation_details':
                node['parameters']['query'] = "={{$json.query_details}}"
                print(f"✓ Updated query in {node_name}")

            # Update Create New Conversation
            elif 'Create New Conversation' in node_name or node.get('id') == 'node_create_conversation':
                node['parameters']['query'] = "={{$json.query_upsert}}"
                print(f"✓ Updated query in {node_name}")

    # 3. Update connections to insert Build SQL Queries between Prepare Phone Formats and Get Conversation Count
    if 'Prepare Phone Formats' in connections:
        # Save original connection from Prepare Phone Formats
        original_connection = connections.get('Prepare Phone Formats', {}).get('main', [[]])[0]

        # Update Prepare Phone Formats to connect to Build SQL Queries
        connections['Prepare Phone Formats'] = {
            'main': [[{
                'node': 'Build SQL Queries',
                'type': 'main',
                'index': 0
            }]]
        }
        print("✓ Connected Prepare Phone Formats → Build SQL Queries")

        # Connect Build SQL Queries to Get Conversation Count
        if original_connection:
            connections['Build SQL Queries'] = {
                'main': [[original_connection[0]]]
            }
            print("✓ Connected Build SQL Queries → Get Conversation Count")

    # 4. Ensure all nodes that use phone data go through Build SQL Queries
    for conn_name, conn_data in connections.items():
        if 'Get Conversation' in conn_name or 'Create New Conversation' in conn_name:
            # These should now receive data from Build SQL Queries or later in the chain
            pass

    return workflow_data


def main():
    """Main function to process the workflow file"""

    # Input and output file paths
    input_file = "n8n/workflows/02_ai_agent_conversation_V15.json"
    output_file = "n8n/workflows/02_ai_agent_conversation_V16.json"

    # Get the project root directory
    project_root = Path("/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot")
    input_path = project_root / input_file
    output_path = project_root / output_file

    print(f"\n🔧 Fixing PostgreSQL Query Interpolation Issue")
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
        fixed_workflow['name'] = fixed_workflow.get('name', 'AI Agent Conversation') + ' - V16 Fixed Queries'
        if 'meta' in fixed_workflow:
            fixed_workflow['meta']['notes'] = 'Fixed PostgreSQL query interpolation by adding Build SQL Queries node'

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
        print(f"2. Test the workflow with a WhatsApp message")
        print(f"3. Check the execution to verify queries are working")
        print(f"4. Monitor logs for any errors")

        # Create a validation script
        validation_script = project_root / "scripts" / "validate-postgres-fix.sh"
        with open(validation_script, 'w') as f:
            f.write("""#!/bin/bash
# Validate PostgreSQL Query Fix

echo "🔍 Validating PostgreSQL Query Fix..."
echo "=================================="

# Check if workflow file exists
if [ -f "n8n/workflows/02_ai_agent_conversation_V16.json" ]; then
    echo "✓ Workflow V16 file exists"
else
    echo "❌ Workflow V16 file not found"
    exit 1
fi

# Check for Build SQL Queries node
if grep -q "Build SQL Queries" n8n/workflows/02_ai_agent_conversation_V16.json; then
    echo "✓ Build SQL Queries node present"
else
    echo "❌ Build SQL Queries node not found"
    exit 1
fi

# Check for query_count usage
if grep -q "query_count" n8n/workflows/02_ai_agent_conversation_V16.json; then
    echo "✓ query_count field is being used"
else
    echo "❌ query_count field not found"
    exit 1
fi

# Check for query_details usage
if grep -q "query_details" n8n/workflows/02_ai_agent_conversation_V16.json; then
    echo "✓ query_details field is being used"
else
    echo "❌ query_details field not found"
    exit 1
fi

# Check for query_upsert usage
if grep -q "query_upsert" n8n/workflows/02_ai_agent_conversation_V16.json; then
    echo "✓ query_upsert field is being used"
else
    echo "❌ query_upsert field not found"
    exit 1
fi

echo ""
echo "✅ All validations passed!"
echo ""
echo "📋 To import into n8n:"
echo "1. Open http://localhost:5678"
echo "2. Go to Workflows → Import"
echo "3. Select file: n8n/workflows/02_ai_agent_conversation_V16.json"
""")
        os.chmod(validation_script, 0o755)
        print(f"\n✓ Created validation script: {validation_script}")

    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in input file: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()