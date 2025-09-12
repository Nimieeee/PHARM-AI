"""
User Service for PharmGPT
Handles all user account management operations with Supabase
"""

import hashlib
import secrets
import uuid
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import streamlit as st
import logging

logger = logging.getLogger(__name__)

def get_supabase_client():
    """Lazy import to avoid circular dependencies"""
    from supabase_manager import get_supabase_client as _get_client
    return _get_client()

# User data cache to prevent duplicate database calls
_user_cache = {}
_user_cache_timeout = 60  # Cache user data for 60 seconds

class UserService:
    """Service class for user account management operations."""
    
    def __init__(self):
        self.supabase = get_supabase_client()
    
    def _hash_password(self, password: str, salt: str = None) -> Tuple[str, str]:
        """Hash password with salt for secure storage."""
        if salt is None:
            salt = secrets.token_hex(32)
        
        # Use SHA-256 with salt for password hashing
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return password_hash, salt
    
    def _generate_user_id(self, username: str) -> str:
        """Generate unique user ID from username."""
        return hashlib.md5(username.encode()).hexdigest()
    
    def create_user(self, username: str, password: str, email: str = None) -> Tuple[bool, str]:
        """
        Create a new user account.
        
        Args:
            username: Unique username
            password: Plain text password (will be hashed)
            email: Optional email address
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            if not self.supabase:
                return False, "Database connection not available"
                
            # Validate input
            if not username or len(username) < 3:
                return False, "Username must be at least 3 characters long"
            
            if not password or len(password) < 6:
                return False, "Password must be at least 6 characters long"
            
            # Check if username already exists
            existing_user = self.get_user_by_username(username)
            if existing_user:
                return False, "Username already exists"
            
            # Hash password
            password_hash, salt = self._hash_password(password)
            user_id = self._generate_user_id(username)
            
            # Create user record
            user_data = {
                'username': username,
                'password_hash': password_hash,
                'salt': salt,
                'user_id': user_id,
                'is_active': True
            }
            
            # Only add email if provided (optional field)
            if email:
                user_data['email'] = email
            
            result = self.supabase.table('users').insert(user_data).execute()
            
            if result.data:
                logger.info(f"User created successfully: {username}")
                return True, "Account created successfully"
            else:
                logger.error(f"Failed to create user: {username}")
                return False, "Failed to create account"
                
        except Exception as e:
            logger.error(f"Error creating user {username}: {str(e)}")
            if "duplicate key" in str(e).lower() or "unique" in str(e).lower():
                return False, "Username already exists"
            return False, f"Error creating account: {str(e)}"
    
    def authenticate_user(self, username: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Authenticate user credentials.
        
        Args:
            username: Username to authenticate
            password: Plain text password
            
        Returns:
            Tuple of (success: bool, message: str, user_data: Optional[Dict])
        """
        logger.info(f"🔐 USER_SERVICE.AUTHENTICATE_USER called for user: {username}")
        
        try:
            if not self.supabase:
                logger.error("❌ No Supabase client available")
                return False, "Database connection not available", None
                
            # Get user by username
            logger.info(f"👤 Fetching user data for: {username}")
            user = self.get_user_by_username(username)
            if not user:
                logger.warning(f"👤 User not found: {username}")
                return False, "Username not found", None
            
            # Check if user is active
            if not user.get('is_active', True):
                logger.warning(f"🚫 User account disabled: {username}")
                return False, "Account is disabled", None
            
            # Verify password
            password_hash, _ = self._hash_password(password, user['salt'])
            
            if password_hash == user['password_hash']:
                # Update last login
                logger.info(f"🔄 Updating last login for: {username}")
                self.update_last_login(user['id'])
                
                logger.info(f"✅ User authenticated successfully: {username}")
                return True, "Authentication successful", user
            else:
                logger.warning(f"❌ Invalid password for user: {username}")
                return False, "Invalid password", None
                
        except Exception as e:
            logger.error(f"💥 Error authenticating user {username}: {str(e)}")
            return False, f"Authentication error: {str(e)}", None
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user by username with caching."""
        import time
        
        logger.info(f"🔍 GET_USER_BY_USERNAME called for: {username}")
        
        # Check cache first
        cache_key = f"user_{username}"
        current_time = time.time()
        
        if cache_key in _user_cache:
            user_data, timestamp = _user_cache[cache_key]
            if current_time - timestamp < _user_cache_timeout:
                logger.info(f"💾 Using cached user data for: {username}")
                return user_data
            else:
                logger.info("⏰ User cache expired, fetching fresh...")
                del _user_cache[cache_key]
        
        try:
            if not self.supabase:
                logger.error("❌ No Supabase client available")
                return None
                
            result = self.supabase.table('users').select('*').eq('username', username).execute()
            
            if result.data:
                user_data = result.data[0]
                # Cache the user data
                _user_cache[cache_key] = (user_data, current_time)
                logger.info(f"✅ User found and cached: {username}")
                return user_data
            logger.info(f"❌ User not found: {username}")
            return None
            
        except Exception as e:
            logger.error(f"💥 Error getting user by username {username}: {str(e)}")
            return None
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Get user by user_id (legacy compatibility)."""
        try:
            if not self.supabase:
                return None
                
            result = self.supabase.table('users').select('*').eq('user_id', user_id).execute()
            
            if result.data:
                return result.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Error getting user by ID {user_id}: {str(e)}")
            return None
    
    async def get_user_by_uuid(self, uuid_id: str) -> Optional[Dict]:
        """Get user by UUID (primary key)."""
        try:
            result = self.connection_manager.execute_query(
                table='users',
                operation='select',
                eq={'id': uuid_id}
            )
            
            if result.data:
                return result.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Error getting user by UUID {uuid_id}: {str(e)}")
            return None
    
    async def update_user_profile(self, user_id: str, data: Dict) -> bool:
        """
        Update user profile information.
        
        Args:
            user_id: User ID to update
            data: Dictionary of fields to update
            
        Returns:
            bool: Success status
        """
        try:
            # Remove sensitive fields that shouldn't be updated directly
            safe_data = {k: v for k, v in data.items() 
                        if k not in ['id', 'password_hash', 'salt', 'user_id', 'created_at']}
            
            if not safe_data:
                return False
            
            safe_data['updated_at'] = datetime.now().isoformat()
            
            result = self.connection_manager.execute_query(
                table='users',
                operation='update',
                data=safe_data,
                eq={'user_id': user_id}
            )
            
            if result.data:
                logger.info(f"User profile updated: {user_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error updating user profile {user_id}: {str(e)}")
            return False
    
    async def update_password(self, user_id: str, old_password: str, new_password: str) -> Tuple[bool, str]:
        """
        Update user password.
        
        Args:
            user_id: User ID
            old_password: Current password for verification
            new_password: New password
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Get user data
            user = await self.get_user_by_id(user_id)
            if not user:
                return False, "User not found"
            
            # Verify old password
            old_hash, _ = self._hash_password(old_password, user['salt'])
            if old_hash != user['password_hash']:
                return False, "Current password is incorrect"
            
            # Validate new password
            if len(new_password) < 6:
                return False, "New password must be at least 6 characters long"
            
            # Hash new password
            new_hash, new_salt = self._hash_password(new_password)
            
            # Update password
            result = self.connection_manager.execute_query(
                table='users',
                operation='update',
                data={
                    'password_hash': new_hash,
                    'salt': new_salt,
                    'updated_at': datetime.now().isoformat()
                },
                eq={'user_id': user_id}
            )
            
            if result.data:
                logger.info(f"Password updated for user: {user_id}")
                return True, "Password updated successfully"
            return False, "Failed to update password"
            
        except Exception as e:
            logger.error(f"Error updating password for user {user_id}: {str(e)}")
            return False, "Error updating password"
    
    def update_last_login(self, uuid_id: str) -> bool:
        """Update user's last login timestamp."""
        try:
            if not self.supabase:
                return False
                
            result = self.supabase.table('users').update({
                'last_login': datetime.now().isoformat()
            }).eq('id', uuid_id).execute()
            
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Error updating last login for user {uuid_id}: {str(e)}")
            return False
    
    async def deactivate_user(self, user_id: str) -> bool:
        """Deactivate user account (soft delete)."""
        try:
            result = self.connection_manager.execute_query(
                table='users',
                operation='update',
                data={
                    'is_active': False,
                    'updated_at': datetime.now().isoformat()
                },
                eq={'user_id': user_id}
            )
            
            if result.data:
                logger.info(f"User deactivated: {user_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error deactivating user {user_id}: {str(e)}")
            return False
    
    async def delete_user(self, user_id: str) -> bool:
        """
        Permanently delete user account and all associated data.
        WARNING: This is irreversible!
        """
        try:
            # This will cascade delete all related data due to foreign key constraints
            result = self.connection_manager.execute_query(
                table='users',
                operation='delete',
                eq={'user_id': user_id}
            )
            
            if result.data:
                logger.info(f"User permanently deleted: {user_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error deleting user {user_id}: {str(e)}")
            return False
    
    async def get_user_stats(self, user_id: str) -> Optional[Dict]:
        """Get user statistics from the user_stats view."""
        try:
            # First get the user's UUID
            user = await self.get_user_by_id(user_id)
            if not user:
                return None
            
            result = self.connection_manager.execute_query(
                table='user_stats',
                operation='select',
                eq={'id': user['id']}
            )
            
            if result.data:
                return result.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Error getting user stats for {user_id}: {str(e)}")
            return None
    
    async def list_users(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        """List all users (admin function)."""
        try:
            result = self.connection_manager.execute_query(
                table='users',
                operation='select',
                columns='id,username,email,created_at,last_login,is_active',
                limit=limit
            )
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Error listing users: {str(e)}")
            return []
    
    async def search_users(self, query: str, limit: int = 20) -> List[Dict]:
        """Search users by username or email."""
        try:
            # This would require a more complex query with ILIKE
            # For now, we'll do a simple filter
            result = self.connection_manager.execute_query(
                table='users',
                operation='select',
                columns='id,username,email,created_at,is_active',
                limit=limit
            )
            
            if result.data:
                # Filter results client-side (not ideal for large datasets)
                filtered = [
                    user for user in result.data
                    if query.lower() in user.get('username', '').lower() or
                       query.lower() in user.get('email', '').lower()
                ]
                return filtered
            
            return []
            
        except Exception as e:
            logger.error(f"Error searching users: {str(e)}")
            return []

# Global user service instance
user_service = UserService()

# Convenience functions for backward compatibility
def create_user(username: str, password: str, email: str = None) -> Tuple[bool, str]:
    """Create user account."""
    return user_service.create_user(username, password, email)

def authenticate_user(username: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
    """Authenticate user."""
    return user_service.authenticate_user(username, password)

def get_user_by_id(user_id: str) -> Optional[Dict]:
    """Get user by ID."""
    return user_service.get_user_by_id(user_id)