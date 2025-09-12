-- Comprehensive Database Fix for PharmGPT Conversation Issues
-- Run this in Supabase SQL Editor to fix conversation creation problems

-- 1. Add the missing exec_sql function for raw SQL execution
CREATE OR REPLACE FUNCTION public.exec_sql(params text[], sql text)
RETURNS TABLE(result jsonb) 
LANGUAGE plpgsql 
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    query_text text;
    i integer;
BEGIN
    -- Replace parameter placeholders with actual values
    query_text := sql;
    FOR i IN 1..array_length(params, 1) LOOP
        query_text := replace(query_text, '$' || i, quote_literal(params[i]));
    END LOOP;
    
    -- Execute the dynamic query and return results
    RETURN QUERY EXECUTE 'SELECT to_jsonb(t.*) FROM (' || query_text || ') t';
EXCEPTION
    WHEN OTHERS THEN
        -- Return error information as JSON
        RETURN QUERY SELECT to_jsonb(row(SQLSTATE, SQLERRM));
END;
$$;

-- 2. Add alternative exec_sql function signature for backwards compatibility
CREATE OR REPLACE FUNCTION public.exec_sql(sql text, params jsonb DEFAULT '{}')
RETURNS TABLE(result jsonb)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public  
AS $$
DECLARE
    query_text text;
    param_key text;
    param_value text;
BEGIN
    query_text := sql;
    
    -- Replace named parameters from JSONB
    FOR param_key, param_value IN SELECT * FROM jsonb_each_text(params) LOOP
        query_text := replace(query_text, ':' || param_key, quote_literal(param_value));
    END LOOP;
    
    -- Execute the dynamic query
    RETURN QUERY EXECUTE 'SELECT to_jsonb(t.*) FROM (' || query_text || ') t';
EXCEPTION
    WHEN OTHERS THEN
        RETURN QUERY SELECT to_jsonb(row(SQLSTATE, SQLERRM));
END;
$$;

-- 3. Ensure conversations table has the correct structure with both fields
DO $$
BEGIN
    -- Check if user_id column exists in conversations, add if missing
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'conversations' AND column_name = 'user_id'
    ) THEN
        ALTER TABLE conversations 
        ADD COLUMN user_id UUID REFERENCES users(id) ON DELETE CASCADE;
        
        -- Populate user_id from user_uuid where possible
        UPDATE conversations SET user_id = user_uuid WHERE user_id IS NULL;
    END IF;
    
    -- Check if messages and message_count columns exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'conversations' AND column_name = 'messages'
    ) THEN
        ALTER TABLE conversations ADD COLUMN messages JSONB DEFAULT '[]';
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'conversations' AND column_name = 'message_count'
    ) THEN
        ALTER TABLE conversations ADD COLUMN message_count INTEGER DEFAULT 0;
    END IF;
    
    -- Ensure model column has proper default
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'conversations' 
        AND column_name = 'model' 
        AND column_default IS NOT NULL
    ) THEN
        ALTER TABLE conversations 
        ALTER COLUMN model SET DEFAULT 'meta-llama/llama-4-maverick-17b-128e-instruct';
    END IF;
END
$$;

-- 4. Create or update the sync trigger function
CREATE OR REPLACE FUNCTION sync_legacy_user_id()
RETURNS TRIGGER AS $$
BEGIN
    -- Sync user_id with user_uuid if user_uuid is provided
    IF NEW.user_uuid IS NOT NULL THEN
        NEW.user_id = NEW.user_uuid;
    ELSIF NEW.user_id IS NOT NULL THEN
        NEW.user_uuid = NEW.user_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 5. Ensure triggers exist
DROP TRIGGER IF EXISTS sync_conversations_user_id ON conversations;
CREATE TRIGGER sync_conversations_user_id 
    BEFORE INSERT OR UPDATE ON conversations
    FOR EACH ROW EXECUTE FUNCTION sync_legacy_user_id();

-- 6. Create a debugging function to check conversation creation
CREATE OR REPLACE FUNCTION debug_conversation_creation(
    p_user_uuid uuid,
    p_conversation_id text,
    p_title text,
    p_model text DEFAULT 'meta-llama/llama-4-maverick-17b-128e-instruct'
)
RETURNS TABLE(
    step text,
    success boolean,
    message text,
    data jsonb
)
LANGUAGE plpgsql
AS $$
DECLARE
    user_exists boolean;
    conv_inserted boolean;
BEGIN
    -- Step 1: Check if user exists
    SELECT EXISTS(SELECT 1 FROM users WHERE id = p_user_uuid) INTO user_exists;
    RETURN QUERY SELECT 'check_user'::text, user_exists, 
                        CASE WHEN user_exists THEN 'User found' ELSE 'User not found' END,
                        to_jsonb(row(p_user_uuid));
    
    IF NOT user_exists THEN
        RETURN;
    END IF;
    
    -- Step 2: Try to insert conversation
    BEGIN
        INSERT INTO conversations (
            conversation_id, user_uuid, title, model, 
            created_at, is_archived, messages, message_count
        ) VALUES (
            p_conversation_id, p_user_uuid, p_title, p_model,
            NOW(), false, '[]'::jsonb, 0
        );
        
        conv_inserted := true;
        RETURN QUERY SELECT 'insert_conversation'::text, true, 'Conversation inserted successfully',
                            to_jsonb(row(p_conversation_id, p_user_uuid, p_title));
                            
    EXCEPTION WHEN OTHERS THEN
        conv_inserted := false;
        RETURN QUERY SELECT 'insert_conversation'::text, false, 
                            format('Insert failed: %s - %s', SQLSTATE, SQLERRM),
                            to_jsonb(row(p_conversation_id, p_user_uuid));
    END;
    
    -- Step 3: Verify the conversation was created
    IF conv_inserted THEN
        RETURN QUERY SELECT 'verify_conversation'::text, 
                            EXISTS(SELECT 1 FROM conversations WHERE conversation_id = p_conversation_id),
                            'Verification complete',
                            (SELECT to_jsonb(c.*) FROM conversations c WHERE conversation_id = p_conversation_id LIMIT 1);
    END IF;
END;
$$;

-- 7. Create a function to clean up test data
CREATE OR REPLACE FUNCTION cleanup_debug_conversations()
RETURNS void
LANGUAGE sql
AS $$
    DELETE FROM conversations WHERE conversation_id LIKE 'debug-test-%';
$$;

-- 8. Grant necessary permissions
GRANT EXECUTE ON FUNCTION exec_sql(text[], text) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION exec_sql(text, jsonb) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION debug_conversation_creation(uuid, text, text, text) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION cleanup_debug_conversations() TO anon, authenticated;

-- 9. Show current schema info for conversations table
SELECT 
    column_name, 
    data_type, 
    is_nullable, 
    column_default
FROM information_schema.columns 
WHERE table_name = 'conversations' 
ORDER BY ordinal_position;