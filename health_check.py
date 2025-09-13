#!/usr/bin/env python3
"""
Health check script for PharmGPT
Use this to diagnose issues on Streamlit Cloud
"""

import streamlit as st
import sys
import os
import traceback
import asyncio

def run_async(coro):
    """Run async function in Streamlit context with better error handling."""
    import logging
    logger = logging.getLogger(__name__)

    try:
        # Try to get existing event loop
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError("Event loop is closed")
    except RuntimeError:
        # Create new event loop for Streamlit Cloud compatibility
        logger.info("Creating new event loop for async operation")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    try:
        return loop.run_until_complete(coro)
    except Exception as e:
        logger.error(f"Error running async operation: {e}")
        raise

def main():
    st.title("🏥 PharmGPT Health Check")

    # Basic system info
    st.subheader("System Information")
    col1, col2 = st.columns(2)

    with col1:
        st.metric("Python Version", f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
        st.metric("Streamlit Version", st.__version__)

    with col2:
        is_cloud = any([
            'STREAMLIT_CLOUD' in os.environ,
            'STREAMLIT_SHARING' in os.environ,
            '.streamlit.app' in os.environ.get('HOSTNAME', ''),
            'streamlit.app' in os.environ.get('SERVER_NAME', '')
        ])
        st.metric("Environment", "Streamlit Cloud" if is_cloud else "Local")

    # Test imports
    st.subheader("Import Tests")

    tests = [
        ("asyncio", lambda: __import__('asyncio')),
        ("supabase", lambda: __import__('supabase')),
        ("config", lambda: __import__('config')),
        ("supabase_manager", lambda: __import__('supabase_manager')),
        ("services.user_service", lambda: __import__('services.user_service')),
        ("services.session_service", lambda: __import__('services.session_service')),
        ("services.conversation_service", lambda: __import__('services.conversation_service')),
        ("auth", lambda: __import__('auth')),
    ]

    for name, test_func in tests:
        try:
            test_func()
            st.success(f"✅ {name}")
        except Exception as e:
            st.error(f"❌ {name}: {str(e)}")
            with st.expander(f"Error details for {name}"):
                st.code(traceback.format_exc())

    # Test secrets
    st.subheader("Secrets Check")
    required_secrets = [
        "SUPABASE_URL",
        "SUPABASE_ANON_KEY",
        "GROQ_API_KEY",
        "OPENROUTER_API_KEY"
    ]

    for secret in required_secrets:
        try:
            value = st.secrets[secret]
            if value:
                st.success(f"✅ {secret} (length: {len(str(value))})")
            else:
                st.error(f"❌ {secret} is empty")
        except KeyError:
            st.error(f"❌ {secret} not found in secrets")

    # Test database connection
    st.subheader("Database Connection")
    try:
        from supabase_manager import get_supabase_client

        async def _test_db():
            client = await get_supabase_client()
            if client:
                # Test query
                await client.table('users').select('count').limit(1).execute()
                return True
            return False

        if run_async(_test_db()):
            st.success("✅ Database connection successful")
        else:
            st.error("❌ Failed to get Supabase client")
    except Exception as e:
        st.error(f"❌ Database connection failed: {str(e)}")
        with st.expander("Database error details"):
            st.code(traceback.format_exc())

    # Test authentication
    st.subheader("Authentication Test")
    try:
        from auth import authenticate_user
        # Test with dummy credentials (should fail gracefully)
        result = authenticate_user("test_user", "test_pass")
        if isinstance(result, tuple) and len(result) == 2:
            st.success("✅ Authentication function working correctly")
        else:
            st.error(f"❌ Authentication function returned unexpected result: {result}")
    except Exception as e:
        st.error(f"❌ Authentication test failed: {str(e)}")
        with st.expander("Authentication error details"):
            st.code(traceback.format_exc())

if __name__ == "__main__":
    main()
