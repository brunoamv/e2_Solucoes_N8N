// Calculate Slot Availability for Multiple Dates - V2.1 INPUT FIX
// ===== FIX: Use correct node reference for input data =====
// PROBLEM: $input.first().json comes from "Get Calendar Events (Batch)" which is EMPTY
// SOLUTION: Use $node["Calculate Next Business Days"].json for business_dates and duration_minutes

const requestData = $node["Calculate Next Business Days"].json;
const businessDates = requestData.business_dates;
const durationMinutes = requestData.duration_minutes;

// ===== V2 FIX: ROBUST EMPTY CALENDAR HANDLING =====
// n8n behavior:
// - Empty calendar: [{ json: {} }] (1 item with empty object)
// - Calendar with events: [{ json: { id: "...", start: {...}, ... } }, ...]
// - API error: [] (no items)

const rawItems = $('Get Calendar Events (Batch)').all();

console.log(`🔍 [WF06 V2.1] Raw items from calendar API:`, {
    count: rawItems.length,
    first_item: rawItems.length > 0 ? JSON.stringify(rawItems[0].json) : 'NO_ITEMS'
});

// Filter out empty objects (check if .json has any meaningful properties)
const calendarEvents = rawItems
    .map(item => item.json)
    .filter(event => {
        // Empty object check: must have 'id' or 'start' property
        // Empty calendar returns: {}
        // Real event returns: { id: "...", start: { dateTime: "..." }, ... }
        const isRealEvent = event && (event.id || event.start);

        if (!isRealEvent && Object.keys(event || {}).length > 0) {
            console.log(`⚠️ [WF06 V2.1] Filtered out invalid event:`, event);
        }

        return isRealEvent;
    });

console.log(`📊 [WF06 V2.1] Processing ${businessDates.length} dates with ${calendarEvents.length} calendar events`);

// ⚠️ V2: Log empty calendar for debugging (this is NORMAL, not an error)
if (calendarEvents.length === 0) {
    console.log('ℹ️ [WF06 V2.1] Empty calendar detected - all slots will be available (no conflicts)');
}

// HARDCODED BUSINESS HOURS (V7 pattern)
const WORK_START = 8;   // 08:00
const WORK_END = 18;    // 18:00
const SLOT_INTERVAL = 60;  // 1-hour intervals

// Helper: Check if slot conflicts with any event
function hasConflict(slotStart, slotEnd, events) {
    for (const event of events) {
        // V2: Extra safety check (should never trigger after filter above)
        if (!event.start || !event.start.dateTime) {
            console.warn(`⚠️ [WF06 V2.1] Invalid event in hasConflict:`, event);
            continue;
        }

        const eventStart = new Date(event.start.dateTime);
        const eventEnd = new Date(event.end.dateTime);

        // Check overlap: slot starts before event ends AND slot ends after event starts
        if (slotStart < eventEnd && slotEnd > eventStart) {
            return true;  // Conflict found
        }
    }
    return false;  // No conflict
}

// Helper: Calculate all slots for a specific date
function calculateSlotsForDate(dateStr, events) {
    const allSlots = [];

    // Generate all possible slots
    for (let hour = WORK_START; hour < WORK_END; hour += (SLOT_INTERVAL / 60)) {
        const startTime = `${String(hour).padStart(2, '0')}:00`;
        const endHour = hour + (durationMinutes / 60);

        // Check if slot + duration fits in business hours
        if (endHour <= WORK_END) {
            const endTime = `${String(endHour).padStart(2, '0')}:00`;

            // Build ISO datetime strings with Brazil timezone
            const slotStart = new Date(`${dateStr}T${startTime}:00-03:00`);
            const slotEnd = new Date(`${dateStr}T${endTime}:00-03:00`);

            // Check for conflicts
            if (!hasConflict(slotStart, slotEnd, events)) {
                allSlots.push({
                    start_time: startTime,
                    end_time: endTime
                });
            }
        }
    }

    return allSlots;
}

// Process each business date
const datesWithAvailability = businessDates.map(dateInfo => {
    const availableSlots = calculateSlotsForDate(dateInfo.date, calendarEvents);

    console.log(`📆 [WF06 V2.1] ${dateInfo.date}: ${availableSlots.length} slots available`);

    return {
        date: dateInfo.date,
        day_of_week: dateInfo.day_of_week,
        total_slots: availableSlots.length,
        slots: availableSlots
    };
});

// Filter dates with at least 1 available slot
const validDates = datesWithAvailability.filter(d => d.total_slots > 0);

if (validDates.length === 0) {
    console.log('⚠️ [WF06 V2.1] No dates with available slots found');
}

console.log(`✅ [WF06 V2.1] ${validDates.length} dates with availability`);

return {
    dates_with_availability: validDates,
    total_dates_checked: businessDates.length,
    total_dates_available: validDates.length
};
