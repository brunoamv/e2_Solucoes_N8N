// Prepare WF06 Available Slots Response V88
// FIX: Preserva dados do usuário (phone_number, conversation_id, etc.) do HTTP Request input
// ANTES V87: Retornava APENAS {wf06_available_slots} → phone_number perdido no Merge
// DEPOIS V88: Retorna input completo + wf06_available_slots → phone_number preservado

const httpResponse = $input.first().json;
const inputData = $input.first().json; // V88: Preservar TODOS os dados de entrada

console.log('=== PREPARE WF06 AVAILABLE SLOTS V88 (DATA PRESERVATION FIX) ===');
console.log('Full inputData keys:', Object.keys(inputData));
console.log('Has phone_number:', !!inputData.phone_number);
console.log('Has conversation_id:', !!inputData.conversation_id);

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

// V88 FIX: Preservar TODOS os dados de entrada + adicionar wf06_available_slots
const preparedData = {
  ...inputData,  // V88: Preserva phone_number, conversation_id, message, etc.
  wf06_available_slots: slotsData  // Adiciona resposta do WF06
};

console.log('✅ V88 Data preservation:');
console.log('  - phone_number:', preparedData.phone_number);
console.log('  - conversation_id:', preparedData.conversation_id);
console.log('  - wf06_available_slots count:', preparedData.wf06_available_slots.length);

return preparedData;
