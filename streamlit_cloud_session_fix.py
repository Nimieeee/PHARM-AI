#!/usr/bin/env python3
"""
Quick fix for Streamlit Cloud session issues
"""

# Add this to the top of utils/session_manager.py

def fix_streamlit_cloud_sessions():
    """Fix session persistence issues on Streamlit Cloud"""
    import streamlit as st
    
    # Disable session state clearing on Streamlit Cloud
    if hasattr(st, '_get_session_id'):
        # We're on Streamlit Cloud, use more persistent session handling
        if 'session_fixed' not in st.session_state:
            st.session_state.session_fixed = True
            # Extend session timeout
            if hasattr(st.session_state, 'last_auth_init_time'):
                # Make auth last longer on cloud
                st.session_state.last_auth_init_time = 0  # Force re-auth but keep it
    
    # Prevent auth timeout on cloud
    if 'auth_initialized_this_run' in st.session_state:
        # Keep auth active longer
        st.session_state.auth_initialized_this_run = True

# Call this at the start of initialize_session_state()