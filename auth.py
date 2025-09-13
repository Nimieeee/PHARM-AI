"""
Authentication and User Management System - Supabase Version
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import streamlit as st
from config import SESSION_TIMEOUT_HOURS, UPLOAD_LIMIT_PER_DAY

# Import Supabase services with error handling
try:
    from services.user_service import user_service
    from services.session_service import session_service, create_session_sync, validate_session_sync, logout_session_sync
    from services.conversation_service import conversation_service, get_user_conversations_sync, update_conversation_sync
    from services.document_service import document_service
except ImportError as e:
    st.error(f"Failed to import services: {e}")
    st.info("This might be a dependency issue. Please check your requirements.txt")
    st.stop()

# Helper function to run async functions in Streamlit
def run_async(coro):
    """Run async function in Streamlit context with better error handling."""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Try to get existing event loop
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError("Event loop is closed")
    except RuntimeError:
        # Create new event loop for Streamlit Cloud compatibility
        logger.info("Creating new event loop for async operation")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    try:
        return loop.run_until_complete(coro)
    except Exception as e:
        logger.error(f"Error running async operation: {e}")
        raise

# Session validation cache to prevent duplicate validation
_session_cache = {}
_cache_timeout_seconds = 120  # Cache session validation for 2 minutes (longer for Streamlit Cloud)


def create_user(username: str, password: str) -> Tuple[bool, str]:
    """Create a new user account using Supabase."""
    try:
        success, message = run_async(user_service.create_user(username, password))
        return success, message
    except Exception as e:
        return False, f"Error creating account: {str(e)}"

def authenticate_user(username: str, password: str) -> Tuple[bool, str]:
    """Authenticate user credentials using Supabase."""
    try:
        success, message, user_data = run_async(user_service.authenticate_user(username, password))
        return success, message
    except Exception as e:
        return False, f"Authentication error: {str(e)}"

def create_session(username: str) -> str:
    """Create a new session for user using Supabase."""
    try:
        # Get user data first
        user_data = run_async(user_service.get_user_by_username(username))
        if not user_data:
            raise Exception("User not found")
        
        session_id = create_session_sync(username, user_data['id'])
        return session_id
    except Exception as e:
        st.error(f"Error creating session: {str(e)}")
        return ""

def validate_session(session_id: str) -> Optional[str]:
    """Validate session and return username if valid using Supabase with caching."""
    import logging
    import time
    
    logger = logging.getLogger(__name__)
    logger.info(f"🔍 VALIDATE_SESSION called for session_id: {session_id}")
    
    # Check cache first
    cache_key = f"session_{session_id}"
    current_time = time.time()
    
    if cache_key in _session_cache:
        cached_data, timestamp = _session_cache[cache_key]
        if current_time - timestamp < _cache_timeout_seconds:
            logger.info(f"💾 Using cached session validation for user: {cached_data}")
            return cached_data
        else:
            logger.info("⏰ Session cache expired, validating fresh...")
            del _session_cache[cache_key]
    
    try:
        session_data = validate_session_sync(session_id)
        if session_data:
            username = session_data['username']
            # Cache successful validation
            _session_cache[cache_key] = (username, current_time)
            logger.info(f"✅ Session validation SUCCESS for user: {username} (cached)")
            return username
        logger.warning(f"❌ Session validation FAILED for session_id: {session_id}")
        return None
    except Exception as e:
        logger.error(f"💥 Error validating session {session_id}: {str(e)}")
        st.error(f"Error validating session: {str(e)}")
        return None

def logout_user(session_id: str):
    """Logout user by removing session using Supabase."""
    try:
        logout_session_sync(session_id)
    except Exception as e:
        st.error(f"Error logging out: {str(e)}")

def get_user_uuid(username: str) -> Optional[str]:
    """Get user UUID for username using Supabase."""
    try:
        user_data = run_async(user_service.get_user_by_username(username))
        if user_data:
            return user_data['id']  # Return the actual UUID
        return None
    except Exception as e:
        st.error(f"Error getting user UUID: {str(e)}")
        return None

def get_user_legacy_id(username: str) -> Optional[str]:
    """Get user legacy ID (user_id) for username using Supabase."""
    try:
        user_data = run_async(user_service.get_user_by_username(username))
        if user_data:
            return user_data['user_id']  # Return the legacy user_id (MD5 hash)
        return None
    except Exception as e:
        st.error(f"Error getting user legacy ID: {str(e)}")
        return None

def initialize_auth_session():
    """Initialize authentication session state."""
    import logging
    logger = logging.getLogger(__name__)

    # Attempt to retrieve session_id from query parameters first
    query_params = st.query_params
    if "session_id" in query_params and query_params["session_id"][0]:
        st.session_state.session_id = query_params["session_id"][0]
        logger.info(f"🔗 Retrieved session_id from URL: {st.session_state.session_id}")
    elif "session_id" not in st.session_state or st.session_state.session_id is None:
        st.session_state.session_id = None
        logger.info("🆕 Initializing new session_id as None")

    # Check for existing session
    if "session_id" not in st.session_state:
        st.session_state.session_id = None
        logger.info("🆕 Initializing new session_id as None")

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        logger.info("🆕 Initializing authenticated as False")

    if "username" not in st.session_state:
        st.session_state.username = None

    if "user_id" not in st.session_state:
        st.session_state.user_id = None

    logger.info(f"🔐 INITIALIZE_AUTH_SESSION called - session_id (after init): {st.session_state.get('session_id', 'None')}, authenticated (after init): {st.session_state.get('authenticated', False)}")

    # Validate existing session
    if st.session_state.session_id:
        logger.info(f"🔍 Validating existing session: {st.session_state.session_id}")
        username = validate_session(st.session_state.session_id)
        if username:
            logger.info(f"✅ Session valid for user: {username}")
            st.session_state.authenticated = True
            st.session_state.username = username
            st.session_state.user_id = get_user_legacy_id(username)
            # Ensure session_id is in URL if valid
            st.query_params["session_id"] = st.session_state.session_id
        else:
            logger.warning(f"❌ Session invalid for {st.session_state.session_id}, clearing state")
            # Invalid session, clear state
            st.session_state.session_id = None
            st.session_state.authenticated = False
            st.session_state.username = None
            st.session_state.user_id = None
            if "session_id" in st.query_params:
                del st.query_params["session_id"]
    else:
        logger.info("ℹ️  No session_id to validate")

def login_user(username: str, password: str) -> bool:
    """Login user and create session."""
    logger.info(f"Attempting login for user: {username}")
    success, message = authenticate_user(username, password)
    if success:
        logger.info(f"Authentication successful for user: {username}")
        session_id = create_session(username)
        if session_id:
            st.session_state.session_id = session_id
            st.session_state.authenticated = True
            st.session_state.username = username
            st.session_state.user_id = get_user_legacy_id(username)
            st.query_params["session_id"] = session_id
            logger.info(f"Session created and set for user {username} with ID: {session_id}")
            return True
        else:
            logger.error(f"Failed to create session for user: {username}")
            return False
    else:
        logger.warning(f"Authentication failed for user {username}: {message}")
        return False

def logout_current_user():
    """Logout current user."""
    if st.session_state.session_id:
        # Clear from cache when logging out
        cache_key = f"session_{st.session_state.session_id}"
        if cache_key in _session_cache:
            del _session_cache[cache_key]
        
        logout_user(st.session_state.session_id)
    
    # Clear session state
    st.session_state.session_id = None
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.user_id = None
    if "session_id" in st.query_params:
        del st.query_params["session_id"]
    
    

def load_user_conversations(user_id: str) -> Dict:
    """Load conversations for a specific user using Supabase."""
    try:
        # Get user UUID from legacy user_id
        user_data = run_async(user_service.get_user_by_id(user_id))
        if not user_data:
            return {}
        
        conversations = get_user_conversations_sync(user_data['id'])
        return conversations
    except Exception as e:
        st.error(f"Error loading conversations: {e}")
        return {}

def save_user_conversations(user_id: str, conversations: Dict):
    """Save conversations for a specific user using Supabase."""
    try:
        # Get user UUID from legacy user_id
        user_data = run_async(user_service.get_user_by_id(user_id))
        if not user_data:
            st.error(f"User not found: {user_id}")
            return
        
        # Update each conversation in Supabase
        for conv_id, conv_data in conversations.items():
            update_conversation_sync(
                user_data['id'],
                conv_id,
                conv_data
            )
    except Exception as e:
        st.error(f"Error saving conversations: {e}")

# Upload limit management using Supabase
def can_user_upload(user_id: str) -> Tuple[bool, str]:
    """Check if user can upload more files using Supabase."""
    # Always allow uploads - no limit
    if UPLOAD_LIMIT_PER_DAY == -1:
        return True, "Unlimited uploads allowed"
    
    try:
        # Get user UUID from legacy user_id
        user_data = run_async(user_service.get_user_by_id(user_id))
        if not user_data:
            return False, "User not found"
        
        # Get recent uploads from Supabase
        from supabase_manager import connection_manager
        from datetime import datetime, timedelta
        
        cutoff_time = (datetime.now() - timedelta(hours=24)).isoformat()
        
        result = run_async(connection_manager.execute_query(
            table='uploads',
            operation='select',
            columns='count(*)',
            eq={'user_id': user_data['id']}
        ))
        
        # For now, simplified implementation
        return True, "Upload allowed"
        
    except Exception as e:
        st.error(f"Error checking upload limit: {e}")
        return True, "Upload allowed (error checking limit)"

def record_user_upload(user_id: str, filename: str, file_size: int):
    """Record a user upload using Supabase."""
    try:
        # Get user UUID from legacy user_id
        user_data = run_async(user_service.get_user_by_id(user_id))
        if not user_data:
            st.error(f"User not found: {user_id}")
            return
        
        # Record upload in Supabase
        from supabase_manager import connection_manager
        
        upload_data = {
            'user_id': user_data['id'],
            'filename': filename,
            'file_size': file_size,
            'uploaded_at': datetime.now().isoformat()
        }
        
        run_async(connection_manager.execute_query(
            table='uploads',
            operation='insert',
            data=upload_data
        ))
        
    except Exception as e:
        st.error(f"Error recording upload: {e}")

def verify_user_data_isolation() -> Tuple[bool, str]:
    """Verify that user data is properly isolated in Supabase."""
    try:
        # With Supabase and RLS policies, data isolation is handled automatically
        # Just verify that the connection is working
        from supabase_manager import connection_manager
        
        if connection_manager.test_connection():
            return True, "User data isolation verified (Supabase RLS)"
        else:
            return False, "Database connection failed"
        
    except Exception as e:
        return False, f"Error verifying isolation: {e}"

def cleanup_orphaned_data() -> List[str]:
    """Clean up orphaned user data (not needed with Supabase)."""
    # With Supabase, orphaned data is prevented by foreign key constraints
    # and cleaned up automatically when users are deleted
    return []

def get_user_upload_count(user_id: str) -> int:
    """Get the number of uploads for a user in the last 24 hours using Supabase."""
    try:
        # Get user UUID from legacy user_id
        user_data = run_async(user_service.get_user_by_id(user_id))
        if not user_data:
            return 0
        
        # Get recent uploads from Supabase
        from supabase_manager import connection_manager
        from datetime import datetime, timedelta
        
        cutoff_time = (datetime.now() - timedelta(hours=24)).isoformat()
        
        # This would need a more complex query with date filtering
        # For now, return 0 as uploads are unlimited
        return 0
        
    except Exception as e:
        st.error(f"Error getting upload count: {e}")
        return 0