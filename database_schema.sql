-- PharmGPT Database Schema for Supabase
-- Clean, simple schema with proper RLS policies

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    salt VARCHAR(64) NOT NULL,
    user_id VARCHAR(32) UNIQUE NOT NULL, -- Legacy compatibility
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE
);

-- Sessions table
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_uuid UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
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
    conversation_id VARCHAR(255) UNIQUE NOT NULL,
    title VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
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
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    document_id VARCHAR(255) UNIQUE NOT NULL,
    filename VARCHAR(500) NOT NULL,
    file_type VARCHAR(50),
    file_size INTEGER,
    content TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_processed BOOLEAN DEFAULT FALSE
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_user_uuid ON sessions(user_uuid);
CREATE INDEX IF NOT EXISTS idx_sessions_session_id ON sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_conversations_user_uuid ON conversations(user_uuid);
CREATE INDEX IF NOT EXISTS idx_conversations_conversation_id ON conversations(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_conversation_uuid ON messages(conversation_uuid);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);
CREATE INDEX IF NOT EXISTS idx_documents_user_uuid ON documents(user_uuid);
CREATE INDEX IF NOT EXISTS idx_documents_conversation_id ON documents(conversation_id);
CREATE INDEX IF NOT EXISTS idx_documents_document_id ON documents(document_id);

-- Enable Row Level Security (RLS)
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

-- RLS Policies for users table
CREATE POLICY "Users can view their own profile" ON users
    FOR SELECT USING (auth.uid()::text = user_id OR auth.uid() = id);

CREATE POLICY "Users can update their own profile" ON users
    FOR UPDATE USING (auth.uid()::text = user_id OR auth.uid() = id);

-- RLS Policies for sessions table
CREATE POLICY "Users can manage their own sessions" ON sessions
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM users 
            WHERE users.id = sessions.user_uuid 
            AND (auth.uid()::text = users.user_id OR auth.uid() = users.id)
        )
    );

-- RLS Policies for conversations table
CREATE POLICY "Users can manage their own conversations" ON conversations
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM users 
            WHERE users.id = conversations.user_uuid 
            AND (auth.uid()::text = users.user_id OR auth.uid() = users.id)
        )
    );

-- RLS Policies for messages table
CREATE POLICY "Users can manage their own messages" ON messages
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM conversations 
            JOIN users ON users.id = conversations.user_uuid
            WHERE conversations.id = messages.conversation_uuid 
            AND (auth.uid()::text = users.user_id OR auth.uid() = users.id)
        )
    );

-- RLS Policies for documents table
CREATE POLICY "Users can manage their own documents" ON documents
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM users 
            WHERE users.id = documents.user_uuid 
            AND (auth.uid()::text = users.user_id OR auth.uid() = users.id)
        )
    );

-- Create a view for user statistics
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

-- Function to set user context for RLS (if needed)
CREATE OR REPLACE FUNCTION set_user_context(user_identifier TEXT)
RETURNS VOID AS $$
BEGIN
    -- Set the user context for RLS policies
    PERFORM set_config('app.current_user_id', user_identifier, false);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get current user context
CREATE OR REPLACE FUNCTION get_current_user_id()
RETURNS TEXT AS $$
BEGIN
    RETURN current_setting('app.current_user_id', true);
END;
$$ LANGUAGE plpgsql;

-- Update triggers for updated_at columns
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