#!/usr/bin/env python3
"""
Check what users exist in the database
"""

import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_users():
    """Check what users exist in the database."""
    print("🔍 Checking users in database...")
    
    try:
        from services.user_service import user_service
        
        # Try to get all users (this might not work due to security)
        print("Attempting to list users...")
        
        # Let's try to get user by username instead
        usernames_to_try = ['admin', 'test', 'user', 'demo']
        
        for username in usernames_to_try:
            try:
                user_data = await user_service.get_user_by_username(username)
                if user_data:
                    print(f"✅ Found user: {username}")
                    print(f"   - ID: {user_data.get('legacy_id', 'N/A')}")
                    print(f"   - UUID: {user_data.get('id', 'N/A')}")
                    print(f"   - Email: {user_data.get('email', 'N/A')}")
                else:
                    print(f"❌ User not found: {username}")
            except Exception as e:
                print(f"❌ Error checking user {username}: {e}")
        
        # Also try some common user IDs
        print("\nTrying common user IDs...")
        for user_id in [1, 2, 3, 'admin', 'test']:
            try:
                user_data = await user_service.get_user_by_id(user_id)
                if user_data:
                    print(f"✅ Found user by ID {user_id}: {user_data.get('username', 'N/A')}")
                else:
                    print(f"❌ No user found with ID: {user_id}")
            except Exception as e:
                print(f"❌ Error checking user ID {user_id}: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to check users: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = asyncio.run(check_users())
    print(f"\n🎯 Check result: {'SUCCESS' if success else 'FAILED'}")