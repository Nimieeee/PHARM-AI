"""
Clean Session State Management for PharmGPT
Simple, reliable session initialization
"""

import streamlit as st
import logging
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

def initialize_session_state():
    """Initialize session state variables with optimized security checks."""
    # Check if already initialized to avoid redundant work
    if st.session_state.get('_session_initialized'):
        # Just extend session activity
        extend_session()
        return
    
    logger.info("Initializing session state with security checks")
    
    # Import the enhanced validation
    try:
        from fix_user_isolation import enhanced_session_validation, initialize_secure_session
        
        # Run enhanced validation (but cache the result)
        if enhanced_session_validation():
            # Initialize secure session if validation passed
            initialize_secure_session()
            st.session_state._session_initialized = True
        else:
            logger.warning("Enhanced session validation failed")
            # Still mark as initialized to avoid loops
            st.session_state._session_initialized = True
            return
            
    except ImportError:
        logger.warning("Enhanced validation not available, using basic initialization")
        st.session_state._session_initialized = True
        # Fallback to basic initialization
        basic_session_initialization()
    
    # Initialize other session variables
    if "theme_mode" not in st.session_state:
        st.session_state.theme_mode = "light"
    
    if "current_page" not in st.session_state:
        if st.session_state.authenticated:
            st.session_state.current_page = "chatbot"
        else:
            st.session_state.current_page = "homepage"
    
    if "current_conversation_id" not in st.session_state:
        st.session_state.current_conversation_id = None
    
    if "conversation_counter" not in st.session_state:
        st.session_state.conversation_counter = 0

def basic_session_initialization():
    """Basic session initialization without enhanced security."""
    # Initialize conversations to an empty dict if not present
    if "conversations" not in st.session_state:
        st.session_state.conversations = {}
    
    # Initialize authentication state
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if "username" not in st.session_state:
        st.session_state.username = None
    
    if "user_id" not in st.session_state:
        st.session_state.user_id = None
    
    if "session_id" not in st.session_state:
        st.session_state.session_id = None
    
    # Try to restore session from browser storage if available
    if not st.session_state.authenticated and st.session_state.session_id:
        try:
            restore_session_from_storage()
        except Exception as e:
            logger.warning(f"Session restoration failed: {e}")
    
    # Validate existing session on page load
    if st.session_state.authenticated and st.session_state.user_id:
        try:
            if not validate_existing_session():
                # Clear invalid session
                clear_session_state()
        except Exception as e:
            logger.warning(f"Session validation failed: {e}")
            # Don't clear session immediately, let user continue
    
    # Initialize theme
    if "theme_mode" not in st.session_state:
        st.session_state.theme_mode = "light"
    
    # Page navigation
    if "current_page" not in st.session_state:
        if st.session_state.authenticated:
            st.session_state.current_page = "chatbot"
        else:
            st.session_state.current_page = "homepage"
    
    # Initialize conversation-related state
    if "current_conversation_id" not in st.session_state:
        st.session_state.current_conversation_id = None
    
    if "conversation_counter" not in st.session_state:
        st.session_state.conversation_counter = 0

def validate_existing_session():
    """Validate that the current session is still valid."""
    try:
        if not st.session_state.get('user_id'):
            return False
        
        # Import here to avoid circular imports
        from services.user_service import user_service
        import asyncio
        
        # Check if user still exists
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        user_data = loop.run_until_complete(user_service.get_user_by_id(st.session_state.user_id))
        
        if user_data:
            logger.info(f"Session validated for user: {st.session_state.username}")
            return True
        else:
            logger.warning(f"User not found during session validation: {st.session_state.user_id}")
            return False
            
    except Exception as e:
        logger.error(f"Session validation error: {e}")
        return False

def extend_session():
    """Extend the current session timeout."""
    if st.session_state.get('authenticated'):
        st.session_state.session_last_activity = datetime.now()
        logger.debug("Session activity updated")
    
    if "search_query" not in st.session_state:
        st.session_state.search_query = ""
    
    # Initialize auth if we have session info
    if st.session_state.authenticated and st.session_state.user_id:
        try:
            load_user_conversations()
        except Exception as e:
            logger.error(f"Error loading user conversations: {e}")

def restore_session_from_storage():
    """Try to restore session from stored session ID."""
    try:
        if st.session_state.session_id:
            from auth import validate_session
            username = validate_session(st.session_state.session_id)
            if username:
                st.session_state.authenticated = True
                st.session_state.username = username
                # Get user_id from username
                from services.user_service import user_service
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                user_data = loop.run_until_complete(user_service.get_user_by_username(username))
                if user_data:
                    st.session_state.user_id = user_data['legacy_id']
                    logger.info(f"Session restored for user: {username}")
                    return True
    except Exception as e:
        logger.error(f"Session restoration error: {e}")
    return False

def clear_session_state():
    """Clear all session state variables."""
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.user_id = None
    st.session_state.session_id = None
    st.session_state.conversations = {}
    st.session_state.current_conversation_id = None
    st.session_state.chat_messages = []
    logger.info("Session state cleared")

def load_user_conversations():
    """Load user conversations from database with proper user isolation."""
    if not st.session_state.authenticated or not st.session_state.user_id:
        return
    
    try:
        # Use the secure loading function
        from fix_user_isolation import load_user_conversations_safely, secure_update_conversations
        
        # Load conversations safely
        conversations = load_user_conversations_safely()
        if secure_update_conversations(conversations):
            st.session_state.conversation_counter = len(conversations)
            logger.info(f"Loaded {len(conversations)} conversations for user: {st.session_state.username}")
        else:
            logger.error("Failed to securely update conversations in session manager")
    except Exception as e:
        logger.error(f"Failed to load conversations: {e}")
        # Don't clear existing conversations on error