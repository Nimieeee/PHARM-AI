"""
Sign In Page
"""

import streamlit as st
from auth import authenticate_user, create_user, get_user_uuid, get_user_legacy_id

def render_signin_page():
    """Render the sign in page."""
    st.markdown("# 💊 PharmGPT")
    st.markdown("### Sign In to Your Account")
    st.markdown("---")
    
    # Create tabs for Sign In and Sign Up
    tab1, tab2 = st.tabs(["🔐 Sign In", "📝 Sign Up"])
    
    with tab1:
        render_signin_form()
    
    with tab2:
        render_signup_form()

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
                    st.session_state.current_page = "chatbot"
                    st.success("✅ Successfully signed in!")
                    st.rerun()
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
                    st.session_state.current_page = "chatbot"
                    st.success("✅ Account created successfully!")
                    st.rerun()
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