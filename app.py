"""
PharmGPT - AI Pharmacology Assistant
Main Streamlit Application

For Streamlit Cloud deployment, make sure to:
1. Add your API keys to Streamlit Cloud secrets
2. Use app.py as the main file
"""

# Apply Streamlit Cloud fixes first
try:
    from streamlit_cloud_fix import apply_all_fixes
    apply_all_fixes()
except ImportError:
    pass  # Fixes not available, continue anyway

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
    import logging
    logger = logging.getLogger(__name__)
    logger.info("🚀 App started - main() called.")
    
    # Handle URL routing for Streamlit Cloud
    handle_url_routing()
    
    # Check for setup page via query params
    query_params = st.query_params
    if query_params.get("page") == "setup":
        # Import and run setup page
        try:
            import streamlit_cloud_setup
            streamlit_cloud_setup.main()
            return
        except ImportError:
            st.error("Setup page not available")
            return
    
    # Initialize session state
    initialize_session_state()
    
    # Apply theme
    apply_theme()
    
    # Render navigation
    render_navigation()
    
    # Route to appropriate page with optimized logic
    current_page = st.session_state.current_page
    authenticated = st.session_state.authenticated
    
    if current_page == "homepage":
        render_homepage()
    elif current_page == "signin":
        render_signin_page()
    elif current_page == "chatbot":
        if authenticated:
            render_chatbot_page()
        else:
            # Redirect to signin for unauthenticated users
            st.session_state.current_page = "signin"
            render_signin_page()
    else:
        # Default to homepage without rerun
        st.session_state.current_page = "homepage"
        render_homepage()

def handle_url_routing():
    """Handle direct URL access for Streamlit Cloud."""
    try:
        # Check if we're accessing a direct page URL
        query_params = st.query_params
        
        # Handle direct page access via URL parameters
        if "page" in query_params:
            page = query_params["page"]
            if page in ["homepage", "signin", "chatbot", "chatbot_complex"]:
                # Map chatbot_complex to regular chatbot
                if page == "chatbot_complex":
                    page = "chatbot"
                st.session_state.current_page = page
                logger = logging.getLogger(__name__)
                logger.info(f"URL routing: Set page to {page}")
        
        # Handle Streamlit multipage navigation
        # If user is accessing via sidebar navigation, respect that
        if hasattr(st, 'session_state') and 'current_page' not in st.session_state:
            # Default to homepage for new sessions
            st.session_state.current_page = "homepage"
            
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"URL routing error (non-critical): {e}")
        # Continue with default routing

if __name__ == "__main__":
    main()