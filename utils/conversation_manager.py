"""
Conversation Management
"""

import streamlit as st
import uuid
from datetime import datetime
from auth import save_user_conversations
from pathlib import Path
import shutil

# Fixed model
FIXED_MODEL = "meta-llama/llama-4-maverick-17b-128e-instruct"

def create_new_conversation():
    """Create a new conversation."""
    conversation_id = str(uuid.uuid4())
    st.session_state.conversation_counter += 1
    st.session_state.conversations[conversation_id] = {
        "title": f"New Chat {st.session_state.conversation_counter}",
        "messages": [],
        "created_at": datetime.now().isoformat(),
        "model": FIXED_MODEL
    }
    st.session_state.current_conversation_id = conversation_id
    
    # Save conversations to file
    save_user_conversations(st.session_state.user_id, st.session_state.conversations)
    
    return conversation_id

def get_current_messages():
    """Get messages from current conversation."""
    try:
        if (hasattr(st.session_state, 'current_conversation_id') and 
            st.session_state.current_conversation_id and 
            hasattr(st.session_state, 'conversations') and
            st.session_state.current_conversation_id in st.session_state.conversations):
            return st.session_state.conversations[st.session_state.current_conversation_id]["messages"]
    except Exception:
        pass
    return []

def add_message_to_current_conversation(role: str, content: str):
    """Add message to current conversation."""
    if not st.session_state.current_conversation_id:
        create_new_conversation()
    
    st.session_state.conversations[st.session_state.current_conversation_id]["messages"].append({
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat()
    })
    
    # Update conversation title based on first user message
    if role == "user" and len(st.session_state.conversations[st.session_state.current_conversation_id]["messages"]) == 1:
        title = content[:50] + "..." if len(content) > 50 else content
        st.session_state.conversations[st.session_state.current_conversation_id]["title"] = title
    
    # Save conversations to file
    save_user_conversations(st.session_state.user_id, st.session_state.conversations)

def delete_conversation(conversation_id: str):
    """Delete a conversation and its associated RAG data."""
    if conversation_id in st.session_state.conversations:
        # Clean up conversation-specific RAG data
        try:
            user_rag_dir = Path("user_data") / f"rag_{st.session_state.user_id}"
            conv_rag_dir = user_rag_dir / f"conversation_{conversation_id}"
            if conv_rag_dir.exists():
                shutil.rmtree(conv_rag_dir)
            
            # Clean up session state RAG system
            rag_key = f"chromadb_rag_system_{conversation_id}"
            if rag_key in st.session_state:
                del st.session_state[rag_key]
        except Exception as e:
            print(f"Error cleaning up RAG data: {e}")
        
        del st.session_state.conversations[conversation_id]
        if st.session_state.current_conversation_id == conversation_id:
            # Switch to another conversation or create new one
            if st.session_state.conversations:
                st.session_state.current_conversation_id = list(st.session_state.conversations.keys())[0]
            else:
                st.session_state.current_conversation_id = None
        
        # Save conversations to file
        save_user_conversations(st.session_state.user_id, st.session_state.conversations)

def duplicate_conversation(conversation_id: str):
    """Create a duplicate of an existing conversation."""
    if conversation_id not in st.session_state.conversations:
        return None
    
    original_conv = st.session_state.conversations[conversation_id]
    new_conversation_id = str(uuid.uuid4())
    
    st.session_state.conversation_counter += 1
    st.session_state.conversations[new_conversation_id] = {
        "title": f"Copy of {original_conv['title']}",
        "messages": original_conv["messages"].copy(),
        "created_at": datetime.now().isoformat(),
        "model": original_conv.get("model", FIXED_MODEL)
    }
    
    # Save conversations to file
    save_user_conversations(st.session_state.user_id, st.session_state.conversations)
    
    return new_conversation_id