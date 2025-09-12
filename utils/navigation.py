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
        st.markdown("# 💊 PharmBot")
        
        # Theme toggle
        st.markdown("### 🎨 Appearance")
        from utils.theme import render_theme_toggle
        render_theme_toggle()
        
        st.markdown("---")
        st.markdown("### About")
        st.info("PharmBot is your AI-powered pharmacology learning assistant. Sign in to start chatting!")

def render_authenticated_navigation():
    """Render navigation for authenticated users."""
    from utils.sidebar import render_sidebar
    render_sidebar()