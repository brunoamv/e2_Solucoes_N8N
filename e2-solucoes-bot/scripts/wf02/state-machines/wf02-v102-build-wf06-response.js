// WF02 V102 - Build WF06 Response Message
// Purpose: Format WF06 calendar dates for WhatsApp without triggering State Machine
// This fixes the double State Machine execution bug

const input = $input.first().json;
const dates = input.wf06_next_dates || [];

console.log('=== BUILD WF06 RESPONSE MESSAGE V102 ===');
console.log('Input phone_number:', input.phone_number);
console.log('WF06 dates count:', dates.length);

// Handle empty calendar
if (!dates || dates.length === 0) {
  console.log('⚠️ No dates available from WF06');
  return {
    json: {
      phone_number: input.phone_number,
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
console.log('Message length:', responseText.length);

return {
  json: {
    phone_number: input.phone_number,
    response_text: responseText,
    date_suggestions: dates
  }
};
