"""
Chatbot Page - Streamlit Cloud Compatible
"""

import streamlit as st
import sys
import os

# Add the parent directory to the path so we can import from the main app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Apply Streamlit Cloud fixes first
try:
    from streamlit_cloud_fix import apply_all_fixes
    apply_all_fixes()
except ImportError:
    pass

from utils.session_manager import initialize_session_state
from utils.navigation import render_navigation
from utils.theme import apply_theme
from pages.chatbot import render_chatbot_page
from pages.signin import render_signin_page
from config import APP_TITLE, APP_ICON

# Page configuration
st.set_page_config(
    page_title=f"{APP_TITLE} - Chat",
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    """Chatbot page entry point."""
    # Initialize session state
    initialize_session_state()
    
    # Apply theme
    apply_theme()
    
    # Render navigation
    render_navigation()
    
    # Set current page
    st.session_state.current_page = "chatbot"
    
    # Check authentication
    if st.session_state.authenticated:
        render_chatbot_page()
    else:
        st.error("🔐 Please sign in to access the chatbot.")
        st.info("👈 Use the sidebar to navigate to the Sign In page.")
        
        # Provide direct link to sign in
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🔐 Go to Sign In", use_container_width=True, type="primary"):
                st.session_state.current_page = "signin"
                st.switch_page("pages/2_🔐_Sign_In.py")

if __name__ == "__main__":
    main()