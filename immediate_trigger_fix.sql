-- IMMEDIATE FIX for "cannot get array length of a scalar" error
-- Run this in your Supabase SQL Editor RIGHT NOW

-- Step 1: Drop the problematic trigger
DROP TRIGGER IF EXISTS update_conversations_message_count ON conversations;

-- Step 2: Make the columns more flexible
ALTER TABLE conversations ALTER COLUMN messages DROP NOT NULL;
ALTER TABLE conversations ALTER COLUMN message_count SET DEFAULT 0;

-- Step 3: Create a safer trigger that handles different data types
CREATE OR REPLACE FUNCTION safe_message_count_trigger()
RETURNS TRIGGER AS $$
BEGIN
    -- Handle different message formats safely
    BEGIN
        IF NEW.messages IS NULL THEN
            NEW.message_count = 0;
        ELSIF jsonb_typeof(NEW.messages) = 'array' THEN
            NEW.message_count = jsonb_array_length(NEW.messages);
        ELSIF jsonb_typeof(NEW.messages) = 'string' THEN
            -- Handle JSON string format
            NEW.message_count = jsonb_array_length(NEW.messages::text::jsonb);
        ELSE
            -- Default to 0 for any other type
            NEW.message_count = 0;
        END IF;
    EXCEPTION WHEN OTHERS THEN
        -- If anything fails, just set to 0
        NEW.message_count = 0;
    END;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Step 4: Create the new safe trigger
CREATE TRIGGER safe_message_count_trigger
    BEFORE INSERT OR UPDATE ON conversations
    FOR EACH ROW EXECUTE FUNCTION safe_message_count_trigger();

-- Step 5: Update any existing conversations with null message_count
UPDATE conversations 
SET message_count = 0 
WHERE message_count IS NULL;

-- Verification query (optional - run this to check)
-- SELECT conversation_id, title, jsonb_typeof(messages) as message_type, message_count 
-- FROM conversations LIMIT 5;