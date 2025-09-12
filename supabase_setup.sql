-- PharmGPT Database Setup for Supabase
-- Copy and paste this entire script into your Supabase SQL Editor

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    salt VARCHAR(64) NOT NULL,
    user_id VARCHAR(32) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE
);

-- Sessions table
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_uuid UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE, -- Legacy compatibility
    session_id VARCHAR(255) UNIQUE NOT NULL,
    session_data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE
);

-- Conversations table
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_uuid UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE, -- Legacy compatibility
    conversation_id VARCHAR(255) UNIQUE NOT NULL,
    title VARCHAR(500),
    model VARCHAR(255) DEFAULT 'meta-llama/llama-4-maverick-17b-128e-instruct',
    messages JSONB DEFAULT '[]',
    message_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    is_archived BOOLEAN DEFAULT FALSE
);

-- Messages table
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_uuid UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    message_id VARCHAR(255) UNIQUE NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Documents table
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_uuid UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE, -- Legacy compatibility
    document_id VARCHAR(255) UNIQUE NOT NULL,
    document_hash VARCHAR(255),
    filename VARCHAR(500) NOT NULL,
    file_type VARCHAR(50),
    file_size INTEGER,
    content TEXT,
    chunk_count INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(), -- For compatibility
    is_processed BOOLEAN DEFAULT FALSE
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_user_uuid ON sessions(user_uuid);
CREATE INDEX IF NOT EXISTS idx_sessions_session_id ON sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_conversations_user_uuid ON conversations(user_uuid);
CREATE INDEX IF NOT EXISTS idx_conversations_conversation_id ON conversations(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_conversation_uuid ON messages(conversation_uuid);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);
CREATE INDEX IF NOT EXISTS idx_documents_user_uuid ON documents(user_uuid);
CREATE INDEX IF NOT EXISTS idx_documents_document_id ON documents(document_id);

-- Enable RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

-- RLS Policies (simplified for anon key usage)
CREATE POLICY "Enable all operations for authenticated users" ON users FOR ALL USING (true);
CREATE POLICY "Enable all operations for authenticated users" ON sessions FOR ALL USING (true);
CREATE POLICY "Enable all operations for authenticated users" ON conversations FOR ALL USING (true);
CREATE POLICY "Enable all operations for authenticated users" ON messages FOR ALL USING (true);
CREATE POLICY "Enable all operations for authenticated users" ON documents FOR ALL USING (true);

-- User stats view
CREATE OR REPLACE VIEW user_stats AS
SELECT 
    u.id,
    u.username,
    u.created_at,
    u.last_login,
    COUNT(DISTINCT c.id) as conversation_count,
    COUNT(DISTINCT m.id) as message_count,
    COUNT(DISTINCT d.id) as document_count,
    MAX(c.updated_at) as last_conversation_at,
    MAX(m.created_at) as last_message_at
FROM users u
LEFT JOIN conversations c ON u.id = c.user_uuid AND c.is_active = true
LEFT JOIN messages m ON c.id = m.conversation_uuid
LEFT JOIN documents d ON u.id = d.user_uuid
GROUP BY u.id, u.username, u.created_at, u.last_login;

-- Update triggers
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sessions_updated_at BEFORE UPDATE ON sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_conversations_updated_at BEFORE UPDATE ON conversations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_documents_updated_at BEFORE UPDATE ON documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Triggers to keep legacy columns in sync
CREATE OR REPLACE FUNCTION sync_legacy_user_id()
RETURNS TRIGGER AS $$
BEGIN
    NEW.user_id = NEW.user_uuid;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER sync_conversations_user_id BEFORE INSERT OR UPDATE ON conversations
    FOR EACH ROW EXECUTE FUNCTION sync_legacy_user_id();

CREATE TRIGGER sync_sessions_user_id BEFORE INSERT OR UPDATE ON sessions
    FOR EACH ROW EXECUTE FUNCTION sync_legacy_user_id();

CREATE TRIGGER sync_documents_user_id BEFORE INSERT OR UPDATE ON documents
    FOR EACH ROW EXECUTE FUNCTION sync_legacy_user_id();

-- Trigger to sync added_at with created_at for documents
CREATE OR REPLACE FUNCTION sync_added_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.added_at = NEW.created_at;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER sync_documents_added_at BEFORE INSERT OR UPDATE ON documents
    FOR EACH ROW EXECUTE FUNCTION sync_added_at();