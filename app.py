"""
PharmGPT - AI Pharmacology Assistant
Main Streamlit Application

For Streamlit Cloud deployment, make sure to:
1. Add your API keys to Streamlit Cloud secrets
2. Use app.py as the main file
"""

import streamlit as st
from utils.session_manager import initialize_session_state
from utils.navigation import render_navigation
from utils.theme import apply_theme
from pages.homepage import render_homepage
from pages.signin import render_signin_page
from pages.chatbot import render_chatbot_page
from config import APP_TITLE, APP_ICON

# Page configuration
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    """Main application entry point."""
    # Initialize session state
    initialize_session_state()
    
    # Apply theme
    apply_theme()
    
    # Render navigation
    render_navigation()
    
    # Route to appropriate page
    if st.session_state.current_page == "homepage":
        render_homepage()
    elif st.session_state.current_page == "signin":
        render_signin_page()
    elif st.session_state.current_page == "chatbot":
        if st.session_state.authenticated:
            render_chatbot_page()
        else:
            st.session_state.current_page = "homepage"
            st.rerun()
    else:
        # Default to homepage
        st.session_state.current_page = "homepage"
        st.rerun()

if __name__ == "__main__":
    main()