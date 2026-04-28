// Build Update Queries1 - WF06 Next Dates State Update
// Prepares data for updating state after showing WF06 dates to user
//
// PURPOSE: After showing dates from WF06, update database to:
// - state_machine_state = "show_available_dates"
// - collected_data.current_stage = "show_available_dates"
// - collected_data.awaiting_wf06_next_dates = true
// - collected_data.date_suggestions = [array of dates] ✅ CRITICAL FIX
//
// This ensures when user sends next message (date selection),
// State Machine knows to process it as date selection, not as error.
//
// DATA SOURCE: Uses explicit node reference to get phone_number and date_suggestions
// This is more reliable than using $input because HTTP Request nodes
// replace the data with their response.

// Get phone number AND date_suggestions from explicit node reference
// "Build WF06 NEXT DATE Response Message" node has the original data
const responseData = $node["Build WF06 NEXT DATE Response Message"].json;
const phone_number = responseData.phone_number;
const date_suggestions = responseData.date_suggestions || [];

// Validate phone number exists
if (!phone_number) {
  console.error('Build Update Queries1: No phone_number found!');
  console.error('Build Update Queries1: Response data:', responseData);
  console.error('Build Update Queries1: Available keys:', Object.keys(responseData));
  throw new Error('Phone number is required for state update');
}

// Serialize date_suggestions array to JSON string for PostgreSQL
// PostgreSQL needs JSON string, not JavaScript object
// Single quotes must be escaped as '' for SQL string safety
const dateSuggestionsJson = JSON.stringify(date_suggestions).replace(/'/g, "''");

// Build SQL query for state update
// ✅ CRITICAL FIX: Added date_suggestions to collected_data JSONB field
const update_query = `
UPDATE conversations
SET
  state_machine_state = 'show_available_dates',
  collected_data = jsonb_set(
    jsonb_set(
      jsonb_set(
        collected_data,
        '{current_stage}',
        '"show_available_dates"'
      ),
      '{awaiting_wf06_next_dates}',
      'true'
    ),
    '{date_suggestions}',
    '${dateSuggestionsJson}'::jsonb
  ),
  updated_at = NOW()
WHERE phone_number = '${phone_number.replace(/'/g, "''")}'
RETURNING *;
`.trim();

// Log for debugging
console.log('=== Build Update Queries1 (V113) ===');
console.log('Phone number:', phone_number);
console.log('Setting state to: show_available_dates');
console.log('Setting awaiting_wf06_next_dates: true');
console.log('✅ CRITICAL FIX: Saving date_suggestions to database:', date_suggestions.length, 'dates');
console.log('Data source: Build WF06 NEXT DATE Response Message node');

// Return data for Update Conversation State1 node
return [{
  json: {
    // Add query for PostgreSQL node
    update_query: update_query,

    // Explicitly set phone_number for reference
    phone_number: phone_number,

    // Add metadata
    state_update_type: 'wf06_next_dates_shown',
    target_state: 'show_available_dates',
    timestamp: new Date().toISOString()
  }
}];
