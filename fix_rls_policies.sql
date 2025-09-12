-- Fix RLS policies to allow user registration
-- Run this in your Supabase SQL Editor

-- Drop the existing restrictive policy for users
DROP POLICY IF EXISTS "Users can access their own profile" ON users;

-- Create separate policies for different operations
-- Allow anyone to INSERT (register) new users
CREATE POLICY "Allow user registration" ON users
    FOR INSERT WITH CHECK (true);

-- Allow users to SELECT their own profile
CREATE POLICY "Users can view their own profile" ON users
    FOR SELECT USING (
        id = auth.uid() OR 
        user_id = current_setting('app.current_user_id', true) OR
        id::text = current_setting('app.current_user_id', true)
    );

-- Allow users to UPDATE their own profile
CREATE POLICY "Users can update their own profile" ON users
    FOR UPDATE USING (
        id = auth.uid() OR 
        user_id = current_setting('app.current_user_id', true) OR
        id::text = current_setting('app.current_user_id', true)
    );

-- Allow users to DELETE their own profile (optional - you might want to restrict this)
CREATE POLICY "Users can delete their own profile" ON users
    FOR DELETE USING (
        id = auth.uid() OR 
        user_id = current_setting('app.current_user_id', true) OR
        id::text = current_setting('app.current_user_id', true)
    );