import streamlit as st
import hashlib
import json
import os
from pathlib import Path
from datetime import datetime
import uuid
import secrets

# User data directory
USER_DATA_DIR = Path("user_data")
USER_DATA_DIR.mkdir(exist_ok=True)

# Users file
USERS_FILE = USER_DATA_DIR / "users.json"

# Session timeout (in seconds) - 24 hours
SESSION_TIMEOUT = 24 * 60 * 60

def generate_salt() -> str:
    """Generate a random salt for password hashing."""
    return secrets.token_hex(32)

def hash_password(password: str, salt: str = None) -> tuple:
    """Hash a password using SHA-256 with salt."""
    if salt is None:
        salt = generate_salt()
    
    # Combine password and salt
    salted_password = password + salt
    password_hash = hashlib.sha256(salted_password.encode()).hexdigest()
    
    return password_hash, salt

def load_users() -> dict:
    """Load users from file."""
    if USERS_FILE.exists():
        try:
            with open(USERS_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    return {}

def save_users(users: dict):
    """Save users to file."""
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

def create_user(username: str, password: str, email: str = "") -> tuple:
    """Create a new user account. Returns (success, message)."""
    users = load_users()
    
    # Validate username
    if not username or len(username) < 3:
        return False, "Username must be at least 3 characters long."
    
    if username in users:
        return False, "Username already exists. Please choose a different username."
    
    # Validate password
    if len(password) < 6:
        return False, "Password must be at least 6 characters long."
    
    # Create user data
    user_id = str(uuid.uuid4())
    password_hash, salt = hash_password(password)
    
    users[username] = {
        "user_id": user_id,
        "password_hash": password_hash,
        "salt": salt,
        "email": email,
        "created_at": datetime.now().isoformat(),
        "last_login": None,
        "login_count": 0
    }
    
    save_users(users)
    
    # Create user's conversation directory
    user_conv_dir = USER_DATA_DIR / f"conversations_{user_id}"
    user_conv_dir.mkdir(exist_ok=True)
    
    return True, "Account created successfully!"

def authenticate_user(username: str, password: str) -> tuple:
    """Authenticate a user. Returns (success, message)."""
    users = load_users()
    
    if not username or not password:
        return False, "Please enter both username and password."
    
    if username not in users:
        return False, "Invalid username or password."
    
    user_data = users[username]
    salt = user_data.get("salt", "")
    stored_hash = user_data["password_hash"]
    
    # Hash the provided password with the stored salt
    password_hash, _ = hash_password(password, salt)
    
    if password_hash != stored_hash:
        return False, "Invalid username or password."
    
    # Update last login and login count
    users[username]["last_login"] = datetime.now().isoformat()
    users[username]["login_count"] = users[username].get("login_count", 0) + 1
    save_users(users)
    
    return True, f"Welcome back, {username}!"

def get_user_id(username: str) -> str:
    """Get user ID for a username."""
    users = load_users()
    return users.get(username, {}).get("user_id", "")

def get_user_conversations_file(user_id: str) -> Path:
    """Get the conversations file path for a user."""
    return USER_DATA_DIR / f"conversations_{user_id}" / "conversations.json"

def load_user_conversations(user_id: str) -> dict:
    """Load conversations for a specific user."""
    conv_file = get_user_conversations_file(user_id)
    if conv_file.exists():
        try:
            with open(conv_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    return {}

def save_user_conversations(user_id: str, conversations: dict):
    """Save conversations for a specific user."""
    conv_file = get_user_conversations_file(user_id)
    conv_file.parent.mkdir(exist_ok=True)
    
    # Convert datetime objects to strings for JSON serialization
    serializable_conversations = {}
    for conv_id, conv_data in conversations.items():
        serializable_conv = conv_data.copy()
        if 'created_at' in serializable_conv and hasattr(serializable_conv['created_at'], 'isoformat'):
            serializable_conv['created_at'] = serializable_conv['created_at'].isoformat()
        
        # Handle messages with timestamps
        if 'messages' in serializable_conv:
            for message in serializable_conv['messages']:
                if 'timestamp' in message and hasattr(message['timestamp'], 'isoformat'):
                    message['timestamp'] = message['timestamp'].isoformat()
        
        serializable_conversations[conv_id] = serializable_conv
    
    with open(conv_file, 'w') as f:
        json.dump(serializable_conversations, f, indent=2)

def initialize_auth_session():
    """Initialize authentication session state."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "username" not in st.session_state:
        st.session_state.username = ""
    if "user_id" not in st.session_state:
        st.session_state.user_id = ""

def login_user(username: str):
    """Log in a user."""
    st.session_state.authenticated = True
    st.session_state.username = username
    st.session_state.user_id = get_user_id(username)

def logout_user():
    """Log out the current user."""
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.session_state.user_id = ""
    # Clear conversation data
    if "conversations" in st.session_state:
        del st.session_state.conversations
    if "current_conversation_id" in st.session_state:
        del st.session_state.current_conversation_id

def render_auth_page():
    """Render the authentication page."""
    # Custom CSS for auth page
    st.markdown("""
    <style>
        .auth-header {
            text-align: center;
            padding: 2rem 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 15px;
            color: white;
            margin-bottom: 2rem;
        }
        .auth-form {
            max-width: 400px;
            margin: 0 auto;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div class="auth-header">
        <h1>💊 PharmBot</h1>
        <h3>AI-Powered Pharmacology Assistant</h3>
        <p>Sign in to access your personal conversations</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create tabs for login and signup
    tab1, tab2 = st.tabs(["🔑 Sign In", "📝 Sign Up"])
    
    with tab1:
        st.markdown("#### Welcome back!")
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username", help="Your unique username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            remember_me = st.checkbox("Remember me", help="Stay signed in for 24 hours")
            login_button = st.form_submit_button("Sign In", use_container_width=True, type="primary")
            
            if login_button:
                success, message = authenticate_user(username, password)
                if success:
                    login_user(username)
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
    
    with tab2:
        st.markdown("#### Create your account")
        with st.form("signup_form"):
            new_username = st.text_input(
                "Choose Username", 
                placeholder="Enter a unique username (3+ characters)",
                help="Username must be at least 3 characters long"
            )
            new_email = st.text_input(
                "Email (optional)", 
                placeholder="your.email@example.com",
                help="Optional: for account recovery"
            )
            new_password = st.text_input(
                "Choose Password", 
                type="password", 
                placeholder="Enter a secure password (6+ characters)",
                help="Password must be at least 6 characters long"
            )
            confirm_password = st.text_input(
                "Confirm Password", 
                type="password", 
                placeholder="Confirm your password"
            )
            
            # Terms checkbox
            agree_terms = st.checkbox(
                "I agree that this is for educational purposes only and will consult healthcare professionals for medical advice",
                help="Required to create an account"
            )
            
            signup_button = st.form_submit_button("Create Account", use_container_width=True, type="primary")
            
            if signup_button:
                if not agree_terms:
                    st.error("Please agree to the terms to create an account.")
                elif new_password != confirm_password:
                    st.error("Passwords do not match.")
                else:
                    success, message = create_user(new_username, new_password, new_email)
                    if success:
                        st.success(message)
                        st.balloons()
                        st.info("You can now sign in with your new account!")
                    else:
                        st.error(message)
    
    # Features section
    st.markdown("---")
    st.markdown("### ✨ Why Create an Account?")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        **🔒 Private Conversations**
        
        Your chats are completely private and separated from other users.
        """)
    
    with col2:
        st.markdown("""
        **💾 Saved History**
        
        Access your conversation history anytime, anywhere.
        """)
    
    with col3:
        st.markdown("""
        **🎯 Personalized Experience**
        
        Tailored pharmacology assistance based on your interests.
        """)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.9rem;">
        <p>🔒 <strong>Privacy:</strong> Your data is stored locally and never shared</p>
        <p>⚠️ <strong>Disclaimer:</strong> Educational purposes only - Always consult healthcare professionals</p>
        <p>🛡️ <strong>Security:</strong> Passwords are hashed and salted for maximum security</p>
    </div>
    """, unsafe_allow_html=True)