-- Emergency script to disable problematic database features
-- Run this in Supabase SQL editor if issues persist

-- Disable the message count trigger temporarily
DROP TRIGGER IF EXISTS update_conversations_message_count ON conversations;
DROP TRIGGER IF EXISTS safe_update_conversations_message_count ON conversations;

-- Make message_count nullable and set default
ALTER TABLE conversations ALTER COLUMN message_count DROP NOT NULL;
ALTER TABLE conversations ALTER COLUMN message_count SET DEFAULT 0;

-- Make messages column nullable temporarily
ALTER TABLE conversations ALTER COLUMN messages DROP NOT NULL;
ALTER TABLE conversations ALTER COLUMN messages SET DEFAULT '[]'::jsonb;

-- Add a simple function to manually update message counts when needed
CREATE OR REPLACE FUNCTION manual_update_message_count(conv_id text)
RETURNS void AS $$
BEGIN
    UPDATE conversations 
    SET message_count = CASE 
        WHEN messages IS NULL THEN 0
        WHEN jsonb_typeof(messages) = 'array' THEN jsonb_array_length(messages)
        ELSE 0
    END
    WHERE conversation_id = conv_id;
END;
$$ LANGUAGE plpgsql;
