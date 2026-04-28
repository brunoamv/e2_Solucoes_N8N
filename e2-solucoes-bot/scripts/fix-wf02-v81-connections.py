#!/usr/bin/env python3
"""
Script para corrigir conexões dos nodes no WF02 V81

PROBLEMA IDENTIFICADO:
- HTTP Requests conectam direto ao State Machine
- Nodes Prepare e Merge estão desconectados

ESTRUTURA CORRETA ESPERADA:
Path 1 (Next Dates):
  HTTP Request → Prepare WF06 Next Dates → Merge (Input 1)
  Get Conversation Details → Merge (Input 2)
  Merge → State Machine

Path 2 (Available Slots):
  HTTP Request → Prepare WF06 Available Slots → Merge (Input 1)
  Get Conversation Details → Merge (Input 2)
  Merge → State Machine
"""

import json
import sys
from pathlib import Path

def fix_wf02_v81_connections():
    """Corrige as conexões do workflow V81"""

    # Caminhos
    base_dir = Path(__file__).parent.parent
    input_file = base_dir / 'n8n/workflows/02_ai_agent_conversation_V81_WF06_INTEGRATION.json'
    output_file = base_dir / 'n8n/workflows/02_ai_agent_conversation_V81_WF06_INTEGRATION_FIXED.json'

    print(f"📖 Lendo workflow: {input_file}")

    with open(input_file, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    # Verificar estrutura
    if 'nodes' not in workflow or 'connections' not in workflow:
        print("❌ ERRO: Estrutura de workflow inválida")
        sys.exit(1)

    print(f"✅ Workflow carregado: {len(workflow['nodes'])} nodes, {len(workflow['connections'])} conexões")

    # ====================
    # PASSO 1: Corrigir Path 1 (Next Dates)
    # ====================
    print("\n🔧 Corrigindo Path 1 (Next Dates)...")

    # 1.1: HTTP Request → Prepare
    workflow['connections']['HTTP Request - Get Next Dates'] = {
        'main': [[{
            'node': 'Prepare WF06 Next Dates Data',
            'type': 'main',
            'index': 0
        }]]
    }
    print("  ✅ HTTP Request - Get Next Dates → Prepare WF06 Next Dates Data")

    # 1.2: Prepare → Merge (Input 1)
    workflow['connections']['Prepare WF06 Next Dates Data'] = {
        'main': [[{
            'node': 'Merge WF06 Next Dates with User Data',
            'type': 'main',
            'index': 0
        }]]
    }
    print("  ✅ Prepare WF06 Next Dates Data → Merge (Input 1)")

    # 1.3: Get Conversation → Merge (Input 2)
    # Verificar se já existe conexão
    if 'Get Conversation Details' not in workflow['connections']:
        workflow['connections']['Get Conversation Details'] = {'main': [[]]}

    # Adicionar conexão ao Merge Next Dates (Input 2)
    if not any(conn.get('node') == 'Merge WF06 Next Dates with User Data'
               for conn in workflow['connections']['Get Conversation Details']['main'][0]):
        workflow['connections']['Get Conversation Details']['main'][0].append({
            'node': 'Merge WF06 Next Dates with User Data',
            'type': 'main',
            'index': 1  # Input 2
        })
    print("  ✅ Get Conversation Details → Merge (Input 2)")

    # 1.4: Merge → State Machine
    workflow['connections']['Merge WF06 Next Dates with User Data'] = {
        'main': [[{
            'node': 'State Machine Logic',
            'type': 'main',
            'index': 0
        }]]
    }
    print("  ✅ Merge WF06 Next Dates → State Machine")

    # ====================
    # PASSO 2: Corrigir Path 2 (Available Slots)
    # ====================
    print("\n🔧 Corrigindo Path 2 (Available Slots)...")

    # 2.1: HTTP Request → Prepare
    workflow['connections']['HTTP Request - Get Available Slots'] = {
        'main': [[{
            'node': 'Prepare WF06 Available Slots Data',
            'type': 'main',
            'index': 0
        }]]
    }
    print("  ✅ HTTP Request - Get Available Slots → Prepare WF06 Available Slots Data")

    # 2.2: Prepare → Merge (Input 1)
    workflow['connections']['Prepare WF06 Available Slots Data'] = {
        'main': [[{
            'node': 'Merge WF06 Available Slots with User Data',
            'type': 'main',
            'index': 0
        }]]
    }
    print("  ✅ Prepare WF06 Available Slots Data → Merge (Input 1)")

    # 2.3: Get Conversation → Merge (Input 2)
    if not any(conn.get('node') == 'Merge WF06 Available Slots with User Data'
               for conn in workflow['connections']['Get Conversation Details']['main'][0]):
        workflow['connections']['Get Conversation Details']['main'][0].append({
            'node': 'Merge WF06 Available Slots with User Data',
            'type': 'main',
            'index': 1  # Input 2
        })
    print("  ✅ Get Conversation Details → Merge (Input 2)")

    # 2.4: Merge → State Machine
    workflow['connections']['Merge WF06 Available Slots with User Data'] = {
        'main': [[{
            'node': 'State Machine Logic',
            'type': 'main',
            'index': 0
        }]]
    }
    print("  ✅ Merge WF06 Available Slots → State Machine")

    # ====================
    # PASSO 3: Salvar workflow corrigido
    # ====================
    print(f"\n💾 Salvando workflow corrigido: {output_file}")

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print(f"✅ Workflow corrigido salvo com sucesso!")
    print(f"\n📊 Total de conexões agora: {len(workflow['connections'])}")

    # Verificação final
    print("\n🔍 Verificação Final:")
    required_connections = [
        'Prepare WF06 Next Dates Data',
        'Prepare WF06 Available Slots Data',
        'Merge WF06 Next Dates with User Data',
        'Merge WF06 Available Slots with User Data'
    ]

    for node_name in required_connections:
        if node_name in workflow['connections']:
            print(f"  ✅ {node_name}: CONECTADO")
        else:
            print(f"  ❌ {node_name}: SEM CONEXÕES")
            return False

    print("\n🎉 TODAS AS CONEXÕES CORRIGIDAS COM SUCESSO!")
    print(f"\n📝 Próximo passo:")
    print(f"   Importe o arquivo no n8n:")
    print(f"   {output_file}")

    return True

if __name__ == '__main__':
    success = fix_wf02_v81_connections()
    sys.exit(0 if success else 1)
