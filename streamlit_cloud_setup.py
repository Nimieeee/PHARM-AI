"""
Streamlit Cloud Setup for PharmGPT Supabase Integration
This script helps set up the database when running on Streamlit Cloud
"""

import streamlit as st
import os
from supabase import create_client, Client
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_supabase_connection():
    """Check if Supabase is properly configured."""
    try:
        supabase_url = st.secrets.get("SUPABASE_URL")
        supabase_key = st.secrets.get("SUPABASE_ANON_KEY")
        
        if not supabase_url or not supabase_key:
            return False, "Supabase credentials not found in secrets"
        
        # Test connection
        supabase: Client = create_client(supabase_url, supabase_key)
        result = supabase.table('users').select('count').limit(1).execute()
        
        return True, "Connection successful"
        
    except Exception as e:
        return False, str(e)

def setup_database_if_needed():
    """Set up database tables if they don't exist."""
    try:
        supabase_url = st.secrets.get("SUPABASE_URL")
        supabase_key = st.secrets.get("SUPABASE_ANON_KEY")
        
        if not supabase_url or not supabase_key:
            return False, "Supabase credentials not configured"
        
        supabase: Client = create_client(supabase_url, supabase_key)
        
        # Check if tables exist by trying to query them
        tables_to_check = ['users', 'sessions', 'conversations', 'messages', 'documents']
        missing_tables = []
        
        for table in tables_to_check:
            try:
                supabase.table(table).select('count').limit(1).execute()
            except Exception:
                missing_tables.append(table)
        
        if missing_tables:
            return False, f"Missing tables: {', '.join(missing_tables)}. Please run the SQL schema in your Supabase dashboard."
        
        return True, "All tables exist"
        
    except Exception as e:
        return False, str(e)

def main():
    st.title("🔧 PharmGPT Supabase Setup")
    st.write("This page helps you set up Supabase integration for PharmGPT on Streamlit Cloud.")
    
    # Check connection
    st.subheader("1. Connection Test")
    with st.spinner("Testing Supabase connection..."):
        conn_success, conn_message = check_supabase_connection()
    
    if conn_success:
        st.success(f"✅ {conn_message}")
    else:
        st.error(f"❌ {conn_message}")
        st.info("""
        **To fix this:**
        1. Go to your Streamlit Cloud app settings
        2. Add these secrets:
           - `SUPABASE_URL`: Your Supabase project URL
           - `SUPABASE_ANON_KEY`: Your Supabase anon/public key
        3. Restart your app
        """)
        return
    
    # Check database setup
    st.subheader("2. Database Setup")
    with st.spinner("Checking database tables..."):
        db_success, db_message = setup_database_if_needed()
    
    if db_success:
        st.success(f"✅ {db_message}")
    else:
        st.error(f"❌ {db_message}")
        
        st.info("""
        **To set up your database:**
        1. Go to your Supabase dashboard
        2. Navigate to the SQL Editor
        3. Copy and paste the SQL schema from `database_schema.sql`
        4. Run the SQL to create all tables and policies
        """)
        
        # Show the SQL schema
        if st.button("Show Database Schema SQL"):
            try:
                with open("database_schema.sql", "r") as f:
                    schema_sql = f.read()
                st.code(schema_sql, language="sql")
            except FileNotFoundError:
                st.error("database_schema.sql file not found")
        
        return
    
    # Test user operations
    st.subheader("3. Test User Operations")
    
    if st.button("Test User Creation"):
        from services.user_service import UserService
        from datetime import datetime
        
        user_service = UserService()
        test_username = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        with st.spinner("Creating test user..."):
            success, message = user_service.create_user(test_username, "testpass123", "test@example.com")
        
        if success:
            st.success(f"✅ Test user created: {test_username}")
            
            # Test authentication
            with st.spinner("Testing authentication..."):
                auth_success, auth_message, user_data = user_service.authenticate_user(test_username, "testpass123")
            
            if auth_success:
                st.success("✅ Authentication test successful")
                st.json({"username": user_data["username"], "user_id": user_data["user_id"]})
            else:
                st.error(f"❌ Authentication failed: {auth_message}")
        else:
            st.error(f"❌ User creation failed: {message}")
    
    # Show connection stats
    st.subheader("4. Connection Statistics")
    try:
        from supabase_manager import get_connection_stats
        stats = get_connection_stats()
        st.json(stats)
    except Exception as e:
        st.error(f"Error getting stats: {e}")
    
    st.success("🎉 Setup complete! Your PharmGPT app should now work with Supabase.")

if __name__ == "__main__":
    main()