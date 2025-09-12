"""
Conversation Management - Supabase Version
"""

import streamlit as st
import uuid
import asyncio
from datetime import datetime
from services.conversation_service import conversation_service
from services.user_service import user_service

# Fixed model
FIXED_MODEL = "meta-llama/llama-4-maverick-17b-128e-instruct"

# Helper function to run async functions in Streamlit
def run_async(coro):
    """Run async function in Streamlit context."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(coro)

def create_new_conversation():
    """Create a new conversation using Supabase."""
    try:
        # Get user UUID from legacy user_id
        user_data = run_async(user_service.get_user_by_id(st.session_state.user_id))
        if not user_data:
            st.error("User not found")
            return None
        
        st.session_state.conversation_counter += 1
        title = f"New Chat {st.session_state.conversation_counter}"
        
        # Create conversation in Supabase
        conversation_id = run_async(conversation_service.create_conversation(
            user_data['id'], 
            title, 
            FIXED_MODEL
        ))
        
        # Update local session state
        st.session_state.conversations[conversation_id] = {
            "title": title,
            "messages": [],
            "created_at": datetime.now().isoformat(),
            "model": FIXED_MODEL
        }
        st.session_state.current_conversation_id = conversation_id
        
        return conversation_id
        
    except Exception as e:
        st.error(f"Error creating conversation: {e}")
        return None

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
    """Add message to current conversation using Supabase."""
    try:
        if not st.session_state.current_conversation_id:
            create_new_conversation()
        
        # Get user UUID from legacy user_id
        user_data = run_async(user_service.get_user_by_id(st.session_state.user_id))
        if not user_data:
            st.error("User not found")
            return
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        
        # Add message to Supabase
        success = run_async(conversation_service.add_message(
            user_data['id'],
            st.session_state.current_conversation_id,
            message
        ))
        
        if success:
            # Update local session state
            st.session_state.conversations[st.session_state.current_conversation_id]["messages"].append(message)
            
            # Update conversation title based on first user message
            if role == "user" and len(st.session_state.conversations[st.session_state.current_conversation_id]["messages"]) == 1:
                title = content[:50] + "..." if len(content) > 50 else content
                st.session_state.conversations[st.session_state.current_conversation_id]["title"] = title
                
                # Update title in Supabase
                run_async(conversation_service.update_conversation_title(
                    user_data['id'],
                    st.session_state.current_conversation_id,
                    title
                ))
            
            # Update cache
            conversations_cache_key = f"conversations_cache_{st.session_state.user_id}"
            st.session_state[conversations_cache_key] = st.session_state.conversations
        else:
            st.error("Failed to save message")
            
    except Exception as e:
        st.error(f"Error adding message: {e}")

def delete_conversation(conversation_id: str):
    """Delete a conversation and its associated data using Supabase."""
    try:
        if conversation_id in st.session_state.conversations:
            # Get user UUID from legacy user_id
            user_data = run_async(user_service.get_user_by_id(st.session_state.user_id))
            if not user_data:
                st.error("User not found")
                return
            
            # Delete conversation from Supabase (this will cascade delete related documents)
            success = run_async(conversation_service.delete_conversation(
                user_data['id'],
                conversation_id
            ))
            
            if success:
                # Clean up session state
                del st.session_state.conversations[conversation_id]
                
                if st.session_state.current_conversation_id == conversation_id:
                    # Switch to another conversation or create new one
                    if st.session_state.conversations:
                        st.session_state.current_conversation_id = list(st.session_state.conversations.keys())[0]
                    else:
                        st.session_state.current_conversation_id = None
                
                # Clean up session state RAG system cache
                rag_key = f"chromadb_rag_system_{conversation_id}"
                if rag_key in st.session_state:
                    del st.session_state[rag_key]
                
                # Update cache
                conversations_cache_key = f"conversations_cache_{st.session_state.user_id}"
                st.session_state[conversations_cache_key] = st.session_state.conversations
            else:
                st.error("Failed to delete conversation")
                
    except Exception as e:
        st.error(f"Error deleting conversation: {e}")

def duplicate_conversation(conversation_id: str):
    """Create a duplicate of an existing conversation using Supabase."""
    try:
        if conversation_id not in st.session_state.conversations:
            return None
        
        # Get user UUID from legacy user_id
        user_data = run_async(user_service.get_user_by_id(st.session_state.user_id))
        if not user_data:
            st.error("User not found")
            return None
        
        original_conv = st.session_state.conversations[conversation_id]
        new_title = f"Copy of {original_conv['title']}"
        
        # Duplicate conversation in Supabase
        new_conversation_id = run_async(conversation_service.duplicate_conversation(
            user_data['id'],
            conversation_id,
            new_title
        ))
        
        if new_conversation_id:
            # Update local session state
            st.session_state.conversation_counter += 1
            st.session_state.conversations[new_conversation_id] = {
                "title": new_title,
                "messages": original_conv["messages"].copy(),
                "created_at": datetime.now().isoformat(),
                "model": original_conv.get("model", FIXED_MODEL)
            }
            
            # Update cache
            conversations_cache_key = f"conversations_cache_{st.session_state.user_id}"
            st.session_state[conversations_cache_key] = st.session_state.conversations
            
            return new_conversation_id
        else:
            st.error("Failed to duplicate conversation")
            return None
            
    except Exception as e:
        st.error(f"Error duplicating conversation: {e}")
        return None