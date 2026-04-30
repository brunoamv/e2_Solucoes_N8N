# Diagrama de Arquitetura do Sistema - E2 Bot

> **Versão**: 1.0 (Production V1)
> **Última atualização**: 2026-04-29

## Visão Geral do Sistema

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          E2 BOT ARCHITECTURE                            │
│                         Production V1 Package                           │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   WhatsApp   │      │  Evolution   │      │     n8n      │
│    Client    │─────▶│  API v2.3.7  │─────▶│   2.14.2     │
│              │      │              │      │              │
└──────────────┘      └──────────────┘      └──────────────┘
                              │                     │
                              │                     │
                              ▼                     ▼
                      ┌──────────────┐      ┌──────────────┐
                      │  PostgreSQL  │◀─────│   Claude AI  │
                      │     14.x     │      │ 3.5 Sonnet   │
                      │              │      │              │
                      └──────────────┘      └──────────────┘
                              │                     │
                              │                     │
                              ▼                     ▼
                      ┌──────────────┐      ┌──────────────┐
                      │    Gmail     │      │   Google     │
                      │  SMTP 465    │      │  Calendar    │
                      │              │      │   OAuth2     │
                      └──────────────┘      └──────────────┘
```

---

## Fluxo de Mensagens (Message Flow)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      COMPLETE MESSAGE FLOW                              │
└─────────────────────────────────────────────────────────────────────────┘

User WhatsApp Message
        │
        ▼
┌────────────────┐
│ Evolution API  │  Port 8080
│   Webhook      │  POST /webhook/whatsapp
└────────────────┘
        │
        ▼
┌────────────────┐
│   WF01 V2.8.3  │  Deduplication Layer
│                │  ON CONFLICT DO NOTHING
│   PostgreSQL   │  conversations table
│   Dedup Check  │
└────────────────┘
        │
        ├─ Duplicate? → Stop ⛔
        │
        ▼ New/Unique
┌────────────────┐
│   WF02 V114    │  AI Conversation Engine
│                │  15-State Machine
│  State Machine │  + Claude 3.5 Sonnet
│     Logic      │  + V111 Row Locking
└────────────────┘  + V113 WF06 Persistence
        │           + V114 TIME Fields
        │
        ├─ Service 1/3 + "Agendar"?
        │         │
        │         YES ─────────────────────┐
        │                                   │
        │                                   ▼
        │                          ┌────────────────┐
        │                          │   WF06 V2.2    │  Calendar Service
        │                          │                │  Microservice
        │                          │  Next Dates    │  OAuth + Empty Fix
        │                          │  Available     │  + Input Data
        │                          │  Slots         │
        │                          └────────────────┘
        │                                   │
        │         ┌─────────────────────────┘
        │         │
        │         ▼ Dates/Slots
        │   User Selection
        │         │
        │         ▼
        │   ┌────────────────┐
        │   │   WF05 V7      │  Scheduler
        │   │                │  Hardcoded Hours
        │   │ Google Calendar│  + Database
        │   │   + Database   │  + WF07 Trigger
        │   └────────────────┘
        │         │
        │         ▼
        │   ┌────────────────┐
        │   │   WF07 V13     │  Email Service
        │   │                │  nginx → HTTP
        │   │ Gmail SMTP 465 │  INSERT...SELECT
        │   │   + Database   │  + email_logs
        │   └────────────────┘
        │         │
        ▼         ▼
┌────────────────────────────────┐
│  WhatsApp Response to User     │
│  + Email Confirmation          │
│  + Google Calendar Event       │
└────────────────────────────────┘
```

---

## Arquitetura de Workflows (n8n)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         WORKFLOW ARCHITECTURE                           │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│  WF01 - Main WhatsApp Handler (V2.8.3)                              │
│  ────────────────────────────────────────────────────────────────── │
│                                                                      │
│  Webhook Trigger → Parse Message → PostgreSQL Dedup                 │
│                                     (ON CONFLICT phone DO NOTHING)   │
│                                            │                         │
│                                            ▼                         │
│                                    Trigger WF02 ────────────┐        │
└──────────────────────────────────────────────────────────────────────┘
                                                               │
                                                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│  WF02 - AI Agent Conversation (V114) ⭐ CORE WORKFLOW               │
│  ────────────────────────────────────────────────────────────────── │
│                                                                      │
│  1. Build SQL Queries (V111 Row Locking)                            │
│     SELECT * FROM conversations WHERE phone IN (...)                 │
│     FOR UPDATE SKIP LOCKED  ← V111 CRITICAL FIX                     │
│                                                                      │
│  2. State Machine Logic (V114)                                      │
│     ┌─────────────────────────────────────────┐                     │
│     │  15 States:                             │                     │
│     │  1.  greeting                           │                     │
│     │  2.  collect_name                       │                     │
│     │  3.  collect_email                      │                     │
│     │  4.  service_selection                  │                     │
│     │  5.  collect_city                       │                     │
│     │  6.  claude_analysis (AI call)          │                     │
│     │  7.  ai_response_display                │                     │
│     │  8.  confirmation                       │                     │
│     │  9.  trigger_wf06_next_dates ──────┐    │                     │
│     │  10. show_available_dates          │    │                     │
│     │  11. process_date_selection        │    │                     │
│     │  12. trigger_wf06_available_slots ─┼─┐  │                     │
│     │  13. show_available_slots          │ │  │                     │
│     │  14. process_appointment_booking   │ │  │                     │
│     │  15. booking_confirmation          │ │  │                     │
│     └─────────────────────────────────────┼─┼──┘                     │
│                                           │ │                        │
│  3. Build Update Queries (V104.2 + V113)  │ │                        │
│     - Schema-compliant (no contact_phone) │ │                        │
│     - WF06 suggestions persistence        │ │                        │
│       date_suggestions (JSONB)            │ │                        │
│       slot_suggestions (JSONB)            │ │                        │
│       scheduled_time_start (TIME)  ← V114 │ │                        │
│       scheduled_time_end (TIME)    ← V114 │ │                        │
│                                           │ │                        │
│  4. Update Conversation State (V105)      │ │                        │
│     UPDATE conversations SET ...          │ │                        │
│     ↓ EXECUTES BEFORE WF06 CHECK ← V105   │ │                        │
│                                           │ │                        │
│  5. Check If WF06 Next Dates              │ │                        │
│     IF next_stage = 'trigger_wf06_next_dates'                       │
│        → TRUE ─────────────────────────────┘ │                        │
│        → FALSE (continue normal flow)        │                        │
│                                              │                        │
│  6. HTTP Request to WF06 (next_dates) ◀─────┘                        │
│     POST /webhook/calendar-availability                              │
│     { action: "next_dates", count: 3 }                               │
│                                              │                        │
│  7. Check If WF06 Available Slots            │                        │
│     IF next_stage = 'trigger_wf06_available_slots'                   │
│        → TRUE ───────────────────────────────┘                        │
│        → FALSE (continue normal flow)                                │
│                                                                      │
│  8. HTTP Request to WF06 (available_slots) ◀─┘                       │
│     POST /webhook/calendar-availability                              │
│     { action: "available_slots", date: "..." }                       │
│                                                                      │
│  9. Send WhatsApp Response (V106.1)                                  │
│     response_text from Build Update Queries  ← EXPLICIT NODE REF    │
│                                                                      │
│  10. Trigger WF05 (if booking_confirmation state)                    │
└──────────────────────────────────────────────────────────────────────┘
                                                               │
                                                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│  WF06 - Calendar Availability Service (V2.2) 🔄 MICROSERVICE        │
│  ────────────────────────────────────────────────────────────────── │
│                                                                      │
│  Webhook Trigger → Parse Action                                     │
│                                                                      │
│  IF action = "next_dates":                                           │
│     Google Calendar OAuth → List Events                              │
│     Calculate Available Dates (3) with Slot Counts                   │
│     Return: { dates_with_availability: [...] }                       │
│                                                                      │
│  IF action = "available_slots":                                      │
│     Google Calendar OAuth → List Events for Date                     │
│     Calculate Available Time Slots                                   │
│     Return: {                                                        │
│       available_slots: [                                             │
│         {                                                            │
│           start_time: "08:00",  ← V114 USES THIS                     │
│           end_time: "10:00",    ← V114 USES THIS                     │
│           formatted: "8h às 10h"                                     │
│         }                                                            │
│       ]                                                              │
│     }                                                                │
│                                                                      │
│  V2.2 FIXES:                                                         │
│  ✅ OAuth credential re-authentication                               │
│  ✅ Empty calendar handling (no crashes)                            │
│  ✅ Correct input data source ($input.first().json)                 │
└──────────────────────────────────────────────────────────────────────┘
                                                               │
                                                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│  WF05 - Appointment Scheduler (V7)                                   │
│  ────────────────────────────────────────────────────────────────── │
│                                                                      │
│  1. Receive Data from WF02                                           │
│     { lead_name, email, service, city, date, time_start, time_end } │
│                                                                      │
│  2. Google Calendar API                                              │
│     Create Event → Get event_id                                      │
│                                                                      │
│  3. PostgreSQL Insert                                                │
│     INSERT INTO appointments (...)                                   │
│     VALUES (...) RETURNING id                                        │
│                                                                      │
│  4. Trigger WF07 with Data                                           │
│     { lead_email, event_id, appointment_id }                         │
└──────────────────────────────────────────────────────────────────────┘
                                                               │
                                                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│  WF07 - Send Email (V13) 📧                                          │
│  ────────────────────────────────────────────────────────────────── │
│                                                                      │
│  1. Prepare Email Data                                               │
│     Code node with email template                                    │
│                                                                      │
│  2. nginx File Serve (n8n 2.x workaround)                            │
│     HTTP Request to http://nginx/email-template.html                 │
│     (filesystem access blocked in Code nodes)                        │
│                                                                      │
│  3. Gmail SMTP Send                                                  │
│     Port 465 SSL/TLS (NOT STARTTLS!)                                 │
│     To: lead_email                                                   │
│     Subject: Confirmação de Agendamento                              │
│                                                                      │
│  4. PostgreSQL Log (V13 INSERT...SELECT)                             │
│     INSERT INTO email_logs (recipient_email, status, sent_at)        │
│     SELECT '{{ $json.email }}', 'sent', NOW()                        │
│     RETURNING *                                                      │
│     (queryReplacement blocked for ={{ }}, use INSERT...SELECT)       │
└──────────────────────────────────────────────────────────────────────┘
```

---

## State Machine Detalhado (WF02 Core)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    WF02 STATE MACHINE - 15 STATES                       │
│                        Production V114                                  │
└─────────────────────────────────────────────────────────────────────────┘

State 1: greeting
┌────────────────────────────────────────────┐
│ Input: "oi", "olá", any first message     │
│ Action: Display welcome + service options  │
│ Validation: None (always accepts)          │
│ Response: "Bem-vindo! Escolha serviço..."  │
│ Next: collect_name                         │
└────────────────────────────────────────────┘
        │
        ▼
State 2: collect_name
┌────────────────────────────────────────────┐
│ Input: Any text                            │
│ Validation: length > 2                     │
│ Action: Save to collected_data.lead_name   │
│ Response: "Ótimo, [Nome]! Seu email?"     │
│ Next: collect_email                        │
└────────────────────────────────────────────┘
        │
        ▼
State 3: collect_email
┌────────────────────────────────────────────┐
│ Input: Email format                        │
│ Validation: regex ^[^@]+@[^@]+\.[^@]+$    │
│ Action: Save to collected_data.email       │
│ Response: "Email registrado!"              │
│ Next: service_selection                    │
└────────────────────────────────────────────┘
        │
        ▼
State 4: service_selection
┌────────────────────────────────────────────┐
│ Input: "1" | "2" | "3" | "4" | "5"        │
│ Validation: Must be 1-5                    │
│ Action: Map to service type                │
│   1 → energia_solar                        │
│   2 → subestacao                           │
│   3 → projetos_eletricos                   │
│   4 → bess                                 │
│   5 → analise_tecnica                      │
│ Response: "Você escolheu [Service]"        │
│ Next: collect_city                         │
└────────────────────────────────────────────┘
        │
        ▼
State 5: collect_city
┌────────────────────────────────────────────┐
│ Input: City name                           │
│ Validation: length > 2                     │
│ Action: Save to collected_data.city        │
│ Response: "Cidade registrada!"             │
│ Next: claude_analysis                      │
└────────────────────────────────────────────┘
        │
        ▼
State 6: claude_analysis
┌────────────────────────────────────────────┐
│ Action: HTTP Request to Claude AI          │
│ Payload: All collected_data                │
│ Model: claude-3-5-sonnet-20241022          │
│ System Prompt: E2 specialist context       │
│ Next: ai_response_display (auto)           │
└────────────────────────────────────────────┘
        │
        ▼
State 7: ai_response_display
┌────────────────────────────────────────────┐
│ Action: Display Claude AI response         │
│ Response: AI-generated analysis            │
│ Next: confirmation (auto)                  │
└────────────────────────────────────────────┘
        │
        ▼
State 8: confirmation
┌────────────────────────────────────────────┐
│ Input: "1" (agendar) | "2" (falar humano) │
│ Validation: Must be 1 or 2                 │
│                                            │
│ IF "1" + service IN [1, 3]:                │
│    Next: trigger_wf06_next_dates           │
│                                            │
│ IF "1" + service IN [2, 4, 5]:             │
│    Next: handoff_to_human                  │
│                                            │
│ IF "2":                                    │
│    Next: handoff_to_human                  │
└────────────────────────────────────────────┘
        │
        ▼ (Service 1 or 3 + "Agendar")
State 9: trigger_wf06_next_dates
┌────────────────────────────────────────────┐
│ Action: Mark for WF06 HTTP call            │
│ V105: Update State FIRST, then check       │
│ V113: Prepare to save date_suggestions     │
│ Next: show_available_dates (after WF06)    │
└────────────────────────────────────────────┘
        │
        ▼ (WF06 returns 3 dates with slot counts)
State 10: show_available_dates
┌────────────────────────────────────────────┐
│ Input: From WF06 response                  │
│ Action: Display 3 dates with slot counts   │
│ V113: Save date_suggestions to JSONB       │
│ Response:                                  │
│   "Escolha uma data:                       │
│    1. 2026-05-01 (8 horários)             │
│    2. 2026-05-02 (5 horários)             │
│    3. 2026-05-03 (10 horários)"           │
│ Validation: Input must be 1-3              │
│ Next: process_date_selection               │
└────────────────────────────────────────────┘
        │
        ▼
State 11: process_date_selection
┌────────────────────────────────────────────┐
│ Input: "1" | "2" | "3"                     │
│ Validation: Must match available dates     │
│ Action: Save selected_date_index           │
│ Next: trigger_wf06_available_slots         │
└────────────────────────────────────────────┘
        │
        ▼
State 12: trigger_wf06_available_slots
┌────────────────────────────────────────────┐
│ Action: HTTP call to WF06 with date        │
│ V113: Prepare to save slot_suggestions     │
│ Next: show_available_slots (after WF06)    │
└────────────────────────────────────────────┘
        │
        ▼ (WF06 returns slots for selected date)
State 13: show_available_slots
┌────────────────────────────────────────────┐
│ Input: From WF06 response                  │
│ Action: Display available time slots       │
│ V113: Save slot_suggestions to JSONB       │
│ V114: Extract start_time and end_time      │
│ Response:                                  │
│   "Escolha um horário:                     │
│    1. 8h às 10h                           │
│    2. 10h às 12h                          │
│    3. 14h às 16h"                         │
│ Validation: Input must be 1-N              │
│ Next: process_appointment_booking          │
└────────────────────────────────────────────┘
        │
        ▼
State 14: process_appointment_booking
┌────────────────────────────────────────────┐
│ Input: Slot selection "1" | "2" | ...     │
│ Action: Save appointment details           │
│ V114: Extract TIME fields:                 │
│   scheduled_time_start: "08:00"           │
│   scheduled_time_end: "10:00"             │
│ Trigger: WF05 (calendar + email)          │
│ Next: booking_confirmation (auto)          │
└────────────────────────────────────────────┘
        │
        ▼
State 15: booking_confirmation
┌────────────────────────────────────────────┐
│ Action: Display success message            │
│ Response:                                  │
│   "✅ Agendamento confirmado!              │
│    Data: 01/05/2026                        │
│    Horário: 8h às 10h                      │
│    Você receberá email em instantes."      │
│ Next: END (conversation complete)          │
└────────────────────────────────────────────┘
```

---

## Database Schema

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         DATABASE ARCHITECTURE                           │
│                           PostgreSQL 14.x                               │
└─────────────────────────────────────────────────────────────────────────┘

TABLE: conversations
┌──────────────────────────┬──────────────┬─────────────────────────────┐
│ Column                   │ Type         │ Notes                       │
├──────────────────────────┼──────────────┼─────────────────────────────┤
│ id                       │ UUID         │ PK, default gen_random_uuid │
│ phone_number             │ VARCHAR(20)  │ UNIQUE, indexed             │
│ lead_name                │ VARCHAR(255) │                             │
│ email                    │ VARCHAR(255) │                             │
│ service_type             │ VARCHAR(50)  │ energia_solar, subestacao.. │
│ city                     │ VARCHAR(100) │                             │
│ current_state            │ VARCHAR(50)  │ greeting, agendando, etc    │
│ state_machine_state      │ VARCHAR(50)  │ ACTUAL state for machine    │
│ next_stage               │ VARCHAR(50)  │ Next state to transition    │
│ collected_data           │ JSONB        │ V113: date/slot suggestions │
│                          │              │ V114: TIME fields           │
│                          │              │ {                           │
│                          │              │   "lead_name": "...",       │
│                          │              │   "email": "...",           │
│                          │              │   "current_stage": "...",   │
│                          │              │   "date_suggestions": [...],│
│                          │              │   "slot_suggestions": [...],│
│                          │              │   "scheduled_time_start":"08:00",│
│                          │              │   "scheduled_time_end":"10:00"  │
│                          │              │ }                           │
│ created_at               │ TIMESTAMP    │ default NOW()               │
│ updated_at               │ TIMESTAMP    │ default NOW()               │
└──────────────────────────┴──────────────┴─────────────────────────────┘

INDEXES:
- idx_conversations_phone (phone_number)
- idx_conversations_state (state_machine_state)
- idx_conversations_updated (updated_at DESC)

CONSTRAINTS:
- UNIQUE (phone_number) ← V2.8.3 dedup in WF01


TABLE: appointments
┌──────────────────────────┬──────────────┬─────────────────────────────┐
│ Column                   │ Type         │ Notes                       │
├──────────────────────────┼──────────────┼─────────────────────────────┤
│ id                       │ UUID         │ PK, default gen_random_uuid │
│ conversation_id          │ UUID         │ FK → conversations.id       │
│ lead_name                │ VARCHAR(255) │                             │
│ lead_email               │ VARCHAR(255) │                             │
│ service_type             │ VARCHAR(50)  │                             │
│ city                     │ VARCHAR(100) │                             │
│ scheduled_date           │ DATE         │                             │
│ scheduled_time_start     │ TIME         │ V114: PostgreSQL TIME       │
│ scheduled_time_end       │ TIME         │ V114: PostgreSQL TIME       │
│ google_calendar_event_id │ VARCHAR(255) │ From WF05                   │
│ status                   │ VARCHAR(20)  │ confirmed, cancelled        │
│ created_at               │ TIMESTAMP    │ default NOW()               │
│ updated_at               │ TIMESTAMP    │ default NOW()               │
└──────────────────────────┴──────────────┴─────────────────────────────┘

INDEXES:
- idx_appointments_date (scheduled_date)
- idx_appointments_email (lead_email)
- idx_appointments_calendar_id (google_calendar_event_id)


TABLE: email_logs
┌──────────────────────────┬──────────────┬─────────────────────────────┐
│ Column                   │ Type         │ Notes                       │
├──────────────────────────┼──────────────┼─────────────────────────────┤
│ id                       │ UUID         │ PK, default gen_random_uuid │
│ appointment_id           │ UUID         │ FK → appointments.id        │
│ recipient_email          │ VARCHAR(255) │                             │
│ recipient_name           │ VARCHAR(255) │                             │
│ subject                  │ VARCHAR(255) │                             │
│ template_used            │ VARCHAR(50)  │                             │
│ status                   │ VARCHAR(20)  │ sent, failed                │
│ error_message            │ TEXT         │ NULL if sent successfully   │
│ sent_at                  │ TIMESTAMP    │ default NOW()               │
└──────────────────────────┴──────────────┴─────────────────────────────┘

INDEXES:
- idx_email_logs_status (status)
- idx_email_logs_sent (sent_at DESC)


TABLE: appointment_reminders (V8)
┌──────────────────────────┬──────────────┬─────────────────────────────┐
│ Column                   │ Type         │ Notes                       │
├──────────────────────────┼──────────────┼─────────────────────────────┤
│ id                       │ UUID         │ PK, default gen_random_uuid │
│ appointment_id           │ UUID         │ FK → appointments.id        │
│ reminder_type            │ VARCHAR(20)  │ 24h, 1h                     │
│ scheduled_for            │ TIMESTAMP    │ When to send                │
│ sent_at                  │ TIMESTAMP    │ NULL until sent             │
│ status                   │ VARCHAR(20)  │ pending, sent, failed       │
│ created_at               │ TIMESTAMP    │ default NOW()               │
└──────────────────────────┴──────────────┴─────────────────────────────┘

CONSTRAINTS:
- UNIQUE (appointment_id, reminder_type)
```

---

## Correções Críticas (V111-V114)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      CRITICAL FIXES TIMELINE                            │
└─────────────────────────────────────────────────────────────────────────┘

V104 (State Sync Issue)
─────────────────────────
Problem: State Machine state != Database state
Solution: Put state in collected_data.current_stage
Code: scripts/wf02/state-machines/wf02-v104-database-state-update-fix.js
Impact: ✅ State synchronization between executions

V104.2 (Schema Mismatch)
────────────────────────
Problem: Build Update Queries uses contact_phone (doesn't exist)
Solution: Use phone_number (correct column name)
Code: scripts/wf02/state-machines/wf02-v104_2-build-update-queries-schema-fix.js
Impact: ✅ Database updates work correctly

V105 (Routing Fix)
──────────────────
Problem: Check If WF06 runs BEFORE Update Conversation State
         → Database has OLD state when routing decision made
         → Infinite loop (dates → dates → dates)
Solution: Reconnect workflow:
          Build Update Queries → Update Conversation State → Check If WF06
Code: Workflow connection change (no code file)
Impact: ✅ Correct routing based on updated state

V106.1 (response_text Routing)
───────────────────────────────
Problem: Send WhatsApp Response uses {{ $input.first().json.response_text }}
         → Different routes (normal vs WF06) have different data structures
         → response_text = undefined
Solution: Explicit node reference: {{ $node["Build Update Queries"].json.response_text }}
Code: Workflow Send node configuration (no code file)
Impact: ✅ Messages always have content on all routes

V111 (Database Row Locking) 🔴 CRITICAL
────────────────────────────────────────
Problem: User sends rapid messages → Multiple executions read stale state
         → WF06 HTTP Request executes with wrong state_machine_state
Solution: PostgreSQL row locking:
          SELECT * FROM conversations WHERE phone IN (...)
          FOR UPDATE SKIP LOCKED
Code: scripts/wf02/state-machines/wf02-v111-build-sql-queries-row-locking.js
Impact: ✅ Only ONE execution processes conversation at a time
        ✅ Race condition eliminated

V113 (WF06 Suggestions Persistence)
────────────────────────────────────
Problem: WF06 data lost between HTTP calls
         → User selections can't be validated
Solution: Save WF06 responses to collected_data:
          - date_suggestions (JSONB array of dates)
          - slot_suggestions (JSONB array of slots)
Code: scripts/wf02/state-machines/wf02-v113-build-update-queries1-wf06-next-dates.js
      scripts/wf02/state-machines/wf02-v113-build-update-queries2-wf06-available-slots.js
Impact: ✅ WF06 data persisted and accessible

V114 (PostgreSQL TIME Fields) 🔴 CRITICAL
──────────────────────────────────────────
Problem: WF05 creates appointment with scheduled_time_start/end as TIME
         → State Machine only saves scheduled_time_display: "8h às 10h"
         → PostgreSQL ERROR: invalid input syntax for type time
Solution: Extract TIME fields from WF06 slot structure:
          slot = { start_time: "08:00", end_time: "10:00", formatted: "8h às 10h" }
          Save: scheduled_time_start: "08:00", scheduled_time_end: "10:00"
Code: scripts/wf02/state-machines/wf02-v114-slot-time-fields-fix.js
Impact: ✅ Appointment creation succeeds in WF05
        ✅ Database TIME columns receive valid values
```

---

## Deployment Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         DEPLOYMENT WORKFLOW                             │
└─────────────────────────────────────────────────────────────────────────┘

Development
───────────
1. Modify workflow locally (n8n dev instance)
2. Test complete flow (WhatsApp → Database → Email)
3. Export workflow JSON
4. Increment version number (V114 → V115)
5. Add descriptive suffix (_FUNCIONANDO, _FIX, etc)
6. Save to n8n/workflows/development/

Code Review
───────────
1. Check State Machine Logic (switch structure, validation)
2. Check Build Update Queries (schema compliance, V113 persistence)
3. Check Build SQL Queries (V111 row locking present?)
4. Check Workflow Connections (V105 routing correct?)
5. Check Send nodes (V106.1 explicit node references?)
6. Verify V114 TIME field extraction
7. Run complete checklist: docs/development/04_CODE_REVIEW_CHECKLIST.md

Staging
───────
1. Import to staging n8n instance
2. Activate workflow
3. Test with real WhatsApp messages
4. Monitor logs for errors
5. Verify database state after each message
6. Test race conditions (3 rapid messages)
7. Test WF06 integration (dates + slots)
8. Validate appointment creation

Production
──────────
1. Backup current production workflow JSON
2. Import new workflow to production n8n
3. Deactivate old workflow
4. Activate new workflow
5. Monitor first 10 conversations
6. Verify database updates
7. Check email delivery
8. Validate Google Calendar events
9. Move old workflow to historical/
10. Move new workflow to production/
11. Update CLAUDE.md with new version
12. Document changes in docs/deployment/

Rollback (if issues)
────────────────────
1. Deactivate problematic workflow
2. Import previous version from production/
3. Activate previous version
4. Verify functionality restored
5. Document rollback reason
6. Fix issues in development
7. Repeat deployment flow
```

---

## Technology Stack

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          TECHNOLOGY STACK                               │
└─────────────────────────────────────────────────────────────────────────┘

Automation & Orchestration
───────────────────────────
n8n 2.14.2
  ├─ Self-hosted workflow automation
  ├─ JavaScript Code nodes for State Machine
  ├─ HTTP Request nodes for Claude AI + WF06
  ├─ PostgreSQL nodes for database operations
  ├─ Gmail SMTP nodes for email
  └─ Google Calendar OAuth for events

Limitations:
  ✗ $env access blocked in Code and Set nodes → Use hardcoded values
  ✗ Filesystem read/write blocked → Use HTTP + nginx workaround
  ✗ queryReplacement limited with ={{ }} → Use INSERT...SELECT pattern

AI & NLP
────────
Claude 3.5 Sonnet (claude-3-5-sonnet-20241022)
  ├─ Context: 200K tokens
  ├─ Endpoint: https://api.anthropic.com/v1/messages
  ├─ Usage: AI analysis in State 6 (claude_analysis)
  └─ System Prompt: E2 Soluções specialist with Brazilian context

Database
────────
PostgreSQL 14.x
  ├─ Tables: conversations, appointments, email_logs, appointment_reminders
  ├─ JSONB for collected_data (flexible schema)
  ├─ V111: Row-level locking (FOR UPDATE SKIP LOCKED)
  ├─ V114: TIME data type for scheduled_time_start/end
  └─ Indexes on phone_number, state_machine_state, scheduled_date

WhatsApp Integration
────────────────────
Evolution API v2.3.7
  ├─ Baileys protocol (no official WhatsApp Business API)
  ├─ Webhook: POST /webhook/whatsapp → n8n WF01
  ├─ QR Code authentication
  └─ Message send/receive

Email
─────
Gmail SMTP
  ├─ Port: 465 (SSL/TLS, NOT STARTTLS!)
  ├─ App Password authentication
  ├─ Templates served via nginx
  └─ V13: INSERT...SELECT for email_logs

Calendar
────────
Google Calendar API
  ├─ OAuth 2.0 authentication
  ├─ Event creation via WF05
  ├─ Availability checking via WF06
  └─ V2.2: Empty calendar handling

Infrastructure
──────────────
Docker Compose
  ├─ n8n container
  ├─ PostgreSQL container
  ├─ Evolution API container
  └─ nginx container (template serving)

nginx
  ├─ Serves email templates (filesystem workaround)
  ├─ Proxy for Evolution API
  └─ Static file serving
```

---

## Referências

- **Arquitetura Completa**: `docs/guidelines/00_VISAO_GERAL.md`
- **State Machine Patterns**: `docs/guidelines/02_STATE_MACHINE_PATTERNS.md`
- **Database Patterns**: `docs/guidelines/03_DATABASE_PATTERNS.md`
- **Workflow Integration**: `docs/guidelines/04_WORKFLOW_INTEGRATION.md`
- **Deployment Guide**: `docs/guidelines/06_DEPLOYMENT_GUIDE.md`
- **Production Workflows**: `n8n/workflows/production/`
- **Scripts**: `scripts/wf02/state-machines/`

---

**Última atualização**: 2026-04-29
**Versão**: Production V1 (WF02 V114)
