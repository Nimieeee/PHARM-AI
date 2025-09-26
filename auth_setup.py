#!/usr/bin/env python3
"""
Database setup script with authentication functions
"""

import os
import asyncio
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

async def setup_auth_database():
    """Setup database structure with authentication functions"""
    # Get Supabase credentials
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_ANON_KEY")
    
    if not url or not key:
        print("❌ Error: SUPABASE_URL and SUPABASE_ANON_KEY must be set in .env file")
        return False
    
    print(f"🔗 Connecting to Supabase at {url}")
    
    # Create Supabase client
    supabase: Client = create_client(url, key)
    print("✅ Supabase client created successfully")
    
    # SQL to create users table, sessions table, and authentication functions
    auth_sql = """
    -- Enable required extensions
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    CREATE EXTENSION IF NOT EXISTS vector;
    CREATE EXTENSION IF NOT EXISTS pgcrypto;
    
    -- Create users table with display_name column
    CREATE TABLE IF NOT EXISTS users (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        user_id VARCHAR(255) UNIQUE NOT NULL,
        username VARCHAR(255) NOT NULL,
        email VARCHAR(255) UNIQUE,
        password_hash VARCHAR(255),
        display_name VARCHAR(255),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        last_login TIMESTAMP WITH TIME ZONE,
        is_active BOOLEAN DEFAULT TRUE,
        profile_data JSONB DEFAULT '{}'
    );
    
    -- Create sessions table
    CREATE TABLE IF NOT EXISTS sessions (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        user_uuid UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        session_token VARCHAR(255) UNIQUE NOT NULL,
        expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        ip_address INET,
        user_agent TEXT,
        is_active BOOLEAN DEFAULT TRUE
    );
    
    -- Create indexes
    CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
    CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
    CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(session_token);
    CREATE INDEX IF NOT EXISTS idx_sessions_user_uuid ON sessions(user_uuid);
    
    -- Create updated_at trigger function
    CREATE OR REPLACE FUNCTION update_updated_at_column()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = NOW();
        RETURN NEW;
    END;
    $$ language 'plpgsql';
    
    -- Apply trigger to users table
    DROP TRIGGER IF EXISTS update_users_updated_at ON users;
    CREATE TRIGGER update_users_updated_at
        BEFORE UPDATE ON users
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    
    -- Function to create user account
    CREATE OR REPLACE FUNCTION create_user_account(
        p_username VARCHAR,
        p_password VARCHAR,
        p_email VARCHAR DEFAULT NULL
    )
    RETURNS TABLE (
        success BOOLEAN,
        user_id UUID,
        message TEXT
    ) AS $$
    DECLARE
        v_user_id UUID;
        v_password_hash VARCHAR;
    BEGIN
        -- Check if username exists
        IF EXISTS (SELECT 1 FROM users WHERE username = p_username) THEN
            RETURN QUERY SELECT FALSE, NULL::UUID, 'Username already exists';
            RETURN;
        END IF;
        
        -- Check if email exists
        IF p_email IS NOT NULL AND EXISTS (SELECT 1 FROM users WHERE email = p_email) THEN
            RETURN QUERY SELECT FALSE, NULL::UUID, 'Email already exists';
            RETURN;
        END IF;
        
        -- Hash password
        v_password_hash := crypt(p_password, gen_salt('bf', 10));
        
        -- Create user
        INSERT INTO users (username, email, password_hash, display_name)
        VALUES (p_username, p_email, v_password_hash, p_username)
        RETURNING id INTO v_user_id;
        
        RETURN QUERY SELECT TRUE, v_user_id, 'User created successfully';
    END;
    $$ LANGUAGE plpgsql SECURITY DEFINER;
    
    -- Function to authenticate user
    CREATE OR REPLACE FUNCTION authenticate_user(
        p_username VARCHAR,
        p_password VARCHAR
    )
    RETURNS TABLE (
        success BOOLEAN,
        user_id UUID,
        username VARCHAR,
        display_name VARCHAR,
        message TEXT
    ) AS $$
    DECLARE
        v_user_id UUID;
        v_password_hash VARCHAR;
        v_display_name VARCHAR;
    BEGIN
        -- Get user details
        SELECT id, password_hash, display_name 
        INTO v_user_id, v_password_hash, v_display_name
        FROM users 
        WHERE username = p_username AND is_active = TRUE;
        
        -- Check if user exists
        IF v_user_id IS NULL THEN
            RETURN QUERY SELECT FALSE, NULL::UUID, NULL::VARCHAR, NULL::VARCHAR, 'User not found';
            RETURN;
        END IF;
        
        -- Verify password
        IF v_password_hash IS NOT NULL AND p_password IS NOT NULL THEN
            IF crypt(p_password, v_password_hash) = v_password_hash THEN
                -- Update last login
                UPDATE users SET last_login = NOW() WHERE id = v_user_id;
                RETURN QUERY SELECT TRUE, v_user_id, p_username, v_display_name, 'Authentication successful';
            ELSE
                RETURN QUERY SELECT FALSE, NULL::UUID, NULL::VARCHAR, NULL::VARCHAR, 'Invalid password';
            END IF;
        ELSE
            RETURN QUERY SELECT FALSE, NULL::UUID, NULL::VARCHAR, NULL::VARCHAR, 'Authentication failed';
        END IF;
    END;
    $$ LANGUAGE plpgsql SECURITY DEFINER;
    
    -- Function to validate session token
    CREATE OR REPLACE FUNCTION validate_session_token(p_session_token VARCHAR)
    RETURNS TABLE (
        success BOOLEAN,
        user_id UUID,
        username VARCHAR,
        display_name VARCHAR,
        message TEXT
    ) AS $$
    DECLARE
        v_user_id UUID;
        v_username VARCHAR;
        v_display_name VARCHAR;
    BEGIN
        -- Get user details from session
        SELECT u.id, u.username, u.display_name
        INTO v_user_id, v_username, v_display_name
        FROM sessions s
        JOIN users u ON s.user_uuid = u.id
        WHERE s.session_token = p_session_token 
        AND s.expires_at > NOW() 
        AND s.is_active = TRUE;
        
        -- Check if session is valid
        IF v_user_id IS NOT NULL THEN
            -- Update last activity
            UPDATE sessions SET last_activity = NOW() WHERE session_token = p_session_token;
            RETURN QUERY SELECT TRUE, v_user_id, v_username, v_display_name, 'Session valid';
        ELSE
            RETURN QUERY SELECT FALSE, NULL::UUID, NULL::VARCHAR, NULL::VARCHAR, 'Invalid or expired session';
        END IF;
    END;
    $$ LANGUAGE plpgsql SECURITY DEFINER;
    
    -- Function to enable testing mode (bypasses RLS temporarily)
    CREATE OR REPLACE FUNCTION enable_testing_mode()
    RETURNS VOID
    LANGUAGE plpgsql
    SECURITY DEFINER
    AS $$
    BEGIN
        -- Set bypass flag for testing
        PERFORM set_config('app.testing_mode', 'true', false);
        RAISE NOTICE 'Testing mode enabled - RLS policies will be bypassed';
    END;
    $$;
    
    -- Function to disable testing mode
    CREATE OR REPLACE FUNCTION disable_testing_mode()
    RETURNS VOID
    LANGUAGE plpgsql
    SECURITY DEFINER
    AS $$
    BEGIN
        -- Remove bypass flag
        PERFORM set_config('app.testing_mode', 'false', false);
        RAISE NOTICE 'Testing mode disabled - RLS policies are active';
    END;
    $$;
    """
    
    print("📋 Executing authentication database setup...")
    print("⚠️  Note: This script provides the SQL statements that need to be executed in Supabase SQL Editor")
    print("📋 Copy and paste the following SQL into your Supabase SQL Editor:\n")
    print("=" * 50)
    print(auth_sql)
    print("=" * 50)
    
    return True

if __name__ == "__main__":
    print("🚀 Starting authentication database setup...")
    try:
        result = asyncio.run(setup_auth_database())
        if result:
            print("✅ Authentication database setup completed!")
            print("📋 Please execute the SQL statements above in your Supabase SQL Editor")
        else:
            print("⚠️  Authentication database setup completed with issues")
    except Exception as e:
        print(f"❌ Authentication database setup failed: {e}")
        import traceback
        traceback.print_exc()