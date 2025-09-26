"""
Conversation Manager for PharmGPT
Handles conversation lifecycle, user isolation, and message management
"""

import logging
import asyncio
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import uuid

from core.supabase_client import supabase_manager
from core.auth import get_current_user_id

# Configure logging
logger = logging.getLogger(__name__)


def run_async(coro):
    """Helper to run async functions in Streamlit."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    try:
        return loop.run_until_complete(coro)
    except Exception as e:
        logger.error(f"Error running async operation: {e}")
        raise


class ConversationManager:
    """Manages conversations with proper user isolation."""
    
    def __init__(self):
        self._cache = {}
        self._cache_timeout = 300  # 5 minutes
    
    def _get_cache_key(self, user_id: str, key: str) -> str:
        """Generate cache key for user-specific data."""
        return f"{user_id}:{key}"
    
    def _is_cache_valid(self, timestamp: datetime) -> bool:
        """Check if cached data is still valid."""
        return (datetime.now() - timestamp).seconds < self._cache_timeout
    
    async def create_conversation(self, title: str, model: str = 'normal',
                                user_id: str = None) -> Optional[str]:
        """Create a new conversation for the user."""
        try:
            if not user_id:
                user_id = get_current_user_id()
            
            if not user_id:
                logger.error("No user ID provided for conversation creation")
                return None
            
            conversation_id = await supabase_manager.create_conversation(
                user_id=user_id,
                title=title,
                model=model
            )
            
            if conversation_id:
                # Clear conversations cache for user
                cache_key = self._get_cache_key(user_id, 'conversations')
                if cache_key in self._cache:
                    del self._cache[cache_key]
                
                logger.info(f"Created conversation {conversation_id} for user {user_id}")
            
            return conversation_id
            
        except Exception as e:
            logger.error(f"Error creating conversation: {e}")
            return None
    
    async def get_user_conversations(self, user_id: str = None) -> List[Dict]:
        """Get all conversations for the user with caching."""
        try:
            if not user_id:
                user_id = get_current_user_id()
            
            if not user_id:
                logger.error("No user ID provided for getting conversations")
                return []
            
            # Check cache first
            cache_key = self._get_cache_key(user_id, 'conversations')
            if cache_key in self._cache:
                cached_data, timestamp = self._cache[cache_key]
                if self._is_cache_valid(timestamp):
                    return cached_data
            
            # Fetch from database
            conversations = await supabase_manager.get_user_conversations(user_id)
            
            # Cache the result
            self._cache[cache_key] = (conversations, datetime.now())
            
            logger.info(f"Retrieved {len(conversations)} conversations for user {user_id}")
            return conversations
            
        except Exception as e:
            logger.error(f"Error getting user conversations: {e}")
            return []
    
    async def get_conversation_messages(self, conversation_id: str,
                                      user_id: str = None) -> List[Dict]:
        """Get messages for a specific conversation with user validation."""
        try:
            if not user_id:
                user_id = get_current_user_id()
            
            if not user_id:
                logger.error("No user ID provided for getting messages")
                return []
            
            # Check cache first
            cache_key = self._get_cache_key(user_id, f'messages:{conversation_id}')
            if cache_key in self._cache:
                cached_data, timestamp = self._cache[cache_key]
                if self._is_cache_valid(timestamp):
                    return cached_data
            
            # Fetch from database (user isolation handled by RLS)
            messages = await supabase_manager.get_conversation_messages(
                conversation_id, user_id
            )
            
            # Cache the result
            self._cache[cache_key] = (messages, datetime.now())
            
            logger.info(f"Retrieved {len(messages)} messages for conversation {conversation_id}")
            return messages
            
        except Exception as e:
            logger.error(f"Error getting conversation messages: {e}")
            return []
    
    async def add_message(self, conversation_id: str, role: str, content: str,
                         model: str = None, metadata: Dict = None,
                         user_id: str = None) -> Optional[str]:
        """Add a message to conversation."""
        try:
            if not user_id:
                user_id = get_current_user_id()
            
            if not user_id:
                logger.error("No user ID provided for adding message")
                return None
            
            # Validate that user owns the conversation
            conversations = await self.get_user_conversations(user_id)
            if not any(conv['id'] == conversation_id for conv in conversations):
                logger.error(f"User {user_id} attempted to access conversation {conversation_id}")
                return None
            
            message_id = await supabase_manager.add_message(
                conversation_id=conversation_id,
                user_id=user_id,
                role=role,
                content=content,
                model=model,
                metadata=metadata or {}
            )
            
            if message_id:
                # Clear messages cache for this conversation
                cache_key = self._get_cache_key(user_id, f'messages:{conversation_id}')
                if cache_key in self._cache:
                    del self._cache[cache_key]
                
                # Clear conversations cache to update last_message_at
                cache_key = self._get_cache_key(user_id, 'conversations')
                if cache_key in self._cache:
                    del self._cache[cache_key]
                
                logger.info(f"Added message {message_id} to conversation {conversation_id}")
            
            return message_id
            
        except Exception as e:
            logger.error(f"Error adding message: {e}")
            return None
    
    async def update_conversation_title(self, conversation_id: str, new_title: str,
                                      user_id: str = None) -> bool:
        """Update conversation title."""
        try:
            if not user_id:
                user_id = get_current_user_id()
            
            if not user_id:
                logger.error("No user ID provided for updating conversation")
                return False
            
            # Validate ownership first
            conversations = await self.get_user_conversations(user_id)
            if not any(conv['id'] == conversation_id for conv in conversations):
                logger.error(f"User {user_id} attempted to update conversation {conversation_id}")
                return False
            
            client = await supabase_manager.get_client()
            
            result = await client.table('conversations')\
                .update({'title': new_title})\
                .eq('id', conversation_id)\
                .eq('user_id', user_id)\
                .execute()
            
            if result.data:
                # Clear cache
                cache_key = self._get_cache_key(user_id, 'conversations')
                if cache_key in self._cache:
                    del self._cache[cache_key]
                
                logger.info(f"Updated title for conversation {conversation_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error updating conversation title: {e}")
            return False
    
    async def delete_conversation(self, conversation_id: str,
                                user_id: str = None) -> bool:
        """Delete a conversation and all associated data."""
        try:
            if not user_id:
                user_id = get_current_user_id()
            
            if not user_id:
                logger.error("No user ID provided for deleting conversation")
                return False
            
            # Validate ownership first
            conversations = await self.get_user_conversations(user_id)
            if not any(conv['id'] == conversation_id for conv in conversations):
                logger.error(f"User {user_id} attempted to delete conversation {conversation_id}")
                return False
            
            client = await supabase_manager.get_client()
            
            # Mark as inactive instead of actual deletion (soft delete)
            result = await client.table('conversations')\
                .update({'is_active': False})\
                .eq('id', conversation_id)\
                .eq('user_id', user_id)\
                .execute()
            
            if result.data:
                # Clear all related caches
                cache_key = self._get_cache_key(user_id, 'conversations')
                if cache_key in self._cache:
                    del self._cache[cache_key]
                
                cache_key = self._get_cache_key(user_id, f'messages:{conversation_id}')
                if cache_key in self._cache:
                    del self._cache[cache_key]
                
                logger.info(f"Deleted conversation {conversation_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting conversation: {e}")
            return False
    
    async def get_conversation_stats(self, user_id: str = None) -> Dict:
        """Get conversation statistics for user."""
        try:
            if not user_id:
                user_id = get_current_user_id()
            
            if not user_id:
                return {}
            
            conversations = await self.get_user_conversations(user_id)
            
            total_messages = 0
            for conv in conversations:
                messages = await self.get_conversation_messages(conv['id'], user_id)
                total_messages += len(messages)
            
            return {
                'total_conversations': len(conversations),
                'total_messages': total_messages,
                'active_conversations': len([c for c in conversations if c.get('is_active', True)])
            }
            
        except Exception as e:
            logger.error(f"Error getting conversation stats: {e}")
            return {}
    
    def clear_cache(self, user_id: str = None):
        """Clear conversation cache for user."""
        if not user_id:
            user_id = get_current_user_id()
        
        if not user_id:
            return
        
        # Clear all cache entries for this user
        keys_to_remove = [key for key in self._cache.keys() if key.startswith(f"{user_id}:")]
        for key in keys_to_remove:
            del self._cache[key]
        
        logger.info(f"Cleared cache for user {user_id}")


# Global conversation manager
conversation_manager = ConversationManager()

# Convenience functions
def create_conversation(title: str, model: str = 'normal') -> Optional[str]:
    """Create a new conversation."""
    return run_async(conversation_manager.create_conversation(title, model))

def get_user_conversations() -> List[Dict]:
    """Get all conversations for current user."""
    return run_async(conversation_manager.get_user_conversations())

def get_conversation_messages(conversation_id: str) -> List[Dict]:
    """Get messages for a conversation."""
    return run_async(conversation_manager.get_conversation_messages(conversation_id))

def add_message(conversation_id: str, role: str, content: str,
               model: str = None, metadata: Dict = None) -> Optional[str]:
    """Add a message to conversation."""
    return run_async(conversation_manager.add_message(
        conversation_id, role, content, model, metadata
    ))

def update_conversation_title(conversation_id: str, new_title: str) -> bool:
    """Update conversation title."""
    return run_async(conversation_manager.update_conversation_title(conversation_id, new_title))

def delete_conversation(conversation_id: str) -> bool:
    """Delete a conversation."""
    return run_async(conversation_manager.delete_conversation(conversation_id))

def get_conversation_stats() -> Dict:
    """Get conversation statistics."""
    return run_async(conversation_manager.get_conversation_stats())

def clear_conversation_cache():
    """Clear conversation cache."""
    conversation_manager.clear_cache()