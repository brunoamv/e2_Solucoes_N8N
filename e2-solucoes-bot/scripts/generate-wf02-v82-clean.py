#!/usr/bin/env python3
"""
Gera WF02 V82 - Versão Limpa do V81 com Conexões Corrigidas

PROBLEMA: V81 FIXED tem conexões corretas mas n8n rejeita importação
SOLUÇÃO: Criar V82 com novo ID e metadata limpa
"""

import json
import uuid
from datetime import datetime
from pathlib import Path

def generate_wf02_v82():
    """Gera workflow V82 baseado no V81 FIXED"""

    base_dir = Path(__file__).parent.parent
    input_file = base_dir / 'n8n/workflows/02_ai_agent_conversation_V81_WF06_INTEGRATION_FIXED.json'
    output_file = base_dir / 'n8n/workflows/02_ai_agent_conversation_V82_CLEAN.json'

    print("📖 Lendo V81 FIXED...")
    with open(input_file, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    print(f"✅ Carregado: {len(workflow['nodes'])} nodes, {len(workflow['connections'])} conexões")

    # ====================
    # PASSO 1: Gerar Novo ID
    # ====================
    old_id = workflow.get('id')
    new_id = str(uuid.uuid4()).replace('-', '')[:20]  # Format n8n usa

    workflow['id'] = new_id
    print(f"🆔 ID: {old_id} → {new_id}")

    # ====================
    # PASSO 2: Atualizar Metadata
    # ====================
    workflow['name'] = '02_ai_agent_conversation_V82_CLEAN'
    workflow['active'] = False  # Importar inativo para teste primeiro

    # Limpar versionId (n8n gera novo)
    if 'versionId' in workflow:
        del workflow['versionId']

    # Atualizar meta
    workflow['meta'] = {
        'instanceId': str(uuid.uuid4())
    }

    print(f"📝 Name: {workflow['name']}")
    print(f"🔄 Active: {workflow['active']}")

    # ====================
    # PASSO 3: Limpar pinData (dados de teste)
    # ====================
    if 'pinData' in workflow and workflow['pinData']:
        print(f"🧹 Limpando pinData ({len(workflow['pinData'])} entries)")
        workflow['pinData'] = {}

    # ====================
    # PASSO 4: Validar e Normalizar Nodes
    # ====================
    print("\n🔍 Validando nodes...")

    for node in workflow['nodes']:
        # Garantir ID existe
        if 'id' not in node:
            node['id'] = str(uuid.uuid4())

        # Garantir parameters é dict
        if 'parameters' not in node:
            node['parameters'] = {}
        elif not isinstance(node['parameters'], dict):
            node['parameters'] = {}

        # Garantir position é array válido
        if 'position' not in node or not isinstance(node['position'], list) or len(node['position']) != 2:
            # Default position
            node['position'] = [0, 0]

        # Garantir typeVersion existe (default 1)
        if 'typeVersion' not in node:
            node['typeVersion'] = 1

    print(f"✅ Nodes validados")

    # ====================
    # PASSO 5: Validar Conexões
    # ====================
    print("\n🔍 Validando conexões...")

    node_names = {node['name'] for node in workflow['nodes']}
    invalid_connections = []

    for source, conns in list(workflow['connections'].items()):
        # Verificar source existe
        if source not in node_names:
            invalid_connections.append(source)
            continue

        # Verificar estrutura main
        if 'main' not in conns:
            continue

        # Validar cada output
        for output_idx, outputs in enumerate(conns['main']):
            if not outputs:
                continue

            # Verificar cada conexão
            valid_outputs = []
            for conn in outputs:
                if not isinstance(conn, dict):
                    continue

                target_node = conn.get('node')
                if target_node not in node_names:
                    print(f"  ⚠️  Conexão inválida: {source} → {target_node}")
                    continue

                # Garantir campos obrigatórios
                if 'type' not in conn:
                    conn['type'] = 'main'
                if 'index' not in conn:
                    conn['index'] = 0

                valid_outputs.append(conn)

            # Atualizar com conexões válidas
            conns['main'][output_idx] = valid_outputs

    # Remover conexões inválidas
    for invalid in invalid_connections:
        del workflow['connections'][invalid]
        print(f"  🗑️  Removida conexão de node inexistente: {invalid}")

    print(f"✅ Conexões validadas")

    # ====================
    # PASSO 6: Adicionar Tags
    # ====================
    workflow['tags'] = ['V82', 'WF06-Integration', 'Clean']

    # ====================
    # PASSO 7: Salvar V82
    # ====================
    print(f"\n💾 Salvando V82: {output_file}")

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print(f"✅ V82 salvo com sucesso!")

    # ====================
    # PASSO 8: Estatísticas Finais
    # ====================
    print("\n📊 ESTATÍSTICAS V82:")
    print(f"  Nodes: {len(workflow['nodes'])}")
    print(f"  Conexões: {len(workflow['connections'])}")
    print(f"  ID: {workflow['id']}")
    print(f"  Name: {workflow['name']}")
    print(f"  Tags: {workflow['tags']}")

    # Verificar nodes críticos WF06
    wf06_nodes = [
        'Prepare WF06 Next Dates Data',
        'Prepare WF06 Available Slots Data',
        'Merge WF06 Next Dates with User Data',
        'Merge WF06 Available Slots with User Data'
    ]

    print("\n🔍 VERIFICAÇÃO WF06 NODES:")
    for node_name in wf06_nodes:
        if node_name in workflow['connections']:
            print(f"  ✅ {node_name}: CONECTADO")
        else:
            print(f"  ❌ {node_name}: SEM CONEXÕES")

    print("\n🎉 WF02 V82 GERADO COM SUCESSO!")
    print(f"\n📝 Próximo passo:")
    print(f"   1. Importe no n8n: {output_file}")
    print(f"   2. Ative o workflow após validação visual")
    print(f"   3. Execute testes de Service 1 e 3")

    return True

if __name__ == '__main__':
    import sys
    success = generate_wf02_v82()
    sys.exit(0 if success else 1)
