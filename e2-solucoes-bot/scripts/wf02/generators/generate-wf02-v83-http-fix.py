#!/usr/bin/env python3
"""
Gera WF02 V83 - Correção dos HTTP Request Nodes

PROBLEMA IDENTIFICADO:
- HTTP Request nodes usam bodyParameters (formato antigo/inválido)
- Requests falham silenciosamente
- Prepare nodes recebem {message: "Workflow was started"} ao invés de dados reais

SOLUÇÃO:
- Usar jsonBodyParameter para enviar JSON correto
- Formato: {"action": "next_dates", "count": 3, ...}
"""

import json
import uuid
from pathlib import Path

def generate_wf02_v83():
    """Gera workflow V83 com HTTP Request nodes corrigidos"""

    base_dir = Path(__file__).parent.parent
    input_file = base_dir / 'n8n/workflows/02_ai_agent_conversation_V82_CLEAN.json'
    output_file = base_dir / 'n8n/workflows/02_ai_agent_conversation_V83_HTTP_FIX.json'

    print("📖 Lendo V82 CLEAN...")
    with open(input_file, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    print(f"✅ Carregado: {len(workflow['nodes'])} nodes")

    # ====================
    # PASSO 1: Novo ID e Metadata
    # ====================
    old_id = workflow['id']
    new_id = str(uuid.uuid4()).replace('-', '')[:20]
    workflow['id'] = new_id
    workflow['name'] = '02_ai_agent_conversation_V83_HTTP_FIX'
    workflow['tags'] = ['V83', 'WF06-Integration', 'HTTP-Fix']

    print(f"🆔 ID: {old_id} → {new_id}")
    print(f"📝 Name: {workflow['name']}")

    # ====================
    # PASSO 2: Corrigir HTTP Request - Next Dates
    # ====================
    print("\n🔧 Corrigindo HTTP Request - Get Next Dates...")

    for node in workflow['nodes']:
        if node['name'] == 'HTTP Request - Get Next Dates':
            # Configuração correta para n8n HTTP Request node
            node['parameters'] = {
                'method': 'POST',
                'url': 'http://e2bot-n8n-dev:5678/webhook/calendar-availability',
                'authentication': 'none',
                'sendHeaders': False,
                'sendQuery': False,
                'sendBody': True,
                'contentType': 'json',
                'specifyBody': 'json',
                'jsonBody': json.dumps({
                    'action': 'next_dates',
                    'count': 3,
                    'service_type': 'energia_solar',
                    'duration_minutes': 120
                }, indent=2),
                'options': {
                    'response': {
                        'response': {
                            'neverError': True
                        }
                    },
                    'timeout': 30000
                }
            }
            print("  ✅ HTTP Request Next Dates configurado com JSON body correto")
            break

    # ====================
    # PASSO 3: Corrigir HTTP Request - Available Slots
    # ====================
    print("\n🔧 Corrigindo HTTP Request - Get Available Slots...")

    for node in workflow['nodes']:
        if node['name'] == 'HTTP Request - Get Available Slots':
            # Este node precisa receber date do state machine
            # Usar expression para pegar data escolhida
            node['parameters'] = {
                'method': 'POST',
                'url': 'http://e2bot-n8n-dev:5678/webhook/calendar-availability',
                'authentication': 'none',
                'sendHeaders': False,
                'sendQuery': False,
                'sendBody': True,
                'contentType': 'json',
                'specifyBody': 'json',
                'jsonBody': '={\n  "action": "available_slots",\n  "date": "{{ $json.collected_data.selected_date || $json.selected_date }}",\n  "service_type": "{{ $json.service_type || \'energia_solar\' }}",\n  "duration_minutes": 120\n}',
                'options': {
                    'response': {
                        'response': {
                            'neverError': True
                        }
                    },
                    'timeout': 30000
                }
            }
            print("  ✅ HTTP Request Available Slots configurado com JSON body e expressões")
            break

    # ====================
    # PASSO 4: Atualizar Prepare Nodes (adicionar validação)
    # ====================
    print("\n🔧 Atualizando Prepare Nodes com validação...")

    prepare_next_code = """// Prepare WF06 Next Dates Response V83
// Extracts and validates dates_with_availability from WF06 response

const wf06Response = $input.first().json;

console.log('=== PREPARE WF06 NEXT DATES V83 ===');
console.log('Input:', JSON.stringify(wf06Response, null, 2));

// Validar resposta do WF06
if (!wf06Response) {
  console.error('ERROR: No response from WF06');
  throw new Error('WF06 returned empty response');
}

// Extrair dates_with_availability
let datesData;
if (wf06Response.dates_with_availability) {
  // Resposta direta do WF06
  datesData = wf06Response.dates_with_availability;
} else if (wf06Response.json && wf06Response.json.dates_with_availability) {
  // Resposta wrapeada
  datesData = wf06Response.json.dates_with_availability;
} else {
  console.error('ERROR: No dates_with_availability in response');
  console.error('Response keys:', Object.keys(wf06Response));
  throw new Error('Invalid WF06 response format');
}

// Validar estrutura
if (!Array.isArray(datesData) || datesData.length === 0) {
  console.error('ERROR: dates_with_availability not array or empty');
  throw new Error('WF06 returned invalid dates data');
}

console.log(`SUCCESS: Received ${datesData.length} dates with availability`);

// Preparar dados para State Machine
const preparedData = {
  wf06_next_dates: datesData
};

console.log('Prepared data:', JSON.stringify(preparedData, null, 2));

return preparedData;
"""

    prepare_slots_code = """// Prepare WF06 Available Slots Response V83
// Extracts and validates available_slots from WF06 response

const wf06Response = $input.first().json;

console.log('=== PREPARE WF06 AVAILABLE SLOTS V83 ===');
console.log('Input:', JSON.stringify(wf06Response, null, 2));

// Validar resposta do WF06
if (!wf06Response) {
  console.error('ERROR: No response from WF06');
  throw new Error('WF06 returned empty response');
}

// Extrair available_slots
let slotsData;
if (wf06Response.available_slots) {
  // Resposta direta do WF06
  slotsData = wf06Response.available_slots;
} else if (wf06Response.json && wf06Response.json.available_slots) {
  // Resposta wrapeada
  slotsData = wf06Response.json.available_slots;
} else {
  console.error('ERROR: No available_slots in response');
  console.error('Response keys:', Object.keys(wf06Response));
  throw new Error('Invalid WF06 response format');
}

// Validar estrutura
if (!Array.isArray(slotsData) || slotsData.length === 0) {
  console.error('ERROR: available_slots not array or empty');
  throw new Error('WF06 returned invalid slots data');
}

console.log(`SUCCESS: Received ${slotsData.length} available slots`);

// Preparar dados para State Machine
const preparedData = {
  wf06_available_slots: slotsData
};

console.log('Prepared data:', JSON.stringify(preparedData, null, 2));

return preparedData;
"""

    # Atualizar Prepare nodes
    for node in workflow['nodes']:
        if node['name'] == 'Prepare WF06 Next Dates Data':
            node['parameters']['jsCode'] = prepare_next_code
            print("  ✅ Prepare Next Dates atualizado com validação")
        elif node['name'] == 'Prepare WF06 Available Slots Data':
            node['parameters']['jsCode'] = prepare_slots_code
            print("  ✅ Prepare Available Slots atualizado com validação")

    # ====================
    # PASSO 5: Salvar V83
    # ====================
    print(f"\n💾 Salvando V83: {output_file}")

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print(f"✅ V83 salvo com sucesso!")

    # ====================
    # PASSO 6: Estatísticas
    # ====================
    print("\n📊 ESTATÍSTICAS V83:")
    print(f"  Nodes: {len(workflow['nodes'])}")
    print(f"  Conexões: {len(workflow['connections'])}")
    print(f"  ID: {workflow['id']}")
    print(f"  Tags: {workflow['tags']}")

    print("\n✅ CORREÇÕES APLICADAS:")
    print("  1. HTTP Request Next Dates: JSON body correto")
    print("  2. HTTP Request Available Slots: JSON body com expressões")
    print("  3. Prepare Next Dates: Validação robusta de resposta")
    print("  4. Prepare Available Slots: Validação robusta de resposta")

    print("\n🎉 WF02 V83 GERADO COM SUCESSO!")
    print(f"\n📝 Próximo passo:")
    print(f"   1. Importe no n8n: {output_file}")
    print(f"   2. Ative o workflow")
    print(f"   3. Teste Service 1 (Solar) → Deve receber 3 datas do WF06")
    print(f"   4. Verifique logs: docker logs -f e2bot-n8n-dev")

    return True

if __name__ == '__main__':
    import sys
    success = generate_wf02_v83()
    sys.exit(0 if success else 1)
