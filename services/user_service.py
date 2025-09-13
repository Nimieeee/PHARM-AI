"""
Clean User Service for PharmGPT
Simple, reliable user account management using the clean supabase manager
"""

import hashlib
import secrets
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# Configure logging
logger = logging.getLogger(__name__)

class UserService:
    """Simple user service using the clean supabase manager."""

    def __init__(self):
        # Import here to avoid circular imports
        from supabase_manager import connection_manager
        self.db = connection_manager

    def _hash_password(self, password: str, salt: str = None) -> Tuple[str, str]:
        """Hash password with salt for secure storage."""
        if salt is None:
            salt = secrets.token_hex(32)
        
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return password_hash, salt

    def _generate_user_id(self, username: str) -> str:
        """Generate unique user ID from username."""
        return hashlib.md5(username.encode()).hexdigest()

    async def create_user(self, username: str, password: str, email: str = None) -> Tuple[bool, str]:
        """Create a new user account."""
        try:
            # Validate input
            if not username or len(username) < 3:
                return False, "Username must be at least 3 characters long"

            if not password or len(password) < 6:
                return False, "Password must be at least 6 characters long"

            # Check if username already exists
            existing_user = await self.get_user_by_username(username)
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

            # Only add email if provided
            if email:
                user_data['email'] = email

            result = await self.db.execute_query('users', 'insert', data=user_data)

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

    async def authenticate_user(self, username: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
        """Authenticate user credentials."""
        logger.info(f"Authenticating user: {username}")

        try:
            # Get user by username
            user = await self.get_user_by_username(username)
            if not user:
                logger.warning(f"User not found: {username}")
                return False, "Username not found", None

            # Check if user is active
            if not user.get('is_active', True):
                logger.warning(f"User account disabled: {username}")
                return False, "Account is disabled", None

            # Verify password
            password_hash, _ = self._hash_password(password, user['salt'])

            if password_hash == user['password_hash']:
                # Update last login
                await self.update_last_login(user['id'])
                logger.info(f"User authenticated successfully: {username}")
                return True, "Authentication successful", user
            else:
                logger.warning(f"Invalid password for user: {username}")
                return False, "Invalid password", None

        except Exception as e:
            logger.error(f"Error authenticating user {username}: {str(e)}")
            return False, f"Authentication error: {str(e)}", None

    async def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user by username."""
        logger.info(f"Getting user by username: {username}")

        try:
            result = await self.db.execute_query(
                'users', 
                'select', 
                eq={'username': username}
            )

            if result.data:
                user_data = result.data[0]
                logger.info(f"User found: {username}")
                return user_data
            
            logger.info(f"User not found: {username}")
            return None

        except Exception as e:
            logger.error(f"Error getting user by username {username}: {str(e)}")
            return None

    async def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Get user by user_id (legacy compatibility)."""
        try:
            result = await self.db.execute_query(
                'users',
                'select',
                eq={'user_id': user_id}
            )

            if result.data:
                return result.data[0]
            return None

        except Exception as e:
            logger.error(f"Error getting user by ID {user_id}: {str(e)}")
            return None

    async def get_user_by_uuid(self, uuid_id: str) -> Optional[Dict]:
        """Get user by UUID (primary key)."""
        try:
            result = await self.db.execute_query(
                'users',
                'select',
                eq={'id': uuid_id}
            )

            if result.data:
                return result.data[0]
            return None

        except Exception as e:
            logger.error(f"Error getting user by UUID {uuid_id}: {str(e)}")
            return None

    async def update_last_login(self, uuid_id: str) -> bool:
        """Update user's last login timestamp."""
        try:
            result = await self.db.execute_query(
                'users',
                'update',
                data={'last_login': datetime.now().isoformat()},
                eq={'id': uuid_id}
            )

            return bool(result.data)

        except Exception as e:
            logger.error(f"Error updating last login for user {uuid_id}: {str(e)}")
            return False

    async def update_user_profile(self, user_id: str, data: Dict) -> bool:
        """Update user profile information."""
        try:
            # Remove sensitive fields that shouldn't be updated directly
            safe_data = {k: v for k, v in data.items()
                        if k not in ['id', 'password_hash', 'salt', 'user_id', 'created_at']}

            if not safe_data:
                return False

            safe_data['updated_at'] = datetime.now().isoformat()

            result = await self.db.execute_query(
                'users',
                'update',
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
        """Update user password."""
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
            result = await self.db.execute_query(
                'users',
                'update',
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

    async def deactivate_user(self, user_id: str) -> bool:
        """Deactivate user account (soft delete)."""
        try:
            result = await self.db.execute_query(
                'users',
                'update',
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
        """Permanently delete user account and all associated data."""
        try:
            result = await self.db.execute_query(
                'users',
                'delete',
                eq={'user_id': user_id}
            )

            if result.data:
                logger.info(f"User permanently deleted: {user_id}")
                return True
            return False

        except Exception as e:
            logger.error(f"Error deleting user {user_id}: {str(e)}")
            return False

# Global user service instance
user_service = UserService()

# Convenience functions for backward compatibility
async def create_user(username: str, password: str, email: str = None) -> Tuple[bool, str]:
    """Create user account."""
    return await user_service.create_user(username, password, email)

async def authenticate_user(username: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
    """Authenticate user."""
    return await user_service.authenticate_user(username, password)

async def get_user_by_id(user_id: str) -> Optional[Dict]:
    """Get user by ID."""
    return await user_service.get_user_by_id(user_id)