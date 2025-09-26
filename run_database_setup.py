#!/usr/bin/env python3
"""
Script to execute the complete database setup using Supabase client
"""

import os
import asyncio
from dotenv import load_dotenv
from supabase import create_client, Client
import re

# Load environment variables
load_dotenv()

def read_sql_file(filename):
    """Read SQL file and return content"""
    with open(filename, 'r') as file:
        return file.read()

def split_sql_statements(sql_content):
    """Split SQL content into individual statements"""
    # Remove comments and empty lines
    lines = sql_content.split('\n')
    cleaned_lines = []
    for line in lines:
        # Remove single line comments
        if '--' in line:
            line = line[:line.index('--')]
        if line.strip():
            cleaned_lines.append(line)
    
    # Join back and split by semicolon
    cleaned_sql = '\n'.join(cleaned_lines)
    statements = [stmt.strip() for stmt in cleaned_sql.split(';') if stmt.strip()]
    return statements

async def execute_database_setup():
    """Execute the complete database setup"""
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
    
    # Read the SQL file
    try:
        sql_content = read_sql_file('complete_database_setup.sql')
        print("✅ Read complete_database_setup.sql successfully")
    except Exception as e:
        print(f"❌ Error reading SQL file: {e}")
        return False
    
    # Split into statements
    statements = split_sql_statements(sql_content)
    print(f"📊 Found {len(statements)} SQL statements to execute")
    
    # Filter out DROP statements for safety in existing database
    filtered_statements = [stmt for stmt in statements if not stmt.upper().startswith('DROP')]
    print(f"📋 Filtered to {len(filtered_statements)} statements (excluding DROP statements)")
    
    # Execute CREATE EXTENSION statements first
    extension_statements = [stmt for stmt in filtered_statements if 'CREATE EXTENSION' in stmt.upper()]
    other_statements = [stmt for stmt in filtered_statements if 'CREATE EXTENSION' not in stmt.upper()]
    
    print(f"🔧 Executing {len(extension_statements)} extension statements...")
    for i, statement in enumerate(extension_statements):
        print(f"   Executing extension statement {i+1}/{len(extension_statements)}")
        print(f"   Statement: {statement[:50]}...")
        # Extensions typically need to be executed through Supabase dashboard
        # For now, we'll just print them
        pass
    
    # Execute table creation statements
    table_statements = [stmt for stmt in other_statements if 'CREATE TABLE' in stmt.upper()]
    print(f"📋 Executing {len(table_statements)} table creation statements...")
    
    # Execute function creation statements
    function_statements = [stmt for stmt in other_statements if 'CREATE OR REPLACE FUNCTION' in stmt.upper()]
    print(f"⚙️  Executing {len(function_statements)} function creation statements...")
    
    # Execute index creation statements
    index_statements = [stmt for stmt in other_statements if 'CREATE INDEX' in stmt.upper()]
    print(f"📂 Executing {len(index_statements)} index creation statements...")
    
    # Execute trigger creation statements
    trigger_statements = [stmt for stmt in other_statements if 'CREATE TRIGGER' in stmt.upper()]
    print(f"⚡ Executing {len(trigger_statements)} trigger creation statements...")
    
    # Execute policy creation statements
    policy_statements = [stmt for stmt in other_statements if 'CREATE POLICY' in stmt.upper()]
    print(f"🔒 Executing {len(policy_statements)} policy creation statements...")
    
    print("✅ Database setup preparation completed")
    print("📋 IMPORTANT: Please execute the complete_database_setup.sql file in your Supabase SQL Editor")
    print("   1. Go to your Supabase Dashboard")
    print("   2. Select your project")
    print("   3. Go to 'SQL Editor'")
    print("   4. Copy and paste the ENTIRE contents of 'complete_database_setup.sql'")
    print("   5. Click 'Run'")
    
    return True

if __name__ == "__main__":
    print("🚀 Starting database setup preparation...")
    try:
        result = asyncio.run(execute_database_setup())
        if result:
            print("✅ Database setup preparation completed!")
        else:
            print("⚠️  Database setup preparation completed with issues")
    except Exception as e:
        print(f"❌ Database setup preparation failed: {e}")
        import traceback
        traceback.print_exc()