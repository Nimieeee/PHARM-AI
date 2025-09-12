-- Fix Database Schema for Existing PharmGPT Database
-- Run this in your Supabase SQL Editor to fix column mismatches

-- Add missing columns to conversations table
ALTER TABLE conversations 
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id) ON DELETE CASCADE,
ADD COLUMN IF NOT EXISTS model VARCHAR(255) DEFAULT 'meta-llama/llama-4-maverick-17b-128e-instruct',
ADD COLUMN IF NOT EXISTS messages JSONB DEFAULT '[]',
ADD COLUMN IF NOT EXISTS message_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS is_archived BOOLEAN DEFAULT FALSE;

-- Add missing columns to documents table
ALTER TABLE documents 
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id) ON DELETE CASCADE,
ADD COLUMN IF NOT EXISTS document_hash VARCHAR(255),
ADD COLUMN IF NOT EXISTS chunk_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Add missing columns to sessions table
ALTER TABLE sessions 
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id) ON DELETE CASCADE;

-- Update existing records to populate user_id columns
UPDATE conversations SET user_id = user_uuid WHERE user_id IS NULL;
UPDATE documents SET user_id = user_uuid WHERE user_id IS NULL;
UPDATE sessions SET user_id = user_uuid WHERE user_id IS NULL;

-- Update existing documents to populate added_at
UPDATE documents SET added_at = created_at WHERE added_at IS NULL;

-- Create triggers to keep legacy columns in sync
CREATE OR REPLACE FUNCTION sync_legacy_user_id()
RETURNS TRIGGER AS $$
BEGIN
    NEW.user_id = NEW.user_uuid;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop existing triggers if they exist
DROP TRIGGER IF EXISTS sync_conversations_user_id ON conversations;
DROP TRIGGER IF EXISTS sync_sessions_user_id ON sessions;
DROP TRIGGER IF EXISTS sync_documents_user_id ON documents;
DROP TRIGGER IF EXISTS sync_documents_added_at ON documents;

-- Create new triggers
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

-- Create indexes for the new columns
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id);
CREATE INDEX IF NOT EXISTS idx_documents_added_at ON documents(added_at);
CREATE INDEX IF NOT EXISTS idx_documents_document_hash ON documents(document_hash);