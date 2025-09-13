#!/usr/bin/env python3
"""
Streamlit Cloud Database Check
Verify that the database functions are working correctly on Streamlit Cloud
"""

import asyncio
import logging
import streamlit as st
from supabase_manager import get_supabase_client

# Configure logging for Streamlit Cloud
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_streamlit_cloud_database():
    """Check database connectivity and functions on Streamlit Cloud."""
    try:
        st.write("🔍 **Checking Streamlit Cloud Database Connection...**")
        
        # Get client
        client = await get_supabase_client()
        if not client:
            st.error("❌ Could not connect to Supabase")
            return False

        st.success("✅ Connected to Supabase successfully")

        # Check core tables
        st.write("📊 **Checking Core Tables:**")
        
        tables_to_check = ['users', 'conversations', 'messages', 'documents', 'sessions']
        
        for table in tables_to_check:
            try:
                result = await client.table(table).select('count').limit(1).execute()
                st.write(f"✅ Table `{table}` is accessible")
            except Exception as e:
                st.error(f"❌ Table `{table}` failed: {e}")
                return False

        # Check RLS functions (optional)
        st.write("🔐 **Checking RLS Functions (Optional):**")
        
        try:
            await client.rpc('set_user_context', {
                'user_identifier': 'test-user-123'
            }).execute()
            st.write("✅ `set_user_context` function exists and works")
        except Exception as e:
            if "PGRST202" in str(e) or "not found" in str(e).lower():
                st.info("ℹ️ `set_user_context` function not found (optional - RLS context setting disabled)")
            else:
                st.warning(f"⚠️ `set_user_context` function error: {e}")

        try:
            result = await client.rpc('get_current_user_id').execute()
            st.write(f"✅ `get_current_user_id` function exists, returned: {result.data}")
        except Exception as e:
            if "PGRST202" in str(e) or "not found" in str(e).lower():
                st.info("ℹ️ `get_current_user_id` function not found (optional - RLS context reading disabled)")
            else:
                st.warning(f"⚠️ `get_current_user_id` function error: {e}")

        st.success("🎉 **Database check completed successfully!**")
        st.info("Your PharmGPT database is ready to use on Streamlit Cloud.")
        
        return True

    except Exception as e:
        st.error(f"💥 Database check failed: {e}")
        logger.error(f"Database check failed: {e}")
        return False

def main():
    """Main Streamlit app for database checking."""
    st.title("🔧 PharmGPT Database Health Check")
    st.write("This tool verifies that your Supabase database is properly configured for Streamlit Cloud.")
    
    if st.button("🚀 Run Database Check"):
        with st.spinner("Checking database..."):
            # Run the async check
            result = asyncio.run(check_streamlit_cloud_database())
            
            if result:
                st.balloons()
            else:
                st.error("Database check failed. Please check the logs above.")

    st.write("---")
    st.write("### 📝 Next Steps")
    
    with st.expander("If RLS functions are missing (optional)"):
        st.write("If you want to enable Row Level Security context functions:")
        st.write("1. Go to your Supabase Dashboard")
        st.write("2. Navigate to SQL Editor")
        st.write("3. Paste and run this SQL:")
        
        st.code("""
-- Function to set user context for RLS
CREATE OR REPLACE FUNCTION set_user_context(user_identifier TEXT)
RETURNS VOID AS $$
BEGIN
    PERFORM set_config('app.current_user_id', user_identifier, false);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get current user context
CREATE OR REPLACE FUNCTION get_current_user_id()
RETURNS TEXT AS $$
BEGIN
    RETURN current_setting('app.current_user_id', true);
END;
$$ LANGUAGE plpgsql;
        """, language="sql")
        
        st.write("4. Run this check again to verify")

if __name__ == "__main__":
    main()