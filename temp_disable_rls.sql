-- Temporary fix: Disable RLS for users table to allow registration
-- WARNING: This reduces security - use only for testing
-- Run this in your Supabase SQL Editor

-- Temporarily disable RLS for users table
ALTER TABLE users DISABLE ROW LEVEL SECURITY;

-- You can re-enable it later with proper policies:
-- ALTER TABLE users ENABLE ROW LEVEL SECURITY;