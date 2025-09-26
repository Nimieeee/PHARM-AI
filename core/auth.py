"""
Persistent Authentication System for PharmGPT
Handles login, logout, session persistence, and user state management
"""

import logging
import asyncio
from typing import Optional, Dict, Tuple
from datetime import datetime
import streamlit as st

from core.supabase_client import supabase_manager

# Configure logging
logger = logging.getLogger(__name__)

# Session state keys
SESSION_KEYS = {
    'authenticated': 'pharmgpt_authenticated',
    'user_id': 'pharmgpt_user_id',
    'username': 'pharmgpt_username',
    'display_name': 'pharmgpt_display_name',
    'session_token': 'pharmgpt_session_token',
    'login_time': 'pharmgpt_login_time',
    'last_activity': 'pharmgpt_last_activity'
}


def run_async(coro):
    """Helper to run async functions in Streamlit."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    try:
        return loop.run_until_complete(coro)
    except Exception as e:
        logger.error(f"Error running async operation: {e}")
        raise


class AuthenticationManager:
    """Manages authentication state and session persistence."""
    
    def __init__(self):
        self.session_timeout_hours = 24 * 30  # 30 days
        self._init_session_state()
    
    def _init_session_state(self):
        """Initialize session state with default values."""
        for key, session_key in SESSION_KEYS.items():
            if session_key not in st.session_state:
                if key == 'authenticated':
                    st.session_state[session_key] = False
                else:
                    st.session_state[session_key] = None
    
    def is_authenticated(self) -> bool:
        """Check if user is currently authenticated."""
        return st.session_state.get(SESSION_KEYS['authenticated'], False)
    
    def get_current_user(self) -> Optional[Dict[str, str]]:
        """Get current user information."""
        if not self.is_authenticated():
            return None
        
        return {
            'user_id': st.session_state.get(SESSION_KEYS['user_id']),
            'username': st.session_state.get(SESSION_KEYS['username']),
            'display_name': st.session_state.get(SESSION_KEYS['display_name'])
        }
    
    def get_session_token(self) -> Optional[str]:
        """Get current session token."""
        return st.session_state.get(SESSION_KEYS['session_token'])
    
    async def create_account(self, username: str, password: str, 
                           email: str = None) -> Tuple[bool, str]:
        """Create a new user account."""
        try:
            success, message, user_data = await supabase_manager.create_user(
                username, password, email
            )
            
            if success and user_data:
                logger.info(f"Account created successfully for user: {username}")
                return True, "Account created successfully! Please sign in."
            else:
                logger.warning(f"Account creation failed: {message}")
                return False, message
                
        except Exception as e:
            logger.error(f"Error creating account: {e}")
            return False, f"Error creating account: {str(e)}"
    
    async def sign_in(self, username: str, password: str) -> Tuple[bool, str]:
        """Authenticate user and create persistent session."""
        try:
            # Authenticate user
            success, message, user_data = await supabase_manager.authenticate_user(
                username, password
            )
            
            if not success or not user_data:
                logger.warning(f"Authentication failed for {username}: {message}")
                return False, message
            
            # Create persistent session
            session_data = await supabase_manager.create_session(
                user_id=user_data['user_id'],
                device_info={
                    'user_agent': st.runtime.request.headers.get('User-Agent', 'Unknown'),
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            if not session_data:
                logger.error("Failed to create session")
                return False, "Failed to create session"
            
            # Update session state
            self._update_session_state(user_data, session_data['session_token'])
            
            logger.info(f"User {username} signed in successfully")
            return True, "Signed in successfully!"
            
        except Exception as e:
            logger.error(f"Sign-in error: {e}")
            return False, f"Sign-in error: {str(e)}"
    
    async def validate_session(self) -> bool:
        """Validate current session and refresh user state."""
        try:
            session_token = self.get_session_token()
            if not session_token:
                return False
            
            user_data = await supabase_manager.validate_session(session_token)
            
            if user_data:
                # Update last activity
                st.session_state[SESSION_KEYS['last_activity']] = datetime.now()
                
                # Refresh user data in session
                st.session_state[SESSION_KEYS['user_id']] = user_data['user_id']
                st.session_state[SESSION_KEYS['username']] = user_data['username']
                st.session_state[SESSION_KEYS['display_name']] = user_data['display_name']
                
                return True
            else:
                # Session invalid, clear state
                self.sign_out()
                return False
                
        except Exception as e:
            logger.error(f"Session validation error: {e}")
            self.sign_out()
            return False
    
    def _update_session_state(self, user_data: Dict, session_token: str):
        """Update session state with user data."""
        now = datetime.now()
        
        st.session_state[SESSION_KEYS['authenticated']] = True
        st.session_state[SESSION_KEYS['user_id']] = user_data['user_id']
        st.session_state[SESSION_KEYS['username']] = user_data['username']
        st.session_state[SESSION_KEYS['display_name']] = user_data.get('display_name', user_data['username'])
        st.session_state[SESSION_KEYS['session_token']] = session_token
        st.session_state[SESSION_KEYS['login_time']] = now
        st.session_state[SESSION_KEYS['last_activity']] = now
    
    def sign_out(self):
        """Sign out user and clear session state."""
        username = st.session_state.get(SESSION_KEYS['username'], 'Unknown')
        
        # Clear all session state
        for session_key in SESSION_KEYS.values():
            if session_key in st.session_state:
                del st.session_state[session_key]
        
        # Reset authentication state
        st.session_state[SESSION_KEYS['authenticated']] = False
        
        logger.info(f"User {username} signed out")
    
    async def check_and_refresh_session(self) -> bool:
        """Check session validity and refresh if needed."""
        if not self.is_authenticated():
            return False
        
        # Check last activity
        last_activity = st.session_state.get(SESSION_KEYS['last_activity'])
        if last_activity:
            hours_since_activity = (datetime.now() - last_activity).total_seconds() / 3600
            if hours_since_activity > self.session_timeout_hours:
                logger.info("Session expired due to inactivity")
                self.sign_out()
                return False
        
        # Validate session with server
        return await self.validate_session()


# Global authentication manager
auth_manager = AuthenticationManager()

# Convenience functions
def is_authenticated() -> bool:
    """Check if user is authenticated."""
    return auth_manager.is_authenticated()

def get_current_user() -> Optional[Dict[str, str]]:
    """Get current user information."""
    return auth_manager.get_current_user()

def get_current_user_id() -> Optional[str]:
    """Get current user ID."""
    user = get_current_user()
    return user['user_id'] if user else None

def create_account(username: str, password: str, email: str = None) -> Tuple[bool, str]:
    """Create a new account."""
    return run_async(auth_manager.create_account(username, password, email))

def sign_in(username: str, password: str) -> Tuple[bool, str]:
    """Sign in user."""
    return run_async(auth_manager.sign_in(username, password))

def sign_out():
    """Sign out current user."""
    auth_manager.sign_out()

def validate_session() -> bool:
    """Validate current session."""
    return run_async(auth_manager.validate_session())

def require_authentication():
    """Decorator/check to require authentication for a page."""
    if not is_authenticated():
        # Try to validate session first
        if not validate_session():
            st.error("🔒 Please sign in to access this page.")
            st.stop()

def initialize_auth_session():
    """Initialize authentication session on app start."""
    try:
        # Check and refresh session if user appears to be logged in
        if auth_manager.is_authenticated():
            run_async(auth_manager.check_and_refresh_session())
    except Exception as e:
        logger.error(f"Error initializing auth session: {e}")
        # Clear potentially corrupted session state
        auth_manager.sign_out()


# Authentication UI Components
def render_sign_in_form() -> bool:
    """Render sign-in form and handle authentication."""
    st.header("🔐 Sign In")
    
    with st.form("sign_in_form"):
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        
        col1, col2 = st.columns(2)
        
        with col1:
            sign_in_clicked = st.form_submit_button("Sign In", use_container_width=True)
        
        with col2:
            create_account_clicked = st.form_submit_button("Create Account", use_container_width=True)
        
        if sign_in_clicked:
            if username and password:
                with st.spinner("Signing in..."):
                    success, message = sign_in(username, password)
                    
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
            else:
                st.error("Please enter both username and password")
        
        elif create_account_clicked:
            if username and password:
                with st.spinner("Creating account..."):
                    email = st.session_state.get('signup_email', None)
                    success, message = create_account(username, password, email)
                    
                    if success:
                        st.success(message)
                        st.info("You can now sign in with your credentials.")
                    else:
                        st.error(message)
            else:
                st.error("Please enter both username and password")
    
    # Optional email field for account creation
    if st.checkbox("Add email (optional for account creation)"):
        st.session_state['signup_email'] = st.text_input(
            "Email", 
            placeholder="Enter your email (optional)"
        )
    
    return False

def render_user_info():
    """Render current user information and sign-out button."""
    user = get_current_user()
    if user:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.write(f"👤 **{user['display_name']}**")
        
        with col2:
            if st.button("Sign Out", key="sign_out_btn"):
                sign_out()
                st.rerun()