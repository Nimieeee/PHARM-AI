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
    """Initialize session state variables."""
    logger.info("Initializing session state")
    
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
    
    if "search_query" not in st.session_state:
        st.session_state.search_query = ""
    
    # Initialize auth if we have session info
    if st.session_state.authenticated and st.session_state.user_id:
        try:
            load_user_conversations()
        except Exception as e:
            logger.error(f"Error loading user conversations: {e}")

def load_user_conversations():
    """Load user conversations from database."""
    if not st.session_state.authenticated or not st.session_state.user_id:
        return
    
    try:
        from auth import load_user_conversations as load_conversations
        conversations = load_conversations(st.session_state.user_id)
        st.session_state.conversations = conversations
        st.session_state.conversation_counter = len(conversations)
        logger.info(f"Loaded {len(conversations)} conversations for user")
    except Exception as e:
        logger.error(f"Failed to load conversations: {e}")
        st.session_state.conversations = {}