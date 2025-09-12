#!/usr/bin/env python3
"""
Supabase Database Setup Script for PharmGPT
Run this script to initialize your Supabase database with the required schema.
"""

import os
import sys
import streamlit as st
from supabase import create_client, Client
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def read_sql_file(filename: str) -> str:
    """Read SQL file content."""
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        logger.error(f"SQL file not found: {filename}")
        return ""
    except Exception as e:
        logger.error(f"Error reading SQL file {filename}: {e}")
        return ""

def setup_database():
    """Set up the Supabase database with the required schema."""
    try:
        # Get Supabase credentials
        supabase_url = st.secrets.get("SUPABASE_URL")
        supabase_key = st.secrets.get("SUPABASE_ANON_KEY")
        
        if not supabase_url or not supabase_key:
            logger.error("Supabase credentials not found in Streamlit secrets")
            print("❌ Please add SUPABASE_URL and SUPABASE_ANON_KEY to your Streamlit secrets")
            return False
        
        # Create Supabase client
        supabase: Client = create_client(supabase_url, supabase_key)
        logger.info("Connected to Supabase")
        
        # Read schema file
        schema_sql = read_sql_file("database_schema.sql")
        if not schema_sql:
            logger.error("Failed to read database schema")
            return False
        
        # Split SQL into individual statements
        statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
        
        print("🚀 Setting up database schema...")
        
        # Execute each statement
        for i, statement in enumerate(statements, 1):
            try:
                if statement.upper().startswith(('CREATE', 'ALTER', 'DROP', 'INSERT')):
                    # Use RPC to execute DDL statements
                    result = supabase.rpc('exec_sql', {'sql': statement}).execute()
                    print(f"✅ Executed statement {i}/{len(statements)}")
                    
            except Exception as e:
                # Some statements might fail if objects already exist - that's okay
                if "already exists" in str(e).lower():
                    print(f"⚠️  Statement {i} - Object already exists (skipping)")
                else:
                    logger.warning(f"Statement {i} failed: {e}")
                    print(f"⚠️  Statement {i} failed: {e}")
        
        print("✅ Database schema setup completed!")
        
        # Test the setup by creating a test query
        try:
            result = supabase.table('users').select('count').limit(1).execute()
            print("✅ Database connection test successful!")
            return True
            
        except Exception as e:
            logger.error(f"Database test failed: {e}")
            print(f"❌ Database test failed: {e}")
            return False
            
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        print(f"❌ Setup failed: {e}")
        return False

def verify_setup():
    """Verify that the database setup is working correctly."""
    try:
        # Get Supabase credentials
        supabase_url = st.secrets.get("SUPABASE_URL")
        supabase_key = st.secrets.get("SUPABASE_ANON_KEY")
        
        if not supabase_url or not supabase_key:
            return False
        
        # Create client and test
        supabase: Client = create_client(supabase_url, supabase_key)
        
        # Test each table
        tables = ['users', 'sessions', 'conversations', 'messages', 'documents']
        
        print("🔍 Verifying database setup...")
        
        for table in tables:
            try:
                result = supabase.table(table).select('count').limit(1).execute()
                print(f"✅ Table '{table}' is accessible")
            except Exception as e:
                print(f"❌ Table '{table}' failed: {e}")
                return False
        
        # Test the user_stats view
        try:
            result = supabase.table('user_stats').select('*').limit(1).execute()
            print("✅ View 'user_stats' is accessible")
        except Exception as e:
            print(f"❌ View 'user_stats' failed: {e}")
            return False
        
        print("✅ All database components verified successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

def main():
    """Main setup function."""
    print("🔧 PharmGPT Supabase Database Setup")
    print("=" * 40)
    
    # Check if schema file exists
    if not os.path.exists("database_schema.sql"):
        print("❌ database_schema.sql file not found!")
        print("Please make sure the schema file is in the current directory.")
        sys.exit(1)
    
    # Setup database
    if setup_database():
        print("\n🔍 Verifying setup...")
        if verify_setup():
            print("\n🎉 Supabase setup completed successfully!")
            print("\nYour PharmGPT database is ready to use.")
        else:
            print("\n⚠️  Setup completed but verification failed.")
            print("Please check your Supabase dashboard for any issues.")
    else:
        print("\n❌ Setup failed!")
        print("Please check your Supabase credentials and try again.")
        sys.exit(1)

if __name__ == "__main__":
    main()