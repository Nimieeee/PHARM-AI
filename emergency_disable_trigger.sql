-- EMERGENCY: Completely disable the problematic trigger
-- Run this immediately in Supabase SQL Editor to fix conversation creation

-- Step 1: Drop ALL triggers on conversations table
DROP TRIGGER IF EXISTS update_conversations_message_count ON conversations;
DROP TRIGGER IF EXISTS safe_update_conversations_message_count ON conversations;
DROP TRIGGER IF EXISTS safe_message_count_trigger ON conversations;

-- Step 2: Make messages column nullable and set proper default
ALTER TABLE conversations ALTER COLUMN messages DROP NOT NULL;
ALTER TABLE conversations ALTER COLUMN messages SET DEFAULT '[]'::jsonb;

-- Step 3: Make message_count nullable with default
ALTER TABLE conversations ALTER COLUMN message_count DROP NOT NULL;
ALTER TABLE conversations ALTER COLUMN message_count SET DEFAULT 0;

-- Step 4: Update any existing null values
UPDATE conversations SET messages = '[]'::jsonb WHERE messages IS NULL;
UPDATE conversations SET message_count = 0 WHERE message_count IS NULL;

-- Step 5: Create a simple function to manually update message counts when needed
CREATE OR REPLACE FUNCTION update_message_count_manual(conv_id text)
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

-- Verification: Check if conversations can be created now
-- INSERT INTO conversations (conversation_id, user_id, title, model, created_at, is_archived, message_count)
-- VALUES ('test-' || gen_random_uuid(), 'test-user', 'Test Conversation', 'test-model', NOW(), false, 0);

COMMENT ON FUNCTION update_message_count_manual IS 'Manually update message count for a conversation when needed';

-- Success message
SELECT 'Trigger disabled successfully. Conversation creation should now work.' as status;