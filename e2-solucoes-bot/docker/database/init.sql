-- ============================================================================
-- E2 Soluções Bot - Production Database Init
-- Executa automaticamente no primeiro startup do container postgres
-- Contexto: banco e2bot_prod (definido por POSTGRES_DB)
-- ============================================================================

-- Cria banco separado para Evolution API
-- ⚠️ Nome real em produção: evolution_db (docker-compose usa EVOLUTION_DB=evolution_db)
CREATE DATABASE evolution_db OWNER postgres;

-- ============================================================================
-- SCHEMA PRINCIPAL (e2bot_prod)
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ===== CONVERSATIONS =====
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phone_number VARCHAR(20) NOT NULL UNIQUE,
    whatsapp_name VARCHAR(255),
    current_state VARCHAR(50) DEFAULT 'novo',
    state_machine_state VARCHAR(50),
    collected_data JSONB DEFAULT '{}',
    service_type VARCHAR(50),
    error_count INTEGER DEFAULT 0,
    service_id VARCHAR(100),
    contact_name VARCHAR(255),
    contact_email VARCHAR(255),
    city VARCHAR(100),
    rdstation_contact_id VARCHAR(100),
    rdstation_deal_id VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_message_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'active',

    CONSTRAINT valid_state CHECK (current_state IN (
        'novo', 'identificando_servico', 'coletando_dados',
        'aguardando_foto', 'agendando', 'agendado',
        'handoff_comercial', 'concluido'
    )),
    CONSTRAINT valid_service CHECK (service_type IN (
        'energia_solar', 'subestacao', 'projeto_eletrico',
        'armazenamento_energia', 'analise_laudo', 'outro'
    ) OR service_type IS NULL)
);

CREATE INDEX IF NOT EXISTS idx_conversations_phone ON conversations(phone_number);
CREATE INDEX IF NOT EXISTS idx_conversations_status ON conversations(status);
CREATE INDEX IF NOT EXISTS idx_conversations_service ON conversations(service_type);
CREATE INDEX IF NOT EXISTS idx_conversations_state_machine ON conversations(state_machine_state);

-- ===== MESSAGES =====
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    direction VARCHAR(10) NOT NULL,
    content TEXT,
    message_type VARCHAR(20) DEFAULT 'text',
    media_url TEXT,
    media_analysis JSONB,
    whatsapp_message_id VARCHAR(100) UNIQUE,
    synced_to_rdstation BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT valid_direction CHECK (direction IN ('inbound', 'outbound')),
    CONSTRAINT valid_type CHECK (message_type IN (
        'text', 'image', 'document', 'audio', 'location', 'sticker'
    ))
);

CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_created ON messages(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_messages_whatsapp_id ON messages(whatsapp_message_id);

-- ===== LEADS =====
CREATE TABLE IF NOT EXISTS leads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID REFERENCES conversations(id),
    phone_number VARCHAR(20) NOT NULL,
    name VARCHAR(255),
    email VARCHAR(255),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(50),
    zip_code VARCHAR(20),
    service_type VARCHAR(50),
    service_subtype VARCHAR(50),
    service_details JSONB DEFAULT '{}',
    segmento VARCHAR(50),
    tensao_subestacao VARCHAR(20),
    possui_solar BOOLEAN,
    tipo_analise VARCHAR(50),
    preferred_days VARCHAR(100),
    preferred_shift VARCHAR(20),
    observations TEXT,
    media_files JSONB DEFAULT '[]',
    ai_analysis JSONB DEFAULT '{}',
    estimated_value DECIMAL(12,2),
    estimated_kwp DECIMAL(6,2),
    estimated_kwh DECIMAL(10,2),
    status VARCHAR(20) DEFAULT 'novo',
    priority VARCHAR(20) DEFAULT 'normal',
    assigned_to VARCHAR(100),
    rdstation_contact_id VARCHAR(100),
    rdstation_deal_id VARCHAR(100),
    rdstation_company_id VARCHAR(100),
    rdstation_last_sync TIMESTAMP WITH TIME ZONE,
    google_sheets_row INTEGER,
    synced_to_sheets BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT valid_status CHECK (status IN (
        'novo', 'em_atendimento', 'agendado', 'concluido', 'perdido', 'handoff'
    )),
    CONSTRAINT valid_priority CHECK (priority IN ('baixa', 'normal', 'alta', 'urgente'))
);

CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
CREATE INDEX IF NOT EXISTS idx_leads_service ON leads(service_type);
CREATE INDEX IF NOT EXISTS idx_leads_created ON leads(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(email);

-- ===== APPOINTMENTS =====
CREATE TABLE IF NOT EXISTS appointments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
    conversation_id UUID REFERENCES conversations(id),
    scheduled_date DATE NOT NULL,
    scheduled_time_start TIME NOT NULL,
    scheduled_time_end TIME NOT NULL,
    technician_name VARCHAR(100),
    technician_phone VARCHAR(20),
    service_type VARCHAR(50),
    google_calendar_event_id VARCHAR(100),
    rdstation_task_id VARCHAR(100),
    status VARCHAR(20) DEFAULT 'agendado',
    reminder_24h_sent BOOLEAN DEFAULT FALSE,
    reminder_2h_sent BOOLEAN DEFAULT FALSE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT valid_status CHECK (status IN (
        'agendado', 'confirmado', 'em_andamento', 'realizado',
        'cancelado', 'reagendado', 'no_show', 'erro_calendario'
    ))
);

CREATE INDEX IF NOT EXISTS idx_appointments_date ON appointments(scheduled_date);
CREATE INDEX IF NOT EXISTS idx_appointments_status ON appointments(status);
CREATE INDEX IF NOT EXISTS idx_appointments_service ON appointments(service_type);

-- ===== EMAIL LOGS (WF07) =====
CREATE TABLE IF NOT EXISTS email_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    recipient_email VARCHAR(255) NOT NULL,
    recipient_name VARCHAR(255),
    subject VARCHAR(500),
    template_used VARCHAR(100),
    status VARCHAR(20) DEFAULT 'pending',
    sent_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}',
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT valid_email_status CHECK (status IN ('pending', 'sent', 'failed', 'bounce'))
);

CREATE INDEX IF NOT EXISTS idx_email_logs_recipient ON email_logs(recipient_email);
CREATE INDEX IF NOT EXISTS idx_email_logs_status ON email_logs(status);
CREATE INDEX IF NOT EXISTS idx_email_logs_sent_at ON email_logs(sent_at DESC);

-- ===== CHAT MEMORY (n8n AI Agent) =====
CREATE TABLE IF NOT EXISTS chat_memory (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    message JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chat_memory_session ON chat_memory(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_memory_created ON chat_memory(created_at DESC);

-- ===== APPOINTMENT REMINDERS (WF05) =====
-- Tabela de lembretes de agendamentos, criada em 2026-05-04 após erro em produção
-- WF05 node "Create Appointment Reminders" depende desta tabela
CREATE TABLE IF NOT EXISTS appointment_reminders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    appointment_id UUID NOT NULL REFERENCES appointments(id) ON DELETE CASCADE,
    reminder_type VARCHAR(50) NOT NULL,      -- 'email', 'whatsapp', 'sms'
    reminder_time TIMESTAMP WITH TIME ZONE NOT NULL,  -- quando enviar o lembrete
    status VARCHAR(20) DEFAULT 'pending',
    sent_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT valid_reminder_status CHECK (status IN ('pending', 'sent', 'failed', 'cancelled')),
    CONSTRAINT uq_appointment_reminder UNIQUE (appointment_id, reminder_type, reminder_time)
);

CREATE INDEX IF NOT EXISTS idx_reminders_appointment ON appointment_reminders(appointment_id);
CREATE INDEX IF NOT EXISTS idx_reminders_status ON appointment_reminders(status);
CREATE INDEX IF NOT EXISTS idx_reminders_time ON appointment_reminders(reminder_time);

-- ===== TRIGGERS =====
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_conversations_updated_at BEFORE UPDATE ON conversations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_leads_updated_at BEFORE UPDATE ON leads
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_appointments_updated_at BEFORE UPDATE ON appointments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_appointment_reminders_updated_at BEFORE UPDATE ON appointment_reminders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
