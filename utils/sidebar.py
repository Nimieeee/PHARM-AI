"""
Sidebar for Authenticated Users
"""

import streamlit as st
import logging
from auth import logout_current_user
from utils.conversation_manager import delete_conversation, duplicate_conversation

# Configure logging
logger = logging.getLogger(__name__)

def render_sidebar():
    """Render the sidebar with conversations and settings."""
    with st.sidebar:
        # Initialize response generation flag if not exists
        if 'generating_response' not in st.session_state:
            st.session_state.generating_response = False
        
        # App title/logo
        st.markdown("# 💊 PharmGPT")
        
        # Contact Support button
        if st.button("📞 Contact Support", use_container_width=True):
            st.switch_page("pages/4_📞_Contact_Support.py")
        
        # Sign out button
        if st.button("🚪 Sign Out", use_container_width=True, type="secondary"):
            # Only sign out if we're not generating a response
            if not st.session_state.get('generating_response', False):
                logout_current_user()
                st.session_state.current_page = "homepage"
                try:
                    if hasattr(st, 'switch_page'):
                        st.switch_page("pages/1_🏠_Homepage.py")
                    else:
                        st.rerun()
                except Exception as e:
                    logger.warning(f"Page switch failed: {e}")
                    st.rerun()
            else:
                st.warning("⚠️ Please wait for the current response to complete before signing out.")
        
        st.markdown("---")
        
        # Conversations list
        st.markdown("### 💬 Conversations")
        
        # New conversation button
        if st.button("➕ New Chat", use_container_width=True, type="primary"):
            from utils.conversation_manager import create_new_conversation, run_async
            conversation_id = run_async(create_new_conversation())
            if conversation_id:
                # Only rerun if we're not currently generating a response
                if not st.session_state.get('generating_response', False):
                    st.success("✅ New conversation created!")
                    st.rerun()
                else:
                    st.success("✅ New conversation created! It will appear after the current response completes.")
            else:
                st.error("Failed to create conversation")
        
        # List conversations
        if st.session_state.conversations:
            # Sort conversations by creation date (newest first)
            sorted_conversations = sorted(
                st.session_state.conversations.items(),
                key=lambda x: x[1].get('created_at', ''),
                reverse=True
            )
            
            for conv_id, conv_data in sorted_conversations:
                with st.container():
                    col1, col2 = st.columns([4, 1])
                    
                    with col1:
                        # Conversation button
                        is_active = conv_id == st.session_state.current_conversation_id
                        button_style = "🟢 " if is_active else ""
                        
                        if st.button(
                            f"{button_style}{conv_data['title'][:25]}...",
                            key=f"conv_{conv_id}",
                            use_container_width=True
                        ):
                            # Only switch conversations if we're not generating a response
                            if not st.session_state.get('generating_response', False):
                                st.session_state.current_conversation_id = conv_id
                                # Clear chat messages to force reload
                                if 'last_loaded_conversation' in st.session_state:
                                    st.session_state.last_loaded_conversation = None
                                st.rerun()
                            else:
                                st.warning("⚠️ Please wait for the current response to complete before switching conversations.")
                    
                    with col2:
                        # Delete button
                        if st.button("🗑️", key=f"del_{conv_id}", help="Delete conversation"):
                            from utils.conversation_manager import run_async, create_new_conversation
                            success = run_async(delete_conversation(conv_id))
                            if success:
                                # Check if we need to create a new conversation
                                if not st.session_state.conversations:
                                    # No conversations left, create a new one automatically
                                    new_conv_id = run_async(create_new_conversation())
                                    if new_conv_id:
                                        st.session_state.current_conversation_id = new_conv_id
                                        # Clear chat messages to force reload
                                        if 'last_loaded_conversation' in st.session_state:
                                            st.session_state.last_loaded_conversation = None
                                
                                # Only rerun if we're not currently generating a response
                                if not st.session_state.get('generating_response', False):
                                    st.success("✅ Conversation deleted!")
                                    st.rerun()
                                else:
                                    st.success("✅ Conversation deleted! Changes will appear after the current response completes.")
                            else:
                                st.error("Failed to delete conversation")
        else:
            st.info("No conversations yet. Click 'New Chat' to start!")
            # Auto-create first conversation if none exist
            if not st.session_state.get('auto_created_first_chat', False):
                from utils.conversation_manager import create_new_conversation, run_async
                conversation_id = run_async(create_new_conversation())
                if conversation_id:
                    st.session_state.current_conversation_id = conversation_id
                    st.session_state.auto_created_first_chat = True
                    # Clear chat messages to force reload
                    if 'last_loaded_conversation' in st.session_state:
                        st.session_state.last_loaded_conversation = None
                    st.rerun()

