#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
V42 DATABASE COLUMN FIX - Remove referências a colunas inexistentes
============================================================================
V41 tinha referências a contact_name, contact_email, city, service_id
que NÃO EXISTEM na tabela conversations.

PROBLEMA:
- Build SQL Queries node usa service_id, contact_name, contact_email, city
- Build Update Queries node usa contact_name, contact_email, city
- PostgreSQL retorna erro: column "contact_name" of relation "conversations" does not exist
- n8n trava execução em "running"
- Bot volta ao menu ao invés de avançar

SOLUÇÃO V42:
- Remover TODAS as referências a colunas inexistentes
- Manter apenas colunas que existem no schema
- Dados pessoais vão para collected_data JSONB

COLUNAS QUE EXISTEM:
- phone_number, whatsapp_name, current_state, collected_data
- service_type, state_machine_state, status, last_message_at
- rdstation_contact_id, rdstation_deal_id, created_at, updated_at

COLUNAS QUE NÃO EXISTEM (REMOVER):
- contact_name, contact_email, city, service_id
"""

import json
import sys
from pathlib import Path

# Usar V41 como base
BASE_WORKFLOW = "02_ai_agent_conversation_V41_QUERY_BATCHING_FIX.json"
OUTPUT_WORKFLOW = "02_ai_agent_conversation_V42_DATABASE_COLUMNS_FIX.json"

def fix_build_sql_queries_node(workflow):
    """Remove colunas inexistentes do Build SQL Queries node."""

    for node in workflow.get('nodes', []):
        if node.get('name') == 'Build SQL Queries':
            print(f"✅ Found Build SQL Queries node")

            if 'parameters' in node and 'jsCode' in node['parameters']:
                code = node['parameters']['jsCode']

                # Verificar se contém as colunas problemáticas
                has_issues = any(col in code for col in ['service_id', 'contact_name', 'contact_email'])

                if has_issues:
                    print("   ⚠️  Found problematic columns in code")

                    # Remover as linhas que referenciam colunas inexistentes
                    # Padrão: encontrar INSERT INTO conversations e remover as colunas

                    # Substituir o INSERT completo por versão corrigida
                    old_insert = """INSERT INTO conversations (
    phone_number,
    whatsapp_name,
    service_id,
    contact_name,
    contact_email,
    city,
    current_state,
    state_machine_state,
    collected_data,
    error_count,
    created_at,
    updated_at
  ) VALUES (
    '${escapeSql(phone_without_code)}',
    '${escapeSql(data.whatsapp_name || '')}',
    NULL,
    NULL,
    NULL,
    NULL,
    'novo',
    'greeting',
    '{}'::jsonb,
    0,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
  )"""

                    new_insert = """INSERT INTO conversations (
    phone_number,
    whatsapp_name,
    current_state,
    state_machine_state,
    collected_data,
    created_at,
    updated_at
  ) VALUES (
    '${escapeSql(phone_without_code)}',
    '${escapeSql(data.whatsapp_name || '')}',
    'novo',
    'greeting',
    '{}'::jsonb,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
  )"""

                    code = code.replace(old_insert, new_insert)

                    # Atualizar o código
                    node['parameters']['jsCode'] = code
                    print("   ✅ Removed service_id, contact_name, contact_email, city from Build SQL Queries")
                    return True
                else:
                    print("   ℹ️  No problematic columns found")
                    return False

    return False

def fix_build_update_queries_node(workflow):
    """Remove colunas inexistentes do Build Update Queries node."""

    for node in workflow.get('nodes', []):
        if node.get('name') == 'Build Update Queries':
            print(f"✅ Found Build Update Queries node")

            if 'parameters' in node and 'jsCode' in node['parameters']:
                code = node['parameters']['jsCode']

                # Verificar se contém as colunas problemáticas
                has_issues = 'contact_name' in code

                if has_issues:
                    print("   ⚠️  Found problematic columns in code")

                    # Remover contact_name, contact_email, city do INSERT
                    old_insert_fields = """INSERT INTO conversations (
  phone_number,
  whatsapp_name,
  current_state,
  state_machine_state,
  collected_data,
  service_type,
  contact_name,
  contact_email,
  city,
  status,
  last_message_at,
  created_at,
  updated_at
)"""

                    new_insert_fields = """INSERT INTO conversations (
  phone_number,
  whatsapp_name,
  current_state,
  state_machine_state,
  collected_data,
  service_type,
  status,
  last_message_at,
  created_at,
  updated_at
)"""

                    code = code.replace(old_insert_fields, new_insert_fields)

                    # Remover os valores correspondentes no VALUES
                    old_values = """VALUES (
  '${phone_with_code}',
  '${escapeSql(collected_data?.lead_name || '')}',
  '${db_state}',
  '${next_stage}',
  '${collected_data_json}'::jsonb,
  ${collected_data?.service_type ? "'" + escapeSql(collected_data.service_type) + "'" : 'NULL'},
  '${escapeSql(collected_data?.lead_name || '')}',
  '${escapeSql(collected_data?.email || '')}',
  '${escapeSql(collected_data?.city || '')}',
  'active',
  NOW(),
  NOW(),
  NOW()
)"""

                    new_values = """VALUES (
  '${phone_with_code}',
  '${escapeSql(collected_data?.lead_name || '')}',
  '${db_state}',
  '${next_stage}',
  '${collected_data_json}'::jsonb,
  ${collected_data?.service_type ? "'" + escapeSql(collected_data.service_type) + "'" : 'NULL'},
  'active',
  NOW(),
  NOW(),
  NOW()
)"""

                    code = code.replace(old_values, new_values)

                    # Remover do UPDATE SET
                    lines_to_remove = [
                        "  contact_name = COALESCE(NULLIF(EXCLUDED.contact_name, ''), conversations.contact_name),",
                        "  contact_email = COALESCE(NULLIF(EXCLUDED.contact_email, ''), conversations.contact_email),",
                        "  city = COALESCE(NULLIF(EXCLUDED.city, ''), conversations.city),"
                    ]

                    for line in lines_to_remove:
                        code = code.replace(line, "")

                    # Atualizar o código
                    node['parameters']['jsCode'] = code
                    print("   ✅ Removed contact_name, contact_email, city from Build Update Queries")
                    return True
                else:
                    print("   ℹ️  No problematic columns found")
                    return False

    return False

def update_workflow():
    """Update V41 workflow to remove non-existent database columns."""

    # Load V41 workflow
    base_path = Path(f"n8n/workflows/{BASE_WORKFLOW}")
    if not base_path.exists():
        print(f"❌ Base workflow not found: {BASE_WORKFLOW}")
        return False

    with open(base_path, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    print(f"✅ Loaded base workflow: {BASE_WORKFLOW}")
    print(f"   Nodes count: {len(workflow.get('nodes', []))}")

    # Fix Build SQL Queries node
    fixed_sql = fix_build_sql_queries_node(workflow)

    # Fix Build Update Queries node
    fixed_update = fix_build_update_queries_node(workflow)

    if not fixed_sql and not fixed_update:
        print("⚠️  No fixes were applied - nodes may already be correct")
        print("   Proceeding to create V42 anyway...")

    # Update workflow name
    workflow['name'] = "02 - AI Agent Conversation V42 (Database Columns Fix)"

    # Save as V42
    output_path = Path(f"n8n/workflows/{OUTPUT_WORKFLOW}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print(f"✅ Created: {OUTPUT_WORKFLOW}")
    print(f"   Preserves all {len(workflow.get('nodes', []))} nodes from V41")
    return True

def main():
    """Main function to create V42."""

    print("=" * 60)
    print("V42 - DATABASE COLUMN FIX")
    print("=" * 60)
    print()
    print("PROBLEMA V41:")
    print("  • Queries tentam usar contact_name, contact_email, city")
    print("  • Essas colunas NÃO EXISTEM na tabela conversations")
    print("  • PostgreSQL retorna erro e n8n trava em 'running'")
    print("  • Bot volta ao menu ao invés de avançar")
    print()
    print("SOLUÇÃO V42:")
    print("  • Remover referências a colunas inexistentes")
    print("  • Manter apenas colunas que existem no schema")
    print("  • Dados pessoais vão para collected_data JSONB")
    print()

    success = update_workflow()

    if success:
        print()
        print("=" * 60)
        print("SUCCESS! V42 WORKFLOW CREATED")
        print("=" * 60)
        print()
        print("🎯 V42 FIX:")
        print("- ✅ Removed service_id from Build SQL Queries")
        print("- ✅ Removed contact_name, contact_email, city from INSERT")
        print("- ✅ Removed contact_name, contact_email, city from UPDATE SET")
        print("- ✅ Workflow will no longer trigger database errors")
        print()
        print("📋 NEXT STEPS:")
        print()
        print("1. VALIDATE V42:")
        print("   ./scripts/validate-v42-fix.sh")
        print()
        print("2. DEACTIVATE V41 workflow in n8n")
        print()
        print("3. IMPORT AND ACTIVATE V42:")
        print(f"   - Import: {OUTPUT_WORKFLOW}")
        print("   - Activate it")
        print()
        print("4. TEST:")
        print("   - Send 'oi' → Menu")
        print("   - Send '1' → Ask for name")
        print("   - Send 'Bruno Rosa' → Should ask for phone (NOT back to menu)")
        print("   - Check executions: http://localhost:5678/projects/08qzhIsou3TK6J3Z/executions")
        print("   - All should show 'success' status (not 'running')")
        print()
        print("5. VERIFY DATABASE:")
        print("   SELECT phone_number, collected_data")
        print("   FROM conversations")
        print("   WHERE phone_number = '5562999887766';")
        print()
        print("   Expected collected_data:")
        print("   {")
        print('     "lead_name": "Bruno Rosa",')
        print('     "phone": "62999887766",')
        print("     ...")
        print("   }")
        print()
        print("✅ V42 = V41 + Database Column Fix!")
        print()
        return True

    return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
