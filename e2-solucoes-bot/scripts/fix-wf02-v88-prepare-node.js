// Prepare WF06 Next Dates Response V88
// FIX: Preserva dados do usuário (phone_number, conversation_id, etc.) do HTTP Request input
// ANTES V87: Retornava APENAS {wf06_next_dates} → phone_number perdido no Merge
// DEPOIS V88: Retorna input completo + wf06_next_dates → phone_number preservado

// IMPORTANTE: Este node recebe dados do "HTTP Request - Get Next Dates"
// que contém: phone_number, phone_with_code, conversation_id, message, etc.

const httpResponse = $input.first().json;
const inputData = $input.first().json; // V88: Preservar TODOS os dados de entrada

console.log('=== PREPARE WF06 NEXT DATES V88 (DATA PRESERVATION FIX) ===');
console.log('Full inputData keys:', Object.keys(inputData));
console.log('Has phone_number:', !!inputData.phone_number);
console.log('Has conversation_id:', !!inputData.conversation_id);

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

// V88 FIX: Preservar TODOS os dados de entrada + adicionar wf06_next_dates
// Isso garante que phone_number, conversation_id, etc. sejam passados para o Merge
const preparedData = {
  ...inputData,  // V88: Preserva phone_number, conversation_id, message, etc.
  wf06_next_dates: datesData  // Adiciona resposta do WF06
};

console.log('✅ V88 Data preservation:');
console.log('  - phone_number:', preparedData.phone_number);
console.log('  - conversation_id:', preparedData.conversation_id);
console.log('  - wf06_next_dates count:', preparedData.wf06_next_dates.length);

return preparedData;
