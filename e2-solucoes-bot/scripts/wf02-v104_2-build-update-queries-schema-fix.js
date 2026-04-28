// Build Update Queries - V104.2 (DATABASE STATE UPDATE FIX + SCHEMA FIX)
// Purpose: Fix state persistence by reading from collected_data.current_stage
// Critical Fix: Read state from collected_data to sync with V104 State Machine
// V104.2 Fix: Remove contact_phone column (does not exist in database schema)
const inputData = $input.first().json;

console.log('=== V104.2 BUILD UPDATE QUERIES - DATABASE STATE + SCHEMA FIX ===');

// V104.2 FIX: Declare query_correction_update at function scope
let query_correction_update = null;

console.log('Input keys:', Object.keys(inputData));

// Helper functions
const escapeSql = (str) => {
  if (str === null || str === undefined || str === '') return '';
  return String(str).replace(/'/g, "''");
};

const prepareJsonb = (obj) => {
  if (!obj || typeof obj !== 'object') return '{}';
  return JSON.stringify(obj).replace(/'/g, "''");
};

// Extract phone data
let phone_number = String(inputData.phone_number || '');
phone_number = phone_number.replace(/[^0-9]/g, '');

if (phone_number && !phone_number.startsWith('55')) {
  if (phone_number.length === 10 || phone_number.length === 11) {
    phone_number = '55' + phone_number;
  }
}

const phone_with_code = phone_number;
const phone_without_code = phone_number.startsWith('55') ? phone_number.substring(2) : phone_number;

// Extract other data
const response_text = escapeSql(inputData.response_text || 'Olá! Como posso ajudar?');

// V104.1 CRITICAL FIX: Read next_stage from collected_data FIRST (syncs with V104 State Machine)
// This ensures database updates with the SAME state that State Machine outputs
const collected_data = inputData.collected_data || {};
const next_stage = collected_data.current_stage ||      // V104.1: Primary source (State Machine V104 puts it here)
                   collected_data.next_stage ||         // V104.1: Fallback 1
                   inputData.next_stage ||              // V104.1: Fallback 2 (legacy)
                   inputData.current_state ||           // V104.1: Fallback 3
                   'greeting';                          // V104.1: Default

console.log('🔍 V104.1 CRITICAL FIX - State resolution:');
console.log('  collected_data.current_stage:', collected_data.current_stage);
console.log('  collected_data.next_stage:', collected_data.next_stage);
console.log('  inputData.next_stage:', inputData.next_stage);
console.log('  ✅ RESOLVED next_stage:', next_stage);

const collected_data_json = prepareJsonb(collected_data);
const message_content = escapeSql(inputData.message || '');
const message_type = inputData.message_type || 'text';
const message_id = inputData.message_id || '';
const conversation_id = inputData.conversation_id || null;

// Extract service_type from collected_data
const service_type = collected_data?.service_type || null;

// V104.2 NOTE: contact_phone column does NOT exist in conversations table
// Phone number is stored in phone_number column and collected_data JSONB field only

// State mapping
const state_mapping = {
  'greeting': 'novo',
  'service_selection': 'identificando_servico',
  'collect_name': 'coletando_dados',
  'collect_phone': 'coletando_dados',
  'collect_phone_whatsapp_confirmation': 'coletando_dados',
  'collect_phone_alternative': 'coletando_dados',
  'collect_email': 'coletando_dados',
  'collect_city': 'coletando_dados',
  'confirmation': 'coletando_dados',
  'trigger_wf06_next_dates': 'agendando',              // V104.1: WF06 intermediate state
  'show_available_dates': 'agendando',                 // V104.1: WF06 state
  'process_date_selection': 'agendando',               // V104.1: WF06 state
  'trigger_wf06_available_slots': 'agendando',         // V104.1: WF06 intermediate state
  'show_available_slots': 'agendando',                 // V104.1: WF06 state
  'process_slot_selection': 'agendando',               // V104.1: WF06 state
  'schedule_confirmation': 'agendando',                // V104.1: WF06 final state
  'scheduling': 'agendando',
  'handoff_comercial': 'handoff_comercial',
  'completed': 'concluido'
};

const db_state = state_mapping[next_stage] || 'novo';

console.log('✅ V104.2: Building queries with state from collected_data');
console.log('  state_machine_state will be:', next_stage);
console.log('  current_state will be:', db_state);

// Query 1: Update Conversation State (V104.2 - state from collected_data + schema fix)
const query_update_conversation = `
INSERT INTO conversations (
  phone_number,
  whatsapp_name,
  current_state,
  state_machine_state,
  collected_data,
  service_type,
  contact_name,
  contact_email,
  city,
  status,
  last_message_at,
  created_at,
  updated_at
) VALUES (
  '${phone_with_code}',
  '${escapeSql(collected_data?.lead_name || '')}',
  '${db_state}',
  '${next_stage}',
  '${collected_data_json}'::jsonb,
  ${service_type ? "'" + escapeSql(service_type) + "'" : 'NULL'},
  '${escapeSql(collected_data?.lead_name || '')}',
  '${escapeSql(collected_data?.email || '')}',
  '${escapeSql(collected_data?.city || '')}',
  'active',
  NOW(),
  NOW(),
  NOW()
)
ON CONFLICT (phone_number)
DO UPDATE SET
  current_state = EXCLUDED.current_state,
  state_machine_state = EXCLUDED.state_machine_state,
  collected_data = conversations.collected_data || EXCLUDED.collected_data,
  service_type = COALESCE(EXCLUDED.service_type, conversations.service_type),
  contact_name = COALESCE(NULLIF(EXCLUDED.contact_name, ''), conversations.contact_name),
  contact_email = COALESCE(NULLIF(EXCLUDED.contact_email, ''), conversations.contact_email),
  city = COALESCE(NULLIF(EXCLUDED.city, ''), conversations.city),
  whatsapp_name = COALESCE(NULLIF(EXCLUDED.whatsapp_name, ''), conversations.whatsapp_name),
  last_message_at = NOW(),
  updated_at = NOW()
RETURNING *`.trim();

console.log('✅ V104.2: UPSERT query with state from collected_data.current_stage (schema-compliant)');

// Query 2: Save Inbound Message
const query_save_inbound = `
INSERT INTO messages (
  conversation_id,
  direction,
  content,
  message_type,
  whatsapp_message_id,
  created_at
)
VALUES (
  (SELECT id FROM conversations WHERE phone_number IN ('${phone_with_code}', '${phone_without_code}') ORDER BY updated_at DESC LIMIT 1),
  'inbound',
  '${message_content}',
  '${message_type}',
  '${message_id}',
  NOW()
)
ON CONFLICT (whatsapp_message_id)
WHERE whatsapp_message_id IS NOT NULL AND whatsapp_message_id != ''
DO NOTHING
RETURNING *`.trim();

// Query 3: Save Outbound Message
const query_save_outbound = `
INSERT INTO messages (
  conversation_id,
  direction,
  content,
  message_type,
  whatsapp_message_id,
  created_at
)
VALUES (
  (SELECT id FROM conversations WHERE phone_number IN ('${phone_with_code}', '${phone_without_code}') ORDER BY updated_at DESC LIMIT 1),
  'outbound',
  '${response_text}',
  'text',
  'out_' || extract(epoch from NOW())::bigint || '_' || random()::text,
  NOW()
)
RETURNING *`.trim();

// Query 4: Upsert Lead Data
const query_upsert_lead = `
WITH existing_lead AS (
  SELECT id
  FROM leads
  WHERE phone_number IN ('${phone_with_code}', '${phone_without_code}')
  LIMIT 1
),
updated AS (
  UPDATE leads
  SET
    name = COALESCE(NULLIF('${escapeSql(collected_data?.lead_name || '')}', ''), name),
    email = COALESCE(NULLIF('${escapeSql(collected_data?.email || '')}', ''), email),
    city = COALESCE(NULLIF('${escapeSql(collected_data?.city || '')}', ''), city),
    service_type = COALESCE(NULLIF('${escapeSql(collected_data?.service_type || '')}', ''), service_type),
    service_details = '${collected_data_json}'::jsonb,
    updated_at = NOW()
  WHERE id IN (SELECT id FROM existing_lead)
  RETURNING *, 'updated' as operation
),
inserted AS (
  INSERT INTO leads (
    phone_number,
    name,
    email,
    city,
    service_type,
    service_details,
    created_at,
    updated_at
  )
  SELECT
    '${phone_with_code}',
    '${escapeSql(collected_data?.lead_name || '')}',
    '${escapeSql(collected_data?.email || '')}',
    '${escapeSql(collected_data?.city || '')}',
    '${escapeSql(collected_data?.service_type || '')}',
    '${collected_data_json}'::jsonb,
    NOW(),
    NOW()
  WHERE NOT EXISTS (SELECT 1 FROM existing_lead)
  RETURNING *, 'inserted' as operation
)
SELECT * FROM updated
UNION ALL
SELECT * FROM inserted`.trim();

console.log('✅ V104.2: All queries built (schema-compliant)');

// V104.2: Correction UPDATE Query Builder (contact_phone removed - does not exist in schema)
if (inputData.needs_db_update && inputData.update_field) {
  console.log('V104.2: Building correction UPDATE query for field:', inputData.update_field);

  const fieldConfig = {
    'lead_name': { db_column: 'contact_name', jsonb_key: 'lead_name' },
    // V104.2: contact_phone removed - column does not exist in conversations table
    'email': { db_column: 'contact_email', jsonb_key: 'email' },
    'city': { db_column: 'city', jsonb_key: 'city' }
  };

  const config = fieldConfig[inputData.update_field];
  const newValue = escapeSql(inputData[inputData.update_field] || '');

  let additionalUpdates = '';
  if (config.also_update) {
    const additionalValue = escapeSql(inputData[config.also_update] || newValue);
    additionalUpdates = `${config.also_update} = '${additionalValue}',`;
  }

  query_correction_update = `
UPDATE conversations
SET
  ${config.db_column} = '${newValue}',
  ${additionalUpdates}
  collected_data = jsonb_set(
    collected_data,
    '{${config.jsonb_key}}',
    to_jsonb('${newValue}')
  ),
  current_state = 'coletando_dados',
  state_machine_state = 'confirmation',
  updated_at = NOW()
WHERE conversation_id = '${conversation_id}'
  AND phone_number IN ('${phone_with_code}', '${phone_without_code}')
RETURNING conversation_id, phone_number, collected_data,
          ${config.db_column} as corrected_field, current_state,
          state_machine_state, updated_at
  `.trim();

  console.log('V104.2: Correction UPDATE query built for field:', inputData.update_field);
}

// V104.2 DEBUG: Log final state values
console.log('V104.2 DEBUG - Final state values:', {
  next_stage: next_stage,
  db_state: db_state,
  service_selected: collected_data.service_selected,
  status: collected_data.status
});

console.log('✅ V104.2 BUILD UPDATE QUERIES COMPLETE - State from collected_data + schema-compliant');

// Return all queries and data
return {
  query_correction_update: query_correction_update || null,
  correction_field_updated: inputData.update_field || null,
  phone_number: phone_with_code,
  phone_with_code: phone_with_code,
  phone_without_code: phone_without_code,
  response_text: inputData.response_text,
  next_stage: next_stage,  // V104.1 FIX: Now reads from collected_data
  collected_data: collected_data,
  conversation_id: conversation_id,
  message: inputData.message,
  message_type: message_type,
  message_id: message_id,

  // Queries SQL
  query_update_conversation,
  query_save_inbound,
  query_save_outbound,
  query_upsert_lead,

  // V104.2 metadata
  v104_2_applied: true,
  state_from_collected_data: true,
  schema_compliant: true,
  timestamp: new Date().toISOString()
};
