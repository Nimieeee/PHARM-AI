-- Fix RLS policies to handle custom authentication without auth.uid()
-- This removes the auth.uid() references that cause KeyError: 'auth'

-- Drop existing policies that reference auth.uid()
DROP POLICY IF EXISTS "Users can access their own profile" ON users;
DROP POLICY IF EXISTS "Users can access their own sessions" ON sessions;
DROP POLICY IF EXISTS "Users can access their own conversations" ON conversations;
DROP POLICY IF EXISTS "Users can access their own documents" ON documents;
DROP POLICY IF EXISTS "Users can access their own uploads" ON uploads;
DROP POLICY IF EXISTS "Users can access their own preferences" ON user_preferences;

-- Create new policies that only use current_setting for custom auth
CREATE POLICY "Users can access their own profile" ON users
    FOR ALL USING (
        user_id = current_setting('app.current_user_id', true) OR
        id::text = current_setting('app.current_user_id', true)
    );

CREATE POLICY "Users can access their own sessions" ON sessions
    FOR ALL USING (
        user_id::text = current_setting('app.current_user_id', true)
    );

CREATE POLICY "Users can access their own conversations" ON conversations
    FOR ALL USING (
        user_id::text = current_setting('app.current_user_id', true)
    );

CREATE POLICY "Users can access their own documents" ON documents
    FOR ALL USING (
        user_id::text = current_setting('app.current_user_id', true)
    );

CREATE POLICY "Users can access their own uploads" ON uploads
    FOR ALL USING (
        user_id::text = current_setting('app.current_user_id', true)
    );

CREATE POLICY "Users can access their own preferences" ON user_preferences
    FOR ALL USING (
        user_id::text = current_setting('app.current_user_id', true)
    );

-- Temporarily disable RLS for testing (can be re-enabled later)
-- Uncomment these lines if you want to disable RLS completely for now:
-- ALTER TABLE users DISABLE ROW LEVEL SECURITY;
-- ALTER TABLE sessions DISABLE ROW LEVEL SECURITY;
-- ALTER TABLE conversations DISABLE ROW LEVEL SECURITY;
-- ALTER TABLE documents DISABLE ROW LEVEL SECURITY;
-- ALTER TABLE uploads DISABLE ROW LEVEL SECURITY;
-- ALTER TABLE user_preferences DISABLE ROW LEVEL SECURITY;