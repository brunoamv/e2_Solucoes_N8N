// FIX WF02 V101 - Prepare WF06 Next Dates Data - User Data Preservation
// Problem: After HTTP Request node, $input.first().json only contains HTTP response
//          User data (phone_number, conversation_id, collected_data) is LOST
// Solution: Explicitly get user data from "Build Update Queries" node using $node["Build Update Queries"].json

const httpResponse = $input.first().json;

// V101 FIX: Get user data from Build Update Queries node (BEFORE HTTP Request)
// This is CRITICAL because HTTP Request node replaces $input with HTTP response only
const userData = $node["Build Update Queries"].json;

console.log('=== PREPARE WF06 NEXT DATES V101 (USER DATA PRESERVATION FIX) ===');
console.log('HTTP Response keys:', Object.keys(httpResponse));
console.log('User Data keys:', Object.keys(userData));
console.log('User phone_number:', userData.phone_number);
console.log('User conversation_id:', userData.conversation_id);
console.log('User collected_data exists:', !!userData.collected_data);

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

// V101 FIX: Merge user data from Build Update Queries + WF06 response
// This preserves phone_number, conversation_id, collected_data, etc.
const preparedData = {
  ...userData,  // V101: User data from BEFORE HTTP Request (phone_number, conversation_id, etc.)
  wf06_next_dates: datesData  // WF06 response dates
};

console.log('✅ V101 User Data Preservation:');
console.log('  - phone_number:', preparedData.phone_number);
console.log('  - phone_with_code:', preparedData.phone_with_code);
console.log('  - conversation_id:', preparedData.conversation_id);
console.log('  - next_stage:', preparedData.next_stage);
console.log('  - response_text:', preparedData.response_text ? 'exists' : 'missing');
console.log('  - collected_data exists:', !!preparedData.collected_data);
console.log('  - wf06_next_dates count:', preparedData.wf06_next_dates.length);
console.log('=== V101 PREPARE WF06 COMPLETE ===');

return preparedData;
