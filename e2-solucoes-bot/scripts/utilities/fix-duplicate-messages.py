#!/usr/bin/env python3
"""
Fix duplicate WhatsApp messages issue in n8n workflows.
Adds ON CONFLICT handling to gracefully handle duplicate message IDs.
"""

import json
import sys
from pathlib import Path

def fix_duplicate_messages(input_file, output_file):
    """
    Fix the Store Message node to handle duplicate WhatsApp message IDs.
    """
    print(f"Reading workflow from: {input_file}")

    with open(input_file, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    modified = False

    # Find and fix the Store Message node
    for node in workflow.get('nodes', []):
        if node.get('name') == 'Store Message' and node.get('type') == 'n8n-nodes-base.postgres':
            print(f"Found Store Message node, fixing duplicate handling...")

            # Get the current query
            params = node.get('parameters', {})
            current_query = params.get('query', '')

            # Check if already has ON CONFLICT
            if 'ON CONFLICT' in current_query:
                print("ON CONFLICT already present, skipping...")
                continue

            # Create the new query with ON CONFLICT handling
            new_query = """INSERT INTO messages (
    conversation_id,
    direction,
    content,
    message_type,
    media_url,
    whatsapp_message_id
) VALUES (
    {{$json.conversation_id}},
    'incoming',
    {{$json.message_content}},
    {{$json.message_type}},
    {{$json.media_url}},
    {{$json.whatsapp_message_id}}
)
ON CONFLICT (whatsapp_message_id) DO UPDATE SET
    updated_at = CURRENT_TIMESTAMP,
    content = EXCLUDED.content,
    media_url = EXCLUDED.media_url
RETURNING
    id,
    created_at,
    CASE
        WHEN xmax = 0 THEN 'inserted'
        ELSE 'updated'
    END as operation;"""

            params['query'] = new_query

            # Also ensure the node always outputs data
            params['alwaysOutputData'] = True

            node['parameters'] = params
            modified = True
            print("✅ Store Message node fixed with ON CONFLICT handling")

    if not modified:
        print("⚠️ No Store Message node found to fix")

    # Save the modified workflow
    print(f"Saving fixed workflow to: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print("✅ Workflow fixed successfully!")

    return modified

def main():
    # Define file paths
    base_dir = Path("/home/bruno/Desktop/Programas/E2_Solucoes/e2-solucoes-bot")
    input_file = base_dir / "n8n/workflows/01_main_whatsapp_handler_V2.3_FIXED_IMPORT.json"
    output_file = base_dir / "n8n/workflows/01_main_whatsapp_handler_V2.4_DEDUP.json"

    if not input_file.exists():
        print(f"❌ Input file not found: {input_file}")
        sys.exit(1)

    # Fix the workflow
    success = fix_duplicate_messages(input_file, output_file)

    if success:
        print("\n📋 Next steps:")
        print("1. Import the fixed workflow into n8n:")
        print(f"   - File: {output_file}")
        print("2. Deactivate the old workflow")
        print("3. Activate the new workflow")
        print("4. Test with a WhatsApp message")

        print("\n🔍 To monitor for duplicates:")
        print("docker logs -f e2bot-n8n-dev 2>&1 | grep -E '(duplicate|conflict|inserted|updated)'")

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())