# V73 - Google Calendar Integration & UX Enhancement

> **Date**: 2026-03-18
> **Base**: V72 COMPLETE (when stable)
> **Goal**: Advanced appointment UX with Google Calendar API integration
> **Priority**: 🟡 MEDIUM - After V72 COMPLETE validation
> **Timeline**: 1-2 weeks (phased approach)

---

## 🎯 Vision

Transform the appointment booking experience from basic date/time input to an intelligent, calendar-aware system with:
- ✅ Real-time availability checking
- ✅ Smart date/time suggestions
- ✅ Visual availability display
- ✅ Automatic conflict prevention
- ✅ Seamless calendar synchronization

---

## 📋 Complete Feature Set (V73)

### Phase 1: Google Calendar API Setup (3 days)
**Goal**: Establish secure Google Calendar API integration

#### 1.1 Google Cloud Project Setup
- [ ] Create Google Cloud project for E2 Bot
- [ ] Enable Google Calendar API
- [ ] Create OAuth 2.0 credentials (service account)
- [ ] Download service account JSON key
- [ ] Configure API scopes and permissions
- [ ] Set up calendar sharing with service account

#### 1.2 Environment Configuration
```bash
# Add to docker/docker-compose-dev.yml
services:
  n8n:
    environment:
      - GOOGLE_CALENDAR_CLIENT_EMAIL=${GOOGLE_CALENDAR_CLIENT_EMAIL}
      - GOOGLE_CALENDAR_PRIVATE_KEY=${GOOGLE_CALENDAR_PRIVATE_KEY}
      - GOOGLE_CALENDAR_ID=${GOOGLE_CALENDAR_ID}
      - APPOINTMENT_DURATION_MINUTES=120  # 2 hours default
      - BUSINESS_HOURS_START=08:00
      - BUSINESS_HOURS_END=18:00
      - SATURDAY_END=12:00
```

#### 1.3 Calendar Setup
- [ ] Create dedicated calendar: "E2 Bot - Agendamentos"
- [ ] Share calendar with service account email
- [ ] Configure calendar permissions (read/write)
- [ ] Test API connection from n8n
- [ ] Validate event creation/reading

---

### Phase 2: Availability Service (4 days)
**Goal**: Build intelligent availability checking system

#### 2.1 Create WF06: Calendar Availability Service
**File**: `06_calendar_availability_service.json`

**Webhook Endpoint**: `/webhook/calendar-availability`

**Request Format**:
```json
{
  "action": "check_availability",
  "date": "2026-03-25",        // YYYY-MM-DD
  "service_type": "energia_solar",
  "duration_minutes": 120
}
```

**Response Format**:
```json
{
  "success": true,
  "date": "2026-03-25",
  "available_slots": [
    {
      "start_time": "08:00",
      "end_time": "10:00",
      "status": "available",
      "formatted": "8h às 10h"
    },
    {
      "start_time": "10:00",
      "end_time": "12:00",
      "status": "available",
      "formatted": "10h ao meio-dia"
    },
    {
      "start_time": "14:00",
      "end_time": "16:00",
      "status": "booked",
      "formatted": "14h às 16h"
    }
  ],
  "suggestions": ["08:00", "10:00"],  // Top 2 available slots
  "total_available": 2
}
```

#### 2.2 Availability Check Logic

**Node Structure**:
```
Webhook Trigger
  ↓
Parse Request
  ↓
Validate Date (future, business day)
  ↓
Get Calendar Events (Google Calendar API)
  ↓
Calculate Time Slots
  ↓
Filter Available Slots
  ↓
Format Response
  ↓
Return JSON
```

**Calculate Time Slots Code**:
```javascript
// Calculate all possible slots for a business day
function calculateAvailableSlots(date, existingEvents, duration) {
    const dateObj = new Date(date);
    const dayOfWeek = dateObj.getDay();

    // Define business hours
    let startHour = 8;
    let endHour = (dayOfWeek === 6) ? 12 : 18;  // Saturday ends at 12

    // Generate all possible slots (30-min intervals)
    const allSlots = [];
    for (let hour = startHour; hour < endHour; hour++) {
        for (let minute of [0, 30]) {
            const startTime = `${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}`;
            const endDateTime = new Date(dateObj);
            endDateTime.setHours(hour, minute + duration, 0);

            // Check if slot + duration fits in business hours
            const endHour = endDateTime.getHours();
            const endMinute = endDateTime.getMinutes();

            if (endHour < (dayOfWeek === 6 ? 12 : 18) ||
                (endHour === (dayOfWeek === 6 ? 12 : 18) && endMinute === 0)) {
                allSlots.push({
                    start_time: startTime,
                    end_time: `${String(endHour).padStart(2, '0')}:${String(endMinute).padStart(2, '0')}`,
                    status: 'available'
                });
            }
        }
    }

    // Filter out booked slots
    const availableSlots = allSlots.filter(slot => {
        return !hasConflict(slot, existingEvents, date);
    });

    return availableSlots;
}

function hasConflict(slot, events, date) {
    const slotStart = new Date(`${date}T${slot.start_time}`);
    const slotEnd = new Date(`${date}T${slot.end_time}`);

    for (const event of events) {
        const eventStart = new Date(event.start.dateTime);
        const eventEnd = new Date(event.end.dateTime);

        // Check overlap
        if (slotStart < eventEnd && slotEnd > eventStart) {
            return true;  // Conflict found
        }
    }

    return false;  // No conflict
}
```

#### 2.3 Google Calendar API Nodes

**Node 1: Get Calendar Events**
```json
{
  "name": "Get Calendar Events",
  "type": "n8n-nodes-base.googleCalendar",
  "parameters": {
    "authentication": "serviceAccount",
    "resource": "event",
    "operation": "getAll",
    "calendarId": "={{$env.GOOGLE_CALENDAR_ID}}",
    "options": {
      "timeMin": "={{$json.date}}T00:00:00Z",
      "timeMax": "={{$json.date}}T23:59:59Z",
      "singleEvents": true,
      "orderBy": "startTime"
    }
  }
}
```

**Node 2: Create Calendar Event** (for confirmed appointments)
```json
{
  "name": "Create Calendar Event",
  "type": "n8n-nodes-base.googleCalendar",
  "parameters": {
    "authentication": "serviceAccount",
    "resource": "event",
    "operation": "create",
    "calendarId": "={{$env.GOOGLE_CALENDAR_ID}}",
    "start": "={{$json.scheduled_date}}T{{$json.scheduled_time_start}}:00",
    "end": "={{$json.scheduled_date}}T{{$json.scheduled_time_end}}:00",
    "summary": "Visita Técnica - {{$json.lead_name}}",
    "description": "Cliente: {{$json.lead_name}}\nTelefone: {{$json.contact_phone}}\nServiço: {{$json.service_name}}\nCidade: {{$json.city}}\n\nAgendado via WhatsApp Bot",
    "location": "{{$json.city}}, Goiás, Brasil"
  }
}
```

---

### Phase 3: Enhanced UX Integration (5 days)
**Goal**: Integrate availability into WF02 appointment flow

#### 3.1 Update State 9: Date Collection with Availability

**New Template V73**:
```javascript
const collectAppointmentDateV73Template = `📅 *Agendamento de Visita Técnica*

Por favor, informe a *data desejada* para o agendamento.

💡 *Formato*: DD/MM/AAAA ou escolha uma sugestão:

📆 *Próximas datas disponíveis*:
{{#each suggestedDates}}
{{this.number}}️⃣ *{{this.display}}* ({{this.day_of_week}}) - {{this.slots_available}} horários livres
{{/each}}

⚠️ *Importante*: A data deve ser:
• No futuro (não pode ser hoje ou passado)
• Em dia útil (segunda a sexta-feira)

💬 Digite a data ou escolha uma opção (1-3)`;
```

**State Machine Logic Enhancement**:
```javascript
// State 9: Enhanced with suggestions
case 'collect_appointment_date':
    console.log('V73: Processing COLLECT_APPOINTMENT_DATE with suggestions');

    // If first time in state, get suggestions
    if (!currentData.date_suggestions_shown) {
        // Call WF06 to get next 3 available dates
        const suggestions = await getNextAvailableDates(3);

        responseText = templates.collect_appointment_date_v73
            .replace('{{suggestedDates}}', formatSuggestions(suggestions));

        updateData.date_suggestions = suggestions;
        updateData.date_suggestions_shown = true;
        nextStage = 'collect_appointment_date';
    }
    // User selected from suggestions (1-3)
    else if (['1', '2', '3'].includes(message)) {
        const selectedDate = currentData.date_suggestions[parseInt(message) - 1];

        responseText = `✅ Data selecionada: *${selectedDate.display}*\n\n` +
                       templates.collect_appointment_time_v73
                           .replace('{{date}}', selectedDate.display)
                           .replace('{{availableSlots}}', formatAvailableSlots(selectedDate.slots));

        updateData.scheduled_date = selectedDate.iso;
        updateData.scheduled_date_display = selectedDate.display;
        updateData.day_of_week = selectedDate.day_of_week;
        updateData.available_slots = selectedDate.slots;
        nextStage = 'collect_appointment_time';
    }
    // User entered custom date
    else {
        // Validate and check availability (existing logic + API call)
        // ...
    }
    break;
```

#### 3.2 Update State 10: Time Selection with Real-time Validation

**New Template V73**:
```javascript
const collectAppointmentTimeV73Template = `🕐 *Horário do Agendamento*

Data selecionada: *{{date}}* ({{day_of_week}})

📍 *Horários disponíveis*:
{{#each availableSlots}}
{{this.number}}️⃣ *{{this.formatted}}* ✅
{{/each}}

{{#if noSlotsAvailable}}
❌ *Não há horários disponíveis nesta data.*
Por favor, escolha outra data.
{{/if}}

💡 Digite o horário (HH:MM) ou escolha uma opção (1-{{count}})

⏰ *Horários de atendimento:*
• Segunda a Sexta: 08:00 às 18:00
• Sábado: 08:00 às 12:00

💡 *Duração média*: 2 horas`;
```

**State Machine Logic Enhancement**:
```javascript
// State 10: Enhanced with real-time validation
case 'collect_appointment_time':
    console.log('V73: Processing COLLECT_APPOINTMENT_TIME with availability');

    // If first time in state, show available slots
    if (!currentData.time_slots_shown) {
        // Get available slots from WF06
        const availability = await checkAvailability(currentData.scheduled_date);

        if (availability.total_available === 0) {
            responseText = `❌ *Ops! Esta data está totalmente ocupada.*\n\n` +
                          `Por favor, escolha outra data.\n\n` +
                          templates.collect_appointment_date_v73;

            nextStage = 'collect_appointment_date';
            updateData.scheduled_date = null;  // Clear invalid date
        } else {
            responseText = templates.collect_appointment_time_v73
                .replace('{{date}}', currentData.scheduled_date_display)
                .replace('{{day_of_week}}', currentData.day_of_week)
                .replace('{{availableSlots}}', formatSlotOptions(availability.available_slots))
                .replace('{{count}}', availability.total_available);

            updateData.available_time_slots = availability.available_slots;
            updateData.time_slots_shown = true;
            nextStage = 'collect_appointment_time';
        }
    }
    // User selected from slot options (1-N)
    else if (isNumeric(message) && parseInt(message) <= currentData.available_time_slots.length) {
        const selectedSlot = currentData.available_time_slots[parseInt(message) - 1];

        // Double-check availability (race condition prevention)
        const stillAvailable = await verifySlotAvailable(
            currentData.scheduled_date,
            selectedSlot.start_time
        );

        if (stillAvailable) {
            responseText = buildAppointmentConfirmation(currentData, selectedSlot);
            updateData.scheduled_time_start = selectedSlot.start_time;
            updateData.scheduled_time_end = selectedSlot.end_time;
            nextStage = 'appointment_confirmation';
        } else {
            responseText = `❌ *Ops! Este horário acabou de ser reservado.*\n\n` +
                          `Por favor, escolha outro horário.\n\n` +
                          templates.collect_appointment_time_v73;
            nextStage = 'collect_appointment_time';
            updateData.time_slots_shown = false;  // Refresh slots
        }
    }
    // User entered custom time (HH:MM)
    else {
        // Validate format and availability
        const timeValidation = await validateCustomTime(
            message,
            currentData.scheduled_date,
            currentData.available_time_slots
        );

        if (timeValidation.valid && timeValidation.available) {
            responseText = buildAppointmentConfirmation(currentData, timeValidation.slot);
            updateData.scheduled_time_start = timeValidation.slot.start_time;
            updateData.scheduled_time_end = timeValidation.slot.end_time;
            nextStage = 'appointment_confirmation';
        } else {
            responseText = timeValidation.error_message + '\n\n' +
                          templates.collect_appointment_time_v73;
            nextStage = 'collect_appointment_time';
        }
    }
    break;
```

#### 3.3 Helper Functions for WF02

**Get Next Available Dates**:
```javascript
async function getNextAvailableDates(count = 3) {
    const suggestions = [];
    const today = new Date();
    let daysChecked = 0;

    while (suggestions.length < count && daysChecked < 30) {
        const checkDate = new Date(today);
        checkDate.setDate(today.getDate() + daysChecked + 1);  // Start from tomorrow

        // Skip weekends (if Sunday)
        if (checkDate.getDay() === 0) {
            daysChecked++;
            continue;
        }

        // Call WF06 availability service
        const response = await httpRequest({
            method: 'POST',
            url: 'http://e2bot-n8n-dev:5678/webhook/calendar-availability',
            body: {
                action: 'check_availability',
                date: formatDate(checkDate, 'YYYY-MM-DD'),
                service_type: 'energia_solar',
                duration_minutes: 120
            }
        });

        if (response.success && response.total_available > 0) {
            suggestions.push({
                number: suggestions.length + 1,
                iso: response.date,
                display: formatDate(checkDate, 'DD/MM/YYYY'),
                day_of_week: getDayOfWeek(checkDate),
                slots_available: response.total_available,
                slots: response.available_slots
            });
        }

        daysChecked++;
    }

    return suggestions;
}
```

**Check Availability**:
```javascript
async function checkAvailability(dateISO) {
    const response = await httpRequest({
        method: 'POST',
        url: 'http://e2bot-n8n-dev:5678/webhook/calendar-availability',
        body: {
            action: 'check_availability',
            date: dateISO,
            service_type: 'energia_solar',
            duration_minutes: 120
        }
    });

    return response;
}
```

**Verify Slot Available** (race condition check):
```javascript
async function verifySlotAvailable(dateISO, startTime) {
    const availability = await checkAvailability(dateISO);

    return availability.available_slots.some(slot =>
        slot.start_time === startTime && slot.status === 'available'
    );
}
```

---

### Phase 4: Calendar Event Creation (2 days)
**Goal**: Create Google Calendar events for confirmed appointments

#### 4.1 Update WF05: Appointment Scheduler

Add Google Calendar event creation after database insert:

**New Node: Create Google Calendar Event**:
```
Webhook Trigger
  ↓
Parse Appointment Data
  ↓
Insert into Database
  ↓
**Create Google Calendar Event** ✨ NEW
  ↓
Send Confirmation Email/SMS
  ↓
Respond Success
```

**Calendar Event Node**:
```javascript
{
    "name": "Create Google Calendar Event",
    "type": "n8n-nodes-base.googleCalendar",
    "parameters": {
        "authentication": "serviceAccount",
        "resource": "event",
        "operation": "create",
        "calendarId": "={{$env.GOOGLE_CALENDAR_ID}}",
        "start": "={{$json.scheduled_date}}T{{$json.scheduled_time_start}}:00-03:00",
        "end": "={{$json.scheduled_date}}T{{$json.scheduled_time_end}}:00-03:00",
        "summary": "Visita Técnica - {{$json.lead_name}}",
        "description": `Cliente: {{$json.lead_name}}
Telefone: {{$json.contact_phone}}
Email: {{$json.email}}
Cidade: {{$json.city}}
Serviço: {{$json.service_name}}

Agendado via WhatsApp Bot E2 Soluções
ID Agendamento: {{$json.appointment_id}}
Data/Hora Agendamento: {{$json.created_at}}`,
        "location": "{{$json.city}}, Goiás, Brasil",
        "attendees": [
            {"email": "comercial@e2solucoes.com.br"},
            {"email": "{{$json.email}}", "optional": true}
        ],
        "reminders": {
            "useDefault": false,
            "overrides": [
                {"method": "email", "minutes": 1440},  // 1 day before
                {"method": "popup", "minutes": 60}      // 1 hour before
            ]
        },
        "colorId": "9"  // Blue color for E2 appointments
    }
}
```

#### 4.2 Store Calendar Event ID

Update database schema to store Google Calendar event ID:

**Migration**: `database/migrations/002_add_calendar_event_id.sql`
```sql
-- Add calendar_event_id column to appointments table
ALTER TABLE appointments
ADD COLUMN calendar_event_id VARCHAR(255) DEFAULT NULL;

-- Add index for faster lookup
CREATE INDEX idx_appointments_calendar_event_id ON appointments(calendar_event_id);

-- Add calendar sync status
ALTER TABLE appointments
ADD COLUMN calendar_sync_status VARCHAR(50) DEFAULT 'pending';

-- Add calendar sync timestamp
ALTER TABLE appointments
ADD COLUMN calendar_synced_at TIMESTAMP DEFAULT NULL;
```

**Update WF05 Insert Query**:
```sql
INSERT INTO appointments (
    conversation_id,
    scheduled_date,
    scheduled_time_start,
    scheduled_time_end,
    appointment_status,
    calendar_event_id,        -- NEW
    calendar_sync_status,     -- NEW
    calendar_synced_at,       -- NEW
    created_at
) VALUES (
    {{$json.conversation_id}},
    {{$json.scheduled_date}},
    {{$json.scheduled_time_start}},
    {{$json.scheduled_time_end}},
    'scheduled',
    {{$('Create Google Calendar Event').item.json.id}},     -- NEW
    'synced',                                                -- NEW
    NOW(),                                                   -- NEW
    NOW()
)
RETURNING appointment_id, calendar_event_id;
```

---

### Phase 5: Advanced Features (3 days)
**Goal**: Polish UX with advanced calendar features

#### 5.1 Smart Suggestions Algorithm

**Priority-based slot ranking**:
```javascript
function rankTimeSlots(slots, preferences = {}) {
    return slots
        .map(slot => {
            let score = 100;  // Base score

            const hour = parseInt(slot.start_time.split(':')[0]);

            // Morning slots (9-11) get bonus
            if (hour >= 9 && hour <= 11) score += 20;

            // Afternoon slots (14-16) get bonus
            if (hour >= 14 && hour <= 16) score += 15;

            // Avoid very early (8am) or very late (5-6pm)
            if (hour === 8 || hour >= 17) score -= 10;

            // Lunch time (12-13) gets penalty
            if (hour === 12) score -= 20;

            // Weekend (Saturday) morning preferred
            if (preferences.isSaturday && hour <= 10) score += 10;

            return { ...slot, score };
        })
        .sort((a, b) => b.score - a.score)
        .slice(0, 5);  // Return top 5 suggestions
}
```

#### 5.2 Visual Availability Calendar (Text-based)

**Show weekly availability**:
```javascript
function formatWeeklyAvailability(weekDates) {
    let calendar = `📅 *Disponibilidade desta semana*:\n\n`;

    for (const date of weekDates) {
        const emoji = date.total_available > 5 ? '🟢' :
                     date.total_available > 2 ? '🟡' :
                     date.total_available > 0 ? '🟠' : '🔴';

        calendar += `${emoji} *${date.display}* (${date.day_of_week})\n`;
        calendar += `   └ ${date.total_available} horários livres\n\n`;
    }

    calendar += `\n🟢 Alta disponibilidade | 🟡 Média | 🟠 Baixa | 🔴 Lotado`;

    return calendar;
}
```

#### 5.3 Conflict Prevention

**Double-booking prevention**:
```javascript
// Before creating appointment, lock time slot
async function lockTimeSlot(date, startTime, leadPhone, duration = 5) {
    // Create temporary lock in Redis or database
    await redis.set(
        `slot_lock:${date}:${startTime}`,
        leadPhone,
        'EX',
        duration * 60  // Lock for 5 minutes
    );
}

async function verifyAndCreateAppointment(appointmentData) {
    const lockKey = `slot_lock:${appointmentData.date}:${appointmentData.time}`;
    const lockHolder = await redis.get(lockKey);

    // If slot locked by another user, reject
    if (lockHolder && lockHolder !== appointmentData.phone) {
        return {
            success: false,
            error: 'Slot just booked by another user'
        };
    }

    // Create calendar event (atomic operation)
    const calendarEvent = await createGoogleCalendarEvent(appointmentData);

    if (calendarEvent.success) {
        // Create database record
        const dbRecord = await createAppointmentRecord({
            ...appointmentData,
            calendar_event_id: calendarEvent.id
        });

        // Release lock
        await redis.del(lockKey);

        return { success: true, appointment: dbRecord };
    } else {
        return { success: false, error: calendarEvent.error };
    }
}
```

#### 5.4 Appointment Reminder System

**WF07: Appointment Reminders** (separate workflow)

**Schedule**:
- 24 hours before: Email + WhatsApp
- 2 hours before: WhatsApp only

**Node Structure**:
```
Schedule Trigger (every hour)
  ↓
Get Appointments Next 24h
  ↓
Check If Reminder Sent
  ↓
Send Email Reminder
  ↓
Send WhatsApp Reminder
  ↓
Mark Reminder Sent
```

---

## 📊 Database Schema Updates

### New Tables

**appointments** (enhanced):
```sql
CREATE TABLE IF NOT EXISTS appointments (
    appointment_id SERIAL PRIMARY KEY,
    conversation_id INTEGER REFERENCES conversations(conversation_id),
    scheduled_date DATE NOT NULL,
    scheduled_time_start TIME NOT NULL,
    scheduled_time_end TIME NOT NULL,
    appointment_status VARCHAR(50) DEFAULT 'scheduled',

    -- V73 Calendar Integration
    calendar_event_id VARCHAR(255) DEFAULT NULL,
    calendar_sync_status VARCHAR(50) DEFAULT 'pending',
    calendar_synced_at TIMESTAMP DEFAULT NULL,

    -- Reminders
    reminder_24h_sent BOOLEAN DEFAULT FALSE,
    reminder_2h_sent BOOLEAN DEFAULT FALSE,
    reminder_24h_sent_at TIMESTAMP DEFAULT NULL,
    reminder_2h_sent_at TIMESTAMP DEFAULT NULL,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    cancelled_at TIMESTAMP DEFAULT NULL,

    UNIQUE(scheduled_date, scheduled_time_start)  -- Prevent double-booking
);
```

**calendar_sync_log** (new):
```sql
CREATE TABLE IF NOT EXISTS calendar_sync_log (
    log_id SERIAL PRIMARY KEY,
    appointment_id INTEGER REFERENCES appointments(appointment_id),
    calendar_event_id VARCHAR(255),
    sync_action VARCHAR(50),  -- 'create', 'update', 'delete'
    sync_status VARCHAR(50),  -- 'success', 'failed'
    error_message TEXT DEFAULT NULL,
    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🚀 Deployment Plan

### Phase 1: Setup (Days 1-3)
```bash
# 1. Google Cloud setup
- Create project
- Enable Calendar API
- Generate service account credentials
- Share calendar

# 2. Environment configuration
cp .env.example .env
# Add Google Calendar credentials

# 3. Test API connection
python3 scripts/test-google-calendar-connection.py
```

### Phase 2: WF06 Availability Service (Days 4-7)
```bash
# 1. Generate WF06
python3 scripts/generate-wf06-calendar-availability.py

# 2. Import and test
# http://localhost:5678 → Import WF06

# 3. Validate API responses
curl -X POST http://localhost:5678/webhook/calendar-availability \
  -H "Content-Type: application/json" \
  -d '{"action":"check_availability","date":"2026-03-25","duration_minutes":120}'
```

### Phase 3: Enhanced UX (Days 8-12)
```bash
# 1. Generate V73 workflow
python3 scripts/generate-v73-calendar-ux.py

# 2. Database migration
docker exec -it e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -f database/migrations/002_add_calendar_event_id.sql

# 3. Import V73
# http://localhost:5678 → Import V73

# 4. Test appointment flow
# WhatsApp: "oi" → service 1 → complete → date suggestions → time slots → confirm
```

### Phase 4: Calendar Events (Days 13-14)
```bash
# 1. Update WF05 with calendar node
python3 scripts/update-wf05-calendar-events.py

# 2. Test calendar creation
# Complete appointment → verify Google Calendar event created

# 3. Validate calendar_event_id in database
docker exec -it e2bot-postgres-dev psql -U postgres -d e2bot_dev \
  -c "SELECT appointment_id, calendar_event_id, calendar_sync_status FROM appointments LIMIT 5;"
```

---

## ✅ Success Criteria

### Must Have (V73.0)
- [x] Google Calendar API connected and authenticated
- [x] WF06 availability service returns accurate slot data
- [x] State 9 shows 3 date suggestions with availability count
- [x] State 10 shows available time slots for selected date
- [x] Real-time slot validation prevents double-booking
- [x] Calendar events created for confirmed appointments
- [x] Database stores calendar_event_id and sync status

### Should Have (V73.1)
- [ ] Smart slot ranking (morning/afternoon preferences)
- [ ] Weekly availability view (text-based calendar)
- [ ] 5-minute slot lock during booking process
- [ ] Race condition handling (already booked slots)
- [ ] Calendar event metadata (service, customer info)

### Could Have (V73.2)
- [ ] Appointment reminder system (24h/2h before)
- [ ] Cancellation flow with calendar sync
- [ ] Rescheduling flow with availability check
- [ ] Multiple service duration support (1h, 2h, 3h)
- [ ] Team member calendar integration (multiple calendars)

---

## 🧪 Testing Strategy

### Unit Tests
```bash
# Test availability calculation
npm run test:availability

# Test slot conflict detection
npm run test:conflicts

# Test date/time parsing
npm run test:datetime
```

### Integration Tests
```bash
# Test Google Calendar API
npm run test:calendar-api

# Test WF06 webhook
npm run test:wf06-availability

# Test WF02 → WF06 integration
npm run test:wf02-calendar-integration
```

### E2E Tests
```bash
# Test complete flow: date suggestion → time selection → calendar creation
npm run test:e2e:appointment-calendar

# Test conflict prevention
npm run test:e2e:double-booking

# Test race conditions
npm run test:e2e:concurrent-booking
```

---

## 📈 Metrics & Monitoring

### Key Metrics
```yaml
appointment_metrics:
  - suggestion_acceptance_rate: "% users who chose suggested dates"
  - slot_selection_rate: "% users who chose suggested times vs custom"
  - booking_completion_time: "Average time from date input to confirmation"
  - calendar_sync_success_rate: "% successful calendar event creations"
  - double_booking_prevention: "Count of prevented conflicts"

performance_metrics:
  - availability_api_response_time: "< 500ms target"
  - calendar_event_creation_time: "< 1s target"
  - slot_validation_time: "< 200ms target"
```

### Monitoring Queries
```sql
-- Calendar sync success rate
SELECT
    calendar_sync_status,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
FROM appointments
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY calendar_sync_status;

-- Average appointment booking time
SELECT
    AVG(EXTRACT(EPOCH FROM (a.created_at - c.created_at))) / 60 as avg_minutes
FROM appointments a
JOIN conversations c ON a.conversation_id = c.conversation_id
WHERE a.created_at >= NOW() - INTERVAL '7 days';

-- Slot selection patterns
SELECT
    EXTRACT(HOUR FROM scheduled_time_start) as hour,
    COUNT(*) as bookings
FROM appointments
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY hour
ORDER BY hour;
```

---

## 🐛 Known Limitations & Future Work

### V73 Limitations
1. **Single Calendar**: Only supports one shared calendar (no multi-technician routing)
2. **No Timezone Handling**: Assumes Brazil/Goiania timezone (GMT-3)
3. **No Recurring Appointments**: Only supports one-time appointments
4. **No Mobile Calendar View**: Text-based availability display only
5. **Manual Cancellation**: No automated cancellation flow with calendar sync

### Future Enhancements (V74+)
1. **Multi-Calendar Support**: Route appointments to specific technician calendars
2. **Timezone Management**: Support for different Brazilian timezones
3. **Visual Calendar**: WhatsApp-compatible calendar image generation
4. **Smart Routing**: Automatic technician assignment based on availability/location
5. **Predictive Scheduling**: ML-based slot suggestions based on historical patterns
6. **Two-way Calendar Sync**: Handle calendar updates from external sources

---

## 📚 References

### Google Calendar API Documentation
- [Google Calendar API Reference](https://developers.google.com/calendar/api/v3/reference)
- [Service Account Authentication](https://developers.google.com/identity/protocols/oauth2/service-account)
- [Event Resource](https://developers.google.com/calendar/api/v3/reference/events)
- [n8n Google Calendar Node](https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.googlecalendar/)

### Related Documentation
- [V72 COMPLETE Implementation Plan](./PLAN_V72_COMPLETE_IMPLEMENTATION.md)
- [V71 Appointment Fix](./V71_APPOINTMENT_FIX_COMPLETE.md)
- [Google Calendar Setup Guide](./Setups/SETUP_GOOGLE_CALENDAR.md)

---

**Maintained by**: Claude Code
**Status**: 📋 PLAN READY - V73 CALENDAR UX ARCHITECTURE
**Priority**: 🟡 MEDIUM - Deploy after V72 COMPLETE validation
**Estimated Time**: 1-2 weeks (phased deployment)
**Dependencies**: V72 COMPLETE must be stable in production
