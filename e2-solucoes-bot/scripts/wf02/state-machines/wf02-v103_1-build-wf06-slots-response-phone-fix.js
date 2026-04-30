// WF02 V103.1 - Build WF06 Slots Response Message with Phone Number Preservation
// Purpose: Format WF06 available slots for WhatsApp without triggering State Machine
// V103.1 FIX: Add phone_number fallback chain to prevent "Bad request" errors

const input = $input.first().json;
const slots = input.wf06_available_slots || [];
const selectedDate = input.selected_date || 'Data selecionada';

console.log('=== BUILD WF06 SLOTS RESPONSE MESSAGE V103.1 ===');
console.log('Input keys:', Object.keys(input));
console.log('Input phone_number:', input.phone_number);
console.log('WF06 slots count:', slots.length);
console.log('Selected date:', selectedDate);

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

// Handle empty slots
if (!slots || slots.length === 0) {
  console.log('⚠️ No slots available for selected date');
  return {
    json: {
      phone_number: phoneNumber,
      response_text: '⚠️ Não há horários disponíveis para a data selecionada.\n\n📞 Entre em contato: (62) 3092-2900'
    }
  };
}

// Build slot options message
let slotOptions = '';
slots.forEach((slot, index) => {
  const number = index + 1;
  slotOptions += `${number}️⃣ *${slot.time}* (${slot.duration}min)\n`;
});

const responseText = `🕐 *Horários Disponíveis*\n\n` +
                    `📅 Data: *${selectedDate}*\n\n` +
                    `⏰ *Escolha um horário:*\n\n` +
                    slotOptions +
                    `\n💡 *Digite o número do horário desejado (1-${slots.length})*`;

console.log('✅ Slots response message built successfully');
console.log('✅ Phone number preserved:', phoneNumber);
console.log('Message length:', responseText.length);

return {
  json: {
    phone_number: phoneNumber,           // V103.1: With fallback chain
    response_text: responseText,
    slot_options: slots,
    selected_date: selectedDate
  }
};
