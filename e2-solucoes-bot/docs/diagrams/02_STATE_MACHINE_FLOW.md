# Diagrama de Fluxo - State Machine WF02

> **Versão**: Production V114
> **Última atualização**: 2026-04-29

## Fluxograma Completo (15 Estados)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    WF02 STATE MACHINE COMPLETE FLOW                     │
│                              15 States                                  │
└─────────────────────────────────────────────────────────────────────────┘


START: User sends "oi" via WhatsApp
        │
        ▼
┌───────────────────────────────────────────────────────────────────┐
│ STATE 1: greeting                                                 │
│ ─────────────────────────────────────────────────────────────── │
│ Input: Any message (first contact)                               │
│ Validation: None (always accepts)                                │
│ Action:                                                           │
│   - Create or load conversation from database                    │
│   - Display welcome message                                      │
│   - Show service options                                         │
│ Response:                                                         │
│   "👋 Olá! Bem-vindo à E2 Soluções!                              │
│                                                                   │
│    Somos especialistas em:                                       │
│    1️⃣ Energia Solar                                             │
│    2️⃣ Subestações                                               │
│    3️⃣ Projetos Elétricos                                        │
│    4️⃣ BESS (Armazenamento)                                      │
│    5️⃣ Análise Técnica                                           │
│                                                                   │
│    Para começar, preciso de algumas informações.                 │
│    Qual é o seu nome completo?"                                  │
│ Next: collect_name                                               │
└───────────────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────────┐
│ STATE 2: collect_name                                             │
│ ─────────────────────────────────────────────────────────────── │
│ Input: User's full name                                           │
│ Validation:                                                       │
│   ✓ Length > 2 characters                                        │
│   ✗ Empty string                                                 │
│   ✗ Only numbers                                                 │
│ Action:                                                           │
│   collected_data.lead_name = message                             │
│ Response (Valid):                                                 │
│   "✅ Ótimo, [Nome]!                                              │
│    Agora preciso do seu e-mail para contato."                    │
│ Response (Invalid):                                               │
│   "⚠️ Por favor, informe seu nome completo (mínimo 3 letras)."   │
│ Next:                                                             │
│   Valid → collect_email                                          │
│   Invalid → collect_name (stay in same state)                    │
└───────────────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────────┐
│ STATE 3: collect_email                                            │
│ ─────────────────────────────────────────────────────────────── │
│ Input: Email address                                              │
│ Validation:                                                       │
│   Regex: /^[^\s@]+@[^\s@]+\.[^\s@]+$/                           │
│   ✓ user@domain.com                                             │
│   ✗ invalidemail                                                 │
│   ✗ user@domain (no extension)                                  │
│ Action:                                                           │
│   collected_data.email = message                                 │
│ Response (Valid):                                                 │
│   "✅ Email registrado com sucesso!                               │
│                                                                   │
│    Qual serviço você precisa?                                    │
│    1️⃣ Energia Solar                                             │
│    2️⃣ Subestação                                                │
│    3️⃣ Projetos Elétricos                                        │
│    4️⃣ BESS                                                       │
│    5️⃣ Análise Técnica                                           │
│                                                                   │
│    Digite o número da opção desejada."                           │
│ Response (Invalid):                                               │
│   "⚠️ Email inválido. Use formato: nome@dominio.com"             │
│ Next:                                                             │
│   Valid → service_selection                                      │
│   Invalid → collect_email (stay in same state)                   │
└───────────────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────────┐
│ STATE 4: service_selection                                        │
│ ─────────────────────────────────────────────────────────────── │
│ Input: "1" | "2" | "3" | "4" | "5"                              │
│ Validation:                                                       │
│   ✓ Exactly "1", "2", "3", "4", or "5"                          │
│   ✗ Other numbers or text                                        │
│ Action (Mapping):                                                 │
│   "1" → collected_data.service_type = "energia_solar"           │
│   "2" → collected_data.service_type = "subestacao"              │
│   "3" → collected_data.service_type = "projetos_eletricos"      │
│   "4" → collected_data.service_type = "bess"                    │
│   "5" → collected_data.service_type = "analise_tecnica"         │
│ Response (Valid):                                                 │
│   "✅ Você escolheu: [Service Name]                               │
│                                                                   │
│    Em qual cidade será o projeto?"                               │
│ Response (Invalid):                                               │
│   "⚠️ Opção inválida. Digite um número de 1 a 5."               │
│ Next:                                                             │
│   Valid → collect_city                                           │
│   Invalid → service_selection (stay in same state)               │
└───────────────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────────┐
│ STATE 5: collect_city                                             │
│ ─────────────────────────────────────────────────────────────── │
│ Input: City name                                                  │
│ Validation:                                                       │
│   ✓ Length > 2 characters                                        │
│   ✗ Empty string                                                 │
│ Action:                                                           │
│   collected_data.city = message                                  │
│ Response (Valid):                                                 │
│   "✅ Cidade registrada: [City]                                   │
│                                                                   │
│    Perfeito! Agora vou analisar suas necessidades...            │
│    ⏳ Processando..."                                            │
│ Response (Invalid):                                               │
│   "⚠️ Por favor, informe o nome da cidade."                      │
│ Next:                                                             │
│   Valid → claude_analysis (automatic)                            │
│   Invalid → collect_city (stay in same state)                    │
└───────────────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────────┐
│ STATE 6: claude_analysis                                          │
│ ─────────────────────────────────────────────────────────────── │
│ Type: AUTOMATIC (no user input)                                   │
│ Action:                                                           │
│   HTTP Request to Claude AI API                                  │
│   Endpoint: https://api.anthropic.com/v1/messages                │
│   Model: claude-3-5-sonnet-20241022                              │
│   Payload:                                                        │
│     {                                                             │
│       "system": "Você é especialista da E2 Soluções...",         │
│       "messages": [                                               │
│         {                                                         │
│           "role": "user",                                         │
│           "content": "Cliente: [lead_name]                        │
│                      Email: [email]                               │
│                      Serviço: [service_type]                      │
│                      Cidade: [city]                               │
│                                                                   │
│                      Forneça análise técnica personalizada..."    │
│         }                                                         │
│       ]                                                           │
│     }                                                             │
│   Response: AI-generated analysis (Portuguese)                   │
│ collected_data.ai_response = Claude response                      │
│ Next: ai_response_display (automatic)                            │
└───────────────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────────┐
│ STATE 7: ai_response_display                                      │
│ ─────────────────────────────────────────────────────────────── │
│ Type: AUTOMATIC (no user input)                                   │
│ Action:                                                           │
│   Display Claude AI analysis to user                             │
│ Response:                                                         │
│   "🤖 Análise Personalizada:                                      │
│                                                                   │
│    [Claude AI Response]                                           │
│    (Detailed technical analysis based on service + city)          │
│                                                                   │
│    Esta análise foi gerada especialmente para você!"             │
│ Next: confirmation (automatic)                                   │
└───────────────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────────┐
│ STATE 8: confirmation                                             │
│ ─────────────────────────────────────────────────────────────── │
│ Input: "1" (agendar) | "2" (falar com humano)                   │
│ Validation:                                                       │
│   ✓ "1" or "2"                                                   │
│   ✗ Other input                                                  │
│ Response:                                                         │
│   "O que você gostaria de fazer?                                 │
│                                                                   │
│    1️⃣ Agendar uma reunião técnica                               │
│    2️⃣ Falar com um especialista humano                          │
│                                                                   │
│    Digite 1 ou 2."                                               │
│                                                                   │
│ Decision Tree:                                                    │
│   IF input = "1" AND service_type IN ["energia_solar", "projetos_eletricos"]:│
│      → trigger_wf06_next_dates                                   │
│                                                                   │
│   IF input = "1" AND service_type IN ["subestacao", "bess", "analise_tecnica"]:│
│      → handoff_to_human (não tem agendamento automático)         │
│                                                                   │
│   IF input = "2":                                                │
│      → handoff_to_human                                          │
│                                                                   │
│ Next:                                                             │
│   Service 1/3 + "1" → trigger_wf06_next_dates                    │
│   Service 2/4/5 + "1" → handoff_to_human                         │
│   Any + "2" → handoff_to_human                                   │
└───────────────────────────────────────────────────────────────────┘
        │
        │ (Service 1 or 3 + "Agendar")
        ▼
┌───────────────────────────────────────────────────────────────────┐
│ STATE 9: trigger_wf06_next_dates                                  │
│ ─────────────────────────────────────────────────────────────── │
│ Type: AUTOMATIC (marks for WF06 HTTP call)                        │
│ Action:                                                           │
│   1. Set flag for WF06 next_dates call                           │
│   2. V105: Update database state FIRST                           │
│   3. V113: Prepare to save date_suggestions                      │
│                                                                   │
│ Workflow Flow (V105 Fix):                                         │
│   Build Update Queries                                            │
│      ↓                                                            │
│   Update Conversation State  ← EXECUTES HERE FIRST!              │
│      ↓                                                            │
│   Check If WF06 Next Dates  ← THEN checks for trigger            │
│      ↓ (IF TRUE)                                                 │
│   HTTP Request to WF06                                           │
│      POST /webhook/calendar-availability                         │
│      {                                                            │
│        "action": "next_dates",                                   │
│        "count": 3,                                               │
│        "service_type": "energia_solar",                          │
│        "duration_minutes": 120                                   │
│      }                                                            │
│                                                                   │
│   WF06 Response:                                                  │
│      {                                                            │
│        "dates_with_availability": [                              │
│          {                                                        │
│            "date": "2026-05-01",                                 │
│            "available_slots_count": 8,                           │
│            "formatted_date": "Quinta, 01/05/2026"               │
│          },                                                       │
│          ...                                                      │
│        ]                                                          │
│      }                                                            │
│                                                                   │
│ Next: show_available_dates (after WF06 returns)                  │
└───────────────────────────────────────────────────────────────────┘
        │
        ▼ (WF06 returns 3 dates)
┌───────────────────────────────────────────────────────────────────┐
│ STATE 10: show_available_dates                                    │
│ ─────────────────────────────────────────────────────────────── │
│ Input: User selects date ("1", "2", or "3")                      │
│ Data Source: WF06 response (dates_with_availability)             │
│ V113 Action:                                                      │
│   Save to collected_data.date_suggestions (JSONB):               │
│   [                                                               │
│     {                                                             │
│       "date": "2026-05-01",                                      │
│       "available_slots_count": 8,                                │
│       "formatted_date": "Quinta, 01/05/2026"                    │
│     },                                                            │
│     ...                                                           │
│   ]                                                               │
│                                                                   │
│ Response:                                                         │
│   "📅 Datas Disponíveis:                                          │
│                                                                   │
│    1️⃣ Quinta, 01/05/2026 (8 horários)                           │
│    2️⃣ Sexta, 02/05/2026 (5 horários)                            │
│    3️⃣ Segunda, 05/05/2026 (10 horários)                         │
│                                                                   │
│    Escolha a data digitando 1, 2 ou 3."                          │
│                                                                   │
│ Validation:                                                       │
│   ✓ "1", "2", or "3"                                            │
│   ✗ Other input                                                  │
│                                                                   │
│ Next:                                                             │
│   Valid → process_date_selection                                 │
│   Invalid → show_available_dates (stay in same state)            │
└───────────────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────────┐
│ STATE 11: process_date_selection                                  │
│ ─────────────────────────────────────────────────────────────── │
│ Input: "1", "2", or "3"                                          │
│ Validation:                                                       │
│   ✓ Must match available dates from State 10                    │
│   ✗ Out of range                                                 │
│ Action:                                                           │
│   1. Get selected date from date_suggestions[input - 1]          │
│   2. Save to collected_data.selected_date                        │
│   3. Save to collected_data.selected_date_index                  │
│                                                                   │
│ Example:                                                          │
│   User input: "1"                                                │
│   selected_date = date_suggestions[0].date = "2026-05-01"       │
│   selected_date_formatted = "Quinta, 01/05/2026"                │
│                                                                   │
│ Response:                                                         │
│   "✅ Data selecionada: Quinta, 01/05/2026                        │
│                                                                   │
│    ⏳ Buscando horários disponíveis..."                          │
│                                                                   │
│ Next: trigger_wf06_available_slots (automatic)                   │
└───────────────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────────┐
│ STATE 12: trigger_wf06_available_slots                            │
│ ─────────────────────────────────────────────────────────────── │
│ Type: AUTOMATIC (HTTP call to WF06)                              │
│ Action:                                                           │
│   HTTP Request to WF06                                           │
│      POST /webhook/calendar-availability                         │
│      {                                                            │
│        "action": "available_slots",                              │
│        "date": "2026-05-01",  ← from selected_date               │
│        "service_type": "energia_solar",                          │
│        "duration_minutes": 120                                   │
│      }                                                            │
│                                                                   │
│   V113: Prepare to save slot_suggestions                         │
│                                                                   │
│   WF06 Response:                                                  │
│      {                                                            │
│        "available_slots": [                                       │
│          {                                                        │
│            "start_time": "08:00",  ← V114 USES THIS              │
│            "end_time": "10:00",    ← V114 USES THIS              │
│            "formatted": "8h às 10h"                              │
│          },                                                       │
│          {                                                        │
│            "start_time": "10:00",                                │
│            "end_time": "12:00",                                  │
│            "formatted": "10h às 12h"                             │
│          },                                                       │
│          ...                                                      │
│        ]                                                          │
│      }                                                            │
│                                                                   │
│ Next: show_available_slots (after WF06 returns)                  │
└───────────────────────────────────────────────────────────────────┘
        │
        ▼ (WF06 returns slots)
┌───────────────────────────────────────────────────────────────────┐
│ STATE 13: show_available_slots                                    │
│ ─────────────────────────────────────────────────────────────── │
│ Input: User selects slot number                                  │
│ Data Source: WF06 response (available_slots)                     │
│                                                                   │
│ V113 Action:                                                      │
│   Save to collected_data.slot_suggestions (JSONB):               │
│   [                                                               │
│     {                                                             │
│       "start_time": "08:00",                                     │
│       "end_time": "10:00",                                       │
│       "formatted": "8h às 10h"                                   │
│     },                                                            │
│     ...                                                           │
│   ]                                                               │
│                                                                   │
│ Response:                                                         │
│   "⏰ Horários Disponíveis para Quinta, 01/05/2026:               │
│                                                                   │
│    1️⃣ 8h às 10h                                                 │
│    2️⃣ 10h às 12h                                                │
│    3️⃣ 14h às 16h                                                │
│    4️⃣ 16h às 18h                                                │
│                                                                   │
│    Escolha o horário digitando o número."                        │
│                                                                   │
│ Validation:                                                       │
│   ✓ Valid slot number (1-N where N = available slots)           │
│   ✗ Out of range                                                 │
│                                                                   │
│ Next:                                                             │
│   Valid → process_appointment_booking                            │
│   Invalid → show_available_slots (stay in same state)            │
└───────────────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────────┐
│ STATE 14: process_appointment_booking                             │
│ ─────────────────────────────────────────────────────────────── │
│ Input: Slot selection number                                     │
│ Validation:                                                       │
│   ✓ Must match available slots from State 13                    │
│   ✗ Out of range                                                 │
│                                                                   │
│ V114 CRITICAL Action:                                             │
│   1. Get selected slot from slot_suggestions[input - 1]          │
│   2. Extract TIME fields:                                         │
│      slot = {                                                     │
│        "start_time": "08:00",  ← PostgreSQL TIME                │
│        "end_time": "10:00",    ← PostgreSQL TIME                │
│        "formatted": "8h às 10h"                                  │
│      }                                                            │
│                                                                   │
│   3. Save to collected_data:                                      │
│      scheduled_time_start: "08:00"  ← V114 FIX                   │
│      scheduled_time_end: "10:00"    ← V114 FIX                   │
│      scheduled_time_display: "8h às 10h"                         │
│                                                                   │
│   4. Prepare all appointment data:                                │
│      {                                                            │
│        lead_name: "...",                                         │
│        lead_email: "...",                                        │
│        service_type: "energia_solar",                            │
│        city: "brasilia",                                         │
│        scheduled_date: "2026-05-01",                             │
│        scheduled_time_start: "08:00",  ← TIME field              │
│        scheduled_time_end: "10:00",    ← TIME field              │
│        scheduled_time_display: "8h às 10h"                       │
│      }                                                            │
│                                                                   │
│   5. Trigger WF05 (Appointment Scheduler)                         │
│      → Creates Google Calendar event                             │
│      → Inserts into appointments table                           │
│      → Triggers WF07 (Email Service)                             │
│                                                                   │
│ Response:                                                         │
│   "⏳ Confirmando seu agendamento..."                             │
│                                                                   │
│ Next: booking_confirmation (automatic after WF05 success)        │
└───────────────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────────┐
│ STATE 15: booking_confirmation                                    │
│ ─────────────────────────────────────────────────────────────── │
│ Type: FINAL STATE                                                 │
│ Action:                                                           │
│   Display success message with all details                       │
│                                                                   │
│ Response:                                                         │
│   "✅ AGENDAMENTO CONFIRMADO!                                     │
│                                                                   │
│    📋 Detalhes do Agendamento:                                    │
│    ────────────────────────────                                  │
│    👤 Nome: Bruno Rosa                                            │
│    📧 Email: bruno@example.com                                    │
│    🏢 Serviço: Energia Solar                                      │
│    📍 Cidade: Brasília                                            │
│    📅 Data: Quinta, 01/05/2026                                    │
│    ⏰ Horário: 8h às 10h                                          │
│                                                                   │
│    📨 Você receberá um email de confirmação em instantes!         │
│    📆 O evento foi adicionado ao seu Google Calendar.             │
│                                                                   │
│    Em caso de dúvidas, entre em contato:                         │
│    📞 (61) 3333-4444                                              │
│    📧 contato@e2solucoes.com                                      │
│                                                                   │
│    Obrigado por escolher a E2 Soluções! 🙏"                       │
│                                                                   │
│ Next: END (conversation complete)                                │
│       User can send "oi" to start new conversation               │
└───────────────────────────────────────────────────────────────────┘
```

---

## Rotas Alternativas (Error Handling)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        ALTERNATIVE ROUTES                               │
└─────────────────────────────────────────────────────────────────────────┘

Service 2/4/5 + "Agendar" → handoff_to_human
─────────────────────────────────────────────
STATE 8: confirmation
        │
        ▼ (Service 2/4/5 + Input "1")
┌───────────────────────────────────────────┐
│ handoff_to_human                          │
│ ───────────────────────────────────────── │
│ Response:                                 │
│   "👨‍💼 Vou transferir você para um       │
│    especialista humano.                   │
│                                           │
│    Nossa equipe entrará em contato        │
│    em até 24 horas úteis.                │
│                                           │
│    Seus dados foram salvos:              │
│    • Nome: [lead_name]                   │
│    • Email: [email]                      │
│    • Serviço: [service_type]             │
│    • Cidade: [city]                      │
│                                           │
│    Obrigado!"                            │
│ Next: END                                 │
└───────────────────────────────────────────┘


User Chooses "Falar com Humano" → handoff_to_human
───────────────────────────────────────────────────
STATE 8: confirmation
        │
        ▼ (Input "2")
[Same handoff_to_human response as above]


Validation Errors → Stay in Same State
──────────────────────────────────────
ANY STATE with Invalid Input:
        │
        ▼
┌───────────────────────────────────────────┐
│ Error Response + Stay in State            │
│ ───────────────────────────────────────── │
│ Example (State 2 - collect_name):         │
│   Input: "ab" (too short)                 │
│   Response:                               │
│     "⚠️ Por favor, informe seu nome       │
│      completo (mínimo 3 letras)."        │
│   Next: collect_name (SAME STATE)         │
│                                           │
│ Example (State 3 - collect_email):        │
│   Input: "invalidemail"                   │
│   Response:                               │
│     "⚠️ Email inválido.                   │
│      Use formato: nome@dominio.com"      │
│   Next: collect_email (SAME STATE)        │
│                                           │
│ Example (State 4 - service_selection):    │
│   Input: "10" (out of range)              │
│   Response:                               │
│     "⚠️ Opção inválida.                   │
│      Digite um número de 1 a 5."         │
│   Next: service_selection (SAME STATE)    │
└───────────────────────────────────────────┘
```

---

## Critical Fixes Integration

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    CRITICAL FIXES IN FLOW                               │
└─────────────────────────────────────────────────────────────────────────┘

V111: Database Row Locking (Concurrent Messages)
─────────────────────────────────────────────────
BEFORE State 1 (greeting):
        │
        ▼
┌───────────────────────────────────────────┐
│ Build SQL Queries                         │
│ ───────────────────────────────────────── │
│ SELECT * FROM conversations               │
│ WHERE phone_number IN (                   │
│   '556181755748',                         │
│   '5561181755748'                         │
│ )                                         │
│ ORDER BY updated_at DESC                  │
│ LIMIT 1                                   │
│ FOR UPDATE SKIP LOCKED;  ← V111 FIX       │
│                                           │
│ Impact:                                   │
│   ✅ Only ONE execution at a time         │
│   ✅ Concurrent messages queued           │
│   ✅ No stale state processing            │
└───────────────────────────────────────────┘


V104+V104.2: State Synchronization
───────────────────────────────────
AFTER ANY State:
        │
        ▼
┌───────────────────────────────────────────┐
│ Build Update Queries                      │
│ ───────────────────────────────────────── │
│ V104: Put state in collected_data         │
│   collected_data.current_stage = nextStage│
│                                           │
│ V104.2: Use correct column names          │
│   phone_number (NOT contact_phone) ✅     │
│                                           │
│ UPDATE conversations SET                  │
│   state_machine_state = '...',            │
│   collected_data = jsonb_set(             │
│     collected_data,                       │
│     '{current_stage}',                    │
│     '"nextStage"'                         │
│   )                                       │
│ WHERE phone_number = '...'                │
└───────────────────────────────────────────┘


V105: Routing Fix (State 9 → State 10)
───────────────────────────────────────
STATE 9: trigger_wf06_next_dates
        │
        ▼
┌───────────────────────────────────────────┐
│ Build Update Queries                      │
│   → Prepare UPDATE statement              │
└───────────────────────────────────────────┘
        │
        ▼ V105: EXECUTE UPDATE FIRST!
┌───────────────────────────────────────────┐
│ Update Conversation State                 │
│   → UPDATE conversations SET              │
│     state_machine_state = 'show_available_dates',│
│     next_stage = 'show_available_dates'   │
└───────────────────────────────────────────┘
        │
        ▼ THEN check for WF06 trigger
┌───────────────────────────────────────────┐
│ Check If WF06 Next Dates                  │
│   IF next_stage = 'trigger_wf06_next_dates'│
│      → TRUE (execute HTTP Request)        │
│      → FALSE (skip HTTP Request)          │
└───────────────────────────────────────────┘
        │
        ▼ (IF TRUE)
┌───────────────────────────────────────────┐
│ HTTP Request to WF06                      │
│   POST /webhook/calendar-availability     │
└───────────────────────────────────────────┘


V106.1: response_text Routing
──────────────────────────────
AFTER Build Update Queries:
        │
        ▼
┌───────────────────────────────────────────┐
│ Send WhatsApp Response                    │
│ ───────────────────────────────────────── │
│ V106.1: Explicit node reference           │
│                                           │
│ Text parameter:                           │
│   {{ $node["Build Update Queries"].json.response_text }}│
│                                           │
│ NOT:                                      │
│   {{ $input.first().json.response_text }}│
│   (breaks on WF06 routes!)                │
│                                           │
│ Impact:                                   │
│   ✅ Messages always have content         │
│   ✅ Works on ALL routes (normal + WF06)  │
└───────────────────────────────────────────┘


V113: WF06 Suggestions Persistence
───────────────────────────────────
STATE 10: show_available_dates
        │
        ▼
┌───────────────────────────────────────────┐
│ Build Update Queries1 (V113)              │
│ ───────────────────────────────────────── │
│ Save date_suggestions to collected_data:  │
│   collected_data.date_suggestions = [     │
│     {                                     │
│       "date": "2026-05-01",              │
│       "available_slots_count": 8,        │
│       "formatted_date": "Quinta, 01/05"  │
│     },                                   │
│     ...                                  │
│   ]                                      │
│                                           │
│ Impact:                                   │
│   ✅ Date selection can be validated      │
│   ✅ Date data persists across states     │
└───────────────────────────────────────────┘

STATE 13: show_available_slots
        │
        ▼
┌───────────────────────────────────────────┐
│ Build Update Queries2 (V113)              │
│ ───────────────────────────────────────── │
│ Save slot_suggestions to collected_data:  │
│   collected_data.slot_suggestions = [     │
│     {                                     │
│       "start_time": "08:00",             │
│       "end_time": "10:00",               │
│       "formatted": "8h às 10h"           │
│     },                                   │
│     ...                                  │
│   ]                                      │
│                                           │
│ Impact:                                   │
│   ✅ Slot selection can be validated      │
│   ✅ V114 uses TIME fields from here      │
└───────────────────────────────────────────┘


V114: TIME Field Extraction
────────────────────────────
STATE 14: process_appointment_booking
        │
        ▼
┌───────────────────────────────────────────┐
│ State Machine Logic (V114)                │
│ ───────────────────────────────────────── │
│ Extract TIME fields from WF06 slot:        │
│                                           │
│   const selectedSlot =                    │
│     collectedData.slot_suggestions[index];│
│                                           │
│   collectedData.scheduled_time_start =    │
│     selectedSlot.start_time;  // "08:00" │
│                                           │
│   collectedData.scheduled_time_end =      │
│     selectedSlot.end_time;    // "10:00" │
│                                           │
│   collectedData.scheduled_time_display =  │
│     selectedSlot.formatted;   // "8h às 10h"│
│                                           │
│ Impact:                                   │
│   ✅ PostgreSQL TIME columns get values   │
│   ✅ WF05 appointment creation succeeds   │
│   ✅ No "invalid input syntax" errors     │
└───────────────────────────────────────────┘
```

---

## Referências

- **Código State Machine V114**: `scripts/wf02/state-machines/wf02-v114-slot-time-fields-fix.js`
- **Guidelines State Machine**: `docs/guidelines/02_STATE_MACHINE_PATTERNS.md`
- **Workflow Modification Guide**: `docs/development/01_WORKFLOW_MODIFICATION.md`
- **Database Patterns**: `docs/guidelines/03_DATABASE_PATTERNS.md`
- **Production Workflow**: `n8n/workflows/production/wf02/02_ai_agent_conversation_V114_FUNCIONANDO.json`

---

**Última atualização**: 2026-04-29
**Versão**: Production V114
