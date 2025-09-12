-- URGENT: Run this immediately in Supabase SQL Editor
-- This will fix the conversation creation issue once and for all

-- Step 1: Drop the problematic trigger
DROP TRIGGER IF EXISTS update_conversations_message_count ON conversations;

-- Step 2: Drop the trigger function as well
DROP FUNCTION IF EXISTS update_message_count();

-- Step 3: Make columns more flexible
ALTER TABLE conversations ALTER COLUMN messages DROP NOT NULL;
ALTER TABLE conversations ALTER COLUMN messages SET DEFAULT '[]'::jsonb;
ALTER TABLE conversations ALTER COLUMN message_count DROP NOT NULL;
ALTER TABLE conversations ALTER COLUMN message_count SET DEFAULT 0;

-- Step 4: Fix any existing data
UPDATE conversations SET messages = '[]'::jsonb WHERE messages IS NULL;
UPDATE conversations SET message_count = 0 WHERE message_count IS NULL;

-- Step 5: Test that conversation creation works now
-- (This should succeed without errors)
INSERT INTO conversations (
    conversation_id, 
    user_id, 
    title, 
    model, 
    created_at, 
    is_archived,
    messages,
    message_count
) VALUES (
    'test-fix-' || gen_random_uuid()::text,
    'a3cc3247-bfdb-4145-a9d4-3010f834f6c6',
    'Test Conversation After Fix',
    'meta-llama/llama-4-maverick-17b-128e-instruct',
    NOW(),
    false,
    '[]'::jsonb,
    0
);

-- Step 6: Verify the fix worked
SELECT 'SUCCESS: Conversation creation is now working!' as status
WHERE EXISTS (
    SELECT 1 FROM conversations 
    WHERE title = 'Test Conversation After Fix'
);

-- Clean up the test conversation
DELETE FROM conversations WHERE title = 'Test Conversation After Fix';