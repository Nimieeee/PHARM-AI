"""
Sidebar for Authenticated Users
"""

import streamlit as st
from auth import logout_user
from utils.conversation_manager import delete_conversation, duplicate_conversation
from rag_interface_chromadb import get_conversation_document_count, get_all_user_documents_count

def render_sidebar():
    """Render the sidebar with conversations and settings."""
    with st.sidebar:
        # User info and logout
        st.markdown(f"### 👋 Welcome, {st.session_state.username}!")
        
        # Sign out button
        if st.button("🚪 Sign Out", use_container_width=True, type="secondary"):
            logout_user()
            st.session_state.current_page = "homepage"
            st.rerun()
        
        st.markdown("---")
        
        # Search conversations
        st.markdown("### 🔍 Search Conversations")
        search_query = st.text_input("Search titles and messages", key="search_conversations", placeholder="Type to search...")
        
        if search_query:
            search_conversations(search_query)
        
        st.markdown("---")
        
        # Conversations list
        st.markdown("### 💬 Conversations")
        
        # New conversation button
        if st.button("➕ New Chat", use_container_width=True, type="primary"):
            from utils.conversation_manager import create_new_conversation
            create_new_conversation()
            st.rerun()
        
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
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        # Conversation button with document count
                        is_active = conv_id == st.session_state.current_conversation_id
                        button_style = "🟢 " if is_active else ""
                        
                        # Get document count for this conversation
                        doc_count = get_conversation_document_count(conv_id)
                        doc_indicator = f" 📚{doc_count}" if doc_count > 0 else ""
                        
                        if st.button(
                            f"{button_style}{conv_data['title'][:20]}...{doc_indicator}",
                            key=f"conv_{conv_id}",
                            use_container_width=True
                        ):
                            st.session_state.current_conversation_id = conv_id
                            st.rerun()
                    
                    with col2:
                        # More options dropdown
                        if st.button("⋯", key=f"more_{conv_id}", help="More options"):
                            st.session_state[f"show_options_{conv_id}"] = not st.session_state.get(f"show_options_{conv_id}", False)
                    
                    with col3:
                        # Delete button
                        if st.button("🗑️", key=f"del_{conv_id}", help="Delete conversation"):
                            delete_conversation(conv_id)
                            st.rerun()
                    
                    # Show options if toggled
                    if st.session_state.get(f"show_options_{conv_id}", False):
                        with st.expander("Options", expanded=True):
                            # Duplicate conversation
                            if st.button("📋 Duplicate", key=f"duplicate_{conv_id}", use_container_width=True):
                                new_conv_id = duplicate_conversation(conv_id)
                                if new_conv_id:
                                    st.session_state.current_conversation_id = new_conv_id
                                    st.success("Conversation duplicated!")
                                    st.rerun()
        else:
            st.info("No conversations yet. Click 'New Chat' to start!")
        
        st.markdown("---")
        
        # Document count and upload status
        if st.session_state.current_conversation_id:
            # Show documents for current conversation
            conv_doc_count = get_conversation_document_count()
            if conv_doc_count > 0:
                st.success(f"📚 {conv_doc_count} documents in this chat")
            else:
                st.info("📚 No documents in this chat")
        
        # Show total documents across all conversations
        total_doc_count = get_all_user_documents_count()
        if total_doc_count > 0:
            st.info(f"📊 {total_doc_count} total documents across all chats")
        
        # Upload limit status
        from auth import get_user_upload_count
        upload_count = get_user_upload_count(st.session_state.user_id)
        st.info(f"📤 Uploads: {upload_count} today (unlimited)")
        
        st.markdown("---")
        
        # Theme toggle
        st.markdown("### 🎨 Appearance")
        from utils.theme import render_theme_toggle
        render_theme_toggle()

def search_conversations(query: str):
    """Search conversations by title and content."""
    if not query.strip():
        return
    
    query_lower = query.lower()
    matching_conversations = []
    
    for conv_id, conv_data in st.session_state.conversations.items():
        # Search in title
        if query_lower in conv_data.get('title', '').lower():
            matching_conversations.append((conv_id, conv_data, 'title'))
            continue
        
        # Search in messages
        for message in conv_data.get('messages', []):
            if query_lower in message.get('content', '').lower():
                matching_conversations.append((conv_id, conv_data, 'message'))
                break
    
    if matching_conversations:
        st.markdown("#### 🔍 Search Results")
        for conv_id, conv_data, match_type in matching_conversations[:5]:  # Limit to 5 results
            match_indicator = "📝" if match_type == 'title' else "💬"
            if st.button(
                f"{match_indicator} {conv_data['title'][:30]}...",
                key=f"search_{conv_id}",
                use_container_width=True
            ):
                st.session_state.current_conversation_id = conv_id
                st.session_state.search_query = ""  # Clear search
                st.rerun()
    else:
        st.info("No conversations found matching your search.")