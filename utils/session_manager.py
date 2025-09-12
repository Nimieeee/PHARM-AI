"""
Session State Management
"""

import streamlit as st
from auth import load_user_conversations

def initialize_session_state():
    """Initialize session state variables."""
    # Initialize authentication with persistent session support
    from auth import initialize_auth_session
    initialize_auth_session()
    
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
        # Verify user data isolation on first load
        if "privacy_verified" not in st.session_state:
            from auth import verify_user_data_isolation, cleanup_orphaned_data
            is_isolated, message = verify_user_data_isolation()
            if not is_isolated:
                # Clean up orphaned data
                cleaned = cleanup_orphaned_data()
                if cleaned:
                    st.warning(f"🔒 Cleaned up orphaned data for privacy: {len(cleaned)} items removed")
            st.session_state.privacy_verified = True
        
        # Force reload conversations if user changed or not loaded
        current_user_key = f"conversations_for_{st.session_state.user_id}"
        if (current_user_key not in st.session_state or 
            "conversations" not in st.session_state or
            st.session_state.get("last_loaded_user_id") != st.session_state.user_id):
            
            # Clear any existing conversation data to prevent cross-contamination
            keys_to_clear = [k for k in st.session_state.keys() if 'conversation' in k.lower()]
            for key in keys_to_clear:
                if key != 'conversation_counter':  # Keep counter
                    del st.session_state[key]
            
            # Load fresh conversations for this user
            st.session_state.conversations = load_user_conversations(st.session_state.user_id)
            st.session_state[current_user_key] = True
            st.session_state.last_loaded_user_id = st.session_state.user_id
            st.session_state.current_conversation_id = None  # Reset current conversation
            
        if "current_conversation_id" not in st.session_state:
            st.session_state.current_conversation_id = None
        if "conversation_counter" not in st.session_state:
            st.session_state.conversation_counter = len(st.session_state.conversations)
        if "search_query" not in st.session_state:
            st.session_state.search_query = ""