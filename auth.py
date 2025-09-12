"""
Authentication and User Management System
"""

import json
import os
import hashlib
import secrets
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import streamlit as st
from config import USER_DATA_DIR, SESSION_TIMEOUT_HOURS, UPLOAD_LIMIT_PER_DAY

# File paths
USERS_FILE = os.path.join(USER_DATA_DIR, "users.json")
SESSIONS_FILE = os.path.join(USER_DATA_DIR, "sessions.json")
UPLOADS_FILE = os.path.join(USER_DATA_DIR, "uploads.json")

def ensure_user_data_dir():
    """Ensure user data directory exists."""
    os.makedirs(USER_DATA_DIR, exist_ok=True)

def hash_password(password: str, salt: str = None) -> Tuple[str, str]:
    """Hash password with salt."""
    if salt is None:
        salt = secrets.token_hex(32)
    
    password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return password_hash, salt

def load_users() -> Dict:
    """Load users from file."""
    ensure_user_data_dir()
    try:
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        st.error(f"Error loading users: {e}")
    return {}

def save_users(users: Dict):
    """Save users to file."""
    ensure_user_data_dir()
    try:
        with open(USERS_FILE, 'w') as f:
            json.dump(users, f, indent=2)
    except Exception as e:
        st.error(f"Error saving users: {e}")

def load_sessions() -> Dict:
    """Load sessions from file."""
    ensure_user_data_dir()
    try:
        if os.path.exists(SESSIONS_FILE):
            with open(SESSIONS_FILE, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def save_sessions(sessions: Dict):
    """Save sessions to file."""
    ensure_user_data_dir()
    try:
        with open(SESSIONS_FILE, 'w') as f:
            json.dump(sessions, f, indent=2)
    except Exception as e:
        st.error(f"Error saving sessions: {e}")

def create_user(username: str, password: str) -> tuple[bool, str]:
    """Create a new user account."""
    users = load_users()
    
    if username in users:
        return False, "Username already exists"
    
    try:
        password_hash, salt = hash_password(password)
        
        users[username] = {
            "password_hash": password_hash,
            "salt": salt,
            "created_at": datetime.now().isoformat(),
            "user_id": hashlib.md5(username.encode()).hexdigest()
        }
        
        save_users(users)
        
        # Create user-specific directories
        user_id = users[username]["user_id"]
        user_conv_dir = os.path.join(USER_DATA_DIR, f"conversations_{user_id}")
        user_rag_dir = os.path.join(USER_DATA_DIR, f"rag_{user_id}")
        os.makedirs(user_conv_dir, exist_ok=True)
        os.makedirs(user_rag_dir, exist_ok=True)
        
        return True, "Account created successfully"
    except Exception as e:
        return False, f"Error creating account: {str(e)}"

def authenticate_user(username: str, password: str) -> tuple[bool, str]:
    """Authenticate user credentials."""
    users = load_users()
    
    if username not in users:
        return False, "Username not found"
    
    user_data = users[username]
    password_hash, _ = hash_password(password, user_data["salt"])
    
    if password_hash == user_data["password_hash"]:
        return True, "Authentication successful"
    else:
        return False, "Invalid password"

def create_session(username: str) -> str:
    """Create a new session for user."""
    sessions = load_sessions()
    session_id = secrets.token_urlsafe(32)
    
    sessions[session_id] = {
        "username": username,
        "created_at": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(hours=SESSION_TIMEOUT_HOURS)).isoformat()
    }
    
    save_sessions(sessions)
    return session_id

def validate_session(session_id: str) -> Optional[str]:
    """Validate session and return username if valid."""
    if not session_id:
        return None
    
    sessions = load_sessions()
    
    if session_id not in sessions:
        return None
    
    session_data = sessions[session_id]
    expires_at = datetime.fromisoformat(session_data["expires_at"])
    
    if datetime.now() > expires_at:
        # Session expired, remove it
        del sessions[session_id]
        save_sessions(sessions)
        return None
    
    return session_data["username"]

def logout_user(session_id: str):
    """Logout user by removing session."""
    if not session_id:
        return
    
    sessions = load_sessions()
    if session_id in sessions:
        del sessions[session_id]
        save_sessions(sessions)

def get_user_id(username: str) -> Optional[str]:
    """Get user ID for username."""
    users = load_users()
    if username in users:
        return users[username]["user_id"]
    return None

def initialize_auth_session():
    """Initialize authentication session state."""
    # Check for existing session
    if "session_id" not in st.session_state:
        st.session_state.session_id = None
    
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if "username" not in st.session_state:
        st.session_state.username = None
    
    if "user_id" not in st.session_state:
        st.session_state.user_id = None
    
    # Validate existing session
    if st.session_state.session_id:
        username = validate_session(st.session_state.session_id)
        if username:
            st.session_state.authenticated = True
            st.session_state.username = username
            st.session_state.user_id = get_user_id(username)
        else:
            # Invalid session, clear state
            st.session_state.session_id = None
            st.session_state.authenticated = False
            st.session_state.username = None
            st.session_state.user_id = None

def login_user(username: str, password: str) -> bool:
    """Login user and create session."""
    if authenticate_user(username, password):
        session_id = create_session(username)
        st.session_state.session_id = session_id
        st.session_state.authenticated = True
        st.session_state.username = username
        st.session_state.user_id = get_user_id(username)
        return True
    return False

def logout_current_user():
    """Logout current user."""
    if st.session_state.session_id:
        logout_user(st.session_state.session_id)
    
    # Clear session state
    st.session_state.session_id = None
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.user_id = None
    
    # Clear conversation state
    keys_to_clear = [k for k in st.session_state.keys() if 'conversation' in k.lower()]
    for key in keys_to_clear:
        del st.session_state[key]

def load_user_conversations(user_id: str) -> Dict:
    """Load conversations for a specific user."""
    conv_file = os.path.join(USER_DATA_DIR, f"conversations_{user_id}", "conversations.json")
    try:
        if os.path.exists(conv_file):
            with open(conv_file, 'r') as f:
                content = f.read().strip()
                if not content:
                    # Empty file, return empty dict
                    return {}
                return json.loads(content)
    except json.JSONDecodeError as e:
        st.warning(f"Corrupted conversation file for user {user_id}. Creating backup and starting fresh.")
        # Backup corrupted file
        if os.path.exists(conv_file):
            backup_file = f"{conv_file}.backup_{int(time.time())}"
            try:
                import shutil
                shutil.copy2(conv_file, backup_file)
                os.remove(conv_file)  # Remove corrupted file
            except Exception:
                pass
    except Exception as e:
        st.error(f"Error loading conversations: {e}")
    return {}

def save_user_conversations(user_id: str, conversations: Dict):
    """Save conversations for a specific user."""
    conv_dir = os.path.join(USER_DATA_DIR, f"conversations_{user_id}")
    os.makedirs(conv_dir, exist_ok=True)
    conv_file = os.path.join(conv_dir, "conversations.json")
    try:
        with open(conv_file, 'w') as f:
            json.dump(conversations, f, indent=2)
    except Exception as e:
        st.error(f"Error saving conversations: {e}")

# Upload limit management
def load_uploads() -> Dict:
    """Load upload tracking data."""
    ensure_user_data_dir()
    try:
        if os.path.exists(UPLOADS_FILE):
            with open(UPLOADS_FILE, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def save_uploads(uploads: Dict):
    """Save upload tracking data."""
    ensure_user_data_dir()
    try:
        with open(UPLOADS_FILE, 'w') as f:
            json.dump(uploads, f, indent=2)
    except Exception as e:
        st.error(f"Error saving uploads: {e}")

def can_user_upload(user_id: str) -> Tuple[bool, str]:
    """Check if user can upload more files."""
    # Always allow uploads - no limit
    if UPLOAD_LIMIT_PER_DAY == -1:
        return True, "Unlimited uploads allowed"
    
    # Legacy code for if limits are re-enabled
    uploads = load_uploads()
    
    if user_id not in uploads:
        return True, "Upload allowed"
    
    user_uploads = uploads[user_id]
    now = datetime.now()
    
    # Count uploads in last 24 hours
    recent_uploads = 0
    for upload in user_uploads:
        upload_time = datetime.fromisoformat(upload["timestamp"])
        if now - upload_time < timedelta(hours=24):
            recent_uploads += 1
    
    if recent_uploads >= UPLOAD_LIMIT_PER_DAY:
        return False, f"Upload limit reached ({UPLOAD_LIMIT_PER_DAY} files per 24 hours)"
    
    return True, f"Upload allowed ({recent_uploads}/{UPLOAD_LIMIT_PER_DAY} used)"

def record_user_upload(user_id: str, filename: str, file_size: int):
    """Record a user upload."""
    uploads = load_uploads()
    
    if user_id not in uploads:
        uploads[user_id] = []
    
    uploads[user_id].append({
        "filename": filename,
        "file_size": file_size,
        "timestamp": datetime.now().isoformat()
    })
    
    save_uploads(uploads)

def verify_user_data_isolation() -> Tuple[bool, str]:
    """Verify that user data is properly isolated."""
    try:
        users = load_users()
        user_dirs = []
        
        # Check for user-specific directories
        if os.path.exists(USER_DATA_DIR):
            for item in os.listdir(USER_DATA_DIR):
                if item.startswith("conversations_") or item.startswith("rag_"):
                    user_dirs.append(item)
        
        # Verify each directory belongs to a valid user
        valid_user_ids = set()
        for username, user_data in users.items():
            valid_user_ids.add(user_data["user_id"])
        
        orphaned_dirs = []
        for dir_name in user_dirs:
            if dir_name.startswith("conversations_"):
                user_id = dir_name.replace("conversations_", "")
            elif dir_name.startswith("rag_"):
                user_id = dir_name.replace("rag_", "")
            else:
                continue
            
            if user_id not in valid_user_ids:
                orphaned_dirs.append(dir_name)
        
        if orphaned_dirs:
            return False, f"Found orphaned directories: {orphaned_dirs}"
        
        return True, "User data isolation verified"
        
    except Exception as e:
        return False, f"Error verifying isolation: {e}"

def cleanup_orphaned_data() -> List[str]:
    """Clean up orphaned user data directories."""
    try:
        users = load_users()
        valid_user_ids = set()
        for username, user_data in users.items():
            valid_user_ids.add(user_data["user_id"])
        
        cleaned = []
        if os.path.exists(USER_DATA_DIR):
            for item in os.listdir(USER_DATA_DIR):
                if item.startswith("conversations_") or item.startswith("rag_"):
                    if item.startswith("conversations_"):
                        user_id = item.replace("conversations_", "")
                    elif item.startswith("rag_"):
                        user_id = item.replace("rag_", "")
                    else:
                        continue
                    
                    if user_id not in valid_user_ids:
                        import shutil
                        dir_path = os.path.join(USER_DATA_DIR, item)
                        shutil.rmtree(dir_path, ignore_errors=True)
                        cleaned.append(item)
        
        return cleaned
        
    except Exception as e:
        st.error(f"Error cleaning orphaned data: {e}")
        return []

def get_user_upload_count(user_id: str) -> int:
    """Get the number of uploads for a user in the last 24 hours."""
    # If unlimited uploads, return total uploads today for stats
    uploads = load_uploads()
    
    if user_id not in uploads:
        return 0
    
    user_uploads = uploads[user_id]
    now = datetime.now()
    
    # Count uploads in last 24 hours
    recent_uploads = 0
    for upload in user_uploads:
        try:
            upload_time = datetime.fromisoformat(upload["timestamp"])
            if now - upload_time < timedelta(hours=24):
                recent_uploads += 1
        except Exception:
            continue
    
    return recent_uploads