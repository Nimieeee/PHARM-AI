#!/usr/bin/env python3
"""
Minimal database setup script to fix authentication issues
"""

import os
import asyncio
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

async def setup_minimal_database():
    """Setup minimal database structure for authentication"""
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
    
    # Minimal SQL to create users table and authentication functions
    minimal_sql = """
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
    
    -- Create index on username for faster lookups
    CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
    
    -- Create index on email for faster lookups
    CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
    
    -- Create index on session token for faster lookups
    CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(session_token);
    """
    
    print("📋 Executing minimal database setup...")
    print("⚠️  Note: This script provides the SQL statements that need to be executed in Supabase SQL Editor")
    print("📋 Copy and paste the following SQL into your Supabase SQL Editor:\n")
    print("=" * 50)
    print(minimal_sql)
    print("=" * 50)
    
    return True

if __name__ == "__main__":
    print("🚀 Starting minimal database setup...")
    try:
        result = asyncio.run(setup_minimal_database())
        if result:
            print("✅ Minimal database setup completed!")
            print("📋 Please execute the SQL statements above in your Supabase SQL Editor")
        else:
            print("⚠️  Minimal database setup completed with issues")
    except Exception as e:
        print(f"❌ Minimal database setup failed: {e}")
        import traceback
        traceback.print_exc()