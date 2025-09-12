#!/usr/bin/env python3
"""
Database Setup Checker for PharmGPT
Verifies that your Supabase database schema is properly configured
"""

import streamlit as st
from supabase_manager import connection_manager, health_check

def check_database_schema():
    """Check if the database schema is properly set up."""
    print("🔍 Checking Supabase database schema...")
    
    # Check connection
    health = health_check()
    if not health['supabase_available']:
        print("❌ Supabase library not available. Please install: pip install supabase")
        return False
    
    if not health['client_initialized']:
        print("❌ Supabase client not initialized. Please check your credentials in Streamlit secrets.")
        return False
    
    if not health['connection_test']:
        print("❌ Supabase connection test failed. Please check your configuration.")
        return False
    
    print("✅ Supabase connection successful")
    
    # Check required tables
    required_tables = ['users', 'sessions', 'conversations', 'documents', 'uploads', 'user_preferences']
    
    for table in required_tables:
        try:
            # Try to query the table structure
            result = connection_manager.execute_query(
                table=table,
                operation='select',
                columns='*',
                limit=1
            )
            print(f"✅ Table '{table}' exists and is accessible")
        except Exception as e:
            print(f"❌ Table '{table}' missing or inaccessible: {str(e)}")
            print(f"   Please run the SQL schema from 'supabase_schema.sql' in your Supabase SQL editor")
            return False
    
    print("\n🎉 Database schema check completed successfully!")
    print("Your Supabase database is properly configured for PharmGPT.")
    return True

def setup_instructions():
    """Print setup instructions."""
    print("\n" + "="*60)
    print("SUPABASE SETUP INSTRUCTIONS")
    print("="*60)
    print("1. Go to your Supabase project dashboard")
    print("2. Navigate to 'SQL Editor'")
    print("3. Copy the contents of 'supabase_schema.sql' from your project")
    print("4. Paste and run the SQL script")
    print("5. Verify all tables were created successfully")
    print("6. Run this script again to verify setup")
    print("\nFor detailed instructions, see: SUPABASE_MIGRATION_GUIDE.md")
    print("="*60)

if __name__ == "__main__":
    try:
        # Try to load Streamlit secrets
        if hasattr(st, 'secrets'):
            success = check_database_schema()
        else:
            # Try to load secrets from file for command line usage
            import os
            if os.path.exists(".streamlit/secrets.toml"):
                import toml
                secrets = toml.load(".streamlit/secrets.toml")
                # Mock streamlit secrets
                st.secrets = type('Secrets', (), secrets)()
                success = check_database_schema()
            else:
                print("❌ Streamlit secrets not found.")
                print("Please ensure your Supabase credentials are configured.")
                success = False
        
        if not success:
            setup_instructions()
            exit(1)
        else:
            print("\n🚀 Your PharmGPT database is ready!")
            
    except Exception as e:
        print(f"❌ Error checking database: {str(e)}")
        setup_instructions()
        exit(1)