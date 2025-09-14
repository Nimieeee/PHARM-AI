"""
Sign In Page - Streamlit Cloud Compatible
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
from utils.theme import apply_theme
from pages.signin import render_signin_page
from config import APP_TITLE, APP_ICON

# Page configuration
st.set_page_config(
    page_title=f"{APP_TITLE} - Sign In",
    page_icon=APP_ICON,
    layout="wide"
)

def main():
    """Sign in page entry point."""
    # Initialize session state
    initialize_session_state()
    
    # Apply theme
    apply_theme()
    
    # Set current page
    st.session_state.current_page = "signin"
    
    # Render sign in page
    render_signin_page()

if __name__ == "__main__":
    main()