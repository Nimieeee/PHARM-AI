"""
Enhanced Conversation Management for PharmGPT
Advanced conversation and message handling with better features
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

async def create_new_conversation(title: str = None) -> Optional[str]:
    """Create a new conversation with enhanced features."""
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
        if not title:
            st.session_state.conversation_counter = st.session_state.get('conversation_counter', 0) + 1
            title = f"New Chat {st.session_state.conversation_counter}"
        
        # Create conversation in database
        conversation_id = await conversation_service.create_conversation(
            user_data['id'], 
            title, 
            st.session_state.get('selected_model_mode', 'normal')
        )
        
        # Update local session state securely
        from fix_user_isolation import get_secure_conversations, secure_update_conversations
        conversations = get_secure_conversations()
        conversations[conversation_id] = {
            "title": title,
            "messages": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "model": st.session_state.get('selected_model_mode', 'normal'),
            "message_count": 0
        }
        secure_update_conversations(conversations)
        
        # Set as current conversation
        st.session_state.current_conversation_id = conversation_id
        st.session_state.chat_messages = []
        
        # Clear any existing documents for new conversation
        if 'conversation_documents' not in st.session_state:
            st.session_state.conversation_documents = {}
        st.session_state.conversation_documents[conversation_id] = []
        
        logger.info(f"✅ New conversation created: {conversation_id}")
        return conversation_id
        
    except Exception as e:
        logger.error(f"Failed to create conversation: {e}")
        return None

async def load_user_conversations() -> Dict:
    """Load all conversations for the current user."""
    try:
        if not st.session_state.get('authenticated') or not st.session_state.get('user_id'):
            return {}
        
        from services.conversation_service import conversation_service
        from services.user_service import user_service
        
        # Get user UUID
        user_data = await user_service.get_user_by_id(st.session_state.user_id)
        if not user_data:
            return {}
        
        # Load conversations from database
        conversations = await conversation_service.get_user_conversations(user_data['id'])
        
        # Update session state securely
        from fix_user_isolation import secure_update_conversations
        secure_update_conversations(conversations)
        
        logger.info(f"Loaded {len(conversations)} conversations")
        return conversations
        
    except Exception as e:
        logger.error(f"Error loading conversations: {e}")
        return {}

def get_current_messages() -> List[Dict]:
    """Get messages from current conversation."""
    try:
        from fix_user_isolation import get_secure_current_conversation
        current_conv = get_secure_current_conversation()
        if current_conv:
            return current_conv.get("messages", [])
    except Exception as e:
        logger.error(f"Error getting current messages: {e}")
    
    return []

async def add_message_to_current_conversation(role: str, content: str) -> bool:
    """Add message to current conversation with enhanced features."""
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
        
        # Create message with enhanced metadata
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "model": st.session_state.get('selected_model_mode', 'normal') if role == "assistant" else None
        }
        
        # Add to database
        success = await conversation_service.add_message(
            user_data['id'],
            st.session_state.current_conversation_id,
            message
        )
        
        if success:
            # Update local session state securely
            from fix_user_isolation import secure_update_conversation, get_secure_conversations
            conv_id = st.session_state.current_conversation_id
            
            # Get current conversation data
            conversations = get_secure_conversations()
            if conv_id in conversations:
                current_conv = conversations[conv_id]
                messages = current_conv.get("messages", [])
                messages.append(message)
                
                updates = {
                    "messages": messages,
                    "updated_at": datetime.now().isoformat(),
                    "message_count": len(messages)
                }
                
                # Update conversation title based on first user message
                if role == "user" and len(messages) == 1:
                    title = generate_smart_title(content)
                    updates["title"] = title
                
                secure_update_conversation(conv_id, updates)
                
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

def generate_smart_title(content: str) -> str:
    """Generate a smart title based on message content."""
    # Remove common question words and clean up
    content = content.strip()
    
    # Common pharmacology terms to prioritize in titles
    pharma_terms = [
        'mechanism', 'action', 'drug', 'interaction', 'side effect', 'dosage',
        'pharmacokinetics', 'pharmacodynamics', 'receptor', 'enzyme', 'pathway',
        'metabolism', 'absorption', 'distribution', 'excretion', 'bioavailability',
        'half-life', 'clearance', 'toxicity', 'adverse', 'contraindication'
    ]
    
    # Look for important terms
    words = content.lower().split()
    important_words = []
    
    for word in words:
        if any(term in word for term in pharma_terms):
            important_words.append(word)
    
    # Create title
    if important_words:
        # Use important pharmacology terms
        title_base = ' '.join(important_words[:3])
    else:
        # Fallback to first few words
        title_base = ' '.join(words[:5])
    
    # Capitalize and limit length
    title = title_base.title()
    if len(title) > 50:
        title = title[:47] + "..."
    
    return title if title else f"Chat {datetime.now().strftime('%m/%d %H:%M')}"

async def update_conversation_title(conversation_id: str, new_title: str) -> bool:
    """Update conversation title."""
    try:
        from services.conversation_service import conversation_service
        from services.user_service import user_service
        
        # Get user UUID
        user_data = await user_service.get_user_by_id(st.session_state.user_id)
        if not user_data:
            return False
        
        # Update in database
        success = await conversation_service.update_conversation_title(
            user_data['id'],
            conversation_id,
            new_title
        )
        
        if success:
            # Update local session state securely
            from fix_user_isolation import secure_update_conversation
            secure_update_conversation(conversation_id, {
                "title": new_title,
                "updated_at": datetime.now().isoformat()
            })
            
            logger.info(f"✅ Conversation title updated: {conversation_id}")
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error updating conversation title: {e}")
        return False

async def delete_conversation(conversation_id: str) -> bool:
    """Delete a conversation with enhanced cleanup."""
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
            # Clean up session state securely
            from fix_user_isolation import secure_delete_conversation, get_secure_conversations
            secure_delete_conversation(conversation_id)
            
            # Clean up conversation documents
            if 'conversation_documents' in st.session_state and conversation_id in st.session_state.conversation_documents:
                del st.session_state.conversation_documents[conversation_id]
            
            # Handle current conversation
            if st.session_state.current_conversation_id == conversation_id:
                # Switch to another conversation or clear current
                conversations = get_secure_conversations()
                if conversations:
                    # Switch to most recent conversation
                    sorted_conversations = sorted(
                        conversations.items(),
                        key=lambda x: x[1].get('updated_at', x[1].get('created_at', '')),
                        reverse=True
                    )
                    st.session_state.current_conversation_id = sorted_conversations[0][0]
                    st.session_state.chat_messages = sorted_conversations[0][1].get('messages', [])
                else:
                    st.session_state.current_conversation_id = None
                    st.session_state.chat_messages = []
            
            logger.info(f"✅ Conversation deleted: {conversation_id}")
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error deleting conversation: {e}")
        return False

async def duplicate_conversation(conversation_id: str, new_title: str = None) -> Optional[str]:
    """Duplicate a conversation with enhanced features."""
    try:
        # Import here to avoid circular imports
        from services.conversation_service import conversation_service
        from services.user_service import user_service
        
        # Get user UUID
        user_data = await user_service.get_user_by_id(st.session_state.user_id)
        if not user_data:
            return None
        
        # Get original conversation securely
        from fix_user_isolation import get_secure_conversations
        conversations = get_secure_conversations()
        if conversation_id not in conversations:
            logger.error(f"Conversation not found: {conversation_id}")
            return None
        
        original_conv = conversations[conversation_id]
        
        # Create new conversation with duplicated title
        if not new_title:
            new_title = f"Copy of {original_conv['title']}"
        
        new_conversation_id = await conversation_service.create_conversation(
            user_data['id'], 
            new_title, 
            original_conv.get('model', 'normal')
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
        
        # Update local session state securely
        from fix_user_isolation import get_secure_conversations, secure_update_conversations
        conversations = get_secure_conversations()
        conversations[new_conversation_id] = {
            "title": new_title,
            "messages": original_conv.get('messages', []).copy(),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "model": original_conv.get('model', 'normal'),
            "message_count": len(original_conv.get('messages', []))
        }
        secure_update_conversations(conversations)
        
        # Copy documents if any
        if 'conversation_documents' in st.session_state and conversation_id in st.session_state.conversation_documents:
            st.session_state.conversation_documents[new_conversation_id] = st.session_state.conversation_documents[conversation_id].copy()
        
        logger.info(f"✅ Conversation duplicated: {new_conversation_id}")
        return new_conversation_id
        
    except Exception as e:
        logger.error(f"Error duplicating conversation: {e}")
        return None

async def search_conversations(query: str) -> List[Dict]:
    """Search conversations by title and content."""
    try:
        from fix_user_isolation import get_secure_conversations
        conversations = get_secure_conversations()
        results = []
        
        query_lower = query.lower()
        
        for conv_id, conv_data in conversations.items():
            # Search in title
            if query_lower in conv_data.get('title', '').lower():
                results.append({
                    'conversation_id': conv_id,
                    'title': conv_data['title'],
                    'match_type': 'title',
                    'relevance': 1.0
                })
                continue
            
            # Search in messages
            messages = conv_data.get('messages', [])
            for message in messages:
                if query_lower in message.get('content', '').lower():
                    results.append({
                        'conversation_id': conv_id,
                        'title': conv_data['title'],
                        'match_type': 'content',
                        'relevance': 0.8,
                        'message_preview': message['content'][:100] + "..."
                    })
                    break
        
        # Sort by relevance
        results.sort(key=lambda x: x['relevance'], reverse=True)
        return results
        
    except Exception as e:
        logger.error(f"Error searching conversations: {e}")
        return []

def get_conversation_stats() -> Dict:
    """Get statistics about user's conversations."""
    try:
        from fix_user_isolation import get_secure_conversations
        conversations = get_secure_conversations()
        
        total_conversations = len(conversations)
        total_messages = sum(len(conv.get('messages', [])) for conv in conversations.values())
        
        # Most active conversation
        most_active = None
        max_messages = 0
        
        for conv_id, conv_data in conversations.items():
            message_count = len(conv_data.get('messages', []))
            if message_count > max_messages:
                max_messages = message_count
                most_active = conv_data.get('title', 'Untitled')
        
        return {
            'total_conversations': total_conversations,
            'total_messages': total_messages,
            'most_active_conversation': most_active,
            'most_active_message_count': max_messages
        }
        
    except Exception as e:
        logger.error(f"Error getting conversation stats: {e}")
        return {}