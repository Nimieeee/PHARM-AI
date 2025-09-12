"""
Session State Management - Supabase Version
"""

import streamlit as st
import asyncio

# Import with error handling for Streamlit Cloud
try:
    from auth import load_user_conversations
except ImportError as e:
    st.error(f"Failed to import auth module: {e}")
    st.stop()

# Helper function to run async functions in Streamlit
def run_async(coro):
    """Run async function in Streamlit context."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(coro)

def initialize_session_state():
    """Initialize session state variables with Supabase optimizations."""
    import logging
    import time
    
    logger = logging.getLogger(__name__)
    logger.info(f"🔄 INITIALIZE_SESSION_STATE called - authenticated: {st.session_state.get('authenticated', False)}, session_id: {st.session_state.get('session_id', 'None')}")
    
    # Smart caching - avoid repeated initialization within same session
    cache_key = "last_auth_init_time"
    init_marker = "auth_initialized_this_run"
    current_time = time.time()
    
    # Check if we've already initialized auth in this very session run
    if init_marker in st.session_state:
        logger.info("💾 Skipping auth initialization (already done this run)")
        return
    
    # Only re-initialize auth if it's been more than 10 seconds or not initialized
    if (cache_key not in st.session_state or
        current_time - st.session_state.get(cache_key, 0) > 10.0):
        
        logger.info("🆕 Running auth initialization (cache miss or timeout)")
        from auth import initialize_auth_session
        initialize_auth_session()
        st.session_state[cache_key] = current_time
        st.session_state[init_marker] = True
    else:
        logger.info("💾 Skipping auth initialization (cached)")
    
    # Initialize theme
    if "theme_mode" not in st.session_state:
        st.session_state.theme_mode = "light"  # Default to light mode
    
    # Page navigation
    if "current_page" not in st.session_state:
        if st.session_state.authenticated:
            st.session_state.current_page = "chatbot"
        else:
            st.session_state.current_page = "homepage"
    
    # Only initialize conversation-related state if authenticated
    if st.session_state.authenticated:
        # Cache privacy verification to avoid repeated checks
        privacy_key = f"privacy_verified_{st.session_state.user_id}"
        if privacy_key not in st.session_state:
            from auth import verify_user_data_isolation, cleanup_orphaned_data
            is_isolated, message = verify_user_data_isolation()
            if not is_isolated:
                # Clean up orphaned data
                cleaned = cleanup_orphaned_data()
                if cleaned:
                    st.warning(f"🔒 Cleaned up orphaned data for privacy: {len(cleaned)} items removed")
            st.session_state[privacy_key] = True
        
        # Optimize conversation loading with Supabase caching
        current_user_key = f"conversations_for_{st.session_state.user_id}"
        conversations_cache_key = f"conversations_cache_{st.session_state.user_id}"
        
        # Only reload if user changed or conversations not cached
        if (st.session_state.get("last_loaded_user_id") != st.session_state.user_id or
            conversations_cache_key not in st.session_state):
            
            # Clear any existing conversation data to prevent cross-contamination
            keys_to_clear = [k for k in st.session_state.keys() 
                           if 'conversation' in k.lower() and st.session_state.user_id not in k]
            for key in keys_to_clear:
                if key != 'conversation_counter':  # Keep counter
                    del st.session_state[key]
            
            # Load fresh conversations for this user from Supabase (cached)
            if conversations_cache_key not in st.session_state:
                try:
                    conversations = load_user_conversations(st.session_state.user_id)
                    st.session_state[conversations_cache_key] = conversations
                except Exception as e:
                    st.error(f"Error loading conversations: {e}")
                    st.session_state[conversations_cache_key] = {}
            
            st.session_state.conversations = st.session_state[conversations_cache_key]
            st.session_state[current_user_key] = True
            st.session_state.last_loaded_user_id = st.session_state.user_id
            st.session_state.current_conversation_id = None  # Reset current conversation
            
        # Use cached conversations if available
        elif conversations_cache_key in st.session_state:
            st.session_state.conversations = st.session_state[conversations_cache_key]
            
        if "current_conversation_id" not in st.session_state:
            st.session_state.current_conversation_id = None
        if "conversation_counter" not in st.session_state:
            st.session_state.conversation_counter = len(st.session_state.conversations)
        if "search_query" not in st.session_state:
            st.session_state.search_query = ""