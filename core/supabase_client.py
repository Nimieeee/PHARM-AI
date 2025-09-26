"""
Clean Supabase Client Manager for PharmGPT
Handles authentication, sessions, and database operations with proper user isolation
"""

import os
import asyncio
import logging
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
import streamlit as st

# Configure logging
logger = logging.getLogger(__name__)

try:
    from supabase import create_client, create_async_client, Client, AsyncClient
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    Client = AsyncClient = type("Client", (), {})
    logger.error("Supabase not available. Install with: pip install supabase")

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class SupabaseManager:
    """Comprehensive Supabase manager with authentication and RAG support."""
    
    def __init__(self):
        if not SUPABASE_AVAILABLE:
            raise ImportError("Supabase library not available")
            
        self._client: Optional[AsyncClient] = None
        self._sync_client: Optional[Client] = None
        self.stats = {
            'queries': 0,
            'errors': 0,
            'sessions_created': 0,
            'auth_attempts': 0
        }
    
    def _get_credentials(self) -> Tuple[str, str]:
        """Get Supabase credentials from Streamlit secrets or environment."""
        # Try Streamlit secrets first
        try:
            url = st.secrets.get("SUPABASE_URL")
            key = st.secrets.get("SUPABASE_ANON_KEY")
            if url and key:
                return url, key
        except Exception:
            pass
        
        # Fallback to environment variables
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")
        
        if not url or not key:
            raise ValueError(
                "Missing Supabase credentials. Set SUPABASE_URL and SUPABASE_ANON_KEY "
                "in Streamlit secrets or environment variables."
            )
        
        return url, key
    
    async def get_client(self) -> AsyncClient:
        """Get or create async Supabase client."""
        if not self._client:
            url, key = self._get_credentials()
            self._client = await create_async_client(url, key)
        return self._client
    
    def get_sync_client(self) -> Client:
        """Get or create sync Supabase client."""
        if not self._sync_client:
            url, key = self._get_credentials()
            self._sync_client = create_client(url, key)
        return self._sync_client
    
    async def test_connection(self) -> bool:
        """Test database connection."""
        try:
            client = await self.get_client()
            result = await client.table('users').select('count').limit(1).execute()
            logger.info("✅ Database connection successful")
            return True
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False
    
    # ========================================
    # Authentication Methods
    # ========================================
    
    async def create_user(self, username: str, password: str, email: str = None) -> Tuple[bool, str, Optional[Dict]]:
        """Create a new user account."""
        try:
            self.stats['auth_attempts'] += 1
            client = await self.get_client()
            
            # Call the database function
            result = await client.rpc(
                'create_user_account',
                {
                    'p_username': username,
                    'p_password': password,
                    'p_email': email
                }
            ).execute()
            
            if result.data and len(result.data) > 0:
                user_data = result.data[0]
                if user_data.get('success'):
                    return True, user_data.get('message', 'User created'), {
                        'user_id': user_data.get('user_id'),
                        'username': username
                    }
                else:
                    return False, user_data.get('message', 'Failed to create user'), None
            
            return False, 'Unexpected response from server', None
            
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Error creating user: {e}")
            return False, f"Error creating account: {str(e)}", None
    
    async def authenticate_user(self, username: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
        """Authenticate user credentials."""
        try:
            self.stats['auth_attempts'] += 1
            client = await self.get_client()
            
            # Call the database function
            result = await client.rpc(
                'authenticate_user',
                {
                    'p_username': username,
                    'p_password': password
                }
            ).execute()
            
            if result.data and len(result.data) > 0:
                auth_data = result.data[0]
                if auth_data.get('success'):
                    return True, auth_data.get('message', 'Authentication successful'), {
                        'user_id': auth_data.get('user_id'),
                        'username': auth_data.get('username'),
                        'display_name': auth_data.get('display_name')
                    }
                else:
                    return False, auth_data.get('message', 'Authentication failed'), None
            
            return False, 'Unexpected response from server', None
            
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Authentication error: {e}")
            return False, f"Authentication error: {str(e)}", None
    
    async def create_session(self, user_id: str, device_info: Dict = None, 
                           ip_address: str = None, user_agent: str = None) -> Optional[Dict]:
        """Create a persistent session."""
        try:
            self.stats['sessions_created'] += 1
            client = await self.get_client()
            
            result = await client.rpc(
                'create_session',
                {
                    'p_user_id': user_id,
                    'p_device_info': device_info or {},
                    'p_ip_address': ip_address,
                    'p_user_agent': user_agent
                }
            ).execute()
            
            if result.data and len(result.data) > 0:
                session_data = result.data[0]
                return {
                    'session_token': session_data.get('session_token'),
                    'refresh_token': session_data.get('refresh_token'),
                    'expires_at': session_data.get('expires_at')
                }
            
            return None
            
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Error creating session: {e}")
            return None
    
    async def validate_session(self, session_token: str) -> Optional[Dict]:
        """Validate session token and return user info."""
        try:
            client = await self.get_client()
            
            result = await client.rpc(
                'validate_session_token',
                {'p_session_token': session_token}
            ).execute()
            
            if result.data and len(result.data) > 0:
                session_data = result.data[0]
                if session_data.get('valid'):
                    return {
                        'user_id': session_data.get('user_id'),
                        'username': session_data.get('username'),
                        'display_name': session_data.get('display_name')
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error validating session: {e}")
            return None
    
    # ========================================
    # Conversation Management
    # ========================================
    
    async def create_conversation(self, user_id: str, title: str,
                                model: str = 'normal') -> Optional[str]:
        """Create a new conversation."""
        try:
            self.stats['queries'] += 1
            client = await self.get_client()

            # Set user context for RLS
            await client.rpc('set_user_context', {'user_uuid_param': user_id}).execute()

            # Generate conversation ID
            import uuid
            conversation_id = str(uuid.uuid4())

            result = await client.table('conversations').insert({
                'id': conversation_id,
                'user_id': user_id,
                'title': title,
                'model': model
            }).execute()

            if result.data:
                return conversation_id

            return None

        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Error creating conversation: {e}")
            return None
    
    async def get_user_conversations(self, user_id: str) -> List[Dict]:
        """Get all conversations for a user."""
        try:
            self.stats['queries'] += 1
            client = await self.get_client()
            
            result = await client.table('conversations')\
                .select('*')\
                .eq('user_id', user_id)\
                .eq('is_active', True)\
                .order('updated_at', desc=True)\
                .execute()
            
            return result.data or []
            
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Error getting conversations: {e}")
            return []
    
    async def get_conversation_messages(self, conversation_id: str,
                                      user_id: str) -> List[Dict]:
        """Get messages for a specific conversation."""
        try:
            self.stats['queries'] += 1
            client = await self.get_client()

            # Set user context for RLS
            await client.rpc('set_user_context', {'user_uuid_param': user_id}).execute()

            result = await client.table('messages')\
                .select('*')\
                .eq('conversation_id', conversation_id)\
                .eq('user_id', user_id)\
                .order('message_index')\
                .execute()

            return result.data or []

        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Error getting messages: {e}")
            return []
    
    async def add_message(self, conversation_id: str, user_id: str,
                         role: str, content: str, model: str = None,
                         metadata: Dict = None) -> Optional[str]:
        """Add a message to conversation."""
        try:
            self.stats['queries'] += 1
            client = await self.get_client()

            # Set user context for RLS
            await client.rpc('set_user_context', {'user_uuid_param': user_id}).execute()

            # Get next message index
            count_result = await client.table('messages')\
                .select('message_index', count='exact')\
                .eq('conversation_id', conversation_id)\
                .execute()

            message_index = len(count_result.data)

            # Insert message
            result = await client.table('messages').insert({
                'conversation_id': conversation_id,
                'user_id': user_id,
                'role': role,
                'content': content,
                'model': model,
                'message_index': message_index,
                'metadata': metadata or {}
            }).execute()

            if result.data:
                return result.data[0]['id']

            return None

        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Error adding message: {e}")
            return None
    
    # ========================================
    # Document & RAG Methods
    # ========================================
    
    async def save_document(self, conversation_id: str, user_id: str,
                          filename: str, file_type: str, 
                          file_size: int, content_preview: str = None) -> Optional[str]:
        """Save document metadata."""
        try:
            self.stats['queries'] += 1
            client = await self.get_client()
            
            result = await client.table('documents').insert({
                'conversation_id': conversation_id,
                'user_id': user_id,
                'filename': filename,
                'file_type': file_type,
                'file_size': file_size,
                'content_preview': content_preview,
                'upload_status': 'completed',
                'processing_status': 'pending'
            }).execute()
            
            if result.data:
                return result.data[0]['id']
            
            return None
            
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Error saving document: {e}")
            return None
    
    async def save_document_chunks(self, chunks: List[Dict]) -> bool:
        """Save document chunks with embeddings."""
        try:
            self.stats['queries'] += 1
            client = await self.get_client()
            
            # Insert chunks in batches
            batch_size = 100
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
                await client.table('document_chunks').insert(batch).execute()
            
            return True
            
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Error saving document chunks: {e}")
            return False
    
    async def search_documents(self, query_embedding: List[float], 
                             user_id: str, conversation_id: str = None,
                             similarity_threshold: float = 0.7,
                             limit: int = 10) -> List[Dict]:
        """Search documents using vector similarity."""
        try:
            self.stats['queries'] += 1
            client = await self.get_client()
            
            result = await client.rpc(
                'search_documents',
                {
                    'p_query_embedding': query_embedding,
                    'p_user_id': user_id,
                    'p_conversation_id': conversation_id,
                    'p_similarity_threshold': similarity_threshold,
                    'p_limit': limit
                }
            ).execute()
            
            return result.data or []
            
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Error searching documents: {e}")
            return []
    
    async def get_conversation_context(self, conversation_id: str, 
                                     user_id: str) -> List[Dict]:
        """Get all document chunks for a conversation."""
        try:
            self.stats['queries'] += 1
            client = await self.get_client()
            
            result = await client.rpc(
                'get_conversation_context',
                {
                    'p_conversation_id': conversation_id,
                    'p_user_id': user_id
                }
            ).execute()
            
            return result.data or []
            
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Error getting conversation context: {e}")
            return []
    
    async def update_document_status(self, document_id: str, 
                                   processing_status: str, 
                                   chunk_count: int = 0) -> bool:
        """Update document processing status."""
        try:
            self.stats['queries'] += 1
            client = await self.get_client()
            
            await client.table('documents')\
                .update({
                    'processing_status': processing_status,
                    'chunk_count': chunk_count
                })\
                .eq('id', document_id)\
                .execute()
            
            return True
            
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Error updating document status: {e}")
            return False
    
    # ========================================
    # Utility Methods
    # ========================================
    
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions."""
        try:
            client = await self.get_client()
            
            result = await client.rpc('cleanup_expired_sessions').execute()
            
            if result.data:
                return result.data
            
            return 0
            
        except Exception as e:
            logger.error(f"Error cleaning up sessions: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get manager statistics."""
        return {
            'stats': self.stats.copy(),
            'timestamp': datetime.now().isoformat(),
            'supabase_available': SUPABASE_AVAILABLE
        }


# Global instance
supabase_manager = SupabaseManager()

# Convenience functions
async def get_client() -> AsyncClient:
    """Get async Supabase client."""
    return await supabase_manager.get_client()

def get_sync_client() -> Client:
    """Get sync Supabase client."""
    return supabase_manager.get_sync_client()

async def test_connection() -> bool:
    """Test database connection."""
    return await supabase_manager.test_connection()

def get_stats() -> Dict[str, Any]:
    """Get connection statistics."""
    return supabase_manager.get_stats()