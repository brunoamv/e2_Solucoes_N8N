// WF02 V103.1 - Build WF06 Response Message with Phone Number Preservation
// Purpose: Format WF06 calendar dates for WhatsApp without triggering State Machine
// V103.1 FIX: Add phone_number fallback chain to prevent "Bad request" errors

const input = $input.first().json;
const dates = input.wf06_next_dates || [];

console.log('=== BUILD WF06 RESPONSE MESSAGE V103.1 ===');
console.log('Input keys:', Object.keys(input));
console.log('Input phone_number:', input.phone_number);
console.log('WF06 dates count:', dates.length);

// CRITICAL V103.1 FIX: Extract phone_number with fallback chain
// After removing parallel connection, phone_number may not be in $input
// Fallback to Build Update Queries node which always has phone_number
const phoneNumber = input.phone_number
                 || input.phone_with_code
                 || input.phone_without_code
                 || $node["Build Update Queries"].json.phone_number
                 || $node["Build Update Queries"].json.phone_with_code;

console.log('🔍 Phone number resolved:', phoneNumber);

if (!phoneNumber) {
  console.error('❌ CRITICAL: No phone_number found!');
  console.error('Input data:', JSON.stringify(input, null, 2));
  console.error('Build Update Queries:', JSON.stringify($node["Build Update Queries"].json, null, 2));
}

// Handle empty calendar
if (!dates || dates.length === 0) {
  console.log('⚠️ No dates available from WF06');
  return {
    json: {
      phone_number: phoneNumber,
      response_text: '⚠️ Não encontramos horários disponíveis no momento.\n\n📞 Entre em contato: (62) 3092-2900'
    }
  };
}

// Build date options message
let dateOptions = '';
dates.forEach((dateObj, index) => {
  const number = index + 1;
  const qualityEmoji = dateObj.quality === 'high' ? '✨' :
                      dateObj.quality === 'medium' ? '📅' : '⚠️';
  dateOptions += `${number}️⃣ *${dateObj.display}*\n   🕐 ${dateObj.total_slots} horários livres ${qualityEmoji}\n\n`;
});

const responseText = `📅 *Agendar Visita Técnica*\n\n` +
                    `📆 *Próximas datas disponíveis:*\n\n` +
                    dateOptions +
                    `💡 *Escolha uma opção (1-3)*\n` +
                    `_Digite o número da data desejada_`;

console.log('✅ Response message built successfully');
console.log('✅ Phone number preserved:', phoneNumber);
console.log('Message length:', responseText.length);

return {
  json: {
    phone_number: phoneNumber,           // V103.1: With fallback chain
    response_text: responseText,
    date_suggestions: dates
  }
};
