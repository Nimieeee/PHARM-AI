"""
Sign In Page - Multipage Streamlit App
"""

import streamlit as st
import sys
import os

# Add the parent directory to the path so we can import from the main app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.session_manager import initialize_session_state
from utils.theme import apply_theme
from auth import authenticate_user, create_user, get_user_legacy_id, initialize_auth_session

# Page configuration
st.set_page_config(
    page_title="Sign In - PharmGPT",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def main():
    """Main sign in page entry point."""
    # Initialize session state and theme
    initialize_session_state()
    apply_theme()
    initialize_auth_session()
    
    # Add mobile optimizations
    from utils.theme import add_mobile_meta_tags
    
    # If already authenticated, redirect to chatbot
    if st.session_state.get('authenticated'):
        st.success(f"Welcome back, {st.session_state.username}!")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("Continue to Chatbot", use_container_width=True, type="primary"):
                st.switch_page("pages/3_💬_Chatbot.py")
            if st.button("← Back to Home", use_container_width=True):
                st.switch_page("app.py")
        return
    
    # Get current theme for styling
    is_dark_mode = st.session_state.get('dark_mode', True)
    
    # Theme-aware colors
    if is_dark_mode:
        header_color = "#f8fafc"
        tab_list_bg = "#1e293b"
        tab_inactive_bg = "#334155"
        tab_inactive_color = "#94a3b8"
        tab_inactive_border = "#475569"
        tab_hover_bg = "#475569"
        tab_hover_color = "#e2e8f0"
    else:
        header_color = "#333333"
        tab_list_bg = "#f8fafc"
        tab_inactive_bg = "#ffffff"
        tab_inactive_color = "#6b7280"
        tab_inactive_border = "#e5e7eb"
        tab_hover_bg = "#f9fafb"
        tab_hover_color = "#374151"
    
    # Custom CSS for sign in page with theme support
    st.markdown(f"""
    <style>
    .auth-container {{
        max-width: 500px;
        margin: 0 auto;
        padding: 16px;
        background: transparent;
        border-radius: 0;
        box-shadow: none;
        margin-top: 0;
    }}
    .auth-header {{
        text-align: center;
        margin-bottom: 2rem;
        color: {header_color};
        padding: 16px;
    }}
    .auth-header h1 {{
        color: {header_color};
    }}
    .auth-header p {{
        color: {header_color};
        opacity: 0.8;
    }}
    
    /* Theme-aware tab styling */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px !important;
        padding: 8px !important;
        background-color: {tab_list_bg} !important;
        border-radius: 12px !important;
        margin-bottom: 24px !important;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        padding: 16px 24px !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        font-size: 16px !important;
        min-height: 48px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        transition: all 0.2s ease !important;
    }}
    
    .stTabs [aria-selected="true"] {{
        background-color: #6366f1 !important;
        color: white !important;
        font-weight: 600 !important;
        box-shadow: 0 2px 4px rgba(99, 102, 241, 0.2) !important;
    }}
    
    .stTabs [aria-selected="false"] {{
        background-color: {tab_inactive_bg} !important;
        color: {tab_inactive_color} !important;
        border: 1px solid {tab_inactive_border} !important;
    }}
    
    .stTabs [aria-selected="false"]:hover {{
        background-color: {tab_hover_bg} !important;
        color: {tab_hover_color} !important;
    }}
    </style>
    """, unsafe_allow_html=True)
    
    # Back to home button
    if st.button("← Back to Home", key="back_home"):
        st.switch_page("app.py")
    
    # Main authentication container
    st.markdown('<div class="auth-container">', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="auth-header">
        <h1>🔐 PharmGPT</h1>
        <p>Sign in to access your AI pharmacology assistant</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create tabs for Sign In and Sign Up
    tab1, tab2 = st.tabs(["🔐 Sign In", "📝 Sign Up"])
    
    with tab1:
        render_signin_form()
    
    with tab2:
        render_signup_form()
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_signin_form():
    """Render the sign in form."""
    st.markdown("### Welcome Back!")
    st.markdown("Sign in to continue your pharmacology learning journey.")
    
    with st.form("signin_form"):
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            submit_button = st.form_submit_button("🔐 Sign In", use_container_width=True, type="primary")
        
        if submit_button:
            if not username or not password:
                st.error("❌ Please enter both username and password")
            else:
                success, message = authenticate_user(username, password)
                if success:
                    # Set session state
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.user_id = get_user_legacy_id(username)
                    st.success("✅ Successfully signed in!")
                    st.balloons()
                    st.switch_page("pages/3_💬_Chatbot.py")
                else:
                    st.error(f"❌ {message}")
    
    # Demo credentials info
    with st.expander("🧪 Demo Credentials"):
        st.info("""
        **For testing purposes, you can use:**
        - Username: `admin` / Password: `admin123`
        - Username: `demo` / Password: `demo123`
        
        Or create your own account using the Sign Up tab.
        """)

def render_signup_form():
    """Render the sign up form."""
    st.markdown("### Create Your Account")
    st.markdown("Join PharmGPT to start your personalized learning experience.")
    
    with st.form("signup_form"):
        username = st.text_input("Username", placeholder="Choose a username")
        password = st.text_input("Password", type="password", placeholder="Create a password")
        confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            submit_button = st.form_submit_button("📝 Create Account", use_container_width=True, type="primary")
        
        if submit_button:
            if not username or not password or not confirm_password:
                st.error("❌ Please fill in all fields")
            elif password != confirm_password:
                st.error("❌ Passwords do not match")
            elif len(password) < 6:
                st.error("❌ Password must be at least 6 characters long")
            else:
                success, message = create_user(username, password)
                if success:
                    # Set session state
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.user_id = get_user_legacy_id(username)
                    st.success("✅ Account created successfully!")
                    st.balloons()
                    st.switch_page("pages/3_💬_Chatbot.py")
                else:
                    st.error(f"❌ {message}")
    
    # Account requirements
    with st.expander("📋 Account Requirements"):
        st.info("""
        **Password Requirements:**
        - At least 6 characters long
        - Can contain letters, numbers, and special characters
        
        **Username Requirements:**
        - Must be unique
        - Can contain letters, numbers, and underscores
        - No spaces allowed
        """)

if __name__ == "__main__":
    main()