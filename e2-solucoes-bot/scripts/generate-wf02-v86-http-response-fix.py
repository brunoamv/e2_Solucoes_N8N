#!/usr/bin/env python3
"""
Gera WF02 V86 - Correção do HTTP Response Wrapping

DESCOBERTA CRÍTICA (V85):
- WF06 retorna formato correto: {success, action, dates: [...], total_available}
- HTTP Request node do n8n TRANSFORMA a resposta antes de passar adiante
- Prepare node precisa verificar MÚLTIPLAS propriedades de acesso

PROBLEMA REAL:
- n8n HTTP Request node v3 pode wrapar resposta de webhook em estruturas diferentes
- Não é só 'dates' vs 'dates_with_availability'
- É sobre COMO ACESSAR a resposta dentro do objeto do n8n

SOLUÇÃO V86:
- Adicionar verificação COMPLETA de todas propriedades possíveis
- Verificar: response direto, body, data, json wrapeado, e mais
- Logs ainda mais detalhados para capturar estrutura REAL
"""

import json
import uuid
from pathlib import Path

def generate_wf02_v86():
    """Gera workflow V86 com correção completa do HTTP Response wrapping"""

    base_dir = Path(__file__).parent.parent
    input_file = base_dir / 'n8n/workflows/02_ai_agent_conversation_V85_DIAGNOSTIC.json'
    output_file = base_dir / 'n8n/workflows/02_ai_agent_conversation_V86_HTTP_RESPONSE_FIX.json'

    print("📖 Lendo V85 DIAGNOSTIC...")
    with open(input_file, 'r', encoding='utf-8') as f:
        workflow = json.load(f)

    print(f"✅ Carregado: {len(workflow['nodes'])} nodes")

    # ====================
    # PASSO 1: Novo ID e Metadata
    # ====================
    old_id = workflow['id']
    new_id = str(uuid.uuid4()).replace('-', '')[:20]
    workflow['id'] = new_id
    workflow['name'] = '02_ai_agent_conversation_V86_HTTP_RESPONSE_FIX'
    workflow['tags'] = ['V86', 'WF06-Integration', 'HTTP-Response-Fix']

    print(f"🆔 ID: {old_id} → {new_id}")
    print(f"📝 Name: {workflow['name']}")

    # ====================
    # PASSO 2: Atualizar Prepare WF06 Next Dates Data
    # ====================
    print("\n🔧 Atualizando Prepare WF06 Next Dates Data com acesso COMPLETO...")

    prepare_next_code = """// Prepare WF06 Next Dates Response V86
// CORREÇÃO COMPLETA: Acessa resposta do HTTP Request de TODAS as formas possíveis

const httpResponse = $input.first().json;

console.log('=== PREPARE WF06 NEXT DATES V86 (COMPLETE FIX) ===');
console.log('Full httpResponse:', JSON.stringify(httpResponse, null, 2));
console.log('Type:', typeof httpResponse);
console.log('Keys:', Object.keys(httpResponse));

// Validar resposta existe
if (!httpResponse) {
  console.error('ERROR: No httpResponse from HTTP Request node');
  throw new Error('HTTP Request returned empty response');
}

// Extrair 'dates' array - TODAS as possibilidades de acesso
let datesData = null;
let accessPath = '';

// 1. Acesso direto ao root
if (httpResponse.dates && Array.isArray(httpResponse.dates)) {
  datesData = httpResponse.dates;
  accessPath = 'httpResponse.dates';
  console.log('✅ Found dates at ROOT level');
}
// 2. Propriedade 'json' wrapeada (comum em n8n)
else if (httpResponse.json && httpResponse.json.dates) {
  datesData = httpResponse.json.dates;
  accessPath = 'httpResponse.json.dates';
  console.log('✅ Found dates in WRAPPED .json property');
}
// 3. Propriedade 'body' (algumas versões n8n)
else if (httpResponse.body) {
  console.log('Found .body property, parsing...');
  const bodyData = typeof httpResponse.body === 'string' ? JSON.parse(httpResponse.body) : httpResponse.body;
  if (bodyData.dates) {
    datesData = bodyData.dates;
    accessPath = 'httpResponse.body.dates';
    console.log('✅ Found dates in .body property');
  }
}
// 4. Propriedade 'data' (outro padrão comum)
else if (httpResponse.data && httpResponse.data.dates) {
  datesData = httpResponse.data.dates;
  accessPath = 'httpResponse.data.dates';
  console.log('✅ Found dates in .data property');
}
// 5. Response direta é o JSON do WF06 (raro mas possível)
else if (httpResponse.success && httpResponse.dates) {
  datesData = httpResponse.dates;
  accessPath = 'httpResponse.dates (WF06 direct)';
  console.log('✅ Found dates in WF06 direct format');
}

// Se não encontrou, logar estrutura completa e falhar
if (!datesData) {
  console.error('❌ ERROR: Could not find dates property in ANY expected location');
  console.error('Response structure:', JSON.stringify(httpResponse, null, 2));
  console.error('Checked paths: root.dates, json.dates, body.dates, data.dates, direct WF06');
  throw new Error('Invalid WF06 response format - missing dates property in all locations');
}

// Validar estrutura
if (!Array.isArray(datesData)) {
  console.error('ERROR: dates is not an array');
  console.error('Received type:', typeof datesData);
  console.error('Received value:', datesData);
  throw new Error('WF06 returned dates in invalid format (not array)');
}

if (datesData.length === 0) {
  console.error('ERROR: dates array is empty');
  throw new Error('WF06 returned empty dates array');
}

console.log(`✅ SUCCESS: Received ${datesData.length} dates with availability`);
console.log(`Access path used: ${accessPath}`);

// Preparar dados para State Machine
// WF06 V2.1 retorna: {date, display, day_of_week, total_slots, quality, slots: [...]}
const preparedData = {
  wf06_next_dates: datesData
};

console.log('Prepared data structure:', JSON.stringify(preparedData, null, 2));

return preparedData;
"""

    # ====================
    # PASSO 3: Atualizar Prepare WF06 Available Slots Data
    # ====================
    print("🔧 Atualizando Prepare WF06 Available Slots Data com acesso COMPLETO...")

    prepare_slots_code = """// Prepare WF06 Available Slots Response V86
// CORREÇÃO COMPLETA: Acessa resposta do HTTP Request de TODAS as formas possíveis

const httpResponse = $input.first().json;

console.log('=== PREPARE WF06 AVAILABLE SLOTS V86 (COMPLETE FIX) ===');
console.log('Full httpResponse:', JSON.stringify(httpResponse, null, 2));
console.log('Type:', typeof httpResponse);
console.log('Keys:', Object.keys(httpResponse));

// Validar resposta existe
if (!httpResponse) {
  console.error('ERROR: No httpResponse from HTTP Request node');
  throw new Error('HTTP Request returned empty response');
}

// Extrair 'slots' array - TODAS as possibilidades de acesso
let slotsData = null;
let accessPath = '';

// 1. Acesso direto ao root (formato WF06 V2.1)
if (httpResponse.slots && Array.isArray(httpResponse.slots)) {
  slotsData = httpResponse.slots;
  accessPath = 'httpResponse.slots';
  console.log('✅ Found slots at ROOT level');
}
// 2. Propriedade 'json' wrapeada
else if (httpResponse.json && httpResponse.json.slots) {
  slotsData = httpResponse.json.slots;
  accessPath = 'httpResponse.json.slots';
  console.log('✅ Found slots in WRAPPED .json property');
}
// 3. Propriedade 'body'
else if (httpResponse.body) {
  console.log('Found .body property, parsing...');
  const bodyData = typeof httpResponse.body === 'string' ? JSON.parse(httpResponse.body) : httpResponse.body;
  if (bodyData.slots) {
    slotsData = bodyData.slots;
    accessPath = 'httpResponse.body.slots';
    console.log('✅ Found slots in .body property');
  }
}
// 4. Propriedade 'data'
else if (httpResponse.data && httpResponse.data.slots) {
  slotsData = httpResponse.data.slots;
  accessPath = 'httpResponse.data.slots';
  console.log('✅ Found slots in .data property');
}
// 5. Response direta WF06 format
else if (httpResponse.success && httpResponse.slots) {
  slotsData = httpResponse.slots;
  accessPath = 'httpResponse.slots (WF06 direct)';
  console.log('✅ Found slots in WF06 direct format');
}
// 6. Fallback: WF06 pode retornar 'available_slots' para este endpoint
else if (httpResponse.available_slots && Array.isArray(httpResponse.available_slots)) {
  slotsData = httpResponse.available_slots;
  accessPath = 'httpResponse.available_slots';
  console.log('⚠️ Found available_slots (fallback format)');
}

// Se não encontrou, logar estrutura completa e falhar
if (!slotsData) {
  console.error('❌ ERROR: Could not find slots/available_slots property in ANY expected location');
  console.error('Response structure:', JSON.stringify(httpResponse, null, 2));
  console.error('Checked paths: root.slots, json.slots, body.slots, data.slots, available_slots');
  throw new Error('Invalid WF06 response format - missing slots property in all locations');
}

// Validar estrutura
if (!Array.isArray(slotsData)) {
  console.error('ERROR: slots is not an array');
  console.error('Received type:', typeof slotsData);
  console.error('Received value:', slotsData);
  throw new Error('WF06 returned slots in invalid format (not array)');
}

if (slotsData.length === 0) {
  console.error('ERROR: slots array is empty');
  throw new Error('WF06 returned empty slots array');
}

console.log(`✅ SUCCESS: Received ${slotsData.length} available slots`);
console.log(`Access path used: ${accessPath}`);

// Preparar dados para State Machine
const preparedData = {
  wf06_available_slots: slotsData
};

console.log('Prepared data structure:', JSON.stringify(preparedData, null, 2));

return preparedData;
"""

    # ====================
    # PASSO 4: Atualizar Prepare nodes
    # ====================
    for node in workflow['nodes']:
        if node['name'] == 'Prepare WF06 Next Dates Data':
            node['parameters']['jsCode'] = prepare_next_code
            print("  ✅ Prepare Next Dates: COMPLETE access path checking")
        elif node['name'] == 'Prepare WF06 Available Slots Data':
            node['parameters']['jsCode'] = prepare_slots_code
            print("  ✅ Prepare Available Slots: COMPLETE access path checking")

    # ====================
    # PASSO 5: Salvar V86
    # ====================
    print(f"\n💾 Salvando V86: {output_file}")

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    print(f"✅ V86 salvo com sucesso!")

    # ====================
    # PASSO 6: Estatísticas
    # ====================
    print("\n📊 ESTATÍSTICAS V86:")
    print(f"  Nodes: {len(workflow['nodes'])}")
    print(f"  Conexões: {len(workflow['connections'])}")
    print(f"  ID: {workflow['id']}")
    print(f"  Tags: {workflow['tags']}")

    print("\n✅ CORREÇÕES APLICADAS V86:")
    print("  1. COMPLETE HTTP Response access path checking")
    print("  2. Verifica: root.dates, json.dates, body.dates, data.dates, WF06 direct")
    print("  3. Logs mostram QUAL path funcionou (access path)")
    print("  4. Validação robusta de tipo e estrutura")
    print("  5. Mensagens de erro ultra-detalhadas")

    print("\n🎯 DIFERENÇA V85 → V86:")
    print("  V85: Verificava 2 paths (root + json wrapeado)")
    print("  V86: Verifica 6 paths + logs do path usado")
    print("  V86: Considera que n8n HTTP Request pode wrapar de várias formas")

    print("\n🎉 WF02 V86 HTTP RESPONSE FIX GERADO COM SUCESSO!")
    print(f"\n📝 Próximo passo:")
    print(f"   1. Importe no n8n: {output_file}")
    print(f"   2. Ative o workflow")
    print(f"   3. Execute teste com Service 1 (Solar)")
    print(f"   4. Verifique logs: docker logs -f e2bot-n8n-dev")
    print(f"   5. Logs mostrarão EXATAMENTE qual access path funcionou!")
    print(f"   6. Se ainda falhar, logs mostrarão estrutura COMPLETA da resposta")

    return True

if __name__ == '__main__':
    import sys
    success = generate_wf02_v86()
    sys.exit(0 if success else 1)
