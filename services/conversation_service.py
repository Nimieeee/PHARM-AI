"""
Clean Conversation Service for PharmGPT
Simple, reliable conversation and message management using clean supabase manager
"""

import json
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Optional

# Configure logging
logger = logging.getLogger(__name__)

class ConversationService:
    """Simple conversation service using the clean supabase manager."""
    
    def __init__(self):
        # Import here to avoid circular imports
        from supabase_manager import connection_manager
        self.db = connection_manager
    
    def _generate_conversation_id(self) -> str:
        """Generate unique conversation ID."""
        return str(uuid.uuid4())
    
    def _validate_message(self, message: Dict) -> bool:
        """Validate message structure."""
        required_fields = ['role', 'content']
        return all(field in message for field in required_fields)
    
    async def create_conversation(self, user_uuid: str, title: str, model: str = None) -> str:
        """Create a new conversation."""
        # Validate user_uuid
        if not user_uuid or user_uuid.strip() == '':
            logger.error(f"Invalid user_uuid provided: '{user_uuid}'")
            raise ValueError("User UUID cannot be null or empty")
        
        conversation_id = self._generate_conversation_id()
        
        conversation_data = {
            'conversation_id': conversation_id,
            'user_uuid': user_uuid,
            'title': title,
            'model': model or 'meta-llama/llama-4-maverick-17b-128e-instruct',
            'created_at': datetime.now().isoformat(),
            'is_archived': False,
            'messages': json.dumps([])  # Initialize with empty messages array
        }
        
        logger.info(f"Creating conversation with user_uuid: '{user_uuid}'")
        
        try:
            result = await self.db.execute_query(
                'conversations',
                'insert',
                data=conversation_data
            )
            
            if result.data:
                logger.info(f"Conversation created successfully: {conversation_id}")
                return conversation_id
            else:
                logger.error("No data returned from conversation insert")
                raise Exception("Failed to create conversation - no data returned")
                
        except Exception as e:
            logger.error(f"Conversation creation failed: {str(e)}")
            raise Exception(f"Conversation creation failed: {str(e)}")
    
    async def get_user_conversations(self, user_uuid: str, include_archived: bool = False, limit: int = 100) -> Dict:
        """Get all conversations for a user."""
        try:
            eq_conditions = {'user_uuid': user_uuid}
            if not include_archived:
                eq_conditions['is_archived'] = False
            
            result = await self.db.execute_query(
                'conversations',
                'select',
                eq=eq_conditions,
                limit=limit,
                order='updated_at.desc'
            )
            
            conversations = {}
            if result.data:
                for conv in result.data:
                    # Handle messages as array or JSON string
                    messages = conv['messages'] if isinstance(conv['messages'], list) else (json.loads(conv['messages']) if conv['messages'] else [])
                    
                    conversations[conv['conversation_id']] = {
                        'title': conv['title'],
                        'messages': messages,
                        'created_at': conv['created_at'],
                        'updated_at': conv.get('updated_at', conv['created_at']),
                        'model': conv.get('model', 'meta-llama/llama-4-maverick-17b-128e-instruct'),
                        'message_count': conv.get('message_count', len(messages)),
                        'is_archived': conv.get('is_archived', False)
                    }
            
            logger.info(f"Retrieved {len(conversations)} conversations for user: {user_uuid}")
            return conversations
            
        except Exception as e:
            logger.error(f"Error getting conversations for user {user_uuid}: {str(e)}")
            return {}
    
    async def get_conversation(self, user_uuid: str, conversation_id: str) -> Optional[Dict]:
        """Get a specific conversation."""
        try:
            result = await self.db.execute_query(
                'conversations',
                'select',
                eq={
                    'user_uuid': user_uuid,
                    'conversation_id': conversation_id
                }
            )
            
            if result.data:
                conv = result.data[0]
                messages = conv['messages'] if isinstance(conv['messages'], list) else (json.loads(conv['messages']) if conv['messages'] else [])
                
                return {
                    'conversation_id': conv['conversation_id'],
                    'title': conv['title'],
                    'messages': messages,
                    'created_at': conv['created_at'],
                    'updated_at': conv.get('updated_at', conv['created_at']),
                    'model': conv.get('model', 'meta-llama/llama-4-maverick-17b-128e-instruct'),
                    'message_count': conv.get('message_count', len(messages)),
                    'is_archived': conv.get('is_archived', False)
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting conversation {conversation_id} for user {user_uuid}: {str(e)}")
            return None
    
    async def add_message(self, user_uuid: str, conversation_id: str, message: Dict) -> bool:
        """Add a message to a conversation."""
        try:
            # Validate message
            if not self._validate_message(message):
                logger.error(f"Invalid message format: {message}")
                return False
            
            # Add timestamp if not present
            if 'timestamp' not in message:
                message['timestamp'] = datetime.now().isoformat()
            
            # Get current conversation
            conversation = await self.get_conversation(user_uuid, conversation_id)
            if not conversation:
                logger.error(f"Conversation not found: {conversation_id}")
                return False
            
            # Add message to conversation
            messages = conversation['messages']
            messages.append(message)
            
            # Update conversation with new messages
            return await self.update_conversation(
                user_uuid,
                conversation_id,
                {'messages': messages}
            )
            
        except Exception as e:
            logger.error(f"Error adding message to conversation {conversation_id}: {str(e)}")
            return False
    
    async def update_conversation(self, user_uuid: str, conversation_id: str, data: Dict) -> bool:
        """Update conversation data - SECURITY ENHANCED."""
        try:
            # SECURITY FIX: First verify the conversation exists and belongs to the user
            existing_conversation = await self.get_conversation(user_uuid, conversation_id)
            if not existing_conversation:
                logger.warning(f"SECURITY: Attempted to update non-existent or unauthorized conversation: {conversation_id} by user: {user_uuid}")
                return False
            
            # Remove fields that shouldn't be updated directly
            safe_data = {k: v for k, v in data.items() 
                        if k not in ['id', 'conversation_id', 'user_id', 'user_uuid', 'created_at']}
            
            if not safe_data:
                return False
            
            # Handle messages update
            if 'messages' in safe_data:
                # Ensure messages are properly formatted as JSON string for JSONB
                if isinstance(safe_data['messages'], list):
                    safe_data['messages'] = json.dumps(safe_data['messages'])
                safe_data['message_count'] = len(data['messages']) if isinstance(data['messages'], list) else 0
            
            safe_data['updated_at'] = datetime.now().isoformat()
            
            result = await self.db.execute_query(
                'conversations',
                'update',
                data=safe_data,
                eq={
                    'user_uuid': user_uuid,
                    'conversation_id': conversation_id
                }
            )
            
            if result.data:
                logger.info(f"Conversation updated: {conversation_id} by user: {user_uuid}")
                return True
            else:
                logger.warning(f"SECURITY: Update operation returned no data for conversation: {conversation_id}")
                return False
            
        except Exception as e:
            logger.error(f"Error updating conversation {conversation_id}: {str(e)}")
            return False
    
    async def delete_conversation(self, user_uuid: str, conversation_id: str) -> bool:
        """Delete a conversation permanently - SECURITY ENHANCED."""
        try:
            # SECURITY FIX: First verify the conversation exists and belongs to the user
            existing_conversation = await self.get_conversation(user_uuid, conversation_id)
            if not existing_conversation:
                logger.warning(f"SECURITY: Attempted to delete non-existent or unauthorized conversation: {conversation_id} by user: {user_uuid}")
                return False
            
            # Now delete the conversation
            result = await self.db.execute_query(
                'conversations',
                'delete',
                eq={
                    'user_uuid': user_uuid,
                    'conversation_id': conversation_id
                }
            )
            
            # Verify deletion was successful by checking affected rows
            if result.data is not None:
                logger.info(f"Conversation successfully deleted: {conversation_id} by user: {user_uuid}")
                return True
            else:
                logger.warning(f"SECURITY: Delete operation returned no data for conversation: {conversation_id}")
                return False
            
        except Exception as e:
            logger.error(f"Error deleting conversation {conversation_id}: {str(e)}")
            return False
    
    async def update_conversation_title(self, user_uuid: str, conversation_id: str, title: str) -> bool:
        """Update conversation title."""
        try:
            result = await self.db.execute_query(
                'conversations',
                'update',
                data={
                    'title': title,
                    'updated_at': datetime.now().isoformat()
                },
                eq={
                    'user_uuid': user_uuid,
                    'conversation_id': conversation_id
                }
            )
            
            if result.data:
                logger.info(f"Conversation title updated: {conversation_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error updating conversation title {conversation_id}: {str(e)}")
            return False
    
    async def duplicate_conversation(self, user_uuid: str, conversation_id: str, new_title: str = None) -> Optional[str]:
        """Duplicate a conversation."""
        try:
            # Get original conversation
            original = await self.get_conversation(user_uuid, conversation_id)
            if not original:
                return None
            
            # Create new conversation
            title = new_title or f"Copy of {original['title']}"
            new_conversation_id = await self.create_conversation(
                user_uuid,
                title,
                original['model']
            )
            
            # Copy messages if any
            if original['messages']:
                await self.update_conversation(
                    user_uuid,
                    new_conversation_id,
                    {'messages': original['messages']}
                )
            
            logger.info(f"Conversation duplicated: {conversation_id} -> {new_conversation_id}")
            return new_conversation_id
            
        except Exception as e:
            logger.error(f"Error duplicating conversation {conversation_id}: {str(e)}")
            return None

# Global conversation service instance
conversation_service = ConversationService()

# Sync wrapper methods for Streamlit compatibility
def run_async_operation(coro):
    """Run async operation with proper event loop handling."""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(coro)

def create_conversation_sync(user_uuid: str, title: str, model: str = None) -> str:
    """Create new conversation (sync wrapper)."""
    return run_async_operation(conversation_service.create_conversation(user_uuid, title, model))

def get_user_conversations_sync(user_uuid: str, include_archived: bool = False, limit: int = 100) -> Dict:
    """Get user conversations (sync wrapper)."""
    return run_async_operation(conversation_service.get_user_conversations(user_uuid, include_archived, limit))

def update_conversation_sync(user_uuid: str, conversation_id: str, data: Dict) -> bool:
    """Update conversation (sync wrapper)."""
    return run_async_operation(conversation_service.update_conversation(user_uuid, conversation_id, data))

def add_message_sync(user_uuid: str, conversation_id: str, message: Dict) -> bool:
    """Add message to conversation (sync wrapper)."""
    return run_async_operation(conversation_service.add_message(user_uuid, conversation_id, message))

def update_conversation_title_sync(user_uuid: str, conversation_id: str, title: str) -> bool:
    """Update conversation title (sync wrapper)."""
    return run_async_operation(conversation_service.update_conversation_title(user_uuid, conversation_id, title))

def delete_conversation_sync(user_uuid: str, conversation_id: str) -> bool:
    """Delete conversation (sync wrapper)."""
    return run_async_operation(conversation_service.delete_conversation(user_uuid, conversation_id))

def duplicate_conversation_sync(user_uuid: str, conversation_id: str, new_title: str = None) -> Optional[str]:
    """Duplicate conversation (sync wrapper)."""
    return run_async_operation(conversation_service.duplicate_conversation(user_uuid, conversation_id, new_title))

# Convenience functions for backward compatibility
async def create_conversation(user_uuid: str, title: str) -> str:
    """Create new conversation."""
    return await conversation_service.create_conversation(user_uuid, title)

async def get_user_conversations(user_uuid: str) -> Dict:
    """Get user conversations."""
    return await conversation_service.get_user_conversations(user_uuid)

async def add_message(user_uuid: str, conversation_id: str, message: Dict) -> bool:
    """Add message to conversation."""
    return await conversation_service.add_message(user_uuid, conversation_id, message)