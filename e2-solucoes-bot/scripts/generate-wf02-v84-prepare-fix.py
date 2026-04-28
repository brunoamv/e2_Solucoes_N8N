#!/usr/bin/env python3
"""
Gera WF02 V84 - Correção dos Prepare Nodes

PROBLEMA IDENTIFICADO (V83):
- Prepare nodes procuram por 'dates_with_availability' (ERRADO)
- WF06 retorna 'dates' array (CORRETO)
- Formato real: {dates: [{date, display, day_of_week, total_slots, quality, slots: [...]}], total_available: N}

SOLUÇÃO V84:
- Corrigir extração para usar 'dates' property
- Manter validação robusta
- Preservar toda estrutura do V83 (HTTP Request correto)
"""

import json
import uuid
from pathlib import Path

def generate_wf02_v84():
    """Gera workflow V84 com Prepare nodes corrigidos para formato real WF06"""

    base_dir = Path(__file__).parent.parent
    input_file = base_dir / 'n8n/workflows/02_ai_agent_conversation_V83_HTTP_FIX.json'
    output_file = base_dir / 'n8n/workflows/02_ai_agent_conversation_V84_PREPARE_FIX.json'

    print("📖 Lendo V83 HTTP FIX...")
    with open(input_file, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    print(f"✅ Carregado: {len(workflow['nodes'])} nodes")

    # ====================
    # PASSO 1: Novo ID e Metadata
    # ====================
    old_id = workflow['id']
    new_id = str(uuid.uuid4()).replace('-', '')[:20]
    workflow['id'] = new_id
    workflow['name'] = '02_ai_agent_conversation_V84_PREPARE_FIX'
    workflow['tags'] = ['V84', 'WF06-Integration', 'Prepare-Fix']

    print(f"🆔 ID: {old_id} → {new_id}")
    print(f"📝 Name: {workflow['name']}")

    # ====================
    # PASSO 2: Corrigir Prepare WF06 Next Dates Data
    # ====================
    print("\n🔧 Corrigindo Prepare WF06 Next Dates Data...")

    prepare_next_code = """// Prepare WF06 Next Dates Response V84
// Extracts and validates 'dates' from WF06 response (CORRECTED)

const wf06Response = $input.first().json;

console.log('=== PREPARE WF06 NEXT DATES V84 ===');
console.log('Input:', JSON.stringify(wf06Response, null, 2));

// Validar resposta do WF06
if (!wf06Response) {
  console.error('ERROR: No response from WF06');
  throw new Error('WF06 returned empty response');
}

// Extrair 'dates' array (FORMATO CORRETO)
let datesData;
if (wf06Response.dates) {
  // Resposta direta do WF06 com 'dates' property
  datesData = wf06Response.dates;
} else if (wf06Response.json && wf06Response.json.dates) {
  // Resposta wrapeada
  datesData = wf06Response.json.dates;
} else {
  console.error('ERROR: No dates in response');
  console.error('Response keys:', Object.keys(wf06Response));
  throw new Error('Invalid WF06 response format - missing dates property');
}

// Validar estrutura
if (!Array.isArray(datesData) || datesData.length === 0) {
  console.error('ERROR: dates not array or empty');
  console.error('Received dates:', datesData);
  throw new Error('WF06 returned invalid dates data');
}

console.log(`SUCCESS: Received ${datesData.length} dates with availability`);

// Preparar dados para State Machine
// WF06 retorna: {date, display, day_of_week, total_slots, quality, slots: [...]}
const preparedData = {
  wf06_next_dates: datesData
};

console.log('Prepared data:', JSON.stringify(preparedData, null, 2));

return preparedData;
"""

    # ====================
    # PASSO 3: Corrigir Prepare WF06 Available Slots Data
    # ====================
    print("\n🔧 Corrigindo Prepare WF06 Available Slots Data...")

    prepare_slots_code = """// Prepare WF06 Available Slots Response V84
// Extracts and validates 'slots' from WF06 response (CORRECTED)

const wf06Response = $input.first().json;

console.log('=== PREPARE WF06 AVAILABLE SLOTS V84 ===');
console.log('Input:', JSON.stringify(wf06Response, null, 2));

// Validar resposta do WF06
if (!wf06Response) {
  console.error('ERROR: No response from WF06');
  throw new Error('WF06 returned empty response');
}

// Extrair 'slots' array (FORMATO CORRETO)
let slotsData;
if (wf06Response.slots) {
  // Resposta direta do WF06 com 'slots' property
  slotsData = wf06Response.slots;
} else if (wf06Response.json && wf06Response.json.slots) {
  // Resposta wrapeada
  slotsData = wf06Response.json.slots;
} else if (wf06Response.available_slots) {
  // Fallback: talvez WF06 retorne 'available_slots' para este endpoint
  slotsData = wf06Response.available_slots;
} else if (wf06Response.json && wf06Response.json.available_slots) {
  slotsData = wf06Response.json.available_slots;
} else {
  console.error('ERROR: No slots or available_slots in response');
  console.error('Response keys:', Object.keys(wf06Response));
  throw new Error('Invalid WF06 response format - missing slots property');
}

// Validar estrutura
if (!Array.isArray(slotsData) || slotsData.length === 0) {
  console.error('ERROR: slots not array or empty');
  console.error('Received slots:', slotsData);
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

    # ====================
    # PASSO 4: Atualizar Prepare nodes
    # ====================
    for node in workflow['nodes']:
        if node['name'] == 'Prepare WF06 Next Dates Data':
            node['parameters']['jsCode'] = prepare_next_code
            print("  ✅ Prepare Next Dates atualizado para extrair 'dates' property")
        elif node['name'] == 'Prepare WF06 Available Slots Data':
            node['parameters']['jsCode'] = prepare_slots_code
            print("  ✅ Prepare Available Slots atualizado para extrair 'slots' property")

    # ====================
    # PASSO 5: Salvar V84
    # ====================
    print(f"\n💾 Salvando V84: {output_file}")

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print(f"✅ V84 salvo com sucesso!")

    # ====================
    # PASSO 6: Estatísticas
    # ====================
    print("\n📊 ESTATÍSTICAS V84:")
    print(f"  Nodes: {len(workflow['nodes'])}")
    print(f"  Conexões: {len(workflow['connections'])}")
    print(f"  ID: {workflow['id']}")
    print(f"  Tags: {workflow['tags']}")

    print("\n✅ CORREÇÕES APLICADAS:")
    print("  1. Prepare Next Dates: Extrai 'dates' array (não 'dates_with_availability')")
    print("  2. Prepare Available Slots: Extrai 'slots' array (com fallback 'available_slots')")
    print("  3. Validação robusta: Suporta formato direto e wrapeado")
    print("  4. Logs detalhados: Console.log para troubleshooting")

    print("\n🎉 WF02 V84 GERADO COM SUCESSO!")
    print(f"\n📝 Próximo passo:")
    print(f"   1. Importe no n8n: {output_file}")
    print(f"   2. Ative o workflow")
    print(f"   3. Teste Service 1 (Solar) → Deve processar 'dates' array corretamente")
    print(f"   4. Verifique logs: docker logs -f e2bot-n8n-dev")

    return True

if __name__ == '__main__':
    import sys
    success = generate_wf02_v84()
    sys.exit(0 if success else 1)
