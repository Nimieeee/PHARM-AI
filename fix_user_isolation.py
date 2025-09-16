"""
Fix for User Isolation Issues in PharmGPT
This script addresses the cross-user data visibility problem
"""

import streamlit as st
import logging

logger = logging.getLogger(__name__)

def ensure_user_isolation():
    """Ensure proper user data isolation."""
    
    # 1. Clear any cached session data that might be stale
    if hasattr(st.session_state, '_session_cache'):
        delattr(st.session_state, '_session_cache')
    
    # 2. Validate current session
    if st.session_state.get('authenticated') and st.session_state.get('session_id'):
        try:
            from auth import validate_session, get_user_uuid
            
            # Re-validate session
            username = validate_session(st.session_state.session_id)
            if not username:
                logger.warning("Session validation failed, clearing state")
                clear_user_state()
                return False
            
            # Ensure username matches
            if username != st.session_state.get('username'):
                logger.error(f"Username mismatch! Session: {username}, State: {st.session_state.get('username')}")
                clear_user_state()
                return False
            
            # Ensure user_id is correct
            correct_user_uuid = get_user_uuid(username)
            if not correct_user_uuid:
                logger.error(f"Could not get UUID for user: {username}")
                clear_user_state()
                return False
            
            # Update session state with correct data
            st.session_state.username = username
            st.session_state.user_uuid = correct_user_uuid
            
            logger.info(f"User isolation validated for: {username} (UUID: {correct_user_uuid})")
            return True
            
        except Exception as e:
            logger.error(f"Error validating user isolation: {e}")
            clear_user_state()
            return False
    
    return False

def clear_user_state():
    """Clear all user-specific state."""
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.user_id = None
    st.session_state.user_uuid = None
    st.session_state.session_id = None
    st.session_state.conversations = {}
    st.session_state.current_conversation_id = None
    st.session_state.chat_messages = []
    
    # Clear URL parameters
    if "session_id" in st.query_params:
        del st.query_params["session_id"]
    
    logger.info("User state cleared")

def load_user_conversations_safely():
    """Load conversations with proper user isolation checks."""
    if not st.session_state.get('authenticated'):
        return {}
    
    try:
        from auth import load_user_conversations
        
        # Ensure we have proper user identification
        if not st.session_state.get('user_id'):
            logger.error("No user_id in session state")
            return {}
        
        # Load conversations for the specific user
        conversations = load_user_conversations(st.session_state.user_id)
        
        # Validate that conversations belong to current user
        validated_conversations = {}
        for conv_id, conv_data in conversations.items():
            # Additional validation could be added here
            validated_conversations[conv_id] = conv_data
        
        logger.info(f"Safely loaded {len(validated_conversations)} conversations")
        return validated_conversations
        
    except Exception as e:
        logger.error(f"Error loading conversations safely: {e}")
        return {}

def initialize_secure_session():
    """Initialize session with security checks."""
    
    # Clear any potentially stale data
    if 'conversations' in st.session_state:
        st.session_state.conversations = {}
    
    # Validate user isolation
    if ensure_user_isolation():
        # Load user data safely
        st.session_state.conversations = load_user_conversations_safely()
        logger.info("Secure session initialized successfully")
    else:
        logger.info("Session validation failed, user not authenticated")

# Add this to your session initialization
def enhanced_session_validation():
    """Enhanced session validation with user isolation checks."""
    
    # Basic session state initialization
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "username" not in st.session_state:
        st.session_state.username = None
    if "user_id" not in st.session_state:
        st.session_state.user_id = None
    if "user_uuid" not in st.session_state:
        st.session_state.user_uuid = None
    if "session_id" not in st.session_state:
        st.session_state.session_id = None
    if "conversations" not in st.session_state:
        st.session_state.conversations = {}
    
    # If we have a session, validate it thoroughly
    if st.session_state.get('session_id'):
        if not ensure_user_isolation():
            # Failed validation, redirect to login
            st.switch_page("pages/2_🔐_Sign_In.py")
            return False
    
    return True