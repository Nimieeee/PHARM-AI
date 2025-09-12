#!/usr/bin/env python3
"""
Test script to diagnose Streamlit Cloud issues
"""

import streamlit as st
import sys
import traceback

st.title("🔧 Streamlit Cloud Diagnostic Test")

st.write("## System Information")
st.write(f"Python version: {sys.version}")
st.write(f"Streamlit version: {st.__version__}")

st.write("## Import Tests")

# Test 1: Basic imports
try:
    import asyncio
    st.success("✅ asyncio imported successfully")
except Exception as e:
    st.error(f"❌ asyncio import failed: {e}")

# Test 2: Supabase import
try:
    from supabase import create_client, Client
    st.success("✅ supabase imported successfully")
except Exception as e:
    st.error(f"❌ supabase import failed: {e}")
    st.code(traceback.format_exc())

# Test 3: Config import
try:
    from config import SUPABASE_URL, SUPABASE_ANON_KEY
    if SUPABASE_URL and SUPABASE_ANON_KEY:
        st.success("✅ Config loaded successfully")
        st.write(f"Supabase URL: {SUPABASE_URL[:20]}...")
    else:
        st.error("❌ Supabase credentials not found in secrets")
except Exception as e:
    st.error(f"❌ Config import failed: {e}")
    st.code(traceback.format_exc())

# Test 4: Supabase manager import
try:
    from supabase_manager import get_supabase_client
    st.success("✅ supabase_manager imported successfully")
except Exception as e:
    st.error(f"❌ supabase_manager import failed: {e}")
    st.code(traceback.format_exc())

# Test 5: Services import
try:
    from services.user_service import user_service
    st.success("✅ user_service imported successfully")
except Exception as e:
    st.error(f"❌ user_service import failed: {e}")
    st.code(traceback.format_exc())

try:
    from services.session_service import session_service
    st.success("✅ session_service imported successfully")
except Exception as e:
    st.error(f"❌ session_service import failed: {e}")
    st.code(traceback.format_exc())

try:
    from services.conversation_service import conversation_service
    st.success("✅ conversation_service imported successfully")
except Exception as e:
    st.error(f"❌ conversation_service import failed: {e}")
    st.code(traceback.format_exc())

# Test 6: Auth import
try:
    from auth import authenticate_user, initialize_auth_session
    st.success("✅ auth imported successfully")
except Exception as e:
    st.error(f"❌ auth import failed: {e}")
    st.code(traceback.format_exc())

# Test 7: Database connection
st.write("## Database Connection Test")
try:
    from supabase_manager import get_supabase_client
    client = get_supabase_client()
    if client:
        # Test a simple query
        result = client.table('users').select('count').limit(1).execute()
        st.success("✅ Database connection successful")
    else:
        st.error("❌ Failed to get Supabase client")
except Exception as e:
    st.error(f"❌ Database connection failed: {e}")
    st.code(traceback.format_exc())

# Test 8: Authentication test
st.write("## Authentication Test")
try:
    from auth import authenticate_user
    # Test with dummy credentials (should fail gracefully)
    result = authenticate_user("test_user", "test_pass")
    st.success(f"✅ Authentication function works: {result}")
except Exception as e:
    st.error(f"❌ Authentication test failed: {e}")
    st.code(traceback.format_exc())

st.write("## Environment Variables")
try:
    import os
    st.write("Environment variables:")
    for key in sorted(os.environ.keys()):
        if any(secret in key.upper() for secret in ['KEY', 'SECRET', 'TOKEN', 'PASSWORD']):
            st.write(f"{key}: [HIDDEN]")
        else:
            st.write(f"{key}: {os.environ[key][:50]}...")
except Exception as e:
    st.error(f"Error reading environment: {e}")