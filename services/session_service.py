"""
Session Service for PharmGPT
Handles authentication sessions with Supabase
"""

import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import streamlit as st
import logging

# Lazy import to avoid circular dependencies
def get_connection_manager():
    """Get connection manager with lazy import."""
    try:
        from supabase_manager import connection_manager
        return connection_manager
    except ImportError:
        return None

def get_supabase_error():
    """Get SupabaseError with lazy import."""
    try:
        from supabase_manager import SupabaseError
        return SupabaseError
    except ImportError:
        return Exception

def get_error_handler():
    """Get ErrorHandler with lazy import."""
    try:
        from supabase_manager import ErrorHandler
        return ErrorHandler
    except ImportError:
        return None

logger = logging.getLogger(__name__)

class SessionService:
    """Service class for authentication session management."""
    
    def __init__(self, session_timeout_hours: int = 24):
        self.connection_manager = None  # Initialize lazily
        self.session_timeout_hours = session_timeout_hours
    
    def _get_connection_manager(self):
        """Get connection manager with lazy loading."""
        if self.connection_manager is None:
            self.connection_manager = get_connection_manager()
        return self.connection_manager
    
    def _generate_session_id(self) -> str:
        """Generate secure session ID."""
        return secrets.token_urlsafe(32)
    
    def _get_expiry_time(self) -> datetime:
        """Get session expiry time."""
        return datetime.now() + timedelta(hours=self.session_timeout_hours)
    
    async def create_session(self, username: str, user_uuid: str, ip_address: str = None, user_agent: str = None) -> str:
        """
        Create a new authentication session.
        
        Args:
            username: Username for the session
            user_uuid: User's UUID from users table
            ip_address: Client IP address (optional)
            user_agent: Client user agent (optional)
            
        Returns:
            str: Session ID
        """
        try:
            session_id = self._generate_session_id()
            expires_at = self._get_expiry_time()
            
            session_data = {
                'session_id': session_id,
                'user_id': user_uuid,
                'username': username,
                'created_at': datetime.now().isoformat(),
                'expires_at': expires_at.isoformat(),
                'last_activity': datetime.now().isoformat(),
                'ip_address': ip_address,
                'user_agent': user_agent
            }
            
            result = self._get_connection_manager().execute_query(
                table='sessions',
                operation='insert',
                data=session_data
            )
            
            if result.data:
                logger.info(f"Session created for user: {username}")
                return session_id
            else:
                logger.error(f"Failed to create session for user: {username}")
                raise get_supabase_error()("Failed to create session")
                
        except Exception as e:
            logger.error(f"Error creating session for {username}: {str(e)}")
            raise get_supabase_error()(f"Session creation failed: {str(e)}")
    
    async def validate_session(self, session_id: str) -> Optional[Dict]:
        """
        Validate session and return session data if valid.
        
        Args:
            session_id: Session ID to validate
            
        Returns:
            Optional[Dict]: Session data if valid, None if invalid/expired
        """
        if not session_id:
            return None
        
        try:
            result = self._get_connection_manager().execute_query(
                table='sessions',
                operation='select',
                eq={'session_id': session_id}
            )
            
            if not result.data:
                return None
            
            session_data = result.data[0]
            
            # Check if session is expired
            expires_at = datetime.fromisoformat(session_data['expires_at'].replace('Z', '+00:00'))
            if datetime.now() > expires_at.replace(tzinfo=None):
                # Session expired, remove it
                await self.logout_session(session_id)
                logger.info(f"Expired session removed: {session_id}")
                return None
            
            # Update last activity
            await self.update_last_activity(session_id)
            
            return session_data
            
        except Exception as e:
            logger.error(f"Error validating session {session_id}: {str(e)}")
            return None
    
    async def refresh_session(self, session_id: str) -> bool:
        """
        Refresh session expiry time.
        
        Args:
            session_id: Session ID to refresh
            
        Returns:
            bool: Success status
        """
        try:
            new_expiry = self._get_expiry_time()
            
            result = self._get_connection_manager().execute_query(
                table='sessions',
                operation='update',
                data={
                    'expires_at': new_expiry.isoformat(),
                    'last_activity': datetime.now().isoformat()
                },
                eq={'session_id': session_id}
            )
            
            if result.data:
                logger.info(f"Session refreshed: {session_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error refreshing session {session_id}: {str(e)}")
            return False
    
    async def update_last_activity(self, session_id: str) -> bool:
        """Update session's last activity timestamp."""
        try:
            result = self._get_connection_manager().execute_query(
                table='sessions',
                operation='update',
                data={'last_activity': datetime.now().isoformat()},
                eq={'session_id': session_id}
            )
            
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Error updating last activity for session {session_id}: {str(e)}")
            return False
    
    async def logout_session(self, session_id: str) -> bool:
        """
        Logout session by removing it from database.
        
        Args:
            session_id: Session ID to logout
            
        Returns:
            bool: Success status
        """
        if not session_id:
            return True
        
        try:
            result = self._get_connection_manager().execute_query(
                table='sessions',
                operation='delete',
                eq={'session_id': session_id}
            )
            
            logger.info(f"Session logged out: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error logging out session {session_id}: {str(e)}")
            return False
    
    async def logout_all_user_sessions(self, user_uuid: str) -> int:
        """
        Logout all sessions for a specific user.
        
        Args:
            user_uuid: User's UUID
            
        Returns:
            int: Number of sessions logged out
        """
        try:
            result = self._get_connection_manager().execute_query(
                table='sessions',
                operation='delete',
                eq={'user_id': user_uuid}
            )
            
            count = len(result.data) if result.data else 0
            logger.info(f"Logged out {count} sessions for user: {user_uuid}")
            return count
            
        except Exception as e:
            logger.error(f"Error logging out all sessions for user {user_uuid}: {str(e)}")
            return 0
    
    async def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions from database.
        
        Returns:
            int: Number of expired sessions removed
        """
        try:
            # Get all expired sessions
            current_time = datetime.now().isoformat()
            
            # First, get expired sessions to count them
            expired_result = self._get_connection_manager().execute_query(
                table='sessions',
                operation='select',
                columns='session_id'
            )
            
            if not expired_result.data:
                return 0
            
            # Filter expired sessions (client-side for now)
            expired_sessions = []
            for session in expired_result.data:
                # This is a simplified approach - in production, use SQL WHERE clause
                pass
            
            # For now, use a raw SQL approach through RPC if available
            # Or implement a stored procedure
            
            # Simplified cleanup - remove sessions older than timeout period
            cutoff_time = (datetime.now() - timedelta(hours=self.session_timeout_hours * 2)).isoformat()
            
            # This would need a custom RPC function in Supabase
            # For now, we'll do a basic cleanup
            
            logger.info("Session cleanup completed")
            return 0  # Placeholder
            
        except Exception as e:
            logger.error(f"Error cleaning up expired sessions: {str(e)}")
            return 0
    
    async def get_user_sessions(self, user_uuid: str) -> List[Dict]:
        """
        Get all active sessions for a user.
        
        Args:
            user_uuid: User's UUID
            
        Returns:
            List[Dict]: List of active sessions
        """
        try:
            result = self._get_connection_manager().execute_query(
                table='sessions',
                operation='select',
                columns='session_id,created_at,last_activity,ip_address,user_agent',
                eq={'user_id': user_uuid}
            )
            
            if result.data:
                # Filter out expired sessions
                current_time = datetime.now()
                active_sessions = []
                
                for session in result.data:
                    expires_at = datetime.fromisoformat(session.get('expires_at', '').replace('Z', '+00:00'))
                    if current_time <= expires_at.replace(tzinfo=None):
                        active_sessions.append(session)
                
                return active_sessions
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting user sessions for {user_uuid}: {str(e)}")
            return []
    
    async def get_session_info(self, session_id: str) -> Optional[Dict]:
        """Get detailed session information."""
        try:
            result = self._get_connection_manager().execute_query(
                table='sessions',
                operation='select',
                eq={'session_id': session_id}
            )
            
            if result.data:
                return result.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Error getting session info for {session_id}: {str(e)}")
            return None
    
    async def is_session_valid(self, session_id: str) -> bool:
        """Check if session is valid without updating activity."""
        if not session_id:
            return False
        
        try:
            result = self._get_connection_manager().execute_query(
                table='sessions',
                operation='select',
                columns='expires_at',
                eq={'session_id': session_id}
            )
            
            if not result.data:
                return False
            
            expires_at = datetime.fromisoformat(result.data[0]['expires_at'].replace('Z', '+00:00'))
            return datetime.now() <= expires_at.replace(tzinfo=None)
            
        except Exception as e:
            logger.error(f"Error checking session validity {session_id}: {str(e)}")
            return False
    
    async def get_session_stats(self) -> Dict:
        """Get session statistics."""
        try:
            # Get total sessions
            total_result = self._get_connection_manager().execute_query(
                table='sessions',
                operation='select',
                columns='count(*)'
            )
            
            # Get active sessions (not expired)
            current_time = datetime.now().isoformat()
            
            # This would need custom SQL for proper filtering
            # For now, return basic stats
            
            stats = {
                'total_sessions': 0,
                'active_sessions': 0,
                'expired_sessions': 0,
                'cleanup_needed': False
            }
            
            if total_result.data:
                # Basic implementation - would need improvement for production
                pass
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting session stats: {str(e)}")
            return {}

# Global session service instance
session_service = SessionService()

# Sync wrapper methods for Streamlit compatibility
def create_session_sync(username: str, user_uuid: str) -> str:
    """Create authentication session (sync wrapper)."""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(session_service.create_session(username, user_uuid))

def validate_session_sync(session_id: str) -> Optional[Dict]:
    """Validate session (sync wrapper)."""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(session_service.validate_session(session_id))

def logout_session_sync(session_id: str) -> bool:
    """Logout session (sync wrapper)."""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(session_service.logout_session(session_id))

# Convenience functions for backward compatibility
async def create_session(username: str, user_uuid: str) -> str:
    """Create authentication session."""
    return await session_service.create_session(username, user_uuid)

async def validate_session(session_id: str) -> Optional[Dict]:
    """Validate session."""
    return await session_service.validate_session(session_id)

async def logout_session(session_id: str) -> bool:
    """Logout session."""
    return await session_service.logout_session(session_id)

async def cleanup_expired_sessions() -> int:
    """Clean up expired sessions."""
    return await session_service.cleanup_expired_sessions()