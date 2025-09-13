"""
Clean Conversation Management for PharmGPT
Simple, reliable conversation and message handling
"""

import asyncio
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Optional

import streamlit as st

# Configure logging
logger = logging.getLogger(__name__)

def run_async(coro):
    """Run async function in Streamlit context - simple and reliable."""
    try:
        # Try to get existing event loop
        loop = asyncio.get_event_loop()
    except RuntimeError:
        # Create new event loop if none exists
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    try:
        return loop.run_until_complete(coro)
    except Exception as e:
        logger.error(f"Async operation failed: {e}")
        raise

async def create_new_conversation():
    """Create a new conversation."""
    logger.info("Creating new conversation")
    
    try:
        # Import here to avoid circular imports
        from services.conversation_service import conversation_service
        from services.user_service import user_service
        
        # Get user UUID from legacy user_id
        user_data = await user_service.get_user_by_id(st.session_state.user_id)
        if not user_data:
            logger.error(f"User not found: {st.session_state.user_id}")
            return None
        
        # Generate conversation title
        st.session_state.conversation_counter = st.session_state.get('conversation_counter', 0) + 1
        title = f"New Chat {st.session_state.conversation_counter}"
        
        # Create conversation in database
        conversation_id = await conversation_service.create_conversation(
            user_data['id'], 
            title, 
            "meta-llama/llama-4-maverick-17b-128e-instruct"
        )
        
        # Update local session state
        if 'conversations' not in st.session_state:
            st.session_state.conversations = {}
        
        st.session_state.conversations[conversation_id] = {
            "title": title,
            "messages": [],
            "created_at": datetime.now().isoformat(),
            "model": "meta-llama/llama-4-maverick-17b-128e-instruct"
        }
        st.session_state.current_conversation_id = conversation_id
        
        logger.info(f"✅ New conversation created: {conversation_id}")
        return conversation_id
        
    except Exception as e:
        logger.error(f"Failed to create conversation: {e}")
        return None

def get_current_messages() -> List[Dict]:
    """Get messages from current conversation."""
    try:
        if (st.session_state.get('current_conversation_id') and 
            st.session_state.get('conversations') and
            st.session_state.current_conversation_id in st.session_state.conversations):
            return st.session_state.conversations[st.session_state.current_conversation_id]["messages"]
    except Exception as e:
        logger.error(f"Error getting current messages: {e}")
    
    return []

async def add_message_to_current_conversation(role: str, content: str) -> bool:
    """Add message to current conversation."""
    logger.info(f"Adding {role} message to conversation")
    
    try:
        # Ensure we have a conversation
        if not st.session_state.get('current_conversation_id'):
            conversation_id = await create_new_conversation()
            if not conversation_id:
                return False
        
        # Import here to avoid circular imports
        from services.conversation_service import conversation_service
        from services.user_service import user_service
        
        # Get user UUID
        user_data = await user_service.get_user_by_id(st.session_state.user_id)
        if not user_data:
            logger.error("User not found")
            return False
        
        # Create message
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        
        # Add to database
        success = await conversation_service.add_message(
            user_data['id'],
            st.session_state.current_conversation_id,
            message
        )
        
        if success:
            # Update local session state
            if st.session_state.current_conversation_id in st.session_state.conversations:
                st.session_state.conversations[st.session_state.current_conversation_id]["messages"].append(message)
                
                # Update conversation title based on first user message
                if (role == "user" and 
                    len(st.session_state.conversations[st.session_state.current_conversation_id]["messages"]) == 1):
                    title = content[:50] + "..." if len(content) > 50 else content
                    st.session_state.conversations[st.session_state.current_conversation_id]["title"] = title
                    
                    # Update title in database
                    await conversation_service.update_conversation_title(
                        user_data['id'],
                        st.session_state.current_conversation_id,
                        title
                    )
            
            logger.info(f"✅ Message added successfully")
            return True
        else:
            logger.error("Failed to save message to database")
            return False
            
    except Exception as e:
        logger.error(f"Error adding message: {e}")
        return False

async def delete_conversation(conversation_id: str) -> bool:
    """Delete a conversation."""
    try:
        # Import here to avoid circular imports
        from services.conversation_service import conversation_service
        from services.user_service import user_service
        
        # Get user UUID
        user_data = await user_service.get_user_by_id(st.session_state.user_id)
        if not user_data:
            return False
        
        # Delete from database
        success = await conversation_service.delete_conversation(
            user_data['id'],
            conversation_id
        )
        
        if success:
            # Clean up session state
            if conversation_id in st.session_state.conversations:
                del st.session_state.conversations[conversation_id]
            
            if st.session_state.current_conversation_id == conversation_id:
                # Switch to another conversation or clear current
                if st.session_state.conversations:
                    st.session_state.current_conversation_id = list(st.session_state.conversations.keys())[0]
                else:
                    st.session_state.current_conversation_id = None
            
            logger.info(f"✅ Conversation deleted: {conversation_id}")
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error deleting conversation: {e}")
        return False

async def duplicate_conversation(conversation_id: str) -> Optional[str]:
    """Duplicate a conversation."""
    try:
        # Import here to avoid circular imports
        from services.conversation_service import conversation_service
        from services.user_service import user_service
        
        # Get user UUID
        user_data = await user_service.get_user_by_id(st.session_state.user_id)
        if not user_data:
            return None
        
        # Get original conversation
        if conversation_id not in st.session_state.conversations:
            logger.error(f"Conversation not found: {conversation_id}")
            return None
        
        original_conv = st.session_state.conversations[conversation_id]
        
        # Create new conversation with duplicated title
        new_title = f"Copy of {original_conv['title']}"
        new_conversation_id = await conversation_service.create_conversation(
            user_data['id'], 
            new_title, 
            original_conv.get('model', 'meta-llama/llama-4-maverick-17b-128e-instruct')
        )
        
        if not new_conversation_id:
            return None
        
        # Copy messages to new conversation
        for message in original_conv.get('messages', []):
            await conversation_service.add_message(
                user_data['id'],
                new_conversation_id,
                message
            )
        
        # Update local session state
        st.session_state.conversations[new_conversation_id] = {
            "title": new_title,
            "messages": original_conv.get('messages', []).copy(),
            "created_at": datetime.now().isoformat(),
            "model": original_conv.get('model', 'meta-llama/llama-4-maverick-17b-128e-instruct')
        }
        
        logger.info(f"✅ Conversation duplicated: {new_conversation_id}")
        return new_conversation_id
        
    except Exception as e:
        logger.error(f"Error duplicating conversation: {e}")
        return None