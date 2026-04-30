#!/usr/bin/env python3
"""
Gera WF02 V85 - Versão Diagnóstica para Debug

PROBLEMA PERSISTENTE (V84):
- HTTP Request configurado corretamente (jsonBody)
- Prepare node código correto (extrai 'dates')
- MAS: Prepare node recebe resposta vazia ou incorreta

SOLUÇÃO V85 DIAGNÓSTICA:
- Adicionar logs extensivos ANTES do Prepare node
- Adicionar node "Debug WF06 Response" entre HTTP Request e Prepare
- Capturar response completa para análise
"""

import json
import uuid
from pathlib import Path

def generate_wf02_v85():
    """Gera workflow V85 com diagnóstico extensivo"""

    base_dir = Path(__file__).parent.parent
    input_file = base_dir / 'n8n/workflows/02_ai_agent_conversation_V84_PREPARE_FIX.json'
    output_file = base_dir / 'n8n/workflows/02_ai_agent_conversation_V85_DIAGNOSTIC.json'

    print("📖 Lendo V84 PREPARE FIX...")
    with open(input_file, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    print(f"✅ Carregado: {len(workflow['nodes'])} nodes")

    # ====================
    # PASSO 1: Novo ID e Metadata
    # ====================
    old_id = workflow['id']
    new_id = str(uuid.uuid4()).replace('-', '')[:20]
    workflow['id'] = new_id
    workflow['name'] = '02_ai_agent_conversation_V85_DIAGNOSTIC'
    workflow['tags'] = ['V85', 'WF06-Integration', 'Diagnostic']

    print(f"🆔 ID: {old_id} → {new_id}")
    print(f"📝 Name: {workflow['name']}")

    # ====================
    # PASSO 2: Criar Debug Node para Next Dates
    # ====================
    print("\n🔧 Criando Debug WF06 Next Dates Response node...")

    debug_next_dates_code = """// DEBUG WF06 Next Dates Response V85
// Captura e loga TODA a resposta do HTTP Request

const httpResponse = $input.first().json;

console.log('=== DEBUG WF06 NEXT DATES RESPONSE ===');
console.log('Full HTTP Response:', JSON.stringify(httpResponse, null, 2));
console.log('Response type:', typeof httpResponse);
console.log('Response is array:', Array.isArray(httpResponse));
console.log('Response keys:', Object.keys(httpResponse));

// Verificar se tem property 'json' wrapeada
if (httpResponse.json) {
  console.log('Found wrapped .json property');
  console.log('Wrapped json:', JSON.stringify(httpResponse.json, null, 2));
  console.log('Wrapped json keys:', Object.keys(httpResponse.json));
}

// Verificar se tem property 'body'
if (httpResponse.body) {
  console.log('Found .body property');
  console.log('Body type:', typeof httpResponse.body);
  console.log('Body:', httpResponse.body);
}

// Verificar se tem property 'data'
if (httpResponse.data) {
  console.log('Found .data property');
  console.log('Data:', JSON.stringify(httpResponse.data, null, 2));
}

// Verificar propriedades dates e dates_with_availability
if (httpResponse.dates) {
  console.log('✅ Found .dates property (EXPECTED FORMAT)');
  console.log('Dates count:', httpResponse.dates.length);
}

if (httpResponse.dates_with_availability) {
  console.log('⚠️ Found .dates_with_availability property (OLD FORMAT)');
}

// Passar resposta original adiante para Prepare node
return httpResponse;
"""

    debug_next_node = {
        "parameters": {
            "jsCode": debug_next_dates_code
        },
        "id": str(uuid.uuid4()),
        "name": "Debug WF06 Next Dates Response",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [920, 204]
    }

    # ====================
    # PASSO 3: Criar Debug Node para Available Slots
    # ====================
    print("🔧 Criando Debug WF06 Available Slots Response node...")

    debug_slots_code = """// DEBUG WF06 Available Slots Response V85
// Captura e loga TODA a resposta do HTTP Request

const httpResponse = $input.first().json;

console.log('=== DEBUG WF06 AVAILABLE SLOTS RESPONSE ===');
console.log('Full HTTP Response:', JSON.stringify(httpResponse, null, 2));
console.log('Response type:', typeof httpResponse);
console.log('Response is array:', Array.isArray(httpResponse));
console.log('Response keys:', Object.keys(httpResponse));

// Verificar se tem property 'json' wrapeada
if (httpResponse.json) {
  console.log('Found wrapped .json property');
  console.log('Wrapped json:', JSON.stringify(httpResponse.json, null, 2));
  console.log('Wrapped json keys:', Object.keys(httpResponse.json));
}

// Verificar se tem property 'body'
if (httpResponse.body) {
  console.log('Found .body property');
  console.log('Body type:', typeof httpResponse.body);
  console.log('Body:', httpResponse.body);
}

// Verificar propriedades slots e available_slots
if (httpResponse.slots) {
  console.log('✅ Found .slots property (EXPECTED FORMAT)');
  console.log('Slots count:', httpResponse.slots.length);
}

if (httpResponse.available_slots) {
  console.log('⚠️ Found .available_slots property (ALTERNATE FORMAT)');
}

// Passar resposta original adiante para Prepare node
return httpResponse;
"""

    debug_slots_node = {
        "parameters": {
            "jsCode": debug_slots_code
        },
        "id": str(uuid.uuid4()),
        "name": "Debug WF06 Available Slots Response",
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "position": [920, 424]
    }

    # ====================
    # PASSO 4: Inserir Debug Nodes na lista
    # ====================
    workflow['nodes'].append(debug_next_node)
    workflow['nodes'].append(debug_slots_node)
    print(f"  ✅ Debug nodes adicionados: {len(workflow['nodes'])} nodes total")

    # ====================
    # PASSO 5: Reconfigurar Conexões
    # ====================
    print("\n🔧 Reconfigurando conexões para incluir Debug nodes...")

    # Encontrar índices dos nodes relevantes
    http_next_idx = None
    http_slots_idx = None
    debug_next_idx = len(workflow['nodes']) - 2  # Penúltimo
    debug_slots_idx = len(workflow['nodes']) - 1  # Último
    prepare_next_idx = None
    prepare_slots_idx = None

    for i, node in enumerate(workflow['nodes']):
        if node['name'] == 'HTTP Request - Get Next Dates':
            http_next_idx = i
        elif node['name'] == 'HTTP Request - Get Available Slots':
            http_slots_idx = i
        elif node['name'] == 'Prepare WF06 Next Dates Data':
            prepare_next_idx = i
        elif node['name'] == 'Prepare WF06 Available Slots Data':
            prepare_slots_idx = i

    # Atualizar conexões: HTTP → Debug → Prepare
    if 'HTTP Request - Get Next Dates' not in workflow['connections']:
        workflow['connections']['HTTP Request - Get Next Dates'] = {'main': [[]]}

    workflow['connections']['HTTP Request - Get Next Dates']['main'] = [[{
        'node': 'Debug WF06 Next Dates Response',
        'type': 'main',
        'index': 0
    }]]

    workflow['connections']['Debug WF06 Next Dates Response'] = {
        'main': [[{
            'node': 'Prepare WF06 Next Dates Data',
            'type': 'main',
            'index': 0
        }]]
    }

    if 'HTTP Request - Get Available Slots' not in workflow['connections']:
        workflow['connections']['HTTP Request - Get Available Slots'] = {'main': [[]]}

    workflow['connections']['HTTP Request - Get Available Slots']['main'] = [[{
        'node': 'Debug WF06 Available Slots Response',
        'type': 'main',
        'index': 0
    }]]

    workflow['connections']['Debug WF06 Available Slots Response'] = {
        'main': [[{
            'node': 'Prepare WF06 Available Slots Data',
            'type': 'main',
            'index': 0
        }]]
    }

    print("  ✅ Conexões reconfiguradas:")
    print("    Path 1: HTTP Request Next Dates → Debug → Prepare")
    print("    Path 2: HTTP Request Slots → Debug → Prepare")

    # ====================
    # PASSO 6: Salvar V85
    # ====================
    print(f"\n💾 Salvando V85 DIAGNOSTIC: {output_file}")

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print(f"✅ V85 DIAGNOSTIC salvo com sucesso!")

    # ====================
    # PASSO 7: Estatísticas
    # ====================
    print("\n📊 ESTATÍSTICAS V85:")
    print(f"  Nodes: {len(workflow['nodes'])}")
    print(f"  Conexões: {len(workflow['connections'])}")
    print(f"  ID: {workflow['id']}")
    print(f"  Tags: {workflow['tags']}")

    print("\n✅ DIAGNÓSTICO ADICIONADO:")
    print("  1. Debug WF06 Next Dates Response: Loga resposta completa HTTP Request")
    print("  2. Debug WF06 Available Slots Response: Loga resposta completa HTTP Request")
    print("  3. Logs incluem: tipo, keys, properties wrapeadas (.json, .body, .data)")
    print("  4. Verificação de formatos: .dates vs .dates_with_availability")

    print("\n🎉 WF02 V85 DIAGNOSTIC GERADO COM SUCESSO!")
    print(f"\n📝 Próximo passo:")
    print(f"   1. Importe no n8n: {output_file}")
    print(f"   2. Ative o workflow")
    print(f"   3. Execute teste com Service 1 (Solar)")
    print(f"   4. Verifique logs: docker logs -f e2bot-n8n-dev")
    print(f"   5. Analise output do Debug node para identificar estrutura real da resposta")

    return True

if __name__ == '__main__':
    import sys
    success = generate_wf02_v85()
    sys.exit(0 if success else 1)
