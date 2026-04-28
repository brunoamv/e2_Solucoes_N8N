// Build Update Queries2 - WF06 Available Slots State Update
// Prepares data for updating state after showing WF06 available time slots to user
//
// PURPOSE: After showing time slots from WF06, update database to:
// - state_machine_state = "show_available_slots"
// - collected_data.current_stage = "show_available_slots"
// - collected_data.awaiting_wf06_available_slots = true
// - collected_data.slot_suggestions = [array of slots] ✅ CRITICAL FIX
//
// This ensures when user sends next message (slot selection),
// State Machine knows to process it as slot selection, not as error.
//
// DATA SOURCE: Uses explicit node reference to get phone_number and slot_suggestions
// This is more reliable than using $input because HTTP Request nodes
// replace the data with their response.

// Get phone number AND slot_suggestions from explicit node reference
// "Build WF06 Available SLOTS Response Message" node has the original data
const responseData = $node["Build WF06 Available SLOTS Response Message"].json;
const phone_number = responseData.phone_number;
const slot_suggestions = responseData.slot_suggestions || [];

// Validate phone number exists
if (!phone_number) {
  console.error('Build Update Queries2: No phone_number found!');
  console.error('Build Update Queries2: Response data:', responseData);
  console.error('Build Update Queries2: Available keys:', Object.keys(responseData));
  throw new Error('Phone number is required for state update');
}

// Serialize slot_suggestions array to JSON string for PostgreSQL
// PostgreSQL needs JSON string, not JavaScript object
// Single quotes must be escaped as '' for SQL string safety
const slotSuggestionsJson = JSON.stringify(slot_suggestions).replace(/'/g, "''");

// Build SQL query for state update
// ✅ CRITICAL FIX: Added slot_suggestions to collected_data JSONB field
const update_query = `
UPDATE conversations
SET
  state_machine_state = 'show_available_slots',
  collected_data = jsonb_set(
    jsonb_set(
      jsonb_set(
        collected_data,
        '{current_stage}',
        '"show_available_slots"'
      ),
      '{awaiting_wf06_available_slots}',
      'true'
    ),
    '{slot_suggestions}',
    '${slotSuggestionsJson}'::jsonb
  ),
  updated_at = NOW()
WHERE phone_number = '${phone_number.replace(/'/g, "''")}'
RETURNING *;
`.trim();

// Log for debugging
console.log('=== Build Update Queries2 (V113) ===');
console.log('Phone number:', phone_number);
console.log('Setting state to: show_available_slots');
console.log('Setting awaiting_wf06_available_slots: true');
console.log('✅ CRITICAL FIX: Saving slot_suggestions to database:', slot_suggestions.length, 'slots');
console.log('Data source: Build WF06 Available SLOTS Response Message node');

// Return data for Update Conversation State2 node
return [{
  json: {
    // Add query for PostgreSQL node
    update_query: update_query,

    // Explicitly set phone_number for reference
    phone_number: phone_number,

    // Add metadata
    state_update_type: 'wf06_available_slots_shown',
    target_state: 'show_available_slots',
    timestamp: new Date().toISOString()
  }
}];
