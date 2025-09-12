-- Add conversation_id column to documents table
-- This allows documents to be associated with specific conversations

-- Add the conversation_id column
ALTER TABLE documents 
ADD COLUMN IF NOT EXISTS conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE;

-- Create index for better performance
CREATE INDEX IF NOT EXISTS idx_documents_conversation_id ON documents(conversation_id);

-- Update the RLS policy for documents to include conversation-based access
DROP POLICY IF EXISTS "Users can manage their own documents" ON documents;

CREATE POLICY "Users can manage their own documents" ON documents
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM users 
            WHERE users.id = documents.user_uuid 
            AND (auth.uid()::text = users.user_id OR auth.uid() = users.id)
        )
        OR
        EXISTS (
            SELECT 1 FROM conversations c
            JOIN users u ON u.id = c.user_uuid
            WHERE c.id = documents.conversation_id
            AND (auth.uid()::text = u.user_id OR auth.uid() = u.id)
        )
    );