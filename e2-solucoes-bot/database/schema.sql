-- ====================================
-- E2 SOLUÇÕES BOT - DATABASE SCHEMA
-- PostgreSQL 15+ com pgvector
-- ====================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ===== CONVERSATIONS TABLE =====
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phone_number VARCHAR(20) NOT NULL UNIQUE,
    whatsapp_name VARCHAR(255),
    current_state VARCHAR(50) DEFAULT 'novo',
    collected_data JSONB DEFAULT '{}',
    service_type VARCHAR(50),
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

CREATE INDEX idx_conversations_phone ON conversations(phone_number);
CREATE INDEX idx_conversations_status ON conversations(status);
CREATE INDEX idx_conversations_service ON conversations(service_type);
CREATE INDEX idx_conversations_rdstation_contact ON conversations(rdstation_contact_id);
CREATE INDEX idx_conversations_rdstation_deal ON conversations(rdstation_deal_id);

-- ===== MESSAGES TABLE =====
CREATE TABLE messages (
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

CREATE INDEX idx_messages_conversation ON messages(conversation_id);
CREATE INDEX idx_messages_created ON messages(created_at DESC);
CREATE INDEX idx_messages_whatsapp_id ON messages(whatsapp_message_id);

-- ===== LEADS TABLE =====
CREATE TABLE leads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID REFERENCES conversations(id),
    phone_number VARCHAR(20) NOT NULL,
    name VARCHAR(255),
    email VARCHAR(255),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(50),
    zip_code VARCHAR(20),

    -- Serviço
    service_type VARCHAR(50),
    service_subtype VARCHAR(50),
    service_details JSONB DEFAULT '{}',

    -- Específico por serviço
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

    -- RD Station CRM IDs
    rdstation_contact_id VARCHAR(100),
    rdstation_deal_id VARCHAR(100),
    rdstation_company_id VARCHAR(100),
    rdstation_last_sync TIMESTAMP WITH TIME ZONE,

    -- Google Sheets
    google_sheets_row INTEGER,
    synced_to_sheets BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT valid_status CHECK (status IN (
        'novo', 'em_atendimento', 'agendado', 'concluido', 'perdido', 'handoff'
    )),
    CONSTRAINT valid_priority CHECK (priority IN ('baixa', 'normal', 'alta', 'urgente'))
);

CREATE INDEX idx_leads_status ON leads(status);
CREATE INDEX idx_leads_service ON leads(service_type);
CREATE INDEX idx_leads_created ON leads(created_at DESC);
CREATE INDEX idx_leads_rdstation_deal ON leads(rdstation_deal_id);
CREATE INDEX idx_leads_email ON leads(email);

-- ===== APPOINTMENTS TABLE =====
CREATE TABLE appointments (
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
        'agendado', 'confirmado', 'em_andamento', 'realizado', 'cancelado', 'reagendado', 'no_show'
    ))
);

CREATE INDEX idx_appointments_date ON appointments(scheduled_date);
CREATE INDEX idx_appointments_status ON appointments(status);
CREATE INDEX idx_appointments_service ON appointments(service_type);
CREATE INDEX idx_appointments_rdstation_task ON appointments(rdstation_task_id);

-- ===== RD STATION SYNC LOG =====
CREATE TABLE rdstation_sync_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    rdstation_id VARCHAR(100),
    operation VARCHAR(20) NOT NULL,
    request_payload JSONB,
    response_payload JSONB,
    status VARCHAR(20) DEFAULT 'pending',
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE,

    CONSTRAINT valid_operation CHECK (operation IN ('create', 'update', 'delete'))
);

CREATE INDEX idx_rdstation_sync_status ON rdstation_sync_log(status);
CREATE INDEX idx_rdstation_sync_entity ON rdstation_sync_log(entity_type, entity_id);

-- ===== CHAT MEMORY (n8n) =====
CREATE TABLE chat_memory (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    message JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_chat_memory_session ON chat_memory(session_id);
CREATE INDEX idx_chat_memory_created ON chat_memory(created_at DESC);

-- ===== TRIGGERS =====

-- Update timestamps
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

-- Cleanup old chat memory (keep 30 days)
CREATE OR REPLACE FUNCTION cleanup_old_chat_memory()
RETURNS void AS $$
BEGIN
    DELETE FROM chat_memory
    WHERE created_at < NOW() - INTERVAL '30 days';
END;
$$ LANGUAGE plpgsql;

-- ===== UTILITY FUNCTIONS =====

-- Get conversation summary
CREATE OR REPLACE FUNCTION get_conversation_summary(p_phone_number VARCHAR)
RETURNS TABLE (
    conversation_id UUID,
    current_state VARCHAR,
    service_type VARCHAR,
    collected_data JSONB,
    message_count BIGINT,
    last_message_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.id,
        c.current_state,
        c.service_type,
        c.collected_data,
        COUNT(m.id),
        c.last_message_at
    FROM conversations c
    LEFT JOIN messages m ON c.id = m.conversation_id
    WHERE c.phone_number = p_phone_number
    GROUP BY c.id, c.current_state, c.service_type, c.collected_data, c.last_message_at;
END;
$$ LANGUAGE plpgsql;

-- Check if data collection is complete
CREATE OR REPLACE FUNCTION is_data_collection_complete(p_conversation_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
    v_data JSONB;
    v_service VARCHAR;
BEGIN
    SELECT collected_data, service_type INTO v_data, v_service
    FROM conversations
    WHERE id = p_conversation_id;

    -- Check mandatory fields
    IF NOT (
        v_data ? 'nome' AND
        v_data ? 'email' AND
        v_data ? 'endereco' AND
        v_data ? 'preferencia_dias'
    ) THEN
        RETURN FALSE;
    END IF;

    -- Service-specific checks
    IF v_service = 'energia_solar' AND NOT (v_data ? 'foto_conta') THEN
        RETURN FALSE;
    END IF;

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Comments
COMMENT ON TABLE conversations IS 'Armazena conversas do WhatsApp com estado e dados coletados';
COMMENT ON TABLE messages IS 'Histórico completo de mensagens trocadas';
COMMENT ON TABLE leads IS 'Leads qualificados prontos para atendimento comercial';
COMMENT ON TABLE appointments IS 'Agendamentos de visitas técnicas';
COMMENT ON TABLE rdstation_sync_log IS 'Log de sincronização com RD Station CRM';
COMMENT ON TABLE chat_memory IS 'Memória de conversação para n8n AI Agent';
