-- PharmGPT Supabase Database Schema
-- Complete database setup for migrating from file-based storage

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Users table - Core user account management
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    salt VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) UNIQUE NOT NULL, -- Legacy compatibility
    email VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Constraints
    CONSTRAINT username_length CHECK (LENGTH(username) >= 3),
    CONSTRAINT password_hash_not_empty CHECK (LENGTH(password_hash) > 0),
    CONSTRAINT salt_not_empty CHECK (LENGTH(salt) > 0)
);

-- Sessions table - Authentication session management
CREATE TABLE sessions (
    session_id VARCHAR(255) PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    username VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT,
    
    -- Constraints
    CONSTRAINT session_id_not_empty CHECK (LENGTH(session_id) > 0),
    CONSTRAINT expires_after_created CHECK (expires_at > created_at)
);

-- Conversations table - Chat conversations with messages
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id VARCHAR(255) NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    messages JSONB NOT NULL DEFAULT '[]',
    model VARCHAR(255) DEFAULT 'meta-llama/llama-4-maverick-17b-128e-instruct',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    message_count INTEGER DEFAULT 0,
    is_archived BOOLEAN DEFAULT FALSE,
    
    -- Constraints
    CONSTRAINT conversation_id_not_empty CHECK (LENGTH(conversation_id) > 0),
    CONSTRAINT title_not_empty CHECK (LENGTH(title) > 0),
    CONSTRAINT message_count_non_negative CHECK (message_count >= 0),
    UNIQUE(conversation_id, user_id)
);

-- Documents table - RAG document metadata
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_hash VARCHAR(255) NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    conversation_id VARCHAR(255) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(255) NOT NULL,
    file_size INTEGER NOT NULL,
    chunk_count INTEGER NOT NULL,
    added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    is_processed BOOLEAN DEFAULT FALSE,
    processing_error TEXT,
    
    -- Constraints
    CONSTRAINT document_hash_not_empty CHECK (LENGTH(document_hash) > 0),
    CONSTRAINT filename_not_empty CHECK (LENGTH(filename) > 0),
    CONSTRAINT file_size_positive CHECK (file_size > 0),
    CONSTRAINT chunk_count_positive CHECK (chunk_count > 0),
    UNIQUE(document_hash, conversation_id)
);

-- Uploads table - File upload tracking
CREATE TABLE uploads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    file_size INTEGER NOT NULL,
    file_type VARCHAR(255),
    upload_status VARCHAR(50) DEFAULT 'completed',
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processing_time_ms INTEGER,
    
    -- Constraints
    CONSTRAINT filename_not_empty CHECK (LENGTH(filename) > 0),
    CONSTRAINT file_size_non_negative CHECK (file_size >= 0),
    CONSTRAINT processing_time_non_negative CHECK (processing_time_ms IS NULL OR processing_time_ms >= 0)
);

-- User preferences table - User settings and preferences
CREATE TABLE user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    preference_key VARCHAR(255) NOT NULL,
    preference_value JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT preference_key_not_empty CHECK (LENGTH(preference_key) > 0),
    UNIQUE(user_id, preference_key)
);

-- Performance indexes
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_user_id ON users(user_id);
CREATE INDEX idx_users_created_at ON users(created_at);

CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_expires_at ON sessions(expires_at);
CREATE INDEX idx_sessions_last_activity ON sessions(last_activity);

CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_conversations_conversation_id ON conversations(conversation_id);
CREATE INDEX idx_conversations_created_at ON conversations(created_at);
CREATE INDEX idx_conversations_updated_at ON conversations(updated_at);
CREATE INDEX idx_conversations_user_created ON conversations(user_id, created_at);

CREATE INDEX idx_documents_user_id ON documents(user_id);
CREATE INDEX idx_documents_conversation_id ON documents(conversation_id);
CREATE INDEX idx_documents_user_conversation ON documents(user_id, conversation_id);
CREATE INDEX idx_documents_added_at ON documents(added_at);
CREATE INDEX idx_documents_is_processed ON documents(is_processed);

CREATE INDEX idx_uploads_user_id ON uploads(user_id);
CREATE INDEX idx_uploads_uploaded_at ON uploads(uploaded_at);
CREATE INDEX idx_uploads_user_date ON uploads(user_id, uploaded_at);

CREATE INDEX idx_preferences_user_id ON user_preferences(user_id);
CREATE INDEX idx_preferences_key ON user_preferences(preference_key);

-- Enable Row Level Security (RLS)
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE uploads ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;

-- RLS Policies for data isolation
-- Users can only access their own data
CREATE POLICY "Users can access their own profile" ON users
    FOR ALL USING (id = auth.uid() OR user_id = current_setting('app.current_user_id', true));

CREATE POLICY "Users can access their own sessions" ON sessions
    FOR ALL USING (user_id = auth.uid() OR user_id::text = current_setting('app.current_user_id', true));

CREATE POLICY "Users can access their own conversations" ON conversations
    FOR ALL USING (user_id = auth.uid() OR user_id::text = current_setting('app.current_user_id', true));

CREATE POLICY "Users can access their own documents" ON documents
    FOR ALL USING (user_id = auth.uid() OR user_id::text = current_setting('app.current_user_id', true));

CREATE POLICY "Users can access their own uploads" ON uploads
    FOR ALL USING (user_id = auth.uid() OR user_id::text = current_setting('app.current_user_id', true));

CREATE POLICY "Users can access their own preferences" ON user_preferences
    FOR ALL USING (user_id = auth.uid() OR user_id::text = current_setting('app.current_user_id', true));

-- Functions for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for automatic timestamp updates
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_conversations_updated_at BEFORE UPDATE ON conversations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_preferences_updated_at BEFORE UPDATE ON user_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to update message count automatically
CREATE OR REPLACE FUNCTION update_message_count()
RETURNS TRIGGER AS $$
BEGIN
    NEW.message_count = jsonb_array_length(NEW.messages);
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_conversations_message_count BEFORE INSERT OR UPDATE ON conversations
    FOR EACH ROW EXECUTE FUNCTION update_message_count();

-- Function to clean up expired sessions
CREATE OR REPLACE FUNCTION cleanup_expired_sessions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM sessions WHERE expires_at < NOW();
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ language 'plpgsql';

-- Create a view for user statistics
CREATE VIEW user_stats AS
SELECT 
    u.id,
    u.username,
    u.created_at,
    u.last_login,
    COUNT(DISTINCT c.id) as conversation_count,
    COUNT(DISTINCT d.id) as document_count,
    COUNT(DISTINCT up.id) as upload_count,
    COALESCE(SUM(c.message_count), 0) as total_messages
FROM users u
LEFT JOIN conversations c ON u.id = c.user_id AND c.is_archived = false
LEFT JOIN documents d ON u.id = d.user_id
LEFT JOIN uploads up ON u.id = up.user_id
GROUP BY u.id, u.username, u.created_at, u.last_login;

-- Grant necessary permissions (adjust based on your Supabase setup)
-- These will be handled by Supabase's built-in auth system

COMMENT ON TABLE users IS 'User accounts and authentication data';
COMMENT ON TABLE sessions IS 'User authentication sessions';
COMMENT ON TABLE conversations IS 'Chat conversations with message history';
COMMENT ON TABLE documents IS 'Document metadata for RAG system';
COMMENT ON TABLE uploads IS 'File upload tracking and statistics';
COMMENT ON TABLE user_preferences IS 'User settings and preferences';

COMMENT ON COLUMN conversations.messages IS 'JSONB array of message objects with role, content, and timestamp';
COMMENT ON COLUMN documents.metadata IS 'Additional document metadata as JSONB';
COMMENT ON COLUMN user_preferences.preference_value IS 'Preference value stored as JSONB for flexibility';