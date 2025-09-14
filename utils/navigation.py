"""
Navigation System
"""

import streamlit as st

def render_navigation():
    """Render navigation sidebar only."""
    # Handle authentication flow
    if not st.session_state.authenticated:
        # Show navigation for unauthenticated users
        render_public_navigation()
    else:
        # Show navigation for authenticated users
        render_authenticated_navigation()

def render_public_navigation():
    """Render navigation for unauthenticated users."""
    with st.sidebar:
        st.markdown("# 💊 PharmGPT")
        
        # Navigation buttons for public users
        if st.button("🏠 Home", use_container_width=True, type="secondary"):
            st.session_state.current_page = "homepage"
            try:
                st.switch_page("pages/1_🏠_Homepage.py")
            except:
                st.rerun()
        
        if st.button("🔐 Sign In", use_container_width=True, type="primary"):
            st.session_state.current_page = "signin"
            try:
                st.switch_page("pages/2_🔐_Sign_In.py")
            except:
                st.rerun()
        
        st.markdown("---")
        st.markdown("### About")
        st.info("PharmGPT is your AI-powered pharmacology learning assistant. Sign in to start chatting!")

def render_authenticated_navigation():
    """Render navigation for authenticated users."""
    from utils.sidebar import render_sidebar
    render_sidebar()