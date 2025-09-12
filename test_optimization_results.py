"""
Test script to verify optimization effectiveness
"""

import streamlit as st
import time
import logging
from datetime import datetime

# Configure logging to see our optimizations
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    st.title("🚀 Optimization Test Results")
    
    # Track function calls
    if "call_counter" not in st.session_state:
        st.session_state.call_counter = {}
    
    # Test multiple calls to see caching in action
    st.subheader("Testing Session Initialization")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Initialize Session State"):
            from utils.session_manager import initialize_session_state
            start_time = time.time()
            initialize_session_state()
            end_time = time.time()
            st.success(f"✅ Completed in {end_time - start_time:.3f}s")
    
    with col2:
        if st.button("Test Auth Flow"):
            from auth import initialize_auth_session
            start_time = time.time()
            initialize_auth_session()
            end_time = time.time()
            st.success(f"✅ Completed in {end_time - start_time:.3f}s")
    
    with col3:
        if st.button("Test Supabase Connection"):
            from supabase_manager import test_supabase_connection
            start_time = time.time()
            result = test_supabase_connection()
            end_time = time.time()
            if result:
                st.success(f"✅ Connected in {end_time - start_time:.3f}s")
            else:
                st.error(f"❌ Failed in {end_time - start_time:.3f}s")
    
    # Show current session state
    st.subheader("Current Session State")
    with st.expander("Session State Details"):
        st.json(dict(st.session_state))
    
    # Performance metrics
    st.subheader("Performance Improvements")
    
    improvements = [
        "🔥 **Supabase Client Initialization:** Reduced from 2+ calls to 1 call per session",
        "💾 **Session Validation Caching:** 30-second cache prevents duplicate DB hits",
        "🚀 **Auth Initialization Caching:** Smart prevention of redundant auth checks", 
        "👤 **User Data Caching:** 60-second cache for user lookup operations",
        "⚡ **Connection Test Optimization:** Single initialization per session"
    ]
    
    for improvement in improvements:
        st.markdown(improvement)
    
    # Show optimization status
    st.subheader("Optimization Status")
    
    status_checks = {
        "Supabase Client Cache": "auth_initialized_this_run" in st.session_state,
        "Auth Cache Active": "last_auth_init_time" in st.session_state,
        "Session Authenticated": st.session_state.get("authenticated", False),
        "User ID Set": st.session_state.get("user_id") is not None
    }
    
    for check, status in status_checks.items():
        if status:
            st.success(f"✅ {check}")
        else:
            st.info(f"ℹ️ {check}: Not active")

if __name__ == "__main__":
    main()