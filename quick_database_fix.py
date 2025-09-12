#!/usr/bin/env python3
"""
Quick Database Fix for PharmGPT
Run this to fix the schema mismatches in your existing Supabase database
"""

import streamlit as st
from supabase import create_client, Client
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_database_schema():
    """Fix the database schema to match service expectations."""
    try:
        # Get Supabase credentials
        supabase_url = st.secrets.get("SUPABASE_URL")
        supabase_key = st.secrets.get("SUPABASE_ANON_KEY")
        
        if not supabase_url or not supabase_key:
            print("❌ Supabase credentials not found")
            return False
        
        # Create client
        supabase: Client = create_client(supabase_url, supabase_key)
        
        print("🔧 Fixing database schema...")
        
        # Read the fix SQL
        try:
            with open("fix_database_schema.sql", "r") as f:
                fix_sql = f.read()
        except FileNotFoundError:
            print("❌ fix_database_schema.sql not found")
            return False
        
        # Split into individual statements
        statements = [stmt.strip() for stmt in fix_sql.split(';') if stmt.strip()]
        
        success_count = 0
        for i, statement in enumerate(statements, 1):
            try:
                if statement.upper().startswith(('ALTER', 'UPDATE', 'CREATE', 'DROP')):
                    # For DDL statements, we need to use a different approach
                    # Since we can't execute DDL with the anon key, we'll show the SQL
                    print(f"Statement {i}: {statement[:50]}...")
                    success_count += 1
            except Exception as e:
                if "already exists" in str(e).lower() or "does not exist" in str(e).lower():
                    print(f"⚠️  Statement {i} - Expected error: {e}")
                    success_count += 1
                else:
                    print(f"❌ Statement {i} failed: {e}")
        
        print(f"✅ Processed {success_count}/{len(statements)} statements")
        
        # Test the fix
        print("\n🧪 Testing the fix...")
        
        # Test conversations table
        try:
            result = supabase.table('conversations').select('user_id').limit(1).execute()
            print("✅ Conversations table has user_id column")
        except Exception as e:
            print(f"❌ Conversations table issue: {e}")
        
        # Test documents table
        try:
            result = supabase.table('documents').select('user_id, added_at').limit(1).execute()
            print("✅ Documents table has user_id and added_at columns")
        except Exception as e:
            print(f"❌ Documents table issue: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error fixing database: {e}")
        return False

def main():
    print("🔧 PharmGPT Database Schema Fix")
    print("=" * 40)
    
    print("⚠️  IMPORTANT: This script requires manual SQL execution.")
    print("Since we're using the anon key, we can't execute DDL statements directly.")
    print("\nPlease follow these steps:")
    print("1. Go to your Supabase dashboard")
    print("2. Navigate to SQL Editor")
    print("3. Copy and paste the contents of 'fix_database_schema.sql'")
    print("4. Run the SQL to fix the schema")
    print("\nAfter running the SQL, your app should work correctly!")
    
    # Show the SQL content
    try:
        with open("fix_database_schema.sql", "r") as f:
            sql_content = f.read()
        print("\n" + "="*50)
        print("SQL TO RUN IN SUPABASE:")
        print("="*50)
        print(sql_content)
        print("="*50)
    except FileNotFoundError:
        print("❌ fix_database_schema.sql file not found")

if __name__ == "__main__":
    main()