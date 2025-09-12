-- Quick fix: Add missing email column to users table
-- Run this in your Supabase SQL Editor

ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR(255);

-- Add index for performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);