-- Complete RLS fix for user registration
-- This addresses the specific issue with user creation in your app

-- First, disable RLS temporarily to clear any conflicting policies
ALTER TABLE users DISABLE ROW LEVEL SECURITY;

-- Drop all existing policies on users table
DROP POLICY IF EXISTS "Users can access their own profile" ON users;
DROP POLICY IF EXISTS "Allow user registration" ON users;
DROP POLICY IF EXISTS "Users can view their own profile" ON users;
DROP POLICY IF EXISTS "Users can update their own profile" ON users;
DROP POLICY IF EXISTS "Users can delete their own profile" ON users;

-- Re-enable RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Create a simple policy that allows all operations for now
-- You can make this more restrictive later once user registration works
CREATE POLICY "Allow all operations on users" ON users
    FOR ALL USING (true) WITH CHECK (true);

-- Alternative: If you want more security, use these specific policies instead:
-- (Comment out the above policy and uncomment these)

/*
-- Allow user registration (INSERT)
CREATE POLICY "Allow user registration" ON users
    FOR INSERT WITH CHECK (true);

-- Allow users to view their own data
CREATE POLICY "Users can view own data" ON users
    FOR SELECT USING (
        auth.uid()::text = id::text OR 
        auth.uid()::text = user_id OR
        current_setting('app.current_user_id', true) = user_id OR
        current_setting('app.current_user_id', true) = id::text
    );

-- Allow users to update their own data
CREATE POLICY "Users can update own data" ON users
    FOR UPDATE USING (
        auth.uid()::text = id::text OR 
        auth.uid()::text = user_id OR
        current_setting('app.current_user_id', true) = user_id OR
        current_setting('app.current_user_id', true) = id::text
    );

-- Allow users to delete their own data
CREATE POLICY "Users can delete own data" ON users
    FOR DELETE USING (
        auth.uid()::text = id::text OR 
        auth.uid()::text = user_id OR
        current_setting('app.current_user_id', true) = user_id OR
        current_setting('app.current_user_id', true) = id::text
    );
*/