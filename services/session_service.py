"""
Clean Session Service for PharmGPT
Simple, reliable session management using clean supabase manager
"""

import secrets
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional

# Configure logging
logger = logging.getLogger(__name__)

class SessionService:
    """Simple session service using the clean supabase manager."""
    
    def __init__(self, session_timeout_hours: int = 24):
        # Import here to avoid circular imports
        from supabase_manager import connection_manager
        self.db = connection_manager
        self.session_timeout_hours = session_timeout_hours
    
    def _generate_session_id(self) -> str:
        """Generate a secure session ID."""
        return secrets.token_urlsafe(32)
    
    async def create_session(self, username: str, user_uuid: str) -> str:
        """Create a new session for a user."""
        try:
            session_id = self._generate_session_id()
            expires_at = datetime.now() + timedelta(hours=self.session_timeout_hours)
            
            session_data = {
                'session_id': session_id,
                'username': username,
                'user_uuid': user_uuid,
                'created_at': datetime.now().isoformat(),
                'expires_at': expires_at.isoformat(),
                'is_active': True
            }
            
            result = await self.db.execute_query(
                'sessions',
                'insert',
                data=session_data
            )
            
            if result.data:
                logger.info(f"Session created for user: {username}")
                return session_id
            else:
                logger.error(f"Failed to create session for user: {username}")
                return ""
                
        except Exception as e:
            logger.error(f"Error creating session for {username}: {str(e)}")
            return ""
    
    async def validate_session(self, session_id: str) -> Optional[Dict]:
        """Validate a session and return session data if valid."""
        try:
            result = await self.db.execute_query(
                'sessions',
                'select',
                eq={
                    'session_id': session_id,
                    'is_active': True
                }
            )
            
            if result.data:
                session = result.data[0]
                
                # Check if session has expired
                expires_at = datetime.fromisoformat(session['expires_at'])
                if datetime.now() > expires_at:
                    # Session expired, deactivate it
                    await self.logout_session(session_id)
                    logger.info(f"Session expired: {session_id}")
                    return None
                
                logger.info(f"Session validated: {session_id}")
                return session
            
            logger.warning(f"Session not found or inactive: {session_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error validating session {session_id}: {str(e)}")
            return None
    
    async def logout_session(self, session_id: str) -> bool:
        """Logout a session by marking it as inactive."""
        try:
            result = await self.db.execute_query(
                'sessions',
                'update',
                data={
                    'is_active': False,
                    'logged_out_at': datetime.now().isoformat()
                },
                eq={'session_id': session_id}
            )
            
            if result.data:
                logger.info(f"Session logged out: {session_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error logging out session {session_id}: {str(e)}")
            return False
    
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions."""
        try:
            # This would require a more complex query
            # For now, we'll rely on the validation check
            logger.info("Session cleanup completed")
            return 0
            
        except Exception as e:
            logger.error(f"Error cleaning up sessions: {str(e)}")
            return 0

# Global session service instance
session_service = SessionService()

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

def create_session_sync(username: str, user_uuid: str) -> str:
    """Create session (sync wrapper)."""
    return run_async_operation(session_service.create_session(username, user_uuid))

def validate_session_sync(session_id: str) -> Optional[Dict]:
    """Validate session (sync wrapper)."""
    return run_async_operation(session_service.validate_session(session_id))

def logout_session_sync(session_id: str) -> bool:
    """Logout session (sync wrapper)."""
    return run_async_operation(session_service.logout_session(session_id))

# Convenience functions for backward compatibility
async def create_session(username: str, user_uuid: str) -> str:
    """Create session."""
    return await session_service.create_session(username, user_uuid)

async def validate_session(session_id: str) -> Optional[Dict]:
    """Validate session."""
    return await session_service.validate_session(session_id)

async def logout_session(session_id: str) -> bool:
    """Logout session."""
    return await session_service.logout_session(session_id)