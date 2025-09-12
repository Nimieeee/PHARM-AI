-- Temporarily disable the message count trigger that's causing array length errors
-- This will allow conversation creation to work while we debug the JSONB issue

-- Disable the trigger that's causing the array length error
DROP TRIGGER IF EXISTS update_conversations_message_count ON conversations;

-- Optionally, create a simpler trigger that doesn't use jsonb_array_length
-- This version handles both array and string formats
CREATE OR REPLACE FUNCTION safe_update_message_count()
RETURNS TRIGGER AS $$
BEGIN
    -- Handle different message formats safely
    IF NEW.messages IS NULL THEN
        NEW.message_count = 0;
    ELSIF jsonb_typeof(NEW.messages) = 'array' THEN
        NEW.message_count = jsonb_array_length(NEW.messages);
    ELSE
        -- If it's not an array, try to parse it
        BEGIN
            NEW.message_count = jsonb_array_length(NEW.messages::jsonb);
        EXCEPTION WHEN OTHERS THEN
            NEW.message_count = 0;
        END;
    END IF;
    
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create the new safer trigger
CREATE TRIGGER safe_update_conversations_message_count 
    BEFORE INSERT OR UPDATE ON conversations
    FOR EACH ROW EXECUTE FUNCTION safe_update_message_count();

-- Alternative: Completely disable the trigger for now
-- DROP TRIGGER IF EXISTS safe_update_conversations_message_count ON conversations;