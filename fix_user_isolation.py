"""
Fix for User Isolation Issues in PharmGPT
This script addresses the cross-user data visibility problem
"""

import streamlit as st
import logging

logger = logging.getLogger(__name__)

def ensure_user_isolation():
    """Ensure proper user data isolation - LESS AGGRESSIVE VERSION."""
    
    # 1. Clear any cached session data that might be stale
    if hasattr(st.session_state, '_session_cache'):
        delattr(st.session_state, '_session_cache')
    
    # 2. Validate current session WITHOUT clearing conversations
    if st.session_state.get('authenticated') and st.session_state.get('session_id'):
        try:
            from auth import validate_session
            
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
            
            # Basic validation passed
            logger.debug(f"User isolation validated for: {username}")
            return True
            
        except Exception as e:
            logger.error(f"Error validating user isolation: {e}")
            clear_user_state()
            return False
    
    # If not authenticated, that's okay for some operations
    return st.session_state.get('authenticated', False)

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
        from services.conversation_service import conversation_service
        from services.user_service import user_service
        import asyncio
        
        # Get user data - try multiple methods
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        user_data = None
        user_id = st.session_state.get('user_id')
        
        # Method 1: Try by user_id - could be legacy_id or UUID
        if user_id:
            # First try as legacy_id
            user_data = loop.run_until_complete(user_service.get_user_by_id(user_id))
            
            # If not found, try as UUID (for users like admin)
            if not user_data:
                try:
                    user_data = loop.run_until_complete(user_service.get_user_by_uuid(user_id))
                    logger.info(f"Found user by UUID: {user_id}")
                except Exception:
                    pass
        
        # Method 2: Try by username if user_id lookup failed
        if not user_data and st.session_state.get('username'):
            logger.info(f"Trying to find user by username: {st.session_state.username}")
            user_data = loop.run_until_complete(user_service.get_user_by_username(st.session_state.username))
        
        # Method 3: Try by UUID if available
        if not user_data and st.session_state.get('user_uuid'):
            user_data = loop.run_until_complete(user_service.get_user_by_uuid(st.session_state.user_uuid))
        
        if not user_data:
            logger.error(f"User not found with any method. user_id: {st.session_state.get('user_id')}, username: {st.session_state.get('username')}")
            return {}
        
        logger.info(f"Found user: {user_data.get('username')} (UUID: {user_data['id']})")
        
        # Load conversations using the secure service with user UUID
        conversations = loop.run_until_complete(conversation_service.get_user_conversations(user_data['id']))
        
        # Additional validation - ensure all conversations belong to this user
        validated_conversations = {}
        for conv_id, conv_data in conversations.items():
            # Only include conversations that have proper structure
            if isinstance(conv_data, dict) and 'messages' in conv_data:
                validated_conversations[conv_id] = conv_data
        
        logger.info(f"Safely loaded {len(validated_conversations)} conversations for user: {st.session_state.username}")
        return validated_conversations
        
    except Exception as e:
        logger.error(f"Error loading conversations safely: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {}

def initialize_secure_session():
    """Initialize session with security checks."""
    
    # Clear ALL potentially stale data to prevent cross-user contamination
    clear_all_user_data()
    
    # Validate user isolation
    if ensure_user_isolation():
        # Load user data safely
        st.session_state.conversations = load_user_conversations_safely()
        logger.info("Secure session initialized successfully")
    else:
        logger.info("Session validation failed, user not authenticated")

def clear_all_user_data():
    """Clear all user-specific data to prevent cross-contamination."""
    # Clear conversations and related data
    st.session_state.conversations = {}
    st.session_state.current_conversation_id = None
    st.session_state.chat_messages = []
    
    # Clear document data
    if 'conversation_documents' in st.session_state:
        st.session_state.conversation_documents = {}
    
    # Clear any cached data
    keys_to_remove = []
    for key in st.session_state.keys():
        if any(cache_key in key for cache_key in ['conversations_loaded_', 'isolation_validated_', 'processed_doc_', 'processing_doc_']):
            keys_to_remove.append(key)
    
    for key in keys_to_remove:
        del st.session_state[key]
    
    logger.info("All user data cleared for secure session initialization")

def get_secure_conversations():
    """Get conversations with user validation - use this instead of direct session state access."""
    if not st.session_state.get('authenticated') or not st.session_state.get('user_id'):
        logger.warning("Attempted to access conversations without authentication")
        return {}
    
    # Basic validation without clearing data
    if not st.session_state.get('username') or not st.session_state.get('session_id'):
        logger.warning("Missing username or session_id")
        return {}
    
    # Return conversations only if they belong to the current user
    conversations = st.session_state.get('conversations', {})
    
    # Additional validation: check if conversations are empty and reload if needed
    if not conversations and st.session_state.get('authenticated'):
        logger.info("No conversations in session state, reloading...")
        conversations = load_user_conversations_safely()
        if conversations:
            st.session_state.conversations = conversations
    
    return conversations

def get_secure_current_conversation():
    """Get current conversation with user validation."""
    conversations = get_secure_conversations()
    current_id = st.session_state.get('current_conversation_id')
    
    if current_id and current_id in conversations:
        return conversations[current_id]
    
    return None

def secure_update_conversations(new_conversations):
    """Securely update conversations after user validation."""
    if not st.session_state.get('authenticated') or not st.session_state.get('user_id'):
        logger.error("Attempted to update conversations without authentication")
        return False
    
    # Basic validation without aggressive clearing
    if not st.session_state.get('username') or not st.session_state.get('session_id'):
        logger.error("Missing username or session_id during conversation update")
        return False
    
    st.session_state.conversations = new_conversations
    logger.info(f"Updated conversations for user: {st.session_state.username}")
    return True

def secure_update_conversation(conv_id, updates):
    """Securely update a specific conversation."""
    conversations = get_secure_conversations()
    
    if conv_id in conversations:
        conversations[conv_id].update(updates)
        return secure_update_conversations(conversations)
    
    return False

def secure_delete_conversation(conv_id):
    """Securely delete a conversation."""
    conversations = get_secure_conversations()
    
    if conv_id in conversations:
        del conversations[conv_id]
        return secure_update_conversations(conversations)
    
    return False

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