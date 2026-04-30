// Build Update Queries - V79.1 (SCHEMA-ALIGNED FIX)
// ===================================================
// CRITICAL FIX: Remove contact_phone column (does not exist in PostgreSQL schema)
//
// PostgreSQL Schema Analysis:
// ✅ phone_number (exists)
// ✅ contact_name (exists)
// ✅ contact_email (exists)
// ❌ contact_phone (DOES NOT EXIST!)
//
// Reason V74 "works": ON CONFLICT may be silently ignoring the error
// V79.1 Fix: Remove contact_phone from INSERT and UPDATE statements
//
// Date: 2026-04-13
// Version: V79.1 Schema-Aligned Fix
// ===================================================

const inputData = $input.first().json;

console.log('=== V79.1 BUILD UPDATE QUERIES (SCHEMA-ALIGNED) ===');

// V66 FIX: Declare query_correction_update at function scope
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
const next_stage = inputData.next_stage || inputData.current_state || 'greeting';
const collected_data = inputData.collected_data || {};
const collected_data_json = prepareJsonb(collected_data);
const message_content = escapeSql(inputData.message || '');
const message_type = inputData.message_type || 'text';
const message_id = inputData.message_id || '';
const conversation_id = inputData.conversation_id || null;

// Extract service_type from collected_data
const service_type = collected_data?.service_type || null;
console.log('V79.1: service_type extracted:', service_type);

// V79.1 FIX: Store contact_phone in collected_data JSONB only (no DB column)
const contact_phone = collected_data?.contact_phone ||
                     collected_data?.phone_primary ||
                     collected_data?.phone ||
                     '';
console.log('V79.1: contact_phone extracted (JSONB only):', contact_phone);

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
  'scheduling': 'agendando',
  'handoff_comercial': 'handoff_comercial',
  'completed': 'concluido'
};

const db_state = state_mapping[next_stage] || 'novo';

console.log('V79.1: Building queries with SCHEMA-ALIGNED fix (no contact_phone column)');

// ===================================================
// Query 1: Update Conversation State (V79.1 SCHEMA-ALIGNED)
// ===================================================
// REMOVED: contact_phone column (does not exist in PostgreSQL)
// PRESERVED: All other columns that exist in schema
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

console.log('✅ V79.1: UPSERT query SCHEMA-ALIGNED (no contact_phone column)');

// Query 2: Save Inbound Message (unchanged)
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

// Query 3: Save Outbound Message (unchanged)
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

// Query 4: Upsert Lead Data (unchanged)
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

console.log('✅ V79.1: All queries built with SCHEMA-ALIGNED fix');

  // V66: Correction UPDATE Query Builder
  // V79.1 FIX: Remove contact_phone from correction logic (column does not exist)
  if (inputData.needs_db_update && inputData.update_field) {
    console.log('V79.1: Building correction UPDATE query for field:', inputData.update_field);

    const fieldConfig = {
      'lead_name': { db_column: 'contact_name', jsonb_key: 'lead_name' },
      // V79.1 REMOVED: contact_phone (no DB column)
      'email': { db_column: 'contact_email', jsonb_key: 'email' },
      'city': { db_column: 'city', jsonb_key: 'city' }
    };

    const config = fieldConfig[inputData.update_field];

    if (!config) {
      console.warn('V79.1: Field not supported for correction:', inputData.update_field);
      query_correction_update = null;
    } else {
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

      console.log('V79.1: Correction UPDATE query built for field:', inputData.update_field);
    }
  }

  // V68 DEBUG: Log trigger check data
  console.log('V79.1 DEBUG - Trigger check:', {
    next_stage: inputData.next_stage,
    service_selected: collected_data.service_selected,
    status: collected_data.status
  });

  // V79.1 RETURN
  return {
    query_correction_update: query_correction_update || null,
    correction_field_updated: inputData.update_field || null,
  phone_number: phone_with_code,
  phone_with_code: phone_with_code,
  phone_without_code: phone_without_code,
  response_text: inputData.response_text,
  next_stage: inputData.next_stage,
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

  // V79.1 metadata
  v79_1_schema_aligned: true,
  v79_1_contact_phone_removed: true,  // Stored in JSONB only
  timestamp: new Date().toISOString()
};
