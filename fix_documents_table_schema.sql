-- Fix documents table schema to match DocumentService expectations

-- Add missing columns
ALTER TABLE documents 
ADD COLUMN IF NOT EXISTS document_hash VARCHAR(255);

ALTER TABLE documents 
ADD COLUMN IF NOT EXISTS user_id UUID;

ALTER TABLE documents 
ADD COLUMN IF NOT EXISTS chunk_count INTEGER DEFAULT 0;

ALTER TABLE documents 
ADD COLUMN IF NOT EXISTS added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

ALTER TABLE documents 
ADD COLUMN IF NOT EXISTS processing_error TEXT;

-- Update existing document_id column to be document_hash (if needed)
-- Note: This assumes document_id was meant to be document_hash
UPDATE documents SET document_hash = document_id WHERE document_hash IS NULL;

-- Update user_id to match user_uuid for compatibility
UPDATE documents SET user_id = user_uuid WHERE user_id IS NULL;

-- Create indexes for new columns
CREATE INDEX IF NOT EXISTS idx_documents_document_hash ON documents(document_hash);
CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id);
CREATE INDEX IF NOT EXISTS idx_documents_added_at ON documents(added_at);

-- Update the unique constraint to use document_hash instead of document_id
ALTER TABLE documents DROP CONSTRAINT IF EXISTS documents_document_id_key;
ALTER TABLE documents ADD CONSTRAINT documents_document_hash_key UNIQUE (document_hash);