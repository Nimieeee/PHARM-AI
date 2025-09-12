"""
Conversation Service for PharmGPT
Handles chat conversations and messages with Supabase
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import streamlit as st
import logging

from supabase_manager import connection_manager, SupabaseError, ErrorHandler

logger = logging.getLogger(__name__)

class ConversationService:
    """Service class for conversation and message management."""
    
    def __init__(self):
        self.connection_manager = connection_manager
    
    def _generate_conversation_id(self) -> str:
        """Generate unique conversation ID."""
        return str(uuid.uuid4())
    
    def _validate_message(self, message: Dict) -> bool:
        """Validate message structure."""
        required_fields = ['role', 'content']
        return all(field in message for field in required_fields)
    
    async def create_conversation(self, user_uuid: str, title: str, model: str = None) -> str:
        """
        Create a new conversation.
        
        Args:
            user_uuid: User's UUID
            title: Conversation title
            model: AI model to use (optional)
            
        Returns:
            str: Conversation ID
        """
        # Set user context for RLS policies
        self.connection_manager.set_user_context(user_uuid)
        
        # Immediately use the simple method to avoid trigger issues
        logger.info("Using simple conversation creation to avoid trigger issues")
        try:
            return await self.create_conversation_simple(user_uuid, title, model)
        except Exception as simple_error:
            logger.error(f"Simple conversation creation failed: {str(simple_error)}")
            
            # If simple method fails, try the original approach as fallback
            try:
                logger.info("Trying original conversation creation as fallback...")
                conversation_id = self._generate_conversation_id()
                
                conversation_data = {
                    'conversation_id': conversation_id,
                    'user_uuid': user_uuid,  # Primary field
                    'user_id': user_uuid,    # Legacy compatibility
                    'title': title,
                    'model': model or 'meta-llama/llama-4-maverick-17b-128e-instruct',
                    'created_at': datetime.now().isoformat(),
                    'is_archived': False,
                    'message_count': 0
                }
                
                result = self.connection_manager.execute_query(
                    table='conversations',
                    operation='insert',
                    data=conversation_data
                )
                
                if result.data:
                    logger.info(f"Fallback conversation created: {conversation_id}")
                    return conversation_id
                else:
                    raise SupabaseError("Failed to create conversation")
                    
            except Exception as fallback_error:
                logger.error(f"All conversation creation methods failed: {str(fallback_error)}")
                raise SupabaseError(f"Conversation creation failed: {str(fallback_error)}")
    
    async def get_user_conversations(self, user_uuid: str, include_archived: bool = False, limit: int = 100) -> Dict:
        """
        Get all conversations for a user.
        
        Args:
            user_uuid: User's UUID
            include_archived: Whether to include archived conversations
            limit: Maximum number of conversations to return
            
        Returns:
            Dict: Conversations indexed by conversation_id
        """
        try:
            # Build query conditions
            eq_conditions = {'user_id': user_uuid}
            if not include_archived:
                eq_conditions['is_archived'] = False
            
            result = self.connection_manager.execute_query(
                table='conversations',
                operation='select',
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
        """
        Get a specific conversation.
        
        Args:
            user_uuid: User's UUID
            conversation_id: Conversation ID
            
        Returns:
            Optional[Dict]: Conversation data or None if not found
        """
        try:
            result = self.connection_manager.execute_query(
                table='conversations',
                operation='select',
                eq={
                    'user_id': user_uuid,
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
    
    async def update_conversation(self, user_uuid: str, conversation_id: str, data: Dict) -> bool:
        """
        Update conversation data.
        
        Args:
            user_uuid: User's UUID
            conversation_id: Conversation ID
            data: Data to update
            
        Returns:
            bool: Success status
        """
        try:
            # Remove fields that shouldn't be updated directly
            safe_data = {k: v for k, v in data.items() 
                        if k not in ['id', 'conversation_id', 'user_id', 'created_at']}
            
            if not safe_data:
                return False
            
            # Handle messages update
            if 'messages' in safe_data:
                # Ensure messages are properly formatted as JSON string for JSONB
                if isinstance(safe_data['messages'], list):
                    safe_data['messages'] = json.dumps(safe_data['messages'])
                safe_data['message_count'] = len(data['messages']) if isinstance(data['messages'], list) else 0
            
            safe_data['updated_at'] = datetime.now().isoformat()
            
            result = self.connection_manager.execute_query(
                table='conversations',
                operation='update',
                data=safe_data,
                eq={
                    'user_id': user_uuid,
                    'conversation_id': conversation_id
                }
            )
            
            if result.data:
                logger.info(f"Conversation updated: {conversation_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error updating conversation {conversation_id}: {str(e)}")
            return False
    
    async def delete_conversation(self, user_uuid: str, conversation_id: str) -> bool:
        """
        Delete a conversation permanently.
        
        Args:
            user_uuid: User's UUID
            conversation_id: Conversation ID
            
        Returns:
            bool: Success status
        """
        try:
            result = self.connection_manager.execute_query(
                table='conversations',
                operation='delete',
                eq={
                    'user_id': user_uuid,
                    'conversation_id': conversation_id
                }
            )
            
            logger.info(f"Conversation deleted: {conversation_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting conversation {conversation_id}: {str(e)}")
            return False
    
    async def archive_conversation(self, user_uuid: str, conversation_id: str) -> bool:
        """Archive a conversation (soft delete)."""
        return await self.update_conversation(
            user_uuid, 
            conversation_id, 
            {'is_archived': True}
        )
    
    async def unarchive_conversation(self, user_uuid: str, conversation_id: str) -> bool:
        """Unarchive a conversation."""
        return await self.update_conversation(
            user_uuid, 
            conversation_id, 
            {'is_archived': False}
        )
    
    async def add_message(self, user_uuid: str, conversation_id: str, message: Dict) -> bool:
        """
        Add a message to a conversation.
        
        Args:
            user_uuid: User's UUID
            conversation_id: Conversation ID
            message: Message data with role, content, timestamp
            
        Returns:
            bool: Success status
        """
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
    
    async def get_messages(self, user_uuid: str, conversation_id: str, limit: int = 50, offset: int = 0) -> List[Dict]:
        """
        Get messages from a conversation with pagination.
        
        Args:
            user_uuid: User's UUID
            conversation_id: Conversation ID
            limit: Maximum number of messages
            offset: Number of messages to skip
            
        Returns:
            List[Dict]: List of messages
        """
        try:
            conversation = await self.get_conversation(user_uuid, conversation_id)
            if not conversation:
                return []
            
            messages = conversation['messages']
            
            # Apply pagination
            start_idx = offset
            end_idx = offset + limit
            
            return messages[start_idx:end_idx]
            
        except Exception as e:
            logger.error(f"Error getting messages from conversation {conversation_id}: {str(e)}")
            return []
    
    async def update_conversation_title(self, user_uuid: str, conversation_id: str, title: str) -> bool:
        """Update conversation title."""
        return await self.update_conversation(
            user_uuid,
            conversation_id,
            {'title': title}
        )
    
    async def duplicate_conversation(self, user_uuid: str, conversation_id: str, new_title: str = None) -> Optional[str]:
        """
        Duplicate a conversation.
        
        Args:
            user_uuid: User's UUID
            conversation_id: Original conversation ID
            new_title: Title for the new conversation
            
        Returns:
            Optional[str]: New conversation ID or None if failed
        """
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
    
    async def search_conversations(self, user_uuid: str, query: str, limit: int = 20) -> List[Dict]:
        """
        Search conversations by title or content.
        
        Args:
            user_uuid: User's UUID
            query: Search query
            limit: Maximum results
            
        Returns:
            List[Dict]: Matching conversations
        """
        try:
            # Get all user conversations
            conversations = await self.get_user_conversations(user_uuid, include_archived=True)
            
            # Search in titles and messages (client-side for now)
            results = []
            query_lower = query.lower()
            
            for conv_id, conv_data in conversations.items():
                # Search in title
                if query_lower in conv_data['title'].lower():
                    results.append({
                        'conversation_id': conv_id,
                        'title': conv_data['title'],
                        'created_at': conv_data['created_at'],
                        'message_count': conv_data['message_count'],
                        'match_type': 'title'
                    })
                    continue
                
                # Search in messages
                for message in conv_data['messages']:
                    if query_lower in message.get('content', '').lower():
                        results.append({
                            'conversation_id': conv_id,
                            'title': conv_data['title'],
                            'created_at': conv_data['created_at'],
                            'message_count': conv_data['message_count'],
                            'match_type': 'message'
                        })
                        break
                
                if len(results) >= limit:
                    break
            
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Error searching conversations for user {user_uuid}: {str(e)}")
            return []
    
    async def get_conversation_stats(self, user_uuid: str) -> Dict:
        """Get conversation statistics for a user."""
        try:
            conversations = await self.get_user_conversations(user_uuid, include_archived=True)
            
            total_conversations = len(conversations)
            total_messages = sum(conv['message_count'] for conv in conversations.values())
            archived_count = sum(1 for conv in conversations.values() if conv.get('is_archived', False))
            
            # Find most recent conversation
            most_recent = None
            if conversations:
                most_recent_conv = max(
                    conversations.values(),
                    key=lambda x: x.get('updated_at', x['created_at'])
                )
                most_recent = most_recent_conv.get('updated_at', most_recent_conv['created_at'])
            
            return {
                'total_conversations': total_conversations,
                'active_conversations': total_conversations - archived_count,
                'archived_conversations': archived_count,
                'total_messages': total_messages,
                'avg_messages_per_conversation': total_messages / total_conversations if total_conversations > 0 else 0,
                'most_recent_activity': most_recent
            }
            
        except Exception as e:
            logger.error(f"Error getting conversation stats for user {user_uuid}: {str(e)}")
            return {}
    
    async def batch_update_conversations(self, user_uuid: str, updates: List[Dict]) -> int:
        """
        Batch update multiple conversations.
        
        Args:
            user_uuid: User's UUID
            updates: List of update dictionaries with conversation_id and data
            
        Returns:
            int: Number of successfully updated conversations
        """
        success_count = 0
        
        for update in updates:
            conversation_id = update.get('conversation_id')
            data = update.get('data', {})
            
            if conversation_id and data:
                if await self.update_conversation(user_uuid, conversation_id, data):
                    success_count += 1
        
        logger.info(f"Batch updated {success_count}/{len(updates)} conversations")
        return success_count


    async def create_conversation_simple(self, user_uuid: str, title: str, model: str = None) -> str:
        """
        Simple conversation creation using raw SQL to bypass triggers.
        Fallback method for when the main creation fails.
        """
        try:
            conversation_id = self._generate_conversation_id()
            model = model or 'meta-llama/llama-4-maverick-17b-128e-instruct'
            
            # Use raw SQL to bypass all triggers
            client = self.connection_manager.get_client()
            if not client:
                raise SupabaseError("No Supabase client available")
            
            # Raw SQL insert that bypasses triggers
            sql = """
            INSERT INTO conversations (
                conversation_id, user_id, title, model, 
                created_at, is_archived, messages, message_count
            ) VALUES (
                %s, %s, %s, %s, 
                NOW(), false, '[]'::jsonb, 0
            )
            """
            
            try:
                # Try using rpc to execute raw SQL
                result = client.rpc('exec_sql', {
                    'sql': sql,
                    'params': [conversation_id, user_uuid, title, model]
                }).execute()
                
                logger.info(f"Conversation created via raw SQL: {conversation_id}")
                return conversation_id
                
            except Exception as rpc_error:
                logger.warning(f"Raw SQL failed: {rpc_error}")
                
                # Fallback to minimal insert without messages field
                minimal_data = {
                    'conversation_id': conversation_id,
                    'user_uuid': user_uuid,  # Primary field
                    'user_id': user_uuid,    # Legacy compatibility
                    'title': title,
                    'model': model,
                    'created_at': datetime.now().isoformat(),
                    'is_archived': False
                }
                
                result = self.connection_manager.execute_query(
                    table='conversations',
                    operation='insert',
                    data=minimal_data
                )
                
                if result.data:
                    logger.info(f"Conversation created (minimal): {conversation_id}")
                    return conversation_id
                else:
                    raise SupabaseError("Failed to create minimal conversation")
                
        except Exception as e:
            logger.error(f"Error creating simple conversation: {str(e)}")
            raise SupabaseError(f"Simple conversation creation failed: {str(e)}")


# Global conversation service instance
conversation_service = ConversationService()

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