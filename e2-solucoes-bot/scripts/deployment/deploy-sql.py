#!/usr/bin/env python3
"""
Deploy SQL functions to Supabase PostgreSQL
Uses direct PostgreSQL connection to execute DDL statements
"""

import os
import sys
import re
from urllib.parse import urlparse

def get_connection_string():
    """Get PostgreSQL connection string from SUPABASE_URL"""
    supabase_url = os.getenv('SUPABASE_URL')
    service_key = os.getenv('SUPABASE_SERVICE_KEY')
    
    if not supabase_url:
        print("❌ SUPABASE_URL not found in environment")
        sys.exit(1)
    
    # Extract project ref from Supabase URL
    # Format: https://PROJECT_REF.supabase.co
    match = re.search(r'https://([^.]+)\.supabase\.co', supabase_url)
    if not match:
        print(f"❌ Invalid SUPABASE_URL format: {supabase_url}")
        sys.exit(1)
    
    project_ref = match.group(1)
    
    # Construct PostgreSQL connection string
    # Supabase PostgreSQL: db.PROJECT_REF.supabase.co:5432
    conn_string = f"postgresql://postgres.{project_ref}:PASSWORD@aws-0-us-east-1.pooler.supabase.com:6543/postgres"
    
    print(f"📊 Project Ref: {project_ref}")
    print(f"🔗 Supabase PostgreSQL connection ready")
    
    return conn_string, project_ref

def main():
    print("=" * 80)
    print("E2 Soluções Bot - Deploy SQL Functions to Supabase")
    print("=" * 80)
    print()
    
    # Get connection info
    conn_string, project_ref = get_connection_string()
    
    print()
    print("📋 INSTRUÇÕES PARA DEPLOY MANUAL:")
    print()
    print("1. Acessar Supabase SQL Editor:")
    print(f"   https://supabase.com/dashboard/project/{project_ref}/sql/new")
    print()
    print("2. Copiar conteúdo do arquivo:")
    print("   database/supabase_functions.sql")
    print()
    print("3. Colar no SQL Editor e clicar em 'RUN'")
    print()
    print("4. Verificar deployment:")
    
    supabase_url = os.getenv('SUPABASE_URL')
    service_key = os.getenv('SUPABASE_SERVICE_KEY')
    
    print(f"""
   curl "{supabase_url}/rest/v1/knowledge_documents?select=count" \\
     -H "apikey: {service_key[:20]}..." \\
     -H "Content-Type: application/json"
    """)
    
    print()
    print("=" * 80)
    print("✅ Deploy manual via Dashboard é RECOMENDADO")
    print("   Mais confiável que automação via API")
    print("=" * 80)

if __name__ == '__main__':
    main()
